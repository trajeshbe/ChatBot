#!/bin/bash

# Monitor Hybrid Extraction - Testing Helper Script
# Usage: ./scripts/testing/monitor_hybrid_extraction.sh

echo "========================================"
echo "Hybrid Extraction Live Monitor"
echo "========================================"
echo ""
echo "Watching for:"
echo "  ✅ Multi-analyzer ensemble"
echo "  ✅ Content type detection"
echo "  ✅ Hybrid extraction trigger"
echo "  ✅ OCR processing"
echo "  ✅ Vision model analysis"
echo "  ✅ Result merging"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================"
echo ""

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Monitor logs with color highlighting
docker-compose logs backend -f 2>&1 | grep --line-buffered -E \
  "(Processing document:|Multi-analyzer|Voting result|Content type:|Running hybrid|Hybrid extraction|Methods used|Confidence|OCR.*complete|Vision.*complete|chunks generated|Embedding)" \
  | while IFS= read -r line; do
    # Color code different types of messages
    if echo "$line" | grep -q "Processing document:"; then
        echo -e "${BLUE}${line}${NC}"
    elif echo "$line" | grep -q "Multi-analyzer"; then
        echo -e "${YELLOW}${line}${NC}"
    elif echo "$line" | grep -q "Voting result"; then
        echo -e "${YELLOW}${line}${NC}"
    elif echo "$line" | grep -q "Running hybrid"; then
        echo -e "${GREEN}${line}${NC}"
    elif echo "$line" | grep -q "Hybrid extraction.*complete"; then
        echo -e "${GREEN}${line}${NC}"
    elif echo "$line" | grep -q "ERROR"; then
        echo -e "${RED}${line}${NC}"
    else
        echo "$line"
    fi
done
