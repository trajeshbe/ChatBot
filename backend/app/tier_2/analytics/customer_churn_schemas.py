"""Customer Churn Predictor - Pydantic Schemas"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class ChurnRiskLevel(str, Enum):
    """Churn risk levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class CustomerSegment(str, Enum):
    """Customer segments"""
    VIP = "vip"
    REGULAR = "regular"
    OCCASIONAL = "occasional"
    AT_RISK = "at_risk"
    CHURNED = "churned"


class RetentionStrategy(str, Enum):
    """Retention strategy types"""
    DISCOUNT = "discount"
    LOYALTY_PROGRAM = "loyalty_program"
    PERSONALIZED_OFFER = "personalized_offer"
    ENGAGEMENT_CAMPAIGN = "engagement_campaign"
    PREMIUM_SUPPORT = "premium_support"


class CustomerData(BaseModel):
    """Customer data for churn prediction"""
    customer_id: str
    tenure_months: int = Field(..., ge=0)
    monthly_spend: float = Field(..., ge=0.0)
    purchase_frequency: int = Field(..., ge=0, description="Purchases in last 3 months")
    last_purchase_days_ago: int = Field(..., ge=0)
    support_tickets: int = Field(default=0, ge=0)
    contract_type: str = Field(default="month_to_month")
    payment_method: str = Field(default="credit_card")
    has_discount: bool = Field(default=False)
    satisfaction_score: Optional[float] = Field(None, ge=0.0, le=10.0)


class PredictChurnRequest(BaseModel):
    """Request for churn prediction"""
    customers: List[CustomerData] = Field(..., min_items=1, max_items=1000)
    include_retention_strategies: bool = Field(default=True)
    risk_threshold: float = Field(default=0.5, ge=0.0, le=1.0)


class ChurnPrediction(BaseModel):
    """Churn prediction for a customer"""
    customer_id: str
    churn_probability: float = Field(..., ge=0.0, le=100.0)
    risk_level: ChurnRiskLevel
    customer_segment: CustomerSegment
    key_risk_factors: List[str]
    lifetime_value_estimate: float
    retention_priority: int = Field(..., ge=1, le=10)


class RetentionRecommendation(BaseModel):
    """Retention strategy recommendation"""
    customer_id: str
    strategy: RetentionStrategy
    description: str
    expected_success_rate: float = Field(..., ge=0.0, le=100.0)
    estimated_cost: float
    estimated_value_retention: float


class PredictChurnResponse(BaseModel):
    """Response from churn prediction"""
    success: bool
    predictions: List[ChurnPrediction]
    retention_recommendations: List[RetentionRecommendation]
    segment_summary: Dict[str, int]
    risk_distribution: Dict[str, int]
    ai_insights: str
    overall_recommendations: List[str]


class SearchPredictionsRequest(BaseModel):
    """Search historical predictions"""
    customer_id: Optional[str] = None
    risk_level: Optional[ChurnRiskLevel] = None
    segment: Optional[CustomerSegment] = None
    min_churn_probability: Optional[float] = Field(None, ge=0.0, le=100.0)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(default=10, ge=1, le=100)


class PredictionRecord(BaseModel):
    """Historical prediction record"""
    prediction_id: str
    customer_id: str
    prediction_date: datetime
    churn_probability: float
    risk_level: ChurnRiskLevel
    actual_churned: Optional[bool] = None


class SearchPredictionsResponse(BaseModel):
    """Response from prediction search"""
    success: bool
    predictions: List[PredictionRecord]
    total_count: int
    summary_stats: Dict[str, Any]


class ExportPredictionsRequest(BaseModel):
    """Export predictions request"""
    prediction_ids: Optional[List[str]] = None
    risk_level: Optional[ChurnRiskLevel] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    format: str = Field(default="json", pattern="^(json|csv|excel)$")


class ExportPredictionsResponse(BaseModel):
    """Response from export"""
    success: bool
    export_data: Any
    format: str
    record_count: int


class ChurnStatsResponse(BaseModel):
    """Churn prediction statistics"""
    success: bool
    total_predictions: int
    total_customers_analyzed: int
    average_churn_probability: float
    risk_level_distribution: Dict[str, int]
    segment_distribution: Dict[str, int]
    retention_success_rate: float
    most_effective_strategy: str


class StatusResponse(BaseModel):
    """Service status"""
    success: bool
    service_name: str = "Customer Churn Predictor"
    version: str = "1.0.0"
    status: str
    capabilities: List[str]
