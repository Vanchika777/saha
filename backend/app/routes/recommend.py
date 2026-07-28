"""
Recommendation routes.
Requires the user to have at least one book uploaded.
"""
from flask import Blueprint, request, jsonify, current_app, g

from app.utils.auth_helpers import login_required
from app.services.recommendation_service import get_recommendations

recommend_bp = Blueprint("recommend", __name__)


@recommend_bp.get("/")
@login_required
def recommendations():
    """
    Get book recommendations based on the user's reading profile.
    User must have uploaded at least one book.
    """
    db = current_app.db

    # Check user has books
    book_count = db.books.count_documents({"user_id": g.user_id})
    if book_count == 0:
        return jsonify({
            "error": "Upload at least one book to get recommendations",
            "recommendations": [],
        }), 200

    user = g.user
    reading_profile = user.get("reading_profile", {
        "genres": {}, "authors": {}, "languages": {}, "countries": {},
    })

    limit = min(int(request.args.get("limit", 12)), 24)

    try:
        recs = get_recommendations(reading_profile, limit=limit)
        return jsonify({"recommendations": recs, "total": len(recs)})
    except Exception as e:
        return jsonify({"error": "Failed to fetch recommendations", "detail": str(e)}), 500


@recommend_bp.get("/profile")
@login_required
def reading_profile():
    """Return the user's reading profile (genre/author/language stats)."""
    profile = g.user.get("reading_profile", {})
    return jsonify({"reading_profile": profile})
