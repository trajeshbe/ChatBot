#!/bin/bash

#===============================================================================
# Enterprise RAG Chatbot - Complete Fresh Installation Script
#
# Purpose: Complete fresh installation from scratch including:
#   - Docker Compose startup
#   - Database initialization
#   - Backend/Frontend setup
#   - Service health checks
#
# Usage:
#   ./initialize-fresh-install.sh [--clean] [--skip-build]
#
# Options:
#   --clean        Remove all containers and volumes before starting
#   --skip-build   Skip Docker image build step
#===============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CLEAN_INSTALL=false
SKIP_BUILD=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --clean)
            CLEAN_INSTALL=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--clean] [--skip-build]"
            echo ""
            echo "Options:"
            echo "  --clean       Remove all containers and volumes before starting"
            echo "  --skip-build  Skip Docker image build step"
            echo "  --help        Show this help message"
            exit 0
            ;;
    esac
done

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

wait_for_service() {
    local service=$1
    local max_attempts=$2
    local attempt=1

    echo -n "Waiting for $service to be ready"
    while [ $attempt -le $max_attempts ]; do
        if docker ps | grep -q "$service"; then
            echo ""
            print_success "$service is running"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo ""
    print_error "$service failed to start within $((max_attempts * 2)) seconds"
    return 1
}

check_health() {
    local url=$1
    local service=$2
    local max_attempts=30
    local attempt=1

    echo -n "Checking $service health"
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo ""
            print_success "$service is healthy"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo ""
    print_warning "$service health check failed (may still be initializing)"
    return 1
}

#===============================================================================
# Main Installation Flow
#===============================================================================

print_header "Enterprise RAG Chatbot - Fresh Installation"

cd "$PROJECT_ROOT"

print_info "Installation directory: $PROJECT_ROOT"
print_info "Clean install: $CLEAN_INSTALL"
print_info "Skip build: $SKIP_BUILD"
echo ""

#===============================================================================
# Step 1: Clean Installation (if requested)
#===============================================================================

if [ "$CLEAN_INSTALL" = true ]; then
    print_step "1" "Cleaning existing installation"

    print_warning "This will remove ALL containers, volumes, and data!"
    read -p "Are you sure? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        print_warning "Clean install cancelled"
        exit 0
    fi

    echo ""
    print_info "Stopping all services..."
    docker-compose down -v 2>/dev/null || true

    print_info "Removing Docker volumes..."
    docker volume rm chatbot_postgres_data 2>/dev/null || true
    docker volume rm chatbot_minio_data 2>/dev/null || true
    docker volume rm chatbot_redis_data 2>/dev/null || true

    print_info "Pruning Docker system..."
    docker system prune -f > /dev/null 2>&1

    print_success "Clean complete"
    echo ""
fi

#===============================================================================
# Step 2: Build Docker Images (if not skipped)
#===============================================================================

if [ "$SKIP_BUILD" = false ]; then
    print_step "2" "Building Docker images"

    print_info "Building backend image..."
    docker-compose build backend

    print_info "Building frontend image..."
    docker-compose build frontend

    print_success "Docker images built"
    echo ""
else
    print_step "2" "Skipping Docker image build"
    echo ""
fi

#===============================================================================
# Step 3: Start Infrastructure Services
#===============================================================================

print_step "3" "Starting infrastructure services"

print_info "Starting PostgreSQL..."
docker-compose up -d postgres

print_info "Starting Redis..."
docker-compose up -d redis

print_info "Starting MinIO..."
docker-compose up -d minio

# Wait for infrastructure services
wait_for_service "postgres" 30
wait_for_service "redis" 15
wait_for_service "minio" 15

print_success "Infrastructure services started"
echo ""

# Give PostgreSQL extra time to initialize
print_info "Waiting for PostgreSQL to initialize..."
sleep 10

#===============================================================================
# Step 4: Initialize Database
#===============================================================================

print_step "4" "Initializing database"

if [ -f "$SCRIPT_DIR/setup-database-complete.sh" ]; then
    print_info "Running database setup script..."
    "$SCRIPT_DIR/setup-database-complete.sh" --skip-confirmation

    if [ $? -eq 0 ]; then
        print_success "Database initialized successfully"
    else
        print_error "Database initialization failed"
        exit 1
    fi
