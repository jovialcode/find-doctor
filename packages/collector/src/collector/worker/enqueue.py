"""Service for enqueueing crawl/parse jobs to Celery."""

import logging
from typing import Any

from collector.rules.loader import RuleLoader
from collector.worker.tasks import (
    crawl_site_ai_task,
    crawl_site_browser_task,
    crawl_site_task,
    parse_site_task,
)

logger = logging.getLogger(__name__)


def enqueue_all_sites(
    rules_dir: str,
    output_dir: str,
    params: dict[str, Any] | None = None,
) -> list[str]:
    """Enqueue crawl tasks for all enabled sites.

    Loads site rules and dispatches each to the appropriate Celery queue
    based on crawler type.

    Args:
        rules_dir: Directory containing rule files
        output_dir: Directory for output files
        params: Optional URL parameters

    Returns:
        List of Celery task IDs
    """
    loader = RuleLoader(rules_dir)
    rules = loader.load_all_rules()

    task_ids: list[str] = []

    for rule in rules:
        if not rule.enabled:
            continue

        crawler_type = rule.crawler.type

        if crawler_type == "ai_agent":
            result = crawl_site_ai_task.delay(
                site_id=rule.id,
                rules_dir=rules_dir,
                output_dir=output_dir,
                params=params,
            )
        elif crawler_type == "browser":
            result = crawl_site_browser_task.delay(
                site_id=rule.id,
                rules_dir=rules_dir,
                output_dir=output_dir,
                params=params,
            )
        else:
            result = crawl_site_task.delay(
                site_id=rule.id,
                rules_dir=rules_dir,
                output_dir=output_dir,
                params=params,
            )

        task_ids.append(result.id)
        logger.info("Enqueued crawl for site %s (type=%s) -> task %s", rule.id, crawler_type, result.id)

    return task_ids


def enqueue_parse_all_sites(
    rules_dir: str,
    input_dir: str,
    output_dir: str,
) -> list[str]:
    """Enqueue parse tasks for all enabled sites.

    Args:
        rules_dir: Directory containing rule files
        input_dir: Directory containing crawled HTML files
        output_dir: Directory for parsed output

    Returns:
        List of Celery task IDs
    """
    loader = RuleLoader(rules_dir)
    rules = loader.load_all_rules()

    task_ids: list[str] = []

    for rule in rules:
        if not rule.enabled:
            continue

        result = parse_site_task.delay(
            site_id=rule.id,
            rules_dir=rules_dir,
            input_dir=input_dir,
            output_dir=output_dir,
        )

        task_ids.append(result.id)
        logger.info("Enqueued parse for site %s -> task %s", rule.id, result.id)

    return task_ids


def wait_for_tasks(task_ids: list[str], timeout: float = 3600) -> list[dict[str, Any]]:
    """Wait for a list of Celery tasks to complete.

    Args:
        task_ids: List of Celery task IDs to wait for
        timeout: Maximum time to wait in seconds

    Returns:
        List of task results with status
    """
    from celery.result import AsyncResult

    from collector.worker.celery_app import celery_app

    results: list[dict[str, Any]] = []

    for task_id in task_ids:
        async_result = AsyncResult(task_id, app=celery_app)
        try:
            result = async_result.get(timeout=timeout)
            results.append({
                "task_id": task_id,
                "status": "completed",
                "result": result,
            })
        except Exception as e:
            results.append({
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
            })

    return results
