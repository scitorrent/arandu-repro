"""Artifact schemas for API validation."""

from pydantic import BaseModel, ConfigDict

from app.models.artifact import ArtifactType


class ArtifactResponse(BaseModel):
    """Schema for artifact response."""

    model_config = ConfigDict(from_attributes=True)

    type: ArtifactType
    format: str
    download_url: str
