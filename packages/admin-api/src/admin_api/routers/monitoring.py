"""Monitoring router for system status and metrics."""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter

from core.database.job_log_repository import JobLogRepository

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_repo() -> JobLogRepository:
    return JobLogRepository.from_settings()


@router.get("/status")
async def get_system_status() -> dict[str, Any]:
    """Get overall system status."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "api": "healthy",
            "database": "healthy",
            "storage": "healthy",
            "celery": "healthy",
        },
    }


@router.get("/stats")
async def get_stats() -> dict[str, Any]:
    """Get collection statistics from job_logs."""
    try:
        repo = _get_repo()
        counts = repo.count_by_status()

        recent = repo.find_recent(limit=1)
        last_crawl = recent[0].created_at.isoformat() if recent else None

        return {
            "last_crawl": last_crawl,
            "jobs_today": {
                "total": sum(counts.values()),
                "completed": counts.get("completed", 0),
                "failed": counts.get("failed", 0),
                "running": counts.get("running", 0),
                "pending": counts.get("pending", 0),
            },
        }
    except Exception:
        logger.exception("Failed to fetch stats")
        return {
            "last_crawl": None,
            "jobs_today": {"total": 0, "completed": 0, "failed": 0, "running": 0},
        }


@router.get("/crawl-history")
async def get_crawl_history(
    site_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Get crawl history from job_logs."""
    try:
        repo = _get_repo()
        logs = repo.find_recent(limit=limit, site_id=site_id)
        return [log.to_dict() for log in logs]
    except Exception:
        logger.exception("Failed to fetch crawl history")
        return []


@router.get("/errors")
async def get_recent_errors(
    limit: int = 100,
    site_id: str | None = None,
) -> list[dict[str, Any]]:
    """Get recent errors from job_logs."""
    try:
        repo = _get_repo()
        logs = repo.find_recent_errors(limit=limit, site_id=site_id)
        return [log.to_dict() for log in logs]
    except Exception:
        logger.exception("Failed to fetch recent errors")
        return []


@router.get("/sites/{site_id}/stats")
async def get_site_stats(site_id: str) -> dict[str, Any]:
    """Get statistics for a specific site from job_logs."""
    try:
        repo = _get_repo()
        counts = repo.count_by_status(site_id=site_id)
        recent = repo.find_by_site_id(site_id, limit=1)

        last_crawl = recent[0].created_at.isoformat() if recent else None
        completed = [
            log for log in repo.find_by_site_id(site_id, limit=1)
            if log.status == "completed"
        ]
        last_success = completed[0].created_at.isoformat() if completed else None

        return {
            "site_id": site_id,
            "total_crawls": sum(counts.values()),
            "successful_crawls": counts.get("completed", 0),
            "failed_crawls": counts.get("failed", 0),
            "last_crawl": last_crawl,
            "last_success": last_success,
        }
    except Exception:
        logger.exception("Failed to fetch site stats for %s", site_id)
        return {
            "site_id": site_id,
            "total_crawls": 0,
            "successful_crawls": 0,
            "failed_crawls": 0,
            "last_crawl": None,
            "last_success": None,
        }


@router.get("/alerts")
async def get_alerts() -> list[dict[str, Any]]:
    """Get active alerts based on recent failures."""
    try:
        repo = _get_repo()
        recent_errors = repo.find_recent_errors(limit=10)
        return [
            {
                "level": "error",
                "site_id": log.site_id,
                "message": log.error_message or "Unknown error",
                "timestamp": log.created_at.isoformat(),
            }
            for log in recent_errors
        ]
    except Exception:
        logger.exception("Failed to fetch alerts")
        return []
