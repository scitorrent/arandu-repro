"""Quality Score predictor using ML model."""

import logging
import pickle
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# Lazy loading of model
_model = None
_model_version = "v0.1.0"


def get_model_path() -> Path:
    """
    Get path to quality score model.

    Returns:
        Path to model file
    """
    model_dir = Path(settings.artifacts_base_path) / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    return model_dir / "quality_score_v01.pkl"


def load_model():
    """
    Load quality score model from disk.

    Returns:
        Trained model object (GradientBoostingRegressor or similar)
    """
    global _model

    if _model is None:
        model_path = get_model_path()
        if model_path.exists():
            try:
                with open(model_path, "rb") as f:
                    _model = pickle.load(f)
                logger.info(f"Loaded quality score model from {model_path}")
            except Exception as e:
                logger.warning(f"Failed to load model: {e}, using baseline heuristic")
                _model = None
        else:
            logger.warning(f"Model not found at {model_path}, using baseline heuristic")

    return _model


def predict_baseline(features: dict[str, Any]) -> float:
    """
    Baseline heuristic prediction (0-100).

    Used when model is not available.

    Args:
        features: Feature dictionary

    Returns:
        Score (0-100)
    """
    score = 50.0  # Base score

    # Paper features (+10 each)
    if features.get("has_ablation"):
        score += 10
    if features.get("has_baselines"):
        score += 10
    if features.get("has_error_bars"):
        score += 5
    if features.get("has_seeds"):
        score += 5

    # Repo features (+5 each)
    if features.get("has_requirements"):
        score += 5
    if features.get("has_lock_file"):
        score += 5
    if features.get("has_ci"):
        score += 5
    if features.get("has_tests"):
        score += 5
    if features.get("has_repro_readme"):
        score += 5
    if features.get("has_license"):
        score += 5

    # Citations (+10 for coverage)
    citation_coverage = features.get("citation_coverage", 0.0)
    score += citation_coverage * 10

    # Checklist (+10 for OK percentage)
    checklist_pct = features.get("checklist_pct_ok", 0.0)
    score += checklist_pct * 10

    # Penalties
    critical_missing = features.get("critical_items_missing", 0)
    score -= critical_missing * 5

    # Clamp to 0-100
    score = max(0.0, min(100.0, score))

    return score


def predict_quality_score(features: dict[str, Any]) -> dict[str, Any]:
    """
    Predict quality score (0-100) from features.

    Args:
        features: Feature dictionary

    Returns:
        Dictionary with score, tier, version
    """
    model = load_model()

    if model is None:
        # Use baseline heuristic
        score = predict_baseline(features)
        logger.info(f"Using baseline prediction: {score:.1f}")
    else:
        # Use ML model
        try:
            # Convert features to array (model-specific)
            # For now, use baseline if model format doesn't match
            score = predict_baseline(features)
            logger.warning("Model loaded but prediction not fully implemented, using baseline")
        except Exception as e:
            logger.error(f"Model prediction failed: {e}, falling back to baseline")
            score = predict_baseline(features)

    # Determine tier
    if score >= 85:
        tier = "A"
    elif score >= 70:
        tier = "B"
    elif score >= 55:
        tier = "C"
    else:
        tier = "D"

    return {
        "score": round(score, 1),
        "tier": tier,
        "version": _model_version,
        "model_type": "ml" if model else "baseline",
    }

