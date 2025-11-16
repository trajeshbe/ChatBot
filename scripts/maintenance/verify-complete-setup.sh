#!/bin/bash

echo "=========================================="
echo "  Complete Setup Verification"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASS++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAIL++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 1. Check database exists
echo "1. Checking database..."
DB_EXISTS=$(docker exec rag-postgres psql -U postgres -t -c "SELECT 1 FROM pg_database WHERE datname = 'ragchatbot';" 2>/dev/null | tr -d '[:space:]')
if [ "$DB_EXISTS" == "1" ]; then
    check_pass "Database 'ragchatbot' exists"
else
    check_fail "Database 'ragchatbot' NOT found"
fi

# 2. Check base tables
echo ""
echo "2. Checking base tables..."
TABLES=$(docker exec rag-postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('documents', 'document_chunks', 'session_documents');" 2>/dev/null | tr -d '[:space:]')
if [ "$TABLES" == "3" ]; then
    check_pass "All 3 base tables exist (documents, document_chunks, session_documents)"
else
    check_fail "Base tables missing (found $TABLES/3)"
fi

# 3. Check enhanced tables
echo ""
echo "3. Checking enhanced tables..."
ENHANCED_TABLES=$(docker exec rag-postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('users', 'chat_sessions', 'audit_logs');" 2>/dev/null | tr -d '[:space:]')
if [ "$ENHANCED_TABLES" == "3" ]; then
    check_pass "Enhanced tables exist (users, chat_sessions, audit_logs)"
else
    check_warn "Enhanced tables partially missing (found $ENHANCED_TABLES/3)"
fi

# 4. Check pgvector extension
echo ""
echo "4. Checking pgvector extension..."
PGVECTOR=$(docker exec rag-postgres psql -U postgres -d ragchatbot -t -c "SELECT 1 FROM pg_extension WHERE extname='vector';" 2>/dev/null | tr -d '[:space:]')
if [ "$PGVECTOR" == "1" ]; then
    check_pass "pgvector extension installed"
else
    check_fail "pgvector extension NOT installed"
fi

# 5. Check backend health
echo ""
echo "5. Checking backend service..."
BACKEND_HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null)
if echo "$BACKEND_HEALTH" | grep -q "healthy"; then
    check_pass "Backend is healthy and responding"
else
    check_fail "Backend NOT responding at http://localhost:8000/health"
fi

# 6. Check frontend
echo ""
echo "6. Checking frontend service..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001 2>/dev/null)
if [ "$FRONTEND_STATUS" == "200" ]; then
    check_pass "Frontend accessible at http://localhost:3001"
else
    check_fail "Frontend NOT accessible (HTTP $FRONTEND_STATUS)"
fi

# 7. Check documents
echo ""
echo "7. Checking documents in database..."
DOC_COUNT=$(docker exec rag-postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM documents;" 2>/dev/null | tr -d '[:space:]')
CHUNK_COUNT=$(docker exec rag-postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM document_chunks;" 2>/dev/null | tr -d '[:space:]')

echo "   Documents: ${DOC_COUNT:-0}"
echo "   Chunks (embeddings): ${CHUNK_COUNT:-0}"

if [ "${DOC_COUNT:-0}" -gt 0 ] && [ "${CHUNK_COUNT:-0}" -gt 0 ]; then
    check_pass "Documents uploaded and processed correctly"
elif [ "${DOC_COUNT:-0}" -gt 0 ] && [ "${CHUNK_COUNT:-0}" -eq 0 ]; then
    check_warn "Documents uploaded but NOT processed (no chunks)"
    echo "         → Delete and re-upload documents to trigger processing"
elif [ "${DOC_COUNT:-0}" -eq 0 ]; then
    check_warn "No documents uploaded yet"
    echo "         → Upload a document via http://localhost:3001"
fi

# 8. Check API endpoints
echo ""
echo "8. Checking new API endpoints..."
SESSION_ENDPOINT=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/sessions/test-session/documents 2>/dev/null)
if [ "$SESSION_ENDPOINT" == "200" ] || [ "$SESSION_ENDPOINT" == "404" ]; then
    check_pass "Session documents endpoint responding (status: $SESSION_ENDPOINT)"
else
    check_fail "Session documents endpoint NOT working (status: $SESSION_ENDPOINT)"
fi

# 9. Check Docker containers
echo ""
echo "9. Checking Docker containers..."
BACKEND_RUNNING=$(docker ps --filter "name=rag-backend" --filter "status=running" -q)
POSTGRES_RUNNING=$(docker ps --filter "name=rag-postgres" --filter "status=running" -q)
FRONTEND_RUNNING=$(docker ps --filter "name=rag-frontend" --filter "status=running" -q)

if [ -n "$BACKEND_RUNNING" ]; then
    check_pass "Backend container running"
else
    check_fail "Backend container NOT running"
fi

if [ -n "$POSTGRES_RUNNING" ]; then
    check_pass "PostgreSQL container running"
else
    check_fail "PostgreSQL container NOT running"
fi

if [ -n "$FRONTEND_RUNNING" ]; then
    check_pass "Frontend container running"
else
    check_fail "Frontend container NOT running"
fi

# Summary
echo ""
echo "=========================================="
echo "  Summary"
echo "=========================================="
echo -e "${GREEN}Passed:${NC} $PASS checks"
if [ $FAIL -gt 0 ]; then
    echo -e "${RED}Failed:${NC} $FAIL checks"
fi
echo ""

if [ $FAIL -eq 0 ] && [ "${DOC_COUNT:-0}" -gt 0 ] && [ "${CHUNK_COUNT:-0}" -gt 0 ]; then
    echo -e "${GREEN}🎉 SUCCESS!${NC} Your system is fully set up and working!"
    echo ""
    echo "✅ Database tables created"
    echo "✅ Services running"
    echo "✅ Documents uploaded and processed"
    echo ""
    echo "Next steps:"
    echo "  1. Open http://localhost:3001"
    echo "  2. Ask: 'What is in the uploaded document?'"
    echo "  3. Verify response references YOUR document content"
    echo ""
elif [ $FAIL -eq 0 ] && [ "${DOC_COUNT:-0}" -eq 0 ]; then
    echo -e "${GREEN}✓ System Ready!${NC} Now upload a document to test."
    echo ""
    echo "How to upload:"
    echo "  1. Open http://localhost:3001"
    echo "  2. Click paperclip button (📎)"
    echo "  3. Select your file (e.g., 'Short Story.txt')"
    echo "  4. Click Send"
    echo "  5. Wait 10-15 seconds for processing"
    echo "  6. Check 'Uploaded Documents' list shows: ✓ chunks"
    echo "  7. Ask about document content"
    echo ""
elif [ $FAIL -eq 0 ] && [ "${DOC_COUNT:-0}" -gt 0 ] && [ "${CHUNK_COUNT:-0}" -eq 0 ]; then
    echo -e "${YELLOW}⚠ Almost There!${NC} Documents uploaded but not processed."
    echo ""
    echo "Fix:"
    echo "  1. Delete documents from UI (trash icon)"
    echo "  2. Restart backend: docker compose restart backend"
    echo "  3. Wait 10 seconds: sleep 10"
    echo "  4. Re-upload your documents"
    echo ""
else
    echo -e "${RED}❌ Issues Found!${NC} Fix the failed checks above."
    echo ""
    echo "Common fixes:"
    echo "  • Run: ./quick-setup-and-fix.sh"
    echo "  • Or: docker compose down && docker compose up -d --build"
    echo "  • Check logs: docker compose logs backend --tail=50"
    echo ""
fi

echo "=========================================="
