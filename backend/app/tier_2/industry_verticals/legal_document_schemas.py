"""Legal Document Analyzer - Data Schemas"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime


class DocumentType(str, Enum):
    CONTRACT = "contract"
    AGREEMENT = "agreement"
    LEASE = "lease"
    LITIGATION = "litigation"
    PATENT = "patent"
    REGULATORY = "regulatory"


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class ClauseType(str, Enum):
    TERMINATION = "termination"
    CONFIDENTIALITY = "confidentiality"
    INDEMNITY = "indemnity"
    LIABILITY = "liability"
    PAYMENT = "payment"
    DISPUTE_RESOLUTION = "dispute_resolution"


class AnalyzeDocumentRequest(BaseModel):
    document_id: str
    document_text: str
    document_type: DocumentType
    include_risk_assessment: bool = Field(default=True)
    include_clause_extraction: bool = Field(default=True)


class ExtractedClause(BaseModel):
    clause_type: ClauseType
    clause_text: str
    risk_level: RiskLevel
    concerns: List[str]
    recommendations: List[str]


class RiskAssessment(BaseModel):
    overall_risk: RiskLevel
    risk_score: float = Field(..., ge=0.0, le=100.0)
    risk_factors: List[str]
    mitigation_strategies: List[str]


class AnalyzeDocumentResponse(BaseModel):
    success: bool
    document_id: str
    extracted_clauses: List[ExtractedClause]
    risk_assessment: Optional[RiskAssessment] = None
    key_terms: List[str]
    ai_insights: str
    legal_disclaimer: str = "AI analysis for informational purposes. Consult licensed attorney for legal advice."


class SearchDocumentsRequest(BaseModel):
    document_types: Optional[List[DocumentType]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_risk_level: Optional[RiskLevel] = None
    limit: int = Field(default=100, ge=1, le=1000)


class SearchDocumentsResponse(BaseModel):
    success: bool
    documents: List[Dict]
    total_count: int


class ExportAnalysisRequest(BaseModel):
    document_ids: List[str]
    format: str = Field(default="pdf", pattern="^(pdf|docx|json)$")


class ExportAnalysisResponse(BaseModel):
    success: bool
    export_data: Dict
    format: str


class LegalStatsResponse(BaseModel):
    success: bool
    total_documents_analyzed: int
    high_risk_documents: int
    most_common_document_type: str


class StatusResponse(BaseModel):
    success: bool
    status: str
    capabilities: List[str]
