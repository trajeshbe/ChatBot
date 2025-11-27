#!/bin/bash
# Phase 6 Comprehensive Tests

echo "🧪 Phase 6 - Tool Discovery & MCP APIs Test Report"
echo "=================================================="
echo ""

PASS=0
FAIL=0

# Test 1: List all tools
echo "Test 1: GET /api/v1/tools - List all tools"
RESPONSE=$(curl -s -w "\nHTTP:%{http_code}" http://localhost:8000/api/v1/tools)
CODE=$(echo "$RESPONSE" | grep "HTTP:" | cut -d: -f2)
if [ "$CODE" = "200" ]; then
    TOOLS=$(echo "$RESPONSE" | grep -v "HTTP:" | jq -r '.total')
    echo "  ✅ PASS (HTTP 200) - Found $TOOLS tools"
    PASS=$((PASS + 1))
else
    echo "  ❌ FAIL (HTTP $CODE)"
    FAIL=$((FAIL + 1))
fi

# Test 2: Filter enabled tools only
echo ""
echo "Test 2: GET /api/v1/tools?enabled_only=true"
RESPONSE=$(curl -s -w "\nHTTP:%{http_code}" "http://localhost:8000/api/v1/tools?enabled_only=true")
CODE=$(echo "$RESPONSE" | grep "HTTP:" | cut -d: -f2)
if [ "$CODE" = "200" ]; then
    ENABLED=$(echo "$RESPONSE" | grep -v "HTTP:" | jq -r '.enabled')
    echo "  ✅ PASS (HTTP 200) - $ENABLED enabled tools"
    PASS=$((PASS + 1))
else
    echo "  ❌ FAIL (HTTP $CODE)"
    FAIL=$((FAIL + 1))
fi

# Test 3: Get tool statistics
echo ""
echo "Test 3: GET /api/v1/tools/statistics"
RESPONSE=$(curl -s -w "\nHTTP:%{http_code}" http://localhost:8000/api/v1/tools/statistics)
CODE=$(echo "$RESPONSE" | grep "HTTP:" | cut -d: -f2)
if [ "$CODE" = "200" ]; then
    TOTAL=$(echo "$RESPONSE" | grep -v "HTTP:" | jq -r '.total_tools')
    BUILTIN=$(echo "$RESPONSE" | grep -v "HTTP:" | jq -r '.builtin_tools')
    echo "  ✅ PASS (HTTP 200) - $TOTAL total, $BUILTIN built-in"
    PASS=$((PASS + 1))
else
    echo "  ❌ FAIL (HTTP $CODE)"
    FAIL=$((FAIL + 1))
fi

# Test 4: List categories
echo ""
echo "Test 4: GET /api/v1/tools/categories/list"
RESPONSE=$(curl -s -w "\nHTTP:%{http_code}" http://localhost:8000/api/v1/tools/categories/list)
CODE=$(echo "$RESPONSE" | grep "HTTP:" | cut -d: -f2)
if [ "$CODE" = "200" ]; then
    CATS=$(echo "$RESPONSE" | grep -v "HTTP:" | jq -r 'length')
    echo "  ✅ PASS (HTTP 200) - $CATS categories"
    PASS=$((PASS + 1))
else
    echo "  ❌ FAIL (HTTP $CODE)"
    FAIL=$((FAIL + 1))
fi

# Test 5: Get specific tool
echo ""
echo "Test 5: GET /api/v1/tools/document_rag"
RESPONSE=$(curl -s -w "\nHTTP:%{http_code}" http://localhost:8000/api/v1/tools/document_rag)
CODE=$(echo "$RESPONSE" | grep "HTTP:" | cut -d: -f2)
if [ "$CODE" = "200" ]; then
    NAME=$(echo "$RESPONSE" | grep -v "HTTP:" | jq -r '.name')
    echo "  ✅ PASS (HTTP 200) - Tool: $NAME"
    PASS=$((PASS + 1))
else
    echo "  ❌ FAIL (HTTP $CODE)"
    FAIL=$((FAIL + 1))
fi

# Test 6: Get tools in LLM format
echo ""
echo "Test 6: GET /api/v1/tools/llm/format"
RESPONSE=$(curl -s -w "\nHTTP:%{http_code}" "http://localhost:8000/api/v1/tools/llm/format?enabled_only=true")
CODE=$(echo "$RESPONSE" | grep "HTTP:" | cut -d: -f2)
if [ "$CODE" = "200" ]; then
    COUNT=$(echo "$RESPONSE" | grep -v "HTTP:" | jq -r 'length')
    echo "  ✅ PASS (HTTP 200) - $COUNT tools in LLM format"
    PASS=$((PASS + 1))
else
    echo "  ❌ FAIL (HTTP $CODE)"
    FAIL=$((FAIL + 1))
fi

# Test 7: MCP Provider Status
echo ""
echo "Test 7: GET /api/v1/mcp/provider/status"
RESPONSE=$(curl -s -w "\nHTTP:%{http_code}" http://localhost:8000/api/v1/mcp/provider/status)
CODE=$(echo "$RESPONSE" | grep "HTTP:" | cut -d: -f2)
if [ "$CODE" = "200" ] || [ "$CODE" = "503" ]; then
    echo "  ✅ PASS (HTTP $CODE) - Expected (200=enabled, 503=not installed)"
    PASS=$((PASS + 1))
else
    echo "  ❌ FAIL (HTTP $CODE)"
    FAIL=$((FAIL + 1))
fi

# Test 8: Error handling - non-existent tool
echo ""
echo "Test 8: GET /api/v1/tools/nonexistent_tool (expect 404)"
RESPONSE=$(curl -s -w "\nHTTP:%{http_code}" http://localhost:8000/api/v1/tools/nonexistent_tool)
CODE=$(echo "$RESPONSE" | grep "HTTP:" | cut -d: -f2)
if [ "$CODE" = "404" ]; then
    echo "  ✅ PASS (HTTP 404) - Error handling works"
    PASS=$((PASS + 1))
else
    echo "  ❌ FAIL (HTTP $CODE - expected 404)"
    FAIL=$((FAIL + 1))
fi

echo ""
echo "=================================================="
echo "📊 Test Results Summary"
echo "=================================================="
echo "Total Tests: $((PASS + FAIL))"
echo "✅ Passed: $PASS"
echo "❌ Failed: $FAIL"
RATE=$((PASS * 100 / (PASS + FAIL)))
echo "Success Rate: $RATE%"
echo ""
if [ $FAIL -eq 0 ]; then
    echo "🎉 All Phase 6 tests PASSED!"
else
    echo "⚠️  Some tests failed - review above"
fi
