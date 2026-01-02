"""
Predictive Analytics Engine - Pydantic Schemas
AI-powered predictive analytics for business forecasting and trend analysis.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class ForecastModel(str, Enum):
    """Forecasting model types"""
    ARIMA = "arima"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    PROPHET = "prophet"
    ML_ENSEMBLE = "ml_ensemble"


class TimeGranularity(str, Enum):
    """Time series granularity"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class TrendType(str, Enum):
    """Trend classification"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    SEASONAL = "seasonal"
    VOLATILE = "volatile"


class AnomalyType(str, Enum):
    """Anomaly types"""
    SPIKE = "spike"
    DROP = "drop"
    OUTLIER = "outlier"
    PATTERN_BREAK = "pattern_break"


# ============================================================================
# Request/Response Models
# ============================================================================

class TimeSeriesDataPoint(BaseModel):
    """Single time series data point"""
    timestamp: datetime
    value: float = Field(..., description="Metric value")
    metadata: Optional[Dict[str, Any]] = None


class ForecastRequest(BaseModel):
    """Request for time series forecasting"""
    series_name: str
    historical_data: List[TimeSeriesDataPoint]
    forecast_periods: int = Field(..., ge=1, le=365, description="Number of periods to forecast")
    granularity: TimeGranularity = TimeGranularity.DAILY
    model_type: ForecastModel = ForecastModel.ML_ENSEMBLE
    confidence_level: float = Field(default=0.95, ge=0.5, le=0.99)
    detect_seasonality: bool = Field(default=True)
    detect_anomalies: bool = Field(default=True)


class ForecastPoint(BaseModel):
    """Single forecast point"""
    timestamp: datetime
    predicted_value: float
    lower_bound: float
    upper_bound: float
    confidence: float = Field(..., ge=0.0, le=100.0)


class TrendAnalysis(BaseModel):
    """Trend analysis results"""
    trend_type: TrendType
    strength: float = Field(..., ge=0.0, le=100.0, description="Trend strength percentage")
    direction: str
    rate_of_change: float
    description: str


class SeasonalityPattern(BaseModel):
    """Seasonality detection results"""
    detected: bool
    period: Optional[int] = None
    strength: Optional[float] = Field(None, ge=0.0, le=100.0)
    pattern_description: Optional[str] = None


class Anomaly(BaseModel):
    """Detected anomaly"""
    timestamp: datetime
    actual_value: float
    expected_value: float
    deviation: float
    anomaly_type: AnomalyType
    severity: float = Field(..., ge=0.0, le=100.0)
    explanation: str


class ModelPerformance(BaseModel):
    """Forecast model performance metrics"""
    model_used: ForecastModel
    mae: float = Field(..., description="Mean Absolute Error")
    rmse: float = Field(..., description="Root Mean Square Error")
    mape: float = Field(..., description="Mean Absolute Percentage Error")
    r_squared: float = Field(..., ge=0.0, le=1.0)
    accuracy_score: float = Field(..., ge=0.0, le=100.0)


class ForecastResponse(BaseModel):
    """Response from forecasting"""
    success: bool
    series_name: str
    forecast: List[ForecastPoint]
    trend_analysis: TrendAnalysis
    seasonality: SeasonalityPattern
    anomalies: List[Anomaly]
    model_performance: ModelPerformance
    ai_insights: str
    recommendations: List[str]
    metadata: Dict[str, Any]


class SearchForecastsRequest(BaseModel):
    """Search historical forecasts"""
    series_name: Optional[str] = None
    model_type: Optional[ForecastModel] = None
    min_accuracy: Optional[float] = Field(None, ge=0.0, le=100.0)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(default=10, ge=1, le=100)


class ForecastRecord(BaseModel):
    """Historical forecast record"""
    forecast_id: str
    series_name: str
    model_type: ForecastModel
    forecast_date: datetime
    periods_forecasted: int
    accuracy_score: float
    trend_type: TrendType


class SearchForecastsResponse(BaseModel):
    """Response from forecast search"""
    success: bool
    forecasts: List[ForecastRecord]
    total_count: int
    summary_stats: Dict[str, Any]


class ExportForecastsRequest(BaseModel):
    """Export forecasts request"""
    forecast_ids: Optional[List[str]] = None
    series_name: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    format: str = Field(default="json", pattern="^(json|csv|excel)$")


class ExportForecastsResponse(BaseModel):
    """Response from export"""
    success: bool
    export_data: Any
    format: str
    record_count: int


class PredictiveStatsResponse(BaseModel):
    """Predictive analytics statistics"""
    success: bool
    total_forecasts_generated: int
    total_series_analyzed: int
    average_accuracy: float
    most_accurate_model: str
    trend_distribution: Dict[str, int]
    seasonality_detection_rate: float
    anomaly_detection_count: int


class StatusResponse(BaseModel):
    """Service status"""
    success: bool
    service_name: str = "Predictive Analytics Engine"
    version: str = "1.0.0"
    status: str
    capabilities: List[str]
