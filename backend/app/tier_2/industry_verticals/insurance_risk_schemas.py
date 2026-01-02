"""Insurance Risk Assessor - Data Schemas"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum

class InsuranceType(str, Enum):
    AUTO = "auto"
    HOME = "home"
    LIFE = "life"
    HEALTH = "health"

class RiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class AssessRiskRequest(BaseModel):
    policy_id: str
    insurance_type: InsuranceType
    applicant_age: int = Field(..., ge=0, le=120)
    coverage_amount: float = Field(..., gt=0)
    risk_factors: List[str]

class AssessRiskResponse(BaseModel):
    success: bool
    policy_id: str
    risk_score: float = Field(..., ge=0.0, le=100.0)
    risk_level: RiskLevel
    premium_estimate: float
    risk_factors_analysis: List[Dict]
    ai_insights: str

class SearchAssessmentsRequest(BaseModel):
    insurance_types: Optional[List[InsuranceType]] = None
    limit: int = Field(default=100, ge=1, le=1000)

class SearchAssessmentsResponse(BaseModel):
    success: bool
    assessments: List[Dict]
    total_count: int

class ExportAssessmentsRequest(BaseModel):
    policy_ids: List[str]
    format: str = Field(default="pdf", pattern="^(pdf|csv|json)$")

class ExportAssessmentsResponse(BaseModel):
    success: bool
    export_data: Dict
    format: str

class InsuranceStatsResponse(BaseModel):
    success: bool
    total_assessments: int
    average_risk_score: float

class StatusResponse(BaseModel):
    success: bool
    status: str
    capabilities: List[str]
