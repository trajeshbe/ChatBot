"""
Enhanced Web Scraper API Routes

This module provides REST API endpoints for the enhanced web scraper with
compliance modes, LLM integration, and dynamic protocol adaptation.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from enum import Enum
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.tier_1.infrastructure.database import get_db
from app.models.database import WebScrapeJob, Document
from app.tier_1.data_extraction.webscraper.core.scraper_engine import (
    ScraperEngine,
    strict_scraper,
    balanced_scraper,
    aggressive_scraper
)
from app.tier_1.data_extraction.webscraper.compliance import ComplianceLevel, AuthType
from app.tier_1.document_processing.document_service import document_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/scraper", tags=["Enhanced Web Scraper"])


# Request/Response Models

class ComplianceLevelEnum(str, Enum):
    """Compliance levels for scraping"""
    STRICT = "strict"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class LLMProviderEnum(str, Enum):
    """LLM providers for smart scraping"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class AuthConfigRequest(BaseModel):
    """Authentication configuration"""
    auth_type: str = Field(..., description="Authentication type")
    credentials: Dict[str, Any] = Field(..., description="Authentication credentials")


class ScrapeRequest(BaseModel):
    """Request model for scraping a single URL"""
    url: HttpUrl = Field(..., description="URL to scrape")
    compliance_level: ComplianceLevelEnum = Field(
        default=ComplianceLevelEnum.BALANCED,
        description="Compliance level: strict, balanced, or aggressive"
    )
    scrape_prompt: Optional[str] = Field(
        None,
        description="Optional prompt for LLM-powered content extraction"
    )
    llm_provider: LLMProviderEnum = Field(
        default=LLMProviderEnum.OPENAI,
        description="LLM provider for smart scraping"
    )
    auth_config: Optional[AuthConfigRequest] = Field(
        None,
        description="Optional authentication configuration"
    )
    session_id: Optional[str] = Field(
        None,
        description="Optional session ID to associate scraped document"
    )
    project_id: Optional[str] = Field(
        None,
        description="Optional project/module ID for organization"
    )
    department: Optional[str] = Field(
        None,
        description="Optional department name for organization"
    )
    team: Optional[str] = Field(
        None,
        description="Optional team name for organization"
    )


class BulkScrapeRequest(BaseModel):
    """Request model for scraping multiple URLs"""
    urls: List[HttpUrl] = Field(..., max_items=50, description="List of URLs to scrape (max 50)")
    compliance_level: ComplianceLevelEnum = Field(
        default=ComplianceLevelEnum.BALANCED,
        description="Compliance level for all URLs"
    )
    scrape_prompt: Optional[str] = Field(
        None,
        description="Optional prompt for LLM-powered content extraction"
    )
    llm_provider: LLMProviderEnum = Field(
        default=LLMProviderEnum.OPENAI,
        description="LLM provider for smart scraping"
    )
    session_id: Optional[str] = Field(
        None,
        description="Optional session ID to associate scraped documents"
    )
    project_id: Optional[str] = Field(
        None,
        description="Optional project/module ID for organization"
    )
    department: Optional[str] = Field(
        None,
        description="Optional department name for organization"
    )
    team: Optional[str] = Field(
        None,
        description="Optional team name for organization"
    )


class ScrapeResponse(BaseModel):
    """Response model for scrape operation"""
    success: bool
    job_id: Optional[str] = None
    document_id: Optional[str] = None
    url: str
    title: Optional[str] = None
    content_length: Optional[int] = None
    compliance_level: str
    llm_provider: Optional[str] = None
    scraping_time_ms: Optional[float] = None
    error: Optional[str] = None


class BulkScrapeResponse(BaseModel):
    """Response model for bulk scrape operation"""
    results: List[ScrapeResponse]
    total: int
    successful: int
    failed: int


class CapabilitiesResponse(BaseModel):
    """Response model for scraper capabilities"""
    compliance_level: str
    smart_scraping_enabled: bool
    compliance_settings: Dict[str, Any]
    supported_llm_providers: List[str]
    default_llm_provider: str
    ollama_models: List[str]
    supported_compliance_levels: List[str] = ["strict", "balanced", "aggressive"]
    supported_auth_types: List[str] = ["none", "basic", "bearer", "api_key", "oauth2", "jwt", "session", "custom"]


# Helper Functions

def get_scraper_for_level(compliance_level: ComplianceLevelEnum) -> ScraperEngine:
    """Get scraper instance for compliance level"""
    if compliance_level == ComplianceLevelEnum.STRICT:
        return strict_scraper
    elif compliance_level == ComplianceLevelEnum.BALANCED:
        return balanced_scraper
    elif compliance_level == ComplianceLevelEnum.AGGRESSIVE:
        return aggressive_scraper
    else:
        return balanced_scraper


