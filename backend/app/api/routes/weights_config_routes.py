"""
Weights Configuration API Routes

API endpoints for managing configurable weights in the RAG system.

Endpoints:
- GET /api/v1/config/weights - Get all weights
- GET /api/v1/config/weights/{section} - Get specific section
- POST /api/v1/config/weights - Update weights
- POST /api/v1/config/weights/save - Save to file
- POST /api/v1/config/weights/reset - Reset to defaults
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from app.services.weights_config_service import weights_config_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/config", tags=["Configuration"])


# ==========================================
# REQUEST/RESPONSE MODELS
# ==========================================

class WeightUpdate(BaseModel):
    """Request model for updating weights"""
    strategy_weights: Optional[Dict[str, float]] = None
    scoring_formula_weights: Optional[Dict[str, float]] = None
    source_quality_weights: Optional[Dict[str, float]] = None
    classification_thresholds: Optional[Dict[str, float]] = None
    similarity_thresholds: Optional[Dict[str, float]] = None
    reranking_weights: Optional[Dict[str, float]] = None
    query_preprocessing: Optional[Dict[str, Any]] = None
    cache: Optional[Dict[str, Any]] = None
    multi_tool_weights: Optional[Dict[str, float]] = None
    answer_fusion: Optional[Dict[str, float]] = None
    rag_settings: Optional[Dict[str, Any]] = None


class WeightsResponse(BaseModel):
    """Response model for weights"""
    success: bool
    data: Dict[str, Any]
    message: Optional[str] = None


class UpdateResponse(BaseModel):
    """Response model for update operations"""
    success: bool
    message: str
    updated_sections: Optional[list] = None
    error: Optional[str] = None


# ==========================================
# ENDPOINTS
# ==========================================

@router.get("/weights", response_model=WeightsResponse)
async def get_all_weights():
    """
    Get all weights configuration

    Returns complete weights configuration including:
    - Strategy weights
    - Scoring formula weights
    - Source quality weights
    - Classification thresholds
    - Similarity thresholds
    - Reranking weights
    - Query preprocessing parameters
    - Cache configuration
    - Multi-tool weights
    - Answer fusion weights
    - RAG settings (top_k, chunk_size, etc.)
    """
    try:
        config = weights_config_service.get_all_weights()

        return WeightsResponse(
            success=True,
            data=config,
            message="Weights configuration retrieved successfully"
        )

    except Exception as e:
        logger.error(f"Error getting weights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weights/{section}", response_model=WeightsResponse)
async def get_weights_section(section: str):
    """
    Get specific weights section

    Args:
        section: One of:
            - strategy_weights
            - scoring_formula_weights
            - source_quality_weights
            - classification_thresholds
            - similarity_thresholds
            - reranking_weights
            - query_preprocessing
            - cache
            - multi_tool_weights
            - answer_fusion
            - rag_settings

    Returns:
        Weights for the specified section
    """
    try:
        config = weights_config_service.get_all_weights()

        if section not in config:
            raise HTTPException(
                status_code=404,
                detail=f"Section '{section}' not found. Valid sections: {list(config.keys())}"
            )

        return WeightsResponse(
            success=True,
            data={section: config[section]},
            message=f"Section '{section}' retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting section {section}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/weights", response_model=UpdateResponse)
async def update_weights(updates: WeightUpdate):
    """
    Update weights configuration

    Args:
        updates: Weight updates to apply

    Returns:
        Update status and results

    Example:
        ```json
        {
          "strategy_weights": {
            "rag_short_term": 1.0,
            "direct_llm": 0.8
          },
          "classification_thresholds": {
            "general_knowledge_skip": 0.80
          }
        }
        ```
    """
    try:
        # Convert to dict and filter out None values
        updates_dict = {
            k: v for k, v in updates.dict().items()
            if v is not None
        }

        if not updates_dict:
            raise HTTPException(
                status_code=400,
                detail="No updates provided"
            )

        result = weights_config_service.update_weights(updates_dict)

        if not result['success']:
            raise HTTPException(
                status_code=400,
                detail=result.get('message', 'Update failed')
            )

        return UpdateResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating weights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/weights/save", response_model=UpdateResponse)
async def save_weights():
    """
    Save current weights configuration to file

    Persists the current in-memory weights configuration
    to the YAML config file.

    Returns:
        Save status and results
    """
    try:
        result = weights_config_service.save_config()

        if not result['success']:
            raise HTTPException(
                status_code=500,
                detail=result.get('message', 'Save failed')
            )

        return UpdateResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving weights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/weights/reset", response_model=UpdateResponse)
async def reset_weights():
    """
    Reset all weights to default values

    Resets the configuration to default values defined
    in the Pydantic models.

    WARNING: This will overwrite all current weights!

    Returns:
        Reset status and results
    """
    try:
        result = weights_config_service.reset_to_defaults()

        if not result['success']:
            raise HTTPException(
                status_code=500,
                detail=result.get('message', 'Reset failed')
            )

        return UpdateResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting weights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weights/strategy", response_model=WeightsResponse)
async def get_strategy_weights():
    """Get strategy weights (shortcut endpoint)"""
    weights = weights_config_service.get_strategy_weights()
    return WeightsResponse(
        success=True,
        data={"strategy_weights": weights},
        message="Strategy weights retrieved successfully"
    )


@router.get("/weights/scoring", response_model=WeightsResponse)
async def get_scoring_weights():
    """Get scoring formula weights (shortcut endpoint)"""
    weights = weights_config_service.get_scoring_weights()
    return WeightsResponse(
        success=True,
        data={"scoring_formula_weights": weights},
        message="Scoring weights retrieved successfully"
    )


@router.get("/weights/classification", response_model=WeightsResponse)
async def get_classification_thresholds():
    """Get classification thresholds (shortcut endpoint)"""
    thresholds = weights_config_service.get_classification_thresholds()
    return WeightsResponse(
        success=True,
        data={"classification_thresholds": thresholds},
        message="Classification thresholds retrieved successfully"
    )


@router.get("/weights/similarity", response_model=WeightsResponse)
async def get_similarity_thresholds():
    """Get similarity thresholds (shortcut endpoint)"""
    thresholds = weights_config_service.get_similarity_thresholds()
    return WeightsResponse(
        success=True,
        data={"similarity_thresholds": thresholds},
        message="Similarity thresholds retrieved successfully"
    )
