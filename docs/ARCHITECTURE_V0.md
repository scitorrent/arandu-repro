# Arandu Repro v0 – Architecture

## 1. Overview

Arandu Repro v0 is a single-service application with three main processes:
1. **API Service** (FastAPI) - handles HTTP requests, job creation, status queries, artifact downloads
2. **Worker Process** (async) - processes jobs: clones repos, detects environments, builds containers, executes commands, generates artifacts
3. **Frontend** (Next.js) - minimal web UI for job submission and viewing results

The system uses a job queue (Redis + RQ) to decouple API requests from long-running worker tasks. All state is persisted in a database (PostgreSQL/SQLite). Artifacts (reports, notebooks, badges) are stored on the local filesystem.

**Key design principles:**
- Simple, single-repo monolith (no microservices)
- Async job processing via queue
- Containerized execution for isolation
- Minimal dependencies and complexity
- Focus on Python-only environments for v0

---

## 2. Components

### 2.1 API Service (FastAPI)

**Location:** `backend/app/api/`

**Responsibilities:**
- HTTP request handling
- Input validation
- Database operations (via ORM)
- Job queue enqueueing
- Artifact file serving

**Key endpoints:**
- `GET /health` - health check
- `POST /jobs` - create new job
- `GET /jobs/{id}` - get job details
- `GET /jobs/{id}/status` - get job status (lightweight)
- `GET /jobs/{id}/artifacts/{type}` - download artifact (report/notebook/badge)
- `GET /jobs` - list all jobs (Sprint 2)

**Dependencies:**
- FastAPI
- SQLAlchemy (ORM)
- Pydantic (validation)
- RQ (job queue client)

### 2.2 Job Queue & Worker

**Location:** `backend/app/worker/`

**Queue:** Redis + RQ (simple, sufficient for v0)

**Worker Process Responsibilities:**
1. Dequeue jobs from Redis queue
2. Update job status: `pending` → `running`
3. Execute job pipeline (see below)
4. Update job status: `running` → `completed` or `failed`
5. Store artifacts and update database

**Worker Pipeline Steps:**
1. **Clone repo** (`backend/app/worker/repo_cloner.py`)
2. **Detect environment** (`backend/app/worker/env_detector.py`)
3. **Build Docker image** (`backend/app/worker/docker_builder.py`)
4. **Execute command** (`backend/app/worker/executor.py`)
5. **Generate artifacts** (`backend/app/worker/artifact_generator.py`)
6. **Cleanup** (temp dirs, Docker images)

### 2.3 Environment Detector & Builder

**Location:** `backend/app/worker/env_detector.py`, `backend/app/worker/docker_builder.py`

**Environment Detection:**
- Scans cloned repo for dependency files:
  - `requirements.txt` (pip)
  - `environment.yml` (conda)
  - `pyproject.toml` (poetry/pip)
  - `Pipfile` (pipenv)
- Extracts dependencies and versions
- Returns structured dependency list

**Docker Builder:**
- Creates Dockerfile dynamically based on detected environment
- Uses base Python image (python:3.11-slim)
- Installs dependencies via detected method (pip/conda)
- Tags image uniquely per job: `arandu-job-{job_id}:latest`
- Applies security constraints (non-root user, resource limits)

### 2.4 Executor (Docker Runner)

**Location:** `backend/app/worker/executor.py`

**Responsibilities:**
- Run Docker container with built image
- Execute user-provided command (or default)
- Capture stdout, stderr, exit code
- Enforce timeout (default: 30 minutes)
- Apply security constraints:
  - Non-root user
  - CPU/memory limits
  - Network restrictions
  - Volume mounts (working dir + artifacts only)

**Security:**
- Containers run as non-root user (`arandu-user`, UID 1000)
- Resource limits: CPU (2 cores), Memory (4GB) - configurable
- Network: Default is `none` (no network access). Enabling network access (e.g., to download models or data) is a future, opt-in capability controlled via configuration, not part of v0's default behavior
- Read-only root filesystem where possible
- No host filesystem access outside working directory

### 2.5 Report & Notebook Generator

**Location:** `backend/app/worker/artifact_generator.py`

**Report Generator:**
- Input: job metadata, environment info, execution results, logs
- Output: Markdown report (Sprint 1), HTML report (Sprint 2)
- Includes: metadata, environment summary, execution status, logs excerpt, timestamps

**Notebook Generator:**
- Input: job metadata, detected environment, repo info
- Output: Jupyter notebook (.ipynb) with cells for:
  - Environment setup
  - Dependency installation
  - Code execution
  - Error handling
