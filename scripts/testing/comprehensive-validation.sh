#!/bin/bash

##############################################################################
# Comprehensive Validation Script
#
# This script validates:
# 1. Database schema and tables
# 2. Backend API endpoints
# 3. Frontend components
# 4. Integration between layers
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# API URLs
API_URL=${API_URL:-"http://localhost:8000"}
FRONTEND_URL=${FRONTEND_URL:-"http://localhost:3001"}

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

##############################################################################
# Helper Functions
##############################################################################

print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}\n"
}

print_section() {
    echo -e "\n${YELLOW}─── $1 ───${NC}"
}

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    WARNING_CHECKS=$((WARNING_CHECKS + 1))
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
}

##############################################################################
# Database Validation
##############################################################################

validate_database() {
    print_header "DATABASE VALIDATION"

    print_section "Checking Database Connection"
    if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
        check_pass "PostgreSQL is running"
    else
        check_fail "PostgreSQL is not responding"
        return 1
    fi

    print_section "Checking Core Tables"

    # Check documents table
    if docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "\d documents" > /dev/null 2>&1; then
        check_pass "documents table exists"
    else
        check_fail "documents table missing"
    fi

    # Check document_chunks table
    if docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "\d document_chunks" > /dev/null 2>&1; then
        check_pass "document_chunks table exists"
    else
        check_fail "document_chunks table missing"
    fi

    # Check conversations table
    if docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "\d conversations" > /dev/null 2>&1; then
        check_pass "conversations table exists"
    else
        check_fail "conversations table missing"
    fi

    # Check messages table
    if docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "\d messages" > /dev/null 2>&1; then
        check_pass "messages table exists"
    else
        check_fail "messages table missing"
    fi

    print_section "Checking Web Scraping Tables"

    # Check web_scrape_jobs table
    if docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "\d web_scrape_jobs" > /dev/null 2>&1; then
        check_pass "web_scrape_jobs table exists"

        # Check for enhanced scraping fields
        if docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "\d web_scrape_jobs" 2>&1 | grep -q "compliance_level"; then
            check_pass "web_scrape_jobs has compliance_level field (Phase 1)"
        else
            check_warn "web_scrape_jobs missing compliance_level field"
        fi

        if docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "\d web_scrape_jobs" 2>&1 | grep -q "llm_provider"; then
            check_pass "web_scrape_jobs has llm_provider field (Phase 1)"
        else
            check_warn "web_scrape_jobs missing llm_provider field"
        fi

        if docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "\d web_scrape_jobs" 2>&1 | grep -q "protocols_detected"; then
            check_pass "web_scrape_jobs has protocols_detected field (Phase 1)"
        else
            check_warn "web_scrape_jobs missing protocols_detected field"
        fi
    else
        check_fail "web_scrape_jobs table missing"
    fi

    print_section "Checking Enhanced Tables (RBAC & Sessions)"

    # Check users table
    if docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "\d users" > /dev/null 2>&1; then
        check_pass "users table exists"
    else
        check_warn "users table missing (enhanced features unavailable)"
    fi

    # Check chat_sessions table
    if docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "\d chat_sessions" > /dev/null 2>&1; then
        check_pass "chat_sessions table exists"
    else
        check_warn "chat_sessions table missing (session management unavailable)"
    fi

    # Check session_documents table
    if docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "\d session_documents" > /dev/null 2>&1; then
        check_pass "session_documents table exists (memory hierarchy)"
    else
        check_warn "session_documents table missing (memory hierarchy unavailable)"
    fi

    # Check audit_logs table
    if docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "\d audit_logs" > /dev/null 2>&1; then
        check_pass "audit_logs table exists"
    else
        check_warn "audit_logs table missing (auditing unavailable)"
    fi

    print_section "Checking pgvector Extension"

    if docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "SELECT * FROM pg_extension WHERE extname='vector'" | grep -q "vector"; then
        check_pass "pgvector extension installed"

        # Check for vector columns
        if docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL" > /dev/null 2>&1; then
            COUNT=$(docker-compose exec -T postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL" | tr -d ' ')
            check_pass "document_chunks has $COUNT embeddings"
        fi
    else
        check_fail "pgvector extension not installed"
    fi

    print_section "Checking Data"

    # Count documents
    DOC_COUNT=$(docker-compose exec -T postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM documents" | tr -d ' ')
    if [ "$DOC_COUNT" -gt 0 ]; then
        check_pass "$DOC_COUNT documents in database"
    else
        check_warn "No documents in database"
    fi

    # Count scrape jobs
    SCRAPE_COUNT=$(docker-compose exec -T postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM web_scrape_jobs" 2>/dev/null | tr -d ' ')
    if [ -n "$SCRAPE_COUNT" ] && [ "$SCRAPE_COUNT" -gt 0 ]; then
        check_pass "$SCRAPE_COUNT scrape jobs in database"
    else
        check_warn "No scrape jobs in database"
    fi
}

##############################################################################
# Backend API Validation
##############################################################################

validate_backend() {
    print_header "BACKEND API VALIDATION"

    print_section "Checking Backend Service"

    # Check if backend is running
    if curl -s "$API_URL/health" > /dev/null 2>&1; then
        check_pass "Backend service is running ($API_URL)"
    else
        check_fail "Backend service is not responding"
        return 1
    fi

    # Check API docs
    if curl -s "$API_URL/api/docs" > /dev/null 2>&1; then
        check_pass "API documentation available at $API_URL/api/docs"
    else
        check_warn "API documentation not available"
    fi

    print_section "Checking Core API Endpoints"

    # Health endpoint
    if curl -s "$API_URL/api/v1/health" | grep -q "status"; then
        check_pass "GET /api/v1/health"
    else
        check_fail "GET /api/v1/health"
    fi

    # Documents endpoint
    if curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/v1/documents" | grep -q "200"; then
        check_pass "GET /api/v1/documents"
    else
        check_fail "GET /api/v1/documents"
    fi

    print_section "Checking Web Scraper Endpoints (Phase 1 & 2)"

    # Basic scraper capabilities
    if curl -s "$API_URL/api/v1/scraper/capabilities" > /dev/null 2>&1; then
        RESPONSE=$(curl -s "$API_URL/api/v1/scraper/capabilities")
        check_pass "GET /api/v1/scraper/capabilities"

        # Check for Phase 1 features
        if echo "$RESPONSE" | grep -q "compliance_level"; then
            check_pass "Phase 1: Compliance levels supported"
        else
            check_warn "Phase 1: Compliance levels not found in capabilities"
        fi

        if echo "$RESPONSE" | grep -q "smart_scraping_enabled"; then
            check_pass "Phase 1: Smart scraping with LLM supported"
        else
            check_warn "Phase 1: Smart scraping not found in capabilities"
        fi

        if echo "$RESPONSE" | grep -q "supported_llm_providers"; then
            check_pass "Phase 1: Multiple LLM providers supported"
        else
            check_warn "Phase 1: LLM providers not found in capabilities"
        fi

        # Check for supported compliance levels
        if echo "$RESPONSE" | grep -q "strict.*balanced.*aggressive"; then
            check_pass "Phase 1: All compliance levels available (strict, balanced, aggressive)"
        else
            check_warn "Phase 1: Not all compliance levels found"
        fi
    else
        check_fail "GET /api/v1/scraper/capabilities (Enhanced scraper not available)"
    fi

    # Check scrape endpoint exists (we won't actually scrape)
    if curl -s -X POST "$API_URL/api/v1/scraper/scrape" \
        -H "Content-Type: application/json" \
        -d '{"url": "invalid"}' 2>&1 | grep -qE "422|400|500"; then
        check_pass "POST /api/v1/scraper/scrape endpoint exists"
    else
        check_fail "POST /api/v1/scraper/scrape endpoint not responding"
    fi

    # Check bulk scrape endpoint
    if curl -s -X POST "$API_URL/api/v1/scraper/scrape/bulk" \
        -H "Content-Type: application/json" \
        -d '{"urls": []}' 2>&1 | grep -qE "422|400|500"; then
        check_pass "POST /api/v1/scraper/scrape/bulk endpoint exists (Phase 2)"
    else
        check_fail "POST /api/v1/scraper/scrape/bulk endpoint not responding"
    fi

    print_section "Checking Extraction Workflow Endpoints (Phase 3)"

    # Check extraction jobs endpoint
    if curl -s "$API_URL/api/v1/extraction/jobs" > /dev/null 2>&1; then
        check_pass "GET /api/v1/extraction/jobs (Phase 3)"
    else
        check_warn "GET /api/v1/extraction/jobs not available (Phase 3 not deployed)"
    fi

    # Check extraction job creation endpoint
    if curl -s -X POST "$API_URL/api/v1/extraction/jobs" \
        -H "Content-Type: application/json" \
        -d '{"urls": [], "output_format": "excel"}' 2>&1 | grep -qE "422|400|500"; then
        check_pass "POST /api/v1/extraction/jobs endpoint exists (Phase 3)"
    else
        check_warn "POST /api/v1/extraction/jobs not available (Phase 3 not deployed)"
    fi

    print_section "Checking GraphQL API"

    # GraphQL endpoint
    if curl -s "$API_URL/graphql" > /dev/null 2>&1; then
        check_pass "GraphQL endpoint available"
    else
        check_warn "GraphQL endpoint not available"
    fi
}

##############################################################################
# Frontend Validation
##############################################################################

validate_frontend() {
    print_header "FRONTEND VALIDATION"

    print_section "Checking Frontend Service"

    # Check if frontend is running
    if curl -s "$FRONTEND_URL" > /dev/null 2>&1; then
        check_pass "Frontend service is running ($FRONTEND_URL)"
    else
        check_fail "Frontend service is not responding"
        return 1
    fi

    print_section "Checking Component Files"

    # Check for ChatInterface components
    if [ -f "frontend/src/components/ChatInterface.tsx" ]; then
        check_pass "ChatInterface.tsx exists"
    else
        check_fail "ChatInterface.tsx missing"
    fi

    if [ -f "frontend/src/components/ChatInterfaceEnhanced.tsx" ]; then
        check_pass "ChatInterfaceEnhanced.tsx exists"
    else
        check_fail "ChatInterfaceEnhanced.tsx missing"
    fi

    # Check for WebScraper components
    if [ -f "frontend/src/components/WebScraper.tsx" ]; then
        check_pass "WebScraper.tsx exists (old)"
    else
        check_warn "WebScraper.tsx missing"
    fi

    if [ -f "frontend/src/components/WebScraperEnhanced.tsx" ]; then
        check_pass "WebScraperEnhanced.tsx exists (new with Phase 1-3)"
    else
        check_fail "WebScraperEnhanced.tsx missing"
    fi

    # Check for FileUpload component
    if [ -f "frontend/src/components/FileUpload.tsx" ]; then
        check_pass "FileUpload.tsx exists"
    else
        check_fail "FileUpload.tsx missing"
    fi

    print_section "Checking Component Usage"

    # Check which WebScraper is being imported in ChatInterfaceEnhanced
    if grep -q "import WebScraper from './WebScraper'" frontend/src/components/ChatInterfaceEnhanced.tsx; then
        check_warn "ChatInterfaceEnhanced uses OLD WebScraper (should use WebScraperEnhanced)"
    elif grep -q "import WebScraperEnhanced from './WebScraperEnhanced'" frontend/src/components/ChatInterfaceEnhanced.tsx; then
        check_pass "ChatInterfaceEnhanced uses NEW WebScraperEnhanced"
    else
        check_warn "Cannot determine which WebScraper component is used"
    fi

    # Check main page
    if [ -f "frontend/src/pages/index.tsx" ]; then
        check_pass "Main page (index.tsx) exists"

        # Check which ChatInterface is being used
        if grep -q "ChatInterfaceEnhanced" frontend/src/pages/index.tsx; then
            check_pass "Main page uses ChatInterfaceEnhanced"
        else
            check_warn "Main page may not be using enhanced components"
        fi
    else
        check_fail "Main page (index.tsx) missing"
    fi

    print_section "Checking WebScraperEnhanced Features"

    if [ -f "frontend/src/components/WebScraperEnhanced.tsx" ]; then
        # Check for Phase 1 features
        if grep -q "ComplianceLevel" frontend/src/components/WebScraperEnhanced.tsx; then
            check_pass "Phase 1: Compliance level support in UI"
        else
            check_warn "Phase 1: Compliance level not found in UI"
        fi

        if grep -q "llmProvider\|LLMProvider" frontend/src/components/WebScraperEnhanced.tsx; then
            check_pass "Phase 1: LLM provider selection in UI"
        else
            check_warn "Phase 1: LLM provider selection not found in UI"
        fi

        if grep -q "AuthConfig\|auth_type" frontend/src/components/WebScraperEnhanced.tsx; then
            check_pass "Phase 1: Authentication configuration in UI"
        else
            check_warn "Phase 1: Authentication not found in UI"
        fi

        # Check for Phase 2 features
        if grep -q "ScrapingStrategy\|strategy" frontend/src/components/WebScraperEnhanced.tsx; then
            check_pass "Phase 2: Scraping strategy selection in UI"
        else
            check_warn "Phase 2: Scraping strategy not found in UI"
        fi

        if grep -q "AdvancedConfig\|advancedConfig" frontend/src/components/WebScraperEnhanced.tsx; then
            check_pass "Phase 2: Advanced configuration in UI"
        else
            check_warn "Phase 2: Advanced configuration not found in UI"
        fi

        # Check for Phase 3 features
        if grep -q "TemplateExtractionTab\|template" frontend/src/components/WebScraperEnhanced.tsx; then
            check_pass "Phase 3: Template extraction tab in UI"
        else
            check_warn "Phase 3: Template extraction not found in UI"
        fi

        if grep -q "OutputFormat.*excel.*csv.*json" frontend/src/components/WebScraperEnhanced.tsx; then
            check_pass "Phase 3: Multiple output formats in UI"
        else
            check_warn "Phase 3: Output formats not found in UI"
        fi

        if grep -q "DeliveryMethod.*email.*webhook" frontend/src/components/WebScraperEnhanced.tsx; then
            check_pass "Phase 3: Delivery methods in UI"
        else
            check_warn "Phase 3: Delivery methods not found in UI"
        fi

        if grep -q "JobMonitorTab\|ExtractionJob" frontend/src/components/WebScraperEnhanced.tsx; then
            check_pass "Phase 3: Job monitoring in UI"
        else
            check_warn "Phase 3: Job monitoring not found in UI"
        fi
    fi
}

##############################################################################
# Integration Validation
##############################################################################

validate_integration() {
    print_header "INTEGRATION VALIDATION"

    print_section "Checking Service Connectivity"

    # Check if frontend can reach backend
    if docker-compose exec -T frontend sh -c "wget -q -O- $API_URL/health" > /dev/null 2>&1; then
        check_pass "Frontend can reach backend"
    else
        check_warn "Frontend cannot reach backend (check NEXT_PUBLIC_API_URL)"
    fi

    # Check MinIO connection
    if curl -s http://localhost:9001 > /dev/null 2>&1; then
        check_pass "MinIO service is running"
    else
        check_warn "MinIO service not accessible"
    fi

    # Check Redis connection
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        check_pass "Redis service is running"
    else
        check_warn "Redis service not accessible"
    fi

    print_section "Checking Environment Variables"

    # Check backend environment
    if docker-compose exec -T backend sh -c 'echo $DATABASE_URL' | grep -q "postgresql"; then
        check_pass "Backend has DATABASE_URL configured"
    else
        check_warn "Backend DATABASE_URL may not be configured"
    fi

    # Check frontend environment
    if docker-compose exec -T frontend sh -c 'echo $NEXT_PUBLIC_API_URL' | grep -q "http"; then
        check_pass "Frontend has NEXT_PUBLIC_API_URL configured"
    else
        check_warn "Frontend NEXT_PUBLIC_API_URL may not be configured"
    fi
}

##############################################################################
# Feature Gap Analysis
##############################################################################

analyze_gaps() {
    print_header "FEATURE GAP ANALYSIS"

    print_section "Identified Issues"

    # Check if WebScraperEnhanced is being used
    if grep -q "import WebScraper from './WebScraper'" frontend/src/components/ChatInterfaceEnhanced.tsx; then
        echo -e "${RED}CRITICAL:${NC} ChatInterfaceEnhanced is using OLD WebScraper component"
        echo "  Fix: Change import to 'import WebScraperEnhanced from \"./WebScraperEnhanced\"'"
        echo "       Change usage to '<WebScraperEnhanced />'"
    fi

    # Check backend routes
    echo -e "\n${YELLOW}Backend Routes Status:${NC}"
    echo "  Phase 1 (Compliance): $(curl -s "$API_URL/api/v1/scraper/capabilities" > /dev/null 2>&1 && echo -e "${GREEN}Available${NC}" || echo -e "${RED}Missing${NC}")"
    echo "  Phase 2 (Strategies): $(curl -s -X POST "$API_URL/api/v1/scraper/scrape/bulk" -H "Content-Type: application/json" -d '{"urls":[]}' 2>&1 | grep -qE "422|400|500" && echo -e "${GREEN}Available${NC}" || echo -e "${RED}Missing${NC}")"
    echo "  Phase 3 (Extraction): $(curl -s "$API_URL/api/v1/extraction/jobs" > /dev/null 2>&1 && echo -e "${GREEN}Available${NC}" || echo -e "${RED}Missing${NC}")"

    echo -e "\n${YELLOW}Frontend Components Status:${NC}"
    echo "  WebScraper (old): $([ -f "frontend/src/components/WebScraper.tsx" ] && echo -e "${GREEN}Exists${NC}" || echo -e "${RED}Missing${NC}")"
    echo "  WebScraperEnhanced (new): $([ -f "frontend/src/components/WebScraperEnhanced.tsx" ] && echo -e "${GREEN}Exists${NC}" || echo -e "${RED}Missing${NC}")"
    echo "  Currently Used: $(grep -q "import WebScraperEnhanced" frontend/src/components/ChatInterfaceEnhanced.tsx && echo -e "${GREEN}Enhanced${NC}" || echo -e "${RED}Old${NC}")"
}

##############################################################################
# Summary Report
##############################################################################

print_summary() {
    print_header "VALIDATION SUMMARY"

    echo -e "Total Checks: ${BLUE}$TOTAL_CHECKS${NC}"
    echo -e "Passed:       ${GREEN}$PASSED_CHECKS${NC}"
    echo -e "Failed:       ${RED}$FAILED_CHECKS${NC}"
    echo -e "Warnings:     ${YELLOW}$WARNING_CHECKS${NC}"

    PASS_RATE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))

    echo ""
    if [ "$FAILED_CHECKS" -eq 0 ]; then
        echo -e "${GREEN}✓ All critical checks passed!${NC}"
    else
        echo -e "${RED}✗ Some critical checks failed. Please review the output above.${NC}"
    fi

    echo -e "\nPass Rate: ${BLUE}${PASS_RATE}%${NC}"

    if [ "$PASS_RATE" -ge 90 ]; then
        echo -e "${GREEN}Excellent! System is in good shape.${NC}"
    elif [ "$PASS_RATE" -ge 70 ]; then
        echo -e "${YELLOW}Good, but some improvements needed.${NC}"
    else
        echo -e "${RED}System needs attention. Multiple issues found.${NC}"
    fi
}

##############################################################################
# Main Execution
##############################################################################

main() {
    echo -e "${BLUE}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║         COMPREHENSIVE VALIDATION SCRIPT                               ║
║         Enterprise RAG Chatbot                                        ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"

    echo "Starting comprehensive validation..."
    echo "API URL: $API_URL"
    echo "Frontend URL: $FRONTEND_URL"
    echo ""

    # Run all validations
    validate_database
    validate_backend
    validate_frontend
    validate_integration
    analyze_gaps

    # Print summary
    print_summary

    echo -e "\n${BLUE}═══════════════════════════════════════════════════════${NC}\n"

    # Exit with appropriate code
    if [ "$FAILED_CHECKS" -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# Run main function
main
