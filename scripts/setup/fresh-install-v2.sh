#!/bin/bash
# Fresh Installation Script v2
#
# Comprehensive installation script for Enterprise RAG Chatbot
# Includes Phase 1 & Phase 2 enhancements
#
# Author: AI Assistant
# Date: 2026-01-07
# Related: Phase 2 - Requirement #9 (Fresh Installation Scripts)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MIGRATIONS_DIR="$PROJECT_ROOT/backend/migrations"
POSTGRES_CONTAINER="rag-postgres"
POSTGRES_DB="ragchatbot"
POSTGRES_USER="postgres"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
    echo ""
}

check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    log_success "Docker is installed"

    # Check if docker-compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    log_success "Docker Compose is installed"

    # Check if PostgreSQL container is running
    if ! docker ps | grep -q "$POSTGRES_CONTAINER"; then
        log_error "PostgreSQL container is not running. Please start services first:"
        echo "  docker-compose up -d postgres"
        exit 1
    fi
    log_success "PostgreSQL container is running"

    # Wait for PostgreSQL to be ready
    log_info "Waiting for PostgreSQL to be ready..."
    for i in {1..30}; do
        if docker exec "$POSTGRES_CONTAINER" pg_isready -U "$POSTGRES_USER" &> /dev/null; then
            log_success "PostgreSQL is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "PostgreSQL did not become ready in time"
            exit 1
        fi
        sleep 1
    done
}

create_database() {
    print_header "Creating Database"

    # Check if database exists
    DB_EXISTS=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -tAc "SELECT 1 FROM pg_database WHERE datname='$POSTGRES_DB'")

    if [ "$DB_EXISTS" == "1" ]; then
        log_warning "Database '$POSTGRES_DB' already exists"
        read -p "Do you want to drop and recreate it? (yes/no): " -r
        if [[ $REPLY =~ ^[Yy]es$ ]]; then
            log_info "Dropping existing database..."
            docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -c "DROP DATABASE $POSTGRES_DB;"
            log_success "Database dropped"
        else
            log_info "Skipping database creation"
            return
        fi
    fi

    log_info "Creating database '$POSTGRES_DB'..."
    docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -c "CREATE DATABASE $POSTGRES_DB;"
    log_success "Database created"
}

enable_extensions() {
    print_header "Enabling PostgreSQL Extensions"

    log_info "Enabling uuid-ossp extension..."
    docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
    log_success "uuid-ossp enabled"

    log_info "Enabling pgvector extension..."
    docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE EXTENSION IF NOT EXISTS vector;"
    log_success "pgvector enabled"
}

