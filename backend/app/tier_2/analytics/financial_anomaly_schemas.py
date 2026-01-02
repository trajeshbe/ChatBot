"""Financial Anomaly Detector - Data Schemas"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime


class AnomalyType(str, Enum):
    """Types of financial anomalies"""
    UNUSUAL_TRANSACTION = "unusual_transaction"
    FRAUD_PATTERN = "fraud_pattern"
    SPENDING_SPIKE = "spending_spike"
    REVENUE_DROP = "revenue_drop"
    DUPLICATE_TRANSACTION = "duplicate_transaction"
    ACCOUNT_TAKEOVER = "account_takeover"
    REFUND_ABUSE = "refund_abuse"


class RiskLevel(str, Enum):
    """Risk severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class TransactionCategory(str, Enum):
    """Transaction categories"""
    PAYMENT = "payment"
    REFUND = "refund"
    TRANSFER = "transfer"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    PURCHASE = "purchase"


class TransactionData(BaseModel):
    """Financial transaction data"""
    transaction_id: str
    account_id: str
    amount: float
    category: TransactionCategory
    timestamp: datetime
    merchant: Optional[str] = None
    location: Optional[str] = None
    ip_address: Optional[str] = None
    device_id: Optional[str] = None


class AccountData(BaseModel):
    """Account profile data"""
    account_id: str
    account_type: str
    created_date: datetime
    typical_daily_volume: float = Field(..., ge=0.0)
    typical_transaction_amount: float = Field(..., ge=0.0)
    country: Optional[str] = None


class DetectAnomaliesRequest(BaseModel):
    """Request for anomaly detection"""
    transactions: List[TransactionData]
    accounts: List[AccountData]
    detection_sensitivity: float = Field(default=0.7, ge=0.0, le=1.0)
    include_fraud_scoring: bool = Field(default=True)
    historical_window_days: int = Field(default=30, ge=1, le=365)


class AnomalyDetection(BaseModel):
    """Detected anomaly"""
    transaction_id: str
    account_id: str
    anomaly_type: AnomalyType
    risk_level: RiskLevel
    anomaly_score: float = Field(..., ge=0.0, le=100.0)
    deviation_percentage: float
    description: str
    contributing_factors: List[str]
    recommended_actions: List[str]
    similar_cases_detected: int = Field(default=0, ge=0)


class FraudRiskScore(BaseModel):
    """Fraud risk assessment"""
    transaction_id: str
    fraud_probability: float = Field(..., ge=0.0, le=100.0)
    risk_level: RiskLevel
    fraud_indicators: List[str]
    behavioral_patterns: List[str]
    recommended_verification: List[str]


class AnomalyPattern(BaseModel):
    """Detected anomaly pattern"""
    pattern_id: str
    pattern_type: str
    affected_accounts: int
    total_transactions: int
    total_amount: float
    first_occurrence: datetime
    last_occurrence: datetime
    severity: RiskLevel


class DetectAnomaliesResponse(BaseModel):
    """Response for anomaly detection"""
    success: bool
    anomalies: List[AnomalyDetection]
    fraud_scores: List[FraudRiskScore]
    patterns: List[AnomalyPattern]
    summary_stats: Dict[str, float]
    ai_insights: str
    risk_mitigation_recommendations: List[str]


class SearchAnomaliesRequest(BaseModel):
    """Request to search historical anomalies"""
    account_ids: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    anomaly_types: Optional[List[AnomalyType]] = None
    min_risk_level: Optional[RiskLevel] = None
    limit: int = Field(default=100, ge=1, le=1000)


class SearchAnomaliesResponse(BaseModel):
    """Response for anomaly search"""
    success: bool
    anomalies: List[AnomalyDetection]
    total_count: int
    summary_stats: Dict[str, float]


class ExportAnomaliesRequest(BaseModel):
    """Request to export anomaly data"""
    account_ids: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    format: str = Field(default="csv", pattern="^(csv|json|excel)$")
    include_fraud_scores: bool = Field(default=True)


class ExportAnomaliesResponse(BaseModel):
    """Response for anomaly export"""
    success: bool
    export_data: Dict
    format: str
    record_count: int


class AnomalyStatsResponse(BaseModel):
    """Anomaly detection statistics"""
    success: bool
    total_anomalies_detected: int
    total_transactions_analyzed: int
    anomaly_rate: float
    fraud_rate: float
    most_common_anomaly_type: str
    average_anomaly_score: float
    total_amount_flagged: float


class StatusResponse(BaseModel):
    """Service status response"""
    success: bool
    status: str
    capabilities: List[str]
