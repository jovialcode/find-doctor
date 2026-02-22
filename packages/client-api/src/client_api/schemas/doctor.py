"""Doctor schemas."""

from pydantic import BaseModel


class ConsultationHoursSchema(BaseModel):
    """Schema for consultation hours."""

    day: str
    start_time: str
    end_time: str
    note: str | None = None


class DoctorResponse(BaseModel):
    """Schema for doctor response."""

    id: str
    name: str
    hospital_id: str
    department: str
    specialty: list[str] = []
    photo_url: str | None = None
    education: list[str] = []
    career: list[str] = []
    certifications: list[str] = []
    publications: list[str] = []
    awards: list[str] = []
    consultation_hours: list[ConsultationHoursSchema] = []
    is_accepting_new: bool = True
    booking_url: str | None = None
    phone: str | None = None
    source_url: str = ""
    collected_at: str | None = None

    model_config = {"from_attributes": True}


class DoctorListResponse(BaseModel):
    """Schema for doctor list response."""

    items: list[DoctorResponse]
    total: int
    skip: int
    limit: int
