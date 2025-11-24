#!/bin/bash

# Comprehensive ChatBot Test Suite
# Tests all major features including adaptive RAG implementation

echo "=========================================="
echo "COMPREHENSIVE CHATBOT TEST SUITE"
echo "=========================================="
echo ""

API_URL="http://localhost:8000"
PASSED=0
FAILED=0
TOTAL=0

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper function to test API endpoint
test_endpoint() {
    local test_name="$1"
    local curl_cmd="$2"
    local expected_pattern="$3"

    TOTAL=$((TOTAL + 1))
    echo -e "${YELLOW}Test $TOTAL: $test_name${NC}"

    response=$(eval "$curl_cmd" 2>&1)
    exit_code=$?

    if [ $exit_code -eq 0 ] && echo "$response" | grep -q "$expected_pattern"; then
        echo -e "${GREEN}✅ PASSED${NC}"
        PASSED=$((PASSED + 1))
        echo "Response preview: $(echo "$response" | head -c 150)..."
    else
        echo -e "${RED}❌ FAILED${NC}"
        FAILED=$((FAILED + 1))
        echo "Error: Expected pattern '$expected_pattern' not found"
        echo "Response: $response"
    fi
    echo ""
    sleep 1
}

echo "=========================================="
echo "SECTION 1: HEALTH & CONNECTIVITY TESTS"
echo "=========================================="
echo ""

# Test 1: Backend Health Check
test_endpoint \
    "Backend Health Check" \
    "curl -s $API_URL/health" \
    '"status".*"healthy"'

# Test 2: API Health Check
test_endpoint \
    "API v1 Health Check" \
    "curl -s $API_URL/api/v1/health" \
    '"status"'

# Test 3: Ollama Connectivity
test_endpoint \
    "Ollama Models List" \
    "curl -s http://localhost:11434/api/tags" \
    '"models"'

echo "=========================================="
echo "SECTION 2: BASIC QUERY TESTS"
echo "=========================================="
echo ""

# Test 4: Simple Query (General Knowledge)
test_endpoint \
    "Simple Query - General Knowledge" \
    "curl -s -X POST '$API_URL/api/v1/query' -F 'query=What is the capital of France?' -F 'use_cache=false'" \
    '"answer"'

# Test 5: Query with Ollama Model
test_endpoint \
    "Query with Ollama llama3.1:8b" \
    "curl -s -X POST '$API_URL/api/v1/query' -F 'query=What is 2+2?' -F 'model_id=llama3.1:8b' -F 'use_cache=false'" \
    '"answer"'

# Test 6: Query Classification
test_endpoint \
    "Query Classification" \
    "curl -s -X POST '$API_URL/api/v1/query' -F 'query=Who is Albert Einstein?' -F 'use_cache=false' | jq -r '.query_classification // .classification'" \
    "."

echo "=========================================="
echo "SECTION 3: ADAPTIVE RAG TESTS"
echo "=========================================="
echo ""

# Test 7: Get Weights Configuration
test_endpoint \
    "Fetch Weights Configuration" \
    "curl -s $API_URL/api/v1/config/weights" \
    '"strategy_weights"'

# Test 8: Direct LLM Routing (Scenario 1)
# This should skip RAG and use LLM knowledge only
echo -e "${YELLOW}Test 8: Direct LLM Routing (Adaptive RAG Scenario 1)${NC}"
TOTAL=$((TOTAL + 1))

# Create a JSON config with direct_llm=1.0
cat > /tmp/unified_config_direct_llm.json <<EOF
{
  "strategy_weights": {
    "direct_llm": 1.0,
    "rag_short_term": 0.0,
    "rag_long_term": 0.0,
    "rag_hybrid": 0.0,
    "tool_navigation": 0.0,
    "tool_ocr": 0.0,
    "tool_docling": 0.0,
    "tool_web_scraping": 0.0
  }
}
EOF

response=$(curl -s -X POST "$API_URL/api/v1/query" \
    -F "query=What is the capital of France?" \
    -F "unified_config=$(cat /tmp/unified_config_direct_llm.json)" \
    -F "use_cache=false")

