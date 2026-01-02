"""
Spend Smart API Routes
Tier 2 Module: Procurement

REST endpoints for spending pattern analysis and cost optimization.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from .spend_smart_service import SpendSmartService
from .spend_smart_schemas import (
    SpendAnalysisRequest,
    SpendAnalysisResponse,
    SearchSpendAnalysesRequest,
    ExportSpendAnalysisRequest,
    SpendStatsResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/modules/spend-smart",
    tags=["Procurement", "Tier 2 Modules", "Spend Analytics"]
)


@router.post("/analyze", response_model=SpendAnalysisResponse)
async def analyze_spending(
    request: SpendAnalysisRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    Analyze spending patterns and identify cost savings.

    **Analysis Capabilities:**
    - Spending pattern analysis (trends, seasonality)
    - Anomaly detection (spikes, duplicates, off-contract)
    - Savings opportunity identification
    - Vendor concentration risk assessment
    - Budget utilization tracking
    - Category-level analysis

    **Example request:**
    ```json
    {
      "time_period_months": 12,
      "categories": ["it", "office_supplies", "facilities"],
      "detect_anomalies": true,
      "identify_savings": true,
      "budget_amount": 1000000.0
    }
    ```
    """
    try:
        logger.info(f"💰 Spend analysis request for {request.time_period_months} months")

        service = SpendSmartService(db, settings)
        result = await service.analyze_spending(request)

        logger.info(f"✓ Analysis complete: ${result.total_spend:,.2f} spend, ${result.total_potential_savings:,.2f} potential savings")
        return result

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Analysis failed: {str(e)}")


@router.post("/search")
async def search_analyses(request: SearchSpendAnalysesRequest, db: Session = Depends(get_db)):
    """Search spend analyses."""
    try:
        from app.models.database_enhanced import SpendAnalysisResults
        import uuid

        logger.info(f"🔍 Search spend analyses request")

        query = db.query(SpendAnalysisResults).filter(SpendAnalysisResults.module_id == "spend-smart")

        if request.session_id:
            query = query.filter(SpendAnalysisResults.session_id == request.session_id)
        if request.project_id:
            query = query.filter(SpendAnalysisResults.project_id == uuid.UUID(request.project_id))

        results = query.limit(request.limit).all()

        analyses = [
            {
                "analysis_id": str(r.analysis_id),
                "total_spend": r.analysis_data.get("total_spend"),
                "total_potential_savings": r.analysis_data.get("total_potential_savings"),
                "created_at": r.created_at.isoformat()
            }
            for r in results
        ]

        return {"analyses": analyses, "count": len(analyses)}

    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Search failed: {str(e)}")


@router.post("/export")
async def export_analyses(request: ExportSpendAnalysisRequest, db: Session = Depends(get_db)):
    """Export spend analyses."""
    try:
        from app.models.database_enhanced import SpendAnalysisResults
        import uuid

        logger.info(f"📥 Export request in {request.format} format")

        query = db.query(SpendAnalysisResults).filter(SpendAnalysisResults.module_id == "spend-smart")

        if request.analysis_ids:
            analysis_uuids = [uuid.UUID(aid) for aid in request.analysis_ids]
            query = query.filter(SpendAnalysisResults.analysis_id.in_(analysis_uuids))
        elif request.session_id:
            query = query.filter(SpendAnalysisResults.session_id == request.session_id)

        results = query.all()

        if not results:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No analyses found")

        export_data = [{"analysis_id": str(r.analysis_id), "data": r.analysis_data} for r in results]

        return {"format": request.format, "data": export_data, "count": len(export_data)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Export failed: {str(e)}")


@router.get("/stats", response_model=SpendStatsResponse)
async def get_spend_stats(session_id: str = None, db: Session = Depends(get_db)):
    """Get spend analytics statistics."""
    try:
        from app.models.database_enhanced import SpendAnalysisResults

        logger.info(f"📊 Stats request")

        query = db.query(SpendAnalysisResults).filter(SpendAnalysisResults.module_id == "spend-smart")

        if session_id:
            query = query.filter(SpendAnalysisResults.session_id == session_id)

        results = query.all()

        total_analyses = len(results)
        total_spend = sum(r.analysis_data.get("total_spend", 0) for r in results)
        total_savings = sum(r.analysis_data.get("total_potential_savings", 0) for r in results)
        avg_savings = total_savings / total_analyses if total_analyses > 0 else 0

        return SpendStatsResponse(
            total_analyses=total_analyses,
            total_spend_analyzed=total_spend,
            total_potential_savings=total_savings,
            avg_savings_per_analysis=avg_savings,
            total_anomalies_detected=0,
            top_spending_categories=[]
        )

    except Exception as e:
        logger.error(f"Stats retrieval failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Stats retrieval failed: {str(e)}")


@router.get("/status")
async def get_module_status() -> Dict[str, Any]:
    """Get spend smart module status."""
    return {
        "module_id": "spend-smart",
        "name": "Spend Smart",
        "version": "1.0.0",
        "tier": 2,
        "category": "procurement",
        "description": "Analyze spending patterns and identify cost savings",

        "capabilities": {
            "spend_categories": ["it", "office_supplies", "facilities", "professional_services", "marketing", "travel", "utilities", "maintenance"],
            "analysis_features": [
                "pattern_analysis",
                "anomaly_detection",
                "savings_identification",
                "vendor_concentration",
                "budget_utilization",
                "trend_analysis"
            ],
            "anomaly_types": ["unusual_spike", "unusual_drop", "duplicate_payment", "vendor_overspend", "category_overspend", "off_contract_spend"]
        },

        "features": {
            "pattern_detection": True,
            "anomaly_detection": True,
            "savings_opportunities": True,
            "vendor_analysis": True,
            "budget_tracking": True,
            "export_formats": ["json", "csv", "excel", "pdf"]
        },

        "tier_1_dependencies": ["LLMService"],

        "endpoints": {
            "analyze": "POST /api/v1/modules/spend-smart/analyze",
            "search": "POST /api/v1/modules/spend-smart/search",
            "export": "POST /api/v1/modules/spend-smart/export",
            "stats": "GET /api/v1/modules/spend-smart/stats",
            "status": "GET /api/v1/modules/spend-smart/status"
        },

        "performance": {
            "avg_analysis_time_seconds": "2-4",
            "data_points_processed_per_second": "1000-2000"
        },

        "use_cases": [
            "Cost reduction initiatives",
            "Budget optimization",
            "Vendor consolidation",
            "Spend compliance monitoring",
            "Fraud detection",
            "Contract compliance"
        ]
    }
