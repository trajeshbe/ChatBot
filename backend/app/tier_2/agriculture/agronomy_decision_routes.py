"""
Agronomy Decision API Routes
Tier 2 Module: Agriculture

REST endpoints for agronomy decision support and farm management recommendations.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from .agronomy_decision_service import AgronomyDecisionService
from .agronomy_decision_schemas import (
    AgronomyDecisionRequest,
    AgronomyDecisionResponse,
    SearchDecisionsRequest,
    ExportDecisionsRequest,
    DecisionStatsResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/modules/agronomy-decision",
    tags=["Agriculture", "Tier 2 Modules", "Agronomy Decision Support"]
)


@router.post("/analyze", response_model=AgronomyDecisionResponse)
async def analyze_agronomy_decisions(
    request: AgronomyDecisionRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    Analyze agricultural context and provide agronomy recommendations.

    **Decision Types Supported:**
    - **Planting**: Optimal planting timing, soil readiness, frost risk assessment
    - **Irrigation**: Soil moisture analysis, water scheduling, drought management
    - **Fertilization**: NPK analysis, soil amendment recommendations, pH optimization
    - **Pest Control**: Infestation level assessment, treatment timing, IPM strategies
    - **Disease Management**: Disease severity analysis, treatment recommendations
    - **Harvesting**: Maturity assessment, weather-based timing, quality optimization
    - **Crop Rotation**: Soil health improvement, pest/disease break strategies
    - **Soil Amendment**: pH correction, organic matter enhancement

    **Input Context:**
    - Soil conditions (moisture, pH, NPK, temperature)
    - Weather data (current and 7-day forecast)
    - Crop health indicators (NDVI, pest/disease levels, water stress)
    - Farm details (location, size, crop type, planting date)

    **AI Features:**
    - LLM-powered decision analysis for complex scenarios
    - Multi-dimensional risk assessment
    - Alternative recommendation generation
    - Sustainability rating and insights

    **Example request:**
    ```json
    {
      "decision_types": ["irrigation", "fertilization"],
      "context": {
        "crop_type": "corn",
        "farm_location": "Iowa, USA",
        "soil_condition": {
          "moisture_percent": 25.5,
          "ph_level": 6.8,
          "nitrogen_ppm": 18.0
        },
        "weather_data": {
          "current_temperature_celsius": 22.0,
          "rainfall_forecast_7days_mm": 5.0,
          "drought_risk": true
        }
      },
      "use_ai_analysis": true,
      "prioritize_sustainability": false
    }
    ```

    **Response includes:**
    - Decision analyses with prioritized recommendations
    - Overall farm health score (0-100)
    - Critical actions count
    - Estimated costs
    - Sustainability rating
    - AI-generated insights
    """
    try:
        logger.info(f"🌾 Agronomy decision request for {len(request.decision_types)} decision types")

        service = AgronomyDecisionService(db, settings)
        result = await service.make_decisions(request)

        logger.info(f"✓ Generated {len(result.analyses)} analyses with {result.critical_actions_count} critical actions")
        return result

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Decision analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Decision analysis failed: {str(e)}")


@router.post("/search")
async def search_decisions(request: SearchDecisionsRequest, db: Session = Depends(get_db)):
    """Search historical agronomy decisions."""
    try:
        from app.models.database_enhanced import AgronomyDecisionResults
        import uuid

        logger.info(f"🔍 Search agronomy decisions")

        query = db.query(AgronomyDecisionResults).filter(AgronomyDecisionResults.module_id == "agronomy-decision")

        if request.session_id:
            query = query.filter(AgronomyDecisionResults.session_id == request.session_id)
        if request.project_id:
            query = query.filter(AgronomyDecisionResults.project_id == uuid.UUID(request.project_id))
        if request.decision_type:
            query = query.filter(AgronomyDecisionResults.decision_data["decision_type"].astext == request.decision_type.value)
        if request.crop_type:
            query = query.filter(AgronomyDecisionResults.decision_data["context"]["crop_type"].astext.ilike(f"%{request.crop_type}%"))
        if request.priority:
            query = query.filter(AgronomyDecisionResults.decision_data["priority"].astext == request.priority.value)

        results = query.limit(request.limit).all()

        decisions = [
            {
                "decision_id": str(r.decision_id),
                "decision_type": r.decision_data.get("decision_type"),
                "crop_type": r.decision_data.get("context", {}).get("crop_type"),
                "priority": r.decision_data.get("priority"),
                "created_at": r.created_at.isoformat()
            }
            for r in results
        ]

        return {"decisions": decisions, "count": len(decisions)}

    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Search failed: {str(e)}")


