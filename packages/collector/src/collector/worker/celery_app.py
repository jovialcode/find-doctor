"""Celery application configuration."""

from celery import Celery

from core.config.settings import get_settings


def create_celery_app() -> Celery:
    """Create and configure the Celery application."""
    settings = get_settings()

    app = Celery(
        "collector",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend or settings.database_url,
    )

    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="Asia/Seoul",
        enable_utc=True,
        task_track_started=True,
        task_routes={
            "collector.worker.tasks.crawl_site_task": {"queue": "scraper.http"},
            "collector.worker.tasks.crawl_site_browser_task": {"queue": "scraper.browser"},
            "collector.worker.tasks.crawl_site_ai_task": {"queue": "scraper.ai_agent"},
            "collector.worker.tasks.parse_site_task": {"queue": "scraper.http"},
        },
        task_default_queue="scraper.http",
        worker_prefetch_multiplier=1,
        task_acks_late=True,
    )

    app.autodiscover_tasks(["collector.worker"])

    return app


celery_app = create_celery_app()
