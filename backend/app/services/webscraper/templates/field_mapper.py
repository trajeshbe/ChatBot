"""
Field Mapper - Map extracted data to template fields

This module handles mapping and transformation of extracted data to match template structure.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class FieldMapper:
    """
    Map and transform extracted data to template fields

    Features:
    - Field name mapping
    - Data type conversion
    - Value transformations
    - Default value handling
    """

    def __init__(self):
        self.logger = logger

    async def map_data(
        self,
        extracted_data: Dict[str, Any],
        field_definitions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Map extracted data to template fields

        Args:
            extracted_data: Raw extracted data
            field_definitions: Field definitions from template

        Returns:
            Mapped and transformed data
        """
        mapped_data = {}

        for field_def in field_definitions:
            field_name = field_def.get('name')
            if not field_name:
                continue

            # Get value from extracted data
            value = extracted_data.get(field_name)

            # Apply default if value is None and default exists
            if value is None:
                default_value = field_def.get('default_value')
                if default_value is not None:
                    value = default_value

            # Skip if still None
            if value is None:
                continue

            # Convert type
            field_type = field_def.get('type', 'string')
            converted_value = self._convert_type(value, field_type)

            # Apply transformation if specified
            transformation = field_def.get('transformation')
            if transformation and converted_value is not None:
                converted_value = await self._apply_transformation(
                    converted_value, transformation
                )

            mapped_data[field_name] = converted_value

        return mapped_data

    def _convert_type(self, value: Any, target_type: str) -> Optional[Any]:
        """Convert value to target type"""
        try:
            if value is None:
                return None

            if target_type == 'string':
                return str(value)

            elif target_type == 'integer':
                return int(value) if not isinstance(value, bool) else value

            elif target_type == 'float':
                return float(value)

            elif target_type == 'boolean':
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    return value.lower() in ['true', 'yes', '1', 'y']
                return bool(value)

            else:
                return value

        except Exception as e:
            self.logger.error(f"Type conversion failed: {str(e)}")
            return value

    async def _apply_transformation(
        self,
        value: Any,
        transformation: Any
    ) -> Any:
        """Apply transformation to value"""
        try:
            # Handle string transformation names
            if isinstance(transformation, str):
                return await self._apply_named_transformation(value, transformation)

            # Handle transformation dict
            if isinstance(transformation, dict):
                trans_type = transformation.get('type')
                if trans_type:
                    return await self._apply_transformation_dict(value, transformation)

            return value

        except Exception as e:
            self.logger.error(f"Transformation failed: {str(e)}")
            return value

    async def _apply_named_transformation(self, value: Any, trans_name: str) -> Any:
        """Apply named transformation"""
        if not isinstance(value, str):
            value = str(value)

        if trans_name == 'to_lowercase':
            return value.lower()
        elif trans_name == 'to_uppercase':
            return value.upper()
        elif trans_name == 'title_case':
            return value.title()
        elif trans_name == 'trim':
            return value.strip()
        elif trans_name == 'normalize_whitespace':
            return ' '.join(value.split())
        else:
            return value

    async def _apply_transformation_dict(
        self,
        value: Any,
        transformation: Dict[str, Any]
    ) -> Any:
        """Apply transformation from dict config"""
        trans_type = transformation.get('type')

        if trans_type == 'replace':
            if isinstance(value, str):
                find = transformation.get('find', '')
                replace_with = transformation.get('replace_with', '')
                return value.replace(find, replace_with)

        elif trans_type == 'split':
            if isinstance(value, str):
                separator = transformation.get('separator', ',')
                return [v.strip() for v in value.split(separator)]

        elif trans_type == 'join':
            if isinstance(value, list):
                join_with = transformation.get('join_with', ', ')
                return join_with.join(str(v) for v in value)

        return value
