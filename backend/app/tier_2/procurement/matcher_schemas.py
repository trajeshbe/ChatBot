"""
Matcher Module Schemas
Tier 2 Module: Procurement

Pydantic models for PO-to-invoice matching and reconciliation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class MatchStatus(str, Enum):
    """Match status between PO and invoice"""
    EXACT_MATCH = "exact_match"
    PARTIAL_MATCH = "partial_match"
    NO_MATCH = "no_match"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class DiscrepancyType(str, Enum):
    """Types of discrepancies"""
    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MISSING_INVOICE = "missing_invoice"
    DUPLICATE_INVOICE = "duplicate_invoice"
    VENDOR_MISMATCH = "vendor_mismatch"
    DATE_MISMATCH = "date_mismatch"
    TOTAL_AMOUNT_VARIANCE = "total_amount_variance"
    TAX_VARIANCE = "tax_variance"
    LINE_ITEM_MISMATCH = "line_item_mismatch"


class LineItem(BaseModel):
    """Line item in PO or invoice"""
    item_id: Optional[str] = None
    description: str
    quantity: float
    unit_price: float
    total: float
    tax_amount: Optional[float] = None
    discount_amount: Optional[float] = None


class PurchaseOrder(BaseModel):
    """Purchase order details"""
    po_number: str
    vendor_name: str
    vendor_id: Optional[str] = None
    po_date: Optional[datetime] = None
    total_amount: float
    tax_amount: Optional[float] = None
    currency: str = "USD"
    line_items: List[LineItem] = []
    department: Optional[str] = None
    requester: Optional[str] = None
    delivery_date: Optional[datetime] = None


class Invoice(BaseModel):
    """Invoice details"""
    invoice_number: str
    vendor_name: str
    vendor_id: Optional[str] = None
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    total_amount: float
    tax_amount: Optional[float] = None
    currency: str = "USD"
    line_items: List[LineItem] = []
    payment_terms: Optional[str] = None
    po_number_reference: Optional[str] = None


class Discrepancy(BaseModel):
    """Identified discrepancy"""
    discrepancy_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    discrepancy_type: DiscrepancyType
    description: str
    po_value: Optional[Any] = None
    invoice_value: Optional[Any] = None
    variance_amount: Optional[float] = None
    variance_percent: Optional[float] = None
    severity: str = Field(..., description="critical, high, medium, low")
    recommended_action: str


class MatchResult(BaseModel):
    """Result of PO-to-invoice matching"""
    match_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    po_number: str
    invoice_number: str
    match_status: MatchStatus
    match_confidence: float = Field(ge=0.0, le=1.0)
    total_variance_amount: float = 0.0
    total_variance_percent: float = 0.0
    discrepancies: List[Discrepancy] = []
    matched_line_items: int = 0
    total_line_items: int = 0
    requires_approval: bool = False
    approval_threshold_exceeded: bool = False


class POMatchRequest(BaseModel):
    """Request to match PO with invoices"""
    po_document_id: Optional[str] = Field(None, description="Document ID of PO")
    invoice_document_id: Optional[str] = Field(None, description="Document ID of invoice")
    po_data: Optional[PurchaseOrder] = Field(None, description="Manual PO data")
    invoice_data: Optional[Invoice] = Field(None, description="Manual invoice data")
    use_document_extraction: bool = Field(True, description="Extract data from documents using LLM")
    variance_tolerance_percent: float = Field(5.0, description="Acceptable variance %", ge=0.0, le=100.0)
    auto_approve_threshold_percent: float = Field(2.0, description="Auto-approve if variance below this %", ge=0.0, le=100.0)
    session_id: Optional[str] = None
    project_id: Optional[str] = None


class BulkMatchRequest(BaseModel):
    """Bulk matching request"""
    po_document_ids: List[str] = Field(default_factory=list)
    invoice_document_ids: List[str] = Field(default_factory=list)
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    variance_tolerance_percent: float = Field(5.0, ge=0.0, le=100.0)
    auto_approve_threshold_percent: float = Field(2.0, ge=0.0, le=100.0)
    parallel_workers: int = Field(4, ge=1, le=20, description="Number of parallel workers")


class POMatchResponse(BaseModel):
    """Response from PO matching"""
    match_id: str
    po_number: str
    invoice_number: str
    match_status: MatchStatus
    match_confidence: float
    po_summary: Dict[str, Any]
    invoice_summary: Dict[str, Any]
    match_result: MatchResult
    processing_time_seconds: float
    tier_1_services_used: List[str] = []


class BulkMatchResponse(BaseModel):
    """Bulk matching response"""
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    total_matches: int
    exact_matches: int
    partial_matches: int
    no_matches: int
    requires_review: int
    total_variance_amount: float
    avg_match_confidence: float
    matches: List[MatchResult]
    processing_time_seconds: float


class SearchMatchesRequest(BaseModel):
    """Search for matches"""
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    match_status: Optional[MatchStatus] = None
    vendor_name: Optional[str] = None
    min_variance_amount: Optional[float] = None
    requires_approval: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)


class ExportMatchesRequest(BaseModel):
    """Export matches request"""
    match_ids: List[str] = Field(default_factory=list)
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    format: str = Field("excel", description="json, csv, excel, pdf")
    include_discrepancies: bool = True
    include_line_items: bool = True


class MatcherStatsResponse(BaseModel):
    """Matcher statistics"""
    total_matches: int
    exact_matches: int
    partial_matches: int
    no_matches: int
    avg_match_confidence: float
    total_variance_amount: float
    matches_requiring_approval: int
    top_discrepancy_types: List[Dict[str, Any]]
    top_vendors_by_variance: List[Dict[str, Any]]


class ApprovalDecisionRequest(BaseModel):
    """Approval decision for a match"""
    match_id: str
    decision: str = Field(..., description="approve or reject")
    approver_id: str
    comments: Optional[str] = None
    override_variance: bool = Field(False, description="Approve despite variance")


class ApprovalDecisionResponse(BaseModel):
    """Approval decision response"""
    match_id: str
    decision: str
    previous_status: MatchStatus
    new_status: MatchStatus
    approved_at: datetime
    approved_by: str
