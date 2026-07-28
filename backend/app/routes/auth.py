"""
Auth routes: register, login, Google OAuth, logout, /me
"""
from flask import Blueprint, request, jsonify, current_app, g
from datetime import datetime, timezone

from app.config import Config
from app.models.user import UserModel
from app.utils.auth_helpers import generate_token, login_required

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    """Email + password registration."""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")
    display_name = (data.get("display_name") or email.split("@")[0]).strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    db = current_app.db
    if db.users.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 409

    from app import bcrypt
    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    user_doc = UserModel.new(
        email=email,
        display_name=display_name,
        password_hash=password_hash,
    )
    result = db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    token = generate_token(str(result.inserted_id), email)
    return jsonify({
        "token": token,
        "user": UserModel.to_public(user_doc),
    }), 201


@auth_bp.post("/login")
def login():
    """Email + password login."""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    db = current_app.db
    user = db.users.find_one({"email": email})
    if not user or not user.get("password_hash"):
        return jsonify({"error": "Invalid credentials"}), 401

    from app import bcrypt
    if not bcrypt.check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = generate_token(str(user["_id"]), email)
    return jsonify({
        "token": token,
        "user": UserModel.to_public(user),
    })


@auth_bp.get("/google")
def google_login():
    """Redirect user to Google OAuth consent screen."""
    from authlib.integrations.flask_client import OAuth
    # OAuth client is initialised lazily here to keep app factory clean
    oauth = _get_oauth_client()
    redirect_uri = Config.GOOGLE_REDIRECT_URI
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.get("/google/callback")
def google_callback():
    """Handle Google OAuth callback, create/update user, issue JWT."""
    from authlib.integrations.flask_client import OAuth
    oauth = _get_oauth_client()

    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get("userinfo") or oauth.google.userinfo()
    except Exception as e:
        return jsonify({"error": "Google OAuth failed", "detail": str(e)}), 400

    google_id = user_info.get("sub")
    email = (user_info.get("email") or "").lower()
    name = user_info.get("name") or email.split("@")[0]
    avatar = user_info.get("picture")

    db = current_app.db
    # Try to find existing user by google_id or email
    user = db.users.find_one({"$or": [{"google_id": google_id}, {"email": email}]})

    if user:
        # Update google_id + avatar if missing
        db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "google_id": google_id,
                "avatar_url": avatar,
                "updated_at": datetime.now(timezone.utc),
            }},
        )
        user["google_id"] = google_id
    else:
        user_doc = UserModel.new(
            email=email,
            display_name=name,
            google_id=google_id,
            avatar_url=avatar,
        )
        result = db.users.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        user = user_doc

    jwt_token = generate_token(str(user["_id"]), email)

    # Redirect to frontend with token in query param (frontend stores it)
    frontend_url = Config.FRONTEND_URL
    return f"""
    <script>
      window.opener && window.opener.postMessage(
        {{ type: 'GOOGLE_AUTH_SUCCESS', token: '{jwt_token}' }},
        '{frontend_url}'
      );
      window.close();
    </script>
    """


@auth_bp.get("/me")
@login_required
def me():
    """Return the currently authenticated user's profile."""
    return jsonify({"user": UserModel.to_public(g.user)})


@auth_bp.post("/logout")
def logout():
    """Client-side logout — just confirm (token is stateless)."""
    return jsonify({"message": "Logged out successfully"})


# ── Helpers ───────────────────────────────────────────────────

_oauth_instance = None


def _get_oauth_client():
    """Lazy OAuth client (avoids circular import with app factory)."""
    global _oauth_instance
    if _oauth_instance is None:
        from authlib.integrations.flask_client import OAuth
        from flask import current_app
        _oauth_instance = OAuth(current_app)
        _oauth_instance.register(
            name="google",
            client_id=Config.GOOGLE_CLIENT_ID,
            client_secret=Config.GOOGLE_CLIENT_SECRET,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
    return _oauth_instance
