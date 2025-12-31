"""
Scraper Strategy Plugin Architecture

This module implements a plugin-based architecture for web scraping,
allowing multiple scraping strategies with different strengths.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List
import httpx
from bs4 import BeautifulSoup
from trafilatura import extract
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ScraperStrategy(str, Enum):
    """Available scraper strategies"""
    TRAFILATURA = "trafilatura"  # Best for articles and blog posts
    BEAUTIFULSOUP = "beautifulsoup"  # General purpose HTML parsing
    PLAYWRIGHT = "playwright"  # JavaScript-heavy sites (requires browser)
    HYBRID = "hybrid"  # Tries multiple strategies in sequence
    AUTO = "auto"  # Automatically selects best strategy


@dataclass
class ScraperConfig:
    """Configuration for scraper behavior"""
    strategy: ScraperStrategy = ScraperStrategy.AUTO
    timeout: float = 30.0
    max_retries: int = 3
    follow_redirects: bool = True
    user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

    # Content extraction options
    include_links: bool = True
    include_tables: bool = True
    include_images: bool = False
    include_metadata: bool = True

    # Filtering options
    remove_nav: bool = True
    remove_footer: bool = True
    remove_header: bool = True
    remove_ads: bool = True

    # JavaScript rendering (for Playwright)
    enable_javascript: bool = False
    wait_for_selector: Optional[str] = None
    wait_timeout: float = 10.0

    # Rate limiting
    respect_robots_txt: bool = True
    delay_between_requests: float = 1.0

    # Content quality
    min_content_length: int = 100
    max_content_length: Optional[int] = None


@dataclass
class ScrapedContent:
    """Structured result from scraping"""
    content: str
    title: str
    description: str
    url: str
    metadata: Dict
    strategy_used: str
    success: bool
    error: Optional[str] = None
    content_length: int = 0

    def __post_init__(self):
        self.content_length = len(self.content) if self.content else 0


class BaseScraperStrategy(ABC):
    """Abstract base class for scraper strategies"""

    def __init__(self, config: ScraperConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def scrape(self, url: str, html_content: Optional[str] = None) -> ScrapedContent:
        """
        Scrape content from a URL

        Args:
            url: URL to scrape
            html_content: Pre-fetched HTML (optional, for efficiency)

        Returns:
            ScrapedContent object with extracted data
        """
        pass

    @abstractmethod
    def is_suitable_for(self, url: str, html_content: Optional[str] = None) -> bool:
        """
        Determine if this strategy is suitable for the given URL

        Args:
            url: URL to check
            html_content: HTML content (optional)

        Returns:
            True if this strategy is suitable
        """
        pass

    def extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract metadata from HTML"""
        metadata = {'url': url}

        # Title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.string

        # Meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[name] = content

        # Links
        if self.config.include_links:
            metadata['links'] = [a.get('href') for a in soup.find_all('a', href=True)]

        # Images
        if self.config.include_images:
            metadata['images'] = [img.get('src') for img in soup.find_all('img', src=True)]

        return metadata