run_migrations() {
    print_header "Running Database Migrations"

    # Get list of migration files in order
    MIGRATION_FILES=$(ls -1v "$MIGRATIONS_DIR"/*.sql 2>/dev/null | grep -E '^[0-9]' || true)

    if [ -z "$MIGRATION_FILES" ]; then
        log_warning "No migration files found in $MIGRATIONS_DIR"
        return
    fi

    # Count total migrations
    TOTAL=$(echo "$MIGRATION_FILES" | wc -l)
    CURRENT=0

    log_info "Found $TOTAL migration files"
    echo ""

    # Run each migration
    for migration_file in $MIGRATION_FILES; do
        CURRENT=$((CURRENT + 1))
        FILENAME=$(basename "$migration_file")

        log_info "[$CURRENT/$TOTAL] Running migration: $FILENAME"

        # Execute migration
        if docker exec -i "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f - < "$migration_file" > /dev/null 2>&1; then
            log_success "  ✓ $FILENAME completed"
        else
            # Try again with verbose output for debugging
            log_warning "  Migration had warnings, running with verbose output..."
            docker exec -i "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f - < "$migration_file"
        fi
    done

    echo ""
    log_success "All migrations completed"
}

verify_installation() {
    print_header "Verifying Installation"

    # Check if critical tables exist
    TABLES=(
        "documents"
        "document_chunks"
        "users"
        "projects"
        "system_config"
        "models"
        "agent_tasks"
    )

    log_info "Checking critical tables..."
    for table in "${TABLES[@]}"; do
        TABLE_EXISTS=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT 1 FROM information_schema.tables WHERE table_name='$table'")

        if [ "$TABLE_EXISTS" == "1" ]; then
            log_success "  ✓ Table '$table' exists"
        else
            log_error "  ✗ Table '$table' NOT found"
            exit 1
        fi
    done

    # Check if Prefect schema exists
    log_info "Checking Prefect schema..."
    SCHEMA_EXISTS=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT 1 FROM information_schema.schemata WHERE schema_name='prefect'")

    if [ "$SCHEMA_EXISTS" == "1" ]; then
        log_success "  ✓ Prefect schema exists"
    else
        log_error "  ✗ Prefect schema NOT found"
        exit 1
    fi

    # Check system config seeded
    log_info "Checking system configuration..."
    CONFIG_COUNT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM system_config WHERE is_active=true")

    if [ "$CONFIG_COUNT" -gt 0 ]; then
        log_success "  ✓ System config seeded ($CONFIG_COUNT configurations)"
    else
        log_warning "  ⚠ No system configurations found (expected 17)"
    fi

    # Check models seeded
    log_info "Checking models registry..."
    MODELS_COUNT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM models WHERE is_active=true")

    if [ "$MODELS_COUNT" -gt 0 ]; then
        log_success "  ✓ Models registry seeded ($MODELS_COUNT models)"
    else
        log_warning "  ⚠ No models found (expected 17)"
    fi

    # Check Global project
    log_info "Checking default Global project..."
    GLOBAL_PROJECT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM projects WHERE name='Global'")

    if [ "$GLOBAL_PROJECT" -gt 0 ]; then
        log_success "  ✓ Global project exists"
    else
        log_warning "  ⚠ Global project not found"
    fi

    # Check admin user
    log_info "Checking admin user..."
    ADMIN_USER=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM users WHERE username='admin'")

    if [ "$ADMIN_USER" -gt 0 ]; then
        log_success "  ✓ Admin user exists"
    else
        log_warning "  ⚠ Admin user not found"
    fi

    # Check vector indexes
    log_info "Checking vector indexes..."
    INDEX_EXISTS=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT 1 FROM pg_indexes WHERE indexname LIKE '%embedding%' LIMIT 1")

    if [ "$INDEX_EXISTS" == "1" ]; then
        log_success "  ✓ Vector indexes exist"
    else
        log_warning "  ⚠ Vector indexes not found (may need to be created)"
    fi
}

print_summary() {
    print_header "Installation Summary"

    echo ""
    echo "Database: $POSTGRES_DB"
    echo "Status: Ready"
    echo ""

    # Get table count
    TABLE_COUNT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
    echo "Tables: $TABLE_COUNT"

    # Get system config count
    CONFIG_COUNT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM system_config WHERE is_active=true" 2>/dev/null || echo "0")
    echo "System Configs: $CONFIG_COUNT"

    # Get models count
    MODELS_COUNT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM models WHERE is_active=true" 2>/dev/null || echo "0")
    echo "Models: $MODELS_COUNT"

    # Get projects count
    PROJECTS_COUNT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM projects" 2>/dev/null || echo "0")
    echo "Projects: $PROJECTS_COUNT"

    echo ""
    log_success "Installation completed successfully!"
    echo ""
    echo "Next Steps:"
    echo "  1. Start all services: docker-compose up -d"
    echo "  2. Access Frontend: http://localhost:3001"
    echo "  3. Access API Docs: http://localhost:8000/api/docs"
    echo "  4. Access Prefect UI: http://localhost:4200"
    echo ""
    echo "Default Credentials:"
    echo "  Username: admin"
    echo "  Password: admin"
    echo "  Department: Technology"
    echo "  Team: ITM11"
    echo ""
}

# Main execution
main() {
    print_header "Enterprise RAG Chatbot - Fresh Installation v2"
    echo "This script will install the database schema with Phase 1 & 2 enhancements"
    echo ""

    # Run installation steps
    check_prerequisites
    create_database
    enable_extensions
    run_migrations
    verify_installation
    print_summary
}

# Run main function
main "$@"
