"""
Maritime Logistics Optimizer - API Routes
AI-powered maritime logistics optimization with route planning, port scheduling, and cargo management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from app.services.module_config_helper import load_module_config
from .maritime_logistics_service import MaritimeLogisticsService
from .maritime_logistics_schemas import (
    OptimizeRouteRequest,
    OptimizeRouteResponse,
    SearchRoutesRequest,
    SearchRoutesResponse,
    ExportRoutesRequest,
    ExportRoutesResponse,
    MaritimeStatsResponse,
    StatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/modules/maritime-logistics", tags=["Maritime Logistics"])


@router.post("/optimize", response_model=OptimizeRouteResponse)
async def optimize_route(
    request: OptimizeRouteRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    **Optimize Maritime Route**

    AI-powered route optimization with:
    - Multi-objective optimization (cost, time, fuel, balanced)
    - Weather impact assessment
    - Port scheduling
    - Cargo loading optimization
    - Vessel performance analytics

    **Optimization Goals**:
    - `minimize_cost`: Reduce total shipping costs
    - `minimize_time`: Fastest route with minimal delays
    - `minimize_fuel`: Optimize for fuel efficiency
    - `balance_all`: Balanced optimization across all factors

    **Returns**:
    - Optimized route with segments
    - Port arrival/departure schedule
    - Cargo loading plan with weight distribution
    - Vessel performance metrics
    - AI-generated insights and recommendations
    - Alternative route options

    **Example**:
    ```json
    {
      "vessel": {
        "vessel_id": "V001",
        "name": "MV Ocean Pioneer",
        "vessel_type": "container",
        "capacity_teu": 5000,
        "speed_knots": 18.5,
        "fuel_consumption_rate": 50.0
      },
      "origin_port": {
        "port_id": "P001",
        "name": "Singapore",
        "port_type": "seaport",
        "location": {"lat": 1.29, "lon": 103.85},
        "berth_capacity": 20,
        "handling_cost_per_hour": 1500
      },
      "destination_port": {
        "port_id": "P002",
        "name": "Rotterdam",
        "port_type": "seaport",
        "location": {"lat": 51.92, "lon": 4.48},
        "berth_capacity": 25,
        "handling_cost_per_hour": 2000
      },
      "cargo": [
        {
          "cargo_id": "C001",
          "cargo_type": "container",
          "weight_tons": 150,
          "priority": 8
        }
      ],
      "optimization_goal": "balance_all"
    }
    ```
    """
    try:
        # Load module configuration
        module_config = await load_module_config(db, "maritime_logistics")
        logger.info(f"✓ Loaded config for maritime_logistics")

        # Initialize service with config
        service = MaritimeLogisticsService(db, settings, config=module_config)
        result = await service.optimize_route(request)
        return result
    except Exception as e:
        logger.error(f"Error in optimize_route endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchRoutesResponse)
async def search_routes(
    request: SearchRoutesRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    **Search Historical Routes**

    Search and filter optimized routes by:
    - Vessel type
    - Origin/destination ports
    - Optimization goal
    - Efficiency score threshold

    **Returns**:
    - List of matching route records
    - Summary statistics
    - Total count

    **Example**:
    ```json
    {
      "vessel_type": "container",
      "origin_port_id": "P001",
      "min_efficiency_score": 80,
      "limit": 20
    }
    ```
    """
    try:
        # Load module configuration
        module_config = await load_module_config(db, "maritime_logistics")
        logger.info(f"✓ Loaded config for maritime_logistics")

        # Initialize service with config
        service = MaritimeLogisticsService(db, settings, config=module_config)
        result = await service.search_routes(request)
        return result
    except Exception as e:
        logger.error(f"Error in search_routes endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export", response_model=ExportRoutesResponse)
async def export_routes(
    request: ExportRoutesRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    **Export Routes**

    Export route data in multiple formats:
    - JSON: Structured data with full details
    - CSV: Tabular format for spreadsheet analysis
    - PDF: Professional report with visualizations

    **Filters**:
    - Specific route IDs
    - Vessel type
    - Date range

    **Returns**:
    - Formatted export data
    - Record count
    - Format confirmation

    **Example**:
    ```json
    {
      "vessel_type": "container",
      "date_from": "2025-01-01T00:00:00Z",
      "date_to": "2025-12-31T23:59:59Z",
      "format": "csv"
    }
    ```
    """
    try:
        # Load module configuration
        module_config = await load_module_config(db, "maritime_logistics")
        logger.info(f"✓ Loaded config for maritime_logistics")

        # Initialize service with config
        service = MaritimeLogisticsService(db, settings, config=module_config)
        result = await service.export_routes(request)
        return result
    except Exception as e:
        logger.error(f"Error in export_routes endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=MaritimeStatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    **Maritime Logistics Statistics**

    Get comprehensive statistics:
    - Total routes optimized
    - Total distance traveled (nautical miles)
    - Total fuel cost savings
    - Average optimization scores
    - Most efficient vessel types
    - Busiest ports
    - Weather impact analysis

    **Returns**:
    - Aggregate statistics
    - Performance metrics
    - Trend data

    **Example Response**:
    ```json
    {
      "success": true,
      "total_routes_optimized": 1250,
      "total_distance_traveled_nm": 5600000,
      "total_fuel_saved_usd": 12500000,
      "average_optimization_score": 87.5,
      "most_efficient_vessel_type": "container",
      "busiest_ports": [
        {"port_name": "Singapore", "route_count": 450},
        {"port_name": "Rotterdam", "route_count": 380}
      ]
    }
    ```
    """
    try:
        # Load module configuration
        module_config = await load_module_config(db, "maritime_logistics")
        logger.info(f"✓ Loaded config for maritime_logistics")

        # Initialize service with config
        service = MaritimeLogisticsService(db, settings, config=module_config)
        result = await service.get_stats()
        return result
    except Exception as e:
        logger.error(f"Error in get_stats endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=StatusResponse)
async def get_status(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    **Service Status**

    Check service health and capabilities.

    **Returns**:
    - Service operational status
    - Version information
    - Available capabilities
    - Feature list

    **Example Response**:
    ```json
    {
      "success": true,
      "service_name": "Maritime Logistics Optimizer",
      "version": "1.0.0",
      "status": "operational",
      "capabilities": [
        "Route Optimization",
        "Port Scheduling",
        "Cargo Loading Plans",
        "Weather Impact Assessment",
        "Cost Optimization",
        "AI-Powered Insights"
      ]
    }
    ```
    """
    try:
        # Load module configuration
        module_config = await load_module_config(db, "maritime_logistics")
        logger.info(f"✓ Loaded config for maritime_logistics")

        # Initialize service with config
        service = MaritimeLogisticsService(db, settings, config=module_config)
        result = await service.get_status()
        return result
    except Exception as e:
        logger.error(f"Error in get_status endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
