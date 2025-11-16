"""Tests for RAG pipeline components."""

import pytest

from app.worker.rag.embeddings import cosine_similarity, embed_text


@pytest.mark.skipif(
    not hasattr(__import__("sentence_transformers", fromlist=[""]), "SentenceTransformer"),
    reason="sentence-transformers not available",
)
def test_embed_text():
    """Test text embedding generation."""
    embedding = embed_text("This is a test sentence.")
    assert isinstance(embedding, list)
    assert len(embedding) > 0
    assert all(isinstance(x, float) for x in embedding)


@pytest.mark.skipif(
    not hasattr(__import__("sentence_transformers", fromlist=[""]), "SentenceTransformer"),
    reason="sentence-transformers not available",
)
def test_cosine_similarity():
    """Test cosine similarity computation."""
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    similarity = cosine_similarity(vec1, vec2)
    assert 0.99 <= similarity <= 1.0  # Should be ~1.0 for identical vectors

    vec3 = [0.0, 1.0, 0.0]
    similarity_orthogonal = cosine_similarity(vec1, vec3)
    assert -0.01 <= similarity_orthogonal <= 0.01  # Should be ~0.0 for orthogonal


def test_hybrid_search_normalize_scores():
    """Test score normalization in hybrid search."""
    from app.worker.rag.hybrid_search import normalize_scores

    scores = [1.0, 2.0, 3.0, 4.0, 5.0]
    normalized = normalize_scores(scores)
    assert len(normalized) == len(scores)
    assert sum(normalized) < 0.1  # Should be approximately zero-mean


def test_hybrid_search_combine():
    """Test hybrid search score combination."""
    from app.worker.rag.hybrid_search import hybrid_search

    bm25_results = [("doc1", 10.0), ("doc2", 8.0), ("doc3", 6.0)]
    dense_results = [(0, 0.9), (1, 0.8), (2, 0.7)]
    dense_to_doc_id = {0: "doc1", 1: "doc2", 2: "doc3"}

    # Mock query embedding (not used in hybrid_search function)
    query_embedding = [0.0] * 384

    combined = hybrid_search(
        query="test",
        query_embedding=query_embedding,
        bm25_results=bm25_results,
        dense_results=dense_results,
        dense_to_doc_id=dense_to_doc_id,
        alpha=0.5,
        top_k=3,
    )

    assert len(combined) <= 3
    assert all(isinstance(item, tuple) and len(item) == 2 for item in combined)
    # Should be sorted by score descending
    scores = [score for _, score in combined]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.skipif(
    not hasattr(__import__("sentence_transformers", fromlist=[""]), "CrossEncoder"),
    reason="sentence-transformers CrossEncoder not available",
)
def test_reranker():
    """Test reranker."""
    from app.worker.rag.reranker import rerank

    query = "machine learning"
    candidates = [
        {"title": "Deep Learning", "abstract": "A paper about deep learning"},
        {"title": "Random Forests", "abstract": "A paper about random forests"},
    ]

    reranked = rerank(query, candidates, top_k=2)
    assert len(reranked) <= 2
    assert all(isinstance(item, tuple) and len(item) == 2 for item in reranked)

