"""
API Routes for Multi-Strategy RAG

Provides endpoints to:
1. Query using multi-strategy RAG
2. Configure strategy weights
3. View strategy statistics
4. Compare strategies

Author: AI Assistant
Date: 2025-11-24
"""

from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging
import uuid

from app.core.database import get_db
from app.services.multi_strategy_rag import multi_strategy_rag, AnswerStrategy
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/multi-strategy", tags=["Multi-Strategy RAG"])


# ============================================================================
# Request/Response Models
# ============================================================================

class MultiStrategyQueryRequest(BaseModel):
    """Request model for multi-strategy query"""
    query: str = Field(..., description="User query text")
    session_id: Optional[str] = Field(None, description="Session ID for short-term memory")
    model_id: Optional[str] = Field(None, description="LLM model to use (uses recommended model if not specified)")

    # Strategy enablement
    enable_direct_llm: bool = Field(True, description="Enable direct LLM strategy")
    enable_rag_short_term: bool = Field(True, description="Enable short-term memory RAG")
    enable_rag_long_term: bool = Field(True, description="Enable long-term memory RAG")
    enable_tools: bool = Field(False, description="Enable tool-based strategies")

    # Scoring parameters
    min_confidence: float = Field(0.3, ge=0.0, le=1.0, description="Minimum confidence threshold")
    diversity_bonus: float = Field(0.1, ge=0.0, le=0.5, description="Bonus for answers with sources")


