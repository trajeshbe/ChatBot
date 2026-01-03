#!/bin/bash

# Tier 3 POCs Validation Script
# Tests all six POCs (British Council, CRU, Grant Thornton, GT Motive, Solera, Construction Monitor)
# Date: 2026-01-02

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test result arrays
declare -a FAILED_TESTS

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Tier 3 Customer POCs Validation Test Suite${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Function to print test result
print_result() {
    local test_name=$1
    local status=$2
    local message=$3

    TESTS_RUN=$((TESTS_RUN + 1))

    if [ "$status" == "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC} - $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    elif [ "$status" == "FAIL" ]; then
        echo -e "${RED}✗ FAIL${NC} - $test_name"
        echo -e "  ${RED}Error: $message${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        FAILED_TESTS+=("$test_name: $message")
    elif [ "$status" == "WARN" ]; then
        echo -e "${YELLOW}⚠ WARN${NC} - $test_name"
        echo -e "  ${YELLOW}Warning: $message${NC}"
    fi
}

# Function to test API endpoint
test_endpoint() {
    local endpoint=$1
    local test_name=$2

    local response=$(curl -s -o /dev/null -w "%{http_code}" "$endpoint" 2>&1)

    if [ "$response" == "200" ]; then
        print_result "$test_name" "PASS" ""
        return 0
    else
        print_result "$test_name" "FAIL" "HTTP $response"
        return 1
    fi
}

# Function to test JSON endpoint with field check
test_json_endpoint() {
    local endpoint=$1
    local test_name=$2
    local expected_field=$3
    local expected_value=$4

    local response=$(curl -s "$endpoint" 2>&1)
    local http_code=$(curl -s -o /dev/null -w "%{http_code}" "$endpoint" 2>&1)

    if [ "$http_code" != "200" ]; then
        print_result "$test_name" "FAIL" "HTTP $http_code"
        return 1
    fi

    local field_value=$(echo "$response" | jq -r ".$expected_field" 2>/dev/null)

    if [ "$field_value" == "$expected_value" ]; then
        print_result "$test_name" "PASS" ""
        return 0
    else
        print_result "$test_name" "FAIL" "Expected $expected_field='$expected_value', got '$field_value'"
        return 1
    fi
}

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  1. Backend Health Check${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

test_endpoint "http://localhost:8000/health" "Backend Health Endpoint"
test_endpoint "http://localhost:8000/api/docs" "API Documentation (Swagger)"

echo ""
echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  2. British Council POC${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Test British Council status endpoint
test_json_endpoint \
    "http://localhost:8000/api/v1/customer/british_council/status" \
    "British Council Status - Operational" \
    "status" \
    "operational"

# Test British Council description
DESCRIPTION=$(curl -s http://localhost:8000/api/v1/customer/british_council/status | jq -r '.description' 2>/dev/null)
if [[ "$DESCRIPTION" == *"course recommendations"* ]]; then
    print_result "British Council Description Accuracy" "PASS" ""
else
    print_result "British Council Description Accuracy" "FAIL" "Description doesn't mention course recommendations"
fi

# Test British Council modules
MODULES=$(curl -s http://localhost:8000/api/v1/customer/british_council/status | jq -r '.tier_2_modules_used[]' 2>/dev/null | wc -l)
if [ "$MODULES" -ge 3 ]; then
    print_result "British Council Tier 2 Modules (≥3)" "PASS" ""
else
    print_result "British Council Tier 2 Modules (≥3)" "FAIL" "Only $MODULES modules listed"
fi

echo ""
echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  3. CRU Mining Intelligence POC${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Test CRU status endpoint
test_json_endpoint \
    "http://localhost:8000/api/v1/customer/cru/status" \
    "CRU Status - Operational" \
    "status" \
    "operational"

# Test CRU mode detection
DESCRIPTION=$(curl -s http://localhost:8000/api/v1/customer/cru/status | jq -r '.description' 2>/dev/null)
if [[ "$DESCRIPTION" == *"pgvector-only mode"* ]] || [[ "$DESCRIPTION" == *"Multi-pipeline"* ]]; then
    print_result "CRU Mode Detection" "PASS" ""
else
    print_result "CRU Mode Detection" "FAIL" "Description doesn't indicate mode: $DESCRIPTION"
fi

# Check for Elasticsearch availability indicator
CAPABILITIES=$(curl -s http://localhost:8000/api/v1/customer/cru/status | jq -r '.capabilities[]' 2>/dev/null)
if echo "$CAPABILITIES" | grep -q "Elasticsearch unavailable" || echo "$CAPABILITIES" | grep -q "BM25"; then
    print_result "CRU Elasticsearch Status Indicator" "PASS" ""
else
    print_result "CRU Elasticsearch Status Indicator" "WARN" "No clear ES status in capabilities"
fi

# Test CRU reranker
if echo "$CAPABILITIES" | grep -q "rerank"; then
    print_result "CRU Reranker Capability Listed" "PASS" ""
else
    print_result "CRU Reranker Capability Listed" "FAIL" "Reranking not listed in capabilities"
fi

echo ""
echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  4. Grant Thornton POC${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Test Grant Thornton status endpoint
test_json_endpoint \
    "http://localhost:8000/api/v1/customer/grant_thornton/status" \
    "Grant Thornton Status - Operational" \
    "status" \
    "operational"

# Test Grant Thornton description
DESCRIPTION=$(curl -s http://localhost:8000/api/v1/customer/grant_thornton/status | jq -r '.description' 2>/dev/null)
if [[ "$DESCRIPTION" == *"Financial"* ]] || [[ "$DESCRIPTION" == *"audit"* ]]; then
    print_result "Grant Thornton Description Accuracy" "PASS" ""
else
    print_result "Grant Thornton Description Accuracy" "FAIL" "Description doesn't mention financial/audit"
fi

# Test Grant Thornton modules
MODULES=$(curl -s http://localhost:8000/api/v1/customer/grant_thornton/status | jq -r '.tier_2_modules_used[]' 2>/dev/null | wc -l)
if [ "$MODULES" -ge 2 ]; then
    print_result "Grant Thornton Tier 2 Modules (≥2)" "PASS" ""
else
    print_result "Grant Thornton Tier 2 Modules (≥2)" "FAIL" "Only $MODULES modules listed"
fi

echo ""
echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  5. GT Motive POC${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Test GT Motive status endpoint
test_json_endpoint \
    "http://localhost:8000/api/v1/customer/gt_motive/status" \
    "GT Motive Status - Operational" \
    "status" \
    "operational"

# Test GT Motive description
DESCRIPTION=$(curl -s http://localhost:8000/api/v1/customer/gt_motive/status | jq -r '.description' 2>/dev/null)
if [[ "$DESCRIPTION" == *"automotive"* ]] || [[ "$DESCRIPTION" == *"part"* ]] || [[ "$DESCRIPTION" == *"damage"* ]]; then
    print_result "GT Motive Description Accuracy" "PASS" ""
else
    print_result "GT Motive Description Accuracy" "WARN" "Description doesn't mention automotive/parts"
fi

# Test GT Motive modules
MODULES=$(curl -s http://localhost:8000/api/v1/customer/gt_motive/status | jq -r '.tier_2_modules_used[]' 2>/dev/null | wc -l)
if [ "$MODULES" -ge 1 ]; then
    print_result "GT Motive Tier 2 Modules (≥1)" "PASS" ""
else
    print_result "GT Motive Tier 2 Modules (≥1)" "FAIL" "Only $MODULES modules listed"
fi

echo ""
echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  6. Solera POC${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Test Solera status endpoint
test_json_endpoint \
    "http://localhost:8000/api/v1/customer/solera/status" \
    "Solera Status - Operational" \
    "status" \
    "operational"

# Test Solera description
DESCRIPTION=$(curl -s http://localhost:8000/api/v1/customer/solera/status | jq -r '.description' 2>/dev/null)
if [[ "$DESCRIPTION" == *"insurance"* ]] || [[ "$DESCRIPTION" == *"claims"* ]] || [[ "$DESCRIPTION" == *"workflow"* ]]; then
    print_result "Solera Description Accuracy" "PASS" ""
else
    print_result "Solera Description Accuracy" "WARN" "Description doesn't mention insurance/claims"
fi

# Test Solera modules
MODULES=$(curl -s http://localhost:8000/api/v1/customer/solera/status | jq -r '.tier_2_modules_used[]' 2>/dev/null | wc -l)
if [ "$MODULES" -ge 1 ]; then
    print_result "Solera Tier 2 Modules (≥1)" "PASS" ""
else
    print_result "Solera Tier 2 Modules (≥1)" "FAIL" "Only $MODULES modules listed"
fi

echo ""
echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  7. Construction Monitor POC${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Test Construction Monitor status endpoint
test_json_endpoint \
    "http://localhost:8000/api/v1/customer/construction_monitor/status" \
    "Construction Monitor Status - Operational" \
    "status" \
    "operational"

# Test Construction Monitor description
DESCRIPTION=$(curl -s http://localhost:8000/api/v1/customer/construction_monitor/status | jq -r '.description' 2>/dev/null)
if [[ "$DESCRIPTION" == *"construction"* ]] || [[ "$DESCRIPTION" == *"project"* ]] || [[ "$DESCRIPTION" == *"monitor"* ]]; then
    print_result "Construction Monitor Description Accuracy" "PASS" ""
else
    print_result "Construction Monitor Description Accuracy" "WARN" "Description doesn't mention construction/project"
fi

# Test Construction Monitor modules
MODULES=$(curl -s http://localhost:8000/api/v1/customer/construction_monitor/status | jq -r '.tier_2_modules_used[]' 2>/dev/null | wc -l)
if [ "$MODULES" -ge 1 ]; then
    print_result "Construction Monitor Tier 2 Modules (≥1)" "PASS" ""
else
    print_result "Construction Monitor Tier 2 Modules (≥1)" "FAIL" "Only $MODULES modules listed"
fi

echo ""
echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  8. Frontend Validation${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Test frontend accessibility
test_endpoint "http://localhost:3001" "Frontend Accessibility"

# Test if frontend is actually serving React (check for typical React patterns)
FRONTEND_CONTENT=$(curl -s http://localhost:3001 2>&1)
if echo "$FRONTEND_CONTENT" | grep -q "root" && echo "$FRONTEND_CONTENT" | grep -q "script"; then
    print_result "Frontend React App Structure" "PASS" ""
else
    print_result "Frontend React App Structure" "WARN" "Frontend content doesn't match expected React structure"
fi

echo ""
echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  9. Integration Tests${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Test that all six POCs have unique descriptions
BC_DESC=$(curl -s http://localhost:8000/api/v1/customer/british_council/status | jq -r '.description' 2>/dev/null)
CRU_DESC=$(curl -s http://localhost:8000/api/v1/customer/cru/status | jq -r '.description' 2>/dev/null)
GT_DESC=$(curl -s http://localhost:8000/api/v1/customer/grant_thornton/status | jq -r '.description' 2>/dev/null)
GTM_DESC=$(curl -s http://localhost:8000/api/v1/customer/gt_motive/status | jq -r '.description' 2>/dev/null)
SOL_DESC=$(curl -s http://localhost:8000/api/v1/customer/solera/status | jq -r '.description' 2>/dev/null)
CM_DESC=$(curl -s http://localhost:8000/api/v1/customer/construction_monitor/status | jq -r '.description' 2>/dev/null)

UNIQUE_COUNT=$(echo -e "$BC_DESC\n$CRU_DESC\n$GT_DESC\n$GTM_DESC\n$SOL_DESC\n$CM_DESC" | sort -u | wc -l)

if [ "$UNIQUE_COUNT" -eq 6 ]; then
    print_result "All 6 POCs Have Unique Descriptions" "PASS" ""
else
    print_result "All 6 POCs Have Unique Descriptions" "WARN" "Only $UNIQUE_COUNT unique descriptions found"
fi

# Test response times
echo ""
echo -e "${BLUE}Response Time Tests:${NC}"

for POC in "british_council" "cru" "grant_thornton" "gt_motive" "solera" "construction_monitor"; do
    START=$(date +%s%N)
    curl -s "http://localhost:8000/api/v1/customer/${POC}/status" > /dev/null
    END=$(date +%s%N)
    ELAPSED=$((($END - $START) / 1000000)) # Convert to milliseconds

    if [ "$ELAPSED" -lt 500 ]; then
        print_result "${POC} Response Time (<500ms)" "PASS" "Actual: ${ELAPSED}ms"
    elif [ "$ELAPSED" -lt 1000 ]; then
        print_result "${POC} Response Time (<500ms)" "WARN" "Slow response: ${ELAPSED}ms"
    else
        print_result "${POC} Response Time (<500ms)" "FAIL" "Very slow response: ${ELAPSED}ms"
    fi
done

echo ""
echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  Test Results Summary${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

echo -e "Total Tests Run:    ${BLUE}$TESTS_RUN${NC}"
echo -e "Tests Passed:       ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed:       ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=====================================${NC}"
    echo -e "${GREEN}  ✓ ALL TESTS PASSED${NC}"
    echo -e "${GREEN}=====================================${NC}"
    echo ""
    exit 0
else
    echo ""
    echo -e "${RED}=====================================${NC}"
    echo -e "${RED}  ✗ SOME TESTS FAILED${NC}"
    echo -e "${RED}=====================================${NC}"
    echo ""
    echo -e "${RED}Failed Tests:${NC}"
    for test in "${FAILED_TESTS[@]}"; do
        echo -e "  ${RED}- $test${NC}"
    done
    echo ""
    exit 1
fi
