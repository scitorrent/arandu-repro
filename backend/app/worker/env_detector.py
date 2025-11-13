"""Environment detection utilities."""

import logging
from pathlib import Path
from typing import Any

import yaml

from app.utils.errors import NoEnvironmentDetectedError
from app.utils.logging import log_step

logger = logging.getLogger(__name__)


class Dependency:
    """Represents a single dependency."""

    def __init__(self, name: str, version: str | None = None):
        self.name = name
        self.version = version

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {"name": self.name}
        if self.version:
            result["version"] = self.version
        return result

    def format_for_pip(self) -> str:
        """
        Format dependency for pip install command.

        Returns dependency string with proper version operator.
        Checks for existing operators (==, >=, <=, !=, ~=, >, <) and avoids
        double operators. Longer operators are checked first to avoid false matches.

        Returns:
            Formatted dependency string (e.g., "numpy==1.24.0" or "torch>=2.0.0")
        """
        if not self.version:
            return self.name

        # Check if version already contains any operator (not just at start)
        # This handles edge cases like "1>=2.0" where operator is in the middle
        version_operators = ("==", ">=", "<=", "!=", "~=", ">", "<")
        if any(op in self.version for op in version_operators):
            return f"{self.name}{self.version}"
        else:
            return f"{self.name}=={self.version}"


class EnvironmentInfo:
    """Represents detected environment information."""

    def __init__(
        self,
        env_type: str,
        dependencies: list[Dependency],
        detected_files: list[str],
        base_image: str = "python:3.11-slim",
    ):
        self.type = env_type
        self.dependencies = dependencies
        self.detected_files = detected_files
        self.base_image = base_image

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "type": self.type,
            "dependencies": [dep.to_dict() for dep in self.dependencies],
            "detected_files": self.detected_files,
            "base_image": self.base_image,
        }


def detect_environment(repo_path: Path, job_id: str) -> EnvironmentInfo:
    """
    Detect Python environment from repository files.

    Checks for:
    - requirements.txt (pip)
    - environment.yml (conda)
    - pyproject.toml (poetry/pip)
    - Pipfile (pipenv)

    Args:
        repo_path: Path to cloned repository
        job_id: Job ID for logging

    Returns:
        EnvironmentInfo with type, dependencies, detected files

    Raises:
        NoEnvironmentDetectedError: If no dependency files found
    """
    with log_step(job_id, "detect_environment", repo_path=str(repo_path)):
        detected_files: list[str] = []
        dependencies: list[Dependency] = []
        env_type: str | None = None
        base_image = "python:3.11-slim"

        # Check for requirements.txt (pip)
        requirements_txt = repo_path / "requirements.txt"
        if requirements_txt.exists():
            detected_files.append("requirements.txt")
            env_type = "pip"
            dependencies = _parse_requirements_txt(requirements_txt)
            logger.info(
                f"Detected pip environment from requirements.txt: {len(dependencies)} dependencies"
            )

        # Check for environment.yml (conda)
        environment_yml = repo_path / "environment.yml"
        if environment_yml.exists():
            detected_files.append("environment.yml")
            if env_type is None:
                env_type = "conda"
                dependencies = _parse_environment_yml(environment_yml)
                logger.info(
                    f"Detected conda environment from environment.yml: {len(dependencies)} dependencies"
                )

        # Check for pyproject.toml (poetry/pip)
        pyproject_toml = repo_path / "pyproject.toml"
        if pyproject_toml.exists():
            detected_files.append("pyproject.toml")
            if env_type is None:
                env_type = "poetry"
                dependencies = _parse_pyproject_toml(pyproject_toml)
                logger.info(
                    f"Detected poetry/pip environment from pyproject.toml: {len(dependencies)} dependencies"
                )

        # Check for Pipfile (pipenv)
        pipfile = repo_path / "Pipfile"
        if pipfile.exists():
            detected_files.append("Pipfile")
            if env_type is None:
                env_type = "pipenv"
                dependencies = _parse_pipfile(pipfile)
                logger.info(
                    f"Detected pipenv environment from Pipfile: {len(dependencies)} dependencies"
                )

        if env_type is None:
            raise NoEnvironmentDetectedError(
                "No environment files detected. Supported: requirements.txt, environment.yml, pyproject.toml, Pipfile"
            )

        return EnvironmentInfo(
            env_type=env_type,
            dependencies=dependencies,
            detected_files=detected_files,
            base_image=base_image,
        )


