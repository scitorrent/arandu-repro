"""Application configuration."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = "sqlite:///./arandu.db"

    # Redis / Queue
    redis_url: str = "redis://localhost:6379/0"

    # Docker
    docker_socket: str = "unix:///var/run/docker.sock"
    docker_cpu_limit: float = 2.0
    docker_memory_limit: str = "4g"
    docker_network_mode: str = "none"  # "none" (default) or "bridge" with allowlist
    docker_readonly_rootfs: bool = True  # Read-only root filesystem when viable

    # Execution
    default_timeout_seconds: int = 1800  # 30 minutes
    max_log_size_bytes: int = 1_000_000  # 1MB

    # Storage
    artifacts_base_path: Path = Path("/var/arandu/artifacts")
    temp_repos_path: Path = Path("/tmp/arandu/repos")

    # Security
    docker_user: str = "arandu-user"
    docker_user_uid: int = 1000
    docker_allowlist_domains: list[
        str
    ] = []  # Allowed domains for network access (empty = no network)

    # API
    api_base_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
