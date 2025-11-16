"""Storage utilities for papers."""

import os
import secrets
from pathlib import Path

from app.config import settings


def validate_papers_base() -> Path:
    """Validate and ensure PAPERS_BASE directory exists."""
    base = settings.papers_base_path
    base.mkdir(parents=True, exist_ok=True)

    # Check write permissions
    if not os.access(base, os.W_OK):
        raise PermissionError(f"Cannot write to PAPERS_BASE: {base}")

    return base


def get_paper_version_path(aid: str, version: int, filename: str = "file.pdf") -> Path:
    """Get path for paper version file.

    Args:
        aid: Paper AID
        version: Version number
        filename: Filename (default: file.pdf)

    Returns:
        Path object (relative to PAPERS_BASE)

    Raises:
        ValueError: If path contains traversal attempts
    """
    # Validate aid (alphanumeric, dash, underscore only)
    if not all(c.isalnum() or c in ('-', '_') for c in aid):
        raise ValueError(f"Invalid AID format: {aid}")

    # Validate version
    if version < 1:
        raise ValueError(f"Version must be >= 1: {version}")

    # Validate filename (no path traversal)
    if '..' in filename or '/' in filename or '\\' in filename:
        raise ValueError(f"Invalid filename: {filename}")

    # Construct path: /papers/{aid}/v{version}/{filename}
    path = Path("papers") / aid / f"v{version}" / filename

    # Resolve to ensure no traversal
    resolved = (Path("/") / path).resolve()
    base_resolved = Path("/") / Path("papers")

    if not str(resolved).startswith(str(base_resolved)):
        raise ValueError(f"Path traversal detected: {path}")

    return path


def ensure_paper_version_directory(aid: str, version: int) -> Path:
    """Ensure paper version directory exists.

    Creates directory atomically and returns full path.
    """
    base = validate_papers_base()
    rel_path = get_paper_version_path(aid, version)
    full_path = base / rel_path

    # Create directory atomically
    full_path.parent.mkdir(parents=True, exist_ok=True)

    return full_path


def generate_secure_aid(length: int = 12) -> str:
    """Generate secure AID (alphanumeric, URL-safe)."""
    # Use URL-safe base64 without padding
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def validate_pdf_path(path: Path) -> bool:
    """Validate PDF path exists and is readable."""
    if not path.exists():
        return False
    if not path.is_file():
        return False
    if not os.access(path, os.R_OK):
        return False
    return True

