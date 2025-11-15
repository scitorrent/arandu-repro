"""Claim link schemas."""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ClaimLinkBase(BaseModel):
    """Base claim link schema."""

    source_paper_id: Optional[UUID] = None
    source_doc_id: Optional[str] = Field(None, max_length=200)
    source_citation: Optional[str] = Field(None, max_length=500)
    relation: Literal["equivalent", "complementary", "contradictory", "unclear"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    context_excerpt: Optional[str] = Field(None, max_length=2000)
    reasoning_ref: Optional[str] = Field(None, max_length=500)

    @field_validator("source_paper_id", "source_doc_id")
    @classmethod
    def validate_source(cls, v, info):
        """Validate that at least one source is provided."""
        source_paper_id = info.data.get("source_paper_id")
        source_doc_id = info.data.get("source_doc_id")
        if not source_paper_id and not source_doc_id:
            raise ValueError("Either source_paper_id or source_doc_id must be provided")
        return v


class ClaimLinkCreate(ClaimLinkBase):
    """Schema for creating a claim link."""

    claim_id: UUID


class ClaimLink(ClaimLinkBase):
    """Schema for claim link response."""

    id: UUID
    claim_id: UUID
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True

