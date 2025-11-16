"""
Template Validator - Validate extraction templates and extracted data

This module provides validation for:
- Template structure and schema
- Field definitions
- Extracted data against template rules
- Data quality scoring
"""

from typing import Dict, Any, List, Optional
import re
from datetime import datetime
import logging

from .template_models import (
    FieldDefinition,
    ValidationRule,
    ValidationReport
)

logger = logging.getLogger(__name__)


class TemplateValidator:
    """
    Validate templates and extracted data

    Features:
    - Template schema validation
    - Field-level validation rules
    - Data quality scoring
    - Comprehensive error reporting
    """

    def __init__(self):
        self.logger = logger

    def validate_template(self, template_data: Dict[str, Any]) -> ValidationReport:
        """
        Validate template structure

        Args:
            template_data: Template dictionary

        Returns:
            Validation report
        """
        errors = []

        # Check required fields
        required_fields = ['name', 'fields']
        for field in required_fields:
            if field not in template_data:
                errors.append({
                    'field': field,
                    'error': 'missing_required_field',
                    'message': f"Template missing required field: {field}"
                })

        # Validate fields list
        if 'fields' in template_data:
            if not isinstance(template_data['fields'], list):
                errors.append({
                    'field': 'fields',
                    'error': 'invalid_type',
                    'message': "'fields' must be a list"
                })
            elif len(template_data['fields']) == 0:
                errors.append({
                    'field': 'fields',
                    'error': 'empty_fields',
                    'message': "Template must have at least one field"
                })
            else:
                # Validate each field
                field_errors = self._validate_fields(template_data['fields'])
                errors.extend(field_errors)

        # Calculate quality score
        quality_score = 1.0 if len(errors) == 0 else max(0.0, 1.0 - (len(errors) * 0.1))

        return ValidationReport(
            is_valid=len(errors) == 0,
            errors=errors,
            quality_score=quality_score,
            completeness=1.0,
            accuracy=quality_score,
            field_errors={}
        )

    def _validate_fields(self, fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate field definitions"""
        errors = []

        field_names = set()
        for i, field in enumerate(fields):
            # Check if field is a dictionary
            if not isinstance(field, dict):
                errors.append({
                    'field': f'fields[{i}]',
                    'error': 'invalid_type',
                    'message': f"Field at index {i} must be a dictionary"
                })
                continue

            # Check required field attributes
            if 'name' not in field:
                errors.append({
                    'field': f'fields[{i}]',
                    'error': 'missing_name',
                    'message': f"Field at index {i} missing 'name'"
                })
                continue

            field_name = field['name']

            # Check for duplicate names
            if field_name in field_names:
                errors.append({
                    'field': field_name,
                    'error': 'duplicate_field_name',
                    'message': f"Duplicate field name: {field_name}"
                })
            field_names.add(field_name)

            # Validate field name format
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', field_name):
                errors.append({
                    'field': field_name,
                    'error': 'invalid_field_name',
                    'message': f"Invalid field name: {field_name}. Must be a valid identifier"
                })

            # Validate field type
            valid_types = ['string', 'integer', 'float', 'boolean', 'date', 'datetime', 'array', 'object']
            field_type = field.get('type', 'string')
            if field_type not in valid_types:
                errors.append({
                    'field': field_name,
                    'error': 'invalid_field_type',
                    'message': f"Invalid type '{field_type}' for field {field_name}. "
                               f"Must be one of: {', '.join(valid_types)}"
                })

        return errors

    def validate_extracted_data(
        self,
        data: Dict[str, Any],
        fields: List[Dict[str, Any]]
    ) -> ValidationReport:
        """
        Validate extracted data against template fields

        Args:
            data: Extracted data dictionary
            fields: Field definitions from template

        Returns:
            Validation report
        """
        errors = []
        field_errors = {}

        for field in fields:
            field_name = field.get('name')
            if not field_name:
                continue

            field_type = field.get('type', 'string')
            required = field.get('required', False)
            validation_rules = field.get('validation', {})

            # Check if field exists
            if field_name not in data:
                if required:
                    error = {
                        'field': field_name,
                        'error': 'missing_required_field',
                        'message': f"Required field '{field_name}' is missing"
                    }
                    errors.append(error)
                    field_errors.setdefault(field_name, []).append('missing')
                continue

            value = data[field_name]

            # Skip validation if value is None and field is not required
            if value is None:
                if required:
                    errors.append({
                        'field': field_name,
                        'error': 'null_required_field',
                        'message': f"Required field '{field_name}' is null"
                    })
                    field_errors.setdefault(field_name, []).append('null')
                continue

            # Type validation
            type_error = self._validate_type(field_name, value, field_type)
            if type_error:
                errors.append(type_error)
                field_errors.setdefault(field_name, []).append('type_mismatch')

            # Validation rules
            rule_errors = self._validate_rules(field_name, value, validation_rules)
            if rule_errors:
                errors.extend(rule_errors)
                field_errors.setdefault(field_name, []).extend(
                    [e['error'] for e in rule_errors]
                )

        # Calculate metrics
        total_fields = len(fields)
        complete_fields = sum(1 for f in fields if f.get('name') in data and data[f['name']] is not None)
        completeness = complete_fields / total_fields if total_fields > 0 else 0.0

        error_fields = len(field_errors)
        accuracy = 1.0 - (error_fields / total_fields) if total_fields > 0 else 0.0

        quality_score = (completeness * 0.5) + (accuracy * 0.5)

        return ValidationReport(
            is_valid=len(errors) == 0,
            errors=errors,
            quality_score=quality_score,
            completeness=completeness,
            accuracy=accuracy,
            field_errors=field_errors
        )

    def _validate_type(self, field_name: str, value: Any, field_type: str) -> Optional[Dict[str, Any]]:
        """Validate value type"""
        try:
            if field_type == 'string':
                if not isinstance(value, str):
                    return {
                        'field': field_name,
                        'error': 'type_mismatch',
                        'message': f"Field '{field_name}' must be a string, got {type(value).__name__}"
                    }

            elif field_type == 'integer':
                if not isinstance(value, int) or isinstance(value, bool):
                    return {
                        'field': field_name,
                        'error': 'type_mismatch',
                        'message': f"Field '{field_name}' must be an integer"
                    }

            elif field_type == 'float':
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    return {
                        'field': field_name,
                        'error': 'type_mismatch',
                        'message': f"Field '{field_name}' must be a number"
                    }

            elif field_type == 'boolean':
                if not isinstance(value, bool):
                    return {
                        'field': field_name,
                        'error': 'type_mismatch',
                        'message': f"Field '{field_name}' must be a boolean"
                    }

            elif field_type in ['date', 'datetime']:
                # Accept string or datetime object
                if not isinstance(value, (str, datetime)):
                    return {
                        'field': field_name,
                        'error': 'type_mismatch',
                        'message': f"Field '{field_name}' must be a date/datetime string or object"
                    }

            elif field_type == 'array':
                if not isinstance(value, list):
                    return {
                        'field': field_name,
                        'error': 'type_mismatch',
                        'message': f"Field '{field_name}' must be an array"
                    }

            elif field_type == 'object':
                if not isinstance(value, dict):
                    return {
                        'field': field_name,
                        'error': 'type_mismatch',
                        'message': f"Field '{field_name}' must be an object"
                    }

            return None

        except Exception as e:
            return {
                'field': field_name,
                'error': 'validation_error',
                'message': f"Type validation failed: {str(e)}"
            }

    def _validate_rules(
        self,
        field_name: str,
        value: Any,
        rules: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Validate value against validation rules"""
        errors = []

        # String validation
        if 'min_length' in rules and isinstance(value, str):
            if len(value) < rules['min_length']:
                errors.append({
                    'field': field_name,
                    'error': 'below_min_length',
                    'message': f"Field '{field_name}' is below minimum length {rules['min_length']}"
                })

        if 'max_length' in rules and isinstance(value, str):
            if len(value) > rules['max_length']:
                errors.append({
                    'field': field_name,
                    'error': 'above_max_length',
                    'message': f"Field '{field_name}' exceeds maximum length {rules['max_length']}"
                })

        # Numeric validation
        if 'min_value' in rules and isinstance(value, (int, float)):
            if value < rules['min_value']:
                errors.append({
                    'field': field_name,
                    'error': 'below_min_value',
                    'message': f"Field '{field_name}' is below minimum value {rules['min_value']}"
                })

        if 'max_value' in rules and isinstance(value, (int, float)):
            if value > rules['max_value']:
                errors.append({
                    'field': field_name,
                    'error': 'above_max_value',
                    'message': f"Field '{field_name}' exceeds maximum value {rules['max_value']}"
                })

        # Enum validation
        if 'enum' in rules:
            if value not in rules['enum']:
                errors.append({
                    'field': field_name,
                    'error': 'invalid_enum_value',
                    'message': f"Field '{field_name}' must be one of: {', '.join(map(str, rules['enum']))}"
                })

        # Regex validation
        if 'regex' in rules and isinstance(value, str):
            pattern = rules['regex']
            if not re.match(pattern, value):
                errors.append({
                    'field': field_name,
                    'error': 'regex_validation_failed',
                    'message': f"Field '{field_name}' does not match pattern {pattern}"
                })

        return errors
