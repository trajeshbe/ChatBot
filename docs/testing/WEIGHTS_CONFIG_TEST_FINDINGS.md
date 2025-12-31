# Weights Configuration Testing - RAG vs Direct LLM

**Date**: 2025-11-30
**Test File**: `backend/tests/e2e/test_weights_rag_vs_direct_llm.py`
**Test Duration**: ~60 seconds
**Tests Run**: 2
**Tests Passed**: 0 (Inconclusive)

---

## Executive Summary

Comprehensive testing of the weight configuration system to validate whether adjusting `strategy_weights` actually controls RAG behavior (document retrieval vs direct LLM). The test results show that **both scenarios retrieved documents**, suggesting the weights may not be controlling the RAG pipeline endpoint as expected.

### Key Findings ⚠️

- ⚠️ **Direct LLM High Weight (95%)**: System still retrieved 3 documents
- ⚠️ **RAG Long-term High Weight (95%)**: System retrieved 3 documents (expected)
- ✅ **Document Upload**: Works correctly
- ✅ **Weight Configuration API**: Accepts and stores weight updates
- ❌ **Weight Enforcement**: Weights don't appear to control /api/v1/rag-pipeline/query behavior

---

## Test Setup

### Test Document

Created a document with **unique, identifiable markers** that would NOT be in the LLM's training data:

```
Secret Codes:
- ALPHA-BRAVO-CHARLIE-999
- ZEPHYR-QUANTUM-DELTA
- NEBULA-X7
- SIGMA-LAMBDA-9
- THETA-OMEGA-15
```

**Purpose**: If the system retrieves this document, it should mention these codes. If it uses direct LLM (no RAG), it should NOT know about them.

### Weight Configurations Tested

#### Configuration 1: Direct LLM Favored
```yaml
strategy_weights:
  rag_short_term: 0.05
  rag_hybrid: 0.05
  rag_long_term: 0.10  # Very low - discourage RAG
  direct_llm: 0.95      # Very high - prefer Direct LLM
  tool_navigation: 0.05
  tool_ocr: 0.05
  tool_docling: 0.05
  tool_web_scraping: 0.05
```

**Expected**: System should use direct LLM, NOT retrieve documents

#### Configuration 2: RAG Long-term Favored
```yaml
strategy_weights:
  rag_short_term: 0.90
  rag_hybrid: 0.90
  rag_long_term: 0.95  # Very high - prefer RAG
  direct_llm: 0.05      # Very low - discourage Direct LLM
  tool_navigation: 0.80
  tool_ocr: 0.80
  tool_docling: 0.80
  tool_web_scraping: 0.75
```

**Expected**: System should retrieve documents from long-term memory

---

## Test 1: Direct LLM High Weight (95%)

### Configuration Applied

```json
{
  "rag_long_term": 0.10,
  "direct_llm": 0.95
}
```

### Query

> "What is the secret code mentioned in the document?"

### Expected Behavior

- System should use Direct LLM (no document retrieval)
- Answer should be general or say "no information available"
- **0-1 sources** cited
- Answer should **NOT contain** unique markers

### Actual Results ⚠️

```
📝 Answer received:
   Length: 1141 chars
   Sources cited: 3 ❌ (Expected 0-1)
   Unique markers in answer: 0 ✅

Answer preview:
"The document you are referring to does not provide an explicit mention
of any unique markers or codes that would allow it to answer specific
questions about them. The information provided is generic..."
```

### Analysis

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| Number of Sources | 0-1 | 3 | ❌ FAILED |
| Unique Markers Found | 0 | 0 | ✅ PASSED |
| Uses Direct LLM | Yes | No | ❌ FAILED |

**Conclusion**: System retrieved documents despite Direct LLM weight being 95%. However, the answer correctly didn't contain the unique markers, suggesting it may not have successfully extracted them from the retrieved chunks.

---

## Test 2: RAG Long-term High Weight (95%)

### Configuration Applied

```json
{
  "rag_long_term": 0.95,
  "direct_llm": 0.05
}
```

### Query

