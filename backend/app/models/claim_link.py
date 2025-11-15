"""Claim link model."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Float, Index, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import ClaimRelation


class ClaimLink(Base):
    """Claim link model."""

    __tablename__ = "claim_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(
        UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_paper_id = Column(
        UUID(as_uuid=True), ForeignKey("papers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_doc_id = Column(String(200), nullable=True)
    source_citation = Column(String(500), nullable=True)
    relation = Column(SQLEnum(ClaimRelation), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    context_excerpt = Column(String(2000), nullable=True)
    reasoning_ref = Column(String(500), nullable=True)  # Path para trace/justificativa
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )

    # Relationships
    claim = relationship("Claim", back_populates="claim_links", foreign_keys=[claim_id])
    source_paper = relationship("Paper", foreign_keys=[source_paper_id])

    __table_args__ = (
        CheckConstraint(
            "source_paper_id IS NOT NULL OR source_doc_id IS NOT NULL",
            name="check_source_exists",
        ),
        CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0", name="check_confidence_range"
        ),
        # UNIQUE(claim_id, COALESCE(source_paper_id::text, source_doc_id), relation)
        # Nota: UniqueConstraint com COALESCE pode precisar de índice funcional ou trigger
        # Por enquanto, validar na aplicação
        Index("idx_claim_links_claim_id", "claim_id"),
        Index("idx_claim_links_source_paper_id", "source_paper_id"),
        Index("idx_claim_links_relation", "relation"),
        Index("idx_claim_links_confidence", "confidence"),
    )

