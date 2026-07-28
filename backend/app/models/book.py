from datetime import datetime, timezone
from typing import Optional, List
from enum import Enum


class EmbeddingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class BookModel:
    """
    MongoDB schema for 'books' collection.

    Each document represents one uploaded book for one user.
    Vector embeddings are stored in ChromaDB (keyed by book_id).
    The PDF and cover are stored in Cloudflare R2.
    """

    COLLECTION = "books"

    @staticmethod
    def new(
        user_id: str,
        original_filename: str,
        file_key: str,              # R2 object key for the PDF
        cover_key: Optional[str],   # R2 object key for the cover image
        cover_url: Optional[str],   # public URL of cover
        title: str,
        author: Optional[str] = None,
        language: Optional[str] = None,
        genre: Optional[str] = None,
        country: Optional[str] = None,
        page_count: int = 0,
        file_size_bytes: int = 0,
        tags: Optional[List[str]] = None,
        isbn: Optional[str] = None,
    ) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "user_id": user_id,
            "original_filename": original_filename,
            "file_key": file_key,
            "cover_key": cover_key,
            "cover_url": cover_url,
            "title": title,
            "author": author,
            "language": language or "unknown",
            "genre": genre,
            "country": country,
            "page_count": page_count,
            "file_size_bytes": file_size_bytes,
            "tags": tags or [],
            "isbn": isbn,
            "embedding_status": EmbeddingStatus.PENDING,
            "embedding_chunk_count": 0,
            "created_at": now,
            "updated_at": now,
        }

    @staticmethod
    def to_public(book: dict, file_url: Optional[str] = None) -> dict:
        return {
            "id": str(book["_id"]),
            "title": book.get("title", ""),
            "author": book.get("author"),
            "language": book.get("language"),
            "genre": book.get("genre"),
            "country": book.get("country"),
            "cover_url": book.get("cover_url"),
            "file_url": file_url,
            "page_count": book.get("page_count", 0),
            "file_size_bytes": book.get("file_size_bytes", 0),
            "tags": book.get("tags", []),
            "embedding_status": book.get("embedding_status"),
            "embedding_chunk_count": book.get("embedding_chunk_count", 0),
            "created_at": book["created_at"].isoformat()
            if isinstance(book.get("created_at"), datetime)
            else "",
        }
