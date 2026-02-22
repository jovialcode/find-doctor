"""Site schemas."""

from pydantic import BaseModel, Field


class SiteCreate(BaseModel):
    """Schema for creating a site."""

    id: str = Field(..., min_length=1, description="Unique site identifier")
    name: str = Field(..., min_length=1, description="Site display name")
    base_url: str = Field(..., description="Base URL of the site")
    type: str = Field(default="", description="Site type (university, general, etc.)")
    region: str = Field(default="", description="Region/city")
    enabled: bool = Field(default=True, description="Whether site is enabled for crawling")


class SiteUpdate(BaseModel):
    """Schema for updating a site."""

    name: str | None = Field(None, min_length=1, description="Site display name")
    base_url: str | None = Field(None, description="Base URL of the site")
    type: str | None = Field(None, description="Site type")
    region: str | None = Field(None, description="Region/city")
    enabled: bool | None = Field(None, description="Whether site is enabled")


class SiteResponse(BaseModel):
    """Schema for site response."""

    id: str
    name: str
    base_url: str
    type: str = ""
    region: str = ""
    enabled: bool = True

    model_config = {"from_attributes": True}
