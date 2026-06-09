"""Daily collection DAG for crawling hospital/doctor data.

Uses Celery worker pool for distributed task execution instead of
sequential for-loop processing.
"""

from datetime import datetime, timedelta
from typing import Any

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

RULES_DIR = "/opt/airflow/rules"
DATA_DIR = "/opt/airflow/data"

default_args = {
    "owner": "find-doctor",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def enqueue_crawl_jobs(**context: Any) -> list[str]:
    """Enqueue crawl tasks for all enabled sites to Celery.

    Returns:
        List of Celery task IDs
    """
    from collector.worker.enqueue import enqueue_all_sites

    task_ids = enqueue_all_sites(
        rules_dir=RULES_DIR,
        output_dir=DATA_DIR,
    )

    context["ti"].xcom_push(key="crawl_task_ids", value=task_ids)
    return task_ids


def wait_for_crawl_completion(**context: Any) -> list[dict[str, Any]]:
    """Wait for all crawl tasks to complete.

    Returns:
        List of task results
    """
    from collector.worker.enqueue import wait_for_tasks

    task_ids = context["ti"].xcom_pull(
        task_ids="enqueue_crawl_jobs",
        key="crawl_task_ids",
    )

    if not task_ids:
        return []

    return wait_for_tasks(task_ids, timeout=3600)


def enqueue_parse_jobs(**context: Any) -> list[str]:
    """Enqueue parse tasks for all enabled sites to Celery.

    Returns:
        List of Celery task IDs
    """
    from collector.worker.enqueue import enqueue_parse_all_sites

    task_ids = enqueue_parse_all_sites(
        rules_dir=RULES_DIR,
        input_dir=DATA_DIR,
        output_dir=DATA_DIR,
    )

    context["ti"].xcom_push(key="parse_task_ids", value=task_ids)
    return task_ids


def wait_for_parse_completion(**context: Any) -> list[dict[str, Any]]:
    """Wait for all parse tasks to complete.

    Returns:
        List of task results
    """
    from collector.worker.enqueue import wait_for_tasks

    task_ids = context["ti"].xcom_pull(
        task_ids="enqueue_parse_jobs",
        key="parse_task_ids",
    )

    if not task_ids:
        return []

    return wait_for_tasks(task_ids, timeout=3600)


def send_notifications(**context: Any) -> None:
    """Send notifications about job completion."""
    # TODO: Implement notification sending (Slack, email, etc.)
    pass


with DAG(
    dag_id="daily_collect",
    default_args=default_args,
    description="Daily collection of hospital and doctor data via Celery worker pool",
    schedule="0 2 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["collection", "daily"],
) as dag:

    start = EmptyOperator(task_id="start")

    enqueue_crawl = PythonOperator(
        task_id="enqueue_crawl_jobs",
        python_callable=enqueue_crawl_jobs,
    )

    wait_crawl = PythonOperator(
        task_id="wait_for_crawl_completion",
        python_callable=wait_for_crawl_completion,
    )

    enqueue_parse = PythonOperator(
        task_id="enqueue_parse_jobs",
        python_callable=enqueue_parse_jobs,
    )

    wait_parse = PythonOperator(
        task_id="wait_for_parse_completion",
        python_callable=wait_for_parse_completion,
    )

    notify_task = PythonOperator(
        task_id="send_notifications",
        python_callable=send_notifications,
        trigger_rule="all_done",
    )

    end = EmptyOperator(task_id="end")

    start >> enqueue_crawl >> wait_crawl >> enqueue_parse >> wait_parse >> notify_task >> end
