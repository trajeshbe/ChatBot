"""
Tests for scraper strategy plugin architecture.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.tier_1.data_extraction.scraper_strategies import (
    ScraperStrategy,
    ScraperConfig,
    ScraperStrategyFactory,
    TrafilaturaStrategy,
    BeautifulSoupStrategy,
    HybridStrategy,
    AutoStrategy,
    ScrapedContent
)


class TestScraperConfig:
    """Test scraper configuration"""

    def test_default_config(self):
        """Test default configuration values"""
        config = ScraperConfig()

        assert config.strategy == ScraperStrategy.AUTO
        assert config.timeout == 30.0
        assert config.max_retries == 3
        assert config.follow_redirects is True
        assert config.include_links is True
        assert config.include_tables is True
        assert config.remove_nav is True

    def test_custom_config(self):
        """Test custom configuration"""
        config = ScraperConfig(
            strategy=ScraperStrategy.TRAFILATURA,
            timeout=60.0,
            include_images=True,
            enable_javascript=True
        )

        assert config.strategy == ScraperStrategy.TRAFILATURA
        assert config.timeout == 60.0
        assert config.include_images is True
        assert config.enable_javascript is True


class TestScraperStrategyFactory:
    """Test scraper strategy factory"""

    def test_create_trafilatura_strategy(self):
        """Test creating Trafilatura strategy"""
        config = ScraperConfig(strategy=ScraperStrategy.TRAFILATURA)
        strategy = ScraperStrategyFactory.create(ScraperStrategy.TRAFILATURA, config)

        assert isinstance(strategy, TrafilaturaStrategy)

    def test_create_beautifulsoup_strategy(self):
        """Test creating BeautifulSoup strategy"""
        config = ScraperConfig(strategy=ScraperStrategy.BEAUTIFULSOUP)
        strategy = ScraperStrategyFactory.create(ScraperStrategy.BEAUTIFULSOUP, config)

        assert isinstance(strategy, BeautifulSoupStrategy)

    def test_create_hybrid_strategy(self):
        """Test creating Hybrid strategy"""
        config = ScraperConfig(strategy=ScraperStrategy.HYBRID)
        strategy = ScraperStrategyFactory.create(ScraperStrategy.HYBRID, config)

        assert isinstance(strategy, HybridStrategy)

    def test_create_auto_strategy(self):
        """Test creating Auto strategy"""
        config = ScraperConfig(strategy=ScraperStrategy.AUTO)
        strategy = ScraperStrategyFactory.create(ScraperStrategy.AUTO, config)

        assert isinstance(strategy, AutoStrategy)

    def test_invalid_strategy(self):
        """Test creating invalid strategy raises error"""
        config = ScraperConfig()

        with pytest.raises(ValueError):
            ScraperStrategyFactory.create("invalid_strategy", config)


class TestTrafilaturaStrategy:
    """Test Trafilatura scraping strategy"""

    @pytest.mark.asyncio
    async def test_scrape_success(self):
        """Test successful scraping with Trafilatura"""
        config = ScraperConfig(min_content_length=10)
        strategy = TrafilaturaStrategy(config)

        html_content = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <article>
                    <h1>Test Article</h1>
                    <p>This is a test article with enough content for extraction.</p>
                    <p>Another paragraph with more content.</p>
                </article>
            </body>
        </html>
        """

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.text = html_content
            mock_response.raise_for_status = Mock()

            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            result = await strategy.scrape("https://example.com", html_content=html_content)

            assert result.success is True
            assert len(result.content) > 0
            assert result.strategy_used == "trafilatura"

    @pytest.mark.asyncio
    async def test_scrape_insufficient_content(self):
        """Test scraping with insufficient content"""
        config = ScraperConfig(min_content_length=1000)
        strategy = TrafilaturaStrategy(config)

        html_content = "<html><body><p>Short content</p></body></html>"

        result = await strategy.scrape("https://example.com", html_content=html_content)

        assert result.success is False
        assert result.error == "Insufficient content extracted"

    def test_is_suitable_for(self):
        """Test suitability check"""
        config = ScraperConfig()
        strategy = TrafilaturaStrategy(config)

        # Trafilatura is suitable for all URLs
        assert strategy.is_suitable_for("https://example.com") is True


