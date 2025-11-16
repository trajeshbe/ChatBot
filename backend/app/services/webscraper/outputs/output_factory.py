"""
Output Factory

This module provides a factory for creating output generators based on format.
"""

import logging
from typing import Dict, Any, Type

from .excel_generator import ExcelGenerator
from .csv_generator import CSVGenerator
from .json_generator import JSONGenerator
from .xml_generator import XMLGenerator
from .parquet_generator import ParquetGenerator

logger = logging.getLogger(__name__)


class OutputFactory:
    """
    Factory for creating output generators

    Provides a centralized way to get the appropriate output generator
    based on the requested output format.
    """

    # Registry of output generators
    _generators: Dict[str, Type] = {
        'excel': ExcelGenerator,
        'xlsx': ExcelGenerator,
        'csv': CSVGenerator,
        'json': JSONGenerator,
        'xml': XMLGenerator,
        'parquet': ParquetGenerator,
        'pq': ParquetGenerator
    }

    @classmethod
    def create(cls, output_format: str):
        """
        Create output generator for specified format

        Args:
            output_format: Output format (excel, csv, json, xml, parquet)

        Returns:
            Output generator instance

        Raises:
            ValueError: If format is not supported
        """
        output_format = output_format.lower()

        generator_class = cls._generators.get(output_format)

        if generator_class is None:
            supported_formats = ', '.join(cls._generators.keys())
            raise ValueError(
                f"Unsupported output format '{output_format}'. "
                f"Supported formats: {supported_formats}"
            )

        logger.debug(f"Creating {generator_class.__name__} for format '{output_format}'")
        return generator_class()

    @classmethod
    def get_supported_formats(cls) -> list:
        """
        Get list of supported output formats

        Returns:
            List of format names
        """
        return list(cls._generators.keys())

    @classmethod
    def register_generator(cls, format_name: str, generator_class: Type):
        """
        Register a custom output generator

        Args:
            format_name: Name of the format
            generator_class: Generator class
        """
        cls._generators[format_name.lower()] = generator_class
        logger.info(f"Registered custom generator for format '{format_name}'")


# Export
__all__ = ['OutputFactory']
