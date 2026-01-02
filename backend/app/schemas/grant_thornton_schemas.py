"""
Grant Thornton Pydantic Schemas

Data models for financial extraction, calculation, and output.

Author: Claude Code
Date: 2026-01-01
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


# ============================================================================
# Extraction Schemas
# ============================================================================

class ValueSchema(BaseModel):
    """
    Schema for extracted financial datapoint value.

    Used as LLM output format for agentic extraction.
    """
    value: float = Field(default=0.0, description="Extracted numerical value")
    page_no: int = Field(default=0, description="Page number where value was found")
    reference_notes: str = Field(
        default="Not Applicable",
        description="Context or reference note about the extraction"
    )


class ExtractedDatapoint(BaseModel):
    """
    Complete extracted financial datapoint with metadata.
    """
    field_name: str = Field(..., description="Original field name from Excel")
    cleaned_field_name: str = Field(..., description="Python-safe variable name")
    definition: str = Field(..., description="Field definition from Excel")
    typical_location: Optional[str] = Field(None, description="Where to find in report")

    # Extracted values
    value: float = Field(default=0.0, description="Extracted value")
    page_no: int = Field(default=0, description="Page number")
    reference_notes: str = Field(default="Not Applicable", description="Reference context")

    # Status
    extraction_status: str = Field(
        default="pending",
        description="Status: pending, success, failed, defaulted"
    )
    retry_count: int = Field(default=0, description="Number of extraction attempts")


# ============================================================================
# Sub-Calculation Schemas
# ============================================================================

class SubCalculationFormula(BaseModel):
    """
    Schema for sub-calculation formula definition.
    """
    sub_field_name: str = Field(..., description="Name of calculated field")
    formula: str = Field(..., description="Original formula from Excel")
    cleaned_formula: str = Field(..., description="Python-safe formula")
    cleaned_sub_field: str = Field(..., description="Python-safe variable name")

    # Calculation result
    calculated_value: Optional[float] = Field(None, description="Result of calculation")
    calculation_status: str = Field(
        default="pending",
        description="Status: pending, success, failed"
    )
    error_message: Optional[str] = Field(None, description="Error if calculation failed")


# ============================================================================
# Ratio Calculation Schemas
# ============================================================================

class RatioFormula(BaseModel):
    """
    Schema for financial ratio formula.
    """
    ratio_name: str = Field(..., description="Name of ratio")
    category: str = Field(..., description="Category: liquidity, leverage, profitability, efficiency")
    formula: str = Field(..., description="Original formula")
    cleaned_formula: str = Field(..., description="Python-safe formula")

    # Result
    value: Optional[float] = Field(None, description="Calculated ratio value")
    calculation_status: str = Field(default="pending", description="Status")
    error_message: Optional[str] = Field(None, description="Error if failed")


class FinancialRatios(BaseModel):
    """
    Complete set of calculated financial ratios organized by category.
    """

    # Liquidity Ratios
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    cash_ratio: Optional[float] = None
    working_capital_ratio: Optional[float] = None

    # Leverage Ratios
    debt_to_equity: Optional[float] = None
    debt_to_assets: Optional[float] = None
    interest_coverage: Optional[float] = None
    equity_ratio: Optional[float] = None

    # Profitability Ratios
    return_on_assets: Optional[float] = None
    return_on_equity: Optional[float] = None
    net_profit_margin: Optional[float] = None
    gross_profit_margin: Optional[float] = None
    operating_profit_margin: Optional[float] = None
    ebitda_margin: Optional[float] = None

    # Efficiency Ratios
    asset_turnover: Optional[float] = None
    inventory_turnover: Optional[float] = None
    receivables_turnover: Optional[float] = None
    days_sales_outstanding: Optional[float] = None
    days_inventory_outstanding: Optional[float] = None
    days_payable_outstanding: Optional[float] = None
    cash_conversion_cycle: Optional[float] = None

    # Growth Ratios
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    asset_growth: Optional[float] = None


# ============================================================================
# Request/Response Schemas
# ============================================================================

class GrantThorntonExtractionRequest(BaseModel):
    """
    Request schema for financial extraction.
    """
    pdf_path: str = Field(..., description="Path to PDF annual report")
    company_name: Optional[str] = Field(None, description="Company name for output")
    use_cache: bool = Field(default=True, description="Use cached results if available")


class GrantThorntonExtractionResponse(BaseModel):
    """
    Response schema for financial extraction.
    """
    status: str = Field(..., description="Status: processing, completed, failed")
    md5_hash: str = Field(..., description="Document MD5 hash for caching")
    company_name: Optional[str] = None

    # Progress tracking
    total_datapoints: int = Field(default=0, description="Total datapoints to extract")
    datapoints_extracted: int = Field(default=0, description="Datapoints extracted so far")
    progress_percentage: float = Field(default=0.0, description="Progress percentage")

    # Extracted data
    extracted_datapoints: List[ExtractedDatapoint] = Field(
        default_factory=list,
        description="List of extracted datapoints"
    )

    # Calculated data
    sub_calculations: List[SubCalculationFormula] = Field(
        default_factory=list,
        description="List of sub-calculations"
    )
    financial_ratios: Optional[FinancialRatios] = Field(
        None,
        description="Calculated financial ratios"
    )

    # Output
    excel_output_path: Optional[str] = Field(
        None,
        description="Path to generated Excel output"
    )

    # Timing
    processing_time_seconds: Optional[float] = Field(
        None,
        description="Total processing time"
    )


class GrantThorntonStreamEvent(BaseModel):
    """
    SSE stream event for real-time progress updates.
    """
    event_type: str = Field(
        ...,
        description="Event type: progress, datapoint_extracted, calculation_complete, complete, error"
    )
    message: str = Field(..., description="Human-readable message")
    data: Optional[Dict[str, Any]] = Field(None, description="Event-specific data")
    timestamp: str = Field(..., description="ISO timestamp")


# ============================================================================
# Configuration Schemas
# ============================================================================

class GrantThorntonConfig(BaseModel):
    """
    Configuration schema for Grant Thornton module.
    """
    # Vector store config
    persist_directory: str = Field(default="vector_store", description="ChromaDB persist dir")

    # Excel artifact paths
    datapoints_excel_path: str = Field(
        default="backend/app/services/grant_thornton/artifacts/datapoints_prompt.xlsx",
        description="Path to datapoints Excel"
    )
    calculation_formula_path: str = Field(
        default="backend/app/services/grant_thornton/artifacts/calculation_formula.xlsx",
        description="Path to sub-calculation formulas"
    )
    ratio_formula_path: str = Field(
        default="backend/app/services/grant_thornton/artifacts/final_calculation_formula.xlsx",
        description="Path to ratio formulas"
    )

    # Model configurations
    embed_model_name: str = Field(
        default="BAAI/bge-large-en-v1.5",
        description="Embedding model"
    )
    reranker_model_name: str = Field(
        default="BAAI/bge-reranker-large",
        description="Reranker model"
    )
    llm_model_name: str = Field(
        default="gpt-4o-mini",
        description="LLM for extraction"
    )

    # Retrieval config
    retrieval_top_k: int = Field(default=20, description="Initial retrieval top-k")
    rerank_top_n: int = Field(default=2, description="After reranking top-n")
    initial_context_queries: List[str] = Field(
        default_factory=lambda: [
            "Standalone Statement of Profit and Loss",
            "standalone Balance sheet",
            "standalone Cash flow statement"
        ],
        description="Initial context retrieval queries"
    )

    # Processing config
    retry_count: int = Field(default=2, description="Extraction retry attempts")
    use_gpu: bool = Field(default=True, description="Use GPU for embeddings/reranking")

    # Header tags for chunking
    header_tags: Dict[str, str] = Field(
        default_factory=lambda: {
            "#": "#",
            "##": "##",
            "###": "###"
        },
        description="Markdown header tags"
    )

    # Field mappings for formula normalization
    mapping_fields: Dict[str, str] = Field(
        default_factory=dict,
        description="Field name mappings for formula conversion"
    )

    # Sub-calculation list
    sub_calculation_list: List[str] = Field(
        default_factory=lambda: [
            "average_total_equity",
            "tangible_net_worth",
            "cash_profit",
            "dso",
            "dio",
            "dpo",
            "average_receivables",
            "average_payables",
            "average_inventory",
            "debt_service",
            "total_bank_borrowings",
            "cash_conversion_cycle"
        ],
        description="List of sub-calculations to perform"
    )


# ============================================================================
# Tool Schemas
# ============================================================================

class FinancialSearchToolInput(BaseModel):
    """
    Input schema for LangGraph financial search tool.
    """
    query: str = Field(..., description="Search query for financial information")


class FinancialSearchToolOutput(BaseModel):
    """
    Output schema for financial search tool.
    """
    results: str = Field(..., description="Retrieved financial information")
    source_pages: List[int] = Field(
        default_factory=list,
        description="Page numbers of sources"
    )
