"""Review schemas for API."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


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
    paper_title: str | None = None
    paper_authors: list[str] | None = None
    paper_venue: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='before')
    @classmethod
    def extract_paper_meta(cls, data: Any) -> Any:
        """Extract paper metadata from paper_meta JSON field."""
        # Handle SQLAlchemy model objects
        if hasattr(data, 'paper_meta') and data.paper_meta and isinstance(data.paper_meta, dict):
            # Convert SQLAlchemy model to dict for Pydantic
            if not isinstance(data, dict):
                # Build dict with all attributes plus extracted paper_meta fields
                result = {}
                # Copy all model attributes
                for key in ['id', 'url', 'doi', 'repo_url', 'status', 'created_at', 'updated_at', 'completed_at']:
                    if hasattr(data, key):
                        result[key] = getattr(data, key)
                # Extract paper_meta fields
                result['paper_title'] = data.paper_meta.get('title')
                result['paper_authors'] = data.paper_meta.get('authors')
                result['paper_venue'] = data.paper_meta.get('venue')
                return result
            else:
                # If it's already a dict, modify it directly
                data['paper_title'] = data.get('paper_meta', {}).get('title')
                data['paper_authors'] = data.get('paper_meta', {}).get('authors')
                data['paper_venue'] = data.get('paper_meta', {}).get('venue')
        return data


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

