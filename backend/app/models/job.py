"""Job model."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class JobStatus(str, Enum):
    """Job status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(Base):
    """Job model."""

    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_url = Column(String, nullable=False)
    arxiv_id = Column(String, nullable=True)
    run_command = Column(String, nullable=True)
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.PENDING)
    error_message = Column(Text, nullable=True)
    detected_environment = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    run = relationship("Run", back_populates="job", uselist=False)  # One-to-one in v0
    artifacts = relationship("Artifact", back_populates="job", cascade="all, delete-orphan")
