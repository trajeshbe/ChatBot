"""
Template Parser - Parse extraction templates from various formats

This module parses templates from:
- Excel files (.xlsx, .xls)
- CSV files
- JSON files
- YAML files
"""

from typing import Optional, Dict, Any, List
import json
import csv
import logging
from pathlib import Path
import pandas as pd

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    logging.warning("PyYAML not installed. YAML template parsing unavailable.")

from .template_models import (
    TemplateSchema,
    FieldDefinition,
    SourceHint,
    ValidationRule,
    TransformationRule
)

logger = logging.getLogger(__name__)


class TemplateParser:
    """
    Parse extraction templates from various file formats

    Supported formats:
    - Excel (.xlsx, .xls)
    - CSV (.csv)
    - JSON (.json)
    - YAML (.yaml, .yml)
    """

    def __init__(self):
        self.logger = logger

    async def parse_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Parse template from file

        Args:
            file_path: Path to template file

        Returns:
            Parsed template dictionary, or None if parsing failed
        """
        try:
            path = Path(file_path)
            extension = path.suffix.lower()

            if extension in ['.xlsx', '.xls']:
                return await self.parse_excel(file_path)
            elif extension == '.csv':
                return await self.parse_csv(file_path)
            elif extension == '.json':
                return await self.parse_json(file_path)
            elif extension in ['.yaml', '.yml']:
                return await self.parse_yaml(file_path)
            else:
                self.logger.error(f"Unsupported template format: {extension}")
                return None

        except Exception as e:
            self.logger.error(f"Template parsing failed: {str(e)}")
            return None

    async def parse_excel(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Parse template from Excel file

        Expected structure:
        Sheet1 (Fields):
        | field_name | type | required | source_type | source_value | validation | transformation |
        |------------|------|----------|-------------|--------------|------------|----------------|
        | name       | str  | yes      | css         | .title       | min:2      | trim           |

        Args:
            file_path: Path to Excel file

        Returns:
            Parsed template dictionary
        """
        try:
            # Read Excel file
            df = pd.read_excel(file_path, sheet_name=0)

            # Parse metadata from first rows or separate sheet
            template_name = Path(file_path).stem
            template_desc = "Extracted from Excel template"

            # Parse fields
            fields = []
            for _, row in df.iterrows():
                field = self._parse_excel_field_row(row)
                if field:
                    fields.append(field)

            if not fields:
                self.logger.error("No fields found in Excel template")
                return None

            return {
                'name': template_name,
                'description': template_desc,
                'template_type': 'excel',
                'schema_definition': {
                    'version': '1.0',
                    'type': 'extracted_from_excel'
                },
                'fields': fields
            }

        except Exception as e:
            self.logger.error(f"Excel parsing failed: {str(e)}")
            return None

    def _parse_excel_field_row(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """Parse a single field row from Excel"""
        try:
            field_name = str(row.get('field_name', row.get('name', ''))).strip()
            if not field_name or field_name == 'nan':
                return None

            # Build field definition
            field = {
                'name': field_name,
                'type': str(row.get('type', 'string')).lower(),
                'required': str(row.get('required', 'no')).lower() in ['yes', 'true', '1'],
            }

            # Parse source hint
            source_type = str(row.get('source_type', 'css')).lower()
            source_value = str(row.get('source_value', '')).strip()

            if source_value and source_value != 'nan':
                field['source_hint'] = self._parse_source_hint(source_type, source_value)

            # Parse validation
            validation_str = str(row.get('validation', '')).strip()
            if validation_str and validation_str != 'nan':
                field['validation'] = self._parse_validation_string(validation_str)

            # Parse transformation
            transformation_str = str(row.get('transformation', '')).strip()
            if transformation_str and transformation_str != 'nan':
                field['transformation'] = transformation_str

            return field

        except Exception as e:
            self.logger.error(f"Field row parsing failed: {str(e)}")
            return None

    async def parse_csv(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Parse template from CSV file

        CSV format same as Excel

        Args:
            file_path: Path to CSV file

        Returns:
            Parsed template dictionary
        """
        try:
            # Use pandas to read CSV
            df = pd.read_csv(file_path)

            # Same parsing logic as Excel
            template_name = Path(file_path).stem
            template_desc = "Extracted from CSV template"

            fields = []
            for _, row in df.iterrows():
                field = self._parse_excel_field_row(row)  # Reuse Excel parser
                if field:
                    fields.append(field)

            if not fields:
                self.logger.error("No fields found in CSV template")
                return None

            return {
                'name': template_name,
                'description': template_desc,
                'template_type': 'csv',
                'schema_definition': {
                    'version': '1.0',
                    'type': 'extracted_from_csv'
                },
                'fields': fields
            }

        except Exception as e:
            self.logger.error(f"CSV parsing failed: {str(e)}")
            return None

    async def parse_json(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Parse template from JSON file

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed template dictionary
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate required fields
            if 'fields' not in data:
                self.logger.error("JSON template missing 'fields'")
                return None

            # Set defaults if not provided
            if 'name' not in data:
                data['name'] = Path(file_path).stem

            if 'template_type' not in data:
                data['template_type'] = 'json'

            if 'schema_definition' not in data:
                data['schema_definition'] = {
                    'version': '1.0',
                    'type': 'custom'
                }

            return data

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"JSON parsing failed: {str(e)}")
            return None

    async def parse_yaml(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Parse template from YAML file

        Args:
            file_path: Path to YAML file

        Returns:
            Parsed template dictionary
        """
        if not YAML_AVAILABLE:
            self.logger.error("PyYAML not installed")
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            # Validate required fields
            if 'fields' not in data:
                self.logger.error("YAML template missing 'fields'")
                return None

            # Set defaults
            if 'name' not in data:
                data['name'] = Path(file_path).stem

            if 'template_type' not in data:
                data['template_type'] = 'yaml'

            if 'schema_definition' not in data:
                data['schema_definition'] = {
                    'version': '1.0',
                    'type': 'custom'
                }

            return data

        except yaml.YAMLError as e:
            self.logger.error(f"Invalid YAML: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"YAML parsing failed: {str(e)}")
            return None

    def _parse_source_hint(self, source_type: str, source_value: str) -> Dict[str, Any]:
        """Parse source hint from string"""
        hint = {'type': source_type}

        if source_type == 'css':
            hint['selector'] = source_value
        elif source_type == 'xpath':
            hint['xpath'] = source_value
        elif source_type == 'regex':
            hint['pattern'] = source_value
        elif source_type == 'llm':
            hint['prompt'] = source_value
        elif source_type == 'jsonpath':
            hint['path'] = source_value
        else:
            # Generic handling
            hint['value'] = source_value

        return hint

    def _parse_validation_string(self, validation_str: str) -> Dict[str, Any]:
        """
        Parse validation rules from string

        Format: "min:2,max:100,regex:^[A-Z]"

        Args:
            validation_str: Validation string

        Returns:
            Validation rules dictionary
        """
        rules = {}

        # Split by comma
        parts = validation_str.split(',')

        for part in parts:
            part = part.strip()
            if ':' in part:
                key, value = part.split(':', 1)
                key = key.strip()
                value = value.strip()

                # Convert to appropriate type
                if key in ['min_length', 'max_length', 'min_value', 'max_value']:
                    try:
                        rules[key] = int(value) if '.' not in value else float(value)
                    except ValueError:
                        rules[key] = value
                elif key == 'enum':
                    rules[key] = [v.strip() for v in value.split('|')]
                else:
                    rules[key] = value

        return rules

    async def validate_template(self, template_data: Dict[str, Any]) -> bool:
        """
        Validate template structure

        Args:
            template_data: Template dictionary

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            required = ['name', 'fields']
            for field in required:
                if field not in template_data:
                    self.logger.error(f"Template missing required field: {field}")
                    return False

            # Validate fields list
            if not isinstance(template_data['fields'], list):
                self.logger.error("'fields' must be a list")
                return False

            if len(template_data['fields']) == 0:
                self.logger.error("Template must have at least one field")
                return False

            # Validate each field
            for field in template_data['fields']:
                if not isinstance(field, dict):
                    self.logger.error(f"Invalid field definition: {field}")
                    return False

                if 'name' not in field:
                    self.logger.error("Field missing 'name'")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Template validation failed: {str(e)}")
            return False
