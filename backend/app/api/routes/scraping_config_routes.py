"""
Admin API routes for Scraping Configuration & Compliance Management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid

from app.tier_1.infrastructure.database import get_db
from app.tier_1.data_extraction.scraping_config_service import scraping_config_service

router = APIRouter()


# Pydantic schemas for request/response
class ScrapingConfigCreate(BaseModel):
    """Request model for creating scraping config"""
    domain: str = Field(..., description="Domain name (e.g., example.com)")
    allow_scraping: bool = Field(default=False, description="Whether scraping is allowed")
    robots_txt_compliant: bool = Field(default=True, description="Enforce robots.txt")
    rate_limit_requests_per_minute: int = Field(default=10, description="Max requests per minute")
    rate_limit_delay_seconds: float = Field(default=2.0, description="Delay between requests")
    use_api: bool = Field(default=False, description="Use official API instead")
    api_endpoint: Optional[str] = Field(None, description="API base URL")
    api_key: Optional[str] = Field(None, description="API key (will be encrypted)")
    preferred_method: str = Field(default='auto', description="Preferred scraping method")
    notes: Optional[str] = Field(None, description="Additional notes")


class ScrapingConfigUpdate(BaseModel):
    """Request model for updating scraping config"""
    allow_scraping: Optional[bool] = None
    robots_txt_compliant: Optional[bool] = None
    rate_limit_requests_per_minute: Optional[int] = None
    rate_limit_delay_seconds: Optional[float] = None
    use_api: Optional[bool] = None
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    preferred_method: Optional[str] = None
    status: Optional[str] = None
    block_reason: Optional[str] = None
    notes: Optional[str] = None


class ScrapingConfigResponse(BaseModel):
    """Response model for scraping config"""
    id: str
    domain: str
    allow_scraping: bool
    robots_txt_compliant: bool
    rate_limit_requests_per_minute: int
    rate_limit_delay_seconds: float
    use_api: bool
    api_endpoint: Optional[str]
    preferred_method: str
    status: str
    notes: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


class CheckScrapingAllowedResponse(BaseModel):
    """Response model for checking if scraping is allowed"""
    allowed: bool
    reason: Optional[str] = None
    status: str
    alternative: Optional[str] = None
    rate_limit: Optional[dict] = None
    preferred_method: Optional[str] = None


class DomainStatsResponse(BaseModel):
    """Response model for domain statistics"""
    domain: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    blocked_requests: int
    total_bytes_downloaded: int
    avg_response_time_ms: Optional[float]
    rate_limit_violations: int
    robots_txt_violations: int
    first_scraped_at: Optional[str]
    last_scraped_at: Optional[str]


# ========== CRUD Endpoints ==========

@router.post(
    "/scraping-configs",
    response_model=ScrapingConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create scraping configuration",
    description="Create a new scraping configuration for a domain"
)
async def create_scraping_config(
    config: ScrapingConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new scraping configuration for a domain.

    This endpoint allows administrators to configure scraping policies including:
    - Whether scraping is allowed
    - Robots.txt compliance
    - Rate limiting settings
    - API integration details
    - Preferred scraping methods
    """
    try:
        result = await scraping_config_service.create_config(
            db=db,
            domain=config.domain,
            allow_scraping=config.allow_scraping,
            robots_txt_compliant=config.robots_txt_compliant,
            rate_limit_requests_per_minute=config.rate_limit_requests_per_minute,
            rate_limit_delay_seconds=config.rate_limit_delay_seconds,
            use_api=config.use_api,
            api_endpoint=config.api_endpoint,
            api_key=config.api_key,
            preferred_method=config.preferred_method,
            notes=config.notes
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating scraping config: {str(e)}"
        )


