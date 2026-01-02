"""Multilingual Content Translator - API Routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from .multilingual_translator_service import MultilingualTranslatorService
from .multilingual_translator_schemas import *

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/modules/multilingual-translator", tags=["Multilingual Translator"])

@router.post("/translate", response_model=TranslateResponse)
async def translate_content(
    request: TranslateRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """Translate content into multiple target languages with quality assessment"""
    try:
        return await MultilingualTranslatorService(db, settings).translate_content(request)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=SearchTranslationsResponse)
async def search_translations(
    request: SearchTranslationsRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """Search historical translations"""
    try:
        return await MultilingualTranslatorService(db, settings).search_translations(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export", response_model=ExportTranslationsResponse)
async def export_translations(
    request: ExportTranslationsRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """Export translations in specified format"""
    try:
        return await MultilingualTranslatorService(db, settings).export_translations(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=TranslationStatsResponse)
async def get_stats(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """Get translation statistics"""
    try:
        return await MultilingualTranslatorService(db, settings).get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=StatusResponse)
async def get_status(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """Get service status and capabilities"""
    try:
        return await MultilingualTranslatorService(db, settings).get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
