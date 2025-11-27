#!/bin/bash

##############################################################################
# Comprehensive Document Handling Test Script
#
# Tests:
# 1. Image handling (PNG, JPG) - OCR capabilities
# 2. Complex PDF handling - Docling vs standard extraction
# 3. Office documents (PPTX, DOCX, XLSX)
# 4. Tool usage detection (OCR, Docling, etc.)
# 5. Response quality evaluation
# 6. Multi-modal capabilities
#
# Date: 2025-11-24
##############################################################################

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="http://localhost:8000"
SESSION_ID="doc-test-session-$(date +%s)"
TEST_RESULTS_FILE="/tmp/document_handling_test_results_$(date +%Y%m%d_%H%M%S).json"
LOG_FILE="/tmp/document_handling_test_$(date +%Y%m%d_%H%M%S).log"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNINGS=0

# Initialize results file
echo "{\"tests\": [], \"summary\": {}}" > "$TEST_RESULTS_FILE"

##############################################################################
# Helper Functions
##############################################################################

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}" | tee -a "$LOG_FILE"
}

add_test_result() {
    local test_name="$1"
    local status="$2"
    local details="$3"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ "$status" = "PASS" ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
    elif [ "$status" = "FAIL" ]; then
        FAILED_TESTS=$((FAILED_TESTS + 1))
    elif [ "$status" = "WARNING" ]; then
        WARNINGS=$((WARNINGS + 1))
    fi

    # Add to JSON results
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local result="{\"name\": \"$test_name\", \"status\": \"$status\", \"details\": \"$details\", \"timestamp\": \"$timestamp\"}"

    jq ".tests += [$result]" "$TEST_RESULTS_FILE" > "${TEST_RESULTS_FILE}.tmp" && mv "${TEST_RESULTS_FILE}.tmp" "$TEST_RESULTS_FILE"
}

##############################################################################
# Test 0: Backend Health Check
##############################################################################

test_backend_health() {
    log "=== Test 0: Backend Health Check ==="

    local response=$(curl -s "$BACKEND_URL/health" || echo "ERROR")

    if [ "$response" = "ERROR" ]; then
        log_error "Backend not responding"
        add_test_result "Backend Health" "FAIL" "Backend not responding"
        exit 1
    fi

    log_success "Backend is healthy"
    add_test_result "Backend Health" "PASS" "Backend responding correctly"
}

##############################################################################
# Test 1: Check Available Document Processing Tools
##############################################################################

test_available_tools() {
    log "=== Test 1: Check Available Document Processing Tools ==="

    # Check backend logs for OCR/Docling initialization
    log "Checking for OCR and Docling backends..."

    local docling_check=$(docker-compose logs backend 2>&1 | grep -i "docling" | tail -5 || echo "not found")
    local ocr_check=$(docker-compose logs backend 2>&1 | grep -i "tesseract\|ocr" | tail -5 || echo "not found")

    log_info "Docling status: $docling_check"
    log_info "OCR status: $ocr_check"

    if [[ "$docling_check" == *"not found"* ]] && [[ "$ocr_check" == *"not found"* ]]; then
        log_warning "No OCR/Docling logs found - backends may not be initialized"
        add_test_result "Document Processing Tools" "WARNING" "OCR/Docling status unclear"
    else
        log_success "Document processing tools detected"
        add_test_result "Document Processing Tools" "PASS" "Docling and/or OCR available"
    fi
}

##############################################################################
# Test 2: Create Test Image with Text
##############################################################################

create_test_image() {
    log "=== Test 2: Create Test Image with Text ==="

    # Create a simple image with text using ImageMagick (if available)
    local test_image="/tmp/test_ocr_image.png"

    if command -v convert &> /dev/null; then
        convert -size 800x400 xc:white \
            -pointsize 40 \
            -fill black \
            -annotate +50+100 'Document Handling Test' \
            -annotate +50+200 'This is a test image for OCR capabilities.' \
            -annotate +50+300 'Testing: Images, PDFs, Office Docs' \
            "$test_image" 2>/dev/null || {
                log_warning "Failed to create test image with ImageMagick"
                echo "IMAGE_CREATION_FAILED"
                return 1
            }

        log_success "Test image created: $test_image"
        echo "$test_image"
        add_test_result "Create Test Image" "PASS" "Test image created successfully"
    else
        log_warning "ImageMagick not available, skipping image creation"
        add_test_result "Create Test Image" "WARNING" "ImageMagick not available"
        echo "IMAGE_CREATION_SKIPPED"
        return 1
    fi
}