- Colab-compatible format

**Badge Generator:**
- Input: job status, job URL
- Output: Markdown badge snippet: `[![Reproducible](badge_url)](job_url)`
- Status colors: green (success), yellow (partial), red (failed)

### 2.6 Database (SQLAlchemy + Alembic)

**Location:** `backend/app/models/`, `backend/alembic/`

**ORM:** SQLAlchemy
**Migrations:** Alembic

**Database choice:**
- Development/Testing: SQLite (simple, no setup)
- Production: PostgreSQL (better concurrency, features)

**Connection:** Via SQLAlchemy engine, connection pooling

### 2.7 Frontend (Next.js)

**Location:** `frontend/`

**Tech Stack:**
- Next.js 14+ (App Router)
- TypeScript
- Minimal styling (Tailwind CSS or similar)

**Pages:**
- `/` - Home / Job submission form
- `/jobs` - Jobs list view
- `/jobs/[id]` - Job detail / status page

**API Integration:**
- Calls backend API endpoints
- Polls job status if pending/running
- Downloads artifacts via API

---

## 3. Data Model

### 3.1 Job

**Table:** `jobs`

**Fields:**
- `id` (UUID, primary key)
- `repo_url` (string, required) - GitHub repo URL
- `arxiv_id` (string, nullable) - Optional arXiv paper ID
- `run_command` (string, nullable) - Command to execute (default: auto-detect)
- `status` (enum, required) - `pending`, `running`, `completed`, `failed`
- `error_message` (text, nullable) - Error message if failed
- `created_at` (timestamp)
- `updated_at` (timestamp)

**Relationships:**
- One-to-one: `runs` (in v0, each job has exactly one run)
- One-to-many: `artifacts`

**Status transitions:**
- `pending` → `running` (when worker picks up job)
- `running` → `completed` (on success)
- `running` → `failed` (on error)

**v0 Constraint:** In v0, each Job has exactly one Run. The API and worker logic assume a single-run-per-job model. Multiple runs per job are a Phase 2+ concern.

### 3.2 Run / Execution

**Table:** `runs`

**Fields:**
- `id` (UUID, primary key)
- `job_id` (UUID, foreign key → jobs.id, unique in v0)
- `exit_code` (integer, nullable) - Process exit code
- `stdout` (text, nullable) - Truncated stdout preview (for quick inspection in DB)
- `stderr` (text, nullable) - Truncated stderr preview (for quick inspection in DB)
- `logs_path` (string, nullable) - Filesystem path to full logs file (stdout + stderr combined)
- `started_at` (timestamp)
- `completed_at` (timestamp, nullable)
- `duration_seconds` (float, nullable) - Execution duration

**v0 Constraint:** In v0, each Job has exactly one Run. The relationship is one-to-one. Multiple runs per job are a Phase 2+ feature.

**Log Storage Policy:**
- Full logs (stdout + stderr) are stored as files under `{artifacts_base_path}/{job_id}/logs/combined.log`
- The database stores only truncated snippets in `stdout`/`stderr` fields (max ~1MB total) for quick inspection
- The `logs_path` field points to the full logs file location
- The database is NOT used to store multi-MB logs; all full logs live on the filesystem

### 3.3 Artifact

**Table:** `artifacts`

**Fields:**
- `id` (UUID, primary key)
- `job_id` (UUID, foreign key → jobs.id)
- `type` (enum, required) - `report`, `notebook`, `badge`
- `format` (string, required) - `markdown`, `html`, `ipynb`, `svg`, etc.
- `content_path` (string, required) - Filesystem path to artifact file
- `content_size` (integer, nullable) - File size in bytes
- `created_at` (timestamp)

**Artifact types:**
- `report` - Reproducibility report (markdown or HTML)
- `notebook` - Jupyter notebook (.ipynb)
- `badge` - Badge snippet (markdown or SVG)

### 3.4 Environment Info (Stored in Job or separate table)

**Option A:** Store as JSON field in `jobs` table
**Option B:** Separate `job_environments` table

**For v0, use Option A (JSON field):**

**Field in `jobs` table:**
- `detected_environment` (JSON, nullable) - Structured dependency list:
  ```json
  {
    "type": "pip",
    "dependencies": [
      {"name": "numpy", "version": "1.24.0"},
      {"name": "torch", "version": "2.0.0"}
    ],
    "detected_files": ["requirements.txt"]
  }
  ```

---

## 4. Interfaces / Contracts

### 4.1 API Endpoints

#### `POST /jobs`

