"""
Maritime Logistics Optimizer - Pydantic Schemas
AI-powered maritime logistics optimization with route planning, port scheduling, and cargo management.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class VesselType(str, Enum):
    """Types of maritime vessels"""
    CONTAINER = "container"
    TANKER = "tanker"
    BULK = "bulk"
    RO_RO = "ro_ro"
    GENERAL_CARGO = "general_cargo"


class PortType(str, Enum):
    """Types of ports"""
    SEAPORT = "seaport"
    RIVER_PORT = "river_port"
    INLAND_PORT = "inland_port"


class CargoType(str, Enum):
    """Types of cargo"""
    CONTAINER = "container"
    BULK = "bulk"
    LIQUID = "liquid"
    BREAKBULK = "breakbulk"


class RouteOptimizationGoal(str, Enum):
    """Optimization objectives"""
    MINIMIZE_COST = "minimize_cost"
    MINIMIZE_TIME = "minimize_time"
    MINIMIZE_FUEL = "minimize_fuel"
    BALANCE_ALL = "balance_all"


class WeatherCondition(str, Enum):
    """Weather conditions"""
    CLEAR = "clear"
    MODERATE = "moderate"
    ROUGH = "rough"
    SEVERE = "severe"
    STORM = "storm"


class RouteStatus(str, Enum):
    """Route status"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    CANCELLED = "cancelled"


# ============================================================================
# Request/Response Models
# ============================================================================

class Vessel(BaseModel):
    """Vessel information"""
    vessel_id: str
    name: str
    vessel_type: VesselType
    capacity_teu: Optional[int] = Field(None, description="Twenty-foot Equivalent Unit capacity")
    capacity_tons: Optional[float] = Field(None, ge=0.0)
    speed_knots: float = Field(..., ge=0.0, le=50.0)
    fuel_consumption_rate: float = Field(..., ge=0.0, description="Fuel consumption per hour")
    current_location: Optional[Dict[str, float]] = Field(None, description="Lat/Lon coordinates")


class Port(BaseModel):
    """Port information"""
    port_id: str
    name: str
    port_type: PortType
    location: Dict[str, float] = Field(..., description="Lat/Lon coordinates")
    berth_capacity: int = Field(..., ge=1)
    handling_cost_per_hour: float = Field(..., ge=0.0)
    average_wait_time_hours: Optional[float] = Field(None, ge=0.0)


class CargoItem(BaseModel):
    """Cargo item details"""
    cargo_id: str
    cargo_type: CargoType
    weight_tons: float = Field(..., ge=0.0)
    volume_cubic_meters: Optional[float] = Field(None, ge=0.0)
    value_usd: Optional[float] = Field(None, ge=0.0)
    special_handling: Optional[str] = None
    priority: int = Field(default=5, ge=1, le=10, description="Priority 1-10, 10=highest")


class RouteSegment(BaseModel):
    """Route segment between ports"""
    from_port: Port
    to_port: Port
    distance_nautical_miles: float = Field(..., ge=0.0)
    estimated_duration_hours: float = Field(..., ge=0.0)
    fuel_cost_usd: float = Field(..., ge=0.0)
    weather_condition: WeatherCondition


class OptimizeRouteRequest(BaseModel):
    """Request for route optimization"""
    vessel: Vessel
    origin_port: Port
    destination_port: Port
    intermediate_ports: Optional[List[Port]] = Field(default_factory=list)
    cargo: List[CargoItem]
    optimization_goal: RouteOptimizationGoal = RouteOptimizationGoal.BALANCE_ALL
    consider_weather: bool = Field(default=True)
    max_intermediate_stops: int = Field(default=3, ge=0, le=10)
    departure_time: Optional[datetime] = None
    arrival_deadline: Optional[datetime] = None


class OptimizedRoute(BaseModel):
    """Optimized route result"""
    route_id: str
    segments: List[RouteSegment]
    total_distance_nm: float
    total_duration_hours: float
    total_fuel_cost_usd: float
    total_port_fees_usd: float
    total_cost_usd: float
    estimated_arrival: datetime
    optimization_score: float = Field(..., ge=0.0, le=100.0)
    weather_risk_level: str
    fuel_efficiency_rating: str


class PortSchedule(BaseModel):
    """Port scheduling information"""
    port: Port
    arrival_time: datetime
    departure_time: datetime
    berth_number: Optional[int] = None
    handling_operations: List[str]
    estimated_cost_usd: float


class CargoLoadingPlan(BaseModel):
    """Cargo loading optimization plan"""
    cargo_item: CargoItem
    position: str
    load_sequence: int
    weight_distribution_score: float = Field(..., ge=0.0, le=100.0)
    stability_impact: str


class OptimizeRouteResponse(BaseModel):
    """Response from route optimization"""
    success: bool
    optimized_route: OptimizedRoute
    port_schedule: List[PortSchedule]
    cargo_loading_plan: List[CargoLoadingPlan]
    vessel_performance_metrics: Dict[str, Any]
    ai_insights: str
    recommendations: List[str]
    alternative_routes: Optional[List[OptimizedRoute]] = None


class SearchRoutesRequest(BaseModel):
    """Search for historical routes"""
    vessel_type: Optional[VesselType] = None
    origin_port_id: Optional[str] = None
    destination_port_id: Optional[str] = None
    optimization_goal: Optional[RouteOptimizationGoal] = None
    min_efficiency_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    limit: int = Field(default=10, ge=1, le=100)


class RouteRecord(BaseModel):
    """Historical route record"""
    route_id: str
    vessel_type: VesselType
    origin_port: str
    destination_port: str
    total_distance_nm: float
    total_duration_hours: float
    total_cost_usd: float
    optimization_score: float
    created_at: datetime


class SearchRoutesResponse(BaseModel):
    """Response from route search"""
    success: bool
    routes: List[RouteRecord]
    total_count: int
    summary_stats: Dict[str, Any]


class ExportRoutesRequest(BaseModel):
    """Export routes request"""
    route_ids: Optional[List[str]] = None
    vessel_type: Optional[VesselType] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    format: str = Field(default="json", pattern="^(json|csv|pdf)$")


class ExportRoutesResponse(BaseModel):
    """Response from export"""
    success: bool
    export_data: Any
    format: str
    record_count: int


class MaritimeStatsResponse(BaseModel):
    """Maritime logistics statistics"""
    success: bool
    total_routes_optimized: int
    total_distance_traveled_nm: float
    total_fuel_saved_usd: float
    average_optimization_score: float
    most_efficient_vessel_type: str
    busiest_ports: List[Dict[str, Any]]
    weather_impact_stats: Dict[str, Any]


class StatusResponse(BaseModel):
    """Service status"""
    success: bool
    service_name: str = "Maritime Logistics Optimizer"
    version: str = "1.0.0"
    status: str
    capabilities: List[str]
