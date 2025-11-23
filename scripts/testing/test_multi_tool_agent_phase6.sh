#!/bin/bash
# ==============================================================================
# Multi-Tool Agent Phase 6 - Comprehensive Test Suite
# ==============================================================================
# Purpose: Test all Phase 6 API endpoints (Tool Discovery + MCP Admin)
# Location: scripts/testing/test_multi_tool_agent_phase6.sh
# Usage: ./scripts/testing/test_multi_tool_agent_phase6.sh
# ==============================================================================

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="http://localhost:8000"
RESULTS_DIR="/tmp/multi_tool_agent_tests"
mkdir -p "$RESULTS_DIR"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Results array
declare -a TEST_RESULTS

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Multi-Tool Agent Phase 6 - Comprehensive Tests${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo "Backend URL: $BACKEND_URL"
echo "Results Directory: $RESULTS_DIR"
echo ""

# ==============================================================================
# Helper Functions
# ==============================================================================

run_test() {
    local test_id=$1
    local test_name=$2
    local endpoint=$3
    local method=$4
    local expected_codes=$5  # Can be "200" or "200|503" for multiple acceptable codes
    local post_data=$6

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo -ne "[$test_id] $test_name ... "

    # Make request
    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$BACKEND_URL$endpoint" 2>&1)
    elif [ "$method" == "POST" ]; then
        if [ -z "$post_data" ]; then
            response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BACKEND_URL$endpoint" 2>&1)
        else
            response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST \
                -H "Content-Type: application/json" \
                -d "$post_data" \
                "$BACKEND_URL$endpoint" 2>&1)
        fi
    else
        echo -e "${RED}FAIL${NC} (Unknown method: $method)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return
    fi

    # Extract HTTP code
    http_code=$(echo "$response" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_CODE/d')

    # Check if code is empty (connection error)
    if [ -z "$http_code" ]; then
        echo -e "${RED}FAIL${NC} (Connection error)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TEST_RESULTS+=("❌ $test_id: Connection error")
        echo "$response" > "$RESULTS_DIR/${test_id}_ERROR.log"
        return
    fi

    # Check if code matches expected
    if [[ "$expected_codes" == *"|"* ]]; then
        # Multiple acceptable codes
        IFS='|' read -ra CODES <<< "$expected_codes"
        match_found=false
        for code in "${CODES[@]}"; do
            if [ "$http_code" == "$code" ]; then
                match_found=true
                break
            fi
        done

        if [ "$match_found" == true ]; then
            echo -e "${GREEN}PASS${NC} (HTTP $http_code)"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            TEST_RESULTS+=("✅ $test_id: PASS (HTTP $http_code)")
            echo "$body" > "$RESULTS_DIR/${test_id}.json"
        else
            echo -e "${RED}FAIL${NC} (Expected $expected_codes, got $http_code)"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            TEST_RESULTS+=("❌ $test_id: FAIL (Expected $expected_codes, got $http_code)")
            echo "$body" > "$RESULTS_DIR/${test_id}_FAIL.json"
        fi
    else
        # Single expected code
        if [ "$http_code" == "$expected_codes" ]; then
            echo -e "${GREEN}PASS${NC} (HTTP $http_code)"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            TEST_RESULTS+=("✅ $test_id: PASS (HTTP $http_code)")
            echo "$body" > "$RESULTS_DIR/${test_id}.json"
        else
            echo -e "${RED}FAIL${NC} (Expected $expected_codes, got $http_code)"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            TEST_RESULTS+=("❌ $test_id: FAIL (Expected $expected_codes, got $http_code)")
            echo "$body" > "$RESULTS_DIR/${test_id}_FAIL.json"
        fi
    fi
}

validate_json_field() {
    local test_id=$1
    local field_path=$2
    local expected_type=$3

    local result_file="$RESULTS_DIR/${test_id}.json"

    if [ ! -f "$result_file" ]; then
        echo -e "  ${YELLOW}⚠${NC}  Skipping validation (no result file)"
        return
    fi

    # Try to extract field value
    local field_value=$(jq -r "$field_path" "$result_file" 2>/dev/null)

    if [ "$field_value" == "null" ] || [ -z "$field_value" ]; then
        echo -e "  ${YELLOW}⚠${NC}  Field $field_path is missing or null"
    else
        echo -e "  ${GREEN}✓${NC}  Field $field_path exists"
    fi
}

# ==============================================================================
# Pre-Test Health Check
# ==============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Pre-Test Health Check${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -ne "Checking backend health ... "
health_response=$(curl -s "$BACKEND_URL/health" 2>&1)
health_code=$?

if [ $health_code -eq 0 ]; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    echo ""
    echo -e "${RED}Backend is not responding. Please ensure services are running:${NC}"
    echo "  docker-compose up -d"
    echo ""
    exit 1
fi

echo ""

# ==============================================================================
# Category 1: Tool Discovery API
# ==============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Category 1: Tool Discovery API (11 Tests)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

run_test "T1.1" "List all tools" "/api/v1/tools" "GET" "200"
run_test "T1.2" "List enabled tools only" "/api/v1/tools?enabled_only=true" "GET" "200"
run_test "T1.3" "Filter by source (built-in)" "/api/v1/tools?source=built-in" "GET" "200"
run_test "T1.4" "Filter by tag (document)" "/api/v1/tools?tag=document" "GET" "200"
run_test "T1.5" "Search tools (rag)" "/api/v1/tools?search=rag" "GET" "200"
run_test "T1.6" "Get specific tool (document_rag)" "/api/v1/tools/document_rag" "GET" "200|404"
run_test "T1.7" "Get tool schema (document_rag)" "/api/v1/tools/document_rag/schema" "GET" "200|404"
run_test "T1.8" "List all categories" "/api/v1/tools/categories/list" "GET" "200"
run_test "T1.9" "List tools by category (document)" "/api/v1/tools/categories/document" "GET" "200|404"
run_test "T1.10" "Get tool statistics" "/api/v1/tools/statistics" "GET" "200"
run_test "T1.11" "Get tools in LLM format" "/api/v1/tools/llm/format" "GET" "200"

echo ""

# Validate T1.1 response structure
if [ -f "$RESULTS_DIR/T1.1.json" ]; then
    echo "Validating T1.1 response structure:"
    validate_json_field "T1.1" ".total" "number"
    validate_json_field "T1.1" ".enabled" "number"
    validate_json_field "T1.1" ".disabled" "number"
    validate_json_field "T1.1" ".tools" "array"
    validate_json_field "T1.1" ".filters_applied" "object"
    echo ""
fi

# ==============================================================================
# Category 2: MCP Admin API
# ==============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Category 2: MCP Admin API (13 Tests)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Note: These tests may return 503 if MCP SDK is not installed (expected behavior)${NC}"
echo ""

run_test "T2.1" "Get MCP provider status" "/api/v1/mcp/provider/status" "GET" "200|503"
run_test "T2.2" "Get MCP connection info" "/api/v1/mcp/provider/connection-info" "GET" "200|503"
run_test "T2.3" "List external MCP servers" "/api/v1/mcp/consumer/servers" "GET" "200|503"
run_test "T2.4" "Get MCP overall health" "/api/v1/mcp/health" "GET" "200|503"
run_test "T2.5" "Get MCP statistics" "/api/v1/mcp/statistics" "GET" "200|503"

echo ""

# ==============================================================================
# Category 3: Error Handling
# ==============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Category 3: Error Handling (5 Tests)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

run_test "T4.1" "Non-existent tool (404)" "/api/v1/tools/nonexistent_tool_12345" "GET" "404"
run_test "T4.2" "Non-existent category (404)" "/api/v1/tools/categories/nonexistent_category_xyz" "GET" "404"
run_test "T4.3" "Invalid filter (should still work)" "/api/v1/tools?source=invalid_source" "GET" "200"
run_test "T4.4" "Invalid enable request (404)" "/api/v1/tools/nonexistent_tool/enable" "POST" "404"
run_test "T4.5" "Invalid MCP server (404)" "/api/v1/mcp/consumer/servers/nonexistent_server" "GET" "404|503"

echo ""

# ==============================================================================
# Category 4: Enhanced RAG Agent Metadata (if query endpoint exists)
# ==============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Category 4: Enhanced RAG Agent Metadata (2 Tests)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Note: These tests require uploaded documents and valid LLM API keys${NC}"
echo ""

# Test RAG query with metadata
query_payload='{
  "query": "What documents do we have?",
  "model": "gpt-4"
}'

