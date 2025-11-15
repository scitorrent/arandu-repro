"""Badge generator for reviews."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def generate_badge_svg(
    badge_type: str,
    status: str | bool,
    review_id: str,
    base_url: str = "http://localhost:8000",
) -> str:
    """
    Generate SVG badge for a review.

    Args:
        badge_type: Type of badge (claim-mapped, method-check, citations-augmented)
        status: Status (ok/partial/fail) or boolean
        review_id: Review ID
        base_url: Base URL for badge link

    Returns:
        SVG content as string
    """
    # Determine badge color and text
    if badge_type == "claim-mapped":
        if isinstance(status, bool) and status:
            color = "#10B981"  # Green
            text = "Claim-mapped"
        else:
            color = "#9CA3AF"  # Gray
            text = "Not mapped"
    elif badge_type == "method-check":
        if status == "ok":
            color = "#10B981"  # Green
            text = "Method-check: OK"
        elif status == "partial":
            color = "#F59E0B"  # Amber
            text = "Method-check: Partial"
        else:
            color = "#EF4444"  # Red
            text = "Method-check: Fail"
    elif badge_type == "citations-augmented":
        if isinstance(status, bool) and status:
            color = "#10B981"  # Green
            text = "Citations-augmented"
        else:
            color = "#9CA3AF"  # Gray
            text = "No citations"
    else:
        color = "#9CA3AF"
        text = "Unknown"

    # SVG template (shields.io style)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="150" height="20" role="img" aria-label="{text}">
  <title>{text}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="150" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="150" height="20" fill="#555"/>
    <rect x="0" width="150" height="20" fill="{color}"/>
    <rect width="150" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="11">
    <text x="75" y="14" fill="#010101" fill-opacity=".3">{text}</text>
    <text x="75" y="13">{text}</text>
  </g>
</svg>'''

    return svg


def compute_badge_status(
    badge_type: str,
    review_data: dict[str, Any],
) -> str | bool:
    """
    Compute badge status from review data.

    Args:
        badge_type: Type of badge
        review_data: Review data dictionary

    Returns:
        Status (ok/partial/fail) or boolean
    """
    if badge_type == "claim-mapped":
        claims = review_data.get("claims", [])
        return len(claims) >= 5

    elif badge_type == "method-check":
        checklist = review_data.get("checklist", {})
        items = checklist.get("items", [])
        if not items:
            return "fail"

        ok_count = sum(1 for item in items if item.get("status") == "ok")
        partial_count = sum(1 for item in items if item.get("status") == "partial")
        total = len(items)

        if ok_count == total:
            return "ok"
        elif ok_count + partial_count >= total * 0.7:  # 70% OK or partial
            return "partial"
        else:
            return "fail"

    elif badge_type == "citations-augmented":
        citations = review_data.get("citations", {})
        claims = review_data.get("claims", [])

        if not claims:
            return False

        # Count claims with at least one citation
        claims_with_cites = sum(
            1 for claim in claims if citations.get(claim.get("id", ""), [])
        )
        coverage = claims_with_cites / len(claims) if claims else 0.0

        return coverage >= 0.7  # 70% coverage

    return False


def generate_badges(review_data: dict[str, Any], base_url: str = "http://localhost:8000") -> dict[str, str]:
    """
    Generate all badges for a review.

    Args:
        review_data: Review data dictionary
        base_url: Base URL for badge links

    Returns:
        Dictionary mapping badge_type to SVG content
    """
    badges = {}

    badge_types = ["claim-mapped", "method-check", "citations-augmented"]
    for badge_type in badge_types:
        status = compute_badge_status(badge_type, review_data)
        review_id = review_data.get("id", "unknown")
        svg = generate_badge_svg(badge_type, status, review_id, base_url)
        badges[badge_type] = svg

    return badges


def get_badge_snippet(
    badge_type: str,
    review_id: str,
    base_url: str = "http://localhost:8000",
) -> str:
    """
    Generate markdown snippet for badge.

    Args:
        badge_type: Type of badge
        review_id: Review ID
        base_url: Base URL

    Returns:
        Markdown snippet
    """
    badge_url = f"{base_url}/api/v1/badges/{review_id}/{badge_type}.svg"
    review_url = f"{base_url}/reviews/{review_id}"

    return f"[![Arandu: {badge_type}]({badge_url})]({review_url})"

