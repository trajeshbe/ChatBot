"""Insurance Risk Assessor - API Routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from .insurance_risk_service import InsuranceRiskService
from .insurance_risk_schemas import *

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/modules/insurance-risk", tags=["Insurance Risk"])

@router.post("/assess", response_model=AssessRiskResponse)
async def assess_risk(request: AssessRiskRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    try:
        return await InsuranceRiskService(db, settings).assess_risk(request)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=SearchAssessmentsResponse)
async def search_assessments(request: SearchAssessmentsRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    try:
        return await InsuranceRiskService(db, settings).search_assessments(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export", response_model=ExportAssessmentsResponse)
async def export_assessments(request: ExportAssessmentsRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    try:
        return await InsuranceRiskService(db, settings).export_assessments(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=InsuranceStatsResponse)
async def get_stats(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    try:
        return await InsuranceRiskService(db, settings).get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=StatusResponse)
async def get_status(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    try:
        return await InsuranceRiskService(db, settings).get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
