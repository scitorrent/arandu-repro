# AGENTS.md – Arandu Repro v0

This file is for **agents** (Cursor, code assistants, automation).  
Humans can read it too, but it is primarily guidance for tools.

---

## 1. Project focus (for now)

Project name: **Arandu Repro v0**

Goal (MVP):

> A small service that takes a GitHub repo (optionally a paper / arXiv ID),  
> builds a runnable environment, executes a command in a container,  
> and generates:
> - a reproducibility report (markdown/HTML),
> - an executable notebook,
> - an optional badge snippet for the README.

Out of scope for v0 (do NOT implement unless explicitly asked by Carlos):

- P2P network, node discovery, geo-distribution.
- Tokens, DAO, funding engine, royalties.
- Full epistemic ledger, claim-level truth/ethics scoring.
- Audio/video explainers, podcasts, recommendation/matching.
- Complex auth/account system.

If you are unsure whether something belongs to v0, **assume it is out of scope**.

---

## 2. Repository structure (v0)

Agents must respect and use this structure:

- `docs/`
  - Project context, plan, architecture, design system.
  - Start here to understand the project.
- `prompts/`
  - System and initial prompts for Planner, Architect, Dev, Design agents.
- `design/`
  - Design tokens, mockups, and UI-related assets.
- `backend/`
  - Backend service (API, worker, models, core logic).
- `frontend/`
  - Web UI (if present) for jobs, status, reports, downloads.
- `infra/`
  - Docker, docker-compose, CI/CD, infra-related scripts.

If you create new files or folders, keep them under these roots unless there is a strong reason not to.

---

## 3. How agents should behave

1. **Stay within the MVP scope.**
   - Only work on Arandu Repro v0 features (job creation, env build, execution, report/notebook/badge).

2. **Read before you act.**
   - Before major changes, skim:
     - `docs/ARANDU_CONTEXT.md`
     - `docs/PLAN_V0*.md` (if present)
     - `docs/ARCHITECTURE_V0*.md`
     - `docs/DESIGN_SYSTEM_V0*.md`

3. **Small, reviewable changes.**
   - Prefer small PR-sized changes over huge refactors.
   - Describe what you changed and why.

4. **Do not invent new subsystems.**
   - No new services, no microservices, no extra repos, unless explicitly requested.

5. **Ask (via comments or TODOs) when unsure.**
   - Leave a clear `# TODO(agent):` note rather than guessing a big design.

---

## 4. Build & run (expected pattern)

> Note: exact commands may evolve. Update this section as the project matures.

Backend (expected):

- Local dev:
  - `cd backend`
  - `make dev` **or** `uv run uvicorn app.main:app --reload`
- Tests:
  - `cd backend`
  - `pytest`

Frontend (if present):

- Local dev:
  - `cd frontend`
  - `npm install`
  - `npm run dev`

Docker (full stack):

- At repo root:
  - `docker compose up`

Agents:
- If you modify build/run commands, **update this section**.

---

## 5. Coding conventions

General:

- Language: Python for backend, TypeScript/JavaScript for frontend.
- Style:
  - Python: use `black` + `isort` + `ruff` (or project’s configured tools).
  - JS/TS: use `eslint` + `prettier` if configured.

Rules for agents:

- Prefer explicit, readable code over clever tricks.
- Keep functions small and cohesive.
- Write docstrings or comments for non-trivial logic.
- When adding dependencies, keep them minimal and justified.

---

## 6. Git / workflow guidelines

For agents operating on git:

- Do **not** force-push.
- Keep changes focused per branch / commit.
- Commit messages:
  - Short, imperative style:
    - `Add job model and POST /jobs endpoint`
    - `Implement Docker execution for jobs`
- Do not commit secrets (`.env`, API keys, service accounts).

If you generate or modify `.env` or secrets locally, ensure they are **ignored** in `.gitignore`.

---

## 7. Docs and prompts

Agents should know where to look:

- High-level context:
  - `docs/ARANDU_CONTEXT.md`
- Plan and sprints:
  - `docs/PLAN_V0*.md`
- Architecture:
  - `docs/ARCHITECTURE_V0*.md`
- Design system:
  - `docs/DESIGN_SYSTEM_V0*.md`
- Agent prompts:
  - `prompts/engineering_planner_system.txt`
  - `prompts/engineering_planner_initial.txt`
  - `prompts/architect_system.txt`
  - `prompts/architect_initial.txt`
  - `prompts/dev_system.txt`
  - `prompts/dev_initial.txt`
  - `prompts/design_system.txt`
  - `prompts/design_initial.txt`

When in doubt about your role:
- Read the relevant prompt in `prompts/` before acting.

---

## 8. Arandu-specific guardrails

Agents must respect these constraints:

- Do NOT implement:
  - tokenomics,
  - grants logic,
  - complex reputation indexing,
  - multi-node P2P logic,
  - ethics/risk scores,
  - recommendation engines,
  - matching / social graph,
  **unless a document in `docs/` explicitly moves these items into the current scope.**

- Do NOT:
  - rename the project,
  - move or delete root folders (`docs/`, `prompts/`, `backend/`, `frontend/`, `infra/`),
  - rewrite core docs without very clear intent and justification.

Arandu Repro v0 should stay:
- small,
- robust,
- understandable,
- and shippable by a tiny team in weeks, not years.

If a change threatens that, leave a note and stop.
