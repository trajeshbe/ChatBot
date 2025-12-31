#!/bin/bash

echo "========================================="
echo "Diagnosing llama.cpp Model Issue"
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

echo "Step 1: Stopping llama-cpp..."
$COMPOSE_CMD stop llama-cpp
$COMPOSE_CMD rm -f llama-cpp

echo ""
echo "Step 2: Checking volume and files..."
docker run --rm -v llama_models:/models busybox ls -lh /models/

echo ""
echo "Step 3: Checking file count..."
FILE_COUNT=$(docker run --rm -v llama_models:/models busybox sh -c 'ls -1 /models/*.gguf 2>/dev/null | wc -l')
echo "Found $FILE_COUNT GGUF files"

if [ "$FILE_COUNT" = "0" ] || [ -z "$FILE_COUNT" ]; then
    echo ""
    echo "❌ No model files found in volume!"
    echo ""
    echo "Downloading models directly to volume..."

    # Download Llama 3.2 3B
    echo "Downloading Llama 3.2 3B Q4_K_M (2GB)..."
    docker run --rm -v llama_models:/models alpine/curl:latest sh -c '
        cd /models
        if [ ! -f "Llama-3.2-3B-Instruct-Q4_K_M.gguf" ]; then
            curl -L -o Llama-3.2-3B-Instruct-Q4_K_M.gguf \
                "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
            echo "Downloaded Llama 3.2 3B"
        else
            echo "Llama 3.2 3B already exists"
        fi
        ls -lh Llama-3.2-3B-Instruct-Q4_K_M.gguf
    '

    # Download Qwen 1.5B
    echo ""
    echo "Downloading Qwen 1.5B Q4_K_M (1GB)..."
    docker run --rm -v llama_models:/models alpine/curl:latest sh -c '
        cd /models
        if [ ! -f "qwen2.5-1.5b-instruct-q4_k_m.gguf" ]; then
            curl -L -o qwen2.5-1.5b-instruct-q4_k_m.gguf \
                "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
            echo "Downloaded Qwen 1.5B"
        else
            echo "Qwen 1.5B already exists"
        fi
        ls -lh qwen2.5-1.5b-instruct-q4_k_m.gguf
    '
else
    echo "✅ Files found in volume"
    echo ""
    echo "Testing file integrity..."
    docker run --rm -v llama_models:/models busybox sh -c '
        for file in /models/*.gguf; do
            if [ -f "$file" ]; then
                size=$(stat -c %s "$file" 2>/dev/null || stat -f %z "$file" 2>/dev/null)
                if [ "$size" -lt 1000000 ]; then
                    echo "❌ $(basename $file) is too small ($size bytes) - likely corrupt"
                    rm "$file"
                    echo "   Removed corrupt file"
                else
                    echo "✅ $(basename $file) - $size bytes"
                fi
            fi
        done
    '
fi

echo ""
echo "Step 4: Final verification..."
docker run --rm -v llama_models:/models busybox ls -lh /models/

echo ""
echo "Step 5: Starting llama-cpp..."
$COMPOSE_CMD up -d llama-cpp

echo ""
echo "Waiting 10 seconds for startup..."
sleep 10

echo ""
echo "Step 6: Checking llama-cpp status..."
if $COMPOSE_CMD ps | grep -q "llama-cpp.*Up"; then
    echo "✅ llama-cpp is running!"

    # Test the health endpoint
    echo ""
    echo "Testing model endpoint..."
    sleep 3
    HEALTH=$(curl -s http://localhost:8080/health 2>/dev/null || echo "not responding")
    echo "Health check: $HEALTH"
else
    echo "❌ llama-cpp crashed. Last 50 log lines:"
    $COMPOSE_CMD logs --tail=50 llama-cpp | grep -v "warning: no usable GPU"
fi

echo ""
echo "========================================="
echo "Diagnosis Complete"
echo "========================================="
echo ""
echo "If llama-cpp is still crashing, check:"
echo "  docker compose logs llama-cpp"
echo ""
echo "Look for:"
echo "  ✅ 'llm_load_tensors: ...' = Model loaded successfully"
echo "  ❌ 'failed to open GGUF file' = File access issue"
echo ""
