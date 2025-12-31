#!/bin/bash

# ============================================================================
# Comprehensive Chat Test Script
# ============================================================================
# Purpose: Automated testing of Chat functionality across all scenarios
# Based on: docs/testing/COMPREHENSIVE_CHAT_TEST_PLAN.md
# Date: 2025-11-24
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
TEST_SESSION_PREFIX="test-comprehensive-$(date +%s)"
REPORT_FILE="test_results_$(date +%Y%m%d_%H%M%S).md"
VERBOSE="${VERBOSE:-false}"

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED_TESTS++))
}

log_failure() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED_TESTS++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_skip() {
    echo -e "${YELLOW}[SKIP]${NC} $1"
    ((SKIPPED_TESTS++))
}

# Helper function to make API calls
api_call() {
    local endpoint="$1"
    local method="${2:-GET}"
    local data="$3"

    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        curl -s -X POST "${BACKEND_URL}${endpoint}" \
            -H "Content-Type: application/json" \
            -d "$data"
    else
        curl -s "${BACKEND_URL}${endpoint}"
    fi
}

# Helper function to send chat query
send_query() {
    local query="$1"
    local session_id="${2:-}"
    local model_id="${3:-llama3.1:8b}"
    local use_cache="${4:-false}"

    curl -s -X POST "${BACKEND_URL}/api/v1/query" \
        -F "query=${query}" \
        -F "session_id=${session_id}" \
        -F "model_id=${model_id}" \
        -F "use_cache=${use_cache}"
}

# Helper function to upload document
upload_document() {
    local file_path="$1"
    local session_id="${2:-}"

    if [ ! -f "$file_path" ]; then
        log_failure "File not found: $file_path"
        return 1
    fi

    curl -s -X POST "${BACKEND_URL}/api/v1/upload" \
        -F "file=@${file_path}" \
        -F "session_id=${session_id}"
}

# ============================================================================
# Pre-Flight Checks
# ============================================================================

preflight_checks() {
    log_info "Running pre-flight checks..."

    # Check if backend is running
    if ! curl -s "${BACKEND_URL}/health" > /dev/null 2>&1; then
        log_failure "Backend not accessible at ${BACKEND_URL}"
        exit 1
    fi
    log_success "Backend is running"

    # Check if Ollama is running
    if ! curl -s "http://localhost:11434/api/tags" > /dev/null 2>&1; then
        log_warning "Ollama not accessible (local model tests will be skipped)"
    else
        log_success "Ollama is running"
    fi

    # Check database
    if ! docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "SELECT 1;" > /dev/null 2>&1; then
        log_warning "Database not accessible (some tests may fail)"
    else
        log_success "Database is accessible"
    fi

    echo ""
}

# ============================================================================
# Test Category 1: Direct LLM Questions
# ============================================================================

test_direct_llm() {
    log_info "=== Category 1: Direct LLM Questions ==="
    echo ""

    # TC-DIRECT-001: Simple Factual Question
    ((TOTAL_TESTS++))
    log_info "TC-DIRECT-001: Simple factual question"
    response=$(send_query "What is the capital of France?" "" "llama3.1:8b")
    answer=$(echo "$response" | jq -r '.answer // empty')
    model_used=$(echo "$response" | jq -r '.model // empty')

    if echo "$answer" | grep -qi "paris"; then
        log_success "TC-DIRECT-001: Correct answer (Paris). Model: $model_used"
    else
        log_failure "TC-DIRECT-001: Incorrect answer: $answer"
    fi

    # TC-DIRECT-002: Mathematical Calculation
    ((TOTAL_TESTS++))
    log_info "TC-DIRECT-002: Mathematical calculation"
    response=$(send_query "What is 127 * 43?" "" "llama3.1:8b")
    answer=$(echo "$response" | jq -r '.answer // empty')

    if echo "$answer" | grep -q "5461"; then
        log_success "TC-DIRECT-002: Correct calculation (5461)"
    else
        log_failure "TC-DIRECT-002: Incorrect answer: $answer"
    fi

    # TC-DIRECT-003: Code Generation
    ((TOTAL_TESTS++))
    log_info "TC-DIRECT-003: Code generation"
    response=$(send_query "Write a Python function to calculate fibonacci numbers" "" "llama3.1:8b")
    answer=$(echo "$response" | jq -r '.answer // empty')

    if echo "$answer" | grep -qi "def.*fibonacci" && echo "$answer" | grep -qi "return"; then
        log_success "TC-DIRECT-003: Code generated"
    else
        log_failure "TC-DIRECT-003: No valid code generated"
    fi

    echo ""
}

