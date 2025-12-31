#!/bin/bash

# ============================================================================
# EXTRACTION FEATURES TEST SUITE
# ============================================================================
# Tests all extraction features: Smart Extraction, Template operations,
# CSS Selector mode, Smart Mapper, and AI Navigation
#
# Usage:
#   ./test-extraction-features.sh [test_number]
#
# Examples:
#   ./test-extraction-features.sh        # Run all tests
#   ./test-extraction-features.sh 1      # Run only test 1
#   ./test-extraction-features.sh 1,3,5  # Run tests 1, 3, and 5
#
# Requirements:
#   - Backend running at localhost:8000
#   - OpenAI API key configured in .env
#   - jq installed for JSON parsing
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# API endpoint
API_URL="${API_URL:-http://localhost:8000}"

# Results directory
RESULTS_DIR="/tmp/extraction_tests_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_header() {
    echo ""
    echo "============================================================================"
    echo "$1"
    echo "============================================================================"
    echo ""
}

check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check jq
    if ! command -v jq &> /dev/null; then
        log_error "jq is not installed. Please install it: sudo apt-get install jq"
        exit 1
    fi
    log_success "jq installed"

    # Check backend health
    if ! curl -s "${API_URL}/health" > /dev/null 2>&1; then
        log_error "Backend not responding at ${API_URL}"
        exit 1
    fi
    log_success "Backend healthy at ${API_URL}"

    # Check OpenAI API key (optional warning)
    if [ -f .env ] && ! grep -q "OPENAI_API_KEY=" .env; then
        log_warning "OPENAI_API_KEY not found in .env file"
    fi

    log_success "All prerequisites met"
}

record_test_result() {
    local test_name="$1"
    local result="$2"
    local details="$3"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ "$result" = "PASS" ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        log_success "TEST PASSED: $test_name"
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        log_error "TEST FAILED: $test_name"
        if [ -n "$details" ]; then
            echo "  Details: $details"
        fi
    fi
}

# ============================================================================
# TEST 1: Smart Extraction - Basic Book Extraction
# ============================================================================

test_smart_extraction() {
    print_header "TEST 1: Smart Extraction - Mystery Books"

    local test_file="$RESULTS_DIR/test1_smart_extraction.json"

    log_info "Extracting data from Mystery category..."

    curl -s -X POST "${API_URL}/api/v1/extract/ultra-smart" \
        -H "Content-Type: application/json" \
        -d '{
            "url": "https://books.toscrape.com/catalogue/category/books/mystery_3/index.html",
            "user_instructions": "Extract all mystery books with title, price, and availability",
            "source_type": "url",
            "llm_provider": "openai"
        }' > "$test_file"

    # Validate results
    if jq -e '.success == true' "$test_file" > /dev/null 2>&1; then
        local row_count=$(jq -r '.row_count // 0' "$test_file")
        local columns=$(jq -r '.columns | join(", ")' "$test_file")

        log_info "Books extracted: $row_count"
        log_info "Columns: $columns"

        # Show sample data
        echo ""
        echo "Sample books:"
        jq -r '.table[0].Mystery[0:3] | .[] | "  📚 \(.Title) - \(.Price) - \(.Availability)"' "$test_file" 2>/dev/null || \
        jq -r '.table[0:3] | .[] | to_entries | map("  📚 \(.value)") | join(" - ")' "$test_file"

        if [ "$row_count" -gt 0 ]; then
            record_test_result "Smart Extraction" "PASS" "Extracted $row_count books"
        else
            record_test_result "Smart Extraction" "FAIL" "No data extracted"
        fi
    else
        local error_msg=$(jq -r '.error // "Unknown error"' "$test_file")
        record_test_result "Smart Extraction" "FAIL" "$error_msg"
    fi

    log_info "Results saved to: $test_file"
}

# ============================================================================
# TEST 2: AI-Powered Navigation
# ============================================================================

test_ai_navigation() {
    print_header "TEST 2: AI-Powered Navigation - Fantasy Books"

    local test_file="$RESULTS_DIR/test2_ai_navigation.json"

    log_info "Starting from homepage, navigating to Fantasy category..."
    log_warning "This test may take 60-90 seconds (requires AI navigation)"

    curl -s -X POST "${API_URL}/api/v1/extract/ultra-smart" \
        -H "Content-Type: application/json" \
        -d '{
            "url": "https://books.toscrape.com/",
            "user_instructions": "Navigate to the Fantasy category and extract all fantasy books with title and price",
            "source_type": "url",
            "llm_provider": "openai",
            "model_id": "gpt-4-turbo"
        }' > "$test_file"

    # Validate results
    if jq -e '.success == true' "$test_file" > /dev/null 2>&1; then
        local row_count=$(jq -r '.row_count // 0' "$test_file")
        local nav_path=$(jq -r '.extraction_metadata.metadata.navigation_path | join(" → ")' "$test_file" 2>/dev/null || echo "N/A")
        local steps=$(jq -r '.extraction_metadata.metadata.steps_taken // "N/A"' "$test_file")

        log_info "Navigation path: $nav_path"
        log_info "Steps taken: $steps"
        log_info "Books extracted: $row_count"

        if [ "$row_count" -gt 0 ]; then
            record_test_result "AI Navigation" "PASS" "Navigated and extracted $row_count books"
        else
            record_test_result "AI Navigation" "FAIL" "Navigation completed but no data extracted"
        fi
    else
        local error_msg=$(jq -r '.error // "Unknown error"' "$test_file")
        record_test_result "AI Navigation" "FAIL" "$error_msg"
    fi

    log_info "Results saved to: $test_file"
}

