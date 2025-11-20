"""
Ollama Model Management API Routes

Provides REST API endpoints for managing Ollama models.

Phase 1 - Read-Only Endpoints:
- GET /api/v1/admin/ollama/models - List installed models
- GET /api/v1/admin/ollama/models/{model_name} - Get model details
- GET /api/v1/admin/ollama/running - List running models
- GET /api/v1/admin/ollama/stats - Get model statistics
- GET /api/v1/admin/ollama/health - Health check

Phase 2 - Model Management Endpoints:
- POST /api/v1/admin/ollama/pull - Pull/install a new model (streaming)
- DELETE /api/v1/admin/ollama/models/{model_name} - Delete a model

Author: AI Assistant
Date: 2025-11-20
"""

import logging
import json
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.ollama_model_service import (
    OllamaModelService,
    get_ollama_service,
    OllamaModel,
    RunningModel,
    ModelDetails
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/ollama", tags=["Ollama Management"])


# Response models
class ModelsListResponse(BaseModel):
    models: List[OllamaModel]
    total: int


class ModelDetailsResponse(BaseModel):
    model_name: str
    details: ModelDetails
    is_installed: bool


class RunningModelsResponse(BaseModel):
    running_models: List[RunningModel]
    total: int


class ModelStatsResponse(BaseModel):
    stats: Dict[str, Any]


class HealthCheckResponse(BaseModel):
    status: str
    ollama_available: bool
    endpoint: str


# Placeholder admin authentication
async def require_admin():
    """Placeholder for admin authentication (replace with JWT)."""
    pass


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    ollama_service: OllamaModelService = Depends(get_ollama_service)
):
    """Check if Ollama service is accessible."""
    try:
        is_healthy = await ollama_service.health_check()
        return HealthCheckResponse(
            status="healthy" if is_healthy else "unhealthy",
            ollama_available=is_healthy,
            endpoint=ollama_service.ollama_url
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            status="error",
            ollama_available=False,
            endpoint=ollama_service.ollama_url
        )


@router.get("/models", response_model=ModelsListResponse)
async def list_models(
    _: None = Depends(require_admin),
    ollama_service: OllamaModelService = Depends(get_ollama_service)
):
    """List all installed Ollama models."""
    try:
        models = await ollama_service.list_installed_models()
        logger.info(f"Listed {len(models)} Ollama models")
        return ModelsListResponse(models=models, total=len(models))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/running", response_model=RunningModelsResponse)
async def list_running_models(
    _: None = Depends(require_admin),
    ollama_service: OllamaModelService = Depends(get_ollama_service)
):
    """List currently running/loaded Ollama models."""
    try:
        running = await ollama_service.get_running_models()
        return RunningModelsResponse(running_models=running, total=len(running))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing running models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=ModelStatsResponse)
async def get_model_stats(
    _: None = Depends(require_admin),
    ollama_service: OllamaModelService = Depends(get_ollama_service)
):
    """Get statistics about installed models."""
    try:
        stats = await ollama_service.get_model_stats()
        return ModelStatsResponse(stats=stats)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_name:path}", response_model=ModelDetailsResponse)
async def get_model_details(
    model_name: str,
    _: None = Depends(require_admin),
    ollama_service: OllamaModelService = Depends(get_ollama_service)
):
    """Get detailed information about a specific model."""
    try:
        details = await ollama_service.get_model_details(model_name)
        is_installed = await ollama_service.check_model_exists(model_name)
        return ModelDetailsResponse(
            model_name=model_name,
            details=details,
            is_installed=is_installed
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting model details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------------------------------
# Phase 2: Model Management Endpoints
# -------------------------------------------------------------------------

class PullModelRequest(BaseModel):
    """Request to pull/install a model."""
    model_name: str = Field(..., description="Model name to pull (e.g., 'llama2:latest', 'mistral:7b')")


class DeleteModelRequest(BaseModel):
    """Request to delete a model."""
    model_name: str = Field(..., description="Model name to delete")


class DeleteModelResponse(BaseModel):
    """Response after deleting a model."""
    success: bool
    model_name: str
    message: str


@router.post("/pull")
async def pull_model(
    model_name: str = Body(..., embed=True),
    _: None = Depends(require_admin),
    ollama_service: OllamaModelService = Depends(get_ollama_service)
):
    """
    Pull/install a new Ollama model with streaming progress updates.

    Returns Server-Sent Events (SSE) stream with progress updates.
    Each event contains JSON data with status, progress, etc.
    """
    async def generate_progress():
        """Generate SSE events from pull progress."""
        try:
            async for progress_data in ollama_service.pull_model(model_name):
                # Format as Server-Sent Event
                json_data = json.dumps(progress_data)
                yield f"data: {json_data}\n\n"

        except ValueError as e:
            # Model not found
            error_data = {
                "status": "error",
                "error": str(e),
                "code": "model_not_found"
            }
            yield f"data: {json.dumps(error_data)}\n\n"

        except ConnectionError as e:
            # Connection error
            error_data = {
                "status": "error",
                "error": str(e),
                "code": "connection_error"
            }
            yield f"data: {json.dumps(error_data)}\n\n"

        except Exception as e:
            # Unexpected error
            logger.error(f"Error pulling model {model_name}: {e}")
            error_data = {
                "status": "error",
                "error": str(e),
                "code": "internal_error"
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        generate_progress(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.delete("/models/{model_name:path}", response_model=DeleteModelResponse)
async def delete_model(
    model_name: str,
    _: None = Depends(require_admin),
    ollama_service: OllamaModelService = Depends(get_ollama_service)
):
    """Delete an installed Ollama model."""
    try:
        success = await ollama_service.delete_model(model_name)
        return DeleteModelResponse(
            success=success,
            model_name=model_name,
            message=f"Successfully deleted model: {model_name}"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting model {model_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