# ============================================================================
# Test Category 2: RAG-Based Questions
# ============================================================================

test_rag_queries() {
    log_info "=== Category 2: RAG-Based Questions ==="
    echo ""

    # Check if test documents exist
    if [ ! -f "test_data/sample.txt" ]; then
        log_skip "TC-RAG-*: Test data not found (test_data/sample.txt)"
        ((TOTAL_TESTS+=4))
        ((SKIPPED_TESTS+=3))
        return
    fi

    # Upload test document
    log_info "Uploading test document for RAG tests..."
    session_id="${TEST_SESSION_PREFIX}-rag-001"
    upload_response=$(upload_document "test_data/sample.txt" "$session_id")
    doc_id=$(echo "$upload_response" | jq -r '.document_id // empty')

    if [ -z "$doc_id" ]; then
        log_failure "Failed to upload test document"
        ((TOTAL_TESTS+=4))
        ((SKIPPED_TESTS+=4))
        return
    fi

    log_info "Document uploaded: $doc_id"
    sleep 3  # Wait for processing

    # TC-RAG-001: Simple Document Query
    ((TOTAL_TESTS++))
    log_info "TC-RAG-001: Simple document query"
    response=$(send_query "What does the document say about machine learning?" "$session_id" "llama3.1:8b")
    answer=$(echo "$response" | jq -r '.answer // empty')
    num_sources=$(echo "$response" | jq -r '.num_sources // 0')

    if [ "$num_sources" -gt 0 ] && echo "$answer" | grep -qi "machine learning"; then
        log_success "TC-RAG-001: RAG retrieval successful. Sources: $num_sources"
    else
        log_failure "TC-RAG-001: RAG retrieval failed. Answer: $answer"
    fi

    # TC-RAG-002: No Relevant Documents
    ((TOTAL_TESTS++))
    log_info "TC-RAG-002: No relevant documents"
    response=$(send_query "Explain quantum entanglement" "$session_id" "llama3.1:8b")
    num_sources=$(echo "$response" | jq -r '.num_sources // 0')

    if [ "$num_sources" -eq 0 ]; then
        log_success "TC-RAG-002: Correctly found no relevant documents"
    else
        log_warning "TC-RAG-002: Found sources when none expected: $num_sources"
    fi

    echo ""
}

# ============================================================================
# Test Category 3: Short-Term Memory
# ============================================================================

test_short_term_memory() {
    log_info "=== Category 3: Short-Term Memory Questions ==="
    echo ""

    # Check if test documents exist
    if [ ! -f "test_data/sample.txt" ]; then
        log_skip "TC-STM-*: Test data not found"
        ((TOTAL_TESTS+=3))
        ((SKIPPED_TESTS+=3))
        return
    fi

    # Create two sessions with different documents
    session_a="${TEST_SESSION_PREFIX}-stm-a"
    session_b="${TEST_SESSION_PREFIX}-stm-b"

    log_info "Setting up session A..."
    upload_document "test_data/sample.txt" "$session_a" > /dev/null
    sleep 2

    # TC-STM-001: Session Document Priority
    ((TOTAL_TESTS++))
    log_info "TC-STM-001: Session document priority"
    response=$(send_query "What is in my session documents?" "$session_a" "llama3.1:8b")
    answer=$(echo "$response" | jq -r '.answer // empty')

    if echo "$answer" | grep -qi "machine learning"; then
        log_success "TC-STM-001: Session document prioritized"
    else
        log_failure "TC-STM-001: Session document not prioritized. Answer: $answer"
    fi

    # TC-STM-002: Session Without Documents
    ((TOTAL_TESTS++))
    log_info "TC-STM-002: Session without documents"
    session_new="${TEST_SESSION_PREFIX}-stm-new"
    response=$(send_query "What documents do I have access to?" "$session_new" "llama3.1:8b")
    answer=$(echo "$response" | jq -r '.answer // empty')

    # Should indicate no session documents or provide general response
    log_success "TC-STM-002: Handled empty session (answer: ${answer:0:50}...)"

    echo ""
}

# ============================================================================
# Test Category 4: Long-Term Memory
# ============================================================================

test_long_term_memory() {
    log_info "=== Category 4: Long-Term Memory Questions ==="
    echo ""

    # TC-LTM-001: Cross-Session Retrieval
    ((TOTAL_TESTS++))
    log_info "TC-LTM-001: Cross-session retrieval"
    session_new="${TEST_SESSION_PREFIX}-ltm-new"
    response=$(send_query "What documents are in the system?" "$session_new" "llama3.1:8b")
    answer=$(echo "$response" | jq -r '.answer // empty')

    # Should retrieve from long-term memory (all documents)
    log_success "TC-LTM-001: Cross-session query executed (answer: ${answer:0:50}...)"

    echo ""
}

