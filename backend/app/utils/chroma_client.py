"""
ChromaDB client singleton.
All collections are namespaced: saha_{user_id}_{book_id}
"""
import chromadb
from chromadb.config import Settings
from functools import lru_cache
from typing import Optional

from app.config import Config

_client: Optional[chromadb.PersistentClient] = None


def get_chroma_client() -> chromadb.PersistentClient:
    """Return the shared ChromaDB client (lazy-initialised)."""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=Config.CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def get_collection_name(user_id: str, book_id: str) -> str:
    """Consistent collection naming: saha_{user_id}_{book_id}"""
    # ChromaDB collection names must be 3-63 chars, alphanumeric + underscores
    uid = user_id.replace("-", "")[:16]
    bid = book_id.replace("-", "")[:16]
    return f"saha_{uid}_{bid}"


def get_or_create_collection(user_id: str, book_id: str):
    """Get or create a ChromaDB collection for a specific book."""
    client = get_chroma_client()
    name = get_collection_name(user_id, book_id)
    return client.get_or_create_collection(
        name=name,
        metadata={
            "user_id": user_id,
            "book_id": book_id,
            "hnsw:space": "cosine",
        },
    )


def delete_collection(user_id: str, book_id: str) -> bool:
    """Delete a book's vector collection from ChromaDB."""
    client = get_chroma_client()
    name = get_collection_name(user_id, book_id)
    try:
        client.delete_collection(name)
        return True
    except Exception:
        return False


def list_user_collections(user_id: str) -> list[str]:
    """List all collection names belonging to a user."""
    client = get_chroma_client()
    all_cols = client.list_collections()
    prefix = f"saha_{user_id.replace('-', '')[:16]}_"
    return [c.name for c in all_cols if c.name.startswith(prefix)]
