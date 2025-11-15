"""Pydantic schemas."""

from app.schemas.job import Job, JobCreate, JobUpdate
from app.schemas.review import Review, ReviewCreate, ReviewUpdate
from app.schemas.paper import (
    Paper,
    PaperCreate,
    PaperUpdate,
    PaperVisibility,
    PaperWithRelations,
)
from app.schemas.paper_version import PaperVersion, PaperVersionCreate
from app.schemas.paper_external_id import (
    PaperExternalId,
    PaperExternalIdCreate,
    ExternalIdKind,
)
from app.schemas.quality_score import (
    QualityScore,
    QualityScoreCreate,
    QualityScoreScope,
    QualityScoreSignals,
    QualityScoreRationale,
)
from app.schemas.claim import Claim, ClaimCreate
from app.schemas.claim_link import ClaimLink, ClaimLinkCreate

__all__ = [
    "Job",
    "JobCreate",
    "JobUpdate",
    "Review",
    "ReviewCreate",
    "ReviewUpdate",
    "Paper",
    "PaperCreate",
    "PaperUpdate",
    "PaperVisibility",
    "PaperWithRelations",
    "PaperVersion",
    "PaperVersionCreate",
    "PaperExternalId",
    "PaperExternalIdCreate",
    "ExternalIdKind",
    "QualityScore",
    "QualityScoreCreate",
    "QualityScoreScope",
    "QualityScoreSignals",
    "QualityScoreRationale",
    "Claim",
    "ClaimCreate",
    "ClaimLink",
    "ClaimLinkCreate",
]
