"""Embeddings service for RAG pipeline."""

import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Lazy loading of sentence-transformers
_model = None
_tokenizer = None


def get_embedding_model():
    """
    Get or initialize the embedding model.

    Uses all-MiniLM-L6-v2 (384 dim) for speed, or e5-base (768 dim) if configured.

    Returns:
        SentenceTransformer model
    """
    global _model

    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer

            model_name = getattr(settings, "rag_embedding_model", "all-MiniLM-L6-v2")
            logger.info(f"Loading embedding model: {model_name}")
            _model = SentenceTransformer(model_name)
            logger.info(f"Embedding model loaded: {model_name}")
        except ImportError:
            logger.error("sentence-transformers not available, embeddings will fail")
            raise

    return _model


def embed_text(text: str) -> list[float]:
    """
    Generate embedding for a single text.

    Args:
        text: Text to embed

    Returns:
        Embedding vector (list of floats)
    """
    model = get_embedding_model()
    embedding = model.encode(text, normalize_embeddings=True, show_progress_bar=False)
    return embedding.tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a batch of texts.

    Args:
        texts: List of texts to embed

    Returns:
        List of embedding vectors
    """
    model = get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return embeddings.tolist()


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity (0-1)
    """
    import numpy as np

    v1 = np.array(vec1)
    v2 = np.array(vec2)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


def search_dense(
    query_embedding: list[float],
    candidate_embeddings: list[list[float]],
    top_k: int = 50,
) -> list[tuple[int, float]]:
    """
    Search using dense embeddings (cosine similarity).

    Args:
        query_embedding: Query embedding vector
        candidate_embeddings: List of candidate embeddings
        top_k: Number of top results to return

    Returns:
        List of (index, score) tuples, sorted by score descending
    """
    import numpy as np

    query_vec = np.array(query_embedding)
    candidates = np.array(candidate_embeddings)

    # Compute cosine similarities
    similarities = np.dot(candidates, query_vec) / (
        np.linalg.norm(candidates, axis=1) * np.linalg.norm(query_vec)
    )

    # Get top-k indices
    top_indices = np.argsort(similarities)[::-1][:top_k]

    return [(int(idx), float(similarities[idx])) for idx in top_indices]

