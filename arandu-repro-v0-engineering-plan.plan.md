# Arandu Repro v0 – Execution Plan

## 1. MVP Summary

**Arandu Repro v0** is a minimal service that helps reproduce AI research papers by executing their GitHub code in isolated containers and generating reproducibility artifacts.

**Single hero flow:**
1. User submits a GitHub repo URL (optionally with arXiv ID/paper URL and run command)
2. System clones repo, detects environment dependencies, builds container, executes command
3. System captures logs, metrics, and execution results
4. System generates: markdown/HTML reproducibility report, executable notebook template, optional README badge
5. User views/downloads artifacts via simple web UI or API

**Primary users:** AI researchers publishing papers with GitHub repos, reproducibility advocates

---

## 2. Architecture v0 (High-Level)

### Components

```
┌─────────────┐
│   Web UI    │ (minimal frontend)
└──────┬──────┘
       │ HTTP
┌──────▼─────────────────────────────────────┐
│         API Service (FastAPI)              │
│  - POST /jobs                              │
│  - GET /jobs/{id}                          │
│  - GET /jobs/{id}/status                   │
│  - GET /jobs/{id}/artifacts/{type}         │
└──────┬─────────────────────────────────────┘
       │
       ├──► Job Queue (Redis/RQ or in-memory)
       │
       └──► Database (PostgreSQL or SQLite)
              │
              └──► Job, Run, Artifact tables

┌─────────────────────────────────────────────┐
│         Worker Process (async)              │
│  1. Clone repo                              │
│  2. Detect environment (requirements.txt,   │
│     environment.yml, pyproject.toml, etc.)  │
│  3. Build Docker image with dependencies    │
│  4. Execute run_command in container        │
│  5. Capture logs, exit code, metrics        │
│  6. Generate report (markdown/HTML)         │
│  7. Generate notebook template              │
│  8. Generate badge snippet                  │
│  9. Store artifacts, update job status      │
└─────────────────────────────────────────────┘
```

### Technologies

- **Backend:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL (production) or SQLite (dev/testing)
- **Task Queue:** Redis + RQ (simple) or Celery (if more features needed)
- **Containerization:** Docker + docker-compose
- **ORM:** SQLAlchemy with Alembic for migrations
- **Frontend:** Next.js (TypeScript), minimal pages for job submission, job list, job detail
- **Storage:** Local filesystem for artifacts (S3/object storage deferred to Phase 2)

### Data Flow

1. User → API: `POST /jobs` with `repo_url`, optional `arxiv_id`, `run_command`
2. API → DB: Create Job record (status: `pending`)
3. API → Queue: Enqueue job processing task
4. Worker: Process job (clone, detect, build, execute, generate)
5. Worker → DB: Update Job status, create Run record, create Artifact records
6. User → API: `GET /jobs/{id}` to poll status and retrieve artifacts

---

## 3. Sprints

### Sprint 0 – Foundation (Week 1-2)
**Goal:** Project setup, basic infrastructure, core data models, minimal API

**Definition of Done:**
- Repo structure in place
- Docker/docker-compose working
- Database models defined and migrated
- Basic FastAPI app with healthcheck
- `POST /jobs` endpoint accepts input and stores in DB
- `GET /jobs/{id}` endpoint returns job status
- Basic worker skeleton (can dequeue jobs, update status)
- CI/CD pipeline skeleton (GitHub Actions)

### Sprint 1 – Core Pipeline (Week 3-4)
**Goal:** End-to-end execution pipeline working

**Definition of Done:**
- Worker can clone GitHub repos
- Environment detection works for common files (requirements.txt, environment.yml, pyproject.toml)
- Docker image building from detected environment
- Command execution inside container with log capture
- Basic reproducibility report generation (markdown)
- Basic notebook template generation
- Job status transitions: pending → running → completed/failed
- Error handling for common failure modes

