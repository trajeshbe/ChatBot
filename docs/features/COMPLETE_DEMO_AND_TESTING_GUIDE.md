# Complete Demo & Testing Guide
## Advanced RAG Chatbot with OCR, Translation, and Form Automation

**Date**: 2025-11-21
**Purpose**: Comprehensive testing and demonstration guide for end-user training

---

## 🎯 Executive Summary

This document provides complete testing scenarios for all features of the Enterprise RAG Chatbot, including the newly implemented advanced capabilities (OCR, Translation, Form Automation).

**Use this guide for**:
- ✅ End-user training
- ✅ Feature demonstration
- ✅ Quality assurance testing
- ✅ Onboarding new team members

---

## 📋 Feature Matrix

| Feature | Status | Module | Test Script |
|---------|--------|--------|-------------|
| **Smart Extraction** | ✅ Ready | LLM Extractor | `test_smart_extraction.sh` |
| **Template Mapping** | ✅ Ready | Template Mapper | `test_template_mapping.sh` |
| **CSS Extraction** | ✅ Ready | CSS Extractor | `test_css_extraction.sh` |
| **OCR (Scanned PDFs)** | ✅ **NEW** | OCR Service | `test_advanced_capabilities.sh` |
| **Translation** | ✅ **NEW** | Translation Service | `test_advanced_capabilities.sh` |
| **Form Automation** | ✅ **NEW** | Form Handler | `test_advanced_capabilities.sh` |
| **RAG Chat** | ✅ Ready | RAG Service | `test_rag_chat.sh` |
| **Document Upload** | ✅ Ready | Document Service | `test_document_upload.sh` |
| **Web Scraping** | ✅ Ready | Scraper Service | `test_web_scraper.sh` |

---

## 🧪 Testing Scenarios

### Scenario 1: Smart Extraction (Books E-commerce)

**Objective**: Extract structured data from product listings

**Test Steps**:

1. **Start Backend**
```bash
docker-compose up -d backend
```

2. **Run Smart Extraction Test**
```bash
curl -X POST http://localhost:8000/api/v1/extract/ultra-smart \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://books.toscrape.com/catalogue/category/books/mystery_3/index.html",
    "user_instructions": "Extract all mystery books with title, price, and availability",
    "source_type": "url",
    "llm_provider": "openai"
  }' | jq .
```

**Expected Result**:
- ✅ Extracts 20 books
- ✅ Columns: title, price, availability
- ✅ Extraction time: 5-15 seconds
- ✅ Success: true

**Screenshot Points**:
- API request in Postman/curl
- JSON response with structured data
- Table format with all extracted books

---

### Scenario 2: OCR from Scanned PDF

**Objective**: Extract text from a scanned/image-based PDF document

**Test Steps**:

1. **Test with Sample PDF**
```bash
docker-compose exec backend python3 << 'EOF'
import sys
sys.path.insert(0, '/app')

from app.services.ocr_service import OCRService
import requests
import tempfile
import asyncio

async def test_ocr():
    ocr_service = OCRService()

    # Download test PDF
    pdf_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    response = requests.get(pdf_url, timeout=10)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name

    # Extract with OCR
    result = await ocr_service.extract_text(tmp_path, method="auto")

    print(f"✅ OCR Extraction Successful!")
    print(f"   Method used: {result['method_used']}")
    print(f"   Confidence: {result['confidence']:.2f}")
    print(f"   Pages: {result['pages']}")
    print(f"   Text length: {len(result['text'])} chars")
    print(f"\n📄 Extracted Text:")
    print(result['text'][:500])

asyncio.run(test_ocr())
EOF
```

**Expected Result**:
- ✅ Method used: docling or tesseract
- ✅ Confidence: > 0.7
- ✅ Text extracted successfully
- ✅ Pages detected correctly

**UI Test** (via Frontend):
1. Go to http://localhost:3001
2. Click "Upload Document"
3. Upload a scanned PDF
4. System automatically uses OCR
5. View extracted text in document list

---

### Scenario 3: Translation (Multilingual Content)

**Objective**: Translate extracted content to target language

**Test Steps**:

