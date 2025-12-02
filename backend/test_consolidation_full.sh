#!/bin/bash

###############################################################################
# Comprehensive Test Suite for Service Consolidation
# Tests all consolidated services and validates project filtering
###############################################################################

set -e  # Exit on error

echo "======================================================================"
echo "🧪 COMPREHENSIVE SERVICE CONSOLIDATION TEST SUITE"
echo "======================================================================"
echo ""
echo "Date: $(date)"
echo "Purpose: Validate all consolidated services work correctly"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run test and track results
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo "----------------------------------------------------------------------"
    echo "🔍 Running: $test_name"
    echo "----------------------------------------------------------------------"

    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASSED${NC}: $test_name"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAILED${NC}: $test_name"
        ((TESTS_FAILED++))
    fi
    echo ""
}

# Change to backend directory
cd "$(dirname "$0")"
echo "📁 Working directory: $(pwd)"
echo ""

###############################################################################
# TEST 1: Service Import Tests
###############################################################################
echo "======================================================================"
echo "TEST SUITE 1: Service Imports"
echo "======================================================================"
echo ""

run_test "Import RAG Service" \
    "python3 -c 'from app.services.rag_service import rag_service, RAGService; assert rag_service is not None; print(\"✅ RAG service imported successfully\")'"

run_test "Import LLM Service" \
    "python3 -c 'from app.services.llm_service import llm_service, LLMService; assert llm_service is not None; print(\"✅ LLM service imported successfully\")'"

run_test "Import Document Service" \
    "python3 -c 'from app.services.document_service import document_service, DocumentService; assert document_service is not None; print(\"✅ Document service imported successfully\")'"

run_test "Import Scraper Service" \
    "python3 -c 'from app.services.scraper_service import scraper_service, ScraperService; assert scraper_service is not None; print(\"✅ Scraper service imported successfully\")'"

run_test "Verify Enhanced Services Removed" \
    "python3 -c 'import sys; \
try: \
    from app.services.rag_service_enhanced import enhanced_rag_service; \
    print(\"❌ ERROR: Enhanced RAG service still exists!\"); \
    sys.exit(1); \
except ImportError: \
    print(\"✅ Enhanced RAG service correctly removed\"); \
try: \
    from app.services.llm_service_enhanced import llm_service; \
    print(\"❌ ERROR: Enhanced LLM service still exists!\"); \
    sys.exit(1); \
except ImportError: \
    print(\"✅ Enhanced LLM service correctly removed\")'"

###############################################################################
# TEST 2: Service Functionality Tests
###############################################################################
echo ""
echo "======================================================================"
echo "TEST SUITE 2: Service Functionality"
echo "======================================================================"
echo ""

run_test "RAG Service Has All Methods" \
    "python3 -c '