class TrafilaturaStrategy(BaseScraperStrategy):
    """
    Trafilatura-based scraping strategy.
    Best for: Articles, blog posts, news sites.
    """

    async def scrape(self, url: str, html_content: Optional[str] = None) -> ScrapedContent:
        """Scrape using Trafilatura"""
        try:
            self.logger.info(f"Using Trafilatura strategy for {url}")

            # Fetch HTML if not provided
            if not html_content:
                async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    html_content = response.text

            # Extract content
            content = extract(
                html_content,
                include_comments=False,
                include_tables=self.config.include_tables,
                include_links=self.config.include_links,
                output_format='txt'
            )

            if not content or len(content) < self.config.min_content_length:
                return ScrapedContent(
                    content="",
                    title="",
                    description="",
                    url=url,
                    metadata={},
                    strategy_used="trafilatura",
                    success=False,
                    error="Insufficient content extracted"
                )

            # Extract metadata
            soup = BeautifulSoup(html_content, 'lxml')
            metadata = self.extract_metadata(soup, url)

            title = metadata.get('title', '')
            description = metadata.get('description', '')

            return ScrapedContent(
                content=content,
                title=title,
                description=description,
                url=url,
                metadata=metadata,
                strategy_used="trafilatura",
                success=True
            )

        except Exception as e:
            self.logger.error(f"Trafilatura strategy failed for {url}: {e}")
            return ScrapedContent(
                content="",
                title="",
                description="",
                url=url,
                metadata={},
                strategy_used="trafilatura",
                success=False,
                error=str(e)
            )

    def is_suitable_for(self, url: str, html_content: Optional[str] = None) -> bool:
        """Trafilatura is good for most article-based content"""
        # Could add URL pattern matching here
        # e.g., blog.*, medium.com, etc.
        return True


class BeautifulSoupStrategy(BaseScraperStrategy):
    """
    BeautifulSoup-based scraping strategy.
    Best for: General HTML parsing, structured data extraction.
    """

    async def scrape(self, url: str, html_content: Optional[str] = None) -> ScrapedContent:
        """Scrape using BeautifulSoup"""
        try:
            self.logger.info(f"Using BeautifulSoup strategy for {url}")

            # Fetch HTML if not provided
            if not html_content:
                async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    html_content = response.text

            soup = BeautifulSoup(html_content, 'lxml')

            # Remove unwanted elements
            for element in soup(["script", "style"]):
                element.decompose()

            if self.config.remove_nav:
                for nav in soup.find_all('nav'):
                    nav.decompose()

            if self.config.remove_header:
                for header in soup.find_all('header'):
                    header.decompose()

            if self.config.remove_footer:
                for footer in soup.find_all('footer'):
                    footer.decompose()

            # Extract main content
            # Try to find main content container first
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')

            if main_content:
                content = main_content.get_text(separator='\n', strip=True)
            else:
                content = soup.get_text(separator='\n', strip=True)

            # Clean up content
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            content = '\n'.join(lines)

            if len(content) < self.config.min_content_length:
                return ScrapedContent(
                    content="",
                    title="",
                    description="",
                    url=url,
                    metadata={},
                    strategy_used="beautifulsoup",
                    success=False,
                    error="Insufficient content extracted"
                )

            # Extract metadata
            metadata = self.extract_metadata(soup, url)
            title = metadata.get('title', '')
            description = metadata.get('description', '')

            return ScrapedContent(
                content=content,
                title=title,
                description=description,
                url=url,
                metadata=metadata,
                strategy_used="beautifulsoup",
                success=True
            )

        except Exception as e:
            self.logger.error(f"BeautifulSoup strategy failed for {url}: {e}")
            return ScrapedContent(
                content="",
                title="",
                description="",
                url=url,
                metadata={},
                strategy_used="beautifulsoup",
                success=False,
                error=str(e)
            )

    def is_suitable_for(self, url: str, html_content: Optional[str] = None) -> bool:
        """BeautifulSoup works for all HTML content"""
        return True