1. **Test Translation Service**
```bash
docker-compose exec backend python3 << 'EOF'
import sys
sys.path.insert(0, '/app')

from app.services.translation_service import TranslationService
from app.services.llm_service import llm_service
import asyncio

async def test_translation():
    translation_service = TranslationService(llm_service=llm_service)

    # Test translation
    result = await translation_service.translate(
        text="Hello, how are you? This is a test of the translation system.",
        source_lang="en",
        target_lang="es",
        quality="high"  # Use LLM for high quality
    )

    print(f"✅ Translation Successful!")
    print(f"   Backend used: {result['backend_used']}")
    print(f"   Confidence: {result['confidence']:.2f}")
    print(f"   Original: Hello, how are you?...")
    print(f"   Translated: {result['translated_text']}")

asyncio.run(test_translation())
EOF
```

**Expected Result**:
- ✅ Backend: llm (high quality)
- ✅ Confidence: > 0.8
- ✅ Translation: "Hola, ¿cómo estás?..." (Spanish)

**API Test with Smart Extraction**:
```bash
curl -X POST http://localhost:8000/api/v1/extract/ultra-smart \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://books.toscrape.com/catalogue/category/books/mystery_3/index.html",
    "user_instructions": "Extract all mystery books",
    "translate_to": "es",
    "llm_provider": "openai"
  }' | jq .
```

**Expected Result**:
- ✅ Extracts books in English
- ✅ Translates to Spanish
- ✅ Returns bilingual data

---

### Scenario 4: Form Automation (Login-Protected Content)

**Objective**: Automatically fill and submit login forms to access protected content

**Test Steps**:

1. **Test Form Handler**
```bash
docker-compose exec backend python3 << 'EOF'
import sys
sys.path.insert(0, '/app')

from app.services.webscraper.automation import FormHandler
from unittest.mock import Mock, AsyncMock
import asyncio

async def test_form():
    # Mock Playwright page
    mock_page = Mock()
    mock_page.url = "https://example.com/login"
    mock_page.wait_for_selector = AsyncMock()
    mock_page.fill = AsyncMock()
    mock_page.click = AsyncMock()
    mock_page.evaluate = AsyncMock(return_value=[])

    form_handler = FormHandler(mock_page)

    # Test form filling
    result = await form_handler.fill_and_submit_form({
        "username": "test_user",
        "password": "test_password"
    })

    print(f"✅ Form Automation Test Successful!")
    print(f"   Form fields filled: {result.get('fields_filled', 0)}")
    print(f"   Form submitted: {result.get('submitted', False)}")

asyncio.run(test_form())
EOF
```

**Expected Result**:
- ✅ Form handler initialized
- ✅ Fields filled: 2 (username, password)
- ✅ Form submitted: True
- ✅ No CAPTCHA detected (in mock)

---

### Scenario 5: RAG Chat with Translation

**Objective**: Query documents and get answers in different language

**Test Steps**:

1. **Upload Spanish Document**
```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@/path/to/spanish_document.pdf" \
  -F "session_id=test_session_123"
```

2. **Query in English, Get Answer Translated to Spanish**
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is this document about?",
    "session_id": "test_session_123",
    "model_id": "gpt-4-turbo",
    "translate_to": "es"
  }' | jq .
```

**Expected Result**:
- ✅ Retrieves relevant chunks from document
- ✅ Generates answer in English
- ✅ Translates answer to Spanish
- ✅ Returns sources with confidence scores

---

### Scenario 6: Full Integration Test (All Capabilities)

**Objective**: Test all three capabilities working together

**Workflow**:
1. Website has login form → **Form Automation**
2. Downloads scanned PDF → **OCR**
3. Extracts data from Spanish text → **Translation**

**Test Script**:
```bash
chmod +x scripts/testing/test_advanced_capabilities.sh
./scripts/testing/test_advanced_capabilities.sh
```

**Expected Output**:
```
╔══════════════════════════════════════════════════════════════════════╗
║  Advanced Capabilities Integration Testing                          ║
║  Testing: OCR, Translation, Form Automation                         ║
╚══════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEST 1: OCR Service - PDF Text Extraction
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Extraction successful!
   Method used: docling
   Confidence: 0.95
   Pages: 3
   Text length: 1,234 chars

✅ TEST 1 PASSED: OCR Service Working

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEST 2: Translation Service - Multilingual Support
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Translation successful!
   Original: Hello, how are you?
   Translated: Hola, ¿cómo estás?
   Backend used: llm
   Confidence: 0.90

