#!/bin/bash

echo "=========================================="
echo "  Test Document Upload Endpoint"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create a test file
TEST_FILE="/tmp/test-upload-$(date +%s).txt"
echo "This is a test document for upload verification.

The quick brown fox jumps over the lazy dog.

This document contains enough text to be chunked and embedded properly.

Testing RAG system functionality with multiple paragraphs." > "$TEST_FILE"

echo "1. Created test file: $TEST_FILE"
echo ""

# Generate session ID
SESSION_ID="session-test-$(date +%s)"
echo "2. Using session ID: $SESSION_ID"
echo ""

# Test upload
echo "3. Uploading file to backend..."
echo ""

RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST \
  http://localhost:8000/api/v1/upload \
  -F "file=@$TEST_FILE" \
  -F "session_id=$SESSION_ID")

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE:/d')

echo "HTTP Status: $HTTP_CODE"
echo "Response Body:"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""

if [ "$HTTP_CODE" == "200" ]; then
    echo -e "${GREEN}✓ Upload endpoint working!${NC}"
    echo ""
    echo "4. Checking database..."
    sleep 2  # Wait for processing

    # Check documents in database
    DOC_COUNT=$(docker exec rag-postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM documents;" 2>/dev/null | tr -d '[:space:]')
    CHUNK_COUNT=$(docker exec rag-postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM document_chunks;" 2>/dev/null | tr -d '[:space:]')
    SESSION_DOCS=$(docker exec rag-postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM session_documents WHERE session_id IN (SELECT id FROM chat_sessions WHERE session_id = '$SESSION_ID');" 2>/dev/null | tr -d '[:space:]')

    echo "   Documents: $DOC_COUNT"
    echo "   Chunks: $CHUNK_COUNT"
    echo "   Session documents: $SESSION_DOCS"
    echo ""

    if [ "$CHUNK_COUNT" -gt 0 ]; then
        echo -e "${GREEN}🎉 SUCCESS! Document uploaded and processed${NC}"
        echo ""
        echo "Test your document:"
        echo "  1. Open http://localhost:3001"
        echo "  2. Ask: 'What does the test document say?'"
    else
        echo -e "${YELLOW}⚠ Document uploaded but NOT processed (0 chunks)${NC}"
        echo ""
        echo "Check backend logs for processing errors:"
        echo "  docker compose logs backend --tail=50 | grep -i 'process\|chunk\|embed'"
    fi
else
    echo -e "${RED}✗ Upload failed!${NC}"
    echo ""
    echo "Check backend logs:"
    echo "  docker compose logs backend --tail=50"
fi

# Cleanup
rm -f "$TEST_FILE"
echo ""
echo "=========================================="
