# End-to-End Testing

This document describes how to run end-to-end (E2E) integration tests for Arandu Repro v0.

## Overview

E2E tests validate the full pipeline from job creation to artifact generation:
1. Job creation via API (or direct DB insertion)
2. Worker processing (clone, detect, build, execute, generate)
3. Artifact validation (report, notebook, badge)
4. Status transitions and timing

## Running E2E Tests

### Prerequisites

- Docker daemon running
- Python dependencies installed (`uv pip install -e ".[dev]"`)

### Local Execution

**Unit tests only (no Docker required):**
```bash
cd backend
make test-unit
```

**Integration tests (requires Docker):**
```bash
cd backend
make test-integration
```

**Full E2E with docker-compose:**
```bash
cd backend
make e2e
```

This will:
1. Start docker-compose services (API, DB, Redis, Worker)
2. Wait for services to be ready
3. Run integration tests
4. Stop docker-compose services

### Manual E2E Test

1. Start services:
   ```bash
   cd infra
   docker compose up -d
   ```

2. Wait for services to be healthy (check logs: `docker compose logs api`)

3. Create a job:
   ```bash
   curl -X POST http://localhost:8000/api/v1/jobs \
     -H "Content-Type: application/json" \
     -d '{"repo_url": "file:///path/to/test/repo"}'
   ```

4. Check job status:
   ```bash
   curl http://localhost:8000/api/v1/jobs/{job_id}/status
   ```

5. Verify artifacts:
   ```bash
   curl http://localhost:8000/api/v1/jobs/{job_id}/artifacts/report
   ```

## Test Structure

### Integration Test Markers

Tests are marked with `@pytest.mark.integration`:

```python
@pytest.mark.integration
def test_full_pipeline():
    # Test implementation
    pass
```

### Test Fixtures

**Reference Repositories:**
- `tests/fixtures/repos/hello-python/`: Minimal Python repo with `requirements.txt` and `main.py`
- Additional repos can be added under `tests/fixtures/repos/`

**Database:**
- Tests use in-memory SQLite for isolation
- Each test class sets up its own database via `setup_db` fixture

### Test Coverage

E2E tests verify:
- ✅ Job creation and status transitions
- ✅ Repository cloning (local `file://` URLs)
- ✅ Environment detection
- ✅ Docker image building
- ✅ Command execution
- ✅ Artifact generation (report, notebook, badge)
- ✅ Run record creation with timestamps
- ✅ Error handling and failure states

## CI Integration

### GitHub Actions

**Unit tests:** Run in the main `lint-and-test` job (always).

**Integration tests:** Optional job that runs on label `run-e2e`:

```yaml
integration-tests:
  runs-on: ubuntu-latest
  if: contains(github.event.pull_request.labels.*.name, 'run-e2e')
  steps:
    - name: Run integration tests
      run: cd backend && make test-integration
```

### Running in CI

To trigger integration tests in CI, add the `run-e2e` label to your PR.

## Troubleshooting

**Docker daemon not available:**
- Tests will skip with message: "Docker daemon not available"
- Ensure Docker is running: `docker ps`

**Services not ready:**
- Check service health: `docker compose ps`
- View logs: `docker compose logs api worker`

**Test timeouts:**
- Increase timeout in test configuration
- Check Docker resource limits

**Artifact validation failures:**
- Verify artifact files exist at expected paths
- Check file permissions and sizes
- Review artifact content for expected structure

## Adding New E2E Tests

1. Create test in `backend/tests/integration/`
2. Use `@pytest.mark.integration` marker
3. Use `file://` URLs for local repos (or mock GitHub repos)
4. Assert on:
   - Job status transitions
   - Artifact existence and validity
   - Run records with timestamps
   - Error messages for failure cases

Example:
```python
@pytest.mark.integration
def test_my_feature():
    # Setup
    job = create_job(...)
    
    # Execute
    process_job(str(job.id))
    
    # Assert
    assert job.status == JobStatus.COMPLETED
    assert artifacts_exist(job.id)
```

