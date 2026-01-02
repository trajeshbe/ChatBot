"""Solera POC - API Routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from .solera_service import SoleraService
from .solera_schemas import *

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/customer/solera", tags=["Solera POC"])

@router.post("/process", response_model=SoleraResponse)
async def process_request(
    request: SoleraRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """Process customer-specific request"""
    try:
        return await SoleraService(db, settings).process_request(request)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=StatusResponse)
async def get_status(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """Get POC status"""
    try:
        return await SoleraService(db, settings).get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
