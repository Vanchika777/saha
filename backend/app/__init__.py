# Flask app initialization & extensions
from flask import Flask, jsonify
from flask_cors import CORS
from app.config import Config
from app.utils.db import get_db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Allow requests from React frontend
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    app.db = get_db()

    from app.routes.auth import auth_bp
    from app.routes.books import books_bp
    from app.routes.chat import chat_bp
    from app.routes.recommend import recommend_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(books_bp, url_prefix="/api/books")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    app.register_blueprint(recommend_bp, url_prefix="/api/recommend")


    # Health check route to test DB connectivity
    @app.route("/api/health", methods=["GET"])
    def health_check():
        try:
            db = get_db()
            # Command ping tests active MongoDB connection
            db.command("ping")
            return jsonify({
                "status": "online",
                "database": "connected",
                "app": "Saha AI Backend"
            }), 200
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    return app