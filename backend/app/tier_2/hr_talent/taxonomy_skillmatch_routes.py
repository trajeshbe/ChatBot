"""
Taxonomy Skillmatch API Routes
Tier 2 Module: HR & Talent

REST endpoints for skill taxonomy mapping and matching.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from app.services.module_config_helper import load_module_config
from .taxonomy_skillmatch_service import TaxonomySkillmatchService
from .taxonomy_skillmatch_schemas import (
    SkillTaxonomyRequest,
    SkillTaxonomyResponse,
    SkillMatchRequest,
    SkillMatchResponse,
    SearchTaxonomyRequest,
    ExportTaxonomyRequest,
    TaxonomyStatsResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/modules/taxonomy-skillmatch",
    tags=["HR & Talent", "Tier 2 Modules", "Skill Taxonomy"]
)


@router.post("/taxonomy/map", response_model=SkillTaxonomyResponse)
async def map_skills_to_taxonomy(
    request: SkillTaxonomyRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    Map skills to standard taxonomy.

    **Capabilities:**
    - Direct skill matching
    - Synonym-based matching
    - LLM-powered fuzzy matching
    - Related skills discovery

    **Example request:**
    ```json
    {
      "skills": ["python", "machine learning", "team leadership", "agile"],
      "use_llm_mapping": true,
      "include_related_skills": true
    }
    ```
    """
    try:
        logger.info(f"📚 Taxonomy mapping for {len(request.skills)} skills")

        # Load module configuration
        module_config = await load_module_config(db, "taxonomy_skillmatch")
        logger.info(f"✓ Loaded config for taxonomy_skillmatch")

        # Initialize service with config
        service = TaxonomySkillmatchService(db, settings, config=module_config)
        result = await service.map_skills_to_taxonomy(request)

        logger.info(f"✓ Mapped {len(result.mappings)} skills ({result.taxonomy_coverage_percent:.1f}% coverage)")
        return result

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Mapping failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Mapping failed: {str(e)}")


