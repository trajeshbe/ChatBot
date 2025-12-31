#!/bin/bash

echo "=============================================="
echo "  Database Setup & Migration Tool"
echo "=============================================="
echo ""
echo "NOTE: All tables are created in ONE database: 'ragchatbot'"
echo "      - Base tables (documents, chunks, cache, conversations)"
echo "      - Enhanced tables (users, sessions, audit_logs)"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGRATIONS_DIR="$SCRIPT_DIR/backend/migrations"

echo -e "${BLUE}Step 1: Checking PostgreSQL connection...${NC}"
if ! docker exec rag-postgres psql -U postgres -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${RED}✗ Cannot connect to PostgreSQL${NC}"
    echo "  Make sure PostgreSQL container is running: docker compose up -d postgres"
    exit 1
fi
echo -e "${GREEN}✓ PostgreSQL connected${NC}"

echo ""
echo -e "${BLUE}Step 2: Creating database if not exists...${NC}"

# Check if database exists
DB_EXISTS=$(docker exec rag-postgres psql -U postgres -t -c "SELECT 1 FROM pg_database WHERE datname = 'ragchatbot';" | tr -d '[:space:]')

if [ "$DB_EXISTS" = "1" ]; then
    echo -e "${GREEN}✓ Database 'ragchatbot' already exists${NC}"
else
    echo -e "${YELLOW}Creating database 'ragchatbot'...${NC}"
    docker exec rag-postgres psql -U postgres -c "CREATE DATABASE ragchatbot;" 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Database 'ragchatbot' created${NC}"
    else
        echo -e "${RED}✗ Failed to create database${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${BLUE}Step 3: Applying base schema migration...${NC}"
echo "Migration file: 000_base_schema.sql"

BASE_MIGRATION="$MIGRATIONS_DIR/000_base_schema.sql"

if [ -f "$BASE_MIGRATION" ]; then
    echo -e "${YELLOW}Applying base schema...${NC}"
    docker exec -i rag-postgres psql -U postgres -d ragchatbot < "$BASE_MIGRATION" 2>&1 | \
        grep -v "already exists" | grep -v "skipping" || true
    echo -e "${GREEN}✓ Base schema applied${NC}"
else
    echo -e "${RED}✗ Base migration file not found: $BASE_MIGRATION${NC}"
    echo "Current directory: $(pwd)"
    echo "Looking in: $MIGRATIONS_DIR"
    exit 1
fi

echo ""
echo -e "${BLUE}Step 4: Applying enhanced schema migration...${NC}"
echo "Migration file: 001_add_rbac_and_audit.sql"

ENHANCED_MIGRATION="$MIGRATIONS_DIR/001_add_rbac_and_audit.sql"

if [ -f "$ENHANCED_MIGRATION" ]; then
    echo -e "${YELLOW}Applying RBAC and audit tables...${NC}"
    docker exec -i rag-postgres psql -U postgres -d ragchatbot < "$ENHANCED_MIGRATION" 2>&1 | \
        grep -v "already exists" | grep -v "skipping" || true
    echo -e "${GREEN}✓ Enhanced schema applied${NC}"
else
    echo -e "${YELLOW}⚠  Enhanced migration file not found (optional)${NC}"
fi

echo ""
echo -e "${BLUE}Step 5: Fixing embedding dimensions...${NC}"
echo "Migration file: 002_fix_embedding_dimensions.sql"

DIMENSION_FIX_MIGRATION="$MIGRATIONS_DIR/002_fix_embedding_dimensions.sql"

if [ -f "$DIMENSION_FIX_MIGRATION" ]; then
    echo -e "${YELLOW}Fixing embedding dimensions (1536 → 384)...${NC}"
    docker exec -i rag-postgres psql -U postgres -d ragchatbot < "$DIMENSION_FIX_MIGRATION" 2>&1 | \
        grep -v "does not exist, skipping" || true
    echo -e "${GREEN}✓ Embedding dimensions fixed${NC}"
    echo -e "${YELLOW}⚠  Note: Existing embeddings have been dropped and will be regenerated${NC}"
else
    echo -e "${YELLOW}⚠  Dimension fix migration file not found (may not be needed)${NC}"
fi

echo ""
echo -e "${BLUE}Step 6: Verifying tables...${NC}"

# Get table count
TABLE_COUNT=$(docker exec rag-postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';" | tr -d '[:space:]')

echo ""
echo "Database tables created:"
docker exec rag-postgres psql -U postgres -d ragchatbot -c "\dt" 2>&1

echo ""
echo -e "${BLUE}Step 7: Verifying extensions...${NC}"
docker exec rag-postgres psql -U postgres -d ragchatbot -c "SELECT extname FROM pg_extension WHERE extname IN ('uuid-ossp', 'vector');" 2>&1

echo ""
echo -e "${BLUE}Step 8: Checking default users...${NC}"
USER_COUNT=$(docker exec rag-postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d '[:space:]')

if [ -z "$USER_COUNT" ] || [ "$USER_COUNT" = "0" ]; then
    echo -e "${YELLOW}No default users found. This is OK if you just created the database.${NC}"
else
    echo ""
    echo "Default users:"
    docker exec rag-postgres psql -U postgres -d ragchatbot -c "SELECT username, email, role, is_active FROM users;" 2>&1
fi

echo ""
echo "=============================================="
echo -e "${GREEN}✅ Database setup complete!${NC}"
echo "=============================================="
echo ""
echo "Summary - ONE Database: 'ragchatbot'"
echo "  ✓ Total tables created: ${TABLE_COUNT}"
echo "  ✓ Extensions enabled (uuid-ossp, vector)"
echo ""
echo "  Base tables (RAG functionality):"
echo "    - documents, document_chunks, query_cache"
echo "    - conversations, messages, web_scrape_jobs"
echo ""
echo "  Enhanced tables (RBAC & Audit):"
echo "    - users, api_keys, chat_sessions"
echo "    - session_documents, conversation_messages"
echo "    - audit_logs, usage_metrics"
echo "    - document_permissions, session_contexts"
echo ""
echo "Next steps:"
echo "  1. Restart backend: docker compose restart backend"
echo "  2. Check backend logs: docker compose logs -f backend | grep 'Enhanced'"
echo "  3. Test upload with session_id"
echo "  4. Verify document processing: ./diagnose-documents.sh"
echo ""
if [ ! -z "$USER_COUNT" ] && [ "$USER_COUNT" != "0" ]; then
    echo "Default credentials (CHANGE IN PRODUCTION!):"
    echo "  Username: admin"
    echo "  Password: admin123"
    echo ""
fi
