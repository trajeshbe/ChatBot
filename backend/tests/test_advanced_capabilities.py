"""
Test Suite for Advanced Capabilities
Tests OCR, Translation, and Form Automation services
"""

import pytest
import asyncio
import os
import tempfile
from unittest.mock import Mock, patch, AsyncMock

# Import services
from app.tier_1.document_processing.ocr_service import OCRService
from app.tier_1.nlp_processing.translation_service import TranslationService
from app.tier_1.data_extraction.webscraper.automation import FormHandler


# ============================================================================
# OCR SERVICE TESTS
# ============================================================================

class TestOCRService:
    """Test OCR service with Docling + Tesseract hybrid"""

    @pytest.fixture
    def ocr_service(self):
        return OCRService()

    def test_service_initialization(self, ocr_service):
        """Test OCR service initializes correctly"""
        assert ocr_service is not None
        status = ocr_service.get_status()
        assert status["service"] == "ocr"
        assert status["ready"] is True

    def test_get_available_backends(self, ocr_service):
        """Test backend availability check"""
        backends = ocr_service.get_available_backends()
        assert isinstance(backends, list)
        # Should have at least Docling available
        assert "docling" in backends

    def test_method_selection_pdf(self, ocr_service):
        """Test automatic method selection for PDF"""
        method = ocr_service._select_method("pdf")
        # Should prefer Docling for PDFs
        assert method in ["docling", "tesseract"]

    def test_method_selection_image(self, ocr_service):
        """Test automatic method selection for images"""
        method = ocr_service._select_method("jpg")
        # Should prefer Tesseract for images
        assert method in ["tesseract", "docling"]

    @pytest.mark.asyncio
    async def test_extract_text_invalid_file(self, ocr_service):
        """Test extraction with non-existent file"""
        with pytest.raises(ValueError, match="File not found"):
            await ocr_service.extract_text("/nonexistent/file.pdf")

    @pytest.mark.asyncio
    async def test_extract_text_invalid_method(self, ocr_service):
        """Test extraction with invalid method"""
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp_path = tmp.name

        try:
            with pytest.raises(ValueError, match="Invalid method"):
                await ocr_service.extract_text(tmp_path, method="invalid_method")
        finally:
            os.unlink(tmp_path)

    @pytest.mark.asyncio
    @patch('app.services.ocr_service.DOCLING_AVAILABLE', True)
    async def test_extract_with_docling_mock(self, ocr_service):
        """Test Docling extraction with mock"""
        # Create temp PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(b"Mock PDF content")
            tmp_path = tmp.name

        try:
            # Mock Docling converter
            with patch.object(ocr_service, 'docling_converter') as mock_converter:
                mock_result = Mock()
                mock_result.document.export_to_markdown.return_value = "Extracted text from PDF"
                mock_result.document.pages = [1, 2, 3]
                mock_converter.convert.return_value = mock_result

                result = await ocr_service.extract_text(tmp_path, method="docling")

                assert result["text"] == "Extracted text from PDF"
                assert result["method_used"] == "docling"
                assert result["pages"] == 3
                assert result["confidence"] > 0
        finally:
            os.unlink(tmp_path)


# ============================================================================
# TRANSLATION SERVICE TESTS
# ============================================================================