@router.get(
    "/scraping-configs/{domain}",
    response_model=ScrapingConfigResponse,
    summary="Get scraping configuration",
    description="Get scraping configuration for a specific domain"
)
async def get_scraping_config(
    domain: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve scraping configuration for a specific domain.
    """
    config = await scraping_config_service.get_config(db, domain)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No scraping configuration found for domain: {domain}"
        )

    return config


@router.get(
    "/scraping-configs",
    response_model=List[ScrapingConfigResponse],
    summary="List scraping configurations",
    description="List all scraping configurations with optional filters"
)
async def list_scraping_configs(
    status: Optional[str] = None,
    allow_scraping: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    List all scraping configurations with optional filters.

    Query parameters:
    - status: Filter by status (active, blocked, suspended, deprecated)
    - allow_scraping: Filter by whether scraping is allowed
    - limit: Maximum number of results (default: 100)
    - offset: Offset for pagination (default: 0)
    """
    configs = await scraping_config_service.list_configs(
        db=db,
        status=status,
        allow_scraping=allow_scraping,
        limit=limit,
        offset=offset
    )
    return configs


@router.put(
    "/scraping-configs/{domain}",
    response_model=ScrapingConfigResponse,
    summary="Update scraping configuration",
    description="Update scraping configuration for a domain"
)
async def update_scraping_config(
    domain: str,
    config: ScrapingConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update scraping configuration for a domain.

    Only provided fields will be updated. Omitted fields remain unchanged.
    """
    # Convert Pydantic model to dict, excluding unset fields
    update_data = config.dict(exclude_unset=True)

    result = await scraping_config_service.update_config(
        db=db,
        domain=domain,
        **update_data
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No scraping configuration found for domain: {domain}"
        )

    return result


@router.delete(
    "/scraping-configs/{domain}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete scraping configuration",
    description="Delete scraping configuration for a domain"
)
async def delete_scraping_config(
    domain: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete scraping configuration for a domain.
    """
    success = await scraping_config_service.delete_config(db, domain)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No scraping configuration found for domain: {domain}"
        )

    return None


# ========== Compliance Checking ==========

@router.get(
    "/scraping-configs/check-url",
    response_model=CheckScrapingAllowedResponse,
    summary="Check if scraping is allowed for URL",
    description="Check if scraping is allowed for a given URL based on configuration"
)
async def check_scraping_allowed(
    url: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Check if scraping is allowed for a given URL.

    This endpoint checks:
    - Whether a configuration exists for the domain
    - If scraping is explicitly allowed/blocked
    - Robots.txt compliance (if enabled)
    - Whether an API should be used instead
    - Rate limiting settings

    Returns detailed compliance information and recommendations.
    """
    result = await scraping_config_service.check_scraping_allowed(db, url)
    return result


# ========== Statistics & Audit Logs ==========

@router.get(
    "/domain-statistics/{domain}",
    response_model=DomainStatsResponse,
    summary="Get domain statistics",
    description="Get aggregate scraping statistics for a domain"
)
async def get_domain_statistics(
    domain: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get aggregate scraping statistics for a domain.

    Includes:
    - Total requests, successful/failed counts
    - Bytes downloaded
    - Average response time
    - Rate limit and robots.txt violations
    - First and last scrape timestamps
    """
    stats = await scraping_config_service.get_domain_stats(db, domain)

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No statistics found for domain: {domain}"
        )

    return stats


@router.get(
    "/scraping-audit-logs",
    summary="Get scraping audit logs",
    description="Get scraping audit logs with optional filters"
)
async def get_scraping_audit_logs(
    domain: Optional[str] = None,
    success: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Get scraping audit logs with optional filters.

    Query parameters:
    - domain: Filter by domain
    - success: Filter by success/failure
    - limit: Maximum number of results (default: 100)
    - offset: Offset for pagination (default: 0)
    """
    logs = await scraping_config_service.get_audit_logs(
        db=db,
        domain=domain,
        success=success,
        limit=limit,
        offset=offset
    )
    return {"logs": logs, "count": len(logs)}
