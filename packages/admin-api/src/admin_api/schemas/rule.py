"""Rule schemas."""

from pydantic import BaseModel


class RuleResponse(BaseModel):
    """Schema for rule list response."""

    id: str
    name: str
    base_url: str
    enabled: bool = True
    file_path: str
    targets_count: int = 0


class RuleValidationResponse(BaseModel):
    """Schema for rule validation response."""

    valid: bool
    errors: list[str] = []
