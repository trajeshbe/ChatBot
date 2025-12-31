"""
XML Generator

This module generates XML files from extracted data.
"""

import logging
from typing import Optional
from xml.etree.ElementTree import Element, SubElement, tostring, ElementTree
from xml.dom import minidom
import pandas as pd
import os

logger = logging.getLogger(__name__)


class XMLGenerator:
    """Generate XML files"""

    def __init__(self):
        """Initialize XML generator"""
        pass

    async def generate(
        self,
        data: pd.DataFrame,
        output_path: str,
        root_element: str = 'data',
        row_element: str = 'record',
        encoding: str = 'utf-8'
    ) -> str:
        """
        Generate XML file

        Args:
            data: DataFrame to export
            output_path: Path to save XML file
            root_element: Name of root XML element
            row_element: Name of element for each row
            encoding: File encoding

        Returns:
            Path to generated XML file
        """
        logger.info(f"Generating XML file: {output_path}")

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Create root element
            root = Element(root_element)

            # Add rows
            for _, row in data.iterrows():
                record = SubElement(root, row_element)

                for col_name, value in row.items():
                    # Clean column name for XML element
                    element_name = str(col_name).replace(' ', '_').replace('-', '_')

                    # Create element
                    col_element = SubElement(record, element_name)

                    # Set value
                    if pd.notna(value):
                        col_element.text = str(value)

            # Pretty print XML
            xml_str = self._prettify_xml(root)

            # Write to file
            with open(output_path, 'w', encoding=encoding) as f:
                f.write(xml_str)

            file_size = os.path.getsize(output_path)
            logger.info(f"XML file generated: {output_path} ({file_size} bytes)")

            return output_path

        except Exception as e:
            logger.error(f"Error generating XML file: {str(e)}")
            raise

    def _prettify_xml(self, element: Element) -> str:
        """
        Return pretty-printed XML string

        Args:
            element: Root XML element

        Returns:
            Formatted XML string
        """
        rough_string = tostring(element, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")


# Export
__all__ = ['XMLGenerator']
