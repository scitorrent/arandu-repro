"""Tests for Docker image building."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.utils.errors import DockerBuildError
from app.worker.docker_builder import _generate_dockerfile, build_image
from app.worker.env_detector import Dependency, EnvironmentInfo


def test_generate_dockerfile_pip():
    """Test Dockerfile generation for pip environment."""
    env_info = EnvironmentInfo(
        env_type="pip",
        dependencies=[
            Dependency("numpy", "1.24.0"),
            Dependency("pandas"),
        ],
        detected_files=["requirements.txt"],
    )

    dockerfile = _generate_dockerfile(env_info)

    assert "FROM python:3.11-slim" in dockerfile
    assert "useradd -m -u 1000 arandu-user" in dockerfile
    assert "pip install --no-cache-dir numpy==1.24.0 pandas" in dockerfile
    assert "USER arandu-user" in dockerfile
    assert "WORKDIR /workspace" in dockerfile


def test_generate_dockerfile_conda():
    """Test Dockerfile generation for conda environment."""
    env_info = EnvironmentInfo(
        env_type="conda",
        dependencies=[
            Dependency("numpy", "1.24.0"),
            Dependency("pandas"),
        ],
        detected_files=["environment.yml"],
    )

    dockerfile = _generate_dockerfile(env_info)

    assert "FROM python:3.11-slim" in dockerfile
    assert "pip install" in dockerfile
    assert "USER arandu-user" in dockerfile


def test_generate_dockerfile_poetry():
    """Test Dockerfile generation for poetry environment."""
    env_info = EnvironmentInfo(
        env_type="poetry",
        dependencies=[],
        detected_files=["pyproject.toml"],
    )

    dockerfile = _generate_dockerfile(env_info)

    assert "FROM python:3.11-slim" in dockerfile
    assert "pip install poetry" in dockerfile
    assert "COPY pyproject.toml ." in dockerfile
    assert "poetry install --no-dev" in dockerfile
    assert "USER arandu-user" in dockerfile


@patch("app.worker.docker_builder.docker.from_env")
def test_build_image_success(mock_docker_client, tmp_path: Path):
    """Test successful Docker image build."""
    # Setup
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()
    (repo_path / "main.py").write_text("print('hello')")

    env_info = EnvironmentInfo(
        env_type="pip",
        dependencies=[Dependency("numpy", "1.24.0")],
        detected_files=["requirements.txt"],
    )

    # Mock Docker client
    mock_client = MagicMock()
    mock_image = MagicMock()
    mock_client.images.build.return_value = (mock_image, [{"stream": "Successfully built"}])
    mock_docker_client.return_value = mock_client

    # Build image
    image_tag = build_image(repo_path, env_info, job_id="test-job-1")

    assert image_tag == "arandu-job-test-job-1:latest"
    mock_client.images.build.assert_called_once()
    assert (repo_path / "Dockerfile.arandu").exists()


@patch("app.worker.docker_builder.docker.from_env")
def test_build_image_failure(mock_docker_client, tmp_path: Path):
    """Test Docker image build failure."""
    import docker

    # Setup
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()

    env_info = EnvironmentInfo(
        env_type="pip",
        dependencies=[],
        detected_files=["requirements.txt"],
    )

    # Mock Docker client to raise BuildError
    mock_client = MagicMock()
    build_error = docker.errors.BuildError("Build failed", [])
    mock_client.images.build.side_effect = build_error
    mock_docker_client.return_value = mock_client

    # Build image should raise DockerBuildError
    with pytest.raises(DockerBuildError, match="Docker build failed"):
        build_image(repo_path, env_info, job_id="test-job-2")
