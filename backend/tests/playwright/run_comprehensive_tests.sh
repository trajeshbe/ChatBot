#!/bin/bash

# ============================================================================
# Comprehensive Test Runner for Enterprise RAG Chatbot
# ============================================================================
#
# Purpose: Run all Playwright E2E tests (existing + new enhancements)
#
# Usage:
#   bash backend/tests/playwright/run_comprehensive_tests.sh [options]
#
# Options:
#   --quick         Run only fast tests (skip slow exports)
#   --regression    Run only regression tests
#   --new          Run only new enhancement tests
#   --export        Run only Export Wizard tests
#   --all          Run all tests (default)
#   --headful       Run with visible browser
#   --report        Generate HTML report
#
# Environment Variables:
#   FRONTEND_URL    Frontend URL (default: http://localhost:3001)
#   BACKEND_URL     Backend URL (default: http://localhost:8000)
#   HEADLESS        Run headless (default: true)
#   SKIP_LONG_TESTS Skip long-running tests (default: false)
#
# Date: 2026-01-07
# Author: AI Assistant
# Related: Comprehensive E2E Testing Strategy
#
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3001}"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
HEADLESS="${HEADLESS:-true}"
SKIP_LONG_TESTS="${SKIP_LONG_TESTS:-false}"
SCREENSHOT_ON_FAILURE="${SCREENSHOT_ON_FAILURE:-true}"

# Test categories
RUN_MODE="all"  # Default: run all tests
RUN_HEADFUL="false"
GENERATE_REPORT="false"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            RUN_MODE="quick"
            SKIP_LONG_TESTS="true"
            shift
            ;;
        --regression)
            RUN_MODE="regression"
            shift
            ;;
        --new)
            RUN_MODE="new"
            shift
            ;;
        --export)
            RUN_MODE="export"
            shift
            ;;
        --all)
            RUN_MODE="all"
            shift
            ;;
        --headful)
            RUN_HEADFUL="true"
            HEADLESS="false"
            shift
            ;;
        --report)
            GENERATE_REPORT="true"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--quick|--regression|--new|--export|--all] [--headful] [--report]"
            exit 1
            ;;
    esac
done

# Export environment variables for pytest
export FRONTEND_URL
export BACKEND_URL
export HEADLESS
export SKIP_LONG_TESTS
export SCREENSHOT_ON_FAILURE

echo ""
echo -e "${PURPLE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║  Enterprise RAG Chatbot - Comprehensive E2E Test Suite       ║${NC}"
echo -e "${PURPLE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${CYAN}Configuration:${NC}"
echo -e "  Frontend URL:    ${BLUE}${FRONTEND_URL}${NC}"
echo -e "  Backend URL:     ${BLUE}${BACKEND_URL}${NC}"
echo -e "  Headless:        ${BLUE}${HEADLESS}${NC}"
echo -e "  Run Mode:        ${BLUE}${RUN_MODE}${NC}"
echo -e "  Skip Long Tests: ${BLUE}${SKIP_LONG_TESTS}${NC}"
echo ""

# Check if services are running
echo -e "${CYAN}>>> Checking Services${NC}"
echo ""

# Check frontend
if curl -s "${FRONTEND_URL}" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Frontend is running (${FRONTEND_URL})"
else
    echo -e "${RED}✗${NC} Frontend is NOT running (${FRONTEND_URL})"
    echo -e "${YELLOW}⚠${NC}  Please start the frontend with: docker-compose up -d frontend"
    exit 1
fi

# Check backend
if curl -s "${BACKEND_URL}/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend is running (${BACKEND_URL})"
else
    echo -e "${RED}✗${NC} Backend is NOT running (${BACKEND_URL})"
    echo -e "${YELLOW}⚠${NC}  Please start the backend with: docker-compose up -d backend"
    exit 1
fi

echo ""

# Navigate to tests directory
cd "$(dirname "$0")"

# Create test results directory
mkdir -p test_results

# Prepare pytest arguments
PYTEST_ARGS="-v -s --tb=short"

if [ "$GENERATE_REPORT" = "true" ]; then
    PYTEST_ARGS="$PYTEST_ARGS --html=test_results/report.html --self-contained-html"
fi

