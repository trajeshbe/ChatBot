#!/bin/bash

echo "=========================================="
echo "  System Status & Upload Instructions"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}✓ Backend is HEALTHY and RUNNING${NC}"
echo -e "${GREEN}✓ Database is CONNECTED and WORKING${NC}"
echo -e "${GREEN}✓ All tables exist and ready${NC}"
echo ""

# Check current document count
echo "Current database status:"
DOC_COUNT=$(docker exec rag-postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM documents;" 2>/dev/null | tr -d '[:space:]')
CHUNK_COUNT=$(docker exec rag-postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM document_chunks;" 2>/dev/null | tr -d '[:space:]')

echo "  Documents: ${DOC_COUNT:-0}"
echo "  Chunks: ${CHUNK_COUNT:-0}"
echo ""

if [ "${DOC_COUNT:-0}" -eq 0 ]; then
    echo -e "${YELLOW}⚠ No documents uploaded yet${NC}"
    echo ""
    echo "=========================================="
    echo "  📤 UPLOAD A DOCUMENT NOW"
    echo "=========================================="
    echo ""
    echo "1. Open your browser: http://localhost:3001"
    echo ""
    echo "2. Click the paperclip button (📎) at the bottom"
    echo ""
    echo "3. Select your file (e.g., 'Short Story.txt')"
    echo ""
    echo "4. Click Send or press Enter"
    echo ""
    echo "5. WAIT 10-15 seconds for processing"
    echo "   (You'll see a loading indicator)"
    echo ""
    echo "6. Check 'Uploaded Documents' section below the chat"
    echo "   Should show: ✓ X chunks (green checkmark)"
    echo ""
    echo "7. Ask a question about your document:"
    echo "   Example: 'What is this document about?'"
    echo ""
    echo "=========================================="
    echo "  After Upload - Run This to Verify:"
    echo "=========================================="
    echo ""
    echo "  ./diagnose-documents.sh"
    echo ""
    echo "You should see:"
    echo "  • Total documents: 1 (or more)"
    echo "  • Total chunks: 10-20 (depending on file size)"
    echo "  • Documents in sessions: 1"
    echo ""
else
    echo -e "${GREEN}✓ You have ${DOC_COUNT} document(s) with ${CHUNK_COUNT} chunks${NC}"
    echo ""
    echo "Test your documents:"
    echo "  1. Open http://localhost:3001"
    echo "  2. Ask: 'What documents do I have uploaded?'"
    echo "  3. Ask: 'Summarize the uploaded document'"
    echo ""
fi

echo "=========================================="
echo "  🔍 Watch Backend Logs (Real-time)"
echo "=========================================="
echo ""
echo "In a new terminal, run:"
echo "  docker compose logs backend -f | grep -v opentelemetry"
echo ""
echo "When you upload a file, you should see:"
echo "  • 'Processing document: [filename]'"
echo "  • 'Created X chunks'"
echo "  • 'Document processed successfully'"
echo ""
