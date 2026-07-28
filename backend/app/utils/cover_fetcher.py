"""
Cover image fetcher.

Priority chain:
  1. Embedded cover from PDF (passed in as bytes) — handled in pdf_parser
  2. Open Library Covers API (by ISBN or title+author)
  3. Google Books API (by title+author)
  4. Return None (frontend will show a generated gradient placeholder)
"""
import requests
from typing import Optional
from urllib.parse import quote_plus

from app.config import Config

TIMEOUT = 8  # seconds


def fetch_cover_url(
    title: str,
    author: Optional[str] = None,
    isbn: Optional[str] = None,
) -> Optional[str]:
    """
    Try to find a cover image URL for a book.
    Returns a direct image URL string or None.
    """
    # 1. Open Library by ISBN
    if isbn:
        url = _open_library_isbn(isbn)
        if url:
            return url

    # 2. Open Library by title search
    url = _open_library_search(title, author)
    if url:
        return url

    # 3. Google Books by title+author
    url = _google_books(title, author)
    if url:
        return url

    return None


# ── Open Library ──────────────────────────────────────────────

def _open_library_isbn(isbn: str) -> Optional[str]:
    """Direct cover lookup by ISBN via Open Library Covers API."""
    # Large cover
    url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg?default=false"
    try:
        r = requests.head(url, timeout=TIMEOUT)
        if r.status_code == 200:
            return url
    except requests.RequestException:
        pass
    return None


def _open_library_search(title: str, author: Optional[str]) -> Optional[str]:
    """Search Open Library for a book and get its cover URL."""
    query = quote_plus(title)
    if author:
        query += f"+{quote_plus(author)}"

    search_url = f"{Config.OPEN_LIBRARY_API}/search.json?q={query}&limit=1&fields=cover_i,isbn"
    try:
        r = requests.get(search_url, timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        data = r.json()
        docs = data.get("docs", [])
        if not docs:
            return None

        doc = docs[0]
        cover_id = doc.get("cover_i")
        if cover_id:
            return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"

        # Try via ISBN
        isbns = doc.get("isbn", [])
        if isbns:
            url = f"https://covers.openlibrary.org/b/isbn/{isbns[0]}-L.jpg?default=false"
            r2 = requests.head(url, timeout=TIMEOUT)
            if r2.status_code == 200:
                return url
    except requests.RequestException:
        pass
    return None


# ── Google Books ──────────────────────────────────────────────

def _google_books(title: str, author: Optional[str]) -> Optional[str]:
    """Search Google Books API and return thumbnail URL."""
    query = f"intitle:{quote_plus(title)}"
    if author:
        query += f"+inauthor:{quote_plus(author)}"

    params = {"q": query, "maxResults": 1, "fields": "items(volumeInfo/imageLinks)"}
    if Config.GOOGLE_BOOKS_API_KEY:
        params["key"] = Config.GOOGLE_BOOKS_API_KEY

    try:
        r = requests.get(Config.GOOGLE_BOOKS_API + "/volumes", params=params, timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        items = r.json().get("items", [])
        if not items:
            return None

        image_links = items[0].get("volumeInfo", {}).get("imageLinks", {})
        # Prefer large thumbnail, upgrade to higher res by tweaking URL
        thumb = image_links.get("thumbnail") or image_links.get("smallThumbnail")
        if thumb:
            # Google Books returns http; upgrade to https and request larger size
            thumb = thumb.replace("http://", "https://")
            thumb = thumb.replace("&zoom=1", "&zoom=0")
            return thumb
    except requests.RequestException:
        pass
    return None
