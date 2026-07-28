"""
Chat routes: create session, send message (streaming via SSE),
fetch history. Supports both authenticated users and guests.
"""
import json
from flask import Blueprint, request, jsonify, current_app, g, Response, stream_with_context
from bson import ObjectId
from datetime import datetime, timezone

from app.models.chat import ChatSessionModel, MessageRole
from app.utils.auth_helpers import login_required, optional_auth
from app.services.rag_service import stream_answer, answer_question

chat_bp = Blueprint("chat", __name__)


@chat_bp.post("/sessions")
@optional_auth
def create_session():
    """
    Create a new chat session.
    Guests get a session with a 24-hour TTL.
    Body: { title?: str, book_ids?: [str] }
    """
    data = request.get_json(silent=True) or {}
    book_ids = data.get("book_ids", [])
    title = data.get("title", "New Conversation")

    is_guest = g.user_id is None
    session_doc = ChatSessionModel.new(
        user_id=g.user_id,
        title=title,
        book_ids=book_ids,
        is_guest=is_guest,
    )
    result = current_app.db.chat_sessions.insert_one(session_doc)
    session_doc["_id"] = result.inserted_id

    return jsonify({"session": ChatSessionModel.to_public(session_doc)}), 201


@chat_bp.post("/sessions/<session_id>/message")
@optional_auth
def send_message(session_id: str):
    """
    Send a message and get a streaming SSE response.

    Body: { message: str, book_ids?: [str], stream?: bool }
    Returns: Server-Sent Events stream or JSON response.
    """
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    book_ids = data.get("book_ids")
    use_stream = data.get("stream", True)

    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    db = current_app.db

    # Find session (guests can access by session_id without user_id check)
    query = {"session_id": session_id}
    if g.user_id:
        query["user_id"] = g.user_id

    session = db.chat_sessions.find_one(query)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    # Use session's book_ids if not overridden in request
    if book_ids is None:
        book_ids = session.get("book_ids", [])

    # Use authenticated user_id, or fall back to session's user_id (guest)
    effective_user_id = g.user_id or str(session.get("user_id") or "guest")

    # Save user message to DB
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

    # Fetch recent history for context
    history = session.get("messages", [])[-12:]  # last 6 turns

    if use_stream and book_ids:
        # ── Streaming SSE response ─────────────────────────────
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
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                return

            # Save assistant message
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
        # ── Non-streaming fallback (or no book context) ────────
        if book_ids:
            result = answer_question(
                user_id=effective_user_id,
                book_ids=book_ids,
                question=user_message,
                chat_history=history,
            )
            answer = result["answer"]
            sources = result["sources"]
        else:
            # General chat without book context — still use Groq
            from app.services.rag_service import _build_llm
            from langchain.prompts import ChatPromptTemplate
            llm = _build_llm()
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are Saha, an enthusiastic AI book companion. Help the user explore literature."),
                ("human", "{question}"),
            ])
            response = (prompt | llm).invoke({"question": user_message})
            answer = response.content
            sources = []

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
    sessions = db.chat_sessions.find(
        {"user_id": g.user_id},
        {"messages": {"$slice": -1}},  # only last message for preview
        sort=[("updated_at", -1)],
    )
    return jsonify({
        "sessions": [ChatSessionModel.to_public(s) for s in sessions]
    })


@chat_bp.get("/sessions/<session_id>")
@optional_auth
def get_session(session_id: str):
    """Get full session with all messages."""
    db = current_app.db
    query = {"session_id": session_id}
    if g.user_id:
        query["user_id"] = g.user_id

    session = db.chat_sessions.find_one(query)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    return jsonify({"session": ChatSessionModel.to_public(session)})


@chat_bp.delete("/sessions/<session_id>")
@login_required
def delete_session(session_id: str):
    """Delete a chat session."""
    db = current_app.db
    result = db.chat_sessions.delete_one(
        {"session_id": session_id, "user_id": g.user_id}
    )
    if result.deleted_count == 0:
        return jsonify({"error": "Session not found"}), 404
    return jsonify({"message": "Session deleted"})
