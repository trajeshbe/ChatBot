"""
JSON Generator

This module generates JSON files from extracted data.
"""

import logging
import json
from typing import Optional, Literal
import pandas as pd
import os

logger = logging.getLogger(__name__)


class JSONGenerator:
    """Generate JSON files"""

    def __init__(self):
        """Initialize JSON generator"""
        pass

    async def generate(
        self,
        data: pd.DataFrame,
        output_path: str,
        orient: Literal['records', 'index', 'columns', 'values'] = 'records',
        indent: Optional[int] = 2,
        encoding: str = 'utf-8'
    ) -> str:
        """
        Generate JSON file

        Args:
            data: DataFrame to export
            output_path: Path to save JSON file
            orient: JSON orientation
                - 'records': list of dicts [{col1: val1, col2: val2}, ...]
                - 'index': dict of dicts {index: {col1: val1, col2: val2}}
                - 'columns': dict of dicts {col1: {index: val1}, col2: {index: val2}}
                - 'values': just the values array
            indent: Number of spaces for indentation (None for compact)
            encoding: File encoding

        Returns:
            Path to generated JSON file
        """
        logger.info(f"Generating JSON file: {output_path}")

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Write to JSON
            data.to_json(
                output_path,
                orient=orient,
                indent=indent,
                force_ascii=False
            )

            file_size = os.path.getsize(output_path)
            logger.info(f"JSON file generated: {output_path} ({file_size} bytes)")

            return output_path

        except Exception as e:
            logger.error(f"Error generating JSON file: {str(e)}")
            raise


# Export
__all__ = ['JSONGenerator']
