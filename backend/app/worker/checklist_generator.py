"""Method checklist generator for reproducibility assessment."""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.worker.claim_extractor import Claim

logger = logging.getLogger(__name__)


@dataclass
class ChecklistItem:
    """Represents a checklist item."""

    key: str  # e.g., "data_available", "seeds_fixed"
    status: str  # "ok", "partial", "missing"
    evidence: str | None  # Snippet or rationale
    source: str  # "paper" or "repo"


@dataclass
class Checklist:
    """Complete checklist for a review."""

    items: list[ChecklistItem]
    summary: str  # Overall summary


def check_data_available(paper_text: str, repo_path: Path | None = None) -> ChecklistItem:
    """
    Check if data is clearly available (link or instructions).

    Args:
        paper_text: Paper text
        repo_path: Optional repository path

    Returns:
        ChecklistItem
    """
    evidence = None
    status = "missing"

    # Check paper text for data links/mentions
    data_patterns = [
        r"dataset[:\s]+(?:https?://|www\.)",
        r"data[:\s]+(?:available|provided|download)",
        r"https?://[^\s]+(?:data|dataset)",
    ]

    for pattern in data_patterns:
        match = re.search(pattern, paper_text, re.IGNORECASE)
        if match:
            evidence = match.group(0)
            status = "ok"
            break

    # Check repo for data directory or README mention
    if repo_path and repo_path.exists():
        data_dirs = ["data", "datasets", "data_files"]
        for data_dir in data_dirs:
            if (repo_path / data_dir).exists():
                status = "ok" if status == "missing" else "partial"
                evidence = f"Found {data_dir}/ directory in repo"
                break

        # Check README for data instructions
        readme_path = repo_path / "README.md"
        if readme_path.exists():
            readme_text = readme_path.read_text()
            if re.search(r"data|dataset", readme_text, re.IGNORECASE):
                if status == "missing":
                    status = "partial"
                    evidence = "README mentions data"

    return ChecklistItem(
        key="data_available",
        status=status,
        evidence=evidence,
        source="paper" if evidence and "paper" in str(evidence) else "repo",
    )


def check_seeds_fixed(paper_text: str, repo_path: Path | None = None) -> ChecklistItem:
    """
    Check if seeds are fixed (mentions of seed, random_state).

    Args:
        paper_text: Paper text
        repo_path: Optional repository path

    Returns:
        ChecklistItem
    """
    evidence = None
    status = "missing"

    # Check paper for seed mentions
    seed_patterns = [
        r"seed[:\s]+(\d+)",
        r"random[_\s]?state[:\s]+(\d+)",
        r"random[_\s]?seed[:\s]+(\d+)",
    ]

    for pattern in seed_patterns:
        match = re.search(pattern, paper_text, re.IGNORECASE)
        if match:
            evidence = match.group(0)
            status = "ok"
            break

    # Check repo code for seed settings
    if repo_path and repo_path.exists():
        python_files = list(repo_path.rglob("*.py"))
        for py_file in python_files[:10]:  # Check first 10 Python files
            try:
                content = py_file.read_text()
                if re.search(r"seed\s*=\s*\d+|random_state\s*=\s*\d+", content):
                    status = "ok" if status == "missing" else "partial"
                    evidence = f"Found seed setting in {py_file.name}"
                    break
            except Exception:
                continue

    return ChecklistItem(
        key="seeds_fixed",
        status=status,
        evidence=evidence,
        source="paper" if evidence and "paper" in str(evidence) else "repo",
    )


def check_environment_files(repo_path: Path | None = None) -> ChecklistItem:
    """
    Check for environment files (requirements.txt, environment.yml, etc.).

    Args:
        repo_path: Repository path

    Returns:
        ChecklistItem
    """
    if not repo_path or not repo_path.exists():
        return ChecklistItem(
            key="environment",
            status="missing",
            evidence=None,
            source="repo",
        )

    env_files = [
        "requirements.txt",
        "environment.yml",
        "pyproject.toml",
        "Pipfile",
        "setup.py",
    ]

    found_files = []
    for env_file in env_files:
        if (repo_path / env_file).exists():
            found_files.append(env_file)

    if found_files:
        return ChecklistItem(
            key="environment",
            status="ok",
            evidence=f"Found: {', '.join(found_files)}",
            source="repo",
        )
    else:
        return ChecklistItem(
            key="environment",
            status="missing",
            evidence=None,
            source="repo",
        )


