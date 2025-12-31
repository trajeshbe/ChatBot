"""
Enhanced Web Scraper API Routes

Provides comprehensive web scraping capabilities with multiple strategies
and configuration options.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.security import get_current_user_from_request
from app.tier_1.data_extraction.scraper_service import scraper_service
from app.tier_1.data_extraction.scraper_strategies import ScraperConfig, ScraperStrategy
from app.schemas.scraper_schemas import (
    ScrapeRequest,
    ScrapeResponse,
    BulkScrapeRequest,
    BulkScrapeResponse,
    ScraperCapabilitiesResponse,
    ScraperConfigRequest,
    WebScrapeJobStatus
)
from app.tier_1.infrastructure.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/scraper", tags=["Web Scraper"])


@router.get("/capabilities", response_model=ScraperCapabilitiesResponse)
async def get_scraper_capabilities():
    """
    Get information about available scraper capabilities.

    Returns details about enabled features, available strategies,
    and default configuration.
    """
    try:
        capabilities = await scraper_service.get_scraper_capabilities()
        return ScraperCapabilitiesResponse(**capabilities)
    except Exception as e:
        logger.error(f"Error getting scraper capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_url(
    scrape_request: ScrapeRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Scrape a single URL with customizable options.

    Supports multiple scraping strategies, custom configuration,
    AI-powered content filtering, and project-based organization.

    Example:
    ```json
    {
        "url": "https://example.com/article",
        "scrape_prompt": "Extract information about AI",
        "strategy": "auto",
        "config": {
            "include_tables": true,
            "enable_javascript": false
        },
        "session_id": "session_123",
        "project_id": "uuid-here",
        "department": "Engineering",
        "team": "AI-Team"
    }
    ```
    """
    try:
        # Check if scraping is enabled
        if not settings.ENABLE_WEB_SCRAPING:
            raise HTTPException(
                status_code=403,
                detail="Web scraping is disabled. Contact administrator to enable."
            )

        # Get current user (optional - returns None if not authenticated)
        current_user = await get_current_user_from_request(http_request, db)
        user_id = str(current_user.id) if current_user else None

        # Extract organizational context from request or user
        project_id = scrape_request.project_id
        department = scrape_request.department
        team = scrape_request.team

        # Validate project_id exists if provided
        if project_id:
            from sqlalchemy import select
            from app.models.database_enhanced import Project
            project_result = await db.execute(
                select(Project).where(Project.id == project_id)
            )
            project = project_result.scalar_one_or_none()
            if not project:
                logger.warning(f"⚠️ Project {project_id} not found, setting to None")
                project_id = None

        # If user is authenticated but dept/team not provided, get from user
        if current_user and not department:
            from app.models.rbac import Department, Team
            from app.models.database_enhanced import UserTeam
            from sqlalchemy import select

            # Get department name
            if current_user.department_id:
                dept_result = await db.execute(
                    select(Department).where(Department.id == current_user.department_id)
                )
                dept = dept_result.scalar_one_or_none()
                if dept:
                    department = dept.name
                    logger.info(f"📁 Department: {department}")

            # Get primary team (matching upload logic)
            teams_query = select(UserTeam, Team).join(
                Team, UserTeam.team_id == Team.id
            ).where(
                UserTeam.user_id == current_user.id,
                UserTeam.is_primary == True
            ).limit(1)
            teams_result = await db.execute(teams_query)
            user_team_data = teams_result.first()
            if user_team_data:
                team = user_team_data[1].name  # Team.name
                logger.info(f"👥 Team: {team}")

        # Get username for MinIO path
        username = current_user.username if current_user else "anonymous"

        logger.info(f"🔍 Scraping with context - User: {username}/{user_id}, Project: {project_id}, Dept: {department}, Team: {team}")

        # ============================================================
        # SCRAPING COMPLIANCE CHECK - Check configured policies
        # ============================================================
        from app.tier_1.data_extraction.scraping_config_service import scraping_config_service

        compliance_check = await scraping_config_service.check_scraping_allowed(db, str(scrape_request.url))

        # If scraping is not allowed, block the request
        if not compliance_check.get('allowed', False):
            error_msg = compliance_check.get('reason', 'Scraping not allowed for this domain')
            alternative = compliance_check.get('alternative') or compliance_check.get('recommendation')

            if alternative:
                error_msg += f"\n\nAlternative: {alternative}"

            # Log the blocked attempt
            await scraping_config_service.log_scraping_attempt(
                db=db,
                url=str(scrape_request.url),
                method=scrape_request.strategy.value if scrape_request.strategy else 'auto',
                success=False,
                error_message=error_msg,
                robots_txt_allowed=compliance_check.get('status') != 'robots_blocked',
                session_id=scrape_request.session_id
            )

            logger.warning(f"🚫 Web scraping blocked by compliance: {error_msg}")

            return ScrapeResponse(
                success=False,
                url=str(scrape_request.url),
                error=error_msg
            )

        logger.info(f"✅ Compliance check passed for {scrape_request.url}")

        # Convert Pydantic config to ScraperConfig if provided
        scraper_config = None
        if scrape_request.config:
            scraper_config = ScraperConfig(
                strategy=ScraperStrategy(scrape_request.config.strategy) if scrape_request.config.strategy else ScraperStrategy.AUTO,
                timeout=scrape_request.config.timeout,
                max_retries=scrape_request.config.max_retries,
                follow_redirects=scrape_request.config.follow_redirects,
                user_agent=scrape_request.config.user_agent or settings.SCRAPER_USER_AGENT,
                include_links=scrape_request.config.include_links,
                include_tables=scrape_request.config.include_tables,
                include_images=scrape_request.config.include_images,
                include_metadata=scrape_request.config.include_metadata,
                remove_nav=scrape_request.config.remove_nav,
                remove_footer=scrape_request.config.remove_footer,
                remove_header=scrape_request.config.remove_header,
                remove_ads=scrape_request.config.remove_ads,
                enable_javascript=scrape_request.config.enable_javascript,
                wait_for_selector=scrape_request.config.wait_for_selector,
                wait_timeout=scrape_request.config.wait_timeout,
                min_content_length=scrape_request.config.min_content_length,
                max_content_length=scrape_request.config.max_content_length,
            )

        # Perform scraping with project context
        result = await scraper_service.scrape_url(
            url=str(scrape_request.url),
            scrape_prompt=scrape_request.scrape_prompt,
            strategy=scrape_request.strategy.value if scrape_request.strategy else None,
            config=scraper_config,
            session_id=scrape_request.session_id,
            project_id=project_id,
            department=department,
            team=team,
            user_id=user_id,
            username=username,  # Pass username for MinIO path
            db=db
        )

        return ScrapeResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scraping URL {scrape_request.url}: {e}")
        return ScrapeResponse(
            success=False,
            url=str(scrape_request.url),
            error=str(e)
        )