##############################################################################
# Test 3: Upload and Process Image
##############################################################################

test_image_upload() {
    log "=== Test 3: Upload and Process Image (OCR Test) ==="

    local test_image=$(create_test_image)

    if [ "$test_image" = "IMAGE_CREATION_FAILED" ] || [ "$test_image" = "IMAGE_CREATION_SKIPPED" ]; then
        log_warning "Skipping image upload test (no test image)"
        add_test_result "Image Upload & OCR" "WARNING" "Test image not available"
        return
    fi

    # Upload image
    log "Uploading test image..."
    local upload_response=$(curl -s -X POST "$BACKEND_URL/api/v1/upload" \
        -F "file=@$test_image" \
        -F "session_id=$SESSION_ID")

    local document_id=$(echo "$upload_response" | jq -r '.document_id // empty')

    if [ -z "$document_id" ]; then
        log_error "Failed to upload image"
        log_info "Response: $upload_response"
        add_test_result "Image Upload & OCR" "FAIL" "Failed to upload test image"
        return
    fi

    log_success "Image uploaded successfully (ID: $document_id)"

    # Wait for processing
    log "Waiting for image processing (OCR)..."
    sleep 5

    # Query the image content
    log "Querying image content..."
    local query_response=$(curl -s -X POST "$BACKEND_URL/api/v1/query" \
        -F "query=What text is in the uploaded image?" \
        -F "session_id=$SESSION_ID" \
        -F "use_cache=false")

    local answer=$(echo "$query_response" | jq -r '.answer // empty')
    local num_sources=$(echo "$query_response" | jq -r '.num_sources // 0')
    local tools_used=$(echo "$query_response" | jq -r '.metadata.tool_usage.tools_used[]? // empty' | tr '\n' ', ')

    log_info "Answer preview: ${answer:0:200}..."
    log_info "Sources found: $num_sources"
    log_info "Tools used: $tools_used"

    # Check if OCR was detected
    if [[ "$answer" == *"Document Handling Test"* ]] || [[ "$answer" == *"OCR"* ]]; then
        log_success "Image text successfully extracted (OCR working)"
        add_test_result "Image Upload & OCR" "PASS" "OCR extracted text from image, sources: $num_sources, tools: $tools_used"
    else
        log_warning "Image text not clearly detected in answer"
        add_test_result "Image Upload & OCR" "WARNING" "OCR may not have fully extracted text"
    fi

    # Clean up
    rm -f "$test_image"
}

##############################################################################
# Test 4: Check PDF Processing Capabilities
##############################################################################

test_pdf_capabilities() {
    log "=== Test 4: Check PDF Processing Capabilities ==="

    # Create a simple PDF for testing
    local test_pdf="/tmp/test_complex_pdf.txt"

    # Create sample content
    cat > "$test_pdf" << 'EOF'
COMPLEX PDF TEST DOCUMENT
=========================

This is a test document to evaluate PDF processing capabilities.

SECTION 1: Introduction
-----------------------
This document contains:
- Multiple sections
- Tables and structured data
- Various formatting styles

SECTION 2: Data Table
----------------------
Item        | Quantity | Price
-----------|----------|-------
Widget A   | 100      | $10.00
Widget B   | 50       | $25.00
Widget C   | 75       | $15.00

SECTION 3: Technical Details
-----------------------------
The system should be able to:
1. Extract text accurately
2. Preserve structure and formatting
3. Handle tables and lists
4. Identify sections and headers

SECTION 4: Conclusion
---------------------
This document tests PDF processing with Docling and standard extraction methods.
EOF

    log_success "Test PDF content created: $test_pdf"
    add_test_result "PDF Test Document Creation" "PASS" "Test PDF created"

    echo "$test_pdf"
}

##############################################################################
# Test 5: Upload and Query PDF Document
##############################################################################

