"""
Data Validator

This module provides data validation utilities for extracted data based on
template validation rules.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


class ValidationError:
    """Represents a validation error"""

    def __init__(
        self,
        field: str,
        row_index: Optional[int],
        error_type: str,
        message: str,
        value: Any = None
    ):
        self.field = field
        self.row_index = row_index
        self.error_type = error_type
        self.message = message
        self.value = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'field': self.field,
            'row_index': self.row_index,
            'error_type': self.error_type,
            'message': self.message,
            'value': str(self.value) if self.value is not None else None
        }


class ValidationReport:
    """Validation report containing errors, warnings, and quality metrics"""

    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.field_quality: Dict[str, float] = {}
        self.overall_quality: float = 0.0
        self.completeness: float = 0.0
        self.accuracy: float = 0.0
        self.is_valid: bool = True

    def add_error(self, error: ValidationError):
        """Add a validation error"""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: ValidationError):
        """Add a validation warning"""
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'errors': [e.to_dict() for e in self.errors],
            'warnings': [w.to_dict() for w in self.warnings],
            'field_quality': self.field_quality,
            'overall_quality': self.overall_quality,
            'completeness': self.completeness,
            'accuracy': self.accuracy,
            'is_valid': self.is_valid,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }


class DataValidator:
    """
    Data validation engine

    Validates data against field definitions and validation rules.
    """

    def __init__(self, fields: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize validator

        Args:
            fields: List of field definitions with validation rules
        """
        self.fields = fields or []

    def validate(self, df: pd.DataFrame) -> ValidationReport:
        """
        Validate entire DataFrame

        Args:
            df: DataFrame to validate

        Returns:
            Validation report
        """
        report = ValidationReport()

        # Validate each field
        for field in self.fields:
            field_name = field['name']

            # Skip if field not in DataFrame
            if field_name not in df.columns:
                if field.get('required', False):
                    report.add_error(ValidationError(
                        field=field_name,
                        row_index=None,
                        error_type='missing_field',
                        message=f"Required field '{field_name}' is missing"
                    ))
                continue

            # Validate field
            field_errors = self._validate_field(df[field_name], field)
            for error in field_errors:
                if error.error_type in ['missing_required', 'invalid_type']:
                    report.add_error(error)
                else:
                    report.add_warning(error)

            # Calculate field quality
            field_quality = self._calculate_field_quality(df[field_name], field, field_errors)
            report.field_quality[field_name] = field_quality

        # Calculate overall metrics
        report.completeness = self._calculate_completeness(df)
        report.accuracy = self._calculate_accuracy(df, report.errors)

        # Overall quality is weighted average
        if report.field_quality:
            avg_field_quality = sum(report.field_quality.values()) / len(report.field_quality)
            report.overall_quality = (report.completeness * 0.4 +
                                     report.accuracy * 0.3 +
                                     avg_field_quality * 0.3)
        else:
            report.overall_quality = (report.completeness * 0.5 + report.accuracy * 0.5)

        return report

    def _validate_field(
        self,
        series: pd.Series,
        field: Dict[str, Any]
    ) -> List[ValidationError]:
        """
        Validate a single field/column

        Args:
            series: Pandas Series to validate
            field: Field definition with validation rules

        Returns:
            List of validation errors
        """
        errors = []
        field_name = field['name']
        validation_rules = field.get('validation', {})

        # Check required fields
        if field.get('required', False):
            null_indices = series[series.isna()].index.tolist()
            for idx in null_indices:
                errors.append(ValidationError(
                    field=field_name,
                    row_index=idx,
                    error_type='missing_required',
                    message=f"Required field '{field_name}' is missing at row {idx}"
                ))

        # Type validation
        expected_type = field.get('type')
        if expected_type:
            type_errors = self._validate_type(series, field_name, expected_type)
            errors.extend(type_errors)

        # String validations
        if validation_rules.get('min_length'):
            errors.extend(self._validate_min_length(series, field_name, validation_rules['min_length']))

        if validation_rules.get('max_length'):
            errors.extend(self._validate_max_length(series, field_name, validation_rules['max_length']))

        if validation_rules.get('regex'):
            errors.extend(self._validate_regex(series, field_name, validation_rules['regex']))

        # Numeric validations
        if validation_rules.get('min_value') is not None:
            errors.extend(self._validate_min_value(series, field_name, validation_rules['min_value']))

        if validation_rules.get('max_value') is not None:
            errors.extend(self._validate_max_value(series, field_name, validation_rules['max_value']))

        # Enum validation
        if validation_rules.get('enum'):
            errors.extend(self._validate_enum(series, field_name, validation_rules['enum']))

        return errors

    def _validate_type(
        self,
        series: pd.Series,
        field_name: str,
        expected_type: str
    ) -> List[ValidationError]:
        """Validate data type"""
        errors = []

        type_validators = {
            'string': lambda x: isinstance(x, str),
            'integer': lambda x: isinstance(x, (int, float)) and float(x).is_integer(),
            'number': lambda x: isinstance(x, (int, float)),
            'boolean': lambda x: isinstance(x, bool),
        }

        validator = type_validators.get(expected_type)
        if not validator:
            return errors

        for idx, value in series.items():
            if pd.notna(value) and not validator(value):
                errors.append(ValidationError(
                    field=field_name,
                    row_index=idx,
                    error_type='invalid_type',
                    message=f"Expected type '{expected_type}' but got '{type(value).__name__}'",
                    value=value
                ))

        return errors

    def _validate_min_length(
        self,
        series: pd.Series,
        field_name: str,
        min_length: int
    ) -> List[ValidationError]:
        """Validate minimum string length"""
        errors = []

        for idx, value in series.items():
            if pd.notna(value) and len(str(value)) < min_length:
                errors.append(ValidationError(
                    field=field_name,
                    row_index=idx,
                    error_type='min_length_violation',
                    message=f"Value length ({len(str(value))}) is less than minimum ({min_length})",
                    value=value
                ))

        return errors

    def _validate_max_length(
        self,
        series: pd.Series,
        field_name: str,
        max_length: int
    ) -> List[ValidationError]:
        """Validate maximum string length"""
        errors = []

        for idx, value in series.items():
            if pd.notna(value) and len(str(value)) > max_length:
                errors.append(ValidationError(
                    field=field_name,
                    row_index=idx,
                    error_type='max_length_violation',
                    message=f"Value length ({len(str(value))}) exceeds maximum ({max_length})",
                    value=value
                ))

        return errors

    def _validate_regex(
        self,
        series: pd.Series,
        field_name: str,
        pattern: str
    ) -> List[ValidationError]:
        """Validate against regex pattern"""
        errors = []

        try:
            compiled_pattern = re.compile(pattern)
        except re.error as e:
            logger.error(f"Invalid regex pattern '{pattern}': {str(e)}")
            return errors

        for idx, value in series.items():
            if pd.notna(value) and not compiled_pattern.match(str(value)):
                errors.append(ValidationError(
                    field=field_name,
                    row_index=idx,
                    error_type='regex_validation_failed',
                    message=f"Value does not match pattern '{pattern}'",
                    value=value
                ))

        return errors

    def _validate_min_value(
        self,
        series: pd.Series,
        field_name: str,
        min_value: float
    ) -> List[ValidationError]:
        """Validate minimum numeric value"""
        errors = []

        for idx, value in series.items():
            if pd.notna(value):
                try:
                    if float(value) < min_value:
                        errors.append(ValidationError(
                            field=field_name,
                            row_index=idx,
                            error_type='min_value_violation',
                            message=f"Value ({value}) is less than minimum ({min_value})",
                            value=value
                        ))
                except (ValueError, TypeError):
                    pass

        return errors

    def _validate_max_value(
        self,
        series: pd.Series,
        field_name: str,
        max_value: float
    ) -> List[ValidationError]:
        """Validate maximum numeric value"""
        errors = []

        for idx, value in series.items():
            if pd.notna(value):
                try:
                    if float(value) > max_value:
                        errors.append(ValidationError(
                            field=field_name,
                            row_index=idx,
                            error_type='max_value_violation',
                            message=f"Value ({value}) exceeds maximum ({max_value})",
                            value=value
                        ))
                except (ValueError, TypeError):
                    pass

        return errors

    def _validate_enum(
        self,
        series: pd.Series,
        field_name: str,
        allowed_values: List[Any]
    ) -> List[ValidationError]:
        """Validate enum/allowed values"""
        errors = []

        for idx, value in series.items():
            if pd.notna(value) and value not in allowed_values:
                errors.append(ValidationError(
                    field=field_name,
                    row_index=idx,
                    error_type='invalid_enum_value',
                    message=f"Value '{value}' not in allowed values: {allowed_values}",
                    value=value
                ))

        return errors

    def _calculate_field_quality(
        self,
        series: pd.Series,
        field: Dict[str, Any],
        errors: List[ValidationError]
    ) -> float:
        """Calculate quality score for a field"""
        total_values = len(series)
        if total_values == 0:
            return 0.0

        # Count non-null values
        non_null_count = series.notna().sum()

        # Count errors for this field
        error_count = len(errors)

        # Quality = (non-null values - errors) / total values
        quality = max(0, (non_null_count - error_count) / total_values * 100)

        return quality

    def _calculate_completeness(self, df: pd.DataFrame) -> float:
        """Calculate overall completeness percentage"""
        total_cells = df.size
        if total_cells == 0:
            return 0.0

        non_null_cells = df.notna().sum().sum()
        return (non_null_cells / total_cells) * 100

    def _calculate_accuracy(
        self,
        df: pd.DataFrame,
        errors: List[ValidationError]
    ) -> float:
        """Calculate accuracy percentage"""
        total_values = df.size
        if total_values == 0:
            return 0.0

        error_count = len(errors)
        return max(0, (total_values - error_count) / total_values * 100)


# Export
__all__ = ['DataValidator', 'ValidationReport', 'ValidationError']
