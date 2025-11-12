"""Artifact model."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class ArtifactType(str, Enum):
    """Artifact type enumeration."""

    REPORT = "report"
    NOTEBOOK = "notebook"
    BADGE = "badge"


class Artifact(Base):
    """Artifact model."""

    __tablename__ = "artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    type = Column(SQLEnum(ArtifactType), nullable=False)
    format = Column(String, nullable=False)  # markdown, html, ipynb, svg, etc.
    content_path = Column(String, nullable=False)
    content_size = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    job = relationship("Job", back_populates="artifacts")
