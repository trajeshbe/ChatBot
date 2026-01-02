# Merit POC Implementation Plans - Summary

> **Created:** 2026-01-02
> **Status:** Planning Complete - Ready for Implementation
> **Total POCs:** 6 (1 Completed + 5 Planned)

---

## Executive Summary

This document provides a comprehensive overview of all Merit customer POC implementation plans. All POCs leverage a **shared infrastructure** to maximize code reuse and minimize development effort.

### Completion Status

| POC | Status | Priority | Code Reuse | Effort | Timeline |
|-----|--------|----------|------------|--------|----------|
| **Grant Thornton** | ✅ **Complete** | Tier 1 | Baseline | 3 weeks | Complete |
| **British Council** | 📋 **Planned** | Tier 1 | 80% | 3 weeks | Jan 2-22, 2026 |
| **CRU** | 📋 **Planned** | Tier 1 | 75% | 3 weeks | Jan 2-22, 2026 |
| **GT Motive** | 📋 **Planned** | Tier 2 | 60% | 4 weeks | Jan 2-29, 2026 |
| **Solera** | 📋 **Planned** | Tier 2 | 65% | 3 weeks | Jan 2-22, 2026 |
| **Construction Monitor** | 📋 **Planned** | Tier 3 | 50% | 5 weeks | Jan 2-Feb 5, 2026 |

### Key Infrastructure Components

| Component | Purpose | Used By POCs |
|-----------|---------|--------------|
| **Re-ranker (BAAI/bge-reranker-large)** | +15-20% precision improvement | All POCs |
| **Elasticsearch** | Keyword search | CRU, GT Motive, Solera, Construction Monitor |
| **Multi-Pipeline Router** | Semantic vs keyword routing | CRU, GT Motive |
| **Rank Fusion (RRF)** | Combine multiple retrieval sources | CRU, GT Motive |
| **Confidence Scorer** | Calibrated confidence intervals | CRU, Grant Thornton |

---

## 1. Grant Thornton POC (✅ Complete)

### Overview
**Customer:** Grant Thornton (Financial Services)
**Use Case:** Automated financial datapoint extraction from annual reports
**Technology:** RAG + LLM Agent + BAAI Reranker + Excel Export

### Key Features
- 50+ financial datapoints extracted (balance sheet, P&L, cash flow)
- Sub-calculations (e.g., Average Total Equity, DSO, DIO)
- 13 financial ratios (liquidity, leverage, profitability, efficiency)
- Excel export with all extracted data
- MinIO storage with organizational hierarchy

### Success Metrics (Achieved)
- ✅ 15/15 datapoints extracted (100% for olympic_management test)
- ✅ 11/13 financial ratios calculated (85% success rate)
- ✅ Excel export working
- ✅ Formula normalization fixed
- ✅ Processing time: ~112 seconds per annual report

### Architecture
```
PDF Upload → Docling Extraction → ChromaDB Storage →
RAG Retrieval (MMR) → Reranker → LLM Agent →
Datapoint Extraction → Formula Calculation → Excel Export
```

### Location
- **Implementation Plan:** Already implemented (✅ Complete)
- **Backend:** `backend/app/services/grant_thornton/`
- **Frontend:** `frontend/src/components/GrantThorntonExtraction.tsx`

---

## 2. British Council POC (📋 Planned)

### Overview
**Customer:** British Council (Education)
**Use Case:** Course recommendation RAG system
**Technology:** Semantic Search + Profile Analysis + LLM + Azure Bot Framework

### Key Features
- User profile analysis (skills, interests, education level, career goals)
- Course recommendations (semantic + rule-based scoring)
- Chatbot integration (Azure Bot Framework for Teams/Web)
- Multi-step profile builder UI
- Course catalog with 100+ courses

### Code Reuse: 80%
- ✅ Embedding Service (BAAI/bge-large-en-v1.5)
- ✅ Vector Store (ChromaDB)
- ✅ Retrieval Service + MMR
- ✅ Reranker Service (BAAI/bge-reranker-large)
- ✅ LLM Service (GPT-4o-mini)
- ✅ Document Service
- ✅ Excel Export (adapted from Grant Thornton)

### New Components (20%)
- Profile Analyzer Service (LLM-based)
- Course Recommender Service (hybrid scoring)
- Azure Bot Framework Connector
- Course Browser UI

### Timeline: 3 weeks
- **Week 1:** Profile analyzer + course recommender core
- **Week 2:** Azure Bot integration + frontend components
- **Week 3:** Testing + optimization

