import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Flask ────────────────────────────────────────────────
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
    PORT: int = int(os.getenv("PORT", 5000))
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # ── MongoDB ──────────────────────────────────────────────
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/saha")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "saha")

    # ── JWT ──────────────────────────────────────────────────
    JWT_SECRET: str = os.getenv("JWT_SECRET", "jwt-secret-change-in-production")
    JWT_EXPIRY_HOURS: int = int(os.getenv("JWT_EXPIRY_HOURS", 72))

    # ── Google OAuth ─────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:5000/api/auth/google/callback"
    )

    # ── Cloudflare R2 ────────────────────────────────────────
    R2_ACCOUNT_ID: str = os.getenv("R2_ACCOUNT_ID", "")
    R2_ACCESS_KEY_ID: str = os.getenv("R2_ACCESS_KEY_ID", "")
    R2_SECRET_ACCESS_KEY: str = os.getenv("R2_SECRET_ACCESS_KEY", "")
    R2_BUCKET_NAME: str = os.getenv("R2_BUCKET_NAME", "saha-books")
    R2_PUBLIC_URL: str = os.getenv("R2_PUBLIC_URL", "")  # e.g. https://pub-xxx.r2.dev

    # ── Groq ─────────────────────────────────────────────────
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # ── ChromaDB ─────────────────────────────────────────────
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")

    # ── Embeddings ───────────────────────────────────────────
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )

    # ── Celery / Redis ───────────────────────────────────────
    CELERY_BROKER_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # ── External Book APIs ───────────────────────────────────
    OPEN_LIBRARY_API: str = "https://openlibrary.org"
    GOOGLE_BOOKS_API: str = "https://www.googleapis.com/books/v1"
    GUTENBERG_API: str = "https://gutendex.com"
    GOOGLE_BOOKS_API_KEY: str = os.getenv("GOOGLE_BOOKS_API_KEY", "")  # optional

    # ── Upload Limits ────────────────────────────────────────
    MAX_PDF_SIZE_MB: int = int(os.getenv("MAX_PDF_SIZE_MB", 50))
    MAX_CONTENT_LENGTH: int = MAX_PDF_SIZE_MB * 1024 * 1024
