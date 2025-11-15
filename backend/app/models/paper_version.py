"""Paper version model."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

from app.db.base import Base


class PaperVersion(Base):
    """Paper version model."""

    __tablename__ = "paper_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aid = Column(String, ForeignKey("papers.aid", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    pdf_path = Column(String(1000), nullable=False)  # Relativo a PAPERS_BASE/{aid}/v{version}/file.pdf
    meta_json = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)  # Soft delete

    # Relationships
    paper = relationship("Paper", back_populates="versions", foreign_keys=[aid])
    quality_scores = relationship(
        "QualityScore",
        back_populates="paper_version",
        foreign_keys="QualityScore.paper_version_id",
        cascade="all, delete-orphan",
    )
    claims = relationship("Claim", back_populates="paper_version", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("aid", "version", name="uq_paper_versions_aid_version"),
        CheckConstraint("version >= 1", name="check_version_positive"),
        Index("idx_paper_versions_aid", "aid"),
        Index("idx_paper_versions_created_at", "created_at"),
        Index("idx_paper_versions_deleted_at", "deleted_at"),
    )

