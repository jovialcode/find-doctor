"""Jobs management router backed by PostgreSQL job_logs and Celery."""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status

from admin_api.schemas.job import JobCreate, JobResponse, JobStatus
from core.database.job_log_repository import JobLogRepository

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_repo() -> JobLogRepository:
    return JobLogRepository.from_settings()


def _job_log_to_response(log: Any) -> dict[str, Any]:
    """Convert a JobLog to a JobResponse-compatible dict."""
    status_map = {
        "pending": JobStatus.PENDING,
        "running": JobStatus.RUNNING,
        "completed": JobStatus.COMPLETED,
        "failed": JobStatus.FAILED,
    }
    return {
        "id": log.id,
        "site_id": log.site_id,
        "target_name": log.target_name,
        "status": status_map.get(log.status, JobStatus.PENDING),
        "created_at": log.created_at.isoformat(),
        "updated_at": (log.completed_at or log.started_at or log.created_at).isoformat(),
        "started_at": log.started_at.isoformat() if log.started_at else None,
        "completed_at": log.completed_at.isoformat() if log.completed_at else None,
        "result": log.result_summary or None,
        "error": log.error_message,
    }


@router.get("/", response_model=list[JobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    status_filter: JobStatus | None = None,
    site_id: str | None = None,
) -> list[dict[str, Any]]:
    """List all jobs from PostgreSQL job_logs."""
    try:
        repo = _get_repo()
        status_value = status_filter.value if status_filter else None
        logs = repo.find_recent(
            limit=limit,
            offset=skip,
            status=status_value,
            site_id=site_id,
        )
        return [_job_log_to_response(log) for log in logs]
    except Exception:
        logger.exception("Failed to list jobs")
        return []


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str) -> dict[str, Any]:
    """Get a job by ID from PostgreSQL."""
    repo = _get_repo()
    log = repo.find_by_id(job_id)

    if log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found",
        )

    return _job_log_to_response(log)


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(job: JobCreate) -> dict[str, Any]:
    """Create a new crawl job and enqueue it via Celery."""
    from collector.worker.tasks import crawl_site_task

    celery_result = crawl_site_task.delay(site_id=job.site_id)

    repo = _get_repo()
    log = repo.create(
        celery_task_id=celery_result.id,
        site_id=job.site_id,
        target_name=job.target_name,
        status="pending",
    )

    return _job_log_to_response(log)


@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(job_id: str) -> dict[str, Any]:
    """Cancel a running or pending job."""
    repo = _get_repo()
    log = repo.find_by_id(job_id)

    if log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found",
        )

    if log.status in ("completed", "failed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job in state: {log.status}",
        )

    from collector.worker.celery_app import celery_app

    celery_app.control.revoke(log.celery_task_id, terminate=True)

    repo.update_status(
        celery_task_id=log.celery_task_id,
        status="failed",
        error_message="Cancelled by user",
    )

    updated = repo.find_by_id(job_id)
    return _job_log_to_response(updated)


@router.post("/{job_id}/retry", response_model=JobResponse)
async def retry_job(job_id: str) -> dict[str, Any]:
    """Retry a failed job by creating a new Celery task."""
    repo = _get_repo()
    log = repo.find_by_id(job_id)

    if log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found",
        )

    if log.status != "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only retry failed jobs, current state: {log.status}",
        )

    new_job = await create_job(
        JobCreate(site_id=log.site_id, target_name=log.target_name)
    )
    return new_job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: str) -> None:
    """Delete a job."""
    repo = _get_repo()
    log = repo.find_by_id(job_id)

    if log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found",
        )
