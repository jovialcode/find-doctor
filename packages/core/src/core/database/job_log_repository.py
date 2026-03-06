"""Repository for job log persistence using SQLAlchemy."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import MetaData, Table, create_engine
from sqlalchemy.engine import Engine

from core.models.job_log import JobLog

logger = logging.getLogger(__name__)

metadata = MetaData()

job_logs_table = Table(
    "job_logs",
    metadata,
    sa.Column("id", sa.String(36), primary_key=True),
    sa.Column("celery_task_id", sa.String(255), nullable=False, index=True),
    sa.Column("site_id", sa.String(255), nullable=False, index=True),
    sa.Column("target_name", sa.String(255), nullable=True),
    sa.Column("status", sa.String(50), nullable=False, index=True),
    sa.Column("started_at", sa.DateTime, nullable=True),
    sa.Column("completed_at", sa.DateTime, nullable=True),
    sa.Column("urls_crawled", sa.Integer, default=0),
    sa.Column("urls_failed", sa.Integer, default=0),
    sa.Column("items_parsed", sa.Integer, default=0),
    sa.Column("error_message", sa.Text, nullable=True),
    sa.Column("result_summary", sa.Text, nullable=True),
    sa.Column("created_at", sa.DateTime, nullable=False, index=True),
)


class JobLogRepository:
    """Repository for job log CRUD operations."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    @classmethod
    def from_settings(cls) -> JobLogRepository:
        """Create repository from application settings."""
        from core.config.settings import get_settings

        settings = get_settings()
        engine = create_engine(settings.database_url)
        return cls(engine)

    @classmethod
    def from_url(cls, database_url: str) -> JobLogRepository:
        """Create repository from a database URL."""
        engine = create_engine(database_url)
        return cls(engine)

    def create_tables(self) -> None:
        """Create the job_logs table if it doesn't exist."""
        metadata.create_all(self._engine)

    def create(
        self,
        celery_task_id: str,
        site_id: str,
        target_name: str | None = None,
        status: str = "pending",
    ) -> JobLog:
        """Create a new job log entry.

        Args:
            celery_task_id: Celery task ID
            site_id: Site identifier
            target_name: Optional target name
            status: Initial status

        Returns:
            Created JobLog
        """
        now = datetime.now()
        job_id = str(uuid4())
        started_at = now if status == "running" else None

        with self._engine.connect() as conn:
            conn.execute(
                job_logs_table.insert().values(
                    id=job_id,
                    celery_task_id=celery_task_id,
                    site_id=site_id,
                    target_name=target_name,
                    status=status,
                    started_at=started_at,
                    completed_at=None,
                    urls_crawled=0,
                    urls_failed=0,
                    items_parsed=0,
                    error_message=None,
                    result_summary=None,
                    created_at=now,
                )
            )
            conn.commit()

        return JobLog(
            id=job_id,
            celery_task_id=celery_task_id,
            site_id=site_id,
            target_name=target_name,
            status=status,
            started_at=started_at,
            created_at=now,
        )

    def update_status(
        self,
        celery_task_id: str,
        status: str,
        urls_crawled: int = 0,
        urls_failed: int = 0,
        items_parsed: int = 0,
        error_message: str | None = None,
        result_summary: dict[str, Any] | None = None,
    ) -> None:
        """Update the status of a job log by Celery task ID.

        Args:
            celery_task_id: Celery task ID
            status: New status
            urls_crawled: Number of successfully crawled URLs
            urls_failed: Number of failed URLs
            items_parsed: Number of parsed items
            error_message: Error message if failed
            result_summary: Summary of results
        """
        values: dict[str, Any] = {"status": status}

        if status in ("completed", "failed"):
            values["completed_at"] = datetime.now()

        if urls_crawled:
            values["urls_crawled"] = urls_crawled
        if urls_failed:
            values["urls_failed"] = urls_failed
        if items_parsed:
            values["items_parsed"] = items_parsed
        if error_message:
            values["error_message"] = error_message
        if result_summary:
            values["result_summary"] = json.dumps(result_summary, default=str)

        with self._engine.connect() as conn:
            conn.execute(
                job_logs_table.update()
                .where(job_logs_table.c.celery_task_id == celery_task_id)
                .values(**values)
            )
            conn.commit()

    def find_by_id(self, job_id: str) -> JobLog | None:
        """Find a job log by ID."""
        with self._engine.connect() as conn:
            row = conn.execute(
                job_logs_table.select().where(job_logs_table.c.id == job_id)
            ).first()

        if row is None:
            return None
        return self._row_to_job_log(row)

    def find_by_celery_task_id(self, celery_task_id: str) -> JobLog | None:
        """Find a job log by Celery task ID."""
        with self._engine.connect() as conn:
            row = conn.execute(
                job_logs_table.select().where(
                    job_logs_table.c.celery_task_id == celery_task_id
                )
            ).first()

        if row is None:
            return None
        return self._row_to_job_log(row)

    def find_by_site_id(
        self,
        site_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[JobLog]:
        """Find job logs by site ID."""
        with self._engine.connect() as conn:
            rows = conn.execute(
                job_logs_table.select()
                .where(job_logs_table.c.site_id == site_id)
                .order_by(job_logs_table.c.created_at.desc())
                .limit(limit)
                .offset(offset)
            ).fetchall()

        return [self._row_to_job_log(row) for row in rows]

    def find_recent(
        self,
        limit: int = 100,
        offset: int = 0,
        status: str | None = None,
        site_id: str | None = None,
    ) -> list[JobLog]:
        """Find recent job logs with optional filtering."""
        query = job_logs_table.select().order_by(job_logs_table.c.created_at.desc())

        if status:
            query = query.where(job_logs_table.c.status == status)
        if site_id:
            query = query.where(job_logs_table.c.site_id == site_id)

        query = query.limit(limit).offset(offset)

        with self._engine.connect() as conn:
            rows = conn.execute(query).fetchall()

        return [self._row_to_job_log(row) for row in rows]

    def find_recent_errors(
        self,
        limit: int = 100,
        site_id: str | None = None,
    ) -> list[JobLog]:
        """Find recent failed job logs."""
        return self.find_recent(limit=limit, status="failed", site_id=site_id)

    def count_by_status(self, site_id: str | None = None) -> dict[str, int]:
        """Count job logs grouped by status."""
        query = sa.select(
            job_logs_table.c.status,
            sa.func.count().label("count"),
        ).group_by(job_logs_table.c.status)

        if site_id:
            query = query.where(job_logs_table.c.site_id == site_id)

        with self._engine.connect() as conn:
            rows = conn.execute(query).fetchall()

        return {row[0]: row[1] for row in rows}

    def _row_to_job_log(self, row: Any) -> JobLog:
        """Convert a database row to a JobLog instance."""
        result_summary = {}
        if row.result_summary:
            try:
                result_summary = json.loads(row.result_summary)
            except (json.JSONDecodeError, TypeError):
                result_summary = {}

        return JobLog(
            id=row.id,
            celery_task_id=row.celery_task_id,
            site_id=row.site_id,
            target_name=row.target_name,
            status=row.status,
            started_at=row.started_at,
            completed_at=row.completed_at,
            urls_crawled=row.urls_crawled or 0,
            urls_failed=row.urls_failed or 0,
            items_parsed=row.items_parsed or 0,
            error_message=row.error_message,
            result_summary=result_summary,
            created_at=row.created_at,
        )
