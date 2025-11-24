#!/bin/bash

# Comprehensive Chat Testing Script
# Tests all chat scenarios and identifies bugs/improvements

echo "======================================"
echo "COMPREHENSIVE CHAT TEST SUITE"
echo "======================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BACKEND_URL="http://localhost:8000"
TEST_SESSION_ID="test-session-$(date +%s)"
RESULTS_FILE="/tmp/chat_test_results_$(date +%Y%m%d_%H%M%S).json"

echo "Test Session ID: $TEST_SESSION_ID"
echo "Results will be saved to: $RESULTS_FILE"
echo ""

# Initialize results JSON
echo "{\"tests\": [], \"summary\": {}}" > $RESULTS_FILE

# Helper function to add test result
add_result() {
    local test_name="$1"
    local status="$2"
    local details="$3"

    jq --arg name "$test_name" --arg status "$status" --arg details "$details" \
       '.tests += [{name: $name, status: $status, details: $details, timestamp: now|todate}]' \
       $RESULTS_FILE > ${RESULTS_FILE}.tmp && mv ${RESULTS_FILE}.tmp $RESULTS_FILE
}

# Test 1: Health Check
echo "========================================"
echo "Test 1: Backend Health Check"
echo "========================================"
HEALTH=$(curl -s $BACKEND_URL/health)
if echo "$HEALTH" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}: Backend is healthy"
    add_result "Health Check" "PASS" "Backend responding correctly"
else
    echo -e "${RED}✗ FAIL${NC}: Backend health check failed"
    add_result "Health Check" "FAIL" "Backend not healthy: $HEALTH"
fi
echo ""

# Test 2: Direct LLM Question (General Knowledge)
echo "========================================"
echo "Test 2: Direct LLM (General Knowledge)"
echo "========================================"
echo "Query: 'What is the capital of France?'"
RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/query" \
    -F "query=What is the capital of France?" \
    -F "model_id=llama3.1:8b" \
    -F "use_cache=false")

ANSWER=$(echo "$RESPONSE" | jq -r '.answer // "ERROR"')
NUM_SOURCES=$(echo "$RESPONSE" | jq -r '.num_sources // 0')

echo "Answer: ${ANSWER:0:100}..."
echo "Sources: $NUM_SOURCES"

if echo "$ANSWER" | grep -iq "Paris"; then
    echo -e "${GREEN}✓ PASS${NC}: Correct answer for general knowledge"
    add_result "Direct LLM - General Knowledge" "PASS" "Answer mentions Paris"
else
    echo -e "${RED}✗ FAIL${NC}: Incorrect answer"
    add_result "Direct LLM - General Knowledge" "FAIL" "Answer: $ANSWER"
fi
echo ""

# Test 3: Document-Based Question (King Aadhan)
echo "========================================"
echo "Test 3: RAG Query - King Aadhan"
echo "========================================"
echo "Query: 'Who is King Aadhan?'"
RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/query" \
    -F "query=Who is King Aadhan?" \
    -F "model_id=llama3.1:8b" \
    -F "use_cache=false" \
    -F "top_k=10")

ANSWER=$(echo "$RESPONSE" | jq -r '.answer // "ERROR"')
NUM_SOURCES=$(echo "$RESPONSE" | jq -r '.num_sources // 0')
CLASSIFICATION=$(echo "$RESPONSE" | jq -r '.query_classification // "MISSING"')

echo "Answer: ${ANSWER:0:100}..."
echo "Sources: $NUM_SOURCES"
echo "Classification: $CLASSIFICATION"

if [ "$NUM_SOURCES" -gt 0 ]; then
    echo -e "${GREEN}✓ PASS${NC}: Found sources for King Aadhan"
    add_result "RAG - King Aadhan" "PASS" "Sources: $NUM_SOURCES"
else
    echo -e "${RED}✗ FAIL${NC}: No sources found"
    add_result "RAG - King Aadhan" "FAIL" "0 sources, Answer: ${ANSWER:0:100}"
fi

if [ "$CLASSIFICATION" == "MISSING" ] || [ "$CLASSIFICATION" == "null" ]; then
    echo -e "${YELLOW}⚠ WARNING${NC}: Classification field missing"
fi
echo ""

