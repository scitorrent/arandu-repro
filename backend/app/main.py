"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import badges, health, jobs, metrics, papers, reviews
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup: Initialize database
    from app.db.session import init_db

    init_db()
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Arandu Repro v0",
    description="Reproducibility service for AI research papers",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
web_origin = getattr(settings, "web_origin", "http://localhost:3000")
allowed_origins = [
    web_origin,
    "http://web:3000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(badges.router, prefix="/api/v1")
app.include_router(metrics.router, prefix="/api/v1")
app.include_router(papers.router)
