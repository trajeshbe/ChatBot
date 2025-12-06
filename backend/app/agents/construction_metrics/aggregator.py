"""
Multi-Document Aggregation for Construction Metrics

Combines metric extractions from multiple documents using confidence-weighted
averaging and source prioritization.

Priority Order:
1. Architectural Drawings (highest confidence)
2. DA Approvals
3. Specifications
4. Site Photos (lowest confidence, visual estimation only)
"""

import logging
from typing import List, Dict, Any, Optional
from statistics import mean, median

logger = logging.getLogger(__name__)


# ============================================================================
# Document Type Weights for Aggregation
# ============================================================================

DOCUMENT_TYPE_WEIGHTS = {
    'architectural_drawing': 1.0,  # Highest priority
    'da_approval': 0.9,
    'specification': 0.7,
    'site_photo': 0.4,
    'unknown': 0.3
}

# Calculation Method Weights (PHASE 1 Enhancement)
CALCULATION_METHOD_WEIGHTS = {
    'explicit': 1.2,                  # Boost explicit values
    'calculated_per_floor': 0.9,      # Calculated values (slightly lower)
    'estimated': 0.6,                 # Estimated values (lower confidence)
    'unknown': 0.5                    # Unknown method (fallback)
}

CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence to include a metric


# ============================================================================
# Aggregation Strategies
# ============================================================================

def aggregate_metric_values(
    values: List[tuple],  # [(value, confidence, document_type, index, calculation_method), ...]
    metric_name: str
) -> tuple:
    """
    Aggregate a single metric from multiple sources using confidence weighting.

    PHASE 1 ENHANCEMENT: Now handles calculation_method for intelligent weighting.

    Args:
        values: List of (value, confidence, document_type, index, calculation_method) tuples
        metric_name: Name of metric being aggregated

    Returns:
        (aggregated_value, final_confidence, sources_used)
    """
    if not values:
        return None, 0.0, []

    # Filter out None values
    # PHASE 1: Handle both old format (3 items) and new format (5 items)
    valid_values = []
    for i, item in enumerate(values):
        if len(item) >= 5:
            v, c, dt, idx, calc_method = item[:5]
        elif len(item) == 3:
            v, c, dt = item
            idx = i
            calc_method = 'unknown'
        else:
            continue

        if v is not None:
            valid_values.append((v, c, dt, idx, calc_method))

    if not valid_values:
        return None, 0.0, []

    # For discrete metrics (levels), use most common value weighted by confidence
    if metric_name in ['levels_above_ground', 'levels_below_ground']:
        return _aggregate_discrete_metric(valid_values)

    # For continuous metrics (areas, heights), use confidence-weighted average
    else:
        return _aggregate_continuous_metric(valid_values)


def _aggregate_discrete_metric(values: List[tuple]) -> tuple:
    """
    Aggregate discrete metrics (levels) using weighted voting.

    PHASE 1 ENHANCEMENT: Now includes calculation_method weighting to prefer explicit values.

    Args:
        values: List of (value, confidence, document_type, index, calculation_method) tuples

    Returns:
        (most_common_value, confidence, sources)
    """
    # Calculate weighted vote for each unique value
    value_scores = {}
    value_sources = {}

    for item in values:
        # Handle both old format (4 items) and new format (5 items with calculation_method)
        if len(item) == 5:
            value, confidence, doc_type, idx, calc_method = item
        else:
            value, confidence, doc_type, idx = item
            calc_method = 'unknown'

        # Apply triple weighting: confidence × document_type × calculation_method
        doc_weight = DOCUMENT_TYPE_WEIGHTS.get(doc_type, 0.5)
        calc_weight = CALCULATION_METHOD_WEIGHTS.get(calc_method, 0.5)
        weighted_score = confidence * doc_weight * calc_weight

        if value not in value_scores:
            value_scores[value] = 0.0
            value_sources[value] = []

        value_scores[value] += weighted_score
        value_sources[value].append(idx)

    # Return value with highest weighted score
    if value_scores:
        best_value = max(value_scores, key=value_scores.get)
        final_confidence = min(value_scores[best_value], 1.0)
        sources = value_sources[best_value]
        return best_value, final_confidence, sources
    else:
        return None, 0.0, []


