"""SQLAlchemy models."""

from app.models.artifact import Artifact, ArtifactType
from app.models.job import Job, JobStatus
from app.models.review import Review, ReviewStatus
from app.models.run import Run
from app.models.paper import Paper, PaperVisibility
from app.models.paper_version import PaperVersion
from app.models.paper_external_id import PaperExternalId, ExternalIdKind
from app.models.quality_score import QualityScore, QualityScoreScope
from app.models.claim import Claim
from app.models.claim_link import ClaimLink, ClaimRelation

__all__ = [
    "Job",
    "JobStatus",
    "Run",
    "Artifact",
    "ArtifactType",
    "Review",
    "ReviewStatus",
    "Paper",
    "PaperVisibility",
    "PaperVersion",
    "PaperExternalId",
    "ExternalIdKind",
    "QualityScore",
    "QualityScoreScope",
    "Claim",
    "ClaimLink",
    "ClaimRelation",
]
