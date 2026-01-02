"""
Vendor Recommendation Module Schemas
Tier 2 Module: Procurement

Pydantic models for vendor recommendation and evaluation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class VendorCategory(str, Enum):
    """Vendor categories"""
    IT_HARDWARE = "it_hardware"
    IT_SOFTWARE = "it_software"
    IT_SERVICES = "it_services"
    OFFICE_SUPPLIES = "office_supplies"
    FACILITIES = "facilities"
    PROFESSIONAL_SERVICES = "professional_services"
    MARKETING = "marketing"
    MANUFACTURING = "manufacturing"
    LOGISTICS = "logistics"
    CONSTRUCTION = "construction"
    CONSULTING = "consulting"
    TELECOMMUNICATIONS = "telecommunications"


class EvaluationCriteria(str, Enum):
    """Vendor evaluation criteria"""
    COST = "cost"
    QUALITY = "quality"
    DELIVERY_TIME = "delivery_time"
    RELIABILITY = "reliability"
    LOCATION = "location"
    CERTIFICATIONS = "certifications"
    SUSTAINABILITY = "sustainability"
    PAYMENT_TERMS = "payment_terms"
    CUSTOMER_SERVICE = "customer_service"
    INNOVATION = "innovation"


class VendorPerformance(BaseModel):
    """Historical vendor performance metrics"""
    vendor_id: str
    vendor_name: str
    total_orders: int = 0
    total_spend: float = 0.0
    avg_delivery_days: Optional[float] = None
    on_time_delivery_percent: Optional[float] = None
    quality_rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    defect_rate_percent: Optional[float] = None
    invoice_accuracy_percent: Optional[float] = None
    response_time_hours: Optional[float] = None
    certifications: List[str] = []
    last_order_date: Optional[datetime] = None


class VendorProfile(BaseModel):
    """Vendor profile details"""
    vendor_id: str
    vendor_name: str
    category: VendorCategory
    description: Optional[str] = None
    location: Optional[str] = None
    established_year: Optional[int] = None
    employee_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    certifications: List[str] = []
    specialties: List[str] = []
    payment_terms: Optional[str] = None
    minimum_order_value: Optional[float] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None
    sustainability_rating: Optional[float] = Field(None, ge=0.0, le=5.0)


class SelectionCriteria(BaseModel):
    """Vendor selection criteria with weights"""
    criteria: EvaluationCriteria
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight (0.0-1.0)")
    target_value: Optional[Any] = None
    acceptable_range: Optional[Dict[str, Any]] = None


class VendorScore(BaseModel):
    """Vendor scoring details"""
    vendor_id: str
    vendor_name: str
    total_score: float = Field(..., ge=0.0, le=100.0)
    criteria_scores: Dict[str, float] = {}
    strengths: List[str] = []
    weaknesses: List[str] = []
    risk_factors: List[str] = []
    opportunities: List[str] = []


class VendorRecommendation(BaseModel):
    """Vendor recommendation with justification"""
    recommendation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    vendor_name: str
    category: VendorCategory
    total_score: float = Field(..., ge=0.0, le=100.0)
    rank: int = Field(..., ge=1)
    recommendation_reason: str
    key_strengths: List[str]
    potential_risks: List[str]
    estimated_cost: Optional[float] = None
    estimated_delivery_days: Optional[int] = None
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    performance_metrics: Optional[VendorPerformance] = None


class VendorRecommendationRequest(BaseModel):
    """Request for vendor recommendations"""
    category: VendorCategory
    requirement_description: str = Field(..., description="Description of what you need")
    selection_criteria: List[SelectionCriteria] = []
    budget_range_min: Optional[float] = None
    budget_range_max: Optional[float] = None
    required_delivery_days: Optional[int] = None
    required_certifications: List[str] = []
    preferred_location: Optional[str] = None
    minimum_quality_rating: float = Field(3.0, ge=0.0, le=5.0)
    exclude_vendor_ids: List[str] = []
    top_n: int = Field(5, ge=1, le=20, description="Number of recommendations")
    session_id: Optional[str] = None
    project_id: Optional[str] = None


class VendorRecommendationResponse(BaseModel):
    """Response with vendor recommendations"""
    recommendation_batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: VendorCategory
    requirement_description: str
    total_vendors_evaluated: int
    recommendations: List[VendorRecommendation]
    selection_criteria_used: List[SelectionCriteria]
    processing_time_seconds: float
    tier_1_services_used: List[str] = []


class VendorComparisonRequest(BaseModel):
    """Compare specific vendors"""
    vendor_ids: List[str] = Field(..., min_items=2, max_items=10)
    comparison_criteria: List[EvaluationCriteria] = []
    include_performance_history: bool = True
    include_cost_analysis: bool = True
    session_id: Optional[str] = None


class VendorComparisonResponse(BaseModel):
    """Vendor comparison response"""
    comparison_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendors: List[VendorProfile]
    performance_comparison: Dict[str, VendorPerformance]
    criteria_comparison: Dict[str, Dict[str, Any]]
    recommended_vendor_id: Optional[str] = None
    recommendation_reason: str
    processing_time_seconds: float


class SearchVendorsRequest(BaseModel):
    """Search vendors by criteria"""
    category: Optional[VendorCategory] = None
    min_quality_rating: Optional[float] = None
    location: Optional[str] = None
    certifications: List[str] = []
    max_cost_per_unit: Optional[float] = None
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    limit: int = Field(50, ge=1, le=500)


class ExportRecommendationsRequest(BaseModel):
    """Export recommendations request"""
    recommendation_batch_ids: List[str] = Field(default_factory=list)
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    format: str = Field("excel", description="json, csv, excel, pdf")
    include_performance_data: bool = True
    include_scoring_details: bool = True


class VendorRecommendationStatsResponse(BaseModel):
    """Vendor recommendation statistics"""
    total_recommendations: int
    unique_vendors_recommended: int
    avg_vendor_score: float
    top_categories: List[Dict[str, Any]]
    top_recommended_vendors: List[Dict[str, Any]]
    avg_confidence_level: float
