"""Celery task wrappers for crawl and parse operations."""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from celery import signals

from collector.worker.celery_app import celery_app

logger = logging.getLogger(__name__)

RULES_DIR = "/app/rules"
OUTPUT_DIR = "/app/data"


@celery_app.task(
    bind=True,
    name="collector.worker.tasks.crawl_site_task",
    max_retries=3,
    default_retry_delay=60,
)
def crawl_site_task(
    self: Any,
    site_id: str,
    rules_dir: str = RULES_DIR,
    output_dir: str = OUTPUT_DIR,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Crawl all targets for a site.

    Args:
        site_id: Site identifier
        rules_dir: Directory containing rule files
        output_dir: Directory for output files
        params: Optional URL parameters

    Returns:
        Crawl summary
    """
    from collector.tasks.crawl_task import crawl_site

    try:
        return crawl_site(
            site_id=site_id,
            rules_dir=rules_dir,
            output_dir=output_dir,
            params=params,
        )
    except Exception as exc:
        logger.exception("Crawl failed for site %s", site_id)
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    name="collector.worker.tasks.crawl_site_browser_task",
    max_retries=3,
    default_retry_delay=60,
)
def crawl_site_browser_task(
    self: Any,
    site_id: str,
    rules_dir: str = RULES_DIR,
    output_dir: str = OUTPUT_DIR,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Crawl all targets for a site using browser crawler."""
    from collector.tasks.crawl_task import crawl_site

    try:
        return crawl_site(
            site_id=site_id,
            rules_dir=rules_dir,
            output_dir=output_dir,
            params=params,
        )
    except Exception as exc:
        logger.exception("Browser crawl failed for site %s", site_id)
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    name="collector.worker.tasks.crawl_site_ai_task",
    max_retries=2,
    default_retry_delay=120,
)
def crawl_site_ai_task(
    self: Any,
    site_id: str,
    rules_dir: str = RULES_DIR,
    output_dir: str = OUTPUT_DIR,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Crawl all targets for a site using AI agent crawler."""
    from collector.tasks.crawl_task import crawl_site

    try:
        return crawl_site(
            site_id=site_id,
            rules_dir=rules_dir,
            output_dir=output_dir,
            params=params,
        )
    except Exception as exc:
        logger.exception("AI agent crawl failed for site %s", site_id)
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    name="collector.worker.tasks.parse_site_task",
    max_retries=3,
    default_retry_delay=60,
)
def parse_site_task(
    self: Any,
    site_id: str,
    rules_dir: str = RULES_DIR,
    input_dir: str = OUTPUT_DIR,
    output_dir: str = OUTPUT_DIR,
) -> dict[str, Any]:
    """Parse all targets for a site.

    Args:
        site_id: Site identifier
        rules_dir: Directory containing rule files
        input_dir: Directory containing crawled HTML files
        output_dir: Directory for parsed output

    Returns:
        Parse summary
    """
    from collector.tasks.parse_task import parse_all_targets

    try:
        return parse_all_targets(
            site_id=site_id,
            rules_dir=rules_dir,
            input_dir=input_dir,
            output_dir=output_dir,
        )
    except Exception as exc:
        logger.exception("Parse failed for site %s", site_id)
        raise self.retry(exc=exc)


# -- Celery signals for structured logging --

@signals.task_prerun.connect
def on_task_prerun(
    sender: Any = None,
    task_id: str | None = None,
    task: Any = None,
    args: Any = None,
    kwargs: Any = None,
    **extra: Any,
) -> None:
    """Log job as running when task starts."""
    try:
        from core.database.job_log_repository import JobLogRepository

        repo = JobLogRepository.from_settings()
        site_id = kwargs.get("site_id", "") if kwargs else ""
        repo.create(
            celery_task_id=task_id or "",
            site_id=site_id,
            target_name=kwargs.get("target_name") if kwargs else None,
            status="running",
        )
    except Exception:
        logger.exception("Failed to log task_prerun for %s", task_id)


@signals.task_postrun.connect
def on_task_postrun(
    sender: Any = None,
    task_id: str | None = None,
    task: Any = None,
    args: Any = None,
    kwargs: Any = None,
    retval: Any = None,
    state: str | None = None,
    **extra: Any,
) -> None:
    """Log job as completed when task finishes successfully."""
    if state != "SUCCESS":
        return

    try:
        from core.database.job_log_repository import JobLogRepository

        repo = JobLogRepository.from_settings()
        summary = retval if isinstance(retval, dict) else {}
        repo.update_status(
            celery_task_id=task_id or "",
            status="completed",
            urls_crawled=summary.get("success_count", 0),
            urls_failed=summary.get("error_count", 0),
            items_parsed=summary.get("total_items", 0),
            result_summary=summary,
        )
    except Exception:
        logger.exception("Failed to log task_postrun for %s", task_id)


@signals.task_failure.connect
def on_task_failure(
    sender: Any = None,
    task_id: str | None = None,
    exception: BaseException | None = None,
    args: Any = None,
    kwargs: Any = None,
    traceback: Any = None,
    einfo: Any = None,
    **extra: Any,
) -> None:
    """Log job as failed when task fails."""
    try:
        from core.database.job_log_repository import JobLogRepository

        repo = JobLogRepository.from_settings()
        repo.update_status(
            celery_task_id=task_id or "",
            status="failed",
            error_message=str(exception) if exception else "Unknown error",
        )
    except Exception:
        logger.exception("Failed to log task_failure for %s", task_id)
