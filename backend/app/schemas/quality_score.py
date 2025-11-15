"""Quality score schemas."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class QualityScoreScope(str, Enum):
    """Quality score scope enumeration."""

    PAPER = "paper"
    VERSION = "version"


class QualityScoreSignals(BaseModel):
    """Quality score signals structure."""

    has_readme_run_steps: bool
    has_script_paper_mapping: bool
    has_input_example: bool
    has_cpu_synthetic_path: bool
    has_seeds: bool
    has_env_file: bool
    readme_quality: int = Field(..., ge=0, le=5)
    reproducibility_signals_count: int = Field(..., ge=0)


class QualityScoreRationale(BaseModel):
    """Quality score rationale structure."""

    summary: str
    positive_factors: list[str]
    negative_factors: list[str]
    recommendations: list[str]


class QualityScoreBase(BaseModel):
    """Base quality score schema."""

    scope: QualityScoreScope
    score: int = Field(..., ge=0, le=100)
    signals: Dict[str, Any]
    rationale: Dict[str, Any]
    scoring_model_version: str = "v0"


class QualityScoreCreate(QualityScoreBase):
    """Schema for creating a quality score."""

    paper_id: Optional[UUID] = None
    paper_version_id: Optional[UUID] = None

    @field_validator("scope")
    @classmethod
    def validate_scope(cls, v, info):
        """Validate scope and required IDs."""
        scope = v
        paper_id = info.data.get("paper_id")
        paper_version_id = info.data.get("paper_version_id")
        
        if scope == QualityScoreScope.PAPER:
            if not paper_id:
                raise ValueError("paper_id required when scope='paper'")
            if paper_version_id:
                raise ValueError("paper_version_id must be None when scope='paper'")
        elif scope == QualityScoreScope.VERSION:
            if not paper_version_id:
                raise ValueError("paper_version_id required when scope='version'")
            if paper_id:
                raise ValueError("paper_id must be None when scope='version'")
        return v


class QualityScore(QualityScoreBase):
    """Schema for quality score response."""

    id: UUID
    paper_id: Optional[UUID] = None
    paper_version_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True

