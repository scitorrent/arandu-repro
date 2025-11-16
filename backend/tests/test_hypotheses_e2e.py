"""Test cases to validate hypotheses for E2E test failures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.job import Job, JobStatus


class TestE2EHypotheses:
    """Test cases to validate E2E failure hypotheses."""

    def test_hypothesis_1_monkeypatch_works(self, monkeypatch):
        """
        Hypothesis 1: Monkeypatch is not working correctly.
        
        Test: Verify that monkeypatch actually affects SessionLocal import.
        """
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        session_local = sessionmaker(bind=engine)  # noqa: N806
        test_db = session_local()
        
        # Patch SessionLocal
        monkeypatch.setattr("app.db.session.SessionLocal", lambda: test_db)
        
        # Import after patching to see if it works
        from app.db.session import SessionLocal
        
        # Create a session using the patched SessionLocal
        patched_session = SessionLocal()
        
        # Verify it's the same object
        assert patched_session is test_db, "Monkeypatch did not work - different session objects"
        
        test_db.close()

    def test_hypothesis_2_import_caching(self, monkeypatch):
        """
        Hypothesis 2: Import caching prevents monkeypatch from working.
        
        Test: Check if importing SessionLocal before patching causes issues.
        """
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        session_local = sessionmaker(bind=engine)  # noqa: N806
        test_db = session_local()
        
        # Import SessionLocal BEFORE patching (simulating what happens)
        from app.db.session import SessionLocal as OriginalSessionLocal
        
        # Now patch
        monkeypatch.setattr("app.db.session.SessionLocal", lambda: test_db)
        
        # Import again after patching
        from app.db.session import SessionLocal as PatchedSessionLocal
        
        # Try to create a session
        patched_session = PatchedSessionLocal()
        
        # This should be the same as test_db if patching worked
        assert patched_session is test_db, "Import caching prevented monkeypatch"
        
        test_db.close()

    def test_hypothesis_3_job_visibility(self):
        """
        Hypothesis 3: Job is not visible in new session due to transaction isolation.
        
        Test: Create job in one session, verify it's visible in another session.
        """
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        session_local = sessionmaker(bind=engine)  # noqa: N806
        
        # Create job in first session
        session1 = session_local()
        job = Job(
            repo_url="file:///test",
            run_command="echo test",
            status=JobStatus.PENDING,
        )
        session1.add(job)
        session1.commit()
        session1.flush()
        job_id = str(job.id)
        session1.close()
        
        # Try to find job in new session
        session2 = session_local()
        found_job = session2.query(Job).filter(Job.id == job.id).first()
        
        assert found_job is not None, "Job not visible in new session"
        assert found_job.id == job.id, "Wrong job found"
        
        session2.close()

    def test_hypothesis_4_uuid_conversion(self):
        """
        Hypothesis 4: UUID conversion issue in process_job.
        
        Test: Verify UUID conversion works correctly.
        """
        from uuid import UUID
        
        job_id_str = "a2180c43-c93f-4c6e-9c0a-87728797ebe2"
        job_uuid = UUID(job_id_str)
        
        # Verify conversion
        assert str(job_uuid) == job_id_str, "UUID conversion failed"
        
        # Test the conversion logic from process_job
        job_id = job_id_str
        job_uuid_converted = UUID(job_id) if isinstance(job_id, str) else job_id
        assert job_uuid_converted == job_uuid, "Conversion logic mismatch"

