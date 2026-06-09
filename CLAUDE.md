# Gungil Project

## Overview

Healthcare data collection platform that crawls hospital and doctor information using multi-strategy scraping (HTTP, browser automation, and AI-powered extraction). Built as a Python monorepo.

## Architecture

### Monorepo Structure

```
find-doctor/
├── packages/
│   ├── core/          # Shared models, DB repos, config
│   ├── collector/     # Web crawlers, parsers, Celery tasks
│   ├── admin-api/     # Admin management API (port 8500)
│   └── client-api/   # Public query API (port 8501)
├── infra/docker/      # Dockerfiles
├── rules/hospitals/   # YAML crawling rules per site
├── airflow/           # Apache Airflow config
├── pyproject.toml     # UV workspace root
└── docker-compose.yml
```

### Services (Docker Compose)

| Service | Port | Purpose |
|---|---|---|
| postgres | 5432 | Primary database |
| redis | 6379 | Cache & Celery broker |
| minio | 9000/9001 | Object storage |
| admin-api | 8500 | Admin management |
| client-api | 8501 | Public API |
| collector-worker | - | HTTP/Browser scrapers (4 workers) |
| ai-agent-worker | - | AI-powered scrapers (2 workers) |
| flower | 5555 | Celery monitoring UI |

## Tech Stack

- **Language:** Python 3.12
- **Package Manager:** uv
- **Web Framework:** FastAPI + Uvicorn
- **Database:** PostgreSQL 16 + SQLAlchemy 2.0
- **Task Queue:** Celery 5.3 + Redis
- **Browser Automation:** Playwright
- **AI Extraction:** browser-use + langchain-anthropic (Claude)
- **Cloud:** GCP (BigQuery, Cloud Storage, Firestore), MinIO

## Development Commands

```bash
make install       # Install all dependencies
make dev           # Run admin-api + client-api concurrently
make admin-api     # Run admin API only
make client-api    # Run client API only
make test          # Run all tests
make format        # black + isort formatting
make lint          # ruff linting
make docker-up     # Start full stack
make docker-down   # Stop full stack
```

## Coding Standards

- **Formatter:** black (100 char line length)
- **Linter:** ruff
- **Imports:** isort
- **Type checker:** mypy (strict)
- All function signatures must have type annotations
- Use dataclasses/NamedTuples for immutable data structures
- Use `logging` module, not `print()`

## Testing

```bash
pytest                              # Run all tests
pytest --cov=src --cov-report=term-missing  # With coverage
pytest -m unit                      # Unit tests only
pytest -m integration               # Integration tests only
```

Test markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`

## Key Concepts

### Crawling Strategies

The collector supports three crawler types configured via YAML rules:

- **HTTP** (`scraper.http` queue): Standard HTTP requests with httpx
- **Browser** (`scraper.browser` queue): Playwright browser automation
- **AI Agent** (`scraper.ai_agent` queue): Claude-powered intelligent extraction via browser-use

### YAML Rule System

Site-specific crawling behavior is defined in `rules/hospitals/`:

```yaml
site:
  base_url: "https://example.com"
  crawler:
    type: http  # or browser, ai_agent
    rate_limit: 1.0
    timeout: 30
  targets:
    - url_pattern: "/doctors"
      selectors:
        name: ".doctor-name"
        specialty: ".specialty"
  pagination:
    type: page_param  # or next_button, infinite_scroll
```

### Data Models (core package)

- **Hospital:** id, name, address, phone, website, departments, type, region, collected_at
- **Doctor:** name, position, department, specialty, hospital reference
- **JobLog:** Tracks scraping job execution and results

## Environment Configuration

Copy `.env.example` to `.env` and configure:

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `ANTHROPIC_API_KEY` - Required for AI agent crawler
- GCP credentials (for cloud storage/BigQuery features)
- MinIO credentials (for local object storage)

## Package Dependencies

Each package has its own `pyproject.toml`. The root workspace manages shared deps via uv. Run `make install` from the project root to install everything.
