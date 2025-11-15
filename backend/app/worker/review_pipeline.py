"""LangGraph pipeline for review processing."""

import logging
from typing import Any

from app.worker.review_state import ReviewState

logger = logging.getLogger(__name__)

# Try to import LangGraph, but allow graceful degradation
try:
    from langgraph.graph import END, START, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("LangGraph not available, pipeline will use direct function calls")


def create_review_pipeline():
    """
    Create LangGraph pipeline for review processing.

    Returns:
        Compiled LangGraph graph or None if LangGraph not available
    """
    if not LANGGRAPH_AVAILABLE:
        logger.warning("LangGraph not available, returning None")
        return None

    # Import node functions
    from app.worker.review_pipeline_nodes import (
        badge_generation_node,
        checklist_generation_node,
        claim_extraction_node,
        citation_suggestion_node,
        ingestion_node,
        quality_score_node,
        report_generation_node,
    )

    # Create graph
    workflow = StateGraph(ReviewState)

    # Add nodes
    workflow.add_node("ingestion", ingestion_node)
    workflow.add_node("claim_extraction", claim_extraction_node)
    workflow.add_node("citation_suggestion", citation_suggestion_node)
    workflow.add_node("checklist_generation", checklist_generation_node)
    workflow.add_node("quality_score", quality_score_node)
    workflow.add_node("badge_generation", badge_generation_node)
    workflow.add_node("report_generation", report_generation_node)

    # Add edges (define execution flow)
    workflow.set_entry_point("ingestion")
    workflow.add_edge("ingestion", "claim_extraction")
    # Both citation_suggestion and checklist_generation can run in parallel after claim_extraction
    workflow.add_edge("claim_extraction", "citation_suggestion")
    workflow.add_edge("claim_extraction", "checklist_generation")
    # Quality score needs both citations and checklist
    workflow.add_edge("citation_suggestion", "quality_score")
    workflow.add_edge("checklist_generation", "quality_score")
    # Sequential: quality_score → badge_generation → report_generation
    workflow.add_edge("quality_score", "badge_generation")
    workflow.add_edge("badge_generation", "report_generation")
    workflow.add_edge("report_generation", END)

    # Compile graph
    return workflow.compile()


def run_pipeline_direct(state: ReviewState) -> ReviewState:
    """
    Run pipeline using direct function calls (fallback when LangGraph not available).

    This maintains the same interface as LangGraph but uses sequential calls.

    Args:
        state: Initial review state

    Returns:
        Final review state
    """
    from app.worker.review_pipeline_nodes import (
        badge_generation_node,
        checklist_generation_node,
        claim_extraction_node,
        citation_suggestion_node,
        ingestion_node,
        quality_score_node,
        report_generation_node,
    )

    # Sequential execution (same order as LangGraph edges)
    state = ingestion_node(state)
    state = claim_extraction_node(state)
    state = citation_suggestion_node(state)
    state = checklist_generation_node(state)
    state = quality_score_node(state)
    state = badge_generation_node(state)
    state = report_generation_node(state)

    return state

