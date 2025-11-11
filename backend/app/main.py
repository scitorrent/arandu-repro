"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, jobs

app = FastAPI(
    title="Arandu Repro v0",
    description="Reproducibility service for AI research papers",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    from app.db.session import init_db

    init_db()
