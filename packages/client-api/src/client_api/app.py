"""FastAPI application for client API."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from client_api.routers import doctors, hospitals, search


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup - initialize Redis connection pool
    yield
    # Shutdown - close Redis connections


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Gungil Client API",
        description="API for querying hospital and doctor information",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["GET"],  # Read-only API
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(doctors.router, prefix="/api/doctors", tags=["doctors"])
    app.include_router(hospitals.router, prefix="/api/hospitals", tags=["hospitals"])
    app.include_router(search.router, prefix="/api/search", tags=["search"])

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}

    return app


app = create_app()