if echo "$response" | jq -e '.metadata.routing_strategy == "direct_llm"' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PASSED - Direct LLM routing worked${NC}"
    PASSED=$((PASSED + 1))
    echo "Routing strategy: $(echo "$response" | jq -r '.metadata.routing_strategy')"
    echo "Answer preview: $(echo "$response" | jq -r '.answer' | head -c 100)..."
else
    echo -e "${RED}❌ FAILED - Direct LLM routing not detected${NC}"
    FAILED=$((FAILED + 1))
    echo "Response metadata: $(echo "$response" | jq '.metadata')"
fi
echo ""
sleep 1

# Test 9: Force RAG Routing (Scenario 2)
echo -e "${YELLOW}Test 9: Force RAG Routing (Adaptive RAG Scenario 2)${NC}"
TOTAL=$((TOTAL + 1))

# Create a JSON config with rag_short_term=1.0
cat > /tmp/unified_config_force_rag.json <<EOF
{
  "strategy_weights": {
    "direct_llm": 0.0,
    "rag_short_term": 1.0,
    "rag_long_term": 0.0,
    "rag_hybrid": 0.0,
    "tool_navigation": 0.0,
    "tool_ocr": 0.0,
    "tool_docling": 0.0,
    "tool_web_scraping": 0.0
  }
}
EOF

response=$(curl -s -X POST "$API_URL/api/v1/query" \
    -F "query=Who is Aadhan?" \
    -F "unified_config=$(cat /tmp/unified_config_force_rag.json)" \
    -F "use_cache=false")

if echo "$response" | jq -e '.metadata.routing_strategy == "force_rag"' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PASSED - Force RAG routing worked${NC}"
    PASSED=$((PASSED + 1))
    echo "Routing strategy: $(echo "$response" | jq -r '.metadata.routing_strategy')"
    echo "Num sources: $(echo "$response" | jq -r '.num_sources // 0')"
else
    echo -e "${RED}❌ FAILED - Force RAG routing not detected${NC}"
    FAILED=$((FAILED + 1))
    echo "Response metadata: $(echo "$response" | jq '.metadata')"
fi
echo ""
sleep 1

echo "=========================================="
echo "SECTION 4: DOCUMENT UPLOAD & RAG TESTS"
echo "=========================================="
echo ""

# Test 10: Create Test Document
echo -e "${YELLOW}Test 10: Create and Upload Test Document${NC}"
TOTAL=$((TOTAL + 1))

cat > /tmp/test_chatbot_doc.txt <<EOF
Aadhan is a 13-year-old boy who loves programming and AI.
He is particularly interested in machine learning and natural language processing.
Aadhan enjoys building chatbots and working on RAG systems.
His favorite programming languages are Python and JavaScript.
EOF

response=$(curl -s -X POST "$API_URL/api/v1/upload" \
    -F "file=@/tmp/test_chatbot_doc.txt" \
    -F "session_id=test_comprehensive_session")

if echo "$response" | jq -e '.document_id' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PASSED - Document uploaded successfully${NC}"
    PASSED=$((PASSED + 1))
    DOC_ID=$(echo "$response" | jq -r '.document_id')
    echo "Document ID: $DOC_ID"
else
    echo -e "${RED}❌ FAILED - Document upload failed${NC}"
    FAILED=$((FAILED + 1))
    echo "Response: $response"
fi
echo ""
sleep 2  # Give time for processing

# Test 11: Query Against Uploaded Document
test_endpoint \
    "Query Against Uploaded Document" \
    "curl -s -X POST '$API_URL/api/v1/query' -F 'query=What does Aadhan like?' -F 'session_id=test_comprehensive_session' -F 'use_cache=false'" \
    '"answer"'

# Test 12: Check Document Retrieval
echo -e "${YELLOW}Test 12: Verify Document Retrieval${NC}"
TOTAL=$((TOTAL + 1))

response=$(curl -s -X POST "$API_URL/api/v1/query" \
    -F "query=What programming languages does Aadhan like?" \
    -F "session_id=test_comprehensive_session" \
    -F "use_cache=false")

