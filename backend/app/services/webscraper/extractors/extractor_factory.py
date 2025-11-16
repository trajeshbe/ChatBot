"""
Extractor Factory - Create and manage data extractors

This module provides a factory for creating and using different extractors with fallback chains.
"""

from typing import Optional, List, Any, Dict, Union
from .css_extractor import CSSExtractor
from .xpath_extractor import XPathExtractor
from .regex_extractor import RegexExtractor
from .llm_extractor import LLMExtractor
from .structured_extractor import StructuredExtractor
import logging

logger = logging.getLogger(__name__)


class ExtractorFactory:
    """
    Factory for creating and managing extractors

    Features:
    - Create appropriate extractor based on hint type
    - Execute extraction with fallback chain
    - Combine results from multiple extractors
    """

    def __init__(self, llm_service=None):
        """
        Initialize extractor factory

        Args:
            llm_service: LLM service instance for LLM extraction
        """
        self.logger = logger
        self.llm_service = llm_service

        # Initialize extractors
        self.css_extractor = CSSExtractor()
        self.xpath_extractor = XPathExtractor()
        self.regex_extractor = RegexExtractor()
        self.llm_extractor = LLMExtractor(llm_service=llm_service)
        self.structured_extractor = StructuredExtractor()

    def create_extractor(self, extractor_type: str):
        """
        Create extractor instance by type

        Args:
            extractor_type: Type of extractor (css, xpath, regex, llm, structured)

        Returns:
            Extractor instance
        """
        extractors = {
            'css': self.css_extractor,
            'xpath': self.xpath_extractor,
            'regex': self.regex_extractor,
            'llm': self.llm_extractor,
            'structured': self.structured_extractor,
            'jsonpath': self.structured_extractor,
        }

        extractor = extractors.get(extractor_type.lower())
        if not extractor:
            raise ValueError(
                f"Unknown extractor type: {extractor_type}. "
                f"Available: {', '.join(extractors.keys())}"
            )

        return extractor

    async def extract_with_hint(
        self,
        content: str,
        source_hint: Dict[str, Any],
        field_name: str = "value",
        field_type: str = "string",
        llm_provider: str = "ollama"
    ) -> Optional[Any]:
        """
        Extract data using source hint configuration

        Args:
            content: Content to extract from (HTML, text, JSON, etc.)
            source_hint: Source hint dictionary with extraction configuration
            field_name: Name of field being extracted
            field_type: Type of field
            llm_provider: LLM provider for LLM extraction

        Returns:
            Extracted value, or None if extraction failed
        """
        hint_type = source_hint.get('type', 'css')

        try:
            if hint_type == 'css':
                return self._extract_css(content, source_hint)

            elif hint_type == 'xpath':
                return self._extract_xpath(content, source_hint)

            elif hint_type == 'regex':
                return self._extract_regex(content, source_hint)

            elif hint_type == 'llm':
                return await self._extract_llm(
                    content, source_hint, field_name, field_type, llm_provider
                )

            elif hint_type == 'jsonpath':
                return self._extract_jsonpath(content, source_hint)

            elif hint_type == 'structured':
                return self._extract_structured(content, source_hint)

            else:
                self.logger.error(f"Unknown hint type: {hint_type}")
                return None

        except Exception as e:
            self.logger.error(
                f"Extraction failed for field '{field_name}' "
                f"with hint type '{hint_type}': {str(e)}"
            )
            return None

    def _extract_css(self, content: str, hint: Dict[str, Any]) -> Optional[Any]:
        """Extract using CSS selector"""
        selector = hint.get('selector')
        if not selector:
            self.logger.error("CSS hint missing 'selector'")
            return None

        return self.css_extractor.extract(
            html_content=content,
            selector=selector,
            attribute=hint.get('attribute'),
            fallback_selectors=hint.get('fallback_selectors'),
            multiple=hint.get('multiple', False),
            join_with=hint.get('join_with')
        )

    def _extract_xpath(self, content: str, hint: Dict[str, Any]) -> Optional[Any]:
        """Extract using XPath"""
        xpath = hint.get('xpath')
        if not xpath:
            self.logger.error("XPath hint missing 'xpath'")
            return None

        return self.xpath_extractor.extract(
            content=content,
            xpath=xpath,
            attribute=hint.get('attribute'),
            multiple=hint.get('multiple', False),
            join_with=hint.get('join_with'),
            is_xml=hint.get('is_xml', False),
            namespaces=hint.get('namespaces')
        )

    def _extract_regex(self, content: str, hint: Dict[str, Any]) -> Optional[Any]:
        """Extract using regex"""
        pattern = hint.get('pattern')
        if not pattern:
            self.logger.error("Regex hint missing 'pattern'")
            return None

        return self.regex_extractor.extract(
            text=content,
            pattern=pattern,
            group=hint.get('group', 0),
            multiple=hint.get('multiple', False),
            join_with=hint.get('join_with')
        )

    async def _extract_llm(
        self,
        content: str,
        hint: Dict[str, Any],
        field_name: str,
        field_type: str,
        llm_provider: str
    ) -> Optional[Any]:
        """Extract using LLM"""
        prompt = hint.get('prompt')
        if not prompt:
            self.logger.error("LLM hint missing 'prompt'")
            return None

        return await self.llm_extractor.extract(
            content=content,
            prompt=prompt,
            field_name=field_name,
            field_type=field_type,
            llm_provider=llm_provider
        )

    def _extract_jsonpath(self, content: str, hint: Dict[str, Any]) -> Optional[Any]:
        """Extract using JSONPath"""
        path = hint.get('path')
        if not path:
            self.logger.error("JSONPath hint missing 'path'")
            return None

        return self.structured_extractor.extract_json(
            json_content=content,
            path=path
        )

    def _extract_structured(self, content: str, hint: Dict[str, Any]) -> Optional[Any]:
        """Extract structured data"""
        data_type = hint.get('data_type', 'json_ld')

        if data_type == 'json_ld':
            return self.structured_extractor.extract_json_ld(
                html_content=content,
                type_filter=hint.get('type_filter')
            )
        elif data_type == 'microdata':
            return self.structured_extractor.extract_microdata(
                html_content=content,
                itemtype=hint.get('itemtype')
            )
        elif data_type == 'opengraph':
            return self.structured_extractor.extract_opengraph(content)
        elif data_type == 'schema_org':
            return self.structured_extractor.extract_schema_org(
                html_content=content,
                schema_type=hint.get('schema_type')
            )
        else:
            self.logger.error(f"Unknown structured data type: {data_type}")
            return None

    async def extract_with_fallback(
        self,
        content: str,
        source_hints: List[Dict[str, Any]],
        field_name: str = "value",
        field_type: str = "string",
        llm_provider: str = "ollama"
    ) -> Optional[Any]:
        """
        Extract using fallback chain of multiple hints

        Tries each hint in order until one succeeds

        Args:
            content: Content to extract from
            source_hints: List of source hint configurations
            field_name: Name of field being extracted
            field_type: Type of field
            llm_provider: LLM provider for LLM extraction

        Returns:
            First successful extraction result, or None if all fail
        """
        for i, hint in enumerate(source_hints):
            result = await self.extract_with_hint(
                content=content,
                source_hint=hint,
                field_name=field_name,
                field_type=field_type,
                llm_provider=llm_provider
            )

            if result is not None:
                if i > 0:
                    self.logger.info(
                        f"Fallback hint #{i} succeeded for field '{field_name}'"
                    )
                return result

        self.logger.warning(
            f"All extraction hints failed for field '{field_name}'"
        )
        return None

    async def extract_with_default_fallback(
        self,
        content: str,
        source_hint: Dict[str, Any],
        field_name: str = "value",
        field_type: str = "string",
        llm_provider: str = "ollama"
    ) -> Optional[Any]:
        """
        Extract with automatic fallback to LLM if primary extraction fails

        Args:
            content: Content to extract from
            source_hint: Primary source hint
            field_name: Name of field being extracted
            field_type: Type of field
            llm_provider: LLM provider for fallback

        Returns:
            Extracted value or None
        """
        # Try primary extraction
        result = await self.extract_with_hint(
            content=content,
            source_hint=source_hint,
            field_name=field_name,
            field_type=field_type,
            llm_provider=llm_provider
        )

        # If failed and not already using LLM, fallback to LLM
        if result is None and source_hint.get('type') != 'llm':
            self.logger.info(
                f"Primary extraction failed for '{field_name}', "
                f"falling back to LLM"
            )

            llm_hint = {
                'type': 'llm',
                'prompt': f"Extract the {field_name} from this content"
            }

            result = await self.extract_with_hint(
                content=content,
                source_hint=llm_hint,
                field_name=field_name,
                field_type=field_type,
                llm_provider=llm_provider
            )

        return result

    def get_available_extractors(self) -> List[str]:
        """Get list of available extractor types"""
        return ['css', 'xpath', 'regex', 'llm', 'structured', 'jsonpath']

    def get_extractor_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Get capabilities of each extractor type"""
        return {
            'css': {
                'name': 'CSS Selector',
                'description': 'Extract data using CSS selectors',
                'supports': ['html'],
                'features': ['single', 'multiple', 'attributes', 'fallback'],
            },
            'xpath': {
                'name': 'XPath',
                'description': 'Extract data using XPath expressions',
                'supports': ['html', 'xml'],
                'features': ['single', 'multiple', 'attributes', 'namespaces'],
            },
            'regex': {
                'name': 'Regular Expression',
                'description': 'Extract data using regex patterns',
                'supports': ['text', 'html'],
                'features': ['patterns', 'groups', 'multiple', 'common_patterns'],
            },
            'llm': {
                'name': 'LLM-Powered',
                'description': 'Extract data using Large Language Models',
                'supports': ['text', 'html', 'any'],
                'features': ['intelligent', 'flexible', 'multi_provider'],
                'providers': ['ollama', 'openai', 'anthropic'],
            },
            'structured': {
                'name': 'Structured Data',
                'description': 'Extract structured data (JSON-LD, Microdata, etc.)',
                'supports': ['html', 'json'],
                'features': ['json_ld', 'microdata', 'opengraph', 'schema_org'],
            },
            'jsonpath': {
                'name': 'JSONPath',
                'description': 'Extract data from JSON using JSONPath',
                'supports': ['json'],
                'features': ['path_expressions', 'nested_data'],
            },
        }
