#!/bin/bash

# Rebuild services with new features: Docling, Template Extraction, Session Management
# This script installs new dependencies and rebuilds containers

set -e

echo "========================================="
echo "Rebuilding with New Features"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to project root
cd "$(dirname "$0")/.."

echo -e "${YELLOW}Step 1: Stopping existing containers...${NC}"
docker-compose down

echo ""
echo -e "${YELLOW}Step 2: Rebuilding backend with new dependencies...${NC}"
echo "  - Docling 2.0.0 (multi-format document processing)"
echo "  - python-dateutil 2.8.2 (date parsing)"
echo "  - Template extraction service"
echo ""
docker-compose build --no-cache backend

echo ""
echo -e "${YELLOW}Step 3: Rebuilding frontend...${NC}"
echo "  - TemplateExtractor component"
echo "  - Collapsible error messages"
echo "  - Session management for web scraping"
echo "  - Hydration error fixes"
echo ""
docker-compose build --no-cache frontend

echo ""
echo -e "${YELLOW}Step 4: Starting services...${NC}"
docker-compose up -d

echo ""
echo -e "${YELLOW}Step 5: Waiting for services to start...${NC}"
sleep 10

echo ""
echo -e "${YELLOW}Step 6: Installing Playwright dependencies in backend...${NC}"
docker-compose exec -T backend playwright install --with-deps chromium || {
    echo -e "${RED}Note: Playwright install may require manual intervention${NC}"
}

echo ""
echo -e "${YELLOW}Step 7: Checking service health...${NC}"
echo ""

# Check backend health
echo -n "Backend: "
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${RED}✗ Not responding${NC}"
fi

# Check frontend health
echo -n "Frontend: "
if curl -s http://localhost:3001 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${RED}✗ Not responding${NC}"
fi

# Check PostgreSQL
echo -n "PostgreSQL: "
if docker-compose exec -T postgres pg_isready > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${RED}✗ Not responding${NC}"
fi

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Rebuild Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "New Features Available:"
echo "  1. Template-based Data Extraction (Excel export)"
echo "  2. Multi-format document processing with Docling"
echo "  3. Session management for web scraping"
echo "  4. Collapsible error messages"
echo "  5. Fixed Next.js hydration errors"
echo ""
echo "API Endpoints:"
echo "  - POST /api/v1/extract/preset/screener_in"
echo "  - POST /api/v1/extract/custom"
echo "  - POST /api/v1/extract/to-excel"
echo "  - GET  /api/v1/extract/presets"
echo ""
echo "Frontend Access:"
echo "  - Main App: http://localhost:3001"
echo "  - New Tab: Data Extraction"
echo ""
echo "To test Screener.in extraction:"
echo "  1. Go to http://localhost:3001"
echo "  2. Click 'Data Extraction' tab"
echo "  3. Enter URL: https://www.screener.in/company/BHARTIARTL/consolidated/"
echo "  4. Click 'Extract Data'"
echo "  5. Click 'Export Excel' when complete"
echo ""
echo "View logs:"
echo "  docker-compose logs -f backend"
echo "  docker-compose logs -f frontend"
echo ""
