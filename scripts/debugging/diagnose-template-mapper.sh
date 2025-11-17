#!/bin/bash

# Template Mapper Diagnostic Script
# Tests template-based extraction with comprehensive debugging

set -e

echo "═══════════════════════════════════════════════════════════════════"
echo "🔍 Template Mapper Diagnostic Tool"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
TEST_URL="${TEST_URL:-https://www.screener.in/company/RELIANCE/}"

echo "📋 Configuration:"
echo "   API URL: $API_URL"
echo "   Test URL: $TEST_URL"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2

    case $status in
        "success")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "error")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "warning")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "info")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
    esac
}

# Check if backend is running
echo "═══════════════════════════════════════════════════════════════════"
echo "1️⃣  Checking Backend Status"
echo "═══════════════════════════════════════════════════════════════════"

if curl -s -f "$API_URL/health" > /dev/null 2>&1; then
    print_status "success" "Backend is running at $API_URL"
else
    print_status "error" "Backend is not running at $API_URL"
    echo ""
    echo "💡 Start the backend with: docker-compose up -d backend"
    exit 1
fi
echo ""

# Check available presets
echo "═══════════════════════════════════════════════════════════════════"
echo "2️⃣  Checking Available Preset Templates"
echo "═══════════════════════════════════════════════════════════════════"

PRESETS_RESPONSE=$(curl -s "$API_URL/api/v1/extract/presets")
echo "Response:"
echo "$PRESETS_RESPONSE" | jq '.' || echo "$PRESETS_RESPONSE"
echo ""

# Test 1: Preset Template Extraction
echo "═══════════════════════════════════════════════════════════════════"
echo "3️⃣  Test 1: Preset Template Extraction (screener_in)"
echo "═══════════════════════════════════════════════════════════════════"

print_status "info" "Testing preset template extraction from: $TEST_URL"

PRESET_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/extract/preset/screener_in" \
    -H "Content-Type: application/json" \
    -d "{\"url\": \"$TEST_URL\", \"session_id\": \"diagnostic-test\"}")

echo "Response:"
echo "$PRESET_RESPONSE" | jq '.' || echo "$PRESET_RESPONSE"
echo ""

# Check if extraction was successful
if echo "$PRESET_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
    print_status "success" "Preset extraction successful!"

    # Count extracted fields
    ROW_COUNT=$(echo "$PRESET_RESPONSE" | jq -r '.row_count')
    FIELD_COUNT=$(echo "$PRESET_RESPONSE" | jq -r '.data[0] | length')

    echo ""
    print_status "info" "Rows extracted: $ROW_COUNT"
    print_status "info" "Fields per row: $FIELD_COUNT"
    echo ""

    # Display sample data
    echo "📊 Sample Data (first row):"
    echo "$PRESET_RESPONSE" | jq -r '.data[0]'

else
    print_status "error" "Preset extraction failed"
    ERROR_MSG=$(echo "$PRESET_RESPONSE" | jq -r '.error // .detail // "Unknown error"')
    echo "Error: $ERROR_MSG"
fi
echo ""

# Test 2: Smart Template Mapping
echo "═══════════════════════════════════════════════════════════════════"
echo "4️⃣  Test 2: Smart Template Mapping (LLM-based)"
echo "═══════════════════════════════════════════════════════════════════"

print_status "info" "Testing smart template mapping with custom columns"

CUSTOM_COLUMNS='["Company Name", "Market Cap", "Current Price", "Stock P/E", "Revenue", "Profit"]'

SMART_MAP_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/extract/smart-map-to-template" \
    -H "Content-Type: application/json" \
    -d "{
        \"url\": \"$TEST_URL\",
        \"template_columns\": $CUSTOM_COLUMNS,
        \"llm_provider\": \"openai\",
        \"output_format\": \"json\",
        \"session_id\": \"diagnostic-test\"
    }")

echo "Response:"
echo "$SMART_MAP_RESPONSE" | jq '.' || echo "$SMART_MAP_RESPONSE"
echo ""

