"""Feature builder for Quality Score model."""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.worker.checklist_generator import Checklist
from app.worker.claim_extractor import Claim

logger = logging.getLogger(__name__)


@dataclass
class QualityFeatures:
    """Features for Quality Score prediction."""

    # Paper features
    num_claims: int
    claims_per_section: dict[str, float]
    has_ablation: bool
    has_baselines: bool
    has_error_bars: bool
    has_seeds: bool

    # Repo features
    has_requirements: bool
    has_lock_file: bool
    versions_pinned: float  # 0-1
    has_ci: bool
    has_tests: bool
    has_repro_readme: bool
    has_license: bool

    # Citations
    citation_coverage: float  # 0-1 (% of claims with ≥1 citation)
    citation_diversity: float  # 0-1
    avg_citation_relevance: float

    # Checklist
    checklist_pct_ok: float  # 0-1
    critical_items_missing: int

    # Traces (Repro Lite - optional)
    repro_exit_code: int | None = None
    repro_duration: float | None = None
    repro_seed_variance: float | None = None

    # Engagement (optional)
    num_issues: int = 0
    num_prs: int = 0
    num_releases: int = 0


def extract_paper_features(claims: list[Claim], paper_text: str) -> dict[str, Any]:
    """
    Extract features from paper text and claims.

    Args:
        claims: List of Claim objects
        paper_text: Full paper text

    Returns:
        Dictionary of paper features
    """
    import re

    features: dict[str, Any] = {}

    # Number of claims
    features["num_claims"] = len(claims)

    # Claims per section
    claims_per_section: dict[str, int] = {}
    for claim in claims:
        section = claim.section or "unknown"
        claims_per_section[section] = claims_per_section.get(section, 0) + 1

    total_claims = len(claims) if claims else 1
    features["claims_per_section"] = {
        section: count / total_claims for section, count in claims_per_section.items()
    }

    # Check for ablation studies
    features["has_ablation"] = bool(
        re.search(r"ablation|ablative", paper_text, re.IGNORECASE)
    )

    # Check for baselines
    features["has_baselines"] = bool(
        re.search(r"baseline|comparison|compared\s+to", paper_text, re.IGNORECASE)
    )

    # Check for error bars / confidence intervals
    features["has_error_bars"] = bool(
        re.search(
            r"error\s+bar|confidence\s+interval|std|standard\s+deviation",
            paper_text,
            re.IGNORECASE,
        )
    )

    # Check for seeds
    features["has_seeds"] = bool(
        re.search(r"seed|random[_\s]?state", paper_text, re.IGNORECASE)
    )

    return features


def extract_repo_features(repo_path: Path | None = None) -> dict[str, Any]:
    """
    Extract features from repository.

    Args:
        repo_path: Path to repository

    Returns:
        Dictionary of repo features
    """
    features: dict[str, Any] = {
        "has_requirements": False,
        "has_lock_file": False,
        "versions_pinned": 0.0,
        "has_ci": False,
        "has_tests": False,
        "has_repro_readme": False,
        "has_license": False,
    }

    if not repo_path or not repo_path.exists():
        return features

    # Check for requirements files
    req_files = ["requirements.txt", "pyproject.toml", "environment.yml", "Pipfile"]
    for req_file in req_files:
        if (repo_path / req_file).exists():
            features["has_requirements"] = True
            break

    # Check for lock files
    lock_files = ["poetry.lock", "Pipfile.lock", "package-lock.json"]
    for lock_file in lock_files:
        if (repo_path / lock_file).exists():
            features["has_lock_file"] = True
            break

    # Check versions pinned (simple heuristic: check if requirements.txt has ==)
    req_txt = repo_path / "requirements.txt"
    if req_txt.exists():
        content = req_txt.read_text()
        pinned = len(re.findall(r"==|@", content))
        total = len(re.findall(r"\n", content)) or 1
        features["versions_pinned"] = min(pinned / total, 1.0)

    # Check for CI
    ci_dirs = [".github/workflows", ".gitlab-ci.yml", ".travis.yml", "circleci"]
    for ci_dir in ci_dirs:
        ci_path = repo_path / ci_dir
        if ci_path.exists():
            features["has_ci"] = True
            break

    # Check for tests
    test_dirs = ["tests", "test", "tests/"]
    test_files = list(repo_path.rglob("test_*.py"))
    if test_files:
        features["has_tests"] = True

    # Check README for repro instructions
    readme_path = repo_path / "README.md"
    if readme_path.exists():
        readme_text = readme_path.read_text()
        if re.search(r"reproduce|reproducibility|how\s+to\s+run", readme_text, re.IGNORECASE):
            features["has_repro_readme"] = True

    # Check for license
    license_files = ["LICENSE", "LICENSE.txt", "LICENSE.md"]
    for license_file in license_files:
        if (repo_path / license_file).exists():
            features["has_license"] = True
            break

    return features


