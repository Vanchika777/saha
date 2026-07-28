"""
Recommendation service: fetches book recommendations using
Open Library / Gutenberg APIs based on user reading profile.
"""
import requests
from typing import List, Optional
from urllib.parse import quote_plus

from app.config import Config

TIMEOUT = 10


def get_recommendations(
    user_profile: dict,
    limit: int = 12,
) -> List[dict]:
    """
    Build recommendations from user reading profile.

    Strategies (in order of data richness):
      1. By most-read genre via Open Library subject search
      2. By favourite author via Open Library author works
      3. By Gutenberg (public domain — has free PDF links)

    Returns list of recommendation dicts.
    """
    genres = user_profile.get("genres", {})
    authors = user_profile.get("authors", {})
    languages = user_profile.get("languages", {})

    recommendations = []
    seen_titles = set()

    # ── Strategy 1: Top genre via Open Library ────────────────
    top_genre = _top_key(genres)
    if top_genre:
        books = _search_open_library_by_subject(top_genre, limit=limit // 2)
        for b in books:
            if b["title"] not in seen_titles:
                seen_titles.add(b["title"])
                recommendations.append(b)

    # ── Strategy 2: Top author via Open Library ───────────────
    top_author = _top_key(authors)
    if top_author and len(recommendations) < limit:
        books = _search_open_library_by_author(top_author, limit=4)
        for b in books:
            if b["title"] not in seen_titles:
                seen_titles.add(b["title"])
                recommendations.append(b)

    # ── Strategy 3: Gutenberg (free PDFs) ────────────────────
    if len(recommendations) < limit:
        needed = limit - len(recommendations)
        # Search Gutenberg by top genre or general popular books
        search_term = top_genre or "fiction"
        books = _search_gutenberg(search_term, limit=needed)
        for b in books:
            if b["title"] not in seen_titles:
                seen_titles.add(b["title"])
                recommendations.append(b)

    return recommendations[:limit]


def _top_key(d: dict) -> Optional[str]:
    """Return the key with highest count in a frequency dict."""
    if not d:
        return None
    return max(d, key=lambda k: d[k])


# ── Open Library ──────────────────────────────────────────────

def _search_open_library_by_subject(subject: str, limit: int = 6) -> List[dict]:
    """Search books by subject/genre on Open Library."""
    url = f"{Config.OPEN_LIBRARY_API}/subjects/{quote_plus(subject.lower())}.json"
    params = {"limit": limit}
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        works = r.json().get("works", [])
        return [_parse_ol_work(w) for w in works if w]
    except requests.RequestException:
        return []


def _search_open_library_by_author(author: str, limit: int = 4) -> List[dict]:
    """Search Open Library for books by a specific author."""
    search_url = f"{Config.OPEN_LIBRARY_API}/search.json"
    params = {
        "author": author,
        "limit": limit,
        "fields": "title,author_name,cover_i,isbn,key,first_publish_year",
    }
    try:
        r = requests.get(search_url, params=params, timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        docs = r.json().get("docs", [])
        return [_parse_ol_search_doc(d) for d in docs if d]
    except requests.RequestException:
        return []


def _parse_ol_work(work: dict) -> dict:
    cover_id = work.get("cover_id") or (work.get("cover_edition_key") and None)
    cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else None
    authors = work.get("authors", [])
    author_name = authors[0].get("name") if authors else None

    return {
        "title": work.get("title", "Unknown"),
        "author": author_name,
        "cover_url": cover_url,
        "open_library_key": work.get("key"),
        "download_url": None,
        "source": "open_library",
    }


def _parse_ol_search_doc(doc: dict) -> dict:
    cover_id = doc.get("cover_i")
    cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else None
    authors = doc.get("author_name", [])
    return {
        "title": doc.get("title", "Unknown"),
        "author": authors[0] if authors else None,
        "cover_url": cover_url,
        "open_library_key": doc.get("key"),
        "download_url": None,
        "source": "open_library",
    }


# ── Project Gutenberg ─────────────────────────────────────────

def _search_gutenberg(topic: str, limit: int = 6) -> List[dict]:
    """
    Search Project Gutenberg (via gutendex.com API).
    Returns books with free PDF/epub download links.
    """
    params = {"search": topic, "mime_type": "application/pdf", "languages": "en"}
    try:
        r = requests.get(Config.GUTENBERG_API + "/books", params=params, timeout=TIMEOUT)
        if r.status_code != 200:
            # Try without mime_type filter
            params.pop("mime_type", None)
            r = requests.get(Config.GUTENBERG_API + "/books", params=params, timeout=TIMEOUT)
            if r.status_code != 200:
                return []

        results = r.json().get("results", [])[:limit]
        return [_parse_gutenberg_book(b) for b in results]
    except requests.RequestException:
        return []


def _parse_gutenberg_book(book: dict) -> dict:
    # Get cover (Gutenberg calls it "image")
    formats = book.get("formats", {})
    cover_url = formats.get("image/jpeg")

    # Get PDF download link
    pdf_url = (
        formats.get("application/pdf")
        or formats.get("application/epub+zip")  # fallback to epub
    )

    authors = book.get("authors", [])
    author = authors[0].get("name") if authors else None
    # Gutenberg stores authors as "Last, First" — flip it
    if author and "," in author:
        parts = author.split(",", 1)
        author = f"{parts[1].strip()} {parts[0].strip()}"

    return {
        "title": book.get("title", "Unknown"),
        "author": author,
        "cover_url": cover_url,
        "download_url": pdf_url,
        "gutenberg_id": book.get("id"),
        "source": "gutenberg",
    }
