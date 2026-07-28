"""
Book service: orchestrates the full upload pipeline.
  1. Upload PDF to R2
  2. Parse metadata + extract cover
  3. Fetch cover from APIs if not embedded
  4. Upload cover to R2
  5. Save book document to MongoDB
  6. Enqueue Celery task for background embedding
"""
import io
from typing import Optional
from datetime import datetime, timezone
from bson import ObjectId

from app.config import Config
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
    Full book upload pipeline (synchronous part).
    Embedding is queued as a background Celery task.

    Returns the newly created book document (public representation).
    """
    # ── 1. Upload PDF to R2 ───────────────────────────────────
    pdf_key, _ = r2_storage.upload_file(
        pdf_bytes,
        content_type="application/pdf",
        folder="books",
        extension="pdf",
    )

    # ── 2. Parse PDF ──────────────────────────────────────────
    parsed = parse_pdf(pdf_bytes)

    # ── 3. Handle cover ───────────────────────────────────────
    cover_key = None
    cover_url = None

    if parsed.cover_bytes:
        # Upload embedded cover to R2
        cover_key, cover_url = r2_storage.upload_file(
            parsed.cover_bytes,
            content_type=f"image/{parsed.cover_ext}",
            folder="covers",
            extension=parsed.cover_ext,
        )
    else:
        # Fetch cover from Open Library / Google Books
        cover_url = fetch_cover_url(
            title=parsed.title,
            author=parsed.author,
        )
        # We store the external URL directly (no R2 upload for external URLs)

    # ── 4. Build and insert MongoDB document ──────────────────
    book_doc = BookModel.new(
        user_id=user_id,
        original_filename=original_filename,
        file_key=pdf_key,
        cover_key=cover_key,
        cover_url=cover_url,
        title=parsed.title,
        author=parsed.author,
        language=parsed.language,
        page_count=parsed.page_count,
        file_size_bytes=len(pdf_bytes),
    )
    result = db.books.insert_one(book_doc)
    book_id = str(result.inserted_id)

    # ── 5. Update user reading profile ───────────────────────
    _update_reading_profile(db, user_id, parsed)

    # ── 6. Enqueue background embedding task ──────────────────
    _enqueue_embedding(book_id, user_id, parsed.text_chunks, parsed.title)

    # Return public representation
    book_doc["_id"] = result.inserted_id
    return BookModel.to_public(
        book_doc,
        file_url=r2_storage.get_presigned_url(pdf_key),
    )


def _update_reading_profile(db, user_id: str, parsed) -> None:
    """Increment genre/author/language counts in the user's reading profile."""
    updates = {}
    if parsed.language:
        updates[f"reading_profile.languages.{parsed.language}"] = 1
    if parsed.author:
        safe_author = parsed.author.replace(".", "_")
        updates[f"reading_profile.authors.{safe_author}"] = 1

    if updates:
        db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": updates, "$set": {"updated_at": datetime.now(timezone.utc)}},
        )


def _enqueue_embedding(
    book_id: str, user_id: str, chunks: list, title: str
) -> None:
    """Queue the embedding job. Falls back to synchronous if Celery unavailable."""
    try:
        from app.tasks import embed_book_task
        embed_book_task.delay(book_id, user_id, chunks, title)
    except Exception:
        # Celery not running — embed synchronously (blocks request, dev only)
        _embed_synchronously(book_id, user_id, chunks, title)


def _embed_synchronously(
    book_id: str, user_id: str, chunks: list, title: str
) -> None:
    from app.utils.embedder import embed_chunks
    from pymongo import MongoClient
    from app.config import Config
    import certifi

    client = MongoClient(Config.MONGO_URI, tlsCAFile=certifi.where())
    db = client[Config.MONGO_DB_NAME]

    try:
        db.books.update_one(
            {"_id": ObjectId(book_id)},
            {"$set": {"embedding_status": EmbeddingStatus.PROCESSING}},
        )
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
        db.books.update_one(
            {"_id": ObjectId(book_id)},
            {"$set": {"embedding_status": EmbeddingStatus.FAILED}},
        )
    finally:
        client.close()