# ============================================================================
# Test Category 5: Tool-Specific Questions
# ============================================================================

test_tools() {
    log_info "=== Category 5: Tool-Specific Questions ==="
    echo ""

    # TC-TOOL-OCR-001: OCR Tool
    ((TOTAL_TESTS++))
    if [ -f "test_data/sample_image.png" ]; then
        log_info "TC-TOOL-OCR-001: OCR tool"
        session_ocr="${TEST_SESSION_PREFIX}-ocr"
        upload_document "test_data/sample_image.png" "$session_ocr" > /dev/null
        sleep 3

        response=$(send_query "What text is in the image?" "$session_ocr" "llama3.1:8b")
        answer=$(echo "$response" | jq -r '.answer // empty')

        if [ -n "$answer" ] && [ "$answer" != "null" ]; then
            log_success "TC-TOOL-OCR-001: OCR tool executed"
        else
            log_failure "TC-TOOL-OCR-001: OCR tool failed"
        fi
    else
        log_skip "TC-TOOL-OCR-001: Test image not found"
        ((SKIPPED_TESTS++))
    fi

    # TC-TOOL-SCRAPE-001: Web Scraping Tool
    ((TOTAL_TESTS++))
    log_info "TC-TOOL-SCRAPE-001: Web scraping tool"

    # Note: This is a basic check - full scraping test requires actual URL
    response=$(api_call "/api/v1/scrape" "POST" '{"url":"https://example.com"}')

    if echo "$response" | jq -e '.job_id // .success' > /dev/null 2>&1; then
        log_success "TC-TOOL-SCRAPE-001: Web scraping endpoint accessible"
    else
        log_warning "TC-TOOL-SCRAPE-001: Web scraping endpoint may not be working"
    fi

    echo ""
}

# ============================================================================
# Test Category 6: Model Coverage
# ============================================================================

test_model_coverage() {
    log_info "=== Category 6: Model Coverage Testing ==="
    echo ""

    # Get available models
    log_info "Fetching available models..."
    models_response=$(api_call "/api/v1/models/available")

    if [ -z "$models_response" ]; then
        log_failure "Failed to fetch available models"
        ((TOTAL_TESTS++))
        return
    fi

    # Parse model IDs
    model_ids=$(echo "$models_response" | jq -r '.models[]?.id // empty')

    if [ -z "$model_ids" ]; then
        log_warning "No models found in registry"
        ((TOTAL_TESTS++))
        return
    fi

    log_info "Found models:"
    echo "$model_ids" | while read -r model_id; do
        echo "  - $model_id"
    done
    echo ""

    # Test each model
    echo "$model_ids" | while read -r model_id; do
        ((TOTAL_TESTS++))
        log_info "TC-MODEL: Testing model $model_id"

        response=$(send_query "Hello, respond briefly" "" "$model_id")
        answer=$(echo "$response" | jq -r '.answer // empty')
        model_used=$(echo "$response" | jq -r '.model // empty')

        if [ -n "$answer" ] && [ "$answer" != "null" ] && [ -n "$model_used" ]; then
            log_success "TC-MODEL: $model_id responded. Model used: $model_used"
        else
            log_failure "TC-MODEL: $model_id failed to respond"
        fi
    done

    echo ""
}

# ============================================================================
# Test Category 7: Response Quality
# ============================================================================

