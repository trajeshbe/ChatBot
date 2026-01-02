"""
Spend Smart Module Schemas
Tier 2 Module: Procurement

Pydantic models for spending pattern analysis and cost optimization.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class SpendCategory(str, Enum):
    """Spending categories"""
    IT = "it"
    OFFICE_SUPPLIES = "office_supplies"
    FACILITIES = "facilities"
    PROFESSIONAL_SERVICES = "professional_services"
    MARKETING = "marketing"
    TRAVEL = "travel"
    UTILITIES = "utilities"
    MAINTENANCE = "maintenance"
    OTHER = "other"


class AnomalyType(str, Enum):
    """Types of spending anomalies"""
    UNUSUAL_SPIKE = "unusual_spike"
    UNUSUAL_DROP = "unusual_drop"
    DUPLICATE_PAYMENT = "duplicate_payment"
    VENDOR_OVERSPEND = "vendor_overspend"
    CATEGORY_OVERSPEND = "category_overspend"
    OFF_CONTRACT_SPEND = "off_contract_spend"


class SpendingPattern(BaseModel):
    """Identified spending pattern"""
    pattern_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: SpendCategory
    trend: str  # increasing, decreasing, stable, seasonal
    avg_monthly_spend: float
    total_annual_spend: float
    top_vendors: List[Dict[str, Any]] = []
    seasonality: Optional[Dict[str, Any]] = None


class SavingsOpportunity(BaseModel):
    """Cost savings opportunity"""
    opportunity_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    category: SpendCategory
    potential_savings: float
    implementation_effort: str  # low, medium, high
    time_to_realize: str  # immediate, short_term, long_term
    confidence_level: float = Field(..., ge=0.0, le=1.0)


class SpendAnomaly(BaseModel):
    """Detected spending anomaly"""
    anomaly_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    anomaly_type: AnomalyType
    category: SpendCategory
    description: str
    amount: float
    expected_amount: Optional[float] = None
    deviation_percent: Optional[float] = None
    vendor: Optional[str] = None
    transaction_date: Optional[datetime] = None
    severity: str  # critical, high, medium, low


class SpendAnalysisRequest(BaseModel):
    """Request for spend analysis"""
    time_period_months: int = Field(12, ge=1, le=36, description="Analysis period in months")
    categories: List[SpendCategory] = Field(default_factory=list, description="Categories to analyze (empty = all)")
    detect_anomalies: bool = True
    identify_savings: bool = True
    analyze_vendor_spend: bool = True
    budget_amount: Optional[float] = None
    session_id: Optional[str] = None
    project_id: Optional[str] = None


class SpendAnalysisResponse(BaseModel):
    """Spend analysis response"""
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    time_period_months: int
    total_spend: float
    avg_monthly_spend: float
    spend_by_category: Dict[str, float]
    spending_patterns: List[SpendingPattern]
    savings_opportunities: List[SavingsOpportunity] = []
    anomalies: List[SpendAnomaly] = []
    total_potential_savings: float
    vendor_concentration_risk: Optional[Dict[str, Any]] = None
    budget_utilization_percent: Optional[float] = None
    key_insights: List[str]
    recommendations: List[str]
    processing_time_seconds: float
    tier_1_services_used: List[str] = []


class SearchSpendAnalysesRequest(BaseModel):
    """Search spend analyses"""
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    min_total_spend: Optional[float] = None
    has_anomalies: Optional[bool] = None
    limit: int = Field(100, ge=1, le=1000)


class ExportSpendAnalysisRequest(BaseModel):
    """Export spend analysis request"""
    analysis_ids: List[str] = Field(default_factory=list)
    session_id: Optional[str] = None
    format: str = Field("excel", description="json, csv, excel, pdf")
    include_patterns: bool = True
    include_anomalies: bool = True
    include_savings: bool = True


class SpendStatsResponse(BaseModel):
    """Spend analytics statistics"""
    total_analyses: int
    total_spend_analyzed: float
    total_potential_savings: float
    avg_savings_per_analysis: float
    total_anomalies_detected: int
    top_spending_categories: List[Dict[str, Any]]