**Request:**
```python
{
  "repo_url": str,  # Required, must be valid GitHub URL
  "arxiv_id": str | None,  # Optional
  "run_command": str | None  # Optional, default: auto-detect
}
```

**Response (201 Created):**
```python
{
  "job_id": str,  # UUID
  "status": "pending",
  "created_at": str  # ISO 8601 timestamp
}
```

**Errors:**
- `400 Bad Request` - Invalid input (invalid URL, missing repo_url)
- `500 Internal Server Error` - Database/queue error

#### `GET /jobs/{id}`

**Response (200 OK):**
```python
{
  "job_id": str,
  "repo_url": str,
  "arxiv_id": str | None,
  "run_command": str | None,
  "status": "pending" | "running" | "completed" | "failed",
  "error_message": str | None,
  "created_at": str,
  "updated_at": str,
  "artifacts": [
    {
      "type": "report" | "notebook" | "badge",
      "format": str,
      "download_url": str  # /jobs/{id}/artifacts/{type}
    }
  ] | None  # None if not completed
}
```

**Errors:**
- `404 Not Found` - Job not found

#### `GET /jobs/{id}/status`

**Response (200 OK):**
```python
{
  "job_id": str,
  "status": "pending" | "running" | "completed" | "failed",
  "updated_at": str
}
```

**Lightweight endpoint for polling.**

#### `GET /jobs/{id}/artifacts/{type}`

**Path parameters:**
- `type`: `report`, `notebook`, or `badge`

**Response:**
- File download with appropriate `Content-Type` header
- `200 OK` with file body
- `404 Not Found` if artifact doesn't exist

### 4.2 Internal Function Contracts

#### Repo Cloning

**Module:** `backend/app/worker/repo_cloner.py`

```python
def clone_repo(repo_url: str, target_dir: Path) -> Path:
    """
    Clone GitHub repository to target directory.
    
    Args:
        repo_url: GitHub repository URL
        target_dir: Directory to clone into
        
    Returns:
        Path to cloned repository root
        
    Raises:
        RepoCloneError: If clone fails (invalid URL, network error, etc.)
    """
```

#### Environment Detection

**Module:** `backend/app/worker/env_detector.py`

```python
def detect_environment(repo_path: Path) -> EnvironmentInfo:
    """
    Detect Python environment from repository files.
    
    Args:
        repo_path: Path to cloned repository
        
    Returns:
        EnvironmentInfo with type, dependencies, detected files
        
    Raises:
        NoEnvironmentDetectedError: If no dependency files found
    """
    
class EnvironmentInfo(BaseModel):
    type: str  # "pip", "conda", "poetry", "pipenv"
    dependencies: List[Dependency]
    detected_files: List[str]
    base_image: str  # Docker base image suggestion

class Dependency(BaseModel):
    name: str
    version: str | None
```

#### Docker Image Building

**Module:** `backend/app/worker/docker_builder.py`

```python
def build_image(
    repo_path: Path,
    env_info: EnvironmentInfo,
    job_id: str
) -> str:
    """
    Build Docker image from repository and environment info.
    
    Args:
        repo_path: Path to cloned repository
        env_info: Detected environment information
        job_id: Job ID for image tagging
        
    Returns:
        Docker image tag (e.g., "arandu-job-{job_id}:latest")
        
    Raises:
        DockerBuildError: If build fails
    """
```

#### Command Execution

**Module:** `backend/app/worker/executor.py`

```python
def execute_command(
    image_tag: str,
    command: str,
    repo_path: Path,
    artifacts_dir: Path,
    timeout_seconds: int = 1800
) -> ExecutionResult:
    """
    Execute command in Docker container.
    
    Args:
        image_tag: Docker image to run
        command: Command to execute
        repo_path: Repository path (mounted as working directory)
        artifacts_dir: Directory for artifacts (mounted)
        timeout_seconds: Execution timeout (default: 30 minutes)
        
    Returns:
        ExecutionResult with exit code, stdout, stderr, duration
        
    Raises:
        ExecutionTimeoutError: If execution exceeds timeout
        ExecutionError: If container fails to start
    """
    
class ExecutionResult(BaseModel):
    exit_code: int
    stdout: str  # Truncated preview (for DB storage)
    stderr: str  # Truncated preview (for DB storage)
    duration_seconds: float
    logs_path: Path | None  # Path to full logs file (stdout + stderr combined)
    # Note: logs_path is created during execution and points to the full logs file.
    # The persistence layer stores this path in runs.logs_path.
```

#### Artifact Generation

