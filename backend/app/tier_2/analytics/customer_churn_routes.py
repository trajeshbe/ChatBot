"""Customer Churn Predictor - API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from .customer_churn_service import CustomerChurnService
from .customer_churn_schemas import *

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/modules/customer-churn", tags=["Customer Churn"])


@router.post("/predict", response_model=PredictChurnResponse)
async def predict_churn(
    request: PredictChurnRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Predict customer churn with AI-powered analysis"""
    try:
        service = CustomerChurnService(db, settings)
        return await service.predict_churn(request)
    except Exception as e:
        logger.error(f"Error in predict_churn: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchPredictionsResponse)
async def search_predictions(
    request: SearchPredictionsRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Search historical churn predictions"""
    try:
        service = CustomerChurnService(db, settings)
        return await service.search_predictions(request)
    except Exception as e:
        logger.error(f"Error in search_predictions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export", response_model=ExportPredictionsResponse)
async def export_predictions(
    request: ExportPredictionsRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Export churn predictions"""
    try:
        service = CustomerChurnService(db, settings)
        return await service.export_predictions(request)
    except Exception as e:
        logger.error(f"Error in export_predictions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=ChurnStatsResponse)
async def get_stats(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Get customer churn statistics"""
    try:
        service = CustomerChurnService(db, settings)
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
        service = CustomerChurnService(db, settings)
        return await service.get_status()
    except Exception as e:
        logger.error(f"Error in get_status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
