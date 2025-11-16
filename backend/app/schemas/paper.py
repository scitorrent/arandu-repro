"""Paper schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import PaperVisibility


class PaperBase(BaseModel):
    """Base paper schema."""

    aid: str = Field(..., max_length=100)  # Identificador estável
    title: str | None = Field(None, max_length=500)
    repo_url: str | None = Field(None, max_length=1000)
    visibility: PaperVisibility = PaperVisibility.PRIVATE
    license: str | None = Field(None, max_length=200)
    created_by: str | None = Field(None, max_length=200)


class PaperCreate(PaperBase):
    """Schema for creating a paper."""

    pass


class PaperUpdate(BaseModel):
    """Schema for updating a paper."""

    title: str | None = None
    repo_url: str | None = None
    visibility: PaperVisibility | None = None
    license: str | None = None


class Paper(PaperBase):
    """Schema for paper response."""

    id: UUID
    approved_public_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class PaperWithRelations(Paper):
    """Schema for paper with relations."""

    versions: list["PaperVersion"] = []
    external_ids: list["PaperExternalId"] = []
    quality_scores: list["QualityScore"] = []