**Module:** `backend/app/worker/artifact_generator.py`

```python
def generate_report(
    job: Job,
    run: Run,
    env_info: EnvironmentInfo,
    output_path: Path
) -> Path:
    """
    Generate reproducibility report.
    
    Returns:
        Path to generated report file
    """
    
def generate_notebook(
    job: Job,
    env_info: EnvironmentInfo,
    output_path: Path
) -> Path:
    """
    Generate Jupyter notebook template.
    
    Returns:
        Path to generated notebook file
    """
    
def generate_badge(
    job: Job,
    base_url: str,
    output_path: Path
) -> Path:
    """
    Generate badge snippet.
    
    Returns:
        Path to generated badge file
    """
```

### 4.3 Configuration Management

**Module:** `backend/app/config.py`

```python
class Settings(BaseSettings):
    # Database
    database_url: str  # SQLAlchemy connection string
    
    # Redis / Queue
    redis_url: str = "redis://localhost:6379/0"
    
    # Docker
    docker_socket: str = "unix:///var/run/docker.sock"
    docker_cpu_limit: float = 2.0
    docker_memory_limit: str = "4g"
    docker_network_mode: str = "none"  # "none" or "bridge"
    
    # Execution
    default_timeout_seconds: int = 1800  # 30 minutes
    max_log_size_bytes: int = 1_000_000  # 1MB
    
    # Storage
    artifacts_base_path: Path = Path("/var/arandu/artifacts")
    temp_repos_path: Path = Path("/tmp/arandu/repos")
    
    # Security
    docker_user: str = "arandu-user"
    docker_user_uid: int = 1000
    
    # API
    api_base_url: str = "http://localhost:8000"
    
    class Config:
        env_file = ".env"
```

---

