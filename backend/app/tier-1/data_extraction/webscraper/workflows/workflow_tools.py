"""
Workflow Tools

This module provides utility tools and helpers for the LangGraph extraction workflow.
These tools can be used by workflow nodes or as standalone utilities.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class ExtractionPlanner:
    """
    Plans extraction strategies based on URLs and template requirements
    """

    @staticmethod
    def create_plan(
        urls: List[str],
        fields: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Create an extraction plan for multiple URLs

        Args:
            urls: List of URLs to scrape
            fields: Optional field definitions from template

        Returns:
            Dictionary mapping URL to extraction plan
        """
        plan = {}

        for idx, url in enumerate(urls):
            # Analyze URL to determine best strategy
            strategy = ExtractionPlanner._determine_strategy(url)

            # Determine extractors needed based on fields
            extractors = ExtractionPlanner._determine_extractors(fields) if fields else ['content']

            plan[url] = {
                'url': url,
                'strategy': strategy,
                'extractors': extractors,
                'priority': idx
            }

        return plan

    @staticmethod
    def _determine_strategy(url: str) -> str:
        """
        Determine scraping strategy based on URL pattern

        Args:
            url: URL to analyze

        Returns:
            Strategy name (auto, trafilatura, playwright, etc.)
        """
        url_lower = url.lower()

        # JavaScript-heavy sites
        js_sites = ['youtube.com', 'twitter.com', 'facebook.com', 'instagram.com']
        if any(site in url_lower for site in js_sites):
            return 'playwright'

        # Article sites
        article_patterns = ['blog', 'article', 'news', 'medium.com']
        if any(pattern in url_lower for pattern in article_patterns):
            return 'trafilatura'

        # Default to auto strategy
        return 'auto'

    @staticmethod
    def _determine_extractors(fields: List[Dict[str, Any]]) -> List[str]:
        """
        Determine which extractors are needed based on field definitions

        Args:
            fields: Field definitions from template

        Returns:
            List of extractor names needed
        """
        extractors = set()

        for field in fields:
            source_hint = field.get('source_hint', {})
            extractor_type = source_hint.get('type', 'llm')
            extractors.add(extractor_type)

        return list(extractors)


class ProgressTracker:
    """
    Tracks and calculates workflow progress
    """

    # Define progress weights for each step
    STEP_WEIGHTS = {
        'initialized': 0,
        'parsing_template': 10,
        'planning_extraction': 20,
        'scraping_sources': 30,
        'extracting_data': 50,
        'consolidating_data': 60,
        'transforming_data': 65,
        'cleaning_data': 70,
        'deduplicating_data': 75,
        'validating_data': 80,
        'generating_output': 90,
        'delivering_results': 95,
        'completed': 100
    }

    @staticmethod
    def calculate_progress(
        current_step: str,
        urls_processed: int = 0,
        total_urls: int = 0
    ) -> float:
        """
        Calculate overall progress percentage

        Args:
            current_step: Current workflow step
            urls_processed: Number of URLs processed (for scraping step)
            total_urls: Total number of URLs

        Returns:
            Progress percentage (0-100)
        """
        base_progress = ProgressTracker.STEP_WEIGHTS.get(current_step, 0)

        # Add dynamic progress for scraping step
        if current_step == 'scraping_sources' and total_urls > 0:
            scraping_range = ProgressTracker.STEP_WEIGHTS['extracting_data'] - \
                           ProgressTracker.STEP_WEIGHTS['scraping_sources']
            scraping_progress = (urls_processed / total_urls) * scraping_range
            return base_progress + scraping_progress

        return float(base_progress)


