#!/bin/bash

echo "=========================================================================="
echo "TESTING AADHAN RETRIEVAL - Vector Search Investigation"
echo "=========================================================================="
echo ""

# Test 1: Query "Who is Aadhan?" with GPT-4
echo "Test 1: 'Who is Aadhan?' with GPT-4"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s -X POST http://localhost:8000/api/v1/query \
  -F "query=Who is Aadhan?" \
  -F "model_id=gpt-4" \
  -o /tmp/aadhan_test1.json

echo "Tool selected: $(jq -r '.metadata.tool_usage.tools_used[0]' /tmp/aadhan_test1.json)"
echo "Sources found: $(jq -r '.sources | length' /tmp/aadhan_test1.json)"
echo ""
echo "Answer preview:"
jq -r '.answer' /tmp/aadhan_test1.json | head -c 400
echo ""
echo ""

if [ "$(jq -r '.sources | length' /tmp/aadhan_test1.json)" -gt 0 ]; then
    echo "Source filenames:"
    jq -r '.sources[] | .filename' /tmp/aadhan_test1.json
fi

echo ""
echo ""

# Test 2: Query "Tell me about King Aadhan" with GPT-4
echo "Test 2: 'Tell me about King Aadhan' with GPT-4"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s -X POST http://localhost:8000/api/v1/query \
  -F "query=Tell me about King Aadhan from the story" \
  -F "model_id=gpt-4" \
  -o /tmp/aadhan_test2.json

echo "Tool selected: $(jq -r '.metadata.tool_usage.tools_used[0]' /tmp/aadhan_test2.json)"
echo "Sources found: $(jq -r '.sources | length' /tmp/aadhan_test2.json)"
echo ""
echo "Answer preview:"
jq -r '.answer' /tmp/aadhan_test2.json | head -c 400
echo ""
echo ""

if [ "$(jq -r '.sources | length' /tmp/aadhan_test2.json)" -gt 0 ]; then
    echo "Source filenames:"
    jq -r '.sources[] | .filename' /tmp/aadhan_test2.json
fi

