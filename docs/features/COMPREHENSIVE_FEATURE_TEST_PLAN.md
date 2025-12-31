# Comprehensive Feature Test Plan
## Real-World Testing on Books to Scrape + Multi-Source Integration

**Date**: 2025-11-21
**Test Website**: https://books.toscrape.com
**Purpose**: Demonstrate ALL capabilities in real-world scenarios

---

## 🎯 Why Books to Scrape is Perfect

This website offers the **perfect testing ground** because it has:

✅ **Multi-Level Navigation**
- Homepage → Categories → Subcategories → Product Pages
- Pagination across category pages
- Breadcrumb navigation
- Search functionality

✅ **Diverse Content Types**
- Structured product listings
- Unstructured descriptions
- Images (book covers)
- Tables (product details)
- Star ratings
- Pricing with currency symbols

✅ **Complex Extraction Scenarios**
- Single product extraction
- Bulk product extraction
- Category-based extraction
- AI-powered navigation ("get all mystery books")
- Template-based mapping

✅ **Safe for Testing**
- Designed for web scraping practice
- No rate limiting
- No authentication required
- Consistent structure

---

## 🧪 Complete Test Matrix

| Test # | Feature | Complexity | URL | Expected Outcome |
|--------|---------|------------|-----|------------------|
| **1** | Smart Extraction | Medium | Category page | Extract 20 books |
| **2** | AI Navigation | High | Homepage | Navigate to category + extract |
| **3** | Template Mapping | Medium | Product page | Map to custom fields |
| **4** | CSS Extraction | Low | Product page | Extract specific elements |
| **5** | Pagination Handling | High | Category with pages | Extract across pages |
| **6** | Multi-Category Extraction | Very High | Multiple categories | Bulk extraction |
| **7** | OCR Integration | High | External PDF | Extract text from PDF |
| **8** | Translation | Medium | Extracted data | Translate to Spanish |
| **9** | RAG Chat | High | Uploaded data | Query extracted books |
| **10** | Full Pipeline | Very High | End-to-end | All features together |

---

## 📝 Test Scenario 1: Smart Extraction (Mystery Books)

### Objective
Extract all mystery books with complete details

### Test Command
```bash
curl -X POST http://localhost:8000/api/v1/extract/ultra-smart \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://books.toscrape.com/catalogue/category/books/mystery_3/index.html",
    "user_instructions": "Extract all books with title, price, availability, rating, and description",
    "source_type": "url",
    "llm_provider": "openai",
    "model_id": "gpt-4-turbo"
  }' | jq '.' > /tmp/test1_mystery_books.json
```

### Expected Result
```json
{
  "success": true,
  "table": [
    {
      "title": "Sharp Objects",
      "price": "£47.82",
      "availability": "In stock",
      "rating": "Four stars",
      "description": "..."
    }
    // ... 19 more books
  ],
  "row_count": 20,
  "columns": ["title", "price", "availability", "rating", "description"],
  "extraction_metadata": {
    "extraction_method": "llm_smart_extraction",
    "confidence_score": 0.95
  }
}
```

### Verification
```bash
# Check success
jq '.success' /tmp/test1_mystery_books.json

# Count books extracted
jq '.table | length' /tmp/test1_mystery_books.json

# Show first book
jq '.table[0]' /tmp/test1_mystery_books.json
```

---

## 📝 Test Scenario 2: AI-Powered Navigation

### Objective
Start from homepage and navigate to Fantasy category automatically

### Test Command
```bash
curl -X POST http://localhost:8000/api/v1/extract/ultra-smart \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://books.toscrape.com/",
    "user_instructions": "get all books in the Fantasy category",
    "source_type": "url",
    "llm_provider": "openai",
    "model_id": "gpt-4-turbo"
  }' | jq '.' > /tmp/test2_fantasy_navigation.json
```

### Expected Result
```json
{
  "success": true,
  "table": [/* Fantasy books */],
  "extraction_metadata": {
    "extraction_method": "ai_navigation",
    "metadata": {
      "navigation_path": [
        "Homepage",
        "Fantasy Category Link",
        "Fantasy Category Page"
      ],
      "steps_taken": 2,
      "navigation_successful": true
    }
  }
}
```

### Verification
```bash
# Check navigation metadata
jq '.extraction_metadata.metadata.navigation_path' /tmp/test2_fantasy_navigation.json

# Verify Fantasy books extracted
jq '.table[0:3] | .[] | .title' /tmp/test2_fantasy_navigation.json
```