async def save_scrape_result(
    result: Dict[str, Any],
    scrape_request: ScrapeRequest,
    db: AsyncSession
) -> Optional[str]:
    """
    Save scrape result to database

    Args:
        result: Scrape result dict
        scrape_request: Original request
        db: Database session

    Returns:
        Job ID if saved, None otherwise
    """
    try:
        # Create scrape job
        job = WebScrapeJob(
            url=str(scrape_request.url),
            scrape_prompt=scrape_request.scrape_prompt,
            status="completed" if result.get("success") else "failed",
            compliance_level=scrape_request.compliance_level.value,
            llm_provider=scrape_request.llm_provider.value if scrape_request.scrape_prompt else None,
            scraping_time_ms=result.get("scraping_time_ms"),
            protocols_detected=result.get("protocols_detected"),
            user_agent_used=result.get("metadata", {}).get("user_agent"),
            error_message=result.get("error")
        )

        # If successful, create document
        if result.get("success"):
            # Save scraped content as document
            content_text = f"Title: {result['title']}\n\nURL: {result['url']}\n\n{result['content']}"
            content_bytes = content_text.encode('utf-8')

            # Generate filename
            from urllib.parse import urlparse
            parsed = urlparse(str(scrape_request.url))
            filename = f"scraped_{parsed.netloc}_{job.id.hex[:8]}.txt"

            # Upload document
            document = await document_service.upload_file(
                file_data=content_bytes,
                filename=filename,
                file_type="text/plain",
                source_type="scrape",
                source_url=str(scrape_request.url),
                db=db
            )

            # Link document to job
            job.document_id = document.id

            # Process document (chunk and embed)
            await document_service.process_document(document.id, db)

            # Associate with session if provided
            if scrape_request.session_id:
                from app.models.database_enhanced import SessionDocument
                session_doc = SessionDocument(
                    session_id=scrape_request.session_id,
                    document_id=document.id
                )
                db.add(session_doc)

        db.add(job)
        await db.commit()
        await db.refresh(job)

        return str(job.id)

    except Exception as e:
        logger.error(f"Error saving scrape result: {e}")
        return None


# API Endpoints

@router.get("/capabilities", response_model=CapabilitiesResponse)
async def get_capabilities():
    """Get scraper capabilities and configuration"""
    scraper = balanced_scraper
    await scraper.initialize()

    capabilities = scraper.get_capabilities()

    return CapabilitiesResponse(
        **capabilities,
        supported_compliance_levels=["strict", "balanced", "aggressive"],
        supported_auth_types=["none", "basic", "bearer", "api_key", "oauth2", "jwt", "session", "custom"]
    )


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_url(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Scrape a single URL with enhanced features

    Features:
    - Compliance modes: strict, balanced, aggressive
    - LLM-powered smart scraping with Ollama, OpenAI, or Anthropic
    - Dynamic protocol detection and adaptation
    - Authentication support
    - Automatic document processing and embedding
    """
    try:
        # Get scraper for compliance level
        scraper = get_scraper_for_level(request.compliance_level)
        await scraper.initialize()

        # Prepare auth config if provided
        auth_config = None
        if request.auth_config:
            from app.tier_1.data_extraction.webscraper.compliance import auth_manager
            auth_config = auth_manager.create_auth(
                auth_type=request.auth_config.auth_type,
                credentials=request.auth_config.credentials
            )

        # Scrape URL
        result = await scraper.scrape_url(
            url=str(request.url),
            scrape_prompt=request.scrape_prompt,
            llm_provider=request.llm_provider.value,
            auth_config=auth_config
        )

        # Save result to database
        job_id = await save_scrape_result(result, request, db)

        # Return response
        return ScrapeResponse(
            success=result.get("success", False),
            job_id=job_id,
            document_id=str(result.get("document_id")) if result.get("document_id") else None,
            url=str(request.url),
            title=result.get("title"),
            content_length=result.get("content_length"),
            compliance_level=request.compliance_level.value,
            llm_provider=request.llm_provider.value if request.scrape_prompt else None,
            scraping_time_ms=result.get("scraping_time_ms"),
            error=result.get("error")
        )

    except Exception as e:
        logger.error(f"Error scraping URL {request.url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape/bulk", response_model=BulkScrapeResponse)
async def scrape_bulk(
    request: BulkScrapeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Scrape multiple URLs in bulk

    Features:
    - Process up to 50 URLs per request
    - Automatic rate limiting and compliance
    - Parallel processing with concurrency control
    - Individual error handling per URL
    """
    try:
        # Get scraper for compliance level
        scraper = get_scraper_for_level(request.compliance_level)
        await scraper.initialize()

        # Convert URLs to strings
        urls = [str(url) for url in request.urls]

        # Scrape all URLs
        results = await scraper.scrape_multiple_urls(
            urls=urls,
            scrape_prompt=request.scrape_prompt,
            llm_provider=request.llm_provider.value
        )

        # Save results and create responses
        responses = []
        for result in results:
            # Create individual scrape request for saving
            individual_request = ScrapeRequest(
                url=result["url"],
                compliance_level=request.compliance_level,
                scrape_prompt=request.scrape_prompt,
                llm_provider=request.llm_provider,
                session_id=request.session_id
            )

            job_id = await save_scrape_result(result, individual_request, db)

            responses.append(ScrapeResponse(
                success=result.get("success", False),
                job_id=job_id,
                document_id=str(result.get("document_id")) if result.get("document_id") else None,
                url=result["url"],
                title=result.get("title"),
                content_length=result.get("content_length"),
                compliance_level=request.compliance_level.value,
                llm_provider=request.llm_provider.value if request.scrape_prompt else None,
                scraping_time_ms=result.get("scraping_time_ms"),
                error=result.get("error")
            ))

        # Calculate statistics
        successful = sum(1 for r in responses if r.success)
        failed = len(responses) - successful

        return BulkScrapeResponse(
            results=responses,
            total=len(responses),
            successful=successful,
            failed=failed
        )

    except Exception as e:
        logger.error(f"Error in bulk scraping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    """Get scrape job status and details"""
    try:
        from sqlalchemy import select
        from uuid import UUID

        job_uuid = UUID(job_id)

        result = await db.execute(
            select(WebScrapeJob).where(WebScrapeJob.id == job_uuid)
        )
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return {
            "job_id": str(job.id),
            "url": job.url,
            "status": job.status,
            "compliance_level": job.compliance_level,
            "llm_provider": job.llm_provider,
            "scraping_time_ms": job.scraping_time_ms,
            "document_id": str(job.document_id) if job.document_id else None,
            "error_message": job.error_message,
            "protocols_detected": job.protocols_detected,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