class PlaywrightStrategy(BaseScraperStrategy):
    """
    Playwright-based scraping strategy.
    Best for: JavaScript-heavy sites, SPAs, dynamic content.
    Note: Requires playwright installation and browser binaries.
    """

    def __init__(self, config: ScraperConfig):
        super().__init__(config)
        self._browser = None
        self._playwright = None

    async def _ensure_browser(self):
        """Lazy initialization of Playwright browser"""
        if self._browser is None:
            try:
                import os

                # CRITICAL: Set PLAYWRIGHT_BROWSERS_PATH BEFORE importing playwright
                # Workaround for volume mounting issue where docker-compose env vars aren't seen by Python
                os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/ms-playwright'
                self.logger.info(f"Set PLAYWRIGHT_BROWSERS_PATH={os.environ.get('PLAYWRIGHT_BROWSERS_PATH')}")

                # Skip Playwright's dependency check (we have the libs, just different names in Ubuntu 24.04)
                os.environ['PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS'] = 'true'

                # NOW import playwright AFTER setting env vars
                from playwright.async_api import async_playwright

                self.logger.info("🚀 Starting Playwright initialization...")
                self._playwright = await async_playwright().start()
                self.logger.info("✅ Playwright started successfully")

                # Launch with explicit path and Docker-compatible arguments
                chromium_path = "/ms-playwright/chromium-1140/chrome-linux/chrome"
                self.logger.info(f"Using Chromium executable: {chromium_path}")
                self._browser = await self._playwright.chromium.launch(
                    executable_path=chromium_path,
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                        '--no-zygote',
                        '--disable-gpu'
                    ]
                )
                self.logger.info(f"✅ Chromium launched successfully")
            except ImportError:
                raise ImportError(
                    "Playwright not installed. Install with: pip install playwright && playwright install chromium"
                )

    async def scrape(self, url: str, html_content: Optional[str] = None) -> ScrapedContent:
        """Scrape using Playwright (browser automation)"""
        try:
            self.logger.info(f"Using Playwright strategy for {url}")

            await self._ensure_browser()

            # Create a new page
            page = await self._browser.new_page()

            try:
                # Navigate to URL
                await page.goto(url, timeout=self.config.timeout * 1000, wait_until='networkidle')

                # Wait for specific selector if configured
                if self.config.wait_for_selector:
                    await page.wait_for_selector(
                        self.config.wait_for_selector,
                        timeout=self.config.wait_timeout * 1000
                    )

                # Get page content
                html_content = await page.content()

                # Extract text content
                content = await page.evaluate('() => document.body.innerText')

                # Get title
                title = await page.title()

                # Extract metadata
                soup = BeautifulSoup(html_content, 'lxml')
                metadata = self.extract_metadata(soup, url)
                metadata['title'] = title

                description = metadata.get('description', '')

                if len(content) < self.config.min_content_length:
                    return ScrapedContent(
                        content="",
                        title=title,
                        description=description,
                        url=url,
                        metadata=metadata,
                        strategy_used="playwright",
                        success=False,
                        error="Insufficient content extracted"
                    )

                return ScrapedContent(
                    content=content,
                    title=title,
                    description=description,
                    url=url,
                    metadata=metadata,
                    strategy_used="playwright",
                    success=True
                )

            finally:
                await page.close()

        except Exception as e:
            self.logger.error(f"Playwright strategy failed for {url}: {e}")
            return ScrapedContent(
                content="",
                title="",
                description="",
                url=url,
                metadata={},
                strategy_used="playwright",
                success=False,
                error=str(e)
            )

    async def close(self):
        """Clean up browser resources"""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    def is_suitable_for(self, url: str, html_content: Optional[str] = None) -> bool:
        """Playwright is suitable when JavaScript is needed"""
        # Could detect SPAs, React apps, etc.
        # For now, return True if JavaScript is enabled in config
        return self.config.enable_javascript


