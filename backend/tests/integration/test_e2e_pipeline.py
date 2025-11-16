"""End-to-end integration tests for the full pipeline (Issue #32)."""

import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db.base import Base
from app.models.artifact import Artifact, ArtifactType
from app.models.job import Job, JobStatus
from app.models.run import Run
from app.worker.main import process_job


@pytest.mark.integration
class TestE2EPipeline:
    """End-to-end tests for the full job pipeline."""

    db = None  # Will be set by fixture

    @pytest.fixture(autouse=True)
    def setup_db(self, monkeypatch):
        """Set up in-memory SQLite database for testing."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        session_local = sessionmaker(bind=engine)  # noqa: N806
        db = session_local()
        # Store db in class for test methods
        TestE2EPipeline.db = db
        # Patch SessionLocal to return our test db
        monkeypatch.setattr("app.db.session.SessionLocal", lambda: db)
        yield
        db.close()

    @pytest.fixture
    def test_repo_path(self, tmp_path):
        """Create a test repository fixture."""
        repo_path = tmp_path / "test-repo"
        repo_path.mkdir()

        # Create a simple Python script
        (repo_path / "main.py").write_text('print("Hello from Arandu Repro test!")\n')

        # Create requirements.txt
        (repo_path / "requirements.txt").write_text("numpy==1.24.0\n")

        # Create README
        (repo_path / "README.md").write_text("# Test Repo\n")

        return repo_path

    @pytest.fixture
    def temp_artifacts_dir(self, tmp_path, monkeypatch):
        """Set up temporary artifacts directory."""
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()
        # Patch settings to use temp directory
        original_path = settings.artifacts_base_path
        monkeypatch.setattr(settings, "artifacts_base_path", artifacts_dir)
        yield artifacts_dir
        # Restore original path
        monkeypatch.setattr(settings, "artifacts_base_path", original_path)

    def test_full_pipeline_with_local_repo(self, test_repo_path, temp_artifacts_dir):
        """
        Test the full pipeline with a local repository.

        This test:
        1. Creates a job via API (mocked)
        2. Processes the job with the worker
        3. Asserts artifacts are created
        4. Asserts status transitions
        """
        # Create job record
        job = Job(
            repo_url=f"file://{test_repo_path}",
            run_command="python main.py",
            status=JobStatus.PENDING,
        )
        TestE2EPipeline.db.add(job)
        TestE2EPipeline.db.commit()
        TestE2EPipeline.db.flush()  # Ensure job is visible
        job_id = str(job.id)
        
        # Verify job exists before processing
        assert TestE2EPipeline.db.query(Job).filter(Job.id == job.id).first() is not None

        # Process job
        try:
            process_job(job_id)
        except Exception as e:
            # If Docker is not available, skip the test
            if "Cannot connect to the Docker daemon" in str(e):
                pytest.skip("Docker daemon not available")
            raise

        # Refresh job from DB
        TestE2EPipeline.db.refresh(job)

        # Assert job completed
        assert job.status == JobStatus.COMPLETED, f"Job failed: {job.error_message}"

        # Assert run was created
        run = TestE2EPipeline.db.query(Run).filter(Run.job_id == job.id).first()
        assert run is not None
        assert run.exit_code == 0

        # Assert artifacts were created
        artifacts = TestE2EPipeline.db.query(Artifact).filter(Artifact.job_id == job.id).all()
        artifact_types = {a.type for a in artifacts}

        assert ArtifactType.REPORT in artifact_types
        assert ArtifactType.NOTEBOOK in artifact_types

        # Verify artifact files exist
        for artifact in artifacts:
            assert Path(artifact.content_path).exists()
            assert Path(artifact.content_path).stat().st_size > 0

        # Verify report content
        report_artifact = next(a for a in artifacts if a.type == ArtifactType.REPORT)
        report_content = Path(report_artifact.content_path).read_text()
        assert "Arandu Repro" in report_content
        assert job.repo_url in report_content

        # Verify notebook content
        notebook_artifact = next(a for a in artifacts if a.type == ArtifactType.NOTEBOOK)
        notebook_content = json.loads(Path(notebook_artifact.content_path).read_text())
        assert notebook_content["cells"] is not None
        assert len(notebook_content["cells"]) > 0

    def test_status_transitions(self, test_repo_path, temp_artifacts_dir):
        """Test that job status transitions correctly: pending -> running -> completed."""
        # Create job
        job = Job(
            repo_url=f"file://{test_repo_path}",
            run_command="python main.py",
            status=JobStatus.PENDING,
        )
        TestE2EPipeline.db.add(job)
        TestE2EPipeline.db.commit()
        TestE2EPipeline.db.flush()  # Ensure job is visible
        job_id = str(job.id)

        # Verify job exists before processing
        assert TestE2EPipeline.db.query(Job).filter(Job.id == job.id).first() is not None

        # Verify initial status
        assert job.status == JobStatus.PENDING

        # Process job
        try:
            process_job(job_id)
        except Exception as e:
            if "Cannot connect to the Docker daemon" in str(e):
                pytest.skip("Docker daemon not available")
            raise

        # Refresh and verify final status
        TestE2EPipeline.db.refresh(job)
        assert job.status == JobStatus.COMPLETED

        # Verify run has timestamps
        run = TestE2EPipeline.db.query(Run).filter(Run.job_id == job.id).first()
        assert run is not None
        assert run.started_at is not None
        assert run.completed_at is not None
        assert run.duration_seconds is not None
        assert run.duration_seconds > 0
