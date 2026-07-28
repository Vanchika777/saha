"""
JWT authentication helpers and route protection decorator.
"""
import jwt
import functools
from datetime import datetime, timezone, timedelta
from typing import Optional
from flask import request, jsonify, current_app, g
from bson import ObjectId

from app.config import Config


def generate_token(user_id: str, email: str) -> str:
    """Create a signed JWT for a logged-in user."""
    payload = {
        "sub": user_id,
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=Config.JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT. Returns payload or None."""
    try:
        return jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def _extract_token() -> Optional[str]:
    """Pull Bearer token from Authorization header or cookie."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return request.cookies.get("saha_token")


def login_required(f):
    """Decorator: require a valid JWT. Injects g.user_id and g.user."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify({"error": "Authentication required"}), 401

        payload = decode_token(token)
        if not payload:
            return jsonify({"error": "Token expired or invalid"}), 401

        db = current_app.db
        user = db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            return jsonify({"error": "User not found"}), 401

        g.user_id = str(user["_id"])
        g.user = user
        return f(*args, **kwargs)
    return decorated


def optional_auth(f):
    """
    Decorator: attach user to g if token is present, but don't block guests.
    g.user_id will be None for guests.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        g.user_id = None
        g.user = None
        token = _extract_token()
        if token:
            payload = decode_token(token)
            if payload:
                db = current_app.db
                user = db.users.find_one({"_id": ObjectId(payload["sub"])})
                if user:
                    g.user_id = str(user["_id"])
                    g.user = user
        return f(*args, **kwargs)
    return decorated
