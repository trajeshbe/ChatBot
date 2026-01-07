#!/bin/bash
# Installation Verification Script
#
# Comprehensive health check for Enterprise RAG Chatbot installation
# Verifies database, services, APIs, and configuration
#
# Author: AI Assistant
# Date: 2026-01-07

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
POSTGRES_CONTAINER="rag-postgres"
BACKEND_CONTAINER="rag-backend"
FRONTEND_CONTAINER="rag-frontend"
OLLAMA_CONTAINER="rag-ollama"
PREFECT_CONTAINER="rag-prefect-server"
POSTGRES_DB="ragchatbot"
POSTGRES_USER="postgres"

BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3001"
OLLAMA_URL="http://localhost:11434"
PREFECT_URL="http://localhost:4200"

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
    CHECKS_WARNING=$((CHECKS_WARNING + 1))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
}

print_header() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
}

# Check Docker containers
check_containers() {
    print_header "1. Docker Containers"

    # PostgreSQL
    if docker ps | grep -q "$POSTGRES_CONTAINER"; then
        log_success "PostgreSQL container running"
    else
        log_error "PostgreSQL container NOT running"
    fi

    # Backend
    if docker ps | grep -q "$BACKEND_CONTAINER"; then
        log_success "Backend container running"
    else
        log_warning "Backend container NOT running"
    fi

    # Frontend
    if docker ps | grep -q "$FRONTEND_CONTAINER"; then
        log_success "Frontend container running"
    else
        log_warning "Frontend container NOT running"
    fi

    # Ollama
    if docker ps | grep -q "$OLLAMA_CONTAINER"; then
        log_success "Ollama container running"
    else
        log_warning "Ollama container NOT running"
    fi

    # Prefect
    if docker ps | grep -q "$PREFECT_CONTAINER"; then
        log_success "Prefect container running"
    else
        log_warning "Prefect container NOT running"
    fi
}

# Check database
check_database() {
    print_header "2. Database Schema"

    # Database exists
    DB_EXISTS=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -tAc "SELECT 1 FROM pg_database WHERE datname='$POSTGRES_DB'" 2>/dev/null || echo "")
    if [ "$DB_EXISTS" == "1" ]; then
        log_success "Database '$POSTGRES_DB' exists"
    else
        log_error "Database '$POSTGRES_DB' NOT found"
        return
    fi

    # Extensions
    VECTOR_EXT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT 1 FROM pg_extension WHERE extname='vector'" 2>/dev/null || echo "")
    if [ "$VECTOR_EXT" == "1" ]; then
        log_success "pgvector extension enabled"
    else
        log_error "pgvector extension NOT enabled"
    fi

    UUID_EXT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT 1 FROM pg_extension WHERE extname='uuid-ossp'" 2>/dev/null || echo "")
    if [ "$UUID_EXT" == "1" ]; then
        log_success "uuid-ossp extension enabled"
    else
        log_error "uuid-ossp extension NOT enabled"
    fi

    # Critical tables
    TABLES=("documents" "document_chunks" "users" "projects" "system_config" "models")
    for table in "${TABLES[@]}"; do
        TABLE_EXISTS=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT 1 FROM information_schema.tables WHERE table_name='$table'" 2>/dev/null || echo "")
        if [ "$TABLE_EXISTS" == "1" ]; then
            log_success "Table '$table' exists"
        else
            log_error "Table '$table' NOT found"
        fi
    done

    # Prefect schema
    PREFECT_SCHEMA=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT 1 FROM information_schema.schemata WHERE schema_name='prefect'" 2>/dev/null || echo "")
    if [ "$PREFECT_SCHEMA" == "1" ]; then
        log_success "Prefect schema exists"
    else
        log_warning "Prefect schema NOT found"
    fi
}

