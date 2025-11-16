"""Tests for paper hosting APIs."""

import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.main import app
from app.models import Paper, PaperVersion, PaperVisibility


@pytest.fixture
def db_engine():
    """Create in-memory SQLite database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_engine):
    """Create database session."""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def client(db_session, monkeypatch):
    """Create test client with database session."""
    # Mock SessionLocal to return our test session
    monkeypatch.setattr("app.api.routes.papers.SessionLocal", lambda: db_session)
    
    return TestClient(app)


@pytest.fixture
def sample_pdf():
    """Create a minimal PDF file for testing."""
    # Minimal PDF content (valid PDF header)
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\nxref\n0 0\ntrailer\n<< /Size 0 /Root 1 0 R >>\nstartxref\n0\n%%EOF"
    return io.BytesIO(pdf_content)


@patch("app.api.routes.papers.validate_pdf_file")
@patch("app.api.routes.papers.ensure_paper_version_directory")
def test_create_paper_with_pdf(mock_ensure_dir, mock_validate, client, sample_pdf, db_session):
    """Test creating a paper with PDF upload."""
    # Mock PDF validation
    mock_validate.return_value = (True, None)
    
    # Mock directory creation
    mock_dir = MagicMock()
    mock_dir.parent = Path("/tmp/test")
    mock_ensure_dir.return_value = mock_dir
    
    # Mock file operations
    with patch("app.api.routes.papers.shutil.move") as mock_move:
        response = client.post(
            "/api/v1/papers",
            files={"pdf": ("test.pdf", sample_pdf, "application/pdf")},
            data={
                "title": "Test Paper",
                "visibility": "private",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "aid" in data
        assert data["version"] == 1
        assert "viewer_url" in data
        assert "paper_url" in data
        
        # Verify paper was created
        paper = db_session.query(Paper).filter(Paper.aid == data["aid"]).first()
        assert paper is not None
        assert paper.title == "Test Paper"
        
        # Verify version was created
        version = db_session.query(PaperVersion).filter(PaperVersion.aid == data["aid"]).first()
        assert version is not None
        assert version.version == 1


@patch("app.api.routes.papers.validate_pdf_file")
@patch("app.api.routes.papers.ensure_paper_version_directory")
def test_create_paper_version(mock_ensure_dir, mock_validate, client, sample_pdf, db_session):
    """Test creating a new version of an existing paper."""
    # Mock PDF validation
    mock_validate.return_value = (True, None)
    
    # Mock directory creation
    mock_dir = MagicMock()
    mock_dir.parent = Path("/tmp/test")
    mock_ensure_dir.return_value = mock_dir
    
    # Create paper first
    paper = Paper(
        aid="test-001",
        title="Test Paper",
        visibility=PaperVisibility.PRIVATE,
    )
    db_session.add(paper)
    
    version1 = PaperVersion(
        aid="test-001",
        version=1,
        pdf_path="papers/test-001/v1/file.pdf",
    )
    db_session.add(version1)
    db_session.commit()
    
    # Create version 2
    with patch("app.api.routes.papers.shutil.move"):
        response = client.post(
            "/api/v1/papers/test-001/versions",
            files={"pdf": ("test2.pdf", sample_pdf, "application/pdf")},
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["aid"] == "test-001"
        assert data["version"] == 2
        assert "viewer_url" in data


def test_get_paper_metadata(client, db_session):
    """Test getting paper metadata."""
    # Create paper
    paper = Paper(
        aid="test-002",
        title="Test Paper 2",
        visibility=PaperVisibility.PRIVATE,
    )
    db_session.add(paper)
    
    version = PaperVersion(
        aid="test-002",
        version=1,
        pdf_path="papers/test-002/v1/file.pdf",
    )
    db_session.add(version)
    db_session.commit()
    
    response = client.get("/api/v1/papers/test-002")
    
    assert response.status_code == 200
    data = response.json()
    assert data["aid"] == "test-002"
    assert data["title"] == "Test Paper 2"
    assert data["latest_version"] == 1
    assert "counts" in data
    assert data["counts"]["claims"] == 0
    assert data["counts"]["versions"] == 1


def test_get_paper_not_found(client):
    """Test getting non-existent paper."""
    response = client.get("/api/v1/papers/nonexistent")
    assert response.status_code == 404


def test_get_paper_claims_empty(client, db_session):
    """Test getting claims for a paper (initially empty)."""
    # Create paper
    paper = Paper(
        aid="test-003",
        title="Test Paper 3",
        visibility=PaperVisibility.PRIVATE,
    )
    db_session.add(paper)
    
    version = PaperVersion(
        aid="test-003",
        version=1,
        pdf_path="papers/test-003/v1/file.pdf",
    )
    db_session.add(version)
    db_session.commit()
    
    response = client.get("/api/v1/papers/test-003/claims")
    
    assert response.status_code == 200
    data = response.json()
    assert data["aid"] == "test-003"
    assert data["version"] == 1
    assert data["total"] == 0
    assert data["claims"] == []


def test_create_paper_missing_input(client):
    """Test creating paper without PDF or URL."""
    response = client.post("/api/v1/papers", data={})
    assert response.status_code == 400


def test_create_paper_both_pdf_and_url(client, sample_pdf):
    """Test creating paper with both PDF and URL (should fail)."""
    response = client.post(
        "/api/v1/papers",
        files={"pdf": ("test.pdf", sample_pdf, "application/pdf")},
        data={"url": "https://example.com/paper.pdf"},
    )
    assert response.status_code == 400

