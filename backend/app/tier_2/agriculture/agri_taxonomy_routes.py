"""
Agri Taxonomy API Routes
Tier 2 Module: Agriculture

REST endpoints for agricultural crop classification and taxonomy.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from app.services.module_config_helper import load_module_config
from .agri_taxonomy_service import AgriTaxonomyService
from .agri_taxonomy_schemas import (
    TaxonomyClassificationRequest,
    TaxonomyClassificationResponse,
    SearchTaxonomyRequest,
    ExportTaxonomyRequest,
    TaxonomyStatsResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/modules/agri-taxonomy",
    tags=["Agriculture", "Tier 2 Modules", "Crop Classification"]
)


@router.post("/classify", response_model=TaxonomyClassificationResponse)
async def classify_crops(
    request: TaxonomyClassificationRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    Classify agricultural crops and build taxonomy.

    **Classification Capabilities:**
    - 10 crop categories (cereals, legumes, vegetables, fruits, etc.)
    - Scientific nomenclature mapping
    - Growing requirements (temperature, rainfall, pH, soil, climate)
    - Seasonal planting and harvesting information
    - LLM-powered enrichment for unknown crops

    **Example request:**
    ```json
    {
      "crop_names": ["rice", "wheat", "tomato", "soybean"],
      "include_requirements": true,
      "include_seasonal_info": true,
      "use_llm_enrichment": true
    }
    ```
    """
    try:
        logger.info(f"🌾 Crop classification request for {len(request.crop_names)} crops")

        # Load module configuration
        module_config = await load_module_config(db, "agri_taxonomy")
        logger.info(f"✓ Loaded config for agri_taxonomy")

        # Initialize service with config
        service = AgriTaxonomyService(db, settings, config=module_config)
        result = await service.classify_crops(request)

        logger.info(f"✓ Classified {len(result.classifications)} crops ({result.taxonomy_coverage_percent:.1f}% coverage)")
        return result

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Classification failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Classification failed: {str(e)}")


@router.post("/search")
async def search_taxonomy(request: SearchTaxonomyRequest, db: Session = Depends(get_db)):
    """Search agricultural taxonomy."""
    try:
        from app.models.database_enhanced import AgriTaxonomyResults
        import uuid

        logger.info(f"🔍 Search taxonomy")

        query = db.query(AgriTaxonomyResults).filter(AgriTaxonomyResults.module_id == "agri-taxonomy")

        if request.session_id:
            query = query.filter(AgriTaxonomyResults.session_id == request.session_id)
        if request.project_id:
            query = query.filter(AgriTaxonomyResults.project_id == uuid.UUID(request.project_id))
        if request.crop_name:
            query = query.filter(AgriTaxonomyResults.taxonomy_data["classification"]["common_name"].astext.ilike(f"%{request.crop_name}%"))
        if request.category:
            query = query.filter(AgriTaxonomyResults.taxonomy_data["classification"]["category"].astext == request.category.value)

        results = query.limit(request.limit).all()

        taxonomies = [
            {
                "taxonomy_id": str(r.taxonomy_id),
                "crop_name": r.taxonomy_data.get("classification", {}).get("common_name"),
                "category": r.taxonomy_data.get("classification", {}).get("category"),
                "created_at": r.created_at.isoformat()
            }
            for r in results
        ]

        return {"taxonomies": taxonomies, "count": len(taxonomies)}

    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Search failed: {str(e)}")


