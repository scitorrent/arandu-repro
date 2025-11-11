"""Custom exceptions."""


class RepoCloneError(Exception):
    """Error cloning repository."""

    pass


class NoEnvironmentDetectedError(Exception):
    """No environment files detected."""

    pass


class DockerBuildError(Exception):
    """Docker build failed."""

    pass


class ExecutionError(Exception):
    """Command execution failed."""

    pass


class ExecutionTimeoutError(Exception):
    """Execution exceeded timeout."""

    pass
