"""Financial Anomaly Detector - API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from app.services.module_config_helper import load_module_config
from .financial_anomaly_service import FinancialAnomalyService
from .financial_anomaly_schemas import *

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/modules/financial-anomaly", tags=["Financial Anomaly"])


@router.post("/detect", response_model=DetectAnomaliesResponse)
async def detect_anomalies(
    request: DetectAnomaliesRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Detect financial anomalies with AI-powered analysis"""
    try:
        # Load module configuration
        module_config = await load_module_config(db, "financial_anomaly")
        logger.info(f"✓ Loaded config for financial_anomaly")

        # Initialize service with config
        service = FinancialAnomalyService(db, settings, config=module_config)
        return await service.detect_anomalies(request)
    except Exception as e:
        logger.error(f"Error in detect_anomalies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchAnomaliesResponse)
async def search_anomalies(
    request: SearchAnomaliesRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Search historical anomaly data"""
    try:
        service = FinancialAnomalyService(db, settings)
        return await service.search_anomalies(request)
    except Exception as e:
        logger.error(f"Error in search_anomalies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export", response_model=ExportAnomaliesResponse)
async def export_anomalies(
    request: ExportAnomaliesRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Export anomaly data"""
    try:
        service = FinancialAnomalyService(db, settings)
        return await service.export_anomalies(request)
    except Exception as e:
        logger.error(f"Error in export_anomalies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=AnomalyStatsResponse)
async def get_stats(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Get anomaly detection statistics"""
    try:
        service = FinancialAnomalyService(db, settings)
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
        service = FinancialAnomalyService(db, settings)
        return await service.get_status()
    except Exception as e:
        logger.error(f"Error in get_status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
