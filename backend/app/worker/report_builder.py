"""Report builder for reviews (HTML + JSON)."""

import json
import logging
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


def generate_html_report(review_data: dict[str, Any], output_path: Path) -> Path:
    """
    Generate HTML report for a review.

    Args:
        review_data: Complete review data dictionary
        output_path: Path to save HTML file

    Returns:
        Path to generated HTML file
    """
    html_content = _build_html_content(review_data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")

    logger.info(f"Generated HTML report at {output_path}")
    return output_path


def generate_json_report(review_data: dict[str, Any], output_path: Path) -> Path:
    """
    Generate JSON report for a review.

    Args:
        review_data: Complete review data dictionary
        output_path: Path to save JSON file

    Returns:
        Path to generated JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(review_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Generated JSON report at {output_path}")
    return output_path


def _build_html_content(review_data: dict[str, Any]) -> str:
    """Build HTML content from review data."""
    # Extract data
    paper_meta = review_data.get("paper_meta", {})
    claims = review_data.get("claims", [])
    citations = review_data.get("citations", {})
    checklist = review_data.get("checklist", {})
    quality_score = review_data.get("quality_score", {})
    badges = review_data.get("badges", {})

    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Arandu Review: {paper_meta.get('title', 'Untitled')}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        :root {{
            --color-primary: #214235;
            --color-primary-light: #6BA38A;
            --color-text-primary: #111827;
            --color-text-secondary: #6B7280;
            --color-success: #10B981;
            --color-warning: #F59E0B;
            --color-error: #EF4444;
        }}
    </style>
</head>
<body class="bg-gray-50 font-sans">
    <div class="max-w-6xl mx-auto px-6 py-8">
        <!-- Header -->
        <header class="mb-8">
            <h1 class="text-4xl font-semibold text-gray-900 mb-2">
                {paper_meta.get('title', 'Untitled Paper')}
            </h1>
            <div class="text-gray-600">
                {', '.join(paper_meta.get('authors', [])) if paper_meta.get('authors') else 'Unknown authors'}
            </div>
            <div class="text-sm text-gray-500 mt-2">
                {paper_meta.get('venue', 'Unknown venue')} • {paper_meta.get('published_at', 'Unknown date')}
            </div>
        </header>

        <!-- Badges -->
        <section class="mb-8">
            <h2 class="text-2xl font-semibold mb-4">Badges</h2>
            <div class="flex gap-4">
                {_render_badges(badges, review_data.get('id', ''))}
            </div>
        </section>

        <!-- Summary -->
        <section class="mb-8 bg-white rounded-lg shadow-sm p-6">
            <h2 class="text-2xl font-semibold mb-4">Summary</h2>
            <div class="prose max-w-none">
                <p class="text-gray-700">
                    This review analyzed <strong>{len(claims)} claims</strong> extracted from the paper.
                    {'Citations were suggested for most claims.' if citations else 'No citations were suggested.'}
                    The method checklist identified <strong>{_count_checklist_status(checklist, 'ok')} items as complete</strong>.
                </p>
            </div>
        </section>

        <!-- Quality Score -->
        {_render_quality_score(quality_score)}

        <!-- Claims & Citations -->
        <section class="mb-8">
            <h2 class="text-2xl font-semibold mb-4">Claims & Citations</h2>
            <div class="space-y-4">
                {_render_claims_citations(claims, citations)}
            </div>
        </section>

        <!-- Checklist -->
        {_render_checklist(checklist)}

        <!-- Recommendations -->
        {_render_recommendations(quality_score, checklist)}

        <!-- Metadata -->
        <section class="mt-8 pt-8 border-t border-gray-200">
            <h2 class="text-xl font-semibold mb-4">Metadata</h2>
            <div class="text-sm text-gray-600 space-y-1">
                <div><strong>Review ID:</strong> {review_data.get('id', 'Unknown')}</div>
                <div><strong>DOI:</strong> {review_data.get('doi', 'N/A')}</div>
                <div><strong>URL:</strong> {review_data.get('url', 'N/A')}</div>
                <div><strong>Pipeline Version:</strong> {quality_score.get('version', 'v0.1.0')}</div>
            </div>
        </section>
    </div>
</body>
</html>"""

    return html


def _render_badges(badges: dict[str, Any], review_id: str) -> str:
    """Render badge section."""
    base_url = settings.api_base_url
    badge_types = {
        "claim_mapped": "Claim-mapped",
        "method_check": "Method-check",
        "citations_augmented": "Citations-augmented",
    }

    html_parts = []
    for badge_key, badge_label in badge_types.items():
        status = badges.get(badge_key)
        if status:
            badge_url = f"{base_url}/api/v1/badges/{review_id}/{badge_key.replace('_', '-')}.svg"
            html_parts.append(
                f'<img src="{badge_url}" alt="{badge_label}" class="h-5">'
            )

    return "\n".join(html_parts) if html_parts else "<p class='text-gray-500'>No badges available</p>"


def _render_quality_score(quality_score: dict[str, Any]) -> str:
    """Render quality score section."""
    if not quality_score:
        return ""

    score = quality_score.get("value_0_100", 0)
    tier = quality_score.get("tier", "D")
    narrative = quality_score.get("narrative", {})

    # Tier colors
    tier_colors = {
        "A": "text-green-600",
        "B": "text-blue-600",
        "C": "text-yellow-600",
        "D": "text-red-600",
    }
    tier_color = tier_colors.get(tier, "text-gray-600")

    html = f"""
        <section class="mb-8 bg-white rounded-lg shadow-sm p-6">
            <h2 class="text-2xl font-semibold mb-4">Quality Score</h2>
            <div class="flex items-center gap-6 mb-6">
                <div class="text-6xl font-bold {tier_color}">{score:.1f}</div>
                <div>
                    <div class="text-2xl font-semibold {tier_color}">Tier {tier}</div>
                    <div class="text-sm text-gray-500">Out of 100</div>
                </div>
            </div>
            {_render_shap_explanation(quality_score.get('shap', []))}
            {_render_narrative(narrative)}
        </section>
    """

    return html


def _render_shap_explanation(shap_data: list[dict[str, Any]]) -> str:
    """Render SHAP explanation."""
    if not shap_data:
        return ""

    html_parts = ["<div class='mt-4'><h3 class='text-lg font-semibold mb-2'>Top Contributing Factors</h3><ul class='space-y-2'>"]

    for item in shap_data[:5]:  # Top 5
        feature = item.get("feature", "")
        phi = item.get("phi", 0)
        value = item.get("value", "")
        sign = "+" if phi > 0 else ""
        color = "text-green-600" if phi > 0 else "text-red-600"

        html_parts.append(
            f"<li class='{color}'>"
            f"<strong>{feature.replace('_', ' ').title()}:</strong> {sign}{phi:.1f} "
            f"(value: {value})"
            f"</li>"
        )

    html_parts.append("</ul></div>")
    return "\n".join(html_parts)


def _render_narrative(narrative: dict[str, Any]) -> str:
    """Render narrative section."""
    if not narrative:
        return ""

    executive = narrative.get("executive_justification", [])
    technical = narrative.get("technical_deepdive", "")

    html_parts = ["<div class='mt-6'>"]

    if executive:
        html_parts.append("<h3 class='text-lg font-semibold mb-2'>Executive Summary</h3>")
        html_parts.append("<ul class='list-disc list-inside space-y-1 text-gray-700'>")
        for bullet in executive:
            html_parts.append(f"<li>{bullet}</li>")
        html_parts.append("</ul>")

    if technical:
        html_parts.append("<h3 class='text-lg font-semibold mb-2 mt-4'>Technical Details</h3>")
        html_parts.append(f"<pre class='bg-gray-100 p-4 rounded text-sm whitespace-pre-wrap'>{technical}</pre>")

    html_parts.append("</div>")
    return "\n".join(html_parts)


def _render_claims_citations(claims: list[dict[str, Any]], citations: dict[str, list[dict[str, Any]]]) -> str:
    """Render claims and citations section."""
    html_parts = []

    for claim in claims:
        claim_id = claim.get("id", "")
        claim_text = claim.get("text", "")
        section = claim.get("section", "unknown")
        claim_citations = citations.get(claim_id, [])

        html_parts.append(
            f"""
            <div class="bg-white rounded-lg shadow-sm p-4">
                <div class="flex items-start justify-between mb-2">
                    <span class="text-xs font-medium text-gray-500 uppercase">{section}</span>
                    <span class="text-xs text-gray-400">#{claim_id}</span>
                </div>
                <p class="text-gray-900 mb-3">{claim_text}</p>
                {_render_citations_list(claim_citations)}
            </div>
            """
        )

    return "\n".join(html_parts) if html_parts else "<p class='text-gray-500'>No claims available</p>"


def _render_citations_list(citations: list[dict[str, Any]]) -> str:
    """Render citations list."""
    if not citations:
        return "<p class='text-sm text-gray-500 italic'>No citations suggested</p>"

    html_parts = ["<div class='mt-2'><h4 class='text-sm font-semibold mb-2'>Suggested Citations:</h4><ul class='space-y-1'>"]

    for cit in citations[:3]:  # Top 3
        title = cit.get("title", "Unknown")
        authors = cit.get("authors", [])
        url = cit.get("url", "")
        score = cit.get("score_final", 0)

        html_parts.append(
            f"<li class='text-sm'>"
            f"<a href='{url}' target='_blank' class='text-blue-600 hover:underline'>{title}</a> "
            f"({', '.join(authors[:2]) if authors else 'Unknown authors'}) "
            f"<span class='text-gray-500'>(score: {score:.2f})</span>"
            f"</li>"
        )

    html_parts.append("</ul></div>")
    return "\n".join(html_parts)


def _render_checklist(checklist: dict[str, Any]) -> str:
    """Render checklist section."""
    if not checklist:
        return ""

    items = checklist.get("items", [])
    if not items:
        return ""

    html_parts = [
        """
        <section class="mb-8 bg-white rounded-lg shadow-sm p-6">
            <h2 class="text-2xl font-semibold mb-4">Method Checklist</h2>
            <table class="w-full">
                <thead>
                    <tr class="border-b">
                        <th class="text-left py-2">Item</th>
                        <th class="text-left py-2">Status</th>
                        <th class="text-left py-2">Evidence</th>
                    </tr>
                </thead>
                <tbody>
        """
    ]

    for item in items:
        key = item.get("key", "")
        status = item.get("status", "missing")
        evidence = item.get("evidence", "")

        status_colors = {
            "ok": "text-green-600",
            "partial": "text-yellow-600",
            "missing": "text-red-600",
        }
        status_color = status_colors.get(status, "text-gray-600")

        html_parts.append(
            f"""
            <tr class="border-b">
                <td class="py-2">{key.replace('_', ' ').title()}</td>
                <td class="py-2"><span class="{status_color} font-medium">{status.upper()}</span></td>
                <td class="py-2 text-sm text-gray-600">{evidence or 'N/A'}</td>
            </tr>
            """
        )

    html_parts.append("</tbody></table></section>")
    return "\n".join(html_parts)


def _render_recommendations(quality_score: dict[str, Any], checklist: dict[str, Any]) -> str:
    """Render recommendations section."""
    recommendations = []

    # Check quality score
    score = quality_score.get("value_0_100", 0)
    if score < 70:
        recommendations.append("Improve evidence quality: add ablation studies, baseline comparisons, and error bars.")

    # Check checklist
    items = checklist.get("items", [])
    missing_critical = [item for item in items if item.get("status") == "missing" and item.get("key") in ["data_available", "seeds_fixed", "environment"]]
    if missing_critical:
        recommendations.append(f"Add missing critical items: {', '.join(item.get('key', '') for item in missing_critical)}.")

    if not recommendations:
        recommendations.append("Review looks good! All key reproducibility items are present.")

    html_parts = [
        """
        <section class="mb-8 bg-blue-50 rounded-lg shadow-sm p-6">
            <h2 class="text-2xl font-semibold mb-4">Recommendations</h2>
            <ul class="list-disc list-inside space-y-2 text-gray-700">
        """
    ]

    for rec in recommendations:
        html_parts.append(f"<li>{rec}</li>")

    html_parts.append("</ul></section>")
    return "\n".join(html_parts)


def _count_checklist_status(checklist: dict[str, Any], status: str) -> int:
    """Count items with specific status."""
    items = checklist.get("items", [])
    return sum(1 for item in items if item.get("status") == status)


def build_review_data(review: Any) -> dict[str, Any]:
    """
    Build complete review data dictionary from Review model.

    Args:
        review: Review SQLAlchemy model instance

    Returns:
        Complete review data dictionary
    """
    return {
        "id": str(review.id),
        "url": review.url,
        "doi": review.doi,
        "repo_url": review.repo_url,
        "status": review.status.value if hasattr(review.status, "value") else str(review.status),
        "paper_meta": review.paper_meta if hasattr(review, "paper_meta") and review.paper_meta else {
            "title": getattr(review, "paper_title", None),
            "authors": getattr(review, "paper_authors", []),
            "venue": getattr(review, "paper_venue", None),
            "published_at": getattr(review, "paper_published_at", None),
        },
        "claims": review.claims or [],
        "citations": review.citations or {},
        "checklist": review.checklist or {},
        "quality_score": review.quality_score or {},
        "badges": review.badges or {},
        "created_at": review.created_at.isoformat() if review.created_at else None,
        "updated_at": review.updated_at.isoformat() if review.updated_at else None,
    }

