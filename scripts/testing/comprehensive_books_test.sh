#!/bin/bash

#============================================================================
# Comprehensive Books to Scrape Testing Script
# Tests ALL features on a real website with diverse scenarios
#============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║  Comprehensive Feature Test - Books to Scrape                      ║"
echo "║  Testing: All extraction methods + OCR + Translation + RAG          ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Check backend is running
echo "Checking backend status..."
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${RED}❌ Backend not running! Start with: docker-compose up -d backend${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Backend is running${NC}"
echo ""

#============================================================================
# TEST 1: Smart Extraction - Mystery Books
#============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}TEST 1: Smart Extraction - Mystery Books Category${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Extracting all mystery books from category page..."
echo ""

curl -s -X POST http://localhost:8000/api/v1/extract/ultra-smart \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://books.toscrape.com/catalogue/category/books/mystery_3/index.html",
    "user_instructions": "Extract all books with title, price, availability, and rating",
    "source_type": "url",
    "llm_provider": "openai"
  }' > /tmp/test1_mystery_books.json

if jq -e '.success' /tmp/test1_mystery_books.json > /dev/null 2>&1; then
    BOOK_COUNT=$(jq '.table | length' /tmp/test1_mystery_books.json)
    echo -e "${GREEN}✅ TEST 1 PASSED${NC}"
    echo "   Books extracted: $BOOK_COUNT"
    echo "   Columns: $(jq -r '.columns | join(", ")' /tmp/test1_mystery_books.json)"
    echo ""
    echo "   First 3 mystery books:"
    jq -r '.table[0:3] | .[] | "   📚 \(.title // .Title) - \(.price // .Price)"' /tmp/test1_mystery_books.json
else
    echo -e "${RED}❌ TEST 1 FAILED${NC}"
    jq '.' /tmp/test1_mystery_books.json
    exit 1
fi

echo ""

#============================================================================
# TEST 2: AI Navigation - Fantasy Category
#============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}TEST 2: AI Navigation - Fantasy Books${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Starting from homepage, navigating to Fantasy category..."
echo ""

curl -s -X POST http://localhost:8000/api/v1/extract/ultra-smart \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://books.toscrape.com/",
    "user_instructions": "get all fantasy books",
    "source_type": "url",
    "llm_provider": "openai",
    "model_id": "gpt-4-turbo"
  }' > /tmp/test2_fantasy_navigation.json

if jq -e '.success' /tmp/test2_fantasy_navigation.json > /dev/null 2>&1; then
    FANTASY_COUNT=$(jq '.table | length' /tmp/test2_fantasy_navigation.json)
    echo -e "${GREEN}✅ TEST 2 PASSED${NC}"
    echo "   Fantasy books found: $FANTASY_COUNT"

    # Check if navigation metadata exists
    if jq -e '.extraction_metadata.metadata.navigation_path' /tmp/test2_fantasy_navigation.json > /dev/null 2>&1; then
        echo "   Navigation path:"
        jq -r '.extraction_metadata.metadata.navigation_path | .[] | "     → \(.)"' /tmp/test2_fantasy_navigation.json
    fi

    echo ""
    echo "   First 3 Fantasy books:"
    jq -r '.table[0:3] | .[] | "   📚 \(.title // .Title) - \(.price // .Price)"' /tmp/test2_fantasy_navigation.json
else
    echo -e "${RED}❌ TEST 2 FAILED${NC}"
    jq '.' /tmp/test2_fantasy_navigation.json
    exit 1
fi

echo ""

#============================================================================
# TEST 3: Template Mapping - Single Product
#============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}TEST 3: Template Mapping - Sharp Objects Product Page${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Mapping product page to custom template columns..."
echo ""

curl -s -X POST http://localhost:8000/api/v1/extract/smart-map-to-template \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://books.toscrape.com/catalogue/sharp-objects_997/index.html",
    "template_columns": ["Book Title", "Price (GBP)", "Stock Status", "Rating", "UPC", "Product Type"],
    "llm_provider": "openai"
  }' > /tmp/test3_template_mapping.json

if jq -e '.success' /tmp/test3_template_mapping.json > /dev/null 2>&1; then
    echo -e "${GREEN}✅ TEST 3 PASSED${NC}"
    echo "   Mapped fields:"
    jq -r '.mapped_data | to_entries[] | "   \(.key): \(.value)"' /tmp/test3_template_mapping.json

    MISSING=$(jq -r '.missing_fields | length' /tmp/test3_template_mapping.json)
    if [ "$MISSING" -gt 0 ]; then
        echo ""
        echo -e "   ${YELLOW}Missing fields (marked with —):${NC}"
        jq -r '.missing_fields[] | "   - \(.)"' /tmp/test3_template_mapping.json
    fi
else
    echo -e "${RED}❌ TEST 3 FAILED${NC}"
    jq '.' /tmp/test3_template_mapping.json
    exit 1
fi

echo ""

#============================================================================
# TEST 4: CSS Extraction - Direct Selectors
#============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}TEST 4: CSS Extraction - Using Selectors${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Extracting specific fields with CSS selectors..."
echo ""

curl -s -X POST http://localhost:8000/api/v1/extract/css \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://books.toscrape.com/catalogue/sharp-objects_997/index.html",
    "selectors": {
      "title": "h1",
      "price": ".price_color",
      "availability": ".availability",
      "rating": ".star-rating::attr(class)"
    }
  }' > /tmp/test4_css_extraction.json

if jq -e '.success' /tmp/test4_css_extraction.json > /dev/null 2>&1; then
    echo -e "${GREEN}✅ TEST 4 PASSED${NC}"
    echo "   Extracted data:"
    jq -r '.data | to_entries[] | "   \(.key): \(.value)"' /tmp/test4_css_extraction.json
