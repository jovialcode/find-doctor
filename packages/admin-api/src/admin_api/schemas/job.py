"""Job schemas."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobCreate(BaseModel):
    """Schema for creating a job."""

    site_id: str = Field(..., description="Site identifier to crawl")
    target_name: str | None = Field(None, description="Specific target to crawl")


class JobResponse(BaseModel):
    """Schema for job response."""

    id: str
    site_id: str
    target_name: str | None = None
    status: JobStatus
    created_at: str
    updated_at: str
    started_at: str | None = None
    completed_at: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None

    model_config = {"from_attributes": True}
