"""Tests for conditional rules (scope, dedupe, uniqueness)."""

import pytest
import uuid
import hashlib
from datetime import UTC, datetime

from app.models import (
    Paper,
    PaperVersion,
    QualityScore,
    Claim,
    ClaimLink,
    PaperVisibility,
    QualityScoreScope,
    ClaimRelation,
)


@pytest.fixture
def db_session():
    """Create database session."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.db.base import Base
    
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def sample_paper(db_session):
    """Create sample paper."""
    paper = Paper(
        id=uuid.uuid4(),
        aid="test-001",
        visibility=PaperVisibility.PRIVATE,
    )
    db_session.add(paper)
    db_session.commit()
    return paper


@pytest.fixture
def sample_version(db_session, sample_paper):
    """Create sample paper version."""
    version = PaperVersion(
        id=uuid.uuid4(),
        aid=sample_paper.aid,
        version=1,
        pdf_path="/papers/test-001/v1/file.pdf",
    )
    db_session.add(version)
    db_session.commit()
    return version


def test_quality_score_scope_paper_rule(db_session, sample_paper):
    """Test quality score scope='paper' requires paper_id."""
    # Valid: scope='paper' with paper_id
    score = QualityScore(
        id=uuid.uuid4(),
        paper_id=sample_paper.id,
        scope=QualityScoreScope.PAPER,
        score=75,
        signals={},
        rationale={},
    )
    db_session.add(score)
    db_session.commit()
    assert score.paper_id == sample_paper.id
    assert score.paper_version_id is None
    
    # Invalid: scope='paper' without paper_id
    score2 = QualityScore(
        id=uuid.uuid4(),
        scope=QualityScoreScope.PAPER,
        score=80,
        signals={},
        rationale={},
    )
    db_session.add(score2)
    with pytest.raises(Exception):  # CheckConstraint violation
        db_session.commit()


def test_quality_score_scope_version_rule(db_session, sample_version):
    """Test quality score scope='version' requires paper_version_id."""
    # Valid: scope='version' with paper_version_id
    score = QualityScore(
        id=uuid.uuid4(),
        paper_version_id=sample_version.id,
        scope=QualityScoreScope.VERSION,
        score=80,
        signals={},
        rationale={},
    )
    db_session.add(score)
    db_session.commit()
    assert score.paper_version_id == sample_version.id
    assert score.paper_id is None
    
    # Invalid: scope='version' without paper_version_id
    score2 = QualityScore(
        id=uuid.uuid4(),
        scope=QualityScoreScope.VERSION,
        score=85,
        signals={},
        rationale={},
    )
    db_session.add(score2)
    with pytest.raises(Exception):  # CheckConstraint violation
        db_session.commit()


def test_claim_hash_dedupe(db_session, sample_version):
    """Test claim hash deduplication."""
    hash_value = hashlib.sha256(b"test-claim|0|10|test-version").hexdigest()
    
    claim1 = Claim(
        id=uuid.uuid4(),
        paper_version_id=sample_version.id,
        text="Test claim",
        hash=hash_value,
    )
    db_session.add(claim1)
    db_session.commit()
    
    # Try to create duplicate hash
    claim2 = Claim(
        id=uuid.uuid4(),
        paper_version_id=sample_version.id,
        text="Another claim",
        hash=hash_value,  # Same hash
    )
    db_session.add(claim2)
    
    with pytest.raises(Exception):  # UniqueConstraint violation
        db_session.commit()


def test_unique_aid_version(db_session, sample_paper):
    """Test unique constraint on (aid, version)."""
    version1 = PaperVersion(
        id=uuid.uuid4(),
        aid=sample_paper.aid,
        version=1,
        pdf_path="/papers/test-001/v1/file.pdf",
    )
    db_session.add(version1)
    db_session.commit()
    
    # Try duplicate (aid, version)
    version2 = PaperVersion(
        id=uuid.uuid4(),
        aid=sample_paper.aid,
        version=1,  # Same version
        pdf_path="/papers/test-001/v1/file2.pdf",
    )
    db_session.add(version2)
    
    with pytest.raises(Exception):  # UniqueConstraint violation
        db_session.commit()


def test_unique_paper_external_id_kind(db_session, sample_paper):
    """Test unique constraint on (paper_id, kind)."""
    ext_id1 = PaperExternalId(
        id=uuid.uuid4(),
        paper_id=sample_paper.id,
        kind="arxiv",
        value="1234.5678",
    )
    db_session.add(ext_id1)
    db_session.commit()
    
    # Try duplicate (paper_id, kind)
    ext_id2 = PaperExternalId(
        id=uuid.uuid4(),
        paper_id=sample_paper.id,
        kind="arxiv",  # Same kind
        value="9876.5432",
    )
    db_session.add(ext_id2)
    
    with pytest.raises(Exception):  # UniqueConstraint violation
        db_session.commit()


def test_claim_link_source_validation(db_session, sample_version):
    """Test claim link source validation."""
    claim = Claim(
        id=uuid.uuid4(),
        paper_version_id=sample_version.id,
        text="Test claim",
        hash="claim-hash-001",
    )
    db_session.add(claim)
    db_session.commit()
    
    # Valid: with source_paper_id
    link1 = ClaimLink(
        id=uuid.uuid4(),
        claim_id=claim.id,
        source_doc_id="arxiv:1234.5678",
        relation=ClaimRelation.EQUIVALENT,
        confidence=0.9,
    )
    db_session.add(link1)
    db_session.commit()
    
    # Invalid: no source
    link2 = ClaimLink(
        id=uuid.uuid4(),
        claim_id=claim.id,
        relation=ClaimRelation.COMPLEMENTARY,
        confidence=0.8,
        # Missing source_paper_id and source_doc_id
    )
    db_session.add(link2)
    
    with pytest.raises(Exception):  # CheckConstraint violation
        db_session.commit()

