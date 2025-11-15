"""Paper external ID schemas."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ExternalIdKind(str, Enum):
    """External ID kind enumeration."""

    DOI = "doi"
    ARXIV = "arxiv"
    PMID = "pmid"
    URL = "url"


class PaperExternalIdBase(BaseModel):
    """Base paper external ID schema."""

    kind: ExternalIdKind
    value: str = Field(..., max_length=500)


class PaperExternalIdCreate(PaperExternalIdBase):
    """Schema for creating a paper external ID."""

    paper_id: UUID


class PaperExternalId(PaperExternalIdBase):
    """Schema for paper external ID response."""

    id: UUID
    paper_id: UUID
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True

