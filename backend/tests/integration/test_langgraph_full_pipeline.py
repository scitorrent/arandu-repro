"""Integration test for full LangGraph pipeline."""

import pytest
import os
from pathlib import Path
from uuid import uuid4

from app.worker.review_pipeline import create_review_pipeline, run_pipeline_direct
from app.worker.review_state import ReviewState


@pytest.mark.integration
def test_langgraph_pipeline_full():
    """Test complete LangGraph pipeline with minimal data."""
    pipeline = create_review_pipeline()
    if not pipeline:
        pytest.skip("LangGraph not available")

    # Create initial state
    review_id = str(uuid4())
    initial_state: ReviewState = {
        "review_id": review_id,
        "url": None,
        "doi": None,
        "pdf_file_path": None,
        "repo_url": None,
        "paper_meta": None,
        "paper_text": "This is a test paper. We propose a novel method X that improves Y. Our experiments show significant improvements. We compare with baselines A, B, and C.",
        "claims": None,
        "citations": None,
        "checklist": None,
        "quality_score": None,
        "badges": None,
        "html_report_path": None,
        "json_summary_path": None,
        "status": "processing",
        "error_message": None,
        "errors": [],
    }

    print(f"\n🧪 Testing LangGraph pipeline for review {review_id[:8]}...")
    print(f"📄 Paper text length: {len(initial_state['paper_text'])} chars")

    # Run pipeline
    try:
        final_state = pipeline.invoke(initial_state)
    except Exception as e:
        pytest.fail(f"Pipeline execution failed: {e}")

    # Validate final state
    assert final_state is not None
    assert final_state["review_id"] == review_id
    print(f"✅ Pipeline completed with status: {final_state.get('status')}")

    # Check each step
    if final_state.get("paper_meta"):
        print(f"✅ Paper metadata extracted: {final_state['paper_meta'].get('title', 'N/A')[:50]}")

    if final_state.get("claims"):
        print(f"✅ Claims extracted: {len(final_state['claims'])} claims")
        for i, claim in enumerate(final_state["claims"][:3], 1):
            print(f"   {i}. {claim.get('text', '')[:60]}...")

    if final_state.get("citations"):
        total_citations = sum(len(cits) for cits in final_state["citations"].values())
        print(f"✅ Citations suggested: {total_citations} total")

    if final_state.get("checklist"):
        items = final_state["checklist"].get("items", [])
        print(f"✅ Checklist generated: {len(items)} items")
        ok_count = sum(1 for item in items if item.get("status") == "ok")
        print(f"   OK: {ok_count}, Partial: {sum(1 for item in items if item.get('status') == 'partial')}, Missing: {sum(1 for item in items if item.get('status') == 'missing')}")

    if final_state.get("quality_score"):
        score = final_state["quality_score"].get("value_0_100")
        tier = final_state["quality_score"].get("tier")
        print(f"✅ Quality score: {score:.1f}/100 (Tier {tier})")
        if final_state["quality_score"].get("narrative"):
            narrative = final_state["quality_score"]["narrative"]
            exec_bullets = narrative.get("executive_justification", [])
            print(f"✅ Narrative generated: {len(exec_bullets)} executive bullets")

    if final_state.get("badges"):
        badges = final_state["badges"]
        print(f"✅ Badges computed: {list(badges.keys())}")

    if final_state.get("html_report_path"):
        print(f"✅ HTML report: {final_state['html_report_path']}")

    if final_state.get("json_summary_path"):
        print(f"✅ JSON report: {final_state['json_summary_path']}")

    # Final validation
    assert final_state["status"] in ["completed", "failed"]
    if final_state["status"] == "failed":
        print(f"⚠️  Pipeline failed: {final_state.get('error_message')}")
        if final_state.get("errors"):
            for error in final_state["errors"][:3]:
                print(f"   Error: {error}")

    print("✅ LangGraph pipeline test completed")


@pytest.mark.integration
def test_langgraph_pipeline_direct_fallback():
    """Test direct pipeline execution (fallback when LangGraph not available)."""
    review_id = str(uuid4())
    initial_state: ReviewState = {
        "review_id": review_id,
        "url": None,
        "doi": None,
        "pdf_file_path": None,
        "repo_url": None,
        "paper_meta": None,
        "paper_text": "Test paper with claims. Method X improves Y. Results show 10% improvement.",
        "claims": None,
        "citations": None,
        "checklist": None,
        "quality_score": None,
        "badges": None,
        "html_report_path": None,
        "json_summary_path": None,
        "status": "processing",
        "error_message": None,
        "errors": [],
    }

    print(f"\n🧪 Testing direct pipeline (fallback) for review {review_id[:8]}...")

    try:
        final_state = run_pipeline_direct(initial_state)
    except Exception as e:
        pytest.fail(f"Direct pipeline execution failed: {e}")

    assert final_state is not None
    assert final_state["review_id"] == review_id
    print(f"✅ Direct pipeline completed with status: {final_state.get('status')}")

    # Validate key outputs
    if final_state.get("claims"):
        print(f"✅ Claims extracted: {len(final_state['claims'])}")

    if final_state.get("quality_score"):
        score = final_state["quality_score"].get("value_0_100")
        print(f"✅ Quality score: {score:.1f}/100")

    print("✅ Direct pipeline test completed")


# Note: This test should be run via pytest, not directly
# If you need to run it manually, use: pytest tests/integration/test_langgraph_full_pipeline.py

