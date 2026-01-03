#!/bin/bash

# Comprehensive POC Validation Test Runner
# Executes validated Playwright tests with test data

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║      POC Validation - Comprehensive E2E Test Execution        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_URL="${FRONTEND_URL:-http://frontend:3000}"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
TEST_FILE="/app/tests/playwright/test_tier2_validated.py"
RESULTS_DIR="/app/tests/playwright/test_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo -e "${BLUE}[1/5] Test Configuration${NC}"
echo "Frontend URL: $FRONTEND_URL"
echo "Backend URL: $BACKEND_URL"
echo "Test File: $TEST_FILE"
echo "Results Directory: $RESULTS_DIR"
echo ""

echo -e "${BLUE}[2/5] Verifying Services${NC}"
# Check backend
if curl -s "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend service is running${NC}"
else
    echo -e "${RED}✗ Backend service is not accessible${NC}"
    exit 1
fi

# Check frontend
if curl -s "$FRONTEND_URL" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend service is running${NC}"
else
    echo -e "${RED}✗ Frontend service is not accessible${NC}"
    exit 1
fi
echo ""

echo -e "${BLUE}[3/5] Verifying Test Data${NC}"
# Check test data files exist
TEST_DATA_BASE="/app/sample_data/tier2_domain_verticals"
test_files=(
    "hr_talent/job_postings_sample.csv"
    "hr_talent/resume_software_engineer.txt"
    "hr_talent/tech_industry_taxonomy.json"
    "construction/planning_application_residential.txt"
    "procurement/cloud_migration_requirements.txt"
    "procurement/vendor_cloudtech_solutions.txt"
    "procurement/vendor_enterprise_systems.txt"
    "procurement/vendor_global_cloud_partners.txt"
    "document_intelligence/financial_quarterly_report_q4_2023.txt"
    "document_intelligence/research_paper_transformer_architecture.txt"
    "document_intelligence/construction_project_data_extraction.txt"
)

missing_files=0
for file in "${test_files[@]}"; do
    if [ -f "$TEST_DATA_BASE/$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (missing)"
        missing_files=$((missing_files + 1))
    fi
done

if [ $missing_files -gt 0 ]; then
    echo -e "${RED}Error: $missing_files test data files are missing${NC}"
    exit 1
fi
echo ""

echo -e "${BLUE}[4/5] Running Validated Test Suite${NC}"
echo "Executing: pytest $TEST_FILE -v --tb=short"
echo "Environment: FRONTEND_URL=$FRONTEND_URL"
echo ""

# Run tests
pytest "$TEST_FILE" -v --tb=short --capture=no \
    --html="$RESULTS_DIR/test_report_${TIMESTAMP}.html" \
    --self-contained-html \
    2>&1 | tee "$RESULTS_DIR/test_output_${TIMESTAMP}.log"

TEST_EXIT_CODE=${PIPESTATUS[0]}

echo ""
echo -e "${BLUE}[5/5] Test Execution Summary${NC}"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${YELLOW}⚠ Some tests failed or encountered errors${NC}"
fi

echo ""
echo "Test Results:"
echo "  Log File: $RESULTS_DIR/test_output_${TIMESTAMP}.log"
echo "  HTML Report: $RESULTS_DIR/test_report_${TIMESTAMP}.html"
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                  Test Execution Complete                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"

exit $TEST_EXIT_CODE
