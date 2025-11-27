#!/bin/bash

echo "=========================================================================="
echo "TESTING SCRAPING COMPLIANCE ENFORCEMENT"
echo "=========================================================================="
echo ""

# Test 1: httpbin.org (SHOULD BE ALLOWED)
echo "Test 1: Scraping httpbin.org (should be ALLOWED)"
echo "----------------------------------------------------------------------"
curl -s -X POST http://localhost:8000/api/v1/extract/ultra-smart \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://httpbin.org/html",
    "user_instructions": "Extract the page title",
    "source_type": "url",
    "llm_provider": "openai"
  }' > /tmp/httpbin_test.json

if jq -e '.success' /tmp/httpbin_test.json > /dev/null 2>&1; then
    echo "✅ SUCCESS: httpbin.org was scraped successfully"
    echo "   Compliance status: ALLOWED"
else
    echo "❌ BLOCKED: httpbin.org scraping failed"
    echo "   Error: $(jq -r '.error // .detail // "Unknown error"' /tmp/httpbin_test.json)"
fi

echo ""
echo ""

# Test 2: amazon.com (SHOULD BE BLOCKED)
echo "Test 2: Scraping amazon.com (should be BLOCKED)"
echo "----------------------------------------------------------------------"
curl -s -X POST http://localhost:8000/api/v1/extract/ultra-smart \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.amazon.com/",
    "user_instructions": "Extract product information",
    "source_type": "url",
    "llm_provider": "openai"
  }' > /tmp/amazon_test.json

if jq -e '.success' /tmp/amazon_test.json > /dev/null 2>&1; then
    echo "❌ ERROR: amazon.com was scraped (should have been blocked!)"
    echo "   Compliance enforcement NOT working"
else
    echo "✅ CORRECTLY BLOCKED: amazon.com scraping was prevented"
    echo "   Reason: $(jq -r '.error // .detail // "Unknown error"' /tmp/amazon_test.json)"
fi

echo ""
echo ""

# Test 3: Check scraping configs in database
echo "Test 3: Checking scraping configurations in database"
echo "----------------------------------------------------------------------"
docker-compose exec -T postgres psql -U postgres -d ragchatbot << 'SQL'
SELECT 
    domain, 
    allow_scraping, 
    status, 
    notes 
FROM scraping_configs 
WHERE domain IN ('httpbin.org', 'amazon.com', 'www.amazon.com')
ORDER BY domain;
SQL

