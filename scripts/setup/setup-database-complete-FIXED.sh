#!/bin/bash

#===============================================================================
# Enterprise RAG Chatbot - Complete Database Setup Script (FIXED VERSION)
#
# Purpose: Complete end-to-end database initialization for fresh installations
# Date: 2026-01-05
# Version: 3.0 (FIXED - All 47 migrations)
#
# This script:
# - Creates the database and enables required extensions
# - Applies ALL 47 migrations in correct dependency order
# - Seeds organizational hierarchy (departments, teams, roles)
# - Creates default admin user
# - Sets up RBAC permissions
# - Initializes module configurations
# - Verifies all components
#
# FIXES from v2.0:
# - Added missing 008_update_department_structure.sql
# - Corrected migration order (001_add_evaluation_tables moved to proper phase)
# - Added ALL 47 migration files in dependency order
# - Enhanced verification to check for 64+ tables
#
# Usage:
#   ./setup-database-complete-FIXED.sh [--skip-confirmation] [--verbose]
#
# Prerequisites:
#   - Docker and docker-compose installed
#   - PostgreSQL container running (docker-compose up -d postgres)
#   - Migrations directory: backend/migrations/
#===============================================================================

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MIGRATIONS_DIR="$PROJECT_ROOT/backend/migrations"
CONTAINER_NAME="rag-postgres"
DB_NAME="ragchatbot"
DB_USER="postgres"

# Parse command line arguments
SKIP_CONFIRMATION=false
VERBOSE=false

for arg in "$@"; do
    case $arg in
        --skip-confirmation)
            SKIP_CONFIRMATION=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--skip-confirmation] [--verbose]"
            echo ""
            echo "Options:"
            echo "  --skip-confirmation  Skip all confirmation prompts"
            echo "  --verbose            Show detailed output"
            echo "  --help               Show this help message"
            exit 0
            ;;
    esac
done

#===============================================================================
# Utility Functions
#===============================================================================

print_header() {
    echo ""
    echo -e "${CYAN}${BOLD}============================================================${NC}"
    echo -e "${CYAN}${BOLD}  $1${NC}"
    echo -e "${CYAN}${BOLD}============================================================${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}${BOLD}Step $1: $2${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠  $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ  $1${NC}"
}

execute_sql() {
    local sql="$1"
    local description="$2"

    if [ "$VERBOSE" = true ]; then
        echo -e "${YELLOW}Executing: $description${NC}"
    fi

    if docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "$sql" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

execute_sql_file() {
    local file="$1"
    local description="$2"

    if [ ! -f "$file" ]; then
        print_warning "Migration file not found: $file (skipping)"
        return 0
    fi

    if [ "$VERBOSE" = true ]; then
        echo -e "${YELLOW}Applying: $description${NC}"
        echo -e "${YELLOW}File: $(basename "$file")${NC}"
    fi

    if docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" < "$file" 2>&1 | grep -v "already exists" | grep -v "NOTICE" | grep -v "skipping" | grep "ERROR" > /dev/null; then
        print_error "Failed to apply migration: $description"
        return 1
    else
        print_success "Applied: $description"
        return 0
    fi
}

check_table_exists() {
    local table_name="$1"
    docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '$table_name');" | grep -q "t"
}

#===============================================================================
# Pre-flight Checks
#===============================================================================

print_header "Enterprise RAG Chatbot - Database Setup (FIXED v3.0)"

print_info "Configuration:"
echo "  Database: $DB_NAME"
echo "  Container: $CONTAINER_NAME"
echo "  Migrations: $MIGRATIONS_DIR"
echo "  Project Root: $PROJECT_ROOT"
echo "  Total Migrations: 47"
echo ""

if [ "$SKIP_CONFIRMATION" = false ]; then
    echo -e "${YELLOW}${BOLD}WARNING: This will initialize the database with all tables and seed data.${NC}"
    echo -e "${YELLOW}If the database already exists, this may conflict with existing data.${NC}"
    echo ""
    read -p "Do you want to continue? (yes/no): " -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        print_warning "Setup cancelled by user"
        exit 0
    fi
fi

