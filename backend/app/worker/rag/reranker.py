"""Re-ranking using cross-encoder."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Lazy loading of cross-encoder
_model = None


def get_reranker_model():
    """
    Get or initialize the cross-encoder reranker model.

    Uses cross-encoder/ms-marco-MiniLM-L-6-v2 for speed.

    Returns:
        CrossEncoder model
    """
    global _model

    if _model is None:
        try:
            from sentence_transformers import CrossEncoder

            model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
            logger.info(f"Loading reranker model: {model_name}")
            _model = CrossEncoder(model_name)
            logger.info(f"Reranker model loaded: {model_name}")
        except ImportError:
            logger.warning("sentence-transformers CrossEncoder not available, reranking will be skipped")
            return None

    return _model


def rerank(
    query: str,
    candidates: list[dict[str, Any]],  # List of {title, abstract, ...}
    top_k: int = 5,
) -> list[tuple[int, float]]:
    """
    Re-rank candidates using cross-encoder.

    Args:
        query: Search query (claim text)
        candidates: List of candidate documents with 'title' and 'abstract' fields
        top_k: Number of top results to return

    Returns:
        List of (index, rerank_score) tuples, sorted by score descending
    """
    model = get_reranker_model()
    if model is None:
        # Fallback: return original order with dummy scores
        return [(i, 1.0) for i in range(min(len(candidates), top_k))]

    # Prepare pairs for cross-encoder
    pairs = []
    for candidate in candidates:
        candidate_text = f"{candidate.get('title', '')} {candidate.get('abstract', '')}"
        pairs.append([query, candidate_text])

    # Get rerank scores
    scores = model.predict(pairs)

    # Sort by score
    scored_indices = [(i, float(score)) for i, score in enumerate(scores)]
    scored_indices.sort(key=lambda x: x[1], reverse=True)

    return scored_indices[:top_k]

