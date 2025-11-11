.PHONY: dev test lint format install clean

# Install dependencies
install:
	uv pip install -e ".[dev]"

# Run development server
dev:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	uv run pytest

# Run tests with coverage
test-cov:
	uv run pytest --cov=app --cov-report=html --cov-report=term

# Lint code
lint:
	uv run ruff check app tests
	uv run isort --check-only app tests
	uv run black --check app tests

# Format code
format:
	uv run black app tests
	uv run isort app tests
	uv run ruff check --fix app tests

# Run database migrations
migrate:
	uv run alembic upgrade head

# Create new migration
migration:
	uv run alembic revision --autogenerate -m "$(msg)"

# Clean generated files
clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov

