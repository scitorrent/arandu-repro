"""Command execution in Docker containers."""

import logging
import time
from datetime import UTC, datetime
from pathlib import Path

import docker
from docker.errors import ContainerError, DockerException
from pydantic import BaseModel

from app.config import settings
from app.utils.errors import ExecutionError, ExecutionTimeoutError
from app.utils.logging import log_step

logger = logging.getLogger(__name__)


class ExecutionResult(BaseModel):
    """Result of command execution."""

    exit_code: int
    stdout: str  # Truncated preview (for DB storage)
    stderr: str  # Truncated preview (for DB storage)
    duration_seconds: float
    started_at: datetime  # Actual start time of execution
    logs_path: Path | None = None  # Path to full logs file (stdout + stderr combined)


def execute_command(
    image_tag: str,
    command: str,
    repo_path: Path,
    artifacts_dir: Path,
    job_id: str,
    timeout_seconds: int | None = None,
) -> ExecutionResult:
    """
    Execute command in Docker container with security constraints.

    Security constraints enforced:
    - Non-root user (arandu-user, UID 1000)
    - CPU limit (default: 2.0 cores)
    - Memory limit (default: 4GB)
    - Network: none (no network access)
    - Isolated volumes (only repo_path and artifacts_dir mounted)

    Args:
        image_tag: Docker image to run
        command: Command to execute
        repo_path: Repository path (mounted as working directory)
        artifacts_dir: Directory for artifacts (mounted)
        job_id: Job ID for logging
        timeout_seconds: Execution timeout (default: from settings)

    Returns:
        ExecutionResult with exit code, stdout, stderr, duration, logs_path

    Raises:
        ExecutionTimeoutError: If execution exceeds timeout
        ExecutionError: If container fails to start or execute
    """
    if timeout_seconds is None:
        timeout_seconds = settings.default_timeout_seconds

    with log_step(job_id, "execute_command", command=command, timeout=timeout_seconds):
        start_time = time.time()
        started_at = datetime.now(UTC)  # Capture actual start time

        # Ensure artifacts directory exists
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Create logs file
        logs_file = artifacts_dir / "logs" / "combined.log"
        logs_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Initialize Docker client
            client = docker.from_env()

            # Prepare volume mounts
            volumes = {
                str(repo_path): {"bind": "/workspace", "mode": "ro"},  # Read-only repo
                str(artifacts_dir): {"bind": "/artifacts", "mode": "rw"},  # Writable artifacts
            }

            # Validate security constraints are set (BEFORE parsing/using them)
            docker_user_str = str(settings.docker_user or "").strip().lower()
            docker_user_uid = getattr(settings, "docker_user_uid", None)
            if (
                not docker_user_str
                or docker_user_str == "root"
                or docker_user_str == "0"
                or (docker_user_uid is not None and docker_user_uid == 0)
            ):
                raise ExecutionError("Security violation: containers must run as non-root user")
            if settings.docker_cpu_limit <= 0:
                raise ExecutionError("Security violation: CPU limit must be greater than 0")
            if not settings.docker_memory_limit or settings.docker_memory_limit.strip() == "":
                raise ExecutionError("Security violation: memory limit must be set")
            if settings.docker_network_mode not in ("none", "bridge"):
                raise ExecutionError(
                    f"Security violation: invalid network mode '{settings.docker_network_mode}'"
                )

            # Prepare security constraints
            # CPU limit (in nano CPUs: 2.0 cores = 2000000000)
            cpu_quota = int(settings.docker_cpu_limit * 1_000_000_000)
            cpu_period = 1_000_000  # Default period

            # Memory limit (convert string like "4g" to bytes)
            memory_bytes = _parse_memory_limit(settings.docker_memory_limit)

            # Run container with security constraints
            logger.info(
                f"Running container with security constraints: "
                f"user={settings.docker_user}, "
                f"cpu={settings.docker_cpu_limit}, "
                f"memory={settings.docker_memory_limit}, "
                f"network={settings.docker_network_mode}, "
                f"readonly_rootfs={settings.docker_readonly_rootfs}"
            )

            # Prepare container run arguments
            run_kwargs = {
                "image": image_tag,
                "command": command,
                "detach": True,
                "user": settings.docker_user,
                "network_mode": settings.docker_network_mode,
                "cpu_quota": cpu_quota,
                "cpu_period": cpu_period,
                "mem_limit": memory_bytes,
                "volumes": volumes,
                "working_dir": "/workspace",
                "remove": False,  # Keep container for logs
            }

            # Add read-only root filesystem if enabled
            if settings.docker_readonly_rootfs:
                run_kwargs["read_only"] = True

            container = client.containers.run(**run_kwargs)

            # Wait for container with timeout
            try:
                wait_result = container.wait(timeout=timeout_seconds)
                # container.wait() returns a dict with 'StatusCode' key according to Docker SDK
                # According to Docker SDK documentation, this should always be a dict
                assert isinstance(
                    wait_result, dict
                ), f"container.wait() returned unexpected type: {type(wait_result)}, value: {wait_result}"
                exit_code = wait_result.get("StatusCode", 1)
            except Exception as e:
                # Container may have timed out or crashed
                logger.warning(f"Container wait failed: {e}")
                # Try to stop the container
                try:
                    container.stop(timeout=5)
                except Exception:
                    pass
                # Check if it's a timeout
                elapsed = time.time() - start_time
                if elapsed >= timeout_seconds:
                    raise ExecutionTimeoutError(
                        f"Execution exceeded timeout of {timeout_seconds} seconds"
                    )
                raise ExecutionError(f"Container execution failed: {str(e)}")

            # Get logs
            stdout_logs = container.logs(stdout=True, stderr=False).decode(
                "utf-8", errors="replace"
            )
            stderr_logs = container.logs(stdout=False, stderr=True).decode(
                "utf-8", errors="replace"
            )

            # Combine logs and write to file
            combined_logs = f"=== STDOUT ===\n{stdout_logs}\n=== STDERR ===\n{stderr_logs}"
            logs_file.write_text(combined_logs, encoding="utf-8")

            # Truncate logs for DB storage
            max_log_size = settings.max_log_size_bytes
            stdout_truncated = _truncate_log(stdout_logs, max_log_size // 2)
            stderr_truncated = _truncate_log(stderr_logs, max_log_size // 2)

            # Calculate duration
            duration_seconds = time.time() - start_time

            # Remove container
            try:
                container.remove()
            except Exception as e:
                logger.warning(f"Failed to remove container: {e}")

            result = ExecutionResult(
                exit_code=exit_code,
                stdout=stdout_truncated,
                stderr=stderr_truncated,
                duration_seconds=duration_seconds,
                started_at=started_at,
                logs_path=logs_file,
            )

            logger.info(
                f"Execution completed: exit_code={exit_code}, "
                f"duration={duration_seconds:.2f}s, "
                f"logs_path={logs_file}"
            )

            return result

        except ExecutionTimeoutError:
            raise
        except ExecutionError:
            raise
        except ContainerError as e:
            error_msg = f"Container error: {str(e)}"
            logger.error(error_msg)
            raise ExecutionError(error_msg) from e
        except DockerException as e:
            error_msg = f"Docker error: {str(e)}"
            logger.error(error_msg)
            raise ExecutionError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error during execution: {str(e)}"
            logger.error(error_msg)
            raise ExecutionError(error_msg) from e


def _parse_memory_limit(memory_str: str) -> int:
    """
    Parse memory limit string to bytes.

    Supports: "4g", "512m", "1024", etc.
    """
    memory_str = memory_str.lower().strip()
    if memory_str.endswith("g"):
        return int(float(memory_str[:-1]) * 1024 * 1024 * 1024)
    elif memory_str.endswith("m"):
        return int(float(memory_str[:-1]) * 1024 * 1024)
    elif memory_str.endswith("k"):
        return int(float(memory_str[:-1]) * 1024)
    else:
        # Assume bytes
        return int(memory_str)


def _truncate_log(log_content: str, max_bytes: int) -> str:
    """Truncate log content to max_bytes, preserving UTF-8 encoding."""
    if len(log_content.encode("utf-8")) <= max_bytes:
        return log_content

    # Truncate byte by byte until we fit
    truncated = log_content
    while len(truncated.encode("utf-8")) > max_bytes:
        truncated = truncated[:-1]

    # Add truncation indicator
    return truncated + "\n... [truncated]"
