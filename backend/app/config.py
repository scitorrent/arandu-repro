"""Application configuration."""

import tempfile
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
    artifacts_base_path: Path = Path(tempfile.gettempdir()) / "arandu" / "artifacts"
    temp_repos_path: Path = Path(tempfile.gettempdir()) / "arandu" / "repos"

    # Security
    docker_user: str = "arandu-user"
    docker_user_uid: int = 1000
    docker_allowlist_domains: list[
        str
    ] = (
        []
    )  # Reserved for future use: Allowed domains for network access (currently not implemented; empty = no network)

    # API
    api_base_url: str = "http://localhost:8000"
    web_origin: str = "http://localhost:3000"  # Next.js frontend origin

    # Review MVP settings
    reviews_base_path: Path = Path(tempfile.gettempdir()) / "arandu" / "reviews"  # Storage for review artifacts
    max_pdf_size_mb: int = 25
    review_timeout_seconds: int = 90
    pdf_parsing_timeout_seconds: int = 30

    # Papers storage
    papers_base_path: Path = Path(tempfile.gettempdir()) / "arandu" / "papers"
    rag_enabled: bool = True
    arxiv_enabled: bool = True
    crossref_enabled: bool = True
    crossref_mailto: str = "contact@arandu.org"  # For Crossref API
    rag_embedding_model: str = "all-MiniLM-L6-v2"  # Embedding model for RAG
    rag_dense_weight: float = 0.5  # Weight for dense search in hybrid (1-alpha for BM25)
    rag_top_k: int = 5  # Number of citations to return per claim
    rag_min_score: float = 0.3  # Minimum score threshold

    # LLM / Gemini AI settings
    gcp_project_id: str = "tough-valve-465919-m9"  # Project ID where service account exists
    gemini_api_key: str = ""  # Set via GEMINI_API_KEY env var
    gemini_model: str = "gemini-2.5-flash-lite"
    llm_enabled: bool = True  # Enable LLM features (narrative generation, etc.)

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
