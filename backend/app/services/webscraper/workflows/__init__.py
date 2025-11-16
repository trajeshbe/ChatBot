"""
Workflows Package

This package contains LangGraph-based data extraction workflows that orchestrate
the entire scraping, extraction, processing, and delivery pipeline.
"""

from .workflow_state import (
    WorkflowState,
    ScrapedContent,
    FieldDefinition,
    ExtractionPlan,
    ValidationReport,
    DeliveryResult,
    create_initial_state
)

from .workflow_nodes import ExtractionWorkflowNodes

from .workflow_tools import (
    ExtractionPlanner,
    ProgressTracker,
    DataQualityCalculator,
    DuplicateDetector,
    ErrorCollector,
    MetricsCollector
)

from .extraction_workflow import (
    ExtractionWorkflow,
    extract_data_from_urls
)

__all__ = [
    # State
    'WorkflowState',
    'ScrapedContent',
    'FieldDefinition',
    'ExtractionPlan',
    'ValidationReport',
    'DeliveryResult',
    'create_initial_state',

    # Nodes
    'ExtractionWorkflowNodes',

    # Tools
    'ExtractionPlanner',
    'ProgressTracker',
    'DataQualityCalculator',
    'DuplicateDetector',
    'ErrorCollector',
    'MetricsCollector',

    # Workflow
    'ExtractionWorkflow',
    'extract_data_from_urls'
]
