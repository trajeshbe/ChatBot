#!/bin/bash
# Test autonomous ML task with scikit-learn

echo "Testing Autonomous ML Task"
echo "==========================="

TASK="Analyze sales2.txt, build a linear regression model to predict revenue based on quantity, and create a scatter plot showing actual vs predicted values. Save the plot to artifacts/"

echo "Task: $TASK"
echo ""

TASK_B64=$(echo -n "$TASK" | base64 -w 0)

docker exec \
  -e OLLAMA_HOST=http://ollama:11434 \
  -e AGENT_LLM_MODEL=qwen2.5-coder:7b \
  -e TASK_B64="$TASK_B64" \
  -e AGENT_MAX_ITERATIONS=25 \
  -e AGENT_TIMEOUT_SECONDS=600 \
  -e PYTHONUNBUFFERED=1 \
  rag-agent-runtime \
  python /app/entrypoint_agent.py

echo ""
echo "Checking results..."
docker exec rag-agent-runtime ls -lh /workspace/artifacts/ 2>/dev/null || echo "No artifacts directory"
docker exec rag-agent-runtime pip list | grep scikit-learn
