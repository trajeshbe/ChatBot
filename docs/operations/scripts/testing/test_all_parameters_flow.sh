#!/bin/bash

echo "=========================================="
echo "COMPREHENSIVE PARAMETER FLOW TEST"
echo "Testing ALL RAG settings variations"
echo "=========================================="
echo ""

# Test Configuration 1: LOW thresholds, HIGH top_k, SEMANTIC-HEAVY
echo "=== TEST 1: Low Thresholds + Semantic Heavy ==="
echo "Parameters:"
echo "  top_k=15"
echo "  similarity_threshold=0.30"
echo "  min_similarity_threshold=0.20"
echo "  no_relevant_docs_threshold=0.10"
echo "  semantic_weight=0.9"
echo "  keyword_weight=0.1"
echo ""

curl -s -X POST "http://localhost:8000/api/v1/query" \
  -F "query=Who is Aadhan?" \
  -F "use_cache=false" \
  -F "top_k=15" \
  -F "similarity_threshold=0.30" \
  -F "min_similarity_threshold=0.20" \
  -F "no_relevant_docs_threshold=0.10" \
  -F "semantic_weight=0.9" \
  -F "keyword_weight=0.1" | jq '{
    test: "TEST 1",
    num_sources: .num_sources,
    chunks_retrieved: .metadata.chunks_retrieved,
    threshold_used: .metadata.threshold_used,
    answer_preview: (.answer[:100] + "...")
  }'

echo ""
echo "Checking backend logs for parameter receipt..."
docker-compose logs backend --tail=50 | grep -E "top_k=15|similarity=0.3|semantic_weight=0.9" | tail -3
echo ""

sleep 3

# Test Configuration 2: HIGH thresholds, LOW top_k, KEYWORD-HEAVY
echo "=== TEST 2: High Thresholds + Keyword Heavy ==="
echo "Parameters:"
echo "  top_k=3"
echo "  similarity_threshold=0.80"
echo "  min_similarity_threshold=0.70"
echo "  no_relevant_docs_threshold=0.60"
echo "  semantic_weight=0.3"
echo "  keyword_weight=0.7"
echo ""

curl -s -X POST "http://localhost:8000/api/v1/query" \
  -F "query=King Aadhan from fairy tales?" \
  -F "use_cache=false" \
  -F "top_k=3" \
  -F "similarity_threshold=0.80" \
  -F "min_similarity_threshold=0.70" \
  -F "no_relevant_docs_threshold=0.60" \
  -F "semantic_weight=0.3" \
  -F "keyword_weight=0.7" | jq '{
    test: "TEST 2",
    num_sources: .num_sources,
    chunks_retrieved: .metadata.chunks_retrieved,
    threshold_used: .metadata.threshold_used,
    answer_preview: (.answer[:100] + "...")
  }'

echo ""
echo "Checking backend logs for parameter receipt..."
docker-compose logs backend --tail=50 | grep -E "top_k=3|similarity=0.8|keyword_weight=0.7" | tail -3
echo ""

sleep 3

# Test Configuration 3: BALANCED settings
echo "=== TEST 3: Balanced Configuration ==="
echo "Parameters:"
echo "  top_k=8"
echo "  similarity_threshold=0.55"
echo "  min_similarity_threshold=0.45"
echo "  no_relevant_docs_threshold=0.35"
echo "  semantic_weight=0.6"
echo "  keyword_weight=0.4"
echo ""

curl -s -X POST "http://localhost:8000/api/v1/query" \
  -F "query=Tell me about fairy tale characters" \
  -F "use_cache=false" \
  -F "top_k=8" \
  -F "similarity_threshold=0.55" \
  -F "min_similarity_threshold=0.45" \
  -F "no_relevant_docs_threshold=0.35" \
  -F "semantic_weight=0.6" \
  -F "keyword_weight=0.4" | jq '{
    test: "TEST 3",
    num_sources: .num_sources,
    chunks_retrieved: .metadata.chunks_retrieved,
    threshold_used: .metadata.threshold_used,
    answer_preview: (.answer[:100] + "...")
  }'

echo ""
echo "Checking backend logs for parameter receipt..."
docker-compose logs backend --tail=50 | grep -E "top_k=8|similarity=0.55|semantic_weight=0.6" | tail -3
echo ""

echo "=========================================="
echo "PARAMETER FLOW VALIDATION COMPLETE"
echo "=========================================="
echo ""
echo "Summary:"
echo "- Test 1: Low thresholds (should find MORE results)"
echo "- Test 2: High thresholds (should find FEWER results, only high-quality)"
echo "- Test 3: Balanced (should find MODERATE results)"
echo ""
echo "Check backend logs above to confirm parameters were received!"
