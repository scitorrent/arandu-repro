"""Pydantic schemas."""

# Import existing schemas if they exist
try:
    from app.schemas.job import Job, JobCreate, JobUpdate
except ImportError:
    pass

try:
    from app.schemas.review import Review, ReviewCreate, ReviewUpdate
except ImportError:
    pass
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

# Add existing schemas if available
try:
    __all__.extend(["Job", "JobCreate", "JobUpdate"])
except NameError:
    pass

try:
    __all__.extend(["Review", "ReviewCreate", "ReviewUpdate"])
except NameError:
    pass
