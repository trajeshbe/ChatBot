"""
Talent Pulse API Routes
Tier 2 Module: HR & Talent

REST endpoints for employee sentiment and engagement analysis.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from .talent_pulse_service import TalentPulseService
from .talent_pulse_schemas import (
    TalentPulseRequest,
    TalentPulseResponse,
    SearchPulseAnalysesRequest,
    ExportPulseAnalysisRequest,
    PulseStatsResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/modules/talent-pulse",
    tags=["HR & Talent", "Tier 2 Modules", "Employee Engagement"]
)


@router.post("/analyze", response_model=TalentPulseResponse)
async def analyze_talent_pulse(
    request: TalentPulseRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    Analyze employee sentiment and engagement.

    **Analysis Capabilities:**
    - Sentiment analysis using LLM
    - Engagement score calculation
    - Department-level breakdowns
    - Attrition risk assessment
    - Category-based insights (compensation, work-life balance, etc.)
    - AI-generated action items

    **Example request:**
    ```json
    {
      "feedback_data": [
        {
          "employee_id": "emp-123",
          "feedback_text": "Great team collaboration and work-life balance",
          "department": "Engineering",
          "tenure_months": 24
        }
      ],
      "analyze_sentiment": true,
      "calculate_engagement": true,
      "assess_attrition_risk": true
    }
    ```
    """
    try:
        logger.info(f"📊 Talent pulse analysis for {len(request.feedback_data)} feedback items")

        service = TalentPulseService(db, settings)
        result = await service.analyze_talent_pulse(request)

        logger.info(f"✓ Analysis complete: {result.engagement_metrics.engagement_level} engagement")
        return result

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Analysis failed: {str(e)}")


@router.post("/analyses/search")
async def search_analyses(request: SearchPulseAnalysesRequest, db: Session = Depends(get_db)):
    """Search historical pulse analyses."""
    try:
        from app.models.database_enhanced import PulseAnalysisResults
        import uuid

        logger.info(f"🔍 Search pulse analyses")

        query = db.query(PulseAnalysisResults).filter(PulseAnalysisResults.module_id == "talent-pulse")

        if request.session_id:
            query = query.filter(PulseAnalysisResults.session_id == request.session_id)
        if request.project_id:
            query = query.filter(PulseAnalysisResults.project_id == uuid.UUID(request.project_id))
        if request.department:
            query = query.filter(PulseAnalysisResults.analysis_data["department"].astext == request.department)
        if request.min_engagement_score:
            query = query.filter(
                PulseAnalysisResults.analysis_data["engagement_metrics"]["engagement_score"].astext.cast(db.Float) >= request.min_engagement_score
            )

        results = query.limit(request.limit).all()

        analyses = [
            {
                "analysis_id": str(r.analysis_id),
                "engagement_level": r.analysis_data.get("engagement_metrics", {}).get("engagement_level"),
                "sentiment": r.analysis_data.get("overall_sentiment", {}).get("sentiment_score"),
                "created_at": r.created_at.isoformat()
            }
            for r in results
        ]

        return {"analyses": analyses, "count": len(analyses)}

    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Search failed: {str(e)}")