# Determine which tests to run
case $RUN_MODE in
    "quick")
        echo -e "${CYAN}>>> Running Quick Tests (no slow tests)${NC}"
        echo ""
        PYTEST_ARGS="$PYTEST_ARGS -m 'not slow'"
        ;;
    "regression")
        echo -e "${CYAN}>>> Running Regression Tests Only${NC}"
        echo ""
        PYTEST_ARGS="$PYTEST_ARGS -k 'regression'"
        ;;
    "new")
        echo -e "${CYAN}>>> Running New Enhancement Tests Only${NC}"
        echo ""
        PYTEST_ARGS="$PYTEST_ARGS test_export_wizard_e2e_comprehensive.py test_phase2_enhancements_e2e.py"
        ;;
    "export")
        echo -e "${CYAN}>>> Running Export Wizard Tests Only${NC}"
        echo ""
        PYTEST_ARGS="$PYTEST_ARGS test_export_wizard_e2e_comprehensive.py"
        ;;
    "all")
        echo -e "${CYAN}>>> Running All Tests${NC}"
        echo ""
        ;;
esac

# Run tests
echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}  Starting Test Execution${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Record start time
START_TIME=$(date +%s)

# Run pytest
if [ "$RUN_MODE" = "all" ] || [ "$RUN_MODE" = "quick" ]; then
    # Run all test files
    pytest $PYTEST_ARGS . || TEST_EXIT_CODE=$?
else
    # Run specific tests
    pytest $PYTEST_ARGS || TEST_EXIT_CODE=$?
fi

# Record end time
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}  Test Execution Complete${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Summary
echo -e "${CYAN}Test Summary:${NC}"
echo -e "  Duration: ${BLUE}${DURATION}s${NC}"

if [ "${TEST_EXIT_CODE:-0}" -eq 0 ]; then
    echo -e "  Status:   ${GREEN}✓ ALL TESTS PASSED${NC}"
else
    echo -e "  Status:   ${RED}✗ SOME TESTS FAILED${NC}"
fi

echo ""

# Report generation
if [ "$GENERATE_REPORT" = "true" ]; then
    echo -e "${CYAN}HTML Report:${NC}"
    echo -e "  ${BLUE}file://$(pwd)/test_results/report.html${NC}"
    echo ""
fi

# Screenshots
if [ "$SCREENSHOT_ON_FAILURE" = "true" ]; then
    FAILED_SCREENSHOTS=$(ls test_results/FAILED_*.png 2>/dev/null | wc -l)
    if [ "$FAILED_SCREENSHOTS" -gt 0 ]; then
        echo -e "${YELLOW}Failed Test Screenshots:${NC}"
        ls -1 test_results/FAILED_*.png 2>/dev/null | while read screenshot; do
            echo -e "  ${RED}✗${NC} $(basename $screenshot)"
        done
        echo ""
    fi
fi

# Test categories breakdown
echo -e "${CYAN}Test Categories:${NC}"
echo ""

echo -e "  ${BLUE}Regression Tests:${NC}"
echo "    - Existing functionality (chat, admin, documents)"
echo "    - API endpoints still working"
echo "    - UI still loads correctly"
echo ""

echo -e "  ${BLUE}Phase 2 Enhancement Tests:${NC}"
echo "    - System Configuration API"
echo "    - Model Registry & Auto-discovery"
echo "    - Agent Runtime Model Selection"
echo "    - Integration between systems"
echo ""

echo -e "  ${BLUE}Export Wizard Tests (NEW):${NC}"
echo "    - UI rendering and modal functionality"
echo "    - Tier selection (Tier 2 & 3)"
echo "    - Module listing and selection"
echo "    - Export job creation"
echo "    - Progress tracking"
echo "    - Download functionality"
echo "    - Complete workflow testing"
echo ""

# Next steps
echo -e "${CYAN}Next Steps:${NC}"
echo ""

if [ "${TEST_EXIT_CODE:-0}" -eq 0 ]; then
    echo -e "  ${GREEN}1.${NC} Review test coverage"
    echo -e "  ${GREEN}2.${NC} Add tests to CI/CD pipeline"
    echo -e "  ${GREEN}3.${NC} Schedule regular test runs"
else
    echo -e "  ${RED}1.${NC} Review failed tests"
    echo -e "  ${RED}2.${NC} Check screenshots in test_results/"
    echo -e "  ${RED}3.${NC} Fix issues and re-run tests"
fi

echo ""

# Exit with pytest's exit code
exit ${TEST_EXIT_CODE:-0}