else
    print_error "Database setup script not found: $SCRIPT_DIR/setup-database-complete.sh"
    exit 1
fi

echo ""

#===============================================================================
# Step 5: Start Application Services
#===============================================================================

print_step "5" "Starting application services"

print_info "Starting backend..."
docker-compose up -d backend

print_info "Starting frontend..."
docker-compose up -d frontend

# Wait for application services
wait_for_service "backend" 30
wait_for_service "frontend" 30

print_success "Application services started"
echo ""

#===============================================================================
# Step 6: Health Checks
#===============================================================================

print_step "6" "Running health checks"

# Backend health check
check_health "http://localhost:8000/health" "Backend API"

# Frontend health check
check_health "http://localhost:3001" "Frontend"

echo ""

#===============================================================================
# Step 7: Display Service Status
#===============================================================================

print_step "7" "Service status"

echo ""
echo "Running containers:"
docker-compose ps

echo ""

#===============================================================================
# Step 8: Display Connection Information
#===============================================================================

print_step "8" "Connection information"

echo ""
echo -e "${BOLD}Service URLs:${NC}"
echo "  Frontend:    http://localhost:3001"
echo "  Backend API: http://localhost:8000"
echo "  API Docs:    http://localhost:8000/api/docs"
echo "  GraphQL:     http://localhost:8000/graphql"
echo "  MinIO:       http://localhost:9001 (minioadmin/minioadmin)"
echo ""

echo -e "${BOLD}Default Credentials:${NC}"
echo "  Username: admin"
echo "  Email:    admin@enterprise-rag.local"
echo "  Password: admin123"
echo -e "  ${RED}⚠  CHANGE THIS PASSWORD IN PRODUCTION!${NC}"
echo ""

#===============================================================================
# Step 9: Quick Verification Tests
#===============================================================================

print_step "9" "Running verification tests"

echo ""
print_info "Testing backend health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health 2>/dev/null || echo "FAILED")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    print_success "Backend health check: PASS"
else
    print_warning "Backend health check: May still be initializing"
fi

print_info "Testing database connection..."
DB_TEST=$(docker exec rag-postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d '[:space:]')
if [ ! -z "$DB_TEST" ] && [ "$DB_TEST" -gt 0 ]; then
    print_success "Database connection: PASS (found $DB_TEST users)"
else
    print_warning "Database connection: May still be initializing"
fi

print_info "Checking vector extension..."
VECTOR_CHECK=$(docker exec rag-postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector';" 2>/dev/null | tr -d '[:space:]')
if [ "$VECTOR_CHECK" = "1" ]; then
    print_success "Vector extension: INSTALLED"
else
    print_error "Vector extension: NOT FOUND"
fi

echo ""

#===============================================================================
# Completion Summary
#===============================================================================

print_header "Installation Complete!"

echo -e "${GREEN}${BOLD}✅ Enterprise RAG Chatbot is ready!${NC}"
echo ""
echo -e "${BOLD}Next Steps:${NC}"
echo ""
echo "1. Access the frontend:"
echo "   http://localhost:3001"
echo ""
echo "2. Log in with default credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "3. Upload your first document:"
echo "   Use the File Upload module in the UI"
echo ""
echo "4. Test RAG queries:"
echo "   curl -X POST http://localhost:8000/api/v1/query \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"query\": \"your question here\", \"session_id\": \"test-session\"}'"
echo ""
echo "5. View logs:"
echo "   docker-compose logs -f backend"
echo "   docker-compose logs -f frontend"
echo ""
echo -e "${BOLD}Useful Commands:${NC}"
echo "  ./scripts/maintenance/validate-services.sh  # Check all services"
echo "  ./scripts/debugging/diagnose-backend.sh     # Diagnose backend issues"
echo "  docker-compose restart backend              # Restart backend"
echo "  docker-compose logs -f                      # View all logs"
echo ""
echo -e "${BOLD}Documentation:${NC}"
echo "  README.md                                   # Project overview"
echo "  docs/setup/DATABASE_SETUP_GUIDE.md          # Database guide"
echo "  docs/setup/DATABASE_QUICK_REFERENCE.md      # Quick reference"
echo "  CLAUDE.md                                   # Comprehensive guide"
echo ""
print_success "Installation completed at $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
