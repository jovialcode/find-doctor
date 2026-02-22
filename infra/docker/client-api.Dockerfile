# Client API Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy package files
COPY packages/core/pyproject.toml packages/core/pyproject.toml
COPY packages/core/src packages/core/src

COPY packages/client-api/pyproject.toml packages/client-api/pyproject.toml
COPY packages/client-api/src packages/client-api/src

# Copy root pyproject.toml for workspace
COPY pyproject.toml pyproject.toml

# Install dependencies
RUN uv pip install --system --no-cache \
    -e packages/core \
    -e packages/client-api

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app/packages/core/src:/app/packages/client-api/src

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "client_api.app:app", "--host", "0.0.0.0", "--port", "8000"]
