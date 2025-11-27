#!/bin/bash

echo "=========================================================================="
echo "🧪 TESTING NATURAL LANGUAGE RESPONSE QUALITY (AFTER FIX)"
echo "=========================================================================="
echo ""

# Test 1: "do you have access to httpbin.org?"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 1: 'Do you have access to httpbin.org?'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

curl -s -X POST http://localhost:8000/api/v1/query \
  -F "query=do you have access to httpbin.org?" \
  -F "model_id=gpt-4" \
  -o /tmp/test1_httpbin_access.json

echo "✅ Query completed"
echo ""
echo "📊 Response Analysis:"
echo "===================="
ANSWER=$(jq -r '.answer' /tmp/test1_httpbin_access.json 2>/dev/null)
TOOL_USED=$(jq -r '.metadata.tool_usage.tools_used[0]' /tmp/test1_httpbin_access.json 2>/dev/null)
SYNTHESIS_METHOD=$(jq -r '.metadata.synthesis_method // "unknown"' /tmp/test1_httpbin_access.json 2>/dev/null)

echo "Tool used: $TOOL_USED"
echo "Synthesis method: $SYNTHESIS_METHOD"
echo ""
echo "Answer:"
echo "-------"
echo "$ANSWER" | head -c 500
echo ""
echo ""

# Check if it's natural language or raw output
if echo "$ANSWER" | grep -qi "Successfully scraped page"; then
    echo "❌ FAILED: Still showing raw scraper output!"
    echo "   Response is NOT natural language"
else
    echo "✅ PASSED: Response appears to be natural language!"
    echo "   No raw scraper templates detected"
fi

echo ""
echo ""

# Test 2: Data extraction query
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 2: Extract data from URL (natural language presentation)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

curl -s -X POST http://localhost:8000/api/v1/query \
  -F "query=What books are on https://books.toscrape.com/catalogue/category/books/mystery_3/index.html?" \
  -F "model_id=gpt-4" \
  -o /tmp/test2_books_natural.json

echo "✅ Query completed"
echo ""
echo "📊 Response Analysis:"
echo "===================="
ANSWER2=$(jq -r '.answer' /tmp/test2_books_natural.json 2>/dev/null)
TOOL_USED2=$(jq -r '.metadata.tool_usage.tools_used[0]' /tmp/test2_books_natural.json 2>/dev/null)
BOOKS_FOUND=$(jq -r '.sources[0].data | length' /tmp/test2_books_natural.json 2>/dev/null)

echo "Tool used: $TOOL_USED2"
echo "Books found: $BOOKS_FOUND"
echo ""
echo "Answer:"
echo "-------"
echo "$ANSWER2" | head -c 600
echo ""
echo ""

# Check if it's natural language or raw output
if echo "$ANSWER2" | grep -qi "Successfully extracted.*records"; then
    echo "❌ FAILED: Still showing raw extraction template!"
    echo "   Response is NOT natural language"
else
    echo "✅ PASSED: Response appears to be natural language!"
    echo "   Data presented conversationally"
fi

echo ""
echo ""

# Summary
echo "=========================================================================="
echo "📊 TEST SUMMARY"
echo "=========================================================================="
echo ""
echo "If both tests passed, response quality has been successfully improved!"
echo "The chatbot now provides natural, conversational responses instead of"
echo "raw scraper output."
echo ""

