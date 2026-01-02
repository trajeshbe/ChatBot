# Infrastructure Reuse Analysis - Merit POCs

> **Purpose:** Map existing infrastructure vs new components needed
> **Date:** 2026-01-02
> **Status:** Pre-implementation analysis

---

## Executive Summary

Our platform already has **extensive infrastructure** that Merit POCs can reuse. We should **extend, not duplicate**.

---

## Existing Infrastructure (Reusable)

### ✅ Tier 1 Core Services

| Component | Location | Status | Reuse for Merit POCs |
|-----------|----------|--------|----------------------|
| **Embedding Service** | `tier_1/embeddings/embedding_service.py` | ✅ Production | All POCs (semantic search) |
| **Reranker Service** | `tier_1/embeddings/reranker_service.py` | ✅ Production | All POCs (+15-25% accuracy) |
| **Document Service** | `tier_1/document_processing/document_service.py` | ✅ Production | All POCs (upload, MinIO) |
| **LLM Service** | `tier_1/llm/llm_service.py` | ✅ Production | All POCs (GPT, Claude, Ollama) |
| **Vision Service** | `tier_1/document_processing/vision_service.py` | ✅ Production | GT Motive, Solera (images) |
| **OCR Service** | `tier_1/document_processing/ocr_service.py` | ✅ Production | Solera (insurance claims) |
| **Hybrid Extraction** | `tier_1/document_processing/hybrid_extraction_service.py` | ✅ Production | All POCs (PDF + tables) |
| **Scraper Service** | `tier_1/data_extraction/scraper_service.py` | ✅ Production | CRU (mining websites) |
| **Template Extraction** | `tier_1/data_extraction/template_extraction_service.py` | ✅ Production | British Council, GT Motive |
| **Export Service** | `tier_1/export/export_service.py` | ✅ Production | All POCs (Excel, PDF) |
| **Evaluation Service** | `tier_1/evaluation/evaluation_service.py` | ✅ Production | All POCs (metrics) |

### ✅ Grant Thornton POC (Reference Implementation)

| Component | Location | Status | Reusable Pattern |
|-----------|----------|--------|------------------|
| **Embedding Service** | `services/grant_thornton/embedding_service.py` | ✅ Working | Inherits from `BaseEmbeddingService` |
| **Retrieval Service** | `services/grant_thornton/retrieval_service.py` | ✅ Working | Uses tier_1 reranker (line 24) |
| **Vector Store** | `services/grant_thornton/vector_store.py` | ✅ Working | In-memory ChromaDB pattern |
| **Extraction Pipeline** | `services/grant_thornton/extraction_pipeline.py` | ✅ Working | LangGraph agent pattern |
| **Excel Exporter** | `services/grant_thornton/excel_exporter.py` | ✅ Working | ReportLab + openpyxl |
| **Calculation Engine** | `services/grant_thornton/calculation_engine.py` | ✅ Working | Financial ratios logic |

**Key Pattern:** Grant Thornton **reuses core tier_1 services** and adds POC-specific logic on top.

---

## New Components Needed (Add to Core)

### 🆕 Multi-Pipeline Infrastructure

These components don't exist yet and are needed for multiple POCs:

| Component | Location (Proposed) | Needed For | Priority |
|-----------|---------------------|------------|----------|
| **Elasticsearch Service** | `tier_1/retrieval/elasticsearch_service.py` | CRU, GT Motive, Solera | P0 |
| **Query Classifier** | `tier_1/retrieval/query_classifier.py` | CRU (hybrid search) | P0 |
| **Multi-Pipeline Router** | `tier_1/retrieval/multi_pipeline_router.py` | CRU (ChromaDB + ES) | P0 |
| **Rank Fusion Service** | `tier_1/retrieval/rank_fusion_service.py` | CRU (RRF) | P0 |
| **Confidence Scorer** | `tier_1/retrieval/confidence_scorer.py` | All POCs (calibration) | P1 |

### 🆕 POC-Specific Components

| Component | Location (Proposed) | Needed For | Priority |
|-----------|---------------------|------------|----------|
| **Profile Analyzer** | `services/british_council/profile_analyzer.py` | British Council | P1 |
| **Course Recommender** | `services/british_council/course_recommender.py` | British Council | P1 |
| **Multi-OCR Fusion** | `tier_1/document_processing/multi_ocr_service.py` | Solera (3 OCR engines) | P1 |
| **VIN Extractor** | `services/solera/vin_extractor.py` | Solera | P1 |
| **Part Code Extractor** | `services/gt_motive/part_code_extractor.py` | GT Motive | P1 |
| **Custom NER Trainer** | `tier_1/nlp_processing/custom_ner_service.py` | Construction Monitor | P2 |
| **Knowledge Graph Builder** | `services/construction_monitor/kg_builder.py` | Construction Monitor | P2 |

---

## Recommended Implementation Strategy

### Phase 1: Extend Core Retrieval (Week 1)

Add to `backend/app/tier_1/retrieval/` (new folder):

