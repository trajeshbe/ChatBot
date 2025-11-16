"""
Tests for enhanced scraper service.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from app.services.scraper_service_enhanced import EnhancedScraperService
from app.services.scraper_strategies import ScraperConfig, ScraperStrategy


@pytest.fixture
def scraper_service():
    """Create enhanced scraper service instance"""
    return EnhancedScraperService()


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


class TestEnhancedScraperService:
    """Test enhanced scraper service"""

    def test_create_default_config(self, scraper_service):
        """Test creating default configuration"""
        config = scraper_service._create_default_config()

        assert isinstance(config, ScraperConfig)
        assert config.strategy == ScraperStrategy.AUTO
        assert config.timeout > 0
        assert config.max_retries > 0

    @pytest.mark.asyncio
    async def test_scrape_url_disabled(self, scraper_service, mock_db_session):
        """Test scraping when feature is disabled"""
        with patch('app.services.scraper_service_enhanced.settings') as mock_settings:
            mock_settings.ENABLE_WEB_SCRAPING = False

            with pytest.raises(ValueError, match="Web scraping is disabled"):
                await scraper_service.scrape_url(
                    url="https://example.com",
                    db=mock_db_session
                )

    @pytest.mark.asyncio
    async def test_scrape_url_success(self, scraper_service, mock_db_session):
        """Test successful URL scraping"""
        with patch('app.services.scraper_service_enhanced.settings') as mock_settings:
            mock_settings.ENABLE_WEB_SCRAPING = True
            mock_settings.ENABLE_SMART_SCRAPING = False

            # Mock the strategy
            mock_strategy = AsyncMock()
            mock_scraped_content = Mock(
                success=True,
                content="Test content",
                title="Test Title",
                description="Test description",
                url="https://example.com",
                metadata={},
                strategy_used="auto(trafilatura)",
                content_length=100
            )
            mock_strategy.scrape = AsyncMock(return_value=mock_scraped_content)

            # Mock the factory
            with patch('app.services.scraper_service_enhanced.ScraperStrategyFactory') as mock_factory:
                mock_factory.create = Mock(return_value=mock_strategy)

                # Mock document service
                with patch('app.services.scraper_service_enhanced.document_service') as mock_doc_service:
                    mock_document = Mock(id="doc_123")
                    mock_doc_service.upload_file = AsyncMock(return_value=mock_document)
                    mock_doc_service.process_document = AsyncMock()

                    result = await scraper_service.scrape_url(
                        url="https://example.com",
                        db=mock_db_session
                    )

                    assert result['success'] is True
                    assert result['document_id'] == "doc_123"
                    assert result['title'] == "Test Title"
                    assert result['strategy_used'] == "auto(trafilatura)"

    @pytest.mark.asyncio
    async def test_scrape_url_with_custom_config(self, scraper_service, mock_db_session):
        """Test scraping with custom configuration"""
        custom_config = ScraperConfig(
            strategy=ScraperStrategy.BEAUTIFULSOUP,
            timeout=60.0,
            include_tables=True
        )

        with patch('app.services.scraper_service_enhanced.settings') as mock_settings:
            mock_settings.ENABLE_WEB_SCRAPING = True

            # Mock the strategy
            mock_strategy = AsyncMock()
            mock_scraped_content = Mock(
                success=True,
                content="Test content",
                title="Test",
                description="",
                url="https://example.com",
                metadata={},
                strategy_used="beautifulsoup",
                content_length=50
            )
            mock_strategy.scrape = AsyncMock(return_value=mock_scraped_content)

            with patch('app.services.scraper_service_enhanced.ScraperStrategyFactory') as mock_factory:
                mock_factory.create = Mock(return_value=mock_strategy)

                with patch('app.services.scraper_service_enhanced.document_service') as mock_doc_service:
                    mock_document = Mock(id="doc_456")
                    mock_doc_service.upload_file = AsyncMock(return_value=mock_document)
                    mock_doc_service.process_document = AsyncMock()

                    result = await scraper_service.scrape_url(
                        url="https://example.com",
                        config=custom_config,
                        db=mock_db_session
                    )

                    assert result['success'] is True
                    # Verify factory was called with custom config
                    mock_factory.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_scrape_url_failure(self, scraper_service, mock_db_session):
        """Test scraping failure"""
        with patch('app.services.scraper_service_enhanced.settings') as mock_settings:
            mock_settings.ENABLE_WEB_SCRAPING = True

            # Mock the strategy to fail
            mock_strategy = AsyncMock()
            mock_scraped_content = Mock(
                success=False,
                content="",
                title="",
                description="",
                url="https://example.com",
                metadata={},
                strategy_used="auto",
                error="Connection failed",
                content_length=0
            )
            mock_strategy.scrape = AsyncMock(return_value=mock_scraped_content)

            with patch('app.services.scraper_service_enhanced.ScraperStrategyFactory') as mock_factory:
                mock_factory.create = Mock(return_value=mock_strategy)

                with pytest.raises(Exception, match="Scraping failed"):
                    await scraper_service.scrape_url(
                        url="https://example.com",
                        db=mock_db_session
                    )

    @pytest.mark.asyncio
    async def test_scrape_multiple_urls(self, scraper_service, mock_db_session):
        """Test scraping multiple URLs"""
        urls = ["https://example.com/1", "https://example.com/2"]

        with patch('app.services.scraper_service_enhanced.settings') as mock_settings:
            mock_settings.ENABLE_WEB_SCRAPING = True
            mock_settings.SCRAPER_MAX_CONCURRENT_REQUESTS = 5
            mock_settings.SCRAPER_DELAY_BETWEEN_REQUESTS = 0  # No delay in tests

            # Mock individual scraping
            async def mock_scrape_url(url, **kwargs):
                return {
                    'success': True,
                    'url': url,
                    'document_id': f"doc_{url[-1]}",
                    'content_length': 100
                }

            with patch.object(scraper_service, 'scrape_url', side_effect=mock_scrape_url):
                results = await scraper_service.scrape_multiple_urls(
                    urls=urls,
                    db=mock_db_session
                )

                assert len(results) == 2
                assert all(r['success'] for r in results)

    @pytest.mark.asyncio
    async def test_scrape_multiple_urls_with_failure(self, scraper_service, mock_db_session):
        """Test scraping multiple URLs with some failures"""
        urls = ["https://example.com/1", "https://example.com/2"]

        with patch('app.services.scraper_service_enhanced.settings') as mock_settings:
            mock_settings.ENABLE_WEB_SCRAPING = True
            mock_settings.SCRAPER_MAX_CONCURRENT_REQUESTS = 5
            mock_settings.SCRAPER_DELAY_BETWEEN_REQUESTS = 0

            # Mock one success, one failure
            async def mock_scrape_url(url, **kwargs):
                if "1" in url:
                    return {'success': True, 'url': url, 'document_id': 'doc_1'}
                else:
                    raise Exception("Scraping failed")

            with patch.object(scraper_service, 'scrape_url', side_effect=mock_scrape_url):
                results = await scraper_service.scrape_multiple_urls(
                    urls=urls,
                    db=mock_db_session
                )

                assert len(results) == 2
                assert results[0]['success'] is True
                assert results[1]['success'] is False
                assert 'error' in results[1]

    @pytest.mark.asyncio
    async def test_apply_smart_filtering(self, scraper_service):
        """Test AI-powered smart filtering"""
        content = "This is a long article about AI and machine learning. " * 100
        prompt = "Extract information about AI"

        with patch('app.services.scraper_service_enhanced.llm_service') as mock_llm:
            mock_llm.generate_completion = AsyncMock(return_value={
                'content': 'Filtered content about AI'
            })

            filtered = await scraper_service._apply_smart_filtering(content, prompt)

            assert filtered == 'Filtered content about AI'
            mock_llm.generate_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_smart_filtering_fallback(self, scraper_service):
        """Test smart filtering fallback on error"""
        content = "Original content"
        prompt = "Extract something"

        with patch('app.services.scraper_service_enhanced.llm_service') as mock_llm:
            mock_llm.generate_completion = AsyncMock(side_effect=Exception("LLM error"))

            filtered = await scraper_service._apply_smart_filtering(content, prompt)

            # Should return original content on error
            assert filtered == content

    def test_format_document_content(self, scraper_service):
        """Test formatting scraped content as document"""
        from app.services.scraper_strategies import ScrapedContent

        scraped = ScrapedContent(
            content="Main content here",
            title="Test Title",
            description="Test description",
            url="https://example.com",
            metadata={'keywords': 'test, article'},
            strategy_used="test",
            success=True
        )

        formatted = scraper_service._format_document_content(scraped)

        assert "Title: Test Title" in formatted
        assert "URL: https://example.com" in formatted
        assert "Description: Test description" in formatted
        assert "Keywords: test, article" in formatted
        assert "Main content here" in formatted

    @pytest.mark.asyncio
    async def test_get_scraper_capabilities(self, scraper_service):
        """Test getting scraper capabilities"""
        with patch('app.services.scraper_service_enhanced.settings') as mock_settings:
            mock_settings.ENABLE_WEB_SCRAPING = True
            mock_settings.ENABLE_PLAYWRIGHT_SCRAPING = False
            mock_settings.ENABLE_SMART_SCRAPING = True
            mock_settings.SCRAPER_DEFAULT_STRATEGY = 'auto'
            mock_settings.SCRAPER_MAX_CONCURRENT_REQUESTS = 5
            mock_settings.SCRAPER_TIMEOUT = 30
            mock_settings.SCRAPER_MAX_RETRIES = 3
            mock_settings.SCRAPER_MIN_CONTENT_LENGTH = 100
            mock_settings.SCRAPER_ENABLE_JAVASCRIPT = False

            capabilities = await scraper_service.get_scraper_capabilities()

            assert capabilities['web_scraping_enabled'] is True
            assert capabilities['playwright_enabled'] is False
            assert capabilities['smart_scraping_enabled'] is True
            assert capabilities['default_strategy'] == 'auto'
            assert capabilities['max_concurrent_requests'] == 5
            assert len(capabilities['available_strategies']) > 0

    @pytest.mark.asyncio
    async def test_close(self, scraper_service):
        """Test closing HTTP client"""
        scraper_service.http_client.close = AsyncMock()

        await scraper_service.close()

        scraper_service.http_client.close.assert_called_once()