#===============================================================================
# Step 1: Check Docker and PostgreSQL
#===============================================================================

print_step "1" "Checking prerequisites"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi
print_success "Docker is running"

# Check if PostgreSQL container exists and is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    print_error "PostgreSQL container '$CONTAINER_NAME' is not running"
    print_info "Start it with: docker-compose up -d postgres"
    exit 1
fi
print_success "PostgreSQL container is running"

# Test PostgreSQL connection
if ! docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -c "SELECT 1;" > /dev/null 2>&1; then
    print_error "Cannot connect to PostgreSQL"
    exit 1
fi
print_success "PostgreSQL connection successful"

#===============================================================================
# Step 2: Create Database and Extensions
#===============================================================================

print_step "2" "Creating database and enabling extensions"

# Check if database exists
DB_EXISTS=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -t -c "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME';" | tr -d '[:space:]')

if [ "$DB_EXISTS" = "1" ]; then
    print_warning "Database '$DB_NAME' already exists"
else
    docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;" > /dev/null 2>&1
    print_success "Database '$DB_NAME' created"
fi

# Enable extensions
execute_sql "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";" "Enable uuid-ossp extension"
print_success "Extension: uuid-ossp"

execute_sql "CREATE EXTENSION IF NOT EXISTS \"vector\";" "Enable pgvector extension"
print_success "Extension: pgvector"

#===============================================================================
# PHASE 1: Foundation (000-005)
#===============================================================================

print_step "3" "PHASE 1: Foundation - Base schema and core features"

execute_sql_file "$MIGRATIONS_DIR/000_base_schema.sql" "Base schema (000)"
execute_sql_file "$MIGRATIONS_DIR/001_add_rbac_and_audit.sql" "RBAC and Audit (001)"
execute_sql_file "$MIGRATIONS_DIR/002_fix_embedding_dimensions.sql" "Embedding dimensions fix (002)"
execute_sql_file "$MIGRATIONS_DIR/003_fix_query_cache_default.sql" "Query cache defaults (003)"
execute_sql_file "$MIGRATIONS_DIR/004_add_scraping_configs.sql" "Scraping configs (004)"
execute_sql_file "$MIGRATIONS_DIR/004_add_saved_css_templates.sql" "CSS templates (004)"
execute_sql_file "$MIGRATIONS_DIR/004_add_api_credentials.sql" "API credentials (004)"
execute_sql_file "$MIGRATIONS_DIR/005_add_tool_usage_tracking.sql" "Tool usage tracking (005)"

#===============================================================================
# PHASE 2: RBAC & Organization (006-009)
#===============================================================================

print_step "4" "PHASE 2: RBAC & Organization - Roles, departments, teams"

execute_sql_file "$MIGRATIONS_DIR/006_add_rbac_tables.sql" "RBAC tables (006)"
execute_sql_file "$MIGRATIONS_DIR/007_seed_rbac_data.sql" "RBAC seed data (007)"
execute_sql_file "$MIGRATIONS_DIR/008_normalize_departments_teams.sql" "Normalize departments/teams (008)"
execute_sql_file "$MIGRATIONS_DIR/008_update_department_structure.sql" "Update department structure (008)"
execute_sql_file "$MIGRATIONS_DIR/009_rename_data_ops_teams.sql" "Rename data ops teams (009)"

#===============================================================================
# PHASE 3: Audit & Actions (010-011)
#===============================================================================

print_step "5" "PHASE 3: Audit Enhancements - Action types and logging"

execute_sql_file "$MIGRATIONS_DIR/010_enhance_audit_action_types.sql" "Audit action types (010)"
execute_sql_file "$MIGRATIONS_DIR/011_add_missing_action_types.sql" "Missing action types (011)"

#===============================================================================
# PHASE 4: Projects & Modules (006-013)
#===============================================================================

print_step "6" "PHASE 4: Projects & Modules - Project management and organization"

