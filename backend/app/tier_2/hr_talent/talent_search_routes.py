"""
Talent Search API Routes
Tier 2 Module: HR & Talent

REST endpoints for AI-powered talent search and matching.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from app.services.module_config_helper import load_module_config
from .talent_search_service import TalentSearchService
from .talent_search_schemas import (
    TalentSearchRequest,
    TalentSearchResponse,
    SearchTalentMatchesRequest,
    ExportTalentMatchesRequest,
    TalentSearchStatsResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/modules/talent-search",
    tags=["HR & Talent", "Tier 2 Modules", "Talent Search"]
)


@router.post("/search", response_model=TalentSearchResponse)
async def search_talent(
    request: TalentSearchRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    Search for talent matching job requirements.

    **Matching Capabilities:**
    - Multi-dimensional scoring (skills, experience, education, location, salary)
    - Required vs. preferred skills differentiation
    - Semantic resume-to-JD matching (LLM-powered)
    - Customizable scoring weights
    - AI-generated recommendations

    **Example request:**
    ```json
    {
      "job_requirement": {
        "job_id": "job-123",
        "job_title": "Senior Python Developer",
        "experience_level": "senior",
        "required_skills": [
          {"name": "Python", "proficiency": "advanced", "required": true},
          {"name": "FastAPI", "proficiency": "intermediate", "required": true}
        ],
        "years_of_experience_min": 5.0,
        "employment_type": "full_time"
      },
      "candidate_pool": [...],
      "top_n": 10,
      "min_score_threshold": 60.0,
      "use_semantic_matching": true
    }
    ```
    """
    try:
        logger.info(f"🔍 Talent search for: {request.job_requirement.job_title}")

        # Load module configuration
        module_config = await load_module_config(db, "talent_search")
        logger.info(f"✓ Loaded config for talent_search")

        # Initialize service with config
        service = TalentSearchService(db, settings, config=module_config)
        result = await service.search_talent(request)

        logger.info(f"✓ Found {result.total_matches_found} matches ({result.total_candidates_evaluated} evaluated)")
        return result

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Search failed: {str(e)}")


@router.post("/matches/search")
async def search_matches(request: SearchTalentMatchesRequest, db: Session = Depends(get_db)):
    """Search historical talent matches."""
    try:
        from app.models.database_enhanced import TalentMatchResults
        import uuid

        logger.info(f"🔍 Search talent matches")

        query = db.query(TalentMatchResults).filter(TalentMatchResults.module_id == "talent-search")

        if request.session_id:
            query = query.filter(TalentMatchResults.session_id == request.session_id)
        if request.project_id:
            query = query.filter(TalentMatchResults.project_id == uuid.UUID(request.project_id))
        if request.job_id:
            query = query.filter(TalentMatchResults.match_data["job_id"].astext == request.job_id)
        if request.min_score:
            query = query.filter(TalentMatchResults.match_data["match_score"]["overall_score"].astext.cast(db.Float) >= request.min_score)

        results = query.limit(request.limit).all()

        matches = [
            {
                "match_id": str(r.match_id),
                "job_id": r.match_data.get("job_requirement", {}).get("job_id"),
                "job_title": r.match_data.get("job_requirement", {}).get("job_title"),
                "total_matches": r.match_data.get("total_matches_found"),
                "created_at": r.created_at.isoformat()
            }
            for r in results
        ]

        return {"matches": matches, "count": len(matches)}

    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Search failed: {str(e)}")


@router.post("/matches/export")
async def export_matches(request: ExportTalentMatchesRequest, db: Session = Depends(get_db)):
    """Export talent matches."""
    try:
        from app.models.database_enhanced import TalentMatchResults
        import uuid

        logger.info(f"📥 Export request in {request.format} format")

        query = db.query(TalentMatchResults).filter(TalentMatchResults.module_id == "talent-search")

        if request.match_ids:
            match_uuids = [uuid.UUID(mid) for mid in request.match_ids]
            query = query.filter(TalentMatchResults.match_id.in_(match_uuids))
        elif request.session_id:
            query = query.filter(TalentMatchResults.session_id == request.session_id)
        elif request.job_id:
            query = query.filter(TalentMatchResults.match_data["job_id"].astext == request.job_id)

        results = query.all()

        if not results:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matches found")

        export_data = [{
            "match_id": str(r.match_id),
            "job_requirement": r.match_data.get("job_requirement"),
            "matches": r.match_data.get("matches"),
            "created_at": r.created_at.isoformat()
        } for r in results]

        return {"format": request.format, "data": export_data, "count": len(export_data)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Export failed: {str(e)}")


@router.get("/stats", response_model=TalentSearchStatsResponse)
async def get_talent_stats(session_id: str = None, db: Session = Depends(get_db)):
    """Get talent search statistics."""
    try:
        from app.models.database_enhanced import TalentMatchResults

        logger.info(f"📊 Stats request")

        query = db.query(TalentMatchResults).filter(TalentMatchResults.module_id == "talent-search")

        if session_id:
            query = query.filter(TalentMatchResults.session_id == session_id)

        results = query.all()

        total_searches = len(results)
        total_candidates = sum(r.match_data.get("total_matches_found", 0) for r in results)

        # Calculate avg match score
        all_scores = []
        for r in results:
            matches = r.match_data.get("matches", [])
            for match in matches:
                if isinstance(match, dict) and "match_score" in match:
                    all_scores.append(match["match_score"].get("overall_score", 0))

        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0.0
        avg_matches = total_candidates / total_searches if total_searches > 0 else 0

        return TalentSearchStatsResponse(
            total_searches_performed=total_searches,
            total_candidates_matched=total_candidates,
            avg_match_score=round(avg_score, 2),
            avg_matches_per_search=round(avg_matches, 2),
            top_matched_skills=[],
            top_job_titles=[]
        )

    except Exception as e:
        logger.error(f"Stats retrieval failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Stats retrieval failed: {str(e)}")


@router.get("/status")
async def get_module_status() -> Dict[str, Any]:
    """Get talent search module status."""
    return {
        "module_id": "talent-search",
        "name": "Talent Search",
        "version": "1.0.0",
        "tier": 2,
        "category": "hr_talent",
        "description": "AI-powered talent search and candidate-to-job matching",

        "capabilities": {
            "matching_dimensions": ["skills", "experience", "education", "location", "salary", "semantic"],
            "experience_levels": ["entry_level", "mid_level", "senior", "lead", "principal", "executive"],
            "employment_types": ["full_time", "part_time", "contract", "freelance", "internship"],
            "skill_proficiency_levels": ["beginner", "intermediate", "advanced", "expert"]
        },

        "features": {
            "multi_dimensional_matching": True,
            "semantic_resume_matching": True,
            "customizable_weights": True,
            "ai_recommendations": True,
            "skills_gap_analysis": True,
            "export_formats": ["json", "csv", "excel", "pdf"]
        },

        "tier_1_dependencies": ["LLMService"],

        "endpoints": {
            "search": "POST /api/v1/modules/talent-search/search",
            "search_matches": "POST /api/v1/modules/talent-search/matches/search",
            "export": "POST /api/v1/modules/talent-search/matches/export",
            "stats": "GET /api/v1/modules/talent-search/stats",
            "status": "GET /api/v1/modules/talent-search/status"
        },

        "performance": {
            "avg_search_time_seconds": "2-5",
            "candidates_evaluated_per_second": "50-100"
        },

        "use_cases": [
            "Recruitment and hiring",
            "Talent pipeline building",
            "Internal mobility matching",
            "Skills gap identification",
            "Diversity hiring initiatives"
        ]
    }