### Sprint 2 – UX / Aha Moment (Week 5-6)
**Goal:** Polished user experience, badge generation, report improvements

**Definition of Done:**
- Simple web UI to submit jobs and view results
- HTML report with better formatting
- Badge snippet generation (SVG or markdown)
- Improved notebook templates (Colab-ready)
- Job history/list view
- Download artifacts functionality
- Basic error messages and user feedback
- Documentation for users

---

## 4. Backlog Overview

### Epic 1: Foundation & Infrastructure (Sprint 0)
- Project setup and tooling
- Database models and migrations
- Basic API endpoints
- Worker framework

### Epic 2: Execution Pipeline (Sprint 1)
- Repo cloning
- Environment detection
- Docker execution
- Report generation

### Epic 3: User Experience (Sprint 2)
- Web UI
- Badge generation
- Improved reports
- Documentation

### Epic 4: Polish & Reliability (Post-MVP or Sprint 2 stretch)
- Better error handling
- Retry logic
- Performance optimization
- Monitoring/logging

---

## 5. Backlog as GitHub Issues

### MUST-HAVE (Sprint 0)

**Issue #1: Project structure and tooling setup**
- **Labels:** `setup`, `infrastructure`, `must-have`
- **Description:** Set up Python project structure, dependency management (uv/poetry), linting (black, isort, ruff), testing framework (pytest), and basic CI/CD (GitHub Actions).
- **Acceptance:** `make dev` runs backend, `make test` runs tests, CI passes on PR.

**Issue #2: Docker and docker-compose setup**
- **Labels:** `infrastructure`, `docker`, `must-have`
- **Description:** Create Dockerfile for backend, docker-compose.yml with backend, DB, Redis, and worker services. Ensure local development works with `docker compose up`.
- **Acceptance:** All services start, backend connects to DB and Redis, worker can connect to queue.

**Issue #3: Database models and migrations**
- **Labels:** `backend`, `database`, `must-have`
- **Description:** Define SQLAlchemy models for Job, Run, Artifact. Create Alembic migrations. Job fields: id, repo_url, arxiv_id, run_command, status, created_at, updated_at. Run fields: job_id, exit_code, logs, started_at, completed_at. Artifact fields: id, job_id, type (report/notebook/badge), content_path, created_at.
- **Acceptance:** Models defined, migrations run successfully, can create/read records via ORM.

**Issue #4: FastAPI app skeleton and healthcheck**
- **Labels:** `backend`, `api`, `must-have`
- **Description:** Create FastAPI app with `/health` endpoint. Set up dependency injection for DB session. Configure CORS if needed.
- **Acceptance:** `GET /health` returns 200, app starts without errors.

**Issue #5: POST /jobs endpoint**
- **Labels:** `backend`, `api`, `must-have`
- **Description:** Implement endpoint that accepts `repo_url` (required), `arxiv_id` (optional), `run_command` (optional, default to detect). Validates input, creates Job record with status `pending`, enqueues worker task, returns job ID.
- **Acceptance:** Can create job via API, job stored in DB, task enqueued.

**Issue #6: GET /jobs/{id} endpoint**
- **Labels:** `backend`, `api`, `must-have`
- **Description:** Returns job details: status, repo_url, arxiv_id, run_command, created_at, updated_at. If completed, includes links to artifacts.
- **Acceptance:** Can retrieve job by ID, returns correct status and metadata.

**Issue #7: Worker skeleton and job queue setup**
- **Labels:** `backend`, `worker`, `must-have`
- **Description:** Set up RQ or Celery worker. Worker can dequeue jobs, update job status to `running`, then `completed` or `failed`. Basic error handling.
- **Acceptance:** Worker processes jobs, updates status in DB, handles basic errors.

### MUST-HAVE (Sprint 1)

**Issue #8: GitHub repo cloning**
- **Labels:** `backend`, `worker`, `must-have`
- **Description:** Worker clones GitHub repo to temporary directory. Handles public repos, basic auth if needed. Cleans up temp dirs after processing.
- **Acceptance:** Can clone public repos, handles invalid URLs gracefully, cleans up temp files.

