"""Custom exceptions."""


class RepoCloneError(Exception):
    """Error cloning repository."""

    ...


class NoEnvironmentDetectedError(Exception):
    """No environment files detected."""

    ...


class DockerBuildError(Exception):
    """Docker build failed."""

    ...


class ExecutionError(Exception):
    """Command execution failed."""

    ...


class ExecutionTimeoutError(Exception):
    """Execution exceeded timeout."""

    ...