@router.post("/scrape/bulk", response_model=BulkScrapeResponse)
async def scrape_multiple_urls(
    scrape_request: BulkScrapeRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Scrape multiple URLs in a single request.

    Supports up to 50 URLs per request with automatic concurrency control,
    rate limiting, and project-based organization.

    Example:
    ```json
    {
        "urls": [
            "https://example.com/article1",
            "https://example.com/article2"
        ],
        "scrape_prompt": "Extract product information",
        "strategy": "hybrid",
        "session_id": "session_123",
        "project_id": "uuid-here",
        "department": "Engineering",
        "team": "AI-Team"
    }
    ```
    """
    try:
        # Check if scraping is enabled
        if not settings.ENABLE_WEB_SCRAPING:
            raise HTTPException(
                status_code=403,
                detail="Web scraping is disabled. Contact administrator to enable."
            )

        # Get current user (optional - returns None if not authenticated)
        current_user = await get_current_user_from_request(http_request, db)
        user_id = str(current_user.id) if current_user else None

        # Extract organizational context from request or user
        project_id = scrape_request.project_id
        department = scrape_request.department
        team = scrape_request.team

        # Validate project_id exists if provided
        if project_id:
            from sqlalchemy import select
            from app.models.database_enhanced import Project
            project_result = await db.execute(
                select(Project).where(Project.id == project_id)
            )
            project = project_result.scalar_one_or_none()
            if not project:
                logger.warning(f"⚠️ Project {project_id} not found, setting to None")
                project_id = None

        # If user is authenticated but dept/team not provided, get from user
        if current_user and not department:
            from app.models.database_enhanced import Department, Team
            from sqlalchemy import select

            # Get department name
            if current_user.department_id:
                dept_result = await db.execute(
                    select(Department).where(Department.id == current_user.department_id)
                )
                dept = dept_result.scalar_one_or_none()
                if dept:
                    department = dept.name

            # Get team name
            if current_user.team_id:
                team_result = await db.execute(
                    select(Team).where(Team.id == current_user.team_id)
                )
                team_obj = team_result.scalar_one_or_none()
                if team_obj:
                    team = team_obj.name

        logger.info(f"🔍 Bulk scraping with context - User: {user_id}, Project: {project_id}, Dept: {department}, Team: {team}")

        # ============================================================
        # SCRAPING COMPLIANCE CHECK - Check each URL for compliance
        # ============================================================
        from app.tier_1.data_extraction.scraping_config_service import scraping_config_service

        # Check compliance for all URLs before processing
        blocked_urls = []
        for url in scrape_request.urls:
            compliance_check = await scraping_config_service.check_scraping_allowed(db, str(url))

            if not compliance_check.get('allowed', False):
                error_msg = compliance_check.get('reason', 'Scraping not allowed for this domain')

                # Log the blocked attempt
                await scraping_config_service.log_scraping_attempt(
                    db=db,
                    url=str(url),
                    method=scrape_request.strategy.value if scrape_request.strategy else 'auto',
                    success=False,
                    error_message=error_msg,
                    robots_txt_allowed=compliance_check.get('status') != 'robots_blocked',
                    session_id=scrape_request.session_id
                )

                blocked_urls.append({
                    "url": str(url),
                    "reason": error_msg
                })

                logger.warning(f"🚫 Bulk scraping blocked URL: {url} - {error_msg}")

        # If any URLs are blocked, return error response with details
        if blocked_urls:
            # Create failed responses for blocked URLs
            failed_responses = [
                ScrapeResponse(
                    success=False,
                    url=item["url"],
                    error=item["reason"]
                )
                for item in blocked_urls
            ]

            # Filter out blocked URLs from processing
            allowed_urls = [str(url) for url in scrape_request.urls if not any(str(url) == item["url"] for item in blocked_urls)]

            # If ALL URLs are blocked, return all failed
            if not allowed_urls:
                return BulkScrapeResponse(
                    results=failed_responses,
                    total=len(blocked_urls),
                    successful=0,
                    failed=len(blocked_urls)
                )

            # Otherwise, update URLs to only include allowed ones
            logger.info(f"✅ {len(allowed_urls)} URLs passed compliance check, {len(blocked_urls)} blocked")
        else:
            allowed_urls = [str(url) for url in scrape_request.urls]
            failed_responses = []

        # Convert Pydantic config to ScraperConfig if provided
        scraper_config = None
        if scrape_request.config:
            scraper_config = ScraperConfig(
                strategy=ScraperStrategy(scrape_request.config.strategy) if scrape_request.config.strategy else ScraperStrategy.AUTO,
                timeout=scrape_request.config.timeout,
                max_retries=scrape_request.config.max_retries,
                follow_redirects=scrape_request.config.follow_redirects,
                user_agent=scrape_request.config.user_agent or settings.SCRAPER_USER_AGENT,
                include_links=scrape_request.config.include_links,
                include_tables=scrape_request.config.include_tables,
                include_images=scrape_request.config.include_images,
                include_metadata=scrape_request.config.include_metadata,
                remove_nav=scrape_request.config.remove_nav,
                remove_footer=scrape_request.config.remove_footer,
                remove_header=scrape_request.config.remove_header,
                remove_ads=scrape_request.config.remove_ads,
                enable_javascript=scrape_request.config.enable_javascript,
                wait_for_selector=scrape_request.config.wait_for_selector,
                wait_timeout=scrape_request.config.wait_timeout,
                min_content_length=scrape_request.config.min_content_length,
                max_content_length=scrape_request.config.max_content_length,
            )

        # Scrape only allowed URLs with project context
        if allowed_urls:
            results = await scraper_service.scrape_multiple_urls(
                urls=allowed_urls,
                scrape_prompt=scrape_request.scrape_prompt,
                strategy=scrape_request.strategy.value if scrape_request.strategy else None,
                config=scraper_config,
                session_id=scrape_request.session_id,
                project_id=project_id,
                department=department,
                team=team,
                user_id=user_id,
                db=db
            )

            # Convert to response models
            scrape_responses = [ScrapeResponse(**r) for r in results]

            # Combine with failed responses from blocked URLs
            all_responses = failed_responses + scrape_responses
        else:
            # All URLs were blocked
            all_responses = failed_responses

        # Calculate stats
        total = len(all_responses)
        successful = sum(1 for r in all_responses if r.success)
        failed = total - successful

        return BulkScrapeResponse(
            results=all_responses,
            total=total,
            successful=successful,
            failed=failed
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk scraping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=WebScrapeJobStatus)
async def get_scrape_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the status of a scrape job.

    Returns information about the job including its current status,
    associated document, and any errors.
    """
    try:
        from app.models.database import WebScrapeJob
        from sqlalchemy import select

        # Query job
        result = await db.execute(
            select(WebScrapeJob).where(WebScrapeJob.id == job_id)
        )
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Scrape job not found")

        return WebScrapeJobStatus(
            job_id=str(job.id),
            url=job.url,
            status=job.status,
            document_id=str(job.document_id) if job.document_id else None,
            error_message=job.error_message,
            created_at=job.created_at.isoformat() if job.created_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs", response_model=List[WebScrapeJobStatus])
async def list_scrape_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    db: AsyncSession = Depends(get_db)
):
    """
    List scrape jobs with optional filtering.

    Supports pagination and filtering by status (processing, completed, failed).
    """
    try:
        from app.models.database import WebScrapeJob
        from sqlalchemy import select, desc

        # Build query
        query = select(WebScrapeJob).order_by(desc(WebScrapeJob.created_at))

        if status:
            query = query.where(WebScrapeJob.status == status)

        query = query.limit(limit).offset(offset)

        # Execute query
        result = await db.execute(query)
        jobs = result.scalars().all()

        return [
            WebScrapeJobStatus(
                job_id=str(job.id),
                url=job.url,
                status=job.status,
                document_id=str(job.document_id) if job.document_id else None,
                error_message=job.error_message,
                created_at=job.created_at.isoformat() if job.created_at else None,
                completed_at=job.completed_at.isoformat() if job.completed_at else None
            )
            for job in jobs
        ]

    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
