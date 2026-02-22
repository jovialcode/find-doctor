"""Hospital schemas."""

from pydantic import BaseModel


class HospitalResponse(BaseModel):
    """Schema for hospital response."""

    id: str
    name: str
    address: str
    phone: str | None = None
    website: str = ""
    departments: list[str] = []
    type: str = ""
    region: str = ""
    collected_at: str | None = None

    model_config = {"from_attributes": True}


class HospitalListResponse(BaseModel):
    """Schema for hospital list response."""

    items: list[HospitalResponse]
    total: int
    skip: int
    limit: int
