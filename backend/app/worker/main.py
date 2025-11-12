"""Worker main entry point."""

import logging
from datetime import datetime, UTC
from uuid import UUID

from redis import Redis
from rq import Worker
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import SessionLocal
from app.models.job import Job, JobStatus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize Redis connection
redis_conn = Redis.from_url(settings.redis_url)


def process_job(job_id: str):
    """Process a job (main worker function)."""
    db: Session = SessionLocal()
    job = None
    try:
        logger.info(f"Processing job {job_id}")

        # Convert job_id to UUID
        job_uuid = UUID(job_id) if isinstance(job_id, str) else job_id

        # Get job from database
        job = db.query(Job).filter(Job.id == job_uuid).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        # Update status to running
        job.status = JobStatus.RUNNING
        job.updated_at = datetime.now(UTC)
        db.commit()

        # TODO: In Sprint 1, implement actual job processing:
        # - Clone repo
        # - Detect environment
        # - Build Docker image
        # - Execute command
        # - Generate artifacts

        # For now, just simulate completion
        logger.info(f"Job {job_id} processing completed (placeholder)")
        job.status = JobStatus.COMPLETED
        job.updated_at = datetime.now(UTC)
        db.commit()

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}", exc_info=True)
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.updated_at = datetime.now(UTC)
            db.commit()
    finally:
        db.close()


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