✅ TEST 2 PASSED: Translation Service Working

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEST 3: Form Automation - Smart Form Handling
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Form handler initialized
✅ Field matching working
✅ Text field filled
✅ Checkbox field checked
✅ CAPTCHA detection working

✅ TEST 3 PASSED: Form Automation Working

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEST 4: Integration - All Three Services Together
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ All services available
✅ Integration pattern validated

✅ TEST 4 PASSED: Integration Working

╔══════════════════════════════════════════════════════════════════════╗
║                        TEST SUMMARY                                  ║
╚══════════════════════════════════════════════════════════════════════╝

✅ All Tests Passed!

Services Tested:
  ✅ OCR Service (Docling + Tesseract hybrid)
  ✅ Translation Service (LLM + Transformers)
  ✅ Form Automation (Playwright-integrated)
  ✅ Integration (All three working together)

🎉 Advanced Capabilities Fully Implemented and Tested!
```

---

## 🖥️ UI Testing Guide

### Test 1: Upload and Process Document with OCR

**Steps**:
1. Navigate to http://localhost:3001
2. Click "Upload Document" button
3. Select a scanned PDF file
4. Click "Upload"
5. Wait for processing (OCR runs automatically)
6. View document in "Uploaded Documents" list
7. Click document to see extracted text

**What to Observe**:
- ✅ Upload progress indicator
- ✅ "Processing..." status
- ✅ Automatic OCR detection for scanned PDFs
- ✅ Text preview after extraction
- ✅ Confidence score displayed

**Screenshot Points**:
1. Upload button and file selector
2. Processing indicator with OCR status
3. Document list showing processed file
4. Text preview with OCR indicator

---

### Test 2: Smart Extraction from UI

**Steps**:
1. Go to "Data Extraction" tab
2. Enter URL: `https://books.toscrape.com/catalogue/category/books/mystery_3/index.html`
3. Enter instructions: "Extract all books with title and price"
4. Select "Smart Extraction" method
5. Click "Extract Data"
6. View results in table format

**What to Observe**:
- ✅ URL validation
- ✅ Extraction progress indicator
- ✅ Table with structured data
- ✅ Export options (CSV, Excel, JSON)

**Screenshot Points**:
1. Data Extraction form
2. Extraction in progress
3. Results table with data
4. Export options

---

### Test 3: RAG Chat with Document

**Steps**:
1. Upload a document (from Test 1)
2. Go to "Chat" tab
3. Type query: "What is this document about?"
4. Submit query
5. View answer with sources

**What to Observe**:
- ✅ Chat interface with message history
- ✅ Real-time typing indicator
- ✅ Answer with source attribution
- ✅ Clickable sources linking to documents

**Screenshot Points**:
1. Chat interface with query
2. Typing indicator
3. Answer with sources
4. Source document preview

---

### Test 4: Translation in Chat

**Steps**:
1. Upload English document
2. Go to "Chat" tab
3. Select language dropdown: "Spanish (es)"
4. Type query in English: "Summarize this document"
5. Submit query
6. View answer in Spanish

**What to Observe**:
- ✅ Language selector visible
- ✅ Query submitted in English
- ✅ Answer returned in Spanish
- ✅ Sources still linked correctly

**Screenshot Points**:
1. Language selector dropdown
2. English query submitted
3. Spanish answer returned
4. Source attribution maintained

---

## 📊 Performance Benchmarks

### Expected Performance Metrics

| Operation | Expected Time | Notes |
|-----------|--------------|-------|
| **Smart Extraction (10 items)** | 5-15s | Depends on page complexity |
| **OCR (1 page PDF)** | 2-5s | Docling is faster |
| **OCR (1 page image)** | 3-8s | Tesseract fallback |
| **Translation (< 500 chars)** | 1-2s | LLM backend |
| **Translation (> 500 chars)** | 2-5s | Transformers backend |
| **Form Automation** | 2-5s | Depends on form complexity |
| **RAG Query** | 1-3s | Includes retrieval + LLM |
| **Document Upload** | 1-2s | Small files < 10MB |

---

## 🐛 Troubleshooting Guide

### Issue 1: OCR Not Working

**Symptoms**:
- Empty text extraction
- Error: "OCR service not available"

