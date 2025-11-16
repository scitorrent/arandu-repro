"""Score narrator agent: generates human-readable narrative from quality score and SHAP."""

import logging
from typing import Any

from app.worker.llm_client import generate_text

logger = logging.getLogger(__name__)


def generate_narrative(
    score: float,
    tier: str,
    shap_data: list[dict[str, Any]],
    checklist: dict[str, Any],
    claims: list[dict[str, Any]],
    paper_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Generate narrative using LLM (Gemini) if available, otherwise use heuristics.

    Args:
        score: Quality score (0-100)
        tier: Score tier (A/B/C/D)
        shap_data: SHAP explanations
        checklist: Checklist data
        claims: List of claims
        paper_meta: Paper metadata

    Returns:
        Narrative dict with executive_justification and technical_deepdive
    """
    # Try LLM first
    narrative_llm = _generate_narrative_llm(
        score, tier, shap_data, checklist, claims, paper_meta
    )
    if narrative_llm:
        return narrative_llm

    # Fallback to heuristics
    return _generate_narrative_heuristic(score, tier, shap_data, checklist)


def _generate_narrative_llm(
    score: float,
    tier: str,
    shap_data: list[dict[str, Any]],
    checklist: dict[str, Any],
    claims: list[dict[str, Any]],
    paper_meta: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Generate narrative using Gemini LLM."""
    try:
        # Build prompt
        prompt = f"""You are a scientific review assistant. Generate a clear, objective narrative explaining a quality score for a research paper.

Quality Score: {score:.1f}/100 (Tier {tier})

Top Contributing Factors (SHAP):
{_format_shap_for_prompt(shap_data[:5])}

Checklist Summary:
{_format_checklist_for_prompt(checklist)}

Paper: {paper_meta.get('title', 'Unknown') if paper_meta else 'Unknown'}
Claims Extracted: {len(claims)}

Generate a JSON response with two fields:
1. "executive_justification": array of 3-5 bullet points (strings) explaining why this score makes sense, risks/biases identified, and actionable recommendations for the author.
2. "technical_deepdive": a short paragraph (string) explaining how each cluster of features weighed in (method, data, code, results), with references to evidence.

Be objective, evidence-based, and constructive. No ad hominem judgments.

JSON format:
{{
  "executive_justification": ["bullet 1", "bullet 2", ...],
  "technical_deepdive": "paragraph text"
}}
"""

        response = generate_text(prompt, temperature=0.3, max_tokens=1500)
        if not response:
            return None

        # Parse JSON from response
        import json
        import re

        # Extract JSON from markdown code blocks if present
        json_match = re.search(r'\{[^{}]*"executive_justification"[^{}]*\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            # Try to find JSON object
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            json_str = json_str.strip()

        try:
            narrative = json.loads(json_str)
            # Validate structure
            if "executive_justification" in narrative and "technical_deepdive" in narrative:
                return {
                    "executive_justification": narrative["executive_justification"],
                    "technical_deepdive": narrative["technical_deepdive"],
                }
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse LLM JSON, using heuristic fallback. Response: {response[:200]}")

    except Exception as e:
        logger.error(f"LLM narrative generation failed: {e}")

    return None


def _format_shap_for_prompt(shap_data: list[dict[str, Any]]) -> str:
    """Format SHAP data for prompt."""
    if not shap_data:
        return "No SHAP data available"

    lines = []
    for item in shap_data:
        feature = item.get("feature", "unknown")
        phi = item.get("phi", 0.0)
        value = item.get("value", "")
        sign = "+" if phi > 0 else ""
        lines.append(f"- {feature}: {sign}{phi:.2f} (value: {value})")

    return "\n".join(lines)


def _format_checklist_for_prompt(checklist: dict[str, Any]) -> str:
    """Format checklist for prompt."""
    if not checklist:
        return "No checklist data"

    items = checklist.get("items", [])
    if not items:
        return checklist.get("summary", "No checklist items")

    lines = [checklist.get("summary", "")]
    for item in items[:5]:  # Top 5 items
        key = item.get("key", "")
        status = item.get("status", "unknown")
        lines.append(f"- {key}: {status}")

    return "\n".join(lines)


def _generate_narrative_heuristic(
    score: float,
    tier: str,
    shap_data: list[dict[str, Any]],
    checklist: dict[str, Any],
) -> dict[str, Any]:
    """Generate narrative using heuristics (fallback)."""
    # Top positive and negative factors
    positive_factors = [item for item in shap_data if item.get("phi", 0) > 0][:3]
    negative_factors = [item for item in shap_data if item.get("phi", 0) < 0][:3]

    executive = [
        f"Quality score of {score:.1f} (Tier {tier}) reflects the paper's methodological transparency and reproducibility evidence.",
    ]

    if positive_factors:
        top_positive = positive_factors[0]
        executive.append(
            f"Strongest positive factor: {top_positive.get('feature', 'unknown')} "
            f"(contribution: +{top_positive.get('phi', 0):.1f})."
        )

    if negative_factors:
        top_negative = negative_factors[0]
        executive.append(
            f"Main area for improvement: {top_negative.get('feature', 'unknown')} "
            f"(contribution: {top_negative.get('phi', 0):.1f})."
        )

    executive.append(
        "Review the checklist and claims to identify specific actionable improvements."
    )

    technical = f"""
The quality score of {score:.1f} (Tier {tier}) is computed from multiple feature clusters:
- Methodological features (checklist items, reproducibility indicators)
- Evidence quality (claims, citations, documentation)
- Code/data availability indicators

Top contributing factors from SHAP analysis:
{_format_shap_for_prompt(shap_data[:5])}
""".strip()

    return {
        "executive_justification": executive,
        "technical_deepdive": technical,
    }
