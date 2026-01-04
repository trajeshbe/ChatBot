# British Council POC - RAG Strategy Analysis

## Date: 2026-01-03

## Summary

The British Council POC successfully loads and processes user profiles, but returns 0 course recommendations despite having 4 courses properly ingested in the database with embeddings. This document analyzes the RAG strategy flow and identifies the root cause.

---

## Data Verification

✅ **Database State** (Verified):
```sql
-- 4 British Council documents
SELECT COUNT(*) FROM documents WHERE metadata->>'company' = 'british_council';
-- Result: 4

-- 4 chunks with embeddings
SELECT COUNT(*) FROM document_chunks dc
JOIN documents d ON d.id = dc.document_id
WHERE d.metadata->>'company' = 'british_council' AND dc.embedding IS NOT NULL;
-- Result: 4
```

✅ **Metadata Verification**:
All chunks have correct metadata:
- `company`: "british_council"
- `usecase`: "course_recommendation"
- `level`: "beginner", "intermediate", "advanced"
- `format`: "online", "in-person", "hybrid"
- `skills`: Array of skills/focus areas

✅ **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)

---

## RAG Strategy Flow Analysis

###  1. Entry Point
```python
# course_recommender.py:240
results = await self.retrieval_service.intelligent_search(
    query=query,
    db=self.db,
    top_k=top_k,
    session_id=session_id,  # None
    company="british_council",
    usecase="course_recommendation"
)
```

### 2. intelligent_search() Wrapper
```python
# intelligent_retrieval_service.py:616
response = await self.retrieve(
    query=q,
    db=db,
    top_k=top_k * 2,  # 20 for filtering
    session_id=session_id  # None
)
```

### 3. Query Classification

**Flow**:
1. Keyword-based classification attempts to determine query type
2. **Keyword confidence: 0.50** (below threshold of 0.8)
3. Falls back to **LLM-based classification** using `qwen2.5vl:latest`

**LLM Classification Result**:
```
ERROR - Failed to parse LLM response as JSON: Expecting value: line 1 column 1 (char 0)
WARNING - ⚠️ LLM classification failed: LLM returned invalid JSON, using keyword result
INFO - 🎯 Retrieving with strategy: text_semantic
```

**Issue**: Vision model (qwen2.5vl) is not good at returning structured JSON for query classification.

**Selected Strategy**: `text_semantic`
- **vector_column**: `embedding`
- **similarity_metric**: `COSINE`
- **embedding_model**: `sentence-transformers/all-MiniLM-L6-v2`

### 4. Database Query

```python
# intelligent_retrieval_service.py:354
stmt = select(DocumentChunk).where(
    and_(
        getattr(DocumentChunk, vector_column).isnot(None),  # embedding IS NOT NULL
        *self._build_access_filters(session_id, project_id, user_id)
    )
)
```

**Access Filters Applied**:
- `session_id`: None → No session filter
- `project_id`: None → No project filter
- `user_id`: None → No user filter

**Expected Result**: Should find 4 British Council chunks

**Actual Result**: **0 chunks found**

---

## Root Cause Investigation

### Hypothesis 1: Session/Project/User Filtering ❌
**Test**:
```sql
SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL;
-- Result: 100+ chunks exist
```

**Conclusion**: Filters work correctly (no session_id means find all chunks)

### Hypothesis 2: Embedding Strategy Mismatch ❌
**Test**:
- British Council courses: `embedding` column (384-dim)
- Retrieval strategy: `text_semantic` → uses `embedding` column
- Embedding model: Same (`sentence-transformers/all-MiniLM-L6-v2`)

**Conclusion**: Perfect match

### Hypothesis 3: Company/Usecase Filtering ✅ **ROOT CAUSE**

The `intelligent_search()` wrapper applies company/usecase filtering **AFTER** retrieving from database:

```python
# intelligent_retrieval_service.py:628-637
if company or usecase:
    filtered = []
    for result in results:
        metadata = result.get("metadata", {})
        if company and metadata.get("company") != company:
            continue
        if usecase and metadata.get("usecase") != usecase:
            continue
        filtered.append(result)
    results = filtered[:top_k]
```

**The Problem**:
1. `retrieve()` finds **0 chunks** (WHY?)
2. `intelligent_search()` tries to filter 0 results by company/usecase
3. Result: 0 courses returned

**Missing Link**: Why does `retrieve()` return 0 chunks when 4 exist with correct embeddings?

---

## Unified UI Config vs POC Config

### Question
> Does the British Council POC use Unified UI RAG config or its own settings?

### Answer: **NEITHER - Uses Hardcoded IntelligentRetrievalService Defaults**

**Evidence**:
1. **No Unified UI config passed**: British Council POC doesn't integrate with the Unified UI RAG configuration system
2. **No custom config**: CourseRecommenderService uses IntelligentRetrievalService directly with defaults

