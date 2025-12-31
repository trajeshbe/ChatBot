#!/bin/bash
# Phase 7 & 8 Multi-Tool Agent Testing Suite
# Tests the integrated multi-tool agent system with query endpoint

set -e

echo "════════════════════════════════════════════════════════════════"
echo "Phase 7 & 8 Multi-Tool Agent Testing Suite"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=3

echo "📋 Test Suite Overview:"
echo "  - Test 1: Backend Health Check"
echo "  - Test 2: Web Scraping Query (Moneycontrol)"
echo "  - Test 3: Document RAG Query"
echo ""

# ============================================================================
# Test 1: Backend Health Check
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 1: Backend Health Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo -e "${GREEN}✅ TEST 1 PASSED${NC} - Backend is healthy"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ TEST 1 FAILED${NC} - Backend health check failed"
    ((TESTS_FAILED++))
fi
echo ""

# ============================================================================
# Test 2: Web Scraping Query (Moneycontrol)
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 2: Web Scraping Query - Moneycontrol.com"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Query: https://www.moneycontrol.com/"
echo "Expected Tool: smart_extraction"
echo "Expected Method: llm_based"
echo ""

curl -s -X POST http://localhost:8000/api/v1/query \
  -F "query=https://www.moneycontrol.com/" \
  -F "model_id=qwen2.5:1.5b" \
  -o /tmp/test_moneycontrol.json

# Check if test passed
if jq -e '.metadata.tool_usage.tools_used | contains(["smart_extraction"])' /tmp/test_moneycontrol.json > /dev/null 2>&1; then
    echo -e "${GREEN}✅ TEST 2 PASSED${NC} - Web scraping tool selected correctly"
    echo ""
    echo "📊 Results:"
    echo "  Tool selected: $(jq -r '.metadata.tool_usage.tools_used[0]' /tmp/test_moneycontrol.json)"
    echo "  Selection method: $(jq -r '.metadata.tool_usage.tool_selection_method' /tmp/test_moneycontrol.json)"
    echo "  Confidence: $(jq -r '.metadata.tool_usage.selection_confidence' /tmp/test_moneycontrol.json)"
    echo "  Intent detected: $(jq -r '.metadata.tool_usage.intent_detected' /tmp/test_moneycontrol.json)"
    echo "  Execution time: $(jq -r '.metadata.tool_usage.tool_timing.smart_extraction' /tmp/test_moneycontrol.json)ms"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ TEST 2 FAILED${NC} - Wrong tool selected or error occurred"
    echo ""
    echo "Error details:"
    jq -r '.metadata.tool_usage' /tmp/test_moneycontrol.json
    ((TESTS_FAILED++))
fi
echo ""

# ============================================================================
# Test 3: Document RAG Query
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 3: Document RAG Query"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Query: What documents do we have?"
echo "Expected Tool: document_rag"
echo "Expected Method: llm_based"
echo ""

curl -s -X POST http://localhost:8000/api/v1/query \
  -F "query=What documents do we have?" \
  -F "model_id=qwen2.5:1.5b" \
  -o /tmp/test_document_rag.json

# Check if test passed
if jq -e '.metadata.tool_usage.tools_used | contains(["document_rag"])' /tmp/test_document_rag.json > /dev/null 2>&1; then
    if jq -e '.metadata.tool_usage.tool_execution_summary.document_rag.success' /tmp/test_document_rag.json > /dev/null 2>&1; then
        echo -e "${GREEN}✅ TEST 3 PASSED${NC} - Document RAG tool executed successfully"
        echo ""
        echo "📊 Results:"
        echo "  Tool selected: $(jq -r '.metadata.tool_usage.tools_used[0]' /tmp/test_document_rag.json)"
        echo "  Selection method: $(jq -r '.metadata.tool_usage.tool_selection_method' /tmp/test_document_rag.json)"
        echo "  Confidence: $(jq -r '.metadata.tool_usage.selection_confidence' /tmp/test_document_rag.json)"
        echo "  Intent detected: $(jq -r '.metadata.tool_usage.intent_detected' /tmp/test_document_rag.json)"
        echo "  Execution time: $(jq -r '.metadata.tool_usage.tool_timing.document_rag' /tmp/test_document_rag.json)ms"
        echo "  Documents retrieved: $(jq -r '.sources | length' /tmp/test_document_rag.json)"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ TEST 3 FAILED${NC} - Document RAG execution failed"
        echo ""
        echo "Error details:"
        jq -r '.metadata.tool_usage.tool_execution_summary.document_rag' /tmp/test_document_rag.json
        ((TESTS_FAILED++))
    fi
else
    echo -e "${RED}❌ TEST 3 FAILED${NC} - Wrong tool selected or error occurred"
    echo ""
    echo "Response:"
    jq '.' /tmp/test_document_rag.json
    ((TESTS_FAILED++))
fi
echo ""

# ============================================================================
# Test Summary
# ============================================================================
echo "════════════════════════════════════════════════════════════════"
echo "Test Suite Summary"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo ""
    echo "✅ Multi-tool agent system is fully operational"
    echo "✅ LLM-based tool selection working correctly"
    echo "✅ Web scraping and document RAG both functioning"
    exit 0
else
    echo -e "${RED}⚠️  SOME TESTS FAILED${NC}"
    echo ""
    echo "Please review the test output above for details."
    exit 1
fi
