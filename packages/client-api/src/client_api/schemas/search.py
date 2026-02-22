"""Search schemas."""

from typing import Any, Literal

from pydantic import BaseModel


class SearchResult(BaseModel):
    """Schema for a single search result."""

    type: Literal["doctor", "hospital"]
    id: str
    name: str
    description: str
    score: float
    data: dict[str, Any]


class SearchResponse(BaseModel):
    """Schema for search response."""

    query: str
    items: list[SearchResult]
    total: int
    skip: int
    limit: int