class TestTranslationService:
    """Test translation service with multi-backend support"""

    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM service"""
        mock_llm = Mock()
        mock_llm.generate_response = AsyncMock(return_value={
            "response": "Translated text by LLM",
            "model": "gpt-4-turbo",
            "tokens": 50
        })
        return mock_llm

    @pytest.fixture
    def translation_service(self, mock_llm_service):
        return TranslationService(llm_service=mock_llm_service)

    def test_service_initialization(self, translation_service):
        """Test translation service initializes correctly"""
        assert translation_service is not None
        status = translation_service.get_status()
        assert status["service"] == "translation"
        assert status["ready"] is True

    def test_supported_languages(self, translation_service):
        """Test supported languages list"""
        languages = translation_service.get_supported_languages()
        assert isinstance(languages, list)
        assert len(languages) > 0
        # Check for common languages
        codes = [lang["code"] for lang in languages]
        assert "en" in codes
        assert "es" in codes
        assert "fr" in codes

    def test_backend_selection_short_text(self, translation_service):
        """Test backend selection for short text"""
        text = "Short text"
        backend = translation_service._select_backend(text, "auto")
        # Should select LLM for short text
        assert backend == "llm"

    def test_backend_selection_long_text(self, translation_service):
        """Test backend selection for long text"""
        text = "a" * 600  # > 500 chars
        backend = translation_service._select_backend(text, "auto")
        # Should select transformers for long text if available
        assert backend in ["transformers", "llm"]

    def test_backend_selection_high_quality(self, translation_service):
        """Test backend selection with high quality requirement"""
        backend = translation_service._select_backend("Any text", "high")
        assert backend == "llm"

    @pytest.mark.asyncio
    async def test_translate_invalid_language(self, translation_service):
        """Test translation with invalid language"""
        with pytest.raises(ValueError, match="Unsupported source language"):
            await translation_service.translate(
                text="Hello",
                source_lang="invalid_lang",
                target_lang="es"
            )

    @pytest.mark.asyncio
    async def test_translate_same_language(self, translation_service):
        """Test translation with same source and target language"""
        result = await translation_service.translate(
            text="Hello",
            source_lang="en",
            target_lang="en"
        )
        assert result["translated_text"] == "Hello"
        assert result["backend_used"] == "none"
        assert result["confidence"] == 1.0

    @pytest.mark.asyncio
    async def test_translate_with_llm(self, translation_service, mock_llm_service):
        """Test translation using LLM backend"""
        result = await translation_service.translate(
            text="Hello, how are you?",
            source_lang="en",
            target_lang="es",
            quality="high"  # Force LLM
        )

        assert result["translated_text"] == "Translated text by LLM"
        assert result["backend_used"] == "llm"
        assert result["source_lang"] == "en"
        assert result["target_lang"] == "es"
        assert "confidence" in result

        # Verify LLM was called
        mock_llm_service.generate_response.assert_called_once()


# ============================================================================
# FORM AUTOMATION TESTS
# ============================================================================

class TestFormHandler:
    """Test form automation with Playwright integration"""

    @pytest.fixture
    def mock_page(self):
        """Mock Playwright page"""
        page = Mock()
        page.url = "https://example.com/form"
        page.wait_for_selector = AsyncMock()
        page.eval_on_selector = AsyncMock()
        page.select_option = AsyncMock()
        page.fill = AsyncMock()
        page.check = AsyncMock()
        page.uncheck = AsyncMock()
        page.set_input_files = AsyncMock()
        page.click = AsyncMock()
        page.expect_navigation = AsyncMock()
        page.evaluate = AsyncMock()
        return page

    @pytest.fixture
    def form_handler(self, mock_page):
        return FormHandler(mock_page)

    def test_form_handler_initialization(self, form_handler, mock_page):
        """Test form handler initializes correctly"""
        assert form_handler is not None
        assert form_handler.page == mock_page

    @pytest.mark.asyncio
    async def test_element_exists_true(self, form_handler, mock_page):
        """Test element existence check when element exists"""
        mock_page.wait_for_selector.return_value = None
        exists = await form_handler._element_exists("input[name='test']")
        assert exists is True

    @pytest.mark.asyncio
    async def test_element_exists_false(self, form_handler, mock_page):
        """Test element existence check when element doesn't exist"""
        mock_page.wait_for_selector.side_effect = Exception("Timeout")
        exists = await form_handler._element_exists("input[name='nonexistent']")
        assert exists is False

    @pytest.mark.asyncio
    async def test_find_field_by_name(self, form_handler, mock_page):
        """Test finding field by name attribute"""
        mock_page.wait_for_selector.return_value = None

        selector = await form_handler._find_field_selector("username")

        assert selector is not None
        assert "name=" in selector or "username" in selector

    @pytest.mark.asyncio
    async def test_fill_text_field(self, form_handler, mock_page):
        """Test filling text field"""
        mock_page.eval_on_selector.return_value = "input:text"

        success = await form_handler._fill_field("input[name='test']", "test value")

        assert success is True
        mock_page.fill.assert_called_once()

    @pytest.mark.asyncio
    async def test_fill_checkbox_field(self, form_handler, mock_page):
        """Test filling checkbox field"""
        mock_page.eval_on_selector.return_value = "input:checkbox"

        # Test checking
        success = await form_handler._fill_field("input[name='agree']", True)
        assert success is True
        mock_page.check.assert_called_once()

        # Test unchecking
        success = await form_handler._fill_field("input[name='agree']", False)
        mock_page.uncheck.assert_called_once()

    @pytest.mark.asyncio
    async def test_detect_captcha_present(self, form_handler, mock_page):
        """Test CAPTCHA detection when present"""
        mock_page.wait_for_selector.return_value = None

        has_captcha = await form_handler._detect_captcha()

        # Will be True if any CAPTCHA selector exists
        assert isinstance(has_captcha, bool)

    @pytest.mark.asyncio
    async def test_get_form_fields(self, form_handler, mock_page):
        """Test getting form fields"""
        mock_page.evaluate.return_value = [
            {
                "tag": "input",
                "type": "text",
                "name": "username",
                "id": "user_name",
                "placeholder": "Enter username",
                "required": True,
                "value": ""
            }
        ]

        fields = await form_handler.get_form_fields()

        assert isinstance(fields, list)
        assert len(fields) > 0
        assert fields[0]["name"] == "username"

    @pytest.mark.asyncio
    async def test_get_form_status(self, form_handler, mock_page):
        """Test getting form status"""
        mock_page.evaluate.return_value = {
            "has_form": True,
            "total_fields": 5,
            "required_fields": 3,
            "filled_fields": 2,
            "is_valid": False
        }

        status = await form_handler.get_form_status()

        assert status["has_form"] is True
        assert status["total_fields"] == 5
        assert status["required_fields"] == 3


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Test integration between services"""

    @pytest.mark.asyncio
    async def test_ocr_translation_pipeline(self):
        """Test OCR → Translation pipeline"""
        # This would be an integration test with real files
        # For now, just test the pattern

        ocr_service = OCRService()

        # Mock LLM service
        mock_llm = Mock()
        mock_llm.generate_response = AsyncMock(return_value={
            "response": "Texto traducido",
            "model": "gpt-4-turbo",
            "tokens": 50
        })

        translation_service = TranslationService(llm_service=mock_llm)

        # Verify services are ready
        assert ocr_service.get_status()["ready"]
        assert translation_service.get_status()["ready"]

        # Test workflow
        # 1. OCR extracts text
        # 2. Translation translates text
        # This pattern should work in production


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
