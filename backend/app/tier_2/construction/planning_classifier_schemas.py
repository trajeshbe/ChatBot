"""
Planning Classifier Schemas
Tier 2 Module: Construction

Pydantic models for classifying planning documents by type and purpose.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class PlanningDocumentType(str, Enum):
    """Types of planning documents"""
    ARCHITECTURAL = "architectural"
    STRUCTURAL = "structural"
    ELECTRICAL = "electrical"
    MECHANICAL = "mechanical"
    PLUMBING = "plumbing"
    CIVIL = "civil"
    LANDSCAPE = "landscape"
    INTERIOR = "interior"
    FIRE_SAFETY = "fire_safety"
    BIM_MODEL = "bim_model"
    SITE_PLAN = "site_plan"
    FLOOR_PLAN = "floor_plan"
    ELEVATION = "elevation"
    SECTION = "section"
    DETAIL = "detail"
    SCHEDULE = "schedule"
    SPECIFICATION = "specification"
    UNKNOWN = "unknown"


class PlanningDocumentPurpose(str, Enum):
    """Purpose/phase of planning document"""
    CONCEPT = "concept"
    SCHEMATIC_DESIGN = "schematic_design"
    DESIGN_DEVELOPMENT = "design_development"
    CONSTRUCTION_DOCUMENTS = "construction_documents"
    AS_BUILT = "as_built"
    PERMIT_SUBMISSION = "permit_submission"
    BID = "bid"
    SHOP_DRAWINGS = "shop_drawings"
    RFI = "rfi"
    CHANGE_ORDER = "change_order"
    CLOSEOUT = "closeout"
    UNKNOWN = "unknown"


class DrawingClassification(BaseModel):
    """Classification result for a single drawing"""
    document_type: PlanningDocumentType
    purpose: PlanningDocumentPurpose
    confidence: float = Field(ge=0.0, le=1.0)
    detected_features: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PlanningClassificationRequest(BaseModel):
    """Request to classify planning documents"""
    document_id: str = Field(..., description="Document ID to classify")
    session_id: Optional[str] = Field(None, description="Session ID for context")
    project_id: Optional[str] = Field(None, description="Project ID for filtering")

    # Classification options
    use_vision: bool = Field(
        default=True,
        description="Use vision model for image-based classification"
    )
    use_text: bool = Field(
        default=True,
        description="Use text analysis for classification"
    )
    extract_metadata: bool = Field(
        default=True,
        description="Extract additional metadata (drawing number, revision, etc.)"
    )

    # Filtering
    min_confidence: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold"
    )


class ExtractedMetadata(BaseModel):
    """Metadata extracted from planning documents"""
    drawing_number: Optional[str] = None
    drawing_title: Optional[str] = None
    revision: Optional[str] = None
    scale: Optional[str] = None
    date: Optional[str] = None
    project_name: Optional[str] = None
    architect: Optional[str] = None
    engineer: Optional[str] = None
    consultant: Optional[str] = None
    sheet_size: Optional[str] = None
    zone: Optional[str] = None
    discipline: Optional[str] = None


class PlanningClassificationResponse(BaseModel):
    """Response from planning document classification"""
    classification_id: str = Field(..., description="Unique classification ID")
    document_id: str

    # Primary classification
    primary_classification: DrawingClassification

    # Alternative classifications
    alternative_classifications: List[DrawingClassification] = Field(
        default_factory=list,
        description="Other possible classifications with lower confidence"
    )

    # Extracted metadata
    extracted_metadata: Optional[ExtractedMetadata] = None

    # Analysis details
    classification_method: str = Field(
        ...,
        description="Method used: vision, text, or hybrid"
    )
    processing_time_seconds: float

    # Tier 1 services used
    tier_1_services_used: List[str] = Field(default_factory=list)

    # Quality indicators
    has_clear_title_block: bool = Field(default=False)
    has_scale_indicator: bool = Field(default=False)
    has_revision_info: bool = Field(default=False)
    image_quality_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Quality score for scanned images"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)


class BulkClassificationRequest(BaseModel):
    """Request to classify multiple planning documents"""
    document_ids: List[str] = Field(..., description="List of document IDs")
    session_id: Optional[str] = None
    project_id: Optional[str] = None

    use_vision: bool = True
    use_text: bool = True
    extract_metadata: bool = True
    min_confidence: float = 0.7

    # Batch processing options
    parallel_processing: bool = Field(
        default=True,
        description="Process documents in parallel"
    )
    max_workers: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Max parallel workers"
    )


class BulkClassificationResponse(BaseModel):
    """Response from bulk classification"""
    batch_id: str
    total_documents: int
    successful_classifications: int
    failed_classifications: int

    results: List[PlanningClassificationResponse]
    errors: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of errors with document_id and error message"
    )

    total_processing_time_seconds: float
    avg_time_per_document_seconds: float


class ClassificationSearchRequest(BaseModel):
    """Search for classified documents"""
    session_id: Optional[str] = None
    project_id: Optional[str] = None

    # Filters
    document_types: Optional[List[PlanningDocumentType]] = None
    purposes: Optional[List[PlanningDocumentPurpose]] = None
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Metadata filters
    drawing_number: Optional[str] = None
    project_name: Optional[str] = None
    discipline: Optional[str] = None

    # Pagination
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class ClassificationSearchResponse(BaseModel):
    """Search results for classified documents"""
    total_count: int
    returned_count: int
    results: List[PlanningClassificationResponse]

    # Aggregations
    type_counts: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of documents by type"
    )
    purpose_counts: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of documents by purpose"
    )

    limit: int
    offset: int
    has_more: bool


class ClassificationStats(BaseModel):
    """Statistics for classified documents"""
    total_classifications: int
    by_type: Dict[str, int]
    by_purpose: Dict[str, int]
    by_method: Dict[str, int]
    avg_confidence: float
    avg_processing_time_seconds: float


class ExportClassificationRequest(BaseModel):
    """Request to export classifications"""
    classification_ids: Optional[List[str]] = Field(
        None,
        description="Specific classification IDs (if None, export all for session/project)"
    )
    session_id: Optional[str] = None
    project_id: Optional[str] = None

    format: str = Field(
        default="json",
        description="Export format: json, csv, excel"
    )
    include_metadata: bool = Field(
        default=True,
        description="Include extracted metadata in export"
    )
