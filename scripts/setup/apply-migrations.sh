#!/bin/bash

echo "=============================================="
echo "  Database Migration Tool"
echo "=============================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

MIGRATIONS_DIR="/home/user/ChatBot/backend/migrations"

echo -e "${BLUE}Checking database connection...${NC}"
if ! docker exec rag-postgres psql -U postgres -d ragchatbot -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${RED}✗ Cannot connect to database${NC}"
    echo "  Make sure PostgreSQL container is running: docker compose up -d postgres"
    exit 1
fi
echo -e "${GREEN}✓ Database connected${NC}"

echo ""
echo -e "${BLUE}Applying migrations...${NC}"

# Apply migration 001
echo -e "\n${YELLOW}Migration 001: RBAC and Audit Logging${NC}"
if docker exec -i rag-postgres psql -U postgres -d ragchatbot < "$MIGRATIONS_DIR/001_add_rbac_and_audit.sql" 2>&1 | tee /tmp/migration_output.log | grep -i error; then
    echo -e "${RED}✗ Migration failed - check errors above${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Migration 001 applied successfully${NC}"
fi

echo ""
echo -e "${BLUE}Verifying new tables...${NC}"

# List all tables
echo -e "\n${YELLOW}Database tables:${NC}"
docker exec rag-postgres psql -U postgres -d ragchatbot -c "\dt" | grep -E "users|chat_sessions|audit_logs|session_documents|session_contexts" && echo -e "${GREEN}✓ New tables created${NC}" || echo -e "${RED}✗ Tables not found${NC}"

# Check default users
echo -e "\n${YELLOW}Default users:${NC}"
docker exec rag-postgres psql -U postgres -d ragchatbot -c "SELECT username, email, role, is_active FROM users;"

echo ""
echo "=============================================="
echo -e "${GREEN}Migration complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Restart backend: docker compose restart backend"
echo "  2. Test authentication: Create a test user"
echo "  3. Review audit logs: Check audit_logs table"
echo ""
echo "Default credentials (CHANGE IN PRODUCTION!):"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
