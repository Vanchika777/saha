"""
Recommendation routes.
Supports both authenticated users and guest users.
"""
from flask import Blueprint, request, jsonify, current_app, g

from app.utils.auth_helpers import optional_auth
from app.routes.books import _get_effective_user_id
from app.services.recommendation_service import get_recommendations

recommend_bp = Blueprint("recommend", __name__)


@recommend_bp.get("/")
@optional_auth
def recommendations():
    """
    Get book recommendations based on uploaded books.
    """
    db = current_app.db
    effective_id = _get_effective_user_id()

    # Check user/guest has books
    books = list(db.books.find({"user_id": effective_id}))
    if not books:
        return jsonify({
            "error": "Upload at least one book to get recommendations",
            "recommendations": [],
        }), 200

    # Build reading profile dynamically from uploaded books for guests or users
    profile = {"genres": {}, "authors": {}, "languages": {}, "countries": {}}
    if g.user:
        profile = g.user.get("reading_profile", profile)
    else:
        for b in books:
            if b.get("genre"):
                profile["genres"][b["genre"]] = profile["genres"].get(b["genre"], 0) + 1
            if b.get("author"):
                profile["authors"][b["author"]] = profile["authors"].get(b["author"], 0) + 1
            if b.get("language"):
                profile["languages"][b["language"]] = profile["languages"].get(b["language"], 0) + 1

    limit = min(int(request.args.get("limit", 12)), 24)

    try:
        recs = get_recommendations(profile, limit=limit)
        return jsonify({"recommendations": recs, "total": len(recs)})
    except Exception as e:
        print(f"[Recommendation Error]: {e}")
        return jsonify({"error": "Failed to fetch recommendations", "detail": str(e)}), 500


@recommend_bp.get("/profile")
@optional_auth
def reading_profile():
    """Return reading profile."""
    profile = g.user.get("reading_profile", {}) if g.user else {}
    return jsonify({"reading_profile": profile})