### Architecture
```
User Profile Input → Profile Analyzer (LLM) →
Semantic Query Builder → ChromaDB Search →
Reranker → Profile Scoring (rules) →
Top 10 Courses + Reasons
```

### Location
- **Plan:** `backend/docs/poc_implementation_plans/01_british_council_implementation_plan.md`

---

## 3. CRU POC (📋 Planned)

### Overview
**Customer:** CRU (Mining Intelligence)
**Use Case:** Mining document intelligence with multi-pipeline RAG
**Technology:** ChromaDB + Elasticsearch + Hybrid Fusion + Reranker

### Key Features
- Multi-pipeline comparison (ChromaDB vs Elasticsearch vs Hybrid)
- A/B testing framework for pipeline performance
- Confidence scoring with calibration
- Document Q&A for mining reports, feasibility studies, geological surveys
- Knowledge extraction (capex, opex, commodity prices, grades)

### Code Reuse: 75%
- ✅ Embedding Service
- ✅ Retrieval Service (ChromaDB)
- ✅ Reranker Service
- ✅ LLM Service
- ✅ Document Service
- ✅ MinIO Path Builder

### New Components (25%)
- Elasticsearch Service (NEW - shared infrastructure)
- Multi-Pipeline Router (NEW - shared infrastructure)
- Rank Fusion Service (RRF) (NEW - shared infrastructure)
- Confidence Scorer (NEW - shared infrastructure)
- CRU Query Service (orchestrator)

### Timeline: 3 weeks
- **Week 1:** Elasticsearch setup + integration
- **Week 2:** Multi-pipeline logic (router, fusion, confidence)
- **Week 3:** Testing + UI + benchmarking

### Architecture
```
Query → Classifier (semantic/keyword/hybrid) →
[PARALLEL]
├─ ChromaDB Search (top 20)
└─ Elasticsearch Search (top 20)
↓
RRF Fusion (top 20) → Reranker (top 5) →
Confidence Scorer → LLM Synthesis
```

### Location
- **Plan:** `backend/docs/poc_implementation_plans/02_cru_implementation_plan.md`

---

## 4. Infrastructure: Re-Ranking & Multi-Pipeline (📋 Planned)

### Overview
**Purpose:** Shared infrastructure for all Merit POCs
**Components:** BAAI Reranker, Elasticsearch, Multi-Pipeline Router, Query Classifier, Confidence Scorer

### Key Benefits
- **+15-20% precision** improvement with reranker
- **Flexible routing** (semantic, keyword, hybrid)
- **Shared models** (one reranker instance, all POCs)
- **Observable** (metrics at each stage)
- **Extensible** (easy to add new pipelines)

### Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Re-ranker** | BAAI/bge-reranker-large | Cross-encoder precision boost |
| **Elasticsearch** | Elasticsearch 8.x | Keyword search backend |
| **Query Classifier** | LLM-based | Classify query type (semantic/keyword/hybrid) |
| **Multi-Pipeline Router** | Python service | Route to optimal pipeline(s) |
| **Rank Fusion** | RRF (k=60) | Combine ChromaDB + Elasticsearch |
| **Confidence Scorer** | Feature-based | Calibrated confidence intervals |

### Timeline: 1-2 weeks
- **Week 1:** Elasticsearch setup, reranker deployment
- **Week 2:** Multi-pipeline router, testing

### Location
- **Plan:** `backend/docs/poc_implementation_plans/03_infrastructure_reranking_multipipeline.md`

---

## 5. GT Motive POC (📋 Planned)

### Overview
**Customer:** GT Motive (Automotive Parts)
**Use Case:** Multi-modal part code extraction (Vision + NLP)
**Technology:** Claude Vision + OCR + Elasticsearch + Reranker

### Key Features
- Text-based part code extraction (PDF catalogs with tables)
- Diagram part code extraction (exploded views with callouts)
- Vehicle model mapping (part codes → BMW/Mercedes/Audi models)
- Multi-modal processing (text + images)
- Excel catalog export

### Code Reuse: 60%
- ✅ Docling Analyzer (PDF + tables)
- ✅ Vision Service (Claude 3.5 Sonnet)
- ✅ OCR Service (Tesseract + PaddleOCR)
- ✅ Embedding Service
- ✅ Elasticsearch Service (infrastructure)
- ✅ Reranker Service (infrastructure)
- ✅ Excel Export (Grant Thornton)

### New Components (40%)
- Part Code Extractor (regex + LLM)
- Vehicle Model Mapper (LLM-based)
- Diagram Analyzer (vision model)
- Hybrid Search (ChromaDB + Elasticsearch)