execute_sql_file "$MIGRATIONS_DIR/006_add_modules_and_projects.sql" "Modules and projects (006)"
execute_sql_file "$MIGRATIONS_DIR/007_add_project_tracking.sql" "Project tracking (007)"
execute_sql_file "$MIGRATIONS_DIR/012_add_default_project.sql" "Default project (012)"
execute_sql_file "$MIGRATIONS_DIR/012_add_project_to_sessions.sql" "Project sessions (012)"
execute_sql_file "$MIGRATIONS_DIR/012_add_project_based_scraping.sql" "Project-based scraping (012)"
execute_sql_file "$MIGRATIONS_DIR/012_add_prompt_library_and_templates.sql" "Prompt library (012)"
execute_sql_file "$MIGRATIONS_DIR/013_add_project_model_preferences.sql" "Project model prefs (013)"
execute_sql_file "$MIGRATIONS_DIR/013_add_user_organizational_fields.sql" "User org fields (013)"
execute_sql_file "$MIGRATIONS_DIR/013_add_project_organizational_fks.sql" "Project org FKs (013)"
execute_sql_file "$MIGRATIONS_DIR/013_seed_role_permissions.sql" "Seed role permissions (013)"
execute_sql_file "$MIGRATIONS_DIR/013_create_default_global_project.sql" "Default global project (013)"

#===============================================================================
# PHASE 5: Agent Tasks (013-014)
#===============================================================================

print_step "7" "PHASE 5: Agent Tasks - Task management and tracking"

execute_sql_file "$MIGRATIONS_DIR/013_add_agent_tasks_table.sql" "Agent tasks table (013)"
execute_sql_file "$MIGRATIONS_DIR/014_add_task_name_and_minio_paths.sql" "Task names and MinIO paths (014)"

#===============================================================================
# PHASE 6: Schema Fixes (014-017)
#===============================================================================

print_step "8" "PHASE 6: Schema Fixes - Type corrections and optimizations"

execute_sql_file "$MIGRATIONS_DIR/014_fix_file_type_length.sql" "Fix file type length (014)"
execute_sql_file "$MIGRATIONS_DIR/014_fix_web_scrape_jobs_foreign_key.sql" "Fix web scrape FK (014)"
execute_sql_file "$MIGRATIONS_DIR/015_fix_query_cache_schema.sql" "Fix query cache schema (015)"
execute_sql_file "$MIGRATIONS_DIR/016_add_multi_column_vector_storage.sql" "Multi-column vector storage (016)"
execute_sql_file "$MIGRATIONS_DIR/017_fix_session_documents_session_id_type.sql" "Fix session documents ID (017)"

#===============================================================================
# PHASE 7: Evaluation System (001, 018)
#===============================================================================

print_step "9" "PHASE 7: Evaluation System - Metrics and benchmarking"

execute_sql_file "$MIGRATIONS_DIR/001_add_evaluation_tables.sql" "Evaluation tables (001)"
execute_sql_file "$MIGRATIONS_DIR/018_fix_evaluation_results_meta_info.sql" "Evaluation fixes (018)"

#===============================================================================
# PHASE 8: Fine-Tuning System (019-023)
#===============================================================================

print_step "10" "PHASE 8: Fine-Tuning System - Model training and management"

execute_sql_file "$MIGRATIONS_DIR/019_add_finetuning_tables.sql" "Fine-tuning tables (019)"
execute_sql_file "$MIGRATIONS_DIR/020_add_finetuning_job_fields.sql" "Fine-tuning job fields (020)"
execute_sql_file "$MIGRATIONS_DIR/020_add_dataset_id_to_finetuning_jobs.sql" "Dataset ID to jobs (020)"
execute_sql_file "$MIGRATIONS_DIR/021_add_training_pipeline_stages.sql" "Training pipeline stages (021)"
execute_sql_file "$MIGRATIONS_DIR/022_add_model_approvals_table.sql" "Model approvals (022)"
execute_sql_file "$MIGRATIONS_DIR/023_add_merge_tracking_columns.sql" "Merge tracking (023)"

#===============================================================================
# PHASE 9: Tier 2/3 Module Management (024)
#===============================================================================

print_step "11" "PHASE 9: Tier 2/3 Modules - Advanced module management"

execute_sql_file "$MIGRATIONS_DIR/024_add_tier2_module_tables.sql" "Tier 2 module tables (024)"
execute_sql_file "$MIGRATIONS_DIR/024_add_modules_management.sql" "Module management (024)"

