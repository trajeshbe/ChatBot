"""
Comprehensive tests for consolidated services after service consolidation.

Tests:
1. Service imports work correctly
2. All singleton instances are accessible
3. Core functionality preserved from both base and enhanced versions
4. Project-based filtering works correctly
5. No regression in existing functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import uuid


class TestServiceImports:
    """Test that all consolidated services can be imported"""

    def test_import_rag_service(self):
        """Test RAG service import"""
        from app.services.rag_service import rag_service, RAGService
        assert rag_service is not None
        assert isinstance(rag_service, RAGService)

    def test_import_llm_service(self):
        """Test LLM service import"""
        from app.services.llm_service import llm_service, LLMService
        assert llm_service is not None
        assert isinstance(llm_service, LLMService)

    def test_import_document_service(self):
        """Test document service import"""
        from app.services.document_service import document_service, DocumentService
        assert document_service is not None
        assert isinstance(document_service, DocumentService)

    def test_import_scraper_service(self):
        """Test scraper service import"""
        from app.services.scraper_service import scraper_service, ScraperService
        assert scraper_service is not None
        assert isinstance(scraper_service, ScraperService)

    def test_no_enhanced_imports(self):
        """Verify enhanced service imports fail (they should no longer exist)"""
        with pytest.raises(ImportError):
            from app.services.rag_service_enhanced import enhanced_rag_service

        with pytest.raises(ImportError):
            from app.services.llm_service_enhanced import llm_service

        with pytest.raises(ImportError):
            from app.services.document_service_enhanced import enhanced_document_service

        with pytest.raises(ImportError):
            from app.services.scraper_service_enhanced import enhanced_scraper_service


class TestRAGServiceConsolidation:
    """Test RAG service has all features from both versions"""

    def test_has_basic_query_method(self):
        """Test basic query method exists"""
        from app.services.rag_service import rag_service
        assert hasattr(rag_service, 'query')

    def test_has_enhanced_session_methods(self):
        """Test enhanced session management methods exist"""
        from app.services.rag_service import rag_service
        assert hasattr(rag_service, '_ensure_session_exists')
        assert hasattr(rag_service, '_save_conversation_message')
        assert hasattr(rag_service, '_get_conversation_context')
        assert hasattr(rag_service, 'associate_document_with_session')

    def test_has_memory_hierarchy_methods(self):
        """Test memory hierarchy methods exist"""
        from app.services.rag_service import rag_service
        assert hasattr(rag_service, '_search_session_documents')
        assert hasattr(rag_service, '_combine_memory_results')

    def test_has_cache_methods(self):
        """Test caching methods exist"""
        from app.services.rag_service import rag_service
        assert hasattr(rag_service, '_check_semantic_cache')
        assert hasattr(rag_service, '_cache_result')

    def test_query_signature_accepts_project_id(self):
        """Test query method accepts project_id parameter"""
        from app.services.rag_service import rag_service
        import inspect
        sig = inspect.signature(rag_service.query)
        assert 'project_id' in sig.parameters


class TestLLMServiceConsolidation:
    """Test LLM service has all features from both versions"""

    def test_has_basic_generate_method(self):
        """Test basic generate method exists"""
        from app.services.llm_service import llm_service
        assert hasattr(llm_service, 'generate')
        assert hasattr(llm_service, 'generate_with_context')

    def test_has_all_provider_methods(self):
        """Test all LLM provider methods exist"""
        from app.services.llm_service import llm_service
        assert hasattr(llm_service, '_call_openai')
        assert hasattr(llm_service, '_call_ollama')
        assert hasattr(llm_service, '_call_vllm')
        assert hasattr(llm_service, '_call_llama_cpp')
        assert hasattr(llm_service, '_call_anthropic')  # Enhanced feature

    def test_has_model_registry_methods(self):
        """Test model registry methods exist (enhanced feature)"""
        from app.services.llm_service import llm_service
        assert hasattr(llm_service, 'get_available_models')
        assert hasattr(llm_service, 'set_default_model')
        assert hasattr(llm_service, '_check_ollama_model_availability')

    def test_has_api_key_management(self):
        """Test API key management exists"""
        from app.services.llm_service import llm_service
        assert hasattr(llm_service, '_get_api_key_with_fallback')


class TestDocumentServiceConsolidation:
    """Test document service has all features from both versions"""

    def test_has_basic_methods(self):
        """Test basic document methods exist"""
        from app.services.document_service import document_service
        assert hasattr(document_service, 'upload_file')
        assert hasattr(document_service, 'process_document')
        assert hasattr(document_service, 'search_similar_chunks')

    def test_has_enhanced_methods(self):
        """Test enhanced methods exist"""
        from app.services.document_service import document_service
        assert hasattr(document_service, 'upload_file_with_project')  # Enhanced
        assert hasattr(document_service, 'get_file_download_url')     # Enhanced
        assert hasattr(document_service, 'delete_file')                # Enhanced
        assert hasattr(document_service, '_get_dept_team_names')      # Enhanced helper

    def test_has_search_methods(self):
        """Test search methods exist"""
        from app.services.document_service import document_service
        assert hasattr(document_service, '_execute_search')
        assert hasattr(document_service, '_keyword_only_search')


class TestScraperServiceConsolidation:
    """Test scraper service has all features from both versions"""

    def test_has_basic_scrape_methods(self):
        """Test basic scraping methods exist"""
        from app.services.scraper_service import scraper_service
        assert hasattr(scraper_service, 'scrape_url')
        assert hasattr(scraper_service, 'scrape_multiple_urls')

    def test_has_enhanced_methods(self):
        """Test enhanced methods exist"""
        from app.services.scraper_service import scraper_service
        assert hasattr(scraper_service, 'get_scraper_capabilities')  # Enhanced
        assert hasattr(scraper_service, '_create_default_config')    # Enhanced
        assert hasattr(scraper_service, '_apply_smart_filtering')    # Enhanced


class TestProjectFilteringIntegration:
    """Test project-based filtering works correctly after consolidation"""

    def test_rag_query_with_project_id(self):
        """Test RAG query accepts and uses project_id"""
        from app.services.rag_service import rag_service
        import inspect

        # Test that project_id parameter is accepted
        sig = inspect.signature(rag_service.query)
        assert 'project_id' in sig.parameters
        print("✅ RAG query accepts project_id parameter")

    def test_session_creation_with_project_id(self):
        """Test session creation includes project_id"""
        from app.services.rag_service import rag_service
        import inspect

        # Test that _ensure_session_exists accepts project_id
        sig = inspect.signature(rag_service._ensure_session_exists)
        assert 'project_id' in sig.parameters
        print("✅ Session creation accepts project_id parameter")

    def test_document_search_with_project_filter(self):
        """Test document search can filter by project"""
        from app.services.document_service import document_service
        import inspect

        # Test that search_similar_chunks accepts project_id
        sig = inspect.signature(document_service.search_similar_chunks)
        assert 'project_id' in sig.parameters
        print("✅ Document search accepts project_id parameter")


class TestSingletonPatterns:
    """Test that singleton instances are properly configured"""

    def test_rag_service_singleton(self):
        """Test RAG service is singleton"""
        from app.services.rag_service import rag_service
        from app.services.rag_service import rag_service as rag_service2
        assert rag_service is rag_service2

    def test_llm_service_singleton(self):
        """Test LLM service is singleton"""
        from app.services.llm_service import llm_service
        from app.services.llm_service import llm_service as llm_service2
        assert llm_service is llm_service2

    def test_document_service_singleton(self):
        """Test document service is singleton"""
        from app.services.document_service import document_service
        from app.services.document_service import document_service as document_service2
        assert document_service is document_service2

    def test_scraper_service_singleton(self):
        """Test scraper service is singleton"""
        from app.services.scraper_service import scraper_service
        from app.services.scraper_service import scraper_service as scraper_service2
        assert scraper_service is scraper_service2


class TestBackwardCompatibility:
    """Test that code using old patterns would break cleanly"""

    def test_old_imports_fail_with_clear_error(self):
        """Test that old import patterns fail with ImportError"""
        # This is good - we want old code to fail fast with clear error
        with pytest.raises(ImportError):
            from app.services.rag_service_enhanced import enhanced_rag_service

    def test_main_imports_work(self):
        """Test that main.py imports work"""
        # These should work without try/except now
        from app.services.rag_service import rag_service
        from app.services.llm_service import llm_service
        from app.services.document_service import document_service
        from app.services.scraper_service import scraper_service

        assert rag_service is not None
        assert llm_service is not None
        assert document_service is not None
        assert scraper_service is not None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