**Issue #9: Environment detection**
- **Labels:** `backend`, `worker`, `must-have`
- **Description:** Detect Python environment from `requirements.txt`, `environment.yml`, `pyproject.toml`, `Pipfile`. Extract dependencies and versions. Return structured dependency list.
- **Acceptance:** Detects dependencies from common files, handles missing files, returns structured data.

**Issue #10: Docker image building**
- **Labels:** `backend`, `worker`, `docker`, `must-have`
- **Description:** Build Docker image from detected environment. Create Dockerfile dynamically or use base image + install dependencies. Tag images uniquely per job.
- **Acceptance:** Can build Docker images with dependencies, images are tagged and stored, build failures are captured.

**Issue #11: Command execution in container**
- **Labels:** `backend`, `worker`, `docker`, `must-have`
- **Description:** Execute `run_command` (or default like `python main.py`) inside container. Capture stdout, stderr, exit code. Set timeout (e.g., 30 minutes). Stream logs to DB.
- **Acceptance:** Commands execute, logs captured, exit codes recorded, timeouts work.

**Issue #12: Basic reproducibility report generation**
- **Labels:** `backend`, `worker`, `must-have`
- **Description:** Generate markdown report with: job metadata, environment summary, execution results (success/partial/fail), logs excerpt, timestamp. Save as file, create Artifact record.
- **Acceptance:** Reports generated for successful and failed runs, stored correctly, accessible via API.

**Issue #13: Basic notebook template generation**
- **Labels:** `backend`, `worker`, `must-have`
- **Description:** Generate Jupyter notebook (.ipynb) with cells for: environment setup, dependency installation, code execution. Make it Colab-compatible. Save as file, create Artifact record.
- **Acceptance:** Notebooks generated, valid .ipynb format, can be opened in Colab.

**Issue #14: Job status management and transitions**
- **Labels:** `backend`, `worker`, `must-have`
- **Description:** Implement state machine: pending → running → (completed | failed). Update timestamps. Handle worker crashes (jobs stuck in running).
- **Acceptance:** Status transitions work correctly, timestamps updated, stuck jobs can be detected.

**Issue #15: Error handling for common failures**
- **Labels:** `backend`, `worker`, `must-have`
- **Description:** Handle: invalid repo URLs, clone failures, missing environment files, Docker build failures, execution timeouts, container crashes. Set job status to `failed`, store error message.
- **Acceptance:** All failure modes handled gracefully, error messages stored, jobs don't hang.

**Issue #31: Container hardening & minimal sandbox**
- **Labels:** `backend`, `worker`, `security`, `must-have`
- **Description:** Implement minimal security measures for job execution inside Docker containers:
  - Run containers as non-root user.
  - Apply CPU and memory limits.
  - Disable or strictly restrict network access.
  - Mount only the necessary volumes (working dir + artifacts).
  - Define a safe base image and clarify what is allowed to be installed.
- **Acceptance:**
  - Jobs cannot access the host filesystem outside their working directory.
  - Containers run as non-root.
  - Resource limits (CPU/memory) are enforced and verifiable.
  - Network access is blocked or restricted as per configuration.

**Issue #32: Reference repos and end-to-end integration tests**
- **Labels:** `backend`, `testing`, `must-have`
- **Description:** Define 2–3 small reference GitHub repositories ("Hello Papers") and use them to validate the full pipeline:
  - For each reference repo, create a test that:
    - creates a Job via the API,
    - runs the worker,
    - asserts final status is `completed`,
    - asserts that report and notebook artifacts exist and are valid.
  - Provide a simple way to run integration tests separately from unit tests.
- **Acceptance:**
  - There is at least one integration test that exercises the full flow (job → worker → artifacts).
  - `pytest -m integration` (or similar) runs the end-to-end tests successfully.
  - At least one real public GitHub repo is used as a reference.

