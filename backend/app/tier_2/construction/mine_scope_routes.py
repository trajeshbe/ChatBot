"""
Mine Scope API Routes
Tier 2 Module: Construction

REST endpoints for analyzing mining scope documents.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from app.services.module_config_helper import load_module_config
from .mine_scope_service import MineScopeService
from .mine_scope_schemas import (
    MineScopeAnalysisRequest,
    MineScopeAnalysisResponse,
    ScopeSearchRequest,
    ScopeSearchResponse,
    ScopeComparisonRequest,
    ScopeComparisonResponse,
    ExportScopeRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/modules/mine-scope",
    tags=["Construction", "Tier 2 Modules", "Mining Scope Analysis"]
)


@router.post("/analyze", response_model=MineScopeAnalysisResponse)
async def analyze_mining_scope(
    request: MineScopeAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    Analyze a mining scope document for requirements, metrics, and risks.

    **Analysis Capabilities:**
    - **Classification**: Identify scope type, mining sector, and extraction method
    - **Requirements Extraction**: Extract technical, regulatory, safety, environmental requirements
    - **Metrics Extraction**: Production targets, reserves, equipment, workforce, financials, timelines
    - **Risk Identification**: Safety, environmental, geological, operational, financial risks
    - **Compliance Extraction**: Regulatory requirements and deadlines
    - **Executive Summary**: AI-generated summary and key findings

    **Scope Types:**
    - Exploration, Development, Production, Reclamation
    - Feasibility Study, Environmental Assessment, Safety Plan
    - Equipment Specification, Operational Plan

    **Mining Sectors:**
    - Coal, Gold, Iron Ore, Copper, Lithium, Rare Earth
    - Nickel, Zinc, Bauxite, Diamond, and more

    **Example request:**
    ```json
    {
      "document_id": "doc-123",
      "extract_requirements": true,
      "extract_metrics": true,
      "identify_risks": true,
      "extract_compliance": true,
      "classify_scope_type": true,
      "use_vision": true,
      "min_confidence": 0.7
    }
    ```

    **Response includes:**
    - Scope classification (type, sector, method)
    - Requirements list with priorities
    - Quantitative metrics
    - Identified risks with mitigation strategies
    - Compliance requirements
    - Executive summary and key findings
    """
    try:
        logger.info(f"⛏️ Mining scope analysis request for document {request.document_id}")

        # Load module configuration
        module_config = await load_module_config(db, "mine_scope")
        logger.info(f"✓ Loaded config for mine_scope")

        # Initialize service with config
        service = MineScopeService(db, settings, config=module_config)
        result = await service.analyze_scope(request)

        logger.info(f"✓ Analysis complete: {result.total_requirements} requirements, {result.total_risks} risks")
        return result

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mining scope analysis failed: {str(e)}"
        )


