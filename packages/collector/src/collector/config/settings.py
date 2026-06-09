"""Collector-specific settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class CollectorSettings(BaseSettings):
    """Settings for the collector package."""

    # Celery
    celery_broker_url: str = Field(default="redis://localhost:6379/0", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="", alias="CELERY_RESULT_BACKEND")
    worker_concurrency: int = Field(default=4, alias="WORKER_CONCURRENCY")

    # AI Agent
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")

    # Crawler defaults (fallback when not specified in YAML rule)
    crawler_rate_limit: float = Field(default=1.0, alias="CRAWLER_RATE_LIMIT")
    crawler_timeout: int = Field(default=30, alias="CRAWLER_TIMEOUT")
    crawler_max_retries: int = Field(default=3, alias="CRAWLER_MAX_RETRIES")

    # MinIO (local S3-compatible storage)
    minio_endpoint: str = Field(default="localhost:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", alias="MINIO_SECRET_KEY")
    minio_bucket: str = Field(default="find-doctor", alias="MINIO_BUCKET")

    # GCP
    gcp_project_id: str = Field(default="", alias="GCP_PROJECT_ID")
    gcp_region: str = Field(default="asia-northeast3", alias="GCP_REGION")

    # BigQuery
    bigquery_dataset: str = Field(default="find-doctor", alias="BIGQUERY_DATASET")

    # Cloud Storage
    gcs_bucket: str = Field(default="find-doctor-data", alias="GCS_BUCKET")
    gcs_raw_prefix: str = Field(default="raw/", alias="GCS_RAW_PREFIX")

    # Firestore
    firestore_collection: str = Field(default="find-doctor", alias="FIRESTORE_COLLECTION")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_collector_settings() -> CollectorSettings:
    """Get cached collector settings instance."""
    return CollectorSettings()
