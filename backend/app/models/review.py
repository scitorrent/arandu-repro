"""Review model for Arandu CoReview Studio."""

import uuid
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import JSON, Column, DateTime, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class ReviewStatus(str, Enum):
    """Review status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Review(Base):
    """Review model."""

    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Input
    url = Column(String, nullable=True)  # Paper URL
    doi = Column(String, nullable=True)  # DOI
    pdf_file_path = Column(String, nullable=True)  # Path to uploaded PDF
    repo_url = Column(String, nullable=True)  # Optional GitHub repo

    # Metadata (stored as JSON for flexibility)
    paper_meta = Column(JSON, nullable=True)  # {title, authors, venue, published_at}

    # State
    status = Column(
        SQLEnum(ReviewStatus, native_enum=False, values_callable=lambda x: [e.value for e in ReviewStatus]),
        nullable=False,
        default=ReviewStatus.PENDING
    )
    error_message = Column(Text, nullable=True)

    # Processed data (stored as JSON for flexibility)
    paper_text = Column(Text, nullable=True)  # Full extracted text
    claims = Column(JSON, nullable=True)  # List of claims
    citations = Column(JSON, nullable=True)  # Citations by claim_id
    checklist = Column(JSON, nullable=True)  # Checklist items
    quality_score = Column(JSON, nullable=True)  # Quality score + SHAP
    badges = Column(JSON, nullable=True)  # Badge statuses

    # Artifacts
    html_report_path = Column(String, nullable=True)
    json_summary_path = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    completed_at = Column(DateTime, nullable=True)

