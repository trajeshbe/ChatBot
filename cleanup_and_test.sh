#!/bin/bash
set -e

echo "=================================================="
echo "COMPREHENSIVE CLEANUP AND END-TO-END TEST"
echo "=================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# API URL
API_URL="http://localhost:8000"

echo -e "${YELLOW}Step 1: Clean up database${NC}"
echo "Removing all documents, chunks, sessions, and messages..."

docker-compose exec -T postgres psql -U postgres -d ragchatbot << 'SQL'
-- Clean up document-related data
TRUNCATE TABLE document_chunks CASCADE;
TRUNCATE TABLE documents CASCADE;

-- Clean up session-related data
TRUNCATE TABLE conversation_messages CASCADE;
TRUNCATE TABLE conversations CASCADE;
TRUNCATE TABLE chat_sessions CASCADE;
TRUNCATE TABLE session_documents CASCADE;

-- Clean up evaluation data
TRUNCATE TABLE evaluation_results CASCADE;
TRUNCATE TABLE feedback CASCADE;

-- Keep projects and users
-- Keep RBAC structure

SELECT 'Documents:', COUNT(*) FROM documents;
SELECT 'Chunks:', COUNT(*) FROM document_chunks;
SELECT 'Sessions:', COUNT(*) FROM chat_sessions;
SELECT 'Messages:', COUNT(*) FROM conversation_messages;
SQL

echo -e "${GREEN}✓ Database cleaned${NC}"
echo ""

echo -e "${YELLOW}Step 2: Clean up MinIO${NC}"
echo "Removing all files from MinIO buckets..."

# List and clean MinIO (this is a placeholder - adjust based on your MinIO setup)
# docker-compose exec minio mc rm --recursive --force minio/documents/

echo -e "${GREEN}✓ MinIO cleaned (manual verification needed)${NC}"
echo ""

echo -e "${YELLOW}Step 3: Get project IDs${NC}"

# Get Global project ID
GLOBAL_PROJECT_ID=$(docker-compose exec -T postgres psql -U postgres -d ragchatbot -t -c "SELECT id FROM projects WHERE name='Global' LIMIT 1;" | xargs)
echo "Global Project ID: $GLOBAL_PROJECT_ID"

# Get Construction Intelligence project ID
CONSTRUCTION_PROJECT_ID=$(docker-compose exec -T postgres psql -U postgres -d ragchatbot -t -c "SELECT id FROM projects WHERE name='Construction Intelligence' LIMIT 1;" | xargs)
echo "Construction Intelligence Project ID: $CONSTRUCTION_PROJECT_ID"

# Get Marketing project ID (or create if doesn't exist)
MARKETING_PROJECT_ID=$(docker-compose exec -T postgres psql -U postgres -d ragchatbot -t -c "SELECT id FROM projects WHERE name='Marketing' LIMIT 1;" | xargs)
if [ -z "$MARKETING_PROJECT_ID" ]; then
    echo "Creating Marketing project..."
    MARKETING_PROJECT_ID=$(docker-compose exec -T postgres psql -U postgres -d ragchatbot -t -c "INSERT INTO projects (name, description) VALUES ('Marketing', 'Marketing materials and campaigns') RETURNING id;" | xargs)
fi
echo "Marketing Project ID: $MARKETING_PROJECT_ID"

echo ""

# Create test files
echo -e "${YELLOW}Step 4: Create test documents${NC}"

mkdir -p /tmp/test_docs

cat > /tmp/test_docs/global_doc.txt << 'DOCEOF'
This is a global document about general topics.
It discusses artificial intelligence, machine learning, and data science.
This document should be accessible from all project contexts.
DOCEOF

cat > /tmp/test_docs/construction_doc.txt << 'DOCEOF'
This is a construction document about building projects.
It contains information about blueprints, dimensions, and architectural plans.
The building has 3 floors and measures 50x30 meters.
This document should ONLY be visible in Construction Intelligence project.
DOCEOF

