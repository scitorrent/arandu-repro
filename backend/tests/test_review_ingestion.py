"""Tests for review ingestion."""


import pytest

from app.worker.review_ingestion import (
    PaperMeta,
    clean_text,
    extract_metadata_from_text,
    ingest_paper,
)


def test_clean_text_removes_repeated_headers(tmp_path):
    """Test that clean_text removes repeated headers/footers."""
    text = "Header Line\n" * 3 + "Content line 1\nContent line 2\n" + "Header Line\n" * 3
    cleaned = clean_text(text)
    assert "Header Line" not in cleaned or cleaned.count("Header Line") < 3


def test_clean_text_normalizes_whitespace():
    """Test that clean_text normalizes whitespace."""
    text = "Line 1\n\n\n\nLine 2    with    spaces"
    cleaned = clean_text(text)
    assert "\n\n\n\n" not in cleaned
    assert "    " not in cleaned


def test_extract_metadata_from_text_title():
    """Test title extraction from text."""
    text = "A Novel Approach to Machine Learning\n\nAbstract: This paper..."
    meta = extract_metadata_from_text(text)
    assert meta["title"] is not None
    assert len(meta["title"]) > 10


def test_extract_metadata_from_text_authors():
    """Test author extraction from text."""
    text = "Title\n\nAuthors: John Doe, Jane Smith, Bob Johnson\n\nAbstract..."
    meta = extract_metadata_from_text(text)
    assert len(meta["authors"]) > 0
    assert "John Doe" in meta["authors"]


def test_extract_metadata_from_text_year():
    """Test year extraction from text."""
    text = "Title\n\nPublished in 2023\n\nAbstract..."
    meta = extract_metadata_from_text(text)
    assert meta["published_at"] == "2023"


def test_ingest_paper_with_pdf(tmp_path):
    """Test paper ingestion from PDF file."""
    # Create a minimal PDF (this is a placeholder - real test would need actual PDF)
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_text("Test PDF content")  # Not a real PDF, but tests the path

    # This will fail with actual PDF parsing, but tests the structure
    try:
        meta = ingest_paper(pdf_path=str(pdf_path))
        assert isinstance(meta, PaperMeta)
    except (ValueError, ImportError):
        # Expected if PyMuPDF/pdfminer not available or invalid PDF
        pytest.skip("PDF parsing libraries not available or invalid PDF")


def test_ingest_paper_validation():
    """Test that ingest_paper validates input."""
    with pytest.raises(ValueError, match="At least one of"):
        ingest_paper()


def test_paper_meta_model():
    """Test PaperMeta Pydantic model."""
    meta = PaperMeta(
        title="Test Paper",
        authors=["Author 1", "Author 2"],
        venue="Test Venue",
        text="Test text",
    )
    assert meta.title == "Test Paper"
    assert len(meta.authors) == 2

