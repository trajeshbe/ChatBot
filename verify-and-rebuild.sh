#!/bin/bash

echo "========================================="
echo "Verifying Enhanced LLM Service Setup"
echo "========================================="

# Check if docker/docker-compose is available
if ! command -v docker &> /dev/null; then
    echo "✗ Docker not found. Please install Docker first."
    exit 1
fi

if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    echo "✗ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

echo "✓ Using: $COMPOSE_CMD"
echo ""

# Check if required files exist
echo "Checking required files..."
FILES=(
    "backend/app/services/llm_service_enhanced.py"
    "backend/app/models/model_registry.py"
    "backend/app/utils/gpu_detector.py"
    "backend/app/models/__init__.py"
    "backend/app/utils/__init__.py"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "✗ $file (missing)"
        exit 1
    fi
done

echo ""
echo "========================================="
echo "Rebuilding Backend Container"
echo "========================================="

# Stop backend
echo "Stopping backend..."
$COMPOSE_CMD stop backend

# Remove old backend container
echo "Removing old backend container..."
$COMPOSE_CMD rm -f backend

# Rebuild backend (no cache to ensure fresh build)
echo "Rebuilding backend (this may take a few minutes)..."
$COMPOSE_CMD build --no-cache backend

# Start backend
echo "Starting backend..."
$COMPOSE_CMD up -d backend

# Wait for backend to start
echo ""
echo "Waiting for backend to start (10 seconds)..."
sleep 10

# Check logs for Enhanced LLM Service message
echo ""
echo "========================================="
echo "Checking Backend Logs"
echo "========================================="

echo "Looking for LLM service initialization messages..."
$COMPOSE_CMD logs backend | grep -i "llm service\|enhanced\|model.*initialized" | tail -20

echo ""
echo "========================================="
echo "Verification Complete"
echo "========================================="
echo ""
echo "To view live logs, run:"
echo "  $COMPOSE_CMD logs -f backend"
echo ""
echo "To test model selection:"
echo "  1. Open http://localhost:3001"
echo "  2. Select a model from the dropdown (e.g., 'Qwen 1.5B Q4 (CPU)')"
echo "  3. Ask: 'what is your model name?'"
echo "  4. Check the model badge below the response"
echo ""
