"""
Tender Intelligence Module Schemas
Tier 2 Module: Procurement

Pydantic models for tender/RFP analysis and bid intelligence.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class TenderType(str, Enum):
    """Types of tenders"""
    OPEN_TENDER = "open_tender"
    SELECTIVE_TENDER = "selective_tender"
    RESTRICTED_TENDER = "restricted_tender"
    RFP = "rfp"
    RFQ = "rfq"
    RFI = "rfi"
    EOI = "eoi"


class BidRecommendation(str, Enum):
    """Bid/no-bid recommendation"""
    STRONG_BID = "strong_bid"
    BID_WITH_CONDITIONS = "bid_with_conditions"
    NO_BID = "no_bid"
    UNDECIDED = "undecided"


class TenderRequirement(BaseModel):
    """Extracted tender requirement"""
    requirement_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str  # technical, financial, legal, experience
    description: str
    mandatory: bool = True
    weight: Optional[float] = Field(None, ge=0.0, le=1.0)


class EvaluationCriterion(BaseModel):
    """Tender evaluation criterion"""
    criterion_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    weight: float = Field(..., ge=0.0, le=1.0)
    scoring_method: Optional[str] = None


class TenderAnalysisRequest(BaseModel):
    """Request to analyze tender document"""
    document_id: str = Field(..., description="Tender document ID")
    analyze_requirements: bool = True
    analyze_evaluation_criteria: bool = True
    assess_bid_viability: bool = True
    identify_compliance: bool = True
    session_id: Optional[str] = None
    project_id: Optional[str] = None


class TenderAnalysisResponse(BaseModel):
    """Tender analysis response"""
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    tender_summary: Dict[str, Any]
    tender_type: TenderType
    requirements: List[TenderRequirement] = []
    evaluation_criteria: List[EvaluationCriterion] = []
    key_deadlines: List[Dict[str, Any]] = []
    estimated_contract_value: Optional[float] = None
    contract_duration_months: Optional[int] = None
    bid_viability: Dict[str, Any]
    compliance_requirements: List[str] = []
    bid_recommendation: BidRecommendation
    recommendation_reason: str
    win_probability: float = Field(..., ge=0.0, le=1.0)
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    processing_time_seconds: float
    tier_1_services_used: List[str] = []


class SearchTendersRequest(BaseModel):
    """Search tender analyses"""
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    tender_type: Optional[TenderType] = None
    min_contract_value: Optional[float] = None
    bid_recommendation: Optional[BidRecommendation] = None
    limit: int = Field(100, ge=1, le=1000)


class ExportTenderAnalysisRequest(BaseModel):
    """Export tender analysis request"""
    analysis_ids: List[str] = Field(default_factory=list)
    session_id: Optional[str] = None
    format: str = Field("excel", description="json, csv, excel, pdf")
    include_requirements: bool = True
    include_evaluation_criteria: bool = True


class TenderStatsResponse(BaseModel):
    """Tender intelligence statistics"""
    total_analyses: int
    bid_recommendations: Dict[str, int]
    avg_win_probability: float
    avg_contract_value: float
    top_tender_types: List[Dict[str, Any]]
