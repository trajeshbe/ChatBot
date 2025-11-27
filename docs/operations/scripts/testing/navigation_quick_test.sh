#!/bin/bash

echo "🧪 Quick Navigation Agent Test"
echo "=============================="
echo ""

# Test 1: Fantasy Books
echo "Test 1: Navigate to Fantasy category"
curl -s -X POST http://localhost:8000/api/v1/extract/ultra-smart \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://books.toscrape.com/",
    "user_instructions": "get all books under Fantasy",
    "llm_provider": "openai",
    "model_id": "gpt-4-turbo"
  }' | jq -r '
    "✅ Success: \(.success)",
    "📚 Books found: \(.row_count)",
    "🔗 Navigation: \(.extraction_metadata.metadata.navigation_path | join(" → "))",
    "📖 First book: \(.table[0].title) - \(.table[0].price)"
  '

echo ""
echo "=============================="
echo "✅ Test complete!"
