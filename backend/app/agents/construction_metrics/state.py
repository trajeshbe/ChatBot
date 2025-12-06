"""
State definition for Construction Metrics Extraction Agent

Defines the shared state that flows through the LangGraph workflow.
"""

from typing import TypedDict, List, Dict, Any, Optional


class DocumentClassification(TypedDict):
    """Classification result for a single document"""
    file_path: str
    filename: str
    document_type: str  # 'architectural_drawing', 'da_approval', 'site_photo', 'specification', etc.
    confidence: float
    content_type: str  # 'image_heavy', 'scanned', 'text_heavy', 'vector_graphics'


class ExtractedMetrics(TypedDict):
    """Metrics extracted from a single document"""
    file_path: str
    filename: str
    document_type: str
    metrics: Dict[str, Any]  # {levels_above: 4, levels_below: 1, gfa: 2850.5, ...}
    confidence: float
    extraction_method: str  # 'vision_llm', 'ocr', 'text_extraction'
    raw_response: str  # Original LLM response


class AggregatedMetrics(TypedDict):
    """Final aggregated metrics from multiple documents"""
    levels_above_ground: Any  # int or "NA"
    levels_below_ground: Any  # int or "NA"
    gross_floor_area_m2: Any  # float or "NA"
    external_area_m2: Any  # float or "NA"
    site_area_m2: Any  # float or "NA" (optional)
    building_height_m: Any  # float or "NA" (optional)


class ConstructionMetricsState(TypedDict):
    """
    State shared across all nodes in the Construction Metrics workflow.

    This state object flows through the entire LangGraph DAG, with each
    node reading inputs and writing outputs to specific fields.
    """
    # ========== INPUT (from API/Tool call) ==========
    zip_file_path: str                          # Path to uploaded ZIP file
    project_name: Optional[str]                 # Project name (optional)
    session_id: str                             # Session ID for tracking
    model_id: Optional[str]                     # LLM model to use (default: llama3.2-vision:11b)

    # ========== INTERMEDIATE STATE ==========
    # Step 1: ZIP Extraction
    extracted_files: List[str]                  # List of extracted file paths
    extraction_errors: List[str]                # Errors during extraction

    # Step 2: Document Classification
    document_classifications: List[DocumentClassification]  # Classification results
    classification_errors: List[str]            # Errors during classification

    # Step 3: Metric Extraction (per document)
    extracted_metrics: List[ExtractedMetrics]   # Per-document extraction results
    extraction_errors_list: List[str]           # Errors during metric extraction

    # PHASE 2: OpenCV Results
    scale_bars_detected: Dict[str, float]       # {filename: scale_ratio}
    opencv_measurements: List[Dict[str, Any]]   # OpenCV calculation results
    geometric_confidence: Dict[str, float]      # Confidence per metric (OpenCV)

    # Step 4: Aggregation (Enhanced with Phase 3)
    aggregated_metrics: AggregatedMetrics       # Final aggregated metrics
    aggregation_confidence: float               # Overall confidence score
    aggregation_method: str                     # How metrics were aggregated

    # PHASE 3: Hybrid Decision & Cross-Validation
    cross_validation_results: Dict[str, Any]    # Cross-validation between Vision LLM and OpenCV
    discrepancies_flagged: List[Dict[str, Any]] # Metrics with >15% difference between methods

    # ========== OUTPUT ==========
    final_result: Dict[str, Any]                # Final JSON output
    sources: List[str]                          # Source documents used
    confidence_score: float                     # Overall confidence (0.0 - 1.0)
    errors: List[str]                           # All errors encountered
    processing_time_seconds: float              # Total processing time

    # ========== METADATA ==========
    workflow_status: str                        # 'running', 'completed', 'failed'
    current_step: str                           # Current workflow step
    started_at: str                             # ISO timestamp
    completed_at: Optional[str]                 # ISO timestamp
