"""
Construction Metrics Extraction Agent - LangGraph Workflow

Main workflow orchestration for extracting building metrics from
construction project ZIP files using Vision LLM + CLIP + OCR.

Workflow Steps:
1. Extract ZIP → Extract files to temp directory
2. Classify Documents → Classify each file (drawing, DA, photo, etc.)
3. Extract Metrics → Use Vision LLM to extract metrics from each document
4. Aggregate Results → Combine results with confidence weighting
5. Format Output → Return structured JSON

Author: Construction Metrics Agent
Date: 2025-12-03
"""

import asyncio
import logging
import os
import tempfile
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from .state import ConstructionMetricsState, DocumentClassification, ExtractedMetrics
from .extractors import (
    classify_document_type,
    batch_extract_metrics
)
from .aggregator import aggregate_metrics, format_final_output

logger = logging.getLogger(__name__)


class ConstructionMetricsAgent:
    """
    LangGraph workflow for extracting building metrics from construction documents.

    This agent orchestrates the full pipeline:
    - ZIP extraction
    - Document classification
    - Vision LLM metric extraction
    - Multi-document aggregation
    - JSON output formatting
    """

    def __init__(
        self,
        llm_service=None,
        vision_service=None,
        document_service=None,
        db: Optional[Session] = None
    ):
        """
        Initialize Construction Metrics Agent.

        Args:
            llm_service: LLM service instance (optional, will create if None)
            vision_service: Vision service instance (optional, will create if None)
            document_service: Document service instance (optional)
            db: Database session (optional)
        """
        self.llm_service = llm_service
        self.vision_service = vision_service
        self.document_service = document_service
        self.db = db
        self.graph = self._build_graph()

        logger.info("ConstructionMetricsAgent initialized")

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow DAG.

        PHASE 2: Enhanced with OpenCV scale detection and measurement nodes.

        Workflow:
        1. Initialize → 2. Extract ZIP → 3. Classify Documents
        4. Extract Metrics (Vision LLM) → 5. Scale Detection (OpenCV)
        6. OpenCV Measurement → 7. Aggregate Results → 8. Format Output

        Returns:
            Compiled StateGraph
        """
        workflow = StateGraph(ConstructionMetricsState)

        # Add nodes
        workflow.add_node("initialize", self._initialize_workflow)
        workflow.add_node("extract_zip", self._extract_zip_node)
        workflow.add_node("classify_documents", self._classify_documents_node)
        workflow.add_node("extract_metrics", self._extract_metrics_node)

        # PHASE 2: OpenCV nodes
        workflow.add_node("scale_detection", self._scale_detection_node)
        workflow.add_node("opencv_measurement", self._opencv_measurement_node)

        workflow.add_node("aggregate_results", self._aggregate_results_node)
        workflow.add_node("format_output", self._format_output_node)

        # Add edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "extract_zip")
        workflow.add_edge("extract_zip", "classify_documents")
        workflow.add_edge("classify_documents", "extract_metrics")

        # PHASE 2: Run OpenCV analysis after Vision LLM extraction
        workflow.add_edge("extract_metrics", "scale_detection")
        workflow.add_edge("scale_detection", "opencv_measurement")
        workflow.add_edge("opencv_measurement", "aggregate_results")

        workflow.add_edge("aggregate_results", "format_output")
        workflow.add_edge("format_output", END)

        return workflow.compile()

    # ========================================================================
    # Workflow Nodes
    # ========================================================================

    async def _initialize_workflow(self, state: ConstructionMetricsState) -> ConstructionMetricsState:
        """
        Initialize workflow state and metadata.

        Args:
            state: Current workflow state

        Returns:
            Updated state
        """
        logger.info(f"Initializing workflow for ZIP: {state.get('zip_file_path', 'unknown')}")

        state['workflow_status'] = 'running'
        state['current_step'] = 'initialize'
        state['started_at'] = datetime.utcnow().isoformat()
        state['errors'] = []
        state['extraction_errors'] = []
        state['classification_errors'] = []
        state['extraction_errors_list'] = []

        # Initialize services if not provided
        if self.llm_service is None:
            from app.services.llm_service import LLMService
            self.llm_service = LLMService()
            logger.info("Initialized LLM service")

        if self.vision_service is None:
            # Try to use hybrid extraction service which has vision capabilities
            try:
                from app.services.hybrid_extraction_service import HybridExtractionService
                self.vision_service = HybridExtractionService()
                logger.info("Initialized Vision service (HybridExtractionService)")
            except ImportError:
                logger.warning("HybridExtractionService not available")

        if self.document_service is None:
            from app.services.document_service import document_service
            self.document_service = document_service
            logger.info("Initialized Document service")

        return state

    async def _extract_zip_node(self, state: ConstructionMetricsState) -> ConstructionMetricsState:
        """
        Extract ZIP file to temporary directory.

        Args:
            state: Current workflow state

        Returns:
            Updated state with extracted_files list
        """
        state['current_step'] = 'extract_zip'
        logger.info(f"Extracting ZIP: {state['zip_file_path']}")

        zip_path = state['zip_file_path']
        extracted_files = []
        extraction_errors = []

        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix="construction_metrics_")
            logger.info(f"Created temp directory: {temp_dir}")

            # Extract ZIP
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                logger.info(f"Extracted ZIP to {temp_dir}")

            # Collect all extracted files (PDF, images, etc.)
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    # Skip hidden files and system files
                    if file.startswith('.') or file.startswith('__'):
                        continue

                    file_path = os.path.join(root, file)
                    file_ext = Path(file_path).suffix.lower()

                    # Include PDFs and images
                    if file_ext in ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
                        extracted_files.append(file_path)
                        logger.debug(f"Found file: {file}")

            logger.info(f"Extracted {len(extracted_files)} relevant files from ZIP")

            state['extracted_files'] = extracted_files
            state['extraction_errors'] = extraction_errors

        except Exception as e:
            error_msg = f"Failed to extract ZIP: {e}"
            logger.error(error_msg)
            extraction_errors.append(error_msg)
            state['errors'].append(error_msg)
            state['extraction_errors'] = extraction_errors
            state['extracted_files'] = []

        return state

    async def _classify_documents_node(self, state: ConstructionMetricsState) -> ConstructionMetricsState:
        """
        Classify each extracted document by type.

        Args:
            state: Current workflow state

        Returns:
            Updated state with document_classifications list
        """
        state['current_step'] = 'classify_documents'
        logger.info(f"Classifying {len(state['extracted_files'])} documents")

        classifications = []
        classification_errors = []

        for file_path in state['extracted_files']:
            try:
                filename = Path(file_path).name

                # Use multi_analyzer_ensemble if available, otherwise simple classification
                content_type = 'image_heavy'  # Default assumption

                if self.document_service and hasattr(self.document_service, 'multi_analyzer'):
                    # Use multi-analyzer for advanced classification
                    try:
                        analysis = await self.document_service.multi_analyzer.analyze_document(file_path)
                        content_type = analysis.get('consensus', 'image_heavy')
                    except Exception as e:
                        logger.warning(f"Multi-analyzer failed for {filename}: {e}")

                # Classify document type based on filename and content
                doc_type = classify_document_type(filename, content_type)

                classification = DocumentClassification(
                    file_path=file_path,
                    filename=filename,
                    document_type=doc_type,
                    confidence=0.8,  # Default confidence
                    content_type=content_type
                )

                classifications.append(classification)
                logger.debug(f"Classified {filename} as {doc_type}")

            except Exception as e:
                error_msg = f"Failed to classify {Path(file_path).name}: {e}"
                logger.error(error_msg)
                classification_errors.append(error_msg)

        logger.info(f"Classified {len(classifications)} documents")

        state['document_classifications'] = classifications
        state['classification_errors'] = classification_errors

        return state

    async def _extract_metrics_node(self, state: ConstructionMetricsState) -> ConstructionMetricsState:
        """
        Extract metrics from each classified document using Vision LLM.

        Args:
            state: Current workflow state

        Returns:
            Updated state with extracted_metrics list
        """
        state['current_step'] = 'extract_metrics'
        logger.info(f"Extracting metrics from {len(state['document_classifications'])} documents")

        # Prepare files for batch extraction
        files_with_types = [
            (doc['file_path'], doc['document_type'])
            for doc in state['document_classifications']
        ]

        model_id = state.get('model_id', 'llama3.2-vision:11b')

        try:
            # Batch extract metrics
            extracted_metrics = await batch_extract_metrics(
                files_with_types=files_with_types,
                llm_service=self.llm_service,
                vision_service=self.vision_service,
                model_id=model_id
            )

            logger.info(f"Extracted metrics from {len(extracted_metrics)} documents")

            state['extracted_metrics'] = extracted_metrics
            state['extraction_errors_list'] = []

        except Exception as e:
            error_msg = f"Batch extraction failed: {e}"
            logger.error(error_msg)
            state['errors'].append(error_msg)
            state['extraction_errors_list'] = [error_msg]
            state['extracted_metrics'] = []

        return state

    async def _scale_detection_node(self, state: ConstructionMetricsState) -> ConstructionMetricsState:
        """
        PHASE 2: Detect scale bars in architectural drawings using OpenCV.

        Args:
            state: Current workflow state

        Returns:
            Updated state with scale_bars_detected
        """
        state['current_step'] = 'scale_detection'
        logger.info("Detecting scale bars in architectural drawings")

        try:
            from app.services.opencv_measurement_service import OpenCVMeasurementService

            opencv_service = OpenCVMeasurementService()
            scale_bars = {}

            # Process only architectural drawings
            for doc in state.get('document_classifications', []):
                if doc.get('document_type') == 'architectural_drawing':
                    try:
                        scale_result = opencv_service.detect_scale_bar(doc['file_path'])
                        if scale_result:
                            scale_bars[doc['filename']] = scale_result['scale_ratio']
                            logger.info(f"✓ Scale detected for {doc['filename']}: {scale_result['scale_text']} (ratio: {scale_result['scale_ratio']})")
                        else:
                            logger.debug(f"No scale bar found in {doc['filename']}")
                    except Exception as e:
                        logger.error(f"Error detecting scale in {doc['filename']}: {e}")

            logger.info(f"Scale bars detected in {len(scale_bars)} documents")
            state['scale_bars_detected'] = scale_bars

        except ImportError as e:
            logger.warning(f"OpenCV service not available: {e}")
            state['scale_bars_detected'] = {}
        except Exception as e:
            logger.error(f"Error in scale detection node: {e}")
            state['scale_bars_detected'] = {}

        return state

    async def _opencv_measurement_node(self, state: ConstructionMetricsState) -> ConstructionMetricsState:
        """
        PHASE 2: Measure floor plan areas using OpenCV contour detection.

        Args:
            state: Current workflow state

        Returns:
            Updated state with opencv_measurements
        """
        state['current_step'] = 'opencv_measurement'
        logger.info("Measuring floor plan areas with OpenCV")

        try:
            from app.services.opencv_measurement_service import OpenCVMeasurementService

            opencv_service = OpenCVMeasurementService()
            measurements = []
            geometric_confidence = {}

            # Process architectural drawings with detected scales
            for doc in state.get('document_classifications', []):
                if doc.get('document_type') == 'architectural_drawing':
                    try:
                        scale_ratio = state.get('scale_bars_detected', {}).get(doc['filename'])

                        measurement_result = opencv_service.measure_floor_plan_area(
                            doc['file_path'],
                            scale_ratio=scale_ratio
                        )

                        measurements.append({
                            "filename": doc['filename'],
                            "measurements": measurement_result,
                            "scale_ratio": scale_ratio
                        })

                        # Track geometric confidence
                        if measurement_result.get('total_area_m2'):
                            geometric_confidence[doc['filename']] = measurement_result['confidence']
                            logger.info(f"✓ Measured {doc['filename']}: {measurement_result['total_area_m2']:.2f} m² (confidence: {measurement_result['confidence']:.2f})")

                    except Exception as e:
                        logger.error(f"Error measuring {doc['filename']}: {e}")

            logger.info(f"OpenCV measurements completed for {len(measurements)} documents")
            state['opencv_measurements'] = measurements
            state['geometric_confidence'] = geometric_confidence

        except ImportError as e:
            logger.warning(f"OpenCV service not available: {e}")
            state['opencv_measurements'] = []
            state['geometric_confidence'] = {}
        except Exception as e:
            logger.error(f"Error in OpenCV measurement node: {e}")
            state['opencv_measurements'] = []
            state['geometric_confidence'] = {}

        return state

    async def _aggregate_results_node(self, state: ConstructionMetricsState) -> ConstructionMetricsState:
        """
        PHASE 3: Aggregate metrics using hybrid decision logic with cross-validation.

        This node combines:
        - Vision LLM results (OCR + Docling + Vision - Phase 1)
        - OpenCV measurements (Scale detection + Geometry - Phase 2)

        Using intelligent decision logic:
        1. Always prefer explicit values
        2. Cross-validate when both methods available
        3. Use higher confidence method
        4. Flag discrepancies > 15%

        Args:
            state: Current workflow state

        Returns:
            Updated state with aggregated_metrics and cross_validation_results
        """
        from .aggregator import aggregate_with_hybrid_decision

        state['current_step'] = 'aggregate_results'
        logger.info(f"PHASE 3: Hybrid aggregation - Vision LLM + OpenCV cross-validation")

        try:
            # Check if we have OpenCV results (Phase 2)
            has_opencv_results = len(state.get('opencv_measurements', [])) > 0

            if has_opencv_results:
                # PHASE 3: Use hybrid aggregation with cross-validation
                logger.info("Using hybrid aggregation (Vision LLM + OpenCV)")
                aggregation_result = aggregate_with_hybrid_decision(
                    vision_llm_results=state['extracted_metrics'],
                    opencv_results=state['opencv_measurements'],
                    confidence_threshold=0.5
                )

                # Log cross-validation summary
                if aggregation_result.get('discrepancies_flagged'):
                    logger.warning(f"⚠️  {len(aggregation_result['discrepancies_flagged'])} discrepancies flagged for review")
                    for disc in aggregation_result['discrepancies_flagged']:
                        logger.warning(f"  - {disc['metric']}: {disc['difference_pct']:.1f}% difference "
                                     f"(Vision={disc['vision_llm_value']:.1f}, OpenCV={disc['opencv_value']:.1f})")

                # Store cross-validation results in state
                state['cross_validation_results'] = aggregation_result.get('cross_validation_results', {})
                state['discrepancies_flagged'] = aggregation_result.get('discrepancies_flagged', [])

            else:
                # Fallback: Use Vision LLM only (Phase 1)
                logger.info("Using Vision LLM only aggregation (no OpenCV results)")
                from .aggregator import aggregate_metrics
                aggregation_result = aggregate_metrics(
                    extracted_metrics=state['extracted_metrics'],
                    confidence_threshold=0.5
                )

                state['cross_validation_results'] = {}
                state['discrepancies_flagged'] = []

            state['aggregated_metrics'] = aggregation_result['aggregated_metrics']
            state['aggregation_confidence'] = aggregation_result['confidence_score']
            state['sources'] = aggregation_result['sources']
            state['aggregation_method'] = aggregation_result['aggregation_details']['aggregation_method']

            logger.info(f"✓ Aggregation complete: confidence {aggregation_result['confidence_score']:.2f}")
            logger.info(f"  Method: {state['aggregation_method']}")
            logger.info(f"  Metrics found: {aggregation_result['aggregation_details']['metrics_found']}/{aggregation_result['aggregation_details']['total_metrics']}")

        except Exception as e:
            error_msg = f"Aggregation failed: {e}"
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
            state['errors'].append(error_msg)
            state['aggregated_metrics'] = {
                'levels_above_ground': 'NA',
                'levels_below_ground': 'NA',
                'gross_floor_area_m2': 'NA',
                'external_area_m2': 'NA',
                'site_area_m2': 'NA',
                'building_height_m': 'NA'
            }
            state['aggregation_confidence'] = 0.0
            state['sources'] = []
            state['cross_validation_results'] = {}
            state['discrepancies_flagged'] = []

        return state

    async def _format_output_node(self, state: ConstructionMetricsState) -> ConstructionMetricsState:
        """
        Format final JSON output.

        PHASE 3: Enhanced to include cross-validation results and discrepancy flags.

        Args:
            state: Current workflow state

        Returns:
            Updated state with final_result
        """
        state['current_step'] = 'format_output'
        logger.info("Formatting final output with cross-validation details")

        # Calculate processing time
        started_at = datetime.fromisoformat(state['started_at'])
        processing_time = (datetime.utcnow() - started_at).total_seconds()

        # Prepare aggregation result with Phase 3 enhancements
        aggregation_result = {
            'aggregated_metrics': state['aggregated_metrics'],
            'confidence_score': state['aggregation_confidence'],
            'sources': state['sources'],
            'aggregation_details': {
                'metrics_found': sum(1 for v in state['aggregated_metrics'].values() if v != 'NA'),
                'total_metrics': len(state['aggregated_metrics']),
                'documents_processed': len(state.get('extracted_metrics', [])),
                'aggregation_method': state.get('aggregation_method', 'confidence_weighted')
            }
        }

        # PHASE 3: Include cross-validation results if available
        if state.get('cross_validation_results'):
            aggregation_result['cross_validation_results'] = state['cross_validation_results']

        # PHASE 3: Include discrepancy flags if any
        if state.get('discrepancies_flagged'):
            aggregation_result['discrepancies_flagged'] = state['discrepancies_flagged']

        final_output = format_final_output(
            aggregated_result=aggregation_result,
            project_name=state.get('project_name'),
            processing_time=processing_time
        )

        state['final_result'] = final_output
        state['confidence_score'] = state['aggregation_confidence']
        state['processing_time_seconds'] = processing_time
        state['completed_at'] = datetime.utcnow().isoformat()
        state['workflow_status'] = 'completed'

        logger.info(f"✓ Workflow completed in {processing_time:.2f}s")
        if final_output.get('has_discrepancies'):
            logger.warning(f"  ⚠️  {len(final_output.get('discrepancies', []))} discrepancies flagged")

        return state

    # ========================================================================
    # Public API
    # ========================================================================

    async def extract_metrics(
        self,
        zip_file_path: str,
        project_name: Optional[str] = None,
        session_id: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for extracting construction metrics from a ZIP file.

        Args:
            zip_file_path: Path to uploaded ZIP file
            project_name: Project name (optional)
            session_id: Session ID for tracking (optional)
            model_id: LLM model to use (default: llama3.2-vision:11b)

        Returns:
            Final JSON output with metrics
        """
        logger.info(f"Starting construction metrics extraction for: {zip_file_path}")

        # Initialize state
        initial_state = {
            'zip_file_path': zip_file_path,
            'project_name': project_name,
            'session_id': session_id or 'default',
            'model_id': model_id or 'llama3.2-vision:11b'
        }

        # Run workflow
        final_state = await self.graph.ainvoke(initial_state)

        # Return final result
        return final_state['final_result']
