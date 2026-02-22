"""Sites management router."""

from typing import Any

from fastapi import APIRouter, HTTPException, status

from admin_api.schemas.site import SiteCreate, SiteResponse, SiteUpdate

router = APIRouter()

# In-memory storage for demo (replace with database)
_sites: dict[str, dict[str, Any]] = {}


@router.get("/", response_model=list[SiteResponse])
async def list_sites(
    skip: int = 0,
    limit: int = 100,
    enabled: bool | None = None,
) -> list[dict[str, Any]]:
    """List all registered sites.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        enabled: Filter by enabled status

    Returns:
        List of sites
    """
    sites = list(_sites.values())

    if enabled is not None:
        sites = [s for s in sites if s.get("enabled") == enabled]

    return sites[skip : skip + limit]


@router.get("/{site_id}", response_model=SiteResponse)
async def get_site(site_id: str) -> dict[str, Any]:
    """Get a site by ID.

    Args:
        site_id: Site identifier

    Returns:
        Site data

    Raises:
        HTTPException: If site not found
    """
    if site_id not in _sites:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site '{site_id}' not found",
        )

    return _sites[site_id]


@router.post("/", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
async def create_site(site: SiteCreate) -> dict[str, Any]:
    """Create a new site.

    Args:
        site: Site data

    Returns:
        Created site

    Raises:
        HTTPException: If site ID already exists
    """
    if site.id in _sites:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Site '{site.id}' already exists",
        )

    site_data = site.model_dump()
    _sites[site.id] = site_data

    return site_data


@router.put("/{site_id}", response_model=SiteResponse)
async def update_site(site_id: str, site: SiteUpdate) -> dict[str, Any]:
    """Update a site.

    Args:
        site_id: Site identifier
        site: Updated site data

    Returns:
        Updated site

    Raises:
        HTTPException: If site not found
    """
    if site_id not in _sites:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site '{site_id}' not found",
        )

    existing = _sites[site_id]
    update_data = site.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        existing[key] = value

    return existing


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_site(site_id: str) -> None:
    """Delete a site.

    Args:
        site_id: Site identifier

    Raises:
        HTTPException: If site not found
    """
    if site_id not in _sites:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site '{site_id}' not found",
        )

    del _sites[site_id]


@router.post("/{site_id}/enable", response_model=SiteResponse)
async def enable_site(site_id: str) -> dict[str, Any]:
    """Enable a site for crawling.

    Args:
        site_id: Site identifier

    Returns:
        Updated site

    Raises:
        HTTPException: If site not found
    """
    if site_id not in _sites:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site '{site_id}' not found",
        )

    _sites[site_id]["enabled"] = True
    return _sites[site_id]


@router.post("/{site_id}/disable", response_model=SiteResponse)
async def disable_site(site_id: str) -> dict[str, Any]:
    """Disable a site from crawling.

    Args:
        site_id: Site identifier

    Returns:
        Updated site

    Raises:
        HTTPException: If site not found
    """
    if site_id not in _sites:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site '{site_id}' not found",
        )

    _sites[site_id]["enabled"] = False
    return _sites[site_id]
