"""Real Estate Valuation AI - API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from app.services.module_config_helper import load_module_config
from .real_estate_service import RealEstateService
from .real_estate_schemas import *

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/modules/real-estate", tags=["Real Estate"])

@router.post("/valuate", response_model=ValuationResponse)
async def valuate_property(request: ValuationRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    try:
        return await RealEstateService(db, settings).valuate_property(request)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=SearchValuationsResponse)
async def search_valuations(request: SearchValuationsRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    try:
        return await RealEstateService(db, settings).search_valuations(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export", response_model=ExportValuationsResponse)
async def export_valuations(request: ExportValuationsRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    try:
        return await RealEstateService(db, settings).export_valuations(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=ValuationStatsResponse)
async def get_stats(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    try:
        return await RealEstateService(db, settings).get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=StatusResponse)
async def get_status(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    try:
        return await RealEstateService(db, settings).get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
