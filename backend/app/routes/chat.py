"""
Chat routes: create session, send message (streaming via SSE),
fetch history. Supports both authenticated users and guests.
"""
import json
import uuid
from flask import Blueprint, request, jsonify, current_app, g, Response, stream_with_context
from bson import ObjectId
from datetime import datetime, timezone

from app.models.chat import ChatSessionModel, MessageRole
from app.utils.auth_helpers import login_required, optional_auth
from app.services.rag_service import stream_answer, answer_question

chat_bp = Blueprint("chat", __name__)


def _sanitize_doc(doc: dict) -> dict:
    """Ensure BSON types like ObjectId and datetime are converted to JSON-serializable types."""
    if not doc:
        return {}
    
    clean_doc = dict(doc)
    
    if "_id" in clean_doc:
        clean_doc["_id"] = str(clean_doc["_id"])
        
    for key in ["created_at", "updated_at", "expires_at"]:
        if key in clean_doc and isinstance(clean_doc[key], datetime):
            clean_doc[key] = clean_doc[key].isoformat()

    return clean_doc


@chat_bp.post("/sessions")
@optional_auth
def create_session():
    """
    Create a new chat session.
    Guests get a session with a 24-hour TTL.
    """
    try:
        data = request.get_json(silent=True) or {}
        book_ids = data.get("book_ids", [])
        title = data.get("title", "New Conversation")

        user_id = str(g.user_id) if getattr(g, "user_id", None) else None
        is_guest = user_id is None

        session_doc = ChatSessionModel.new(
            user_id=user_id,
            title=title,
            book_ids=book_ids,
            is_guest=is_guest,
        )

        if not session_doc.get("session_id"):
            session_doc["session_id"] = str(uuid.uuid4())

        current_app.db.chat_sessions.insert_one(session_doc)

        clean_session = _sanitize_doc(session_doc)
        
        if hasattr(ChatSessionModel, "to_public"):
            public_data = ChatSessionModel.to_public(clean_session)
        else:
            public_data = clean_session

        return jsonify({"session": _sanitize_doc(public_data)}), 201

    except Exception as e:
        current_app.logger.error(f"Error creating chat session: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Could not start chat session",
            "details": str(e)
        }), 500


@chat_bp.post("/sessions/<session_id>/message")
@optional_auth
def send_message(session_id: str):
    """
    Send a message and stream back response via SSE.
    """
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    book_ids = data.get("book_ids")
    use_stream = data.get("stream", True)

    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    db = current_app.db
    user_id = str(g.user_id) if getattr(g, "user_id", None) else None

    query = {"session_id": session_id}
    if user_id:
        query["user_id"] = user_id

    session = db.chat_sessions.find_one(query)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    # Default to session book_ids if omitted
    if book_ids is None:
        book_ids = session.get("book_ids", [])

    effective_user_id = user_id or str(session.get("user_id") or "guest")

    # Save user message to database
    user_msg = ChatSessionModel.new_message(
        role=MessageRole.USER,
        content=user_message,
    )
    db.chat_sessions.update_one(
        {"session_id": session_id},
        {
            "$push": {"messages": user_msg},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        },
    )

    history = session.get("messages", [])[-12:]

    if use_stream:
        def generate():
            full_response = ""
            sources = []

            yield f"data: {json.dumps({'type': 'start'})}\n\n"

            try:
                for token in stream_answer(
                    user_id=effective_user_id,
                    book_ids=book_ids,
                    question=user_message,
                    chat_history=history,
                ):
                    full_response += token
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            except Exception as e:
                current_app.logger.error(f"Streaming error: {e}", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                return

            assistant_msg = ChatSessionModel.new_message(
                role=MessageRole.ASSISTANT,
                content=full_response,
                sources=sources,
            )
            db.chat_sessions.update_one(
                {"session_id": session_id},
                {
                    "$push": {"messages": assistant_msg},
                    "$set": {"updated_at": datetime.now(timezone.utc)},
                },
            )

            yield f"data: {json.dumps({'type': 'done', 'full_response': full_response})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        result = answer_question(
            user_id=effective_user_id,
            book_ids=book_ids,
            question=user_message,
            chat_history=history,
        )
        answer = result["answer"]
        sources = result.get("sources", [])

        assistant_msg = ChatSessionModel.new_message(
            role=MessageRole.ASSISTANT,
            content=answer,
            sources=sources,
        )
        db.chat_sessions.update_one(
            {"session_id": session_id},
            {
                "$push": {"messages": assistant_msg},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )
        return jsonify({"answer": answer, "sources": sources})


@chat_bp.get("/sessions")
@login_required
def list_sessions():
    """List all chat sessions for authenticated user."""
    db = current_app.db
    user_id = str(g.user_id) if getattr(g, "user_id", None) else None

    sessions = db.chat_sessions.find(
        {"user_id": user_id},
        {"messages": {"$slice": -1}},
        sort=[("updated_at", -1)],
    )
    
    clean_sessions = []
    for s in sessions:
        s = _sanitize_doc(s)
        if hasattr(ChatSessionModel, "to_public"):
            s = ChatSessionModel.to_public(s)
        clean_sessions.append(_sanitize_doc(s))

    return jsonify({"sessions": clean_sessions})


@chat_bp.get("/sessions/<session_id>")
@optional_auth
def get_session(session_id: str):
    """Get full session with all messages."""
    db = current_app.db
    user_id = str(g.user_id) if getattr(g, "user_id", None) else None

    query = {"session_id": session_id}
    if user_id:
        query["user_id"] = user_id

    session = db.chat_sessions.find_one(query)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    clean_session = _sanitize_doc(session)
    if hasattr(ChatSessionModel, "to_public"):
        clean_session = ChatSessionModel.to_public(clean_session)

    return jsonify({"session": _sanitize_doc(clean_session)})


@chat_bp.delete("/sessions/<session_id>")
@login_required
def delete_session(session_id: str):
    """Delete a chat session."""
    db = current_app.db
    user_id = str(g.user_id) if getattr(g, "user_id", None) else None

    result = db.chat_sessions.delete_one(
        {"session_id": session_id, "user_id": user_id}
    )
    if result.deleted_count == 0:
        return jsonify({"error": "Session not found"}), 404
    return jsonify({"message": "Session deleted"})