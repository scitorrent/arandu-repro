"""Badge API routes."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models.review import Review
from app.worker.badge_generator import compute_badge_status, generate_badge_svg

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/badges", tags=["badges"])


@router.get("/{review_id}/{badge_type}.svg")
async def get_badge(
    review_id: UUID,
    badge_type: str,
    db: Session = Depends(get_db),
):
    """
    Get badge SVG for a review.

    Args:
        review_id: Review ID
        badge_type: Type of badge (claim-mapped, method-check, citations-augmented)

    Returns:
        SVG image
    """
    # Validate badge type
    valid_types = ["claim-mapped", "method-check", "citations-augmented"]
    if badge_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid badge type. Must be one of: {', '.join(valid_types)}",
        )

    # Get review
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    # Build review data dictionary
    review_data = {
        "id": str(review.id),
        "claims": review.claims or [],
        "checklist": review.checklist or {},
        "citations": review.citations or {},
    }

    # Compute status and generate SVG
    status_value = compute_badge_status(badge_type, review_data)
    base_url = "http://localhost:8000"  # TODO: Get from config
    svg = generate_badge_svg(badge_type, status_value, str(review.id), base_url)

    # Return SVG with appropriate headers
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
        },
    )

