"""Tests for paper models."""

import pytest
import uuid
from datetime import UTC, datetime

from app.models import (
    Paper,
    PaperVersion,
    PaperExternalId,
    QualityScore,
    Claim,
    ClaimLink,
    PaperVisibility,
    ExternalIdKind,
    QualityScoreScope,
    ClaimRelation,
)

# Import fixtures
pytest_plugins = ["tests.conftest_papers"]


@pytest.fixture
def sample_paper(db_session):
    """Create a sample paper."""
    paper = Paper(
        id=uuid.uuid4(),
        aid="test-paper-001",
        title="Test Paper",
        visibility=PaperVisibility.PRIVATE,
    )
    db_session.add(paper)
    db_session.commit()
    db_session.refresh(paper)
    return paper


@pytest.fixture
def sample_paper_version(db_session, sample_paper):
    """Create a sample paper version."""
    version = PaperVersion(
        id=uuid.uuid4(),
        aid=sample_paper.aid,
        version=1,
        pdf_path="/papers/test-paper-001/v1/file.pdf",
    )
    db_session.add(version)
    db_session.commit()
    db_session.refresh(version)
    return version


def test_create_paper(db_session):
    """Test creating a paper."""
    paper = Paper(
        id=uuid.uuid4(),
        aid="test-001",
        title="Test",
        visibility=PaperVisibility.PRIVATE,
    )
    db_session.add(paper)
    db_session.commit()
    
    assert paper.id is not None
    assert paper.aid == "test-001"
    assert paper.visibility == PaperVisibility.PRIVATE
    assert paper.deleted_at is None


def test_paper_visibility_enum(db_session):
    """Test paper visibility enum."""
    paper = Paper(
        id=uuid.uuid4(),
        aid="test-002",
        visibility=PaperVisibility.UNLISTED,
    )
    db_session.add(paper)
    db_session.commit()
    
    assert paper.visibility == PaperVisibility.UNLISTED


def test_paper_soft_delete(db_session, sample_paper):
    """Test paper soft delete."""
    sample_paper.deleted_at = datetime.now(UTC)
    db_session.commit()
    
    assert sample_paper.deleted_at is not None


def test_paper_with_versions(db_session, sample_paper):
    """Test paper with versions."""
    version1 = PaperVersion(
        id=uuid.uuid4(),
        aid=sample_paper.aid,
        version=1,
        pdf_path="/papers/test-paper-001/v1/file.pdf",
    )
    version2 = PaperVersion(
        id=uuid.uuid4(),
        aid=sample_paper.aid,
        version=2,
        pdf_path="/papers/test-paper-001/v2/file.pdf",
    )
    db_session.add_all([version1, version2])
    db_session.commit()
    
    assert len(sample_paper.versions) == 2
    assert version1.version == 1
    assert version2.version == 2


def test_paper_with_external_ids(db_session, sample_paper):
    """Test paper with external IDs."""
    ext_id1 = PaperExternalId(
        id=uuid.uuid4(),
        paper_id=sample_paper.id,
        kind=ExternalIdKind.ARXIV,
        value="1234.5678",
    )
    ext_id2 = PaperExternalId(
        id=uuid.uuid4(),
        paper_id=sample_paper.id,
        kind=ExternalIdKind.DOI,
        value="10.1234/example",
    )
    db_session.add_all([ext_id1, ext_id2])
    db_session.commit()
    
    assert len(sample_paper.external_ids) == 2


def test_unique_aid_version(db_session, sample_paper):
    """Test unique constraint on (aid, version)."""
    version1 = PaperVersion(
        id=uuid.uuid4(),
        aid=sample_paper.aid,
        version=1,
        pdf_path="/papers/test-paper-001/v1/file.pdf",
    )
    db_session.add(version1)
    db_session.commit()
    
    # Try to create duplicate
    version2 = PaperVersion(
        id=uuid.uuid4(),
        aid=sample_paper.aid,
        version=1,  # Same version
        pdf_path="/papers/test-paper-001/v1/file2.pdf",
    )
    db_session.add(version2)
    
    with pytest.raises(Exception):  # IntegrityError or similar
        db_session.commit()


def test_version_positive_check(db_session, sample_paper):
    """Test version must be >= 1."""
    version = PaperVersion(
        id=uuid.uuid4(),
        aid=sample_paper.aid,
        version=0,  # Invalid
        pdf_path="/papers/test-paper-001/v0/file.pdf",
    )
    db_session.add(version)
    
    with pytest.raises(Exception):  # CheckConstraint violation
        db_session.commit()


def test_quality_score_paper_scope(db_session, sample_paper):
    """Test quality score with paper scope."""
    score = QualityScore(
        id=uuid.uuid4(),
        paper_id=sample_paper.id,
        scope=QualityScoreScope.PAPER,
        score=75,
        signals={"has_readme_run_steps": True},
        rationale={"summary": "Good"},
    )
    db_session.add(score)
    db_session.commit()
    
    assert score.paper_id == sample_paper.id
    assert score.paper_version_id is None
    assert score.scope == QualityScoreScope.PAPER


def test_quality_score_version_scope(db_session, sample_paper, sample_paper_version):
    """Test quality score with version scope."""
    score = QualityScore(
        id=uuid.uuid4(),
        paper_version_id=sample_paper_version.id,
        scope=QualityScoreScope.VERSION,
        score=80,
        signals={"has_readme_run_steps": True},
        rationale={"summary": "Very good"},
    )
    db_session.add(score)
    db_session.commit()
    
    assert score.paper_version_id == sample_paper_version.id
    assert score.paper_id is None
    assert score.scope == QualityScoreScope.VERSION


