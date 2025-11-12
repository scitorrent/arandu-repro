"""Job schemas for API validation."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.job import JobStatus


class JobCreate(BaseModel):
    """Schema for creating a job."""

    repo_url: str
    arxiv_id: str | None = None
    run_command: str | None = None

    @field_validator("repo_url")
    @classmethod
    def validate_repo_url(cls, v: str) -> str:
        """Validate GitHub repo URL."""
        if not v.startswith(("https://github.com/", "http://github.com/")):
            raise ValueError("repo_url must be a valid GitHub URL")
        return v


class JobResponse(BaseModel):
    """Schema for job response."""

    job_id: UUID = Field(alias="id")
    repo_url: str
    arxiv_id: str | None
    run_command: str | None
    status: JobStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    artifacts: list[ArtifactResponse] | None = None

    class Config:
        from_attributes = True
        populate_by_name = True


class JobStatusResponse(BaseModel):
    """Schema for lightweight job status response."""

    job_id: UUID
    status: JobStatus
    updated_at: datetime

    class Config:
        from_attributes = True


# Import after class definition to resolve forward reference
from app.schemas.artifact import ArtifactResponse  # noqa: E402

# Rebuild model to resolve forward reference
JobResponse.model_rebuild()
