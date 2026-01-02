# Infrastructure Gap Analysis - Merit POCs

> **Purpose:** Comprehensive audit of existing platform capabilities vs. Merit POC requirements
> **Date:** 2026-01-02
> **Findings:** Platform has 90% of needed infrastructure - only 3 components missing

---

## Executive Summary

After auditing the existing platform, **we already have most infrastructure components**:

- ✅ **13 core services** ready to reuse
- ✅ **LLM-based query classifier** (production-ready)
- ✅ **Intelligent retrieval** with multi-column vector search
- ✅ **Multi-strategy RAG** with answer fusion
- ✅ **Reranker service** (BAAI/bge-reranker-large)
- ✅ **pgvector database** with multiple embedding columns

**Missing Components (3):**
- ❌ Elasticsearch integration
- ❌ Rank Fusion Service (RRF)
- ❌ Multi-pipeline router (ES + ChromaDB)

---

## Detailed Audit

### ✅ EXISTING Infrastructure (Reusable)

#### 1. Query Classification & Routing

| Component | Location | Status | Capabilities |
|-----------|----------|--------|--------------|
| **Query Classifier** | `tier_1/nlp_processing/query_classifier.py` | ✅ Production | LLM-based classification (ai_personal, document_specific, general, ambiguous) |
| **Dynamic Query Classifier** | `tier_1/nlp_processing/dynamic_query_classifier.py` | ✅ Production | Dynamic routing based on query intent |
| **Query Reformulation** | `tier_1/rag/query_reformulation_service.py` | ✅ Production | Query expansion and rewriting |

**Example Usage:**
```python
from app.tier_1.nlp_processing.query_classifier import QueryClassifier

classifier = QueryClassifier(llm_service)
result = await classifier.classify(
    query="Tell me about Aadhan",
    session_id="xyz"
)
# Returns: {
#   "query_type": "ambiguous",
#   "use_documents": true,
#   "confidence": 0.85
# }
```

#### 2. Retrieval Services

| Component | Location | Status | Capabilities |
|-----------|----------|--------|--------------|
| **Intelligent Retrieval** | `tier_1/rag/intelligent_retrieval_service.py` | ✅ Production | Query-time strategy matching (text, table, visual, code, numerical) |
| **Multi-Strategy RAG** | `tier_1/rag/multi_strategy_rag.py` | ✅ Production | Answer fusion from multiple strategies (short-term, long-term, tools) |
| **RAG Pipeline** | `tier_1/rag/pipeline/` | ✅ Production | Complete RAG pipeline (embeddings, retrieval, reranking, caching) |

**Example Usage:**
```python
from app.tier_1.rag.intelligent_retrieval_service import IntelligentRetrievalService

retrieval = IntelligentRetrievalService()

# Automatically classifies query and routes to appropriate vector column
results = await retrieval.intelligent_search(
    db=db,
    query="Show me the table with iron ore grades",
    top_k=10,
    session_id="xyz"
)
# Searches in table_embedding column + reranks
```

#### 3. Re-ranking

| Component | Location | Status | Capabilities |
|-----------|----------|--------|--------------|
| **Reranker Service** | `tier_1/embeddings/reranker_service.py` | ✅ Production | BAAI/bge-reranker-large cross-encoder (+15-25% accuracy) |
| **Pipeline Reranker** | `tier_1/rag/pipeline/reranker.py` | ✅ Production | Integrated pipeline component |

**Models Supported:**
- `fast`: cross-encoder/ms-marco-MiniLM-L-6-v2 (80MB)
- `balanced`: BAAI/bge-reranker-base (279MB)
- `accurate`: BAAI/bge-reranker-large (560MB) ← Default

#### 4. Embedding & Vector Storage

| Component | Location | Status | Capabilities |
|-----------|----------|--------|--------------|
| **Embedding Service** | `tier_1/embeddings/embedding_service.py` | ✅ Production | BAAI/bge-large-en-v1.5 (1024-dim) |
| **Intelligent Embedding** | `tier_1/embeddings/intelligent_embedding_service.py` | ✅ Production | Multi-column embeddings (text, table, visual, code, numerical) |
| **pgvector Database** | `models/database.py` | ✅ Production | PostgreSQL + pgvector extension |

