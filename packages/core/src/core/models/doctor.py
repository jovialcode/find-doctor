"""Doctor data model."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class ConsultationHours:
    """Doctor consultation hours."""

    day: str
    start_time: str
    end_time: str
    note: str | None = None


@dataclass(frozen=True)
class Doctor:
    """Immutable doctor data model.

    Attributes:
        id: Unique identifier for the doctor
        name: Doctor's name
        hospital_id: ID of the hospital where the doctor works
        department: Department name
        specialty: List of specialties
        photo_url: URL to the doctor's photo
        education: List of educational background
        career: List of career history
        certifications: List of certifications and licenses
        publications: List of publications
        awards: List of awards
        consultation_hours: Dictionary of consultation hours by day
        is_accepting_new: Whether the doctor is accepting new patients
        booking_url: URL for booking appointments
        phone: Contact phone number
        source_url: URL where the data was collected from
        collected_at: Timestamp when the data was collected
    """

    id: str
    name: str
    hospital_id: str
    department: str
    specialty: tuple[str, ...] = field(default_factory=tuple)
    photo_url: str | None = None

    # Detail information
    education: tuple[str, ...] = field(default_factory=tuple)
    career: tuple[str, ...] = field(default_factory=tuple)
    certifications: tuple[str, ...] = field(default_factory=tuple)
    publications: tuple[str, ...] = field(default_factory=tuple)
    awards: tuple[str, ...] = field(default_factory=tuple)

    # Booking information
    consultation_hours: tuple[ConsultationHours, ...] = field(default_factory=tuple)
    is_accepting_new: bool = True
    booking_url: str | None = None
    phone: str | None = None

    # Metadata
    source_url: str = ""
    collected_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "hospital_id": self.hospital_id,
            "department": self.department,
            "specialty": list(self.specialty),
            "photo_url": self.photo_url,
            "education": list(self.education),
            "career": list(self.career),
            "certifications": list(self.certifications),
            "publications": list(self.publications),
            "awards": list(self.awards),
            "consultation_hours": [
                {
                    "day": ch.day,
                    "start_time": ch.start_time,
                    "end_time": ch.end_time,
                    "note": ch.note,
                }
                for ch in self.consultation_hours
            ],
            "is_accepting_new": self.is_accepting_new,
            "booking_url": self.booking_url,
            "phone": self.phone,
            "source_url": self.source_url,
            "collected_at": self.collected_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Doctor":
        """Create Doctor instance from dictionary."""
        consultation_hours = tuple(
            ConsultationHours(
                day=ch["day"],
                start_time=ch["start_time"],
                end_time=ch["end_time"],
                note=ch.get("note"),
            )
            for ch in data.get("consultation_hours", [])
        )

        collected_at = data.get("collected_at")
        if isinstance(collected_at, str):
            collected_at = datetime.fromisoformat(collected_at)
        elif collected_at is None:
            collected_at = datetime.now()

        return cls(
            id=data["id"],
            name=data["name"],
            hospital_id=data["hospital_id"],
            department=data["department"],
            specialty=tuple(data.get("specialty", [])),
            photo_url=data.get("photo_url"),
            education=tuple(data.get("education", [])),
            career=tuple(data.get("career", [])),
            certifications=tuple(data.get("certifications", [])),
            publications=tuple(data.get("publications", [])),
            awards=tuple(data.get("awards", [])),
            consultation_hours=consultation_hours,
            is_accepting_new=data.get("is_accepting_new", True),
            booking_url=data.get("booking_url"),
            phone=data.get("phone"),
            source_url=data.get("source_url", ""),
            collected_at=collected_at,
        )
