"""Review API routes."""

import logging
import uuid
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models.review import Review, ReviewStatus
from app.schemas.review import (
    ReviewDetailResponse,
    ReviewResponse,
    ReviewStatusResponse,
)
from app.utils.logging import log_event
from app.worker.review_tasks import enqueue_review_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=ReviewResponse)
async def create_review(
    url: str | None = Form(None),
    doi: str | None = Form(None),
    repo_url: str | None = Form(None),
    pdf_file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    """
    Create a new review.

    Accepts either:
    - URL/DOI of paper (with optional PDF upload)
    - PDF file upload (with optional URL/DOI)
    - Optional repo_url for GitHub repository

    At least one of {url, doi, pdf_file} must be provided.
    """
    # Validation: at least one input source
    if not any([url, doi, pdf_file]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of 'url', 'doi', or 'pdf_file' must be provided",
        )

    # Validate PDF size (25MB max)
    pdf_file_path = None
    if pdf_file:
        if pdf_file.size and pdf_file.size > 25 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF file size must be ≤ 25MB",
            )
        # Save PDF temporarily (will be moved to permanent location by worker)
        from app.config import settings

        pdf_dir = Path(settings.artifacts_base_path) / "reviews" / "pdfs"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_file_path = str(pdf_dir / f"{uuid.uuid4()}.pdf")
        with open(pdf_file_path, "wb") as f:
            content = await pdf_file.read()
            f.write(content)

    # Create review record
    review = Review(
        url=url,
        doi=doi,
        repo_url=repo_url,
        pdf_file_path=pdf_file_path,
        status=ReviewStatus.PENDING,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    # Enqueue review processing task
    try:
        enqueue_review_task(str(review.id))
    except Exception as e:
        logger.error(f"Failed to enqueue review task: {e}")
        review.status = ReviewStatus.FAILED
        review.error_message = f"Failed to enqueue task: {str(e)}"
        db.commit()

    # Log review creation
    log_event(
        logging.INFO,
        "Review created",
        job_id=str(review.id),
        step="create_review",
        event="review_created",
        status="pending",
    )

    return ReviewResponse.model_validate(review)


@router.get("/{review_id}", response_model=ReviewDetailResponse)
def get_review(review_id: UUID, db: Session = Depends(get_db)):
    """Get review details."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )
    return ReviewDetailResponse.model_validate(review)


@router.get("/{review_id}/status", response_model=ReviewStatusResponse)
def get_review_status(review_id: UUID, db: Session = Depends(get_db)):
    """Get review status."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )
    return ReviewStatusResponse.model_validate(review)


@router.get("/{review_id}/artifacts/{artifact_type}")
def get_review_artifact(
    review_id: UUID, artifact_type: str, db: Session = Depends(get_db)
):
    """
    Get review artifact (report.html or review.json).

    artifact_type must be one of: 'report.html', 'review.json'
    """
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )

    if artifact_type == "report.html":
        if not review.html_report_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="HTML report not available",
            )
        file_path = Path(review.html_report_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="HTML report file not found"
            )
        from fastapi.responses import FileResponse

        return FileResponse(
            file_path, media_type="text/html", filename=f"review_{review_id}.html"
        )

    elif artifact_type == "review.json":
        if not review.json_summary_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="JSON summary not available",
            )
        file_path = Path(review.json_summary_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="JSON summary file not found"
            )
        from fastapi.responses import FileResponse

        return FileResponse(
            file_path, media_type="application/json", filename=f"review_{review_id}.json"
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid artifact_type: {artifact_type}. Must be 'report.html' or 'review.json'",
        )


@router.get("/{review_id}/score")
def get_review_score(review_id: UUID, db: Session = Depends(get_db)):
    """Get review quality score with SHAP explanations."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )

    if not review.quality_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Quality score not available"
        )

    return review.quality_score