def check_commands_available(paper_text: str, repo_path: Path | None = None) -> ChecklistItem:
    """
    Check if execution commands are available (README or paper).

    Args:
        paper_text: Paper text
        repo_path: Optional repository path

    Returns:
        ChecklistItem
    """
    evidence = None
    status = "missing"

    # Check paper for command mentions
    command_patterns = [
        r"(?:run|execute|command)[:\s]+(?:python|bash|sh)",
        r"python\s+[a-z_]+\.py",
    ]

    for pattern in command_patterns:
        if re.search(pattern, paper_text, re.IGNORECASE):
            status = "partial"
            evidence = "Paper mentions execution commands"
            break

    # Check README for commands
    if repo_path and repo_path.exists():
        readme_path = repo_path / "README.md"
        if readme_path.exists():
            readme_text = readme_path.read_text()
            if re.search(r"python|run|execute|usage", readme_text, re.IGNORECASE):
                status = "ok" if status == "missing" else "partial"
                evidence = "README contains execution instructions"

    return ChecklistItem(
        key="commands",
        status=status,
        evidence=evidence,
        source="paper" if "Paper" in str(evidence) else "repo",
    )


def check_metrics_defined(paper_text: str) -> ChecklistItem:
    """
    Check if metrics are defined (accuracy, F1, AUROC, etc.).

    Args:
        paper_text: Paper text

    Returns:
        ChecklistItem
    """
    metric_patterns = [
        r"(?:accuracy|precision|recall|f1|f-score|auroc|auc|roc)",
        r"metric[s]?[:\s]+(?:accuracy|f1)",
    ]

    evidence = None
    status = "missing"

    for pattern in metric_patterns:
        match = re.search(pattern, paper_text, re.IGNORECASE)
        if match:
            evidence = match.group(0)
            status = "ok"
            break

    return ChecklistItem(
        key="metrics",
        status=status,
        evidence=evidence,
        source="paper",
    )


def check_comparatives(paper_text: str) -> ChecklistItem:
    """
    Check if baselines are named and compared.

    Args:
        paper_text: Paper text

    Returns:
        ChecklistItem
    """
    baseline_patterns = [
        r"baseline[s]?",
        r"compared\s+to",
        r"versus|vs\.",
        r"state-of-the-art|SOTA",
    ]

    evidence = None
    status = "missing"

    for pattern in baseline_patterns:
        if re.search(pattern, paper_text, re.IGNORECASE):
            status = "partial"
            evidence = "Paper mentions baselines/comparisons"
            break

    # Check for specific baseline names
    if re.search(r"(?:BERT|GPT|ResNet|VGG)\s+(?:baseline|comparison)", paper_text, re.IGNORECASE):
        status = "ok"
        evidence = "Paper names specific baselines"

    return ChecklistItem(
        key="comparatives",
        status=status,
        evidence=evidence,
        source="paper",
    )


def check_license(repo_path: Path | None = None) -> ChecklistItem:
    """
    Check if code/data has explicit license.

    Args:
        repo_path: Repository path

    Returns:
        ChecklistItem
    """
    if not repo_path or not repo_path.exists():
        return ChecklistItem(
            key="license",
            status="missing",
            evidence=None,
            source="repo",
        )

    license_files = ["LICENSE", "LICENSE.txt", "LICENSE.md", "COPYING"]
    for license_file in license_files:
        if (repo_path / license_file).exists():
            return ChecklistItem(
                key="license",
                status="ok",
                evidence=f"Found {license_file}",
                source="repo",
            )

    # Check README for license mention
    readme_path = repo_path / "README.md"
    if readme_path.exists():
        readme_text = readme_path.read_text()
        if re.search(r"license|licence", readme_text, re.IGNORECASE):
            return ChecklistItem(
                key="license",
                status="partial",
                evidence="License mentioned in README",
                source="repo",
            )

    return ChecklistItem(
        key="license",
        status="missing",
        evidence=None,
        source="repo",
    )


def generate_checklist(
    paper_text: str,
    claims: list[Claim],
    repo_path: Path | None = None,
) -> Checklist:
    """
    Generate complete checklist for a review.

    Args:
        paper_text: Full paper text
        claims: List of extracted claims
        repo_path: Optional repository path

    Returns:
        Checklist object
    """
    items: list[ChecklistItem] = []

    # Check each item
    items.append(check_data_available(paper_text, repo_path))
    items.append(check_seeds_fixed(paper_text, repo_path))
    items.append(check_environment_files(repo_path))
    items.append(check_commands_available(paper_text, repo_path))
    items.append(check_metrics_defined(paper_text))
    items.append(check_comparatives(paper_text))
    items.append(check_license(repo_path))

    # Generate summary
    ok_count = sum(1 for item in items if item.status == "ok")
    partial_count = sum(1 for item in items if item.status == "partial")
    missing_count = sum(1 for item in items if item.status == "missing")

    summary = f"Checklist: {ok_count} OK, {partial_count} partial, {missing_count} missing"

    return Checklist(items=items, summary=summary)


def checklist_to_json(checklist: Checklist) -> dict[str, Any]:
    """
    Convert checklist to JSON-serializable format.

    Args:
        checklist: Checklist object

    Returns:
        Dictionary representation
    """
    return {
        "items": [
            {
                "key": item.key,
                "status": item.status,
                "evidence": item.evidence,
                "source": item.source,
            }
            for item in checklist.items
        ],
        "summary": checklist.summary,
    }