def extract_citation_features(
    citations_by_claim: dict[str, list[dict[str, Any]]],
    claims: list[Claim],
) -> dict[str, Any]:
    """
    Extract features from citations.

    Args:
        citations_by_claim: Dictionary mapping claim_id to list of citations
        claims: List of Claim objects

    Returns:
        Dictionary of citation features
    """
    features: dict[str, Any] = {
        "citation_coverage": 0.0,
        "citation_diversity": 0.0,
        "avg_citation_relevance": 0.0,
    }

    if not claims:
        return features

    # Citation coverage (% of claims with ≥1 citation)
    claims_with_cites = sum(
        1 for claim in claims if citations_by_claim.get(claim.id, [])
    )
    features["citation_coverage"] = claims_with_cites / len(claims) if claims else 0.0

    # Average citation relevance (average of score_final or score_rerank)
    all_scores = []
    for citations in citations_by_claim.values():
        for cit in citations:
            score = cit.get("score_final") or cit.get("score_rerank") or 0.0
            all_scores.append(score)

    features["avg_citation_relevance"] = (
        sum(all_scores) / len(all_scores) if all_scores else 0.0
    )

    # Citation diversity (simple: ratio of unique venues/authors)
    # TODO: Implement more sophisticated diversity metric
    features["citation_diversity"] = 0.5  # Placeholder

    return features


def extract_checklist_features(checklist: Checklist) -> dict[str, Any]:
    """
    Extract features from checklist.

    Args:
        checklist: Checklist object

    Returns:
        Dictionary of checklist features
    """
    features: dict[str, Any] = {
        "checklist_pct_ok": 0.0,
        "critical_items_missing": 0,
    }

    if not checklist.items:
        return features

    ok_count = sum(1 for item in checklist.items if item.status == "ok")
    features["checklist_pct_ok"] = ok_count / len(checklist.items)

    # Critical items: data, seeds, environment, commands
    critical_keys = ["data_available", "seeds_fixed", "environment", "commands"]
    missing_critical = sum(
        1
        for item in checklist.items
        if item.key in critical_keys and item.status == "missing"
    )
    features["critical_items_missing"] = missing_critical

    return features


def build_features(
    claims: list[Claim],
    paper_text: str,
    checklist: Checklist,
    citations_by_claim: dict[str, list[dict[str, Any]]] | None = None,
    repo_path: Path | None = None,
    repro_trace: dict[str, Any] | None = None,
) -> QualityFeatures:
    """
    Build complete feature set for Quality Score prediction.

    Args:
        claims: List of Claim objects
        paper_text: Full paper text
        checklist: Checklist object
        citations_by_claim: Optional citations by claim
        repo_path: Optional repository path
        repro_trace: Optional Repro Lite trace

    Returns:
        QualityFeatures object
    """
    # Extract features from each source
    paper_feat = extract_paper_features(claims, paper_text)
    repo_feat = extract_repo_features(repo_path)
    citation_feat = extract_citation_features(citations_by_claim or {}, claims)
    checklist_feat = extract_checklist_features(checklist)

    # Combine into QualityFeatures
    return QualityFeatures(
        # Paper
        num_claims=paper_feat["num_claims"],
        claims_per_section=paper_feat["claims_per_section"],
        has_ablation=paper_feat["has_ablation"],
        has_baselines=paper_feat["has_baselines"],
        has_error_bars=paper_feat["has_error_bars"],
        has_seeds=paper_feat["has_seeds"],
        # Repo
        has_requirements=repo_feat["has_requirements"],
        has_lock_file=repo_feat["has_lock_file"],
        versions_pinned=repo_feat["versions_pinned"],
        has_ci=repo_feat["has_ci"],
        has_tests=repo_feat["has_tests"],
        has_repro_readme=repo_feat["has_repro_readme"],
        has_license=repo_feat["has_license"],
        # Citations
        citation_coverage=citation_feat["citation_coverage"],
        citation_diversity=citation_feat["citation_diversity"],
        avg_citation_relevance=citation_feat["avg_citation_relevance"],
        # Checklist
        checklist_pct_ok=checklist_feat["checklist_pct_ok"],
        critical_items_missing=checklist_feat["critical_items_missing"],
        # Traces (optional)
        repro_exit_code=repro_trace.get("exit_code") if repro_trace else None,
        repro_duration=repro_trace.get("duration") if repro_trace else None,
        repro_seed_variance=repro_trace.get("seed_variance") if repro_trace else None,
    )


def features_to_dict(features: QualityFeatures) -> dict[str, Any]:
    """
    Convert QualityFeatures to dictionary for model input.

    Args:
        features: QualityFeatures object

    Returns:
        Dictionary representation
    """
    return {
        "num_claims": features.num_claims,
        "claims_per_section": features.claims_per_section,
        "has_ablation": int(features.has_ablation),
        "has_baselines": int(features.has_baselines),
        "has_error_bars": int(features.has_error_bars),
        "has_seeds": int(features.has_seeds),
        "has_requirements": int(features.has_requirements),
        "has_lock_file": int(features.has_lock_file),
        "versions_pinned": features.versions_pinned,
        "has_ci": int(features.has_ci),
        "has_tests": int(features.has_tests),
        "has_repro_readme": int(features.has_repro_readme),
        "has_license": int(features.has_license),
        "citation_coverage": features.citation_coverage,
        "citation_diversity": features.citation_diversity,
        "avg_citation_relevance": features.avg_citation_relevance,
        "checklist_pct_ok": features.checklist_pct_ok,
        "critical_items_missing": features.critical_items_missing,
        "repro_exit_code": features.repro_exit_code or -1,
        "repro_duration": features.repro_duration or 0.0,
        "repro_seed_variance": features.repro_seed_variance or 0.0,
    }

