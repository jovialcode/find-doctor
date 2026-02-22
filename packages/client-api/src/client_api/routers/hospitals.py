"""Hospitals query router."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from client_api.schemas.hospital import HospitalResponse, HospitalListResponse

router = APIRouter()

# In-memory storage for demo (replace with database)
_hospitals: dict[str, dict[str, Any]] = {}


@router.get("/", response_model=HospitalListResponse)
async def list_hospitals(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    type: str | None = Query(None, description="Filter by hospital type"),
    region: str | None = Query(None, description="Filter by region"),
    department: str | None = Query(None, description="Filter by department availability"),
) -> dict[str, Any]:
    """List hospitals with optional filters.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        type: Filter by hospital type (university, general, etc.)
        region: Filter by region/city
        department: Filter by department availability

    Returns:
        List of hospitals with pagination info
    """
    hospitals = list(_hospitals.values())

    # Apply filters
    if type:
        hospitals = [h for h in hospitals if h.get("type") == type]

    if region:
        hospitals = [h for h in hospitals if h.get("region") == region]

    if department:
        hospitals = [
            h for h in hospitals
            if department in h.get("departments", [])
        ]

    total = len(hospitals)
    hospitals = hospitals[skip : skip + limit]

    return {
        "items": hospitals,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{hospital_id}", response_model=HospitalResponse)
async def get_hospital(hospital_id: str) -> dict[str, Any]:
    """Get a hospital by ID.

    Args:
        hospital_id: Hospital identifier

    Returns:
        Hospital data

    Raises:
        HTTPException: If hospital not found
    """
    if hospital_id not in _hospitals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital '{hospital_id}' not found",
        )

    return _hospitals[hospital_id]


@router.get("/region/{region}", response_model=HospitalListResponse)
async def get_hospitals_by_region(
    region: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    type: str | None = None,
) -> dict[str, Any]:
    """Get all hospitals in a region.

    Args:
        region: Region/city name
        skip: Number of records to skip
        limit: Maximum records to return
        type: Optional hospital type filter

    Returns:
        List of hospitals in the region
    """
    hospitals = [h for h in _hospitals.values() if h.get("region") == region]

    if type:
        hospitals = [h for h in hospitals if h.get("type") == type]

    total = len(hospitals)
    hospitals = hospitals[skip : skip + limit]

    return {
        "items": hospitals,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{hospital_id}/departments")
async def get_hospital_departments(hospital_id: str) -> list[str]:
    """Get departments at a hospital.

    Args:
        hospital_id: Hospital identifier

    Returns:
        List of department names

    Raises:
        HTTPException: If hospital not found
    """
    if hospital_id not in _hospitals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital '{hospital_id}' not found",
        )

    return _hospitals[hospital_id].get("departments", [])
