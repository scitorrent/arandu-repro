"""Artifact generation utilities (reports, notebooks, badges)."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from app.models.job import Job
from app.models.run import Run
from app.utils.logging import log_step
from app.worker.env_detector import EnvironmentInfo

logger = logging.getLogger(__name__)


def generate_report(
    job: Job,
    run: Run,
    env_info: EnvironmentInfo,
    output_path: Path,
    job_id: str,
) -> Path:
    """
    Generate reproducibility report in markdown format.

    Args:
        job: Job model instance
        run: Run model instance
        env_info: Detected environment information
        output_path: Directory to save report
        job_id: Job ID for logging

    Returns:
        Path to generated report file
    """
    with log_step(job_id, "generate_report"):
        output_path.mkdir(parents=True, exist_ok=True)
        report_file = output_path / "report.md"

        # Determine execution status
        if run.exit_code == 0:
            status = "✅ Success"
            status_emoji = "✅"
        elif run.exit_code is None:
            status = "⏳ In Progress"
            status_emoji = "⏳"
        else:
            status = f"❌ Failed (exit code: {run.exit_code})"
            status_emoji = "❌"

        # Format timestamps
        created_at = job.created_at.isoformat() if job.created_at else "N/A"
        started_at = run.started_at.isoformat() if run.started_at else "N/A"
        completed_at = run.completed_at.isoformat() if run.completed_at else "N/A"
        duration = f"{run.duration_seconds:.2f}s" if run.duration_seconds else "N/A"

        # Build report content
        report_lines = [
            "# Reproducibility Report",
            "",
            f"**Generated:** {datetime.now(UTC).isoformat()}",
            "",
            "## Job Metadata",
            "",
            f"- **Job ID:** `{job.id}`",
            f"- **Repository:** {job.repo_url}",
            f"- **Status:** {status}",
            f"- **Created:** {created_at}",
            f"- **Started:** {started_at}",
            f"- **Completed:** {completed_at}",
            f"- **Duration:** {duration}",
        ]

        if job.arxiv_id:
            report_lines.append(f"- **arXiv ID:** {job.arxiv_id}")

        if job.run_command:
            report_lines.append(f"- **Command:** `{job.run_command}`")

        report_lines.extend(
            [
                "",
                "## Environment Summary",
                "",
                f"- **Type:** {env_info.type}",
                f"- **Base Image:** {env_info.base_image}",
                f"- **Detected Files:** {', '.join(env_info.detected_files)}",
                "",
                "### Dependencies",
                "",
            ]
        )

        if env_info.dependencies:
            for dep in env_info.dependencies:
                if dep.version:
                    report_lines.append(f"- `{dep.name}=={dep.version}`")
                else:
                    report_lines.append(f"- `{dep.name}`")
        else:
            report_lines.append("- No dependencies detected")

        report_lines.extend(
            [
                "",
                "## Execution Results",
                "",
                f"**Status:** {status_emoji} {status}",
            ]
        )

        if run.exit_code is not None:
            report_lines.append(f"**Exit Code:** {run.exit_code}")

        if run.duration_seconds:
            report_lines.append(f"**Duration:** {run.duration_seconds:.2f} seconds")

        report_lines.extend(
            [
                "",
                "## Logs",
                "",
                "### Standard Output",
                "",
                "```",
            ]
        )

        # Add stdout (truncated)
        if run.stdout:
            report_lines.append(run.stdout)
        else:
            report_lines.append("(no output)")

        report_lines.extend(
            [
                "```",
                "",
                "### Standard Error",
                "",
                "```",
            ]
        )

        # Add stderr (truncated)
        if run.stderr:
            report_lines.append(run.stderr)
        else:
            report_lines.append("(no errors)")

        report_lines.extend(
            [
                "```",
                "",
                "---",
                "",
                f"*Full logs available at: {run.logs_path}*" if run.logs_path else "",
            ]
        )

        # Write report
        report_content = "\n".join(report_lines)
        report_file.write_text(report_content, encoding="utf-8")

        logger.info(f"Generated report at {report_file}")
        return report_file


def generate_notebook(
    job: Job,
    env_info: EnvironmentInfo,
    output_path: Path,
    job_id: str,
) -> Path:
    """
    Generate Jupyter notebook template.

    Args:
        job: Job model instance
        env_info: Detected environment information
        output_path: Directory to save notebook
        job_id: Job ID for logging

    Returns:
        Path to generated notebook file
    """
    with log_step(job_id, "generate_notebook"):
        output_path.mkdir(parents=True, exist_ok=True)
        notebook_file = output_path / "notebook.ipynb"

        # Build notebook cells
        cells = []

        # Cell 1: Markdown header
        cells.append(
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Reproducibility Notebook\n",
                    "\n",
                    f"**Repository:** {job.repo_url}\n",
                    f"**Job ID:** `{job.id}`\n",
                ],
            }
        )

        # Cell 2: Environment setup
        setup_source = ["# Environment Setup\n", "\n"]
        if env_info.type == "pip":
            setup_source.append("```bash\n")
            setup_source.append("pip install ")
            deps = []
            for dep in env_info.dependencies:
                if dep.version:
                    # Check if version already contains an operator (==, >=, ~=, etc.)
                    if dep.version.startswith(("==", ">=", "~=", "<=", "!=", ">", "<")):
                        deps.append(f"{dep.name}{dep.version}")
                    else:
                        deps.append(f"{dep.name}=={dep.version}")
                else:
                    deps.append(dep.name)
            setup_source.append(" ".join(deps))
            setup_source.append("\n```\n")
        elif env_info.type == "conda":
            setup_source.append("```bash\n")
            setup_source.append("conda env create -f environment.yml\n")
            setup_source.append("conda activate <env-name>\n")
            setup_source.append("```\n")

        cells.append(
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": setup_source,
            }
        )

        # Cell 3: Code execution
        command = job.run_command or "python main.py"
        cells.append(
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [f"# Execute: {command}\n", f"!{command}\n"],
            }
        )

        # Build notebook structure
        notebook = {
            "cells": cells,
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3",
                },
                "language_info": {
                    "name": "python",
                    "version": "3.11",
                },
                "colab": {
                    "name": "Reproducibility Notebook",
                    "provenance": [],
                },
            },
            "nbformat": 4,
            "nbformat_minor": 4,
        }

        # Write notebook
        notebook_file.write_text(json.dumps(notebook, indent=2), encoding="utf-8")

        logger.info(f"Generated notebook at {notebook_file}")
        return notebook_file


def generate_badge(
    job: Job,
    base_url: str,
    output_path: Path,
    job_id: str,
) -> Path:
    """
    Generate badge snippet in markdown format.

    Args:
        job: Job model instance
        base_url: Base URL for badge links
        output_path: Directory to save badge
        job_id: Job ID for logging

    Returns:
        Path to generated badge file
    """
    with log_step(job_id, "generate_badge"):
        output_path.mkdir(parents=True, exist_ok=True)
        badge_file = output_path / "badge.md"

        # Determine badge status and color
        if job.status.value == "completed":
            status_text = "Reproducible"
            color = "green"
        elif job.status.value == "failed":
            status_text = "Failed"
            color = "red"
        elif job.status.value == "running":
            status_text = "Running"
            color = "yellow"
        else:
            status_text = "Pending"
            color = "gray"

        job_url = f"{base_url}/jobs/{job.id}"
        badge_url = f"https://img.shields.io/badge/Reproducibility-{status_text}-{color}"

        badge_markdown = f"[![{status_text}]({badge_url})]({job_url})"

        # Write badge
        badge_file.write_text(badge_markdown, encoding="utf-8")

        logger.info(f"Generated badge at {badge_file}")
        return badge_file
