#!/bin/bash
set -e

echo "========================================="
echo "Local Model Setup - Lightweight & Fast"
echo "========================================="
echo ""
echo "This script downloads GGUF quantized models"
echo "optimized for CPU inference."
echo ""
echo "Total models: 2 (max 5 local models total)"
echo "  1. Llama 3.2 3B Q4_K_M (~2.0 GB)"
echo "  2. Qwen 1.5B Q4_K_M (~1.0 GB)"
echo ""
echo "Total download: ~3 GB"
echo "========================================="
echo ""

# Create volume
echo "Creating model volume..."
docker volume create llama_models 2>/dev/null || true

# Ask which models to download
echo ""
echo "Which models do you want to download?"
echo "1) Llama 3.2 3B Q4 only (recommended for most users)"
echo "2) Qwen 1.5B Q4 only (fastest, smallest)"
echo "3) Both (default)"
read -p "Choice [1-3, default=3]: " choice
choice=${choice:-3}

echo ""

# Download Llama 3.2 3B
if [ "$choice" = "1" ] || [ "$choice" = "3" ]; then
    echo "========================================="
    echo "Downloading Llama 3.2 3B Q4_K_M (~2.0 GB)"
    echo "========================================="

    docker run --rm -v llama_models:/models alpine sh -c "
        apk add --no-cache wget && \
        cd /models && \
        if [ -f Llama-3.2-3B-Instruct-Q4_K_M.gguf ]; then
            echo 'Llama 3.2 3B already downloaded!'
        else
            echo 'Downloading from HuggingFace...' && \
            wget --show-progress \
                https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf || \
            wget https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf
        fi
    "

    echo ""
    echo "✅ Llama 3.2 3B downloaded!"
    echo ""
fi

# Download Qwen 1.5B
if [ "$choice" = "2" ] || [ "$choice" = "3" ]; then
    echo "========================================="
    echo "Downloading Qwen 1.5B Q4_K_M (~1.0 GB)"
    echo "========================================="

    docker run --rm -v llama_models:/models alpine sh -c "
        apk add --no-cache wget && \
        cd /models && \
        if [ -f qwen2.5-1.5b-instruct-q4_k_m.gguf ]; then
            echo 'Qwen 1.5B already downloaded!'
        else
            echo 'Downloading from HuggingFace...' && \
            wget --show-progress \
                https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf || \
            wget https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf
        fi
    "

    echo ""
    echo "✅ Qwen 1.5B downloaded!"
    echo ""
fi

# Verify downloads
echo "========================================="
echo "Verifying downloads..."
echo "========================================="

docker run --rm -v llama_models:/models alpine sh -c "
    cd /models && \
    echo 'Downloaded models:' && \
    ls -lh *.gguf 2>/dev/null || echo 'No models found!'
"

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Models downloaded to Docker volume: llama_models"
echo ""
echo "Next steps:"
echo "1. Start llama.cpp service:"
echo "   docker compose up -d llama-cpp"
echo ""
echo "2. Check which model is active in docker-compose.yml"
echo "   (default: Llama 3.2 3B Q4)"
echo ""
echo "3. To switch models, edit docker-compose.yml line 103:"
echo "   - Llama 3.2 3B: /models/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
echo "   - Qwen 1.5B:    /models/qwen2.5-1.5b-instruct-q4_k_m.gguf"
echo ""
echo "4. Restart after model change:"
echo "   docker compose restart llama-cpp"
echo ""
echo "5. Test at http://localhost:3001"
echo "   Select model from dropdown!"
echo ""
