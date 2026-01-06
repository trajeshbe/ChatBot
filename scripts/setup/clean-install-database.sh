#!/bin/bash
# ============================================================================
# CLEAN DATABASE INSTALLATION SCRIPT
# ============================================================================
# Purpose: Complete database setup from exported schema and data
# Version: 1.0
# Date: 2026-01-05
#
# This script performs a CLEAN installation using the exported schema and
# seed data, ensuring an error-free database setup.
#
# Usage:
#   ./scripts/setup/clean-install-database.sh
#
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SQL_DIR="$PROJECT_ROOT/backend/sql"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}CLEAN DATABASE INSTALLATION${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# ============================================================================
# Step 1: Check Prerequisites
# ============================================================================
echo -e "${BLUE}Step 1: Checking prerequisites...${NC}"

# Check if Docker is running
if ! docker ps &> /dev/null; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if PostgreSQL container is running
if ! docker ps --format '{{.Names}}' | grep -q "rag-postgres"; then
    echo -e "${RED}❌ PostgreSQL container (rag-postgres) is not running.${NC}"
    echo -e "${YELLOW}Starting database container...${NC}"
    docker-compose up -d postgres
    sleep 10
fi

# Check if SQL files exist
if [ ! -f "$SQL_DIR/01_complete_schema.sql" ]; then
    echo -e "${RED}❌ Schema file not found: $SQL_DIR/01_complete_schema.sql${NC}"
    echo -e "${YELLOW}Run the following command to generate it:${NC}"
    echo -e "  docker exec rag-postgres pg_dump -U postgres -d ragchatbot --schema-only --no-owner --no-acl > backend/sql/01_complete_schema.sql"
    exit 1
fi

if [ ! -f "$SQL_DIR/02_essential_data.sql" ]; then
    echo -e "${RED}❌ Data file not found: $SQL_DIR/02_essential_data.sql${NC}"
    echo -e "${YELLOW}Run the following command to generate it:${NC}"
    echo -e "  docker exec rag-postgres pg_dump -U postgres -d ragchatbot --data-only --no-owner --no-acl -t roles -t departments -t teams -t modules -t role_module_permissions > backend/sql/02_essential_data.sql"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites met${NC}"
echo ""

# ============================================================================
# Step 2: Confirm Database Wipe
# ============================================================================
echo -e "${YELLOW}============================================================================${NC}"
echo -e "${YELLOW}WARNING: This will COMPLETELY WIPE the existing database!${NC}"
echo -e "${YELLOW}============================================================================${NC}"
echo -e "${YELLOW}All data will be lost, including:${NC}"
echo -e "  - All uploaded documents"
echo -e "  - All chat conversations"
echo -e "  - All user accounts (except the new admin user)"
echo -e "  - All configurations"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${YELLOW}Installation cancelled.${NC}"
    exit 0
fi

echo ""

# ============================================================================
# Step 3: Drop and Recreate Database
# ============================================================================
echo -e "${BLUE}Step 3: Dropping and recreating database...${NC}"

# Terminate existing connections
docker exec rag-postgres psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'ragchatbot' AND pid <> pg_backend_pid();" 2>&1 | grep -v "pg_terminate_backend" || true

# Drop database
echo -e "${YELLOW}Dropping database ragchatbot...${NC}"
docker exec rag-postgres psql -U postgres -c "DROP DATABASE IF EXISTS ragchatbot;" 2>&1

# Create fresh database
echo -e "${YELLOW}Creating fresh database ragchatbot...${NC}"
docker exec rag-postgres psql -U postgres -c "CREATE DATABASE ragchatbot;" 2>&1

echo -e "${GREEN}✅ Database recreated${NC}"
echo ""

# ============================================================================
# Step 4: Install Extensions
# ============================================================================
echo -e "${BLUE}Step 4: Installing PostgreSQL extensions...${NC}"

docker exec rag-postgres psql -U postgres -d ragchatbot -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";" 2>&1
docker exec rag-postgres psql -U postgres -d ragchatbot -c "CREATE EXTENSION IF NOT EXISTS \"vector\";" 2>&1

echo -e "${GREEN}✅ Extensions installed (uuid-ossp, vector)${NC}"
echo ""

# ============================================================================
# Step 5: Load Complete Schema
# ============================================================================
echo -e "${BLUE}Step 5: Loading complete schema (64 tables, 6231 lines)...${NC}"
echo -e "${YELLOW}This may take 30-60 seconds...${NC}"

if docker exec -i rag-postgres psql -U postgres -d ragchatbot < "$SQL_DIR/01_complete_schema.sql" 2>&1 | tee /tmp/schema_load.log | grep -i "error"; then
    echo -e "${RED}❌ Schema load had errors. Check /tmp/schema_load.log${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Schema loaded successfully${NC}"
echo ""

# ============================================================================
# Step 6: Load Essential Seed Data
# ============================================================================
echo -e "${BLUE}Step 6: Loading essential seed data...${NC}"
echo -e "${YELLOW}Loading roles, departments, teams, modules, and permissions...${NC}"

# Disable triggers temporarily to avoid circular foreign key issues
docker exec rag-postgres psql -U postgres -d ragchatbot -c "SET session_replication_role = replica;" 2>&1

if docker exec -i rag-postgres psql -U postgres -d ragchatbot < "$SQL_DIR/02_essential_data.sql" 2>&1 | tee /tmp/data_load.log | grep -i "error"; then
    echo -e "${RED}❌ Data load had errors. Check /tmp/data_load.log${NC}"
    docker exec rag-postgres psql -U postgres -d ragchatbot -c "SET session_replication_role = DEFAULT;" 2>&1
    exit 1
fi

# Re-enable triggers
docker exec rag-postgres psql -U postgres -d ragchatbot -c "SET session_replication_role = DEFAULT;" 2>&1

echo -e "${GREEN}✅ Seed data loaded${NC}"
echo ""

# ============================================================================
# Step 7: Create Admin User
# ============================================================================
echo -e "${BLUE}Step 7: Creating default admin user...${NC}"

# Password hash for 'admin' (bcrypt): $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY.zQ3QNpZa
docker exec rag-postgres psql -U postgres -d ragchatbot << 'EOF'
INSERT INTO users (
    id,
    username,
    email,
    password_hash,
    full_name,
    is_active,
    is_superuser,
    created_at,
    updated_at
) VALUES (
    uuid_generate_v4(),
    'admin',
    'admin@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY.zQ3QNpZa',
    'System Administrator',
    true,
    true,
    NOW(),
    NOW()
)
ON CONFLICT (username) DO NOTHING;
EOF

echo -e "${GREEN}✅ Admin user created${NC}"
echo ""

# ============================================================================
# Step 8: Assign Admin Role
# ============================================================================
echo -e "${BLUE}Step 8: Assigning Admin role to admin user...${NC}"

docker exec rag-postgres psql -U postgres -d ragchatbot << 'EOF'
DO $$
DECLARE
    v_user_id UUID;
    v_role_id UUID;
BEGIN
    SELECT id INTO v_user_id FROM users WHERE username = 'admin';
    SELECT id INTO v_role_id FROM roles WHERE name = 'Admin';

    IF v_user_id IS NOT NULL AND v_role_id IS NOT NULL THEN
        INSERT INTO user_roles (user_id, role_id, assigned_at, assigned_by)
        VALUES (v_user_id, v_role_id, NOW(), v_user_id)
        ON CONFLICT (user_id, role_id) DO NOTHING;
    END IF;
END $$;
EOF

echo -e "${GREEN}✅ Admin role assigned${NC}"
echo ""

# ============================================================================
# Step 9: Verification
# ============================================================================
echo -e "${BLUE}Step 9: Verifying installation...${NC}"
echo ""

# Count tables
TABLE_COUNT=$(docker exec rag-postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')
echo -e "📊 Tables: ${GREEN}$TABLE_COUNT${NC} (expected: 64+)"

# Count roles
ROLE_COUNT=$(docker exec rag-postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM roles;" | tr -d ' ')
echo -e "📊 Roles: ${GREEN}$ROLE_COUNT${NC} (expected: 5)"

# Count departments
DEPT_COUNT=$(docker exec rag-postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM departments WHERE is_active = TRUE;" | tr -d ' ')
echo -e "📊 Departments: ${GREEN}$DEPT_COUNT${NC} (expected: 3)"

# Count teams
TEAM_COUNT=$(docker exec rag-postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM teams WHERE is_active = TRUE;" | tr -d ' ')
echo -e "📊 Teams: ${GREEN}$TEAM_COUNT${NC} (expected: 28)"

# Count modules
MODULE_COUNT=$(docker exec rag-postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM modules WHERE is_active = TRUE OR is_enabled = TRUE;" | tr -d ' ')
echo -e "📊 Modules: ${GREEN}$MODULE_COUNT${NC} (expected: 26)"

# Count users
USER_COUNT=$(docker exec rag-postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM users;" | tr -d ' ')
echo -e "📊 Users: ${GREEN}$USER_COUNT${NC} (expected: 1)"

echo ""

# Check if vector index exists
VECTOR_INDEX=$(docker exec rag-postgres psql -U postgres -d ragchatbot -t -c "SELECT indexname FROM pg_indexes WHERE tablename = 'document_chunks' AND indexname LIKE '%embedding%';" | tr -d ' ')
if [ -n "$VECTOR_INDEX" ]; then
    echo -e "🔍 Vector Index: ${GREEN}$VECTOR_INDEX${NC} ✅"
else
    echo -e "🔍 Vector Index: ${YELLOW}Not found (will be created on first document upload)${NC}"
fi

echo ""

# ============================================================================
# Final Summary
# ============================================================================
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}✅ CLEAN DATABASE INSTALLATION COMPLETE${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""
echo -e "${BLUE}Login Credentials:${NC}"
echo -e "  Username: ${GREEN}admin${NC}"
echo -e "  Password: ${GREEN}admin${NC}"
echo -e "  Email:    ${GREEN}admin@example.com${NC}"
echo ""
echo -e "${YELLOW}⚠️  SECURITY WARNING:${NC}"
echo -e "${YELLOW}   Change the default admin password immediately after first login!${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo -e "  1. Start/restart backend: ${GREEN}docker-compose restart backend${NC}"
echo -e "  2. Access frontend: ${GREEN}http://localhost:3001${NC}"
echo -e "  3. Login with admin credentials"
echo -e "  4. Change admin password in settings"
echo ""
echo -e "${GREEN}============================================================================${NC}"
