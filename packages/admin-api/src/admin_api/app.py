"""FastAPI application for admin API."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from admin_api.routers import jobs, monitoring, rules, sites


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup
    yield
    # Shutdown


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Gungil Admin API",
        description="Admin API for managing hospital/doctor data collection",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(sites.router, prefix="/api/sites", tags=["sites"])
    app.include_router(rules.router, prefix="/api/rules", tags=["rules"])
    app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
    app.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"])

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}

    return app


app = create_app()
