"""British Council POC - API Routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from .british_council_service import British_councilService
from .british_council_schemas import *

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/customer/british_council", tags=["British Council POC"])

@router.post("/process", response_model=British_councilResponse)
async def process_request(
    request: British_councilRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """Process customer-specific request"""
    try:
        return await British_councilService(db, settings).process_request(request)
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
        return await British_councilService(db, settings).get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
