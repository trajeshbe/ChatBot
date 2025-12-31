#!/bin/bash
# PDF Extraction with Docling Integration Test
# Tests Docling library integration for PDF document processing

set -e

echo "════════════════════════════════════════════════════════════════"
echo "PDF Extraction - Docling Integration Test"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================================================
# Test 1: Docling Library Import and Initialization
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 1: Docling Library Import and Initialization"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

docker-compose exec -T backend python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, '/app')

print("1️⃣  Testing Docling import...")
try:
    from docling.document_converter import DocumentConverter
    print("✅ Docling imported successfully!")
except ImportError as e:
    print(f"❌ Docling import failed: {e}")
    sys.exit(1)

print("\n2️⃣  Initializing DocumentConverter...")
try:
    converter = DocumentConverter()
    print("✅ DocumentConverter initialized successfully!")
except Exception as e:
    print(f"❌ DocumentConverter initialization failed: {e}")
    sys.exit(1)

print("\n✅ TEST 1 PASSED - Docling is properly installed and configured")
PYTHON_SCRIPT

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ TEST 1 PASSED${NC}"
else
    echo ""
    echo -e "${RED}❌ TEST 1 FAILED${NC}"
    exit 1
fi
echo ""

# ============================================================================
# Test 2: PDF Extraction with Docling
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 2: PDF Extraction with Docling"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "PDF URL: https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
echo ""

docker-compose exec -T backend python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, '/app')
import requests
import tempfile
import os
from docling.document_converter import DocumentConverter

pdf_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
print(f"📥 Downloading: {pdf_url}")

try:
    response = requests.get(pdf_url, timeout=10)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name

    print(f"✅ Downloaded ({len(response.content)} bytes)")
    print(f"\n🔄 Converting with Docling...")

    converter = DocumentConverter()
    result = converter.convert(tmp_path)
    markdown_text = result.document.export_to_markdown()

    print(f"✅ Extraction successful!")
    print(f"📊 Extracted {len(markdown_text)} characters")
    print(f"\n📄 Content preview (first 200 chars):")
    print("-" * 80)
    print(markdown_text[:200])
    print("-" * 80)

    os.unlink(tmp_path)

    print("\n✅ TEST 2 PASSED - PDF extraction working correctly")

except Exception as e:
    print(f"\n❌ TEST 2 FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ TEST 2 PASSED${NC}"
else
    echo ""
    echo -e "${RED}❌ TEST 2 FAILED${NC}"
    exit 1
fi
echo ""

# ============================================================================
# Test 3: PDF Extraction via API (Ultra-Smart Extraction)
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 3: PDF Extraction via API (Ultra-Smart Extraction)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Testing: /api/v1/extract/ultra-smart with PDF URL"
echo "PDF: https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
echo ""

curl -s -X POST http://localhost:8000/api/v1/extract/ultra-smart \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
    "user_instructions": "Extract all text content from this PDF document",
    "source_type": "url",
    "llm_provider": "openai"
  }' > /tmp/pdf_api_test.json

if jq -e '.success' /tmp/pdf_api_test.json > /dev/null 2>&1; then
    echo -e "${GREEN}✅ TEST 3 PASSED${NC}"
    echo ""
    echo "📊 API Response:"
    echo "  Success: $(jq -r '.success' /tmp/pdf_api_test.json)"
    echo "  Rows extracted: $(jq -r '.row_count' /tmp/pdf_api_test.json)"
    echo "  Extraction method: $(jq -r '.extraction_metadata.extraction_method' /tmp/pdf_api_test.json)"
    echo ""
    echo "📄 Extracted content (first row):"
    jq -r '.table[0]' /tmp/pdf_api_test.json | head -10
else
    echo -e "${RED}❌ TEST 3 FAILED${NC}"
    echo ""
    echo "Error response:"
    jq '.' /tmp/pdf_api_test.json
    exit 1
fi
echo ""

# ============================================================================
# Test Summary
# ============================================================================
echo "════════════════════════════════════════════════════════════════"
echo "Test Summary"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}ALL 3 TESTS PASSED!${NC}"
echo ""
echo "✅ Docling library installed and working"
echo "✅ Direct PDF extraction functional"
echo "✅ API-based PDF extraction operational"
echo ""
echo "🎉 PDF extraction with Docling is fully operational!"
