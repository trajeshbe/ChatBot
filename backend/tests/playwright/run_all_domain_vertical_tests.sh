#!/bin/bash
###############################################################################
# Master Test Runner for All Domain Verticals and Customer Solutions
#
# This script runs comprehensive Playwright E2E tests for:
# - Tier 2 Domain Verticals (30+ modules across 11 categories)
# - Tier 3 Customer Solutions (6 POCs)
#
# Usage: ./run_all_domain_vertical_tests.sh
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3001}"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
HEADLESS="${HEADLESS:-true}"
SLOW_MO="${SLOW_MO:-0}"
SCREENSHOT_ON_FAILURE="${SCREENSHOT_ON_FAILURE:-true}"

# Test report paths
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_DIR="backend/tests/playwright/test_results"
REPORT_FILE="$RESULTS_DIR/comprehensive_validation_report_$TIMESTAMP.md"
HTML_REPORT="$RESULTS_DIR/comprehensive_validation_report_$TIMESTAMP.html"
JSON_REPORT="$RESULTS_DIR/validation_results_$TIMESTAMP.json"

# Create results directory
mkdir -p "$RESULTS_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Domain Verticals & Customer Solutions - E2E Test Suite      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check services are running
echo -e "${YELLOW}[1/6] Checking services...${NC}"
echo "Frontend URL: $FRONTEND_URL"
echo "Backend URL: $BACKEND_URL"

if ! curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health" | grep -q "200"; then
    echo -e "${RED}✗ Backend service not responding at $BACKEND_URL${NC}"
    echo "Please start the backend service first: docker-compose up -d backend"
    exit 1
fi
echo -e "${GREEN}✓ Backend service is running${NC}"

if ! curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" | grep -q "200"; then
    echo -e "${RED}✗ Frontend service not responding at $FRONTEND_URL${NC}"
    echo "Please start the frontend service first: docker-compose up -d frontend"
    exit 1
fi
echo -e "${GREEN}✓ Frontend service is running${NC}"
echo ""

# Initialize validation report
echo -e "${YELLOW}[2/6] Initializing validation report...${NC}"
cat > "$REPORT_FILE" << EOF
# Domain Verticals & Customer Solutions - Comprehensive Validation Report

**Generated:** $(date +"%Y-%m-%d %H:%M:%S")

---

## Executive Summary

This report provides comprehensive E2E test results for all Tier 2 Domain Verticals and Tier 3 Customer Solutions.

### Test Coverage

- **Tier 2 Domain Verticals:** 30+ modules across 11 categories
- **Tier 3 Customer Solutions:** 6 POCs

---

## Test Results

EOF

echo "{" > "$JSON_REPORT"
echo "  \"timestamp\": \"$(date -Iseconds)\"," >> "$JSON_REPORT"
echo "  \"frontend_url\": \"$FRONTEND_URL\"," >> "$JSON_REPORT"
echo "  \"backend_url\": \"$BACKEND_URL\"," >> "$JSON_REPORT"
echo "  \"test_results\": {" >> "$JSON_REPORT"

# Test suite definitions
declare -A test_suites
test_suites=(
    ["Document Intelligence"]="test_tier2_document_intelligence.py"
    ["All Tier 2 Verticals"]="test_tier2_all_verticals.py"
    ["Tier 3 Customer Solutions"]="test_tier3_customer_solutions.py"
)

