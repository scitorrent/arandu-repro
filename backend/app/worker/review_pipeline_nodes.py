"""LangGraph pipeline nodes for review processing."""

import logging
from pathlib import Path

from app.config import settings
from app.worker.badge_generator import compute_badge_status
from app.worker.checklist_generator import checklist_to_json, generate_checklist
from app.worker.claim_extractor import Claim, claims_to_json, extract_claims_by_section
from app.worker.citation_suggester import suggest_citations_for_claims
from app.worker.quality.feature_builder import build_features, features_to_dict
from app.worker.quality.predictor import predict_quality_score
from app.worker.quality.score_narrator import generate_narrative
from app.worker.quality.shap_explainer import explain_with_shap, shap_to_json
from app.worker.report_builder import build_review_data, generate_html_report, generate_json_report
from app.worker.review_ingestion import ingest_paper
from app.worker.review_state import ReviewState

logger = logging.getLogger(__name__)


def ingestion_node(state: ReviewState) -> ReviewState:
    """
    Ingestion node: PDF/URL parsing, metadata extraction.

    If paper_text is already provided, skip ingestion and just set metadata.

    Args:
        state: Review state

    Returns:
        Updated state with paper_meta and paper_text
    """
    try:
        logger.info(f"Ingestion node: processing review {state['review_id']}")

        # If paper_text is already provided, skip ingestion
        if state.get("paper_text") and not (state.get("url") or state.get("doi") or state.get("pdf_file_path")):
            logger.info("Paper text already provided, skipping ingestion")
            # Set minimal metadata if not present
            if not state.get("paper_meta"):
                return {
                    "paper_meta": {
                        "title": "Test Paper",
                        "authors": [],
                        "venue": "Test",
                        "published_at": None,
                    },
                    "status": "processing",
                }
            return {"status": "processing"}

        # Otherwise, try to ingest from URL/DOI/PDF
        paper_meta = ingest_paper(
            url=state.get("url"),
            doi=state.get("doi"),
            pdf_path=state.get("pdf_file_path"),
        )

        state["paper_meta"] = {
            "title": paper_meta.title,
            "authors": paper_meta.authors,
            "venue": paper_meta.venue,
            "published_at": paper_meta.published_at,
        }
        state["paper_text"] = paper_meta.text
        state["status"] = "processing"

        logger.info(f"Ingestion completed: {len(paper_meta.text)} characters extracted")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        # If paper_text is available, continue anyway
        if state.get("paper_text"):
            logger.warning("Ingestion failed but paper_text available, continuing")
            if not state.get("paper_meta"):
                return {
                    "paper_meta": {
                        "title": "Unknown",
                        "authors": [],
                        "venue": "Unknown",
                        "published_at": None,
                    },
                    "status": "processing",
                }
            return {"status": "processing"}
        else:
            return {
                "status": "failed",
                "error_message": f"Ingestion failed: {str(e)}",
                "errors": [{"step": "ingestion", "message": str(e)}],
            }

    return {}


def claim_extraction_node(state: ReviewState) -> ReviewState:
    """
    Claim extraction node: extract claims from paper text.

    Args:
        state: Review state

    Returns:
        Updated state with claims
    """
    try:
        logger.info(f"Claim extraction node: processing review {state['review_id']}")

        paper_text = state.get("paper_text")
        if not paper_text:
            logger.warning("Paper text not available for claim extraction")
            return {"claims": []}

        claims = extract_claims_by_section(paper_text)
        claims_json = claims_to_json(claims)

        logger.info(f"Claim extraction completed: {len(claims)} claims extracted")
        return {"claims": claims_json}
    except Exception as e:
        logger.error(f"Claim extraction failed: {e}")
        # Don't fail completely, continue with empty claims
        return {
            "claims": [],
            "errors": [{"step": "claim_extraction", "message": str(e)}],
        }


