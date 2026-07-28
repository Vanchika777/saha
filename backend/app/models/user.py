from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId


class UserModel:
    """
    MongoDB schema for 'users' collection.

    Fields:
        _id          : ObjectId (auto)
        email        : str, unique
        password_hash: str | None  (None for OAuth-only users)
        google_id    : str | None
        display_name : str
        avatar_url   : str | None
        is_guest     : bool
        created_at   : datetime
        updated_at   : datetime
        reading_profile: dict  — aggregated genre/author/language preferences
    """

    COLLECTION = "users"

    @staticmethod
    def new(
        email: str,
        display_name: str,
        password_hash: Optional[str] = None,
        google_id: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "email": email,
            "password_hash": password_hash,
            "google_id": google_id,
            "display_name": display_name,
            "avatar_url": avatar_url,
            "is_guest": False,
            "reading_profile": {
                "genres": {},       # genre -> count
                "authors": {},      # author -> count
                "languages": {},    # language -> count
                "countries": {},    # country -> count
            },
            "created_at": now,
            "updated_at": now,
        }

    @staticmethod
    def to_public(user: dict) -> dict:
        """Strip sensitive fields before sending to frontend."""
        return {
            "id": str(user["_id"]),
            "email": user.get("email"),
            "display_name": user.get("display_name"),
            "avatar_url": user.get("avatar_url"),
            "created_at": user.get("created_at", "").isoformat()
            if isinstance(user.get("created_at"), datetime)
            else "",
        }
