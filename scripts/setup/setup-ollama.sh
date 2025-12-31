#!/bin/bash

echo "========================================="
echo "Ollama Local Models Setup"
echo "========================================="
echo ""
echo "Ollama provides better WSL2 compatibility than llama.cpp!"
echo ""

# Check docker compose command
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    echo "✗ Docker Compose not found"
    exit 1
fi

echo "Step 1: Starting Ollama service..."
$COMPOSE_CMD up -d ollama

echo ""
echo "Step 2: Finding Ollama container name..."
OLLAMA_CONTAINER=$($COMPOSE_CMD ps --format "{{.Name}}" | grep ollama | head -1)

if [ -z "$OLLAMA_CONTAINER" ]; then
    echo "✗ Error: Ollama container not found"
    echo "Available containers:"
    $COMPOSE_CMD ps
    exit 1
fi

echo "✓ Found Ollama container: $OLLAMA_CONTAINER"

echo ""
echo "Step 3: Waiting for Ollama to be ready (15 seconds)..."
sleep 15

echo ""
echo "Step 4: Checking Ollama health..."
docker exec $OLLAMA_CONTAINER ollama list || {
    echo "⚠️  Ollama not responding yet, waiting 10 more seconds..."
    sleep 10
}

echo ""
echo "Step 5: Pulling Llama 3.2 3B model (~2GB download)..."
docker exec $OLLAMA_CONTAINER ollama pull llama3.2:3b-instruct-q4_K_M

if [ $? -ne 0 ]; then
    echo "Note: Specific quantization tag not found, pulling base model..."
    docker exec $OLLAMA_CONTAINER ollama pull llama3.2:3b
fi

echo ""
echo "Step 6: Pulling Qwen 2.5 1.5B model (~1GB download)..."
docker exec $OLLAMA_CONTAINER ollama pull qwen2.5:1.5b-instruct-q4_K_M

if [ $? -ne 0 ]; then
    echo "Note: Specific quantization tag not found, pulling base model..."
    docker exec $OLLAMA_CONTAINER ollama pull qwen2.5:1.5b
fi

echo ""
echo "Step 7: Verifying installed models..."
docker exec $OLLAMA_CONTAINER ollama list

echo ""
echo "========================================="
echo "✅ Ollama Setup Complete!"
echo "========================================="
echo ""
echo "Downloaded models:"
echo "  • Llama 3.2 3B - General purpose, good quality"
echo "  • Qwen 2.5 1.5B - Fast, multilingual"
echo ""
echo "Next steps:"
echo "1. Rebuild backend to load Ollama support:"
echo "   docker compose restart backend"
echo ""
echo "2. Test at http://localhost:3001"
echo "   Select 'Llama 3.2 3B Q4 (CPU)' or 'Qwen 1.5B Q4 (CPU)'"
echo ""
echo "3. Check logs:"
echo "   docker compose logs -f backend | grep -i ollama"
echo ""
echo "Ollama advantages over llama.cpp:"
echo "  ✅ Better WSL2/Docker volume compatibility"
echo "  ✅ Simpler model management"
echo "  ✅ Automatic model downloads"
echo "  ✅ No file permission issues"
echo ""
