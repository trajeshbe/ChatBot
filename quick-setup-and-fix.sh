#!/bin/bash

echo "=============================================="
echo "  Quick Fix: Setup Database & Re-upload"
echo "=============================================="
echo ""

# Check if database exists
echo "Step 1: Checking if database exists..."
DB_EXISTS=$(docker exec rag-postgres psql -U postgres -t -c "SELECT 1 FROM pg_database WHERE datname = 'rag_chatbot';" 2>/dev/null | tr -d '[:space:]')

if [ "$DB_EXISTS" != "1" ]; then
    echo "❌ Database 'rag_chatbot' does not exist!"
    echo "   Running setup script..."
    ./setup-database.sh
else
    echo "✓ Database exists"
fi

# Check if tables exist
echo ""
echo "Step 2: Checking if tables exist..."
TABLES=$(docker exec rag-postgres psql -U postgres -d rag_chatbot -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('documents', 'document_chunks', 'session_documents');" 2>/dev/null | tr -d '[:space:]')

if [ "$TABLES" != "3" ]; then
    echo "❌ Required tables missing (found $TABLES/3)"
    echo "   Running setup script to create tables..."
    ./setup-database.sh
else
    echo "✓ All required tables exist"
fi

# Check document count
echo ""
echo "Step 3: Checking current documents..."
DOC_COUNT=$(docker exec rag-postgres psql -U postgres -d rag_chatbot -t -c "SELECT COUNT(*) FROM documents;" 2>/dev/null | tr -d '[:space:]')
CHUNK_COUNT=$(docker exec rag-postgres psql -U postgres -d rag_chatbot -t -c "SELECT COUNT(*) FROM document_chunks;" 2>/dev/null | tr -d '[:space:]')

echo "Documents in database: ${DOC_COUNT:-0}"
echo "Document chunks (embeddings): ${CHUNK_COUNT:-0}"

if [ "${CHUNK_COUNT:-0}" -eq 0 ] && [ "${DOC_COUNT:-0}" -gt 0 ]; then
    echo ""
    echo "⚠️  WARNING: You have ${DOC_COUNT} documents but NO chunks!"
    echo "   This means documents were uploaded but not processed."
    echo "   Solution: Delete old documents and re-upload after restart."
    echo ""
fi

# Restart backend
echo ""
echo "Step 4: Restarting backend to apply fixes..."
docker compose restart backend

echo "Waiting for backend to start..."
sleep 10

# Check backend health
echo ""
echo "Step 5: Checking backend health..."
HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null || echo "FAILED")

if echo "$HEALTH" | grep -q "healthy"; then
    echo "✓ Backend is healthy"
else
    echo "❌ Backend not responding"
    echo "   Check logs: docker compose logs backend --tail=50"
fi

echo ""
echo "=============================================="
echo "  Setup Complete!"
echo "=============================================="
echo ""
echo "IMPORTANT: You must now RE-UPLOAD your documents!"
echo ""
echo "Why? Documents uploaded before the database was set up"
echo "      were NOT processed (no chunks/embeddings created)."
echo ""
echo "Steps to upload:"
echo "  1. Open http://localhost:3001"
echo "  2. Click the paperclip button (📎)"
echo "  3. Select your file (e.g., Short Story.txt)"
echo "  4. Click Send"
echo "  5. Wait 10-15 seconds for processing"
echo "  6. Check 'Uploaded Documents' list shows: ✓ chunks"
echo "  7. Ask: 'Who is Aadhan?'"
echo "  8. Should now get answer from YOUR document!"
echo ""
echo "To verify documents are working:"
echo "  ./diagnose-documents.sh"
echo ""
