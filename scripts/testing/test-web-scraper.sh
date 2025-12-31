#!/bin/bash

# ============================================================================
# Web Scraper Testing Script
# ============================================================================
# This script tests all web scraping functionality including:
# - Basic web scraper (single URL)
# - Enhanced scraper with bulk scraping
# - Template extraction
# - Job monitoring
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

API_URL="${API_URL:-http://localhost:8000}"
TEST_URL="https://example.com"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Web Scraper Integration Tests${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# ============================================================================
# Helper Functions
# ============================================================================

print_step() {
    echo -e "\n${YELLOW}>>> $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_service() {
    local service=$1
    local url=$2

    print_step "Checking $service..."

    if curl -s -f "$url" > /dev/null 2>&1; then
        print_success "$service is running"
        return 0
    else
        print_error "$service is not responding at $url"
        return 1
    fi
}

# ============================================================================
# Pre-flight Checks
# ============================================================================

print_step "Running pre-flight checks..."

check_service "Backend API" "$API_URL/health" || {
    echo ""
    echo -e "${RED}ERROR: Backend is not running!${NC}"
    echo ""
    echo "Please start the backend services:"
    echo "  docker compose up -d backend"
    echo "  OR"
    echo "  make up"
    echo ""
    exit 1
}

check_service "Frontend" "http://localhost:3001" || {
    echo ""
    echo -e "${YELLOW}WARNING: Frontend is not running${NC}"
    echo "To start frontend: docker compose up -d frontend"
    echo ""
}

# ============================================================================
# Test 1: Basic Scraper Endpoint (Single URL)
# ============================================================================

print_step "Test 1: Basic Scraper - Single URL (/api/v1/scrape)"

RESPONSE=$(curl -s -X POST "$API_URL/api/v1/scrape" \
    -F "url=$TEST_URL" \
    -F "scrape_prompt=Extract main content")

if echo "$RESPONSE" | grep -q '"success"'; then
    print_success "Basic scraper endpoint working"
    echo "Response preview:"
    echo "$RESPONSE" | jq -r '.title, .content_length' 2>/dev/null || echo "$RESPONSE" | head -c 200
else
    print_error "Basic scraper endpoint failed"
    echo "Response:"
    echo "$RESPONSE"
fi

# ============================================================================
# Test 2: Enhanced Scraper - Bulk Scraping
# ============================================================================

print_step "Test 2: Enhanced Scraper - Bulk Scraping (/api/v1/scraper/scrape/bulk)"

BULK_PAYLOAD=$(cat <<EOF
{
  "urls": ["https://example.com", "https://httpbin.org/html"],
  "compliance_level": "balanced",
  "strategy": "auto"
}
EOF
)

RESPONSE=$(curl -s -X POST "$API_URL/api/v1/scraper/scrape/bulk" \
    -H "Content-Type: application/json" \
    -d "$BULK_PAYLOAD")

if echo "$RESPONSE" | grep -q '"total"'; then
    print_success "Bulk scraper endpoint working"
    echo "Response preview:"
    echo "$RESPONSE" | jq -r '.total, .successful, .failed' 2>/dev/null || echo "$RESPONSE" | head -c 200
else
    print_error "Bulk scraper endpoint failed"
    echo "Response:"
    echo "$RESPONSE"
fi

# ============================================================================
# Test 3: Scraper Capabilities
# ============================================================================

print_step "Test 3: Scraper Capabilities (/api/v1/scraper/capabilities)"

RESPONSE=$(curl -s -X GET "$API_URL/api/v1/scraper/capabilities")

if echo "$RESPONSE" | grep -q '"enabled"'; then
    print_success "Capabilities endpoint working"
    echo "Available strategies:"
    echo "$RESPONSE" | jq -r '.available_strategies[]' 2>/dev/null || echo "Parse error"
else
    print_error "Capabilities endpoint failed"
    echo "Response:"
    echo "$RESPONSE"
fi

# ============================================================================
# Test 4: Extraction Jobs - Create Job
# ============================================================================

print_step "Test 4: Template Extraction - Create Job (/api/v1/extraction/jobs)"

EXTRACTION_PAYLOAD=$(cat <<EOF
{
  "urls": ["https://example.com"],
  "output_format": "json",
  "delivery_method": "download",
  "scrape_config": {
    "compliance_level": "balanced",
    "max_concurrent_requests": 5
  }
}
EOF
)

RESPONSE=$(curl -s -X POST "$API_URL/api/v1/extraction/jobs" \
    -H "Content-Type: application/json" \
    -d "$EXTRACTION_PAYLOAD")

if echo "$RESPONSE" | grep -q '"job_id"'; then
    print_success "Extraction job created"
    JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id' 2>/dev/null)
    echo "Job ID: $JOB_ID"
else
    print_error "Extraction job creation failed"
    echo "Response:"
    echo "$RESPONSE"
    JOB_ID=""
fi

# ============================================================================
# Test 5: List Extraction Jobs
# ============================================================================

print_step "Test 5: List Extraction Jobs (/api/v1/extraction/jobs)"

RESPONSE=$(curl -s -X GET "$API_URL/api/v1/extraction/jobs")

if echo "$RESPONSE" | grep -q '"jobs"'; then
    print_success "Job list endpoint working"
    echo "Total jobs:"
    echo "$RESPONSE" | jq -r '.total' 2>/dev/null || echo "Parse error"
    echo "Jobs:"
    echo "$RESPONSE" | jq -r '.jobs[] | "\(.job_id) - \(.status)"' 2>/dev/null | head -5 || echo "Parse error"
else
    print_error "Job list endpoint failed"
    echo "Response:"
    echo "$RESPONSE"
fi

# ============================================================================
# Test 6: Get Job Details (if job was created)
# ============================================================================

if [ -n "$JOB_ID" ]; then
    print_step "Test 6: Get Job Details (/api/v1/extraction/jobs/$JOB_ID)"

    sleep 2  # Give job time to process

    RESPONSE=$(curl -s -X GET "$API_URL/api/v1/extraction/jobs/$JOB_ID")

    if echo "$RESPONSE" | grep -q '"job_id"'; then
        print_success "Job details retrieved"
        echo "Status:"
        echo "$RESPONSE" | jq -r '.status, .current_step, .progress_percentage' 2>/dev/null || echo "Parse error"
    else
        print_error "Job details retrieval failed"
        echo "Response:"
        echo "$RESPONSE"
    fi
fi

# ============================================================================
# Test 7: Web Scrape Jobs (legacy endpoint)
# ============================================================================

print_step "Test 7: Web Scrape Jobs List (/api/v1/scraper/jobs)"

RESPONSE=$(curl -s -X GET "$API_URL/api/v1/scraper/jobs?limit=10")

if echo "$RESPONSE" | grep -q '\['; then
    print_success "Scraper jobs endpoint working"
    echo "Recent jobs:"
    echo "$RESPONSE" | jq -r '.[] | "\(.job_id) - \(.status)"' 2>/dev/null | head -5 || echo "No jobs or parse error"
else
    print_error "Scraper jobs endpoint failed or returned no jobs"
fi

# ============================================================================
# Summary
# ============================================================================

echo ""
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo "All critical endpoints have been tested."
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo "1. Check the frontend at http://localhost:3001"
echo "2. Navigate to the Web Scraper tab"
echo "3. Try basic scraping with a test URL"
echo "4. Check the Job Monitor tab to see extraction jobs"
echo ""
echo "For detailed logs, check:"
echo "  docker compose logs -f backend"
echo ""
echo -e "${BLUE}============================================================================${NC}"
