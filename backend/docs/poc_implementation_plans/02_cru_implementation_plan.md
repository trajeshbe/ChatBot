# CRU POC - Implementation Plan

> **Customer:** CRU (Mining Intelligence)
> **Use Case:** Mining Document Intelligence with Multi-Pipeline RAG
> **Priority:** Tier 1 (High - 75% code reuse from Grant Thornton)
> **Estimated Effort:** 2-3 weeks
> **Created:** 2026-01-02

---

## Table of Contents
1. [Business Requirements](#1-business-requirements)
2. [Technical Architecture](#2-technical-architecture)
3. [Reusable Components](#3-reusable-components-from-grant-thornton)
4. [New Components](#4-new-components-to-build)
5. [Data Flow](#5-data-flow)
6. [API Endpoints](#6-api-endpoints)
7. [Database Schema](#7-database-schema)
8. [Frontend UI](#8-frontend-ui-components)
9. [Testing Strategy](#9-testing-strategy)
10. [Deployment](#10-deployment)
11. [Timeline](#11-implementation-timeline)

---

## 1. Business Requirements

### 1.1 Core Functionality
- **Multi-Pipeline Comparison**: Compare ChromaDB vs Elasticsearch retrieval strategies
- **Document Intelligence**: Extract insights from mining reports, feasibility studies, geological surveys
- **Re-Ranking Enhancement**: Use BAAI/bge-reranker-large to improve retrieval precision
- **A/B Testing Framework**: Compare pipeline performance with real queries
- **Confidence Scoring**: Provide confidence intervals for extracted data

### 1.2 Document Types
- **Mining Feasibility Reports**: Technical assessments, cost estimates, resource calculations
- **Geological Surveys**: Ore deposits, mineral composition, drilling logs
- **Financial Reports**: Capex/Opex projections, NPV calculations, commodity prices
- **Environmental Impact Assessments**: Regulatory compliance, sustainability metrics
- **Production Reports**: Monthly/quarterly output, grade reconciliation

### 1.3 Key Use Cases
1. **Query**: "What is the estimated capex for the Gold Valley project?"
   - Extract: $125M from feasibility report page 47
   - Sources: [Feasibility Report 2024, Section 5.3]

2. **Query**: "Compare iron ore grades across all drilling sites"
   - Extract: Table of Fe% by site
   - Sources: [Geological Survey Q3 2024, Appendix B]

3. **Query**: "What are the key environmental risks?"
   - Extract: List of risks with mitigation strategies
   - Sources: [EIA Report 2024, Section 8]

### 1.4 Success Metrics
- Retrieval precision: >90% (top 3 documents contain answer)
- Re-ranking improvement: +15% precision vs. baseline semantic search
- Multi-pipeline accuracy: Elasticsearch >= ChromaDB on keyword queries
- Confidence calibration: 95% confidence = 95% accuracy
- Query response time: <5 seconds

---

## 2. Technical Architecture

### 2.1 Multi-Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CRU MULTI-PIPELINE STACK                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   USER QUERY                             │  │
│  │  "What is the estimated capex for Gold Valley project?"  │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            QUERY CLASSIFIER (LLM-based)                  │  │
│  │  - Semantic query? → Pipeline A (ChromaDB)               │  │
│  │  - Keyword query?  → Pipeline B (Elasticsearch)          │  │
│  │  - Hybrid query?   → Pipeline C (Both + Fusion)          │  │
│  └────────────┬────────────────┬─────────────────┬──────────┘  │
│               │                │                 │              │
│               ▼                ▼                 ▼              │
│  ┌─────────────────┐ ┌─────────────────┐ ┌──────────────────┐ │
│  │  PIPELINE A     │ │  PIPELINE B     │ │  PIPELINE C      │ │
│  │  ChromaDB       │ │  Elasticsearch  │ │  Hybrid Fusion   │ │
│  │                 │ │                 │ │                  │ │
│  │ BAAI/bge-large  │ │ BM25 + Filters  │ │ RRF Score Fusion │ │
│  │ Semantic Search │ │ Keyword Match   │ │ (ChromaDB + ES)  │ │
│  │ MMR Diversity   │ │ Boolean Queries │ │                  │ │
│  └────────┬────────┘ └────────┬────────┘ └────────┬─────────┘ │
│           │                   │                    │           │
│           └───────────────────┴────────────────────┘           │
│                               │                                 │
│                               ▼                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              RE-RANKER (BAAI/bge-reranker-large)         │  │
│  │  - Cross-encoder scoring                                 │  │
│  │  - Top 20 → Top 5                                        │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              CONFIDENCE SCORER                           │  │
│  │  - Embedding similarity score                            │  │
│  │  - Re-ranker score                                       │  │
│  │  - Document relevance score                              │  │
│  │  - Calibrated probability: P(correct | scores)           │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              LLM SYNTHESIS (GPT-4o-mini)                 │  │
│  │  - Extract answer from context                           │  │
│  │  - Cite sources with page numbers                        │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              FINAL RESPONSE                              │  │
│  │  {                                                        │  │
│  │    "answer": "$125M capex for Gold Valley project",      │  │
│  │    "confidence": 0.92,                                   │  │
│  │    "sources": [{"doc": "Feasibility Report", "page": 47}],│  │
│  │    "pipeline_used": "ChromaDB + Reranker"                │  │
│  │  }                                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Embeddings** | BAAI/bge-large-en-v1.5 (1024-dim) | Same as Grant Thornton |
| **Vector DB** | ChromaDB (Pipeline A) | Existing infrastructure, semantic search |
| **Keyword DB** | Elasticsearch 8.x (Pipeline B) | Industry-standard BM25, filters |
| **Re-ranker** | BAAI/bge-reranker-large | Cross-encoder for precision boost |
| **LLM** | OpenAI GPT-4o-mini | Cost-effective, fast |
| **Query Classifier** | GPT-4o-mini | Determine pipeline strategy |
| **Score Fusion** | Reciprocal Rank Fusion (RRF) | Combine multiple retrieval sources |
| **Backend** | FastAPI + Pydantic | Existing stack |
| **Storage** | MinIO (documents) + PostgreSQL (metadata) | Existing infrastructure |

### 2.3 Pipeline Selection Strategy

| Query Type | Example | Pipeline | Rationale |
|------------|---------|----------|-----------|
| **Semantic** | "What are the key risks in the project?" | ChromaDB | Meaning-based, no exact keywords |
| **Keyword** | "Find documents mentioning 'Gold Valley'" | Elasticsearch | Exact term match, filters |
| **Hybrid** | "Capex for Gold Valley project 2024" | Both + RRF | Combine semantic + keyword |
| **Table/Data** | "Iron ore grades by drilling site" | Elasticsearch | Structured data, field search |

---

## 3. Reusable Components from Grant Thornton

### 3.1 Backend Services (75% Reuse)

| Service | File | Reuse % | Modifications Needed |
|---------|------|---------|---------------------|
| **Embedding Service** | `app/services/embedding_service.py` | 100% | None - works as-is |
| **Reranker Service** | `app/services/reranker_service.py` | 100% | None - works as-is |
| **LLM Service** | `app/services/llm_service.py` | 100% | None - works as-is |
| **Document Service** | `app/services/document_service.py` | 80% | Adapt for mining documents (PDF tables, images) |
| **Vector Store (ChromaDB)** | `app/rag_pipeline/retrieval.py` | 90% | Add CRU collection |
| **MinIO Path Builder** | `app/services/minio_path_builder.py` | 90% | Add cru-mining paths |

### 3.2 RAG Pipeline Core
```python
# Reuse from Grant Thornton:
# 1. Document upload → MinIO storage
# 2. Text extraction (Docling for PDFs)
# 3. Chunking (500 tokens, 50 overlap)
# 4. Embedding generation (BAAI/bge-large-en-v1.5)
# 5. Storage in ChromaDB
# 6. Query → Embedding → Semantic search
# 7. Rerank with BAAI/bge-reranker-large
# 8. LLM synthesis
```

### 3.3 Database Models
- Reuse `documents` table for mining reports
- Reuse `document_chunks` table for text chunks
- Reuse `chat_sessions` for conversations

---

## 4. New Components to Build

### 4.1 Elasticsearch Integration Service

**File:** `backend/app/services/cru/elasticsearch_service.py`

**Purpose:** Keyword-based retrieval with filters

```python
from elasticsearch import AsyncElasticsearch
from typing import List, Dict, Any

class ElasticsearchService:
    """Elasticsearch-based retrieval for keyword queries."""

    def __init__(self):
        self.client = AsyncElasticsearch(
            hosts=[os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")]
        )
        self.index_name = "cru_mining_documents"

    async def index_document(
        self,
        document_id: str,
        content: str,
        metadata: Dict[str, Any]
    ):
        """Index document in Elasticsearch."""
        doc = {
            "content": content,
            "document_type": metadata.get("document_type"),
            "project_name": metadata.get("project_name"),
            "year": metadata.get("year"),
            "commodity": metadata.get("commodity"),
            "metadata": metadata
        }

        await self.client.index(
            index=self.index_name,
            id=document_id,
            document=doc
        )

    async def search(
        self,
        query: str,
        filters: Dict[str, Any] = None,
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        BM25 keyword search with optional filters.

        Example filters:
        {
            "document_type": "feasibility_report",
            "project_name": "Gold Valley",
            "year": 2024,
            "commodity": "gold"
        }
        """
        # Build Elasticsearch query
        must_clauses = [
            {
                "multi_match": {
                    "query": query,
                    "fields": ["content^2", "metadata.title", "metadata.section"],
                    "type": "best_fields"
                }
            }
        ]

        # Add filters
        filter_clauses = []
        if filters:
            for field, value in filters.items():
                filter_clauses.append({"term": {field: value}})

        es_query = {
            "bool": {
                "must": must_clauses,
                "filter": filter_clauses
            }
        }

        # Execute search
        response = await self.client.search(
            index=self.index_name,
            query=es_query,
            size=top_k
        )

        # Format results
        results = []
        for hit in response["hits"]["hits"]:
            results.append({
                "document_id": hit["_id"],
                "content": hit["_source"]["content"],
                "score": hit["_score"],
                "metadata": hit["_source"]["metadata"]
            })

        return results
```

### 4.2 Multi-Pipeline Router Service

**File:** `backend/app/services/cru/multi_pipeline_router.py`

**Purpose:** Route queries to best pipeline(s)

```python
from enum import Enum
from typing import List, Dict, Any
import json

class PipelineType(str, Enum):
    CHROMADB = "chromadb"
    ELASTICSEARCH = "elasticsearch"
    HYBRID = "hybrid"

class QueryType(str, Enum):
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    TABLE_DATA = "table_data"

class MultiPipelineRouter:
    """Route queries to optimal retrieval pipeline."""

    def __init__(self, llm_service):
        self.llm = llm_service

    async def classify_query(self, query: str) -> QueryType:
        """
        Classify query type using LLM.

        Examples:
        - "What are the key risks?" → SEMANTIC
        - "Find documents mentioning Gold Valley" → KEYWORD
        - "Capex for Gold Valley 2024" → HYBRID
        - "Iron ore grades by site" → TABLE_DATA
        """
        prompt = f"""Classify this mining industry query into one of these types:
1. SEMANTIC - Meaning-based, no exact keywords needed (e.g., "What are the risks?")
2. KEYWORD - Exact term match needed (e.g., "Find 'Gold Valley' documents")
3. HYBRID - Both semantic meaning and specific terms (e.g., "Capex for Gold Valley 2024")
4. TABLE_DATA - Looking for structured data/tables (e.g., "Iron ore grades by site")

Query: {query}

Return ONLY the classification type (SEMANTIC, KEYWORD, HYBRID, or TABLE_DATA):"""

        response = await self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )

        classification = response["content"].strip().upper()
        return QueryType[classification]

    async def route_query(
        self,
        query: str,
        query_type: QueryType = None
    ) -> List[PipelineType]:
        """
        Route query to appropriate pipeline(s).

        Returns:
            List of pipelines to use (in order of priority)
        """
        if query_type is None:
            query_type = await self.classify_query(query)

        # Routing logic
        if query_type == QueryType.SEMANTIC:
            return [PipelineType.CHROMADB]

        elif query_type == QueryType.KEYWORD:
            return [PipelineType.ELASTICSEARCH]

        elif query_type == QueryType.HYBRID:
            return [PipelineType.HYBRID]  # Both pipelines + RRF

        elif query_type == QueryType.TABLE_DATA:
            return [PipelineType.ELASTICSEARCH]  # Better for structured data

        else:
            # Default fallback
            return [PipelineType.CHROMADB]
```

### 4.3 Reciprocal Rank Fusion Service

**File:** `backend/app/services/cru/rank_fusion_service.py`

**Purpose:** Combine results from multiple pipelines

```python
from typing import List, Dict, Any

class RankFusionService:
    """Reciprocal Rank Fusion for combining multiple retrieval sources."""

    def __init__(self, k: int = 60):
        """
        Args:
            k: RRF constant (default 60 per literature)
        """
        self.k = k

    def fuse_rankings(
        self,
        chromadb_results: List[Dict[str, Any]],
        elasticsearch_results: List[Dict[str, Any]],
        weights: Dict[str, float] = None
    ) -> List[Dict[str, Any]]:
        """
        Combine results from ChromaDB and Elasticsearch using RRF.

        RRF formula:
        score(d) = Σ_r [ weight_r / (k + rank_r(d)) ]

        Where:
        - d = document
        - r = ranking source (ChromaDB, Elasticsearch)
        - rank_r(d) = rank of document d in source r
        - k = constant (default 60)

        Args:
            chromadb_results: Results from ChromaDB
            elasticsearch_results: Results from Elasticsearch
            weights: Optional weights per source (default equal)

        Returns:
            Fused results sorted by RRF score
        """
        if weights is None:
            weights = {"chromadb": 1.0, "elasticsearch": 1.0}

        # Build document ID → score mapping
        scores = {}

        # Process ChromaDB results
        for rank, result in enumerate(chromadb_results, start=1):
            doc_id = result["document_id"]
            rrf_score = weights["chromadb"] / (self.k + rank)

            if doc_id not in scores:
                scores[doc_id] = {
                    "document_id": doc_id,
                    "content": result["content"],
                    "metadata": result["metadata"],
                    "rrf_score": 0.0,
                    "chromadb_rank": None,
                    "elasticsearch_rank": None
                }

            scores[doc_id]["rrf_score"] += rrf_score
            scores[doc_id]["chromadb_rank"] = rank

        # Process Elasticsearch results
        for rank, result in enumerate(elasticsearch_results, start=1):
            doc_id = result["document_id"]
            rrf_score = weights["elasticsearch"] / (self.k + rank)

            if doc_id not in scores:
                scores[doc_id] = {
                    "document_id": doc_id,
                    "content": result["content"],
                    "metadata": result["metadata"],
                    "rrf_score": 0.0,
                    "chromadb_rank": None,
                    "elasticsearch_rank": None
                }

            scores[doc_id]["rrf_score"] += rrf_score
            scores[doc_id]["elasticsearch_rank"] = rank

        # Sort by RRF score
        fused_results = sorted(
            scores.values(),
            key=lambda x: x["rrf_score"],
            reverse=True
        )

        return fused_results
```

### 4.4 Confidence Scorer Service

**File:** `backend/app/services/cru/confidence_scorer.py`

**Purpose:** Calibrate confidence scores for answers

```python
import numpy as np
from sklearn.isotonic import IsotonicRegression
from typing import List, Dict, Any

class ConfidenceScorer:
    """Calibrate confidence scores for answer accuracy."""

    def __init__(self):
        # Isotonic regression for calibration
        # (trained on historical query data)
        self.calibrator = IsotonicRegression(out_of_bounds="clip")

    def calculate_confidence(
        self,
        embedding_score: float,
        reranker_score: float,
        num_supporting_docs: int,
        answer_length: int
    ) -> float:
        """
        Calculate calibrated confidence score.

        Features:
        - embedding_score: Cosine similarity (0-1)
        - reranker_score: Cross-encoder score (0-1)
        - num_supporting_docs: Number of docs supporting answer
        - answer_length: Number of tokens in answer

        Returns:
            Calibrated probability P(correct | features)
        """
        # Feature engineering
        features = [
            embedding_score,
            reranker_score,
            min(num_supporting_docs / 5.0, 1.0),  # Normalize to 0-1
            min(answer_length / 100.0, 1.0)  # Normalize to 0-1
        ]

        # Weighted average (can be replaced with trained model)
        raw_score = (
            0.3 * features[0] +  # Embedding score
            0.4 * features[1] +  # Reranker score (most important)
            0.2 * features[2] +  # Supporting docs
            0.1 * features[3]   # Answer length
        )

        # Calibrate (if calibrator is trained)
        # calibrated_score = self.calibrator.predict([raw_score])[0]

        # For now, return raw score
        return min(max(raw_score, 0.0), 1.0)

    def get_confidence_interval(
        self,
        confidence: float
    ) -> Dict[str, str]:
        """
        Convert numeric confidence to human-readable interval.

        Returns:
            {"level": "high", "description": "Very confident in this answer"}
        """
        if confidence >= 0.9:
            return {
                "level": "very_high",
                "description": "Very confident - answer is highly reliable"
            }
        elif confidence >= 0.75:
            return {
                "level": "high",
                "description": "Confident - answer is likely correct"
            }
        elif confidence >= 0.5:
            return {
                "level": "medium",
                "description": "Moderately confident - verify if critical"
            }
        else:
            return {
                "level": "low",
                "description": "Low confidence - manual verification recommended"
            }
```

### 4.5 CRU Query Service (Main Orchestrator)

**File:** `backend/app/services/cru/cru_query_service.py`

**Purpose:** Orchestrate full multi-pipeline query flow

```python
from typing import List, Dict, Any

class CRUQueryService:
    """Main orchestrator for CRU multi-pipeline RAG."""

    def __init__(
        self,
        chromadb_service,
        elasticsearch_service,
        router_service,
        fusion_service,
        reranker_service,
        confidence_scorer,
        llm_service
    ):
        self.chromadb = chromadb_service
        self.elasticsearch = elasticsearch_service
        self.router = router_service
        self.fusion = fusion_service
        self.reranker = reranker_service
        self.confidence_scorer = confidence_scorer
        self.llm = llm_service

    async def query(
        self,
        query: str,
        filters: Dict[str, Any] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Execute multi-pipeline query with reranking and confidence scoring.

        Returns:
            {
                "answer": str,
                "confidence": float,
                "confidence_interval": dict,
                "sources": List[dict],
                "pipeline_used": str,
                "query_type": str
            }
        """
        # 1. Classify query
        query_type = await self.router.classify_query(query)

        # 2. Route to pipeline(s)
        pipelines = await self.router.route_query(query, query_type)

        # 3. Retrieve from pipeline(s)
        if PipelineType.CHROMADB in pipelines and PipelineType.ELASTICSEARCH in pipelines:
            # Hybrid: retrieve from both
            chromadb_results = await self.chromadb.search(query, top_k=20)
            es_results = await self.elasticsearch.search(query, filters=filters, top_k=20)

            # 4. Fuse rankings
            fused_results = self.fusion.fuse_rankings(chromadb_results, es_results)
            results = fused_results[:20]  # Top 20 for reranking

        elif PipelineType.CHROMADB in pipelines:
            # ChromaDB only
            results = await self.chromadb.search(query, top_k=20)

        else:
            # Elasticsearch only
            results = await self.elasticsearch.search(query, filters=filters, top_k=20)

        # 5. Rerank
        reranked_results = await self.reranker.rerank(
            query=query,
            documents=[r["content"] for r in results],
            top_n=top_k
        )

        # 6. Calculate confidence
        embedding_score = reranked_results[0].get("semantic_score", 0.8)
        reranker_score = reranked_results[0]["score"]
        num_supporting_docs = len([r for r in reranked_results if r["score"] > 0.5])

        confidence = self.confidence_scorer.calculate_confidence(
            embedding_score=embedding_score,
            reranker_score=reranker_score,
            num_supporting_docs=num_supporting_docs,
            answer_length=100  # Placeholder
        )

        confidence_interval = self.confidence_scorer.get_confidence_interval(confidence)

        # 7. LLM synthesis
        context = "\n\n".join([
            f"[Document {i+1}]\n{r['content']}"
            for i, r in enumerate(reranked_results)
        ])

        synthesis_prompt = f"""You are a mining document analyst.
Answer this question based ONLY on the provided context:

Question: {query}

Context:
{context}

Provide a concise answer with specific details (numbers, names, dates).
If the context doesn't contain the answer, say "Information not available in provided documents."

Answer:"""

        answer_response = await self.llm.chat(
            messages=[{"role": "user", "content": synthesis_prompt}],
            temperature=0.0
        )

        answer = answer_response["content"]

        # 8. Format response
        return {
            "answer": answer,
            "confidence": confidence,
            "confidence_interval": confidence_interval,
            "sources": [
                {
                    "document_id": r.get("document_id"),
                    "document_name": r.get("metadata", {}).get("filename"),
                    "page": r.get("metadata", {}).get("page_no"),
                    "score": r["score"]
                }
                for r in reranked_results
            ],
            "pipeline_used": "+".join([p.value for p in pipelines]),
            "query_type": query_type.value
        }
```

---

## 5. Data Flow

### 5.1 Document Ingestion Flow

```
1. UPLOAD
   ├─ Mining report PDF uploaded via UI
   └─ MinIO storage: merit/mining/cru/{project}/{filename}

2. METADATA EXTRACTION
   ├─ Extract project name, document type, year, commodity
   └─ Store in PostgreSQL: documents table

3. TEXT EXTRACTION
   ├─ Docling: Extract text + tables + images
   └─ OCR for scanned pages

4. CHUNKING
   ├─ Split into 500-token chunks (50 overlap)
   └─ Preserve table boundaries

5. DUAL INDEXING
   ├─ Pipeline A: Embed with BAAI → ChromaDB
   └─ Pipeline B: Index full text → Elasticsearch

6. READY
   └─ Document available for query
```

### 5.2 Query Flow (Hybrid Pipeline)

```
USER QUERY: "What is the capex for Gold Valley project 2024?"

1. CLASSIFY
   └─ LLM classifier → HYBRID (has specific terms + semantic meaning)

2. RETRIEVE (PARALLEL)
   ├─ ChromaDB: Semantic search (top 20)
   │   ├─ Embed query with BAAI/bge-large-en-v1.5
   │   └─ Cosine similarity search
   │
   └─ Elasticsearch: Keyword search (top 20)
       ├─ BM25 scoring on "capex", "Gold Valley", "2024"
       └─ Filters: document_type=feasibility_report, year=2024

3. FUSE
   └─ RRF: Combine ChromaDB + Elasticsearch rankings
       ├─ Document A: chromadb_rank=1, es_rank=3 → RRF=0.032
       ├─ Document B: chromadb_rank=5, es_rank=1 → RRF=0.031
       └─ Top 20 fused results

4. RERANK
   └─ BAAI/bge-reranker-large (cross-encoder)
       ├─ Query-document pairs
       └─ Top 5 most relevant

5. CONFIDENCE SCORING
   └─ Features: embedding_score=0.85, reranker_score=0.92, num_docs=3
       └─ Calibrated confidence: 0.89 (HIGH)

6. LLM SYNTHESIS
   └─ GPT-4o-mini with top 5 contexts
       └─ "The estimated capex for Gold Valley project is $125M (Feasibility Report 2024, Section 5.3)"

7. RESPONSE
   └─ {
       "answer": "$125M",
       "confidence": 0.89,
       "confidence_interval": {"level": "high"},
       "sources": [{"doc": "Feasibility Report 2024", "page": 47}],
       "pipeline_used": "chromadb+elasticsearch+reranker"
     }
```

---

## 6. API Endpoints

### 6.1 Document Upload

```http
POST /api/v1/cru/documents/upload
Content-Type: multipart/form-data

{
  "file": <mining_report.pdf>,
  "project_name": "Gold Valley",
  "document_type": "feasibility_report",
  "year": 2024,
  "commodity": "gold"
}

Response:
{
  "document_id": "uuid-here",
  "status": "processing",
  "pipeline_status": {
    "chromadb": "pending",
    "elasticsearch": "pending"
  }
}
```

### 6.2 Multi-Pipeline Query

```http
POST /api/v1/cru/query
Content-Type: application/json

{
  "query": "What is the capex for Gold Valley project?",
  "filters": {
    "project_name": "Gold Valley",
    "document_type": "feasibility_report"
  },
  "top_k": 5
}

Response:
{
  "answer": "The estimated capex for Gold Valley project is $125M",
  "confidence": 0.89,
  "confidence_interval": {
    "level": "high",
    "description": "Confident - answer is likely correct"
  },
  "sources": [
    {
      "document_id": "uuid-123",
      "document_name": "Feasibility Report 2024",
      "page": 47,
      "score": 0.92
    }
  ],
  "pipeline_used": "chromadb+elasticsearch+reranker",
  "query_type": "hybrid",
  "processing_time_ms": 3200
}
```

### 6.3 Pipeline Comparison (A/B Testing)

```http
POST /api/v1/cru/compare-pipelines
Content-Type: application/json

{
  "query": "Iron ore grades by drilling site",
  "pipelines": ["chromadb", "elasticsearch", "hybrid"]
}

Response:
{
  "query": "Iron ore grades by drilling site",
  "results": [
    {
      "pipeline": "chromadb",
      "answer": "Fe% ranges from 58-62% across sites A-D",
      "confidence": 0.75,
      "top_sources": [...],
      "processing_time_ms": 2800
    },
    {
      "pipeline": "elasticsearch",
      "answer": "Site A: 62% Fe, Site B: 60% Fe, Site C: 58% Fe",
      "confidence": 0.92,
      "top_sources": [...],
      "processing_time_ms": 1500
    },
    {
      "pipeline": "hybrid",
      "answer": "Site A: 62% Fe, Site B: 60% Fe, Site C: 58% Fe, Site D: 61% Fe",
      "confidence": 0.95,
      "top_sources": [...],
      "processing_time_ms": 3400
    }
  ],
  "winner": "hybrid",
  "reason": "Highest confidence and most complete answer"
}
```

---

## 7. Database Schema

### 7.1 New Tables

```sql
-- CRU mining projects metadata
CREATE TABLE cru_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_name TEXT UNIQUE NOT NULL,
    commodity TEXT,  -- gold, iron ore, copper, etc.
    location TEXT,
    company TEXT,
    status TEXT,  -- exploration, development, production
    created_at TIMESTAMP DEFAULT NOW()
);

-- Document metadata with mining-specific fields
CREATE TABLE cru_document_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id),
    project_id UUID REFERENCES cru_projects(id),
    document_type TEXT,  -- feasibility_report, geological_survey, eia, etc.
    year INT,
    commodity TEXT,
    indexed_in_chromadb BOOLEAN DEFAULT FALSE,
    indexed_in_elasticsearch BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Query analytics for pipeline comparison
CREATE TABLE cru_query_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    query_type TEXT,  -- semantic, keyword, hybrid, table_data
    pipeline_used TEXT,  -- chromadb, elasticsearch, hybrid
    confidence FLOAT,
    user_feedback INT,  -- 1-5 rating
    was_correct BOOLEAN,
    processing_time_ms INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_cru_doc_meta_project ON cru_document_metadata(project_id);
CREATE INDEX idx_cru_doc_meta_type ON cru_document_metadata(document_type);
CREATE INDEX idx_cru_doc_meta_year ON cru_document_metadata(year);
CREATE INDEX idx_cru_query_analytics_pipeline ON cru_query_analytics(pipeline_used);
```

---

## 8. Frontend UI Components

### 8.1 Pipeline Comparison Dashboard

**File:** `frontend/src/components/CRUPipelineComparison.tsx`

```typescript
export const PipelineComparisonDashboard: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<PipelineResult[]>([]);

  const handleCompare = async () => {
    const response = await axios.post('/api/v1/cru/compare-pipelines', {
      query,
      pipelines: ['chromadb', 'elasticsearch', 'hybrid']
    });
    setResults(response.data.results);
  };

  return (
    <div className="grid grid-cols-3 gap-4">
      <PipelineResultCard
        title="ChromaDB (Semantic)"
        result={results.find(r => r.pipeline === 'chromadb')}
      />
      <PipelineResultCard
        title="Elasticsearch (Keyword)"
        result={results.find(r => r.pipeline === 'elasticsearch')}
      />
      <PipelineResultCard
        title="Hybrid (RRF Fusion)"
        result={results.find(r => r.pipeline === 'hybrid')}
      />
    </div>
  );
};
```

### 8.2 Confidence Indicator

**File:** `frontend/src/components/CRUConfidenceIndicator.tsx`

```typescript
export const ConfidenceIndicator: React.FC<{ confidence: number }> = ({ confidence }) => {
  const getColor = () => {
    if (confidence >= 0.9) return 'bg-emerald-500';
    if (confidence >= 0.75) return 'bg-blue-500';
    if (confidence >= 0.5) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="flex items-center gap-2">
      <div className="w-32 h-2 bg-slate-200 rounded-full">
        <div
          className={`h-2 rounded-full ${getColor()}`}
          style={{ width: `${confidence * 100}%` }}
        />
      </div>
      <span className="text-sm font-semibold">{(confidence * 100).toFixed(0)}%</span>
    </div>
  );
};
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

```python
# tests/services/cru/test_rank_fusion.py
def test_rrf_fusion():
    fusion = RankFusionService(k=60)

    chromadb = [{"document_id": "A", "content": "...", "metadata": {}}]
    elasticsearch = [{"document_id": "B", "content": "...", "metadata": {}}]

    fused = fusion.fuse_rankings(chromadb, elasticsearch)

    assert len(fused) == 2
    assert all("rrf_score" in r for r in fused)

# tests/services/cru/test_confidence_scorer.py
def test_confidence_calculation():
    scorer = ConfidenceScorer()

    confidence = scorer.calculate_confidence(
        embedding_score=0.85,
        reranker_score=0.92,
        num_supporting_docs=3,
        answer_length=50
    )

    assert 0.0 <= confidence <= 1.0
    assert confidence > 0.8  # High confidence expected
```

### 9.2 Integration Tests

```python
# tests/integration/cru/test_multi_pipeline.py
async def test_hybrid_pipeline_query(client):
    # Upload test document
    response = client.post("/api/v1/cru/documents/upload", files={...})
    doc_id = response.json()["document_id"]

    # Wait for indexing
    await asyncio.sleep(5)

    # Query with hybrid pipeline
    response = client.post("/api/v1/cru/query", json={
        "query": "What is the capex?",
        "filters": {},
        "top_k": 5
    })

    result = response.json()
    assert result["confidence"] > 0.5
    assert result["pipeline_used"] in ["chromadb", "elasticsearch", "chromadb+elasticsearch+reranker"]
    assert len(result["sources"]) > 0
```

---

## 10. Deployment

### 10.1 Add Elasticsearch to docker-compose.yml

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

### 10.2 Environment Variables

```bash
# CRU Configuration
ELASTICSEARCH_URL=http://elasticsearch:9200
CRU_ENABLE_MULTI_PIPELINE=true
CRU_DEFAULT_PIPELINE=hybrid
CRU_RRF_K=60
```

### 10.3 Deployment Steps

```bash
# 1. Add Elasticsearch service
docker-compose up -d elasticsearch

# 2. Create Elasticsearch index
curl -X PUT "http://localhost:9200/cru_mining_documents" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "content": {"type": "text"},
      "document_type": {"type": "keyword"},
      "project_name": {"type": "keyword"},
      "year": {"type": "integer"},
      "commodity": {"type": "keyword"}
    }
  }
}'

# 3. Database migrations
cd backend
alembic revision --autogenerate -m "add cru tables"
alembic upgrade head

# 4. Restart backend
docker-compose restart backend frontend
```

---

## 11. Implementation Timeline

### Week 1: Infrastructure Setup (Jan 2-8, 2026)
- **Day 1-2**: Add Elasticsearch service, create indexes
- **Day 3-4**: Implement ElasticsearchService
- **Day 5**: Database tables + migrations

### Week 2: Multi-Pipeline Logic (Jan 9-15, 2026)
- **Day 1**: Implement MultiPipelineRouter (query classification)
- **Day 2**: Implement RankFusionService (RRF)
- **Day 3**: Implement ConfidenceScorer
- **Day 4-5**: Implement CRUQueryService (orchestrator)

### Week 3: Testing & UI (Jan 16-22, 2026)
- **Day 1-2**: API endpoints + integration tests
- **Day 3**: Frontend PipelineComparisonDashboard
- **Day 4**: E2E tests + performance benchmarking
- **Day 5**: Documentation + deployment

### Total Effort: 15 working days (3 weeks)

---

## 12. Success Criteria

- [ ] Elasticsearch integration working (index + search)
- [ ] Multi-pipeline router correctly classifies queries (>90% accuracy)
- [ ] RRF fusion improves precision by +10% vs single pipeline
- [ ] Confidence scores calibrated (95% confidence = 95% accuracy)
- [ ] Pipeline comparison dashboard functional
- [ ] Query response time <5 seconds for hybrid pipeline
- [ ] 100% test coverage for new services

---

## 13. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **Elasticsearch learning curve** | Use existing Python client, follow official docs |
| **RRF not improving results** | Tune k parameter, adjust weights |
| **Query classification errors** | Fine-tune LLM prompts, add training data |
| **Confidence calibration inaccurate** | Collect ground truth data, train Isotonic Regression |
| **Performance issues with dual indexing** | Implement async indexing, queue-based |

---

**Status:** Ready for implementation
**Dependencies:** Grant Thornton POC complete (✅), Elasticsearch service added
**Next Steps:** Set up Elasticsearch, start implementing services
