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

## 🧪 Test Categories

### Quick Tests (< 30 seconds)
- `test-upload-now.sh`
- `test-local-llm.sh`
- `test_query_classification.py`

### Standard Tests (< 5 minutes)
- `test-upload-endpoint.sh`
- `test-document-flow.sh`
- `test_rag_validation_simple.py`

### Comprehensive Tests (> 5 minutes)
- `test-integration.sh`
- `test_rag_validation.py`
- `test-slider-real-time.sh`

---

## 🔗 Related Documentation

- [../../docs/evaluation/](../../docs/evaluation/) - Evaluation guides
- [../../docs/debugging/RAG_DEBUGGING_GUIDE.md](../../docs/debugging/RAG_DEBUGGING_GUIDE.md)

---

**Last Updated**: 2025-11-16
