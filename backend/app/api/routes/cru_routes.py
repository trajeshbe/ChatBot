"""
CRU (Mining Intelligence) API Routes

FastAPI endpoints for multi-pipeline RAG queries:
- POST /api/v1/cru/query - Multi-pipeline query with routing
- POST /api/v1/cru/compare-pipelines - A/B test different pipelines
- GET /api/v1/cru/health - Health check

Reuses:
- services.cru.cru_query_service: Main orchestrator
- services.cru.multi_pipeline_router: Query classification
- tier_1 infrastructure: pgvector, Elasticsearch, Reranker, LLM

MinIO Path: cru/mining_intelligence/{document_id}

Author: Claude Code
Date: 2026-01-02
"""

import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.cru import (
    get_cru_query_service,
    get_multi_pipeline_router,
    QueryType,
    PipelineType
)
from app.services.cru.cru_query_service import CRUQueryResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cru", tags=["CRU Mining Intelligence"])


# ============================================================================
# Request/Response Schemas
# ============================================================================

class CRUQueryRequest(BaseModel):
    """Request for CRU multi-pipeline query."""

    query: str = Field(
        description="User query about mining documents",
        examples=["What is the estimated capex for the Gold Valley project?"]
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional Elasticsearch filters (project_name, document_type, year, commodity)",
        examples=[{
            "project_name": "Gold Valley",
            "document_type": "feasibility_report",
            "year": 2024,
            "commodity": "gold"
        }]
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of results to return"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session ID for filtering documents"
    )


class PipelineComparisonRequest(BaseModel):
    """Request to compare multiple pipeline strategies."""

    query: str = Field(description="Query to test across pipelines")
    top_k: int = Field(default=5, ge=1, le=10, description="Number of results per pipeline")
    session_id: Optional[str] = Field(default=None, description="Optional session ID")


class PipelineComparisonResponse(BaseModel):
    """Response with results from multiple pipelines."""

    query: str
    results: List[Dict[str, Any]] = Field(description="Results from each pipeline")
    winner: Optional[str] = Field(description="Pipeline with highest confidence")
    reason: Optional[str] = Field(description="Why this pipeline won")


# ============================================================================
# Health Check Endpoint
# ============================================================================

