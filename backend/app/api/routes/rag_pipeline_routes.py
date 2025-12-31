"""
API Routes for Robust RAG Pipeline

Provides endpoints for the new robust RAG pipeline with:
- Hybrid retrieval
- Reranking
- Self-critique
- Semantic caching
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

from app.tier_1.infrastructure.database import get_db
from app.tier_1.rag.pipeline import rag_answer, get_metrics_collector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/rag-pipeline", tags=["RAG Pipeline"])


# ============================================================================
# Request/Response Models
# ============================================================================

class RagQueryRequest(BaseModel):
    """Request model for RAG query"""
    query: str = Field(..., description="User's question", min_length=1)
    session_id: Optional[str] = Field(None, description="Session ID for memory hierarchy")
    tenant_id: Optional[str] = Field(None, description="Tenant ID for multi-tenancy")
    user_id: Optional[str] = Field(None, description="User ID for audit logging")
    model_name: Optional[str] = Field(None, description="Specific model to use (e.g., 'gpt-4', 'claude-3-opus')")
    use_cache: bool = Field(True, description="Whether to use semantic cache")


class SourceCitation(BaseModel):
    """Source citation model"""
    source_number: int
    filename: str
    source_url: Optional[str]
    excerpt: str


class RagQueryResponse(BaseModel):
    """Response model for RAG query"""
    answer: str
    citations: List[SourceCitation]
    model_used: str
    tokens_used: int
    latency_ms: float

    # Enhanced metadata
    cache_hit: bool
    refined: bool
    rerank_used: bool
    num_candidates: int
    num_chunks_used: int

    # Timing breakdown
    timings_ms: Dict[str, float]

    # Critique info (if applicable)
    critique_passed: Optional[bool] = None


class MetricsResponse(BaseModel):
    """Response model for pipeline metrics"""
    total_requests: int
    cache_hits: int
    cache_misses: int
    cache_hit_rate: Optional[float]
    refinements: int
    refinement_rate: Optional[float]
    errors: int
    error_rate: Optional[float]
    avg_latency_ms: Optional[float]


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/query", response_model=RagQueryResponse)
async def query_robust_pipeline(
    request: RagQueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Query the robust RAG pipeline.

    Features:
    - Hybrid retrieval (semantic + lexical)
    - Memory hierarchy (session documents → all documents)
    - LLM-based reranking
    - Self-critique and refinement
    - Semantic caching

    Example:
        ```
        POST /api/v1/rag-pipeline/query
        {
            "query": "What is the project about?",
            "session_id": "session-123",
            "model_name": "gpt-4-turbo-preview"
        }
        ```
    """
    try:
        logger.info(f"Robust RAG query: {request.query[:100]}... (session: {request.session_id})")

        # Call the robust pipeline
        answer, citations, state = await rag_answer(
            user_query=request.query,
            db=db,
            session_id=request.session_id,
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            model_name=request.model_name,
            extra_meta={"use_cache": request.use_cache}
        )

        # Format response
        response = RagQueryResponse(
            answer=answer,
            citations=[
                SourceCitation(
                    source_number=c.get("source_number", i + 1),
                    filename=c.get("filename", "Unknown"),
                    source_url=c.get("source_url"),
                    excerpt=c.get("excerpt", "")
                )
                for i, c in enumerate(citations)
            ],
            model_used=state.model_name or "pipeline",
            tokens_used=_estimate_tokens(answer, request.query),
            latency_ms=sum(state.timings_ms.values()),
            cache_hit=state.cache_hit,
            refined=state.refined,
            rerank_used=state.rerank_used,
            num_candidates=len(state.candidates),
            num_chunks_used=len(state.reranked_chunks),
            timings_ms=state.timings_ms,
            critique_passed=(
                state.critique_result.is_grounded and state.critique_result.is_complete
                if state.critique_result else None
            )
        )

        return response

    except Exception as e:
        logger.error(f"Error in robust RAG query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@router.get("/metrics", response_model=MetricsResponse)
async def get_pipeline_metrics():
    """
    Get performance metrics for the RAG pipeline.

    Returns aggregated metrics including:
    - Total requests
    - Cache hit rate
    - Refinement rate
    - Average latency
    - Error rate

    Example:
        ```
        GET /api/v1/rag-pipeline/metrics
        ```
    """
    try:
        metrics_collector = get_metrics_collector()
        metrics = metrics_collector.get_metrics()

        return MetricsResponse(**metrics)

    except Exception as e:
        logger.error(f"Error fetching metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching metrics: {str(e)}"
        )


@router.post("/metrics/reset")
async def reset_pipeline_metrics():
    """
    Reset pipeline metrics.

    Use with caution - this will reset all accumulated metrics.

    Example:
        ```
        POST /api/v1/rag-pipeline/metrics/reset
        ```
    """
    try:
        metrics_collector = get_metrics_collector()
        metrics_collector.reset()

        return {"message": "Metrics reset successfully"}

    except Exception as e:
        logger.error(f"Error resetting metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting metrics: {str(e)}"
        )


@router.get("/health")
async def pipeline_health_check():
    """
    Health check for the robust RAG pipeline.

    Returns:
        Status and configuration info

    Example:
        ```
        GET /api/v1/rag-pipeline/health
        ```
    """
    try:
        from app.tier_1.rag.pipeline import get_rag_settings

        settings = get_rag_settings()

        return {
            "status": "healthy",
            "pipeline": "robust_rag",
            "version": "1.0.0",
            "configuration": {
                "reranker_enabled": settings.ENABLE_RERANKER,
                "self_critique_enabled": settings.ENABLE_SELF_CRITIQUE,
                "semantic_cache_enabled": settings.ENABLE_SEMANTIC_CACHE,
                "retrieval_alpha": settings.RETRIEVAL_ALPHA,
                "generation_model": settings.GENERATION_MODEL_NAME
            }
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# ============================================================================
# Helper Functions
# ============================================================================

def _estimate_tokens(answer: str, query: str) -> int:
    """Estimate token count (rough approximation)"""
    total_chars = len(answer) + len(query)
    return total_chars // 4
