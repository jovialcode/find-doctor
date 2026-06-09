"""Application settings using Pydantic."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Shared settings for core infrastructure."""

    # Environment
    env: str = Field(default="development", alias="ENV")
    debug: bool = Field(default=False, alias="DEBUG")

    # Database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/find-doctor",
        alias="DATABASE_URL",
    )

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