# Test 4: Short Query Variation (just "Aadhan")
echo "========================================"
echo "Test 4: RAG Query - Short Form 'Aadhan'"
echo "========================================"
echo "Query: 'Who is Aadhan?'"
RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/query" \
    -F "query=Who is Aadhan?" \
    -F "model_id=llama3.1:8b" \
    -F "use_cache=false" \
    -F "top_k=10")

ANSWER=$(echo "$RESPONSE" | jq -r '.answer // "ERROR"')
NUM_SOURCES=$(echo "$RESPONSE" | jq -r '.num_sources // 0')
CHUNKS=$(echo "$RESPONSE" | jq -r '.metadata.chunks_retrieved // 0')

echo "Answer: ${ANSWER:0:100}..."
echo "Sources: $NUM_SOURCES"
echo "Chunks Retrieved: $CHUNKS"

# Check if answer talks about King or the story (correct) vs Aadhaar ID (wrong)
if echo "$ANSWER" | grep -iq "king\|ruler\|kingdom\|story"; then
    echo -e "${GREEN}✓ PASS${NC}: Correct context (story/kingdom)"
    add_result "RAG - Aadhan Short Form" "PASS" "Found correct context, Sources: $NUM_SOURCES"
elif echo "$ANSWER" | grep -iq "aadhaar\|identification\|biometric"; then
    echo -e "${RED}✗ FAIL${NC}: Wrong context - talking about Aadhaar ID instead of King"
    add_result "RAG - Aadhan Short Form" "FAIL" "Returned Aadhaar ID info instead of King Aadhan"
else
    echo -e "${YELLOW}⚠ WARNING${NC}: Unclear context"
    add_result "RAG - Aadhan Short Form" "WARNING" "Answer unclear, Sources: $NUM_SOURCES"
fi
echo ""

# Test 5: Document-Based Question (Vishwanath Anand)
echo "========================================"
echo "Test 5: RAG Query - Vishwanath Anand"
echo "========================================"
echo "Query: 'Who is Vishwanath Anand?'"
RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/query" \
    -F "query=Who is Vishwanath Anand?" \
    -F "model_id=llama3.1:8b" \
    -F "use_cache=false")

ANSWER=$(echo "$RESPONSE" | jq -r '.answer // "ERROR"')
NUM_SOURCES=$(echo "$RESPONSE" | jq -r '.num_sources // 0')

echo "Answer: ${ANSWER:0:100}..."
echo "Sources: $NUM_SOURCES"

if [ "$NUM_SOURCES" -gt 0 ] && echo "$ANSWER" | grep -iq "chess\|grandmaster"; then
    echo -e "${GREEN}✓ PASS${NC}: Found sources and correct answer"
    add_result "RAG - Vishwanath Anand" "PASS" "Sources: $NUM_SOURCES"
else
    echo -e "${RED}✗ FAIL${NC}: Issue with retrieval or answer"
    add_result "RAG - Vishwanath Anand" "FAIL" "Sources: $NUM_SOURCES, Answer: ${ANSWER:0:100}"
fi
echo ""

# Test 6: Multi-Strategy RAG
echo "========================================"
echo "Test 6: Multi-Strategy RAG - King Aadhan"
echo "========================================"
RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/multi-strategy/query-form" \
    -F "query=Who is King Aadhan?" \
    -F "model_id=llama3.1:8b" \
    -F "enable_direct_llm=true" \
    -F "enable_rag_short_term=true" \
    -F "enable_rag_long_term=true")

SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false')
STRATEGY=$(echo "$RESPONSE" | jq -r '.strategy_used // "NONE"')
SCORE=$(echo "$RESPONSE" | jq -r '.final_score // 0')
CANDIDATES=$(echo "$RESPONSE" | jq -r '.metadata.candidates_evaluated // 0')

echo "Success: $SUCCESS"
echo "Strategy Used: $STRATEGY"
echo "Final Score: $SCORE"
echo "Candidates Evaluated: $CANDIDATES"

if [ "$SUCCESS" == "true" ]; then
    echo -e "${GREEN}✓ PASS${NC}: Multi-strategy executed successfully"
    add_result "Multi-Strategy RAG" "PASS" "Strategy: $STRATEGY, Score: $SCORE"
else
    echo -e "${RED}✗ FAIL${NC}: Multi-strategy failed"
    add_result "Multi-Strategy RAG" "FAIL" "Response: $(echo $RESPONSE | jq -c .)"
fi

