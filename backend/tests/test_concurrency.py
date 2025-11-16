"""Concurrency tests for paper models."""

import pytest
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.models import Paper, PaperVersion, Claim, PaperVisibility


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
    session_local = sessionmaker(bind=engine)  # noqa: N806
    session = session_local()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


def test_concurrent_aid_version_creation(db_session):
    """Test concurrent creation of same (aid, version)."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.db.base import Base

    # Create shared engine for all threads
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)  # noqa: N806

    # Create paper in shared database
    paper = Paper(
        id=uuid.uuid4(),
        aid="test-concurrent-001",
        visibility=PaperVisibility.PRIVATE,
    )
    session = SessionLocal()
    session.add(paper)
    session.commit()
    session.close()

    def create_version(version_num: int):
        """Create version in separate session using shared engine."""
        session = session_local()
        try:
            version = PaperVersion(
                id=uuid.uuid4(),
                aid=paper.aid,
                version=version_num,
                pdf_path=f"/papers/{paper.aid}/v{version_num}/file.pdf",
            )
            session.add(version)
            session.commit()
            return True, None
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    # Try to create same version concurrently
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(create_version, 1) for _ in range(5)]
        results = [f.result() for f in as_completed(futures)]

    # Only one should succeed
    successes = [r for r in results if r[0]]
    assert len(successes) == 1, f"Expected 1 success, got {len(successes)}"


def test_concurrent_claim_hash_creation(db_session):
    """Test concurrent creation of same claim.hash."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.db.base import Base

    # Create shared engine for all threads
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)  # noqa: N806

    # Create paper and version in shared database
    paper = Paper(
        id=uuid.uuid4(),
        aid="test-concurrent-002",
        visibility=PaperVisibility.PRIVATE,
    )
    version = PaperVersion(
        id=uuid.uuid4(),
        aid=paper.aid,
        version=1,
        pdf_path="/papers/test-concurrent-002/v1/file.pdf",
    )
    session = SessionLocal()
    session.add(paper)
    session.add(version)
    session.commit()
    session.close()

    import hashlib
    claim_hash = hashlib.sha256(b"duplicate-claim").hexdigest()

    def create_claim(claim_id: uuid.UUID):
        """Create claim with same hash using shared engine."""
        session = session_local()
        try:
            claim = Claim(
                id=claim_id,
                paper_version_id=version.id,
                text=f"Claim {claim_id}",
                hash=claim_hash,  # Same hash
            )
            session.add(claim)
            session.commit()
            return True, None
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    # Try to create claims with same hash concurrently
    claim_ids = [uuid.uuid4() for _ in range(5)]
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(create_claim, cid) for cid in claim_ids]
        results = [f.result() for f in as_completed(futures)]

    # Only one should succeed
    successes = [r for r in results if r[0]]
    assert len(successes) == 1, f"Expected 1 success, got {len(successes)}"

