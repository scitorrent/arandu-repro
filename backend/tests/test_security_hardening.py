"""Tests for container security hardening (Issue #31)."""

from unittest.mock import Mock, patch

import pytest

from app.utils.errors import ExecutionError
from app.worker.executor import execute_command


def test_executor_fails_if_root_user():
    """Test that executor fails if docker_user is root."""
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
                repo_path=Mock(),
                artifacts_dir=Mock(),
                job_id="test-job",
            )


def test_executor_fails_if_no_cpu_limit():
    """Test that executor fails if CPU limit is not set."""
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
                repo_path=Mock(),
                artifacts_dir=Mock(),
                job_id="test-job",
            )


def test_executor_fails_if_no_memory_limit():
    """Test that executor fails if memory limit is not set."""
    repo_path = Path("/tmp/test-repo")
    artifacts_dir = Path("/tmp/test-artifacts")

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


def test_executor_fails_if_invalid_network_mode():
    """Test that executor fails if network mode is invalid."""
    repo_path = Path("/tmp/test-repo")
    artifacts_dir = Path("/tmp/test-artifacts")

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


def test_executor_enforces_readonly_rootfs():
    """Test that executor applies read-only root filesystem when enabled."""
    with patch("app.worker.executor.docker") as mock_docker, patch(
        "app.worker.executor.settings"
    ) as mock_settings, patch("app.worker.executor.Path"):

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

        repo_path = Mock()
        repo_path.__str__ = lambda x: "/tmp/repo"
        artifacts_dir = Mock()
        artifacts_dir.__str__ = lambda x: "/tmp/artifacts"
        artifacts_dir.mkdir = Mock()
        artifacts_dir.__truediv__ = Mock(return_value=Mock(parent=Mock(mkdir=Mock())))

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