### Timeline: 4 weeks
- **Week 1-2:** Part code extractor + table extraction
- **Week 3:** Diagram analyzer (Claude Vision)
- **Week 4:** Testing + UI + Excel export

### Architecture
```
[TEXT PIPELINE]
PDF Catalog → Docling → Table Extraction →
Part Code Regex → LLM Description Extraction

[VISION PIPELINE]
Diagram Image → Claude Vision →
Callout Mapping → Part Code Extraction

[SEARCH]
Hybrid (ChromaDB + Elasticsearch) → Reranker →
Top 10 Part Codes + Descriptions
```

### Location
- **Plan:** `backend/docs/poc_implementation_plans/04_gt_motive_implementation_plan.md`

---

## 6. Solera POC (📋 Planned)

### Overview
**Customer:** Solera (Insurance & Auto Claims)
**Use Case:** OCR + part code extraction from claims photos
**Technology:** Multi-OCR (PaddleOCR + Tesseract + EasyOCR) + NHTSA VIN API + Elasticsearch

### Key Features
- Multi-OCR pipeline (PaddleOCR, Tesseract, EasyOCR) with confidence-based fusion
- VIN extraction + validation (NHTSA API)
- Part code detection from photos
- Damage classification (minor, moderate, severe, total loss)
- Claims report generation (PDF)

### Code Reuse: 65%
- ✅ OCR Service (Tesseract + PaddleOCR)
- ✅ OpenCV Service (image preprocessing)
- ✅ Document Service
- ✅ LLM Service (damage assessment)
- ✅ Elasticsearch Service (infrastructure)
- ✅ Reranker Service (infrastructure)
- ✅ Part Code Extractor (GT Motive adaptation)

### New Components (35%)
- Multi-OCR Service (parallel execution + fusion)
- VIN Extractor + Validator (NHTSA API)
- Damage Classifier (LLM-based)
- Claims Report Generator (ReportLab PDF)

### Timeline: 3 weeks
- **Week 1:** Multi-OCR service + image preprocessing
- **Week 2:** VIN extractor + damage classifier
- **Week 3:** Claims report generator + testing

### Architecture
```
Claims Photo → Image Preprocessing (OpenCV) →
[PARALLEL]
├─ PaddleOCR
├─ Tesseract
└─ EasyOCR
↓
OCR Fusion (confidence-based) → [PARALLEL]
├─ VIN Extraction → NHTSA Validation
├─ Part Code Extraction → Elasticsearch Search
└─ Damage Classification (LLM)
↓
Claims Report (PDF)
```

### Location
- **Plan:** `backend/docs/poc_implementation_plans/05_solera_implementation_plan.md`

---

## 7. Construction Monitor POC (📋 Planned)

### Overview
**Customer:** Construction Monitor
**Use Case:** Custom NER/REL for construction document intelligence
**Technology:** SpaCy NER + Relation Extraction + Neo4j Knowledge Graph

### Key Features
- Custom Named Entity Recognition (8 entity types: PROJECT, CONTRACTOR, MATERIAL, QUANTITY, COST, DATE, MILESTONE, LOCATION)
- Relation Extraction (6 relation types: HAS_CONTRACTOR, USES_MATERIAL, LOCATED_AT, HAS_COST, DUE_ON, SUPPLIES)
- Knowledge Graph (Neo4j) with Cypher queries
- Hybrid RAG (semantic + keyword + graph)
- Document Q&A with entity context

### Code Reuse: 50%
- ✅ Docling Analyzer (PDF + tables)
- ✅ OCR Service (blueprints)
- ✅ Embedding Service
- ✅ Retrieval Service (ChromaDB)
- ✅ Elasticsearch Service (infrastructure)
- ✅ Reranker Service (infrastructure)
- ✅ LLM Service

### New Components (50%)
- Custom NER Model (SpaCy training)
- NER Inference Service
- Relation Extractor
- Knowledge Graph Builder (Neo4j)
- Construction Q&A Service (hybrid search)

### Timeline: 5 weeks
- **Week 1:** NER model training (annotated construction docs)
- **Week 2:** Relation extraction implementation
- **Week 3:** Neo4j integration + knowledge graph
- **Week 4-5:** Q&A service + testing + frontend

