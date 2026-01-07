"""
Models Registry API Routes

Provides REST API for managing LLM models registry.
Supports manual registration and Ollama auto-discovery.

Author: AI Assistant
Date: 2026-01-07
Related: Phase 2 - Requirement #2 (Ollama Auto-Registration)
"""

import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.database import Model
from app.services.model_registry_sync_service import ModelRegistrySyncService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/models", tags=["Models Registry"])


# Pydantic models for request/response
class ModelResponse(BaseModel):
    """Response model for LLM model"""
    model_id: str
    display_name: str
    provider: str
    model_type: str
    context_length: Optional[int] = None
    max_tokens: Optional[int] = None
    supports_functions: bool = False
    supports_vision: bool = False
    supports_streaming: bool = True
    cost_per_1k_input: Optional[float] = None
    cost_per_1k_output: Optional[float] = None
    is_active: bool = True
    is_default: bool = False
    source: str = 'manual'
    auto_discovered_at: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ModelCreate(BaseModel):
    """Request model for creating/registering a model"""
    model_id: str = Field(..., description="Model identifier (e.g., 'gpt-4o', 'qwen2.5-coder:7b')")
    display_name: str = Field(..., description="Human-readable name")
    provider: str = Field(..., description="Provider: openai, anthropic, ollama, vllm, finetuned")
    model_type: str = Field(default='text', description="Type: text, code, vision, multimodal")
    context_length: Optional[int] = Field(None, description="Context window size")
    max_tokens: Optional[int] = Field(None, description="Max output tokens")
    supports_functions: bool = Field(default=False, description="Supports function calling")
    supports_vision: bool = Field(default=False, description="Supports vision/images")
    cost_per_1k_input: Optional[float] = Field(None, description="Cost per 1k input tokens")
    cost_per_1k_output: Optional[float] = Field(None, description="Cost per 1k output tokens")


class SyncResponse(BaseModel):
    """Response model for sync operation"""
    total_discovered: int
    new_models: int
    updated_models: int
    models_marked_inactive: int = 0
    errors: List[str] = []


