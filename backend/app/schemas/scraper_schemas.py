"""
Pydantic schemas for enhanced web scraper API.
"""

from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, List, Dict, Any
from enum import Enum


class ScraperStrategyEnum(str, Enum):
    """Available scraper strategies"""
    AUTO = "auto"
    TRAFILATURA = "trafilatura"
    BEAUTIFULSOUP = "beautifulsoup"
    PLAYWRIGHT = "playwright"
    HYBRID = "hybrid"


class ScraperConfigRequest(BaseModel):
    """Custom scraper configuration"""
    strategy: Optional[ScraperStrategyEnum] = Field(
        default=ScraperStrategyEnum.AUTO,
        description="Scraping strategy to use"
    )
    timeout: Optional[float] = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="Request timeout in seconds"
    )
    max_retries: Optional[int] = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts"
    )
    follow_redirects: Optional[bool] = Field(
        default=True,
        description="Follow HTTP redirects"
    )
    user_agent: Optional[str] = Field(
        default=None,
        description="Custom user agent string"
    )

    # Content extraction options
    include_links: Optional[bool] = Field(
        default=True,
        description="Include links in extracted content"
    )
    include_tables: Optional[bool] = Field(
        default=True,
        description="Include tables in extracted content"
    )
    include_images: Optional[bool] = Field(
        default=False,
        description="Include image references"
    )
    include_metadata: Optional[bool] = Field(
        default=True,
        description="Include page metadata"
    )

    # Content filtering
    remove_nav: Optional[bool] = Field(
        default=True,
        description="Remove navigation elements"
    )
    remove_footer: Optional[bool] = Field(
        default=True,
        description="Remove footer elements"
    )
    remove_header: Optional[bool] = Field(
        default=True,
        description="Remove header elements"
    )
    remove_ads: Optional[bool] = Field(
        default=True,
        description="Remove advertisement elements"
    )

    # JavaScript rendering
    enable_javascript: Optional[bool] = Field(
        default=False,
        description="Enable JavaScript rendering (requires Playwright)"
    )
    wait_for_selector: Optional[str] = Field(
        default=None,
        description="CSS selector to wait for before scraping"
    )
    wait_timeout: Optional[float] = Field(
        default=10.0,
        ge=1.0,
        le=60.0,
        description="Wait timeout for JavaScript rendering"
    )

    # Content quality
    min_content_length: Optional[int] = Field(
        default=100,
        ge=0,
        description="Minimum content length in characters"
    )
    max_content_length: Optional[int] = Field(
        default=None,
        description="Maximum content length in characters"
    )

    class Config:
        schema_extra = {
            "example": {
                "strategy": "auto",
                "timeout": 30.0,
                "include_tables": True,
                "enable_javascript": False,
                "min_content_length": 100
            }
        }


class ScrapeRequest(BaseModel):
    """Request to scrape a single URL"""
    url: HttpUrl = Field(
        ...,
        description="URL to scrape"
    )
    scrape_prompt: Optional[str] = Field(
        default=None,
        description="Optional prompt to guide content extraction"
    )
    strategy: Optional[ScraperStrategyEnum] = Field(
        default=None,
        description="Override scraping strategy"
    )
    config: Optional[ScraperConfigRequest] = Field(
        default=None,
        description="Custom scraper configuration"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID to associate document with"
    )
    project_id: Optional[str] = Field(
        default=None,
        description="Project/Module ID for organization"
    )
    department: Optional[str] = Field(
        default=None,
        description="Department name for organization"
    )
    team: Optional[str] = Field(
        default=None,
        description="Team name for organization"
    )

    class Config:
        schema_extra = {
            "example": {
                "url": "https://example.com/article",
                "scrape_prompt": "Extract information about AI and machine learning",
                "strategy": "auto",
                "session_id": "session_123"
            }
        }


class BulkScrapeRequest(BaseModel):
    """Request to scrape multiple URLs"""
    urls: List[HttpUrl] = Field(
        ...,
        min_items=1,
        max_items=50,
        description="List of URLs to scrape (max 50)"
    )
    scrape_prompt: Optional[str] = Field(
        default=None,
        description="Optional prompt to guide content extraction for all URLs"
    )
    strategy: Optional[ScraperStrategyEnum] = Field(
        default=None,
        description="Scraping strategy for all URLs"
    )
    config: Optional[ScraperConfigRequest] = Field(
        default=None,
        description="Custom scraper configuration for all URLs"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID to associate documents with"
    )

    @validator('urls')
    def validate_urls_count(cls, v):
        if len(v) > 50:
            raise ValueError('Maximum 50 URLs allowed per request')
        return v

    class Config:
        schema_extra = {
            "example": {
                "urls": [
                    "https://example.com/article1",
                    "https://example.com/article2"
                ],
                "scrape_prompt": "Extract product information",
                "strategy": "hybrid",
                "session_id": "session_123"
            }
        }