@router.post("/skillsets/match", response_model=SkillMatchResponse)
async def match_skillsets(
    request: SkillMatchRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    Match two skill sets and identify gaps.

    **Capabilities:**
    - Multi-dimensional skill matching
    - Skill gap identification
    - Learning path suggestions
    - Category-level breakdown
    - Match quality assessment

    **Example request:**
    ```json
    {
      "source_skills": [
        {"skill_name": "Python", "proficiency": "advanced"},
        {"skill_name": "SQL", "proficiency": "intermediate"}
      ],
      "target_skills": [
        {"skill_name": "Python", "proficiency": "advanced"},
        {"skill_name": "SQL", "proficiency": "advanced"},
        {"skill_name": "Leadership", "proficiency": "intermediate"}
      ],
      "identify_gaps": true,
      "suggest_learning_paths": true
    }
    ```
    """
    try:
        logger.info(f"🔄 Skillset matching")

        # Load module configuration
        module_config = await load_module_config(db, "taxonomy_skillmatch")
        logger.info(f"✓ Loaded config for taxonomy_skillmatch")

        # Initialize service with config
        service = TaxonomySkillmatchService(db, settings, config=module_config)
        result = await service.match_skillsets(request)

        logger.info(f"✓ Match complete: {result.match_result.match_percentage:.1f}% ({result.match_quality})")
        return result

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Matching failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Matching failed: {str(e)}")


@router.post("/taxonomy/search")
async def search_taxonomy(request: SearchTaxonomyRequest, db: Session = Depends(get_db)):
    """Search skill taxonomy mappings."""
    try:
        from app.models.database_enhanced import SkillTaxonomyResults
        import uuid

        logger.info(f"🔍 Search taxonomy mappings")

        query = db.query(SkillTaxonomyResults).filter(SkillTaxonomyResults.module_id == "taxonomy-skillmatch")

        if request.session_id:
            query = query.filter(SkillTaxonomyResults.session_id == request.session_id)
        if request.project_id:
            query = query.filter(SkillTaxonomyResults.project_id == uuid.UUID(request.project_id))
        if request.skill_name:
            query = query.filter(SkillTaxonomyResults.taxonomy_data["skill_name"].astext.ilike(f"%{request.skill_name}%"))
        if request.category:
            query = query.filter(SkillTaxonomyResults.taxonomy_data["category"].astext == request.category.value)

        results = query.limit(request.limit).all()

        mappings = [
            {
                "mapping_id": str(r.taxonomy_id),
                "skill_name": r.taxonomy_data.get("skill_name"),
                "category": r.taxonomy_data.get("category"),
                "created_at": r.created_at.isoformat()
            }
            for r in results
        ]

        return {"mappings": mappings, "count": len(mappings)}

    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Search failed: {str(e)}")


@router.post("/taxonomy/export")
async def export_taxonomy(request: ExportTaxonomyRequest, db: Session = Depends(get_db)):
    """Export skill taxonomy data."""
    try:
        from app.models.database_enhanced import SkillTaxonomyResults
        import uuid

        logger.info(f"📥 Export request in {request.format} format")

        query = db.query(SkillTaxonomyResults).filter(SkillTaxonomyResults.module_id == "taxonomy-skillmatch")

        if request.mapping_ids:
            mapping_uuids = [uuid.UUID(mid) for mid in request.mapping_ids]
            query = query.filter(SkillTaxonomyResults.taxonomy_id.in_(mapping_uuids))
        elif request.session_id:
            query = query.filter(SkillTaxonomyResults.session_id == request.session_id)
        elif request.category:
            query = query.filter(SkillTaxonomyResults.taxonomy_data["category"].astext == request.category.value)

        results = query.all()

        if not results:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No mappings found")

        export_data = [{
            "mapping_id": str(r.taxonomy_id),
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
    """Get skill taxonomy statistics."""
    try:
        from app.models.database_enhanced import SkillTaxonomyResults

        logger.info(f"📊 Stats request")

        query = db.query(SkillTaxonomyResults).filter(SkillTaxonomyResults.module_id == "taxonomy-skillmatch")

        if session_id:
            query = query.filter(SkillTaxonomyResults.session_id == session_id)

        results = query.all()

        total_mappings = len(results)

        # Calculate average confidence
        confidences = [r.taxonomy_data.get("confidence_score", 0) for r in results if "confidence_score" in r.taxonomy_data]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # Category distribution
        categories = {}
        for r in results:
            cat = r.taxonomy_data.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        return TaxonomyStatsResponse(
            total_skills_in_taxonomy=500,  # Hardcoded for demo
            total_categories=8,
            total_mappings_performed=total_mappings,
            avg_confidence_score=round(avg_confidence, 2),
            top_mapped_skills=[],
            category_distribution=categories
        )

    except Exception as e:
        logger.error(f"Stats retrieval failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Stats retrieval failed: {str(e)}")


@router.get("/status")
async def get_module_status() -> Dict[str, Any]:
    """Get taxonomy skillmatch module status."""
    return {
        "module_id": "taxonomy-skillmatch",
        "name": "Taxonomy Skillmatch",
        "version": "1.0.0",
        "tier": 2,
        "category": "hr_talent",
        "description": "Skill taxonomy mapping and matching",

        "capabilities": {
            "skill_categories": ["technical", "soft_skills", "leadership", "domain_knowledge", "tools_platforms", "languages", "certifications", "methodologies"],
            "proficiency_levels": ["beginner", "intermediate", "advanced", "expert"],
            "matching_types": ["direct", "synonym", "fuzzy_llm"],
            "gap_analysis": True
        },

        "features": {
            "taxonomy_mapping": True,
            "fuzzy_matching": True,
            "skillset_comparison": True,
            "gap_identification": True,
            "learning_path_suggestions": True,
            "category_breakdown": True
        },

        "tier_1_dependencies": ["LLMService"],

        "endpoints": {
            "map_taxonomy": "POST /api/v1/modules/taxonomy-skillmatch/taxonomy/map",
            "match_skillsets": "POST /api/v1/modules/taxonomy-skillmatch/skillsets/match",
            "search": "POST /api/v1/modules/taxonomy-skillmatch/taxonomy/search",
            "export": "POST /api/v1/modules/taxonomy-skillmatch/taxonomy/export",
            "stats": "GET /api/v1/modules/taxonomy-skillmatch/stats",
            "status": "GET /api/v1/modules/taxonomy-skillmatch/status"
        },

        "performance": {
            "avg_mapping_time_seconds": "1-2",
            "skills_mapped_per_second": "100-200"
        },

        "use_cases": [
            "Job-candidate skill matching",
            "Skills gap analysis",
            "Learning and development planning",
            "Career pathing",
            "Organizational skill inventory"
        ]
    }
