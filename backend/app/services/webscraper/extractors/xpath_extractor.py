"""
XPath Extractor - Extract data using XPath expressions

This module provides XPath-based data extraction from HTML/XML content.
"""

from typing import List, Optional, Union
from lxml import etree, html as lxml_html
import logging

logger = logging.getLogger(__name__)


class XPathExtractor:
    """
    Extract data from HTML/XML using XPath expressions

    Features:
    - XPath 1.0 expression support
    - Text and attribute extraction
    - Multiple element extraction
    - Namespace support for XML
    """

    def __init__(self):
        self.logger = logger

    def extract(
        self,
        content: str,
        xpath: str,
        attribute: Optional[str] = None,
        multiple: bool = False,
        join_with: Optional[str] = None,
        is_xml: bool = False,
        namespaces: Optional[dict] = None
    ) -> Optional[Union[str, List[str]]]:
        """
        Extract data using XPath expression

        Args:
            content: HTML or XML content
            xpath: XPath expression
            attribute: Optional attribute to extract
            multiple: Whether to extract all matching elements
            join_with: If multiple=True, join results with this separator
            is_xml: Whether content is XML (vs HTML)
            namespaces: Namespace prefix mapping for XML

        Returns:
            Extracted text/attribute value, or None if not found
        """
        try:
            # Parse content
            if is_xml:
                tree = etree.fromstring(content.encode('utf-8'))
            else:
                tree = lxml_html.fromstring(content)

            # Execute XPath query
            if namespaces:
                elements = tree.xpath(xpath, namespaces=namespaces)
            else:
                elements = tree.xpath(xpath)

            if not elements:
                return None

            # Handle different return types
            if isinstance(elements, list):
                if multiple:
                    results = []
                    for element in elements:
                        value = self._extract_from_element(element, attribute)
                        if value:
                            results.append(value)

                    if not results:
                        return None

                    if join_with is not None:
                        return join_with.join(results)
                    return results
                else:
                    # Return first matching element
                    if elements:
                        return self._extract_from_element(elements[0], attribute)
            elif isinstance(elements, str):
                # XPath returned string directly
                return self._normalize_text(elements)
            elif isinstance(elements, (int, float, bool)):
                # XPath returned number or boolean
                return str(elements)

            return None

        except Exception as e:
            self.logger.error(f"XPath extraction failed: {str(e)}")
            return None

    def _extract_from_element(
        self,
        element: any,
        attribute: Optional[str]
    ) -> Optional[str]:
        """
        Extract value from a single element

        Args:
            element: lxml Element object or other XPath result
            attribute: Optional attribute to extract

        Returns:
            Extracted value or None
        """
        try:
            # Handle different element types
            if isinstance(element, str):
                return self._normalize_text(element)

            if isinstance(element, (int, float, bool)):
                return str(element)

            # Handle lxml Element
            if attribute:
                # Extract attribute value
                value = element.get(attribute)
                if value:
                    return str(value).strip()
            else:
                # Extract text content
                text = element.text_content() if hasattr(element, 'text_content') else str(element)
                if text:
                    return self._normalize_text(text)

            return None

        except Exception as e:
            self.logger.error(f"Element extraction failed: {str(e)}")
            return None

    def _normalize_text(self, text: str) -> str:
        """
        Normalize extracted text

        Args:
            text: Raw text

        Returns:
            Normalized text
        """
        # Remove excessive whitespace
        text = ' '.join(text.split())

        # Remove common unwanted characters
        text = text.replace('\xa0', ' ')  # Non-breaking space
        text = text.replace('\u200b', '')  # Zero-width space

        return text.strip()

    def extract_with_fallback(
        self,
        content: str,
        xpath_expressions: List[str],
        attribute: Optional[str] = None,
        is_xml: bool = False
    ) -> Optional[str]:
        """
        Try multiple XPath expressions as fallback chain

        Args:
            content: HTML or XML content
            xpath_expressions: List of XPath expressions to try
            attribute: Optional attribute to extract
            is_xml: Whether content is XML

        Returns:
            First successful extraction result, or None
        """
        for i, xpath in enumerate(xpath_expressions):
            result = self.extract(
                content=content,
                xpath=xpath,
                attribute=attribute,
                is_xml=is_xml
            )

            if result is not None:
                if i > 0:
                    self.logger.info(f"Fallback XPath #{i} succeeded: {xpath}")
                return result

        return None

    def extract_table(
        self,
        content: str,
        table_xpath: str = '//table',
        is_xml: bool = False
    ) -> Optional[List[dict]]:
        """
        Extract table data as list of dictionaries

        Args:
            content: HTML or XML content
            table_xpath: XPath to table element
            is_xml: Whether content is XML

        Returns:
            List of dictionaries with table data, or None
        """
        try:
            if is_xml:
                tree = etree.fromstring(content.encode('utf-8'))
            else:
                tree = lxml_html.fromstring(content)

            tables = tree.xpath(table_xpath)
            if not tables:
                return None

            table = tables[0]  # Use first table

            # Extract headers
            headers = []
            header_cells = table.xpath('.//th')
            if header_cells:
                headers = [
                    self._normalize_text(cell.text_content())
                    for cell in header_cells
                ]

            # Extract rows
            rows = []
            data_rows = table.xpath('.//tr[td]')  # Rows with td elements

            for row in data_rows:
                cells = row.xpath('./td')
                if not cells:
                    continue

                row_data = {}
                for i, cell in enumerate(cells):
                    header = headers[i] if i < len(headers) else f"column_{i}"
                    cell_text = self._normalize_text(cell.text_content())
                    row_data[header] = cell_text

                if row_data:
                    rows.append(row_data)

            return rows if rows else None

        except Exception as e:
            self.logger.error(f"Table extraction failed: {str(e)}")
            return None
