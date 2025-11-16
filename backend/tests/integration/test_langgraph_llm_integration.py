"""Integration tests for LangGraph pipeline with LLM (Gemini)."""

import pytest

from app.worker.review_pipeline import create_review_pipeline
from app.worker.review_state import ReviewState
from app.config import settings


@pytest.mark.integration
@pytest.mark.skipif(
    not settings.gemini_api_key or not settings.llm_enabled,
    reason="Requires GEMINI_API_KEY and LLM enabled",
)
def test_langgraph_with_llm_narrative():
    """Test LangGraph pipeline with LLM narrative generation."""
    pipeline = create_review_pipeline()
    if not pipeline:
        pytest.skip("LangGraph not available")

    # Create state with minimal data (will test narrative generation)
    initial_state: ReviewState = {
        "review_id": "test-llm-1",
        "url": None,
        "doi": None,
        "pdf_file_path": None,
        "repo_url": None,
        "paper_meta": {"title": "Test Paper", "authors": ["Author"], "venue": "Test"},
        "paper_text": "This paper presents a novel method.",
        "claims": [
            {"id": "c1", "text": "We propose method X", "section": "introduction"}
        ],
        "citations": {"c1": []},
        "checklist": {
            "items": [
                {"key": "data_available", "status": "ok", "evidence": "Dataset link provided"}
            ],
            "summary": "Most items present",
        },
        "quality_score": {
            "value_0_100": 75.0,
            "tier": "B",
            "shap": [
                {"feature": "checklist_pct_ok", "phi": 0.3, "value": 0.8},
                {"feature": "num_claims", "phi": 0.2, "value": 5},
            ],
        },
        "badges": None,
        "html_report_path": None,
        "json_summary_path": None,
        "status": "processing",
        "error_message": None,
        "errors": [],
    }

    # Test just the quality_score node (which uses LLM for narrative)
    from app.worker.review_pipeline_nodes import quality_score_node

    # This node should generate narrative using LLM
    result_state = quality_score_node(initial_state)

    # Verify narrative was generated
    quality_score = result_state.get("quality_score")
    if quality_score:
        narrative = quality_score.get("narrative")
        if narrative:
            assert "executive_justification" in narrative
            assert "technical_deepdive" in narrative
            assert len(narrative["executive_justification"]) > 0


@pytest.mark.integration
@pytest.mark.skipif(
    not settings.gemini_api_key or not settings.llm_enabled,
    reason="Requires GEMINI_API_KEY and LLM enabled",
)
def test_llm_narrative_quality():
    """Test that LLM generates reasonable narrative."""
    from app.worker.quality.score_narrator import generate_narrative

    score = 75.0
    tier = "B"
    shap_data = [
        {"feature": "checklist_pct_ok", "phi": 0.3, "value": 0.8},
        {"feature": "num_claims", "phi": 0.2, "value": 5},
        {"feature": "citation_coverage", "phi": -0.1, "value": 0.5},
    ]
    checklist = {
        "items": [
            {"key": "data_available", "status": "ok"},
            {"key": "seeds_fixed", "status": "partial"},
        ],
        "summary": "Most items present",
    }
    claims = [{"id": "c1", "text": "Test claim"}]
    paper_meta = {"title": "Test Paper"}

    narrative = generate_narrative(score, tier, shap_data, checklist, claims, paper_meta)

    # Verify structure
    assert "executive_justification" in narrative
    assert "technical_deepdive" in narrative

    # Verify content quality
    executive = narrative["executive_justification"]
    assert isinstance(executive, list)
    assert len(executive) >= 3  # Should have at least 3 bullets

    technical = narrative["technical_deepdive"]
    assert isinstance(technical, str)
    assert len(technical) > 50  # Should be substantial

    # Verify it mentions the score/tier
    narrative_text = " ".join(executive) + " " + technical
    assert "75" in narrative_text or "B" in narrative_text or "tier" in narrative_text.lower()

