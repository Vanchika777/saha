from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from app.config import Config

# ── Extensions (module-level so routes can import them) ──────
socketio = SocketIO()
bcrypt = Bcrypt()
mongo_client: MongoClient = None
db = None


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH

    # ── CORS ─────────────────────────────────────────────────
    CORS(
        app,
        origins=[Config.FRONTEND_URL],
        supports_credentials=True,
    )

    # ── Extensions init ──────────────────────────────────────
    bcrypt.init_app(app)
    socketio.init_app(
        app,
        cors_allowed_origins=Config.FRONTEND_URL,
        async_mode="eventlet",
        logger=False,
        engineio_logger=False,
    )

    # ── MongoDB ──────────────────────────────────────────────
    global mongo_client, db
    mongo_client = MongoClient(Config.MONGO_URI, tlsCAFile=_get_ca_bundle())
    db = mongo_client[Config.MONGO_DB_NAME]
    _ensure_indexes(db)
    app.db = db  # attach to app for request context access

    # ── Register Blueprints ──────────────────────────────────
    from app.routes.auth import auth_bp
    from app.routes.books import books_bp
    from app.routes.chat import chat_bp
    from app.routes.recommend import recommend_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(books_bp, url_prefix="/api/books")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    app.register_blueprint(recommend_bp, url_prefix="/api/recommend")

    # ── Health check ─────────────────────────────────────────
    @app.get("/api/health")
    def health():
        return {"status": "ok", "app": "saha"}

    return app


def _get_ca_bundle() -> str | None:
    """Return certifi CA bundle for MongoDB TLS (Atlas requires this)."""
    try:
        import certifi
        return certifi.where()
    except ImportError:
        return None


def _ensure_indexes(db) -> None:
    """Create MongoDB indexes on startup."""
    # Users
    db.users.create_index("email", unique=True)
    db.users.create_index("google_id", sparse=True)

    # Books
    db.books.create_index([("user_id", 1), ("created_at", -1)])
    db.books.create_index("embedding_status")

    # Chat sessions
    db.chat_sessions.create_index([("user_id", 1), ("updated_at", -1)])
    db.chat_sessions.create_index("session_id", unique=True)
    # TTL: guest sessions expire after 24 hours
    db.chat_sessions.create_index(
        "expires_at", expireAfterSeconds=0, sparse=True
    )