# Run each test suite
echo -e "${YELLOW}[3/6] Running test suites...${NC}"
total_suites=${#test_suites[@]}
current_suite=0
passed_suites=0
failed_suites=0

for suite_name in "${!test_suites[@]}"; do
    current_suite=$((current_suite + 1))
    test_file="${test_suites[$suite_name]}"

    echo ""
    echo -e "${BLUE}[$current_suite/$total_suites] Running: $suite_name${NC}"
    echo "Test file: $test_file"
    echo "---"

    # Run pytest
    cd backend/tests/playwright

    if pytest "$test_file" -v --tb=short --maxfail=5 2>&1 | tee "$RESULTS_DIR/${suite_name// /_}_output.log"; then
        echo -e "${GREEN}✓ $suite_name: PASSED${NC}"
        passed_suites=$((passed_suites + 1))

        # Append to report
        echo "### ✅ $suite_name - PASSED" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"

        # Add to JSON
        echo "    \"$suite_name\": {" >> "$JSON_REPORT"
        echo "      \"status\": \"PASSED\"," >> "$JSON_REPORT"
        echo "      \"test_file\": \"$test_file\"" >> "$JSON_REPORT"
        echo "    }," >> "$JSON_REPORT"
    else
        echo -e "${RED}✗ $suite_name: FAILED${NC}"
        failed_suites=$((failed_suites + 1))

        # Append to report
        echo "### ❌ $suite_name - FAILED" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
        echo "See detailed logs in: \`$RESULTS_DIR/${suite_name// /_}_output.log\`" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"

        # Add to JSON
        echo "    \"$suite_name\": {" >> "$JSON_REPORT"
        echo "      \"status\": \"FAILED\"," >> "$JSON_REPORT"
        echo "      \"test_file\": \"$test_file\"," >> "$JSON_REPORT"
        echo "      \"log_file\": \"$RESULTS_DIR/${suite_name// /_}_output.log\"" >> "$JSON_REPORT"
        echo "    }," >> "$JSON_REPORT"
    fi

    cd ../../..
done

# Close JSON report
echo "  }" >> "$JSON_REPORT"
echo "}" >> "$JSON_REPORT"

# Generate summary
echo -e "${YELLOW}[4/6] Generating summary...${NC}"

cat >> "$REPORT_FILE" << EOF

---

## Summary

- **Total Test Suites:** $total_suites
- **Passed:** $passed_suites
- **Failed:** $failed_suites
- **Success Rate:** $(( (passed_suites * 100) / total_suites ))%

---

## Module Coverage

### Tier 2 Domain Verticals

#### Document Intelligence (3 modules)
- Generic RAG
- 18-Field Document Extraction
- Relation Extractor

#### Construction (4 modules)
- Planning Classifier
- Mine Scope Analysis
- AU Cost Estimator
- Building Metrics

#### Procurement (4 modules)
- PO-Invoice Matcher
- Vendor Recommendation
- Tender Intelligence
- Spend Analytics

#### HR & Talent (3 modules)
- Talent Pulse
- Talent Search
- Taxonomy Skillmatch

#### Agriculture (2 modules)
- Agri Taxonomy
- Agronomy Decision Support

#### Analytics (4 modules)
- Customer Churn
- Financial Anomaly
- Predictive Analytics
- Sales Performance

### Tier 3 Customer Solutions (6 POCs)

- British Council - Course Recommendation
- CRU - Mining Intelligence
- Grant Thornton - Financial Datapoint Extraction
- GT Motive - Automotive Parts Extraction
- Solera - Insurance Claims Processing
- Construction Monitor - NER/REL for Construction Docs

---

## Recommendations

EOF

if [ $failed_suites -eq 0 ]; then
    echo "✅ **All test suites passed!** The implementation is complete and functional." >> "$REPORT_FILE"
else
    echo "⚠️ **$failed_suites test suite(s) failed.** Review the detailed logs above to identify issues." >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "Common issues:" >> "$REPORT_FILE"
    echo "- Missing frontend UI components" >> "$REPORT_FILE"
    echo "- Backend endpoints not implemented" >> "$REPORT_FILE"
    echo "- Sample data files not available" >> "$REPORT_FILE"
    echo "- Module routing configuration incomplete" >> "$REPORT_FILE"
fi

cat >> "$REPORT_FILE" << EOF

---

## Next Steps

1. Review detailed test logs in \`$RESULTS_DIR/\`
2. Fix any failing tests
3. Ensure all sample data files are present
4. Verify all backend routes are registered in main.py
5. Confirm all frontend modules are configured in modules.ts

---

**Report Generated:** $(date +"%Y-%m-%d %H:%M:%S")
**Location:** \`$REPORT_FILE\`

EOF

# Display final summary
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                     Test Execution Complete                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Summary:${NC}"
echo "  Total Suites: $total_suites"
echo -e "  Passed: ${GREEN}$passed_suites${NC}"
echo -e "  Failed: ${RED}$failed_suites${NC}"
echo "  Success Rate: $(( (passed_suites * 100) / total_suites ))%"
echo ""
echo -e "${YELLOW}Reports:${NC}"
echo "  📄 Markdown: $REPORT_FILE"
echo "  📊 JSON: $JSON_REPORT"
echo ""

if [ $failed_suites -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ $failed_suites test suite(s) failed.${NC}"
    echo "Review the reports for details."
    exit 1
fi