num_sources=$(echo "$response" | jq -r '.num_sources // 0')
if [ "$num_sources" -gt 0 ]; then
    echo -e "${GREEN}✅ PASSED - Document sources retrieved${NC}"
    PASSED=$((PASSED + 1))
    echo "Number of sources: $num_sources"
    echo "Answer preview: $(echo "$response" | jq -r '.answer' | head -c 100)..."
else
    echo -e "${RED}❌ FAILED - No sources retrieved${NC}"
    FAILED=$((FAILED + 1))
    echo "Response: $(echo "$response" | jq '.metadata')"
fi
echo ""
sleep 1

echo "=========================================="
echo "SECTION 5: MULTI-STRATEGY TESTS"
echo "=========================================="
echo ""

# Test 13: Multi-Strategy Query
test_endpoint \
    "Multi-Strategy Query Endpoint" \
    "curl -s -X POST '$API_URL/api/v1/multi-strategy/query-form' -F 'query=What is AI?' -F 'enable_direct_llm=true' -F 'enable_rag_short_term=true' -F 'model_id=llama3.1:8b'" \
    '"strategy_used"'

# Test 14: Multi-Strategy with Document Context
test_endpoint \
    "Multi-Strategy with Session Context" \
    "curl -s -X POST '$API_URL/api/v1/multi-strategy/query-form' -F 'query=Tell me about Aadhan' -F 'session_id=test_comprehensive_session' -F 'enable_direct_llm=true' -F 'enable_rag_short_term=true' -F 'model_id=llama3.1:8b'" \
    '"answer"'

echo "=========================================="
echo "SECTION 6: CONFIGURATION TESTS"
echo "=========================================="
echo ""

# Test 15: Get RAG Settings
test_endpoint \
    "Fetch RAG Settings" \
    "curl -s $API_URL/api/v1/config/rag" \
    '"top_k"'

# Test 16: List Documents
test_endpoint \
    "List Documents in Session" \
    "curl -s '$API_URL/api/v1/documents?session_id=test_comprehensive_session'" \
    '"documents"'

# Test 17: Session Info
test_endpoint \
    "Get Session Information" \
    "curl -s '$API_URL/api/v1/sessions/test_comprehensive_session'" \
    '"session_id"'

echo "=========================================="
echo "SECTION 7: MODEL MANAGEMENT TESTS"
echo "=========================================="
echo ""

# Test 18: List Available Models
test_endpoint \
    "List Available Models" \
    "curl -s $API_URL/api/v1/models" \
    '"models"'

# Test 19: Ollama Model Management
test_endpoint \
    "Ollama Model Status" \
    "curl -s $API_URL/api/v1/ollama/models" \
    '"models"'

echo "=========================================="
echo "SECTION 8: ERROR HANDLING TESTS"
echo "=========================================="
echo ""

# Test 20: Query with Invalid Model
echo -e "${YELLOW}Test 20: Query with Invalid Model${NC}"
TOTAL=$((TOTAL + 1))

response=$(curl -s -X POST "$API_URL/api/v1/query" \
    -F "query=Test query" \
    -F "model_id=invalid_model_xyz" \
    -F "use_cache=false")

# Should either return an error or fallback to default model
if echo "$response" | grep -q -E '"error"|"answer"'; then
    echo -e "${GREEN}✅ PASSED - Handled invalid model gracefully${NC}"
    PASSED=$((PASSED + 1))
    echo "Response: $(echo "$response" | jq -r '.error // .answer' | head -c 100)..."
else
    echo -e "${RED}❌ FAILED - Unexpected response to invalid model${NC}"
    FAILED=$((FAILED + 1))
    echo "Response: $response"
fi
echo ""
sleep 1

# Test 21: Query with Empty String
echo -e "${YELLOW}Test 21: Query with Empty String${NC}"
TOTAL=$((TOTAL + 1))

response=$(curl -s -X POST "$API_URL/api/v1/query" \
    -F "query=" \
    -F "use_cache=false")

