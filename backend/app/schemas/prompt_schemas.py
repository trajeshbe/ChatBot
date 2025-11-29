"""
Pydantic schemas for Prompt Library and Output Templates
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# ============================================================================
# PROMPT LIBRARY SCHEMAS
# ============================================================================

class PromptBase(BaseModel):
    """Base prompt fields"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    prompt_text: str = Field(..., min_length=1)
    prompt_type: str = Field(..., max_length=100)  # entity_extraction, summarization, etc.
    category: Optional[str] = Field(None, max_length=100)
    module: Optional[str] = Field(None, max_length=100)  # chat, scraping, project_estimator, web_scraper, etc.
    tags: List[str] = Field(default_factory=list)
    expected_output_format: str = Field(default='text', max_length=50)
    output_schema: Optional[Dict[str, Any]] = None
    example_input: Optional[str] = None
    example_output: Optional[str] = None
    is_public: bool = Field(default=False)


class PromptCreate(PromptBase):
    """Schema for creating a new prompt"""
    project_id: Optional[UUID] = None


class PromptUpdate(BaseModel):
    """Schema for updating a prompt (all fields optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    prompt_text: Optional[str] = Field(None, min_length=1)
    prompt_type: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    module: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    expected_output_format: Optional[str] = Field(None, max_length=50)
    output_schema: Optional[Dict[str, Any]] = None
    example_input: Optional[str] = None
    example_output: Optional[str] = None
    is_public: Optional[bool] = None
    project_id: Optional[UUID] = None


class PromptResponse(PromptBase):
    """Schema for prompt response"""
    id: UUID
    created_by: Optional[UUID]
    project_id: Optional[UUID]
    department_id: Optional[UUID]
    is_verified: bool
    usage_count: int
    average_rating: float
    total_ratings: int
    last_used_at: Optional[datetime]
    version: int
    parent_prompt_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    # Optional creator info (if joined)
    creator_username: Optional[str] = None
    project_name: Optional[str] = None
    department_name: Optional[str] = None

    class Config:
        from_attributes = True


class PromptListResponse(BaseModel):
    """Schema for list of prompts"""
    prompts: List[PromptResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# PROMPT RATING SCHEMAS
# ============================================================================

class PromptRatingCreate(BaseModel):
    """Schema for rating a prompt"""
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None


class PromptRatingResponse(BaseModel):
    """Schema for rating response"""
    id: UUID
    prompt_id: UUID
    user_id: UUID
    rating: int
    feedback: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# PROMPT USAGE LOG SCHEMAS
# ============================================================================

class PromptUsageCreate(BaseModel):
    """Schema for logging prompt usage"""
    actual_prompt_used: str
    input_provided: Optional[str] = None
    output_generated: Optional[str] = None
    execution_time_ms: Optional[float] = None
    token_count: Optional[int] = None
    was_successful: bool = True
    error_message: Optional[str] = None
    session_id: Optional[UUID] = None


# ============================================================================
# OUTPUT TEMPLATE SCHEMAS
# ============================================================================

class OutputTemplateBase(BaseModel):
    """Base output template fields"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    template_type: str = Field(..., max_length=50)  # excel, word, ppt, markdown, json, pdf
    template_config: Dict[str, Any] = Field(...)
    template_file_path: Optional[str] = Field(None, max_length=512)
    is_public: bool = Field(default=False)


class OutputTemplateCreate(OutputTemplateBase):
    """Schema for creating a new output template"""
    project_id: Optional[UUID] = None


class OutputTemplateUpdate(BaseModel):
    """Schema for updating an output template (all fields optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    template_type: Optional[str] = Field(None, max_length=50)
    template_config: Optional[Dict[str, Any]] = None
    template_file_path: Optional[str] = Field(None, max_length=512)
    is_public: Optional[bool] = None
    project_id: Optional[UUID] = None


class OutputTemplateResponse(OutputTemplateBase):
    """Schema for output template response"""
    id: UUID
    created_by: Optional[UUID]
    project_id: Optional[UUID]
    department_id: Optional[UUID]
    usage_count: int
    last_used_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    # Optional creator info (if joined)
    creator_username: Optional[str] = None
    project_name: Optional[str] = None
    department_name: Optional[str] = None

    class Config:
        from_attributes = True


class OutputTemplateListResponse(BaseModel):
    """Schema for list of output templates"""
    templates: List[OutputTemplateResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# EXPORT SCHEMAS
# ============================================================================

class ExportRequest(BaseModel):
    """Schema for export request - supports both template_id and inline config"""
    template_id: Optional[UUID] = None  # Use existing template
    template_type: Optional[str] = None  # For inline export without template
    template_config: Optional[Dict[str, Any]] = None  # Inline template configuration
    content: str  # The content to export (chat response, extracted data, etc.)
    variables: Optional[Dict[str, Any]] = None  # Variables for template substitution
    filename: Optional[str] = None


class ExportResponse(BaseModel):
    """Schema for export response"""
    success: bool
    file_url: Optional[str] = None  # URL to download the file
    file_path: Optional[str] = None  # MinIO path
    filename: str
    file_type: str
    message: Optional[str] = None
