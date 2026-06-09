# Admin API Dockerfile
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

COPY packages/admin-api/pyproject.toml packages/admin-api/pyproject.toml
COPY packages/admin-api/src packages/admin-api/src

# Copy root pyproject.toml for workspace
COPY pyproject.toml pyproject.toml

# Install dependencies
RUN uv pip install --system --no-cache \
    -e packages/core \
    -e packages/admin-api

# Copy rules directory
COPY rules /app/rules

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app/packages/core/src:/app/packages/admin-api/src

# Expose port
EXPOSE 8500

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8500/health || exit 1

# Run the application
CMD ["uvicorn", "admin_api.app:app", "--host", "0.0.0.0", "--port", "8500"]
