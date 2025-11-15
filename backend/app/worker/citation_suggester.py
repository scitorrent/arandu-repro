"""Citation suggester agent using RAG pipeline."""

import logging
from dataclasses import dataclass
from typing import Any

from app.config import settings
from app.worker.claim_extractor import Claim
from app.worker.rag.bm25_index import get_index, search_bm25
from app.worker.rag.embeddings import embed_text, search_dense
from app.worker.rag.hybrid_search import hybrid_search
from app.worker.rag.reranker import rerank

logger = logging.getLogger(__name__)


@dataclass
class CitationCandidate:
    """Citation candidate with scores."""

    title: str
    authors: list[str]
    venue: str | None
    year: int | None
    doi: str | None
    url: str
    abstract: str | None
    score_dense: float
    score_sparse: float
    score_final: float
    score_rerank: float
    justification: str  # Why this citation is relevant


def suggest_citations(
    claim: Claim,
    paper_context: dict[str, Any] | None = None,
    top_k: int = 5,
    min_score: float = 0.3,
) -> list[CitationCandidate]:
    """
    Suggest citations for a claim using RAG pipeline.

    Pipeline:
    1. Expand query (n-grams + entities)
    2. Search top-50 (BM25 + dense)
    3. Re-rank top-50 with cross-encoder
    4. Dedup and return top-k

    Args:
        claim: Claim object
        paper_context: Optional paper metadata for context
        top_k: Number of citations to return
        min_score: Minimum score threshold

    Returns:
        List of CitationCandidate objects
    """
    if not settings.rag_enabled:
        logger.warning("RAG disabled, returning empty citations")
        return []

    # Step 1: Expand query (simple: use claim text + section context)
    query = claim.text
    if claim.section:
        query = f"{claim.section} {query}"

    # Step 2: Hybrid search (BM25 + dense)
    # For now, use a simple corpus (paper's own text or external API)
    # TODO: Integrate with CrossRef/arXiv APIs for external corpus

    # Mock: In a real implementation, we would:
    # - Build index from paper's related work section
    # - Query external APIs (CrossRef, arXiv) if enabled
    # - Use hybrid search to get top-50

    # Placeholder: return empty for now (will be implemented with actual corpus)
    logger.info(f"Citation suggestion for claim {claim.id} (RAG pipeline placeholder)")

    # TODO: Implement full pipeline:
    # 1. Get corpus (paper text + external if available)
    # 2. Build/update BM25 index
    # 3. Generate embeddings for corpus
    # 4. Hybrid search
    # 5. Re-rank
    # 6. Dedup
    # 7. Return top-k

    return []


def suggest_citations_for_claims(
    claims: list[Claim],
    paper_text: str,
    paper_meta: dict[str, Any] | None = None,
) -> dict[str, list[CitationCandidate]]:
    """
    Suggest citations for multiple claims.

    Args:
        claims: List of Claim objects
        paper_text: Full paper text (for building local index)
        paper_meta: Optional paper metadata

    Returns:
        Dictionary mapping claim_id to list of CitationCandidate
    """
    citations_by_claim: dict[str, list[CitationCandidate]] = {}

    for claim in claims:
        citations = suggest_citations(claim, paper_context=paper_meta)
        citations_by_claim[claim.id] = citations

    return citations_by_claim

