#!/bin/bash

# Debug script to test RAG queries with different parameters
set -e

API_URL="${API_URL:-http://localhost:8000}"
SESSION_ID="test-session-1763116752"

echo "=========================================="
echo "RAG Query Debug Test"
echo "=========================================="
echo ""
echo "Testing with Session ID: $SESSION_ID"
echo ""

# Test 1: Query WITH session_id
echo "1. Testing query WITH session_id..."
RESPONSE_WITH_SESSION=$(curl -s -X POST "$API_URL/api/v1/query" \
    -F "query=What are the key features of the RAG system?" \
    -F "session_id=$SESSION_ID" \
    -F "use_cache=false")

NUM_SOURCES_WITH=$(echo "$RESPONSE_WITH_SESSION" | python3 -c "import sys, json; print(json.load(sys.stdin).get('num_sources', 0))" 2>/dev/null)
NUM_SHORT_TERM=$(echo "$RESPONSE_WITH_SESSION" | python3 -c "import sys, json; print(json.load(sys.stdin).get('num_short_term_sources', 0))" 2>/dev/null)
NUM_LONG_TERM=$(echo "$RESPONSE_WITH_SESSION" | python3 -c "import sys, json; print(json.load(sys.stdin).get('num_long_term_sources', 0))" 2>/dev/null)
CONTEXT_INFO=$(echo "$RESPONSE_WITH_SESSION" | python3 -c "import sys, json; print(json.load(sys.stdin).get('context_info', 'N/A'))" 2>/dev/null)

echo "   Sources found: $NUM_SOURCES_WITH"
echo "   Short-term sources: $NUM_SHORT_TERM"
echo "   Long-term sources: $NUM_LONG_TERM"
echo "   Context info: $CONTEXT_INFO"
echo ""

# Test 2: Query WITHOUT session_id
echo "2. Testing query WITHOUT session_id..."
RESPONSE_WITHOUT_SESSION=$(curl -s -X POST "$API_URL/api/v1/query" \
    -F "query=What are the key features of the RAG system?" \
    -F "use_cache=false")

NUM_SOURCES_WITHOUT=$(echo "$RESPONSE_WITHOUT_SESSION" | python3 -c "import sys, json; print(json.load(sys.stdin).get('num_sources', 0))" 2>/dev/null)

echo "   Sources found: $NUM_SOURCES_WITHOUT"
echo ""

# Test 3: Check if enhanced RAG is being used
echo "3. Checking which RAG service is active..."
HEALTH=$(curl -s "$API_URL/health")
ENHANCED_RAG=$(echo "$HEALTH" | python3 -c "import sys, json; print(json.load(sys.stdin).get('features', {}).get('enhanced_rag', False))" 2>/dev/null)

echo "   Enhanced RAG active: $ENHANCED_RAG"
echo ""

# Test 4: List all documents (not session-specific)
echo "4. Listing all documents in database..."
ALL_DOCS=$(curl -s "$API_URL/api/v1/documents")
DOC_COUNT=$(echo "$ALL_DOCS" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
echo "   Total documents: $DOC_COUNT"
echo ""

# Test 5: Check session documents
echo "5. Checking session-specific documents..."
SESSION_DOCS=$(curl -s "$API_URL/api/v1/sessions/$SESSION_ID/documents")
SESSION_DOC_COUNT=$(echo "$SESSION_DOCS" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('documents', [])))" 2>/dev/null)
echo "   Session documents: $SESSION_DOC_COUNT"

if [ "$SESSION_DOC_COUNT" -gt 0 ]; then
    echo "   Document details:"
    echo "$SESSION_DOCS" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for doc in data.get('documents', []):
    print(f\"     - {doc['filename']}: {doc['chunk_count']} chunks, embeddings={doc['has_embeddings']}\")
" 2>/dev/null
fi
echo ""

echo "=========================================="
echo "Analysis"
echo "=========================================="

if [ "$NUM_SOURCES_WITH" -eq 0 ] && [ "$NUM_SOURCES_WITHOUT" -eq 0 ]; then
    echo "❌ ISSUE: No sources found in either query mode"
    echo ""
    echo "Possible causes:"
    echo "  1. Embeddings not generated correctly"
    echo "  2. Vector similarity threshold too high"
    echo "  3. Query embedding generation failing"
    echo "  4. Database query issue"
    echo ""
elif [ "$NUM_SOURCES_WITH" -eq 0 ] && [ "$NUM_SOURCES_WITHOUT" -gt 0 ]; then
    echo "❌ ISSUE: Sources found without session_id but not with it"
    echo ""
    echo "This suggests:"
    echo "  - Long-term memory (all documents) is working"
    echo "  - Short-term memory (session documents) is NOT working"
    echo "  - Problem with session document association or retrieval"
    echo ""
elif [ "$NUM_SOURCES_WITH" -gt 0 ]; then
    echo "✅ SUCCESS: Sources are being found!"
    echo ""
    if [ "$NUM_SHORT_TERM" -gt 0 ]; then
        echo "✅ Short-term memory (session documents) is working"
    fi
    if [ "$NUM_LONG_TERM" -gt 0 ]; then
        echo "✅ Long-term memory (all documents) is working"
    fi
    echo ""
fi

echo ""
