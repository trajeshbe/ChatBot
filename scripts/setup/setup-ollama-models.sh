#!/bin/bash

# setup-ollama-models.sh
# Pulls required Ollama models for the RAG chatbot

set -e

echo "=================================="
echo "Ollama Model Setup"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Ollama container is running
echo "1. Checking Ollama service..."
if docker ps | grep -q rag-ollama; then
    echo -e "${GREEN}✓ Ollama container is running${NC}"
else
    echo -e "${RED}✗ Ollama container is not running${NC}"
    echo "Please start services with: docker compose up -d ollama"
    exit 1
fi

# Wait for Ollama to be ready
echo ""
echo "2. Waiting for Ollama to be ready..."
MAX_RETRIES=10
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker exec rag-ollama curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama is ready${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting for Ollama... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}✗ Ollama failed to start${NC}"
    exit 1
fi

# List current models
echo ""
echo "3. Current models:"
docker exec rag-ollama ollama list || echo "No models installed yet"

# Pull required models
echo ""
echo "4. Pulling required models..."
echo ""

# Model 1: Llama 3.2 3B Q4 (Best CPU model - ~2GB)
echo -e "${YELLOW}Pulling Llama 3.2 3B Q4_K_M...${NC}"
echo "Size: ~2GB | Speed: 5-10 tokens/s on CPU"
if docker exec rag-ollama ollama pull llama3.2:3b-instruct-q4_K_M; then
    echo -e "${GREEN}✓ Llama 3.2 3B Q4 pulled successfully${NC}"
else
    echo -e "${RED}✗ Failed to pull Llama 3.2 3B Q4${NC}"
fi

echo ""

# Model 2: Qwen 1.5B Q4 (Ultra-fast CPU model - ~1GB)
echo -e "${YELLOW}Pulling Qwen 1.5B Q4_K_M...${NC}"
echo "Size: ~1GB | Speed: 10-15 tokens/s on CPU"
if docker exec rag-ollama ollama pull qwen2.5:1.5b-instruct-q4_K_M; then
    echo -e "${GREEN}✓ Qwen 1.5B Q4 pulled successfully${NC}"
else
    echo -e "${RED}✗ Failed to pull Qwen 1.5B Q4${NC}"
fi

# Verify models
echo ""
echo "5. Verifying installed models..."
echo ""
docker exec rag-ollama ollama list

# Test models
echo ""
echo "6. Testing models..."
echo ""

echo "Testing Llama 3.2 3B..."
if docker exec rag-ollama ollama run llama3.2:3b-instruct-q4_K_M "Hello, respond with 'OK'" --verbose; then
    echo -e "${GREEN}✓ Llama 3.2 3B is working${NC}"
else
    echo -e "${YELLOW}⚠ Llama 3.2 3B test inconclusive${NC}"
fi

echo ""
echo "Testing Qwen 1.5B..."
if docker exec rag-ollama ollama run qwen2.5:1.5b-instruct-q4_K_M "Hello, respond with 'OK'" --verbose; then
    echo -e "${GREEN}✓ Qwen 1.5B is working${NC}"
else
    echo -e "${YELLOW}⚠ Qwen 1.5B test inconclusive${NC}"
fi

# Summary
echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Available models:"
echo "  1. llama3.2:3b-instruct-q4_K_M (Best CPU model)"
echo "  2. qwen2.5:1.5b-instruct-q4_K_M (Ultra-fast CPU model)"
echo ""
echo "You can now use these models in the chatbot."
echo ""
echo "To verify, run:"
echo "  docker exec rag-ollama curl http://localhost:11434/api/tags"
echo ""