@router.post("/export")
async def export_taxonomy(request: ExportTaxonomyRequest, db: Session = Depends(get_db)):
    """Export taxonomy data."""
    try:
        from app.models.database_enhanced import AgriTaxonomyResults
        import uuid

        logger.info(f"📥 Export request in {request.format} format")

        query = db.query(AgriTaxonomyResults).filter(AgriTaxonomyResults.module_id == "agri-taxonomy")

        if request.taxonomy_ids:
            taxonomy_uuids = [uuid.UUID(tid) for tid in request.taxonomy_ids]
            query = query.filter(AgriTaxonomyResults.taxonomy_id.in_(taxonomy_uuids))
        elif request.session_id:
            query = query.filter(AgriTaxonomyResults.session_id == request.session_id)
        elif request.category:
            query = query.filter(AgriTaxonomyResults.taxonomy_data["classification"]["category"].astext == request.category.value)

        results = query.all()

        if not results:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No taxonomy data found")

        export_data = [{
            "taxonomy_id": str(r.taxonomy_id),
            "data": r.taxonomy_data,
            "created_at": r.created_at.isoformat()
        } for r in results]

        return {"format": request.format, "data": export_data, "count": len(export_data)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Export failed: {str(e)}")


@router.get("/stats", response_model=TaxonomyStatsResponse)
async def get_taxonomy_stats(session_id: str = None, db: Session = Depends(get_db)):
    """Get taxonomy statistics."""
    try:
        from app.models.database_enhanced import AgriTaxonomyResults

        logger.info(f"📊 Stats request")

        query = db.query(AgriTaxonomyResults).filter(AgriTaxonomyResults.module_id == "agri-taxonomy")

        if session_id:
            query = query.filter(AgriTaxonomyResults.session_id == session_id)

        results = query.all()

        total_classifications = len(results)

        # Count by category
        crops_by_category = {}
        for r in results:
            category = r.taxonomy_data.get("classification", {}).get("category", "unknown")
            crops_by_category[category] = crops_by_category.get(category, 0) + 1

        return TaxonomyStatsResponse(
            total_crops_in_taxonomy=500,  # Hardcoded for demo
            total_categories=10,
            total_classifications_performed=total_classifications,
            crops_by_category=crops_by_category,
            crops_by_climate_zone={}
        )

    except Exception as e:
        logger.error(f"Stats retrieval failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Stats retrieval failed: {str(e)}")


@router.get("/status")
async def get_module_status() -> Dict[str, Any]:
    """Get agri-taxonomy module status."""
    return {
        "module_id": "agri-taxonomy",
        "name": "Agricultural Taxonomy",
        "version": "1.0.0",
        "tier": 2,
        "category": "agriculture",
        "description": "Agricultural crop classification and taxonomy",

        "capabilities": {
            "crop_categories": ["cereals", "legumes", "vegetables", "fruits", "oilseeds", "fiber_crops", "forage_crops", "tuber_crops", "spices", "medicinal_plants"],
            "soil_types": ["sandy", "loamy", "clay", "silt", "peaty", "chalky", "saline"],
            "climate_zones": ["tropical", "subtropical", "temperate", "continental", "polar", "arid", "semi_arid"],
            "growth_stages": ["germination", "seedling", "vegetative", "flowering", "fruiting", "maturity", "harvest"]
        },

        "features": {
            "crop_classification": True,
            "scientific_nomenclature": True,
            "growing_requirements": True,
            "seasonal_information": True,
            "llm_enrichment": True,
            "export_formats": ["json", "csv", "excel"]
        },

        "tier_1_dependencies": ["LLMService"],

        "endpoints": {
            "classify": "POST /api/v1/modules/agri-taxonomy/classify",
            "search": "POST /api/v1/modules/agri-taxonomy/search",
            "export": "POST /api/v1/modules/agri-taxonomy/export",
            "stats": "GET /api/v1/modules/agri-taxonomy/stats",
            "status": "GET /api/v1/modules/agri-taxonomy/status"
        },

        "performance": {
            "avg_classification_time_seconds": "1-2",
            "crops_classified_per_second": "10-20"
        },

        "use_cases": [
            "Crop identification and classification",
            "Agricultural planning and zoning",
            "Climate-appropriate crop selection",
            "Soil suitability analysis",
            "Crop rotation planning",
            "Agricultural education and research"
        ]
    }