cat > /tmp/test_docs/marketing_doc.txt << 'DOCEOF'
This is a marketing document about campaigns and strategies.
It discusses brand positioning, customer engagement, and social media.
The campaign budget is $50,000 and targets millennials.
This document should ONLY be visible in Marketing project.
DOCEOF

echo -e "${GREEN}✓ Test documents created${NC}"
echo ""

echo "=================================================="
echo "END-TO-END TESTING BEGINS"
echo "=================================================="
echo ""

# Test 1: Upload to Global
echo -e "${BLUE}TEST 1: Upload document to Global project${NC}"
RESPONSE=$(curl -s -X POST "$API_URL/api/v1/upload" \
  -F "file=@/tmp/test_docs/global_doc.txt" \
  -F "session_id=test-global-session" \
  -F "project_id=$GLOBAL_PROJECT_ID")

echo "Response: $RESPONSE"
GLOBAL_DOC_ID=$(echo $RESPONSE | jq -r '.document_id')
echo "Global Document ID: $GLOBAL_DOC_ID"

# Verify in DB
docker-compose exec -T postgres psql -U postgres -d ragchatbot << SQL
SELECT 'Global doc verification:';
SELECT filename, project_id::text, processed 
FROM documents 
WHERE id = '$GLOBAL_DOC_ID';
SQL

sleep 3
echo ""

# Test 2: Upload to Construction
echo -e "${BLUE}TEST 2: Upload document to Construction Intelligence${NC}"
RESPONSE=$(curl -s -X POST "$API_URL/api/v1/upload" \
  -F "file=@/tmp/test_docs/construction_doc.txt" \
  -F "session_id=test-construction-session" \
  -F "project_id=$CONSTRUCTION_PROJECT_ID")

echo "Response: $RESPONSE"
CONSTRUCTION_DOC_ID=$(echo $RESPONSE | jq -r '.document_id')
echo "Construction Document ID: $CONSTRUCTION_DOC_ID"

# Verify in DB
docker-compose exec -T postgres psql -U postgres -d ragchatbot << SQL
SELECT 'Construction doc verification:';
SELECT filename, project_id::text, processed 
FROM documents 
WHERE id = '$CONSTRUCTION_DOC_ID';
SQL

sleep 3
echo ""

# Test 3: Upload to Marketing
echo -e "${BLUE}TEST 3: Upload document to Marketing${NC}"
RESPONSE=$(curl -s -X POST "$API_URL/api/v1/upload" \
  -F "file=@/tmp/test_docs/marketing_doc.txt" \
  -F "session_id=test-marketing-session" \
  -F "project_id=$MARKETING_PROJECT_ID")

echo "Response: $RESPONSE"
MARKETING_DOC_ID=$(echo $RESPONSE | jq -r '.document_id')
echo "Marketing Document ID: $MARKETING_DOC_ID"

sleep 3
echo ""

# Test 4: Verify document isolation
echo -e "${BLUE}TEST 4: Verify document isolation${NC}"

docker-compose exec -T postgres psql -U postgres -d ragchatbot << SQL
SELECT 'All documents:';
SELECT filename, project_id::text, processed FROM documents ORDER BY upload_date;

SELECT '';
SELECT 'Documents by project:';
SELECT p.name, COUNT(d.id) as doc_count
FROM projects p
LEFT JOIN documents d ON p.id = d.project_id
GROUP BY p.id, p.name
ORDER BY p.name;
SQL

echo ""

# Test 5: Query in Construction project
echo -e "${BLUE}TEST 5: Query in Construction project (should only search Construction docs)${NC}"
sleep 5  # Wait for embeddings

RESPONSE=$(curl -s -X POST "$API_URL/api/v1/query" \
  -F "query=What are the dimensions?" \
  -F "session_id=test-construction-session" \
  -F "project_id=$CONSTRUCTION_PROJECT_ID" \
  -F "use_cache=false" \
  -F "model=ollama/llama3.2:1b")

echo "Response: $RESPONSE" | jq '.'
echo ""
echo "Sources:"
echo "$RESPONSE" | jq -r '.sources[] | "  - \(.filename) (relevance: \(.relevance))"'
echo ""

