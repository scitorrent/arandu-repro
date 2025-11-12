# Arandu Repro v0 - Backend

Backend service for Arandu Repro v0.

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- PostgreSQL (for production) or SQLite (for development)
- Redis (for job queue)

### Installation

```bash
# Install dependencies
make install
# or
uv pip install -e ".[dev]"
```

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
DATABASE_URL=sqlite:///./arandu.db
REDIS_URL=redis://localhost:6379/0
ARTIFACTS_BASE_PATH=/var/arandu/artifacts
TEMP_REPOS_PATH=/tmp/arandu/repos
```

## Development

### Run API server

```bash
make dev
# or
uv run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Run worker

```bash
python -m app.worker
```

### Run tests

```bash
make test
# or
uv run pytest
```

### Code formatting

```bash
make format
# or
uv run black app tests
uv run isort app tests
uv run ruff check --fix app tests
```

### Database migrations

```bash
# Run migrations
make migrate
# or
uv run alembic upgrade head

# Create new migration
make migration msg="description"
# or
uv run alembic revision --autogenerate -m "description"
```

## API Endpoints

- `GET /health` - Health check
- `POST /api/v1/jobs` - Create a new job
- `GET /api/v1/jobs/{id}` - Get job details
- `GET /api/v1/jobs/{id}/status` - Get job status (lightweight)

## Project Structure

```
backend/
├── app/
│   ├── api/           # API routes
│   ├── db/             # Database session management
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── worker/         # Worker process
│   ├── utils/          # Utilities
│   ├── config.py       # Configuration
│   └── main.py         # FastAPI app
├── alembic/            # Database migrations
├── tests/              # Tests
└── pyproject.toml      # Dependencies
```

## Docker

See `infra/docker-compose.yml` for full stack setup.
