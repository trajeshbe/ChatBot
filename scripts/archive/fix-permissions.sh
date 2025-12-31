#!/bin/bash

echo "========================================="
echo "Fixing llama.cpp File Permissions"
echo "========================================="

# Check docker compose command
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    echo "✗ Docker Compose not found"
    exit 1
fi

echo "Step 1: Checking current file ownership..."
docker run --rm -v llama_models:/models busybox ls -ln /models/

echo ""
echo "Step 2: Changing ownership to user 1000:1000 (common container user)..."
docker run --rm -v llama_models:/models busybox chown -R 1000:1000 /models/

echo ""
echo "Step 3: Setting permissions to 644 (read for all)..."
docker run --rm -v llama_models:/models busybox chmod -R 644 /models/*.gguf

echo ""
echo "Step 4: Verifying new permissions..."
docker run --rm -v llama_models:/models busybox ls -ln /models/

echo ""
echo "Step 5: Restarting llama-cpp..."
$COMPOSE_CMD stop llama-cpp
$COMPOSE_CMD rm -f llama-cpp
$COMPOSE_CMD up -d llama-cpp

echo ""
echo "Step 6: Waiting for llama-cpp to start (15 seconds)..."
sleep 15

echo ""
echo "Step 7: Checking llama-cpp logs..."
$COMPOSE_CMD logs --tail=30 llama-cpp | grep -v "warning: no usable GPU"

echo ""
echo "Step 8: Testing if llama-cpp is running..."
if $COMPOSE_CMD ps | grep -q "llama-cpp.*Up"; then
    echo "✅ llama-cpp is RUNNING!"
    echo ""
    echo "Testing health endpoint..."
    sleep 3
    curl -s http://localhost:8080/health 2>/dev/null && echo "" || echo "Endpoint not ready yet"
else
    echo "❌ Still crashing. Showing full logs:"
    $COMPOSE_CMD logs llama-cpp
fi

echo ""
echo "========================================="
echo "Done!"
echo "========================================="
