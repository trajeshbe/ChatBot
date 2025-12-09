"""
Enhanced Scraper Service with Plugin Architecture

This service integrates the scraper strategy plugin system with
the document processing pipeline.
"""

import httpx
from typing import Dict, Optional, List
import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import urlparse

from app.models.database import Document, WebScrapeJob
from app.services.document_service import document_service
from app.services.scraper_strategies import (
    ScraperStrategy,
    ScraperConfig,
    ScraperStrategyFactory,
    ScrapedContent
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class ScraperService:
    """
    Enhanced scraper service with plugin architecture support.
    Provides flexible scraping with multiple strategies and comprehensive configuration.
    """

    def __init__(self):
        self.http_client = httpx.AsyncClient(
            timeout=settings.SCRAPER_TIMEOUT,
            follow_redirects=settings.SCRAPER_FOLLOW_REDIRECTS,
            headers={'User-Agent': settings.SCRAPER_USER_AGENT}
        )
        self._default_config = self._create_default_config()

    def _create_default_config(self) -> ScraperConfig:
        """Create default scraper configuration from settings"""
        return ScraperConfig(
            strategy=ScraperStrategy(settings.SCRAPER_DEFAULT_STRATEGY),
            timeout=settings.SCRAPER_TIMEOUT,
            max_retries=settings.SCRAPER_MAX_RETRIES,
            follow_redirects=settings.SCRAPER_FOLLOW_REDIRECTS,
            user_agent=settings.SCRAPER_USER_AGENT,
            include_links=settings.SCRAPER_INCLUDE_LINKS,
            include_tables=settings.SCRAPER_INCLUDE_TABLES,
            include_images=settings.SCRAPER_INCLUDE_IMAGES,
            include_metadata=settings.SCRAPER_INCLUDE_METADATA,
            remove_nav=settings.SCRAPER_REMOVE_NAV,
            remove_footer=settings.SCRAPER_REMOVE_FOOTER,
            remove_header=settings.SCRAPER_REMOVE_HEADER,
            remove_ads=settings.SCRAPER_REMOVE_ADS,
            enable_javascript=settings.SCRAPER_ENABLE_JAVASCRIPT,
            wait_timeout=settings.SCRAPER_WAIT_TIMEOUT,
            respect_robots_txt=settings.SCRAPER_RESPECT_ROBOTS_TXT,
            delay_between_requests=settings.SCRAPER_DELAY_BETWEEN_REQUESTS,
            min_content_length=settings.SCRAPER_MIN_CONTENT_LENGTH,
            max_content_length=settings.SCRAPER_MAX_CONTENT_LENGTH,
        )

    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()

    async def scrape_url(
        self,
        url: str,
        scrape_prompt: Optional[str] = None,
        strategy: Optional[str] = None,
        config: Optional[ScraperConfig] = None,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        department: Optional[str] = None,
        team: Optional[str] = None,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict:
        """
        Scrape a URL and extract content using the specified strategy.

        Args:
            url: URL to scrape
            scrape_prompt: Optional prompt for AI-guided content filtering
            strategy: Scraping strategy to use (overrides config)
            config: Custom scraper configuration (overrides defaults)
            session_id: Optional session ID for document association
            db: Database session

        Returns:
            Dict with scraped content and metadata
        """
        import time
        start_time = time.time()

        # Check if web scraping is enabled
        if not settings.ENABLE_WEB_SCRAPING:
            raise ValueError("Web scraping is disabled. Enable ENABLE_WEB_SCRAPING in settings.")

        # ============================================================
        # SCRAPING COMPLIANCE CHECK - Check configured policies
        # ============================================================
        compliance_check = None
        if db:
            from app.services.scraping_config_service import scraping_config_service

            compliance_check = await scraping_config_service.check_scraping_allowed(db, url)

            # If scraping is not allowed, raise error
            if not compliance_check.get('allowed', False):
                error_msg = compliance_check.get('reason', 'Scraping not allowed for this domain')
                alternative = compliance_check.get('alternative') or compliance_check.get('recommendation')

                if alternative:
                    error_msg += f"\n\nAlternative: {alternative}"

                # Log the blocked attempt
                await scraping_config_service.log_scraping_attempt(
                    db=db,
                    url=url,
                    method=strategy or 'auto',
                    success=False,
                    error_message=error_msg,
                    robots_txt_allowed=compliance_check.get('status') != 'robots_blocked',
                    session_id=session_id
                )

                raise ValueError(error_msg)

            # If API should be used instead, provide API info
            if compliance_check.get('use_api'):
                api_endpoint = compliance_check.get('api_endpoint')
                logger.info(f"API preferred for this domain: {api_endpoint}")
                # Note: Actual API integration would be implemented based on specific API
                # For now, we'll log this but continue with scraping
                # In production, you'd implement API-specific handlers here

        # Create scrape job
        job = None
        if db:
            job = WebScrapeJob(
                url=url,
                scrape_prompt=scrape_prompt,
                status="processing",
                project_id=project_id,
                scraped_by=user_id,
                department=department,
                team=team
            )
            db.add(job)
            await db.commit()
            await db.refresh(job)

        try:
            logger.info(f"Starting enhanced scrape job for URL: {url}")

            # Apply rate limiting from compliance check
            if compliance_check and compliance_check.get('rate_limit'):
                rate_limit = compliance_check['rate_limit']
                delay = rate_limit.get('delay_seconds', 0)
                if delay > 0:
                    logger.info(f"Applying rate limit delay: {delay}s")
                    import asyncio
                    await asyncio.sleep(delay)

            # Use custom config or default
            scraper_config = config or self._default_config

            # Override strategy if specified
            if strategy:
                scraper_config.strategy = ScraperStrategy(strategy)

            # Create scraper strategy
            scraper_strategy = ScraperStrategyFactory.create(
                scraper_config.strategy,
                scraper_config
            )

            # Perform scraping
            scraped_content: ScrapedContent = await scraper_strategy.scrape(url)

            if not scraped_content.success:
                raise Exception(scraped_content.error or "Scraping failed")

            # Apply smart scraping if enabled and prompt provided
            if settings.ENABLE_SMART_SCRAPING and scrape_prompt:
                scraped_content.content = await self._apply_smart_filtering(
                    scraped_content.content,
                    scrape_prompt
                )

            # Create document from scraped content
            filename = f"scraped_{urlparse(url).netloc}_{uuid.uuid4().hex[:8]}.txt"
            content_bytes = self._format_document_content(scraped_content).encode('utf-8')

            # Construct hierarchical MinIO path
            from app.services.document_service import construct_minio_path
            import re

            # Get project name from project_id
            project_name = "Global"
            if db and project_id:
                try:
                    from sqlalchemy import select
                    from app.models.database_enhanced import Project
                    project_result = await db.execute(
                        select(Project).where(Project.id == project_id)
                    )
                    project_obj = project_result.scalar_one_or_none()
                    if project_obj:
                        project_name = project_obj.name
                except Exception as e:
                    logger.warning(f"Could not fetch project name: {e}")

            # Extract domain name for folder organization
            domain = urlparse(url).netloc.replace('www.', '')
            safe_domain = re.sub(r'[^\w\-]', '_', domain)

            # Construct base path and add domain folder
            base_path = construct_minio_path(
                department=department,
                team=team,
                username=username or "anonymous",
                project=project_name,
                filename="",  # We'll add domain folder + filename manually
                folder="extractions"
            )
            minio_path = f"{base_path}{safe_domain}/{filename}"
            logger.info(f"📁 Constructed MinIO path: {minio_path}")

            document = await document_service.upload_file(
                file_data=content_bytes,
                filename=filename,
                file_type="text/plain",
                source_type="scrape",
                source_url=url,
                session_id=session_id,
                project_id=project_id,
                department=department,
                team=team,
                user_id=user_id,
                minio_path=minio_path,  # Pass hierarchical path
                db=db
            )

            # Process the document (chunk and embed)
            await document_service.process_document(document.id, db)

            # Update job status
            if db and job:
                job.status = "completed"
                job.document_id = document.id
                from sqlalchemy import func
                job.completed_at = func.now()
                await db.commit()

            # Calculate metrics
            response_time_ms = (time.time() - start_time) * 1000
            bytes_downloaded = len(content_bytes)

            # ============================================================
            # LOG SUCCESSFUL SCRAPING ATTEMPT
            # ============================================================
            if db:
                from app.services.scraping_config_service import scraping_config_service
                await scraping_config_service.log_scraping_attempt(
                    db=db,
                    url=url,
                    method=scraped_content.strategy_used,
                    success=True,
                    status_code=200,  # Successful scraping
                    response_time_ms=response_time_ms,
                    bytes_downloaded=bytes_downloaded,
                    robots_txt_allowed=compliance_check.get('status') != 'robots_blocked' if compliance_check else True,
                    rate_limit_respected=True,
                    session_id=session_id
                )

            logger.info(f"Successfully scraped and processed {url} using {scraped_content.strategy_used}")

            return {
                'success': True,
                'job_id': str(job.id) if job else None,
                'document_id': str(document.id),
                'title': scraped_content.title,
                'content_length': scraped_content.content_length,
                'url': url,
                'strategy_used': scraped_content.strategy_used,
                'metadata': scraped_content.metadata,
                'compliance': {
                    'checked': compliance_check is not None,
                    'status': compliance_check.get('status') if compliance_check else 'no_config',
                    'rate_limited': compliance_check.get('rate_limit') is not None if compliance_check else False
                }
            }

        except Exception as e:
            logger.error(f"Error scraping URL {url}: {e}")

            # Calculate metrics
            response_time_ms = (time.time() - start_time) * 1000

            # ============================================================
            # LOG FAILED SCRAPING ATTEMPT
            # ============================================================
            if db:
                from app.services.scraping_config_service import scraping_config_service
                await scraping_config_service.log_scraping_attempt(
                    db=db,
                    url=url,
                    method=strategy or 'auto',
                    success=False,
                    error_message=str(e),
                    response_time_ms=response_time_ms,
                    robots_txt_allowed=compliance_check.get('status') != 'robots_blocked' if compliance_check else None,
                    session_id=session_id
                )

            # Update job status
            if db and job:
                job.status = "failed"
                job.error_message = str(e)
                await db.commit()

            raise

    async def scrape_multiple_urls(
        self,
        urls: List[str],
        scrape_prompt: Optional[str] = None,
        strategy: Optional[str] = None,
        config: Optional[ScraperConfig] = None,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        department: Optional[str] = None,
        team: Optional[str] = None,
        user_id: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> List[Dict]:
        """
        Scrape multiple URLs with optional concurrency control.

        Args:
            urls: List of URLs to scrape
            scrape_prompt: Optional prompt for all URLs
            strategy: Scraping strategy to use
            config: Custom scraper configuration
            session_id: Optional session ID
            project_id: Optional project/module ID for organization
            department: Optional department name for organization
            team: Optional team name for organization
            user_id: Optional user ID who initiated the scraping
            db: Database session

        Returns:
            List of results for each URL
        """
        import asyncio

        # Respect concurrency limits
        semaphore = asyncio.Semaphore(settings.SCRAPER_MAX_CONCURRENT_REQUESTS)

        async def scrape_with_limit(url: str) -> Dict:
            """Scrape with concurrency limit and delay"""
            async with semaphore:
                try:
                    result = await self.scrape_url(
                        url=url,
                        scrape_prompt=scrape_prompt,
                        strategy=strategy,
                        config=config,
                        session_id=session_id,
                        project_id=project_id,
                        department=department,
                        team=team,
                        user_id=user_id,
                        db=db
                    )
                    # Add delay between requests
                    await asyncio.sleep(settings.SCRAPER_DELAY_BETWEEN_REQUESTS)
                    return result
                except Exception as e:
                    return {
                        'success': False,
                        'url': url,
                        'error': str(e)
                    }

        # Execute scraping tasks
        tasks = [scrape_with_limit(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        return list(results)

    async def _apply_smart_filtering(self, content: str, prompt: str) -> str:
        """
        Use AI to filter and extract relevant content based on prompt.

        Args:
            content: Raw scraped content
            prompt: User's prompt describing what to extract

        Returns:
            Filtered content
        """
        try:
            from app.services.llm_service import llm_service

            # Create a filtering prompt
            system_prompt = """You are a content extraction assistant.
Given raw web content and a user's specific information need, extract and return
only the most relevant portions of the content. Preserve important details and context.
Remove irrelevant sections, ads, navigation, etc."""

            user_prompt = f"""User is looking for: {prompt}

Raw content:
{content[:settings.SMART_SCRAPE_MAX_TOKENS * 4]}

Extract only the relevant portions:"""

            # Prepare messages for the LLM
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # Use LLM to filter content - use generate method with model_id parameter
            response = await llm_service.generate(
                prompt=user_prompt,
                messages=messages,
                model_id=settings.SMART_SCRAPE_MODEL,
                max_tokens=settings.SMART_SCRAPE_MAX_TOKENS,
                temperature=0.3  # Lower temperature for more focused extraction
            )

            filtered_content = response.get('content', content)
            logger.info(f"Smart filtering reduced content from {len(content)} to {len(filtered_content)} chars")
            logger.info(f"Used model: {response.get('model', 'unknown')} for smart filtering")

            return filtered_content

        except Exception as e:
            logger.warning(f"Smart filtering failed, using raw content: {e}")
            logger.exception(e)  # Log full traceback for debugging
            return content

    def _format_document_content(self, scraped: ScrapedContent) -> str:
        """Format scraped content as a document"""
        parts = []

        if scraped.title:
            parts.append(f"Title: {scraped.title}")

        parts.append(f"URL: {scraped.url}")

        if scraped.description:
            parts.append(f"Description: {scraped.description}")

        if scraped.metadata:
            # Add selected metadata
            if 'keywords' in scraped.metadata:
                parts.append(f"Keywords: {scraped.metadata['keywords']}")

        parts.append("")  # Blank line
        parts.append(scraped.content)

        return "\n".join(parts)

    async def get_scraper_capabilities(self) -> Dict:
        """Get information about available scraper capabilities"""
        return {
            'web_scraping_enabled': settings.ENABLE_WEB_SCRAPING,
            'playwright_enabled': settings.ENABLE_PLAYWRIGHT_SCRAPING,
            'smart_scraping_enabled': settings.ENABLE_SMART_SCRAPING,
            'available_strategies': [s.value for s in ScraperStrategy],
            'default_strategy': settings.SCRAPER_DEFAULT_STRATEGY,
            'max_concurrent_requests': settings.SCRAPER_MAX_CONCURRENT_REQUESTS,
            'configuration': {
                'timeout': settings.SCRAPER_TIMEOUT,
                'max_retries': settings.SCRAPER_MAX_RETRIES,
                'min_content_length': settings.SCRAPER_MIN_CONTENT_LENGTH,
                'javascript_enabled': settings.SCRAPER_ENABLE_JAVASCRIPT,
            }
        }


# Singleton instance
scraper_service = ScraperService()
