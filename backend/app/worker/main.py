"""Worker main entry point."""

import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from redis import Redis
from rq import Worker
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import SessionLocal
from app.models.artifact import Artifact, ArtifactType
from app.models.job import Job, JobStatus
from app.models.run import Run
from app.utils.errors import (
    DockerBuildError,
    ExecutionError,
    ExecutionTimeoutError,
    NoEnvironmentDetectedError,
    RepoCloneError,
)
from app.utils.logging import log_event, log_step, setup_logging
from app.worker.artifact_generator import generate_badge, generate_notebook, generate_report
from app.worker.docker_builder import build_image, cleanup_image
from app.worker.env_detector import detect_environment
from app.worker.executor import execute_command
from app.worker.repo_cloner import cleanup_repo, clone_repo

setup_logging()
logger = logging.getLogger(__name__)

# Initialize Redis connection
redis_conn = Redis.from_url(settings.redis_url)


def process_job(job_id: str):
    """
    Process a job (main worker function).

    Pipeline:
    1. Update status to running
    2. Clone repository
    3. Detect environment
    4. Build Docker image
    5. Execute command
    6. Generate artifacts (report, notebook, badge)
    7. Update status to completed/failed
    """
    db: Session = SessionLocal()
    job = None
    repo_path: Path | None = None
    image_tag: str | None = None

    try:
        log_event(logging.INFO, "Starting job processing", job_id=job_id, step="process_job")

        # Convert job_id to UUID
        job_uuid = UUID(job_id) if isinstance(job_id, str) else job_id

        # Get job from database
        job = db.query(Job).filter(Job.id == job_uuid).first()
        if not job:
            log_event(logging.ERROR, "Job not found", job_id=job_id, step="process_job")
            return

        # Update status to running
        with log_step(job_id, "status_transition", from_status="pending", to_status="running"):
            job.status = JobStatus.RUNNING
            job.updated_at = datetime.now(UTC)
            db.commit()
            log_event(
                logging.INFO,
                "Job status: pending -> running",
                job_id=job_id,
                step="status_transition",
            )

        # Step 1: Clone repository
        repo_path = clone_repo(
            repo_url=job.repo_url,
            target_dir=settings.temp_repos_path / str(job.id),
            job_id=job_id,
        )

        # Step 2: Detect environment
        env_info = detect_environment(repo_path=repo_path, job_id=job_id)
        job.detected_environment = env_info.to_dict()
        db.commit()

        # Step 3: Build Docker image
        image_tag = build_image(
            repo_path=repo_path,
            env_info=env_info,
            job_id=job_id,
        )

        # Step 4: Execute command
        command = job.run_command or "python main.py"
        artifacts_dir = settings.artifacts_base_path / str(job.id)

        execution_result = execute_command(
            image_tag=image_tag,
            command=command,
            repo_path=repo_path,
            artifacts_dir=artifacts_dir,
            job_id=job_id,
            timeout_seconds=settings.default_timeout_seconds,
        )

        # Step 5: Create Run record
        run = Run(
            job_id=job.id,
            exit_code=execution_result.exit_code,
            stdout=execution_result.stdout,
            stderr=execution_result.stderr,
            logs_path=str(execution_result.logs_path) if execution_result.logs_path else None,
            started_at=datetime.now(UTC),  # TODO: Get actual start time from execution
            completed_at=datetime.now(UTC),
            duration_seconds=execution_result.duration_seconds,
        )
        db.add(run)
        db.commit()

        # Step 6: Generate artifacts
        # Report
        report_path = generate_report(
            job=job,
            run=run,
            env_info=env_info,
            output_path=artifacts_dir,
            job_id=job_id,
        )
        report_artifact = Artifact(
            job_id=job.id,
            type=ArtifactType.REPORT,
            format="markdown",
            content_path=str(report_path),
            content_size=report_path.stat().st_size if report_path.exists() else None,
        )
        db.add(report_artifact)

        # Notebook
        notebook_path = generate_notebook(
            job=job,
            env_info=env_info,
            output_path=artifacts_dir,
            job_id=job_id,
        )
        notebook_artifact = Artifact(
            job_id=job.id,
            type=ArtifactType.NOTEBOOK,
            format="ipynb",
            content_path=str(notebook_path),
            content_size=notebook_path.stat().st_size if notebook_path.exists() else None,
        )
        db.add(notebook_artifact)

        # Badge
        badge_path = generate_badge(
            job=job,
            base_url=settings.api_base_url,
            output_path=artifacts_dir,
            job_id=job_id,
        )
        badge_artifact = Artifact(
            job_id=job.id,
            type=ArtifactType.BADGE,
            format="markdown",
            content_path=str(badge_path),
            content_size=badge_path.stat().st_size if badge_path.exists() else None,
        )
        db.add(badge_artifact)

        db.commit()

        # Step 7: Update status to completed
        with log_step(job_id, "status_transition", from_status="running", to_status="completed"):
            job.status = JobStatus.COMPLETED
            job.updated_at = datetime.now(UTC)
            db.commit()
            log_event(
                logging.INFO,
                "Job status: running -> completed",
                job_id=job_id,
                step="status_transition",
                exit_code=execution_result.exit_code,
            )

        # Cleanup
        if repo_path:
            cleanup_repo(repo_path, job_id)
        if image_tag:
            cleanup_image(image_tag, job_id)

        log_event(
            logging.INFO,
            "Job processing completed successfully",
            job_id=job_id,
            step="process_job",
            duration_seconds=execution_result.duration_seconds,
        )

    except RepoCloneError as e:
        error_msg = f"Repository clone failed: {str(e)}"
        log_event(logging.ERROR, error_msg, job_id=job_id, step="clone_repo", error=str(e))
        _handle_job_failure(db, job, error_msg, job_id)

    except NoEnvironmentDetectedError as e:
        error_msg = f"Environment detection failed: {str(e)}"
        log_event(logging.ERROR, error_msg, job_id=job_id, step="detect_environment", error=str(e))
        _handle_job_failure(db, job, error_msg, job_id)

    except DockerBuildError as e:
        error_msg = f"Docker build failed: {str(e)}"
        log_event(logging.ERROR, error_msg, job_id=job_id, step="build_docker_image", error=str(e))
        _handle_job_failure(db, job, error_msg, job_id)

    except ExecutionTimeoutError as e:
        error_msg = f"Execution timeout: {str(e)}"
        log_event(logging.ERROR, error_msg, job_id=job_id, step="execute_command", error=str(e))
        _handle_job_failure(db, job, error_msg, job_id)

    except ExecutionError as e:
        error_msg = f"Execution failed: {str(e)}"
        log_event(logging.ERROR, error_msg, job_id=job_id, step="execute_command", error=str(e))
        _handle_job_failure(db, job, error_msg, job_id)

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log_event(
            logging.ERROR, error_msg, job_id=job_id, step="process_job", error=str(e), exc_info=True
        )
        _handle_job_failure(db, job, error_msg, job_id)

    finally:
        # Cleanup on error
        if repo_path:
            try:
                cleanup_repo(repo_path, job_id)
            except Exception as e:
                logger.warning(f"Failed to cleanup repo: {e}")

        if image_tag:
            try:
                cleanup_image(image_tag, job_id)
            except Exception as e:
                logger.warning(f"Failed to cleanup image: {e}")

        db.close()


def _handle_job_failure(db: Session, job: Job | None, error_message: str, job_id: str) -> None:
    """Handle job failure by updating status and storing error message."""
    if not job:
        return

    try:
        # Capture previous status before updating
        previous_status = job.status.value
        with log_step(job_id, "status_transition", from_status=previous_status, to_status="failed"):
            job.status = JobStatus.FAILED
            job.error_message = error_message
            job.updated_at = datetime.now(UTC)
            db.commit()
            log_event(
                logging.ERROR,
                f"Job status: {previous_status} -> failed",
                job_id=job_id,
                step="status_transition",
                error=error_message,
            )
    except Exception as e:
        logger.error(f"Failed to update job status to failed: {e}")
        db.rollback()


def main():
    """Main worker entry point."""
    logger.info("Starting RQ worker...")
    logger.info(f"Redis URL: {settings.redis_url}")

    # Create worker
    worker = Worker(["default"], connection=redis_conn)

    # Start worker
    logger.info("Worker started. Waiting for jobs...")
    worker.work()


if __name__ == "__main__":
    main()
