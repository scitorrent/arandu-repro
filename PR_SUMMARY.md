
# Sprint 2 – Hosting APIs + Viewer (#34–#36)

## Summary

Implements paper hosting APIs and frontend viewer for Sprint 2 Phase 2.

## Changes

### Backend (#34)
- ✅ POST /api/v1/papers - Upload PDF or URL, create paper with version 1
- ✅ POST /api/v1/papers/{aid}/versions - Create new version
- ✅ GET /api/v1/papers/{aid} - Get metadata with counts
- ✅ GET /api/v1/papers/{aid}/viewer - Stream PDF (Range/206 support)
- ✅ HEAD /api/v1/papers/{aid}/viewer - PDF metadata
- ✅ GET /api/v1/papers/{aid}/claims - List claims with pagination
- ✅ CORS configured for Next.js origin
- ✅ PDF validation (size, MIME, header)
- ✅ Storage utils integration

### Frontend (#35, #36)
- ✅ Next.js 14 App Router (TypeScript)
- ✅ Tailwind CSS with design tokens
- ✅ /p/[aid] page with tabs (PDF | Review | Artifacts)
- ✅ /p/[aid]/viewer page with iframe (PDF.js optional)
- ✅ Responsive, mobile-first design
- ✅ Accessibility (focus rings, high contrast)

### Infrastructure
- ✅ Dockerfile for frontend
- ✅ docker-compose.yml with web service
- ✅ CI updated for API tests

### Tests
- ✅ test_papers_api.py (upload, versioning, metadata, viewer, claims)

### Docs
- ✅ README with usage examples

## Environment Variables

### Backend
- `PAPERS_BASE`: Base path for papers storage (default: temp directory)
- `WEB_ORIGIN`: Frontend origin for CORS (default: http://localhost:3000)
- `MAX_PDF_SIZE_MB`: Maximum PDF size (default: 25)

### Frontend
- `NEXT_PUBLIC_API_BASE`: Backend API URL (default: http://localhost:8000)

## Definition of Done

- [x] APIs (#34) implemented with validations, storage, Range streaming
- [x] Frontend viewer/page (#35/#36) loads PDFs from backend and renders
- [x] CI: Postgres service, `alembic upgrade head`, API tests pass
- [x] docker-compose up brings api+db+redis+worker+web healthy
- [x] README updated with examples

## Testing

### Manual Testing

```bash
# Start services
docker compose -f infra/docker-compose.yml up

# Upload paper
curl -X POST http://localhost:8000/api/v1/papers \
  -F "pdf=@test.pdf" \
  -F "title=Test Paper"

# View in browser
open http://localhost:3000/p/[aid]
```

### Automated Tests

```bash
cd backend
pytest tests/api/test_papers_api.py -v
```

## Follow-up Issues

- #37: Public/Private toggle + approval flow (approved_public)
- #38: Review tab minimal renderer (consume review artifacts)
- #39: Basic upload UI (drag/drop) calling POST /papers