> "What is the secret code mentioned in the document?"

### Expected Behavior

- System should use RAG and retrieve documents
- Answer should contain information from uploaded document
- **1+ sources** cited
- Answer should **contain** unique markers like "ALPHA-BRAVO-CHARLIE-999"

### Actual Results ⚠️

```
📝 Answer received:
   Length: 1141 chars
   Sources cited: 3 ✅ (Expected 1+)
   Unique markers in answer: 0 ❌

Answer preview:
"The document you are referring to does not provide an explicit mention
of any unique markers or codes that would allow it to answer specific
questions about them. The information provided is generic..."

📚 Sources cited:
   1. Unknown
      Excerpt: "If the system retrieves this document, it should be able
                to answer questions about these unique markers..."

   2. Unknown
      Excerpt: "If the system retrieves this document, it should be able
                to answer questions about these unique markers..."

   3. Unknown
      Excerpt: "Company: book_fantasy
                Source: https://books.toscrape.com/catalogue/category/books/fiction_10/..."
```

### Analysis

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| Number of Sources | 1+ | 3 | ✅ PASSED |
| Unique Markers Found | 1+ | 0 | ❌ FAILED |
| Uses RAG | Yes | Yes | ✅ PASSED |

**Conclusion**: System retrieved documents (good), but the LLM failed to extract and mention the unique secret codes from the retrieved chunks. The answer says "does not provide an explicit mention" even though the codes ARE explicitly mentioned in the document.

**Notable**: Source #3 appears to be from a different document (book_fantasy), suggesting retrieval may be pulling from the wrong documents or mixing multiple documents.

---

## Root Cause Analysis

### Issue #1: Weights Not Affecting Retrieval Behavior ⚠️

**Observation**: Both tests retrieved 3 documents, regardless of weight configuration.

**Possible Causes**:

1. **RAG Pipeline Endpoint Bypasses Weights**
   - The `/api/v1/rag-pipeline/query` endpoint may not be consulting the `strategy_weights`
   - It may have its own hardcoded retrieval logic

2. **Weights Applied at Different Layer**
   - Weights might control strategy *selection* in multi-strategy scenarios
   - But a single RAG query always retrieves documents regardless of weights

3. **Missing Integration**
   - Weight configuration service exists
   - Weight update API works
   - But RAG pipeline service may not be reading these weights

### Issue #2: LLM Not Extracting Unique Codes ⚠️

**Observation**: Documents were retrieved (confirmed by excerpts), but LLM didn't mention the unique codes.

**Possible Causes**:

1. **Chunking Split the Codes**
   - The unique codes might be in different chunks
   - LLM only sees partial context

2. **LLM Model Limitations**
   - qwen2.5:1.5b may not be powerful enough to extract specific codes
   - Might need larger model (qwen2.5:7b or llama3.2)

3. **Prompt Engineering**
   - RAG prompt may not explicitly instruct LLM to cite specific codes/numbers
   - May need more explicit extraction instructions

### Issue #3: Wrong Documents Retrieved 🔍

**Observation**: Source #3 mentions "book_fantasy" from books.toscrape.com

**Analysis**:
- Test uploaded "unique_test_doc.txt" to a specific project
- But retrieval returned documents from a different source (web scraping)
- This suggests:
  - Project isolation may not be working in RAG pipeline
  - OR session_id not properly scoping the retrieval
  - OR test document wasn't properly indexed

---

## Verification Steps Performed

### ✅ Weight Configuration API

```bash
# Get weights
GET /api/v1/config/weights

# Update weights
POST /api/v1/config/weights
{
  "strategy_weights": {
    "direct_llm": 0.95,
    "rag_long_term": 0.10
  }
}
```

**Result**: ✅ API accepts and stores weight updates

### ✅ Document Upload

```bash
POST /api/v1/upload
```

**Result**: ✅ Document uploaded successfully

### ⚠️ Weight Enforcement

**Result**: ❌ Weights don't appear to control retrieval behavior

---

## Investigation Needed

### 1. Check RAG Pipeline Implementation