def citation_suggestion_node(state: ReviewState) -> ReviewState:
    """
    Citation suggestion node: suggest citations for claims.

    Args:
        state: Review state

    Returns:
        Updated state with citations
    """
    try:
        logger.info(f"Citation suggestion node: processing review {state['review_id']}")

        if not state.get("claims"):
            logger.warning("No claims available for citation suggestion")
            return {"citations": {}}

        # Convert claims JSON back to Claim objects
        claim_objects = [
            Claim(
                id=c["id"],
                text=c["text"],
                section=c.get("section"),
                spans=c.get("spans", []),
                confidence=c.get("confidence", 0.0),
            )
            for c in state["claims"]
        ]

        citations_by_claim = suggest_citations_for_claims(
            claim_objects,
            state.get("paper_text", ""),
            paper_meta=state.get("paper_meta"),
        )

        # Convert to JSON-serializable format
        citations_json = {}
        for claim_id, citations in citations_by_claim.items():
            citations_json[claim_id] = [
                {
                    "title": cit.title,
                    "authors": cit.authors,
                    "venue": cit.venue,
                    "year": cit.year,
                    "doi": cit.doi,
                    "url": cit.url,
                    "score_final": cit.score_final,
                    "score_rerank": cit.score_rerank,
                    "justification": cit.justification,
                }
                for cit in citations
            ]

        logger.info(f"Citation suggestion completed: {len(citations_by_claim)} claims with citations")
        return {"citations": citations_json}
    except Exception as e:
        logger.error(f"Citation suggestion failed: {e}")
        return {
            "citations": {},
            "errors": [{"step": "citation_suggestion", "message": str(e)}],
        }


def checklist_generation_node(state: ReviewState) -> ReviewState:
    """
    Checklist generation node: generate method checklist.

    Args:
        state: Review state

    Returns:
        Updated state with checklist
    """
    try:
        logger.info(f"Checklist generation node: processing review {state['review_id']}")

        if not state.get("paper_text"):
            logger.warning("No paper text available for checklist")
            return {"checklist": {"items": [], "summary": "No data available"}}

        # Get repo path if available
        repo_path = None
        if state.get("repo_url"):
            # TODO: Clone repo if needed (reuse repo_cloner from Sprint 1)
            pass

        # Convert claims JSON to Claim objects if available
        claim_objects = []
        if state.get("claims"):
            claim_objects = [
                Claim(
                    id=c["id"],
                    text=c["text"],
                    section=c.get("section"),
                    spans=c.get("spans", []),
                    confidence=c.get("confidence", 0.0),
                )
                for c in state["claims"]
            ]

        checklist = generate_checklist(
            state["paper_text"],
            claim_objects,
            repo_path=repo_path,
        )

        checklist_json = checklist_to_json(checklist)

        logger.info(f"Checklist generation completed: {checklist.summary}")
        return {"checklist": checklist_json}
    except Exception as e:
        logger.error(f"Checklist generation failed: {e}")
        return {
            "checklist": {"items": [], "summary": "Generation failed"},
            "errors": [{"step": "checklist_generation", "message": str(e)}],
        }


