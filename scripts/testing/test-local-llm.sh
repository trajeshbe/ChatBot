#!/bin/bash

echo "========================================="
echo "Local LLM Testing Script"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check if llama.cpp is running
echo "Step 1: Checking llama.cpp service status..."
if docker compose ps llama-cpp | grep -q "Up"; then
    echo -e "${GREEN}✓ llama-cpp is running${NC}"
else
    echo -e "${RED}✗ llama-cpp is not running${NC}"
    echo ""
    echo "Please start it with: docker compose up -d llama-cpp"
    exit 1
fi

echo ""

# Step 2: Check llama.cpp health
echo "Step 2: Testing llama.cpp endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8080/health 2>&1)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ llama.cpp health check passed${NC}"
    echo "Response: $HEALTH_RESPONSE"
else
    echo -e "${RED}✗ llama.cpp health check failed${NC}"
    echo "Make sure the service is fully started (check logs)"
    echo "Run: docker compose logs llama-cpp --tail 30"
    exit 1
fi

echo ""

# Step 3: Test direct llama.cpp inference
echo "Step 3: Testing direct llama.cpp completion..."
echo "(This tests the model directly)"
echo ""

PROMPT="Hello, who are you?"
echo "Prompt: $PROMPT"
echo ""
echo "Response from llama.cpp:"
echo "---"

curl -s http://localhost:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"prompt\": \"$PROMPT\",
    \"max_tokens\": 50,
    \"temperature\": 0.7
  }" | python3 -c "import sys, json; print(json.load(sys.stdin)['choices'][0]['text'])" 2>/dev/null

echo ""
echo "---"
echo ""

# Step 4: Check backend configuration
echo "Step 4: Checking backend LLM configuration..."
BACKEND_ENV=$(docker compose exec -T backend env | grep -E "OPENAI_API_KEY|LLAMA_CPP_ENDPOINT|USE_VLLM")
echo "$BACKEND_ENV"

echo ""

# Step 5: Test through backend API
echo "Step 5: Testing through backend RAG API..."
echo "(This tests the full stack: backend -> llama.cpp)"
echo ""

# Temporarily disable OpenAI by passing empty key in the request context
# Note: This tests if llama.cpp fallback works

echo "Sending test query to backend..."
BACKEND_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/query \
  -F "query=Hello, introduce yourself in one sentence" \
  -F "use_cache=false")

echo ""
echo "Backend Response:"
echo "---"
echo "$BACKEND_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$BACKEND_RESPONSE"
echo "---"

# Check which model was used
MODEL_USED=$(echo "$BACKEND_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('model', 'unknown'))" 2>/dev/null)
echo ""
if [ "$MODEL_USED" = "llama.cpp" ]; then
    echo -e "${GREEN}✓ Successfully using local LLM (llama.cpp)!${NC}"
elif [ "$MODEL_USED" = "openai" ]; then
    echo -e "${YELLOW}⚠ Still using OpenAI - llama.cpp not being used as fallback${NC}"
    echo ""
    echo "To force llama.cpp usage:"
    echo "1. Edit .env and remove OPENAI_API_KEY value temporarily"
    echo "2. Run: docker compose restart backend"
    echo "3. Run this test again"
else
    echo -e "${YELLOW}⚠ Could not determine which model was used${NC}"
    echo "Model field: $MODEL_USED"
fi

echo ""
echo "========================================="
echo "Test Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "- Test in UI: http://localhost:3001"
echo "- View llama.cpp logs: docker compose logs llama-cpp -f"
echo "- View backend logs: docker compose logs backend -f"
echo ""