def _aggregate_continuous_metric(values: List[tuple]) -> tuple:
    """
    Aggregate continuous metrics (areas, heights) using confidence-weighted average.

    PHASE 1 ENHANCEMENT: Now includes calculation_method weighting to prefer explicit values.

    Args:
        values: List of (value, confidence, document_type, index, calculation_method) tuples

    Returns:
        (weighted_average, confidence, sources)
    """
    total_weight = 0.0
    weighted_sum = 0.0
    sources = []

    for item in values:
        # Handle both old format (4 items) and new format (5 items with calculation_method)
        if len(item) == 5:
            value, confidence, doc_type, idx, calc_method = item
        else:
            value, confidence, doc_type, idx = item
            calc_method = 'unknown'

        # Apply triple weighting: confidence × document_type × calculation_method
        doc_weight = DOCUMENT_TYPE_WEIGHTS.get(doc_type, 0.5)
        calc_weight = CALCULATION_METHOD_WEIGHTS.get(calc_method, 0.5)
        weight = confidence * doc_weight * calc_weight

        weighted_sum += value * weight
        total_weight += weight
        sources.append(idx)

    if total_weight > 0:
        aggregated_value = weighted_sum / total_weight
        # Confidence is the normalized total weight
        final_confidence = min(total_weight / len(values), 1.0)
        return round(aggregated_value, 2), final_confidence, sources
    else:
        return None, 0.0, []


# ============================================================================
# Main Aggregation Function
# ============================================================================

def aggregate_metrics(
    extracted_metrics: List[Dict[str, Any]],
    confidence_threshold: float = CONFIDENCE_THRESHOLD
) -> Dict[str, Any]:
    """
    Aggregate metrics from multiple document extractions.

    Args:
        extracted_metrics: List of extraction results from extractors.py
        confidence_threshold: Minimum confidence to include a metric (default: 0.5)

    Returns:
        {
            "aggregated_metrics": {
                "levels_above_ground": int or "NA",
                "levels_below_ground": int or "NA",
                "gross_floor_area_m2": float or "NA",
                "external_area_m2": float or "NA",
                "site_area_m2": float or "NA",
                "building_height_m": float or "NA"
            },
            "confidence_score": float,
            "sources": [list of filenames used],
            "aggregation_details": {...}
        }
    """
    logger.info(f"Aggregating metrics from {len(extracted_metrics)} documents")

    # Collect values for each metric
    metric_data = {
        'levels_above_ground': [],
        'levels_below_ground': [],
        'gross_floor_area_m2': [],
        'external_area_m2': [],
        'site_area_m2': [],
        'building_height_m': []
    }

    # Track source documents
    source_documents = []

    # Extract values from each document
    for i, extraction in enumerate(extracted_metrics):
        metrics = extraction.get('metrics', {})
        confidence = extraction.get('confidence', 0.0)
        doc_type = extraction.get('document_type', 'unknown')
        filename = extraction.get('filename', 'unknown')

        # PHASE 1: Extract calculation_method
        calc_method = metrics.get('calculation_method', 'unknown')

        # Skip low-confidence extractions
        if confidence < confidence_threshold:
            logger.debug(f"Skipping {filename} (confidence {confidence:.2f} < threshold {confidence_threshold})")
            continue

        source_documents.append(filename)

        # Collect values for each metric (now with calculation_method)
        for metric_name in metric_data.keys():
            value = metrics.get(metric_name)
            if value is not None:
                # PHASE 1: Include calculation_method in tuple
                metric_data[metric_name].append((value, confidence, doc_type, i, calc_method))

    # Aggregate each metric
    aggregated_metrics = {}
    metric_confidences = {}
    metric_sources = {}

    for metric_name, values in metric_data.items():
        agg_value, agg_confidence, sources_idx = aggregate_metric_values(values, metric_name)

        if agg_value is not None and agg_confidence >= confidence_threshold:
            aggregated_metrics[metric_name] = agg_value
            metric_confidences[metric_name] = agg_confidence
            metric_sources[metric_name] = [extracted_metrics[idx]['filename'] for idx in sources_idx]
        else:
            aggregated_metrics[metric_name] = "NA"
            metric_confidences[metric_name] = 0.0
            metric_sources[metric_name] = []

    # Calculate overall confidence (average of non-NA metrics)
    valid_confidences = [c for c in metric_confidences.values() if c > 0]
    overall_confidence = mean(valid_confidences) if valid_confidences else 0.0

    # Prepare aggregation details
    aggregation_details = {
        "metrics_found": sum(1 for v in aggregated_metrics.values() if v != "NA"),
        "total_metrics": len(aggregated_metrics),
        "documents_processed": len(extracted_metrics),
        "documents_used": len(set(source_documents)),
        "metric_confidences": metric_confidences,
        "metric_sources": metric_sources,
        "aggregation_method": "confidence_weighted_averaging"
    }

    logger.info(f"Aggregation complete: {aggregation_details['metrics_found']}/{aggregation_details['total_metrics']} metrics found")
    logger.info(f"Overall confidence: {overall_confidence:.2f}")

    return {
        "aggregated_metrics": aggregated_metrics,
        "confidence_score": round(overall_confidence, 2),
        "sources": list(set(source_documents)),
        "aggregation_details": aggregation_details
    }