### Architecture
```
Construction Doc → Docling → NER (SpaCy) →
Relation Extraction → Knowledge Graph (Neo4j)
↓
[Q&A Flow]
Question → NER → Cypher Query (Neo4j) →
[PARALLEL]
├─ Graph Results (structured)
└─ Semantic Search (ChromaDB)
↓
LLM Synthesis (graph + context)
```

### Location
- **Plan:** `backend/docs/poc_implementation_plans/06_construction_monitor_implementation_plan.md`

---

## Code Reuse Matrix

| POC | Core Platform | Infrastructure | Previous POCs | New Code |
|-----|---------------|----------------|---------------|----------|
| **Grant Thornton** | 70% | 0% | 0% | 30% |
| **British Council** | 70% | 10% | 0% | 20% |
| **CRU** | 60% | 15% | 0% | 25% |
| **GT Motive** | 50% | 10% | 10% (Grant Thornton Excel) | 30% |
| **Solera** | 50% | 10% | 15% (GT Motive parts, Grant Thornton Excel) | 25% |
| **Construction Monitor** | 40% | 10% | 0% | 50% |

### Reusable Components Breakdown

**From Core Platform (Existing):**
- Document Service (upload, MinIO storage)
- Embedding Service (BAAI/bge-large-en-v1.5)
- Retrieval Service (ChromaDB, MMR)
- LLM Service (OpenAI, Claude, Ollama)
- Vision Service (Claude 3.5 Sonnet)
- OCR Service (Tesseract, PaddleOCR, EasyOCR)
- OpenCV Service (image preprocessing)
- Docling Analyzer (PDF + table extraction)
- MinIO Path Builder (organizational paths)

**From Infrastructure (NEW - Shared Across POCs):**
- Re-ranker Service (BAAI/bge-reranker-large)
- Elasticsearch Service (keyword search)
- Multi-Pipeline Router (query classifier + routing)
- Rank Fusion Service (RRF)
- Confidence Scorer (calibrated probabilities)

**From Grant Thornton (Reusable):**
- Excel Export Service (openpyxl)
- Formula Normalization
- Datapoint Extraction Pattern

**From GT Motive (Reusable):**
- Part Code Extractor
- Vehicle Model Mapper

---

## Implementation Priority & Dependencies

### Phase 1: Foundation (Weeks 1-2)
**Infrastructure Setup**
- Deploy Elasticsearch
- Implement Re-ranker Service
- Implement Multi-Pipeline Router
- Implement Rank Fusion Service
- Implement Confidence Scorer

**Dependencies:** None (standalone)
**Effort:** 1-2 weeks
**Benefits:** All future POCs

### Phase 2: Tier 1 POCs (Weeks 2-5)
**British Council + CRU (Parallel)**
- British Council: Profile analyzer, course recommender, Azure Bot
- CRU: Multi-pipeline orchestrator, mining document Q&A

**Dependencies:** Infrastructure (Elasticsearch, Reranker)
**Effort:** 3 weeks each (can run in parallel)
**Benefits:** High ROI, 75-80% code reuse

### Phase 3: Tier 2 POCs (Weeks 5-9)
**GT Motive + Solera (Parallel)**
- GT Motive: Part code extractor, diagram analyzer, vehicle mapper
- Solera: Multi-OCR, VIN extractor, damage classifier

**Dependencies:** Infrastructure + Grant Thornton (Excel export)
**Effort:** 4 weeks (GT Motive), 3 weeks (Solera)
**Benefits:** Medium ROI, 60-65% code reuse

### Phase 4: Tier 3 POC (Weeks 9-14)
**Construction Monitor**
- Custom NER training
- Relation extraction
- Neo4j knowledge graph
- Construction Q&A

**Dependencies:** Infrastructure
**Effort:** 5 weeks
**Benefits:** Most complex, 50% code reuse, showcases advanced ML

---

## Technology Stack Summary

| Technology | Used In POCs | Purpose |
|------------|-------------|---------|
| **BAAI/bge-large-en-v1.5** | All | Embeddings (1024-dim) |
| **BAAI/bge-reranker-large** | All | Re-ranking for precision |
| **ChromaDB** | All | Vector database |
| **Elasticsearch** | CRU, GT Motive, Solera, Construction Monitor | Keyword search |
| **Neo4j** | Construction Monitor | Knowledge graph |
| **GPT-4o-mini** | All | LLM synthesis |
| **Claude 3.5 Sonnet Vision** | GT Motive | Diagram analysis |
| **Docling** | All (PDF-based) | PDF + table extraction |
| **PaddleOCR** | GT Motive, Solera | OCR for photos/diagrams |
| **Tesseract/EasyOCR** | GT Motive, Solera, Construction Monitor | Backup OCR |
| **SpaCy 3.x** | Construction Monitor | Custom NER |
| **Azure Bot Framework** | British Council | Chatbot integration |
| **ReportLab** | Solera | PDF report generation |
| **FastAPI + Pydantic** | All | Backend framework |
| **React + TypeScript** | All | Frontend framework |
| **MinIO** | All | Object storage |
| **PostgreSQL + pgvector** | All | Database |

