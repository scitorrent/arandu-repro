# Hypothesis Analysis and Fixes

## Root Cause Analysis

### Issues Identified

1. **E2E Pipeline Tests (2 failures)**: "Job not found" error
2. **Concurrency Tests (2 failures)**: `NameError: name 'SessionLocal' is not defined`

### Hypotheses Tested

#### Hypothesis 1: Monkeypatch not working
- **Test**: `test_hypothesis_1_monkeypatch_works`
- **Result**: ✅ PASSED - Monkeypatch works correctly

#### Hypothesis 2: Import caching prevents monkeypatch
- **Test**: `test_hypothesis_2_import_caching`
- **Result**: ✅ PASSED - Import caching doesn't prevent monkeypatch at module level

#### Hypothesis 3: Job visibility in new session
- **Test**: `test_hypothesis_3_job_visibility`
- **Result**: ✅ PASSED - Jobs are visible across sessions

#### Hypothesis 4: UUID conversion issue
- **Test**: `test_hypothesis_4_uuid_conversion`
- **Result**: ✅ PASSED - UUID conversion works correctly

### Root Cause Identified

**E2E Tests**: Two issues:
1. **Import caching**: `app.worker.main` imports `SessionLocal` at module level, so patching only `app.db.session.SessionLocal` doesn't affect the cached reference.
2. **Session closure**: `process_job` calls `db.close()` at the end (line 318), which closes the test's session since we patched `SessionLocal` to return the same `db` object. This detaches all objects in the test session.

**Solution**: 
1. Patch `app.worker.main.SessionLocal` in addition to `app.db.session.SessionLocal`.
2. Patch `db.close()` to be a no-op during tests so `process_job` doesn't close the test session.
3. Save `job_id` before querying to avoid accessing detached objects.

**Concurrency Tests**: Simple bug - `SessionLocal()` should be `session_local()` (2 occurrences).

## Fixes Applied

### 1. E2E Test Fix
**File**: `backend/tests/integration/test_e2e_pipeline.py`
- Added patch for `app.worker.main.SessionLocal` to handle import caching
- Patched `db.close()` to be a no-op so `process_job` doesn't close the test session
- Save `job_id` before querying to avoid detached instance errors
- **Result**: ✅ Both E2E tests now pass locally

### 2. Concurrency Test Fix
**File**: `backend/tests/test_concurrency.py`
- Fixed `SessionLocal()` → `session_local()` (2 occurrences)
- Added error message formatting for debugging

## Remaining Issues

The concurrency tests still fail with "Expected 1 success, got 0", which suggests:
- SQLite in-memory databases may not work well with concurrent threads
- All threads might be failing due to foreign key constraints or other issues
- May need to use file-based SQLite or PostgreSQL for proper concurrency testing

This is a separate issue from the import caching problem and may require a different approach (e.g., using a file-based test database or skipping these tests in CI if they're not critical).

