"""Paper version schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PaperVersionBase(BaseModel):
    """Base paper version schema."""

    aid: str = Field(..., max_length=100)
    version: int = Field(..., ge=1)
    pdf_path: str = Field(..., max_length=1000)
    meta_json: dict[str, Any] | None = None


class PaperVersionCreate(PaperVersionBase):
    """Schema for creating a paper version."""

    pass


class PaperVersion(PaperVersionBase):
    """Schema for paper version response."""

    id: UUID
    created_at: datetime
    deleted_at: datetime | None = None

    class Config:
        """Pydantic config."""

        from_attributes = True