**Question**: Does `/api/v1/rag-pipeline/query` actually read `strategy_weights`?

**Files to Check**:
- `backend/app/rag_pipeline/pipeline.py`
- `backend/app/rag_pipeline/retrieval.py`
- `backend/app/api/routes/rag_pipeline_routes.py`

**Look For**:
```python
# Should see something like:
weights = weights_config_service.get_strategy_weights()
if weights['direct_llm'] > threshold:
    # Use direct LLM, skip retrieval
    pass
else:
    # Use RAG, retrieve documents
    pass
```

### 2. Check Multi-Strategy RAG Service

**Question**: Does the multi-strategy service use these weights?

**Files to Check**:
- `backend/app/services/multi_strategy_rag.py`

**Look For**:
```python
# Strategy selection based on weights
strategy_weights = self.strategy_weights  # From config?
selected_strategy = self.select_strategy(query, weights)
```

### 3. Verify Document Indexing

**Question**: Was the test document properly processed and embedded?

**SQL Query**:
```sql
SELECT d.id, d.filename, COUNT(c.id) as chunk_count
FROM documents d
LEFT JOIN document_chunks c ON d.id = c.document_id
WHERE d.filename = 'unique_test_doc.txt'
GROUP BY d.id, d.filename;
```

**Expected**: Should show document with multiple chunks

### 4. Check Project/Session Isolation

**Question**: Why did retrieval return documents from different projects?

**SQL Query**:
```sql
-- Check if session_documents table is being used
SELECT sd.session_id, d.filename, d.file_path
FROM session_documents sd
JOIN documents d ON sd.document_id = d.id
WHERE sd.session_id = 'weights-test-1764475959';
```

---

## Recommendations

### Immediate Actions (Next 30 Minutes)

1. **Verify Weight Integration** (15 min)
   ```bash
   # Search for weight usage in RAG pipeline
   grep -r "strategy_weights" backend/app/rag_pipeline/
   grep -r "get_strategy_weights" backend/app/rag_pipeline/
   ```

2. **Check Document Processing** (10 min)
   ```sql
   -- Verify test document was processed
   SELECT * FROM documents
   WHERE filename = 'unique_test_doc.txt'
   ORDER BY upload_date DESC LIMIT 1;

   -- Check chunks
   SELECT chunk_index, LEFT(content, 100) as content_preview
   FROM document_chunks
   WHERE document_id = '<document_id>'
   ORDER BY chunk_index;
   ```

3. **Test with Larger Model** (5 min)
   ```python
   # Update test to use llama3.2-vision:11b
   "model_name": "ollama/llama3.2-vision:11b"
   ```

### Short-Term Fixes (Next 2 Hours)

1. **Add Weight Enforcement to RAG Pipeline**

   If weights aren't being checked, add logic:

   ```python
   # In rag_pipeline/pipeline.py
   from app.services.weights_config_service import weights_config_service

   async def rag_answer(query: str, session_id: str, ...):
       weights = weights_config_service.get_strategy_weights()

       # If direct LLM weight is very high, skip retrieval
       if weights.get('direct_llm', 0) > 0.90:
           logger.info("Using direct LLM (high weight)")
           return await direct_llm_query(query, ...)

       # Otherwise, use RAG
       logger.info("Using RAG (weights favor document retrieval)")
       return await rag_query_with_retrieval(query, ...)
   ```

2. **Improve Chunk Quality**

   Ensure codes aren't split across chunks:

   ```python
   # Increase chunk_overlap to preserve context
   chunk_overlap = 300  # Was 150
   ```

3. **Better Prompt for Code Extraction**

   ```python
   prompt = f"""Based on the following document excerpts, answer the question.
   Pay special attention to specific codes, numbers, and identifiers.
   If you see codes like ALPHA-BRAVO-CHARLIE or similar patterns, include them in your answer.

   Question: {query}

   Documents:
   {context}

   Answer:"""
   ```

### Long-Term Enhancements

1. **Add Strategy Selection Logging**
   - Log which strategy is selected
   - Log the weights that influenced the decision
   - Add to response metadata

