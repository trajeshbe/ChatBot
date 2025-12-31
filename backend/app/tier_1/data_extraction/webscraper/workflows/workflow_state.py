"""
Workflow State Management

This module defines the state for the LangGraph data extraction workflow.
The state is passed between workflow nodes and accumulates results as the workflow progresses.
"""

from typing import List, Dict, Any, Optional, TypedDict
from datetime import datetime
from uuid import UUID
import pandas as pd


class ScrapedContent(TypedDict):
    """Single scraped content result"""
    url: str
    content: str
    title: Optional[str]
    metadata: Dict[str, Any]
    strategy_used: str
    success: bool
    error: Optional[str]
    scraped_at: datetime


class FieldDefinition(TypedDict):
    """Field definition from template"""
    name: str
    type: str
    required: bool
    source_hint: Dict[str, Any]
    validation: Optional[Dict[str, Any]]
    transformation: Optional[str]


class ExtractionPlan(TypedDict):
    """Extraction plan for a URL"""
    url: str
    strategy: str
    extractors: List[str]
    priority: int


class ValidationReport(TypedDict):
    """Validation results"""
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    quality_score: float
    completeness: float
    accuracy: float
    is_valid: bool
    field_quality: Dict[str, float]


class DeliveryResult(TypedDict):
    """Delivery result"""
    success: bool
    method: str
    destination: str
    delivered_at: Optional[datetime]
    error: Optional[str]
    metadata: Dict[str, Any]


class WorkflowState(TypedDict):
    """
    State for the data extraction workflow

    This state is passed between all workflow nodes and accumulates
    the results of each step in the extraction process.
    """
    # ========================================================================
    # Input Configuration
    # ========================================================================
    job_id: str
    template_id: Optional[str]
    urls: List[str]
    scrape_config: Optional[Dict[str, Any]]
    output_format: str  # excel, csv, json, xml, parquet
    delivery_method: str  # download, email, webhook, s3, database
    delivery_config: Dict[str, Any]
    session_id: Optional[str]

    # ========================================================================
    # Template & Schema
    # ========================================================================
    template_name: Optional[str]
    template_schema: Optional[Dict[str, Any]]
    fields: Optional[List[FieldDefinition]]
    has_template: bool

    # ========================================================================
    # Extraction Planning
    # ========================================================================
    extraction_plan: Optional[Dict[str, ExtractionPlan]]
    total_urls: int

    # ========================================================================
    # Scraped Data (raw)
    # ========================================================================
    raw_data: List[ScrapedContent]
    successful_scrapes: int
    failed_scrapes: int

    # ========================================================================
    # Extracted Data (structured)
    # ========================================================================
    extracted_data: Optional[Dict[str, Any]]  # Dict of lists by field name
    extraction_errors: List[Dict[str, Any]]

    # ========================================================================
    # Consolidated Data
    # ========================================================================
    consolidated_data: Optional[pd.DataFrame]
    records_extracted: int

    # ========================================================================
    # Data Processing
    # ========================================================================
    cleaned_data: Optional[pd.DataFrame]
    transformed_data: Optional[pd.DataFrame]
    deduplicated_data: Optional[pd.DataFrame]
    duplicates_removed: int

    # ========================================================================
    # Validation & Quality
    # ========================================================================
    validation_results: Optional[ValidationReport]
    quality_score: float
    data_quality_passed: bool

    # ========================================================================
    # Output Generation
    # ========================================================================
    output_file_path: Optional[str]
    output_file_size: Optional[int]
    output_metadata: Optional[Dict[str, Any]]

    # ========================================================================
    # Delivery
    # ========================================================================
    delivery_status: Optional[DeliveryResult]
    delivery_success: bool

    # ========================================================================
    # Workflow Progress & Status
    # ========================================================================
    current_step: str
    progress_percentage: float
    started_at: datetime
    completed_at: Optional[datetime]
    total_duration_seconds: Optional[float]

    # ========================================================================
    # Errors & Warnings
    # ========================================================================
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    workflow_status: str  # pending, running, completed, failed

    # ========================================================================
    # Performance Metrics
    # ========================================================================
    metrics: Dict[str, Any]  # Timing and performance metrics for each step


def create_initial_state(
    job_id: str,
    urls: List[str],
    template_id: Optional[str] = None,
    scrape_config: Optional[Dict[str, Any]] = None,
    output_format: str = "excel",
    delivery_method: str = "download",
    delivery_config: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None
) -> WorkflowState:
    """
    Create initial workflow state

    Args:
        job_id: Unique job identifier
        urls: List of URLs to scrape
        template_id: Optional template ID for structured extraction
        scrape_config: Optional scraping configuration
        output_format: Output format (excel, csv, json, xml, parquet)
        delivery_method: Delivery method (download, email, webhook, s3, database)
        delivery_config: Delivery configuration
        session_id: Optional session ID

    Returns:
        Initial workflow state
    """
    return WorkflowState(
        # Input
        job_id=job_id,
        template_id=template_id,
        urls=urls,
        scrape_config=scrape_config or {},
        output_format=output_format,
        delivery_method=delivery_method,
        delivery_config=delivery_config or {},
        session_id=session_id,

        # Template
        template_name=None,
        template_schema=None,
        fields=None,
        has_template=template_id is not None,

        # Planning
        extraction_plan=None,
        total_urls=len(urls),

        # Scraped data
        raw_data=[],
        successful_scrapes=0,
        failed_scrapes=0,

        # Extracted data
        extracted_data=None,
        extraction_errors=[],

        # Consolidated
        consolidated_data=None,
        records_extracted=0,

        # Processing
        cleaned_data=None,
        transformed_data=None,
        deduplicated_data=None,
        duplicates_removed=0,

        # Validation
        validation_results=None,
        quality_score=0.0,
        data_quality_passed=False,

        # Output
        output_file_path=None,
        output_file_size=None,
        output_metadata=None,

        # Delivery
        delivery_status=None,
        delivery_success=False,

        # Progress
        current_step="initialized",
        progress_percentage=0.0,
        started_at=datetime.utcnow(),
        completed_at=None,
        total_duration_seconds=None,

        # Errors
        errors=[],
        warnings=[],
        workflow_status="pending",

        # Metrics
        metrics={}
    )
