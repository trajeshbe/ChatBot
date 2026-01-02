"""Legal Document Analyzer - API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from .legal_document_service import LegalDocumentService
from .legal_document_schemas import *

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/modules/legal-document", tags=["Legal Document"])


@router.post("/analyze", response_model=AnalyzeDocumentResponse)
async def analyze_document(
    request: AnalyzeDocumentRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Analyze legal document with AI"""
    try:
        service = LegalDocumentService(db, settings)
        return await service.analyze_document(request)
    except Exception as e:
        logger.error(f"Error in analyze_document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchDocumentsResponse)
async def search_documents(
    request: SearchDocumentsRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Search analyzed documents"""
    try:
        service = LegalDocumentService(db, settings)
        return await service.search_documents(request)
    except Exception as e:
        logger.error(f"Error in search_documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export", response_model=ExportAnalysisResponse)
async def export_analysis(
    request: ExportAnalysisRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Export document analysis"""
    try:
        service = LegalDocumentService(db, settings)
        return await service.export_analysis(request)
    except Exception as e:
        logger.error(f"Error in export_analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=LegalStatsResponse)
async def get_stats(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Get legal analysis statistics"""
    try:
        service = LegalDocumentService(db, settings)
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
        service = LegalDocumentService(db, settings)
        return await service.get_status()
    except Exception as e:
        logger.error(f"Error in get_status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
