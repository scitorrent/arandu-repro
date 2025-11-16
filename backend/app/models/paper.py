"""Paper model."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, Column, DateTime, Index, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import PaperVisibility


class Paper(Base):
    """Paper model."""

    __tablename__ = "papers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aid = Column(String, unique=True, nullable=False, index=True)  # Identificador estável
    title = Column(String(500), nullable=True)
    repo_url = Column(String(1000), nullable=True)
    visibility = Column(
        SQLEnum(PaperVisibility, native_enum=False, values_callable=lambda x: [e.value for e in PaperVisibility]),
        default=PaperVisibility.PRIVATE,
        nullable=False,
        index=True
    )
    license = Column(String(200), nullable=True)
    created_by = Column(String(200), nullable=True)  # Stub até auth
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    approved_public_at = Column(DateTime(timezone=True), nullable=True, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)  # Soft delete

    # Relationships
    versions = relationship("PaperVersion", back_populates="paper", cascade="all, delete-orphan")
    external_ids = relationship(
        "PaperExternalId", back_populates="paper", cascade="all, delete-orphan"
    )
    quality_scores = relationship(
        "QualityScore",
        back_populates="paper",
        foreign_keys="QualityScore.paper_id",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_papers_aid", "aid", unique=True),
        Index("idx_papers_visibility", "visibility"),
        Index("idx_papers_created_at", "created_at"),
        Index("idx_papers_approved_public_at", "approved_public_at"),
        Index("idx_papers_deleted_at", "deleted_at"),
    )

