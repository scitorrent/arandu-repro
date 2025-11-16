"""Frozen enum values for database consistency."""

from enum import Enum


class PaperVisibility(str, Enum):
    """Paper visibility enumeration - FROZEN VALUES."""

    PRIVATE = "private"
    UNLISTED = "unlisted"
    PUBLIC = "public"


class ExternalIdKind(str, Enum):
    """External ID kind enumeration - FROZEN VALUES."""

    DOI = "doi"
    ARXIV = "arxiv"
    PMID = "pmid"
    URL = "url"


class QualityScoreScope(str, Enum):
    """Quality score scope enumeration - FROZEN VALUES."""

    PAPER = "paper"
    VERSION = "version"


class ClaimRelation(str, Enum):
    """Claim relation enumeration - FROZEN VALUES."""

    EQUIVALENT = "equivalent"
    COMPLEMENTARY = "complementary"
    CONTRADICTORY = "contradictory"
    UNCLEAR = "unclear"


# Frozen values for validation
PAPER_VISIBILITY_VALUES = [e.value for e in PaperVisibility]
EXTERNAL_ID_KIND_VALUES = [e.value for e in ExternalIdKind]
QUALITY_SCORE_SCOPE_VALUES = [e.value for e in QualityScoreScope]
CLAIM_RELATION_VALUES = [e.value for e in ClaimRelation]

