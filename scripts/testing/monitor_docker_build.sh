#!/bin/bash

# Monitor Docker Build Progress - Testing Helper Script
# Usage: ./scripts/testing/monitor_docker_build.sh

echo "========================================"
echo "Docker Build Progress Monitor"
echo "========================================"
echo ""
echo "Watching for:"
echo "  ✅ System package installation"
echo "  ✅ Tesseract OCR installation"
echo "  ✅ Python package installation"
echo "  ✅ Application code copy"
echo "  ✅ Build completion"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================"
echo ""

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if build is running
if ! ps aux | grep "docker-compose build" | grep -v grep > /dev/null; then
    echo -e "${RED}No Docker build process found running.${NC}"
    echo ""
    echo "To start a build, run:"
    echo "  docker-compose build backend"
    echo "or:"
    echo "  docker-compose build --no-cache backend"
    exit 1
fi

echo -e "${BLUE}Build process detected. Monitoring logs...${NC}"
echo ""

# Follow docker-compose build logs
docker-compose logs -f backend 2>&1 | grep --line-buffered -E \
  "(Step [0-9]+/[0-9]+|tesseract|pip install|COPY|DONE|ERROR|Successfully|WARNING)" \
  | while IFS= read -r line; do
    # Color code different types of messages
    if echo "$line" | grep -q "Step"; then
        echo -e "${YELLOW}${line}${NC}"
    elif echo "$line" | grep -q "tesseract"; then
        echo -e "${GREEN}${line}${NC}"
    elif echo "$line" | grep -q "DONE"; then
        echo -e "${GREEN}${line}${NC}"
    elif echo "$line" | grep -q "Successfully"; then
        echo -e "${GREEN}${line}${NC}"
    elif echo "$line" | grep -q "ERROR"; then
        echo -e "${RED}${line}${NC}"
    elif echo "$line" | grep -q "WARNING"; then
        echo -e "${YELLOW}${line}${NC}"
    else
        echo "$line"
    fi
done
