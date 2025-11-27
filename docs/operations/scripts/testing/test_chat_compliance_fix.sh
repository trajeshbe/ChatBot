#!/bin/bash

echo "=================================================================="
echo "🧪 TESTING CHAT INTERFACE COMPLIANCE ENFORCEMENT (AFTER FIX)"
echo "=================================================================="
echo ""

# Wait for backend to be fully ready
echo "⏳ Waiting for backend to be ready..."
sleep 5

# Test 1: Chat interface should ALLOW httpbin.org
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 1: Chat with httpbin.org (SHOULD BE ALLOWED)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

curl -s -X POST http://localhost:8000/api/v1/query \
  -F "query=Can you scrape https://httpbin.org/html and tell me what you find?" \
  -F "model_id=gpt-4" \
  -o /tmp/chat_httpbin_test.json

echo "Response received. Analyzing..."
echo ""

# Check if it successfully scraped
HTTPBIN_ANSWER=$(jq -r '.answer' /tmp/chat_httpbin_test.json 2>/dev/null || echo "")

if echo "$HTTPBIN_ANSWER" | grep -qi "cannot\|unable\|blocked\|not allowed"; then
    echo "❌ FAILED: httpbin.org was blocked (should have been allowed!)"
    echo "   Answer: $HTTPBIN_ANSWER" | head -c 200
else
    echo "✅ PASSED: httpbin.org was allowed to be scraped"
    echo "   Answer preview: $HTTPBIN_ANSWER" | head -c 200
fi

echo ""
echo ""

# Test 2: Chat interface should BLOCK amazon.com
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 2: Chat with amazon.com (SHOULD BE BLOCKED)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

curl -s -X POST http://localhost:8000/api/v1/query \
  -F "query=Can you scrape https://www.amazon.com/ and tell me about products?" \
  -F "model_id=gpt-4" \
  -o /tmp/chat_amazon_test.json

echo "Response received. Analyzing..."
echo ""

# Check if it was properly blocked
AMAZON_ANSWER=$(jq -r '.answer' /tmp/chat_amazon_test.json 2>/dev/null || echo "")
AMAZON_TOOL_SUCCESS=$(jq -r '.metadata.tool_usage.tool_execution_summary.web_scraper.success // false' /tmp/chat_amazon_test.json 2>/dev/null)
AMAZON_TOOL_ERROR=$(jq -r '.metadata.tool_usage.tool_execution_summary.web_scraper.error // ""' /tmp/chat_amazon_test.json 2>/dev/null)

echo "Tool execution success: $AMAZON_TOOL_SUCCESS"
echo "Tool execution error: $AMAZON_TOOL_ERROR"
echo ""

if [ "$AMAZON_TOOL_SUCCESS" == "false" ] && echo "$AMAZON_TOOL_ERROR" | grep -qi "scraping not allowed\|no scraping configuration\|compliance"; then
    echo "✅ PASSED: amazon.com was correctly blocked by compliance"
    echo "   Error: $AMAZON_TOOL_ERROR"
else
    echo "❌ FAILED: amazon.com was NOT properly blocked!"
    echo "   Tool success: $AMAZON_TOOL_SUCCESS"
    echo "   Tool error: $AMAZON_TOOL_ERROR"
    echo "   Answer preview: $AMAZON_ANSWER" | head -c 200
fi

echo ""
echo ""

# Test 3: Check database for any new amazon scrapes
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 3: Verifying no Amazon documents were created"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

RECENT_AMAZON_DOCS=$(docker-compose exec -T postgres psql -U postgres -d ragchatbot -c \
  "SELECT COUNT(*) FROM documents WHERE source_url LIKE '%amazon.com%' AND upload_date > NOW() - INTERVAL '5 minutes';" \
  2>/dev/null | grep -E "^\s+[0-9]+" | tr -d ' ')

echo "Amazon documents created in last 5 minutes: $RECENT_AMAZON_DOCS"

if [ "$RECENT_AMAZON_DOCS" == "0" ]; then
    echo "✅ PASSED: No Amazon documents were created"
else
    echo "❌ FAILED: Found $RECENT_AMAZON_DOCS Amazon documents created recently!"
fi

echo ""
echo ""

# Summary
echo "=================================================================="
echo "📊 TEST SUMMARY"
echo "=================================================================="
echo ""
echo "If all tests passed, compliance enforcement is now working universally"
echo "across ALL scraping methods (direct API + chat interface)!"
echo ""

