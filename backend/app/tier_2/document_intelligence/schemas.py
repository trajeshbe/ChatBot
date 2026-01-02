"""
Pydantic schemas for Document Intelligence Extraction (18 fields)

Based on Merit AI docu-extract skill
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ProjectStatus(str, Enum):
    """Project status enumeration"""
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    UNKNOWN = "unknown"


class DocumentExtractionRequest(BaseModel):
    """Request for document extraction"""
    document_id: str = Field(..., description="Document ID from tier_1 documents table")
    session_id: Optional[str] = Field(None, description="Optional session ID for tracking")
    project_id: Optional[str] = Field(None, description="Optional project ID")
    extract_mode: str = Field("auto", description="Extraction mode: auto, text, vision, hybrid")
    model_id: Optional[str] = Field(None, description="Optional LLM model to use (default: gpt-4o)")
    

class ProjectMetadata(BaseModel):
    """Project metadata fields (11 fields)"""
    project_name: Optional[str] = Field(None, description="Name of the development project")
    address: Optional[str] = Field(None, description="Complete street address including city")
    project_status: Optional[ProjectStatus] = Field(None, description="Current project status")
    storeys: Optional[int] = Field(None, description="Number of building floors/storeys")
    gross_floor_area: Optional[float] = Field(None, description="Total GFA in square meters or square feet")
    site_area: Optional[float] = Field(None, description="Total site area in square meters or square feet")
    zoning: Optional[str] = Field(None, description="Zoning classification (e.g., R-4, C-2, M-1)")
    heritage_designation: Optional[str] = Field(None, description="Heritage or conservation status")
    architect: Optional[str] = Field(None, description="Architect firm name")
    developer: Optional[str] = Field(None, description="Developer company name")
    planning_consultant: Optional[str] = Field(None, description="Planning consultant name")


class BuildingInformation(BaseModel):
    """Building information fields (7 fields)"""
    residential_units: Optional[int] = Field(None, description="Total number of residential units")
    unit_types: Optional[List[str]] = Field(None, description="Unit types (e.g., 1BR, 2BR, 3BR, penthouse)")
    commercial_uses: Optional[List[str]] = Field(None, description="Commercial uses (retail, office, restaurant, etc.)")
    amenities: Optional[List[str]] = Field(None, description="Building amenities (gym, pool, rooftop, etc.)")
    parking_levels: Optional[int] = Field(None, description="Number of parking levels (underground or above)")
    parking_spaces: Optional[int] = Field(None, description="Total parking spaces")
    public_realm_features: Optional[List[str]] = Field(None, description="Public realm features (plaza, park, pathway, etc.)")


class DocumentExtractionResult(BaseModel):
    """Complete 18-field extraction result"""
    # Project metadata (11 fields)
    project_name: Optional[str] = None
    address: Optional[str] = None
    project_status: Optional[ProjectStatus] = None
    storeys: Optional[int] = None
    gross_floor_area: Optional[float] = None
    site_area: Optional[float] = None
    zoning: Optional[str] = None
    heritage_designation: Optional[str] = None
    architect: Optional[str] = None
    developer: Optional[str] = None
    planning_consultant: Optional[str] = None
    
    # Building information (7 fields)
    residential_units: Optional[int] = None
    unit_types: Optional[List[str]] = None
    commercial_uses: Optional[List[str]] = None
    amenities: Optional[List[str]] = None
    parking_levels: Optional[int] = None
    parking_spaces: Optional[int] = None
    public_realm_features: Optional[List[str]] = None
    
    # Metadata
    extraction_confidence: Optional[float] = Field(None, description="Overall extraction confidence (0-1)")
    fields_extracted: int = Field(0, description="Number of fields successfully extracted")
    total_fields: int = Field(18, description="Total possible fields")
    extraction_method: Optional[str] = Field(None, description="Method used: text, vision, hybrid")
    model_used: Optional[str] = Field(None, description="LLM model used for extraction")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")


class DocumentExtractionResponse(BaseModel):
    """API response for document extraction"""
    success: bool
    document_id: str
    session_id: Optional[str] = None
    data: Optional[DocumentExtractionResult] = None
    error: Optional[str] = None
    extracted_at: Optional[str] = None


class ExportRequest(BaseModel):
    """Request for exporting extraction results"""
    document_id: str
    format: str = Field("json", description="Export format: json, csv, excel")
    session_id: Optional[str] = None
