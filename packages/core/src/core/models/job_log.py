"""Job log model for structured success/failure tracking."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


@dataclass(frozen=True)
class JobLog:
    """Immutable record of a job execution.

    Attributes:
        id: Unique job log identifier
        celery_task_id: Celery task ID
        site_id: Site identifier
        target_name: Optional target name
        status: Job status (pending, running, completed, failed)
        started_at: When the job started
        completed_at: When the job completed
        urls_crawled: Number of successfully crawled URLs
        urls_failed: Number of failed URLs
        items_parsed: Number of parsed items
        error_message: Error message if job failed
        result_summary: Summary of job results
        created_at: When the log was created
    """

    id: str
    celery_task_id: str
    site_id: str
    target_name: str | None = None
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    urls_crawled: int = 0
    urls_failed: int = 0
    items_parsed: int = 0
    error_message: str | None = None
    result_summary: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "celery_task_id": self.celery_task_id,
            "site_id": self.site_id,
            "target_name": self.target_name,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "urls_crawled": self.urls_crawled,
            "urls_failed": self.urls_failed,
            "items_parsed": self.items_parsed,
            "error_message": self.error_message,
            "result_summary": self.result_summary,
            "created_at": self.created_at.isoformat(),
        }