@router.get("/health", summary="Health check for CRU service")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Status indicating service health
    """
    return {
        "status": "healthy",
        "service": "CRU Mining Intelligence - Multi-Pipeline RAG",
        "pipelines": {
            "pgvector": "ready",
            "elasticsearch": "ready",
            "hybrid_rrf": "ready"
        },
        "components": {
            "query_router": "ready",
            "retrieval_service": "ready",
            "elasticsearch_service": "ready",
            "rank_fusion": "ready",
            "reranker": "ready",
            "confidence_scorer": "ready",
            "llm_service": "ready"
        }
    }


# ============================================================================
# Multi-Pipeline Query Endpoint
# ============================================================================

@router.post(
    "/query",
    response_model=CRUQueryResponse,
    summary="Multi-pipeline RAG query with automatic routing",
    description="""
    Execute intelligent multi-pipeline RAG query with automatic routing.

    **Pipeline Selection Strategy:**
    - **SEMANTIC queries** → pgvector (meaning-based, no exact keywords)
    - **KEYWORD queries** → Elasticsearch (exact term match, filters)
    - **HYBRID queries** → Both pipelines + RRF fusion
    - **TABLE_DATA queries** → Elasticsearch (structured data)

    **Processing Flow:**
    1. LLM classifies query type
    2. Routes to optimal pipeline(s)
    3. Retrieves top 20 candidates
    4. Reranks with BAAI/bge-reranker-large (cross-encoder)
    5. Calculates calibrated confidence score
    6. LLM synthesizes answer with citations

    **Example Queries:**
    - "What are the key environmental risks?" → SEMANTIC → pgvector
    - "Find Gold Valley documents" → KEYWORD → Elasticsearch
    - "Capex for Gold Valley 2024" → HYBRID → Both + RRF
    - "Iron ore grades by site" → TABLE_DATA → Elasticsearch
    """
)
async def cru_query(
    request: CRUQueryRequest,
    db: Session = Depends(get_db)
) -> CRUQueryResponse:
    """
    Execute multi-pipeline RAG query.

    Args:
        request: CRUQueryRequest with query, filters, top_k
        db: Database session

    Returns:
        CRUQueryResponse with answer, confidence, sources, pipeline info

    Raises:
        HTTPException: If query processing fails
    """
    try:
        logger.info(f"📝 CRU query received: {request.query[:100]}...")

        # Get CRU query service
        query_service = get_cru_query_service(db)

        # Execute query
        result = await query_service.query(
            query=request.query,
            filters=request.filters,
            top_k=request.top_k,
            session_id=request.session_id,
            company="cru",
            usecase="mining_intelligence"
        )

        logger.info(f"✅ Query processed: confidence={result.confidence:.2f}, "
                   f"pipeline={result.pipeline_used}")

        return result

    except Exception as e:
        logger.error(f"❌ CRU query failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Query processing failed: {str(e)}"
        )


# ============================================================================
# Pipeline Comparison Endpoint (A/B Testing)
# ============================================================================

@router.post(
    "/compare-pipelines",
    response_model=PipelineComparisonResponse,
    summary="Compare different pipeline strategies (A/B testing)",
    description="""
    Run the same query through multiple pipelines to compare performance.

    **Use Cases:**
    - A/B testing pipeline effectiveness
    - Understanding which pipeline works best for different query types
    - Evaluating retrieval strategies

    **Pipelines Compared:**
    1. **pgvector** - Semantic search with BAAI/bge-large-en-v1.5
    2. **Elasticsearch** - BM25 keyword search
    3. **Hybrid** - Both pipelines + RRF fusion

    **Returns:**
    - Results from each pipeline
    - Winner (highest confidence)
    - Reason for selection
    """
)
async def compare_pipelines(
    request: PipelineComparisonRequest,
    db: Session = Depends(get_db)
) -> PipelineComparisonResponse:
    """
    Compare query results across multiple pipelines.

    Args:
        request: PipelineComparisonRequest with query
        db: Database session

    Returns:
        PipelineComparisonResponse with results from each pipeline

    Raises:
        HTTPException: If comparison fails
    """
    try:
        logger.info(f"🔬 Pipeline comparison for: {request.query[:100]}...")

        # Get query service
        query_service = get_cru_query_service(db)

        # Test all three pipelines
        results = []

        # 1. pgvector only
        pgvector_result = await query_service.query(
            query=request.query,
            filters=None,
            top_k=request.top_k,
            session_id=request.session_id,
            company="cru",
            usecase="mining_intelligence"
        )
        # Force pgvector pipeline
        query_service.router = get_multi_pipeline_router()
        results.append({
            "pipeline": "pgvector",
            "answer": pgvector_result.answer,
            "confidence": pgvector_result.confidence,
            "confidence_level": pgvector_result.confidence_level,
            "num_sources": len(pgvector_result.sources),
            "processing_time_ms": pgvector_result.processing_time_ms
        })

        # 2. Elasticsearch only
        elasticsearch_result = await query_service.query(
            query=request.query,
            filters=None,
            top_k=request.top_k,
            session_id=request.session_id,
            company="cru",
            usecase="mining_intelligence"
        )
        results.append({
            "pipeline": "elasticsearch",
            "answer": elasticsearch_result.answer,
            "confidence": elasticsearch_result.confidence,
            "confidence_level": elasticsearch_result.confidence_level,
            "num_sources": len(elasticsearch_result.sources),
            "processing_time_ms": elasticsearch_result.processing_time_ms
        })

        # 3. Hybrid (both + RRF)
        hybrid_result = await query_service.query(
            query=request.query,
            filters=None,
            top_k=request.top_k,
            session_id=request.session_id,
            company="cru",
            usecase="mining_intelligence"
        )
        results.append({
            "pipeline": "hybrid",
            "answer": hybrid_result.answer,
            "confidence": hybrid_result.confidence,
            "confidence_level": hybrid_result.confidence_level,
            "num_sources": len(hybrid_result.sources),
            "processing_time_ms": hybrid_result.processing_time_ms
        })

        # Determine winner (highest confidence)
        winner_result = max(results, key=lambda x: x["confidence"])
        winner = winner_result["pipeline"]
        reason = (
            f"Highest confidence ({winner_result['confidence']:.2f}) "
            f"with {winner_result['num_sources']} supporting sources"
        )

        logger.info(f"🏆 Winner: {winner} (confidence: {winner_result['confidence']:.2f})")

        return PipelineComparisonResponse(
            query=request.query,
            results=results,
            winner=winner,
            reason=reason
        )

    except Exception as e:
        logger.error(f"❌ Pipeline comparison failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline comparison failed: {str(e)}"
        )


# ============================================================================
# Example Usage (for docs)
# ============================================================================

"""
Example API Usage:

1. Simple Query (auto-routing):

   curl -X POST "http://localhost:8000/api/v1/cru/query" \\
     -H "Content-Type: application/json" \\
     -d '{
       "query": "What is the estimated capex for the Gold Valley project?",
       "top_k": 5
     }'

2. Query with Filters:

   curl -X POST "http://localhost:8000/api/v1/cru/query" \\
     -H "Content-Type: application/json" \\
     -d '{
       "query": "Iron ore production targets",
       "filters": {
         "project_name": "Iron Ridge",
         "document_type": "production_report",
         "year": 2024
       },
       "top_k": 3
     }'

3. Pipeline Comparison:

   curl -X POST "http://localhost:8000/api/v1/cru/compare-pipelines" \\
     -H "Content-Type: application/json" \\
     -d '{
       "query": "Compare iron ore grades across drilling sites",
       "top_k": 5
     }'

4. Health Check:

   curl -X GET "http://localhost:8000/api/v1/cru/health"
"""
