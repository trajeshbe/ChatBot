"""Educational Content Recommender - API Routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from .educational_content_service import EducationalContentService
from .educational_content_schemas import *

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/modules/educational-content", tags=["Educational Content"])

@router.post("/recommend", response_model=RecommendContentResponse)
async def recommend_content(request: RecommendContentRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    try:
        return await EducationalContentService(db, settings).recommend_content(request)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=SearchRecommendationsResponse)
async def search_recommendations(request: SearchRecommendationsRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    try:
        return await EducationalContentService(db, settings).search_recommendations(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export", response_model=ExportRecommendationsResponse)
async def export_recommendations(request: ExportRecommendationsRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    try:
        return await EducationalContentService(db, settings).export_recommendations(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=EducationalStatsResponse)
async def get_stats(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    try:
        return await EducationalContentService(db, settings).get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=StatusResponse)
async def get_status(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    try:
        return await EducationalContentService(db, settings).get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
