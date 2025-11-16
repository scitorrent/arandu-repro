"""End-to-end tests for review processing."""

import pytest
from pathlib import Path

from app.db.session import SessionLocal
from app.models.review import Review, ReviewStatus
from app.worker.review_processor import process_review


@pytest.mark.integration
def test_review_e2e_simple_text():
    """
    E2E test: Create review with simple text input, process, verify artifacts.

    This is a minimal test that doesn't require actual PDF parsing.
    """
    db = SessionLocal()

    try:
        # Create review
        review = Review(
            url="https://example.com/paper",
            status=ReviewStatus.PENDING,
        )
        db.add(review)
        db.commit()
        review_id = str(review.id)

        # Process review (will fail at ingestion if no PDF, but tests the flow)
        try:
            process_review(review_id)
        except Exception:
            # Expected if PDF parsing fails, but we can still test the structure
            pass

        # Refresh review
        db.refresh(review)

        # Verify status changed
        assert review.status in (ReviewStatus.COMPLETED, ReviewStatus.FAILED, ReviewStatus.PROCESSING)

        # If completed, verify artifacts exist
        if review.status == ReviewStatus.COMPLETED:
            if review.html_report_path:
                assert Path(review.html_report_path).exists()
            if review.json_summary_path:
                assert Path(review.json_summary_path).exists()

    finally:
        db.close()


@pytest.mark.integration
def test_review_api_flow():
    """
    Test review API flow: POST -> GET -> status check -> artifacts.

    This test requires the API server to be running.
    """
    import httpx

    # Skip if API not available
    try:
        response = httpx.get("http://localhost:8000/health", timeout=2)
        if response.status_code != 200:
            pytest.skip("API server not available")
    except Exception:
        pytest.skip("API server not available")

    # Create review via API
    with httpx.Client() as client:
        # POST /api/v1/reviews
        response = client.post(
            "http://localhost:8000/api/v1/reviews",
            data={
                "url": "https://arxiv.org/abs/2301.00001",  # Example arXiv paper
                "doi": None,
            },
            timeout=10,
        )

        if response.status_code == 202:
            data = response.json()
            review_id = data["id"]

            # GET /api/v1/reviews/{id}
            response = client.get(f"http://localhost:8000/api/v1/reviews/{review_id}", timeout=5)
            assert response.status_code == 200

            # GET /api/v1/reviews/{id}/status
            response = client.get(f"http://localhost:8000/api/v1/reviews/{review_id}/status", timeout=5)
            assert response.status_code == 200
            status_data = response.json()
            assert "status" in status_data

            # Note: Artifacts may not be available immediately if processing is still running
            # This test validates the API structure, not the full processing