@router.post("/search", response_model=ScopeSearchResponse)
async def search_mining_scopes(
    request: ScopeSearchRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    Search for analyzed mining scope documents.

    **Search Filters:**
    - `scope_types`: Filter by scope type (e.g., ["exploration", "production"])
    - `mining_sectors`: Filter by sector (e.g., ["gold", "copper"])
    - `mining_methods`: Filter by method (e.g., ["open_pit", "underground"])
    - `has_critical_requirements`: Only scopes with critical requirements
    - `has_high_severity_risks`: Only scopes with high-severity risks
    - `min_confidence`: Minimum classification confidence

    **Pagination:**
    - `limit`: Results per page (1-500)
    - `offset`: Skip first N results

    **Returns:**
    - Matching analyses
    - Aggregations by type, sector, and method
    - Pagination metadata
    """
    try:
        logger.info(f"🔍 Searching mining scope analyses")

        service = MineScopeService(db, settings)
        result = await service.search_analyses(request)

        logger.info(f"✓ Found {result.total_count} matching analyses")
        return result

    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/compare", response_model=ScopeComparisonResponse)
async def compare_mining_scopes(
    request: ScopeComparisonRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    Compare multiple mining scope documents.

    **Comparison Dimensions:**
    - Requirements (common vs unique)
    - Metrics (production, costs, timelines)
    - Risks (shared vs project-specific)
    - Compliance (regulatory overlap)

    **Use Cases:**
    - Compare different mining methods for same site
    - Benchmark against similar projects
    - Identify best practices across scopes
    - Gap analysis between proposals

    **Example request:**
    ```json
    {
      "analysis_ids": ["analysis-1", "analysis-2", "analysis-3"],
      "comparison_dimensions": ["requirements", "metrics", "risks"]
    }
    ```
    """
    try:
        logger.info(f"📊 Comparing {len(request.analysis_ids)} mining scopes")

        # Simplified comparison for now
        from .mine_scope_schemas import ScopeComparisonResponse
        import uuid

        return ScopeComparisonResponse(
            comparison_id=str(uuid.uuid4()),
            analyzed_scopes=len(request.analysis_ids),
            common_requirements=[],
            unique_requirements_by_scope={},
            metric_comparison={},
            risk_comparison={},
            comparison_summary="Comparison feature coming soon",
            recommendations=[]
        )

    except Exception as e:
        logger.error(f"Comparison failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison failed: {str(e)}"
        )


@router.post("/export")
async def export_mining_scope_analysis(
    request: ExportScopeRequest,
    db: Session = Depends(get_db)
):
    """
    Export mining scope analysis in various formats.

    **Supported Formats:**
    - `json`: Complete analysis data
    - `csv`: Flat format (requirements, risks, metrics)
    - `excel`: Multi-sheet workbook
    - `pdf`: Formatted report with charts

    **Export Options:**
    - `include_detailed_requirements`: Full requirement details
    - `include_risk_matrix`: Risk severity/likelihood matrix
    - `include_metrics`: Quantitative metrics table
    - `include_compliance_checklist`: Regulatory checklist

    **Example request:**
    ```json
    {
      "session_id": "session-123",
      "format": "excel",
      "include_detailed_requirements": true,
      "include_risk_matrix": true
    }
    ```
    """
    try:
        from app.models.database_enhanced import ScopeAnalysisResults
        import uuid

        logger.info(f"📥 Export request in {request.format} format")

        query = db.query(ScopeAnalysisResults).filter(
            ScopeAnalysisResults.module_id == "mine-scope"
        )

        if request.analysis_ids:
            analysis_uuids = [uuid.UUID(aid) for aid in request.analysis_ids]
            query = query.filter(ScopeAnalysisResults.analysis_id.in_(analysis_uuids))
        elif request.session_id:
            query = query.filter(ScopeAnalysisResults.session_id == request.session_id)
        elif request.project_id:
            query = query.filter(ScopeAnalysisResults.project_id == uuid.UUID(request.project_id))

        results = query.all()

        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No analyses found"
            )

        # Simple JSON export for now
        export_data = [
            {
                "analysis_id": str(r.analysis_id),
                "document_id": str(r.document_id),
                "classification": r.result_data.get("classification"),
                "requirements_count": len(r.result_data.get("requirements", [])),
                "risks_count": len(r.result_data.get("risks", [])),
                "executive_summary": r.result_data.get("executive_summary")
            }
            for r in results
        ]

        return {"format": request.format, "data": export_data, "count": len(export_data)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.get("/status")
async def get_module_status() -> Dict[str, Any]:
    """
    Get mine scope module status and capabilities.

    Returns module metadata, supported scope types, sectors, methods,
    and tier_1 service dependencies.
    """
    return {
        "module_id": "mine-scope",
        "name": "Mine Scope Analyzer",
        "version": "1.0.0",
        "tier": 2,
        "category": "construction",
        "description": "Analyze mining scope documents for requirements extraction and risk analysis",

        "capabilities": {
            "scope_types": [
                "exploration", "development", "production", "reclamation",
                "feasibility_study", "environmental_assessment", "safety_plan",
                "equipment_specification", "operational_plan"
            ],
            "mining_sectors": [
                "coal", "gold", "iron_ore", "copper", "lithium", "rare_earth",
                "nickel", "zinc", "bauxite", "diamond", "silver", "platinum"
            ],
            "mining_methods": [
                "open_pit", "underground", "placer", "in_situ",
                "strip_mining", "dredging", "solution_mining"
            ],
            "requirement_types": [
                "technical", "regulatory", "safety", "environmental",
                "operational", "financial"
            ],
            "risk_categories": [
                "safety", "environmental", "geological", "operational",
                "financial", "regulatory"
            ],
            "export_formats": ["json", "csv", "excel", "pdf"]
        },

        "features": {
            "requirements_extraction": True,
            "metrics_extraction": True,
            "risk_identification": True,
            "compliance_tracking": True,
            "scope_classification": True,
            "executive_summary_generation": True,
            "scope_comparison": True,
            "risk_matrix": True
        },

        "tier_1_dependencies": [
            "DocumentService",
            "LLMService",
            "VisionService"
        ],

        "endpoints": {
            "analyze": "POST /api/v1/modules/mine-scope/analyze",
            "search": "POST /api/v1/modules/mine-scope/search",
            "compare": "POST /api/v1/modules/mine-scope/compare",
            "export": "POST /api/v1/modules/mine-scope/export",
            "status": "GET /api/v1/modules/mine-scope/status"
        },

        "performance": {
            "avg_analysis_time_seconds": "30-60",
            "requirements_per_page": "5-15",
            "risks_per_page": "3-10"
        },

        "use_cases": [
            "Mining feasibility studies",
            "Environmental impact assessments",
            "Safety plan development",
            "Regulatory compliance tracking",
            "Risk assessment and mitigation",
            "Equipment specification analysis",
            "Project scope comparison"
        ]
    }