**Issue #33: Basic logging structure**
- **Labels:** `backend`, `infrastructure`, `must-have`
- **Description:** Introduce basic structured logging for backend and worker:
  - Configure a logger with at least INFO and ERROR levels.
  - Log key events:
    - job creation,
    - job status transitions (pending → running → completed/failed),
    - repo clone start/end,
    - Docker build start/end,
    - command execution start/end,
    - failures and exceptions.
  - Clearly separate:
    - system logs (Arandu's own logs),
    - experiment logs (stdout/stderr from the executed command), which are stored as part of the run/artifact.
- **Acceptance:**
  - Logs are emitted for key events and can be used to understand system behavior.
  - Experiment logs are not mixed with system logs; they are stored as part of the run/artifact data model.

### MUST-HAVE (Sprint 2)

**Issue #16: Simple web UI for job submission**
- **Labels:** `frontend`, `ui`, `must-have`
- **Description:** Create minimal form to submit repo URL, optional arxiv ID, optional run command. Show job ID and link to status page. Use Next.js or FastAPI templates.
- **Acceptance:** Users can submit jobs via UI, see confirmation, navigate to status page.

**Issue #17: Job status and results page**
- **Labels:** `frontend`, `ui`, `must-have`
- **Description:** Display job status, metadata, execution logs (scrollable), links to download report/notebook/badge. Auto-refresh if status is pending/running.
- **Acceptance:** Status page shows all job info, logs are readable, download links work.

**Issue #18: HTML report generation**
- **Labels:** `backend`, `worker`, `must-have`
- **Description:** Enhance report generator to output HTML with better formatting, syntax highlighting for logs, collapsible sections. Keep markdown as fallback.
- **Acceptance:** HTML reports are well-formatted, readable, include all info from markdown version.

**Issue #19: Badge snippet generation**
- **Labels:** `backend`, `worker`, `must-have`
- **Description:** Generate badge snippet (markdown or SVG) showing reproducibility status. Format: `[![Reproducible](badge_url)](job_url)`. Create Artifact record.
- **Acceptance:** Badge snippets generated, valid markdown, can be added to README.

**Issue #20: Improved notebook templates**
- **Labels:** `backend`, `worker`, `must-have`
- **Description:** Enhance notebooks with: better cell structure, markdown explanations, error handling cells, Colab-specific setup. Include original repo link.
- **Acceptance:** Notebooks are more polished, Colab-ready, include helpful context.

**Issue #21: Jobs list/history view**
- **Labels:** `frontend`, `ui`, `must-have`
- **Description:** Show table/list of all jobs with: repo URL, status, created date. Filter by status. Link to detail page.
- **Acceptance:** Can view all jobs, filter works, navigation to details works.

**Issue #22: Artifact download endpoints**
- **Labels:** `backend`, `api`, `must-have`
- **Description:** `GET /jobs/{id}/artifacts/report`, `/artifacts/notebook`, `/artifacts/badge` return files with correct content-type headers.
- **Acceptance:** Can download all artifact types, correct MIME types, files are valid.

### NICE-TO-HAVE (Sprint 2 stretch or post-MVP)

**Issue #23: Better error messages and user feedback**
- **Labels:** `frontend`, `ux`, `nice-to-have`
- **Description:** Improve error messages in UI, show helpful hints for common issues (e.g., "Repo not found", "No environment file detected").
- **Acceptance:** Error messages are clear and actionable.

**Issue #24: Retry logic for failed jobs**
- **Labels:** `backend`, `worker`, `nice-to-have`
- **Description:** Allow users to retry failed jobs. Option to retry with same or modified parameters.
- **Acceptance:** Can retry jobs, retry creates new job or updates existing.

**Issue #25: Job cancellation**
- **Labels:** `backend`, `api`, `nice-to-have`
- **Description:** Allow cancelling jobs that are pending or running. Stop worker, update status to `cancelled`.
- **Acceptance:** Can cancel jobs, worker stops gracefully, status updated.

**Issue #26: Log streaming/real-time updates**
- **Labels:** `backend`, `frontend`, `nice-to-have`
- **Description:** Stream execution logs to UI in real-time using WebSockets or SSE instead of polling.
- **Acceptance:** Logs appear in UI as they're generated.

**Issue #27: Basic metrics and monitoring**
- **Labels:** `infrastructure`, `nice-to-have`
- **Description:** Add basic metrics: job success rate, average execution time, queue depth. Simple dashboard or logs.
- **Acceptance:** Can see basic system health metrics.

**Issue #28: Support for more environment types**
- **Labels:** `backend`, `worker`, `nice-to-have`
- **Description:** Detect and support: R (DESCRIPTION, renv), Node.js (package.json), Julia (Project.toml).
- **Acceptance:** Can detect and build environments for additional languages.

**Issue #29: Report comparison/diff**
- **Labels:** `backend`, `nice-to-have`
- **Description:** Compare reports from multiple runs of same repo, highlight differences.
- **Acceptance:** Can compare two reports, differences highlighted.

**Issue #30: User documentation**
- **Labels:** `documentation`, `nice-to-have`
- **Description:** Write user guide: how to submit jobs, interpret reports, use notebooks, add badges.
- **Acceptance:** Documentation is clear and complete.

---

## 6. Risks & Simplifications

### Technical Risks

1. **Docker security and resource limits**
   - Risk: Malicious code execution, resource exhaustion
   - Mitigation: Run containers with limited resources, no network access (or controlled), timeout enforcement, consider sandboxing. **Note:** Issue #31 addresses container hardening with non-root containers, resource limits, and network restrictions as part of v0. v0 adopts resource limits and non-root containers as a baseline security measure.

2. **Environment detection complexity**
   - Risk: Many dependency file formats, version conflicts, missing dependencies
   - Mitigation: Start with Python only, support most common formats (requirements.txt, environment.yml), fail gracefully with clear errors

3. **GitHub rate limiting**
   - Risk: Too many clones hit API limits
   - Mitigation: Use authenticated requests if needed, cache repos, implement backoff

4. **Long-running executions**
   - Risk: Jobs take hours, worker crashes, jobs stuck
   - Mitigation: Timeout enforcement, job status monitoring, retry mechanism for worker crashes. **Note:** End-to-end integration tests on reference repos (Issue #32) are part of the mitigation strategy, helping validate the pipeline and catch issues early.

5. **Storage growth**
   - Risk: Artifacts accumulate, disk fills up
   - Mitigation: Local filesystem for v0, add cleanup job, plan for object storage in Phase 2

### Simplifications for v0

1. **Single language focus:** Python only (most AI research repos)
2. **No authentication:** Public API, no user accounts (add in Phase 2)
3. **Local storage:** Filesystem instead of S3/object storage
4. **Simple queue:** RQ instead of complex Celery setup
5. **Minimal frontend:** Basic forms and status pages, no complex SPA
6. **No caching:** Direct DB queries, add caching in Phase 2
7. **Basic error handling:** Fail fast with clear messages, no complex retry logic initially
8. **No job prioritization:** FIFO queue, add priority in Phase 2
9. **Single worker:** One worker process, scale horizontally in Phase 2
10. **No monitoring/alerting:** Basic logging, add observability in Phase 2

### Explicitly Deferred to Phase 2+

- P2P network and node discovery
- Tokenomics, DAO, funding engine
- Epistemic ledger (truth/cooperation/ethics scoring)
- Multi-language support beyond Python
- User authentication and accounts
- Job scheduling and prioritization
- Advanced monitoring and alerting
- Object storage (S3/GCS)
- API rate limiting and quotas
- Job sharing and collaboration features
- Recommendation and matching systems