def quality_score_node(state: ReviewState) -> ReviewState:
    """
    Quality score node: compute quality score with SHAP.

    Args:
        state: Review state

    Returns:
        Updated state with quality_score
    """
    try:
        logger.info(f"Quality score node: processing review {state['review_id']}")

        # Convert claims JSON to Claim objects
        claim_objects = []
        if state.get("claims"):
            claim_objects = [
                Claim(
                    id=c["id"],
                    text=c["text"],
                    section=c.get("section"),
                    spans=c.get("spans", []),
                    confidence=c.get("confidence", 0.0),
                )
                for c in state["claims"]
            ]

        # Build features
        from app.worker.checklist_generator import Checklist, ChecklistItem

        checklist_items = state.get("checklist", {}).get("items", [])
        checklist_obj = Checklist(
            items=[
                ChecklistItem(
                    key=item.get("key", ""),
                    status=item.get("status", "missing"),
                    evidence=item.get("evidence"),
                    source=item.get("source", "paper"),
                )
                for item in checklist_items
            ],
            summary=state.get("checklist", {}).get("summary", ""),
        )

        features_obj = build_features(
            claim_objects,
            state.get("paper_text", ""),
            checklist_obj,
            state.get("citations"),
            repo_path=None,  # TODO: Get repo path if available
        )

        features_dict = features_to_dict(features_obj)

        # Predict score
        score_result = predict_quality_score(features_dict)

        # Generate SHAP explanations
        shap_explanations = explain_with_shap(features_dict, score_result["score"])

        # Generate narrative
        narrative = generate_narrative(
            score_result["score"],
            score_result["tier"],
            shap_to_json(shap_explanations),
            state.get("checklist", {}),
            state.get("claims", []),
            paper_meta=state.get("paper_meta"),
        )

        logger.info(f"Quality score completed: {score_result['score']:.1f} (Tier {score_result['tier']})")
        return {
            "quality_score": {
                "value_0_100": score_result["score"],
                "tier": score_result["tier"],
                "version": score_result["version"],
                "model_type": score_result["model_type"],
                "features": features_dict,
                "shap": shap_to_json(shap_explanations),
                "narrative": narrative,
            }
        }
    except Exception as e:
        logger.error(f"Quality score failed: {e}")
        return {
            "errors": [{"step": "quality_score", "message": str(e)}],
        }


def badge_generation_node(state: ReviewState) -> ReviewState:
    """
    Badge generation node: compute badge statuses.

    Args:
        state: Review state

    Returns:
        Updated state with badges
    """
    try:
        logger.info(f"Badge generation node: processing review {state['review_id']}")

        review_data = {
            "id": state["review_id"],
            "claims": state.get("claims", []),
            "checklist": state.get("checklist", {}),
            "citations": state.get("citations", {}),
        }

        badges_status = {
            "claim_mapped": compute_badge_status("claim-mapped", review_data),
            "method_check": compute_badge_status("method-check", review_data),
            "citations_augmented": compute_badge_status("citations-augmented", review_data),
        }

        logger.info(f"Badge generation completed: {badges_status}")
        return {"badges": badges_status}
    except Exception as e:
        logger.error(f"Badge generation failed: {e}")
        return {
            "badges": {},
            "errors": [{"step": "badge_generation", "message": str(e)}],
        }


def report_generation_node(state: ReviewState) -> ReviewState:
    """
    Report generation node: generate HTML and JSON reports.

    Args:
        state: Review state

    Returns:
        Updated state with report paths
    """
    try:
        logger.info(f"Report generation node: processing review {state['review_id']}")

        # Build review data for reports
        # Create a mock review object for build_review_data
        class MockReview:
            def __init__(self, state: ReviewState):
                self.id = state["review_id"]
                self.url = state.get("url")
                self.doi = state.get("doi")
                self.repo_url = state.get("repo_url")
                self.status = type("Status", (), {"value": state.get("status", "completed")})()
                self.paper_meta = state.get("paper_meta")
                self.claims = state.get("claims")
                self.citations = state.get("citations")
                self.checklist = state.get("checklist")
                self.quality_score = state.get("quality_score")
                self.badges = state.get("badges")
                from datetime import datetime, UTC
                self.created_at = datetime.now(UTC)
                self.updated_at = datetime.now(UTC)

        mock_review = MockReview(state)
        review_data = build_review_data(mock_review)

        # Generate reports
        reports_dir = Path(settings.reviews_base_path) / state["review_id"]
        reports_dir.mkdir(parents=True, exist_ok=True)

        html_path = reports_dir / "report.html"
        json_path = reports_dir / "review.json"

        generate_html_report(review_data, html_path)
        generate_json_report(review_data, json_path)

        logger.info("Report generation completed")
        return {
            "html_report_path": str(html_path),
            "json_summary_path": str(json_path),
            "status": "completed",
        }
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return {
            "status": "failed",
            "error_message": f"Report generation failed: {str(e)}",
            "errors": [{"step": "report_generation", "message": str(e)}],
        }