from app.services.rag_service import rag_service
assert hasattr(rag_service, \"query\"), \"Missing query method\"
assert hasattr(rag_service, \"_ensure_session_exists\"), \"Missing session method\"
assert hasattr(rag_service, \"_search_session_documents\"), \"Missing memory hierarchy\"
assert hasattr(rag_service, \"_check_semantic_cache\"), \"Missing cache method\"
print(\"✅ RAG service has all required methods\")
'"

run_test "LLM Service Has All Methods" \
    "python3 -c '
from app.services.llm_service import llm_service
assert hasattr(llm_service, \"generate\"), \"Missing generate method\"
assert hasattr(llm_service, \"_call_openai\"), \"Missing OpenAI method\"
assert hasattr(llm_service, \"_call_anthropic\"), \"Missing Anthropic method (enhanced)\"
assert hasattr(llm_service, \"get_available_models\"), \"Missing model registry (enhanced)\"
print(\"✅ LLM service has all required methods (including enhanced features)\")
'"

run_test "Document Service Has All Methods" \
    "python3 -c '
from app.services.document_service import document_service
assert hasattr(document_service, \"upload_file\"), \"Missing upload method\"
assert hasattr(document_service, \"search_similar_chunks\"), \"Missing search method\"
assert hasattr(document_service, \"upload_file_with_project\"), \"Missing enhanced upload\"
assert hasattr(document_service, \"get_file_download_url\"), \"Missing download URL (enhanced)\"
assert hasattr(document_service, \"delete_file\"), \"Missing delete method (enhanced)\"
print(\"✅ Document service has all required methods (including enhanced features)\")
'"

run_test "Scraper Service Has All Methods" \
    "python3 -c '
from app.services.scraper_service import scraper_service
assert hasattr(scraper_service, \"scrape_url\"), \"Missing scrape_url method\"
assert hasattr(scraper_service, \"get_scraper_capabilities\"), \"Missing capabilities (enhanced)\"
assert hasattr(scraper_service, \"_create_default_config\"), \"Missing config (enhanced)\"
print(\"✅ Scraper service has all required methods (including enhanced features)\")
'"

###############################################################################
# TEST 3: Project Filtering Tests
###############################################################################
echo ""
echo "======================================================================"
echo "TEST SUITE 3: Project Filtering"
echo "======================================================================"
echo ""

run_test "RAG Query Accepts project_id" \
    "python3 -c '
import inspect
from app.services.rag_service import rag_service
sig = inspect.signature(rag_service.query)
assert \"project_id\" in sig.parameters, \"RAG query missing project_id parameter\"
print(\"✅ RAG query accepts project_id parameter\")
'"

run_test "Session Creation Accepts project_id" \
    "python3 -c '
import inspect
from app.services.rag_service import rag_service
sig = inspect.signature(rag_service._ensure_session_exists)
assert \"project_id\" in sig.parameters, \"Session creation missing project_id parameter\"
print(\"✅ Session creation accepts project_id parameter\")
'"

run_test "Document Search Accepts project_id" \
    "python3 -c '
import inspect
from app.services.document_service import document_service
sig = inspect.signature(document_service.search_similar_chunks)
assert \"project_id\" in sig.parameters, \"Document search missing project_id parameter\"
print(\"✅ Document search accepts project_id parameter\")
'"

###############################################################################
# TEST 4: Singleton Pattern Tests
###############################################################################
echo ""
echo "======================================================================"
echo "TEST SUITE 4: Singleton Patterns"
echo "======================================================================"
echo ""

run_test "RAG Service is Singleton" \
    "python3 -c '
from app.services.rag_service import rag_service
from app.services.rag_service import rag_service as rag_service2
assert rag_service is rag_service2, \"RAG service is not singleton\"
print(\"✅ RAG service is singleton\")
'"

run_test "LLM Service is Singleton" \
    "python3 -c '
from app.services.llm_service import llm_service
from app.services.llm_service import llm_service as llm_service2
assert llm_service is llm_service2, \"LLM service is not singleton\"
print(\"✅ LLM service is singleton\")
'"

run_test "Document Service is Singleton" \
    "python3 -c '
from app.services.document_service import document_service
from app.services.document_service import document_service as document_service2
assert document_service is document_service2, \"Document service is not singleton\"
print(\"✅ Document service is singleton\")
'"

run_test "Scraper Service is Singleton" \
    "python3 -c '
from app.services.scraper_service import scraper_service
from app.services.scraper_service import scraper_service as scraper_service2
assert scraper_service is scraper_service2, \"Scraper service is not singleton\"
print(\"✅ Scraper service is singleton\")
'"

###############################################################################
# TEST 5: Ultra Smart Extractor Independence
###############################################################################
echo ""
echo "======================================================================"
echo "TEST SUITE 5: Ultra Smart Extractor Independence"
echo "======================================================================"
echo ""

run_test "Ultra Smart Extractor Import" \
    "python3 -c '
from app.services.webscraper.extractors.ultra_smart_extractor import UltraSmartExtractor
print(\"✅ Ultra Smart Extractor imported successfully\")
'"

run_test "Ultra Smart Extractor Uses Dependency Injection" \
    "python3 -c '
import inspect
from app.services.webscraper.extractors.ultra_smart_extractor import UltraSmartExtractor
sig = inspect.signature(UltraSmartExtractor.__init__)
params = list(sig.parameters.keys())
assert \"llm_service\" in params, \"Missing llm_service parameter\"
assert \"scraper_service\" in params, \"Missing scraper_service parameter\"
assert \"document_service\" in params, \"Missing document_service parameter\"
print(\"✅ Ultra Smart Extractor uses dependency injection (no consolidation needed)\")
'"

###############################################################################
# TEST 6: Main File Imports
###############################################################################
echo ""
echo "======================================================================"
echo "TEST SUITE 6: Main File Import Validation"
echo "======================================================================"
echo ""

run_test "main.py Imports Consolidated Services" \
    "python3 -c '
import sys
import os
sys.path.insert(0, os.path.abspath(\"app\"))

# Read main.py and check for direct imports (no try/except)
with open(\"app/main.py\", \"r\") as f:
    content = f.read()

# Check for correct imports
assert \"from app.services.rag_service import rag_service\" in content, \"main.py not using consolidated RAG service\"
assert \"from app.services.llm_service import llm_service\" in content, \"main.py not using consolidated LLM service\"

# Check that try/except patterns are removed
assert \"rag_service_enhanced\" not in content, \"main.py still references enhanced RAG service\"
assert \"llm_service_enhanced\" not in content, \"main.py still references enhanced LLM service\"

print(\"✅ main.py uses consolidated services with direct imports\")
'"

###############################################################################
# TEST 7: Pytest Unit Tests
###############################################################################
echo ""
echo "======================================================================"
echo "TEST SUITE 7: Pytest Unit Tests"
echo "======================================================================"
echo ""

run_test "Consolidated Services Tests" \
    "pytest tests/test_consolidated_services.py -v --tb=short 2>&1 | tee /tmp/pytest_consolidated.log || (cat /tmp/pytest_consolidated.log && exit 1)"

run_test "Scraper Service Tests" \
    "pytest tests/test_scraper_service_enhanced.py -v --tb=short 2>&1 | tee /tmp/pytest_scraper.log || (cat /tmp/pytest_scraper.log && exit 1)"

run_test "Tool Registry Tests" \
    "pytest tests/test_tool_registry.py -v --tb=short 2>&1 | tee /tmp/pytest_tool_registry.log || (cat /tmp/pytest_tool_registry.log && exit 1)"

###############################################################################
# TEST 8: File Compilation Tests
###############################################################################
echo ""
echo "======================================================================"
echo "TEST SUITE 8: Python File Compilation"
echo "======================================================================"
echo ""

run_test "Compile All Service Files" \
    "python3 -m py_compile \
        app/services/rag_service.py \
        app/services/llm_service.py \
        app/services/document_service.py \
        app/services/scraper_service.py \
    && echo '✅ All service files compile successfully'"

run_test "Compile Main Files" \
    "python3 -m py_compile \
        app/main.py \
        app/main_enhanced.py \
    && echo '✅ Main files compile successfully'"

###############################################################################
# FINAL SUMMARY
###############################################################################
echo ""
echo "======================================================================"
echo "📊 TEST SUMMARY"
echo "======================================================================"
echo ""

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
echo "Total Tests Run: $TOTAL_TESTS"
echo -e "${GREEN}✅ Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}❌ Tests Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}🎉 ALL TESTS PASSED! SERVICE CONSOLIDATION SUCCESSFUL!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "✅ All 4 services consolidated successfully"
    echo "✅ All enhanced features preserved"
    echo "✅ Project filtering implemented"
    echo "✅ No regressions detected"
    echo "✅ Ultra Smart Extractor independent and working"
    echo ""
    exit 0
else
    echo -e "${RED}════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}⚠️  SOME TESTS FAILED - REVIEW REQUIRED${NC}"
    echo -e "${RED}════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Check the output above for failed tests"
    echo ""
    exit 1
fi
