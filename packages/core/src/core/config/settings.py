"""Application settings using Pydantic."""

import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment
    env: str = Field(default="development", alias="ENV")
    debug: bool = Field(default=False, alias="DEBUG")

    # GCP Settings
    gcp_project_id: str = Field(default="", alias="GCP_PROJECT_ID")
    gcp_region: str = Field(default="asia-northeast3", alias="GCP_REGION")

    # BigQuery
    bigquery_dataset: str = Field(default="gungil", alias="BIGQUERY_DATASET")

    # Cloud Storage
    gcs_bucket: str = Field(default="gungil-data", alias="GCS_BUCKET")
    gcs_raw_prefix: str = Field(default="raw/", alias="GCS_RAW_PREFIX")

    # Firestore
    firestore_collection: str = Field(default="gungil", alias="FIRESTORE_COLLECTION")

    # Database (for local development)
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/gungil",
        alias="DATABASE_URL",
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # MinIO (local S3-compatible storage)
    minio_endpoint: str = Field(default="localhost:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", alias="MINIO_SECRET_KEY")
    minio_bucket: str = Field(default="gungil", alias="MINIO_BUCKET")

    # Crawler settings
    crawler_rate_limit: float = Field(default=1.0, alias="CRAWLER_RATE_LIMIT")
    crawler_timeout: int = Field(default=30, alias="CRAWLER_TIMEOUT")
    crawler_max_retries: int = Field(default=3, alias="CRAWLER_MAX_RETRIES")

    # Celery settings
    celery_broker_url: str = Field(default="redis://localhost:6379/0", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="", alias="CELERY_RESULT_BACKEND")
    worker_concurrency: int = Field(default=4, alias="WORKER_CONCURRENCY")

    # AI Agent settings
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.env == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
