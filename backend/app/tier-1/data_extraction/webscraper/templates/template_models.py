"""
Template Models - Pydantic schemas for data extraction templates

This module defines the Pydantic models for:
- Field definitions with extraction hints
- Validation rules
- Transformation rules
- Template schemas
- Extraction jobs and results
"""

from typing import List, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import UUID
import re


# ============================================================================
# Field Definition Models
# ============================================================================

class SourceHint(BaseModel):
    """Hint for how to extract a field from scraped content"""
    type: Literal["css", "xpath", "regex", "llm", "jsonpath", "structured"]

    # CSS selector
    selector: Optional[str] = None
    attribute: Optional[str] = None  # For extracting attributes instead of text

    # XPath
    xpath: Optional[str] = None

    # Regex
    pattern: Optional[str] = None
    group: Optional[int] = 1  # Regex capture group

    # LLM extraction
    prompt: Optional[str] = None

    # JSONPath (for structured data)
    path: Optional[str] = None

    # Multiple selectors as fallback chain
    fallback_selectors: Optional[List[str]] = None


class ValidationRule(BaseModel):
    """Validation rules for a field"""
    # String validation
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    regex: Optional[str] = None
    enum: Optional[List[Any]] = None

    # Numeric validation
    min_value: Optional[float] = None
    max_value: Optional[float] = None

    # Date validation
    date_format: Optional[str] = None
    min_date: Optional[str] = None
    max_date: Optional[str] = None

    # Custom validation
    custom_validator: Optional[str] = None  # Name of custom validator function


class TransformationRule(BaseModel):
    """Transformation rules for a field"""
    type: Literal[
        "to_lowercase", "to_uppercase", "title_case",
        "extract_number", "extract_email", "extract_phone",
        "remove_html", "normalize_whitespace", "trim",
        "replace", "split", "join", "custom"
    ]

    # For replace transformation
    find: Optional[str] = None
    replace_with: Optional[str] = None

    # For split transformation
    separator: Optional[str] = None

    # For join transformation
    join_with: Optional[str] = None

    # For custom transformation
    custom_function: Optional[str] = None


class FieldDefinition(BaseModel):
    """Definition of a single field to extract"""
    name: str = Field(..., description="Field name (must be valid identifier)")
    display_name: Optional[str] = None
    description: Optional[str] = None

    type: Literal["string", "integer", "float", "boolean", "date", "datetime", "array", "object"]
    required: bool = False
    default_value: Optional[Any] = None

    # Extraction configuration
    source_hint: Optional[SourceHint] = None

    # Validation
    validation: Optional[ValidationRule] = None

    # Transformation
    transformation: Optional[Union[str, TransformationRule]] = None
    multiple_transformations: Optional[List[TransformationRule]] = None

    # For array and object types
    item_type: Optional[str] = None
    item_schema: Optional[Dict[str, Any]] = None

    @validator('name')
    def validate_field_name(cls, v):
        """Validate that field name is a valid identifier"""
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', v):
            raise ValueError(f"Invalid field name: {v}. Must be a valid identifier")
        return v


# ============================================================================
# Template Models
# ============================================================================

class TemplateSchema(BaseModel):
    """Template schema definition"""
    version: str = "1.0"
    type: str  # e.g., "company_data", "product_info", "article_content"
    metadata: Optional[Dict[str, Any]] = None


class ExtractionTemplate(BaseModel):
    """Complete extraction template"""
    id: Optional[UUID] = None
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    template_type: Literal["excel", "csv", "json", "yaml"]
    template_file_path: Optional[str] = None

    # Schema and fields
    schema_definition: TemplateSchema
    fields: List[FieldDefinition]

    # Rules
    validation_rules: Optional[Dict[str, Any]] = None
    transformation_rules: Optional[Dict[str, Any]] = None

    # Metadata
    version: int = 1
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TemplateCreate(BaseModel):
    """Create new template"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    template_type: Literal["excel", "csv", "json", "yaml"]
    schema_definition: TemplateSchema
    fields: List[FieldDefinition]
    validation_rules: Optional[Dict[str, Any]] = None
    transformation_rules: Optional[Dict[str, Any]] = None


class TemplateUpdate(BaseModel):
    """Update existing template"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    fields: Optional[List[FieldDefinition]] = None
    is_active: Optional[bool] = None


# ============================================================================
# Extraction Job Models
# ============================================================================

class ScraperConfig(BaseModel):
    """Configuration for scraper"""
    compliance_level: Literal["strict", "balanced", "aggressive"] = "balanced"
    llm_provider: Optional[Literal["ollama", "openai", "anthropic"]] = "ollama"
    max_pages: int = 100
    timeout: int = 30
    retries: int = 3


