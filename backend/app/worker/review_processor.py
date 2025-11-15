"""Review processing pipeline."""

import logging
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.review import Review, ReviewStatus
from app.utils.logging import log_event, log_step
from app.worker.claim_extractor import claims_to_json, extract_claims_by_section
from app.worker.review_ingestion import ingest_paper

logger = logging.getLogger(__name__)


def process_review(review_id: str) -> None:
    """
    Process a review through the full pipeline.

    Pipeline:
    1. Ingestion (PDF/URL parsing, metadata extraction)
    2. Claim extraction
    3. Citation suggestion (RAG)
    4. Method checklist
    5. Quality score + SHAP
    6. Badge generation
    7. Report generation (HTML + JSON)
    """
    db: Session = SessionLocal()
    review_uuid = UUID(review_id) if isinstance(review_id, str) else review_id

    # Get review from database
    review = db.query(Review).filter(Review.id == review_uuid).first()
    if not review:
        log_event(
            logging.ERROR,
            "Review not found",
            job_id=review_id,
            step="process_review",
            event="review_not_found",
            status="not_found",
        )
        return

    # Update status to processing
    review.status = ReviewStatus.PROCESSING
    db.commit()

    try:
        with log_step(review_id, "process_review", review_id=review_id):
            # Step 1: Ingestion (PDF/URL parsing, metadata extraction)
            with log_step(review_id, "ingestion", review_id=review_id):
                paper_meta = ingest_paper(
                    url=review.url,
                    doi=review.doi,
                    pdf_path=review.pdf_file_path,
                )

                # Update review with metadata and text
                review.paper_meta = {
                    "title": paper_meta.title,
                    "authors": paper_meta.authors,
                    "venue": paper_meta.venue,
                    "published_at": paper_meta.published_at,
                }
                review.paper_text = paper_meta.text
                db.commit()

                log_event(
                    logging.INFO,
                    "Paper ingested",
                    job_id=review_id,
                    step="ingestion",
                    event="ingestion_completed",
                    status="processing",
                )

            # Step 2: Claim extraction
            with log_step(review_id, "claim_extraction", review_id=review_id):
                claims = extract_claims_by_section(paper_meta.text)
                claims_json = claims_to_json(claims)

                review.claims = claims_json
                db.commit()

                log_event(
                    logging.INFO,
                    f"Extracted {len(claims)} claims",
                    job_id=review_id,
                    step="claim_extraction",
                    event="claims_extracted",
                    status="processing",
                )

            # Step 3: Citation suggestion (RAG)
            with log_step(review_id, "citation_suggestion", review_id=review_id):
                if review.claims:
                    # Convert claims JSON back to Claim objects for processing
                    claim_objects = [
                        Claim(
                            id=c["id"],
                            text=c["text"],
                            section=c.get("section"),
                            spans=c.get("spans", []),
                            confidence=c.get("confidence", 0.0),
                        )
                        for c in review.claims
                    ]

                    citations_by_claim = suggest_citations_for_claims(
                        claim_objects,
                        paper_meta.text,
                        paper_meta={
                            "title": paper_meta.title,
                            "authors": paper_meta.authors,
                            "venue": paper_meta.venue,
                        },
                    )

                    # Convert to JSON-serializable format
                    citations_json = {
                        claim_id: [
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
                        for claim_id, citations in citations_by_claim.items()
                    }

                    review.citations = citations_json
                    db.commit()

                    log_event(
                        logging.INFO,
                        f"Suggested citations for {len(claim_objects)} claims",
                        job_id=review_id,
                        step="citation_suggestion",
                        event="citations_suggested",
                        status="processing",
                    )

            # Step 4: Method checklist
            with log_step(review_id, "checklist_generation", review_id=review_id):
                # Get repo path if available
                repo_path = None
                if review.repo_url:
                    # TODO: Clone repo if needed (reuse repo_cloner from Sprint 1)
                    # For now, checklist will work with paper text only
                    pass

                checklist = generate_checklist(
                    paper_meta.text,
                    claim_objects if review.claims else [],
                    repo_path=repo_path,
                )

                checklist_json = checklist_to_json(checklist)
                review.checklist = checklist_json
                db.commit()

                log_event(
                    logging.INFO,
                    f"Generated checklist: {checklist.summary}",
                    job_id=review_id,
                    step="checklist_generation",
                    event="checklist_generated",
                    status="processing",
                )

            # Step 5: Quality Score + SHAP
            with log_step(review_id, "quality_score", review_id=review_id):
                # Build features
                features_obj = build_features(
                    claim_objects if review.claims else [],
                    paper_meta.text,
                    checklist,
                    citations_by_claim if review.citations else None,
                    repo_path=repo_path,
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
                    checklist_json,
                    review.claims or [],
                    paper_meta={
                        "title": paper_meta.title,
                        "authors": paper_meta.authors,
                        "venue": paper_meta.venue,
                    },
                )

                # Store quality score
                review.quality_score = {
                    "value_0_100": score_result["score"],
                    "tier": score_result["tier"],
                    "version": score_result["version"],
                    "model_type": score_result["model_type"],
                    "features": features_dict,
                    "shap": shap_to_json(shap_explanations),
                    "narrative": narrative,
                }
                db.commit()

                log_event(
                    logging.INFO,
                    f"Quality score: {score_result['score']:.1f} (Tier {score_result['tier']})",
                    job_id=review_id,
                    step="quality_score",
                    event="quality_score_computed",
                    status="processing",
                )

            # Step 6: Badge generation
            with log_step(review_id, "badge_generation", review_id=review_id):
                # Build review data for badge computation
                review_data = {
                    "id": str(review.id),
                    "claims": review.claims or [],
                    "checklist": review.checklist or {},
                    "citations": review.citations or {},
                }

                # Compute badge statuses
                badges_status = {
                    "claim_mapped": compute_badge_status("claim-mapped", review_data),
                    "method_check": compute_badge_status("method-check", review_data),
                    "citations_augmented": compute_badge_status("citations-augmented", review_data),
                }

                review.badges = badges_status
                db.commit()

                log_event(
                    logging.INFO,
                    f"Generated badges: {badges_status}",
                    job_id=review_id,
                    step="badge_generation",
                    event="badges_generated",
                    status="processing",
                )

            # Step 7: Report generation
            with log_step(review_id, "report_generation", review_id=review_id):
                # Build complete review data
                review_data = build_review_data(review)

                # Generate reports
                reports_dir = Path(settings.reviews_base_path) / str(review.id)
                reports_dir.mkdir(parents=True, exist_ok=True)

                html_path = reports_dir / "report.html"
                json_path = reports_dir / "review.json"

                generate_html_report(review_data, html_path)
                generate_json_report(review_data, json_path)

                # Update review with report paths
                review.html_report_path = str(html_path)
                review.json_summary_path = str(json_path)
                db.commit()

                log_event(
                    logging.INFO,
                    "Generated HTML and JSON reports",
                    job_id=review_id,
                    step="report_generation",
                    event="reports_generated",
                    status="processing",
                )

            # All steps complete
            review.status = ReviewStatus.COMPLETED
            db.commit()

            log_event(
                logging.INFO,
                "Review processing completed",
                job_id=review_id,
                step="process_review",
                event="review_processing_completed",
                status="completed",
            )

    except Exception as e:
        logger.exception(f"Error processing review {review_id}: {e}")
        review.status = ReviewStatus.FAILED
        review.error_message = str(e)
        db.commit()

        log_event(
            logging.ERROR,
            f"Review processing failed: {str(e)}",
            job_id=review_id,
            step="process_review",
            event="review_processing_failed",
            status="failed",
            error=str(e),
        )
    finally:
        db.close()

