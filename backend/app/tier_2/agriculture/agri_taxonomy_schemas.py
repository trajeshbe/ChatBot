"""
Agri Taxonomy Schemas
Tier 2 Module: Agriculture

Pydantic models for agricultural classification and taxonomy.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class CropCategory(str, Enum):
    """Crop categories"""
    CEREALS = "cereals"
    LEGUMES = "legumes"
    VEGETABLES = "vegetables"
    FRUITS = "fruits"
    OILSEEDS = "oilseeds"
    FIBER_CROPS = "fiber_crops"
    FORAGE_CROPS = "forage_crops"
    TUBER_CROPS = "tuber_crops"
    SPICES = "spices"
    MEDICINAL_PLANTS = "medicinal_plants"


class GrowthStage(str, Enum):
    """Plant growth stages"""
    GERMINATION = "germination"
    SEEDLING = "seedling"
    VEGETATIVE = "vegetative"
    FLOWERING = "flowering"
    FRUITING = "fruiting"
    MATURITY = "maturity"
    HARVEST = "harvest"


class SoilType(str, Enum):
    """Soil classifications"""
    SANDY = "sandy"
    LOAMY = "loamy"
    CLAY = "clay"
    SILT = "silt"
    PEATY = "peaty"
    CHALKY = "chalky"
    SALINE = "saline"


class ClimateZone(str, Enum):
    """Climate zone classifications"""
    TROPICAL = "tropical"
    SUBTROPICAL = "subtropical"
    TEMPERATE = "temperate"
    CONTINENTAL = "continental"
    POLAR = "polar"
    ARID = "arid"
    SEMI_ARID = "semi_arid"


class CropClassification(BaseModel):
    """Crop classification details"""
    common_name: str
    scientific_name: Optional[str] = None
    category: CropCategory
    sub_category: Optional[str] = None
    family: Optional[str] = None
    origin: Optional[str] = None
    alternate_names: List[str] = Field(default_factory=list)


class GrowingRequirements(BaseModel):
    """Environmental requirements for crops"""
    temperature_min_celsius: Optional[float] = None
    temperature_max_celsius: Optional[float] = None
    temperature_optimal_celsius: Optional[float] = None
    rainfall_min_mm: Optional[float] = None
    rainfall_max_mm: Optional[float] = None
    ph_min: Optional[float] = Field(None, ge=0.0, le=14.0)
    ph_max: Optional[float] = Field(None, ge=0.0, le=14.0)
    ph_optimal: Optional[float] = Field(None, ge=0.0, le=14.0)
    preferred_soil_types: List[SoilType] = Field(default_factory=list)
    climate_zones: List[ClimateZone] = Field(default_factory=list)
    sunlight_hours_per_day: Optional[float] = Field(None, ge=0.0, le=24.0)
    frost_tolerance: bool = False


class SeasonalInfo(BaseModel):
    """Seasonal planting and harvesting information"""
    planting_season: Optional[str] = None
    planting_months: List[str] = Field(default_factory=list)
    growth_duration_days: Optional[int] = Field(None, ge=0)
    harvest_season: Optional[str] = None
    harvest_months: List[str] = Field(default_factory=list)


class CropTaxonomy(BaseModel):
    """Complete crop taxonomy entry"""
    crop_id: str
    classification: CropClassification
    growing_requirements: GrowingRequirements
    seasonal_info: SeasonalInfo
    economic_importance: Optional[str] = None
    nutritional_value: Optional[Dict[str, Any]] = None
    common_pests: List[str] = Field(default_factory=list)
    common_diseases: List[str] = Field(default_factory=list)
    companion_plants: List[str] = Field(default_factory=list)
    incompatible_plants: List[str] = Field(default_factory=list)


class TaxonomyClassificationRequest(BaseModel):
    """Request to classify crops"""
    crop_names: List[str] = Field(..., description="List of crop names to classify")
    include_requirements: bool = Field(True, description="Include growing requirements")
    include_seasonal_info: bool = Field(True, description="Include seasonal information")
    use_llm_enrichment: bool = Field(True, description="Use LLM to enrich taxonomy data")
    session_id: Optional[str] = None
    project_id: Optional[str] = None


class TaxonomyClassificationResponse(BaseModel):
    """Response with classified crops"""
    classifications: List[CropTaxonomy]
    unclassified_crops: List[str] = Field(default_factory=list)
    total_crops_processed: int
    taxonomy_coverage_percent: float


class SearchTaxonomyRequest(BaseModel):
    """Search agricultural taxonomy"""
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    crop_name: Optional[str] = None
    category: Optional[CropCategory] = None
    climate_zone: Optional[ClimateZone] = None
    soil_type: Optional[SoilType] = None
    limit: int = Field(20, ge=1, le=100)


class ExportTaxonomyRequest(BaseModel):
    """Export taxonomy data"""
    taxonomy_ids: Optional[List[str]] = None
    session_id: Optional[str] = None
    category: Optional[CropCategory] = None
    format: str = Field("json", pattern="^(json|csv|excel)$")


class TaxonomyStatsResponse(BaseModel):
    """Taxonomy statistics"""
    total_crops_in_taxonomy: int
    total_categories: int
    total_classifications_performed: int
    crops_by_category: Dict[str, int] = Field(default_factory=dict)
    crops_by_climate_zone: Dict[str, int] = Field(default_factory=dict)
