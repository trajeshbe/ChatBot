#!/bin/bash

echo "=========================================================================="
echo "TESTING SCRAPING COMPLIANCE INTEGRATION"
echo "=========================================================================="
echo ""

# Test 1: Try to scrape BLOCKED site (amazon.com)
echo "Test 1: Attempting to scrape BLOCKED site (amazon.com)"
echo "----------------------------------------------------------------------"
curl -s -X POST http://localhost:8000/api/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://www.amazon.com/"],
    "session_id": "test-compliance"
  }' | jq '.'

echo ""
echo ""

# Test 2: Try to scrape ALLOWED site (books.toscrape.com)
echo "Test 2: Attempting to scrape ALLOWED site (books.toscrape.com)"
echo "----------------------------------------------------------------------"
curl -s -X POST http://localhost:8000/api/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://books.toscrape.com/"],
    "session_id": "test-compliance"
  }' > /tmp/allowed_scrape_result.json

jq '{
  success: .[0].success,
  url: .[0].url,
  compliance_checked: .[0].compliance.checked,
  compliance_status: .[0].compliance.status,
  rate_limited: .[0].compliance.rate_limited,
  content_length: .[0].content_length
}' /tmp/allowed_scrape_result.json

echo ""
echo ""

# Test 3: Check audit logs
echo "Test 3: Checking audit logs for our test attempts"
echo "----------------------------------------------------------------------"
curl -s "http://localhost:8000/api/v1/admin/scraping-audit-logs?limit=5" | jq '{
  count: .count,
  recent_attempts: [.logs[] | {
    domain: .domain,
    success: .success,
    robots_txt_allowed: .robots_txt_allowed,
    rate_limit_respected: .rate_limit_respected,
    created_at: .created_at
  }]
}'

echo ""
echo ""

# Test 4: Check domain statistics
echo "Test 4: Checking domain statistics for books.toscrape.com"
echo "----------------------------------------------------------------------"
curl -s "http://localhost:8000/api/v1/admin/domain-statistics/books.toscrape.com" | jq '.'

