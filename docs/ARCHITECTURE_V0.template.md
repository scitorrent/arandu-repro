# Arandu Repro v0 – Architecture (Template)

## 1. Overview

High-level description of the architecture (API, worker, env builder, executor, storage, UI).

## 2. Components

- API Service
- Job Queue / Worker
- Environment Detector & Builder
- Executor (Docker runner)
- Report & Notebook Generator
- Database

## 3. Data Model

List entities like:
- Job
- Run / Execution
- Artifact (report, notebook, badge)
and their main fields.

## 4. Interfaces / Contracts

Describe function/class signatures and API endpoints:
- `POST /jobs`
- `GET /jobs/{id}`
- internal functions for:
  - repo cloning,
  - env detection/build,
  - command execution,
  - report generation.

## 5. Open Questions

Pending decisions or trade-offs.