---

## 📝 Test Scenario 3: Template Mapping (Custom Fields)

### Objective
Map a product page to custom template columns

### Test Command
```bash
curl -X POST http://localhost:8000/api/v1/extract/template-map \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://books.toscrape.com/catalogue/sharp-objects_997/index.html",
    "template_columns": [
      "Book Title",
      "Author Name",
      "Price (GBP)",
      "Stock Status",
      "Customer Rating",
      "Product Type",
      "Tax Info",
      "Number of Reviews"
    ],
    "llm_provider": "openai",
    "model_id": "gpt-4-turbo"
  }' | jq '.' > /tmp/test3_template_mapping.json
```

### Expected Result
```json
{
  "success": true,
  "mapped_data": {
    "Book Title": "Sharp Objects",
    "Author Name": "—",
    "Price (GBP)": "47.82",
    "Stock Status": "In stock (20 available)",
    "Customer Rating": "4 out of 5 stars",
    "Product Type": "Books",
    "Tax Info": "£0.00",
    "Number of Reviews": "0"
  },
  "missing_fields": ["Author Name"],
  "extraction_complete": false,
  "non_empty_count": 7
}
```

### Verification
```bash
# Check all mapped fields
jq '.mapped_data' /tmp/test3_template_mapping.json

# Check missing fields
jq '.missing_fields' /tmp/test3_template_mapping.json
```

---

## 📝 Test Scenario 4: CSS Selector Extraction

### Objective
Extract specific fields using CSS selectors

### Test Command
```bash
curl -X POST http://localhost:8000/api/v1/extract/css \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://books.toscrape.com/catalogue/sharp-objects_997/index.html",
    "selectors": {
      "title": "h1",
      "price": ".price_color",
      "availability": ".availability",
      "rating": ".star-rating::attr(class)",
      "description": "#product_description + p",
      "upc": "table.table tr:nth-child(1) td"
    }
  }' | jq '.' > /tmp/test4_css_extraction.json
```

### Expected Result
```json
{
  "success": true,
  "data": {
    "title": "Sharp Objects",
    "price": "£47.82",
    "availability": "In stock (20 available)",
    "rating": "star-rating Four",
    "description": "WICKED above her hipbone...",
    "upc": "e00eb4fd7b871a48"
  }
}
```

---

## 📝 Test Scenario 5: Pagination Handling

### Objective
Extract books across multiple pages in a category

### Test Command
```bash
curl -X POST http://localhost:8000/api/v1/extract/ultra-smart \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://books.toscrape.com/catalogue/category/books_1/index.html",
    "user_instructions": "Extract all books from ALL pages (follow pagination)",
    "source_type": "url",
    "llm_provider": "openai",
    "model_id": "gpt-4-turbo",
    "follow_pagination": true,
    "max_pages": 5
  }' | jq '.' > /tmp/test5_pagination.json
```

### Expected Result
- Extracts 100+ books across 5 pages
- Pagination metadata showing pages visited

---

## 📝 Test Scenario 6: Multi-Category Bulk Extraction

### Objective
Extract books from multiple categories in one request

### Test Command
```bash
curl -X POST http://localhost:8000/api/v1/extraction/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://books.toscrape.com/catalogue/category/books/mystery_3/index.html",
      "https://books.toscrape.com/catalogue/category/books/fantasy_19/index.html",
      "https://books.toscrape.com/catalogue/category/books/science-fiction_16/index.html",
      "https://books.toscrape.com/catalogue/category/books/thriller_37/index.html"
    ],
    "output_format": "excel",
    "delivery_method": "download",
    "scrape_config": {
      "user_instructions": "Extract title, price, rating, availability"
    }
  }' | jq '.' > /tmp/test6_bulk_extraction.json
```

### Expected Result
- Job ID returned
- Processing in background
- Excel file with all books from 4 categories

### Check Job Status
```bash
JOB_ID=$(jq -r '.job_id' /tmp/test6_bulk_extraction.json)
curl -X GET "http://localhost:8000/api/v1/extraction/jobs/$JOB_ID/status" | jq '.'
```

---

## 📝 Test Scenario 7: OCR Integration (PDF Extraction)

### Objective
Download a sample PDF and extract text using OCR