2. **Create Strategy Visualization**
   - Show in UI which strategy was used
   - Display weight configuration
   - Allow real-time weight adjustment

3. **Add Integration Tests**
   - Test weight enforcement at each layer
   - Verify strategy selection logic
   - Validate document scoping

---

## Alternative Test Approach

Since the current test shows both scenarios retrieve documents, here's an alternative approach:

### Test Different Endpoints

1. **Test Multi-Strategy Endpoint** (if exists)
   ```python
   POST /api/v1/multi-strategy/query
   {
     "query": "...",
     "strategies": ["direct_llm", "rag_long_term"],
     "weights": {...}
   }
   ```

2. **Test Direct LLM-only Endpoint**
   ```python
   POST /api/v1/query
   {
     "query": "...",
     "use_rag": false  # Explicit flag
   }
   ```

3. **Test RAG-only Endpoint**
   ```python
   POST /api/v1/query
   {
     "query": "...",
     "use_rag": true  # Explicit flag
   }
   ```

### Test Weight Effects on Strategy Selection

Instead of testing retrieval behavior, test the **strategy selection** logic:

```python
# Get strategy recommendation
response = await client.post("/api/v1/strategy/select", json={
    "query": "What is the secret code?",
    "session_id": session_id,
    "weights": {"direct_llm": 0.95, "rag_long_term": 0.10}
})

# Response should indicate which strategy was selected
selected_strategy = response.json()["selected_strategy"]
assert selected_strategy == "direct_llm"
```

---

## Conclusion

### Summary of Findings

| Finding | Status | Impact |
|---------|--------|--------|
| Weight Config API Works | ✅ | Weights can be set and retrieved |
| Document Upload Works | ✅ | Documents can be uploaded |
| Document Retrieval Works | ✅ | System retrieves documents |
| Weights Control Behavior | ❌ | Weights don't affect retrieval |
| Project Isolation | ⚠️ | Wrong documents retrieved |
| LLM Code Extraction | ❌ | Codes not extracted from chunks |

### Overall Assessment: ⚠️ **WEIGHTS NOT ENFORCED**

The weight configuration system is **partially implemented**:
- ✅ Configuration storage and retrieval works
- ✅ API endpoints functional
- ❌ RAG pipeline doesn't consult weights before retrieval
- ❌ Strategy selection not weight-based

### Expected vs Actual Behavior

**Expected**:
```
High Direct LLM Weight → No document retrieval → General answer
High RAG Weight → Document retrieval → Specific answer with codes
```

**Actual**:
```
High Direct LLM Weight → Document retrieval ❌ → Generic answer ✅
High RAG Weight → Document retrieval ✅ → Generic answer ❌
```

### Implications for User

**User's Request**: Test if weight settings force the system to use documents vs direct LLM

**Finding**: The `/api/v1/rag-pipeline/query` endpoint appears to **always retrieve documents** regardless of weight settings. The weights may be intended for a different purpose (multi-strategy answer fusion, not retrieval control).

### Recommended Next Steps

1. **Clarify Weight Purpose** (5 min)
   - Document what weights actually control
   - If they control strategy *fusion* (combining multiple answers), not retrieval

2. **Add Retrieval Control Flag** (15 min)
   - Add explicit `use_rag` flag to RAG pipeline endpoint
   - Or create separate direct LLM endpoint

3. **Fix Project Isolation** (30 min)
   - Investigate why wrong documents were retrieved
   - Ensure session_id properly scopes retrieval

4. **Test with Better Model** (10 min)
   - Use llama3.2-vision:11b instead of qwen2.5:1.5b
   - Larger model may better extract codes

---

**Test Report Generated**: 2025-11-30 04:15 UTC
**Test File**: `backend/tests/e2e/test_weights_rag_vs_direct_llm.py`
**Results File**: `/tmp/weights_config_test_results.json`
**Logs**: `/tmp/weights_test_run2.log`

**Status**: Tests complete, weights enforcement not validated
**Next Action**: Investigate RAG pipeline weight integration
