"""Tests for repository cloning."""

from pathlib import Path

import pytest

from app.utils.errors import RepoCloneError
from app.worker.repo_cloner import cleanup_repo, clone_repo


def test_clone_local_repo(tmp_path: Path):
    """Test cloning a local repository using file:// URL."""
    # Create a test repository
    test_repo = Path(__file__).parent / "fixtures" / "repos" / "hello-python"
    assert test_repo.exists(), "Test repository fixture not found"

    # Clone using file:// URL
    target_dir = tmp_path / "cloned"
    repo_path = clone_repo(f"file://{test_repo.absolute()}", target_dir, job_id="test-job-1")

    # Verify repository was cloned
    assert repo_path.exists()
    assert (repo_path / "requirements.txt").exists()
    assert (repo_path / "main.py").exists()
    assert (repo_path / "README.md").exists()

    # Cleanup
    cleanup_repo(repo_path, "test-job-1")
    assert not repo_path.exists()


def test_clone_invalid_file_url(tmp_path: Path):
    """Test cloning with invalid file:// URL."""
    target_dir = tmp_path / "cloned"

    with pytest.raises(RepoCloneError, match="does not exist"):
        clone_repo("file:///nonexistent/path", target_dir, job_id="test-job-2")


def test_clone_invalid_scheme(tmp_path: Path):
    """Test cloning with unsupported URL scheme."""
    target_dir = tmp_path / "cloned"

    with pytest.raises(RepoCloneError, match="Unsupported URL scheme"):
        clone_repo("ftp://example.com/repo", target_dir, job_id="test-job-3")


def test_clone_non_github_url(tmp_path: Path):
    """Test cloning with non-GitHub URL."""
    target_dir = tmp_path / "cloned"

    with pytest.raises(RepoCloneError, match="Only GitHub repositories are supported"):
        clone_repo("https://gitlab.com/user/repo", target_dir, job_id="test-job-4")


def test_cleanup_repo(tmp_path: Path):
    """Test repository cleanup."""
    # Create a temporary directory
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()
    (repo_path / "file.txt").write_text("test")

    # Cleanup
    cleanup_repo(repo_path, "test-job-5")
    assert not repo_path.exists()