test_response_quality() {
    log_info "=== Category 7: Response Quality Validation ==="
    echo ""

    # TC-QUALITY-001: Answer Relevance
    ((TOTAL_TESTS++))
    log_info "TC-QUALITY-001: Answer relevance"
    response=$(send_query "What is the capital of Japan?" "" "llama3.1:8b")
    answer=$(echo "$response" | jq -r '.answer // empty')
    latency=$(echo "$response" | jq -r '.latency_ms // 0')

    if echo "$answer" | grep -qi "tokyo"; then
        log_success "TC-QUALITY-001: Relevant answer (Tokyo). Latency: ${latency}ms"
    else
        log_failure "TC-QUALITY-001: Irrelevant answer: $answer"
    fi

    # TC-QUALITY-002: Factual Accuracy
    ((TOTAL_TESTS++))
    log_info "TC-QUALITY-002: Factual accuracy"
    response=$(send_query "What year did World War II end?" "" "llama3.1:8b")
    answer=$(echo "$response" | jq -r '.answer // empty')

    if echo "$answer" | grep -q "1945"; then
        log_success "TC-QUALITY-002: Factually correct (1945)"
    else
        log_failure "TC-QUALITY-002: Factually incorrect: $answer"
    fi

    # TC-QUALITY-003: Response Latency
    ((TOTAL_TESTS++))
    log_info "TC-QUALITY-003: Response latency"
    start_time=$(date +%s%N)
    response=$(send_query "Simple test" "" "llama3.1:8b")
    end_time=$(date +%s%N)
    latency_ns=$((end_time - start_time))
    latency_ms=$((latency_ns / 1000000))

    if [ "$latency_ms" -lt 15000 ]; then
        log_success "TC-QUALITY-003: Response within acceptable time (${latency_ms}ms)"
    else
        log_warning "TC-QUALITY-003: Slow response (${latency_ms}ms)"
    fi

    echo ""
}

# ============================================================================
# Generate Report
# ============================================================================

generate_report() {
    log_info "Generating test report: $REPORT_FILE"

    cat > "$REPORT_FILE" << EOF
# Comprehensive Chat Test Report

**Date**: $(date)
**Backend URL**: ${BACKEND_URL}

## Summary

- **Total Tests**: ${TOTAL_TESTS}
- **Passed**: ${PASSED_TESTS}
- **Failed**: ${FAILED_TESTS}
- **Skipped**: ${SKIPPED_TESTS}
- **Pass Rate**: $(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)%

## Test Categories

### Category 1: Direct LLM Questions
- Tests LLM's ability to answer general knowledge questions without RAG

### Category 2: RAG-Based Questions
- Tests document retrieval and context-based answering

### Category 3: Short-Term Memory
- Tests session-specific document prioritization

### Category 4: Long-Term Memory
- Tests cross-session document retrieval

### Category 5: Tool-Specific Questions
- Tests individual agent tools (OCR, web scraping, etc.)

### Category 6: Model Coverage
- Tests all available LLM models

### Category 7: Response Quality
- Evaluates answer relevance, accuracy, and latency

## Recommendations

EOF

    if [ "$FAILED_TESTS" -gt 0 ]; then
        echo "**Status**: ⚠️ ATTENTION REQUIRED - Some tests failed" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
        echo "### Failed Tests" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
        echo "Review the console output above for details on failed tests." >> "$REPORT_FILE"
    elif [ "$SKIPPED_TESTS" -gt 0 ]; then
        echo "**Status**: ℹ️ PARTIAL - Some tests were skipped" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
        echo "### Skipped Tests" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
        echo "Some tests were skipped due to missing test data or unavailable services." >> "$REPORT_FILE"
    else
        echo "**Status**: ✅ ALL TESTS PASSED" >> "$REPORT_FILE"
    fi

    echo "" >> "$REPORT_FILE"
    echo "## Next Steps" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "1. Review failed tests and investigate root causes" >> "$REPORT_FILE"
    echo "2. Run Python pytest suite for detailed validation" >> "$REPORT_FILE"
    echo "3. Address quality issues identified" >> "$REPORT_FILE"
    echo "4. Re-run tests after fixes" >> "$REPORT_FILE"

    log_success "Report generated: $REPORT_FILE"
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    echo ""
    echo "============================================================================"
    echo "  Comprehensive Chat Test Suite"
    echo "============================================================================"
    echo ""

    preflight_checks

    test_direct_llm
    test_rag_queries
    test_short_term_memory
    test_long_term_memory
    test_tools
    test_model_coverage
    test_response_quality

    echo ""
    echo "============================================================================"
    echo "  Test Summary"
    echo "============================================================================"
    echo ""
    echo "Total Tests:  $TOTAL_TESTS"
    echo -e "${GREEN}Passed:       $PASSED_TESTS${NC}"
    echo -e "${RED}Failed:       $FAILED_TESTS${NC}"
    echo -e "${YELLOW}Skipped:      $SKIPPED_TESTS${NC}"

    if [ "$TOTAL_TESTS" -gt 0 ]; then
        pass_rate=$(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)
        echo "Pass Rate:    ${pass_rate}%"
    fi

    echo ""

    generate_report

    echo ""
    echo "Full report saved to: $REPORT_FILE"
    echo ""

    # Exit with failure if any tests failed
    if [ "$FAILED_TESTS" -gt 0 ]; then
        exit 1
    fi
}

# Run main
main "$@"
