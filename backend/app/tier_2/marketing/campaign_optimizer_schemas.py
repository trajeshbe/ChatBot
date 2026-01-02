"""
Campaign Optimizer Schemas
Tier 2 Module: Marketing

Pydantic models for marketing campaign optimization and performance analysis.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class MarketingChannel(str, Enum):
    """Marketing channels"""
    EMAIL = "email"
    SOCIAL_MEDIA = "social_media"
    SEARCH_ADS = "search_ads"
    DISPLAY_ADS = "display_ads"
    VIDEO_ADS = "video_ads"
    CONTENT_MARKETING = "content_marketing"
    INFLUENCER = "influencer"
    AFFILIATE = "affiliate"
    DIRECT = "direct"
    ORGANIC = "organic"


class CampaignObjective(str, Enum):
    """Campaign goals"""
    BRAND_AWARENESS = "brand_awareness"
    LEAD_GENERATION = "lead_generation"
    SALES_CONVERSION = "sales_conversion"
    CUSTOMER_RETENTION = "customer_retention"
    ENGAGEMENT = "engagement"
    TRAFFIC = "traffic"
    APP_INSTALLS = "app_installs"


class OptimizationGoal(str, Enum):
    """What to optimize for"""
    MAXIMIZE_ROI = "maximize_roi"
    MINIMIZE_CPA = "minimize_cpa"  # Cost per acquisition
    MAXIMIZE_CONVERSIONS = "maximize_conversions"
    MAXIMIZE_REACH = "maximize_reach"
    MAXIMIZE_ENGAGEMENT = "maximize_engagement"
    BALANCE_ALL = "balance_all"


class AudienceSegment(str, Enum):
    """Target audience segments"""
    MILLENNIALS = "millennials"
    GEN_Z = "gen_z"
    GEN_X = "gen_x"
    BABY_BOOMERS = "baby_boomers"
    B2B = "b2b"
    B2C = "b2c"
    ENTERPRISE = "enterprise"
    SMB = "smb"
    CUSTOM = "custom"


class CampaignPerformance(BaseModel):
    """Campaign performance metrics"""
    campaign_id: str
    campaign_name: str
    channel: MarketingChannel
    objective: CampaignObjective
    budget_allocated: float = Field(..., ge=0.0)
    budget_spent: float = Field(..., ge=0.0)
    impressions: int = Field(..., ge=0)
    clicks: int = Field(..., ge=0)
    conversions: int = Field(..., ge=0)
    revenue_generated: float = Field(..., ge=0.0)
    cost_per_click: Optional[float] = Field(None, ge=0.0)
    cost_per_conversion: Optional[float] = Field(None, ge=0.0)
    conversion_rate: Optional[float] = Field(None, ge=0.0, le=100.0)
    roi: Optional[float] = Field(None, description="Return on Investment percentage")
    duration_days: Optional[int] = Field(None, ge=1)
    target_audience: List[AudienceSegment] = Field(default_factory=list)


class ABTestVariant(BaseModel):
    """A/B test variant"""
    variant_id: str
    variant_name: str
    description: Optional[str] = None
    impressions: int = Field(..., ge=0)
    clicks: int = Field(..., ge=0)
    conversions: int = Field(..., ge=0)
    click_through_rate: float = Field(..., ge=0.0, le=100.0)
    conversion_rate: float = Field(..., ge=0.0, le=100.0)
    confidence_level: Optional[float] = Field(None, ge=0.0, le=100.0, description="Statistical significance")


class BudgetAllocation(BaseModel):
    """Budget allocation recommendation"""
    channel: MarketingChannel
    current_allocation: float = Field(..., ge=0.0, description="Current budget %")
    recommended_allocation: float = Field(..., ge=0.0, le=100.0, description="Recommended budget %")
    expected_roi_improvement: float = Field(..., description="Expected ROI improvement %")
    reasoning: str = Field(..., description="Why this allocation")


class ChannelPerformanceAnalysis(BaseModel):
    """Channel-level performance analysis"""
    channel: MarketingChannel
    total_spend: float = Field(..., ge=0.0)
    total_conversions: int = Field(..., ge=0)
    average_cpa: float = Field(..., ge=0.0, description="Average cost per acquisition")
    average_roi: float
    channel_efficiency_score: float = Field(..., ge=0.0, le=100.0)
    recommended_action: str


class CampaignOptimizationRequest(BaseModel):
    """Request for campaign optimization analysis"""
    campaigns: List[CampaignPerformance] = Field(..., description="Campaign performance data")
    total_budget: float = Field(..., ge=0.0, description="Total marketing budget")
    optimization_goal: OptimizationGoal = Field(..., description="What to optimize for")
    include_ab_testing: bool = Field(False, description="Include A/B test analysis")
    include_budget_reallocation: bool = Field(True, description="Recommend budget changes")
    include_channel_analysis: bool = Field(True, description="Analyze channel performance")
    target_roi: Optional[float] = Field(None, description="Target ROI percentage")
    session_id: Optional[str] = None
    project_id: Optional[str] = None


class CampaignOptimizationResponse(BaseModel):
    """Response with optimization recommendations"""
    overall_performance_score: float = Field(..., ge=0.0, le=100.0)
    current_total_roi: float
    projected_roi_after_optimization: float
    budget_allocations: List[BudgetAllocation] = Field(default_factory=list)
    channel_analyses: List[ChannelPerformanceAnalysis] = Field(default_factory=list)
    top_performing_campaigns: List[CampaignPerformance] = Field(default_factory=list)
    underperforming_campaigns: List[CampaignPerformance] = Field(default_factory=list)
    ab_test_results: List[ABTestVariant] = Field(default_factory=list)
    optimization_recommendations: List[str] = Field(default_factory=list)
    ai_insights: List[str] = Field(default_factory=list)
    expected_improvement_percent: float


class SearchOptimizationsRequest(BaseModel):
    """Search historical optimizations"""
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    optimization_goal: Optional[OptimizationGoal] = None
    channel: Optional[MarketingChannel] = None
    min_roi: Optional[float] = None
    limit: int = Field(20, ge=1, le=100)


class ExportOptimizationsRequest(BaseModel):
    """Export optimization data"""
    optimization_ids: Optional[List[str]] = None
    session_id: Optional[str] = None
    format: str = Field("json", pattern="^(json|csv|excel|pdf)$")


class OptimizationStatsResponse(BaseModel):
    """Optimization statistics"""
    total_optimizations_performed: int
    optimizations_by_goal: Dict[str, int] = Field(default_factory=dict)
    average_roi_improvement: Optional[float] = None
    total_budget_optimized: float = Field(0.0, ge=0.0)
    top_performing_channels: List[str] = Field(default_factory=list)
    average_performance_score: Optional[float] = Field(None, ge=0.0, le=100.0)