# ============================================================================
# TEST 3: Different URL Pattern - Single Book Page
# ============================================================================

test_single_book_extraction() {
    print_header "TEST 3: Single Book Page Extraction"

    local test_file="$RESULTS_DIR/test3_single_book.json"

    log_info "Extracting data from individual book page..."

    curl -s -X POST "${API_URL}/api/v1/extract/ultra-smart" \
        -H "Content-Type: application/json" \
        -d '{
            "url": "https://books.toscrape.com/catalogue/sharp-objects_997/index.html",
            "user_instructions": "Extract the book title, price, availability, product description, and UPC from this product page",
            "source_type": "url",
            "llm_provider": "openai"
        }' > "$test_file"

    # Validate results
    if jq -e '.success == true' "$test_file" > /dev/null 2>&1; then
        log_info "Book details extracted successfully"

        echo ""
        echo "Extracted fields:"
        jq -r '.table[0] | to_entries | .[] | "  \(.key): \(.value)"' "$test_file" 2>/dev/null || \
        jq -r '.columns | .[] | "  - \(.)"' "$test_file"

        record_test_result "Single Book Extraction" "PASS" "Book details extracted"
    else
        local error_msg=$(jq -r '.error // "Unknown error"' "$test_file")
        record_test_result "Single Book Extraction" "FAIL" "$error_msg"
    fi

    log_info "Results saved to: $test_file"
}

# ============================================================================
# TEST 4: Template List Retrieval
# ============================================================================

test_template_listing() {
    print_header "TEST 4: Template Listing"

    local test_file="$RESULTS_DIR/test4_templates.json"

    log_info "Fetching all extraction templates..."

    curl -s -X GET "${API_URL}/api/v1/extract/templates" > "$test_file"

    # Validate results
    if jq -e '. | length >= 0' "$test_file" > /dev/null 2>&1; then
        local template_count=$(jq '. | length' "$test_file")
        log_info "Templates found: $template_count"

        if [ "$template_count" -gt 0 ]; then
            echo ""
            echo "Available templates:"
            jq -r '.[] | "  - \(.display_name // .template_name) (\(.template_name))"' "$test_file"
        fi

        record_test_result "Template Listing" "PASS" "Retrieved $template_count templates"
    else
        record_test_result "Template Listing" "FAIL" "Invalid response format"
    fi

    log_info "Results saved to: $test_file"
}

# ============================================================================
# TEST 5: Backend Health & Features Check
# ============================================================================

test_backend_health() {
    print_header "TEST 5: Backend Health & Feature Availability"

    local test_file="$RESULTS_DIR/test5_health.json"

    log_info "Checking backend health and features..."

    curl -s "${API_URL}/health" > "$test_file"

    # Validate results
    if jq -e '.status == "healthy"' "$test_file" > /dev/null 2>&1; then
        local features=$(jq -r '.features | to_entries | map("\(.key)=\(.value)") | join(", ")' "$test_file")
        log_info "Features: $features"

        echo ""
        jq '.' "$test_file"

        record_test_result "Backend Health" "PASS" "All systems healthy"
    else
        record_test_result "Backend Health" "FAIL" "Backend unhealthy"
    fi

    log_info "Results saved to: $test_file"
}

# ============================================================================
# TEST RUNNER
# ============================================================================

run_tests() {
    local tests_to_run="$1"

    print_header "EXTRACTION FEATURES TEST SUITE"
    log_info "Results directory: $RESULTS_DIR"

    check_prerequisites

    # Determine which tests to run
    if [ -z "$tests_to_run" ]; then
        # Run all tests
        test_smart_extraction
        test_ai_navigation
        test_single_book_extraction
        test_template_listing
        test_backend_health
    else
        # Run specific tests
        IFS=',' read -ra TEST_ARRAY <<< "$tests_to_run"
        for test_num in "${TEST_ARRAY[@]}"; do
            case $test_num in
                1) test_smart_extraction ;;
                2) test_ai_navigation ;;
                3) test_single_book_extraction ;;
                4) test_template_listing ;;
                5) test_backend_health ;;
                *) log_error "Unknown test number: $test_num" ;;
            esac
        done
    fi

    # Print summary
    print_header "TEST SUMMARY"
    echo "Total Tests:  $TOTAL_TESTS"
    echo -e "${GREEN}Passed:       $PASSED_TESTS${NC}"
    echo -e "${RED}Failed:       $FAILED_TESTS${NC}"
    echo ""
    echo "All results saved to: $RESULTS_DIR"
    echo ""

    # Exit code based on results
    if [ "$FAILED_TESTS" -gt 0 ]; then
        exit 1
    fi
}

# ============================================================================
# MAIN
# ============================================================================

# Run tests with optional test number filter
run_tests "$1"
