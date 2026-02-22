"""Jobs management router."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from admin_api.schemas.job import JobCreate, JobResponse, JobStatus

router = APIRouter()

# In-memory storage for demo (replace with database)
_jobs: dict[str, dict[str, Any]] = {}


@router.get("/", response_model=list[JobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    status_filter: JobStatus | None = None,
    site_id: str | None = None,
) -> list[dict[str, Any]]:
    """List all jobs.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status_filter: Filter by job status
        site_id: Filter by site ID

    Returns:
        List of jobs
    """
    jobs = list(_jobs.values())

    if status_filter:
        jobs = [j for j in jobs if j.get("status") == status_filter]

    if site_id:
        jobs = [j for j in jobs if j.get("site_id") == site_id]

    # Sort by created_at descending
    jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return jobs[skip : skip + limit]


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str) -> dict[str, Any]:
    """Get a job by ID.

    Args:
        job_id: Job identifier

    Returns:
        Job data

    Raises:
        HTTPException: If job not found
    """
    if job_id not in _jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found",
        )

    return _jobs[job_id]


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(job: JobCreate) -> dict[str, Any]:
    """Create a new crawl job.

    Args:
        job: Job configuration

    Returns:
        Created job
    """
    job_id = str(uuid4())
    now = datetime.now().isoformat()

    job_data = {
        "id": job_id,
        "site_id": job.site_id,
        "target_name": job.target_name,
        "status": JobStatus.PENDING,
        "created_at": now,
        "updated_at": now,
        "started_at": None,
        "completed_at": None,
        "result": None,
        "error": None,
    }

    _jobs[job_id] = job_data

    # TODO: Queue job for execution via Airflow/Celery

    return job_data


@router.post("/{job_id}/start", response_model=JobResponse)
async def start_job(job_id: str) -> dict[str, Any]:
    """Start a pending job.

    Args:
        job_id: Job identifier

    Returns:
        Updated job

    Raises:
        HTTPException: If job not found or not in pending state
    """
    if job_id not in _jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found",
        )

    job = _jobs[job_id]

    if job["status"] != JobStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not in pending state: {job['status']}",
        )

    now = datetime.now().isoformat()
    job["status"] = JobStatus.RUNNING
    job["started_at"] = now
    job["updated_at"] = now

    # TODO: Actually start the job

    return job


@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(job_id: str) -> dict[str, Any]:
    """Cancel a running or pending job.

    Args:
        job_id: Job identifier

    Returns:
        Updated job

    Raises:
        HTTPException: If job not found or already completed
    """
    if job_id not in _jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found",
        )

    job = _jobs[job_id]

    if job["status"] in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job in state: {job['status']}",
        )

    now = datetime.now().isoformat()
    job["status"] = JobStatus.CANCELLED
    job["completed_at"] = now
    job["updated_at"] = now

    # TODO: Actually cancel the job

    return job


@router.post("/{job_id}/retry", response_model=JobResponse)
async def retry_job(job_id: str) -> dict[str, Any]:
    """Retry a failed job.

    Args:
        job_id: Job identifier

    Returns:
        New job created from retry

    Raises:
        HTTPException: If job not found or not in failed state
    """
    if job_id not in _jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found",
        )

    job = _jobs[job_id]

    if job["status"] != JobStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only retry failed jobs, current state: {job['status']}",
        )

    # Create a new job with the same parameters
    new_job = await create_job(
        JobCreate(site_id=job["site_id"], target_name=job.get("target_name"))
    )

    return new_job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: str) -> None:
    """Delete a job.

    Args:
        job_id: Job identifier

    Raises:
        HTTPException: If job not found
    """
    if job_id not in _jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found",
        )

    del _jobs[job_id]
