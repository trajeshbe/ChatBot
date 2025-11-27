#!/bin/bash

echo "=========================================="
echo "UI → Backend Flow Test"
echo "=========================================="
echo ""

API_URL="http://localhost:8000"

# Test 1: Change top_k and verify chunk retrieval
echo "=== TEST 1: Change top_k from 5 to 10 ==="
echo ""

# Get baseline with default top_k=5
echo "1a. Query with DEFAULT top_k=5:"
curl -s -X POST "$API_URL/api/v1/query" \
  -F "query=Tell me about machine learning" \
  -F "use_cache=false" | jq -r '"Chunks retrieved: " + (.metadata.chunks_retrieved // 0 | tostring)'

echo ""
echo "1b. Update top_k to 10 via API:"
curl -s -X POST "$API_URL/api/v1/config/weights" \
  -H "Content-Type: application/json" \
  -d '{"rag_settings": {"top_k": 10}}' | jq '{success: .success, message: .message}'

echo ""
echo "1c. Query again with NEW top_k=10:"
curl -s -X POST "$API_URL/api/v1/query" \
  -F "query=Tell me about machine learning" \
  -F "use_cache=false" | jq -r '"Chunks retrieved: " + (.metadata.chunks_retrieved // 0 | tostring)'

echo ""
echo "1d. Reset top_k back to 5:"
curl -s -X POST "$API_URL/api/v1/config/weights" \
  -H "Content-Type: application/json" \
  -d '{"rag_settings": {"top_k": 5}}' | jq -r '.message'

echo ""
echo "=========================================="
echo "=== TEST 2: Change strategy weight ==="
echo "=========================================="
echo ""

# Test 2: Change direct_llm weight
echo "2a. Query with DEFAULT direct_llm weight (0.75):"
RESPONSE=$(curl -s -X POST "$API_URL/api/v1/query" \
  -F "query=What is 2+2?" \
  -F "use_cache=false")
echo "$RESPONSE" | jq -r '"Routing: " + (.metadata.routing_strategy // "unknown"), "Answer: " + (.answer[:80] // "N/A")'

echo ""
echo "2b. Update direct_llm weight to 1.5 (prefer direct LLM):"
curl -s -X POST "$API_URL/api/v1/config/weights" \
  -H "Content-Type: application/json" \
  -d '{"strategy_weights": {"direct_llm": 1.5}}' | jq '{success: .success, message: .message}'

echo ""
echo "2c. Verify weight was updated:"
curl -s "$API_URL/api/v1/config/weights" | jq '.data.strategy_weights.direct_llm'

echo ""
echo "2d. Reset direct_llm weight back to 0.75:"
curl -s -X POST "$API_URL/api/v1/config/weights" \
  -H "Content-Type: application/json" \
  -d '{"strategy_weights": {"direct_llm": 0.75}}' | jq -r '.message'

echo ""
echo "=========================================="
echo "=== TEST 3: Change similarity threshold ==="
echo "=========================================="
echo ""

# Test 3: Change similarity threshold
echo "3a. Get DEFAULT similarity threshold:"
curl -s "$API_URL/api/v1/config/weights" | jq '.data.similarity_thresholds.default'

echo ""
echo "3b. Update similarity threshold to 0.40 (more lenient):"
curl -s -X POST "$API_URL/api/v1/config/weights" \
  -H "Content-Type: application/json" \
  -d '{"similarity_thresholds": {"default": 0.40}}' | jq '{success: .success, message: .message}'

echo ""
echo "3c. Verify threshold was updated:"
curl -s "$API_URL/api/v1/config/weights" | jq '.data.similarity_thresholds.default'

echo ""
echo "3d. Reset similarity threshold back to 0.60:"
curl -s -X POST "$API_URL/api/v1/config/weights" \
  -H "Content-Type: application/json" \
  -d '{"similarity_thresholds": {"default": 0.60}}' | jq -r '.message'

echo ""
echo "=========================================="
echo "✅ UI → Backend Flow Tests Complete"
echo "=========================================="
