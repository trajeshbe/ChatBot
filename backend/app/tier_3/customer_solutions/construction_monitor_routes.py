"""Construction Monitor POC - API Routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from .construction_monitor_service import Construction_monitorService
from .construction_monitor_schemas import *

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/customer/construction_monitor", tags=["Construction Monitor POC"])

@router.post("/process", response_model=Construction_monitorResponse)
async def process_request(
    request: Construction_monitorRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """Process customer-specific request"""
    try:
        return await Construction_monitorService(db, settings).process_request(request)
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
        return await Construction_monitorService(db, settings).get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
