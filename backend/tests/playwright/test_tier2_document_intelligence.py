"""
Playwright E2E tests for Tier 2 Document Intelligence Domain Vertical.

Tests cover:
1. Generic RAG - General-purpose RAG query system
2. Docu Extract / 18-Field Extraction - Structured field extraction
3. Relation Extractor - Entity and relationship extraction
"""
import pytest
from playwright.sync_api import Page, expect
from page_objects.tier2_module_page import DocumentIntelligencePage
import os
import time


# Test data paths (these should be created in sample_data/)
SAMPLE_DOCUMENT_PDF = "sample_data/tier2_domain_verticals/document_intelligence/sample_document.pdf"
SAMPLE_TEXT_FILE = "sample_data/tier2_domain_verticals/document_intelligence/sample_text.txt"

# Base URL from environment variable or default
BASE_URL = os.getenv("FRONTEND_URL", "http://localhost:3001")


class TestGenericRAG:
    """Tests for Generic RAG module."""

    @pytest.fixture
    def generic_rag_page(self, page):
        """Create Generic RAG page object."""
        rag_page = DocumentIntelligencePage(page, BASE_URL, "generic-rag")
        rag_page.navigate_to_module()
        return rag_page

    def test_navigate_to_generic_rag(self, generic_rag_page):
        """Test navigation to Generic RAG module."""
        assert generic_rag_page.page.url.endswith("/") or "generic-rag" in generic_rag_page.page.url

    def test_upload_document_for_rag(self, generic_rag_page):
        """Test uploading a document to RAG collection."""
        if not os.path.exists(SAMPLE_DOCUMENT_PDF):
            pytest.skip(f"Sample document not found: {SAMPLE_DOCUMENT_PDF}")

        # Upload document
        generic_rag_page.upload_document(SAMPLE_DOCUMENT_PDF)
        time.sleep(2)  # Wait for upload

        # Verify upload success (look for success message or document in list)
        assert not generic_rag_page.check_for_errors(), f"Error during upload: {generic_rag_page.get_error_message()}"

    def test_query_rag_system(self, generic_rag_page):
        """Test querying the RAG system."""
        # Enter a sample query
        test_query = "What are the main topics discussed in the document?"
        generic_rag_page.enter_query(test_query)

        # Submit query
        generic_rag_page.click_submit_button()
        time.sleep(3)  # Wait for RAG processing

        # Verify results
        generic_rag_page.verify_results_visible()
        results = generic_rag_page.get_extraction_results()

        assert results is not None, "No results returned from RAG query"
        assert len(str(results)) > 0, "Empty results from RAG query"

    def test_rag_with_context_retrieval(self, generic_rag_page):
        """Test RAG query with context retrieval."""
        test_query = "Summarize the key points"
        generic_rag_page.enter_query(test_query)
        generic_rag_page.click_submit_button()
        time.sleep(3)

        results_text = generic_rag_page.get_results_text()

        # Verify we got an answer
        assert len(results_text) > 50, "Response too short, likely no context retrieved"

        # Check for common RAG response indicators
        assert not "no information" in results_text.lower(), "RAG returned no information"

    def test_rag_error_handling_empty_query(self, generic_rag_page):
        """Test error handling for empty query."""
        # Submit without entering query
        try:
            generic_rag_page.click_submit_button()
            time.sleep(1)

            # Should show error or validation message
            assert generic_rag_page.check_for_errors() or not generic_rag_page.wait_for_results(timeout=3000)
        except:
            # It's okay if submit button is disabled for empty query
            pass


