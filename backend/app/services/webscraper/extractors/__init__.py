"""
Extractors Package - Data extraction from various sources

This package provides multiple extraction strategies:
- CSS selectors
- XPath expressions
- Regular expressions
- LLM-powered extraction
- Structured data (JSON, XML, JSON-LD, Microdata, OpenGraph)
"""

from .css_extractor import CSSExtractor
from .xpath_extractor import XPathExtractor
from .regex_extractor import RegexExtractor
from .llm_extractor import LLMExtractor
from .structured_extractor import StructuredExtractor
from .extractor_factory import ExtractorFactory

__all__ = [
    'CSSExtractor',
    'XPathExtractor',
    'RegexExtractor',
    'LLMExtractor',
    'StructuredExtractor',
    'ExtractorFactory',
]
