"""Search router for full-text search."""

from typing import Any, Literal

from fastapi import APIRouter, Query

from client_api.schemas.search import SearchResponse, SearchResult

router = APIRouter()

# In-memory storage for demo (replace with database)
_doctors: dict[str, dict[str, Any]] = {}
_hospitals: dict[str, dict[str, Any]] = {}


def _search_doctors(query: str) -> list[dict[str, Any]]:
    """Search doctors by name or specialty.

    Args:
        query: Search query

    Returns:
        Matching doctors
    """
    query_lower = query.lower()
    results: list[dict[str, Any]] = []

    for doctor in _doctors.values():
        score = 0.0

        # Check name
        name = doctor.get("name", "").lower()
        if query_lower in name:
            score += 2.0 if name.startswith(query_lower) else 1.0

        # Check specialty
        for specialty in doctor.get("specialty", []):
            if query_lower in specialty.lower():
                score += 1.5

        # Check department
        if query_lower in doctor.get("department", "").lower():
            score += 1.0

        if score > 0:
            results.append({
                "type": "doctor",
                "id": doctor["id"],
                "name": doctor.get("name"),
                "description": f"{doctor.get('department', '')} - {', '.join(doctor.get('specialty', []))}",
                "score": score,
                "data": doctor,
            })

    return results


def _search_hospitals(query: str) -> list[dict[str, Any]]:
    """Search hospitals by name or region.

    Args:
        query: Search query

    Returns:
        Matching hospitals
    """
    query_lower = query.lower()
    results: list[dict[str, Any]] = []

    for hospital in _hospitals.values():
        score = 0.0

        # Check name
        name = hospital.get("name", "").lower()
        if query_lower in name:
            score += 2.0 if name.startswith(query_lower) else 1.0

        # Check region
        if query_lower in hospital.get("region", "").lower():
            score += 1.0

        # Check departments
        for dept in hospital.get("departments", []):
            if query_lower in dept.lower():
                score += 0.5

        if score > 0:
            results.append({
                "type": "hospital",
                "id": hospital["id"],
                "name": hospital.get("name"),
                "description": f"{hospital.get('region', '')} - {hospital.get('type', '')}",
                "score": score,
                "data": hospital,
            })

    return results


@router.get("/", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    type: Literal["all", "doctor", "hospital"] = Query(
        "all", description="Type of results to return"
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
) -> dict[str, Any]:
    """Search for doctors and hospitals.

    Args:
        q: Search query
        type: Type of results (all, doctor, hospital)
        skip: Number of records to skip
        limit: Maximum records to return

    Returns:
        Search results with relevance scores
    """
    results: list[dict[str, Any]] = []

    if type in ("all", "doctor"):
        results.extend(_search_doctors(q))

    if type in ("all", "hospital"):
        results.extend(_search_hospitals(q))

    # Sort by score descending
    results.sort(key=lambda x: x.get("score", 0), reverse=True)

    total = len(results)
    results = results[skip : skip + limit]

    return {
        "query": q,
        "items": results,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/suggest")
async def suggest(
    q: str = Query(..., min_length=1, description="Search prefix"),
    limit: int = Query(10, ge=1, le=50, description="Maximum suggestions"),
) -> list[str]:
    """Get search suggestions based on prefix.

    Args:
        q: Search prefix
        limit: Maximum number of suggestions

    Returns:
        List of suggested search terms
    """
    query_lower = q.lower()
    suggestions: set[str] = set()

    # Collect doctor names
    for doctor in _doctors.values():
        name = doctor.get("name", "")
        if name.lower().startswith(query_lower):
            suggestions.add(name)

        for specialty in doctor.get("specialty", []):
            if specialty.lower().startswith(query_lower):
                suggestions.add(specialty)

    # Collect hospital names
    for hospital in _hospitals.values():
        name = hospital.get("name", "")
        if name.lower().startswith(query_lower):
            suggestions.add(name)

    return sorted(suggestions)[:limit]
