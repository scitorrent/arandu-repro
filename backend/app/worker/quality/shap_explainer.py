"""SHAP explanations for Quality Score."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SHAPExplanation:
    """SHAP explanation for a feature."""

    feature_name: str
    feature_value: Any
    shap_value: float  # Contribution to score
    evidence_anchor: str | None = None  # Link to evidence in paper/repo


def explain_with_shap(
    features: dict[str, Any],
    score: float,
    model=None,  # Optional trained model
) -> list[SHAPExplanation]:
    """
    Generate SHAP explanations for quality score.

    Args:
        features: Feature dictionary
        score: Predicted score
        model: Optional trained model (for TreeExplainer)

    Returns:
        List of SHAPExplanation objects (top-k by absolute value)
    """
    try:
        import shap
    except ImportError:
        logger.warning("SHAP not available, using simple feature importance")
        return explain_simple(features, score)

    if model is None:
        # Use simple explanation when model not available
        return explain_simple(features, score)

    try:
        # Use TreeExplainer for tree-based models
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values([list(features.values())])

        # Map to feature names
        feature_names = list(features.keys())
        explanations = [
            SHAPExplanation(
                feature_name=name,
                feature_value=features[name],
                shap_value=float(shap_val),
            )
            for name, shap_val in zip(feature_names, shap_values[0])
        ]

        # Sort by absolute SHAP value
        explanations.sort(key=lambda x: abs(x.shap_value), reverse=True)

        return explanations[:10]  # Top 10
    except Exception as e:
        logger.warning(f"SHAP explanation failed: {e}, using simple explanation")
        return explain_simple(features, score)


def explain_simple(features: dict[str, Any], score: float) -> list[SHAPExplanation]:
    """
    Simple feature importance when SHAP/model not available.

    Uses heuristic weights based on feature impact.

    Args:
        features: Feature dictionary
        score: Predicted score

    Returns:
        List of SHAPExplanation objects
    """
    # Heuristic weights (approximate impact on score)
    weights: dict[str, float] = {
        "has_ablation": 10.0,
        "has_baselines": 10.0,
        "citation_coverage": 10.0,
        "checklist_pct_ok": 10.0,
        "has_requirements": 5.0,
        "has_lock_file": 5.0,
        "has_ci": 5.0,
        "has_tests": 5.0,
        "has_repro_readme": 5.0,
        "has_license": 5.0,
        "has_error_bars": 5.0,
        "has_seeds": 5.0,
        "critical_items_missing": -5.0,  # Negative impact
    }

    explanations = []
    for feature_name, feature_value in features.items():
        weight = weights.get(feature_name, 0.0)
        if weight != 0.0 and feature_value:
            # Approximate SHAP value
            shap_val = weight * (1.0 if isinstance(feature_value, bool) else float(feature_value))
            explanations.append(
                SHAPExplanation(
                    feature_name=feature_name,
                    feature_value=feature_value,
                    shap_value=shap_val,
                )
            )

    # Sort by absolute value
    explanations.sort(key=lambda x: abs(x.shap_value), reverse=True)

    return explanations[:10]  # Top 10


def shap_to_json(explanations: list[SHAPExplanation]) -> list[dict[str, Any]]:
    """
    Convert SHAP explanations to JSON-serializable format.

    Args:
        explanations: List of SHAPExplanation objects

    Returns:
        List of dictionaries
    """
    return [
        {
            "feature": exp.feature_name,
            "value": exp.feature_value,
            "phi": exp.shap_value,
            "evidence_anchor": exp.evidence_anchor,
        }
        for exp in explanations
    ]

