"""
Books routes: upload, list, get, delete, status polling, serve file.
Supports both authenticated users and guest users.
"""
from flask import Blueprint, request, jsonify, current_app, g, send_file
from bson import ObjectId
import io
import os

from app.models.book import BookModel
from app.utils.auth_helpers import optional_auth
from app.utils import r2_storage
from app.utils.chroma_client import delete_collection
from app.services.book_service import create_book
from app.config import Config

books_bp = Blueprint("books", __name__)


def _get_effective_user_id() -> str:
    """Return authenticated user_id, or fallback to guest header/IP identifier."""
    if g.user_id:
        return g.user_id

    # For guest mode: pull from request header, cookie, or remote IP
    guest_header = request.headers.get("X-Guest-ID") or request.cookies.get("saha_guest_id")
    if guest_header:
        return f"guest_{guest_header}"
    return f"guest_{request.remote_addr or 'default'}"


@books_bp.post("/upload")
@optional_auth
def upload_book():
    """
    Upload a PDF book (Authenticated or Guest).
    Multipart form: field name = 'file'
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are accepted"}), 400

    pdf_bytes = file.read()
    if len(pdf_bytes) > Config.MAX_CONTENT_LENGTH:
        return jsonify({"error": f"File exceeds {Config.MAX_PDF_SIZE_MB}MB limit"}), 413

    if len(pdf_bytes) == 0:
        return jsonify({"error": "File is empty"}), 400

    effective_id = _get_effective_user_id()

    try:
        book = create_book(
            db=current_app.db,
            user_id=effective_id,
            pdf_bytes=pdf_bytes,
            original_filename=file.filename,
        )
        return jsonify({"book": book}), 201
    except Exception as e:
        print(f"[Upload Error]: {e}")
        return jsonify({"error": "Upload failed", "detail": str(e)}), 500


@books_bp.get("/")
@optional_auth
def list_books():
    """List books for authenticated or guest user."""
    db = current_app.db
    effective_id = _get_effective_user_id()

    books_cursor = db.books.find(
        {"user_id": effective_id},
        sort=[("created_at", -1)],
    )

    books = []
    for b in books_cursor:
        file_url = ""
        if b.get("file_key"):
            file_url = r2_storage.get_presigned_url(b["file_key"])
        books.append(BookModel.to_public(b, file_url=file_url))

    return jsonify({"books": books})


@books_bp.get("/<book_id>")
@optional_auth
def get_book(book_id: str):
    """Get a single book by ID."""
    db = current_app.db
    effective_id = _get_effective_user_id()
    try:
        book = db.books.find_one({"_id": ObjectId(book_id), "user_id": effective_id})
    except Exception:
        return jsonify({"error": "Invalid book ID"}), 400

    if not book:
        return jsonify({"error": "Book not found"}), 404

    file_url = r2_storage.get_presigned_url(book["file_key"]) if book.get("file_key") else ""
    return jsonify({"book": BookModel.to_public(book, file_url=file_url)})


@books_bp.get("/<book_id>/status")
@optional_auth
def book_status(book_id: str):
    """Poll embedding status for carousel spinner."""
    db = current_app.db
    effective_id = _get_effective_user_id()
    try:
        book = db.books.find_one(
            {"_id": ObjectId(book_id), "user_id": effective_id},
            {"embedding_status": 1, "embedding_chunk_count": 1},
        )
    except Exception:
        return jsonify({"error": "Invalid book ID"}), 400

    if not book:
        return jsonify({"error": "Book not found"}), 404

    return jsonify({
        "book_id": book_id,
        "embedding_status": book.get("embedding_status"),
        "chunk_count": book.get("embedding_chunk_count", 0),
    })


@books_bp.delete("/<book_id>")
@optional_auth
def delete_book(book_id: str):
    """Delete a book."""
    db = current_app.db
    effective_id = _get_effective_user_id()
    try:
        book = db.books.find_one({"_id": ObjectId(book_id), "user_id": effective_id})
    except Exception:
        return jsonify({"error": "Invalid book ID"}), 400

    if not book:
        return jsonify({"error": "Book not found"}), 404

    if book.get("file_key"):
        r2_storage.delete_file(book["file_key"])
    if book.get("cover_key"):
        r2_storage.delete_file(book["cover_key"])

    delete_collection(effective_id, book_id)
    db.books.delete_one({"_id": ObjectId(book_id)})

    return jsonify({"message": "Book deleted successfully"})


@books_bp.get("/file/<path:file_name>")
def serve_local_file(file_name: str):
    """Serve uploaded local file fallback."""
    local_path = os.path.join(r2_storage.LOCAL_UPLOAD_DIR, file_name)
    if os.path.exists(local_path):
        return send_file(local_path)
    return jsonify({"error": "File not found"}), 404
