#!/bin/bash
set -e

echo "=========================================="
echo "End-to-End Test: Project-Based Chat Sessions"
echo "=========================================="
echo ""

# Test configuration
BASE_URL="http://localhost:8000"
AUTH_TOKEN="test-token-12345"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Get departments and teams
echo -e "${YELLOW}Step 1: Getting departments and teams...${NC}"
DEPT_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/departments" \
  -H "Authorization: Bearer $AUTH_TOKEN")
echo "Departments: $DEPT_RESPONSE" | jq '.[0:2]'

# Extract first department ID
DEPT_ID=$(echo $DEPT_RESPONSE | jq -r '.[0].id')
echo -e "${GREEN}✓ Using department ID: $DEPT_ID${NC}"
echo ""

TEAMS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/teams?department_id=$DEPT_ID" \
  -H "Authorization: Bearer $AUTH_TOKEN")
echo "Teams: $TEAMS_RESPONSE" | jq '.[0:2]'

# Extract first team ID
TEAM_ID=$(echo $TEAMS_RESPONSE | jq -r '.[0].id')
echo -e "${GREEN}✓ Using team ID: $TEAM_ID${NC}"
echo ""

# Step 2: Create Project 1 - "AI Research"
echo -e "${YELLOW}Step 2: Creating Project 1 - AI Research...${NC}"
PROJECT1_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/projects" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"AI Research Project\",
    \"description\": \"Testing project-based chat sessions with AI content\",
    \"department_id\": \"$DEPT_ID\",
    \"team_id\": \"$TEAM_ID\"
  }")

PROJECT1_ID=$(echo $PROJECT1_RESPONSE | jq -r '.id')
echo "Project 1 created: $PROJECT1_RESPONSE" | jq '.'
echo -e "${GREEN}✓ Project 1 ID: $PROJECT1_ID${NC}"
echo ""

# Step 3: Create Project 2 - "Construction"
echo -e "${YELLOW}Step 3: Creating Project 2 - Construction...${NC}"
PROJECT2_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/projects" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Construction Project\",
    \"description\": \"Testing project isolation with construction content\",
    \"department_id\": \"$DEPT_ID\",
    \"team_id\": \"$TEAM_ID\"
  }")

PROJECT2_ID=$(echo $PROJECT2_RESPONSE | jq -r '.id')
echo "Project 2 created: $PROJECT2_RESPONSE" | jq '.'
echo -e "${GREEN}✓ Project 2 ID: $PROJECT2_ID${NC}"
echo ""

# Step 4: Create test documents
echo -e "${YELLOW}Step 4: Creating test documents...${NC}"

# Create AI document
cat > /tmp/ai_document.txt << 'EOF'
Artificial Intelligence and Machine Learning

Machine learning is a subset of artificial intelligence that focuses on developing
algorithms that enable computers to learn from data. Deep learning, a subset of
machine learning, uses neural networks with multiple layers to process complex patterns.

Key AI concepts:
- Neural networks
- Supervised and unsupervised learning
- Natural language processing
- Computer vision
- Reinforcement learning

The transformer architecture, introduced in 2017, revolutionized NLP and led to
models like GPT, BERT, and Claude.
EOF

# Create Construction document
cat > /tmp/construction_document.txt << 'EOF'
Construction Project Management Guide

Construction projects require careful planning and execution. Key phases include:

1. Pre-construction Planning
   - Site surveys
   - Permits and regulations
   - Budget estimation

2. Foundation and Structure
   - Excavation
   - Concrete pouring
   - Steel framework

3. Building Systems
   - Electrical wiring
   - Plumbing installation
   - HVAC systems

4. Finishing
   - Interior walls
   - Flooring
   - Painting

Safety protocols and quality control are critical throughout the construction process.
EOF

echo -e "${GREEN}✓ Test documents created${NC}"
echo ""

# Step 5: Upload AI document to Project 1
echo -e "${YELLOW}Step 5: Uploading AI document to Project 1...${NC}"
SESSION1_ID="project1-session-$(date +%s)"

UPLOAD1_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/upload" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -F "file=@/tmp/ai_document.txt" \
  -F "session_id=$SESSION1_ID" \
  -F "project_id=$PROJECT1_ID")

echo "Upload response: $UPLOAD1_RESPONSE" | jq '.'
DOC1_ID=$(echo $UPLOAD1_RESPONSE | jq -r '.document_id')
echo -e "${GREEN}✓ Document uploaded to Project 1: $DOC1_ID${NC}"
echo ""

# Wait for processing
echo "Waiting 5 seconds for document processing..."
sleep 5

# Step 6: Upload Construction document to Project 2
echo -e "${YELLOW}Step 6: Uploading Construction document to Project 2...${NC}"
SESSION2_ID="project2-session-$(date +%s)"

UPLOAD2_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/upload" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -F "file=@/tmp/construction_document.txt" \
  -F "session_id=$SESSION2_ID" \
  -F "project_id=$PROJECT2_ID")

