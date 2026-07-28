"""
PDF parser: extract metadata and cover image from uploaded PDFs.
Uses PyMuPDF (fitz) for robust parsing.
"""
import io
import re
from typing import Optional
from dataclasses import dataclass, field

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


@dataclass
class ParsedBook:
    title: str = "Unknown Title"
    author: Optional[str] = None
    language: Optional[str] = None
    genre: Optional[str] = None
    page_count: int = 0
    cover_bytes: Optional[bytes] = None   # raw image bytes if found
    cover_ext: str = "jpg"
    text_chunks: list = field(default_factory=list)  # list of str chunks


def parse_pdf(pdf_bytes: bytes, chunk_size: int = 1000, chunk_overlap: int = 150) -> ParsedBook:
    """
    Parse a PDF's bytes into a ParsedBook.

    Steps:
      1. Extract metadata (title, author, language) from PDF properties
      2. Extract cover image (first page rendered or first embedded image)
      3. Extract + chunk text for embeddings
    """
    result = ParsedBook()

    if PYMUPDF_AVAILABLE:
        result = _parse_with_pymupdf(pdf_bytes, chunk_size, chunk_overlap)
    elif PYPDF_AVAILABLE:
        result = _parse_with_pypdf(pdf_bytes, chunk_size, chunk_overlap)

    return result


def _parse_with_pymupdf(pdf_bytes: bytes, chunk_size: int, chunk_overlap: int) -> ParsedBook:
    result = ParsedBook()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    # ── Metadata ─────────────────────────────────────────────
    meta = doc.metadata or {}
    raw_title = meta.get("title", "").strip()
    raw_author = meta.get("author", "").strip()
    raw_lang = meta.get("language", "").strip()

    result.title = raw_title if raw_title else "Unknown Title"
    result.author = raw_author if raw_author else None
    result.language = _normalise_language(raw_lang)
    result.page_count = doc.page_count

    # ── Cover: try first embedded image, else render page 0 ──
    cover_bytes, cover_ext = _extract_cover_pymupdf(doc)
    result.cover_bytes = cover_bytes
    result.cover_ext = cover_ext

    # ── Text chunks ──────────────────────────────────────────
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"
    result.text_chunks = _chunk_text(full_text, chunk_size, chunk_overlap)

    doc.close()
    return result


def _extract_cover_pymupdf(doc) -> tuple[Optional[bytes], str]:
    """Try to get a cover image: first embedded image → rendered page 1."""
    # Try embedded images on page 0
    page0 = doc[0]
    images = page0.get_images(full=True)
    if images:
        xref = images[0][0]
        base_image = doc.extract_image(xref)
        if base_image:
            return base_image["image"], base_image.get("ext", "jpg")

    # Fallback: render page 0 as PNG
    mat = fitz.Matrix(1.5, 1.5)  # 1.5x scale for decent quality
    clip = fitz.Rect(0, 0, page0.rect.width, min(page0.rect.height, 600))
    pix = page0.get_pixmap(matrix=mat, clip=clip)
    return pix.tobytes("png"), "png"


def _parse_with_pypdf(pdf_bytes: bytes, chunk_size: int, chunk_overlap: int) -> ParsedBook:
    """Fallback parser using pypdf (less capable)."""
    result = ParsedBook()
    reader = PdfReader(io.BytesIO(pdf_bytes))

    meta = reader.metadata or {}
    result.title = (meta.get("/Title") or "Unknown Title").strip()
    result.author = (meta.get("/Author") or "").strip() or None
    result.page_count = len(reader.pages)

    full_text = ""
    for page in reader.pages:
        try:
            full_text += (page.extract_text() or "") + "\n"
        except Exception:
            pass

    result.text_chunks = _chunk_text(full_text, chunk_size, chunk_overlap)
    return result


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Split text into overlapping character-level chunks.
    Tries to break at sentence boundaries for better RAG quality.
    """
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # Try to break at last sentence end within the chunk
        if end < len(text):
            last_period = max(
                chunk.rfind(". "),
                chunk.rfind(".\n"),
                chunk.rfind("! "),
                chunk.rfind("? "),
            )
            if last_period > chunk_size // 2:
                end = start + last_period + 1
                chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap

    return chunks


def _normalise_language(lang: str) -> Optional[str]:
    """Map common language codes/names to readable form."""
    if not lang:
        return None
    lang = lang.lower().strip()
    mapping = {
        "en": "English", "eng": "English", "english": "English",
        "fr": "French", "fra": "French", "fre": "French",
        "de": "German", "deu": "German", "ger": "German",
        "es": "Spanish", "spa": "Spanish",
        "it": "Italian", "ita": "Italian",
        "pt": "Portuguese", "por": "Portuguese",
        "ar": "Arabic", "ara": "Arabic",
        "hi": "Hindi", "hin": "Hindi",
        "ur": "Urdu", "urd": "Urdu",
        "zh": "Chinese", "chi": "Chinese", "zho": "Chinese",
        "ja": "Japanese", "jpn": "Japanese",
        "ko": "Korean", "kor": "Korean",
        "ru": "Russian", "rus": "Russian",
    }
    return mapping.get(lang, lang.capitalize())
