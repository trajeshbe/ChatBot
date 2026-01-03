#!/bin/bash

# Customer Solutions Comprehensive Test Runner
# Tests all 6 POCs: British Council, CRU, Grant Thornton, GT Motive, Solera, Construction Monitor

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Customer Solutions - Comprehensive Test Suite${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check backend is running
echo -e "${YELLOW}→ Checking backend status...${NC}"
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${RED}❌ Backend not running. Start with: docker-compose up -d backend${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Backend is running${NC}"
echo ""

# Run pytest with coverage
echo -e "${YELLOW}→ Running comprehensive test suite...${NC}"
cd backend

pytest tests/customer_solutions/test_customer_solutions_comprehensive.py \
    -v \
    --tb=short \
    --color=yes \
    --durations=10 \
    --cov=app.tier_3.customer_solutions \
    --cov-report=term-missing \
    --cov-report=html:htmlcov/customer_solutions

TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}  ✓ ALL TESTS PASSED${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo ""
    echo -e "Coverage report: file://$(pwd)/htmlcov/customer_solutions/index.html"
else
    echo -e "${RED}================================================${NC}"
    echo -e "${RED}  ✗ SOME TESTS FAILED${NC}"
    echo -e "${RED}================================================${NC}"
fi

exit $TEST_EXIT_CODE
