#!/bin/bash
# ============================================================================
# Enterprise RAG Chatbot - Clean Database Installation
# ============================================================================
#
# Purpose: Execute comprehensive SQL setup scripts for fresh installation
#
# Features:
#   - Runs all 13 SQL scripts in correct order
#   - Idempotent (safe to run multiple times)
#   - Complete schema + all essential seed data
#   - Production-ready defaults
#
# Usage:
#   bash scripts/setup/clean-install-database.sh
#
# Requirements:
#   - PostgreSQL container running (rag-postgres)
#   - Database 'ragchatbot' created
#
# Created: 2026-01-07
# Related: Requirement #9 - Comprehensive Installation Scripts
#
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SQL_DIR="$PROJECT_ROOT/backend/sql"
POSTGRES_CONTAINER="rag-postgres"
POSTGRES_DB="ragchatbot"
POSTGRES_USER="postgres"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_header() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
}

# ============================================================================
# Main Installation Function
# ============================================================================

main() {
    log_header "Enterprise RAG Chatbot - Clean Database Installation"

    echo "This script will set up the complete database schema and seed data."
    echo ""
    echo "Location: $SQL_DIR"
    echo "Target Database: $POSTGRES_DB"
    echo "Container: $POSTGRES_CONTAINER"
    echo ""

    # ========================================================================
    # Step 1: Pre-flight Checks
    # ========================================================================

    log_header "Step 1: Pre-flight Checks"

    # Check if Docker is running
    if ! docker ps > /dev/null 2>&1; then
        log_error "Docker is not running or not accessible"
        exit 1
    fi
    log_success "Docker is running"

    # Check if PostgreSQL container is running
    if ! docker ps | grep -q "$POSTGRES_CONTAINER"; then
        log_error "PostgreSQL container '$POSTGRES_CONTAINER' is not running"
        echo ""
        echo "Start PostgreSQL first:"
        echo "  docker-compose up -d postgres"
        exit 1
    fi
    log_success "PostgreSQL container is running"

    # Wait for PostgreSQL to be ready
    log_info "Waiting for PostgreSQL to be ready..."
    for i in {1..30}; do
        if docker exec "$POSTGRES_CONTAINER" pg_isready -U "$POSTGRES_USER" > /dev/null 2>&1; then
            log_success "PostgreSQL is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "PostgreSQL did not become ready in time"
            exit 1
        fi
        sleep 1
    done

    # Check if database exists
    DB_EXISTS=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -tAc "SELECT 1 FROM pg_database WHERE datname='$POSTGRES_DB'" 2>/dev/null || echo "")

    if [ "$DB_EXISTS" != "1" ]; then
        log_error "Database '$POSTGRES_DB' does not exist"
        echo ""
        echo "Create the database first:"
        echo "  docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -c 'CREATE DATABASE $POSTGRES_DB;'"
        exit 1
    fi
    log_success "Database '$POSTGRES_DB' exists"

    # Check if SQL directory exists
    if [ ! -d "$SQL_DIR" ]; then
        log_error "SQL directory not found: $SQL_DIR"
        exit 1
    fi
    log_success "SQL directory found"

    # Check if master script exists
    if [ ! -f "$SQL_DIR/00_CLEAN_INSTALL_MASTER.sql" ]; then
        log_error "Master installation script not found: $SQL_DIR/00_CLEAN_INSTALL_MASTER.sql"
        exit 1
    fi
    log_success "Master installation script found"

    # ========================================================================
    # Step 2: Display Installation Plan
    # ========================================================================

    log_header "Step 2: Installation Plan"

    echo "The following SQL scripts will be executed:"
    echo ""
    echo "  00. Master Installation Script (orchestrates 01-13)"
    echo "  ├── 01. PostgreSQL Extensions (uuid-ossp, pgvector)"
    echo "  ├── 02. Complete Schema (67 tables)"
    echo "  ├── 03. Seed Departments (7 departments)"
    echo "  ├── 04. Seed Teams (28 teams)"
    echo "  ├── 05. Seed Roles (5 roles)"
    echo "  ├── 06. Seed Admin User (admin/admin)"
    echo "  ├── 07. Seed Global Project (default workspace)"
    echo "  ├── 08. Seed System Config (17 configurations)"
    echo "  ├── 09. Seed Models Registry (17 LLM models)"
    echo "  ├── 10. Seed Modules (36 modules)"
    echo "  ├── 11. Seed Prompt Library (25+ prompts)"
    echo "  ├── 12. Seed RBAC Permissions (role-module matrix)"
    echo "  └── 13. Create Performance Indexes (190+ indexes)"
    echo ""

    read -p "Continue with installation? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warning "Installation cancelled by user"
        exit 0
    fi

    # ========================================================================
    # Step 3: Execute Master Installation Script
    # ========================================================================

    log_header "Step 3: Executing Installation"

    log_info "Running master installation script..."
    echo ""

    # Execute the master script
    if docker exec -i "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$SQL_DIR/00_CLEAN_INSTALL_MASTER.sql"; then
        log_success "Master installation script completed successfully"
    else
        log_error "Master installation script failed"
        echo ""
        echo "Check the error messages above for details."
        echo "You can try running individual scripts manually:"
        echo "  docker exec -i $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $POSTGRES_DB < backend/sql/01_extensions.sql"
        exit 1
    fi

    # ========================================================================
    # Step 4: Post-Installation Verification
    # ========================================================================

    log_header "Step 4: Post-Installation Verification"

    # Count tables
    TABLE_COUNT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'" 2>/dev/null || echo "0")
    log_info "Total tables created: $TABLE_COUNT"

    # Check critical tables
    CRITICAL_TABLES=("users" "departments" "teams" "roles" "projects" "modules" "system_config" "models" "prompt_library")

    echo ""
    log_info "Checking critical tables..."
    for table in "${CRITICAL_TABLES[@]}"; do
        if docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT 1 FROM information_schema.tables WHERE table_name='$table'" 2>/dev/null | grep -q "1"; then
            log_success "  ✓ Table '$table' exists"
        else
            log_error "  ✗ Table '$table' NOT found"
        fi
    done

    # Check seed data
    echo ""
    log_info "Checking seed data..."

    USERS_COUNT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM users WHERE username='admin'" 2>/dev/null || echo "0")
    if [ "$USERS_COUNT" -ge 1 ]; then
        log_success "  ✓ Admin user exists"
    else
        log_warning "  ⚠ Admin user NOT found"
    fi

    DEPARTMENTS_COUNT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM departments" 2>/dev/null || echo "0")
    log_info "  - Departments: $DEPARTMENTS_COUNT"

    TEAMS_COUNT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM teams" 2>/dev/null || echo "0")
    log_info "  - Teams: $TEAMS_COUNT"

    ROLES_COUNT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM roles" 2>/dev/null || echo "0")
    log_info "  - Roles: $ROLES_COUNT"

    MODULES_COUNT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM modules" 2>/dev/null || echo "0")
    log_info "  - Modules: $MODULES_COUNT"

    PROMPTS_COUNT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM prompt_library" 2>/dev/null || echo "0")
    log_info "  - Prompt Library: $PROMPTS_COUNT"

    CONFIG_COUNT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM system_config WHERE is_active=true" 2>/dev/null || echo "0")
    log_info "  - System Config: $CONFIG_COUNT"

    MODELS_COUNT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM models WHERE is_active=true" 2>/dev/null || echo "0")
    log_info "  - Models: $MODELS_COUNT"

    # Check extensions
    echo ""
    log_info "Checking extensions..."

    VECTOR_EXT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT 1 FROM pg_extension WHERE extname='vector'" 2>/dev/null || echo "")
    if [ "$VECTOR_EXT" == "1" ]; then
        log_success "  ✓ pgvector extension enabled"
    else
        log_error "  ✗ pgvector extension NOT enabled"
    fi

    UUID_EXT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT 1 FROM pg_extension WHERE extname='uuid-ossp'" 2>/dev/null || echo "")
    if [ "$UUID_EXT" == "1" ]; then
        log_success "  ✓ uuid-ossp extension enabled"
    else
        log_error "  ✗ uuid-ossp extension NOT enabled"
    fi

    # ========================================================================
    # Step 5: Installation Summary
    # ========================================================================

    log_header "Installation Complete!"

    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  Enterprise RAG Chatbot Database - Installation Summary       ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Database: $POSTGRES_DB"
    echo "Total Tables: $TABLE_COUNT"
    echo ""
    echo "Seed Data:"
    echo "  - Admin User: 1"
    echo "  - Departments: $DEPARTMENTS_COUNT"
    echo "  - Teams: $TEAMS_COUNT"
    echo "  - Roles: $ROLES_COUNT"
    echo "  - Modules: $MODULES_COUNT"
    echo "  - Prompts: $PROMPTS_COUNT"
    echo "  - System Configs: $CONFIG_COUNT"
    echo "  - LLM Models: $MODELS_COUNT"
    echo ""
    echo "Default Login Credentials:"
    echo "  ┌─────────────────────────────────────┐"
    echo "  │ Username:   admin                   │"
    echo "  │ Password:   admin                   │"
    echo "  │ Department: Technology              │"
    echo "  │ Team:       ITM11                   │"
    echo "  │ Role:       admin                   │"
    echo "  └─────────────────────────────────────┘"
    echo ""
    echo "⚠️  SECURITY WARNING:"
    echo "  Change the default 'admin' password immediately in production!"
    echo ""
    echo "Next Steps:"
    echo "  1. Restart backend:    docker-compose restart backend"
    echo "  2. Verify installation: bash scripts/setup/verify-installation.sh"
    echo "  3. Access Frontend:     http://localhost:3001"
    echo "  4. Access API Docs:     http://localhost:8000/api/docs"
    echo ""
    log_success "Database installation completed successfully!"
    echo ""
}

# Execute main function
main "$@"
