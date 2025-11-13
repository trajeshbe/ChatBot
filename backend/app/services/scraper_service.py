import httpx
from bs4 import BeautifulSoup
from trafilatura import extract
from typing import Dict, Optional
import logging
from urllib.parse import urlparse
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import Document, WebScrapeJob
from app.services.document_service import document_service

logger = logging.getLogger(__name__)


class ScraperService:
    def __init__(self):
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )

    async def close(self):
        """Close HTTP client"""
        await self.http_client.close()

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

            # Fetch the page
            response = await self.http_client.get(url)
            response.raise_for_status()

            html_content = response.text
            logger.info(f"Fetched {len(html_content)} bytes from {url}")

            # Extract main content using trafilatura (better for articles)
            main_content = extract(
                html_content,
                include_comments=False,
                include_tables=True,
                include_links=True
            )

            # Fallback to BeautifulSoup if trafilatura fails
            if not main_content:
                soup = BeautifulSoup(html_content, 'lxml')

                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()

                # Get text
                main_content = soup.get_text(separator='\n', strip=True)

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

            # Create document from scraped content
            document_data = {
                'title': title_text,
                'content': main_content,
                'description': description,
                'url': url,
                'metadata': {
                    'content_type': response.headers.get('content-type', ''),
                    'status_code': response.status_code,
                    'scrape_prompt': scrape_prompt
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
