"""Review state definition for LangGraph pipeline."""

from typing import Any

from typing_extensions import TypedDict


class ReviewState(TypedDict):
    """
    State definition for LangGraph review pipeline.

    TypedDict allows type checking while maintaining dictionary compatibility.
    """

    review_id: str
    # Input
    url: str | None
    doi: str | None
    pdf_file_path: str | None
    repo_url: str | None

    # Paper metadata and text
    paper_meta: dict[str, Any] | None
    paper_text: str

    # Claims
    claims: list[dict[str, Any]] | None

    # Citations
    citations: dict[str, list[dict[str, Any]]] | None

    # Checklist
    checklist: dict[str, Any] | None

    # Quality Score
    quality_score: dict[str, Any] | None

    # Badges
    badges: dict[str, Any] | None

    # Artifacts
    html_report_path: str | None
    json_summary_path: str | None

    # Status and errors
    status: str  # pending, processing, completed, failed
    error_message: str | None
    errors: list[dict[str, str]]  # List of {step, message}

