"""
Mine Scope Schemas
Tier 2 Module: Construction

Pydantic models for analyzing mining scope documents and extracting requirements.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class MineScopeType(str, Enum):
    """Types of mining scope documents"""
    EXPLORATION = "exploration"
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    RECLAMATION = "reclamation"
    FEASIBILITY_STUDY = "feasibility_study"
    ENVIRONMENTAL_ASSESSMENT = "environmental_assessment"
    SAFETY_PLAN = "safety_plan"
    EQUIPMENT_SPECIFICATION = "equipment_specification"
    OPERATIONAL_PLAN = "operational_plan"
    UNKNOWN = "unknown"


class MiningSector(str, Enum):
    """Mining sectors"""
    COAL = "coal"
    GOLD = "gold"
    IRON_ORE = "iron_ore"
    COPPER = "copper"
    LITHIUM = "lithium"
    RARE_EARTH = "rare_earth"
    NICKEL = "nickel"
    ZINC = "zinc"
    BAUXITE = "bauxite"
    DIAMOND = "diamond"
    SILVER = "silver"
    PLATINUM = "platinum"
    OTHER = "other"


class MiningMethod(str, Enum):
    """Mining extraction methods"""
    OPEN_PIT = "open_pit"
    UNDERGROUND = "underground"
    PLACER = "placer"
    IN_SITU = "in_situ"
    STRIP_MINING = "strip_mining"
    DREDGING = "dredging"
    MOUNTAINTOP_REMOVAL = "mountaintop_removal"
    SOLUTION_MINING = "solution_mining"
    UNKNOWN = "unknown"


class ScopeRequirement(BaseModel):
    """Individual requirement extracted from scope document"""
    requirement_id: str
    requirement_type: str = Field(
        ...,
        description="Type: technical, regulatory, safety, environmental, operational, financial"
    )
    description: str
    priority: str = Field(..., description="Priority: critical, high, medium, low")
    source_section: Optional[str] = Field(None, description="Document section/page")
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractedMetrics(BaseModel):
    """Quantitative metrics extracted from mining scope"""
    # Production
    target_production_rate: Optional[str] = Field(None, description="e.g., '10,000 tonnes/day'")
    annual_production_target: Optional[str] = None
    ore_reserve_estimate: Optional[str] = None
    ore_grade: Optional[str] = Field(None, description="e.g., '2.5% copper'")

    # Operational
    mine_life_years: Optional[float] = None
    depth_meters: Optional[float] = None
    pit_dimensions: Optional[str] = None
    haul_distance_km: Optional[float] = None

    # Equipment
    fleet_size: Optional[int] = None
    equipment_types: List[str] = Field(default_factory=list)

    # Workforce
    workforce_size: Optional[int] = None
    contractor_count: Optional[int] = None

    # Financial
    capex_estimate: Optional[str] = None
    opex_estimate: Optional[str] = None
    roi_years: Optional[float] = None

    # Timeline
    construction_duration_months: Optional[int] = None
    ramp_up_duration_months: Optional[int] = None


class IdentifiedRisk(BaseModel):
    """Risk identified in scope document"""
    risk_id: str
    risk_category: str = Field(
        ...,
        description="Category: safety, environmental, geological, operational, financial, regulatory"
    )
    description: str
    severity: str = Field(..., description="Severity: critical, high, medium, low")
    likelihood: str = Field(..., description="Likelihood: high, medium, low")
    mitigation_strategy: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)


class ComplianceRequirement(BaseModel):
    """Regulatory/compliance requirement"""
    regulation_name: str
    jurisdiction: Optional[str] = None
    requirement_description: str
    deadline: Optional[str] = None
    status: str = Field(default="pending", description="Status: compliant, in_progress, pending, non_compliant")


class MineScopeAnalysisRequest(BaseModel):
    """Request to analyze mining scope document"""
    document_id: str = Field(..., description="Document ID to analyze")
    session_id: Optional[str] = None
    project_id: Optional[str] = None

    # Analysis options
    extract_requirements: bool = Field(default=True, description="Extract scope requirements")
    extract_metrics: bool = Field(default=True, description="Extract quantitative metrics")
    identify_risks: bool = Field(default=True, description="Identify risks")
    extract_compliance: bool = Field(default=True, description="Extract compliance requirements")

    # Classification
    classify_scope_type: bool = Field(default=True, description="Classify document type")
    identify_mining_method: bool = Field(default=True, description="Identify mining method")
    identify_sector: bool = Field(default=True, description="Identify mining sector")

    # Processing options
    use_vision: bool = Field(default=True, description="Use vision for diagrams/charts")
    min_confidence: float = Field(default=0.7, ge=0.0, le=1.0)


class MineScopeAnalysisResponse(BaseModel):
    """Response from mining scope analysis"""
    analysis_id: str
    document_id: str

    # Classification
    scope_type: Optional[MineScopeType] = None
    mining_sector: Optional[MiningSector] = None
    mining_method: Optional[MiningMethod] = None
    classification_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # Extracted content
    requirements: List[ScopeRequirement] = Field(default_factory=list)
    metrics: Optional[ExtractedMetrics] = None
    risks: List[IdentifiedRisk] = Field(default_factory=list)
    compliance_requirements: List[ComplianceRequirement] = Field(default_factory=list)

    # Summary
    executive_summary: Optional[str] = Field(
        None,
        description="AI-generated summary of scope document"
    )
    key_findings: List[str] = Field(default_factory=list)

    # Counts
    total_requirements: int = 0
    critical_requirements: int = 0
    total_risks: int = 0
    high_severity_risks: int = 0

    # Processing metadata
    processing_time_seconds: float
    tier_1_services_used: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScopeSearchRequest(BaseModel):
    """Search for analyzed mining scopes"""
    session_id: Optional[str] = None
    project_id: Optional[str] = None

    # Filters
    scope_types: Optional[List[MineScopeType]] = None
    mining_sectors: Optional[List[MiningSector]] = None
    mining_methods: Optional[List[MiningMethod]] = None
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Requirement filters
    requirement_types: Optional[List[str]] = None
    has_critical_requirements: Optional[bool] = None
    has_high_severity_risks: Optional[bool] = None

    # Pagination
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class ScopeSearchResponse(BaseModel):
    """Search results for analyzed scopes"""
    total_count: int
    returned_count: int
    results: List[MineScopeAnalysisResponse]

    # Aggregations
    scope_type_counts: Dict[str, int] = Field(default_factory=dict)
    sector_counts: Dict[str, int] = Field(default_factory=dict)
    method_counts: Dict[str, int] = Field(default_factory=dict)

    limit: int
    offset: int
    has_more: bool


class ScopeComparisonRequest(BaseModel):
    """Request to compare multiple mining scopes"""
    analysis_ids: List[str] = Field(..., min_items=2, max_items=10, description="2-10 scopes to compare")
    comparison_dimensions: List[str] = Field(
        default=["requirements", "metrics", "risks", "compliance"],
        description="Dimensions to compare"
    )


class ScopeComparisonResponse(BaseModel):
    """Comparison results for multiple scopes"""
    comparison_id: str
    analyzed_scopes: int

    # Comparative analysis
    common_requirements: List[str] = Field(default_factory=list)
    unique_requirements_by_scope: Dict[str, List[str]] = Field(default_factory=dict)

    metric_comparison: Dict[str, Any] = Field(default_factory=dict)
    risk_comparison: Dict[str, Any] = Field(default_factory=dict)

    # Summary
    comparison_summary: str
    recommendations: List[str] = Field(default_factory=list)


class ExportScopeRequest(BaseModel):
    """Request to export scope analysis"""
    analysis_ids: Optional[List[str]] = None
    session_id: Optional[str] = None
    project_id: Optional[str] = None

    format: str = Field(default="json", description="Export format: json, csv, excel, pdf")
    include_detailed_requirements: bool = True
    include_risk_matrix: bool = True
    include_metrics: bool = True
    include_compliance_checklist: bool = True