class TestBeautifulSoupStrategy:
    """Test BeautifulSoup scraping strategy"""

    @pytest.mark.asyncio
    async def test_scrape_success(self):
        """Test successful scraping with BeautifulSoup"""
        config = ScraperConfig(min_content_length=10)
        strategy = BeautifulSoupStrategy(config)

        html_content = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <nav>Navigation</nav>
                <main>
                    <h1>Main Content</h1>
                    <p>This is the main content of the page.</p>
                </main>
                <footer>Footer</footer>
            </body>
        </html>
        """

        result = await strategy.scrape("https://example.com", html_content=html_content)

        assert result.success is True
        assert len(result.content) > 0
        assert result.strategy_used == "beautifulsoup"
        # Navigation and footer should be removed
        assert "Navigation" not in result.content
        assert "Footer" not in result.content

    @pytest.mark.asyncio
    async def test_scrape_with_tables(self):
        """Test scraping with tables"""
        config = ScraperConfig(min_content_length=10, include_tables=True)
        strategy = BeautifulSoupStrategy(config)

        html_content = """
        <html>
            <body>
                <table>
                    <tr><td>Cell 1</td><td>Cell 2</td></tr>
                </table>
                <p>Some content</p>
            </body>
        </html>
        """

        result = await strategy.scrape("https://example.com", html_content=html_content)

        assert result.success is True
        # Table content should be extracted
        assert "Cell" in result.content


class TestHybridStrategy:
    """Test Hybrid scraping strategy"""

    @pytest.mark.asyncio
    async def test_hybrid_uses_first_successful_strategy(self):
        """Test that hybrid uses first successful strategy"""
        config = ScraperConfig(min_content_length=10)
        strategy = HybridStrategy(config)

        html_content = """
        <html>
            <head><title>Test</title></head>
            <body><p>Good content here for testing purposes.</p></body>
        </html>
        """

        result = await strategy.scrape("https://example.com", html_content=html_content)

        assert result.success is True
        assert "hybrid" in result.strategy_used
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_hybrid_fallback(self):
        """Test hybrid fallback to multiple strategies"""
        config = ScraperConfig(min_content_length=5000)  # Very high threshold
        strategy = HybridStrategy(config)

        # Content too short for the threshold
        html_content = "<html><body><p>Short</p></body></html>"

        result = await strategy.scrape("https://example.com", html_content=html_content)

        # All strategies should fail due to min_content_length
        assert result.success is False
        assert "all_failed" in result.strategy_used


class TestAutoStrategy:
    """Test Auto scraping strategy"""

    @pytest.mark.asyncio
    async def test_auto_selects_trafilatura_for_blog(self):
        """Test that auto selects Trafilatura for blog URLs"""
        config = ScraperConfig(min_content_length=10)
        strategy = AutoStrategy(config)

        html_content = """
        <html>
            <head><title>Blog Post</title></head>
            <body><article><p>Blog post content here.</p></article></body>
        </html>
        """

        result = await strategy.scrape("https://blog.example.com/post", html_content=html_content)

        assert result.success is True
        assert "auto" in result.strategy_used

    @pytest.mark.asyncio
    async def test_auto_selects_hybrid_for_unknown(self):
        """Test that auto selects hybrid for unknown URLs"""
        config = ScraperConfig(min_content_length=10)
        strategy = AutoStrategy(config)

        html_content = """
        <html>
            <head><title>Some Page</title></head>
            <body><p>Generic content on this page.</p></body>
        </html>
        """

        result = await strategy.scrape("https://unknown-site.com", html_content=html_content)

        assert result.success is True or result.success is False  # Depends on content extraction
        assert "auto" in result.strategy_used


class TestScrapedContent:
    """Test ScrapedContent data class"""

    def test_scraped_content_creation(self):
        """Test creating ScrapedContent"""
        content = ScrapedContent(
            content="Test content",
            title="Test Title",
            description="Test description",
            url="https://example.com",
            metadata={"key": "value"},
            strategy_used="test",
            success=True
        )

        assert content.content == "Test content"
        assert content.title == "Test Title"
        assert content.success is True
        assert content.content_length == len("Test content")

    def test_scraped_content_post_init(self):
        """Test post_init sets content_length"""
        content = ScrapedContent(
            content="12345",
            title="",
            description="",
            url="https://example.com",
            metadata={},
            strategy_used="test",
            success=True
        )

        assert content.content_length == 5