class DataQualityCalculator:
    """
    Calculates data quality metrics
    """

    @staticmethod
    def calculate_completeness(data: Dict[str, List[Any]]) -> float:
        """
        Calculate data completeness percentage

        Args:
            data: Dictionary of field names to lists of values

        Returns:
            Completeness percentage (0-100)
        """
        if not data:
            return 0.0

        total_cells = 0
        filled_cells = 0

        for field_values in data.values():
            total_cells += len(field_values)
            filled_cells += sum(1 for v in field_values if v is not None and v != '')

        return (filled_cells / total_cells * 100) if total_cells > 0 else 0.0

    @staticmethod
    def calculate_field_quality(
        field_values: List[Any],
        field_def: Dict[str, Any]
    ) -> float:
        """
        Calculate quality score for a single field

        Args:
            field_values: List of values for the field
            field_def: Field definition with validation rules

        Returns:
            Quality score (0-100)
        """
        if not field_values:
            return 0.0

        # Count valid values
        total_values = len(field_values)
        valid_values = sum(
            1 for v in field_values
            if v is not None and v != ''
        )

        # Basic quality score based on presence
        presence_score = (valid_values / total_values) * 100

        # TODO: Add validation-based scoring
        # - Check if values meet validation rules
        # - Apply penalties for invalid values

        return presence_score

    @staticmethod
    def calculate_overall_quality(
        data: Dict[str, List[Any]],
        fields: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, float]:
        """
        Calculate overall quality metrics

        Args:
            data: Extracted data
            fields: Optional field definitions

        Returns:
            Dictionary of quality metrics
        """
        completeness = DataQualityCalculator.calculate_completeness(data)

        field_quality = {}
        if fields:
            for field in fields:
                field_name = field['name']
                if field_name in data:
                    field_quality[field_name] = DataQualityCalculator.calculate_field_quality(
                        data[field_name],
                        field
                    )

        # Overall quality is average of completeness and field qualities
        if field_quality:
            avg_field_quality = sum(field_quality.values()) / len(field_quality)
            overall_quality = (completeness + avg_field_quality) / 2
        else:
            overall_quality = completeness

        return {
            'overall_quality': overall_quality,
            'completeness': completeness,
            'field_quality': field_quality
        }


class DuplicateDetector:
    """
    Detects and handles duplicate records
    """

    @staticmethod
    def detect_duplicates(
        data: List[Dict[str, Any]],
        key_fields: Optional[List[str]] = None
    ) -> List[int]:
        """
        Detect duplicate records

        Args:
            data: List of data records
            key_fields: Optional list of fields to use for duplicate detection
                       If None, uses all fields

        Returns:
            List of indices of duplicate records
        """
        seen = set()
        duplicates = []

        for idx, record in enumerate(data):
            # Create a hash of the record
            if key_fields:
                record_data = {k: v for k, v in record.items() if k in key_fields}
            else:
                record_data = record

            record_hash = DuplicateDetector._hash_dict(record_data)

            if record_hash in seen:
                duplicates.append(idx)
            else:
                seen.add(record_hash)

        return duplicates

    @staticmethod
    def _hash_dict(data: Dict[str, Any]) -> str:
        """
        Create a hash of a dictionary for duplicate detection

        Args:
            data: Dictionary to hash

        Returns:
            Hash string
        """
        # Sort keys for consistent hashing
        sorted_items = sorted(data.items())
        data_str = str(sorted_items)
        return hashlib.md5(data_str.encode()).hexdigest()


class ErrorCollector:
    """
    Collects and categorizes errors during workflow execution
    """

    @staticmethod
    def add_error(
        errors_list: List[Dict[str, Any]],
        step: str,
        error: str,
        severity: str = 'error',
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add an error to the errors list

        Args:
            errors_list: List to append error to
            step: Workflow step where error occurred
            error: Error message
            severity: Error severity (error, warning, info)
            metadata: Optional additional metadata
        """
        error_entry = {
            'step': step,
            'error': error,
            'severity': severity,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }
        errors_list.append(error_entry)

    @staticmethod
    def categorize_errors(
        errors_list: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize errors by step

        Args:
            errors_list: List of errors

        Returns:
            Dictionary mapping step name to list of errors
        """
        categorized = {}

        for error in errors_list:
            step = error.get('step', 'unknown')
            if step not in categorized:
                categorized[step] = []
            categorized[step].append(error)

        return categorized


class MetricsCollector:
    """
    Collects performance and operational metrics
    """

    @staticmethod
    def start_timer() -> datetime:
        """Start a timer"""
        return datetime.utcnow()

    @staticmethod
    def end_timer(start_time: datetime) -> float:
        """
        End a timer and return duration in seconds

        Args:
            start_time: Timer start time

        Returns:
            Duration in seconds
        """
        return (datetime.utcnow() - start_time).total_seconds()

    @staticmethod
    def record_metric(
        metrics_dict: Dict[str, Any],
        metric_name: str,
        value: Any
    ) -> None:
        """
        Record a metric

        Args:
            metrics_dict: Dictionary to store metrics in
            metric_name: Name of the metric
            value: Metric value
        """
        metrics_dict[metric_name] = value

    @staticmethod
    def calculate_throughput(
        items_processed: int,
        duration_seconds: float
    ) -> float:
        """
        Calculate throughput (items per second)

        Args:
            items_processed: Number of items processed
            duration_seconds: Time taken in seconds

        Returns:
            Items per second
        """
        if duration_seconds == 0:
            return 0.0
        return items_processed / duration_seconds


# Export all tools
__all__ = [
    'ExtractionPlanner',
    'ProgressTracker',
    'DataQualityCalculator',
    'DuplicateDetector',
    'ErrorCollector',
    'MetricsCollector'
]
