"""Legal Document Analyzer - API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from app.services.module_config_helper import load_module_config
from .legal_document_service import LegalDocumentService
from .legal_document_schemas import *

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/modules/legal-document", tags=["Legal Document"])


@router.post("/analyze", response_model=AnalyzeDocumentResponse)
async def analyze_document(
    request: AnalyzeDocumentRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Analyze legal document with AI"""
    try:
        # Load module configuration
        module_config = await load_module_config(db, "legal_document")
        logger.info(f"✓ Loaded config for legal_document")

        # Initialize service with config
        service = LegalDocumentService(db, settings, config=module_config)
        return await service.analyze_document(request)
    except Exception as e:
        logger.error(f"Error in analyze_document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchDocumentsResponse)
async def search_documents(
    request: SearchDocumentsRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Search analyzed documents"""
    try:
        # Load module configuration
        module_config = await load_module_config(db, "legal_document")
        logger.info(f"✓ Loaded config for legal_document")

        # Initialize service with config
        service = LegalDocumentService(db, settings, config=module_config)
        return await service.search_documents(request)
    except Exception as e:
        logger.error(f"Error in search_documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export", response_model=ExportAnalysisResponse)
async def export_analysis(
    request: ExportAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Export document analysis"""
    try:
        # Load module configuration
        module_config = await load_module_config(db, "legal_document")
        logger.info(f"✓ Loaded config for legal_document")

        # Initialize service with config
        service = LegalDocumentService(db, settings, config=module_config)
        return await service.export_analysis(request)
    except Exception as e:
        logger.error(f"Error in export_analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=LegalStatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Get legal analysis statistics"""
    try:
        # Load module configuration
        module_config = await load_module_config(db, "legal_document")
        logger.info(f"✓ Loaded config for legal_document")

        # Initialize service with config
        service = LegalDocumentService(db, settings, config=module_config)
        return await service.get_stats()
    except Exception as e:
        logger.error(f"Error in get_stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=StatusResponse)
async def get_status(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Get service status"""
    try:
        # Load module configuration
        module_config = await load_module_config(db, "legal_document")
        logger.info(f"✓ Loaded config for legal_document")

        # Initialize service with config
        service = LegalDocumentService(db, settings, config=module_config)
        return await service.get_status()
    except Exception as e:
        logger.error(f"Error in get_status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
