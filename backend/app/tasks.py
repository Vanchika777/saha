"""
Celery app and task definitions.
"""
from celery import Celery
from app.config import Config

celery_app = Celery(
    "saha",
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)


@celery_app.task(bind=True, max_retries=2, name="embed_book_task")
def embed_book_task(self, book_id: str, user_id: str, chunks: list, title: str):
    """
    Background task: embed all text chunks of a book into ChromaDB.
    Updates MongoDB embedding_status throughout.
    """
    from datetime import datetime, timezone
    from bson import ObjectId
    from pymongo import MongoClient
    import certifi

    from app.utils.embedder import embed_chunks
    from app.models.book import EmbeddingStatus

    client = MongoClient(Config.MONGO_URI, tlsCAFile=certifi.where())
    db = client[Config.MONGO_DB_NAME]

    try:
        # Mark as processing
        db.books.update_one(
            {"_id": ObjectId(book_id)},
            {"$set": {"embedding_status": EmbeddingStatus.PROCESSING,
                      "updated_at": datetime.now(timezone.utc)}},
        )

        count = embed_chunks(user_id, book_id, chunks, title)

        # Mark as done
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
        return {"status": "done", "chunks": count}

    except Exception as exc:
        db.books.update_one(
            {"_id": ObjectId(book_id)},
            {"$set": {"embedding_status": EmbeddingStatus.FAILED,
                      "updated_at": datetime.now(timezone.utc)}},
        )
        raise self.retry(exc=exc, countdown=30)
    finally:
        client.close()
