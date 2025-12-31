#!/bin/bash

echo "========================================="
echo "Multi-Model Integration Test"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Step 1: Checking backend service..."
if docker compose ps backend | grep -q "Up"; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${RED}✗ Backend is not running${NC}"
    echo "Starting backend..."
    docker compose up -d backend
    sleep 5
fi

echo ""
echo "Step 2: Checking frontend service..."
if docker compose ps frontend | grep -q "Up"; then
    echo -e "${GREEN}✓ Frontend is running${NC}"
else
    echo -e "${RED}✗ Frontend is not running${NC}"
    echo "Starting frontend..."
    docker compose up -d frontend
    sleep 5
fi

echo ""
echo "Step 3: Testing backend health..."
HEALTH=$(curl -s http://localhost:8000/health 2>&1)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backend health check passed${NC}"
    echo "Response: $HEALTH"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
    echo "Checking backend logs..."
    docker compose logs backend --tail 20
    exit 1
fi

echo ""
echo "Step 4: Testing models API endpoint..."
MODELS=$(curl -s http://localhost:8000/api/v1/models/ 2>&1)
if [ $? -eq 0 ] && echo "$MODELS" | grep -q "models"; then
    echo -e "${GREEN}✓ Models API is working${NC}"
    echo "Available model groups:"
    echo "$MODELS" | python3 -c "import sys, json; data=json.load(sys.stdin); print('  - Proprietary:', len(data.get('grouped', {}).get('proprietary', [])), 'models'); print('  - Local GPU:', len(data.get('grouped', {}).get('local_gpu', [])), 'models'); print('  - Local CPU:', len(data.get('grouped', {}).get('local_cpu', [])), 'models')" 2>/dev/null || echo "  (Unable to parse model counts)"
else
    echo -e "${YELLOW}⚠ Models API returned unexpected response${NC}"
    echo "Response: $MODELS"
    echo ""
    echo "This is expected if backend dependencies aren't installed yet."
    echo "Rebuild backend with: docker compose build backend"
fi

echo ""
echo "Step 5: Testing GPU detection..."
GPU_INFO=$(curl -s http://localhost:8000/api/v1/models/gpu-info 2>&1)
if [ $? -eq 0 ] && echo "$GPU_INFO" | grep -q "available"; then
    echo -e "${GREEN}✓ GPU detection endpoint is working${NC}"
    echo "$GPU_INFO" | python3 -m json.tool 2>/dev/null || echo "Response: $GPU_INFO"
else
    echo -e "${YELLOW}⚠ GPU detection endpoint not responding${NC}"
    echo "This may require backend rebuild"
fi

echo ""
echo "Step 6: Checking frontend compilation..."
FRONTEND_LOGS=$(docker compose logs frontend --tail 5 2>&1)
if echo "$FRONTEND_LOGS" | grep -q "Compiled" || echo "$FRONTEND_LOGS" | grep -q "ready"; then
    echo -e "${GREEN}✓ Frontend is compiling successfully${NC}"
else
    echo -e "${YELLOW}⚠ Frontend may have compilation issues${NC}"
    echo "Recent logs:"
    echo "$FRONTEND_LOGS"
fi

echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="
echo ""

# Check if everything is OK
BACKEND_OK=$(docker compose ps backend | grep -q "Up" && echo "yes" || echo "no")
FRONTEND_OK=$(docker compose ps frontend | grep -q "Up" && echo "yes" || echo "no")
HEALTH_OK=$(curl -s http://localhost:8000/health 2>&1 | grep -q "healthy" && echo "yes" || echo "no")

if [ "$BACKEND_OK" = "yes" ] && [ "$FRONTEND_OK" = "yes" ] && [ "$HEALTH_OK" = "yes" ]; then
    echo -e "${GREEN}✓ All services are running!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Open http://localhost:3001 in your browser"
    echo "2. You should see the 'Model:' dropdown in the header"
    echo "3. Click it to see available models"
    echo "4. Try sending a message to test"
    echo ""
    echo "If models API shows warnings:"
    echo "  docker compose build backend"
    echo "  docker compose restart backend"
else
    echo -e "${RED}✗ Some issues detected${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Rebuild backend: docker compose build backend"
    echo "2. Restart services: docker compose restart backend frontend"
    echo "3. Check logs: docker compose logs backend --tail 50"
    echo "4. Check logs: docker compose logs frontend --tail 50"
fi

echo ""
echo "========================================="