# Check if mapping was successful
if echo "$SMART_MAP_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
    print_status "success" "Smart mapping successful!"

    # Display mapped data
    echo ""
    echo "📊 Mapped Data:"
    echo "$SMART_MAP_RESPONSE" | jq -r '.data[0]'

    # Count missing vs found fields
    MAPPED_DATA=$(echo "$SMART_MAP_RESPONSE" | jq -r '.data[0]')
    TOTAL_FIELDS=$(echo "$MAPPED_DATA" | jq 'length')
    MISSING_FIELDS=$(echo "$MAPPED_DATA" | jq '[.[] | select(. == "—" or . == "" or . == null)] | length')
    FOUND_FIELDS=$((TOTAL_FIELDS - MISSING_FIELDS))

    echo ""
    print_status "info" "Total fields: $TOTAL_FIELDS"
    print_status "success" "Found fields: $FOUND_FIELDS"
    if [ $MISSING_FIELDS -gt 0 ]; then
        print_status "warning" "Missing fields: $MISSING_FIELDS"
    fi

else
    print_status "error" "Smart mapping failed"
    ERROR_MSG=$(echo "$SMART_MAP_RESPONSE" | jq -r '.error // .detail // "Unknown error"')
    echo "Error: $ERROR_MSG"
fi
echo ""

# Check Ollama for local LLM
echo "═══════════════════════════════════════════════════════════════════"
echo "5️⃣  Checking Ollama (Local LLM) Status"
echo "═══════════════════════════════════════════════════════════════════"

OLLAMA_ENDPOINT="${OLLAMA_ENDPOINT:-http://localhost:11434}"

if curl -s -f "$OLLAMA_ENDPOINT/api/tags" > /dev/null 2>&1; then
    print_status "success" "Ollama is running at $OLLAMA_ENDPOINT"

    # List available models
    OLLAMA_MODELS=$(curl -s "$OLLAMA_ENDPOINT/api/tags" | jq -r '.models[].name')

    if [ -n "$OLLAMA_MODELS" ]; then
        echo ""
        print_status "info" "Available Ollama models:"
        echo "$OLLAMA_MODELS" | while read model; do
            echo "   - $model"
        done
    else
        print_status "warning" "No Ollama models found"
        echo "   💡 Pull a model with: docker exec ollama ollama pull llama3.2:3b"
    fi
else
    print_status "warning" "Ollama is not running"
    echo ""
    echo "💡 Start Ollama with: docker-compose up -d ollama"
    echo "💡 Pull a model: docker exec ollama ollama pull llama3.2:3b"
fi
echo ""

# View backend logs
echo "═══════════════════════════════════════════════════════════════════"
echo "6️⃣  Backend Logs (last 50 lines)"
echo "═══════════════════════════════════════════════════════════════════"

if command -v docker &> /dev/null; then
    # Find backend container
    BACKEND_CONTAINER=$(docker ps --filter "name=backend" --format "{{.Names}}" | head -n 1)

    if [ -n "$BACKEND_CONTAINER" ]; then
        print_status "info" "Showing logs from container: $BACKEND_CONTAINER"
        echo ""
        docker logs "$BACKEND_CONTAINER" --tail 50
    else
        print_status "warning" "Backend container not found"
    fi
else
    print_status "warning" "Docker not available - cannot show logs"
fi
echo ""

# Summary
echo "═══════════════════════════════════════════════════════════════════"
echo "✅ Diagnostic Complete"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "📋 Summary:"
echo "   - Backend status: Checked"
echo "   - Preset templates: Tested"
echo "   - Smart mapping: Tested"
echo "   - Ollama status: Checked"
echo "   - Logs: Displayed"
echo ""
echo "💡 Debugging Tips:"
echo "   - Check backend logs for detailed extraction pipeline info"
echo "   - Look for emoji-prefixed log lines (🔍, 📊, ✅, ❌, etc.)"
echo "   - Preset extraction uses CSS selectors (can fail if page structure changes)"
echo "   - Smart mapping uses LLM (requires OpenAI key or Ollama running)"
echo "   - All extraction steps now have comprehensive debug logging"
echo ""
echo "📖 For more info, see:"
echo "   - docs/guides/TEMPLATE_EXTRACTION_GUIDE.md"
echo "   - docs/guides/SMART_TEMPLATE_MAPPING_GUIDE.md"
echo "   - docs/setup/LOCAL_LLM_SETUP.md"
echo ""