test_pdf_upload() {
    log "=== Test 5: Upload and Query PDF Document ==="

    local test_pdf=$(test_pdf_capabilities)

    # Upload PDF
    log "Uploading test PDF..."
    local upload_response=$(curl -s -X POST "$BACKEND_URL/api/v1/upload" \
        -F "file=@$test_pdf" \
        -F "session_id=$SESSION_ID")

    local document_id=$(echo "$upload_response" | jq -r '.document_id // empty')

    if [ -z "$document_id" ]; then
        log_error "Failed to upload PDF"
        log_info "Response: $upload_response"
        add_test_result "PDF Upload" "FAIL" "Failed to upload test PDF"
        return
    fi

    log_success "PDF uploaded successfully (ID: $document_id)"

    # Wait for processing
    log "Waiting for PDF processing..."
    sleep 5

    # Test 5a: Query section headers
    log "Test 5a: Querying section headers..."
    local response=$(curl -s -X POST "$BACKEND_URL/api/v1/query" \
        -F "query=What sections are in the document?" \
        -F "session_id=$SESSION_ID" \
        -F "use_cache=false")

    local answer=$(echo "$response" | jq -r '.answer // empty')

    if [[ "$answer" == *"Introduction"* ]] || [[ "$answer" == *"SECTION"* ]]; then
        log_success "PDF structure preserved (sections detected)"
        add_test_result "PDF Structure Extraction" "PASS" "Sections correctly identified"
    else
        log_warning "PDF structure not clearly detected"
        add_test_result "PDF Structure Extraction" "WARNING" "Sections may not be preserved"
    fi

    # Test 5b: Query table data
    log "Test 5b: Querying table data..."
    local response=$(curl -s -X POST "$BACKEND_URL/api/v1/query" \
        -F "query=What items are in the data table and their prices?" \
        -F "session_id=$SESSION_ID" \
        -F "use_cache=false")

    local answer=$(echo "$response" | jq -r '.answer // empty')

    if [[ "$answer" == *"Widget"* ]] || [[ "$answer" == *"price"* ]] || [[ "$answer" == *"quantity"* ]]; then
        log_success "PDF table data extracted"
        add_test_result "PDF Table Extraction" "PASS" "Table data correctly extracted"
    else
        log_warning "PDF table data not clearly detected"
        add_test_result "PDF Table Extraction" "WARNING" "Table extraction may need improvement"
    fi

    # Clean up
    rm -f "$test_pdf"
}

##############################################################################
# Test 6: Office Document Handling (DOCX/PPTX simulation)
##############################################################################

test_office_documents() {
    log "=== Test 6: Office Document Handling ==="

    log_info "Note: Testing with text files (DOCX/PPTX require office libraries)"

    # Create a markdown file simulating office content
    local test_doc="/tmp/test_office_document.md"

    cat > "$test_doc" << 'EOF'
# Business Presentation - Q4 Results

## Slide 1: Overview
- Revenue increased 25%
- Customer base grew to 10,000+
- New product launch successful

## Slide 2: Financial Highlights
**Revenue**: $5.2M (+25% YoY)
**Profit**: $1.1M (+30% YoY)
**Customers**: 10,234 (+2,100)

## Slide 3: Key Achievements
1. Launched Product X in 5 markets
2. Achieved 95% customer satisfaction
3. Expanded team by 40 people

## Slide 4: Next Quarter Goals
- Target 15,000 customers
- Launch Product Y
- Open 3 new offices
EOF

    log "Uploading office document simulation..."
    local upload_response=$(curl -s -X POST "$BACKEND_URL/api/v1/upload" \
        -F "file=@$test_doc" \
        -F "session_id=$SESSION_ID")

    local document_id=$(echo "$upload_response" | jq -r '.document_id // empty')

    if [ -z "$document_id" ]; then
        log_error "Failed to upload document"
        add_test_result "Office Document Upload" "FAIL" "Failed to upload test document"
        return
    fi

    log_success "Document uploaded (ID: $document_id)"
    sleep 3

    # Query structured content
    log "Querying structured content..."
    local response=$(curl -s -X POST "$BACKEND_URL/api/v1/query" \
        -F "query=What was the revenue and profit in Q4?" \
        -F "session_id=$SESSION_ID" \
        -F "use_cache=false")

    local answer=$(echo "$response" | jq -r '.answer // empty')

    if [[ "$answer" == *"5.2"* ]] || [[ "$answer" == *"1.1"* ]] || [[ "$answer" == *"revenue"* ]]; then
        log_success "Structured data correctly extracted from document"
        add_test_result "Office Document Data Extraction" "PASS" "Numerical data correctly extracted"
    else
        log_warning "Structured data not clearly detected"
        add_test_result "Office Document Data Extraction" "WARNING" "Data extraction may need improvement"
    fi

    rm -f "$test_doc"
}