## 5. Core Python Modules Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Settings/configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── job.py              # Job SQLAlchemy model
│   │   ├── run.py              # Run SQLAlchemy model
│   │   └── artifact.py         # Artifact SQLAlchemy model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── job.py              # Pydantic schemas for API
│   │   └── artifact.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── jobs.py         # Job endpoints
│   │   │   └── health.py       # Health check
│   │   └── dependencies.py     # FastAPI dependencies (DB session, etc.)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py          # Database session management
│   │   └── base.py             # Base model class
│   ├── worker/
│   │   ├── __init__.py
│   │   ├── main.py             # Worker entry point
│   │   ├── tasks.py            # RQ task definitions
│   │   ├── repo_cloner.py      # Git repo cloning
│   │   ├── env_detector.py     # Environment detection
│   │   ├── docker_builder.py  # Docker image building
│   │   ├── executor.py         # Command execution
│   │   └── artifact_generator.py  # Report/notebook/badge generation
│   └── utils/
│       ├── __init__.py
│       ├── logging.py           # Logging configuration
│       └── errors.py            # Custom exceptions
├── alembic/                     # Database migrations
│   ├── versions/
│   └── env.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── pyproject.toml
├── Dockerfile
└── docker-compose.yml
```

---

## 6. Docker & Deployment Strategy

### 6.1 Development (docker-compose)

**File:** `docker-compose.yml` (repo root)

**Services:**
- `api` - FastAPI backend
- `worker` - RQ worker process
- `db` - PostgreSQL (or SQLite for local dev)
- `redis` - Redis for job queue
- `frontend` - Next.js (dev server or production build)

**Volumes:**
- Database data persistence
- Artifacts directory (shared between API and worker)
- Docker socket (for worker to build/run containers)

### 6.2 Container Security

**Base image:** `python:3.11-slim`

**Security measures:**
- Non-root user in containers (`arandu-user`, UID 1000)
- Resource limits (CPU, memory) via Docker
- Network restrictions (default: `none`, allow specific domains if needed)
- Read-only root filesystem where possible
- Minimal base image (slim variant)
- No unnecessary packages or tools

**Worker container:**
- Requires Docker socket access (mounted as volume: `/var/run/docker.sock`)
- Runs with `--privileged=false`
- **v0 Decision:** Uses Docker socket mounting from the host (`/var/run/docker.sock`)
  - This has security implications (worker container can control host Docker daemon)
  - Acceptable for v0, to be revisited in Phase 2+ for stricter sandboxing
  - Docker-in-Docker (DinD) is a future consideration for better isolation

### 6.3 Artifact Storage

**v0:** Local filesystem
- Base path: `/var/arandu/artifacts` (configurable)
- Structure: `{job_id}/{artifact_type}.{ext}`
- Cleanup: Manual or scheduled job (post-MVP)

**Future (Phase 2):** Object storage (S3, GCS)

---

## 7. Open Questions & Decisions

### 7.1 Resolved Decisions

1. **Queue system:** RQ (simple, sufficient) over Celery
2. **Database:** PostgreSQL for production, SQLite for dev/testing
3. **Frontend:** Next.js (TypeScript) - minimal pages
4. **Container security:** Non-root user, resource limits, network restrictions
5. **Storage:** Local filesystem for v0
6. **Docker socket vs Docker-in-Docker:** **Resolved for v0** - Use Docker socket mounting (`/var/run/docker.sock`)
   - Simpler implementation for v0
   - Security implications documented (worker can control host Docker daemon)
   - Acceptable for v0, to be revisited in Phase 2+ for stricter sandboxing
   - Docker-in-Docker (DinD) moved to future considerations
7. **Log storage strategy:** **Resolved for v0**
   - Full logs stored as files under `{artifacts_base_path}/{job_id}/logs/combined.log`
   - Database stores only truncated snippets (max ~1MB) in `runs.stdout`/`runs.stderr`
   - `runs.logs_path` points to the full logs file
   - Database is NOT used to store multi-MB logs

### 7.2 Pending Decisions

1. **Job retry on failure:**
   - Automatic retry vs. manual only?
   - **Decision:** Manual retry only for v0 (post-MVP: automatic with backoff)

2. **Artifact retention:**
   - How long to keep artifacts?
   - **Decision:** Keep indefinitely for v0, add cleanup job in Phase 2

3. **Default run command:**
   - How to auto-detect default command?
   - **Decision:** Try common patterns: `python main.py`, `python train.py`, `python run.py`, or use repo's README/scripts

### 7.3 Future Considerations (Phase 2+)

- Multi-language support (R, Julia, Node.js)
- User authentication and accounts
- Job prioritization and scheduling
- Advanced monitoring and metrics
- Object storage integration
- API rate limiting
- Job sharing and collaboration
- Multiple runs per job (job history/retries)
- Stricter container sandboxing (Docker-in-Docker or alternative isolation mechanisms)
- Network access configuration (opt-in, controlled network access for downloading models/data)

---

## 8. Implementation Notes

### 8.1 Error Handling

**Strategy:** Fail fast with clear error messages

**Error types:**
- `ValidationError` - Invalid input (400)
- `NotFoundError` - Resource not found (404)
- `RepoCloneError` - Git clone failure
- `NoEnvironmentDetectedError` - No dependency files found
- `DockerBuildError` - Docker build failure
- `ExecutionError` - Command execution failure
- `ExecutionTimeoutError` - Execution exceeded timeout

**Error storage:**
- Store error message in `jobs.error_message`
- Set job status to `failed`
- Log errors with context (job_id, step, exception)

### 8.2 Logging

**Structured logging:**
- Use Python `logging` module with JSON formatter (optional)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Key events: job creation, status transitions, pipeline steps, errors

**Log separation:**
- **System logs:** Arandu's own operations (stored in log files/stdout)
- **Experiment logs:** stdout/stderr from executed commands
  - Full logs stored as files: `{artifacts_base_path}/{job_id}/logs/combined.log`
  - Truncated previews stored in `runs.stdout`/`runs.stderr` (max ~1MB total)
  - Full logs file path stored in `runs.logs_path`
  - Database is NOT used to store multi-MB logs; all full logs live on the filesystem

### 8.3 One Job = One Run (v0 Constraint)

**Implementation constraint for v0:**
- Each Job has exactly one Run. The relationship is one-to-one.
- The API and worker logic assume a single-run-per-job model.
- When creating a Run record, ensure `job_id` has a unique constraint (or enforce in application logic).
- Multiple runs per job (job history, retries, comparisons) are a Phase 2+ concern.
- For v0, if a job needs to be re-run, create a new Job instead of a new Run.

### 8.4 Testing Strategy

**Unit tests:**
- Test individual functions (env detection, artifact generation, etc.)
- Mock external dependencies (Docker, Git, file system)

**Integration tests:**
- Test full pipeline with reference repos (Issue #32)
- Use real Docker containers in tests
- Mark with `@pytest.mark.integration`
- Run separately: `pytest -m integration`

**Test fixtures:**
- Sample GitHub repos (small, public repos for testing)
- Mock Docker responses
- Test database (SQLite in-memory)

---

This architecture document provides a concrete, implementable design for Arandu Repro v0. All components, interfaces, and data models are defined with enough detail for implementation without ambiguity.

