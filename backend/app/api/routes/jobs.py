"""Job endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models.job import Job, JobStatus
from app.schemas.job import JobCreate, JobResponse, JobStatusResponse

router = APIRouter()


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    db: Annotated[Session, Depends(get_db)],
):
    """Create a new job."""
    import logging

    from app.utils.logging import log_event

    # Create job record
    job = Job(
        repo_url=job_data.repo_url,
        arxiv_id=job_data.arxiv_id,
        run_command=job_data.run_command,
        status=JobStatus.PENDING,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Log job creation
    log_event(
        logging.INFO,
        "Job created",
        job_id=str(job.id),
        step="create_job",
        event="job_created",
        status="pending",
    )

    # Enqueue worker task
    try:
        from app.worker.tasks import enqueue_job_task

        enqueue_job_task(str(job.id))
    except Exception as e:
        # If enqueue fails, mark job as failed
        job.status = JobStatus.FAILED
        job.error_message = f"Failed to enqueue job: {str(e)}"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enqueue job (job_id={job.id}, repo_url={job.repo_url})",
        )

    return JobResponse.model_validate(job)


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    db: Annotated[Session, Depends(get_db)],
):
    """Get job details by ID."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Build artifacts list if job is completed
    artifacts = None
    if job.status == JobStatus.COMPLETED and job.artifacts:
        from app.schemas.artifact import ArtifactResponse

        artifacts = [
            ArtifactResponse(
                type=artifact.type,
                format=artifact.format,
                download_url=f"/jobs/{job_id}/artifacts/{artifact.type.value}",
            )
            for artifact in job.artifacts
        ]

    # Use model_validate and override artifacts if needed
    response = JobResponse.model_validate(job)
    if artifacts is not None:
        response.artifacts = artifacts
    return response


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    job_id: UUID,
    db: Annotated[Session, Depends(get_db)],
):
    """Get lightweight job status."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return JobStatusResponse.model_validate(job)
