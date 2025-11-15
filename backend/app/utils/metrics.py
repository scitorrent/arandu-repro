"""Metrics collection for reviews."""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# In-memory metrics store (in production, use Prometheus/StatsD)
_metrics: dict[str, Any] = defaultdict(lambda: {
    "count": 0,
    "total_time": 0.0,
    "errors": 0,
    "last_updated": None,
})


@dataclass
class ReviewMetrics:
    """Metrics for a single review processing."""

    review_id: str
    parsing_time: float = 0.0
    num_claims: int = 0
    citation_coverage: float = 0.0
    checklist_pass_rate: float = 0.0
    total_time: float = 0.0
    errors: list[str] = field(default_factory=list)
    step_times: dict[str, float] = field(default_factory=dict)


def record_step_time(step: str, duration: float):
    """
    Record time for a processing step.

    Args:
        step: Step name (e.g., "ingestion", "claim_extraction")
        duration: Duration in seconds
    """
    _metrics[f"step_{step}"]["count"] += 1
    _metrics[f"step_{step}"]["total_time"] += duration
    _metrics[f"step_{step}"]["last_updated"] = time.time()


def record_review_metrics(metrics: ReviewMetrics):
    """
    Record metrics for a completed review.

    Args:
        metrics: ReviewMetrics object
    """
    # Overall review metrics
    _metrics["reviews_total"]["count"] += 1
    _metrics["reviews_total"]["total_time"] += metrics.total_time
    if metrics.errors:
        _metrics["reviews_total"]["errors"] += 1
    _metrics["reviews_total"]["last_updated"] = time.time()

    # Claims metrics
    _metrics["claims_avg"]["count"] += metrics.num_claims
    _metrics["claims_avg"]["last_updated"] = time.time()

    # Citation coverage
    _metrics["citation_coverage_avg"]["count"] += 1
    _metrics["citation_coverage_avg"]["total_time"] += metrics.citation_coverage
    _metrics["citation_coverage_avg"]["last_updated"] = time.time()

    # Checklist pass rate
    _metrics["checklist_pass_rate_avg"]["count"] += 1
    _metrics["checklist_pass_rate_avg"]["total_time"] += metrics.checklist_pass_rate
    _metrics["checklist_pass_rate_avg"]["last_updated"] = time.time()


def get_metrics_summary() -> dict[str, Any]:
    """
    Get summary of all metrics.

    Returns:
        Dictionary with aggregated metrics
    """
    summary: dict[str, Any] = {}

    # Overall reviews
    reviews_total = _metrics["reviews_total"]
    if reviews_total["count"] > 0:
        summary["reviews"] = {
            "total": reviews_total["count"],
            "avg_time_seconds": reviews_total["total_time"] / reviews_total["count"],
            "error_rate": reviews_total["errors"] / reviews_total["count"],
        }

    # Claims average
    claims_avg = _metrics["claims_avg"]
    if claims_avg["count"] > 0:
        summary["claims"] = {
            "avg_per_review": claims_avg["count"] / _metrics["reviews_total"]["count"]
            if _metrics["reviews_total"]["count"] > 0
            else 0,
        }

    # Citation coverage
    citation_avg = _metrics["citation_coverage_avg"]
    if citation_avg["count"] > 0:
        summary["citation_coverage"] = {
            "avg": citation_avg["total_time"] / citation_avg["count"],
        }

    # Checklist pass rate
    checklist_avg = _metrics["checklist_pass_rate_avg"]
    if checklist_avg["count"] > 0:
        summary["checklist_pass_rate"] = {
            "avg": checklist_avg["total_time"] / checklist_avg["count"],
        }

    # Step times
    step_metrics = {}
    for key, value in _metrics.items():
        if key.startswith("step_") and value["count"] > 0:
            step_name = key.replace("step_", "")
            step_metrics[step_name] = {
                "avg_time_seconds": value["total_time"] / value["count"],
                "count": value["count"],
            }
    if step_metrics:
        summary["steps"] = step_metrics

    return summary


def reset_metrics():
    """Reset all metrics (for testing)."""
    global _metrics
    _metrics.clear()

