#!/bin/bash

echo "=================================================================================="
echo "COMPREHENSIVE SCRAPING COMPLIANCE ENFORCEMENT TEST"
echo "Testing ALL scraper methods to ensure universal compliance"
echo "=================================================================================="
echo ""

PASS_COUNT=0
FAIL_COUNT=0

# Test 1: Ultra-Smart Extraction - httpbin.org (SHOULD BE ALLOWED)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1: Ultra-Smart Extraction - httpbin.org (SHOULD BE ALLOWED)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s -X POST http://localhost:8000/api/v1/extract/ultra-smart \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://httpbin.org/html",
    "user_instructions": "Extract the page title",
    "source_type": "url",
    "llm_provider": "openai"
  }' > /tmp/test1_httpbin_ultra.json

if jq -e '.success' /tmp/test1_httpbin_ultra.json > /dev/null 2>&1; then
    echo "✅ PASS: httpbin.org scraped via ultra-smart"
    ((PASS_COUNT++))
else
    echo "❌ FAIL: httpbin.org blocked (should be allowed)"
    echo "   Error: $(jq -r '.error' /tmp/test1_httpbin_ultra.json)"
    ((FAIL_COUNT++))
fi
echo ""

# Test 2: Ultra-Smart Extraction - amazon.com (SHOULD BE BLOCKED)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 2: Ultra-Smart Extraction - amazon.com (SHOULD BE BLOCKED)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s -X POST http://localhost:8000/api/v1/extract/ultra-smart \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.amazon.com/",
    "user_instructions": "Extract products",
    "source_type": "url",
    "llm_provider": "openai"
  }' > /tmp/test2_amazon_ultra.json

if jq -e '.success' /tmp/test2_amazon_ultra.json > /dev/null 2>&1; then
    echo "❌ FAIL: amazon.com scraped (should be blocked!)"
    ((FAIL_COUNT++))
else
    echo "✅ PASS: amazon.com correctly blocked via ultra-smart"
    echo "   Reason: $(jq -r '.error' /tmp/test2_amazon_ultra.json | head -1)"
    ((PASS_COUNT++))
fi
echo ""

# Test 3: Simple Web Scraper - httpbin.org (SHOULD BE ALLOWED)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 3: Simple Web Scraper - httpbin.org (SHOULD BE ALLOWED)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s -X POST http://localhost:8000/api/v1/scraper/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://httpbin.org/html",
    "scrape_prompt": "Extract page content"
  }' > /tmp/test3_httpbin_simple.json

if jq -e '.success' /tmp/test3_httpbin_simple.json > /dev/null 2>&1; then
    echo "✅ PASS: httpbin.org scraped via simple scraper"
    ((PASS_COUNT++))
else
    echo "❌ FAIL: httpbin.org blocked (should be allowed)"
    echo "   Error: $(jq -r '.error' /tmp/test3_httpbin_simple.json)"
    ((FAIL_COUNT++))
fi
echo ""

# Test 4: Simple Web Scraper - amazon.com (SHOULD BE BLOCKED)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 4: Simple Web Scraper - amazon.com (SHOULD BE BLOCKED)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s -X POST http://localhost:8000/api/v1/scraper/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.amazon.com/",
    "scrape_prompt": "Extract products"
  }' > /tmp/test4_amazon_simple.json

if jq -e '.success' /tmp/test4_amazon_simple.json > /dev/null 2>&1; then
    echo "❌ FAIL: amazon.com scraped (should be blocked!)"
    ((FAIL_COUNT++))
else
    echo "✅ PASS: amazon.com correctly blocked via simple scraper"
    echo "   Reason: $(jq -r '.error' /tmp/test4_amazon_simple.json | head -1)"
    ((PASS_COUNT++))
fi
echo ""

# Test 5: Bulk Web Scraper - Mixed URLs (PARTIAL ALLOWED)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 5: Bulk Web Scraper - Mixed URLs (httpbin ALLOWED, amazon BLOCKED)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s -X POST http://localhost:8000/api/v1/scraper/scrape/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://httpbin.org/html",
      "https://www.amazon.com/"
    ],
    "scrape_prompt": "Extract content"
  }' > /tmp/test5_bulk_mixed.json

TOTAL=$(jq -r '.total' /tmp/test5_bulk_mixed.json)
SUCCESSFUL=$(jq -r '.successful' /tmp/test5_bulk_mixed.json)
FAILED=$(jq -r '.failed' /tmp/test5_bulk_mixed.json)

if [ "$TOTAL" -eq 2 ] && [ "$SUCCESSFUL" -eq 1 ] && [ "$FAILED" -eq 1 ]; then
    echo "✅ PASS: Bulk scraper correctly allowed httpbin and blocked amazon"
    echo "   Total: $TOTAL | Successful: $SUCCESSFUL | Failed: $FAILED"
    
    # Check which URL succeeded
    HTTPBIN_SUCCESS=$(jq -r '.results[] | select(.url | contains("httpbin")) | .success' /tmp/test5_bulk_mixed.json)
    AMAZON_SUCCESS=$(jq -r '.results[] | select(.url | contains("amazon")) | .success' /tmp/test5_bulk_mixed.json)
    
    if [ "$HTTPBIN_SUCCESS" == "true" ] && [ "$AMAZON_SUCCESS" == "false" ]; then
        echo "   ✓ httpbin.org: ALLOWED"
        echo "   ✓ amazon.com: BLOCKED"
        ((PASS_COUNT++))
    else
        echo "❌ FAIL: Incorrect filtering - httpbin=$HTTPBIN_SUCCESS, amazon=$AMAZON_SUCCESS"
        ((FAIL_COUNT++))
    fi
else
    echo "❌ FAIL: Unexpected results - Total: $TOTAL, Successful: $SUCCESSFUL, Failed: $FAILED"
    ((FAIL_COUNT++))
fi
echo ""

# Summary
echo "=================================================================================="
echo "TEST SUMMARY"
echo "=================================================================================="
echo "✅ Passed: $PASS_COUNT"
echo "❌ Failed: $FAIL_COUNT"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo "🎉 ALL TESTS PASSED! Compliance enforcement is working across ALL scraper methods!"
    exit 0
else
    echo "⚠️  Some tests failed. Please review the output above."
    exit 1
fi
