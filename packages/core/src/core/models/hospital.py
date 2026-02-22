"""Hospital data model."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Hospital:
    """Immutable hospital data model.

    Attributes:
        id: Unique identifier for the hospital
        name: Hospital name
        address: Full address of the hospital
        phone: Contact phone number
        website: Official website URL
        departments: List of departments
        type: Hospital type (university, general, specialized, clinic)
        region: Region/city where the hospital is located
        collected_at: Timestamp when the data was collected
    """

    id: str
    name: str
    address: str
    phone: str | None = None
    website: str = ""
    departments: tuple[str, ...] = field(default_factory=tuple)
    type: str = ""
    region: str = ""
    collected_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "phone": self.phone,
            "website": self.website,
            "departments": list(self.departments),
            "type": self.type,
            "region": self.region,
            "collected_at": self.collected_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Hospital":
        """Create Hospital instance from dictionary."""
        collected_at = data.get("collected_at")
        if isinstance(collected_at, str):
            collected_at = datetime.fromisoformat(collected_at)
        elif collected_at is None:
            collected_at = datetime.now()

        return cls(
            id=data["id"],
            name=data["name"],
            address=data["address"],
            phone=data.get("phone"),
            website=data.get("website", ""),
            departments=tuple(data.get("departments", [])),
            type=data.get("type", ""),
            region=data.get("region", ""),
            collected_at=collected_at,
        )