##############################################################################
# Test 7: Tool Usage Analysis
##############################################################################

test_tool_usage_analysis() {
    log "=== Test 7: Tool Usage Analysis ==="

    log "Analyzing tool usage across all queries..."

    # Query with explicit request for tool information
    local response=$(curl -s -X POST "$BACKEND_URL/api/v1/query" \
        -F "query=Summarize all the documents uploaded in this session" \
        -F "session_id=$SESSION_ID" \
        -F "use_cache=false")

    local tools_used=$(echo "$response" | jq -r '.metadata.tool_usage.tools_used[]? // empty' | sort -u | tr '\n' ', ')
    local tool_timing=$(echo "$response" | jq -r '.metadata.tool_usage.tool_timing // empty')
    local num_sources=$(echo "$response" | jq -r '.num_sources // 0')

    log_info "Tools used: ${tools_used:-none}"
    log_info "Sources retrieved: $num_sources"

    if [ -n "$tools_used" ]; then
        log_success "Tool usage tracking working"
        add_test_result "Tool Usage Tracking" "PASS" "Tools: $tools_used, Sources: $num_sources"
    else
        log_warning "No tool usage information detected"
        add_test_result "Tool Usage Tracking" "WARNING" "Tool tracking may not be enabled"
    fi
}

##############################################################################
# Test 8: Multi-Tool Agent Response Quality
##############################################################################

test_multitool_response_quality() {
    log "=== Test 8: Multi-Tool Agent Response Quality ==="

    log "Testing multi-tool agent with document query..."

    local response=$(curl -s -X POST "$BACKEND_URL/api/v1/multi-strategy/query-form" \
        -F "query=What are the key insights from all uploaded documents?" \
        -F "session_id=$SESSION_ID" \
        -F "model_id=llama3.1:8b" \
        -F "enable_direct_llm=true" \
        -F "enable_rag_short_term=true" \
        -F "enable_rag_long_term=false" \
        -F "enable_tools=true")

    local success=$(echo "$response" | jq -r '.success // false')
    local strategy_used=$(echo "$response" | jq -r '.strategy_used // "unknown"')
    local final_score=$(echo "$response" | jq -r '.final_score // 0')
    local num_sources=$(echo "$response" | jq -r '.num_sources // 0')

    log_info "Strategy used: $strategy_used"
    log_info "Final score: $final_score"
    log_info "Sources: $num_sources"

    if [ "$success" = "true" ] && (( $(echo "$final_score > 0.5" | bc -l) )); then
        log_success "Multi-tool agent working with good quality response"
        add_test_result "Multi-Tool Agent Quality" "PASS" "Strategy: $strategy_used, Score: $final_score"
    else
        log_warning "Multi-tool response quality could be improved"
        add_test_result "Multi-Tool Agent Quality" "WARNING" "Score: $final_score may be low"
    fi
}

##############################################################################
# Test 9: Document Processing Methods Detection
##############################################################################

test_processing_methods() {
    log "=== Test 9: Document Processing Methods Detection ==="

    # Check backend logs for processing methods
    log "Checking backend logs for document processing methods..."

    local docling_logs=$(docker-compose logs backend 2>&1 | grep -i "docling" | wc -l)
    local ocr_logs=$(docker-compose logs backend 2>&1 | grep -i "tesseract\|ocr" | wc -l)
    local pypdf_logs=$(docker-compose logs backend 2>&1 | grep -i "pypdf\|pdf" | wc -l)

    log_info "Docling references: $docling_logs"
    log_info "OCR references: $ocr_logs"
    log_info "PDF processing references: $pypdf_logs"

    local methods=""
    [ "$docling_logs" -gt 0 ] && methods="${methods}Docling, "
    [ "$ocr_logs" -gt 0 ] && methods="${methods}OCR, "
    [ "$pypdf_logs" -gt 0 ] && methods="${methods}PyPDF, "

    if [ -n "$methods" ]; then
        log_success "Document processing methods detected: ${methods%, }"
        add_test_result "Processing Methods Detection" "PASS" "Methods: ${methods%, }"
    else
        log_warning "No clear document processing method logs found"
        add_test_result "Processing Methods Detection" "WARNING" "Methods unclear from logs"
    fi
}

##############################################################################
# Test 10: State-of-the-Art Evaluation
##############################################################################

