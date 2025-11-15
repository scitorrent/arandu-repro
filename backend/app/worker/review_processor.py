"""Review processing pipeline."""

import logging
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.review import Review, ReviewStatus
from app.utils.logging import log_event, log_step

logger = logging.getLogger(__name__)


def process_review(review_id: str) -> None:
    """
    Process a review through the full pipeline.

    Pipeline:
    1. Ingestion (PDF/URL parsing, metadata extraction)
    2. Claim extraction
    3. Citation suggestion (RAG)
    4. Method checklist
    5. Quality score + SHAP
    6. Badge generation
    7. Report generation (HTML + JSON)
    """
    db: Session = SessionLocal()
    review_uuid = UUID(review_id) if isinstance(review_id, str) else review_id

    # Get review from database
    review = db.query(Review).filter(Review.id == review_uuid).first()
    if not review:
        log_event(
            logging.ERROR,
            "Review not found",
            job_id=review_id,
            step="process_review",
            event="review_not_found",
            status="not_found",
        )
        return

    # Update status to processing
    review.status = ReviewStatus.PROCESSING
    db.commit()

    try:
        with log_step(review_id, "process_review", review_id=review_id):
            # TODO: Implement pipeline steps
            # 1. Ingestion
            # 2. Claim extraction
            # 3. Citation suggestion
            # 4. Method checklist
            # 5. Quality score
            # 6. Badges
            # 7. Report generation

            # Placeholder: mark as completed
            review.status = ReviewStatus.COMPLETED
            db.commit()

            log_event(
                logging.INFO,
                "Review processing completed",
                job_id=review_id,
                step="process_review",
                event="review_processing_completed",
                status="completed",
            )

    except Exception as e:
        logger.exception(f"Error processing review {review_id}: {e}")
        review.status = ReviewStatus.FAILED
        review.error_message = str(e)
        db.commit()

        log_event(
            logging.ERROR,
            f"Review processing failed: {str(e)}",
            job_id=review_id,
            step="process_review",
            event="review_processing_failed",
            status="failed",
            error=str(e),
        )
    finally:
        db.close()

