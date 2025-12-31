"""
Model Management API Routes

Endpoints for listing available models and selecting models.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.llm_service import llm_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/models", tags=["models"])


class ModelSelectionRequest(BaseModel):
    """Request to set default model"""
    model_id: str


class QueryWithModelRequest(BaseModel):
    """Query request with optional model selection"""
    query: str
    model_id: Optional[str] = None
    session_id: Optional[str] = None
    use_cache: bool = True


@router.get("/")
async def list_models():
    """
    Get all available models grouped by type

    Returns:
        - models: List of all available models
        - grouped: Models grouped by proprietary/local-gpu/local-cpu
        - default: Currently selected default model
        - gpu_info: GPU availability information
    """
    try:
        models_info = llm_service.get_available_models()
        return JSONResponse(content=models_info)

    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available")
async def get_available_models():
    """Get only currently available models (excluding unavailable ones)"""
    try:
        all_models = llm_service.get_available_models()

        # Filter to only available
        available = [m for m in all_models["models"] if m.get("available", False)]

        return {
            "models": available,
            "count": len(available),
            "default": all_models["default"],
            "gpu_available": all_models["gpu_info"]["available"]
        }

    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommended")
async def get_recommended_models():
    """Get recommended models for the current hardware"""
    try:
        all_models = llm_service.get_available_models()

        # Filter to recommended and available
        recommended = [
            m for m in all_models["models"]
            if m.get("recommended", False) and m.get("available", False)
        ]

        return {
            "models": recommended,
            "count": len(recommended)
        }

    except Exception as e:
        logger.error(f"Error getting recommended models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/select")
async def select_default_model(request: ModelSelectionRequest):
    """
    Set the default model for queries

    Body:
        - model_id: ID of the model to set as default

    Returns:
        - success: Boolean
        - model_id: Selected model ID
        - message: Success message
    """
    try:
        llm_service.set_default_model(request.model_id)

        return {
            "success": True,
            "model_id": request.model_id,
            "message": f"Default model set to {request.model_id}"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error setting default model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gpu-info")
async def get_gpu_info():
    """
    Get GPU hardware information

    Returns:
        - available: Whether GPU is available
        - type: GPU type (nvidia/amd/cpu)
        - count: Number of GPUs
        - memory_gb: Total GPU memory
        - recommended_backend: Recommended LLM backend
    """
    try:
        from app.utils.gpu_detector import get_gpu_detector

        detector = get_gpu_detector()
        gpu_info = detector.detect()

        return {
            "available": gpu_info.available,
            "type": gpu_info.type,
            "count": gpu_info.count,
            "memory_gb": gpu_info.memory_gb,
            "names": gpu_info.names,
            "driver_version": gpu_info.driver_version,
            "recommended_backend": detector.get_recommended_backend(),
            "docker_gpu_support": detector.check_docker_gpu_support()
        }

    except Exception as e:
        logger.error(f"Error getting GPU info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}")
async def get_model_details(model_id: str):
    """
    Get details for a specific model

    Path Parameters:
        - model_id: Model identifier

    Returns:
        Model details including capabilities and requirements
    """
    try:
        from app.models.model_registry import get_model_registry

        registry = get_model_registry()
        model = registry.get_model(model_id)

        if not model:
            raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")

        return model.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model details: {e}")
        raise HTTPException(status_code=500, detail=str(e))