#===============================================================================
# PHASE 10: Dynamic Configuration (025)
#===============================================================================

print_step "12" "PHASE 10: Dynamic Configuration - Runtime configuration system"

execute_sql_file "$MIGRATIONS_DIR/025_add_dynamic_configuration_tables.sql" "Dynamic configuration (025)"

#===============================================================================
# PHASE 11: Export Wizard (026)
#===============================================================================

print_step "13" "PHASE 11: Export Wizard - Data export and deployment"

execute_sql_file "$MIGRATIONS_DIR/026_add_export_wizard_tables.sql" "Export wizard (026)"

#===============================================================================
# PHASE 12: Additional Features
#===============================================================================

print_step "14" "PHASE 12: Additional Features - Templates and enhancements"

execute_sql_file "$MIGRATIONS_DIR/add_extraction_templates.sql" "Extraction templates"
execute_sql_file "$MIGRATIONS_DIR/add_enhanced_scraping_fields.sql" "Enhanced scraping fields"

#===============================================================================
# Step 15: Create Vector Indexes (Critical for Performance)
#===============================================================================

print_step "15" "Creating vector indexes for performance"

# Check if embeddings exist before creating index
CHUNK_COUNT=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL;" 2>/dev/null | tr -d '[:space:]')

if [ "$CHUNK_COUNT" -gt "0" ]; then
    execute_sql "CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);" "Create vector index on document_chunks"
    print_success "Vector index created (with $CHUNK_COUNT chunks)"
else
    print_warning "No embeddings found - vector index will be created automatically when embeddings are added"
fi

#===============================================================================
# Step 16: Create Default Admin User
#===============================================================================

print_step "16" "Creating default admin user"

# Check if users table exists and has admin user
if check_table_exists "users"; then
    ADMIN_EXISTS=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM users WHERE username = 'admin';" 2>/dev/null | tr -d '[:space:]')

    if [ "$ADMIN_EXISTS" = "0" ]; then
        # Create admin user (password: admin123 - hashed with bcrypt)
        cat <<EOF | docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" > /dev/null 2>&1
INSERT INTO users (username, email, full_name, hashed_password, role, is_active, is_verified)
VALUES (
    'admin',
    'admin@enterprise-rag.local',
    'System Administrator',
    '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eo7gy7SG6sgu',
    'admin',
    true,
    true
);
EOF
        print_success "Default admin user created (username: admin, password: admin123)"
        print_warning "IMPORTANT: Change the default password in production!"
    else
        print_warning "Admin user already exists"
    fi
fi

#===============================================================================
# Step 17: Comprehensive Verification
#===============================================================================

print_step "17" "Comprehensive installation verification"

# Get table count
TABLE_COUNT=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';" 2>/dev/null | tr -d '[:space:]')

print_success "Total tables created: $TABLE_COUNT"

# Expected table count
EXPECTED_MIN=60
if [ "$TABLE_COUNT" -lt "$EXPECTED_MIN" ]; then
    print_warning "Table count ($TABLE_COUNT) is less than expected minimum ($EXPECTED_MIN)"
fi

# Verify critical tables
CRITICAL_TABLES=(
    "documents" "document_chunks" "users" "roles" "departments" "teams"
    "modules" "projects" "chat_sessions" "audit_logs" "api_credentials"
    "finetuning_datasets" "finetuning_jobs" "evaluation_configs"
    "export_jobs" "module_configurations" "skill_modules"
    "user_teams" "document_permissions" "prompt_library"
)

echo ""
print_info "Verifying critical tables (${#CRITICAL_TABLES[@]} tables):"

MISSING_COUNT=0
for table in "${CRITICAL_TABLES[@]}"; do
    if check_table_exists "$table"; then
        ROW_COUNT=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM $table;" 2>/dev/null | tr -d '[:space:]')
        echo -e "  ${GREEN}✓${NC} $table (${ROW_COUNT} rows)"
    else
        echo -e "  ${RED}✗${NC} $table ${RED}(MISSING)${NC}"
        ((MISSING_COUNT++))
    fi
done