class HybridStrategy(BaseScraperStrategy):
    """
    Hybrid strategy that tries multiple strategies in sequence.
    Falls back to next strategy if previous one fails.
    """

    def __init__(self, config: ScraperConfig):
        super().__init__(config)
        self.strategies: List[BaseScraperStrategy] = [
            TrafilaturaStrategy(config),
            BeautifulSoupStrategy(config),
        ]

        # Always add Playwright as a fallback (critical for bot-protected sites)
        # Playwright can bypass 403 errors from sites like Wikipedia
        self.strategies.append(PlaywrightStrategy(config))

    async def scrape(self, url: str, html_content: Optional[str] = None) -> ScrapedContent:
        """Try multiple strategies until one succeeds"""
        self.logger.info(f"Using Hybrid strategy for {url}")

        last_error = None

        for strategy in self.strategies:
            try:
                result = await strategy.scrape(url, html_content)

                if result.success and len(result.content) >= self.config.min_content_length:
                    self.logger.info(f"Hybrid strategy succeeded with {strategy.__class__.__name__}")
                    result.strategy_used = f"hybrid({result.strategy_used})"
                    return result

                last_error = result.error or "Insufficient content"

            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"Strategy {strategy.__class__.__name__} failed: {e}")
                continue

        # All strategies failed
        return ScrapedContent(
            content="",
            title="",
            description="",
            url=url,
            metadata={},
            strategy_used="hybrid(all_failed)",
            success=False,
            error=f"All strategies failed. Last error: {last_error}"
        )

    def is_suitable_for(self, url: str, html_content: Optional[str] = None) -> bool:
        """Hybrid strategy is always suitable"""
        return True


class AutoStrategy(BaseScraperStrategy):
    """
    Auto strategy that intelligently selects the best strategy
    based on URL patterns and content analysis.
    """

    def __init__(self, config: ScraperConfig):
        super().__init__(config)
        self.strategies = {
            'trafilatura': TrafilaturaStrategy(config),
            'beautifulsoup': BeautifulSoupStrategy(config),
            'playwright': PlaywrightStrategy(config),
            'hybrid': HybridStrategy(config),
        }

    def _select_strategy(self, url: str) -> BaseScraperStrategy:
        """Select best strategy based on URL patterns"""
        url_lower = url.lower()

        # Sites that have strong bot detection and need Playwright
        # These sites will return 403 Forbidden or block simple HTTP clients
        bot_protected_sites = ['wikipedia.org', 'wikimedia.org', 'linkedin.com']
        if any(site in url_lower for site in bot_protected_sites):
            # Always use hybrid with Playwright to bypass bot detection
            return self.strategies['hybrid']

        # JavaScript-heavy sites
        js_sites = ['youtube.com', 'twitter.com', 'facebook.com', 'instagram.com']
        if any(site in url_lower for site in js_sites):
            if self.config.enable_javascript:
                return self.strategies['playwright']

        # News and blog sites (Trafilatura works best)
        article_sites = ['medium.com', 'blog', 'article', 'news', 'post']
        if any(site in url_lower for site in article_sites):
            return self.strategies['trafilatura']

        # Default to hybrid for unknown sites
        return self.strategies['hybrid']

    async def scrape(self, url: str, html_content: Optional[str] = None) -> ScrapedContent:
        """Automatically select and use best strategy"""
        self.logger.info(f"Auto-selecting strategy for {url}")

        strategy = self._select_strategy(url)
        self.logger.info(f"Selected {strategy.__class__.__name__} for {url}")

        result = await strategy.scrape(url, html_content)
        result.strategy_used = f"auto({result.strategy_used})"
        return result

    def is_suitable_for(self, url: str, html_content: Optional[str] = None) -> bool:
        """Auto strategy is always suitable"""
        return True


class ScraperStrategyFactory:
    """Factory for creating scraper strategies"""

    @staticmethod
    def create(strategy: ScraperStrategy, config: ScraperConfig) -> BaseScraperStrategy:
        """Create a scraper strategy instance"""
        strategies = {
            ScraperStrategy.TRAFILATURA: TrafilaturaStrategy,
            ScraperStrategy.BEAUTIFULSOUP: BeautifulSoupStrategy,
            ScraperStrategy.PLAYWRIGHT: PlaywrightStrategy,
            ScraperStrategy.HYBRID: HybridStrategy,
            ScraperStrategy.AUTO: AutoStrategy,
        }

        strategy_class = strategies.get(strategy)
        if not strategy_class:
            raise ValueError(f"Unknown scraper strategy: {strategy}")

        return strategy_class(config)
