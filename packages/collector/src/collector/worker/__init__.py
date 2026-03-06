"""Celery worker pool for distributed task execution."""

from collector.worker.celery_app import celery_app

__all__ = ["celery_app"]
