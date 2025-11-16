#!/bin/bash

# Script to diagnose and fix embedding issues in the RAG system
# This addresses the issue where documents exist but queries return no sources

set -e

API_URL="${API_URL:-http://localhost:8000}"

echo "=========================================="
echo "RAG EMBEDDING DIAGNOSTIC & FIX TOOL"
echo "=========================================="
echo ""

# Step 1: Check API health
echo "1. Checking API health..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health")

if [ "$HEALTH_STATUS" != "200" ]; then
    echo "❌ ERROR: Backend API is not responding (HTTP $HEALTH_STATUS)"
    echo "   Please ensure the backend is running:"
    echo "   - docker compose up -d backend"
    echo "   - OR make up"
    exit 1
fi

echo "✅ API is healthy"
echo ""

# Step 2: Run diagnostic endpoint
echo "2. Running embedding diagnostics..."
DIAGNOSTIC_RESPONSE=$(curl -s "$API_URL/api/v1/debug/embeddings")

if [ -z "$DIAGNOSTIC_RESPONSE" ]; then
    echo "❌ ERROR: Could not get diagnostic information"
    exit 1
fi

# Extract key metrics using python3
TOTAL_DOCS=$(echo "$DIAGNOSTIC_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total_documents', 0))" 2>/dev/null)
TOTAL_CHUNKS=$(echo "$DIAGNOSTIC_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total_chunks', 0))" 2>/dev/null)
CHUNKS_WITH_EMBEDDINGS=$(echo "$DIAGNOSTIC_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('chunks_with_embeddings', 0))" 2>/dev/null)
CHUNKS_WITHOUT_EMBEDDINGS=$(echo "$DIAGNOSTIC_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('chunks_without_embeddings', 0))" 2>/dev/null)
EMBEDDING_COVERAGE=$(echo "$DIAGNOSTIC_RESPONSE" | python3 -c "import sys, json; print('{:.1f}'.format(json.load(sys.stdin).get('embedding_coverage_percentage', 0)))" 2>/dev/null)
STATUS=$(echo "$DIAGNOSTIC_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null)

echo "📊 Diagnostic Results:"
echo "   - Total documents: $TOTAL_DOCS"
echo "   - Total chunks: $TOTAL_CHUNKS"
echo "   - Chunks with embeddings: $CHUNKS_WITH_EMBEDDINGS"
echo "   - Chunks without embeddings: $CHUNKS_WITHOUT_EMBEDDINGS"
echo "   - Embedding coverage: $EMBEDDING_COVERAGE%"
echo "   - System status: $STATUS"
echo ""

# Show issues and recommendations
echo "$DIAGNOSTIC_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
issues = data.get('issues', [])
recommendations = data.get('recommendations', [])

if issues:
    print('⚠️  Issues Found:')
    for issue in issues:
        print(f'   - {issue}')
    print()

if recommendations:
    print('💡 Recommendations:')
    for i, rec in enumerate(recommendations, 1):
        print(f'   {i}. {rec}')
    print()
" 2>/dev/null

# Step 3: Check if fix is needed
if [ "$CHUNKS_WITHOUT_EMBEDDINGS" -eq 0 ]; then
    echo "✅ All chunks have embeddings! System is healthy."
    echo ""
    echo "If you're still not getting search results, check:"
    echo "   1. Similarity threshold is not too high (currently 0.5)"
    echo "   2. Query embeddings are being generated correctly"
    echo "   3. Backend logs for errors: docker compose logs backend --tail=100"
    exit 0
fi

echo "=========================================="
echo "FIX REQUIRED"
echo "=========================================="
echo ""
echo "Found $CHUNKS_WITHOUT_EMBEDDINGS chunks without embeddings."
echo "This is why queries are returning no sources."
echo ""

# Ask user if they want to fix
read -p "Would you like to regenerate embeddings now? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Skipping regeneration."
    echo ""
    echo "To fix this later, run:"
    echo "   curl -X POST '$API_URL/api/v1/admin/regenerate-embeddings'"
    echo "   OR"
    echo "   python3 backend/regenerate_embeddings.py"
    exit 0
fi

echo ""
echo "3. Regenerating embeddings..."
echo "   This may take a few minutes depending on the number of documents..."
echo ""

REGEN_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/admin/regenerate-embeddings")

if [ -z "$REGEN_RESPONSE" ]; then
    echo "❌ ERROR: Could not regenerate embeddings"
    exit 1
fi

# Parse regeneration results
REGEN_STATUS=$(echo "$REGEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null)
DOCS_PROCESSED=$(echo "$REGEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('documents_processed', 0))" 2>/dev/null)
CHUNKS_PROCESSED=$(echo "$REGEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('chunks_processed', 0))" 2>/dev/null)
CHUNKS_REMAINING=$(echo "$REGEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('chunks_remaining', 0))" 2>/dev/null)

echo "📊 Regeneration Results:"
echo "   - Status: $REGEN_STATUS"
echo "   - Documents processed: $DOCS_PROCESSED"
echo "   - Chunks processed: $CHUNKS_PROCESSED"
echo "   - Chunks remaining: $CHUNKS_REMAINING"
echo ""

if [ "$REGEN_STATUS" = "completed" ]; then
    echo "✅ SUCCESS: All embeddings regenerated!"
    echo ""
    echo "Your RAG system should now return search results."
    echo ""
    echo "Next steps:"
    echo "   1. Test a query: ./test_rag_debug.sh"
    echo "   2. Upload new documents to a session for better results"
elif [ "$REGEN_STATUS" = "partial" ]; then
    echo "⚠️  PARTIAL SUCCESS: Some embeddings could not be regenerated."
    echo ""
    echo "Check the logs for errors:"
    echo "   docker compose logs backend --tail=100 | grep -i error"
    echo ""
    echo "You may need to re-upload problematic documents."
elif [ "$REGEN_STATUS" = "already_complete" ]; then
    echo "✅ All embeddings already exist!"
    echo ""
    echo "If queries still don't work, the issue may be elsewhere:"
    echo "   1. Check similarity threshold (currently 0.5)"
    echo "   2. Check query embedding generation"
    echo "   3. Review backend logs"
else
    echo "❌ ERROR: Unexpected status: $REGEN_STATUS"
    exit 1
fi

echo ""
echo "=========================================="
echo "DIAGNOSTIC COMPLETE"
echo "=========================================="