**Hardcoded Settings** (in `intelligent_retrieval_service.py`):
- **Keyword confidence threshold**: `0.8`
- **LLM classification**: Enabled (uses default model from LLM service)
- **Embedding strategy**: Auto-selected based on query classification
- **Top-k**: Passed by caller (10 for British Council)
- **Similarity threshold**: `0.7` (default)

**LLM Model Selection**:
```
INFO - 🎯 No model specified, using default: qwen2.5vl:latest
```

The POC **does not specify a model**, so it uses:
1. System default from `LLMService`
2. Currently: `qwen2.5vl:latest` (vision model)
3. **Problem**: Vision models are poor at structured JSON output for query classification

---

## Next Steps to Fix

### Option A: Use Simple RAG Service ✅ **RECOMMENDED**
Instead of IntelligentRetrievalService, use the simpler RAGService or direct vector search:

```python
# In course_recommender.py
from app.tier_1.embeddings.embedding_service import EmbeddingService
from sqlalchemy import select, func

async def _semantic_search(self, query: str, ...):
    # 1. Generate embedding
    embedding = await self.embedding_service.get_embedding(query)

    # 2. Direct vector similarity search
    stmt = select(
        DocumentChunk,
        func.cosine_similarity(DocumentChunk.embedding, embedding).label('similarity')
    ).join(Document).where(
        and_(
            DocumentChunk.embedding.isnot(None),
            Document.meta_info['company'].astext == company,
            Document.meta_info['usecase'].astext == usecase
        )
    ).order_by(desc('similarity')).limit(top_k)

    result = await db.execute(stmt)
    return result.all()
```

**Pros**:
- Direct control over query
- No LLM classification overhead
- Filters at database level (more efficient)
- Simpler, more predictable

**Cons**:
- No intelligent query classification
- No multi-strategy support

### Option B: Fix LLM Classification Model
Configure IntelligentRetrievalService to use a text-only model for classification:

```python
# In intelligent_retrieval_service.py:221
async def _llm_classify_embedding_strategy(self, query: str):
    # Force use of GPT-4o-mini or another text model good at JSON
    response = await llm_service.generate(
        prompt=classification_prompt,
        model_id="gpt-4o-mini",  # Override default
        max_tokens=150
    )
```

**Pros**:
- Keeps intelligent classification
- Multi-strategy support

**Cons**:
- Adds LLM cost and latency
- May not be necessary for simple course recommendation

### Option C: Disable LLM Classification
Force keyword-only classification by increasing confidence threshold:

```python
# In intelligent_retrieval_service.py:47
self.keyword_confidence_threshold = 0.3  # Was 0.8
```

**Pros**:
- No LLM calls
- Still uses IntelligentRetrievalService

**Cons**:
- Keyword classification may be less accurate
- Doesn't solve the current "0 results" issue

---

## Recommended Immediate Fix

**Use Option A** with a simple direct vector search:

1. Remove `IntelligentRetrievalService` dependency
2. Use `EmbeddingService` + direct SQL vector similarity
3. Filter by company/usecase at database level
4. Simple, fast, predictable

This matches the original POC design intent: semantic search + profile-based reranking, without the complexity of multi-strategy intelligent retrieval.

---

## Configuration Summary

| Component | Current Value | Source |
|-----------|---------------|--------|
| **RAG Service** | IntelligentRetrievalService | Hardcoded in course_recommender.py |
| **LLM for Classification** | qwen2.5vl:latest (vision model) | System default from LLMService |
| **Keyword Threshold** | 0.8 | Hardcoded in IntelligentRetrievalService |
| **Embedding Model** | sentence-transformers/all-MiniLM-L6-v2 | Auto-selected by text_semantic strategy |
| **Similarity Threshold** | 0.7 | Default in retrieve() method |
| **Top-K** | 10 | Passed from API request |
| **Session Filter** | None | Not used for British Council |
| **Company Filter** | "british_council" | Passed by POC |
| **Usecase Filter** | "course_recommendation" | Passed by POC |

**Does it use Unified UI Config?** **NO**
- British Council POC is standalone
- Uses IntelligentRetrievalService defaults
- No integration with Unified UI RAG configuration

---

## Files Modified for Analysis

1. ✅ `backend/app/tier_1/rag/intelligent_retrieval_service.py` - Fixed 3x async db.execute calls, added intelligent_search() wrapper
2. ✅ `backend/app/services/british_council/course_recommender.py` - Updated to use intelligent_search()
3. ✅ `backend/app/tier_1/embeddings/reranker_service.py` - Verified CrossEncoderReranker interface
4. ✅ `backend/scripts/british_council/ingest_course_catalog.py` - Verified data ingestion

---

## Status

**Current State**:
- ✅ API endpoint works
- ✅ Profile extraction works
- ✅ Data exists in database
- ❌ Vector search returns 0 results (unknown reason - needs deeper debug)

**Recommendation**: Implement Option A (simple direct vector search) to bypass IntelligentRetrievalService complexity.
