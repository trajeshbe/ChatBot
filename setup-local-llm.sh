#!/bin/bash
set -e

echo "========================================="
echo "Setting up Local LLM (llama.cpp)"
echo "========================================="
echo ""

# Step 1: Create volume and download model
echo "Step 1: Downloading TinyLlama model (Q4_K_M ~637MB)..."
echo "This will take a few minutes depending on your connection."
echo ""

# Create a temporary container to download the model
docker volume create llama_models 2>/dev/null || true

# Download TinyLlama 1.1B model (Q4_K_M quantization - good balance of quality/size)
docker run --rm -v llama_models:/models alpine sh -c "
    apk add --no-cache wget && \
    cd /models && \
    if [ ! -f tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf ]; then
        echo 'Downloading model...' && \
        wget -q --show-progress https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf || \
        wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
    else
        echo 'Model already downloaded!'
    fi
"

echo ""
echo "✅ Model downloaded successfully!"
echo ""

# Step 2: Check current docker-compose status
echo "Step 2: Checking services..."
docker compose ps

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. The llama.cpp service is ready in docker-compose.yml"
echo "2. Run: docker compose up -d llama-cpp"
echo "3. Wait ~10 seconds for model to load"
echo "4. Check logs: docker compose logs llama-cpp --tail 20"
echo "5. Test endpoint: curl http://localhost:8080/health"
echo ""
echo "To force chatbot to use local LLM:"
echo "6. Temporarily disable OpenAI: export OPENAI_API_KEY=''"
echo "7. Restart backend: docker compose restart backend"
echo "8. Test at http://localhost:3001"
echo ""