def test_quality_score_scope_validation(db_session, sample_paper):
    """Test quality score scope validation."""
    # Invalid: paper scope but no paper_id
    score = QualityScore(
        id=uuid.uuid4(),
        scope=QualityScoreScope.PAPER,
        score=75,
        signals={},
        rationale={},
    )
    db_session.add(score)
    
    with pytest.raises(Exception):  # CheckConstraint violation
        db_session.commit()


def test_create_claim(db_session, sample_paper_version):
    """Test creating a claim."""
    claim = Claim(
        id=uuid.uuid4(),
        paper_version_id=sample_paper_version.id,
        text="This is a test claim",
        section="intro",
        hash="test-hash-001",
    )
    db_session.add(claim)
    db_session.commit()
    
    assert claim.paper_version_id == sample_paper_version.id
    assert claim.text == "This is a test claim"


def test_claim_span_consistency(db_session, sample_paper_version):
    """Test claim span consistency."""
    # Valid: both set
    claim1 = Claim(
        id=uuid.uuid4(),
        paper_version_id=sample_paper_version.id,
        text="Claim 1",
        span_start=0,
        span_end=10,
        hash="hash1",
    )
    db_session.add(claim1)
    db_session.commit()
    
    # Invalid: only one set
    claim2 = Claim(
        id=uuid.uuid4(),
        paper_version_id=sample_paper_version.id,
        text="Claim 2",
        span_start=0,
        span_end=None,  # Missing
        hash="hash2",
    )
    db_session.add(claim2)
    
    with pytest.raises(Exception):  # CheckConstraint violation
        db_session.commit()


def test_claim_hash_dedupe(db_session, sample_paper_version):
    """Test claim hash deduplication."""
    claim1 = Claim(
        id=uuid.uuid4(),
        paper_version_id=sample_paper_version.id,
        text="Duplicate claim",
        hash="duplicate-hash",
    )
    db_session.add(claim1)
    db_session.commit()
    
    # Try to create duplicate hash
    claim2 = Claim(
        id=uuid.uuid4(),
        paper_version_id=sample_paper_version.id,
        text="Another claim",
        hash="duplicate-hash",  # Same hash
    )
    db_session.add(claim2)
    
    with pytest.raises(Exception):  # UniqueConstraint violation
        db_session.commit()


def test_create_claim_link(db_session, sample_paper_version, sample_paper):
    """Test creating a claim link."""
    claim = Claim(
        id=uuid.uuid4(),
        paper_version_id=sample_paper_version.id,
        text="Test claim",
        hash="claim-hash-001",
    )
    db_session.add(claim)
    db_session.commit()
    
    link = ClaimLink(
        id=uuid.uuid4(),
        claim_id=claim.id,
        source_paper_id=sample_paper.id,
        relation=ClaimRelation.EQUIVALENT,
        confidence=0.9,
    )
    db_session.add(link)
    db_session.commit()
    
    assert link.claim_id == claim.id
    assert link.relation == ClaimRelation.EQUIVALENT


def test_claim_link_source_validation(db_session, sample_paper_version):
    """Test claim link source validation."""
    claim = Claim(
        id=uuid.uuid4(),
        paper_version_id=sample_paper_version.id,
        text="Test claim",
        hash="claim-hash-002",
    )
    db_session.add(claim)
    db_session.commit()
    
    # Invalid: no source
    link = ClaimLink(
        id=uuid.uuid4(),
        claim_id=claim.id,
        relation=ClaimRelation.EQUIVALENT,
        confidence=0.9,
        # Missing source_paper_id and source_doc_id
    )
    db_session.add(link)
    
    with pytest.raises(Exception):  # CheckConstraint violation
        db_session.commit()


def test_claim_link_relation_enum(db_session, sample_paper_version):
    """Test claim link relation enum."""
    claim = Claim(
        id=uuid.uuid4(),
        paper_version_id=sample_paper_version.id,
        text="Test claim",
        hash="claim-hash-003",
    )
    db_session.add(claim)
    db_session.commit()
    
    link = ClaimLink(
        id=uuid.uuid4(),
        claim_id=claim.id,
        source_doc_id="arxiv:1234.5678",
        relation=ClaimRelation.CONTRADICTORY,
        confidence=0.8,
    )
    db_session.add(link)
    db_session.commit()
    
    assert link.relation == ClaimRelation.CONTRADICTORY


def test_cascade_delete_paper(db_session, sample_paper):
    """Test cascade delete of paper."""
    version = PaperVersion(
        id=uuid.uuid4(),
        aid=sample_paper.aid,
        version=1,
        pdf_path="/papers/test-paper-001/v1/file.pdf",
    )
    ext_id = PaperExternalId(
        id=uuid.uuid4(),
        paper_id=sample_paper.id,
        kind=ExternalIdKind.ARXIV,
        value="1234.5678",
    )
    db_session.add_all([version, ext_id])
    db_session.commit()
    
    # Delete paper
    db_session.delete(sample_paper)
    db_session.commit()
    
    # Versions and external_ids should be deleted
    assert db_session.query(PaperVersion).filter_by(aid=sample_paper.aid).first() is None
    assert db_session.query(PaperExternalId).filter_by(paper_id=sample_paper.id).first() is None

