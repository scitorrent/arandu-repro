"""Claim model."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Float,
    Index,
    Integer,
    JSON,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

from app.db.base import Base


class Claim(Base):
    """Claim model."""

    __tablename__ = "claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("paper_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    paper_id = Column(
        UUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )  # Para join rápido
    text = Column(String(5000), nullable=False)
    span_start = Column(Integer, nullable=True)
    span_end = Column(Integer, nullable=True)
    page = Column(Integer, nullable=True)  # Página do PDF
    bbox = Column(JSON, nullable=True)  # Bounding box {x, y, width, height}
    section = Column(String(100), nullable=True, index=True)
    confidence = Column(Float, nullable=True)
    extraction_model_version = Column(String(50), nullable=True)
    hash = Column(String(64), unique=True, nullable=False)  # Hash para dedupe
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )

    # Relationships
    paper_version = relationship("PaperVersion", back_populates="claims", foreign_keys=[paper_version_id])
    paper = relationship("Paper", foreign_keys=[paper_id])
    claim_links = relationship("ClaimLink", back_populates="claim", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "(span_start IS NULL AND span_end IS NULL) OR "
            "(span_start IS NOT NULL AND span_end IS NOT NULL)",
            name="check_span_consistency",
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)",
            name="check_confidence_range",
        ),
        UniqueConstraint("hash", name="uq_claims_hash"),
        Index("idx_claims_paper_version_id", "paper_version_id"),
        Index("idx_claims_paper_version_section", "paper_version_id", "section"),
        Index("idx_claims_paper_id", "paper_id"),
        Index("idx_claims_section", "section"),
        Index("idx_claims_hash", "hash", unique=True),
        Index("idx_claims_created_at", "created_at"),
        # GIN/trigram em text (PostgreSQL) - adicionar via migration separada se necessário
    )

