"""
Enhanced Scraper Engine

This module provides the main scraping orchestration with compliance engine integration,
LLM-powered intelligent scraping, and dynamic protocol adaptation.
"""

import logging
from typing import Dict, Optional, List, Any
from urllib.parse import urlparse
import uuid
from datetime import datetime

from bs4 import BeautifulSoup
from trafilatura import extract
import httpx

from ..compliance import (
    ComplianceEngine,
    ComplianceLevel,
    strict_compliance,
    balanced_compliance,
    aggressive_compliance
)

logger = logging.getLogger(__name__)


class ScraperEngine:
    """
    Enhanced web scraper with compliance engine and LLM support
    """

    def __init__(
        self,
        compliance_level: ComplianceLevel = ComplianceLevel.BALANCED,
        enable_smart_scraping: bool = True
    ):
        """
        Initialize scraper engine

        Args:
            compliance_level: The compliance level to use
            enable_smart_scraping: Whether to enable LLM-powered smart scraping
        """
        # Select compliance engine based on level
        if compliance_level == ComplianceLevel.STRICT:
            self.compliance = strict_compliance
        elif compliance_level == ComplianceLevel.BALANCED:
            self.compliance = balanced_compliance
        elif compliance_level == ComplianceLevel.AGGRESSIVE:
            self.compliance = aggressive_compliance
        else:
            self.compliance = balanced_compliance

        self.enable_smart_scraping = enable_smart_scraping
        self.initialized = False

        logger.info(f"Scraper engine initialized with {compliance_level} compliance")

    async def initialize(self):
        """Initialize scraper engine and compliance components"""
        if self.initialized:
            return

        await self.compliance.initialize()
        self.initialized = True
        logger.info("Scraper engine initialized")

    async def close(self):
        """Close scraper engine and compliance components"""
        await self.compliance.close()
        logger.info("Scraper engine closed")

    def _detect_site_protocol(self, url: str, content: str) -> Dict[str, Any]:
        """
        Detect site protocols and conditions for dynamic adaptation

        Args:
            url: The URL being scraped
            content: The HTML content

        Returns:
            Dict with detected protocols and recommendations
        """
        soup = BeautifulSoup(content, 'html.parser')
        protocols = {
            "has_javascript": False,
            "has_api": False,
            "has_structured_data": False,
            "has_sitemap": False,
            "complexity": "simple",
            "recommended_strategy": "trafilatura"
        }

        # Check for JavaScript frameworks
        scripts = soup.find_all('script')
        js_frameworks = ['react', 'vue', 'angular', 'next', 'nuxt']
        for script in scripts:
            script_content = str(script)
            if any(fw in script_content.lower() for fw in js_frameworks):
                protocols["has_javascript"] = True
                protocols["complexity"] = "complex"
                protocols["recommended_strategy"] = "playwright"
                break

        # Check for API endpoints
        if 'api' in url.lower() or '/graphql' in url.lower():
            protocols["has_api"] = True
            protocols["recommended_strategy"] = "api"

        # Check for structured data (JSON-LD, microdata)
        json_ld = soup.find_all('script', type='application/ld+json')
        if json_ld:
            protocols["has_structured_data"] = True

        microdata = soup.find_all(attrs={"itemscope": True})
        if microdata:
            protocols["has_structured_data"] = True

        # Check for sitemap reference
        sitemap_link = soup.find('link', rel='sitemap') or soup.find('a', href=lambda x: x and 'sitemap' in x.lower())
        if sitemap_link:
            protocols["has_sitemap"] = True

        # Determine complexity based on content
        if len(scripts) > 10:
            protocols["complexity"] = "complex"
        elif len(scripts) > 3:
            protocols["complexity"] = "medium"

        return protocols

    async def _extract_with_llm(
        self,
        content: str,
        scrape_prompt: str,
        llm_provider: str = "ollama"
    ) -> str:
        """
        Extract relevant content using LLM

        Args:
            content: The scraped content
            scrape_prompt: User's extraction prompt
            llm_provider: LLM provider to use ("ollama", "openai", "anthropic")

        Returns:
            Filtered/extracted content
        """
        try:
            # Import LLM service
            from app.services.llm_service import llm_service

            # Truncate content if too long (to fit in context window)
            max_content_length = 8000
            if len(content) > max_content_length:
                content = content[:max_content_length] + "...[truncated]"

            # Construct prompt for extraction
            system_prompt = """You are an expert data extraction assistant. Your job is to extract and return only the most relevant portions of the provided content based on the user's specific information need.

IMPORTANT:
- Extract only the portions directly relevant to the user's request
- Preserve the original formatting and structure where possible
- If the content contains the requested information, extract it precisely
- If the content does not contain the requested information, say "No relevant information found"
- Do not add commentary or explanation, just return the extracted content"""

            user_prompt = f"""User is looking for: {scrape_prompt}

Raw content from webpage:
{content}

Extract only the relevant portions:"""

            # Call LLM based on provider
            if llm_provider == "ollama":
                # Use Ollama with a local model (qwen or llama)
                response = await llm_service.generate_response(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    model="ollama/qwen2.5:latest",  # Default to qwen, fallback to llama
                    temperature=0.1,  # Low temperature for precise extraction
                    max_tokens=4000
                )
            elif llm_provider == "openai":
                response = await llm_service.generate_response(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    model="gpt-3.5-turbo",
                    temperature=0.1,
                    max_tokens=4000
                )
            elif llm_provider == "anthropic":
                response = await llm_service.generate_response(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    model="claude-3-haiku-20240307",
                    temperature=0.1,
                    max_tokens=4000
                )
            else:
                logger.warning(f"Unknown LLM provider: {llm_provider}, using original content")
                return content

            extracted_content = response.get("response", content)

            # Check if LLM found relevant information
            if "no relevant information found" in extracted_content.lower():
                logger.warning("LLM did not find relevant information, using original content")
                return content

            logger.info(f"Successfully extracted content using {llm_provider} LLM")
            return extracted_content

        except Exception as e:
            logger.error(f"Error extracting with LLM: {e}")
            # Fall back to original content
            return content

    async def scrape_url(
        self,
        url: str,
        scrape_prompt: Optional[str] = None,
        llm_provider: str = "ollama",
        auth_config: Optional[Dict[str, Any]] = None,
        custom_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Scrape a URL with compliance and smart extraction

        Args:
            url: The URL to scrape
            scrape_prompt: Optional prompt for LLM-powered extraction
            llm_provider: LLM provider for smart scraping ("ollama", "openai", "anthropic")
            auth_config: Optional authentication configuration
            custom_headers: Optional custom headers

        Returns:
            Dict with scraped content and metadata
        """
        start_time = datetime.now()

        try:
            # Make compliant request
            response = await self.compliance.make_compliant_request(
                url,
                method="GET",
                auth_config=auth_config
            )

            html_content = response.text
            logger.info(f"Fetched {len(html_content)} bytes from {url}")

            # Detect site protocols
            protocols = self._detect_site_protocol(url, html_content)
            logger.info(f"Detected protocols for {url}: {protocols}")

            # Extract main content using trafilatura (best for articles)
            main_content = extract(
                html_content,
                include_comments=False,
                include_tables=True,
                include_links=True
            )

            # Fallback to BeautifulSoup if trafilatura fails
            if not main_content or len(main_content) < 100:
                logger.debug("Trafilatura extraction insufficient, using BeautifulSoup")
                soup = BeautifulSoup(html_content, 'html.parser')

                # Remove script and style elements
                for element in soup(["script", "style", "nav", "footer", "header"]):
                    element.decompose()

                # Get text
                main_content = soup.get_text(separator='\n', strip=True)

            # Extract metadata
            soup = BeautifulSoup(html_content, 'html.parser')
            title = soup.find('title')
            title_text = title.string if title else urlparse(url).netloc

            meta_description = soup.find('meta', attrs={'name': 'description'})
            description = meta_description.get('content', '') if meta_description else ""

            # Smart scraping with LLM if enabled and prompt provided
            if self.enable_smart_scraping and scrape_prompt and main_content:
                logger.info(f"Applying LLM extraction with provider: {llm_provider}")
                main_content = await self._extract_with_llm(
                    main_content,
                    scrape_prompt,
                    llm_provider
                )

            # Calculate scraping time
            scraping_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            result = {
                'success': True,
                'url': url,
                'title': title_text,
                'content': main_content,
                'description': description,
                'content_length': len(main_content),
                'protocols_detected': protocols,
                'compliance_level': self.compliance.compliance_level.value,
                'llm_provider': llm_provider if scrape_prompt else None,
                'scraping_time_ms': scraping_time_ms,
                'metadata': {
                    'content_type': response.headers.get('content-type', ''),
                    'status_code': response.status_code,
                    'scrape_prompt': scrape_prompt,
                    'user_agent': response.request.headers.get('user-agent', ''),
                    'proxy_used': None  # TODO: Track proxy from response
                }
            }

            logger.info(f"Successfully scraped {url} in {scraping_time_ms:.2f}ms")
            return result

        except Exception as e:
            logger.error(f"Error scraping URL {url}: {e}")
            scraping_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            return {
                'success': False,
                'url': url,
                'error': str(e),
                'error_type': type(e).__name__,
                'scraping_time_ms': scraping_time_ms,
                'compliance_level': self.compliance.compliance_level.value
            }

    async def scrape_multiple_urls(
        self,
        urls: List[str],
        scrape_prompt: Optional[str] = None,
        llm_provider: str = "ollama",
        auth_config: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs

        Args:
            urls: List of URLs to scrape
            scrape_prompt: Optional prompt for LLM-powered extraction
            llm_provider: LLM provider for smart scraping
            auth_config: Optional authentication configuration

        Returns:
            List of scraping results
        """
        results = []

        for url in urls:
            try:
                result = await self.scrape_url(
                    url,
                    scrape_prompt=scrape_prompt,
                    llm_provider=llm_provider,
                    auth_config=auth_config
                )
                results.append(result)
            except Exception as e:
                results.append({
                    'success': False,
                    'url': url,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'compliance_level': self.compliance.compliance_level.value
                })

        logger.info(f"Scraped {len(urls)} URLs: {sum(1 for r in results if r['success'])} successful")
        return results

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get scraper capabilities and settings

        Returns:
            Dict with capabilities information
        """
        return {
            "compliance_level": self.compliance.compliance_level.value,
            "smart_scraping_enabled": self.enable_smart_scraping,
            "compliance_settings": self.compliance.get_settings(),
            "supported_llm_providers": ["ollama", "openai", "anthropic"],
            "default_llm_provider": "ollama",
            "ollama_models": ["qwen2.5:latest", "llama3.2:latest", "mistral:latest"]
        }


# Global instances for different compliance levels
strict_scraper = ScraperEngine(ComplianceLevel.STRICT)
balanced_scraper = ScraperEngine(ComplianceLevel.BALANCED)
aggressive_scraper = ScraperEngine(ComplianceLevel.AGGRESSIVE)

# Default instance (balanced)
scraper_engine = balanced_scraper
