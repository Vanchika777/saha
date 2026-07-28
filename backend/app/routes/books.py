"""
Books routes: upload, list, get, delete, status polling.
"""
from flask import Blueprint, request, jsonify, current_app, g
from bson import ObjectId
from datetime import datetime, timezone

from app.models.book import BookModel
from app.utils.auth_helpers import login_required, optional_auth
from app.utils import r2_storage
from app.utils.chroma_client import delete_collection
from app.services.book_service import create_book
from app.config import Config

books_bp = Blueprint("books", __name__)

ALLOWED_MIME = {"application/pdf"}


@books_bp.post("/upload")
@login_required
def upload_book():
    """
    Upload a PDF book.
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

    try:
        book = create_book(
            db=current_app.db,
            user_id=g.user_id,
            pdf_bytes=pdf_bytes,
            original_filename=file.filename,
        )
        return jsonify({"book": book}), 201
    except Exception as e:
        return jsonify({"error": "Upload failed", "detail": str(e)}), 500


@books_bp.get("/")
@login_required
def list_books():
    """List all books for the authenticated user."""
    db = current_app.db
    books_cursor = db.books.find(
        {"user_id": g.user_id},
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
@login_required
def get_book(book_id: str):
    """Get a single book by ID (must belong to authenticated user)."""
    db = current_app.db
    try:
        book = db.books.find_one({"_id": ObjectId(book_id), "user_id": g.user_id})
    except Exception:
        return jsonify({"error": "Invalid book ID"}), 400

    if not book:
        return jsonify({"error": "Book not found"}), 404

    file_url = r2_storage.get_presigned_url(book["file_key"]) if book.get("file_key") else ""
    return jsonify({"book": BookModel.to_public(book, file_url=file_url)})


@books_bp.get("/<book_id>/status")
@login_required
def book_status(book_id: str):
    """Poll embedding status for carousel spinner."""
    db = current_app.db
    try:
        book = db.books.find_one(
            {"_id": ObjectId(book_id), "user_id": g.user_id},
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
@login_required
def delete_book(book_id: str):
    """Delete a book: R2 files, ChromaDB collection, MongoDB document."""
    db = current_app.db
    try:
        book = db.books.find_one({"_id": ObjectId(book_id), "user_id": g.user_id})
    except Exception:
        return jsonify({"error": "Invalid book ID"}), 400

    if not book:
        return jsonify({"error": "Book not found"}), 404

    # Delete from R2
    if book.get("file_key"):
        r2_storage.delete_file(book["file_key"])
    if book.get("cover_key"):
        r2_storage.delete_file(book["cover_key"])

    # Delete ChromaDB collection
    delete_collection(g.user_id, book_id)

    # Delete MongoDB document
    db.books.delete_one({"_id": ObjectId(book_id)})

    return jsonify({"message": "Book deleted successfully"})
