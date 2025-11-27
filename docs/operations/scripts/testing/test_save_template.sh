#!/bin/bash

echo "📋 Testing Save Template Feature"
echo "================================"
echo ""

# 1. List current templates
echo "1️⃣  Current templates in database:"
curl -s http://localhost:8000/api/v1/extract/saved-templates | jq '.templates[] | {name, display_name, source}'

echo ""
echo ""

# 2. Save a new template
echo "2️⃣  Saving a test template..."
SAVE_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/extract/save-template \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "test_website",
    "display_name": "Test Website Template",
    "description": "Testing save template functionality",
    "url_pattern": "example.com/*",
    "wait_for_selector": ".content",
    "fields": [
      {
        "name": "Title",
        "selector": "h1.title",
        "data_type": "text",
        "required": true
      },
      {
        "name": "Description",
        "selector": "p.desc",
        "data_type": "text",
        "required": false
      }
    ]
  }')

echo "$SAVE_RESPONSE" | jq '.'

echo ""
echo ""

# 3. List templates again to see the new one
echo "3️⃣  Updated template list (should include 'Test Website Template'):"
curl -s http://localhost:8000/api/v1/extract/saved-templates | jq '.templates[] | {name, display_name, source}'

echo ""
echo ""
echo "✅ Test complete! Check if 'Test Website Template' appears in the list above."