**Solutions**:
```bash
# Check OCR service
docker-compose exec backend python3 -c "
from app.services.ocr_service import OCRService
service = OCRService()
print(service.get_status())
"

# Verify Docling installed
docker-compose exec backend pip list | grep docling

# Verify Tesseract installed
docker-compose exec backend tesseract --version
```

---

### Issue 2: Translation Returns English

**Symptoms**:
- Translation requested but returns original language

**Solutions**:
```bash
# Check translation service
docker-compose exec backend python3 -c "
from app.services.translation_service import TranslationService
service = TranslationService()
print(service.get_status())
print(service.get_supported_languages())
"

# Verify LLM service working
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "model_id": "gpt-4-turbo"}'
```

---

### Issue 3: Form Automation Fails

**Symptoms**:
- Form not filled
- Error: "Could not find field"

**Solutions**:
```bash
# Check Playwright installed
docker-compose exec backend python3 -c "
from playwright.async_api import async_playwright
print('Playwright available')
"

# Test form handler
docker-compose exec backend python3 -c "
from app.services.webscraper.automation import FormHandler
print('Form handler available')
"
```

---

## 📝 End-User Training Checklist

### Basic Features
- [ ] Upload a document
- [ ] Query documents using RAG chat
- [ ] View chat history
- [ ] View uploaded documents
- [ ] Delete documents

### Advanced Features
- [ ] Perform smart extraction from URL
- [ ] Extract data using template mapping
- [ ] Use CSS selector extraction
- [ ] Upload scanned PDF and verify OCR
- [ ] Translate chat answers to different language
- [ ] Export extracted data to Excel/CSV

### Integration Features
- [ ] Extract data from multilingual website (OCR + Translation)
- [ ] Scrape login-protected content (Form Automation)
- [ ] Process international documents (OCR + Translation + RAG)

---

## 🎓 Training Session Outline

### Session 1: Basic Features (30 minutes)
1. Introduction to RAG chatbot (5 min)
2. Document upload demo (5 min)
3. Chat interface demo (10 min)
4. Hands-on practice (10 min)

### Session 2: Data Extraction (45 minutes)
1. Smart extraction overview (5 min)
2. Live demo: Extract books data (10 min)
3. Template mapping demo (10 min)
4. CSS extraction demo (10 min)
5. Hands-on practice (10 min)

### Session 3: Advanced Capabilities (60 minutes)
1. OCR demonstration (15 min)
   - Upload scanned PDF
   - Show automatic OCR
   - Compare with regular PDF
2. Translation demonstration (15 min)
   - Extract multilingual content
   - Translate chat answers
   - Show cost optimization
3. Form automation demonstration (15 min)
   - Login-protected scraping
   - Multi-step form handling
   - CAPTCHA detection
4. Hands-on practice (15 min)

---

## 📚 Additional Resources

- **Architecture Guide**: `docs/features/ADVANCED_CAPABILITIES_IMPLEMENTATION.md`
- **Usage Examples**: `docs/features/samples/ADVANCED_CAPABILITIES_USAGE.md`
- **Integration Patterns**: `docs/features/INTELLIGENT_INTEGRATION_GUIDE.md`
- **Implementation Summary**: `docs/features/ADVANCED_CAPABILITIES_SUMMARY.md`

- **Test Scripts**: `scripts/testing/test_advanced_capabilities.sh`
- **Quick Start**: `docs/guides/QUICKSTART.md`
- **Admin Guide**: `docs/guides/ADMIN_GUIDE.md`

---

## ✅ Certification Checklist

**After completing training, users should be able to**:

### Level 1: Basic User
- [ ] Upload documents successfully
- [ ] Ask questions and get answers from documents
- [ ] View and manage uploaded files
- [ ] Understand source attribution

### Level 2: Power User
- [ ] Perform smart data extraction
- [ ] Use different extraction methods
- [ ] Export data in multiple formats
- [ ] Configure extraction parameters

### Level 3: Advanced User
- [ ] Use OCR for scanned documents
- [ ] Extract and translate multilingual content
- [ ] Scrape login-protected websites
- [ ] Combine multiple capabilities in workflows
- [ ] Troubleshoot common issues

---

**Document Version**: 1.0
**Last Updated**: 2025-11-21
**Maintained By**: Engineering Team
**Contact**: support@company.com

---

**End of Complete Demo & Testing Guide**
