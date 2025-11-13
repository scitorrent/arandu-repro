"""Tests for container security hardening (Issue #31)."""

from unittest.mock import Mock, patch

import pytest

from app.utils.errors import ExecutionError
from app.worker.executor import execute_command


def test_executor_fails_if_root_user(tmp_path):
    """Test that executor fails if docker_user is root."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir(parents=True)
    (artifacts_dir / "logs").mkdir(exist_ok=True)

    with patch("app.worker.executor.settings") as mock_settings:
        mock_settings.docker_user = "root"
        mock_settings.docker_cpu_limit = 2.0
        mock_settings.docker_memory_limit = "4g"
        mock_settings.docker_network_mode = "none"
        mock_settings.docker_readonly_rootfs = True
        mock_settings.default_timeout_seconds = 60

        with pytest.raises(
            ExecutionError, match="Security violation: containers must run as non-root user"
        ):
            execute_command(
                image_tag="test:latest",
                command="echo test",
                repo_path=repo_path,
                artifacts_dir=artifacts_dir,
                job_id="test-job",
            )


def test_executor_fails_if_no_cpu_limit(tmp_path):
    """Test that executor fails if CPU limit is not set."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir(parents=True)
    (artifacts_dir / "logs").mkdir(exist_ok=True)

    with patch("app.worker.executor.settings") as mock_settings:
        mock_settings.docker_user = "arandu-user"
        mock_settings.docker_cpu_limit = 0
        mock_settings.docker_memory_limit = "4g"
        mock_settings.docker_network_mode = "none"
        mock_settings.docker_readonly_rootfs = True
        mock_settings.default_timeout_seconds = 60

        with pytest.raises(
            ExecutionError, match="Security violation: CPU limit must be greater than 0"
        ):
            execute_command(
                image_tag="test:latest",
                command="echo test",
                repo_path=repo_path,
                artifacts_dir=artifacts_dir,
                job_id="test-job",
            )


def test_executor_fails_if_no_memory_limit(tmp_path):
    """Test that executor fails if memory limit is not set."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir(parents=True)
    (artifacts_dir / "logs").mkdir(exist_ok=True)

    with patch("app.worker.executor.settings") as mock_settings:
        mock_settings.docker_user = "arandu-user"
        mock_settings.docker_cpu_limit = 2.0
        mock_settings.docker_memory_limit = ""
        mock_settings.docker_network_mode = "none"
        mock_settings.docker_readonly_rootfs = True
        mock_settings.default_timeout_seconds = 60

        with pytest.raises(ExecutionError, match="Security violation: memory limit must be set"):
            execute_command(
                image_tag="test:latest",
                command="echo test",
                repo_path=repo_path,
                artifacts_dir=artifacts_dir,
                job_id="test-job",
            )


def test_executor_fails_if_invalid_network_mode(tmp_path):
    """Test that executor fails if network mode is invalid."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir(parents=True)
    (artifacts_dir / "logs").mkdir(exist_ok=True)

    with patch("app.worker.executor.settings") as mock_settings:
        mock_settings.docker_user = "arandu-user"
        mock_settings.docker_cpu_limit = 2.0
        mock_settings.docker_memory_limit = "4g"
        mock_settings.docker_network_mode = "host"  # Invalid
        mock_settings.docker_readonly_rootfs = True
        mock_settings.default_timeout_seconds = 60

        with pytest.raises(ExecutionError, match="Security violation: invalid network mode"):
            execute_command(
                image_tag="test:latest",
                command="echo test",
                repo_path=repo_path,
                artifacts_dir=artifacts_dir,
                job_id="test-job",
            )


def test_executor_enforces_readonly_rootfs(tmp_path):
    """Test that executor applies read-only root filesystem when enabled."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir(parents=True)
    (artifacts_dir / "logs").mkdir(exist_ok=True)

    with patch("app.worker.executor.docker") as mock_docker, patch(
        "app.worker.executor.settings"
    ) as mock_settings:

        mock_settings.docker_user = "arandu-user"
        mock_settings.docker_cpu_limit = 2.0
        mock_settings.docker_memory_limit = "4g"
        mock_settings.docker_network_mode = "none"
        mock_settings.docker_readonly_rootfs = True
        mock_settings.default_timeout_seconds = 60

        mock_client = Mock()
        mock_docker.from_env.return_value = mock_client
        mock_container = Mock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b"test output"
        mock_client.containers.run.return_value = mock_container

        # Mock time module to avoid comparison issues
        with patch("app.worker.executor.time") as mock_time:
            mock_time.time.side_effect = [1000.0, 1001.0]  # 1 second duration

            execute_command(
                image_tag="test:latest",
                command="echo test",
                repo_path=repo_path,
                artifacts_dir=artifacts_dir,
                job_id="test-job",
            )

        # Verify read_only was passed to containers.run
        call_kwargs = mock_client.containers.run.call_args[1]
        assert call_kwargs["read_only"] is True
        assert call_kwargs["user"] == "arandu-user"
        assert call_kwargs["network_mode"] == "none"
