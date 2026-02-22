"""Pydantic schemas for client API."""

from client_api.schemas.doctor import DoctorResponse, DoctorListResponse
from client_api.schemas.hospital import HospitalResponse, HospitalListResponse
from client_api.schemas.search import SearchResponse, SearchResult

__all__ = [
    "DoctorResponse",
    "DoctorListResponse",
    "HospitalResponse",
    "HospitalListResponse",
    "SearchResponse",
    "SearchResult",
]