if [ "$CANDIDATES" -lt 3 ]; then
    echo -e "${YELLOW}⚠ WARNING${NC}: Only $CANDIDATES candidates evaluated (expected 3)"
fi
echo ""

# Test 7: Session Management
echo "========================================"
echo "Test 7: Session Management"
echo "========================================"
echo "Using session: $TEST_SESSION_ID"

# Query 1 with session
RESPONSE1=$(curl -s -X POST "$BACKEND_URL/api/v1/query" \
    -F "query=Remember: My favorite color is blue" \
    -F "session_id=$TEST_SESSION_ID" \
    -F "model_id=llama3.1:8b" \
    -F "use_cache=false")

echo "Set session context: 'My favorite color is blue'"

# Query 2 - try to recall
RESPONSE2=$(curl -s -X POST "$BACKEND_URL/api/v1/query" \
    -F "query=What is my favorite color?" \
    -F "session_id=$TEST_SESSION_ID" \
    -F "model_id=llama3.1:8b" \
    -F "use_cache=false")

ANSWER2=$(echo "$RESPONSE2" | jq -r '.answer // "ERROR"')
echo "Recall attempt: ${ANSWER2:0:100}..."

if echo "$ANSWER2" | grep -iq "blue"; then
    echo -e "${GREEN}✓ PASS${NC}: Session context maintained"
    add_result "Session Management" "PASS" "Successfully recalled session context"
else
    echo -e "${YELLOW}⚠ WARNING${NC}: Session context may not be working"
    add_result "Session Management" "WARNING" "Could not recall session context"
fi
echo ""

# Test 8: Cache Behavior
echo "========================================"
echo "Test 8: Cache Behavior"
echo "========================================"

# First query (should not be cached)
START1=$(date +%s%N)
RESPONSE1=$(curl -s -X POST "$BACKEND_URL/api/v1/query" \
    -F "query=What is quantum computing?" \
    -F "model_id=llama3.1:8b" \
    -F "use_cache=false")
END1=$(date +%s%N)
LATENCY1=$((($END1 - $START1) / 1000000))
CACHED1=$(echo "$RESPONSE1" | jq -r '.cached // false')

echo "Query 1 - Latency: ${LATENCY1}ms, Cached: $CACHED1"

# Second query (might be cached if caching enabled)
START2=$(date +%s%N)
RESPONSE2=$(curl -s -X POST "$BACKEND_URL/api/v1/query" \
    -F "query=What is quantum computing?" \
    -F "model_id=llama3.1:8b")
END2=$(date +%s%N)
LATENCY2=$((($END2 - $START2) / 1000000))
CACHED2=$(echo "$RESPONSE2" | jq -r '.cached // false')

echo "Query 2 - Latency: ${LATENCY2}ms, Cached: $CACHED2"

if [ "$CACHED2" == "true" ] && [ "$LATENCY2" -lt "$LATENCY1" ]; then
    echo -e "${GREEN}✓ PASS${NC}: Caching working as expected"
    add_result "Cache Behavior" "PASS" "Cache hit on repeat query, latency improved"
else
    echo -e "${YELLOW}⚠ INFO${NC}: Cache behavior: Query1=${LATENCY1}ms, Query2=${LATENCY2}ms"
    add_result "Cache Behavior" "INFO" "L1: ${LATENCY1}ms, L2: ${LATENCY2}ms, Cached: $CACHED2"
fi
echo ""

# Test 9: Error Handling - Invalid Model
echo "========================================"
echo "Test 9: Error Handling - Invalid Model"
echo "========================================"
RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/query" \
    -F "query=Test" \
    -F "model_id=nonexistent-model-12345")

STATUS=$(echo "$RESPONSE" | jq -r '.error // .detail // "NO_ERROR"')

if [ "$STATUS" != "NO_ERROR" ]; then
    echo -e "${GREEN}✓ PASS${NC}: Error handled correctly"
    add_result "Error Handling - Invalid Model" "PASS" "Returned error as expected"
else
    echo -e "${YELLOW}⚠ WARNING${NC}: Should return error for invalid model"
    add_result "Error Handling - Invalid Model" "WARNING" "No error returned"
fi
echo ""

# Test 10: Empty Query
echo "========================================"
echo "Test 10: Error Handling - Empty Query"
echo "========================================"
RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/query" \
    -F "query=" \
    -F "model_id=llama3.1:8b")

