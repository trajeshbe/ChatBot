"""
Estimator One AU Schemas
Tier 2 Module: Construction

Pydantic models for Australian construction cost estimation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class ProjectType(str, Enum):
    """Australian construction project types"""
    RESIDENTIAL_HOUSE = "residential_house"
    RESIDENTIAL_UNIT = "residential_unit"
    RESIDENTIAL_TOWNHOUSE = "residential_townhouse"
    COMMERCIAL_OFFICE = "commercial_office"
    COMMERCIAL_RETAIL = "commercial_retail"
    COMMERCIAL_WAREHOUSE = "commercial_warehouse"
    INDUSTRIAL = "industrial"
    CIVIL_INFRASTRUCTURE = "civil_infrastructure"
    RENOVATION = "renovation"
    EXTENSION = "extension"


class AustralianState(str, Enum):
    """Australian states and territories"""
    NSW = "nsw"  # New South Wales
    VIC = "vic"  # Victoria
    QLD = "qld"  # Queensland
    WA = "wa"    # Western Australia
    SA = "sa"    # South Australia
    TAS = "tas"  # Tasmania
    ACT = "act"  # Australian Capital Territory
    NT = "nt"    # Northern Territory


class BuildingClass(str, Enum):
    """Building classification under BCA"""
    CLASS_1A = "class_1a"  # Single dwelling
    CLASS_1B = "class_1b"  # Boarding house, guest house
    CLASS_2 = "class_2"    # Apartment building
    CLASS_3 = "class_3"    # Hotel, motel
    CLASS_4 = "class_4"    # Dwelling in another building
    CLASS_5 = "class_5"    # Office
    CLASS_6 = "class_6"    # Shop
    CLASS_7A = "class_7a"  # Car park
    CLASS_7B = "class_7b"  # Storage, warehouse
    CLASS_8 = "class_8"    # Laboratory, factory
    CLASS_9A = "class_9a"  # Healthcare
    CLASS_9B = "class_9b"  # Assembly building
    CLASS_9C = "class_9c"  # Aged care
    CLASS_10 = "class_10"  # Non-habitable building


class CostItem(BaseModel):
    """Individual cost line item"""
    item_id: str
    category: str = Field(..., description="Category: preliminaries, substructure, superstructure, finishes, services, external_works")
    description: str
    quantity: float
    unit: str = Field(..., description="Unit: m², m³, m, ea, item, sum")
    rate_aud: float = Field(..., description="Rate in AUD")
    total_aud: float = Field(..., description="Total in AUD")
    notes: Optional[str] = None


class EstimateBreakdown(BaseModel):
    """Detailed cost estimate breakdown"""
    # Elemental costs (AUD)
    preliminaries_aud: float = Field(default=0.0, description="Site establishment, management")
    substructure_aud: float = Field(default=0.0, description="Foundations, basement")
    superstructure_aud: float = Field(default=0.0, description="Frame, floors, roof, stairs")
    external_walls_aud: float = Field(default=0.0, description="External walls, windows, doors")
    internal_walls_aud: float = Field(default=0.0, description="Partitions, internal doors")
    finishes_aud: float = Field(default=0.0, description="Floor, wall, ceiling finishes")
    services_aud: float = Field(default=0.0, description="Plumbing, HVAC, electrical, fire")
    external_works_aud: float = Field(default=0.0, description="Landscaping, driveways, fencing")

    # Statutory costs
    authority_fees_aud: float = Field(default=0.0, description="Council, water, utility fees")
    consultants_aud: float = Field(default=0.0, description="Architect, engineer, certifier fees")

    # Margins
    contingency_aud: float = Field(default=0.0, description="Contingency allowance")
    profit_margin_aud: float = Field(default=0.0, description="Builder profit and overhead")

    # GST
    subtotal_ex_gst_aud: float
    gst_aud: float = Field(..., description="10% GST")
    total_inc_gst_aud: float


class CostEstimateRequest(BaseModel):
    """Request for Australian construction cost estimate"""
    document_id: Optional[str] = Field(None, description="Document ID with project details")
    session_id: Optional[str] = None
    project_id: Optional[str] = None

    # Project details (if not from document)
    project_type: Optional[ProjectType] = None
    state: AustralianState = Field(..., description="Australian state/territory")
    building_class: Optional[BuildingClass] = None

    # Dimensions
    gross_floor_area_sqm: Optional[float] = Field(None, description="Gross floor area in m²")
    site_area_sqm: Optional[float] = None
    num_bedrooms: Optional[int] = None
    num_bathrooms: Optional[int] = None
    num_storeys: Optional[int] = None

    # Specifications
    quality_level: str = Field(default="standard", description="Quality: basic, standard, high, premium")
    include_site_costs: bool = Field(default=True, description="Include site works and external costs")

    # Estimation options
    use_document_extraction: bool = Field(default=True, description="Extract details from document")
    include_detailed_breakdown: bool = Field(default=True, description="Provide elemental breakdown")
    include_comparables: bool = Field(default=True, description="Include market comparables")


class CostEstimateResponse(BaseModel):
    """Response with Australian construction cost estimate"""
    estimate_id: str
    document_id: Optional[str] = None

    # Project summary
    project_type: Optional[ProjectType] = None
    state: AustralianState
    building_class: Optional[BuildingClass] = None
    gross_floor_area_sqm: float
    quality_level: str

    # Cost summary (AUD)
    total_cost_ex_gst_aud: float
    total_cost_inc_gst_aud: float
    cost_per_sqm_aud: float = Field(..., description="Cost per square meter")

    # Detailed breakdown
    breakdown: Optional[EstimateBreakdown] = None
    line_items: List[CostItem] = Field(default_factory=list)

    # Market context
    market_comparables: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Comparable projects in the region"
    )
    state_avg_cost_per_sqm_aud: Optional[float] = Field(
        None,
        description="State average cost/m² for project type"
    )
    variance_from_average: Optional[float] = Field(
        None,
        description="Percentage variance from state average"
    )

    # Assumptions and exclusions
    key_assumptions: List[str] = Field(default_factory=list)
    exclusions: List[str] = Field(default_factory=list)

    # Metadata
    estimate_date: datetime = Field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None
    confidence_level: float = Field(ge=0.0, le=1.0, description="Estimate confidence")
    tier_1_services_used: List[str] = Field(default_factory=list)


class EstimateComparisonRequest(BaseModel):
    """Request to compare estimates"""
    estimate_ids: List[str] = Field(..., min_items=2, max_items=5)
    comparison_basis: str = Field(
        default="cost_per_sqm",
        description="Basis: cost_per_sqm, total_cost, elemental_costs"
    )


class EstimateComparisonResponse(BaseModel):
    """Comparison of multiple estimates"""
    comparison_id: str
    num_estimates: int

    # Comparative metrics
    cost_per_sqm_comparison: Dict[str, float] = Field(default_factory=dict)
    total_cost_comparison: Dict[str, float] = Field(default_factory=dict)
    elemental_cost_comparison: Dict[str, Dict[str, float]] = Field(default_factory=dict)

    # Analysis
    lowest_cost_estimate_id: str
    highest_cost_estimate_id: str
    avg_cost_per_sqm_aud: float
    cost_variance_percent: float

    insights: List[str] = Field(default_factory=list)


class ExportEstimateRequest(BaseModel):
    """Request to export cost estimate"""
    estimate_ids: Optional[List[str]] = None
    session_id: Optional[str] = None
    project_id: Optional[str] = None

    format: str = Field(default="pdf", description="Format: pdf, excel, csv, json")
    include_line_items: bool = True
    include_comparables: bool = True
    include_charts: bool = True
