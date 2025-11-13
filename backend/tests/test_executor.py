"""Tests for command execution in containers."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.utils.errors import ExecutionError, ExecutionTimeoutError
from app.worker.executor import ExecutionResult, _parse_memory_limit, _truncate_log, execute_command


def test_parse_memory_limit():
    """Test memory limit parsing."""
    assert _parse_memory_limit("4g") == 4 * 1024 * 1024 * 1024
    assert _parse_memory_limit("512m") == 512 * 1024 * 1024
    assert _parse_memory_limit("1024k") == 1024 * 1024
    assert _parse_memory_limit("1024") == 1024


def test_truncate_log():
    """Test log truncation."""
    short_log = "Short log"
    assert _truncate_log(short_log, 1000) == short_log

    long_log = "x" * 2000
    truncated = _truncate_log(long_log, 100)
    assert len(truncated.encode("utf-8")) <= 100
    assert "[truncated]" in truncated


@patch("app.worker.executor.docker.from_env")
def test_execute_command_success(mock_docker_client, tmp_path: Path):
    """Test successful command execution."""
    # Setup
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()

    # Mock Docker client and container
    mock_client = MagicMock()
    mock_container = MagicMock()
    mock_container.wait.return_value = {"StatusCode": 0}
    mock_container.logs.side_effect = [
        b"stdout output",
        b"stderr output",
    ]
    mock_client.containers.run.return_value = mock_container
    mock_docker_client.return_value = mock_client

    # Execute command
    result = execute_command(
        image_tag="test-image:latest",
        command="python main.py",
        repo_path=repo_path,
        artifacts_dir=artifacts_dir,
        job_id="test-job-1",
        timeout_seconds=60,
    )

    assert isinstance(result, ExecutionResult)
    assert result.exit_code == 0
    assert result.stdout == "stdout output"
    assert result.stderr == "stderr output"
    assert result.duration_seconds > 0
    assert result.logs_path is not None
    assert result.logs_path.exists()

    # Verify security constraints were applied
    mock_client.containers.run.assert_called_once()
    call_kwargs = mock_client.containers.run.call_args[1]
    assert call_kwargs["user"] == "arandu-user"
    assert call_kwargs["network_mode"] == "none"
    assert "cpu_quota" in call_kwargs
    assert "mem_limit" in call_kwargs


@patch("app.worker.executor.docker.from_env")
def test_execute_command_timeout(mock_docker_client, tmp_path: Path):
    """Test command execution timeout."""
    # Setup
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()

    # Mock Docker client and container that times out
    mock_client = MagicMock()
    mock_container = MagicMock()

    def wait_side_effect(*args, **kwargs):
        import time

        time.sleep(0.1)  # Simulate delay
        raise Exception("Timeout")

    mock_container.wait.side_effect = wait_side_effect
    mock_client.containers.run.return_value = mock_container
    mock_docker_client.return_value = mock_client

    # Execute command with short timeout
    with pytest.raises(ExecutionTimeoutError, match="exceeded timeout"):
        execute_command(
            image_tag="test-image:latest",
            command="python main.py",
            repo_path=repo_path,
            artifacts_dir=artifacts_dir,
            job_id="test-job-2",
            timeout_seconds=0.05,  # Very short timeout
        )


@patch("app.worker.executor.docker.from_env")
def test_execute_command_container_error(mock_docker_client, tmp_path: Path):
    """Test container error handling."""
    import docker

    # Setup
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()

    # Mock Docker client to raise ContainerError
    mock_client = MagicMock()
    mock_client.containers.run.side_effect = docker.errors.ContainerError(
        container={}, exit_status=1, command="test", image="test-image"
    )
    mock_docker_client.return_value = mock_client

    # Execute command should raise ExecutionError
    with pytest.raises(ExecutionError, match="Container error"):
        execute_command(
            image_tag="test-image:latest",
            command="python main.py",
            repo_path=repo_path,
            artifacts_dir=artifacts_dir,
            job_id="test-job-3",
        )
