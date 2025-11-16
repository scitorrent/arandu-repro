"""BM25 search index using Whoosh."""

import logging
from pathlib import Path


logger = logging.getLogger(__name__)

# Lazy loading of Whoosh
_index_dir: Path | None = None
_schema = None


def get_index_dir() -> Path:
    """
    Get or create BM25 index directory.

    Returns:
        Path to index directory
    """
    global _index_dir

    if _index_dir is None:
        from app.config import settings

        index_base = Path(settings.artifacts_base_path) / "rag" / "bm25_index"
        index_base.mkdir(parents=True, exist_ok=True)
        _index_dir = index_base

    return _index_dir


def create_index():
    """
    Create a new BM25 index.

    Returns:
        Whoosh index object
    """
    try:
        from whoosh import fields
        from whoosh.index import create_index

        index_dir = get_index_dir()

        # Define schema
        schema = fields.Schema(
            id=fields.ID(stored=True, unique=True),
            title=fields.TEXT(stored=True),
            authors=fields.TEXT(stored=True),
            abstract=fields.TEXT(stored=True),
            venue=fields.TEXT(stored=True),
            year=fields.NUMERIC(stored=True),
            doi=fields.ID(stored=True),
            url=fields.ID(stored=True),
            content=fields.TEXT,  # Searchable content (title + abstract)
        )

        # Create index
        index = create_index(index_dir, schema)
        logger.info(f"Created BM25 index at {index_dir}")
        return index
    except ImportError:
        logger.error("Whoosh not available, BM25 search will fail")
        raise


def get_index():
    """
    Get existing index or create new one.

    Returns:
        Whoosh index object
    """
    try:
        from whoosh.index import open_dir

        index_dir = get_index_dir()
        try:
            index = open_dir(index_dir)
            return index
        except Exception:
            # Index doesn't exist, create it
            return create_index()
    except ImportError:
        logger.error("Whoosh not available")
        raise


def add_document(
    index,
    doc_id: str,
    title: str,
    authors: list[str],
    abstract: str,
    venue: str | None = None,
    year: int | None = None,
    doi: str | None = None,
    url: str | None = None,
):
    """
    Add a document to the BM25 index.

    Args:
        index: Whoosh index
        doc_id: Unique document ID
        title: Paper title
        authors: List of authors
        abstract: Abstract text
        venue: Venue name
        year: Publication year
        doi: DOI
        url: URL
    """
    writer = index.writer()
    writer.add_document(
        id=doc_id,
        title=title,
        authors=", ".join(authors),
        abstract=abstract or "",
        venue=venue or "",
        year=year or 0,
        doi=doi or "",
        url=url or "",
        content=f"{title} {abstract or ''}",
    )
    writer.commit()


def search_bm25(
    index,
    query: str,
    top_k: int = 50,
) -> list[tuple[str, float]]:
    """
    Search using BM25.

    Args:
        index: Whoosh index
        query: Search query
        top_k: Number of results

    Returns:
        List of (doc_id, score) tuples, sorted by score descending
    """
    from whoosh.qparser import QueryParser

    with index.searcher() as searcher:
        parser = QueryParser("content", index.schema)
        query_obj = parser.parse(query)
        results = searcher.search(query_obj, limit=top_k)

        return [(hit["id"], hit.score) for hit in results]

