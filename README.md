# Arandu Repro v0

A service for hosting and reviewing scientific papers with reproducibility analysis.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)

### Running with Docker Compose

```bash
# Start all services
docker compose up

# Services will be available at:
# - API: http://localhost:8000
# - Frontend: http://localhost:3000
# - Database: localhost:5432
# - Redis: localhost:6379
```

### Local Development

#### Backend

```bash
cd backend

# Install dependencies
pip install -e ".[dev]"

# Set up environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload

# Start worker (in another terminal)
rq worker --url redis://localhost:6379/0 reviews
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set environment
echo "NEXT_PUBLIC_API_BASE=http://localhost:8000" > .env.local

# Start dev server
npm run dev
```

## Usage

### Upload a Paper

#### Using cURL

```bash
# Upload PDF file
curl -X POST http://localhost:8000/api/v1/papers \
  -F "pdf=@/path/to/paper.pdf" \
  -F "title=My Paper" \
  -F "visibility=private"

# Response:
# {
#   "aid": "abc123xyz",
#   "version": 1,
#   "viewer_url": "http://localhost:8000/api/v1/papers/abc123xyz/viewer",
#   "paper_url": "http://localhost:8000/api/v1/papers/abc123xyz"
# }
```

#### Using the UI

1. Navigate to http://localhost:3000
2. Upload a paper via the upload interface (coming soon)
3. View the paper at `/p/[aid]`

### View a Paper

#### Web UI

- Paper page: http://localhost:3000/p/[aid]
- PDF viewer: http://localhost:3000/p/[aid]/viewer

#### API

```bash
# Get paper metadata
curl http://localhost:8000/api/v1/papers/abc123xyz

# Stream PDF (supports Range requests)
curl http://localhost:8000/api/v1/papers/abc123xyz/viewer -o paper.pdf

# Get claims
curl http://localhost:8000/api/v1/papers/abc123xyz/claims
```

### Create a New Version

```bash
curl -X POST http://localhost:8000/api/v1/papers/abc123xyz/versions \
  -F "pdf=@/path/to/updated-paper.pdf"

# Response:
# {
#   "aid": "abc123xyz",
#   "version": 2,
#   "viewer_url": "http://localhost:8000/api/v1/papers/abc123xyz/viewer?v=2"
# }
```

## Environment Variables

### Backend

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `PAPERS_BASE`: Base path for storing papers (default: temp directory)
- `WEB_ORIGIN`: Frontend origin for CORS (default: http://localhost:3000)
- `MAX_PDF_SIZE_MB`: Maximum PDF size in MB (default: 25)
- `GEMINI_API_KEY`: Google Gemini API key (for LLM features)

### Frontend

- `NEXT_PUBLIC_API_BASE`: Backend API base URL (default: http://localhost:8000)

## Architecture

- **Backend**: FastAPI (Python) with PostgreSQL, Redis/RQ for async tasks
- **Frontend**: Next.js 14 (TypeScript) with Tailwind CSS
- **Database**: PostgreSQL with Alembic migrations
- **Queue**: Redis with RQ workers

## API Endpoints

### Papers

- `POST /api/v1/papers` - Create paper (upload PDF or URL)
- `POST /api/v1/papers/{aid}/versions` - Create new version
- `GET /api/v1/papers/{aid}` - Get paper metadata
- `GET /api/v1/papers/{aid}/viewer` - Stream PDF (Range support)
- `HEAD /api/v1/papers/{aid}/viewer` - Get PDF metadata
- `GET /api/v1/papers/{aid}/claims` - Get claims for paper

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend build test
cd frontend
npm run build
```

### Database Migrations

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## License

MIT
