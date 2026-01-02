"""
Talent Pulse Schemas
Tier 2 Module: HR & Talent

Pydantic models for employee sentiment and engagement analysis.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class SentimentScore(str, Enum):
    """Sentiment classification"""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class EngagementLevel(str, Enum):
    """Employee engagement levels"""
    HIGHLY_ENGAGED = "highly_engaged"
    ENGAGED = "engaged"
    MODERATELY_ENGAGED = "moderately_engaged"
    DISENGAGED = "disengaged"
    HIGHLY_DISENGAGED = "highly_disengaged"


class FeedbackCategory(str, Enum):
    """Feedback topic categories"""
    COMPENSATION = "compensation"
    WORK_LIFE_BALANCE = "work_life_balance"
    CAREER_GROWTH = "career_growth"
    MANAGEMENT = "management"
    CULTURE = "culture"
    WORKLOAD = "workload"
    RECOGNITION = "recognition"
    TEAM_COLLABORATION = "team_collaboration"
    TOOLS_RESOURCES = "tools_resources"
    GENERAL = "general"


class RiskLevel(str, Enum):
    """Attrition risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EmployeeFeedback(BaseModel):
    """Individual employee feedback"""
    employee_id: str
    feedback_text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    feedback_type: str = Field("survey", description="survey, comment, review, exit_interview")
    department: Optional[str] = None
    tenure_months: Optional[int] = Field(None, ge=0)


class SentimentAnalysis(BaseModel):
    """Sentiment analysis result"""
    sentiment_score: SentimentScore
    confidence: float = Field(..., ge=0.0, le=100.0)
    key_phrases: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    emotions: Dict[str, float] = Field(default_factory=dict, description="joy, anger, sadness, etc.")


class EngagementMetrics(BaseModel):
    """Employee engagement metrics"""
    engagement_level: EngagementLevel
    engagement_score: float = Field(..., ge=0.0, le=100.0)
    satisfaction_score: float = Field(..., ge=0.0, le=100.0)
    eNPS: Optional[float] = Field(None, ge=-100.0, le=100.0, description="Employee Net Promoter Score")
    participation_rate: float = Field(..., ge=0.0, le=100.0)


class AttritionRisk(BaseModel):
    """Employee attrition risk assessment"""
    employee_id: str
    risk_level: RiskLevel
    risk_score: float = Field(..., ge=0.0, le=100.0)
    risk_factors: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    predicted_departure_window_months: Optional[int] = None


class TrendData(BaseModel):
    """Time-series trend data"""
    period: str = Field(..., description="YYYY-MM or YYYY-WW")
    value: float
    trend_direction: str = Field(..., pattern="^(up|down|stable)$")


class TalentPulseRequest(BaseModel):
    """Request to analyze employee sentiment and engagement"""
    feedback_data: List[EmployeeFeedback]
    analyze_sentiment: bool = Field(True)
    calculate_engagement: bool = Field(True)
    assess_attrition_risk: bool = Field(False)
    identify_trends: bool = Field(False)
    time_period_months: Optional[int] = Field(3, ge=1, le=24, description="Lookback period for trends")
    session_id: Optional[str] = None
    project_id: Optional[str] = None


class TalentPulseResponse(BaseModel):
    """Response with sentiment and engagement analysis"""
    overall_sentiment: SentimentAnalysis
    engagement_metrics: EngagementMetrics
    department_breakdown: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    category_insights: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    attrition_risks: List[AttritionRisk] = Field(default_factory=list)
    trends: List[TrendData] = Field(default_factory=list)
    key_insights: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)
    total_feedback_analyzed: int


class SearchPulseAnalysesRequest(BaseModel):
    """Search historical pulse analyses"""
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    department: Optional[str] = None
    min_engagement_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    limit: int = Field(20, ge=1, le=100)


class ExportPulseAnalysisRequest(BaseModel):
    """Export pulse analyses"""
    analysis_ids: Optional[List[str]] = None
    session_id: Optional[str] = None
    department: Optional[str] = None
    format: str = Field("json", pattern="^(json|csv|excel|pdf)$")


class PulseStatsResponse(BaseModel):
    """Talent pulse statistics"""
    total_analyses_performed: int
    total_feedback_processed: int
    avg_engagement_score: float
    avg_sentiment_score: float
    high_risk_employees_count: int
    top_feedback_categories: List[Dict[str, Any]] = Field(default_factory=list)
    department_engagement_comparison: Dict[str, float] = Field(default_factory=dict)