class DeliveryConfig(BaseModel):
    """Configuration for result delivery"""
    # Email delivery
    email_to: Optional[List[str]] = None
    email_subject: Optional[str] = None

    # Webhook delivery
    webhook_url: Optional[str] = None
    webhook_headers: Optional[Dict[str, str]] = None

    # Storage delivery (S3, GCS, Azure)
    storage_provider: Optional[Literal["s3", "gcs", "azure", "minio"]] = None
    storage_bucket: Optional[str] = None
    storage_path: Optional[str] = None
    storage_credentials: Optional[Dict[str, str]] = None


class ExtractionJobCreate(BaseModel):
    """Create new extraction job"""
    job_name: str = Field(..., min_length=1, max_length=255)
    template_id: UUID
    urls: List[str] = Field(..., min_items=1, max_items=1000)
    scraper_config: Optional[ScraperConfig] = None
    output_format: Literal["excel", "csv", "json", "xml", "parquet"] = "excel"
    delivery_method: Literal["download", "email", "webhook", "storage"] = "download"
    delivery_config: Optional[DeliveryConfig] = None


class ExtractionJob(BaseModel):
    """Extraction job with status"""
    id: UUID
    job_name: str
    template_id: UUID

    urls: List[str]
    scraper_config: Optional[Dict[str, Any]] = None

    # Status
    status: Literal["pending", "processing", "completed", "failed"]
    progress_percentage: int = 0
    urls_total: int
    urls_processed: int = 0
    records_extracted: int = 0

    # Quality
    quality_score: Optional[float] = None
    validation_errors: Optional[Dict[str, Any]] = None

    # Output
    output_format: str
    output_file_path: Optional[str] = None
    delivery_method: str
    delivery_config: Optional[Dict[str, Any]] = None
    delivery_status: Optional[str] = None

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[float] = None
    error_message: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExtractionJobUpdate(BaseModel):
    """Update extraction job"""
    status: Optional[Literal["pending", "processing", "completed", "failed"]] = None
    progress_percentage: Optional[int] = None
    urls_processed: Optional[int] = None
    records_extracted: Optional[int] = None
    quality_score: Optional[float] = None
    validation_errors: Optional[Dict[str, Any]] = None
    output_file_path: Optional[str] = None
    delivery_status: Optional[str] = None
    error_message: Optional[str] = None


# ============================================================================
# Extraction Result Models
# ============================================================================

class ExtractionResult(BaseModel):
    """Result of extracting data from a single URL"""
    id: Optional[UUID] = None
    job_id: UUID
    source_url: str
    source_index: int

    extracted_data: Dict[str, Any]
    raw_content: Optional[str] = None

    extraction_confidence: Optional[float] = None
    validation_errors: Optional[Dict[str, Any]] = None

    scraped_at: datetime
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExtractionResultCreate(BaseModel):
    """Create extraction result"""
    job_id: UUID
    source_url: str
    source_index: int
    extracted_data: Dict[str, Any]
    raw_content: Optional[str] = None
    extraction_confidence: Optional[float] = None
    validation_errors: Optional[Dict[str, Any]] = None


# ============================================================================
# Schedule Models
# ============================================================================

class ExtractionScheduleCreate(BaseModel):
    """Create new extraction schedule"""
    job_name: str = Field(..., min_length=1, max_length=255)
    template_id: UUID
    schedule_type: Literal["one_time", "recurring", "event_triggered"]
    cron_expression: Optional[str] = None

    urls: List[str] = Field(..., min_items=1)
    scraper_config: Optional[ScraperConfig] = None
    output_format: Literal["excel", "csv", "json", "xml", "parquet"] = "excel"
    delivery_method: Literal["download", "email", "webhook", "storage"] = "download"
    delivery_config: Optional[DeliveryConfig] = None


class ExtractionSchedule(BaseModel):
    """Extraction job schedule"""
    id: UUID
    job_name: str
    template_id: UUID

    schedule_type: str
    cron_expression: Optional[str] = None
    next_run_at: Optional[datetime] = None

    urls: List[str]
    scraper_config: Optional[Dict[str, Any]] = None

    output_format: str
    delivery_method: str
    delivery_config: Optional[Dict[str, Any]] = None

    is_active: bool
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    last_job_id: Optional[UUID] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Response Models
# ============================================================================

class TemplateListResponse(BaseModel):
    """List of templates"""
    templates: List[ExtractionTemplate]
    total: int


class ExtractionJobListResponse(BaseModel):
    """List of extraction jobs"""
    jobs: List[ExtractionJob]
    total: int


class ExtractionResultListResponse(BaseModel):
    """List of extraction results"""
    results: List[ExtractionResult]
    total: int


class ValidationReport(BaseModel):
    """Validation report for extracted data"""
    is_valid: bool
    errors: List[Dict[str, Any]]
    quality_score: float
    completeness: float
    accuracy: float
    field_errors: Dict[str, List[str]]


class ExtractionMetrics(BaseModel):
    """Metrics for an extraction job"""
    total_urls: int
    urls_processed: int
    urls_failed: int
    records_extracted: int
    average_confidence: float
    quality_score: float
    execution_time_ms: float
