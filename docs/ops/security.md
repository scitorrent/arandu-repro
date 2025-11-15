# Container Security Hardening

This document describes the security measures enforced for job execution containers in Arandu Repro v0.

## Overview

All job execution containers are subject to strict security constraints to prevent:
- Unauthorized access to the host filesystem
- Resource exhaustion (CPU, memory)
- Network-based attacks
- Privilege escalation

## Security Constraints

### 1. Non-Root User

**Enforcement:** All containers run as a non-root user (`arandu-user`, UID 1000).

**Configuration:**
- `DOCKER_USER`: User name (default: `arandu-user`)
- `DOCKER_USER_UID`: User UID (default: `1000`)

**Validation:** The executor will fail with `ExecutionError` if `docker_user` is `root` or empty.

### 2. Resource Limits

**CPU Limit:**
- Default: 2.0 cores
- Configurable via `DOCKER_CPU_LIMIT` (float)
- Enforced via Docker CPU quota/period

**Memory Limit:**
- Default: 4GB
- Configurable via `DOCKER_MEMORY_LIMIT` (string, e.g., `"4g"`, `"2g"`)
- Enforced via Docker `mem_limit`

**Validation:** The executor will fail if CPU limit is <= 0 or memory limit is not set.

### 3. Network Isolation

**Default:** `network=none` (no network access)

**Configuration:**
- `DOCKER_NETWORK_MODE`: `"none"` (default) or `"bridge"` (future: with allowlist)
- `DOCKER_ALLOWLIST_DOMAINS`: List of allowed domains (empty by default)

**Validation:** The executor will fail if network mode is not `"none"` or `"bridge"`.

**Future:** Network allowlist support for controlled access to specific domains (e.g., for downloading models).

### 4. Read-Only Root Filesystem

**Enforcement:** Root filesystem is read-only when enabled.

**Configuration:**
- `DOCKER_READONLY_ROOTFS`: Boolean (default: `True`)

**Writable Mounts:**
- `/workspace`: Repository code (read-only)
- `/artifacts`: Artifacts directory (read-write)

### 5. Volume Isolation

**Allowed Mounts:**
- Repository path → `/workspace` (read-only)
- Artifacts directory → `/artifacts` (read-write)

**No Host Filesystem Access:** Containers cannot access any host filesystem paths outside the mounted directories.

## Configuration

All security settings are defined in `backend/app/config.py` and can be overridden via environment variables:

```bash
# Docker security settings
DOCKER_USER=arandu-user
DOCKER_USER_UID=1000
DOCKER_CPU_LIMIT=2.0
DOCKER_MEMORY_LIMIT=4g
DOCKER_NETWORK_MODE=none
DOCKER_READONLY_ROOTFS=true
DOCKER_ALLOWLIST_DOMAINS=[]  # JSON array, empty by default
```

## Override Safely

**⚠️ Warning:** Changing security defaults should only be done in controlled environments and with full understanding of the implications.

**Safe Overrides:**
- Increasing CPU/memory limits (if host resources allow)
- Temporarily enabling network access for specific use cases (with allowlist)

**Unsafe Overrides:**
- Running as root (`DOCKER_USER=root`)
- Disabling resource limits
- Using `host` network mode
- Disabling read-only root filesystem without justification

## Testing

Security constraints are validated by tests in `backend/tests/test_security_hardening.py`:

- `test_executor_fails_if_root_user`: Verifies non-root enforcement
- `test_executor_fails_if_no_cpu_limit`: Verifies CPU limit enforcement
- `test_executor_fails_if_no_memory_limit`: Verifies memory limit enforcement
- `test_executor_fails_if_invalid_network_mode`: Verifies network mode validation
- `test_executor_enforces_readonly_rootfs`: Verifies read-only root filesystem

These tests ensure that security violations cause the executor to fail fast with clear error messages.

## Future Enhancements

- Network allowlist implementation for controlled domain access
- Stricter sandboxing (Docker-in-Docker or alternative isolation mechanisms)
- Resource limit monitoring and alerting
- Audit logging for security events

