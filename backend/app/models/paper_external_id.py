"""Paper external ID model."""

import uuid
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

from app.db.base import Base


class ExternalIdKind(str, Enum):
    """External ID kind enumeration."""

    DOI = "doi"
    ARXIV = "arxiv"
    PMID = "pmid"
    URL = "url"


class PaperExternalId(Base):
    """Paper external ID model."""

    __tablename__ = "paper_external_ids"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(
        UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind = Column(SQLEnum(ExternalIdKind), nullable=False)
    value = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    # Relationships
    paper = relationship("Paper", back_populates="external_ids")

    __table_args__ = (
        UniqueConstraint("paper_id", "kind", name="uq_paper_external_ids_paper_kind"),
        Index("idx_paper_external_ids_kind_value", "kind", "value"),
    )

