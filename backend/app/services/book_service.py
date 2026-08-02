"""
Book service: fast cover-first upload pipeline.
1. Save PDF file to storage.
2. Extract metadata & cover artwork synchronously (~1 sec).
3. Insert complete book doc into MongoDB with real cover & author.
4. Return book object immediately to frontend (no 'Extracting...' / 'Indexing...' state).
5. Silently offload heavy ChromaDB vector chunk embeddings to background thread.
"""
import threading
from datetime import datetime, timezone
from bson import ObjectId

from app.models.book import BookModel, EmbeddingStatus
from app.utils.pdf_parser import parse_pdf
from app.utils.cover_fetcher import fetch_cover_url
from app.utils import r2_storage


def create_book(
    db,
    user_id: str,
    pdf_bytes: bytes,
    original_filename: str,
) -> dict:
    """
    Cover-first upload pipeline:
    Extracts cover & title instantly so response contains complete metadata,
    then offloads vector indexing in the background.
    """
    # ── 1. Upload PDF File ──────────────────────────────────────
    pdf_key, _ = r2_storage.upload_file(
        pdf_bytes,
        content_type="application/pdf",
        folder="books",
        extension="pdf",
    )

    # ── 2. Parse PDF Metadata & Cover Synchronously (~0.5 - 1s) ─
    parsed = parse_pdf(pdf_bytes)

    # Clean fallback title if parsing didn't find one
    fallback_title = (
        original_filename.rsplit('.', 1)[0]
        .replace('-', ' ')
        .replace('_', ' ')
        .title()
    )
    final_title = (
        parsed.title
        if (parsed.title and len(parsed.title.strip()) > 0)
        else fallback_title
    )
    final_author = (
        parsed.author
        if (parsed.author and len(parsed.author.strip()) > 0)
        else "Unknown Author"
    )

    # ── 3. Extract or Fetch Cover Image Immediately ─────────────
    cover_key = None
    cover_url = None

    if parsed.cover_bytes:
        cover_key, cover_url = r2_storage.upload_file(
            parsed.cover_bytes,
            content_type=f"image/{parsed.cover_ext}",
            folder="covers",
            extension=parsed.cover_ext,
        )
    else:
        # Fetch cover directly from Open Library / Google Books API
        cover_url = fetch_cover_url(
            title=final_title,
            author=final_author,
        )

    # ── 4. Insert Complete Document into MongoDB ───────────────
    book_doc = BookModel.new(
        user_id=user_id,
        original_filename=original_filename,
        file_key=pdf_key,
        cover_key=cover_key,
        cover_url=cover_url,
        title=final_title,
        author=final_author,
        language=parsed.language,
        page_count=parsed.page_count,
        file_size_bytes=len(pdf_bytes),
    )
    book_doc["embedding_status"] = EmbeddingStatus.PROCESSING

    result = db.books.insert_one(book_doc)
    book_id = str(result.inserted_id)

    # ── 5. Update User Reading Profile ────────────────────────
    _update_reading_profile(db, user_id, parsed)

    # ── 6. Offload ONLY Heavy Vector Chunking to Background ─────
    if parsed.text_chunks:
        thread = threading.Thread(
            target=_embed_chunks_background,
            args=(book_id, user_id, parsed.text_chunks, final_title),
            daemon=True,
        )
        thread.start()
    else:
        db.books.update_one(
            {"_id": result.inserted_id},
            {
                "$set": {
                    "embedding_status": EmbeddingStatus.DONE,
                    "embedding_chunk_count": 0,
                }
            },
        )

    # ── 7. Return Complete Book Object with Real Cover & Author ──
    book_doc["_id"] = result.inserted_id
    file_url = r2_storage.get_presigned_url(pdf_key) if pdf_key else ""

    # Returns doc directly without invalid extra keyword arguments
    return BookModel.to_public(book_doc, file_url=file_url)


def _update_reading_profile(db, user_id: str, parsed) -> None:
    """Increment genre/author/language counts in user profile."""
    updates = {}
    if parsed.language:
        updates[f"reading_profile.languages.{parsed.language}"] = 1
    if parsed.author:
        safe_author = parsed.author.replace(".", "_")
        updates[f"reading_profile.authors.{safe_author}"] = 1

    if updates:
        try:
            user_obj_id = ObjectId(user_id)
            db.users.update_one(
                {"_id": user_obj_id},
                {
                    "$inc": updates,
                    "$set": {"updated_at": datetime.now(timezone.utc)},
                },
            )
        except Exception:
            pass


def _embed_chunks_background(
    book_id: str, user_id: str, chunks: list, title: str
) -> None:
    """Silent background worker that processes ChromaDB vector embeddings."""
    from pymongo import MongoClient
    from app.config import Config
    from app.utils.embedder import embed_chunks

    kwargs = {}
    if Config.MONGO_URI.startswith("mongodb+srv://"):
        try:
            import certifi
            kwargs["tlsCAFile"] = certifi.where()
        except ImportError:
            pass

    client = MongoClient(Config.MONGO_URI, **kwargs)
    db = client[Config.MONGO_DB_NAME]

    try:
        count = embed_chunks(user_id, book_id, chunks, title)
        db.books.update_one(
            {"_id": ObjectId(book_id)},
            {
                "$set": {
                    "embedding_status": EmbeddingStatus.DONE,
                    "embedding_chunk_count": count,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
    except Exception as e:
        print(f"[Embedding Background Error for {book_id}]: {e}")
        db.books.update_one(
            {"_id": ObjectId(book_id)},
            {"$set": {"embedding_status": EmbeddingStatus.FAILED}},
        )
    finally:
        client.close()