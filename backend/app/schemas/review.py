"""Review schemas for API."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    """Schema for creating a review."""

    url: str | None = None
    doi: str | None = None
    repo_url: str | None = None
    # pdf_file handled via multipart form

    model_config = ConfigDict(from_attributes=True)


class ReviewResponse(BaseModel):
    """Schema for review response."""

    id: UUID
    url: str | None
    doi: str | None
    repo_url: str | None
    paper_title: str | None
    paper_authors: list[str] | None
    paper_venue: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ReviewDetailResponse(ReviewResponse):
    """Schema for detailed review response."""

    claims: list[dict[str, Any]] | None = None
    citations: dict[str, list[dict[str, Any]]] | None = None
    checklist: dict[str, Any] | None = None
    quality_score: dict[str, Any] | None = None
    badges: dict[str, Any] | None = None
    html_report_path: str | None = None
    json_summary_path: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ReviewStatusResponse(BaseModel):
    """Schema for review status response."""

    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    error_message: str | None = None

    model_config = ConfigDict(from_attributes=True)

