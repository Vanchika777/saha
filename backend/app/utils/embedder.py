"""
Embedder: converts text chunks → vectors → stores in ChromaDB.
Uses Hugging Face Inference API to keep RAM lightweight for cloud deployment.
"""
from typing import List
import os
import requests

from app.config import Config
from app.utils.chroma_client import get_or_create_collection

HF_API_URL = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{Config.EMBEDDING_MODEL}"


def get_huggingface_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Call Hugging Face Inference API for a list of strings and return vector embeddings.
    """
    api_key = Config.HUGGINGFACE_API_KEY
    if not api_key:
        raise ValueError("HUGGINGFACE_API_KEY or HF_TOKEN is missing in environment variables!")

    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "inputs": texts,
        "options": {"wait_for_model": True}
    }

    response = requests.post(HF_API_URL, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Hugging Face API Error ({response.status_code}): {response.text}")

    results = response.json()
    
    # Ensure correct format for lists of embeddings
    embeddings = []
    for item in results:
        # Handle token-level pooling if returned nested
        if isinstance(item, list) and len(item) > 0 and isinstance(item[0], list):
            item = [sum(col) / len(col) for col in zip(*item)]
        embeddings.append(item)

    return embeddings


def embed_chunks(
    user_id: str,
    book_id: str,
    chunks: List[str],
    book_title: str = "",
    batch_size: int = 32,
) -> int:
    """
    Embed a list of text chunks via Hugging Face API and store them in ChromaDB.
    """
    if not chunks:
        return 0

    collection = get_or_create_collection(user_id, book_id)

    total = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i: i + batch_size]

        # Generate embeddings via Hugging Face API
        embeddings = get_huggingface_embeddings(batch)

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
            embeddings=embeddings,
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
    """
    collection = get_or_create_collection(user_id, book_id)

    query_embedding = get_huggingface_embeddings([query_text])

    count = collection.count()
    if count == 0:
        return []

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(n_results, count),
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

    all_results.sort(key=lambda x: x.get("distance", 1.0))
    return all_results