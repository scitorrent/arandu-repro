"""Docker image building utilities."""

import logging
from pathlib import Path

import docker
from docker.errors import BuildError, DockerException

from app.config import settings
from app.utils.errors import DockerBuildError
from app.utils.logging import log_step
from app.worker.env_detector import EnvironmentInfo

logger = logging.getLogger(__name__)


def build_image(
    repo_path: Path,
    env_info: EnvironmentInfo,
    job_id: str,
) -> str:
    """
    Build Docker image from repository and environment info.

    Creates a Dockerfile dynamically based on detected environment.
    Applies security constraints:
    - Non-root user (arandu-user, UID 1000)
    - Base image: python:3.11-slim

    Args:
        repo_path: Path to cloned repository
        env_info: Detected environment information
        job_id: Job ID for image tagging

    Returns:
        Docker image tag (e.g., "arandu-job-{job_id}:latest")

    Raises:
        DockerBuildError: If build fails
    """
    with log_step(job_id, "build_docker_image", env_type=env_info.type):
        image_tag = f"arandu-job-{job_id}:latest"

        try:
            # Initialize Docker client
            client = docker.from_env()

            # Generate Dockerfile
            dockerfile_content = _generate_dockerfile(env_info)

            # Write Dockerfile to repo
            dockerfile_path = repo_path / "Dockerfile.arandu"
            dockerfile_path.write_text(dockerfile_content)
            logger.info(f"Generated Dockerfile at {dockerfile_path}")

            # Build image
            logger.info(f"Building Docker image: {image_tag}")
            image, build_logs = client.images.build(
                path=str(repo_path),
                dockerfile=str(dockerfile_path),
                tag=image_tag,
                rm=True,  # Remove intermediate containers
                forcerm=True,  # Always remove intermediate containers
            )

            # Log build output
            for log_line in build_logs:
                if "stream" in log_line:
                    logger.debug(f"Docker build: {log_line['stream'].strip()}")

            logger.info(f"Successfully built image: {image_tag}")
            return image_tag

        except BuildError as e:
            error_msg = f"Docker build failed: {str(e)}"
            logger.error(error_msg)
            raise DockerBuildError(error_msg) from e
        except DockerException as e:
            error_msg = f"Docker error: {str(e)}"
            logger.error(error_msg)
            raise DockerBuildError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error during Docker build: {str(e)}"
            logger.error(error_msg)
            raise DockerBuildError(error_msg) from e


def _generate_dockerfile(env_info: EnvironmentInfo) -> str:
    """
    Generate Dockerfile content based on environment info.

    Args:
        env_info: Environment information

    Returns:
        Dockerfile content as string
    """
    lines = [
        f"FROM {env_info.base_image}",
        "",
        "# Create non-root user",
        f"RUN useradd -m -u {settings.docker_user_uid} {settings.docker_user}",
        "",
        "# Set working directory",
        "WORKDIR /workspace",
        "",
    ]

    # Install dependencies based on environment type
    if env_info.type == "pip":
        # Generate pip install command
        deps = []
        for dep in env_info.dependencies:
            if dep.version:
                # Version may already include ==, >=, etc.
                if dep.version.startswith(("==", ">=", "~=", "<=", "!=", ">", "<")):
                    deps.append(f"{dep.name}{dep.version}")
                else:
                    deps.append(f"{dep.name}=={dep.version}")
            else:
                deps.append(dep.name)

        if deps:
            lines.append("# Install Python dependencies")
            lines.append(f"RUN pip install --no-cache-dir {' '.join(deps)}")
            lines.append("")

    elif env_info.type == "conda":
        # For conda, we'd need conda installed in the base image
        # For v0, convert conda deps to pip or use conda base image
        lines.append("# Install conda dependencies")
        lines.append("# Note: Converting conda deps to pip for v0")
        deps = []
        for dep in env_info.dependencies:
            if dep.version and "=" in dep.version:
                # Extract version from conda format (numpy=1.24.0)
                version = dep.version.split("=")[-1] if "=" in dep.version else None
                if version:
                    deps.append(f"{dep.name}=={version}")
                else:
                    deps.append(dep.name)
            else:
                deps.append(dep.name)

        if deps:
            lines.append(f"RUN pip install --no-cache-dir {' '.join(deps)}")
            lines.append("")

    elif env_info.type in ("poetry", "pipenv"):
        # For poetry/pipenv, copy dependency files and install
        if "pyproject.toml" in env_info.detected_files:
            lines.append("# Install Poetry dependencies")
            lines.append("RUN pip install poetry")
            lines.append("COPY pyproject.toml .")
            lines.append("RUN poetry install --no-dev")
            lines.append("")
        elif "Pipfile" in env_info.detected_files:
            lines.append("# Install Pipenv dependencies")
            lines.append("RUN pip install pipenv")
            lines.append("COPY Pipfile Pipfile.lock* ./")
            lines.append("RUN pipenv install --deploy")
            lines.append("")

    # Copy repository files
    lines.append("# Copy repository files")
    lines.append("COPY . .")
    lines.append("")

    # Change ownership to non-root user
    lines.append("# Change ownership to non-root user")
    lines.append(f"RUN chown -R {settings.docker_user}:{settings.docker_user} /workspace")
    lines.append("")

    # Switch to non-root user
    lines.append("# Switch to non-root user")
    lines.append(f"USER {settings.docker_user}")
    lines.append("")

    # Default command (can be overridden)
    lines.append("# Default command")
    lines.append('CMD ["python", "--version"]')

    return "\n".join(lines)


def cleanup_image(image_tag: str, job_id: str) -> None:
    """
    Clean up Docker image.

    Args:
        image_tag: Docker image tag to remove
        job_id: Job ID for logging
    """
    try:
        client = docker.from_env()
        client.images.remove(image_tag, force=True)
        logger.info(f"Removed Docker image: {image_tag}")
    except Exception as e:
        logger.warning(f"Failed to remove Docker image {image_tag}: {str(e)}")