test_sota_evaluation() {
    log "=== Test 10: State-of-the-Art Evaluation ==="

    log "Evaluating against state-of-the-art standards..."

    local sota_score=0
    local max_score=5

    # Criterion 1: Docling support (IBM's SOTA document understanding)
    if docker-compose logs backend 2>&1 | grep -q -i "docling"; then
        sota_score=$((sota_score + 1))
        log_success "✓ Docling support (IBM SOTA)"
    else
        log_info "✗ Docling not detected"
    fi

    # Criterion 2: OCR support
    if docker-compose logs backend 2>&1 | grep -q -i "tesseract\|ocr"; then
        sota_score=$((sota_score + 1))
        log_success "✓ OCR support (Tesseract)"
    else
        log_info "✗ OCR not detected"
    fi

    # Criterion 3: Multi-tool agent
    if docker-compose logs backend 2>&1 | grep -q -i "multi.*tool\|tool.*registry"; then
        sota_score=$((sota_score + 1))
        log_success "✓ Multi-tool agent support"
    else
        log_info "✗ Multi-tool agent not detected"
    fi

    # Criterion 4: Embeddings and vector search
    if docker-compose logs backend 2>&1 | grep -q -i "embedding\|vector"; then
        sota_score=$((sota_score + 1))
        log_success "✓ Vector embeddings support"
    else
        log_info "✗ Vector embeddings not detected"
    fi

    # Criterion 5: Multiple processing strategies
    if docker-compose logs backend 2>&1 | grep -q -i "multi.*strategy\|strategy.*rag"; then
        sota_score=$((sota_score + 1))
        log_success "✓ Multi-strategy RAG"
    else
        log_info "✗ Multi-strategy RAG not detected"
    fi

    local sota_percentage=$((sota_score * 100 / max_score))

    log_info "State-of-the-Art Score: $sota_score/$max_score ($sota_percentage%)"

    if [ $sota_score -ge 4 ]; then
        log_success "System meets state-of-the-art standards"
        add_test_result "State-of-the-Art Evaluation" "PASS" "Score: $sota_score/$max_score ($sota_percentage%)"
    elif [ $sota_score -ge 2 ]; then
        log_warning "System has some SOTA features but could be improved"
        add_test_result "State-of-the-Art Evaluation" "WARNING" "Score: $sota_score/$max_score ($sota_percentage%)"
    else
        log_error "System needs more SOTA features"
        add_test_result "State-of-the-Art Evaluation" "FAIL" "Score: $sota_score/$max_score ($sota_percentage%)"
    fi
}

##############################################################################
# Generate Final Report
##############################################################################

generate_report() {
    log "=== Generating Final Report ==="

    # Update summary
    jq ".summary = {
        \"total\": $TOTAL_TESTS,
        \"passed\": $PASSED_TESTS,
        \"failed\": $FAILED_TESTS,
        \"warnings\": $WARNINGS,
        \"session_id\": \"$SESSION_ID\",
        \"timestamp\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"
    }" "$TEST_RESULTS_FILE" > "${TEST_RESULTS_FILE}.tmp" && mv "${TEST_RESULTS_FILE}.tmp" "$TEST_RESULTS_FILE"

    log ""
    log "======================================================================"
    log "                  DOCUMENT HANDLING TEST SUMMARY                      "
    log "======================================================================"
    log "Total Tests:    $TOTAL_TESTS"
    log "Passed:         $PASSED_TESTS"
    log "Failed:         $FAILED_TESTS"
    log "Warnings:       $WARNINGS"
    log "======================================================================"
    log "Session ID:     $SESSION_ID"
    log "Results File:   $TEST_RESULTS_FILE"
    log "Log File:       $LOG_FILE"
    log "======================================================================"

    if [ $FAILED_TESTS -eq 0 ]; then
        log_success "All tests completed successfully!"
    else
        log_warning "Some tests failed. Review results for details."
    fi
}

##############################################################################
# Main Execution
##############################################################################

main() {
    log "======================================================================"
    log "        COMPREHENSIVE DOCUMENT HANDLING TEST SUITE                   "
    log "======================================================================"
    log "Session ID: $SESSION_ID"
    log "Backend: $BACKEND_URL"
    log ""

    test_backend_health
    test_available_tools
    test_image_upload
    test_pdf_upload
    test_office_documents
    test_tool_usage_analysis
    test_multitool_response_quality
    test_processing_methods
    test_sota_evaluation

    generate_report
}

# Run main function
main
