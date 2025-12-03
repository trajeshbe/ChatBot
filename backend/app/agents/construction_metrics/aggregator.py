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

CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence to include a metric


# ============================================================================
# Aggregation Strategies
# ============================================================================

def aggregate_metric_values(
    values: List[tuple],  # [(value, confidence, document_type), ...]
    metric_name: str
) -> tuple:
    """
    Aggregate a single metric from multiple sources using confidence weighting.

    Args:
        values: List of (value, confidence, document_type) tuples
        metric_name: Name of metric being aggregated

    Returns:
        (aggregated_value, final_confidence, sources_used)
    """
    if not values:
        return None, 0.0, []

    # Filter out None values
    valid_values = [(v, c, dt, i) for i, (v, c, dt) in enumerate(values) if v is not None]

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

    Args:
        values: List of (value, confidence, document_type, index) tuples

    Returns:
        (most_common_value, confidence, sources)
    """
    # Calculate weighted vote for each unique value
    value_scores = {}
    value_sources = {}

    for value, confidence, doc_type, idx in values:
        doc_weight = DOCUMENT_TYPE_WEIGHTS.get(doc_type, 0.5)
        weighted_score = confidence * doc_weight

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

    Args:
        values: List of (value, confidence, document_type, index) tuples

    Returns:
        (weighted_average, confidence, sources)
    """
    total_weight = 0.0
    weighted_sum = 0.0
    sources = []

    for value, confidence, doc_type, idx in values:
        # Apply both confidence and document type weighting
        doc_weight = DOCUMENT_TYPE_WEIGHTS.get(doc_type, 0.5)
        weight = confidence * doc_weight

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

        # Skip low-confidence extractions
        if confidence < confidence_threshold:
            logger.debug(f"Skipping {filename} (confidence {confidence:.2f} < threshold {confidence_threshold})")
            continue

        source_documents.append(filename)

        # Collect values for each metric
        for metric_name in metric_data.keys():
            value = metrics.get(metric_name)
            if value is not None:
                metric_data[metric_name].append((value, confidence, doc_type, i))

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


def format_final_output(
    aggregated_result: Dict[str, Any],
    project_name: Optional[str] = None,
    processing_time: Optional[float] = None
) -> Dict[str, Any]:
    """
    Format the final JSON output for the API response.

    Args:
        aggregated_result: Result from aggregate_metrics()
        project_name: Project name (optional)
        processing_time: Processing time in seconds (optional)

    Returns:
        Final formatted JSON output
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

    if processing_time is not None:
        output['processing_time_seconds'] = round(processing_time, 2)

    return output
