"""Healthcare Diagnostics AI - API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from .healthcare_diagnostics_service import HealthcareDiagnosticsService
from .healthcare_diagnostics_schemas import *

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/modules/healthcare-diagnostics", tags=["Healthcare Diagnostics"])


@router.post("/analyze", response_model=AnalyzeSymptomsResponse)
async def analyze_symptoms(
    request: AnalyzeSymptomsRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Analyze patient symptoms with AI diagnostics"""
    try:
        service = HealthcareDiagnosticsService(db, settings)
        return await service.analyze_symptoms(request)
    except Exception as e:
        logger.error(f"Error in analyze_symptoms: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchDiagnosesResponse)
async def search_diagnoses(
    request: SearchDiagnosesRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Search historical diagnoses"""
    try:
        service = HealthcareDiagnosticsService(db, settings)
        return await service.search_diagnoses(request)
    except Exception as e:
        logger.error(f"Error in search_diagnoses: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export", response_model=ExportDiagnosesResponse)
async def export_diagnoses(
    request: ExportDiagnosesRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Export diagnostic data"""
    try:
        service = HealthcareDiagnosticsService(db, settings)
        return await service.export_diagnoses(request)
    except Exception as e:
        logger.error(f"Error in export_diagnoses: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=DiagnosticStatsResponse)
async def get_stats(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Get diagnostic statistics"""
    try:
        service = HealthcareDiagnosticsService(db, settings)
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
        service = HealthcareDiagnosticsService(db, settings)
        return await service.get_status()
    except Exception as e:
        logger.error(f"Error in get_status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
