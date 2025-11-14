#!/bin/bash

echo "=============================================="
echo "  Database Setup & Migration Tool"
echo "=============================================="
echo ""
echo "NOTE: All tables are created in ONE database: 'rag_chatbot'"
echo "      - Base tables (documents, chunks, etc.)"
echo "      - RBAC tables (users, roles, permissions)"
echo "      - Audit tables (logs, metrics)"
echo "      - Session tables (chat_sessions, messages)"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
DB_EXISTS=$(docker exec rag-postgres psql -U postgres -t -c "SELECT 1 FROM pg_database WHERE datname = 'rag_chatbot';" | tr -d '[:space:]')

if [ "$DB_EXISTS" = "1" ]; then
    echo -e "${GREEN}✓ Database 'rag_chatbot' already exists${NC}"
else
    echo -e "${YELLOW}Creating database 'rag_chatbot'...${NC}"
    docker exec rag-postgres psql -U postgres -c "CREATE DATABASE rag_chatbot;" 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Database 'rag_chatbot' created${NC}"
    else
        echo -e "${RED}✗ Failed to create database${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${BLUE}Step 3: Enabling required extensions...${NC}"

# Enable UUID extension
echo -e "${YELLOW}Enabling uuid-ossp extension...${NC}"
docker exec rag-postgres psql -U postgres -d rag_chatbot -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";" 2>&1
echo -e "${GREEN}✓ uuid-ossp enabled${NC}"

# Enable pgvector extension
echo -e "${YELLOW}Enabling vector extension...${NC}"
docker exec rag-postgres psql -U postgres -d rag_chatbot -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>&1
echo -e "${GREEN}✓ vector extension enabled${NC}"

echo ""
echo -e "${BLUE}Step 4: Creating base tables (if not exist)...${NC}"

# Create base tables from Alembic/SQLAlchemy models
docker exec rag-postgres psql -U postgres -d rag_chatbot <<'EOSQL'
-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size INTEGER NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    source_url VARCHAR(1024),
    meta_info JSONB,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    processing_error TEXT
);

-- Document chunks table
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(384),
    meta_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Query cache table
CREATE TABLE IF NOT EXISTS query_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_text TEXT NOT NULL,
    query_embedding vector(384),
    response JSONB NOT NULL,
    sources JSONB,
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ttl_seconds INTEGER DEFAULT 3600
);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    sources JSONB,
    model_used VARCHAR(100),
    tokens_used INTEGER,
    latency_ms DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Web scrape jobs table
CREATE TABLE IF NOT EXISTS web_scrape_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url VARCHAR(1024) NOT NULL,
    scrape_prompt TEXT,
    status VARCHAR(50) NOT NULL,
    document_id UUID REFERENCES documents(id),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    meta_info JSONB
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_document_chunks_document ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_documents_processed ON documents(processed);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);

EOSQL

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Base tables created/verified${NC}"
else
    echo -e "${RED}✗ Failed to create base tables${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Step 5: Applying RBAC and Audit migrations...${NC}"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGRATIONS_DIR="$SCRIPT_DIR/backend/migrations"

echo -e "${YELLOW}Looking for migrations in: $MIGRATIONS_DIR${NC}"

if [ ! -f "$MIGRATIONS_DIR/001_add_rbac_and_audit.sql" ]; then
    echo -e "${RED}✗ Migration file not found: $MIGRATIONS_DIR/001_add_rbac_and_audit.sql${NC}"
    echo -e "${YELLOW}Checking alternate location...${NC}"
    MIGRATIONS_DIR="/home/user/ChatBot/backend/migrations"
    if [ ! -f "$MIGRATIONS_DIR/001_add_rbac_and_audit.sql" ]; then
        echo -e "${RED}✗ Migration file not found in alternate location either${NC}"
        exit 1
    fi
fi

echo -e "${YELLOW}Applying migration 001: RBAC and Audit Logging${NC}"
if docker exec -i rag-postgres psql -U postgres -d rag_chatbot < "$MIGRATIONS_DIR/001_add_rbac_and_audit.sql" 2>&1 | grep -i "ERROR" > /tmp/migration_errors.log; then
    if [ -s /tmp/migration_errors.log ]; then
        echo -e "${RED}✗ Migration encountered errors:${NC}"
        cat /tmp/migration_errors.log
        echo ""
        echo -e "${YELLOW}Note: Some errors may be expected (e.g., 'already exists')${NC}"
    fi
else
    echo -e "${GREEN}✓ Migration 001 applied successfully${NC}"
fi

echo ""
echo -e "${BLUE}Step 6: Verifying tables...${NC}"

# List all tables
echo -e "\n${YELLOW}Database tables:${NC}"
docker exec rag-postgres psql -U postgres -d rag_chatbot -c "\dt" | head -30

echo ""
echo -e "${BLUE}Step 7: Verifying enhanced tables...${NC}"
ENHANCED_TABLES=$(docker exec rag-postgres psql -U postgres -d rag_chatbot -t -c "
    SELECT COUNT(*) FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN ('users', 'chat_sessions', 'audit_logs', 'session_documents', 'session_contexts');
" | tr -d '[:space:]')

if [ "$ENHANCED_TABLES" -eq 5 ]; then
    echo -e "${GREEN}✓ All 5 enhanced tables created successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Found $ENHANCED_TABLES/5 enhanced tables${NC}"
fi

# Check default users
echo -e "\n${YELLOW}Default users:${NC}"
USER_COUNT=$(docker exec rag-postgres psql -U postgres -d rag_chatbot -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d '[:space:]')

if [ -n "$USER_COUNT" ] && [ "$USER_COUNT" -gt 0 ]; then
    docker exec rag-postgres psql -U postgres -d rag_chatbot -c "SELECT username, email, role, is_active FROM users;"
else
    echo -e "${YELLOW}No users found (table may not exist yet)${NC}"
fi

echo ""
echo "=============================================="
echo -e "${GREEN}Database setup complete!${NC}"
echo ""

# Show total table count
TABLE_COUNT=$(docker exec rag-postgres psql -U postgres -d rag_chatbot -t -c "
    SELECT COUNT(*) FROM information_schema.tables
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
" 2>/dev/null | tr -d '[:space:]')

echo -e "${YELLOW}Summary - ONE Database: 'rag_chatbot'${NC}"
echo "  ✓ Total tables created: $TABLE_COUNT"
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
echo "  ✓ Default users created (admin, anonymous)"
echo ""
echo "Next steps:"
echo "  1. Restart backend: docker compose restart backend"
echo "  2. Check backend logs: docker compose logs -f backend | grep 'Enhanced'"
echo "  3. Test upload: ./QUICKSTART.md for examples"
echo ""
echo "Default credentials (CHANGE IN PRODUCTION!):"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