# ============================================================================
# PHASE 3: Hybrid Decision Logic & Cross-Validation
# ============================================================================

def aggregate_with_hybrid_decision(
    vision_llm_results: List[Dict[str, Any]],
    opencv_results: List[Dict[str, Any]],
    confidence_threshold: float = 0.5
) -> Dict[str, Any]:
    """
    PHASE 3: Aggregate metrics using hybrid decision logic.

    Decision Logic:
    1. ALWAYS prefer explicit values from Vision LLM (calculation_method='explicit')
    2. Compare Vision LLM vs OpenCV when both available
    3. Use method with higher confidence
    4. Flag discrepancies > 15% for review
    5. Cross-validate all measurements

    Args:
        vision_llm_results: Results from Vision LLM extraction (Phase 1)
        opencv_results: Results from OpenCV measurement (Phase 2)
        confidence_threshold: Minimum confidence to include a metric

    Returns:
        {
            "aggregated_metrics": {...},
            "confidence_score": float,
            "sources": [...],
            "aggregation_details": {...},
            "cross_validation_results": {...},  # NEW
            "discrepancies_flagged": [...]      # NEW
        }
    """
    logger.info("PHASE 3: Starting hybrid aggregation with cross-validation")

    # First, aggregate Vision LLM results normally (Phase 1 logic)
    vision_aggregation = aggregate_metrics(vision_llm_results, confidence_threshold)

    # Extract OpenCV measurements
    opencv_metrics = _extract_opencv_metrics(opencv_results)

    # Perform hybrid decision for each metric
    final_metrics = {}
    cross_validation = {}
    discrepancies = []

    metric_names = ['levels_above_ground', 'levels_below_ground',
                    'gross_floor_area_m2', 'external_area_m2',
                    'site_area_m2', 'building_height_m']

    for metric_name in metric_names:
        result = _hybrid_decision_for_metric(
            metric_name=metric_name,
            vision_value=vision_aggregation['aggregated_metrics'].get(metric_name),
            vision_confidence=vision_aggregation['aggregation_details']['metric_confidences'].get(metric_name, 0.0),
            vision_method=_get_vision_calculation_method(vision_llm_results, metric_name),
            opencv_value=opencv_metrics.get(metric_name),
            opencv_confidence=opencv_metrics.get(f"{metric_name}_confidence", 0.0)
        )

        final_metrics[metric_name] = result['value']
        cross_validation[metric_name] = result['cross_validation']

        if result.get('discrepancy'):
            discrepancies.append(result['discrepancy'])

    # Calculate overall confidence
    valid_confidences = [
        cv['final_confidence']
        for cv in cross_validation.values()
        if cv['final_confidence'] > 0
    ]
    overall_confidence = mean(valid_confidences) if valid_confidences else 0.0

    # Prepare sources
    sources = vision_aggregation['sources'] + [
        m['filename'] for m in opencv_results
        if m.get('measurements', {}).get('total_area_m2')
    ]
    sources = list(set(sources))  # Deduplicate

    return {
        "aggregated_metrics": final_metrics,
        "confidence_score": round(overall_confidence, 2),
        "sources": sources,
        "aggregation_details": {
            "metrics_found": sum(1 for v in final_metrics.values() if v != "NA"),
            "total_metrics": len(final_metrics),
            "documents_processed": len(vision_llm_results) + len(opencv_results),
            "aggregation_method": "hybrid_vision_opencv_cross_validation"
        },
        "cross_validation_results": cross_validation,
        "discrepancies_flagged": discrepancies
    }


