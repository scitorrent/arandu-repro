"""Artifact schemas for API validation."""

from pydantic import BaseModel

from app.models.artifact import ArtifactType


class ArtifactResponse(BaseModel):
    """Schema for artifact response."""

    type: ArtifactType
    format: str
    download_url: str

    class Config:
        from_attributes = True
