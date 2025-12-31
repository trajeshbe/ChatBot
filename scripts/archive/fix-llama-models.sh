#!/bin/bash

echo "========================================="
echo "Fixing llama.cpp Model Access Issue"
echo "========================================="

# Check if docker/docker-compose is available
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    echo "✗ Docker Compose not found"
    exit 1
fi

echo "Step 1: Stopping llama-cpp service..."
$COMPOSE_CMD stop llama-cpp
$COMPOSE_CMD rm -f llama-cpp

echo ""
echo "Step 2: Checking if models exist in volume..."
$COMPOSE_CMD run --rm -v llama_models:/models alpine ls -lh /models/

echo ""
echo "Step 3: Checking file integrity..."
FILE_COUNT=$($COMPOSE_CMD run --rm -v llama_models:/models alpine sh -c 'ls -1 /models/*.gguf 2>/dev/null | wc -l')
echo "Found $FILE_COUNT GGUF model files"

if [ "$FILE_COUNT" -eq "0" ]; then
    echo ""
    echo "❌ No model files found! Re-downloading..."

    # Download Llama 3.2 3B
    echo "Downloading Llama 3.2 3B Q4_K_M..."
    $COMPOSE_CMD run --rm -v llama_models:/models alpine sh -c '
        apk add --no-cache wget
        cd /models
        if [ ! -f "Llama-3.2-3B-Instruct-Q4_K_M.gguf" ]; then
            wget -O Llama-3.2-3B-Instruct-Q4_K_M.gguf \
                "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf" || exit 1
        fi
        ls -lh Llama-3.2-3B-Instruct-Q4_K_M.gguf
    '

    # Download Qwen 1.5B
    echo ""
    echo "Downloading Qwen 1.5B Q4_K_M..."
    $COMPOSE_CMD run --rm -v llama_models:/models alpine sh -c '
        apk add --no-cache wget
        cd /models
        if [ ! -f "qwen2.5-1.5b-instruct-q4_k_m.gguf" ]; then
            wget -O qwen2.5-1.5b-instruct-q4_k_m.gguf \
                "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf" || exit 1
        fi
        ls -lh qwen2.5-1.5b-instruct-q4_k_m.gguf
    '
fi

echo ""
echo "Step 4: Fixing permissions..."
$COMPOSE_CMD run --rm -v llama_models:/models alpine chmod 644 /models/*.gguf 2>/dev/null || true

echo ""
echo "Step 5: Verifying model files..."
$COMPOSE_CMD run --rm -v llama_models:/models alpine ls -lh /models/

echo ""
echo "Step 6: Starting llama-cpp with test model..."
$COMPOSE_CMD up -d llama-cpp

echo ""
echo "Step 7: Waiting for llama-cpp to start (15 seconds)..."
sleep 15

echo ""
echo "Step 8: Checking llama-cpp status..."
if $COMPOSE_CMD ps | grep llama-cpp | grep -q "Up"; then
    echo "✅ llama-cpp is running!"
    echo ""
    echo "Testing model endpoint..."
    sleep 5
    curl -s http://localhost:8080/health 2>/dev/null || echo "Endpoint not responding yet (may need more time)"
else
    echo "❌ llama-cpp failed to start. Checking logs..."
    $COMPOSE_CMD logs --tail=30 llama-cpp
    exit 1
fi

echo ""
echo "========================================="
echo "Fix Complete!"
echo "========================================="
echo ""
echo "To verify:"
echo "  docker compose logs -f llama-cpp"
echo ""
echo "You should see:"
echo "  'HTTP server is listening' (without repeated crashes)"
echo ""
