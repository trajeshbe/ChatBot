"""Healthcare Diagnostics AI - Data Schemas"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime


class DiagnosticCategory(str, Enum):
    """Medical diagnostic categories"""
    CARDIOLOGY = "cardiology"
    RADIOLOGY = "radiology"
    PATHOLOGY = "pathology"
    NEUROLOGY = "neurology"
    ONCOLOGY = "oncology"
    GENERAL = "general"


class SeverityLevel(str, Enum):
    """Condition severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    MINIMAL = "minimal"


class ConfidenceLevel(str, Enum):
    """AI confidence levels"""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class PatientData(BaseModel):
    """Patient medical data"""
    patient_id: str
    age: int = Field(..., ge=0, le=150)
    gender: str
    symptoms: List[str]
    vital_signs: Optional[Dict[str, float]] = None
    medical_history: Optional[List[str]] = None
    lab_results: Optional[Dict[str, float]] = None
    imaging_results: Optional[List[str]] = None


class AnalyzeSymptomsRequest(BaseModel):
    """Request for symptom analysis"""
    patient: PatientData
    category: DiagnosticCategory = DiagnosticCategory.GENERAL
    include_recommendations: bool = Field(default=True)
    urgency_assessment: bool = Field(default=True)


class DiagnosticHypothesis(BaseModel):
    """Potential diagnosis"""
    condition: str
    probability: float = Field(..., ge=0.0, le=100.0)
    severity: SeverityLevel
    confidence: ConfidenceLevel
    supporting_evidence: List[str]
    differential_diagnosis: List[str]
    recommended_tests: List[str]


class TreatmentRecommendation(BaseModel):
    """Treatment recommendation"""
    treatment_type: str
    description: str
    priority: int = Field(..., ge=1, le=5)
    expected_outcome: str
    contraindications: List[str]


class UrgencyAssessment(BaseModel):
    """Patient urgency assessment"""
    urgency_score: int = Field(..., ge=0, le=100)
    severity_level: SeverityLevel
    time_sensitive: bool
    immediate_actions: List[str]
    warning_signs: List[str]


class AnalyzeSymptomsResponse(BaseModel):
    """Response for symptom analysis"""
    success: bool
    diagnoses: List[DiagnosticHypothesis]
    treatment_recommendations: List[TreatmentRecommendation]
    urgency: Optional[UrgencyAssessment] = None
    ai_insights: str
    disclaimer: str = "This is an AI-assisted diagnosis. Consult a licensed medical professional for definitive diagnosis and treatment."


class SearchDiagnosesRequest(BaseModel):
    """Request to search historical diagnoses"""
    patient_ids: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    categories: Optional[List[DiagnosticCategory]] = None
    min_confidence: Optional[ConfidenceLevel] = None
    limit: int = Field(default=100, ge=1, le=1000)


class SearchDiagnosesResponse(BaseModel):
    """Response for diagnosis search"""
    success: bool
    diagnoses: List[DiagnosticHypothesis]
    total_count: int
    summary_stats: Dict[str, float]


class ExportDiagnosesRequest(BaseModel):
    """Request to export diagnostic data"""
    patient_ids: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    format: str = Field(default="csv", pattern="^(csv|json|excel)$")
    include_recommendations: bool = Field(default=True)


class ExportDiagnosesResponse(BaseModel):
    """Response for diagnosis export"""
    success: bool
    export_data: Dict
    format: str
    record_count: int


class DiagnosticStatsResponse(BaseModel):
    """Diagnostic statistics"""
    success: bool
    total_diagnoses: int
    total_patients: int
    category_distribution: Dict[str, int]
    average_confidence: float
    critical_cases: int
    most_common_condition: str


class StatusResponse(BaseModel):
    """Service status response"""
    success: bool
    status: str
    capabilities: List[str]
