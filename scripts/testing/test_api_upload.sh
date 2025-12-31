#!/bin/bash

# Comprehensive API test script for document upload and RAG pipeline
# Tests the full flow via REST API endpoints

set -e  # Exit on error

API_URL="${API_URL:-http://localhost:8000}"
SESSION_ID="test-session-$(date +%s)"

echo "=========================================="
echo "Testing Document Upload and RAG Pipeline"
echo "=========================================="
echo ""
echo "API URL: $API_URL"
echo "Session ID: $SESSION_ID"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Health check
echo "1. Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s "$API_URL/health")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
    echo "$HEALTH_RESPONSE" | python3 -m json.tool || echo "$HEALTH_RESPONSE"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
    echo "$HEALTH_RESPONSE"
    exit 1
fi
echo ""

# 2. Create test document
echo "2. Creating test document..."
TEST_FILE="/tmp/test_rag_doc_${SESSION_ID}.txt"
cat > "$TEST_FILE" << 'EOF'
Enterprise RAG System Test Document

This is a test document for validating the RAG pipeline.

Key Features:
- Document upload and processing
- Text chunking with overlap
- Semantic embeddings using sentence-transformers
- Vector similarity search with pgvector
- Multi-model LLM support (OpenAI, Claude, Ollama)
- Session-based memory hierarchy

The system uses a two-tier memory approach:
1. Short-term memory: Documents associated with specific sessions
2. Long-term memory: All documents in the vector store

This ensures recently uploaded documents are prioritized for queries
within their session context.

Technical Implementation:
- Backend: FastAPI with async/await
- Database: PostgreSQL with pgvector extension
- Storage: MinIO (S3-compatible)
- Embeddings: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
- LLM: Multi-provider support (OpenAI, Anthropic, Ollama)
EOF

echo -e "${GREEN}✅ Test document created: $TEST_FILE${NC}"
echo "   File size: $(wc -c < "$TEST_FILE") bytes"
echo ""

# 3. Upload document
echo "3. Uploading document with session ID..."
UPLOAD_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/upload" \
    -F "file=@$TEST_FILE" \
    -F "session_id=$SESSION_ID")

echo "$UPLOAD_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$UPLOAD_RESPONSE"

# Extract document ID
DOCUMENT_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('document_id', ''))" 2>/dev/null)

if [ -z "$DOCUMENT_ID" ]; then
    echo -e "${RED}❌ Failed to extract document ID from response${NC}"
    exit 1
fi

# Check if upload was successful
SUCCESS=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)
if [ "$SUCCESS" = "True" ] || [ "$SUCCESS" = "true" ]; then
    echo -e "${GREEN}✅ Document uploaded successfully${NC}"
    echo "   Document ID: $DOCUMENT_ID"

    # Extract chunks created
    CHUNKS=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('chunks_created', 0))" 2>/dev/null)
    echo "   Chunks created: $CHUNKS"

    if [ "$CHUNKS" -eq 0 ]; then
        echo -e "${YELLOW}⚠️  WARNING: No chunks were created!${NC}"
    fi
else
    echo -e "${RED}❌ Upload failed${NC}"
    exit 1
fi
echo ""

# 4. Wait for processing (give it a moment)
echo "4. Waiting for document processing to complete..."
sleep 2
echo -e "${GREEN}✅ Processing should be complete${NC}"
echo ""

# 5. Check session documents
echo "5. Checking session documents..."
SESSION_DOCS_RESPONSE=$(curl -s "$API_URL/api/v1/sessions/$SESSION_ID/documents")
echo "$SESSION_DOCS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$SESSION_DOCS_RESPONSE"

# Count documents
DOC_COUNT=$(echo "$SESSION_DOCS_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('documents', [])))" 2>/dev/null)
if [ "$DOC_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Found $DOC_COUNT document(s) in session${NC}"
else
    echo -e "${YELLOW}⚠️  WARNING: No documents found in session!${NC}"
fi
echo ""

# 6. Test RAG queries
echo "6. Testing RAG queries with uploaded document..."

QUERIES=(
    "What are the key features of the RAG system?"
    "How does the memory hierarchy work?"
    "What is the embedding model used?"
)

for QUERY in "${QUERIES[@]}"; do
    echo ""
    echo "   Query: $QUERY"
    echo "   ----------------------------------------"

    QUERY_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/query" \
        -F "query=$QUERY" \
        -F "session_id=$SESSION_ID" \
        -F "use_cache=false")

    # Extract key fields
    ANSWER=$(echo "$QUERY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', 'N/A')[:200])" 2>/dev/null)
    NUM_SOURCES=$(echo "$QUERY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('num_sources', 0))" 2>/dev/null)
    MODEL=$(echo "$QUERY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('model_name', 'N/A'))" 2>/dev/null)

    echo "   Model: $MODEL"
    echo "   Sources found: $NUM_SOURCES"

    if [ "$NUM_SOURCES" -gt 0 ]; then
        echo -e "   ${GREEN}✅ Sources found!${NC}"

        # Check if our document was used
        SOURCES_JSON=$(echo "$QUERY_RESPONSE" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin).get('sources', [])))" 2>/dev/null)
        DOCUMENT_USED=$(echo "$SOURCES_JSON" | grep -q "$DOCUMENT_ID" && echo "true" || echo "false")

        if [ "$DOCUMENT_USED" = "true" ]; then
            echo -e "   ${GREEN}✅ Our uploaded document WAS used in response!${NC}"

            # Extract memory type
            MEMORY_TYPE=$(echo "$SOURCES_JSON" | python3 -c "import sys, json; sources = json.loads(sys.stdin.read()); print(next((s.get('memory_type', 'unknown') for s in sources if '$DOCUMENT_ID' in str(s)), 'unknown'))" 2>/dev/null)
            echo "   Memory type: $MEMORY_TYPE"
        else
            echo -e "   ${RED}❌ Our uploaded document was NOT used${NC}"
            echo "   Sources: $(echo "$SOURCES_JSON" | python3 -c "import sys, json; print([s.get('filename') for s in json.loads(sys.stdin.read())])" 2>/dev/null)"
        fi
    else
        echo -e "   ${YELLOW}⚠️  No sources found - document may not be retrieved${NC}"
    fi

    echo "   Answer preview: $ANSWER..."
done

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "Session ID: $SESSION_ID"
echo -e "Document ID: $DOCUMENT_ID"
echo -e "Test file: $TEST_FILE"
echo ""
echo -e "${GREEN}✅ All API tests completed!${NC}"
echo ""
echo "To clean up, you can delete the document via:"
echo "  curl -X DELETE $API_URL/api/v1/documents/$DOCUMENT_ID"
echo ""
