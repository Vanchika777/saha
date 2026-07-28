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