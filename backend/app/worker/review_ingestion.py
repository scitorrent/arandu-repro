"""PDF/HTML ingestion and metadata extraction for reviews."""

import logging
import re
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)


class PaperMeta(BaseModel):
    """Paper metadata."""

    title: str | None = None
    authors: list[str] = []
    venue: str | None = None
    published_at: str | None = None  # ISO date string
    doi: str | None = None
    url: str | None = None
    pdf_path: str | None = None  # Path to PDF file if uploaded
    text: str = ""  # Full extracted text


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract text from PDF file.

    Uses PyMuPDF (fitz) as primary, falls back to pdfminer.six if needed.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text

    Raises:
        ValueError: If PDF cannot be read
    """
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(pdf_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        text = "\n".join(text_parts)
        logger.info(f"Extracted {len(text)} characters from PDF using PyMuPDF")
        return text
    except ImportError:
        logger.warning("PyMuPDF not available, trying pdfminer.six")
        # Fallback to pdfminer.six
        from pdfminer.high_level import extract_text

        text = extract_text(pdf_path)
        logger.info(f"Extracted {len(text)} characters from PDF using pdfminer")
        return text
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {e}") from e


def extract_text_from_url(url: str) -> str:
    """
    Extract text from URL (HTML page).

    Args:
        url: URL to fetch

    Returns:
        Extracted text (cleaned HTML)

    Raises:
        ValueError: If URL cannot be fetched or parsed
    """
    try:
        response = httpx.get(url, timeout=30, follow_redirects=True)
        response.raise_for_status()

        # Simple HTML text extraction (can be enhanced with BeautifulSoup)
        from html.parser import HTMLParser

        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text_parts = []
                self.skip_tags = {"script", "style", "nav", "footer", "header"}
                self.skip_tag_depth = 0

            def handle_data(self, data):
                if self.skip_tag_depth == 0 and data.strip():
                    self.text_parts.append(data.strip())

            def handle_starttag(self, tag, attrs):
                if tag in self.skip_tags:
                    self.skip_tag_depth += 1

            def handle_endtag(self, tag):
                if tag in self.skip_tags and self.skip_tag_depth > 0:
                    self.skip_tag_depth -= 1

        parser = TextExtractor()
        parser.feed(response.text)
        text = " ".join(parser.text_parts)
        logger.info(f"Extracted {len(text)} characters from URL")
        return text
    except Exception as e:
        raise ValueError(f"Failed to extract text from URL: {e}") from e


def clean_text(text: str) -> str:
    """
    Clean extracted text: remove repeated headers/footers, normalize whitespace.

    Args:
        text: Raw extracted text

    Returns:
        Cleaned text
    """
    lines = text.split("\n")
    cleaned_lines = []

    # Remove lines that appear in first 3 or last 3 lines (likely headers/footers)
    if len(lines) > 6:
        first_lines = set(lines[:3])
        last_lines = set(lines[-3:])
        repeated = first_lines & last_lines

        for line in lines:
            if line not in repeated:
                cleaned_lines.append(line)
    else:
        cleaned_lines = lines

    # Normalize whitespace
    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\s+", " ", cleaned)  # Multiple spaces to single
    cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)  # Multiple newlines to double

    return cleaned.strip()


def extract_metadata_from_text(text: str, doi: str | None = None) -> dict[str, Any]:
    """
    Extract metadata from paper text using heuristics.

    Args:
        text: Paper text
        doi: Optional DOI (if provided, can be used for API lookup)

    Returns:
        Dictionary with title, authors, venue, published_at
    """
    meta: dict[str, Any] = {
        "title": None,
        "authors": [],
        "venue": None,
        "published_at": None,
    }

    # Try to extract title (first line or line with "Title:" pattern)
    lines = text.split("\n")[:20]  # Check first 20 lines
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Look for title patterns
        if len(line) > 20 and len(line) < 200 and not line.startswith(("Abstract", "Introduction")):
            if not meta["title"]:
                meta["title"] = line
                break

    # Try to extract authors (lines with "Author" or comma-separated names)
    author_pattern = re.compile(r"(?:Authors?|By):\s*(.+)", re.IGNORECASE)
    for line in lines:
        match = author_pattern.search(line)
        if match:
            authors_str = match.group(1)
            # Split by comma or "and"
            authors = re.split(r",\s*|\s+and\s+", authors_str)
            meta["authors"] = [a.strip() for a in authors if a.strip()]
            break

    # Try to extract venue (look for conference/journal names)
    venue_patterns = [
        r"(?:Proceedings of |Conference on |Journal of )([A-Z][A-Za-z\s]+)",
        r"(?:arXiv|ICML|NeurIPS|ICLR|AAAI|IJCAI)",
    ]
    for pattern in venue_patterns:
        match = re.search(pattern, text[:5000])  # Check first 5000 chars
        if match:
            meta["venue"] = match.group(0) if match.groups() else match.group(0)
            break

    # Try to extract year (4-digit year in first 1000 chars)
    year_match = re.search(r"\b(19|20)\d{2}\b", text[:1000])
    if year_match:
        meta["published_at"] = year_match.group(0)

    return meta


async def fetch_metadata_from_crossref(doi: str) -> dict[str, Any]:
    """
    Fetch metadata from Crossref API.

    Args:
        doi: DOI string

    Returns:
        Dictionary with title, authors, venue, published_at

    Note: Falls back gracefully if API is unavailable.
    """
    if not settings.crossref_enabled:
        return {}

    try:
        url = f"https://api.crossref.org/works/{doi}"
        params = {"mailto": settings.crossref_mailto}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "message" in data:
                msg = data["message"]
                return {
                    "title": msg.get("title", [None])[0] if msg.get("title") else None,
                    "authors": [
                        f"{a.get('given', '')} {a.get('family', '')}".strip()
                        for a in msg.get("author", [])
                    ],
                    "venue": msg.get("container-title", [None])[0] if msg.get("container-title") else None,
                    "published_at": msg.get("published-print", {}).get("date-parts", [[None]])[0][0]
                    if msg.get("published-print")
                    else None,
                }
    except Exception as e:
        logger.warning(f"Failed to fetch metadata from Crossref: {e}")
        return {}

    return {}


def ingest_paper(
    url: str | None = None,
    doi: str | None = None,
    pdf_path: str | None = None,
) -> PaperMeta:
    """
    Ingest paper from URL, DOI, or PDF file.

    Args:
        url: Paper URL
        doi: DOI
        pdf_path: Path to PDF file

    Returns:
        PaperMeta with extracted text and metadata

    Raises:
        ValueError: If no valid input source or extraction fails
    """
    text = ""
    meta_dict: dict[str, Any] = {}

    # Extract text
    if pdf_path:
        text = extract_text_from_pdf(Path(pdf_path))
        meta_dict = extract_metadata_from_text(text, doi)
        meta_dict["pdf_path"] = pdf_path
    elif url:
        text = extract_text_from_url(url)
        meta_dict = extract_metadata_from_text(text, doi)
        meta_dict["url"] = url
    elif doi:
        # Try to fetch from DOI (can be enhanced with DOI resolver)
        logger.warning("DOI-only ingestion not fully implemented, need URL or PDF")
        raise ValueError("DOI-only ingestion requires URL or PDF file")
    else:
        raise ValueError("At least one of url, doi, or pdf_path must be provided")

    # Clean text
    text = clean_text(text)

    # Try to enhance metadata from Crossref if DOI available (sync version, no API call)
    # For async version, use ingest_paper_async
    # if doi and settings.crossref_enabled:
    #     crossref_meta = await fetch_metadata_from_crossref(doi)  # Requires async context

    return PaperMeta(
        title=meta_dict.get("title"),
        authors=meta_dict.get("authors", []),
        venue=meta_dict.get("venue"),
        published_at=str(meta_dict.get("published_at")) if meta_dict.get("published_at") else None,
        doi=doi,
        url=url,
        pdf_path=meta_dict.get("pdf_path"),
        text=text,
    )

