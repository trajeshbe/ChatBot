#!/bin/bash

# diagnose-ollama.sh
# Comprehensive Ollama diagnostics

set +e  # Don't exit on errors, we want to see all checks

echo "=================================="
echo "Ollama Diagnostics"
echo "=================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check 1: Container status
echo -e "${BLUE}1. Container Status${NC}"
if docker ps | grep -q rag-ollama; then
    echo -e "${GREEN}✓ Ollama container is running${NC}"
    docker ps | grep rag-ollama
else
    echo -e "${RED}✗ Ollama container is NOT running${NC}"
    echo "To start: docker compose up -d ollama"
    exit 1
fi
echo ""

# Check 2: Container health
echo -e "${BLUE}2. Container Health${NC}"
HEALTH=$(docker inspect --format='{{.State.Health.Status}}' rag-ollama 2>/dev/null || echo "no healthcheck")
if [ "$HEALTH" = "healthy" ]; then
    echo -e "${GREEN}✓ Ollama is healthy${NC}"
elif [ "$HEALTH" = "unhealthy" ]; then
    echo -e "${RED}✗ Ollama is unhealthy${NC}"
    echo "Recent healthcheck logs:"
    docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' rag-ollama
else
    echo -e "${YELLOW}⚠ Healthcheck status: $HEALTH${NC}"
fi
echo ""

# Check 3: Network connectivity
echo -e "${BLUE}3. Network Connectivity${NC}"
if docker exec rag-ollama curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama API is accessible${NC}"
else
    echo -e "${RED}✗ Ollama API is NOT accessible${NC}"
    echo "Testing basic connectivity:"
    docker exec rag-ollama curl -v http://localhost:11434/api/tags 2>&1 | tail -20
fi
echo ""

# Check 4: List available models
echo -e "${BLUE}4. Available Models${NC}"
MODELS=$(docker exec rag-ollama curl -s http://localhost:11434/api/tags 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "$MODELS" | python3 -m json.tool 2>/dev/null || echo "$MODELS"

    # Check for required models
    echo ""
    echo "Required models check:"
    if echo "$MODELS" | grep -q "llama3.2:3b-instruct-q4_K_M"; then
        echo -e "${GREEN}✓ llama3.2:3b-instruct-q4_K_M is available${NC}"
    else
        echo -e "${RED}✗ llama3.2:3b-instruct-q4_K_M is MISSING${NC}"
        echo "  Pull with: docker exec rag-ollama ollama pull llama3.2:3b-instruct-q4_K_M"
    fi

    if echo "$MODELS" | grep -q "qwen2.5:1.5b-instruct-q4_K_M"; then
        echo -e "${GREEN}✓ qwen2.5:1.5b-instruct-q4_K_M is available${NC}"
    else
        echo -e "${RED}✗ qwen2.5:1.5b-instruct-q4_K_M is MISSING${NC}"
        echo "  Pull with: docker exec rag-ollama ollama pull qwen2.5:1.5b-instruct-q4_K_M"
    fi
else
    echo -e "${RED}✗ Failed to list models${NC}"
fi
echo ""

# Check 5: Test API endpoint
echo -e "${BLUE}5. Test API Endpoint${NC}"
echo "Testing /api/generate endpoint..."
TEST_RESPONSE=$(docker exec rag-ollama curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:3b-instruct-q4_K_M",
    "prompt": "Say OK",
    "stream": false,
    "options": {
      "num_predict": 5
    }
  }' 2>&1)

if [ $? -eq 0 ] && echo "$TEST_RESPONSE" | grep -q "response"; then
    echo -e "${GREEN}✓ /api/generate endpoint is working${NC}"
    echo "Response:"
    echo "$TEST_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$TEST_RESPONSE"
else
    echo -e "${RED}✗ /api/generate endpoint failed${NC}"
    echo "Error response:"
    echo "$TEST_RESPONSE"
fi
echo ""

# Check 6: Container logs
echo -e "${BLUE}6. Recent Container Logs (last 20 lines)${NC}"
docker logs --tail 20 rag-ollama
echo ""

# Check 7: Resource usage
echo -e "${BLUE}7. Resource Usage${NC}"
docker stats --no-stream rag-ollama
echo ""

# Summary
echo "=================================="
echo "Diagnostics Complete"
echo "=================================="
echo ""
echo "Next steps:"
echo "  1. If models are missing, run: ./scripts/setup/setup-ollama-models.sh"
echo "  2. If API is not responding, restart: docker compose restart ollama"
echo "  3. If issues persist, check logs: docker logs -f rag-ollama"
echo ""