STATUS=$(echo "$RESPONSE" | jq -r '.error // .detail // "NO_ERROR"')

if [ "$STATUS" != "NO_ERROR" ]; then
    echo -e "${GREEN}✓ PASS${NC}: Empty query rejected"
    add_result "Error Handling - Empty Query" "PASS" "Validation working"
else
    echo -e "${YELLOW}⚠ WARNING${NC}: Should validate empty queries"
    add_result "Error Handling - Empty Query" "WARNING" "Empty query not validated"
fi
echo ""

# Test 11: Response Structure Validation
echo "========================================"
echo "Test 11: Response Structure Validation"
echo "========================================"
RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/query" \
    -F "query=What is AI?" \
    -F "model_id=llama3.1:8b" \
    -F "use_cache=false")

REQUIRED_FIELDS=("answer" "num_sources" "latency_ms" "metadata")
MISSING=0

for field in "${REQUIRED_FIELDS[@]}"; do
    if echo "$RESPONSE" | jq -e ".$field" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Field '$field' present"
    else
        echo -e "${RED}✗${NC} Field '$field' MISSING"
        MISSING=$((MISSING + 1))
    fi
done

if [ $MISSING -eq 0 ]; then
    echo -e "${GREEN}✓ PASS${NC}: All required fields present"
    add_result "Response Structure" "PASS" "All fields present"
else
    echo -e "${RED}✗ FAIL${NC}: $MISSING required fields missing"
    add_result "Response Structure" "FAIL" "$MISSING fields missing"
fi
echo ""

# Test 12: Classification Field Check
echo "========================================"
echo "Test 12: Classification Field Check"
echo "========================================"
RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/query" \
    -F "query=Who is Albert Einstein?" \
    -F "model_id=llama3.1:8b" \
    -F "use_cache=false")

CLASSIFICATION=$(echo "$RESPONSE" | jq -r '.query_classification // "MISSING"')
CONFIDENCE=$(echo "$RESPONSE" | jq -r '.classification_confidence // "MISSING"')

echo "Classification: $CLASSIFICATION"
echo "Confidence: $CONFIDENCE"

if [ "$CLASSIFICATION" != "MISSING" ] && [ "$CLASSIFICATION" != "null" ]; then
    echo -e "${GREEN}✓ PASS${NC}: Classification field populated"
    add_result "Classification Field" "PASS" "Classification: $CLASSIFICATION"
else
    echo -e "${RED}✗ FAIL${NC}: Classification field missing or null"
    add_result "Classification Field" "FAIL" "BUG: Classification not populated"
fi
echo ""

# Generate Summary
echo "========================================"
echo "TEST SUMMARY"
echo "========================================"

TOTAL=$(jq '.tests | length' $RESULTS_FILE)
PASSED=$(jq '[.tests[] | select(.status == "PASS")] | length' $RESULTS_FILE)
FAILED=$(jq '[.tests[] | select(.status == "FAIL")] | length' $RESULTS_FILE)
WARNINGS=$(jq '[.tests[] | select(.status == "WARNING" or .status == "INFO")] | length' $RESULTS_FILE)

echo "Total Tests: $TOTAL"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"

# Update summary in results file
jq --arg total "$TOTAL" --arg passed "$PASSED" --arg failed "$FAILED" --arg warnings "$WARNINGS" \
   '.summary = {total: ($total|tonumber), passed: ($passed|tonumber), failed: ($failed|tonumber), warnings: ($warnings|tonumber)}' \
   $RESULTS_FILE > ${RESULTS_FILE}.tmp && mv ${RESULTS_FILE}.tmp $RESULTS_FILE

echo ""
echo "Detailed results saved to: $RESULTS_FILE"
echo ""

# Print failed tests
if [ "$FAILED" -gt 0 ]; then
    echo "========================================"
    echo "FAILED TESTS (ACTION REQUIRED)"
    echo "========================================"
    jq -r '.tests[] | select(.status == "FAIL") | "\(.name): \(.details)"' $RESULTS_FILE
    echo ""
fi

# Print warnings
if [ "$WARNINGS" -gt 0 ]; then
    echo "========================================"
    echo "WARNINGS (REVIEW RECOMMENDED)"
    echo "========================================"
    jq -r '.tests[] | select(.status == "WARNING" or .status == "INFO") | "\(.name): \(.details)"' $RESULTS_FILE
    echo ""
fi

echo "Test execution complete!"
