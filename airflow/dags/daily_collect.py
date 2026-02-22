"""Daily collection DAG for crawling hospital/doctor data."""

from datetime import datetime, timedelta
from typing import Any

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.task_group import TaskGroup

# Default arguments for all tasks
default_args = {
    "owner": "gungil",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def crawl_site_group(site_ids: list[str], **context: Any) -> dict[str, Any]:
    """Crawl a group of sites.

    Args:
        site_ids: List of site IDs to crawl
        context: Airflow context

    Returns:
        Crawl results summary
    """
    from collector.tasks.crawl_task import crawl_site

    results: list[dict[str, Any]] = []

    for site_id in site_ids:
        try:
            result = crawl_site(
                site_id=site_id,
                rules_dir="/opt/airflow/rules",
                output_dir="/opt/airflow/data",
            )
            results.append(result)
        except Exception as e:
            results.append({
                "site_id": site_id,
                "error": str(e),
            })

    return {
        "group_size": len(site_ids),
        "success_count": len([r for r in results if "error" not in r]),
        "results": results,
    }


def parse_all_sites(**context: Any) -> dict[str, Any]:
    """Parse all crawled data.

    Args:
        context: Airflow context

    Returns:
        Parse results summary
    """
    from collector.tasks.parse_task import parse_all_targets
    from collector.rules.loader import RuleLoader

    loader = RuleLoader("/opt/airflow/rules")
    rules = loader.load_all_rules()

    results: list[dict[str, Any]] = []

    for rule in rules:
        if not rule.enabled:
            continue

        try:
            result = parse_all_targets(
                site_id=rule.id,
                rules_dir="/opt/airflow/rules",
                input_dir="/opt/airflow/data",
                output_dir="/opt/airflow/data",
            )
            results.append(result)
        except Exception as e:
            results.append({
                "site_id": rule.id,
                "error": str(e),
            })

    return {
        "sites_processed": len(results),
        "results": results,
    }


def load_to_storage(**context: Any) -> dict[str, Any]:
    """Load parsed data to permanent storage.

    Args:
        context: Airflow context

    Returns:
        Load results summary
    """
    # TODO: Implement loading to BigQuery/GCS
    return {"status": "not_implemented"}


def send_notifications(**context: Any) -> None:
    """Send notifications about job completion.

    Args:
        context: Airflow context
    """
    # TODO: Implement notification sending (Slack, email, etc.)
    pass


# Define the DAG
with DAG(
    dag_id="daily_collect",
    default_args=default_args,
    description="Daily collection of hospital and doctor data",
    schedule="0 2 * * *",  # Run at 02:00 daily
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["collection", "daily"],
) as dag:

    start = EmptyOperator(task_id="start")

    # Site groups for parallel crawling
    # In production, this would be loaded from configuration
    site_groups = [
        ["site_group_0"],  # Sites 0-19
        ["site_group_1"],  # Sites 20-39
        # ... more groups
    ]

    with TaskGroup(group_id="crawl_sites") as crawl_group:
        crawl_tasks = []
        for i, group in enumerate(site_groups):
            task = PythonOperator(
                task_id=f"crawl_group_{i}",
                python_callable=crawl_site_group,
                op_kwargs={"site_ids": group},
            )
            crawl_tasks.append(task)

    parse_task = PythonOperator(
        task_id="parse_all",
        python_callable=parse_all_sites,
    )

    load_task = PythonOperator(
        task_id="load_to_storage",
        python_callable=load_to_storage,
    )

    notify_task = PythonOperator(
        task_id="send_notifications",
        python_callable=send_notifications,
        trigger_rule="all_done",  # Run even if upstream fails
    )

    end = EmptyOperator(task_id="end")

    # Define task dependencies
    start >> crawl_group >> parse_task >> load_task >> notify_task >> end