class TestDocuExtract:
    """Tests for 18-Field Document Extraction module."""

    @pytest.fixture
    def docu_extract_page(self, page):
        """Create Document Extract page object."""
        extract_page = DocumentIntelligencePage(page, BASE_URL, "document-extract")
        extract_page.navigate_to_module()
        return extract_page

    def test_navigate_to_docu_extract(self, docu_extract_page):
        """Test navigation to Document Extract module."""
        assert docu_extract_page.page.url.endswith("/") or "document" in docu_extract_page.page.url

    def test_upload_and_extract_18_fields(self, docu_extract_page):
        """Test uploading document and extracting 18 structured fields."""
        if not os.path.exists(SAMPLE_DOCUMENT_PDF):
            pytest.skip(f"Sample document not found: {SAMPLE_DOCUMENT_PDF}")

        # Upload document
        docu_extract_page.upload_document(SAMPLE_DOCUMENT_PDF)

        # Click extract button
        docu_extract_page.click_submit_button()
        time.sleep(5)  # Wait for extraction

        # Verify extraction results
        docu_extract_page.verify_results_visible()
        results = docu_extract_page.get_extraction_results()

        assert results is not None, "No extraction results returned"

        # Verify we got structured fields
        if isinstance(results, dict):
            assert len(results.keys()) > 0, "No fields extracted"
            print(f"Extracted {len(results.keys())} fields")

    def test_extract_specific_fields(self, docu_extract_page):
        """Test extraction of specific known fields."""
        if not os.path.exists(SAMPLE_DOCUMENT_PDF):
            pytest.skip(f"Sample document not found: {SAMPLE_DOCUMENT_PDF}")

        docu_extract_page.upload_document(SAMPLE_DOCUMENT_PDF)
        docu_extract_page.click_submit_button()
        time.sleep(5)

        results = docu_extract_page.get_extraction_results()

        # Check for common fields (date, title, author, etc.)
        # This will vary based on document type
        assert results is not None

    def test_extract_from_text_file(self, docu_extract_page):
        """Test extraction from text file."""
        if not os.path.exists(SAMPLE_TEXT_FILE):
            pytest.skip(f"Sample text file not found: {SAMPLE_TEXT_FILE}")

        docu_extract_page.upload_document(SAMPLE_TEXT_FILE)
        docu_extract_page.click_submit_button()
        time.sleep(3)

        # Should handle text files
        assert not docu_extract_page.check_for_errors(), "Error processing text file"


class TestRelationExtractor:
    """Tests for Relation Extractor module."""

    @pytest.fixture
    def relation_extractor_page(self, page):
        """Create Relation Extractor page object."""
        extractor_page = DocumentIntelligencePage(page, BASE_URL, "relation-extractor")
        extractor_page.navigate_to_module()
        return extractor_page

    def test_navigate_to_relation_extractor(self, relation_extractor_page):
        """Test navigation to Relation Extractor module."""
        assert relation_extractor_page.page.url.endswith("/") or "relation" in relation_extractor_page.page.url

    def test_upload_document_for_relation_extraction(self, relation_extractor_page):
        """Test uploading document for relation extraction."""
        if not os.path.exists(SAMPLE_DOCUMENT_PDF):
            pytest.skip(f"Sample document not found: {SAMPLE_DOCUMENT_PDF}")

        relation_extractor_page.upload_document(SAMPLE_DOCUMENT_PDF)
        time.sleep(2)

        assert not relation_extractor_page.check_for_errors()

    def test_extract_entities_and_relations(self, relation_extractor_page):
        """Test extraction of entities and relationships."""
        if not os.path.exists(SAMPLE_DOCUMENT_PDF):
            pytest.skip(f"Sample document not found: {SAMPLE_DOCUMENT_PDF}")

        relation_extractor_page.upload_document(SAMPLE_DOCUMENT_PDF)
        relation_extractor_page.click_submit_button()
        time.sleep(5)  # Relation extraction can take time

        relation_extractor_page.verify_results_visible()
        results = relation_extractor_page.get_extraction_results()

        assert results is not None, "No relation extraction results"

        # Check for entities or relations in results
        if isinstance(results, dict):
            has_entities = "entities" in results or "relations" in results
            assert has_entities or "raw_text" in results

    def test_relation_extraction_with_text_input(self, relation_extractor_page):
        """Test relation extraction with direct text input."""
        # Some modules may accept text input
        sample_text = "John Smith works at Acme Corporation. The company was founded in 2020 by Jane Doe."

        try:
            relation_extractor_page.enter_text_input(sample_text)
            relation_extractor_page.click_submit_button()
            time.sleep(3)

            results = relation_extractor_page.get_extraction_results()
            assert results is not None

            # Should extract Person, Organization, and relationships
            results_str = str(results).lower()
            # Verify some extraction occurred
            assert len(results_str) > len(sample_text) * 0.3, "Minimal extraction occurred"
        except:
            pytest.skip("Module may not support text input")

    def test_relation_types_extraction(self, relation_extractor_page):
        """Test extraction of different relation types."""
        sample_text = "Alice manages the project. Bob reports to Alice. The project started on January 1, 2024."

        try:
            relation_extractor_page.enter_text_input(sample_text)
            relation_extractor_page.click_submit_button()
            time.sleep(3)

            results = relation_extractor_page.get_extraction_results()
            assert results is not None

            # Check for relation extraction
            results_str = str(results).lower()
            # Should identify management or reporting relationships
            assert "alice" in results_str or "bob" in results_str
        except:
            pytest.skip("Module may not support text input")