@router.post("/analyses/export")
async def export_analyses(request: ExportPulseAnalysisRequest, db: Session = Depends(get_db)):
    """Export pulse analyses."""
    try:
        from app.models.database_enhanced import PulseAnalysisResults
        import uuid

        logger.info(f"📥 Export request in {request.format} format")

        query = db.query(PulseAnalysisResults).filter(PulseAnalysisResults.module_id == "talent-pulse")

        if request.analysis_ids:
            analysis_uuids = [uuid.UUID(aid) for aid in request.analysis_ids]
            query = query.filter(PulseAnalysisResults.analysis_id.in_(analysis_uuids))
        elif request.session_id:
            query = query.filter(PulseAnalysisResults.session_id == request.session_id)
        elif request.department:
            query = query.filter(PulseAnalysisResults.analysis_data["department"].astext == request.department)

        results = query.all()

        if not results:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No analyses found")

        export_data = [{
            "analysis_id": str(r.analysis_id),
            "data": r.analysis_data,
            "created_at": r.created_at.isoformat()
        } for r in results]

        return {"format": request.format, "data": export_data, "count": len(export_data)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Export failed: {str(e)}")


@router.get("/stats", response_model=PulseStatsResponse)
async def get_pulse_stats(session_id: str = None, db: Session = Depends(get_db)):
    """Get talent pulse statistics."""
    try:
        from app.models.database_enhanced import PulseAnalysisResults

        logger.info(f"📊 Stats request")

        query = db.query(PulseAnalysisResults).filter(PulseAnalysisResults.module_id == "talent-pulse")

        if session_id:
            query = query.filter(PulseAnalysisResults.session_id == session_id)

        results = query.all()

        total_analyses = len(results)
        total_feedback = sum(r.analysis_data.get("total_feedback_analyzed", 0) for r in results)

        # Calculate averages
        engagement_scores = []
        sentiment_scores = []
        high_risk_count = 0

        for r in results:
            eng_data = r.analysis_data.get("engagement_metrics", {})
            if "engagement_score" in eng_data:
                engagement_scores.append(eng_data["engagement_score"])

            sent_data = r.analysis_data.get("overall_sentiment", {})
            if "confidence" in sent_data:
                sentiment_scores.append(sent_data["confidence"])

            attrition = r.analysis_data.get("attrition_risks", [])
            high_risk_count += len([a for a in attrition if a.get("risk_level") == "high"])

        avg_engagement = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0.0
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0

        return PulseStatsResponse(
            total_analyses_performed=total_analyses,
            total_feedback_processed=total_feedback,
            avg_engagement_score=round(avg_engagement, 2),
            avg_sentiment_score=round(avg_sentiment, 2),
            high_risk_employees_count=high_risk_count,
            top_feedback_categories=[],
            department_engagement_comparison={}
        )

    except Exception as e:
        logger.error(f"Stats retrieval failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Stats retrieval failed: {str(e)}")


@router.get("/status")
async def get_module_status() -> Dict[str, Any]:
    """Get talent pulse module status."""
    return {
        "module_id": "talent-pulse",
        "name": "Talent Pulse",
        "version": "1.0.0",
        "tier": 2,
        "category": "hr_talent",
        "description": "Employee sentiment and engagement analysis",

        "capabilities": {
            "sentiment_levels": ["very_positive", "positive", "neutral", "negative", "very_negative"],
            "engagement_levels": ["highly_engaged", "engaged", "moderately_engaged", "disengaged", "highly_disengaged"],
            "feedback_categories": [
                "compensation", "work_life_balance", "career_growth", "management",
                "culture", "workload", "recognition", "team_collaboration", "tools_resources"
            ],
            "risk_levels": ["low", "medium", "high", "critical"]
        },

        "features": {
            "sentiment_analysis": True,
            "engagement_scoring": True,
            "attrition_risk_assessment": True,
            "department_breakdown": True,
            "category_insights": True,
            "ai_generated_insights": True,
            "action_recommendations": True
        },

        "tier_1_dependencies": ["LLMService"],

        "endpoints": {
            "analyze": "POST /api/v1/modules/talent-pulse/analyze",
            "search": "POST /api/v1/modules/talent-pulse/analyses/search",
            "export": "POST /api/v1/modules/talent-pulse/analyses/export",
            "stats": "GET /api/v1/modules/talent-pulse/stats",
            "status": "GET /api/v1/modules/talent-pulse/status"
        },

        "performance": {
            "avg_analysis_time_seconds": "3-6",
            "feedback_processed_per_second": "20-50"
        },

        "use_cases": [
            "Employee engagement surveys",
            "Exit interview analysis",
            "Pulse surveys",
            "Attrition risk management",
            "Organizational health monitoring",
            "Department-level sentiment tracking"
        ]
    }