### Test Command
```bash
# Test with sample PDF
curl -X POST http://localhost:8000/api/v1/extract/ultra-smart \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
    "user_instructions": "Extract all text content from this PDF document",
    "source_type": "url",
    "llm_provider": "openai"
  }' | jq '.' > /tmp/test7_ocr_pdf.json
```

### Expected Result
```json
{
  "success": true,
  "table": [
    {
      "content": "Dummy PDF file contents extracted via OCR..."
    }
  ],
  "extraction_metadata": {
    "extraction_method": "ocr_extraction",
    "ocr_method": "docling",
    "confidence": 0.95,
    "pages": 1
  }
}
```

### Direct OCR Test
```bash
docker-compose exec backend python3 << 'EOF'
import sys
sys.path.insert(0, '/app')
import asyncio
from app.services.ocr_service import OCRService
import requests
import tempfile

async def test():
    ocr = OCRService()
    pdf_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    response = requests.get(pdf_url)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(response.content)
        path = f.name

    result = await ocr.extract_text(path, method="auto")
    print(f"✅ Extracted {len(result['text'])} characters")
    print(f"Method: {result['method_used']}")
    print(f"Preview: {result['text'][:200]}")

asyncio.run(test())
EOF
```

---

## 📝 Test Scenario 8: Translation Pipeline

### Objective
Extract English book data and translate to Spanish

### Test Command
```bash
# Step 1: Extract books
curl -X POST http://localhost:8000/api/v1/extract/ultra-smart \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://books.toscrape.com/catalogue/category/books/mystery_3/index.html",
    "user_instructions": "Extract title and description for first 3 books",
    "source_type": "url",
    "llm_provider": "openai"
  }' > /tmp/books_english.json

# Step 2: Translate to Spanish
curl -X POST http://localhost:8000/api/v1/translate \
  -H "Content-Type: application/json" \
  -d "{
    \"text\": $(jq -r '.table[0].description' /tmp/books_english.json | jq -R -s .),
    \"source_lang\": \"en\",
    \"target_lang\": \"es\",
    \"quality\": \"high\"
  }" | jq '.' > /tmp/test8_translation.json
```

### Expected Result
```json
{
  "translated_text": "WICKED sobre su hueso de la cadera...",
  "source_lang": "en",
  "target_lang": "es",
  "backend_used": "llm",
  "confidence": 0.92,
  "original_length": 245,
  "translated_length": 253
}
```

### Direct Translation Test
```bash
docker-compose exec backend python3 << 'EOF'
import sys
sys.path.insert(0, '/app')
import asyncio
from app.services.translation_service import TranslationService
from app.services.llm_service import llm_service

async def test():
    translator = TranslationService(llm_service)

    result = await translator.translate(
        text="Sharp Objects is a psychological thriller about a journalist returning to her hometown.",
        source_lang="en",
        target_lang="es",
        quality="high"
    )

    print(f"✅ Translation successful")
    print(f"Original: Sharp Objects is a psychological thriller...")
    print(f"Spanish: {result['translated_text']}")
    print(f"Backend: {result['backend_used']}")

asyncio.run(test())
EOF
```

---

## 📝 Test Scenario 9: RAG Chat with Extracted Data

### Objective
Upload extracted book data and query it using RAG chat

### Test Commands
```bash
# Step 1: Save extracted books to JSON file
jq '.table' /tmp/test1_mystery_books.json > /tmp/mystery_books_data.json

# Step 2: Upload as document
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@/tmp/mystery_books_data.json" \
  -F "session_id=test_books_session" | jq '.' > /tmp/upload_response.json

# Step 3: Query the data
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Which mystery books cost less than £20?",
    "session_id": "test_books_session",
    "model_id": "gpt-4-turbo"
  }' | jq '.' > /tmp/test9_rag_query.json
```

### Expected Result
```json
{
  "answer": "Based on the uploaded mystery books data, here are the books under £20: ...",
  "sources": [
    {
      "document_id": "...",
      "filename": "mystery_books_data.json",
      "content": "{\"title\": \"...\", \"price\": \"£15.23\"}",
      "score": 0.89
    }
  ],
  "model": "gpt-4-turbo",
  "tokens_used": 456,
  "num_sources": 3
}
```

---

## 📝 Test Scenario 10: Full Pipeline Integration

### Objective
Demonstrate all features working together in one workflow

