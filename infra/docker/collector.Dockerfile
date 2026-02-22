# Collector Worker Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies including playwright dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    gnupg \
    # Playwright dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy package files
COPY packages/core/pyproject.toml packages/core/pyproject.toml
COPY packages/core/src packages/core/src

COPY packages/collector/pyproject.toml packages/collector/pyproject.toml
COPY packages/collector/src packages/collector/src

# Copy root pyproject.toml for workspace
COPY pyproject.toml pyproject.toml

# Install dependencies
RUN uv pip install --system --no-cache \
    -e packages/core \
    -e packages/collector

# Install playwright browsers
RUN playwright install chromium

# Copy rules directory
COPY rules /app/rules

# Create data directory
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app/packages/core/src:/app/packages/collector/src

# Default command (can be overridden)
CMD ["python", "-m", "collector"]