**Database Schema:**
```sql
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY,
    content TEXT,
    embedding VECTOR(1024),           -- Text embeddings
    table_embedding VECTOR(1024),     -- Table structure embeddings
    visual_embedding VECTOR(1024),    -- Image/diagram embeddings
    code_embedding VECTOR(1024),      -- Code embeddings
    numerical_embedding VECTOR(1024), -- Statistical embeddings
    ...
);

-- Indexes for fast cosine similarity search
CREATE INDEX idx_chunks_embedding ON document_chunks
USING ivfflat (embedding vector_cosine_ops);
```

#### 5. LLM Services

| Component | Location | Status | Capabilities |
|-----------|----------|--------|--------------|
| **LLM Service** | `tier_1/llm/llm_service.py` | ✅ Production | GPT-4, Claude 3.5, Ollama models |
| **Vision Service** | `tier_1/document_processing/vision_service.py` | ✅ Production | Claude 3.5 Sonnet for image analysis |
| **OCR Service** | `tier_1/document_processing/ocr_service.py` | ✅ Production | Tesseract, PaddleOCR, EasyOCR |

#### 6. Document Processing

| Component | Location | Status | Capabilities |
|-----------|----------|--------|--------------|
| **Document Service** | `tier_1/document_processing/document_service.py` | ✅ Production | Upload, chunking, MinIO storage |
| **Hybrid Extraction** | `tier_1/document_processing/hybrid_extraction_service.py` | ✅ Production | PDF + table extraction |
| **Content Analyzer** | `tier_1/document_processing/content_analyzer.py` | ✅ Production | Detect content type (text, table, code, etc.) |

#### 7. Export & Utilities

| Component | Location | Status | Capabilities |
|-----------|----------|--------|--------------|
| **Export Service** | `tier_1/export/export_service.py` | ✅ Production | Excel, PDF, JSON export |
| **Evaluation Service** | `tier_1/evaluation/evaluation_service.py` | ✅ Production | RAG metrics (precision, recall, F1) |

---

### ❌ MISSING Infrastructure (Need to Build)

#### 1. Elasticsearch Service

**Status:** ❌ Not found in codebase

**Required For:** CRU, GT Motive, Solera (keyword search + filters)

**Proposed Location:** `tier_1/rag/elasticsearch_service.py`

**Functionality:**
- BM25 keyword search
- Field filters (document_type, year, etc.)
- Index management
- Bulk indexing

**Estimated Effort:** 4-6 hours

#### 2. Rank Fusion Service (RRF)

**Status:** ❌ Not implemented

**Required For:** CRU (combining ChromaDB + Elasticsearch results)

**Proposed Location:** `tier_1/rag/rank_fusion_service.py`

**Functionality:**
- Reciprocal Rank Fusion (RRF)
- Configurable k parameter (default: 60)
- Weighted fusion (configurable per source)
- Source attribution

**Estimated Effort:** 2-3 hours

#### 3. Confidence Scorer

**Status:** ❌ Not implemented (basic confidence exists in multi_strategy_rag.py but not calibrated)

**Required For:** All POCs (answer reliability)

**Proposed Location:** `tier_1/rag/confidence_scorer.py`

**Functionality:**
- Feature-based scoring (embedding score, reranker score, num docs, answer length)
- Calibrated confidence intervals
- Per-POC calibration curves

**Estimated Effort:** 3-4 hours

---

## Gap Summary

| Category | Existing | Missing | Reuse % |
|----------|----------|---------|---------|
| **Query Classification** | ✅ Complete | None | 100% |
| **Retrieval (pgvector)** | ✅ Complete | None | 100% |
| **Retrieval (Elasticsearch)** | ❌ None | Full implementation | 0% |
| **Re-ranking** | ✅ Complete | None | 100% |
| **Rank Fusion** | ❌ None | RRF implementation | 0% |
| **Confidence Scoring** | ⚠️ Basic | Calibrated scorer | 30% |
| **LLM Services** | ✅ Complete | None | 100% |
| **Document Processing** | ✅ Complete | None | 100% |
| **Export** | ✅ Complete | None | 100% |

**Overall Platform Reuse:** ~90% (only 3 missing components)

---

## Recommended Implementation Plan

### Phase 1: Add Missing Core Components (1-2 days)

**Location:** `backend/app/tier_1/rag/`

1. **elasticsearch_service.py** (4-6 hours)
   - Async Elasticsearch client
   - Index management
   - BM25 search with filters
   - Bulk indexing

