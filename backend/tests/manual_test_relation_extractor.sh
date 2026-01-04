#!/bin/bash
# Manual E2E Test for Relation Extractor Module

echo "🧪 Relation Extractor E2E Test"
echo "=============================="
echo

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_BASE="http://localhost:8000"
SESSION_ID="test-relation-extractor-$(date +%s)"

echo "📝 Step 1: Create sample document"
echo "--------------------------------"

SAMPLE_DOC="/tmp/apple_relationships_test.txt"
cat > "$SAMPLE_DOC" << 'EOF'
Apple Inc. was founded by Steve Jobs in Cupertino, California in 1976.

In 2011, Tim Cook became the CEO of Apple Inc. after Steve Jobs stepped down.

Apple acquired Beats Electronics for $3 billion in 2014, bringing Dr. Dre
and Jimmy Iovine into the company.

Apple is headquartered in Cupertino, California and operates globally.
The company developed the iPhone, which revolutionized mobile technology.

In 2021, Apple partnered with Hyundai to develop autonomous vehicles.
EOF

echo "✅ Sample document created at $SAMPLE_DOC"
echo

echo "📤 Step 2: Upload document"
echo "-------------------------"

UPLOAD_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/upload" \
  -F "file=@$SAMPLE_DOC" \
  -F "session_id=$SESSION_ID")

DOCUMENT_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('document_id', ''))" 2>/dev/null)

if [ -z "$DOCUMENT_ID" ]; then
    echo -e "${RED}❌ Failed to upload document${NC}"
    echo "Response: $UPLOAD_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✅ Document uploaded successfully${NC}"
echo "   Document ID: $DOCUMENT_ID"
echo

echo "🔍 Step 3: Extract relations (auto mode)"
echo "---------------------------------------"

EXTRACT_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/modules/relation-extractor/extract" \
  -H "Content-Type: application/json" \
  -d "{
    \"document_id\": \"$DOCUMENT_ID\",
    \"extraction_mode\": \"auto\",
    \"min_confidence\": 0.5,
    \"deduplicate\": true
  }")

# Check if response contains expected fields
if echo "$EXTRACT_RESPONSE" | grep -q "extraction_id"; then
    echo -e "${GREEN}✅ Extraction successful${NC}"

    # Parse and display key metrics
    EXTRACTION_ID=$(echo "$EXTRACT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('extraction_id', 'N/A'))" 2>/dev/null)
    TOTAL_RELATIONS=$(echo "$EXTRACT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total_relations_found', 0))" 2>/dev/null)
    AVG_CONFIDENCE=$(echo "$EXTRACT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('avg_confidence', 0))" 2>/dev/null)
    EXTRACTION_TIME=$(echo "$EXTRACT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('extraction_time_seconds', 0))" 2>/dev/null)

    echo "   Extraction ID: $EXTRACTION_ID"
    echo "   Total Relations Found: $TOTAL_RELATIONS"
    echo "   Average Confidence: $AVG_CONFIDENCE"
    echo "   Extraction Time: ${EXTRACTION_TIME}s"
    echo

    # Display sample relations
    echo "📊 Sample Relations:"
    echo "-------------------"
    echo "$EXTRACT_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    relations = data.get('relations', [])

    for i, rel in enumerate(relations[:5], 1):
        subject = rel.get('subject', {})
        obj = rel.get('object', {})
        relation_type = rel.get('relation', 'UNKNOWN')
        confidence = rel.get('confidence', 0)
        context = rel.get('context', '')[:80]

        print(f\"{i}. {subject.get('text', 'N/A')} --[{relation_type}]--> {obj.get('text', 'N/A')}\")
        print(f\"   Confidence: {confidence:.2f}\")
        print(f\"   Context: {context}...\")
        print()
except Exception as e:
    print(f\"Error parsing relations: {e}\")
" 2>&1

    # Display graph statistics
    echo
    echo "📈 Graph Statistics:"
    echo "-------------------"
    echo "$EXTRACT_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    graph = data.get('graph', {})

    print(f\"Entities: {graph.get('num_entities', 0)}\")
    print(f\"Relations: {graph.get('num_relations', 0)}\")

    entity_counts = graph.get('entity_type_counts', {})
    if entity_counts:
        print(\"\\nEntity Types:\")
        for etype, count in sorted(entity_counts.items(), key=lambda x: x[1], reverse=True):
            print(f\"  - {etype}: {count}\")

    relation_counts = graph.get('relation_type_counts', {})
    if relation_counts:
        print(\"\\nRelation Types:\")
        for rtype, count in sorted(relation_counts.items(), key=lambda x: x[1], reverse=True):
            print(f\"  - {rtype}: {count}\")
except Exception as e:
    print(f\"Error parsing graph: {e}\")
" 2>&1

else
    echo -e "${RED}❌ Extraction failed${NC}"
    echo "Response:"
    echo "$EXTRACT_RESPONSE" | python3 -m json.tool 2>&1 || echo "$EXTRACT_RESPONSE"
    exit 1
fi

echo
echo "🎉 Test completed successfully!"
echo "================================"
echo
echo "📋 Summary:"
echo "  - Document uploaded: ✅"
echo "  - Relations extracted: ✅"
echo "  - Total relations found: $TOTAL_RELATIONS"
echo "  - Average confidence: $AVG_CONFIDENCE"
echo

# Cleanup
rm -f "$SAMPLE_DOC"
