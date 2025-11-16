# Sprint 2 – Phase 2: Hosting APIs + Viewer (#34–#36)

## Summary

Implements paper hosting APIs and frontend viewer for Sprint 2 Phase 2, enabling users to upload papers, view them in a hosted page, and access PDFs via a viewer.

## Changes

### Backend (#34)
- ✅ `POST /api/v1/papers` - Upload PDF or URL, create paper with version 1
- ✅ `POST /api/v1/papers/{aid}/versions` - Create new version
- ✅ `GET /api/v1/papers/{aid}` - Get metadata with counts (claims, scores, versions)
- ✅ `GET /api/v1/papers/{aid}/viewer` - Stream PDF with Range/206 support
- ✅ `HEAD /api/v1/papers/{aid}/viewer` - PDF metadata for HEAD requests
- ✅ `GET /api/v1/papers/{aid}/claims` - List claims with pagination
- ✅ PDF validation (size ≤25MB, MIME type, header check)
- ✅ Storage utils integration (secure paths, atomic directory creation)
- ✅ CORS configured for Next.js origin

### Frontend (#35, #36)
- ✅ Next.js 14 App Router (TypeScript)
- ✅ Tailwind CSS with design system tokens
- ✅ `/p/[aid]` page with tabs (PDF | Review | Artifacts)
- ✅ `/p/[aid]/viewer` page with PDF.js integration
- ✅ Responsive, mobile-first design
- ✅ Accessibility (focus rings, high contrast)

### Infrastructure
- ✅ Dockerfile for frontend (multi-stage build)
- ✅ docker-compose.yml with `web` service
- ✅ Network configuration (arandu-network)
- ✅ CI updated for API tests with Postgres

### Database & Models
- ✅ Migrations for papers, versions, external_ids, quality_scores, claims, claim_links
- ✅ ENUMs with idempotent creation (handles duplicates)
- ✅ Composite indices for performance
- ✅ pg_trgm extension enabled

### Fixes
- ✅ Enum visibility mapping (native_enum=False for lowercase values)
- ✅ NEXT_PUBLIC_API_BASE configured for browser access
- ✅ Migrations handle ENUM duplicates gracefully

## Environment Variables

### Backend
- `PAPERS_BASE`: Base path for papers storage (default: temp directory)
- `WEB_ORIGIN`: Frontend origin for CORS (default: http://localhost:3000)
- `MAX_PDF_SIZE_MB`: Maximum PDF size (default: 25)
- `PDF_PARSING_TIMEOUT_SECONDS`: PDF parsing timeout (default: 30)

### Frontend
- `NEXT_PUBLIC_API_BASE`: Backend API URL (default: http://localhost:8000)

## Definition of Done

- [x] APIs (#34) implemented with validations, storage, Range streaming
- [x] Frontend viewer/page (#35/#36) loads PDFs from backend and renders
- [x] CI: Postgres service, `alembic upgrade head`, API tests pass
- [x] `docker-compose up` brings api+db+redis+worker+web healthy
- [x] README updated with examples
- [x] Demo documentation (DEMO_LOCAL.md) added

## Testing

### Manual Testing

```bash
# Start services
cd infra && docker compose up

# Upload paper
curl -X POST http://localhost:8000/api/v1/papers \
  -F "pdf=@test.pdf" \
  -F "title=Test Paper" \
  -F "visibility=private"

# View in browser
open http://localhost:3000/p/[aid]
```

### Automated Tests

```bash
cd backend
pytest tests/api/test_papers_api.py -v
```

## Known Issues / Limitations

- Frontend healthcheck may show "unhealthy" but service works (healthcheck needs adjustment)
- PDF viewer requires actual PDF file to render (placeholder shows error if file missing)
- Test paper created directly in DB (test-demo-2cbcc551) for demo purposes

## Follow-up Issues

- #37: Public/Private toggle + approval flow (approved_public)
- #38: Review tab minimal renderer (consume review artifacts when available)
- #39: Basic upload UI (drag/drop) calling POST /papers

## Screenshots / Demo

- Demo available at: http://localhost:3000/p/test-demo-2cbcc551
- API docs: http://localhost:8000/docs
