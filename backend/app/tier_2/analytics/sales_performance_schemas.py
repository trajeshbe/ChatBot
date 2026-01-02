"""Sales Performance Analytics - Data Schemas"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime


class OpportunityStage(str, Enum):
    """Sales opportunity stages"""
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class SalesPerformanceMetric(str, Enum):
    """Performance metrics for sales analysis"""
    REVENUE = "revenue"
    DEALS_CLOSED = "deals_closed"
    WIN_RATE = "win_rate"
    AVERAGE_DEAL_SIZE = "average_deal_size"
    SALES_CYCLE_LENGTH = "sales_cycle_length"
    PIPELINE_VALUE = "pipeline_value"
    CONVERSION_RATE = "conversion_rate"


class PerformanceTier(str, Enum):
    """Sales rep performance tiers"""
    TOP_PERFORMER = "top_performer"
    ABOVE_AVERAGE = "above_average"
    AVERAGE = "average"
    BELOW_AVERAGE = "below_average"
    NEEDS_IMPROVEMENT = "needs_improvement"


class OpportunityData(BaseModel):
    """Sales opportunity data"""
    opportunity_id: str
    sales_rep_id: str
    stage: OpportunityStage
    value: float = Field(..., ge=0.0)
    probability: float = Field(..., ge=0.0, le=100.0)
    created_date: datetime
    expected_close_date: datetime
    product_category: Optional[str] = None
    customer_segment: Optional[str] = None


class SalesRepData(BaseModel):
    """Sales representative data"""
    rep_id: str
    rep_name: str
    region: Optional[str] = None
    team: Optional[str] = None
    tenure_months: int = Field(..., ge=0)
    quota: float = Field(..., ge=0.0)


class AnalyzeSalesRequest(BaseModel):
    """Request for sales performance analysis"""
    sales_reps: List[SalesRepData]
    opportunities: List[OpportunityData]
    period_start: datetime
    period_end: datetime
    include_win_probability: bool = Field(default=True)
    include_rep_scoring: bool = Field(default=True)


class RepPerformanceScore(BaseModel):
    """Individual sales rep performance"""
    rep_id: str
    rep_name: str
    performance_score: float = Field(..., ge=0.0, le=100.0)
    performance_tier: PerformanceTier
    total_revenue: float
    deals_closed: int
    win_rate: float
    average_deal_size: float
    pipeline_value: float
    quota_attainment: float
    key_strengths: List[str]
    improvement_areas: List[str]


class OpportunityPrediction(BaseModel):
    """Opportunity win probability prediction"""
    opportunity_id: str
    win_probability: float = Field(..., ge=0.0, le=100.0)
    predicted_close_date: datetime
    risk_factors: List[str]
    success_factors: List[str]
    recommended_actions: List[str]


class PipelineHealth(BaseModel):
    """Pipeline health metrics"""
    total_value: float
    weighted_value: float
    stage_distribution: Dict[str, int]
    average_deal_size: float
    conversion_rate: float
    health_score: float = Field(..., ge=0.0, le=100.0)
    bottleneck_stages: List[str]


class AnalyzeSalesResponse(BaseModel):
    """Response for sales analysis"""
    success: bool
    rep_scores: List[RepPerformanceScore]
    opportunity_predictions: List[OpportunityPrediction]
    pipeline_health: PipelineHealth
    period_summary: Dict[str, float]
    ai_insights: str
    strategic_recommendations: List[str]


class SearchPerformanceRequest(BaseModel):
    """Request to search historical performance"""
    rep_ids: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_performance_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    limit: int = Field(default=100, ge=1, le=1000)


class SearchPerformanceResponse(BaseModel):
    """Response for performance search"""
    success: bool
    records: List[RepPerformanceScore]
    total_count: int
    summary_stats: Dict[str, float]


class ExportPerformanceRequest(BaseModel):
    """Request to export performance data"""
    rep_ids: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    format: str = Field(default="csv", pattern="^(csv|json|excel)$")
    include_opportunities: bool = Field(default=True)


class ExportPerformanceResponse(BaseModel):
    """Response for performance export"""
    success: bool
    export_data: Dict
    format: str
    record_count: int


class PerformanceStatsResponse(BaseModel):
    """Sales performance statistics"""
    success: bool
    total_reps_analyzed: int
    total_opportunities: int
    average_win_rate: float
    average_deal_size: float
    top_performers_count: int
    total_pipeline_value: float
    quarter_over_quarter_growth: float


class StatusResponse(BaseModel):
    """Service status response"""
    success: bool
    status: str
    capabilities: List[str]
