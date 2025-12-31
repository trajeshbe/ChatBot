"""
Parquet Generator

This module generates Parquet files from extracted data for analytics workflows.
"""

import logging
from typing import Optional
import pandas as pd
import os

logger = logging.getLogger(__name__)


class ParquetGenerator:
    """Generate Parquet files"""

    def __init__(self):
        """Initialize Parquet generator"""
        pass

    async def generate(
        self,
        data: pd.DataFrame,
        output_path: str,
        compression: str = 'snappy',
        include_index: bool = False
    ) -> str:
        """
        Generate Parquet file

        Args:
            data: DataFrame to export
            output_path: Path to save Parquet file
            compression: Compression algorithm (snappy, gzip, brotli, none)
            include_index: Whether to include DataFrame index

        Returns:
            Path to generated Parquet file
        """
        logger.info(f"Generating Parquet file: {output_path}")

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Write to Parquet
            data.to_parquet(
                output_path,
                compression=compression,
                index=include_index
            )

            file_size = os.path.getsize(output_path)
            logger.info(f"Parquet file generated: {output_path} ({file_size} bytes)")

            return output_path

        except Exception as e:
            logger.error(f"Error generating Parquet file: {str(e)}")
            raise


# Export
__all__ = ['ParquetGenerator']
