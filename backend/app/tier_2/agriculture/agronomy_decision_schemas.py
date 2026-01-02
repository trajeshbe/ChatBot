"""
Agronomy Decision Schemas
Tier 2 Module: Agriculture

Pydantic models for agronomy decision support and recommendation systems.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class DecisionType(str, Enum):
    """Types of agronomy decisions"""
    PLANTING = "planting"
    IRRIGATION = "irrigation"
    FERTILIZATION = "fertilization"
    PEST_CONTROL = "pest_control"
    DISEASE_MANAGEMENT = "disease_management"
    HARVESTING = "harvesting"
    CROP_ROTATION = "crop_rotation"
    SOIL_AMENDMENT = "soil_amendment"


class WeatherPattern(str, Enum):
    """Weather pattern classifications"""
    SUNNY = "sunny"
    RAINY = "rainy"
    CLOUDY = "cloudy"
    STORMY = "stormy"
    DROUGHT = "drought"
    FROST = "frost"


class CropHealthStatus(str, Enum):
    """Crop health indicators"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class RecommendationPriority(str, Enum):
    """Priority levels for recommendations"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    OPTIONAL = "optional"


class SoilCondition(BaseModel):
    """Current soil condition parameters"""
    moisture_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    ph_level: Optional[float] = Field(None, ge=0.0, le=14.0)
    nitrogen_ppm: Optional[float] = Field(None, ge=0.0)
    phosphorus_ppm: Optional[float] = Field(None, ge=0.0)
    potassium_ppm: Optional[float] = Field(None, ge=0.0)
    organic_matter_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    temperature_celsius: Optional[float] = None
    salinity_ec: Optional[float] = Field(None, ge=0.0, description="Electrical conductivity in dS/m")


class WeatherData(BaseModel):
    """Weather and climate information"""
    current_temperature_celsius: Optional[float] = None
    forecast_7day_pattern: Optional[WeatherPattern] = None
    rainfall_last_7days_mm: Optional[float] = Field(None, ge=0.0)
    rainfall_forecast_7days_mm: Optional[float] = Field(None, ge=0.0)
    humidity_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    wind_speed_kmh: Optional[float] = Field(None, ge=0.0)
    frost_risk: bool = False
    drought_risk: bool = False


class CropHealthIndicators(BaseModel):
    """Crop health assessment parameters"""
    overall_health_status: CropHealthStatus
    growth_stage: Optional[str] = None
    leaf_color_index: Optional[float] = Field(None, ge=0.0, le=100.0, description="Normalized Difference Vegetation Index (NDVI)")
    pest_infestation_level: Optional[float] = Field(None, ge=0.0, le=100.0)
    disease_severity: Optional[float] = Field(None, ge=0.0, le=100.0)
    water_stress_level: Optional[float] = Field(None, ge=0.0, le=100.0)
    nutrient_deficiency_indicators: List[str] = Field(default_factory=list)
    observed_issues: List[str] = Field(default_factory=list)


class DecisionContext(BaseModel):
    """Context information for decision-making"""
    farm_location: Optional[str] = None
    farm_size_hectares: Optional[float] = Field(None, ge=0.0)
    crop_type: str = Field(..., description="Current or planned crop")
    crop_variety: Optional[str] = None
    planting_date: Optional[str] = None
    expected_harvest_date: Optional[str] = None
    soil_condition: Optional[SoilCondition] = None
    weather_data: Optional[WeatherData] = None
    crop_health: Optional[CropHealthIndicators] = None
    previous_crops: List[str] = Field(default_factory=list, description="For crop rotation decisions")
    available_resources: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AgronomyRecommendation(BaseModel):
    """Single agronomy recommendation"""
    recommendation_id: str
    decision_type: DecisionType
    priority: RecommendationPriority
    action: str = Field(..., description="Recommended action to take")
    reasoning: str = Field(..., description="Why this action is recommended")
    expected_outcome: str = Field(..., description="Expected result if action is taken")
    timing: Optional[str] = Field(None, description="When to implement (e.g., 'within 24 hours', 'next week')")
    estimated_cost: Optional[float] = Field(None, ge=0.0, description="Estimated cost in local currency")
    confidence_score: float = Field(..., ge=0.0, le=100.0, description="AI confidence in recommendation")
    supporting_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    alternative_options: List[str] = Field(default_factory=list)


class DecisionAnalysis(BaseModel):
    """Complete decision analysis result"""
    decision_type: DecisionType
    recommendations: List[AgronomyRecommendation]
    risk_factors: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    key_considerations: List[str] = Field(default_factory=list)
    optimal_timing_window: Optional[str] = None
    estimated_yield_impact: Optional[str] = None


class AgronomyDecisionRequest(BaseModel):
    """Request for agronomy decision support"""
    decision_types: List[DecisionType] = Field(..., description="Types of decisions needed")
    context: DecisionContext
    use_ai_analysis: bool = Field(True, description="Use LLM for advanced analysis")
    include_alternatives: bool = Field(True, description="Include alternative recommendations")
    prioritize_sustainability: bool = Field(False, description="Prioritize sustainable practices")
    budget_constraint: Optional[float] = Field(None, ge=0.0, description="Budget limit for recommendations")
    session_id: Optional[str] = None
    project_id: Optional[str] = None


class AgronomyDecisionResponse(BaseModel):
    """Response with agronomy decisions and recommendations"""
    analyses: List[DecisionAnalysis]
    overall_farm_health_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    critical_actions_count: int = Field(0, ge=0)
    estimated_total_cost: Optional[float] = Field(None, ge=0.0)
    sustainability_rating: Optional[str] = None
    ai_insights: List[str] = Field(default_factory=list)


class SearchDecisionsRequest(BaseModel):
    """Search historical decisions"""
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    decision_type: Optional[DecisionType] = None
    crop_type: Optional[str] = None
    priority: Optional[RecommendationPriority] = None
    limit: int = Field(20, ge=1, le=100)


class ExportDecisionsRequest(BaseModel):
    """Export decision data"""
    decision_ids: Optional[List[str]] = None
    session_id: Optional[str] = None
    decision_type: Optional[DecisionType] = None
    format: str = Field("json", pattern="^(json|csv|excel|pdf)$")


class DecisionStatsResponse(BaseModel):
    """Decision statistics"""
    total_decisions_made: int
    decisions_by_type: Dict[str, int] = Field(default_factory=dict)
    decisions_by_priority: Dict[str, int] = Field(default_factory=dict)
    average_confidence_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    most_common_crop_types: List[str] = Field(default_factory=list)
    sustainability_metrics: Optional[Dict[str, Any]] = Field(default_factory=dict)
