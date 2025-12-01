#!/bin/bash
# Test script to debug agent task execution
# This simulates exactly what happens when a user creates an agent task

set -e

echo "======================================"
echo "Agent Task Debugging Test Script"
echo "======================================"
echo ""

# Task description
TASK_DESC="Analyze sales2.txt using Pandas and create visualizations"
echo "📝 Task Description: $TASK_DESC"
echo ""

# Step 1: Check if sales2.txt exists in workspace
echo "Step 1: Checking workspace files..."
docker exec rag-agent-runtime ls -lah /workspace/ || echo "⚠️  Workspace not accessible"
echo ""

# Step 2: Verify Ollama connectivity
echo "Step 2: Verifying Ollama connectivity..."
docker exec rag-agent-runtime curl -s http://ollama:11434/api/tags | head -20
echo ""

# Step 3: Check qwen2.5-coder:7b model
echo "Step 3: Checking if qwen2.5-coder:7b is available..."
docker exec rag-agent-runtime curl -s http://ollama:11434/api/tags | grep -q "qwen2.5-coder:7b" && echo "✅ Model found" || echo "❌ Model NOT found"
echo ""

# Step 4: Encode task in base64
echo "Step 4: Encoding task description..."
TASK_B64=$(echo -n "$TASK_DESC" | base64 -w 0)
echo "Base64: $TASK_B64"
echo ""

# Step 5: Test base64 decoding
echo "Step 5: Testing base64 decoding..."
echo "$TASK_B64" | base64 -d
echo ""
echo ""

# Step 6: Check entrypoint_agent.py exists
echo "Step 6: Checking entrypoint_agent.py..."
docker exec rag-agent-runtime ls -lh /app/entrypoint_agent.py
echo ""

# Step 7: Test Python imports
echo "Step 7: Testing Python environment..."
docker exec rag-agent-runtime python -c "
import sys
print(f'Python version: {sys.version}')

try:
    import pandas
    print('✅ pandas imported')
except ImportError as e:
    print(f'❌ pandas import failed: {e}')

try:
    import matplotlib
    print('✅ matplotlib imported')
except ImportError as e:
    print(f'❌ matplotlib import failed: {e}')

try:
    import requests
    print('✅ requests imported')
except ImportError as e:
    print(f'❌ requests import failed: {e}')

try:
    from langchain_community.chat_models import ChatOllama
    print('✅ ChatOllama imported')
except ImportError as e:
    print(f'❌ ChatOllama import failed: {e}')
"
echo ""

# Step 8: Run the actual agent task with full debugging
echo "Step 8: Running agent task (this may take 1-2 minutes)..."
echo "----------------------------------------"

docker exec \
  -e OLLAMA_HOST=http://ollama:11434 \
  -e AGENT_LLM_MODEL=qwen2.5-coder:7b \
  -e TASK_B64="$TASK_B64" \
  -e AGENT_MAX_ITERATIONS=20 \
  -e AGENT_TIMEOUT_SECONDS=600 \
  -e PYTHONUNBUFFERED=1 \
  rag-agent-runtime \
  python /app/entrypoint_agent.py 2>&1 || {
    EXIT_CODE=$?
    echo ""
    echo "❌ Agent task failed with exit code: $EXIT_CODE"
    echo ""

    # Try to get more details
    echo "Checking last 50 lines of container logs..."
    docker logs rag-agent-runtime --tail 50

    exit $EXIT_CODE
  }

echo ""
echo "✅ Agent task completed successfully"
echo ""

# Step 9: Check for generated artifacts
echo "Step 9: Checking for generated artifacts..."
docker exec rag-agent-runtime ls -lah /artifacts/ 2>/dev/null || echo "⚠️  No artifacts directory or empty"

echo ""
echo "======================================"
echo "Test Complete"
echo "======================================"
