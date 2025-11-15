"""Score-Narrator Agent: generates executive and technical narratives."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def generate_narrative(
    score: float,
    tier: str,
    shap_explanations: list[dict[str, Any]],
    checklist: dict[str, Any],
    claims: list[dict[str, Any]],
    paper_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Generate executive and technical narratives for quality score.

    Args:
        score: Quality score (0-100)
        tier: Tier (A/B/C/D)
        shap_explanations: List of SHAP explanations
        checklist: Checklist dictionary
        claims: List of claims
        paper_meta: Optional paper metadata

    Returns:
        Dictionary with executive_justification and technical_deepdive
    """
    # Executive justification (3-5 bullets)
    executive = _generate_executive(score, tier, shap_explanations, checklist)

    # Technical deep-dive
    technical = _generate_technical(score, shap_explanations, checklist, claims)

    return {
        "executive_justification": executive,
        "technical_deepdive": technical,
    }


def _generate_executive(
    score: float,
    tier: str,
    shap_explanations: list[dict[str, Any]],
    checklist: dict[str, Any],
) -> list[str]:
    """Generate executive justification bullets."""
    bullets = []

    # Overall assessment
    if tier == "A":
        bullets.append(
            f"Score {score:.1f}/100 (Tier {tier}): Excellent evidence quality and reproducibility practices."
        )
    elif tier == "B":
        bullets.append(
            f"Score {score:.1f}/100 (Tier {tier}): Good evidence quality with minor gaps in reproducibility."
        )
    elif tier == "C":
        bullets.append(
            f"Score {score:.1f}/100 (Tier {tier}): Moderate evidence quality; several reproducibility items need attention."
        )
    else:
        bullets.append(
            f"Score {score:.1f}/100 (Tier {tier}): Evidence quality needs significant improvement for reproducibility."
        )

    # Top positive factors
    positive_shap = [e for e in shap_explanations if e.get("phi", 0) > 0]
    positive_shap.sort(key=lambda x: x.get("phi", 0), reverse=True)
    if positive_shap:
        top_positive = positive_shap[0]
        feature_name = top_positive.get("feature", "")
        bullets.append(
            f"Strongest positive factor: {_format_feature_name(feature_name)} "
            f"(contributes +{top_positive.get('phi', 0):.1f} points)."
        )

    # Top negative factors
    negative_shap = [e for e in shap_explanations if e.get("phi", 0) < 0]
    negative_shap.sort(key=lambda x: abs(x.get("phi", 0)), reverse=True)
    if negative_shap:
        top_negative = negative_shap[0]
        feature_name = top_negative.get("feature", "")
        bullets.append(
            f"Main area for improvement: {_format_feature_name(feature_name)} "
            f"(reduces score by {abs(top_negative.get('phi', 0)):.1f} points)."
        )

    # Checklist summary
    checklist_items = checklist.get("items", [])
    missing_critical = [
        item for item in checklist_items if item.get("status") == "missing" and item.get("key") in ["data_available", "seeds_fixed", "environment"]
    ]
    if missing_critical:
        bullets.append(
            f"Critical reproducibility items missing: {', '.join(item.get('key', '') for item in missing_critical[:3])}."
        )

    # Recommendations
    if tier in ("C", "D"):
        bullets.append(
            "Recommendations: Add missing reproducibility artifacts (data links, seeds, environment files) "
            "and improve evidence quality (ablation studies, baselines, error bars)."
        )

    return bullets[:5]  # Max 5 bullets


def _generate_technical(
    score: float,
    shap_explanations: list[dict[str, Any]],
    checklist: dict[str, Any],
    claims: list[dict[str, Any]],
) -> str:
    """Generate technical deep-dive."""
    lines = []

    lines.append(f"Technical Analysis (Score: {score:.1f}/100)")

    # Feature contributions
    lines.append("\nTop Feature Contributions:")
    top_features = shap_explanations[:5]
    for i, exp in enumerate(top_features, 1):
        feature = _format_feature_name(exp.get("feature", ""))
        phi = exp.get("phi", 0)
        value = exp.get("value", "")
        lines.append(f"  {i}. {feature}: {phi:+.1f} (value: {value})")

    # Checklist details
    lines.append("\nChecklist Status:")
    checklist_items = checklist.get("items", [])
    for item in checklist_items:
        status = item.get("status", "unknown")
        key = item.get("key", "")
        lines.append(f"  - {_format_feature_name(key)}: {status}")

    # Claims summary
    if claims:
        lines.append(f"\nClaims Extracted: {len(claims)}")
        sections = {}
        for claim in claims:
            section = claim.get("section", "unknown")
            sections[section] = sections.get(section, 0) + 1
        lines.append(f"  By section: {', '.join(f'{k}: {v}' for k, v in sections.items())}")

    return "\n".join(lines)


def _format_feature_name(feature: str) -> str:
    """Format feature name for human readability."""
    replacements = {
        "has_ablation": "Ablation studies",
        "has_baselines": "Baseline comparisons",
        "has_error_bars": "Error bars / confidence intervals",
        "has_seeds": "Random seed control",
        "has_requirements": "Dependency files",
        "has_lock_file": "Lock files",
        "has_ci": "CI/CD configuration",
        "has_tests": "Test suite",
        "has_repro_readme": "Reproducibility instructions",
        "has_license": "License file",
        "citation_coverage": "Citation coverage",
        "checklist_pct_ok": "Checklist completion",
        "critical_items_missing": "Critical items missing",
        "data_available": "Data availability",
        "seeds_fixed": "Seed fixation",
        "environment": "Environment files",
        "commands": "Execution commands",
        "metrics": "Metrics definition",
        "comparatives": "Baseline comparisons",
        "license": "License",
    }
    return replacements.get(feature, feature.replace("_", " ").title())