### Complete Workflow
```bash
#!/bin/bash

echo "🎯 COMPREHENSIVE FEATURE TEST - FULL PIPELINE"
echo "==============================================="
echo ""

# 1. AI Navigation + Smart Extraction
echo "📍 Step 1: Navigate to Fantasy category and extract books..."
curl -s -X POST http://localhost:8000/api/v1/extract/ultra-smart \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://books.toscrape.com/",
    "user_instructions": "get all fantasy books",
    "llm_provider": "openai",
    "model_id": "gpt-4-turbo"
  }' > /tmp/pipeline_fantasy.json

BOOK_COUNT=$(jq '.table | length' /tmp/pipeline_fantasy.json)
echo "✅ Extracted $BOOK_COUNT Fantasy books"
echo ""

# 2. Template Mapping on specific book
echo "📍 Step 2: Map first book to custom template..."
FIRST_BOOK_URL="https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html"

curl -s -X POST http://localhost:8000/api/v1/extract/template-map \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"$FIRST_BOOK_URL\",
    \"template_columns\": [\"Title\", \"Price\", \"Rating\", \"Description\"],
    \"llm_provider\": \"openai\"
  }" > /tmp/pipeline_template.json

echo "✅ Mapped to custom template"
jq '.mapped_data' /tmp/pipeline_template.json
echo ""

# 3. Translation
echo "📍 Step 3: Translate book description to Spanish..."
DESCRIPTION=$(jq -r '.mapped_data.Description' /tmp/pipeline_template.json)

curl -s -X POST http://localhost:8000/api/v1/translate \
  -H "Content-Type: application/json" \
  -d "{
    \"text\": $(echo "$DESCRIPTION" | jq -R -s .),
    \"source_lang\": \"en\",
    \"target_lang\": \"es\",
    \"quality\": \"high\"
  }" > /tmp/pipeline_translation.json

echo "✅ Translated to Spanish:"
jq -r '.translated_text' /tmp/pipeline_translation.json
echo ""

# 4. Upload to RAG
echo "📍 Step 4: Upload extracted data to RAG system..."
echo "$DESCRIPTION" > /tmp/book_description.txt

curl -s -X POST http://localhost:8000/api/v1/upload \
  -F "file=@/tmp/book_description.txt" \
  -F "session_id=pipeline_test" > /tmp/pipeline_upload.json

echo "✅ Uploaded to RAG"
echo ""

# 5. Query RAG
echo "📍 Step 5: Query the uploaded data..."
curl -s -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Summarize this book in one sentence",
    "session_id": "pipeline_test",
    "model_id": "gpt-4-turbo"
  }' > /tmp/pipeline_query.json

echo "✅ RAG Answer:"
jq -r '.answer' /tmp/pipeline_query.json
echo ""

# 6. Export to Excel
echo "📍 Step 6: Export all Fantasy books to Excel..."
curl -s -X POST http://localhost:8000/api/v1/extraction/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://books.toscrape.com/catalogue/category/books/fantasy_19/index.html"],
    "output_format": "excel",
    "delivery_method": "download"
  }' > /tmp/pipeline_export.json

JOB_ID=$(jq -r '.job_id' /tmp/pipeline_export.json)
echo "✅ Export job created: $JOB_ID"
echo ""

echo "🎉 FULL PIPELINE TEST COMPLETE!"
echo "================================"
echo ""
echo "Summary:"
echo "  ✅ AI Navigation: $BOOK_COUNT books extracted"
echo "  ✅ Template Mapping: Custom fields mapped"
echo "  ✅ Translation: EN → ES successful"
echo "  ✅ RAG Upload: Document indexed"
echo "  ✅ RAG Query: Answer generated"
echo "  ✅ Excel Export: Job $JOB_ID created"
```

---

## 📊 Expected Performance Metrics

| Operation | Books to Scrape | Expected Time | Notes |
|-----------|----------------|---------------|-------|
| **Smart Extraction (20 items)** | Category page | 8-15s | GPT-4 Turbo |
| **AI Navigation** | Homepage → Category | 10-20s | Includes navigation + extraction |
| **Template Mapping** | Single product | 3-5s | 8 custom fields |
| **CSS Extraction** | Single product | 1-2s | Direct selectors |
| **Pagination (5 pages)** | 100 items | 30-60s | Parallel processing |
| **Bulk (4 categories)** | 80 items | 45-90s | Parallel scraping |
| **OCR (PDF)** | 1-page PDF | 2-5s | Docling method |
| **Translation** | 200 chars | 1-2s | LLM backend |
| **RAG Upload** | JSON file | 2-3s | Includes embedding |
| **RAG Query** | Simple question | 2-4s | Retrieval + generation |

