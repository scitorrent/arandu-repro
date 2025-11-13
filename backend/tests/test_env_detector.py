"""Tests for environment detection."""

from pathlib import Path

import pytest

from app.utils.errors import NoEnvironmentDetectedError
from app.worker.env_detector import (
    Dependency,
    EnvironmentInfo,
    _parse_requirements_txt,
    detect_environment,
)


def test_detect_requirements_txt(tmp_path: Path):
    """Test detection from requirements.txt."""
    # Create a test repo with requirements.txt
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()
    (repo_path / "requirements.txt").write_text("numpy==1.24.0\ntorch>=2.0.0\npandas\n")

    env_info = detect_environment(repo_path, job_id="test-job-1")

    assert env_info.type == "pip"
    assert "requirements.txt" in env_info.detected_files
    assert len(env_info.dependencies) == 3
    assert any(dep.name == "numpy" and dep.version == "==1.24.0" for dep in env_info.dependencies)
    assert any(dep.name == "torch" and dep.version == ">=2.0.0" for dep in env_info.dependencies)
    assert any(dep.name == "pandas" and dep.version is None for dep in env_info.dependencies)


def test_detect_environment_yml(tmp_path: Path):
    """Test detection from environment.yml."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()
    (repo_path / "environment.yml").write_text(
        "name: test-env\n"
        "dependencies:\n"
        "  - numpy=1.24.0\n"
        "  - pandas\n"
        "  - pip:\n"
        "    - torch==2.0.0\n"
    )

    env_info = detect_environment(repo_path, job_id="test-job-2")

    assert env_info.type == "conda"
    assert "environment.yml" in env_info.detected_files
    assert len(env_info.dependencies) >= 2


def test_detect_pyproject_toml(tmp_path: Path):
    """Test detection from pyproject.toml."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()
    (repo_path / "pyproject.toml").write_text(
        "[project]\n" "dependencies = [\n" '    "numpy==1.24.0",\n' '    "pandas",\n' "]\n"
    )

    env_info = detect_environment(repo_path, job_id="test-job-3")

    assert env_info.type == "poetry"
    assert "pyproject.toml" in env_info.detected_files
    assert len(env_info.dependencies) >= 1


def test_detect_no_environment(tmp_path: Path):
    """Test detection when no environment files exist."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()
    (repo_path / "README.md").write_text("# Test repo\n")

    with pytest.raises(NoEnvironmentDetectedError, match="No environment files detected"):
        detect_environment(repo_path, job_id="test-job-4")


def test_parse_requirements_txt(tmp_path: Path):
    """Test parsing requirements.txt."""
    requirements_file = tmp_path / "requirements.txt"
    requirements_file.write_text(
        "numpy==1.24.0\n"
        "torch>=2.0.0\n"
        "pandas~=2.0.0\n"
        "scipy\n"
        "# This is a comment\n"
        "  \n"  # Empty line
    )

    deps = _parse_requirements_txt(requirements_file)

    assert len(deps) == 4
    assert deps[0].name == "numpy"
    assert deps[0].version == "==1.24.0"  # The version string includes the operator (e.g., '==')
    assert deps[1].name == "torch"
    assert deps[1].version == ">=2.0.0"
    assert deps[2].name == "pandas"
    assert deps[2].version == "~=2.0.0"
    assert deps[3].name == "scipy"
    assert deps[3].version is None


def test_environment_info_to_dict():
    """Test EnvironmentInfo.to_dict()."""
    deps = [Dependency("numpy", "1.24.0"), Dependency("pandas")]
    env_info = EnvironmentInfo(
        env_type="pip",
        dependencies=deps,
        detected_files=["requirements.txt"],
    )

    data = env_info.to_dict()

    assert data["type"] == "pip"
    assert data["detected_files"] == ["requirements.txt"]
    assert len(data["dependencies"]) == 2
    assert data["dependencies"][0]["name"] == "numpy"
    assert data["dependencies"][0]["version"] == "1.24.0"
    assert data["dependencies"][1]["name"] == "pandas"
    assert "version" not in data["dependencies"][1]


def test_dependency_to_dict():
    """Test Dependency.to_dict()."""
    dep_with_version = Dependency("numpy", "1.24.0")
    dep_without_version = Dependency("pandas")

    assert dep_with_version.to_dict() == {"name": "numpy", "version": "1.24.0"}
    assert dep_without_version.to_dict() == {"name": "pandas"}
