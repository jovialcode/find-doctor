"""Doctors query router."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from client_api.schemas.doctor import DoctorResponse, DoctorListResponse

router = APIRouter()

# In-memory storage for demo (replace with database)
_doctors: dict[str, dict[str, Any]] = {}


@router.get("/", response_model=DoctorListResponse)
async def list_doctors(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    hospital_id: str | None = Query(None, description="Filter by hospital"),
    department: str | None = Query(None, description="Filter by department"),
    specialty: str | None = Query(None, description="Filter by specialty"),
    region: str | None = Query(None, description="Filter by region"),
    is_accepting_new: bool | None = Query(None, description="Filter by accepting new patients"),
) -> dict[str, Any]:
    """List doctors with optional filters.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        hospital_id: Filter by hospital ID
        department: Filter by department
        specialty: Filter by specialty
        region: Filter by region
        is_accepting_new: Filter by accepting new patients

    Returns:
        List of doctors with pagination info
    """
    doctors = list(_doctors.values())

    # Apply filters
    if hospital_id:
        doctors = [d for d in doctors if d.get("hospital_id") == hospital_id]

    if department:
        doctors = [d for d in doctors if d.get("department") == department]

    if specialty:
        doctors = [
            d for d in doctors
            if specialty.lower() in [s.lower() for s in d.get("specialty", [])]
        ]

    if is_accepting_new is not None:
        doctors = [d for d in doctors if d.get("is_accepting_new") == is_accepting_new]

    total = len(doctors)
    doctors = doctors[skip : skip + limit]

    return {
        "items": doctors,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{doctor_id}", response_model=DoctorResponse)
async def get_doctor(doctor_id: str) -> dict[str, Any]:
    """Get a doctor by ID.

    Args:
        doctor_id: Doctor identifier

    Returns:
        Doctor data

    Raises:
        HTTPException: If doctor not found
    """
    if doctor_id not in _doctors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor '{doctor_id}' not found",
        )

    return _doctors[doctor_id]


@router.get("/hospital/{hospital_id}", response_model=DoctorListResponse)
async def get_doctors_by_hospital(
    hospital_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    department: str | None = None,
) -> dict[str, Any]:
    """Get all doctors at a hospital.

    Args:
        hospital_id: Hospital identifier
        skip: Number of records to skip
        limit: Maximum records to return
        department: Optional department filter

    Returns:
        List of doctors at the hospital
    """
    doctors = [d for d in _doctors.values() if d.get("hospital_id") == hospital_id]

    if department:
        doctors = [d for d in doctors if d.get("department") == department]

    total = len(doctors)
    doctors = doctors[skip : skip + limit]

    return {
        "items": doctors,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/department/{department}", response_model=DoctorListResponse)
async def get_doctors_by_department(
    department: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """Get all doctors in a department.

    Args:
        department: Department name
        skip: Number of records to skip
        limit: Maximum records to return

    Returns:
        List of doctors in the department
    """
    doctors = [d for d in _doctors.values() if d.get("department") == department]

    total = len(doctors)
    doctors = doctors[skip : skip + limit]

    return {
        "items": doctors,
        "total": total,
        "skip": skip,
        "limit": limit,
    }
