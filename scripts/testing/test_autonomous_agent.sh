#!/bin/bash
# Test autonomous agent with package installation

echo "=========================================="
echo "Testing Autonomous Agent"
echo "Task: ML predictions requiring scikit-learn"
echo "=========================================="
echo ""

# Task that requires ML library not pre-installed
TASK_DESC="Analyze sales2.txt, build a linear regression model to predict revenue based on quantity, and create a scatter plot showing actual vs predicted values. Save the plot to artifacts/"

echo "📝 Task: $TASK_DESC"
echo ""

# Encode task
TASK_B64=$(echo -n "$TASK_DESC" | base64 -w 0)

echo "Running autonomous agent..."
echo "Expected behavior:"
echo "1. Agent analyzes task"
echo "2. Realizes it needs scikit-learn"
echo "3. Installs scikit-learn using install_package tool"
echo "4. Reads sales data"
echo "5. Builds ML model"
echo "6. Creates visualization"
echo "7. Provides final answer"
echo ""

# Run agent
docker exec \
  -e OLLAMA_HOST=http://ollama:11434 \
  -e AGENT_LLM_MODEL=qwen2.5-coder:7b \
  -e TASK_B64="$TASK_B64" \
  -e AGENT_MAX_ITERATIONS=25 \
  -e AGENT_TIMEOUT_SECONDS=600 \
  -e PYTHONUNBUFFERED=1 \
  rag-agent-runtime \
  python /app/entrypoint_agent.py 2>&1 | grep -E "Installing package|install_package|scikit-learn|FINAL_ANSWER|Artifacts:|Task completed"

echo ""
echo "Checking if scikit-learn was installed..."
docker exec rag-agent-runtime pip list | grep scikit-learn && echo "✅ scikit-learn installed!" || echo "❌ scikit-learn NOT installed"

echo ""
echo "Checking for generated artifacts..."
docker exec rag-agent-runtime ls -lh /workspace/artifacts/*.png 2>/dev/null || echo "No artifacts found"

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="
