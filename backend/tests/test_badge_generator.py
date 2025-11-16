"""Tests for badge generator."""


from app.worker.badge_generator import (
    compute_badge_status,
    generate_badge_svg,
    get_badge_snippet,
)


def test_compute_badge_status_claim_mapped():
    """Test claim-mapped badge status."""
    review_data = {
        "claims": [{"id": f"c{i}"} for i in range(5)],
    }
    status = compute_badge_status("claim-mapped", review_data)
    assert status is True

    review_data_few = {
        "claims": [{"id": "c1"}],
    }
    status_few = compute_badge_status("claim-mapped", review_data_few)
    assert status_few is False


def test_compute_badge_status_method_check():
    """Test method-check badge status."""
    review_data_ok = {
        "checklist": {
            "items": [
                {"key": "data_available", "status": "ok"},
                {"key": "seeds_fixed", "status": "ok"},
            ],
        },
    }
    status = compute_badge_status("method-check", review_data_ok)
    assert status == "ok"

    review_data_partial = {
        "checklist": {
            "items": [
                {"key": "data_available", "status": "ok"},
                {"key": "seeds_fixed", "status": "partial"},
            ],
        },
    }
    status = compute_badge_status("method-check", review_data_partial)
    assert status in ("ok", "partial")

    review_data_fail = {
        "checklist": {
            "items": [
                {"key": "data_available", "status": "missing"},
                {"key": "seeds_fixed", "status": "missing"},
            ],
        },
    }
    status = compute_badge_status("method-check", review_data_fail)
    assert status == "fail"


def test_compute_badge_status_citations_augmented():
    """Test citations-augmented badge status."""
    review_data = {
        "claims": [{"id": "c1"}, {"id": "c2"}, {"id": "c3"}],
        "citations": {
            "c1": [{"title": "Paper 1"}],
            "c2": [{"title": "Paper 2"}],
            "c3": [{"title": "Paper 3"}],
        },
    }
    status = compute_badge_status("citations-augmented", review_data)
    assert status is True

    review_data_low = {
        "claims": [{"id": "c1"}, {"id": "c2"}, {"id": "c3"}],
        "citations": {
            "c1": [{"title": "Paper 1"}],
        },
    }
    status = compute_badge_status("citations-augmented", review_data_low)
    assert status is False


def test_generate_badge_svg():
    """Test SVG badge generation."""
    svg = generate_badge_svg("claim-mapped", True, "test-id")
    assert "svg" in svg.lower()
    assert "claim-mapped" in svg.lower()
    assert "#10B981" in svg  # Green color


def test_get_badge_snippet():
    """Test badge snippet generation."""
    snippet = get_badge_snippet("claim-mapped", "test-id")
    assert "[![Arandu:" in snippet
    assert "claim-mapped" in snippet
    assert ".svg" in snippet

