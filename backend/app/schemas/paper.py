"""Paper schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PaperVisibility(str, Enum):
    """Paper visibility enumeration."""

    PRIVATE = "private"
    UNLISTED = "unlisted"
    PUBLIC = "public"


class PaperBase(BaseModel):
    """Base paper schema."""

    aid: str = Field(..., max_length=100)  # Identificador estável
    title: Optional[str] = Field(None, max_length=500)
    repo_url: Optional[str] = Field(None, max_length=1000)
    visibility: PaperVisibility = PaperVisibility.PRIVATE
    license: Optional[str] = Field(None, max_length=200)
    created_by: Optional[str] = Field(None, max_length=200)


class PaperCreate(PaperBase):
    """Schema for creating a paper."""

    pass


class PaperUpdate(BaseModel):
    """Schema for updating a paper."""

    title: Optional[str] = None
    repo_url: Optional[str] = None
    visibility: Optional[PaperVisibility] = None
    license: Optional[str] = None


class Paper(PaperBase):
    """Schema for paper response."""

    id: UUID
    approved_public_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class PaperWithRelations(Paper):
    """Schema for paper with relations."""

    versions: list["PaperVersion"] = []
    external_ids: list["PaperExternalId"] = []
    quality_scores: list["QualityScore"] = []

