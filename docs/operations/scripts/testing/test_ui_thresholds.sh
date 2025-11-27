#!/bin/bash
echo "=== Testing UI Threshold Parameters ==="
echo ""
echo "Test 1: Query with LOW thresholds (should find more results)"
curl -s -X POST "http://localhost:8000/api/v1/query" \
  -F "query=Who is Aadhan?" \
  -F "use_cache=false" \
  -F "top_k=10" \
  -F "similarity_threshold=0.3" \
  -F "min_similarity_threshold=0.2" \
  -F "no_relevant_docs_threshold=0.1" | jq '{
    num_sources: .num_sources,
    chunks_retrieved: .metadata.chunks_retrieved,
    answer_preview: (.answer[:100] + "...")
  }'

echo ""
echo "Test 2: Query with DEFAULT thresholds"  
curl -s -X POST "http://localhost:8000/api/v1/query" \
  -F "query=Who is Aadhan?" \
  -F "use_cache=false" \
  -F "top_k=5" | jq '{
    num_sources: .num_sources,
    chunks_retrieved: .metadata.chunks_retrieved,
    answer_preview: (.answer[:100] + "...")
  }'

echo ""
echo "Now check backend logs for 'RAG Config:' lines showing the thresholds being used"
