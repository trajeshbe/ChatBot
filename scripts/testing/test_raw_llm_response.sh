#!/bin/bash
# Test raw LLM response to understand what qwen2.5-coder is returning

echo "======================================"
echo "Testing Raw LLM Response"
echo "======================================"
echo ""

# Test 1: Simple prompt to see format
echo "Test 1: Simple test prompt"
echo "----------------------------"
curl -s http://localhost:11434/api/chat -d '{
  "model": "qwen2.5-coder:7b",
  "messages": [
    {
      "role": "system",
      "content": "You must use tools to complete tasks. Respond with TOOL_CALL: followed by the tool name and ARGS: with JSON arguments."
    },
    {
      "role": "user",
      "content": "Read the file at /workspace/sales2.txt"
    }
  ],
  "stream": false
}' | jq -r '.message.content'

echo ""
echo ""

# Test 2: The actual agent task
echo "Test 2: Agent task prompt"
echo "----------------------------"
curl -s http://localhost:11434/api/chat -d '{
  "model": "qwen2.5-coder:7b",
  "messages": [
    {
      "role": "system",
      "content": "You are an autonomous AI agent with access to tools. You MUST use tools to complete tasks - you cannot provide answers without using tools first.\n\nAvailable tools:\n- read_file: Read file contents\n- analyze_dataframe: Analyze data with Pandas\n- visualize_data: Create visualizations\n\nFormat: TOOL_CALL: tool_name\\nARGS: {\"arg\":\"value\"}\n\nFor final answer: FINAL_ANSWER: your response"
    },
    {
      "role": "user",
      "content": "Analyze sales2.txt using Pandas and create visualizations"
    }
  ],
  "stream": false
}' | jq -r '.message.content'

echo ""
echo ""
echo "======================================"
echo "Test Complete"
echo "======================================"
