"""Run / Execution model."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Run(Base):
    """Run / Execution model."""

    __tablename__ = "runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, unique=True)
    exit_code = Column(Integer, nullable=True)
    stdout = Column(Text, nullable=True)  # Truncated preview
    stderr = Column(Text, nullable=True)  # Truncated preview
    logs_path = Column(String, nullable=True)  # Path to full logs file
    started_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Relationships
    job = relationship("Job", back_populates="run")