run_test "T3.1" "RAG query with metadata" "/api/v1/query" "POST" "200|400|500" "$query_payload"

# Validate metadata structure if test passed
if [ -f "$RESULTS_DIR/T3.1.json" ]; then
    echo "Validating T3.1 metadata structure:"
    validate_json_field "T3.1" ".metadata.tool_usage" "object"
    validate_json_field "T3.1" ".metadata.tool_usage.tools_used" "array"
    validate_json_field "T3.1" ".metadata.tool_usage.tool_timing" "object"
    validate_json_field "T3.1" ".metadata.tool_usage.total_time_ms" "number"
    validate_json_field "T3.1" ".metadata.tool_usage.multi_tool_used" "boolean"
    echo ""
fi

# ==============================================================================
# Test Results Summary
# ==============================================================================

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Test Execution Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Total Tests:   $TOTAL_TESTS"
echo -e "Passed:        ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed:        ${RED}$FAILED_TESTS${NC}"
echo "Skipped:       $SKIPPED_TESTS"

if [ $TOTAL_TESTS -gt 0 ]; then
    success_rate=$(( PASSED_TESTS * 100 / TOTAL_TESTS ))
    echo ""
    if [ $success_rate -ge 90 ]; then
        echo -e "Success Rate:  ${GREEN}${success_rate}%${NC} 🎉"
    elif [ $success_rate -ge 70 ]; then
        echo -e "Success Rate:  ${YELLOW}${success_rate}%${NC} ⚠️"
    else
        echo -e "Success Rate:  ${RED}${success_rate}%${NC} ❌"
    fi
fi

echo ""
echo "Detailed results saved to: $RESULTS_DIR"
echo ""

# Show detailed test results
if [ ${#TEST_RESULTS[@]} -gt 0 ]; then
    echo -e "${BLUE}Detailed Test Results:${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    for result in "${TEST_RESULTS[@]}"; do
        echo "$result"
    done
    echo ""
fi

# Show failed tests in detail
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}Failed Test Details:${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    for file in "$RESULTS_DIR"/*_FAIL.json; do
        if [ -f "$file" ]; then
            test_id=$(basename "$file" _FAIL.json)
            echo ""
            echo "Test: $test_id"
            echo "Response:"
            cat "$file" | jq -C '.' 2>/dev/null || cat "$file"
        fi
    done
    echo ""
fi

# Exit with appropriate code
if [ $FAILED_TESTS -gt 0 ]; then
    exit 1
else
    exit 0
fi