# Check seeded data
check_seeded_data() {
    print_header "3. Seeded Data"

    # System config
    CONFIG_COUNT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM system_config WHERE is_active=true" 2>/dev/null || echo "0")
    if [ "$CONFIG_COUNT" -ge 10 ]; then
        log_success "System config seeded ($CONFIG_COUNT configurations)"
    else
        log_warning "System config incomplete ($CONFIG_COUNT/17 expected)"
    fi

    # Models
    MODELS_COUNT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM models WHERE is_active=true" 2>/dev/null || echo "0")
    if [ "$MODELS_COUNT" -ge 10 ]; then
        log_success "Models registry seeded ($MODELS_COUNT models)"
    else
        log_warning "Models registry incomplete ($MODELS_COUNT/17 expected)"
    fi

    # Global project
    GLOBAL_PROJECT=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM projects WHERE name='Global'" 2>/dev/null || echo "0")
    if [ "$GLOBAL_PROJECT" -ge 1 ]; then
        log_success "Global project exists"
    else
        log_warning "Global project NOT found"
    fi

    # Admin user
    ADMIN_USER=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM users WHERE username='admin'" 2>/dev/null || echo "0")
    if [ "$ADMIN_USER" -ge 1 ]; then
        log_success "Admin user exists"

        # Check admin team assignment
        ADMIN_TEAM=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM user_teams ut JOIN users u ON ut.user_id = u.id WHERE u.username='admin'" 2>/dev/null || echo "0")
        if [ "$ADMIN_TEAM" -ge 1 ]; then
            log_success "Admin user assigned to team"
        else
            log_warning "Admin user NOT assigned to team"
        fi
    else
        log_warning "Admin user NOT found"
    fi
}

# Check services
check_services() {
    print_header "4. Service Health"

    # Backend health
    if curl -s -f "$BACKEND_URL/health" > /dev/null 2>&1; then
        log_success "Backend API responding ($BACKEND_URL/health)"
    else
        log_warning "Backend API NOT responding"
    fi

    # Frontend
    if curl -s -f "$FRONTEND_URL" > /dev/null 2>&1; then
        log_success "Frontend responding ($FRONTEND_URL)"
    else
        log_warning "Frontend NOT responding"
    fi

    # Ollama
    if curl -s -f "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
        log_success "Ollama API responding ($OLLAMA_URL/api/tags)"
    else
        log_warning "Ollama API NOT responding"
    fi

    # Prefect
    if curl -s -f "$PREFECT_URL/api/health" > /dev/null 2>&1; then
        log_success "Prefect API responding ($PREFECT_URL/api/health)"
    else
        log_warning "Prefect API NOT responding"
    fi
}

# Check Phase 2 APIs
check_phase2_apis() {
    print_header "5. Phase 2 APIs (System Config & Models)"

    # System config API
    if curl -s -f "$BACKEND_URL/api/v1/system/config" > /dev/null 2>&1; then
        log_success "System Config API responding"

        # Check specific config
        RESPONSE=$(curl -s "$BACKEND_URL/api/v1/system/config/agent.runtime.default_model" 2>/dev/null || echo "")
        if echo "$RESPONSE" | grep -q "config_key"; then
            log_success "System Config API returns valid data"
        else
            log_warning "System Config API response invalid"
        fi
    else
        log_error "System Config API NOT responding"
    fi

    # Models registry API
    if curl -s -f "$BACKEND_URL/api/v1/models" > /dev/null 2>&1; then
        log_success "Models Registry API responding"

        # Check stats endpoint
        if curl -s -f "$BACKEND_URL/api/v1/models/stats" > /dev/null 2>&1; then
            log_success "Models stats endpoint responding"
        else
            log_warning "Models stats endpoint NOT responding"
        fi
    else
        log_error "Models Registry API NOT responding"
    fi
}

# Print summary
print_summary() {
    print_header "Verification Summary"

    TOTAL=$((CHECKS_PASSED + CHECKS_FAILED + CHECKS_WARNING))

    echo ""
    echo "Total Checks: $TOTAL"
    echo -e "${GREEN}Passed: $CHECKS_PASSED${NC}"
    echo -e "${YELLOW}Warnings: $CHECKS_WARNING${NC}"
    echo -e "${RED}Failed: $CHECKS_FAILED${NC}"
    echo ""

    if [ $CHECKS_FAILED -eq 0 ] && [ $CHECKS_WARNING -eq 0 ]; then
        echo -e "${GREEN}✓ Installation is healthy!${NC}"
        return 0
    elif [ $CHECKS_FAILED -eq 0 ]; then
        echo -e "${YELLOW}⚠ Installation is functional with warnings${NC}"
        return 0
    else
        echo -e "${RED}✗ Installation has critical issues${NC}"
        return 1
    fi
}

# Main
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║  Enterprise RAG Chatbot - Installation Verification   ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""

    check_containers
    check_database
    check_seeded_data
    check_services
    check_phase2_apis
    print_summary
}

main "$@"
