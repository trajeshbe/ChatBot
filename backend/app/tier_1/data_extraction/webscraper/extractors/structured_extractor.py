"""
Structured Data Extractor - Extract data from JSON, XML, and structured formats

This module provides extraction from structured data formats including:
- JSON (with JSONPath)
- XML (with XPath)
- JSON-LD
- Microdata
- OpenGraph
- Schema.org
"""

from typing import Optional, List, Dict, Any, Union
import json
import logging
from lxml import etree, html as lxml_html
from bs4 import BeautifulSoup
import re

try:
    from jsonpath_ng import parse as jsonpath_parse
    JSONPATH_AVAILABLE = True
except ImportError:
    JSONPATH_AVAILABLE = False
    logging.warning("jsonpath-ng not installed. JSONPath extraction will be limited.")

logger = logging.getLogger(__name__)


class StructuredExtractor:
    """
    Extract data from structured formats

    Features:
    - JSON extraction with JSONPath
    - XML extraction with XPath
    - JSON-LD extraction
    - Microdata extraction
    - OpenGraph metadata extraction
    - Schema.org structured data extraction
    """

    def __init__(self):
        self.logger = logger

    def extract_json(
        self,
        json_content: Union[str, dict],
        path: Optional[str] = None
    ) -> Optional[Any]:
        """
        Extract data from JSON using JSONPath

        Args:
            json_content: JSON string or dict
            path: JSONPath expression (e.g., "$.data.items[*].name")
                  If None, returns entire JSON

        Returns:
            Extracted data, or None if not found
        """
        try:
            # Parse JSON if string
            if isinstance(json_content, str):
                data = json.loads(json_content)
            else:
                data = json_content

            # Return full JSON if no path specified
            if not path:
                return data

            # Use JSONPath if available
            if JSONPATH_AVAILABLE:
                jsonpath_expr = jsonpath_parse(path)
                matches = [match.value for match in jsonpath_expr.find(data)]

                if not matches:
                    return None
                elif len(matches) == 1:
                    return matches[0]
                else:
                    return matches
            else:
                # Fallback to simple path parsing (limited)
                return self._simple_json_path(data, path)

        except Exception as e:
            self.logger.error(f"JSON extraction failed: {str(e)}")
            return None

    def _simple_json_path(self, data: dict, path: str) -> Optional[Any]:
        """
        Simple JSONPath implementation (fallback)

        Supports basic paths like: $.key1.key2[0].key3
        """
        try:
            # Remove leading $. if present
            path = path.lstrip('$.')

            # Split path into parts
            parts = re.split(r'\.|\[|\]', path)
            parts = [p for p in parts if p]  # Remove empty strings

            current = data
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                elif isinstance(current, list):
                    # Try to convert to index
                    try:
                        index = int(part)
                        current = current[index]
                    except (ValueError, IndexError):
                        return None
                else:
                    return None

                if current is None:
                    return None

            return current

        except Exception as e:
            self.logger.error(f"Simple JSON path failed: {str(e)}")
            return None

    def extract_json_ld(
        self,
        html_content: str,
        type_filter: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Extract JSON-LD structured data from HTML

        Args:
            html_content: HTML content
            type_filter: Optional Schema.org type to filter (e.g., "Product", "Article")

        Returns:
            List of JSON-LD objects, or None if not found
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find all JSON-LD script tags
            scripts = soup.find_all(
                'script',
                type='application/ld+json'
            )

            if not scripts:
                return None

            results = []
            for script in scripts:
                try:
                    data = json.loads(script.string)

                    # Handle @graph notation
                    if isinstance(data, dict) and '@graph' in data:
                        items = data['@graph']
                    else:
                        items = [data] if isinstance(data, dict) else []

                    # Filter by type if specified
                    for item in items:
                        if type_filter:
                            item_type = item.get('@type', '')
                            if item_type == type_filter or type_filter in item_type:
                                results.append(item)
                        else:
                            results.append(item)

                except json.JSONDecodeError:
                    self.logger.warning("Failed to parse JSON-LD script")
                    continue

            return results if results else None

        except Exception as e:
            self.logger.error(f"JSON-LD extraction failed: {str(e)}")
            return None

    def extract_microdata(
        self,
        html_content: str,
        itemtype: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Extract Microdata from HTML

        Args:
            html_content: HTML content
            itemtype: Optional itemtype to filter (e.g., "http://schema.org/Product")

        Returns:
            List of microdata items, or None if not found
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find all elements with itemscope
            items = soup.find_all(attrs={'itemscope': True})

            if not items:
                return None

            results = []
            for item in items:
                # Check itemtype filter
                if itemtype and item.get('itemtype') != itemtype:
                    continue

                # Extract properties
                properties = {}
                props = item.find_all(attrs={'itemprop': True})

                for prop in props:
                    prop_name = prop.get('itemprop')
                    prop_value = self._extract_microdata_value(prop)

                    if prop_name:
                        if prop_name in properties:
                            # Convert to list if multiple values
                            if not isinstance(properties[prop_name], list):
                                properties[prop_name] = [properties[prop_name]]
                            properties[prop_name].append(prop_value)
                        else:
                            properties[prop_name] = prop_value

                if properties:
                    properties['@type'] = item.get('itemtype', 'Unknown')
                    results.append(properties)

            return results if results else None

        except Exception as e:
            self.logger.error(f"Microdata extraction failed: {str(e)}")
            return None

    def _extract_microdata_value(self, element) -> Any:
        """Extract value from microdata property element"""
        # Check for specific attributes first
        if element.name == 'meta':
            return element.get('content', '')
        elif element.name == 'link':
            return element.get('href', '')
        elif element.name in ['img', 'audio', 'video']:
            return element.get('src', '')
        elif element.name == 'time':
            return element.get('datetime', element.get_text())
        else:
            # Return text content
            return element.get_text(strip=True)

    def extract_opengraph(
        self,
        html_content: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract OpenGraph metadata from HTML

        Args:
            html_content: HTML content

        Returns:
            Dictionary of OpenGraph properties, or None if not found
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find all OpenGraph meta tags
            og_tags = soup.find_all('meta', property=re.compile(r'^og:'))

            if not og_tags:
                return None

            og_data = {}
            for tag in og_tags:
                property_name = tag.get('property', '').replace('og:', '')
                content = tag.get('content', '')

                if property_name and content:
                    og_data[property_name] = content

            return og_data if og_data else None

        except Exception as e:
            self.logger.error(f"OpenGraph extraction failed: {str(e)}")
            return None

    def extract_meta_tags(
        self,
        html_content: str,
        include_patterns: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extract meta tags from HTML

        Args:
            html_content: HTML content
            include_patterns: List of patterns to match (e.g., ["og:", "twitter:", "article:"])

        Returns:
            Dictionary of meta tag properties, or None if not found
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            meta_tags = soup.find_all('meta')
            if not meta_tags:
                return None

            meta_data = {}

            for tag in meta_tags:
                # Check property attribute
                prop = tag.get('property', '')
                if prop:
                    content = tag.get('content', '')
                    if content:
                        if include_patterns:
                            if any(prop.startswith(pattern) for pattern in include_patterns):
                                meta_data[prop] = content
                        else:
                            meta_data[prop] = content

                # Check name attribute
                name = tag.get('name', '')
                if name:
                    content = tag.get('content', '')
                    if content:
                        if include_patterns:
                            if any(name.startswith(pattern) for pattern in include_patterns):
                                meta_data[name] = content
                        else:
                            meta_data[name] = content

            return meta_data if meta_data else None

        except Exception as e:
            self.logger.error(f"Meta tag extraction failed: {str(e)}")
            return None

    def extract_schema_org(
        self,
        html_content: str,
        schema_type: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Extract Schema.org data from HTML

        Combines JSON-LD and Microdata extraction

        Args:
            html_content: HTML content
            schema_type: Optional Schema.org type to filter

        Returns:
            List of Schema.org objects, or None if not found
        """
        results = []

        # Extract JSON-LD
        json_ld_data = self.extract_json_ld(html_content, type_filter=schema_type)
        if json_ld_data:
            results.extend(json_ld_data)

        # Extract Microdata
        itemtype = f"http://schema.org/{schema_type}" if schema_type else None
        microdata = self.extract_microdata(html_content, itemtype=itemtype)
        if microdata:
            results.extend(microdata)

        return results if results else None

    def extract_all_structured_data(
        self,
        html_content: str
    ) -> Dict[str, Any]:
        """
        Extract all structured data from HTML

        Returns:
            Dictionary with all structured data types found
        """
        result = {
            'json_ld': self.extract_json_ld(html_content),
            'microdata': self.extract_microdata(html_content),
            'opengraph': self.extract_opengraph(html_content),
            'meta_tags': self.extract_meta_tags(html_content),
        }

        # Remove None values
        return {k: v for k, v in result.items() if v is not None}