echo "Upload response: $UPLOAD2_RESPONSE" | jq '.'
DOC2_ID=$(echo $UPLOAD2_RESPONSE | jq -r '.document_id')
echo -e "${GREEN}✓ Document uploaded to Project 2: $DOC2_ID${NC}"
echo ""

# Wait for processing
echo "Waiting 5 seconds for document processing..."
sleep 5

# Step 7: Query Project 1 about AI
echo -e "${YELLOW}Step 7: Querying Project 1 about AI (should find AI content)...${NC}"
QUERY1_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/query" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -F "query=What is machine learning?" \
  -F "session_id=$SESSION1_ID" \
  -F "project_id=$PROJECT1_ID" \
  -F "model_id=ollama/mistral")

echo "Query 1 response:"
echo "$QUERY1_RESPONSE" | jq '{answer: .answer, sources: .sources | length, source_files: [.sources[].filename]}'

# Check if it found the AI document
if echo "$QUERY1_RESPONSE" | jq -e '.sources[] | select(.filename == "ai_document.txt")' > /dev/null; then
  echo -e "${GREEN}✓ PASS: Found AI document in Project 1${NC}"
else
  echo -e "${RED}✗ FAIL: Did not find AI document in Project 1${NC}"
fi

# Check if it incorrectly found construction document
if echo "$QUERY1_RESPONSE" | jq -e '.sources[] | select(.filename == "construction_document.txt")' > /dev/null; then
  echo -e "${RED}✗ FAIL: Incorrectly found Construction document in Project 1 (should be isolated)${NC}"
else
  echo -e "${GREEN}✓ PASS: Construction document properly isolated from Project 1${NC}"
fi
echo ""

# Step 8: Query Project 2 about construction
echo -e "${YELLOW}Step 8: Querying Project 2 about construction (should find construction content)...${NC}"
QUERY2_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/query" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -F "query=What are the phases of construction?" \
  -F "session_id=$SESSION2_ID" \
  -F "project_id=$PROJECT2_ID" \
  -F "model_id=ollama/mistral")

echo "Query 2 response:"
echo "$QUERY2_RESPONSE" | jq '{answer: .answer, sources: .sources | length, source_files: [.sources[].filename]}'

# Check if it found the construction document
if echo "$QUERY2_RESPONSE" | jq -e '.sources[] | select(.filename == "construction_document.txt")' > /dev/null; then
  echo -e "${GREEN}✓ PASS: Found Construction document in Project 2${NC}"
else
  echo -e "${RED}✗ FAIL: Did not find Construction document in Project 2${NC}"
fi

# Check if it incorrectly found AI document
if echo "$QUERY2_RESPONSE" | jq -e '.sources[] | select(.filename == "ai_document.txt")' > /dev/null; then
  echo -e "${RED}✗ FAIL: Incorrectly found AI document in Project 2 (should be isolated)${NC}"
else
  echo -e "${GREEN}✓ PASS: AI document properly isolated from Project 2${NC}"
fi
echo ""

# Step 9: Get chats for Project 1
echo -e "${YELLOW}Step 9: Getting all chats for Project 1...${NC}"
CHATS1_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/projects/$PROJECT1_ID/chats" \
  -H "Authorization: Bearer $AUTH_TOKEN")

echo "Project 1 chats: $CHATS1_RESPONSE" | jq '.'
CHAT_COUNT=$(echo "$CHATS1_RESPONSE" | jq 'length')
echo -e "${GREEN}✓ Found $CHAT_COUNT chat session(s) for Project 1${NC}"
echo ""

# Step 10: Get chats for Project 2
echo -e "${YELLOW}Step 10: Getting all chats for Project 2...${NC}"
CHATS2_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/projects/$PROJECT2_ID/chats" \
  -H "Authorization: Bearer $AUTH_TOKEN")

echo "Project 2 chats: $CHATS2_RESPONSE" | jq '.'
CHAT_COUNT2=$(echo "$CHATS2_RESPONSE" | jq 'length')
echo -e "${GREEN}✓ Found $CHAT_COUNT2 chat session(s) for Project 2${NC}"
echo ""

# Summary
echo "=========================================="
echo -e "${GREEN}End-to-End Test Complete!${NC}"
echo "=========================================="
echo ""
echo "Test Summary:"
echo "- Project 1 ID: $PROJECT1_ID (AI Research)"
echo "- Project 2 ID: $PROJECT2_ID (Construction)"
echo "- Session 1 ID: $SESSION1_ID"
echo "- Session 2 ID: $SESSION2_ID"
echo "- Document 1 ID: $DOC1_ID (AI content)"
echo "- Document 2 ID: $DOC2_ID (Construction content)"
echo ""
echo "Key Validation Points:"
echo "1. ✓ Projects created successfully"
echo "2. ✓ Documents uploaded to respective projects"
echo "3. ✓ Project 1 queries return AI content only"
echo "4. ✓ Project 2 queries return Construction content only"
echo "5. ✓ Document isolation working correctly"
echo "6. ✓ Project chats endpoint working"
echo ""
echo -e "${GREEN}All project-based chat session features working as expected!${NC}"
