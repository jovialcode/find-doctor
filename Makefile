.PHONY: help install admin-api client-api dev test lint format clean \
	docker-up docker-down docker-build docker-logs docker-ps

# Default ports
ADMIN_PORT ?= 8500
CLIENT_PORT ?= 8501

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Local Development:"
	@echo "  install      Install dependencies"
	@echo "  admin-api    Run admin API server (port $(ADMIN_PORT))"
	@echo "  client-api   Run client API server (port $(CLIENT_PORT))"
	@echo "  dev          Run both API servers concurrently"
	@echo "  test         Run tests"
	@echo "  lint         Run linter (ruff)"
	@echo "  format       Format code (black + isort)"
	@echo "  clean        Clean cache files"
	@echo ""
	@echo "Docker:"
	@echo "  docker-up    Start all services with Docker Compose"
	@echo "  docker-down  Stop all Docker Compose services"
	@echo "  docker-build Build Docker images"
	@echo "  docker-logs  Show logs from Docker Compose services"
	@echo "  docker-ps    Show running Docker Compose services"

install:
	uv sync

admin-api:
	uv run uvicorn admin_api.app:app --reload --port $(ADMIN_PORT)

client-api:
	uv run uvicorn client_api.app:app --reload --port $(CLIENT_PORT)

dev:
	@echo "Starting admin-api on port $(ADMIN_PORT) and client-api on port $(CLIENT_PORT)..."
	@trap 'kill 0' SIGINT; \
	uv run uvicorn admin_api.app:app --reload --port $(ADMIN_PORT) & \
	uv run uvicorn client_api.app:app --reload --port $(CLIENT_PORT) & \
	wait

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run black .
	uv run isort .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Docker targets
docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-build:
	docker compose build

docker-logs:
	docker compose logs -f

docker-ps:
	docker compose ps
