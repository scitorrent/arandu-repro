"""Quality score model."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import QualityScoreScope


class QualityScore(Base):
    """Quality score model."""

    __tablename__ = "quality_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(
        UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=True, index=True
    )
    paper_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("paper_versions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    scope = Column(SQLEnum(QualityScoreScope), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    signals = Column(JSON, nullable=False)
    rationale = Column(JSON, nullable=False)
    scoring_model_version = Column(String(20), default="v0", nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )

    # Relationships
    paper = relationship("Paper", back_populates="quality_scores", foreign_keys=[paper_id])
    paper_version = relationship(
        "PaperVersion", back_populates="quality_scores", foreign_keys=[paper_version_id]
    )

    __table_args__ = (
        CheckConstraint(
            "(scope = 'paper' AND paper_id IS NOT NULL AND paper_version_id IS NULL) OR "
            "(scope = 'version' AND paper_version_id IS NOT NULL AND paper_id IS NULL)",
            name="check_quality_score_scope",
        ),
        CheckConstraint("score >= 0 AND score <= 100", name="check_score_range"),
        Index("idx_quality_scores_paper_id", "paper_id"),
        Index("idx_quality_scores_paper_version_id", "paper_version_id"),
        Index("idx_quality_scores_scope", "scope"),
        Index("idx_quality_scores_created_at", "created_at"),
        Index("idx_quality_scores_score", "score"),
        Index("idx_quality_scores_score_created", "score", "created_at"),  # Composto para ranking
    )