```
tier_1/retrieval/
├── __init__.py
├── elasticsearch_service.py      # NEW: Keyword search backend
├── query_classifier.py            # NEW: LLM-based classification
├── multi_pipeline_router.py       # NEW: Route to ChromaDB/ES/Hybrid
├── rank_fusion_service.py         # NEW: RRF for combining results
└── confidence_scorer.py           # NEW: Calibrated confidence
```

**Why `tier_1/retrieval/`?**
- Reusable across ALL Merit POCs
- Complements existing `tier_1/embeddings/` folder
- Natural home for multi-pipeline logic

### Phase 2: Implement British Council POC (Week 2)

Create `backend/app/services/british_council/`:

```
services/british_council/
├── __init__.py
├── profile_analyzer.py            # LLM-based profile extraction
├── course_recommender.py          # Hybrid semantic + rule-based
└── api_routes.py                  # FastAPI endpoints
```

**Reuses:**
- `tier_1/embeddings/embedding_service.py` (semantic search)
- `tier_1/embeddings/reranker_service.py` (course re-ranking)
- `tier_1/llm/llm_service.py` (profile analysis)
- `tier_1/retrieval/confidence_scorer.py` (recommendation confidence)

### Phase 3: Implement CRU POC (Week 3)

Create `backend/app/services/cru/`:

```
services/cru/
├── __init__.py
├── cru_query_service.py           # Multi-pipeline query handling
└── api_routes.py                  # FastAPI endpoints
```

**Reuses:**
- `tier_1/retrieval/elasticsearch_service.py` (keyword search)
- `tier_1/retrieval/query_classifier.py` (semantic vs keyword vs hybrid)
- `tier_1/retrieval/multi_pipeline_router.py` (routing logic)
- `tier_1/retrieval/rank_fusion_service.py` (RRF)
- `tier_1/embeddings/reranker_service.py` (final re-ranking)

---

## Code Reuse Matrix

| POC | Core Reuse % | Tier 1 Components Reused | New Components |
|-----|--------------|--------------------------|----------------|
| **Grant Thornton** | Baseline | Embedding, Reranker, Document, LLM, Export | 6 GT-specific |
| **British Council** | 80% | Embedding, Reranker, LLM, Confidence | 2 BC-specific |
| **CRU** | 75% | Embedding, Reranker, ES, Query Classifier, Router, RRF | 1 CRU-specific |
| **GT Motive** | 60% | Vision, Embedding, Reranker, ES, LLM | 3 GTM-specific |
| **Solera** | 65% | OCR, Vision, Multi-OCR, ES, Reranker | 3 Solera-specific |
| **Construction Monitor** | 50% | NER (custom), Embedding, Reranker, LLM | 4 CM-specific |

---

## Migration Plan

### Step 1: Create tier_1/retrieval/ folder

```bash
mkdir -p backend/app/tier_1/retrieval
```

### Step 2: Move/enhance existing reranker (OPTIONAL)

Current: `tier_1/embeddings/reranker_service.py`

**Decision:** Keep it there OR move to `tier_1/retrieval/` for consistency.

**Recommendation:** KEEP in `embeddings/` (it's already production-ready).

### Step 3: Add new retrieval components

Implement in `tier_1/retrieval/`:
1. `elasticsearch_service.py` - Elasticsearch client wrapper
2. `query_classifier.py` - LLM-based classification
3. `multi_pipeline_router.py` - Route to pipelines
4. `rank_fusion_service.py` - RRF implementation
5. `confidence_scorer.py` - Calibrated confidence

### Step 4: Update docker-compose.yml

Add Elasticsearch service:

```yaml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
```

### Step 5: Implement POCs sequentially

1. British Council (reuses tier_1 + Elasticsearch)
2. CRU (reuses tier_1 + multi-pipeline)
3. GT Motive (reuses tier_1 + Vision + ES)
4. Solera (reuses tier_1 + Multi-OCR)
5. Construction Monitor (reuses tier_1 + custom NER)

---

## Summary

### What We Already Have ✅
- Embedding service (BAAI/bge-large-en-v1.5)
- **Reranker service (BAAI/bge-reranker-large)** ← KEY FINDING
- Document service (MinIO, PDF, etc.)
- LLM service (GPT, Claude, Ollama)
- Vision service (Claude 3.5)
- OCR service (Tesseract, etc.)
- Export service (Excel, PDF)
- Grant Thornton reference implementation

### What We Need to Add 🆕
- Elasticsearch integration
- Query classification
- Multi-pipeline routing
- Rank fusion (RRF)
- Confidence scoring
- POC-specific services (British Council, CRU, etc.)

### Key Principle
**Extend `tier_1/`, don't create `infrastructure/`**

Grant Thornton already demonstrated the pattern:
- Inherit from tier_1 base services
- Add POC-specific logic
- Reuse shared components

---

## Next Steps

1. ✅ Delete `backend/app/services/infrastructure/` (incorrectly created)
2. 🔄 Create `backend/app/tier_1/retrieval/` with new components
3. 🔄 Implement British Council POC (first Tier 1 POC)
4. 🔄 Implement CRU POC (first multi-pipeline POC)

---

**Status:** Analysis complete, ready to implement with proper reuse
