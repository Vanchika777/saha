"""
Authentication routes (Email + Password only).
Handles user registration, login, token refresh, and profile retrieval.
"""
from datetime import datetime, timezone
import bcrypt
import jwt
from flask import Blueprint, request, jsonify
from bson import ObjectId

from app.config import Config
from app.utils.db import get_db

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _hash_password(password: str) -> str:
    """Hashes a plain text password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    """Verifies a plain text password against a stored hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def _generate_token(user_id: str, email: str) -> str:
    """Generates a JWT access token for authentication."""
    payload = {
        "sub": user_id,
        "email": email,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user account with email and password."""
    db = get_db()
    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    name = data.get("name", "").strip() or email.split("@")[0]

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long"}), 400

    # Check if user already exists
    existing_user = db.users.find_one({"email": email})
    if existing_user:
        return jsonify({"error": "An account with this email already exists"}), 409

    hashed_pw = _hash_password(password)

    # Construct user document
    now = datetime.now(timezone.utc)
    user_doc = {
        "email": email,
        "password_hash": hashed_pw,
        "name": name,
        "avatar_url": None,
        "created_at": now,
        "updated_at": now,
        "reading_profile": {
            "genres": {},
            "authors": {},
            "languages": {},
        },
    }

    result = db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)

    token = _generate_token(user_id, email)

    return jsonify({
        "message": "Account created successfully",
        "token": token,
        "user": {
            "id": user_id,
            "email": email,
            "name": name,
            "avatar_url": None,
        }
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Log in an existing user with email and password."""
    db = get_db()
    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = db.users.find_one({"email": email})
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.get("password_hash") or not _verify_password(password, user["password_hash"]):
        return jsonify({"error": "Invalid email or password"}), 401

    user_id = str(user["_id"])
    token = _generate_token(user_id, email)

    return jsonify({
        "token": token,
        "user": {
            "id": user_id,
            "email": user["email"],
            "name": user.get("name", ""),
            "avatar_url": user.get("avatar_url"),
        }
    }), 200


@auth_bp.route("/me", methods=["GET"])
def get_current_user():
    """Fetch current logged-in user info using JWT token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing or invalid authorization header"}), 401

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
    except Exception:
        return jsonify({"error": "Token is invalid or expired"}), 401

    db = get_db()
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "name": user.get("name", ""),
            "avatar_url": user.get("avatar_url"),
            "reading_profile": user.get("reading_profile", {}),
        }
    }), 200