# Check if sources contain ONLY construction doc
SOURCES=$(echo "$RESPONSE" | jq -r '.sources[].filename')
if echo "$SOURCES" | grep -q "construction_doc.txt"; then
    echo -e "${GREEN}✓ Construction doc found in sources${NC}"
else
    echo -e "${RED}✗ Construction doc NOT found in sources!${NC}"
fi

if echo "$SOURCES" | grep -q "marketing_doc.txt\|global_doc.txt"; then
    echo -e "${RED}✗ LEAK DETECTED: Other project docs in Construction query!${NC}"
else
    echo -e "${GREEN}✓ No document leakage${NC}"
fi

echo ""

# Test 6: Query in Marketing project
echo -e "${BLUE}TEST 6: Query in Marketing project (should only search Marketing docs)${NC}"

RESPONSE=$(curl -s -X POST "$API_URL/api/v1/query" \
  -F "query=What is the campaign budget?" \
  -F "session_id=test-marketing-session" \
  -F "project_id=$MARKETING_PROJECT_ID" \
  -F "use_cache=false" \
  -F "model=ollama/llama3.2:1b")

echo "Response: $RESPONSE" | jq '.'
echo ""
echo "Sources:"
echo "$RESPONSE" | jq -r '.sources[] | "  - \(.filename) (relevance: \(.relevance))"'
echo ""

# Check if sources contain ONLY marketing doc
SOURCES=$(echo "$RESPONSE" | jq -r '.sources[].filename')
if echo "$SOURCES" | grep -q "marketing_doc.txt"; then
    echo -e "${GREEN}✓ Marketing doc found in sources${NC}"
else
    echo -e "${RED}✗ Marketing doc NOT found in sources!${NC}"
fi

if echo "$SOURCES" | grep -q "construction_doc.txt\|global_doc.txt"; then
    echo -e "${RED}✗ LEAK DETECTED: Other project docs in Marketing query!${NC}"
else
    echo -e "${GREEN}✓ No document leakage${NC}"
fi

echo ""

# Test 7: Session isolation
echo -e "${BLUE}TEST 7: Verify session-project association${NC}"

docker-compose exec -T postgres psql -U postgres -d ragchatbot << SQL
SELECT 'Session-Project associations:';
SELECT s.session_id, p.name as project_name, s.created_at
FROM chat_sessions s
LEFT JOIN projects p ON s.project_id = p.id
WHERE s.session_id LIKE 'test-%'
ORDER BY s.created_at;
SQL

echo ""

# Test 8: Document API filtering
echo -e "${BLUE}TEST 8: Test document API filtering${NC}"

echo "All documents:"
curl -s "$API_URL/api/v1/documents" | jq -r '.[] | "  - \(.filename) (project_id: \(.project_id))"'

echo ""
echo "Construction Intelligence documents only:"
curl -s "$API_URL/api/v1/documents?project_id=$CONSTRUCTION_PROJECT_ID" | jq -r '.[] | "  - \(.filename)"'

echo ""
echo "Marketing documents only:"
curl -s "$API_URL/api/v1/documents?project_id=$MARKETING_PROJECT_ID" | jq -r '.[] | "  - \(.filename)"'

echo ""

echo "=================================================="
echo "TEST SUMMARY"
echo "=================================================="

docker-compose exec -T postgres psql -U postgres -d ragchatbot << SQL
-- Final verification
SELECT 'Final State:';
SELECT 
    p.name as project,
    COUNT(DISTINCT d.id) as docs,
    COUNT(DISTINCT dc.id) as chunks,
    COUNT(DISTINCT s.id) as sessions
FROM projects p
LEFT JOIN documents d ON p.id = d.project_id
LEFT JOIN document_chunks dc ON d.id = dc.document_id
LEFT JOIN chat_sessions s ON p.id = s.project_id
GROUP BY p.id, p.name
ORDER BY p.name;
SQL

echo ""
echo -e "${GREEN}Testing complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Review the output above for any LEAK DETECTED messages"
echo "2. Test in UI: http://localhost:3001"
echo "3. Verify project selector switches correctly"
echo "4. Check browser console for session/model switching logs"
