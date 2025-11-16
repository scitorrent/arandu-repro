"""Hybrid search combining BM25 and dense embeddings."""

import logging


logger = logging.getLogger(__name__)


def normalize_scores(scores: list[float]) -> list[float]:
    """
    Normalize scores using z-score normalization.

    Args:
        scores: List of scores

    Returns:
        Normalized scores
    """
    import numpy as np

    if not scores:
        return []

    scores_arr = np.array(scores)
    mean = np.mean(scores_arr)
    std = np.std(scores_arr)

    if std == 0:
        return [1.0] * len(scores)

    normalized = (scores_arr - mean) / std
    return normalized.tolist()


def hybrid_search(
    query: str,
    query_embedding: list[float],
    bm25_results: list[tuple[str, float]],  # (doc_id, bm25_score)
    dense_results: list[tuple[int, float]],  # (index, dense_score)
    dense_to_doc_id: dict[int, str],  # Map dense index to doc_id
    alpha: float = 0.5,  # Weight for BM25 (1-alpha for dense)
    top_k: int = 50,
) -> list[tuple[str, float]]:
    """
    Combine BM25 and dense search results using late fusion.

    Args:
        query: Search query (for logging)
        query_embedding: Query embedding vector
        bm25_results: BM25 search results [(doc_id, score), ...]
        dense_results: Dense search results [(index, score), ...]
        dense_to_doc_id: Mapping from dense index to doc_id
        alpha: Weight for BM25 (0-1), (1-alpha) for dense
        top_k: Number of final results

    Returns:
        Combined results [(doc_id, final_score), ...] sorted by score descending
    """
    # Normalize BM25 scores
    bm25_scores = [score for _, score in bm25_results]
    bm25_normalized = normalize_scores(bm25_scores)

    # Normalize dense scores
    dense_scores = [score for _, score in dense_results]
    dense_normalized = normalize_scores(dense_scores)

    # Create score maps
    bm25_map = {doc_id: score for (doc_id, _), score in zip(bm25_results, bm25_normalized)}
    dense_map = {
        dense_to_doc_id[idx]: score
        for (idx, _), score in zip(dense_results, dense_normalized)
    }

    # Combine scores
    all_doc_ids = set(bm25_map.keys()) | set(dense_map.keys())
    combined_scores: dict[str, float] = {}

    for doc_id in all_doc_ids:
        bm25_score = bm25_map.get(doc_id, 0.0)
        dense_score = dense_map.get(doc_id, 0.0)
        combined_score = alpha * bm25_score + (1 - alpha) * dense_score
        combined_scores[doc_id] = combined_score

    # Sort by combined score
    sorted_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)

    return sorted_results[:top_k]

