"""
System Configuration API Routes

Provides REST API for managing system configuration from database.
Allows dynamic configuration updates without restarting services.

Author: AI Assistant
Date: 2026-01-07
Related: Phase 2 - Requirement #8
"""

import logging
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.system_config_service import SystemConfigService
from app.models.database import SystemConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/system/config", tags=["System Configuration"])


# Pydantic models for request/response
class SystemConfigResponse(BaseModel):
    """Response model for system configuration"""
    config_key: str
    config_value: str
    config_type: str
    category: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class SystemConfigUpdate(BaseModel):
    """Request model for updating system configuration"""
    config_value: str = Field(..., description="Configuration value")
    description: Optional[str] = Field(None, description="Optional description")


class SystemConfigCreate(BaseModel):
    """Request model for creating system configuration"""
    config_key: str = Field(..., description="Configuration key (e.g., 'agent.runtime.default_model')")
    config_value: str = Field(..., description="Configuration value")
    config_type: str = Field(default='string', description="Type: string, integer, boolean, json, url, api_key")
    category: Optional[str] = Field(None, description="Category: agent, embedding, ollama, prefect, rag, system")
    description: Optional[str] = Field(None, description="Description of the configuration")


@router.get("/{config_key}", response_model=SystemConfigResponse)
async def get_config(
    config_key: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific system configuration value.

    Args:
        config_key: Configuration key (e.g., 'agent.runtime.default_model')

    Returns:
        System configuration object

    Example:
        GET /api/v1/system/config/agent.runtime.default_model
    """
    try:
        config_service = SystemConfigService(db)

        # Get the config directly from database
        from sqlalchemy import select
        result = await db.execute(
            select(SystemConfig).where(
                SystemConfig.config_key == config_key,
                SystemConfig.is_active == True
            )
        )
        config = result.scalar_one_or_none()

        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Configuration '{config_key}' not found"
            )

        return config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get config '{config_key}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[SystemConfigResponse])
async def list_configs(
    category: Optional[str] = Query(None, description="Filter by category"),
    active_only: bool = Query(True, description="Only return active configs"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all system configurations, optionally filtered by category.

    Args:
        category: Optional category filter (agent, embedding, ollama, etc.)
        active_only: Only return active configurations

    Returns:
        List of system configuration objects

    Examples:
        GET /api/v1/system/config
        GET /api/v1/system/config?category=agent
        GET /api/v1/system/config?active_only=false
    """
    try:
        config_service = SystemConfigService(db)

        if category:
            configs = await config_service.get_by_category(category, active_only=active_only)
        else:
            # Get all configs
            from sqlalchemy import select
            query = select(SystemConfig)
            if active_only:
                query = query.where(SystemConfig.is_active == True)

            query = query.order_by(SystemConfig.category, SystemConfig.config_key)
            result = await db.execute(query)
            configs = list(result.scalars().all())

        return configs

    except Exception as e:
        logger.error(f"Failed to list configs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=SystemConfigResponse, status_code=201)
async def create_config(
    config: SystemConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new system configuration.

    Args:
        config: Configuration to create

    Returns:
        Created system configuration object

    Example:
        POST /api/v1/system/config
        {
            "config_key": "agent.runtime.default_model",
            "config_value": "qwen2.5-coder:14b",
            "config_type": "string",
            "category": "agent",
            "description": "Default LLM model for agent tasks"
        }
    """
    try:
        config_service = SystemConfigService(db)

        # Create config
        success = await config_service.set(
            key=config.config_key,
            value=config.config_value,
            config_type=config.config_type,
            description=config.description,
            category=config.category
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to create configuration")

        # Fetch and return the created config
        from sqlalchemy import select
        result = await db.execute(
            select(SystemConfig).where(SystemConfig.config_key == config.config_key)
        )
        created_config = result.scalar_one()

        return created_config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{config_key}", response_model=SystemConfigResponse)
async def update_config(
    config_key: str,
    update: SystemConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing system configuration.

    Args:
        config_key: Configuration key to update
        update: New configuration value

    Returns:
        Updated system configuration object

    Example:
        PUT /api/v1/system/config/agent.runtime.default_model
        {
            "config_value": "llama3.2:3b",
            "description": "Updated to use lighter model"
        }
    """
    try:
        config_service = SystemConfigService(db)

        # Check if exists
        existing_value = await config_service.get(config_key)
        if existing_value is None:
            raise HTTPException(
                status_code=404,
                detail=f"Configuration '{config_key}' not found"
            )

        # Update config
        success = await config_service.set(
            key=config_key,
            value=update.config_value,
            description=update.description
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update configuration")

        # Fetch and return the updated config
        from sqlalchemy import select
        result = await db.execute(
            select(SystemConfig).where(SystemConfig.config_key == config_key)
        )
        updated_config = result.scalar_one()

        return updated_config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update config '{config_key}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{config_key}", status_code=204)
async def delete_config(
    config_key: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete (deactivate) a system configuration.

    Note: This marks the config as inactive rather than deleting it.

    Args:
        config_key: Configuration key to delete

    Returns:
        204 No Content on success

    Example:
        DELETE /api/v1/system/config/agent.runtime.custom_setting
    """
    try:
        config_service = SystemConfigService(db)

        success = await config_service.delete(config_key)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Configuration '{config_key}' not found"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete config '{config_key}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear", status_code=204)
async def clear_cache():
    """
    Clear the system configuration cache.

    Useful after making database changes directly or when testing.

    Returns:
        204 No Content on success

    Example:
        POST /api/v1/system/config/cache/clear
    """
    try:
        SystemConfigService.clear_cache()
        logger.info("System config cache cleared")
        return None

    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))
