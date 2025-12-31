"""
CSS Extractor - Extract data using CSS selectors

This module provides CSS selector-based data extraction from HTML content.
"""

from typing import List, Optional, Any, Union
from bs4 import BeautifulSoup, Tag
import logging

logger = logging.getLogger(__name__)


class CSSExtractor:
    """
    Extract data from HTML using CSS selectors

    Features:
    - Single and multiple element extraction
    - Attribute extraction
    - Text extraction with normalization
    - Fallback selector chain support
    """

    def __init__(self):
        self.logger = logger

    def extract(
        self,
        html_content: str,
        selector: str,
        attribute: Optional[str] = None,
        fallback_selectors: Optional[List[str]] = None,
        multiple: bool = False,
        join_with: Optional[str] = None
    ) -> Optional[Union[str, List[str]]]:
        """
        Extract data using CSS selector

        Args:
            html_content: HTML content to parse
            selector: CSS selector
            attribute: Optional attribute to extract (e.g., 'href', 'src')
            fallback_selectors: List of fallback selectors to try if primary fails
            multiple: Whether to extract all matching elements
            join_with: If multiple=True, join results with this separator

        Returns:
            Extracted text/attribute value, or None if not found
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Try primary selector
            result = self._extract_with_selector(
                soup, selector, attribute, multiple
            )

            # Try fallback selectors if primary failed
            if result is None and fallback_selectors:
                for fallback in fallback_selectors:
                    result = self._extract_with_selector(
                        soup, fallback, attribute, multiple
                    )
                    if result is not None:
                        self.logger.info(
                            f"Fallback selector '{fallback}' succeeded"
                        )
                        break

            # Join multiple results if requested
            if multiple and isinstance(result, list) and join_with is not None:
                result = join_with.join(result)

            return result

        except Exception as e:
            self.logger.error(f"CSS extraction failed: {str(e)}")
            return None

    def _extract_with_selector(
        self,
        soup: BeautifulSoup,
        selector: str,
        attribute: Optional[str],
        multiple: bool
    ) -> Optional[Union[str, List[str]]]:
        """
        Extract data using a single selector

        Args:
            soup: BeautifulSoup object
            selector: CSS selector
            attribute: Optional attribute to extract
            multiple: Whether to extract all matching elements

        Returns:
            Extracted data or None
        """
        try:
            if multiple:
                elements = soup.select(selector)
                if not elements:
                    return None

                results = []
                for element in elements:
                    value = self._extract_from_element(element, attribute)
                    if value:
                        results.append(value)

                return results if results else None
            else:
                element = soup.select_one(selector)
                if not element:
                    return None

                return self._extract_from_element(element, attribute)

        except Exception as e:
            self.logger.error(
                f"Selector '{selector}' failed: {str(e)}"
            )
            return None

    def _extract_from_element(
        self,
        element: Tag,
        attribute: Optional[str]
    ) -> Optional[str]:
        """
        Extract value from a single element

        Args:
            element: BeautifulSoup Tag element
            attribute: Optional attribute to extract

        Returns:
            Extracted value or None
        """
        try:
            if attribute:
                # Extract attribute value
                value = element.get(attribute)
                if value:
                    return str(value).strip()
            else:
                # Extract text content
                text = element.get_text(separator=' ', strip=True)
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

    def extract_table(
        self,
        html_content: str,
        table_selector: str = 'table',
        header_selector: str = 'th',
        row_selector: str = 'tr',
        cell_selector: str = 'td'
    ) -> Optional[List[dict]]:
        """
        Extract table data as list of dictionaries

        Args:
            html_content: HTML content
            table_selector: Selector for table element
            header_selector: Selector for header cells
            row_selector: Selector for rows
            cell_selector: Selector for data cells

        Returns:
            List of dictionaries with table data, or None if not found
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            table = soup.select_one(table_selector)

            if not table:
                self.logger.warning(f"Table not found with selector '{table_selector}'")
                return None

            # Extract headers
            headers = []
            header_row = table.select_one(f'{row_selector}:has({header_selector})')
            if header_row:
                header_cells = header_row.select(header_selector)
                headers = [
                    self._normalize_text(cell.get_text())
                    for cell in header_cells
                ]

            # If no headers found, generate default ones
            if not headers:
                first_row = table.select_one(row_selector)
                if first_row:
                    num_columns = len(first_row.select(cell_selector))
                    headers = [f"column_{i}" for i in range(num_columns)]

            # Extract rows
            rows = []
            data_rows = table.select(row_selector)

            for row in data_rows:
                # Skip header rows
                if row.select(header_selector):
                    continue

                cells = row.select(cell_selector)
                if not cells:
                    continue

                row_data = {}
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        cell_text = self._normalize_text(cell.get_text())
                        row_data[headers[i]] = cell_text

                if row_data:
                    rows.append(row_data)

            return rows if rows else None

        except Exception as e:
            self.logger.error(f"Table extraction failed: {str(e)}")
            return None

    def extract_list(
        self,
        html_content: str,
        list_selector: str = 'ul, ol',
        item_selector: str = 'li'
    ) -> Optional[List[str]]:
        """
        Extract list items

        Args:
            html_content: HTML content
            list_selector: Selector for list container
            item_selector: Selector for list items

        Returns:
            List of item texts, or None if not found
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            list_container = soup.select_one(list_selector)

            if not list_container:
                self.logger.warning(f"List not found with selector '{list_selector}'")
                return None

            items = list_container.select(item_selector)
            if not items:
                return None

            result = []
            for item in items:
                text = self._normalize_text(item.get_text())
                if text:
                    result.append(text)

            return result if result else None

        except Exception as e:
            self.logger.error(f"List extraction failed: {str(e)}")
            return None
