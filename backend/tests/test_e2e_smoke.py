"""E2E smoke tests for paper models."""

import pytest
import uuid
import hashlib

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


def test_smoke_e2e_full_flow(db_session):
    """Smoke test: full E2E flow.
    
    Creates:
    1. Paper
    2. PaperVersion (v1)
    3. PaperExternalId
    4. Claims (≥3)
    5. QualityScore (scope='version')
    6. ClaimLinks
    """
    # 1. Create Paper
    paper = Paper(
        id=uuid.uuid4(),
        aid="test-smoke-001",
        title="Test Paper for Smoke",
        visibility=PaperVisibility.PRIVATE,
        repo_url="https://github.com/test/repo",
    )
    db_session.add(paper)
    db_session.commit()
    db_session.refresh(paper)

    assert paper.id is not None
    assert paper.aid == "test-smoke-001"

    # 2. Create PaperVersion
    version = PaperVersion(
        id=uuid.uuid4(),
        aid=paper.aid,
        version=1,
        pdf_path="/papers/test-smoke-001/v1/file.pdf",
        meta_json={"pages": 10, "title": "Test Paper"},
    )
    db_session.add(version)
    db_session.commit()
    db_session.refresh(version)

    assert version.id is not None
    assert version.aid == paper.aid
    assert version.version == 1

    # 3. Create PaperExternalId
    ext_id = PaperExternalId(
        id=uuid.uuid4(),
        paper_id=paper.id,
        kind=ExternalIdKind.ARXIV,
        value="1234.5678",
    )
    db_session.add(ext_id)
    db_session.commit()
    db_session.refresh(ext_id)

    assert ext_id.paper_id == paper.id
    assert ext_id.kind == ExternalIdKind.ARXIV

    # 4. Create Claims (≥3)
    claims = []
    for i in range(3):
        text = f"Test claim {i+1}: This is a sample claim for testing."
        span_start = i * 100
        span_end = (i + 1) * 100
        content = f"{text}|{span_start}|{span_end}|{version.id}"
        claim_hash = hashlib.sha256(content.encode()).hexdigest()

        claim = Claim(
            id=uuid.uuid4(),
            paper_version_id=version.id,
            paper_id=paper.id,  # For join rápido
            text=text,
            span_start=span_start,
            span_end=span_end,
            section="intro" if i == 0 else "method",
            confidence=0.9,
            hash=claim_hash,
            text_hash=hashlib.sha256(b"document-base").hexdigest(),  # Hash do documento base
        )
        db_session.add(claim)
        claims.append(claim)

    db_session.commit()
    for claim in claims:
        db_session.refresh(claim)

    assert len(claims) == 3
    assert all(c.paper_version_id == version.id for c in claims)

    # 5. Create QualityScore (scope='version')
    score = QualityScore(
        id=uuid.uuid4(),
        paper_version_id=version.id,
        scope=QualityScoreScope.VERSION,
        score=75,
        signals={
            "has_readme_run_steps": True,
            "has_script_paper_mapping": True,
            "has_input_example": False,
            "has_cpu_synthetic_path": True,
            "has_seeds": True,
            "has_env_file": False,
            "readme_quality": 4,
            "reproducibility_signals_count": 4,
        },
        rationale={
            "summary": "Good reproducibility signals",
            "positive_factors": ["README with steps", "Script mapping", "Seeds"],
            "negative_factors": ["No input example", "No env file"],
            "recommendations": ["Add input example", "Add .env file"],
        },
        scoring_model_version="v0",
    )
    db_session.add(score)
    db_session.commit()
    db_session.refresh(score)

    assert score.paper_version_id == version.id
    assert score.scope == QualityScoreScope.VERSION
    assert score.paper_id is None  # Must be None for version scope

    # 6. Create ClaimLinks
    link = ClaimLink(
        id=uuid.uuid4(),
        claim_id=claims[0].id,
        source_doc_id="arxiv:9876.5432",
        source_citation="Smith et al. (2023)",
        relation=ClaimRelation.EQUIVALENT,
        confidence=0.85,
        context_excerpt="Similar finding in related work",
        reasoning_ref="/traces/claim-link-001.json",
    )
    db_session.add(link)
    db_session.commit()
    db_session.refresh(link)

    assert link.claim_id == claims[0].id
    assert link.relation == ClaimRelation.EQUIVALENT
    assert link.reasoning_ref is not None

    # Verify relationships
    db_session.refresh(paper)
    assert len(paper.versions) == 1
    assert len(paper.external_ids) == 1

    db_session.refresh(version)
    assert len(version.claims) == 3
    assert len(version.quality_scores) == 1

    db_session.refresh(claims[0])
    assert len(claims[0].claim_links) == 1

    print("✅ E2E smoke test passed: full flow completed")


def test_quality_score_scope_xor_in_db(db_session):
    """Test quality score scope XOR constraint in database."""
    paper = Paper(
        id=uuid.uuid4(),
        aid="test-xor-001",
        visibility=PaperVisibility.PRIVATE,
    )
    db_session.add(paper)
    db_session.commit()

    version = PaperVersion(
        id=uuid.uuid4(),
        aid=paper.aid,
        version=1,
        pdf_path="/papers/test-xor-001/v1/file.pdf",
    )
    db_session.add(version)
    db_session.commit()

    # Valid: scope='paper' with paper_id only
    score1 = QualityScore(
        id=uuid.uuid4(),
        paper_id=paper.id,
        scope=QualityScoreScope.PAPER,
        score=70,
        signals={},
        rationale={},
    )
    db_session.add(score1)
    db_session.commit()

    # Valid: scope='version' with paper_version_id only
    score2 = QualityScore(
        id=uuid.uuid4(),
        paper_version_id=version.id,
        scope=QualityScoreScope.VERSION,
        score=80,
        signals={},
        rationale={},
    )
    db_session.add(score2)
    db_session.commit()

    # Invalid: scope='paper' but both IDs set
    score3 = QualityScore(
        id=uuid.uuid4(),
        paper_id=paper.id,
        paper_version_id=version.id,  # Should be None
        scope=QualityScoreScope.PAPER,
        score=75,
        signals={},
        rationale={},
    )
    db_session.add(score3)

    with pytest.raises(Exception):  # CheckConstraint violation
        db_session.commit()

    db_session.rollback()

    # Invalid: scope='version' but both IDs set
    score4 = QualityScore(
        id=uuid.uuid4(),
        paper_id=paper.id,  # Should be None
        paper_version_id=version.id,
        scope=QualityScoreScope.VERSION,
        score=85,
        signals={},
        rationale={},
    )
    db_session.add(score4)

    with pytest.raises(Exception):  # CheckConstraint violation
        db_session.commit()

