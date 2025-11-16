"""Tests for metrics collection."""


from app.utils.metrics import ReviewMetrics, get_metrics_summary, record_review_metrics, reset_metrics


def test_record_review_metrics():
    """Test recording review metrics."""
    reset_metrics()

    metrics = ReviewMetrics(
        review_id="test-1",
        parsing_time=1.5,
        num_claims=10,
        citation_coverage=0.8,
        checklist_pass_rate=0.7,
        total_time=5.0,
    )

    record_review_metrics(metrics)

    summary = get_metrics_summary()
    assert summary["reviews"]["total"] == 1
    assert summary["reviews"]["avg_time_seconds"] == 5.0
    assert summary["citation_coverage"]["avg"] == 0.8
    assert summary["checklist_pass_rate"]["avg"] == 0.7


def test_get_metrics_summary_empty():
    """Test metrics summary when no metrics recorded."""
    reset_metrics()
    summary = get_metrics_summary()
    assert "reviews" not in summary or summary.get("reviews", {}).get("total", 0) == 0

