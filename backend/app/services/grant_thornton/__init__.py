"""
Grant Thornton Financial Analysis Module

Automated financial datapoint extraction and ratio calculation from annual reports.

Author: Claude Code
Date: 2026-01-01
"""

from .pdf_parser import PDFParser, parse_financial_report
from .config import load_config, load_datapoints, load_formulas
from .embedding_service import GrantThorntonEmbeddingService, get_grant_thornton_embeddings
from .vector_store import GrantThorntonVectorStore, get_vector_store
from .retrieval_service import (
    GrantThorntonRetriever,
    get_retriever,
    get_initial_context,
    search_financial_details
)
from .agent_service import GrantThorntonAgent, get_agent
from .extraction_pipeline import GrantThorntonExtractionPipeline, get_pipeline
from .calculation_engine import (
    CalculationEngine,
    get_calculation_engine,
    calculate_sub_calculations,
    calculate_financial_ratios,
    calculate_all
)
from .excel_exporter import ExcelExporter, export_to_excel

__all__ = [
    # PDF Processing
    "PDFParser",
    "parse_financial_report",

    # Configuration
    "load_config",
    "load_datapoints",
    "load_formulas",

    # Embeddings
    "GrantThorntonEmbeddingService",
    "get_grant_thornton_embeddings",

    # Vector Store
    "GrantThorntonVectorStore",
    "get_vector_store",

    # Retrieval
    "GrantThorntonRetriever",
    "get_retriever",
    "get_initial_context",
    "search_financial_details",

    # Agent & Extraction
    "GrantThorntonAgent",
    "get_agent",
    "GrantThorntonExtractionPipeline",
    "get_pipeline",

    # Calculations
    "CalculationEngine",
    "get_calculation_engine",
    "calculate_sub_calculations",
    "calculate_financial_ratios",
    "calculate_all",

    # Excel Export
    "ExcelExporter",
    "export_to_excel",
]
