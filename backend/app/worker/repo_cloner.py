"""Repository cloning utilities."""

import logging
import shutil
from pathlib import Path
from urllib.parse import urlparse

from app.utils.errors import RepoCloneError
from app.utils.logging import log_step

logger = logging.getLogger(__name__)


def clone_repo(repo_url: str, target_dir: Path, job_id: str) -> Path:
    """
    Clone GitHub repository to target directory.

    Supports:
    - GitHub HTTPS URLs (https://github.com/user/repo)
    - GitHub SSH URLs (git@github.com:user/repo.git)
    - Local file:// URLs for testing (file:///path/to/repo)

    Args:
        repo_url: Repository URL (GitHub or file://)
        target_dir: Directory to clone into
        job_id: Job ID for logging

    Returns:
        Path to cloned repository root

    Raises:
        RepoCloneError: If clone fails (invalid URL, network error, etc.)
    """
    with log_step(job_id, "clone_repo", repo_url=repo_url):
        # Parse URL
        parsed = urlparse(repo_url)

        # Handle file:// URLs for testing
        if parsed.scheme == "file":
            source_path = Path(parsed.path)
            if not source_path.exists():
                raise RepoCloneError(f"Source path does not exist: {source_path}")
            if not source_path.is_dir():
                raise RepoCloneError(f"Source path is not a directory: {source_path}")

            # Copy directory instead of cloning
            target_dir.mkdir(parents=True, exist_ok=True)
            repo_path = target_dir / source_path.name
            if repo_path.exists():
                shutil.rmtree(repo_path)
            shutil.copytree(source_path, repo_path)
            logger.info(f"Copied local repo from {source_path} to {repo_path}")
            return repo_path

        # Handle GitHub URLs
        if parsed.scheme not in ("https", "http", "git"):
            raise RepoCloneError(f"Unsupported URL scheme: {parsed.scheme}")

        # Normalize GitHub URL
        if "github.com" not in parsed.netloc:
            raise RepoCloneError(f"Only GitHub repositories are supported, got: {parsed.netloc}")

        # Ensure target directory exists
        target_dir.mkdir(parents=True, exist_ok=True)

        # Import git here to avoid dependency if not needed
        try:
            import git
        except ImportError:
            raise RepoCloneError("GitPython not installed. Install with: pip install GitPython")

        # Clone repository
        try:
            repo_path = target_dir / Path(repo_url).stem.replace(".git", "")
            if repo_path.exists():
                shutil.rmtree(repo_path)

            git.Repo.clone_from(repo_url, repo_path, depth=1)
            logger.info(f"Cloned repository to {repo_path}")
            return repo_path
        except git.GitCommandError as e:
            raise RepoCloneError(f"Git clone failed: {str(e)}")
        except Exception as e:
            raise RepoCloneError(f"Unexpected error during clone: {str(e)}")


def cleanup_repo(repo_path: Path, job_id: str) -> None:
    """
    Clean up cloned repository directory.

    Args:
        repo_path: Path to repository directory
        job_id: Job ID for logging
    """
    try:
        if repo_path.exists():
            shutil.rmtree(repo_path)
            logger.info(f"Cleaned up repository at {repo_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup repository at {repo_path}: {str(e)}")
