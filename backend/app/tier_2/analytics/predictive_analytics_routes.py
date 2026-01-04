"""Predictive Analytics Engine - API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from app.services.module_config_helper import load_module_config
from .predictive_analytics_service import PredictiveAnalyticsService
from .predictive_analytics_schemas import *

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/modules/predictive-analytics", tags=["Predictive Analytics"])


@router.post("/forecast", response_model=ForecastResponse)
async def generate_forecast(
    request: ForecastRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Generate time series forecast with AI-powered analysis"""
    try:
        # Load module configuration
        module_config = await load_module_config(db, "predictive_analytics")
        logger.info(f"✓ Loaded config for predictive_analytics")

        # Initialize service with config
        service = PredictiveAnalyticsService(db, settings, config=module_config)
        return await service.generate_forecast(request)
    except Exception as e:
        logger.error(f"Error in generate_forecast: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchForecastsResponse)
async def search_forecasts(
    request: SearchForecastsRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Search historical forecasts"""
    try:
        service = PredictiveAnalyticsService(db, settings)
        return await service.search_forecasts(request)
    except Exception as e:
        logger.error(f"Error in search_forecasts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export", response_model=ExportForecastsResponse)
async def export_forecasts(
    request: ExportForecastsRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Export forecasts"""
    try:
        service = PredictiveAnalyticsService(db, settings)
        return await service.export_forecasts(request)
    except Exception as e:
        logger.error(f"Error in export_forecasts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=PredictiveStatsResponse)
async def get_stats(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Get predictive analytics statistics"""
    try:
        service = PredictiveAnalyticsService(db, settings)
        return await service.get_stats()
    except Exception as e:
        logger.error(f"Error in get_stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=StatusResponse)
async def get_status(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Get service status"""
    try:
        service = PredictiveAnalyticsService(db, settings)
        return await service.get_status()
    except Exception as e:
        logger.error(f"Error in get_status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
