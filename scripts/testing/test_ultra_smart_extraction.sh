#!/bin/bash
# Ultra-Smart Extraction Testing Suite
# Tests the AI-powered web scraping with various scenarios

set -e

echo "════════════════════════════════════════════════════════════════"
echo "Ultra-Smart Extraction Testing Suite"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0

# ============================================================================
# Test 1: Mystery Books Category Page
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 1: Mystery Books Category Page Extraction"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "URL: https://books.toscrape.com/catalogue/category/books/mystery_3/index.html"
echo "Instructions: Extract all mystery books with title, price, and availability"
echo ""

curl -s -X POST http://localhost:8000/api/v1/extract/ultra-smart \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://books.toscrape.com/catalogue/category/books/mystery_3/index.html",
    "user_instructions": "Extract all mystery books with title, price, and availability",
    "source_type": "url",
    "llm_provider": "openai"
  }' > /tmp/test_mystery_books.json

if jq -e '.success' /tmp/test_mystery_books.json > /dev/null 2>&1; then
    BOOKS_COUNT=$(jq -r '.table | length' /tmp/test_mystery_books.json)
    echo -e "${GREEN}✅ TEST 1 PASSED${NC}"
    echo ""
    echo "📊 Results:"
    echo "  Books extracted: $BOOKS_COUNT"
    echo "  Columns: $(jq -r '.columns | join(", ")' /tmp/test_mystery_books.json)"
    echo "  Extraction method: $(jq -r '.extraction_metadata.extraction_method' /tmp/test_mystery_books.json)"
    echo ""
    echo "📚 First 3 books:"
    jq -r '.table[0:3] | .[] | "  - \(.title // .Title) | \(.price // .Price) | \(.availability // .Availability // "N/A")"' /tmp/test_mystery_books.json
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ TEST 1 FAILED${NC}"
    ((TESTS_FAILED++))
fi
echo ""

# ============================================================================
# Test 2: Sharp Objects Product Page
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 2: Sharp Objects Product Page Extraction"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "URL: https://books.toscrape.com/catalogue/sharp-objects_997/index.html"
echo "Instructions: Extract book title, price, availability, and description"
echo ""

curl -s -X POST http://localhost:8000/api/v1/extract/ultra-smart \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://books.toscrape.com/catalogue/sharp-objects_997/index.html",
    "user_instructions": "Extract the book title, price, availability, product description, and category",
    "source_type": "url",
    "llm_provider": "openai"
  }' > /tmp/test_sharp_objects.json

if jq -e '.success' /tmp/test_sharp_objects.json > /dev/null 2>&1; then
    echo -e "${GREEN}✅ TEST 2 PASSED${NC}"
    echo ""
    echo "📊 Extracted data:"
    jq -r '.table[0] | to_entries | .[] | "  \(.key): \(.value)"' /tmp/test_sharp_objects.json
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ TEST 2 FAILED${NC}"
    ((TESTS_FAILED++))
fi
echo ""

# ============================================================================
# Test 3: AI-Powered Navigation - Fantasy Books
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 3: AI-Powered Navigation - Fantasy Books"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "URL: https://books.toscrape.com/"
echo "Instructions: get all books under Fantasy (AI navigation required)"
echo ""
echo -e "${YELLOW}⏳ This test requires AI to navigate from homepage to Fantasy category...${NC}"
echo ""

curl -s -X POST http://localhost:8000/api/v1/extract/ultra-smart \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://books.toscrape.com/",
    "user_instructions": "get all books under Fantasy",
    "llm_provider": "openai",
    "model_id": "gpt-4-turbo"
  }' > /tmp/test_fantasy_navigation.json

if jq -e '.success' /tmp/test_fantasy_navigation.json > /dev/null 2>&1; then
    BOOKS_COUNT=$(jq -r '.table | length' /tmp/test_fantasy_navigation.json)
    echo -e "${GREEN}✅ TEST 3 PASSED${NC} - AI Navigation worked!"
    echo ""
    echo "📊 Results:"
    echo "  Books found: $BOOKS_COUNT"
    echo "  Extraction method: $(jq -r '.extraction_metadata.extraction_method' /tmp/test_fantasy_navigation.json)"

    if jq -e '.extraction_metadata.metadata.navigation_path' /tmp/test_fantasy_navigation.json > /dev/null 2>&1; then
        echo ""
        echo "🧭 Navigation path:"
        jq -r '.extraction_metadata.metadata.navigation_path | .[] | "    → \(.)"' /tmp/test_fantasy_navigation.json
        echo ""
        echo "  Steps taken: $(jq -r '.extraction_metadata.metadata.steps_taken' /tmp/test_fantasy_navigation.json)"
    fi

    echo ""
    echo "📚 First 3 Fantasy books:"
    jq -r '.table[0:3] | .[] | "  - \(.title // .Title // "No title") | \(.price // .Price // "No price")"' /tmp/test_fantasy_navigation.json
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ TEST 3 FAILED${NC}"
    ((TESTS_FAILED++))
fi
echo ""

# ============================================================================
# Test 4: AI-Powered Navigation - Mystery Books
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 4: AI-Powered Navigation - Mystery Books"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "URL: https://books.toscrape.com/"
echo "Instructions: get all mystery books (AI navigation required)"
echo ""
echo -e "${YELLOW}⏳ This test requires AI to navigate from homepage to Mystery category...${NC}"
echo ""

curl -s -X POST http://localhost:8000/api/v1/extract/ultra-smart \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://books.toscrape.com/",
    "user_instructions": "get all mystery books",
    "source_type": "url",
    "llm_provider": "openai",
    "model_id": "gpt-4-turbo"
  }' > /tmp/test_mystery_navigation.json

if jq -e '.success' /tmp/test_mystery_navigation.json > /dev/null 2>&1; then
    BOOKS_COUNT=$(jq -r '.row_count' /tmp/test_mystery_navigation.json)
    echo -e "${GREEN}✅ TEST 4 PASSED${NC} - AI Navigation worked!"
    echo ""
    echo "📊 Results:"
    echo "  Books found: $BOOKS_COUNT"
    echo "  Extraction method: $(jq -r '.extraction_metadata.extraction_method' /tmp/test_mystery_navigation.json)"

    if jq -e '.extraction_metadata.metadata.navigation_path' /tmp/test_mystery_navigation.json > /dev/null 2>&1; then
        echo ""
        echo "🧭 Navigation path:"
        jq -r '.extraction_metadata.metadata.navigation_path | .[] | "    → \(.)"' /tmp/test_mystery_navigation.json
        echo ""
        echo "  Steps taken: $(jq -r '.extraction_metadata.metadata.steps_taken' /tmp/test_mystery_navigation.json)"
    fi

    echo ""
    echo "📚 First 5 Mystery books:"
    jq -r '.table[0:5] | .[] | "  - \(.title // .Title // "No title") | \(.price // .Price // "No price")"' /tmp/test_mystery_navigation.json
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ TEST 4 FAILED${NC}"
    ((TESTS_FAILED++))
fi
echo ""

# ============================================================================
# Test Summary
# ============================================================================
echo "════════════════════════════════════════════════════════════════"
echo "Test Summary"
echo "════════════════════════════════════════════════════════════════"
echo ""
TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo ""
    echo "✅ Direct page extraction working"
    echo "✅ Product page extraction working"
    echo "✅ AI-powered navigation working"
    exit 0
else
    echo -e "${RED}⚠️  SOME TESTS FAILED${NC}"
    exit 1
fi