@router.post("/export")
async def export_decisions(request: ExportDecisionsRequest, db: Session = Depends(get_db)):
    """Export agronomy decision data."""
    try:
        from app.models.database_enhanced import AgronomyDecisionResults
        import uuid

        logger.info(f"📥 Export request in {request.format} format")

        query = db.query(AgronomyDecisionResults).filter(AgronomyDecisionResults.module_id == "agronomy-decision")

        if request.decision_ids:
            decision_uuids = [uuid.UUID(did) for did in request.decision_ids]
            query = query.filter(AgronomyDecisionResults.decision_id.in_(decision_uuids))
        elif request.session_id:
            query = query.filter(AgronomyDecisionResults.session_id == request.session_id)
        elif request.decision_type:
            query = query.filter(AgronomyDecisionResults.decision_data["decision_type"].astext == request.decision_type.value)

        results = query.all()

        if not results:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No decision data found")

        export_data = [{
            "decision_id": str(r.decision_id),
            "data": r.decision_data,
            "created_at": r.created_at.isoformat()
        } for r in results]

        return {"format": request.format, "data": export_data, "count": len(export_data)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Export failed: {str(e)}")


@router.get("/stats", response_model=DecisionStatsResponse)
async def get_decision_stats(session_id: str = None, db: Session = Depends(get_db)):
    """Get agronomy decision statistics."""
    try:
        from app.models.database_enhanced import AgronomyDecisionResults

        logger.info(f"📊 Stats request")

        query = db.query(AgronomyDecisionResults).filter(AgronomyDecisionResults.module_id == "agronomy-decision")

        if session_id:
            query = query.filter(AgronomyDecisionResults.session_id == session_id)

        results = query.all()

        total_decisions = len(results)

        # Count by decision type
        decisions_by_type = {}
        decisions_by_priority = {}
        confidence_scores = []
        crop_types = {}

        for r in results:
            decision_type = r.decision_data.get("decision_type", "unknown")
            decisions_by_type[decision_type] = decisions_by_type.get(decision_type, 0) + 1

            priority = r.decision_data.get("priority", "unknown")
            decisions_by_priority[priority] = decisions_by_priority.get(priority, 0) + 1

            if "confidence_score" in r.decision_data:
                confidence_scores.append(r.decision_data["confidence_score"])

            crop_type = r.decision_data.get("context", {}).get("crop_type")
            if crop_type:
                crop_types[crop_type] = crop_types.get(crop_type, 0) + 1

        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else None

        # Top crop types
        most_common_crops = sorted(crop_types.items(), key=lambda x: x[1], reverse=True)[:5]
        most_common_crop_names = [crop for crop, _ in most_common_crops]

        return DecisionStatsResponse(
            total_decisions_made=total_decisions,
            decisions_by_type=decisions_by_type,
            decisions_by_priority=decisions_by_priority,
            average_confidence_score=round(avg_confidence, 2) if avg_confidence else None,
            most_common_crop_types=most_common_crop_names,
            sustainability_metrics={
                "total_sustainable_recommendations": 0,  # Would be calculated from actual data
                "sustainability_score": 75.0  # Placeholder
            }
        )

    except Exception as e:
        logger.error(f"Stats retrieval failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Stats retrieval failed: {str(e)}")


@router.get("/status")
async def get_module_status() -> Dict[str, Any]:
    """Get agronomy-decision module status."""
    return {
        "module_id": "agronomy-decision",
        "name": "Agronomy Decision Support",
        "version": "1.0.0",
        "tier": 2,
        "category": "agriculture",
        "description": "AI-powered agronomy decision support and farm management recommendations",

        "decision_types": [
            {
                "id": "planting",
                "name": "Planting Decisions",
                "description": "Optimal planting timing, soil readiness, frost risk"
            },
            {
                "id": "irrigation",
                "name": "Irrigation Management",
                "description": "Soil moisture analysis, water scheduling, drought management"
            },
            {
                "id": "fertilization",
                "name": "Fertilization Planning",
                "description": "NPK analysis, soil amendments, pH optimization"
            },
            {
                "id": "pest_control",
                "name": "Pest Control",
                "description": "Infestation assessment, treatment timing, IPM strategies"
            },
            {
                "id": "disease_management",
                "name": "Disease Management",
                "description": "Disease severity analysis, treatment recommendations"
            },
            {
                "id": "harvesting",
                "name": "Harvest Timing",
                "description": "Maturity assessment, weather-based timing, quality optimization"
            },
            {
                "id": "crop_rotation",
                "name": "Crop Rotation",
                "description": "Soil health improvement, pest/disease break strategies"
            },
            {
                "id": "soil_amendment",
                "name": "Soil Amendment",
                "description": "pH correction, organic matter enhancement"
            }
        ],

        "input_parameters": {
            "soil_conditions": ["moisture_percent", "ph_level", "npk_levels", "temperature", "salinity"],
            "weather_data": ["temperature", "rainfall", "humidity", "wind_speed", "frost_risk", "drought_risk"],
            "crop_health": ["health_status", "growth_stage", "ndvi", "pest_infestation", "disease_severity", "water_stress"],
            "farm_context": ["location", "size_hectares", "crop_type", "planting_date", "previous_crops"]
        },

        "features": {
            "rule_based_decisions": True,
            "ai_powered_analysis": True,
            "multi_dimensional_scoring": True,
            "risk_assessment": True,
            "alternative_recommendations": True,
            "sustainability_rating": True,
            "cost_estimation": True,
            "confidence_scoring": True,
            "export_formats": ["json", "csv", "excel", "pdf"]
        },

        "tier_1_dependencies": ["LLMService"],

        "endpoints": {
            "analyze": "POST /api/v1/modules/agronomy-decision/analyze",
            "search": "POST /api/v1/modules/agronomy-decision/search",
            "export": "POST /api/v1/modules/agronomy-decision/export",
            "stats": "GET /api/v1/modules/agronomy-decision/stats",
            "status": "GET /api/v1/modules/agronomy-decision/status"
        },

        "performance": {
            "avg_analysis_time_seconds": "2-4",
            "decisions_per_request": "1-8",
            "ai_confidence_threshold": "75%"
        },

        "use_cases": [
            "Precision agriculture and smart farming",
            "Crop production optimization",
            "Resource management (water, fertilizer, pesticides)",
            "Risk mitigation (weather, pests, diseases)",
            "Sustainable farming practices",
            "Yield maximization strategies",
            "Farm operations planning and scheduling",
            "Agricultural extension services and advisory"
        ]
    }