@router.get("", response_model=List[ModelResponse])
async def list_models(
    provider: Optional[str] = Query(None, description="Filter by provider"),
    model_type: Optional[str] = Query(None, description="Filter by type"),
    active_only: bool = Query(True, description="Only return active models"),
    source: Optional[str] = Query(None, description="Filter by source (manual, auto_discovered, finetuned)"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all registered models.

    Args:
        provider: Optional provider filter (openai, anthropic, ollama, etc.)
        model_type: Optional type filter (text, code, vision, multimodal)
        active_only: Only return active models
        source: Optional source filter

    Returns:
        List of model objects

    Examples:
        GET /api/v1/models
        GET /api/v1/models?provider=ollama
        GET /api/v1/models?model_type=code
        GET /api/v1/models?source=auto_discovered
    """
    try:
        query = select(Model)

        if provider:
            query = query.where(Model.provider == provider)

        if model_type:
            query = query.where(Model.model_type == model_type)

        if active_only:
            query = query.where(Model.is_active == True)

        if source:
            query = query.where(Model.source == source)

        query = query.order_by(Model.provider, Model.model_type, Model.display_name)

        result = await db.execute(query)
        models = list(result.scalars().all())

        return models

    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers", response_model=List[str])
async def list_providers(
    db: AsyncSession = Depends(get_db)
):
    """
    List all unique providers.

    Returns:
        List of provider names

    Example:
        GET /api/v1/models/providers
        Returns: ["openai", "anthropic", "ollama"]
    """
    try:
        result = await db.execute(
            select(Model.provider).distinct().order_by(Model.provider)
        )
        providers = [row[0] for row in result.all()]
        return providers

    except Exception as e:
        logger.error(f"Failed to list providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_model_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics about registered models.

    Returns:
        Model statistics (counts by provider, type, source, etc.)

    Example:
        GET /api/v1/models/stats
    """
    try:
        # Total models
        total_result = await db.execute(select(func.count(Model.id)))
        total_models = total_result.scalar()

        # Active models
        active_result = await db.execute(
            select(func.count(Model.id)).where(Model.is_active == True)
        )
        active_models = active_result.scalar()

        # By provider
        provider_result = await db.execute(
            select(Model.provider, func.count(Model.id))
            .group_by(Model.provider)
            .order_by(Model.provider)
        )
        by_provider = {row[0]: row[1] for row in provider_result.all()}

        # By type
        type_result = await db.execute(
            select(Model.model_type, func.count(Model.id))
            .group_by(Model.model_type)
            .order_by(Model.model_type)
        )
        by_type = {row[0]: row[1] for row in type_result.all()}

        # By source
        source_result = await db.execute(
            select(Model.source, func.count(Model.id))
            .group_by(Model.source)
            .order_by(Model.source)
        )
        by_source = {row[0]: row[1] for row in source_result.all()}

        return {
            "total_models": total_models,
            "active_models": active_models,
            "by_provider": by_provider,
            "by_type": by_type,
            "by_source": by_source
        }

    except Exception as e:
        logger.error(f"Failed to get model stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific model by ID.

    Args:
        model_id: Model identifier

    Returns:
        Model object

    Example:
        GET /api/v1/models/qwen2.5-coder:7b
    """
    try:
        result = await db.execute(
            select(Model).where(Model.model_id == model_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(
                status_code=404,
                detail=f"Model '{model_id}' not found"
            )

        return model

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model '{model_id}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=ModelResponse, status_code=201)
async def register_model(
    model: ModelCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new model manually.

    Args:
        model: Model to register

    Returns:
        Created model object

    Example:
        POST /api/v1/models
        {
            "model_id": "gpt-4o",
            "display_name": "GPT-4o",
            "provider": "openai",
            "model_type": "multimodal",
            "context_length": 128000,
            "max_tokens": 16384,
            "supports_functions": true,
            "supports_vision": true,
            "cost_per_1k_input": 0.0025,
            "cost_per_1k_output": 0.01
        }
    """
    try:
        # Check if already exists
        existing_result = await db.execute(
            select(Model).where(Model.model_id == model.model_id)
        )
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail=f"Model '{model.model_id}' already exists"
            )

        # Create new model
        new_model = Model(
            model_id=model.model_id,
            display_name=model.display_name,
            provider=model.provider,
            model_type=model.model_type,
            context_length=model.context_length,
            max_tokens=model.max_tokens,
            supports_functions=model.supports_functions,
            supports_vision=model.supports_vision,
            cost_per_1k_input=model.cost_per_1k_input,
            cost_per_1k_output=model.cost_per_1k_output,
            is_active=True,
            source='manual'
        )

        db.add(new_model)
        await db.commit()
        await db.refresh(new_model)

        logger.info(f"Registered new model: {model.model_id}")

        return new_model

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register model: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/ollama", response_model=SyncResponse)
async def sync_ollama_models(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger Ollama model synchronization.

    This will discover all installed Ollama models and register them.

    Returns:
        Sync statistics

    Example:
        POST /api/v1/models/sync/ollama
    """
    try:
        sync_service = ModelRegistrySyncService(db)
        stats = await sync_service.run_once()

        logger.info(f"Ollama sync completed: {stats}")

        return stats

    except Exception as e:
        logger.error(f"Failed to sync Ollama models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{model_id}", status_code=204)
async def deactivate_model(
    model_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate a model (mark as inactive).

    Note: This marks the model as inactive rather than deleting it.

    Args:
        model_id: Model identifier

    Returns:
        204 No Content on success

    Example:
        DELETE /api/v1/models/qwen2.5-coder:7b
    """
    try:
        result = await db.execute(
            select(Model).where(Model.model_id == model_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(
                status_code=404,
                detail=f"Model '{model_id}' not found"
            )

        model.is_active = False
        model.updated_at = datetime.now()

        await db.commit()

        logger.info(f"Deactivated model: {model_id}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate model '{model_id}': {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