class ScrapeResponse(BaseModel):
    """Response from scraping a URL"""
    success: bool = Field(
        ...,
        description="Whether scraping was successful"
    )
    job_id: Optional[str] = Field(
        default=None,
        description="Scrape job ID"
    )
    document_id: Optional[str] = Field(
        default=None,
        description="Created document ID"
    )
    title: Optional[str] = Field(
        default=None,
        description="Extracted page title"
    )
    content_length: Optional[int] = Field(
        default=None,
        description="Length of extracted content"
    )
    url: str = Field(
        ...,
        description="URL that was scraped"
    )
    strategy_used: Optional[str] = Field(
        default=None,
        description="Strategy that was used for scraping"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata extracted from page"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if scraping failed"
    )

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "job_id": "job_123",
                "document_id": "doc_456",
                "title": "Example Article",
                "content_length": 5000,
                "url": "https://example.com/article",
                "strategy_used": "auto(trafilatura)",
                "metadata": {
                    "description": "Article description",
                    "keywords": "AI, ML, NLP"
                }
            }
        }


class BulkScrapeResponse(BaseModel):
    """Response from bulk scraping"""
    results: List[ScrapeResponse] = Field(
        ...,
        description="Results for each URL"
    )
    total: int = Field(
        ...,
        description="Total URLs processed"
    )
    successful: int = Field(
        ...,
        description="Number of successful scrapes"
    )
    failed: int = Field(
        ...,
        description="Number of failed scrapes"
    )

    class Config:
        schema_extra = {
            "example": {
                "results": [
                    {
                        "success": True,
                        "document_id": "doc_1",
                        "url": "https://example.com/1",
                        "content_length": 3000
                    },
                    {
                        "success": False,
                        "url": "https://example.com/2",
                        "error": "Connection timeout"
                    }
                ],
                "total": 2,
                "successful": 1,
                "failed": 1
            }
        }


class ScraperCapabilitiesResponse(BaseModel):
    """Information about scraper capabilities"""
    web_scraping_enabled: bool = Field(
        ...,
        description="Whether web scraping is enabled"
    )
    playwright_enabled: bool = Field(
        ...,
        description="Whether Playwright (JavaScript rendering) is enabled"
    )
    smart_scraping_enabled: bool = Field(
        ...,
        description="Whether AI-powered smart scraping is enabled"
    )
    available_strategies: List[str] = Field(
        ...,
        description="List of available scraping strategies"
    )
    default_strategy: str = Field(
        ...,
        description="Default scraping strategy"
    )
    max_concurrent_requests: int = Field(
        ...,
        description="Maximum concurrent scraping requests"
    )
    configuration: Dict[str, Any] = Field(
        ...,
        description="Default configuration values"
    )

    class Config:
        schema_extra = {
            "example": {
                "web_scraping_enabled": True,
                "playwright_enabled": False,
                "smart_scraping_enabled": True,
                "available_strategies": ["auto", "trafilatura", "beautifulsoup", "hybrid"],
                "default_strategy": "auto",
                "max_concurrent_requests": 5,
                "configuration": {
                    "timeout": 30.0,
                    "max_retries": 3,
                    "min_content_length": 100
                }
            }
        }


class WebScrapeJobStatus(BaseModel):
    """Status of a web scrape job"""
    job_id: str = Field(..., description="Job ID")
    url: str = Field(..., description="URL being scraped")
    status: str = Field(..., description="Job status (processing, completed, failed)")
    document_id: Optional[str] = Field(default=None, description="Document ID if completed")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    created_at: str = Field(..., description="Job creation timestamp")
    completed_at: Optional[str] = Field(default=None, description="Job completion timestamp")

    class Config:
        schema_extra = {
            "example": {
                "job_id": "job_123",
                "url": "https://example.com/article",
                "status": "completed",
                "document_id": "doc_456",
                "created_at": "2024-01-01T12:00:00Z",
                "completed_at": "2024-01-01T12:00:05Z"
            }
        }
