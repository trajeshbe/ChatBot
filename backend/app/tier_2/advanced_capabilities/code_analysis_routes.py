"""Code Analysis & Review AI - API Routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from app.services.module_config_helper import load_module_config
from .code_analysis_service import CodeAnalysisService
from .code_analysis_schemas import *

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/modules/code-analysis", tags=["Code Analysis"])

@router.post("/analyze", response_model=AnalyzeCodeResponse)
async def analyze_code(
    request: AnalyzeCodeRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """Perform comprehensive code analysis with AI insights"""
    try:
        return await CodeAnalysisService(db, settings).analyze_code(request)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=SearchAnalysesResponse)
async def search_analyses(
    request: SearchAnalysesRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """Search historical code analyses"""
    try:
        return await CodeAnalysisService(db, settings).search_analyses(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export", response_model=ExportAnalysesResponse)
async def export_analyses(
    request: ExportAnalysesRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """Export code analyses in specified format"""
    try:
        return await CodeAnalysisService(db, settings).export_analyses(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=CodeAnalysisStatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """Get code analysis statistics"""
    try:
        return await CodeAnalysisService(db, settings).get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=StatusResponse)
async def get_status(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """Get service status and capabilities"""
    try:
        return await CodeAnalysisService(db, settings).get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