---

## Estimated Total Effort

| Phase | POCs | Weeks | Team Size | Total Person-Weeks |
|-------|------|-------|-----------|-------------------|
| **Phase 1: Infrastructure** | N/A | 2 | 2 developers | 4 person-weeks |
| **Phase 2: Tier 1** | British Council, CRU | 3 | 2 developers | 6 person-weeks (parallel) |
| **Phase 3: Tier 2** | GT Motive, Solera | 4 | 2 developers | 8 person-weeks (parallel) |
| **Phase 4: Tier 3** | Construction Monitor | 5 | 1-2 developers | 5-10 person-weeks |
| **Total** | 5 POCs + Infrastructure | **14 weeks** | **2 developers** | **23-28 person-weeks** |

**Timeline:** **~3.5 months** (with 2 developers working in parallel where possible)

---

## Success Metrics

### Per-POC Metrics

| POC | Accuracy Target | Response Time | Success Rate |
|-----|----------------|---------------|--------------|
| **Grant Thornton** | 95% datapoint extraction | <120s | ✅ 100% (15/15) |
| **British Council** | 85% course match satisfaction | <3s | Pending |
| **CRU** | 90% retrieval precision | <5s | Pending |
| **GT Motive** | 95% part code extraction | <5s | Pending |
| **Solera** | 90% OCR accuracy, 95% VIN | <3s | Pending |
| **Construction Monitor** | 90% NER F1, 85% REL F1 | <5s | Pending |

### Infrastructure Metrics

| Component | Target |
|-----------|--------|
| **Re-ranker Precision Gain** | +15-20% vs baseline |
| **RRF Fusion Improvement** | +10% vs single pipeline |
| **Confidence Calibration Error** | <5% |
| **End-to-End Latency** | <3s (Tier 1), <5s (Tier 2/3) |

---

## Next Steps

### Immediate Actions (Week 1)
1. ✅ Create all POC implementation plans (DONE)
2. ⏳ Deploy infrastructure (Elasticsearch, Re-ranker)
3. ⏳ Set up development environments
4. ⏳ Create feature branches for each POC

### Short-Term (Weeks 2-5)
1. Implement British Council POC
2. Implement CRU POC (parallel)
3. Test infrastructure with both POCs

### Medium-Term (Weeks 5-9)
1. Implement GT Motive POC
2. Implement Solera POC (parallel)

### Long-Term (Weeks 9-14)
1. Implement Construction Monitor POC
2. Comprehensive testing across all POCs
3. Performance optimization
4. Documentation finalization

---

## Documentation Structure

```
backend/docs/poc_implementation_plans/
├── 00_IMPLEMENTATION_PLANS_SUMMARY.md  ← This file
├── 01_british_council_implementation_plan.md
├── 02_cru_implementation_plan.md
├── 03_infrastructure_reranking_multipipeline.md
├── 04_gt_motive_implementation_plan.md
├── 05_solera_implementation_plan.md
└── 06_construction_monitor_implementation_plan.md
```

Each plan includes:
- Business requirements
- Technical architecture
- Reusable components
- New components to build
- Data flow diagrams
- API endpoints
- Database schema
- Frontend UI components
- Testing strategy
- Deployment steps
- Timeline

---

## Conclusion

All 6 POC implementation plans are now complete and ready for development. The plans maximize code reuse through:

1. **Shared infrastructure** (re-ranker, Elasticsearch, multi-pipeline router)
2. **Core platform components** (embedding, retrieval, LLM, document processing)
3. **Cross-POC component reuse** (Excel export, part code extraction)

**Key Benefits:**
- **60-80% code reuse** for Tier 1 POCs
- **50-65% code reuse** for Tier 2 POCs
- **Accelerated development** through shared infrastructure
- **Consistent architecture** across all POCs
- **Observable and maintainable** systems

**Total Delivery Time:** ~14 weeks (3.5 months) with 2 developers

**Status:** ✅ Planning Complete - Ready for Implementation

---

**Last Updated:** 2026-01-02
**Author:** Claude Code
**Version:** 1.0
