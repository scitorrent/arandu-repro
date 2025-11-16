"""Test to reproduce the actual E2E import caching issue."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.job import Job, JobStatus


def test_import_caching_issue(monkeypatch):
    """
    Reproduce the actual issue: process_job imports SessionLocal at module level.
    
    When we monkeypatch app.db.session.SessionLocal AFTER the module is imported,
    the cached reference in app.worker.main doesn't change.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)  # noqa: N806
    test_db = session_local()
    
    # Simulate: Import process_job (which imports SessionLocal at module level)
    # This is what happens when pytest imports the test file
    import app.worker.main
    
    # Now patch (this is what the test fixture does)
    monkeypatch.setattr("app.db.session.SessionLocal", lambda: test_db)
    
    # Check what SessionLocal refers to in the worker module
    worker_session_local = app.worker.main.SessionLocal
    
    # Try to create a session using the worker's SessionLocal
    # This should use the patched version, but it might use the cached one
    try:
        worker_session = worker_session_local()
        # If this is the same as test_db, patching worked
        # If it's different, import caching is the issue
        is_same = worker_session is test_db
        worker_session.close()
        
        if not is_same:
            pytest.fail(
                "Import caching issue confirmed: "
                "SessionLocal in worker module is not affected by monkeypatch"
            )
    except Exception as e:
        pytest.fail(f"Error creating session: {e}")
    
    test_db.close()

