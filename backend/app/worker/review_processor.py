"""Review processing pipeline."""

import logging
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.review import Review, ReviewStatus
from app.utils.logging import log_event, log_step
from app.worker.claim_extractor import claims_to_json, extract_claims_by_section
from app.worker.review_ingestion import ingest_paper

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
            # Step 1: Ingestion (PDF/URL parsing, metadata extraction)
            with log_step(review_id, "ingestion", review_id=review_id):
                paper_meta = ingest_paper(
                    url=review.url,
                    doi=review.doi,
                    pdf_path=review.pdf_file_path,
                )

                # Update review with metadata and text
                review.paper_title = paper_meta.title
                review.paper_authors = paper_meta.authors
                review.paper_venue = paper_meta.venue
                review.paper_published_at = paper_meta.published_at
                review.paper_text = paper_meta.text
                db.commit()

                log_event(
                    logging.INFO,
                    "Paper ingested",
                    job_id=review_id,
                    step="ingestion",
                    event="ingestion_completed",
                    status="processing",
                )

            # Step 2: Claim extraction
            with log_step(review_id, "claim_extraction", review_id=review_id):
                claims = extract_claims_by_section(paper_meta.text)
                claims_json = claims_to_json(claims)

                review.claims = claims_json
                db.commit()

                log_event(
                    logging.INFO,
                    f"Extracted {len(claims)} claims",
                    job_id=review_id,
                    step="claim_extraction",
                    event="claims_extracted",
                    status="processing",
                )

            # TODO: Steps 3-7 (Citations, Checklist, Quality Score, Badges, Reports)
            # For now, mark as completed after claims extraction
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

