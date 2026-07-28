"""
Embedder: converts text chunks → vectors → stores in ChromaDB.
Uses sentence-transformers locally (CPU-friendly, no API key needed).
"""
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import numpy as np

from app.config import Config
from app.utils.chroma_client import get_or_create_collection

# ── Singleton embedding model (loaded once on first use) ─────
_model: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(Config.EMBEDDING_MODEL)
    return _model


def embed_chunks(
    user_id: str,
    book_id: str,
    chunks: List[str],
    book_title: str = "",
    batch_size: int = 64,
) -> int:
    """
    Embed a list of text chunks and store them in ChromaDB.

    Args:
        user_id   : owner of the book
        book_id   : MongoDB _id of the book document
        chunks    : list of text strings to embed
        book_title: stored as metadata for source attribution
        batch_size: how many chunks to embed at once (memory management)

    Returns:
        Number of chunks stored.
    """
    if not chunks:
        return 0

    model = get_embedding_model()
    collection = get_or_create_collection(user_id, book_id)

    total = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i: i + batch_size]

        # Generate embeddings
        embeddings: np.ndarray = model.encode(
            batch,
            normalize_embeddings=True,  # cosine similarity works best normalised
            show_progress_bar=False,
        )

        # Build IDs and metadata
        ids = [f"{book_id}_chunk_{i + j}" for j in range(len(batch))]
        metadatas = [
            {
                "book_id": book_id,
                "book_title": book_title,
                "chunk_index": i + j,
                "user_id": user_id,
            }
            for j in range(len(batch))
        ]

        collection.upsert(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=batch,
            metadatas=metadatas,
        )
        total += len(batch)

    return total


def query_collection(
    user_id: str,
    book_id: str,
    query_text: str,
    n_results: int = 5,
) -> List[dict]:
    """
    Query a single book's ChromaDB collection for relevant chunks.

    Returns list of {text, book_id, book_title, chunk_index, distance}
    """
    model = get_embedding_model()
    collection = get_or_create_collection(user_id, book_id)

    query_embedding = model.encode(
        [query_text], normalize_embeddings=True
    ).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    output = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(docs, metas, dists):
        output.append({
            "text": doc,
            "book_id": meta.get("book_id"),
            "book_title": meta.get("book_title"),
            "chunk_index": meta.get("chunk_index"),
            "distance": dist,
        })

    return output


def query_multiple_collections(
    user_id: str,
    book_ids: List[str],
    query_text: str,
    n_results_per_book: int = 3,
) -> List[dict]:
    """
    Query multiple books and return merged, ranked results.
    """
    all_results = []
    for book_id in book_ids:
        try:
            results = query_collection(user_id, book_id, query_text, n_results_per_book)
            all_results.extend(results)
        except Exception:
            continue

    # Sort by distance (lower = more similar in cosine space)
    all_results.sort(key=lambda x: x.get("distance", 1.0))
    return all_results
