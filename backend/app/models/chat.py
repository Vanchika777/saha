from datetime import datetime, timezone
from typing import Optional, List
import uuid


class MessageRole(str):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatSessionModel:
    """
    MongoDB schema for 'chat_sessions' collection.

    One session = one conversation thread (can span many messages).
    Guest sessions have expires_at set (TTL index auto-deletes them).
    Logged-in sessions are permanent.
    """

    COLLECTION = "chat_sessions"

    @staticmethod
    def new(
        user_id: Optional[str] = None,
        title: str = "New Conversation",
        book_ids: Optional[List[str]] = None,
        is_guest: bool = False,
    ) -> dict:
        now = datetime.now(timezone.utc)
        doc = {
            "session_id": str(uuid.uuid4()),
            "user_id": user_id,          # None for guests
            "title": title,
            "book_ids": book_ids or [],  # books scoped to this session
            "messages": [],
            "is_guest": is_guest,
            "created_at": now,
            "updated_at": now,
        }
        if is_guest:
            from datetime import timedelta
            doc["expires_at"] = now + timedelta(hours=24)
        return doc

    @staticmethod
    def new_message(
        role: str,
        content: str,
        book_ids_referenced: Optional[List[str]] = None,
        sources: Optional[List[dict]] = None,
    ) -> dict:
        """Build a single message object to $push into messages array."""
        return {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "book_ids_referenced": book_ids_referenced or [],
            "sources": sources or [],   # [{book_title, page, chunk}]
            "timestamp": datetime.now(timezone.utc),
        }

    @staticmethod
    def to_public(session: dict) -> dict:
        messages = []
        for m in session.get("messages", []):
            messages.append({
                "id": m.get("id"),
                "role": m.get("role"),
                "content": m.get("content"),
                "sources": m.get("sources", []),
                "timestamp": m["timestamp"].isoformat()
                if isinstance(m.get("timestamp"), datetime)
                else "",
            })
        return {
            "session_id": session.get("session_id"),
            "title": session.get("title"),
            "book_ids": session.get("book_ids", []),
            "messages": messages,
            "created_at": session["created_at"].isoformat()
            if isinstance(session.get("created_at"), datetime)
            else "",
            "updated_at": session["updated_at"].isoformat()
            if isinstance(session.get("updated_at"), datetime)
            else "",
        }