def _parse_requirements_txt(requirements_path: Path) -> list[Dependency]:
    """Parse requirements.txt file."""
    dependencies: list[Dependency] = []
    with open(requirements_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Handle various formats:
            # package==1.0.0
            # package>=1.0.0
            # package~=1.0.0
            # package
            parts = line.split()
            if not parts:
                continue

            spec = parts[0]
            # Parse all valid pip version specifiers
            # Check longer operators first to avoid false matches
            if "==" in spec:
                name, version = spec.split("==", 1)
                dependencies.append(Dependency(name=name.strip(), version=f"=={version.strip()}"))
            elif ">=" in spec:
                name, version = spec.split(">=", 1)
                dependencies.append(Dependency(name=name.strip(), version=f">={version.strip()}"))
            elif "<=" in spec:
                name, version = spec.split("<=", 1)
                dependencies.append(Dependency(name=name.strip(), version=f"<={version.strip()}"))
            elif "!=" in spec:
                name, version = spec.split("!=", 1)
                dependencies.append(Dependency(name=name.strip(), version=f"!={version.strip()}"))
            elif "~=" in spec:
                name, version = spec.split("~=", 1)
                dependencies.append(Dependency(name=name.strip(), version=f"~={version.strip()}"))
            elif ">" in spec and ">=" not in spec:  # Check > only if >= not present
                name, version = spec.split(">", 1)
                dependencies.append(Dependency(name=name.strip(), version=f">{version.strip()}"))
            elif "<" in spec and "<=" not in spec:  # Check < only if <= not present
                name, version = spec.split("<", 1)
                dependencies.append(Dependency(name=name.strip(), version=f"<{version.strip()}"))
            else:
                # No version specified
                dependencies.append(Dependency(name=spec.strip()))

    return dependencies


def _parse_environment_yml(environment_path: Path) -> list[Dependency]:
    """Parse environment.yml file (conda)."""
    dependencies: list[Dependency] = []
    try:
        with open(environment_path) as f:
            data = yaml.safe_load(f)
            if not isinstance(data, dict):
                return dependencies

            # Check for dependencies list
            deps = data.get("dependencies", [])
            for dep in deps:
                if isinstance(dep, str):
                    # Format: "package=1.0.0" or "package"
                    if "=" in dep:
                        name, version = dep.split("=", 1)
                        dependencies.append(Dependency(name=name.strip(), version=version.strip()))
                    else:
                        dependencies.append(Dependency(name=dep.strip()))
                elif isinstance(dep, dict):
                    # pip dependencies in conda env
                    if "pip" in dep:
                        pip_deps = dep["pip"]
                        if isinstance(pip_deps, list):
                            for pip_dep in pip_deps:
                                if isinstance(pip_dep, str):
                                    if "==" in pip_dep:
                                        name, version = pip_dep.split("==", 1)
                                        dependencies.append(
                                            Dependency(name=name.strip(), version=version.strip())
                                        )
                                    else:
                                        dependencies.append(Dependency(name=pip_dep.strip()))

    except Exception as e:
        logger.warning(f"Error parsing environment.yml: {e}")
        raise NoEnvironmentDetectedError(f"Failed to parse environment.yml: {str(e)}")

    return dependencies


def _parse_pyproject_toml(pyproject_path: Path) -> list[Dependency]:
    """Parse pyproject.toml file (poetry/pip)."""
    dependencies: list[Dependency] = []
    try:
        import tomli

        with open(pyproject_path, "rb") as f:
            data = tomli.load(f)

        # Check for poetry dependencies
        if "tool" in data and "poetry" in data["tool"]:
            poetry_deps = data["tool"]["poetry"].get("dependencies", {})
            for name, spec in poetry_deps.items():
                if name == "python":
                    continue
                if isinstance(spec, str):
                    dependencies.append(Dependency(name=name, version=spec))
                elif isinstance(spec, dict):
                    version = spec.get("version", "")
                    dependencies.append(Dependency(name=name, version=version))
                else:
                    dependencies.append(Dependency(name=name))

        # Check for project dependencies (PEP 621)
        elif "project" in data and "dependencies" in data["project"]:
            deps = data["project"]["dependencies"]
            for dep in deps:
                if isinstance(dep, str):
                    if "==" in dep:
                        name, version = dep.split("==", 1)
                        dependencies.append(Dependency(name=name.strip(), version=version.strip()))
                    else:
                        dependencies.append(Dependency(name=dep.strip()))

    except ImportError:
        logger.warning("tomli not available, cannot parse pyproject.toml")
        raise NoEnvironmentDetectedError(
            "tomli required to parse pyproject.toml. Install with: pip install tomli"
        )
    except Exception as e:
        logger.warning(f"Error parsing pyproject.toml: {e}")
        raise NoEnvironmentDetectedError(f"Failed to parse pyproject.toml: {str(e)}")

    return dependencies


def _parse_pipfile(pipfile_path: Path) -> list[Dependency]:
    """Parse Pipfile (pipenv)."""
    dependencies: list[Dependency] = []
    try:
        import tomli

        with open(pipfile_path, "rb") as f:
            data = tomli.load(f)

        # Check for packages section
        packages = data.get("packages", {})
        for name, spec in packages.items():
            if isinstance(spec, str):
                dependencies.append(Dependency(name=name, version=spec))
            elif isinstance(spec, dict):
                version = spec.get("version", "")
                dependencies.append(Dependency(name=name, version=version))
            else:
                dependencies.append(Dependency(name=name))

    except ImportError:
        logger.warning("tomli not available, cannot parse Pipfile")
        raise NoEnvironmentDetectedError(
            "tomli required to parse Pipfile. Install with: pip install tomli"
        )
    except Exception as e:
        logger.warning(f"Error parsing Pipfile: {e}")
        raise NoEnvironmentDetectedError(f"Failed to parse Pipfile: {str(e)}")

    return dependencies