else
    echo -e "${RED}❌ TEST 4 FAILED${NC}"
    jq '.' /tmp/test4_css_extraction.json
    exit 1
fi

echo ""

#============================================================================
# TEST 5: OCR - PDF Extraction
#============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}TEST 5: OCR - PDF Text Extraction${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Testing OCR on sample PDF..."
echo ""

docker-compose exec -T backend python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, '/app')
import asyncio
from app.services.ocr_service import OCRService
import requests
import tempfile
import os

async def test_ocr():
    ocr_service = OCRService()

    # Download test PDF
    pdf_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    response = requests.get(pdf_url, timeout=10)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name

    # Extract text
    result = await ocr_service.extract_text(tmp_path, method="auto")

    print(f"METHOD:{result['method_used']}")
    print(f"CONFIDENCE:{result['confidence']:.2f}")
    print(f"CHARS:{len(result['text'])}")
    print(f"PREVIEW:{result['text'][:100]}")

    # Cleanup
    os.unlink(tmp_path)

    return True

try:
    asyncio.run(test_ocr())
except Exception as e:
    print(f"ERROR:{e}")
    sys.exit(1)
PYTHON_SCRIPT

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ TEST 5 PASSED - OCR Working${NC}"
else
    echo -e "${RED}❌ TEST 5 FAILED - OCR Error${NC}"
    exit 1
fi

echo ""

#============================================================================
# TEST 6: Translation - EN to ES
#============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}TEST 6: Translation - English to Spanish${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Testing translation service..."
echo ""

docker-compose exec -T backend python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, '/app')
import asyncio
from app.services.translation_service import TranslationService
from app.services.llm_service import llm_service

async def test_translation():
    translator = TranslationService(llm_service=llm_service)

    result = await translator.translate(
        text="Sharp Objects is a gripping psychological thriller about a troubled journalist.",
        source_lang="en",
        target_lang="es",
        quality="high"
    )

    print(f"ORIGINAL:Sharp Objects is a gripping psychological thriller...")
    print(f"TRANSLATED:{result['translated_text']}")
    print(f"BACKEND:{result['backend_used']}")
    print(f"CONFIDENCE:{result['confidence']:.2f}")

    return True

try:
    asyncio.run(test_translation())
except Exception as e:
    print(f"ERROR:{e}")
    sys.exit(1)
PYTHON_SCRIPT

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ TEST 6 PASSED - Translation Working${NC}"
else
    echo -e "${RED}❌ TEST 6 FAILED - Translation Error${NC}"
    exit 1
fi

echo ""

#============================================================================
# TEST 7: RAG Chat - Query Extracted Data
#============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}TEST 7: RAG Chat - Query Book Data${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Uploading extracted books and querying..."
echo ""

# Save mystery books to file
jq '.table' /tmp/test1_mystery_books.json > /tmp/mystery_books_data.json

# Upload to RAG
curl -s -X POST http://localhost:8000/api/v1/upload \
  -F "file=@/tmp/mystery_books_data.json" \
  -F "session_id=comprehensive_test_session" > /tmp/test7_upload.json

if jq -e '.document_id' /tmp/test7_upload.json > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Document uploaded${NC}"

    # Wait for processing
    sleep 3

    # Query the data
    curl -s -X POST http://localhost:8000/api/v1/query \
      -H "Content-Type: application/json" \
      -d '{
        "query": "How many mystery books are there and what is the price range?",
        "session_id": "comprehensive_test_session",
        "model_id": "gpt-4-turbo"
      }' > /tmp/test7_rag_query.json

    if jq -e '.answer' /tmp/test7_rag_query.json > /dev/null 2>&1; then
        echo -e "${GREEN}✅ TEST 7 PASSED - RAG Chat Working${NC}"
        echo "   Answer:"
        jq -r '.answer' /tmp/test7_rag_query.json | fold -w 70 -s | sed 's/^/   /'
        echo ""
        echo "   Sources used: $(jq '.sources | length' /tmp/test7_rag_query.json)"
    else
        echo -e "${RED}❌ TEST 7 FAILED - Query Error${NC}"
        jq '.' /tmp/test7_rag_query.json
        exit 1
    fi
else
    echo -e "${RED}❌ TEST 7 FAILED - Upload Error${NC}"
    jq '.' /tmp/test7_upload.json
    exit 1
fi

echo ""

#============================================================================
# SUMMARY
#============================================================================

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                        TEST SUMMARY                                  ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}✅ All 7 Tests Passed!${NC}"
echo ""
echo "Tests Completed:"
echo "  ✅ Smart Extraction (Mystery books)"
echo "  ✅ AI Navigation (Fantasy category)"
echo "  ✅ Template Mapping (Custom fields)"
echo "  ✅ CSS Extraction (Direct selectors)"
echo "  ✅ OCR (PDF text extraction)"
echo "  ✅ Translation (EN → ES)"
echo "  ✅ RAG Chat (Query uploaded data)"
echo ""
echo "Test Results Saved:"
echo "  📁 /tmp/test1_mystery_books.json"
echo "  📁 /tmp/test2_fantasy_navigation.json"
echo "  📁 /tmp/test3_template_mapping.json"
echo "  📁 /tmp/test4_css_extraction.json"
echo "  📁 /tmp/test7_rag_query.json"
echo ""
echo "Website Tested:"
echo "  🌐 Books to Scrape (https://books.toscrape.com)"
echo ""
echo -e "${GREEN}🎉 Comprehensive Feature Test Complete!${NC}"
echo ""