def _extract_opencv_metrics(opencv_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract metrics from OpenCV measurement results.

    Args:
        opencv_results: List of OpenCV measurement results

    Returns:
        Dictionary of OpenCV-derived metrics
    """
    opencv_metrics = {}

    # Extract GFA from OpenCV measurements
    gfa_values = []
    for result in opencv_results:
        measurements = result.get('measurements', {})
        total_area = measurements.get('total_area_m2')
        confidence = measurements.get('confidence', 0.0)

        if total_area and confidence > 0.3:
            gfa_values.append((total_area, confidence))

    if gfa_values:
        # Use highest confidence OpenCV measurement
        best_gfa, best_confidence = max(gfa_values, key=lambda x: x[1])
        opencv_metrics['gross_floor_area_m2'] = best_gfa
        opencv_metrics['gross_floor_area_m2_confidence'] = best_confidence

    return opencv_metrics


def _get_vision_calculation_method(
    vision_results: List[Dict[str, Any]],
    metric_name: str
) -> str:
    """
    Get the calculation method used by Vision LLM for a metric.

    Args:
        vision_results: Vision LLM extraction results
        metric_name: Name of the metric

    Returns:
        Calculation method: 'explicit', 'calculated_per_floor', 'estimated', 'unknown'
    """
    for result in vision_results:
        metrics = result.get('metrics', {})
        if metrics.get(metric_name) is not None:
            return metrics.get('calculation_method', 'unknown')
    return 'unknown'


def _hybrid_decision_for_metric(
    metric_name: str,
    vision_value: Any,
    vision_confidence: float,
    vision_method: str,
    opencv_value: Optional[float],
    opencv_confidence: float
) -> Dict[str, Any]:
    """
    Make hybrid decision for a single metric using cross-validation.

    Decision Logic:
    1. If Vision method is 'explicit' → ALWAYS use Vision (highest trust)
    2. If only one method has value → Use that method
    3. If both methods have values → Compare and choose:
       a) If difference < 10% → Use higher confidence
       b) If difference 10-15% → Use higher confidence, log warning
       c) If difference > 15% → Flag discrepancy, use higher confidence
    4. If neither has value → Return "NA"

    Args:
        metric_name: Name of metric
        vision_value: Value from Vision LLM
        vision_confidence: Confidence from Vision LLM
        vision_method: Calculation method ('explicit', 'calculated_per_floor', etc.)
        opencv_value: Value from OpenCV
        opencv_confidence: Confidence from OpenCV

    Returns:
        {
            "value": final_value,
            "cross_validation": {...},
            "discrepancy": {...} or None
        }
    """
    # Rule 1: ALWAYS trust explicit values from Vision LLM
    if vision_method == 'explicit' and vision_value not in [None, "NA"]:
        logger.debug(f"{metric_name}: Using explicit Vision LLM value (highest trust)")
        return {
            "value": vision_value,
            "cross_validation": {
                "method_used": "vision_llm_explicit",
                "final_confidence": vision_confidence,
                "vision_llm_value": vision_value,
                "opencv_value": opencv_value,
                "agreement": None,  # No comparison needed
                "difference_pct": None
            },
            "discrepancy": None
        }

    # Rule 2: Only one method has value
    if vision_value in [None, "NA"] and opencv_value is None:
        # Neither has value
        return {
            "value": "NA",
            "cross_validation": {
                "method_used": "none",
                "final_confidence": 0.0,
                "vision_llm_value": None,
                "opencv_value": None,
                "agreement": None,
                "difference_pct": None
            },
            "discrepancy": None
        }

    if vision_value in [None, "NA"]:
        # Only OpenCV has value
        return {
            "value": opencv_value,
            "cross_validation": {
                "method_used": "opencv_only",
                "final_confidence": opencv_confidence,
                "vision_llm_value": None,
                "opencv_value": opencv_value,
                "agreement": None,
                "difference_pct": None
            },
            "discrepancy": None
        }

    if opencv_value is None:
        # Only Vision LLM has value
        return {
            "value": vision_value,
            "cross_validation": {
                "method_used": f"vision_llm_{vision_method}",
                "final_confidence": vision_confidence,
                "vision_llm_value": vision_value,
                "opencv_value": None,
                "agreement": None,
                "difference_pct": None
            },
            "discrepancy": None
        }

    # Rule 3: Both methods have values - Cross-validate
    try:
        # Calculate percentage difference
        diff_pct = abs(vision_value - opencv_value) / vision_value * 100

        # Determine agreement
        if diff_pct < 10:
            agreement = "excellent"
        elif diff_pct < 15:
            agreement = "good"
        else:
            agreement = "poor"

        # Choose method with higher confidence
        if vision_confidence >= opencv_confidence:
            chosen_value = vision_value
            method_used = f"vision_llm_{vision_method}"
            final_confidence = vision_confidence
        else:
            chosen_value = opencv_value
            method_used = "opencv_calculated"
            final_confidence = opencv_confidence

        logger.info(f"{metric_name}: Vision={vision_value:.1f} (conf={vision_confidence:.2f}), "
                   f"OpenCV={opencv_value:.1f} (conf={opencv_confidence:.2f}), "
                   f"Diff={diff_pct:.1f}%, Using {method_used}")

        # Create discrepancy if difference > 15%
        discrepancy = None
        if diff_pct > 15:
            discrepancy = {
                "metric": metric_name,
                "vision_llm_value": vision_value,
                "opencv_value": opencv_value,
                "difference_pct": round(diff_pct, 2),
                "vision_confidence": vision_confidence,
                "opencv_confidence": opencv_confidence,
                "chosen_method": method_used,
                "chosen_value": chosen_value,
                "severity": "high" if diff_pct > 25 else "medium"
            }
            logger.warning(f"⚠️  Discrepancy detected for {metric_name}: {diff_pct:.1f}% difference")

        return {
            "value": chosen_value,
            "cross_validation": {
                "method_used": method_used,
                "final_confidence": final_confidence,
                "vision_llm_value": vision_value,
                "opencv_value": opencv_value,
                "agreement": agreement,
                "difference_pct": round(diff_pct, 2)
            },
            "discrepancy": discrepancy
        }

    except (TypeError, ZeroDivisionError) as e:
        logger.error(f"Error in cross-validation for {metric_name}: {e}")
        # Fallback: use vision value
        return {
            "value": vision_value,
            "cross_validation": {
                "method_used": f"vision_llm_{vision_method}_fallback",
                "final_confidence": vision_confidence,
                "vision_llm_value": vision_value,
                "opencv_value": opencv_value,
                "agreement": "error",
                "difference_pct": None
            },
            "discrepancy": None
        }


# ============================================================================
# Enhanced Output Formatting (Phase 3)
# ============================================================================

def format_final_output(
    aggregated_result: Dict[str, Any],
    project_name: Optional[str] = None,
    processing_time: Optional[float] = None
) -> Dict[str, Any]:
    """
    Format the final JSON output for the API response.

    PHASE 3: Enhanced with cross-validation results and discrepancy flags.

    Args:
        aggregated_result: Result from aggregate_metrics() or aggregate_with_hybrid_decision()
        project_name: Project name (optional)
        processing_time: Processing time in seconds (optional)

    Returns:
        Final formatted JSON output with cross-validation details
    """
    metrics = aggregated_result['aggregated_metrics']

    output = {
        "project_name": project_name or "Unknown",
        "metrics": {
            "levels_above_ground": metrics.get('levels_above_ground', 'NA'),
            "levels_below_ground": metrics.get('levels_below_ground', 'NA'),
            "gross_floor_area_m2": metrics.get('gross_floor_area_m2', 'NA'),
            "external_area_m2": metrics.get('external_area_m2', 'NA'),
            "site_area_m2": metrics.get('site_area_m2', 'NA'),
            "building_height_m": metrics.get('building_height_m', 'NA')
        },
        "confidence": aggregated_result['confidence_score'],
        "sources": aggregated_result['sources'],
        "details": {
            "metrics_found": aggregated_result['aggregation_details']['metrics_found'],
            "total_metrics": aggregated_result['aggregation_details']['total_metrics'],
            "documents_processed": aggregated_result['aggregation_details']['documents_processed'],
            "aggregation_method": aggregated_result['aggregation_details']['aggregation_method']
        }
    }

    # PHASE 3: Add cross-validation results if available
    if 'cross_validation_results' in aggregated_result:
        output['cross_validation'] = aggregated_result['cross_validation_results']

    # PHASE 3: Add discrepancy flags if any
    if aggregated_result.get('discrepancies_flagged'):
        output['discrepancies'] = aggregated_result['discrepancies_flagged']
        output['has_discrepancies'] = True
    else:
        output['has_discrepancies'] = False

    if processing_time is not None:
        output['processing_time_seconds'] = round(processing_time, 2)

    return output