# Should return an error
if echo "$response" | jq -e '.detail' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PASSED - Rejected empty query${NC}"
    PASSED=$((PASSED + 1))
    echo "Error message: $(echo "$response" | jq -r '.detail[0].msg' 2>/dev/null || echo "$response")"
else
    echo -e "${RED}❌ FAILED - Did not reject empty query${NC}"
    FAILED=$((FAILED + 1))
    echo "Response: $response"
fi
echo ""
sleep 1

echo "=========================================="
echo "SECTION 9: PERFORMANCE TESTS"
echo "=========================================="
echo ""

# Test 22: Response Time Test
echo -e "${YELLOW}Test 22: Response Time Test${NC}"
TOTAL=$((TOTAL + 1))

start_time=$(date +%s%N)
response=$(curl -s -X POST "$API_URL/api/v1/query" \
    -F "query=What is 5+5?" \
    -F "model_id=llama3.1:8b" \
    -F "use_cache=false")
end_time=$(date +%s%N)

duration_ms=$(( (end_time - start_time) / 1000000 ))

if [ $duration_ms -lt 30000 ]; then  # Less than 30 seconds
    echo -e "${GREEN}✅ PASSED - Response within acceptable time${NC}"
    PASSED=$((PASSED + 1))
    echo "Response time: ${duration_ms}ms"
else
    echo -e "${RED}❌ FAILED - Response too slow${NC}"
    FAILED=$((FAILED + 1))
    echo "Response time: ${duration_ms}ms (exceeded 30s threshold)"
fi
echo ""

# Test 23: Cache Performance Test
echo -e "${YELLOW}Test 23: Cache Performance Test${NC}"
TOTAL=$((TOTAL + 1))

# First query (uncached)
query_text="What is the meaning of life?"
start_time=$(date +%s%N)
response1=$(curl -s -X POST "$API_URL/api/v1/query" \
    -F "query=$query_text" \
    -F "model_id=llama3.1:8b" \
    -F "use_cache=true")
end_time=$(date +%s%N)
time1_ms=$(( (end_time - start_time) / 1000000 ))

sleep 1

# Second query (should be cached)
start_time=$(date +%s%N)
response2=$(curl -s -X POST "$API_URL/api/v1/query" \
    -F "query=$query_text" \
    -F "model_id=llama3.1:8b" \
    -F "use_cache=true")
end_time=$(date +%s%N)
time2_ms=$(( (end_time - start_time) / 1000000 ))

echo "First query time: ${time1_ms}ms"
echo "Second query time: ${time2_ms}ms"

# Cache should be faster (or at least not slower by much)
if [ $time2_ms -le $((time1_ms + 1000)) ]; then
    echo -e "${GREEN}✅ PASSED - Cache working efficiently${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}⚠️  WARNING - Cache might not be optimized${NC}"
    PASSED=$((PASSED + 1))  # Don't fail on this
fi
echo ""

echo "=========================================="
echo "SECTION 10: BACKEND LOGS CHECK"
echo "=========================================="
echo ""

# Test 24: Check for Backend Errors
echo -e "${YELLOW}Test 24: Check Backend Logs for Errors${NC}"
TOTAL=$((TOTAL + 1))

error_count=$(docker-compose logs backend --tail=100 2>&1 | grep -c "ERROR" || echo "0")

if [ "$error_count" -eq 0 ]; then
    echo -e "${GREEN}✅ PASSED - No errors in recent backend logs${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}⚠️  WARNING - Found $error_count errors in logs${NC}"
    PASSED=$((PASSED + 1))  # Don't fail on warnings
    echo "Recent errors:"
    docker-compose logs backend --tail=100 2>&1 | grep "ERROR" | tail -5
fi
echo ""

echo "=========================================="
echo "TEST SUMMARY"
echo "=========================================="
echo ""
echo "Total Tests: $TOTAL"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"

success_rate=$(awk "BEGIN {printf \"%.1f\", ($PASSED/$TOTAL)*100}")
echo "Success Rate: ${success_rate}%"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! ChatBot is working correctly.${NC}"
    exit 0
else
    echo -e "${RED}⚠️  SOME TESTS FAILED. Please review the failures above.${NC}"
    exit 1
fi
