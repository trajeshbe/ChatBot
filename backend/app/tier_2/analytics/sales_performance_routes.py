"""Sales Performance Analytics - API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from app.services.module_config_helper import load_module_config
from .sales_performance_service import SalesPerformanceService
from .sales_performance_schemas import *

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/modules/sales-performance", tags=["Sales Performance"])


@router.post("/analyze", response_model=AnalyzeSalesResponse)
async def analyze_sales(
    request: AnalyzeSalesRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Analyze sales performance with AI-powered insights"""
    try:
        # Load module configuration
        module_config = await load_module_config(db, "sales_performance")
        logger.info(f"✓ Loaded config for sales_performance")

        # Initialize service with config
        service = SalesPerformanceService(db, settings, config=module_config)
        return await service.analyze_sales(request)
    except Exception as e:
        logger.error(f"Error in analyze_sales: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchPerformanceResponse)
async def search_performance(
    request: SearchPerformanceRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Search historical sales performance data"""
    try:
        service = SalesPerformanceService(db, settings)
        return await service.search_performance(request)
    except Exception as e:
        logger.error(f"Error in search_performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export", response_model=ExportPerformanceResponse)
async def export_performance(
    request: ExportPerformanceRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Export sales performance data"""
    try:
        service = SalesPerformanceService(db, settings)
        return await service.export_performance(request)
    except Exception as e:
        logger.error(f"Error in export_performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=PerformanceStatsResponse)
async def get_stats(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Get sales performance statistics"""
    try:
        service = SalesPerformanceService(db, settings)
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
        service = SalesPerformanceService(db, settings)
        return await service.get_status()
    except Exception as e:
        logger.error(f"Error in get_status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