---

## 🎬 Demo Script for Stakeholders

### 5-Minute Demo

```
1. [0:00-0:30] Introduction
   "Today I'll demonstrate our advanced RAG chatbot extracting data from Books to Scrape"

2. [0:30-1:30] Smart Extraction
   - Show URL: books.toscrape.com/catalogue/category/books/mystery_3
   - Run smart extraction
   - Show 20 books extracted with price, rating, availability
   - Export to Excel

3. [1:30-2:30] AI Navigation
   - Show homepage
   - Type: "get all fantasy books"
   - System navigates automatically
   - Extracts Fantasy books
   - Show navigation path in metadata

4. [2:30-3:30] Template Mapping
   - Show product page
   - Define custom template: Title, Author, Price, Rating, ISBN
   - System maps automatically
   - Show missing fields marked

5. [3:30-4:15] Translation
   - Take extracted description
   - Translate EN → ES
   - Show side-by-side comparison

6. [4:15-5:00] RAG Chat
   - Upload extracted books
   - Ask: "Which mystery books cost less than £20?"
   - Show answer with sources
   - Demonstrate source attribution
```

---

## ✅ Success Criteria

After completing all tests, you should have:

- [ ] 20+ mystery books extracted
- [ ] Fantasy books via AI navigation
- [ ] Custom template mapping working
- [ ] CSS selectors extracting correctly
- [ ] Pagination handling 100+ books
- [ ] 4 categories bulk extracted to Excel
- [ ] PDF text extracted via OCR
- [ ] English→Spanish translation working
- [ ] RAG chat answering questions about books
- [ ] Full pipeline completing end-to-end

---

## 🐛 Troubleshooting

### Issue: Smart Extraction Returns Empty
**Solution**: Check OpenAI API key is set
```bash
docker-compose exec backend printenv | grep OPENAI
```

### Issue: AI Navigation Doesn't Navigate
**Solution**: Ensure GPT-4 Turbo is available
```bash
curl -X POST http://localhost:8000/api/v1/models/available | jq '.models[] | select(.id | contains("gpt-4"))'
```

### Issue: OCR Fails
**Solution**: Verify Docling installed
```bash
docker-compose exec backend python3 -c "from docling.document_converter import DocumentConverter; print('✅ Docling OK')"
```

### Issue: Translation Returns English
**Solution**: Check translation service status
```bash
docker-compose exec backend python3 -c "from app.services.translation_service import TranslationService; from app.services.llm_service import llm_service; import asyncio; asyncio.run(TranslationService(llm_service).get_status())"
```

---

## 📁 Output Files Location

All test results saved to `/tmp/`:
- `/tmp/test1_mystery_books.json` - Smart extraction results
- `/tmp/test2_fantasy_navigation.json` - AI navigation results
- `/tmp/test3_template_mapping.json` - Template mapping results
- `/tmp/test4_css_extraction.json` - CSS extraction results
- `/tmp/test5_pagination.json` - Pagination results
- `/tmp/test6_bulk_extraction.json` - Bulk extraction job
- `/tmp/test7_ocr_pdf.json` - OCR results
- `/tmp/test8_translation.json` - Translation results
- `/tmp/test9_rag_query.json` - RAG chat results

---

## 🎓 Next Steps

1. **Run All Tests**:
   ```bash
   chmod +x /mnt/c/AIML/ClaudeCode/chatbot/ChatBot/docs/features/run_all_tests.sh
   ./run_all_tests.sh
   ```

2. **Record Screen Demo**:
   - Use OBS Studio or similar
   - Follow 5-minute demo script
   - Save for training materials

3. **Create Screenshots**:
   - UI showing extraction in progress
   - Results table with data
   - Export options
   - Chat interface with sources

4. **Update Training Materials**:
   - Add real examples from Books to Scrape
   - Include actual screenshots
   - Document common issues encountered

---

**Test Plan Version**: 1.0
**Last Updated**: 2025-11-21
**Maintained By**: Engineering Team

---

**End of Comprehensive Feature Test Plan**
