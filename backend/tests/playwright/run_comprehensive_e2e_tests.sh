#!/bin/bash

################################################################################
# Comprehensive E2E Test Execution Script
#
# Runs comprehensive Playwright tests for:
# 1. Procurement Matcher (Domain Vertical - Tier 2)
# 2. British Council (Customer Solution - Tier 3)
#
# Each test suite covers:
# - UI Navigation & Interface
# - Business Logic
# - Frontend Components
# - Backend API
# - Export Package Generation
################################################################################

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Timestamp for this test run
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Test results directory
RESULTS_DIR="backend/tests/playwright/test_results"
mkdir -p "$RESULTS_DIR"

# Report file
REPORT_FILE="$RESULTS_DIR/comprehensive_e2e_report_$TIMESTAMP.md"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Comprehensive E2E Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Initialize report
cat > "$REPORT_FILE" << EOF
# Comprehensive E2E Test Execution Report

**Date**: $(date +"%Y-%m-%d %H:%M:%S")
**Test Run ID**: $TIMESTAMP

---

## Test Scope

### Module 1: Procurement Matcher (Domain Vertical - Tier 2)
- **Category**: Domain Vertical
- **Business Logic**: RFP Analysis, Supplier Matching, Variance Detection
- **Test Data**: sample_data/tier2_domain_verticals/procurement_matcher/

### Module 2: British Council (Customer Solution - Tier 3)
- **Category**: Customer Solution POC
- **Business Logic**: Course Recommendations, Skill Matching, Profile Analysis
- **Test Data**: sample_data/tier3_customer_pocs/british_council/

---

## Test Coverage

Each module is tested across 5 dimensions:

1. **UI Navigation & Interface**
   - Module accessibility
   - UI component presence
   - Layout and display

2. **Business Logic**
   - Core algorithms
   - Data processing
   - Result accuracy

3. **Frontend Components**
   - Input validation
   - Results display
   - User interactions

4. **Backend API**
   - Endpoint availability
   - Request/response validation
   - Error handling

5. **Export Package**
   - Export wizard functionality
   - Package generation
   - Content validation

---

## Test Execution

EOF

# Function to run tests and capture results
run_test_suite() {
    local test_file=$1
    local module_name=$2
    local category=$3

    echo -e "${YELLOW}Running tests for: $module_name${NC}"
    echo ""

    # Add to report
    echo "### $module_name ($category)" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "**Test File**: \`$test_file\`" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    # Run pytest with detailed output
    if pytest "$test_file" -v -s --tb=short --html="$RESULTS_DIR/${module_name// /_}_report_$TIMESTAMP.html" --self-contained-html 2>&1 | tee "$RESULTS_DIR/${module_name// /_}_output_$TIMESTAMP.log"; then
        echo -e "${GREEN}✓ $module_name tests PASSED${NC}"
        echo "" >> "$REPORT_FILE"
        echo "**Status**: ✅ **PASSED**" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
        return 0
    else
        echo -e "${RED}✗ $module_name tests FAILED${NC}"
        echo "" >> "$REPORT_FILE"
        echo "**Status**: ❌ **FAILED**" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
        return 1
    fi
}

# Track overall results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Suite 1: Procurement Matcher${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if run_test_suite \
    "backend/tests/playwright/test_procurement_matcher_e2e_comprehensive.py" \
    "Procurement Matcher" \
    "Domain Vertical - Tier 2"; then
    ((PASSED_TESTS++))
else
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Suite 2: British Council${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if run_test_suite \
    "backend/tests/playwright/test_british_council_e2e_comprehensive.py" \
    "British Council" \
    "Customer Solution - Tier 3"; then
    ((PASSED_TESTS++))
else
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))

# Add summary to report
cat >> "$REPORT_FILE" << EOF

---

## Test Summary

| Metric | Value |
|--------|-------|
| Total Test Suites | $TOTAL_TESTS |
| Passed | $PASSED_TESTS |
| Failed | $FAILED_TESTS |
| Success Rate | $(awk "BEGIN {printf \"%.1f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")% |

---

## Test Results by Category

### Procurement Matcher

| Category | Status |
|----------|--------|
| UI Navigation | See detailed report |
| Business Logic | See detailed report |
| Frontend Components | See detailed report |
| Backend API | See detailed report |
| Export Package | See detailed report |

### British Council

| Category | Status |
|----------|--------|
| UI Navigation | See detailed report |
| Business Logic | See detailed report |
| Frontend Components | See detailed report |
| Backend API | See detailed report |
| Export Package | See detailed report |

---

## Generated Artifacts

- **Detailed HTML Reports**: \`$RESULTS_DIR/*_report_$TIMESTAMP.html\`
- **Test Output Logs**: \`$RESULTS_DIR/*_output_$TIMESTAMP.log\`
- **Screenshots (on failure)**: \`$RESULTS_DIR/FAILED_*.png\`
- **Videos**: \`$RESULTS_DIR/videos/*/\`

---

## Next Steps

1. **Review Failures**: Check \`FAILED_*.png\` screenshots and logs
2. **Verify Export Packages**: Validate generated export packages if tests passed
3. **Performance Check**: Review test execution times
4. **Documentation**: Update test documentation with any new findings

---

## Notes

- All tests use realistic sample data from \`sample_data/\` directory
- Export package tests validate end-to-end export functionality
- API tests may skip if backend endpoints use different routes
- Some UI tests may skip if interface differs from expected structure

---

**Report Generated**: $(date +"%Y-%m-%d %H:%M:%S")
**Status**: Complete

EOF

# Print final summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TEST EXECUTION SUMMARY${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Total Test Suites: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"
echo ""
echo -e "Success Rate: $(awk "BEGIN {printf \"%.1f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")%"
echo ""
echo -e "${YELLOW}Detailed Report: $REPORT_FILE${NC}"
echo ""

# Exit with failure if any tests failed
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}Some tests failed. Please review the detailed reports.${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed successfully!${NC}"
    exit 0
fi