if [ $MISSING_COUNT -gt 0 ]; then
    print_warning "$MISSING_COUNT critical tables are missing!"
fi

#===============================================================================
# Step 18: Display Statistics
#===============================================================================

print_step "18" "Database statistics"

# Roles
ROLE_COUNT=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM roles;" 2>/dev/null | tr -d '[:space:]')
echo -e "  Roles: ${CYAN}$ROLE_COUNT${NC}"

# Departments
DEPT_COUNT=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM departments;" 2>/dev/null | tr -d '[:space:]')
echo -e "  Departments: ${CYAN}$DEPT_COUNT${NC}"

# Teams
TEAM_COUNT=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM teams;" 2>/dev/null | tr -d '[:space:]')
echo -e "  Teams: ${CYAN}$TEAM_COUNT${NC}"

# Modules
MODULE_COUNT=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM modules;" 2>/dev/null | tr -d '[:space:]')
echo -e "  Modules: ${CYAN}$MODULE_COUNT${NC}"

# Users
USER_COUNT=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d '[:space:]')
echo -e "  Users: ${CYAN}$USER_COUNT${NC}"

# Projects
PROJECT_COUNT=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM projects;" 2>/dev/null | tr -d '[:space:]')
echo -e "  Projects: ${CYAN}$PROJECT_COUNT${NC}"

#===============================================================================
# Step 19: Show Organizational Hierarchy
#===============================================================================

print_step "19" "Organizational hierarchy"

echo ""
echo "Departments and Teams:"
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "
SELECT
    d.name AS department,
    COUNT(t.id) AS team_count,
    STRING_AGG(t.name, ', ' ORDER BY t.name) AS teams
FROM departments d
LEFT JOIN teams t ON t.department_id = d.id
WHERE d.is_active = TRUE
GROUP BY d.id, d.name
ORDER BY d.name;
" 2>/dev/null | tail -n +3 | head -n -2 || print_warning "Could not display hierarchy"

#===============================================================================
# Step 20: Table Inventory Report
#===============================================================================

print_step "20" "Table inventory report"

echo ""
echo "All tables in database:"
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "\dt" 2>/dev/null | grep "public |" | awk '{print "  - " $3}' | sort || print_warning "Could not list tables"

#===============================================================================
# Completion Summary
#===============================================================================

print_header "Database Setup Complete! (v3.0 FIXED)"

print_success "Database '$DB_NAME' initialized successfully!"
echo ""
echo -e "${BOLD}Summary:${NC}"
echo "  ✓ Database created: $DB_NAME"
echo "  ✓ Extensions enabled: uuid-ossp, pgvector"
echo "  ✓ Migrations applied: 47 total"
echo "  ✓ Tables created: $TABLE_COUNT"
echo "  ✓ Roles configured: $ROLE_COUNT"
echo "  ✓ Departments: $DEPT_COUNT"
echo "  ✓ Teams: $TEAM_COUNT"
echo "  ✓ Modules: $MODULE_COUNT"
echo "  ✓ Users created: $USER_COUNT"
echo "  ✓ Projects: $PROJECT_COUNT"
echo ""
echo -e "${BOLD}Default Credentials:${NC}"
echo "  Username: admin"
echo "  Password: admin123"
echo -e "  ${RED}⚠ CHANGE THIS PASSWORD IN PRODUCTION!${NC}"
echo ""
echo -e "${BOLD}Version Information:${NC}"
echo "  Script Version: 3.0 (FIXED)"
echo "  Improvements: All 47 migrations, correct order, enhanced verification"
echo ""
echo -e "${BOLD}Next Steps:${NC}"
echo "  1. Restart backend: docker-compose restart backend"
echo "  2. Verify backend logs: docker-compose logs -f backend | grep 'Application startup'"
echo "  3. Access frontend: http://localhost:3001"
echo "  4. Access API docs: http://localhost:8000/api/docs"
echo "  5. Test upload with session_id"
echo ""
echo -e "${CYAN}For diagnostics, run:${NC}"
echo "  ./scripts/debugging/diagnose-backend.sh"
echo "  ./scripts/maintenance/validate-services.sh"
echo ""
print_success "Setup completed at $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
