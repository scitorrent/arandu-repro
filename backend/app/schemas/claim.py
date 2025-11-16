"""Claim schemas."""

import hashlib
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ClaimBase(BaseModel):
    """Base claim schema."""

    text: str = Field(..., max_length=5000)
    span_start: int | None = None  # Inclusive start [start, end)
    span_end: int | None = None  # Exclusive end [start, end)
    text_hash: str | None = Field(None, max_length=64)  # Hash do documento base
    page: int | None = None
    bbox: dict[str, Any] | None = None  # {x, y, width, height}
    section: str | None = Field(None, max_length=100)
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    extraction_model_version: str | None = Field(None, max_length=50)


class ClaimCreate(ClaimBase):
    """Schema for creating a claim."""

    paper_version_id: UUID

    @field_validator("span_start", "span_end")
    @classmethod
    def validate_span(cls, v, info):
        """Validate span consistency."""
        span_start = info.data.get("span_start")
        span_end = info.data.get("span_end")
        if (span_start is None) != (span_end is None):
            raise ValueError("span_start and span_end must both be set or both be None")
        return v

    def compute_hash(self, paper_version_id: UUID) -> str:
        """Compute hash for deduplication."""
        content = f"{self.text}|{self.span_start}|{self.span_end}|{paper_version_id}"
        return hashlib.sha256(content.encode()).hexdigest()


class Claim(ClaimBase):
    """Schema for claim response."""

    id: UUID
    paper_version_id: UUID
    paper_id: UUID | None = None
    hash: str
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True