2. **rank_fusion_service.py** (2-3 hours)
   - RRF implementation
   - Weighted fusion
   - Source attribution

3. **confidence_scorer.py** (3-4 hours)
   - Feature extraction
   - Calibrated scoring
   - Interval mapping

**Total Effort:** 9-13 hours (~1.5 days)

### Phase 2: Docker Compose Updates (1 hour)

Add Elasticsearch service:

```yaml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - app_network

volumes:
  elasticsearch_data:
```

### Phase 3: Implement POCs (Reuse Existing Infrastructure)

#### British Council POC (3-4 days)
**Reuses:** Query classifier, intelligent retrieval, reranker, LLM, export

**New:**
- `services/british_council/profile_analyzer.py` (1 day)
- `services/british_council/course_recommender.py` (2 days)
- `services/british_council/api_routes.py` (0.5 day)

#### CRU POC (4-5 days)
**Reuses:** Query classifier, intelligent retrieval, ES, rank fusion, reranker, confidence

**New:**
- `services/cru/cru_query_service.py` (2 days) - Multi-pipeline orchestration
- `services/cru/api_routes.py` (0.5 day)
- A/B testing logic (1 day)
- Dashboard (1 day)

---

## Migration from Implementation Plans

The implementation plans created earlier assumed we needed to build everything from scratch. Based on this audit:

### Original Plan Updates

| Original Component | Actual Status | Action Required |
|-------------------|---------------|-----------------|
| **Re-ranker Service** | ✅ Exists | Reuse `tier_1/embeddings/reranker_service.py` |
| **Query Classifier** | ✅ Exists | Reuse `tier_1/nlp_processing/query_classifier.py` |
| **Intelligent Retrieval** | ✅ Exists | Reuse `tier_1/rag/intelligent_retrieval_service.py` |
| **Multi-Pipeline Router** | ⚠️ Partial | Extend existing intelligent retrieval for ES |
| **Elasticsearch Service** | ❌ Missing | Build new `tier_1/rag/elasticsearch_service.py` |
| **Rank Fusion** | ❌ Missing | Build new `tier_1/rag/rank_fusion_service.py` |
| **Confidence Scorer** | ⚠️ Basic | Enhance to `tier_1/rag/confidence_scorer.py` |

---

## Example: British Council POC (Simplified)

**Old Implementation Plan (from scratch):**
- Build query classifier ❌
- Build retrieval service ❌
- Build reranker ❌
- Build LLM integration ❌
- Build profile analyzer ✅
- Build course recommender ✅

**New Implementation Plan (reuse existing):**
- ✅ Reuse `QueryClassifier` for query intent
- ✅ Reuse `IntelligentRetrievalService` for course search
- ✅ Reuse `CrossEncoderReranker` for course ranking
- ✅ Reuse `LLMService` for profile analysis
- 🆕 Build `ProfileAnalyzer` (1 day)
- 🆕 Build `CourseRecommender` (2 days)

**Effort Reduction:** From ~10 days to ~3 days (70% reduction)

---

## Next Steps

1. ✅ **Delete** `backend/app/services/infrastructure/` (already done)
2. 🔄 **Build** 3 missing components in `tier_1/rag/`:
   - `elasticsearch_service.py`
   - `rank_fusion_service.py`
   - `confidence_scorer.py`
3. 🔄 **Update** `docker-compose.yml` with Elasticsearch
4. 🔄 **Implement** British Council POC (reuse 80%+)
5. 🔄 **Implement** CRU POC (reuse 75%+)

---

## Conclusion

The platform already has **extensive infrastructure** that Merit POCs can leverage:

- ✅ LLM-based query classification
- ✅ Intelligent multi-column retrieval (pgvector)
- ✅ Cross-encoder re-ranking (BAAI models)
- ✅ Multi-strategy RAG with answer fusion
- ✅ Complete document processing pipeline
- ✅ Vision, OCR, and export services

**We only need to add:**
- Elasticsearch integration (keyword search)
- Rank Fusion Service (RRF)
- Calibrated confidence scorer

This brings total development effort from **~14 weeks** (original estimate) to **~6-8 weeks** (with reuse).

---

**Status:** Ready to implement missing components and POCs
**Recommendation:** Build 3 missing components first, then implement POCs sequentially