class StrategyWeightsUpdate(BaseModel):
    """Update strategy weights"""
    rag_short_term: Optional[float] = Field(None, ge=0.0, le=2.0)
    rag_long_term: Optional[float] = Field(None, ge=0.0, le=2.0)
    direct_llm: Optional[float] = Field(None, ge=0.0, le=2.0)
    tool_navigation: Optional[float] = Field(None, ge=0.0, le=2.0)


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/query")
async def multi_strategy_query(
    request: MultiStrategyQueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute multi-strategy RAG query

    This endpoint executes multiple answer strategies in parallel and returns
    the best answer based on weighted scoring.

    Strategies evaluated:
    - Direct LLM (no RAG)
    - RAG with short-term memory (session documents) - HIGHEST WEIGHT
    - RAG with long-term memory (all documents)
    - Tool-based answers (if enabled)

    Returns the best answer with metadata about all strategies evaluated.
    """
    try:
        logger.info(f"Multi-strategy query: {request.query[:50]}...")

        result = await multi_strategy_rag.query(
            query_text=request.query,
            session_id=request.session_id,
            user_id=None,  # TODO: Get from auth
            model_id=request.model_id,
            db=db,
            enable_direct_llm=request.enable_direct_llm,
            enable_rag_short_term=request.enable_rag_short_term,
            enable_rag_long_term=request.enable_rag_long_term,
            enable_tools=request.enable_tools,
            min_confidence=request.min_confidence,
            diversity_bonus=request.diversity_bonus
        )

        return {
            "success": True,
            **result
        }

    except Exception as e:
        logger.error(f"Multi-strategy query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query-form")
async def multi_strategy_query_form(
    query: str = Form(...),
    session_id: Optional[str] = Form(None),
    model_id: Optional[str] = Form(None),
    enable_direct_llm: bool = Form(True),
    enable_rag_short_term: bool = Form(True),
    enable_rag_long_term: bool = Form(True),
    enable_tools: bool = Form(False),
    db: AsyncSession = Depends(get_db)
):
    """
    Multi-strategy query (form-encoded version for easy testing)

    Example:
    ```bash
    curl -X POST http://localhost:8000/api/v1/multi-strategy/query-form \
      -F "query=Who is Aadhan?" \
      -F "session_id=test-session"
    # Optional: -F "model_id=qwen2.5:1.5b-instruct-q4_K_M"
    ```
    """
    try:
        result = await multi_strategy_rag.query(
            query_text=query,
            session_id=session_id,
            model_id=model_id,
            db=db,
            enable_direct_llm=enable_direct_llm,
            enable_rag_short_term=enable_rag_short_term,
            enable_rag_long_term=enable_rag_long_term,
            enable_tools=enable_tools
        )

        return {
            "success": True,
            **result
        }

    except Exception as e:
        logger.error(f"Multi-strategy query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weights")
async def get_strategy_weights():
    """
    Get current strategy weights

    Returns the weights used to score each strategy.
    Higher weight = strategy is trusted more.
    """
    return {
        "strategy_weights": {
            k.value: v
            for k, v in multi_strategy_rag.strategy_weights.items()
        },
        "source_weights": multi_strategy_rag.source_weights,
        "description": {
            "strategy_weights": "Weight given to each strategy (higher = more trusted)",
            "source_weights": "Quality score for different source types"
        }
    }


@router.post("/weights")
async def update_strategy_weights(update: StrategyWeightsUpdate):
    """
    Update strategy weights

    Allows dynamic tuning of which strategies are prioritized.

    Example:
    ```json
    {
      "rag_short_term": 1.5,  // Increase short-term memory priority
      "direct_llm": 0.6       // Decrease direct LLM priority
    }
    ```
    """
    try:
        updated_weights = {}

        if update.rag_short_term is not None:
            multi_strategy_rag.strategy_weights[AnswerStrategy.RAG_SHORT_TERM] = update.rag_short_term
            updated_weights["rag_short_term"] = update.rag_short_term

        if update.rag_long_term is not None:
            multi_strategy_rag.strategy_weights[AnswerStrategy.RAG_LONG_TERM] = update.rag_long_term
            updated_weights["rag_long_term"] = update.rag_long_term

        if update.direct_llm is not None:
            multi_strategy_rag.strategy_weights[AnswerStrategy.DIRECT_LLM] = update.direct_llm
            updated_weights["direct_llm"] = update.direct_llm

        if update.tool_navigation is not None:
            multi_strategy_rag.strategy_weights[AnswerStrategy.TOOL_NAVIGATION] = update.tool_navigation
            updated_weights["tool_navigation"] = update.tool_navigation

        logger.info(f"Updated strategy weights: {updated_weights}")

        return {
            "success": True,
            "updated_weights": updated_weights,
            "current_weights": {
                k.value: v
                for k, v in multi_strategy_rag.strategy_weights.items()
            }
        }

    except Exception as e:
        logger.error(f"Failed to update weights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_strategies(
    query: str = Form(...),
    session_id: Optional[str] = Form(None),
    model_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Compare all strategies side-by-side

    Executes all strategies and returns detailed comparison.
    Useful for debugging and understanding strategy selection.

    Returns:
    - All candidate answers
    - Scores for each
    - Winner and why it won
    """
    try:
        result = await multi_strategy_rag.query(
            query_text=query,
            session_id=session_id,
            model_id=model_id,
            db=db,
            enable_direct_llm=True,
            enable_rag_short_term=True,
            enable_rag_long_term=True,
            enable_tools=False
        )

        # Return detailed comparison
        return {
            "query": query,
            "winner": {
                "strategy": result["strategy_used"],
                "score": result["final_score"],
                "confidence": result["confidence"],
                "answer": result["answer"][:200] + "..." if len(result["answer"]) > 200 else result["answer"],
                "sources": result["num_sources"]
            },
            "all_candidates": result["metadata"]["top_3_strategies"],
            "strategy_weights": result["metadata"]["strategy_weights_used"],
            "explanation": f"Winner selected based on highest final score. {result['strategy_used']} scored {result['final_score']:.3f}"
        }

    except Exception as e:
        logger.error(f"Strategy comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check for multi-strategy RAG service"""
    return {
        "status": "healthy",
        "service": "multi-strategy-rag",
        "strategies_available": [s.value for s in AnswerStrategy],
        "current_weights": {
            k.value: v
            for k, v in multi_strategy_rag.strategy_weights.items()
        }
    }
