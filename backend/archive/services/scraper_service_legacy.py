import httpx
from bs4 import BeautifulSoup
from trafilatura import extract
from typing import Dict, Optional
import logging
from urllib.parse import urlparse
import uuid
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import Document, WebScrapeJob
from app.services.document_service import document_service

logger = logging.getLogger(__name__)


class ScraperService:
    def __init__(self):
        # Realistic browser headers to avoid 403 errors
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',  # Removed 'br' - httpx only auto-decompresses gzip/deflate
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
        )

    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()

    async def _scrape_with_playwright(self, url: str) -> str:
        """
        Fallback scraping method using Playwright for bot-protected sites

        Args:
            url: URL to scrape

        Returns:
            HTML content as string
        """
        try:
            from playwright.async_api import async_playwright
            import traceback

            logger.info(f"🎭 Attempting Playwright fallback for {url}")

            async with async_playwright() as p:
                logger.info("🚀 Launching Chromium browser...")
                browser = await p.chromium.launch(headless=True)

                logger.info("📱 Creating browser context with user agent...")
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()

                try:
                    logger.info(f"🌐 Navigating to {url}...")
                    await page.goto(url, wait_until='networkidle', timeout=60000)
                    logger.info("✅ Page loaded successfully")

                    logger.info("⏳ Waiting 2 seconds for dynamic content...")
                    await page.wait_for_timeout(2000)

                    logger.info("📄 Extracting page content...")
                    html_content = await page.content()

                    logger.info(f"✅ Playwright successfully fetched {len(html_content)} bytes")
                    return html_content

                except Exception as page_error:
                    logger.error(f"❌ Page navigation/content extraction error: {str(page_error)}")
                    logger.error(f"📋 Traceback: {traceback.format_exc()}")
                    raise
                finally:
                    logger.info("🔒 Closing browser...")
                    await browser.close()

        except Exception as e:
            logger.error(f"❌ Playwright scraping failed for {url}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            logger.error(f"❌ Error message: {str(e)}")
            raise

    async def scrape_url(
        self,
        url: str,
        scrape_prompt: Optional[str] = None,
        db: AsyncSession = None
    ) -> Dict:
        """
        Scrape a URL and extract content

        Args:
            url: URL to scrape
            scrape_prompt: Optional prompt to guide content extraction
            db: Database session

        Returns:
            Dict with scraped content and metadata
        """
        try:
            # Create scrape job
            job = WebScrapeJob(
                url=url,
                scrape_prompt=scrape_prompt,
                status="processing"
            )

            if db:
                db.add(job)
                await db.commit()
                await db.refresh(job)

            logger.info(f"Starting scrape job for URL: {url}")

            # Fetch the page with retry logic and Playwright fallback
            max_retries = 3
            retry_delay = 1  # Start with 1 second
            use_playwright = False
            html_content = None
            response = None  # Initialize response

            try:
                for attempt in range(max_retries):
                    try:
                        logger.info(f"Fetching URL (attempt {attempt + 1}/{max_retries}): {url}")
                        response = await self.http_client.get(url)
                        response.raise_for_status()
                        html_content = response.text
                        break  # Success, exit retry loop
                    except httpx.HTTPStatusError as e:
                        if e.response.status_code == 403:
                            logger.warning(f"403 Forbidden for {url} on attempt {attempt + 1}")
                            if attempt < max_retries - 1:
                                # Add delay before retry
                                await asyncio.sleep(retry_delay)
                                retry_delay *= 2  # Exponential backoff
                            else:
                                # Last HTTP attempt failed, try Playwright
                                logger.warning(f"⚠️ HTTP blocked after {max_retries} attempts, attempting Playwright fallback")
                                use_playwright = True
                        else:
                            # Other HTTP errors, don't retry
                            raise
                    except httpx.RequestError as e:
                        logger.error(f"Request error on attempt {attempt + 1}: {e}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                            retry_delay *= 2
                        else:
                            # Last HTTP attempt failed, try Playwright
                            logger.warning(f"⚠️ HTTP requests failed after {max_retries} attempts, attempting Playwright fallback")
                            use_playwright = True
            except Exception as http_error:
                # Any other errors during HTTP attempts, try Playwright
                logger.warning(f"⚠️ HTTP scraping failed: {str(http_error)}, attempting Playwright fallback")
                use_playwright = True

            # Use Playwright if HTTP failed
            if use_playwright or html_content is None:
                html_content = await self._scrape_with_playwright(url)

            logger.info(f"Fetched {len(html_content)} bytes from {url}")

            # Primary: Use BeautifulSoup for reliable text extraction (works on all sites)
            soup = BeautifulSoup(html_content, 'lxml')

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text
            main_content = soup.get_text(separator='\n', strip=True)

            # If BeautifulSoup extraction is too short, try trafilatura as fallback (better for long articles)
            if len(main_content.strip()) < 100:
                logger.info("🔄 BeautifulSoup text too short, trying trafilatura fallback...")
                try:
                    trafilatura_text = extract(
                        html_content,
                        include_comments=False,
                        include_tables=True,
                        include_links=True
                    )
                    if trafilatura_text and len(trafilatura_text) > len(main_content):
                        main_content = trafilatura_text
                        logger.info(f"✅ Using trafilatura text ({len(main_content)} chars)")
                except Exception as e:
                    logger.debug(f"Trafilatura extraction failed: {e}")

            logger.info(f"📝 Extracted {len(main_content)} characters of text for LLM")

            # Extract metadata
            soup = BeautifulSoup(html_content, 'lxml')
            title = soup.find('title')
            title_text = title.string if title else urlparse(url).netloc

            meta_description = soup.find('meta', attrs={'name': 'description'})
            description = meta_description['content'] if meta_description else ""

            # If scrape_prompt is provided, use LLM to extract relevant content
            if scrape_prompt and main_content:
                # TODO: Use LLM to filter content based on prompt
                # For now, we'll just use the full content
                pass

            # Analyze HTML structure for template generation
            structure = {
                'tables': len(soup.find_all('table')),
                'lists': len(soup.find_all(['ul', 'ol'])),
                'forms': len(soup.find_all('form')),
                'divs_with_classes': len([d for d in soup.find_all('div') if d.get('class')]),
                'common_classes': [],
                'common_ids': []
            }

            # Find common class patterns
            classes = []
            for elem in soup.find_all(class_=True):
                classes.extend(elem.get('class', []))

            if classes:
                from collections import Counter
                common = Counter(classes).most_common(10)
                structure['common_classes'] = [c[0] for c in common]

            # If no database session provided, return content directly (for template generation)
            if db is None:
                logger.info(f"No DB session provided - returning raw content for {url}")
                return {
                    'html': html_content[:10000],  # Limit for LLM analysis
                    'text': main_content[:5000] if main_content else "",
                    'structure': structure,
                    'title': title_text,
                    'description': description
                }

            # Below this point, we have a DB session - create and save document

            # Create document from scraped content
            document_data = {
                'title': title_text,
                'content': main_content,
                'description': description,
                'url': url,
                'metadata': {
                    'content_type': response.headers.get('content-type', '') if response and not use_playwright else 'text/html',
                    'status_code': response.status_code if response and not use_playwright else 200,
                    'scrape_prompt': scrape_prompt,
                    'scraping_method': 'playwright' if use_playwright else 'http'
                }
            }

            # Save as document
            filename = f"scraped_{urlparse(url).netloc}_{uuid.uuid4().hex[:8]}.txt"
            content_bytes = f"Title: {title_text}\n\nURL: {url}\n\n{main_content}".encode('utf-8')

            document = await document_service.upload_file(
                file_data=content_bytes,
                filename=filename,
                file_type="text/plain",
                source_type="scrape",
                source_url=url,
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

            logger.info(f"Successfully scraped and processed {url}")

            return {
                'success': True,
                'job_id': str(job.id) if job else None,
                'document_id': str(document.id),
                'title': title_text,
                'content_length': len(main_content),
                'url': url
            }

        except Exception as e:
            logger.error(f"Error scraping URL {url}: {e}")

            # Update job status
            if db and job:
                job.status = "failed"
                job.error_message = str(e)
                await db.commit()

            raise

    async def scrape_multiple_urls(
        self,
        urls: list[str],
        scrape_prompt: Optional[str] = None,
        db: AsyncSession = None
    ) -> list[Dict]:
        """Scrape multiple URLs"""
        results = []
        for url in urls:
            try:
                result = await self.scrape_url(url, scrape_prompt, db)
                results.append(result)
            except Exception as e:
                results.append({
                    'success': False,
                    'url': url,
                    'error': str(e)
                })
        return results


# Singleton instance
scraper_service = ScraperService()
