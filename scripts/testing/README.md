# Testing Scripts

Test scripts for integration, validation, and performance testing.

## Available Scripts

### Integration Tests

#### `test-integration.sh`
Comprehensive integration test suite.
- Tests document upload
- Tests RAG queries
- Tests all API endpoints
- Validates end-to-end flow

```bash
./test-integration.sh
```

---

### Document Upload Tests

#### `test-upload-endpoint.sh`
Test document upload endpoint.
```bash
./test-upload-endpoint.sh
```

#### `test-upload-now.sh`
Quick upload test with sample document.
```bash
./test-upload-now.sh
```

#### `test_api_upload.sh`
API-level upload testing.
```bash
./test_api_upload.sh
```

#### `test_upload_pipeline.py`
Python-based upload pipeline testing.
```bash
python test_upload_pipeline.py
```

#### `test-document-flow.sh`
Test complete document processing flow.
```bash
./test-document-flow.sh
```

---

### RAG System Tests

#### `test_rag_validation.py`
Comprehensive RAG validation with RAGAS metrics.
```bash
python test_rag_validation.py
```

#### `test_rag_validation_simple.py`
Simplified RAG validation tests.
```bash
python test_rag_validation_simple.py
```

#### `test_rag_debug.sh`
RAG pipeline debugging and testing.
```bash
./test_rag_debug.sh
```

---

### LLM Tests

#### `test-local-llm.sh`
Test local LLM (Ollama) integration.
```bash
./test-local-llm.sh
```

#### `test_llm_classifier.py`
Test LLM-based query classification.
```bash
python test_llm_classifier.py
```

#### `test_query_classification.py`
Test query classification system.
```bash
python test_query_classification.py
```

---

### Performance Tests

#### `test-slider-real-time.sh`
Test RAG system with different K values (real-time slider testing).
```bash
./test-slider-real-time.sh
```

---

### Multi-Tool Agent Tests (Phase 7 & 8)

#### `test_phase7_8_multitool_agent.sh`
**NEW** - Comprehensive test suite for Phase 7 & 8 multi-tool agent implementation.
- Tests backend health check
- Tests web scraping query (Moneycontrol)
- Tests document RAG query
- Validates LLM-based tool selection
- Verifies metadata tracking

```bash
./test_phase7_8_multitool_agent.sh
```

**Expected Output**: All 3 tests should pass, demonstrating multi-tool agent is operational.

---

### Web Scraping & Extraction Tests

#### `test_ultra_smart_extraction.sh`
**NEW** - Tests ultra-smart extraction endpoint with various scenarios.
- Test 1: Mystery Books category page (direct extraction)
- Test 2: Sharp Objects product page (single item extraction)
- Test 3: AI-powered navigation to Fantasy category
- Test 4: AI-powered navigation to Mystery category

```bash
./test_ultra_smart_extraction.sh
```

**Expected Output**: 4/4 tests pass, including AI navigation tests.

**What This Tests**:
- Direct page extraction
- Single product extraction
- AI-powered navigation from homepage to specific category
- OpenAI GPT-4 integration for navigation decisions

---

### PDF Extraction Tests

#### `test_pdf_extraction_docling.sh`
**NEW** - Tests Docling integration for PDF document processing.
- Test 1: Docling library import and initialization
- Test 2: Direct PDF extraction with Docling
- Test 3: PDF extraction via API (Ultra-Smart Extraction)

```bash
./test_pdf_extraction_docling.sh
```

**Expected Output**: 3/3 tests pass, demonstrating PDF extraction is working.

**What This Tests**:
- Docling library installation
- PDF text extraction to Markdown
- API-based PDF processing

---

### Web Scraper Tests

#### `test-web-scraper.sh`
Test web scraping functionality.
```bash
./test-web-scraper.sh
```

---

## 🧪 Test Categories

### Quick Tests (< 30 seconds)
- `test-upload-now.sh`
- `test-local-llm.sh`
- `test_query_classification.py`
- `test_pdf_extraction_docling.sh` ⭐ NEW

### Standard Tests (< 5 minutes)
- `test-upload-endpoint.sh`
- `test-document-flow.sh`
- `test_rag_validation_simple.py`
- `test_phase7_8_multitool_agent.sh` ⭐ NEW
- `test_ultra_smart_extraction.sh` ⭐ NEW

### Comprehensive Tests (> 5 minutes)
- `test-integration.sh`
- `test_rag_validation.py`
- `test-slider-real-time.sh`

---

## 🔗 Related Documentation

- [../../docs/evaluation/](../../docs/evaluation/) - Evaluation guides
- [../../docs/debugging/RAG_DEBUGGING_GUIDE.md](../../docs/debugging/RAG_DEBUGGING_GUIDE.md)

---

**Last Updated**: 2025-11-23

---

## 📝 Recently Added (2025-11-23)

- ⭐ **`test_phase7_8_multitool_agent.sh`** - Multi-tool agent integration tests (Phase 7 & 8)
- ⭐ **`test_ultra_smart_extraction.sh`** - Web scraping and AI navigation tests
- ⭐ **`test_pdf_extraction_docling.sh`** - PDF extraction with Docling integration
