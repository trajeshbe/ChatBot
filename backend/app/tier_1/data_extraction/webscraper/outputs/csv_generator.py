"""
CSV Generator

This module generates CSV files from extracted data.
"""

import logging
from typing import Optional
import pandas as pd
import os

logger = logging.getLogger(__name__)


class CSVGenerator:
    """Generate CSV files"""

    def __init__(self):
        """Initialize CSV generator"""
        pass

    async def generate(
        self,
        data: pd.DataFrame,
        output_path: str,
        delimiter: str = ',',
        include_index: bool = False,
        encoding: str = 'utf-8'
    ) -> str:
        """
        Generate CSV file

        Args:
            data: DataFrame to export
            output_path: Path to save CSV file
            delimiter: CSV delimiter (default: comma)
            include_index: Whether to include DataFrame index
            encoding: File encoding

        Returns:
            Path to generated CSV file
        """
        logger.info(f"Generating CSV file: {output_path}")

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Write to CSV
            data.to_csv(
                output_path,
                index=include_index,
                sep=delimiter,
                encoding=encoding
            )

            file_size = os.path.getsize(output_path)
            logger.info(f"CSV file generated: {output_path} ({file_size} bytes)")

            return output_path

        except Exception as e:
            logger.error(f"Error generating CSV file: {str(e)}")
            raise


# Export
__all__ = ['CSVGenerator']
