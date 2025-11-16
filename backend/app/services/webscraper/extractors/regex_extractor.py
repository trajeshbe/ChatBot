"""
Regex Extractor - Extract data using regular expressions

This module provides regex-based pattern extraction from text content.
"""

from typing import List, Optional, Union, Pattern
import re
import logging

logger = logging.getLogger(__name__)


class RegexExtractor:
    """
    Extract data from text using regular expressions

    Features:
    - Single and multiple pattern matching
    - Capture group extraction
    - Named group support
    - Common pattern library (emails, phones, URLs, etc.)
    """

    def __init__(self):
        self.logger = logger

        # Common regex patterns
        self.common_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'url': r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)',
            'phone_us': r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            'phone_intl': r'\+?[1-9]\d{1,14}',
            'ssn': r'\d{3}-\d{2}-\d{4}',
            'zip_code': r'\d{5}(?:-\d{4})?',
            'credit_card': r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}',
            'ipv4': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'date_iso': r'\d{4}-\d{2}-\d{2}',
            'date_us': r'\d{1,2}/\d{1,2}/\d{2,4}',
            'time': r'\d{1,2}:\d{2}(?::\d{2})?(?:\s?[AP]M)?',
            'currency_usd': r'\$\s?\d+(?:,\d{3})*(?:\.\d{2})?',
            'number': r'-?\d+(?:\.\d+)?',
            'integer': r'-?\d+',
            'hex_color': r'#[0-9A-Fa-f]{6}',
        }

    def extract(
        self,
        text: str,
        pattern: str,
        group: int = 0,
        multiple: bool = False,
        join_with: Optional[str] = None,
        flags: int = 0
    ) -> Optional[Union[str, List[str]]]:
        """
        Extract data using regex pattern

        Args:
            text: Text content to search
            pattern: Regex pattern
            group: Capture group index (0 = full match)
            multiple: Whether to find all matches
            join_with: If multiple=True, join results with this separator
            flags: Regex flags (e.g., re.IGNORECASE)

        Returns:
            Extracted text, or None if not found
        """
        try:
            compiled_pattern = re.compile(pattern, flags)

            if multiple:
                matches = compiled_pattern.findall(text)
                if not matches:
                    return None

                # Handle tuple results from multiple groups
                if matches and isinstance(matches[0], tuple):
                    # If group specified, extract that group from each match
                    if group < len(matches[0]):
                        results = [match[group] for match in matches if match[group]]
                    else:
                        results = [match[0] for match in matches if match[0]]
                else:
                    results = matches

                if not results:
                    return None

                if join_with is not None:
                    return join_with.join(str(r) for r in results)
                return results
            else:
                match = compiled_pattern.search(text)
                if not match:
                    return None

                # Extract specified group
                if group == 0:
                    return match.group(0)
                elif group <= match.lastindex if match.lastindex else 0:
                    return match.group(group)
                else:
                    self.logger.warning(
                        f"Group {group} not found in match (max: {match.lastindex})"
                    )
                    return match.group(0)

        except Exception as e:
            self.logger.error(f"Regex extraction failed: {str(e)}")
            return None

    def extract_named_groups(
        self,
        text: str,
        pattern: str,
        multiple: bool = False
    ) -> Optional[Union[dict, List[dict]]]:
        """
        Extract named capture groups as dictionary

        Args:
            text: Text content to search
            pattern: Regex pattern with named groups
            multiple: Whether to find all matches

        Returns:
            Dictionary of named groups, or list of dictionaries if multiple
        """
        try:
            compiled_pattern = re.compile(pattern)

            if multiple:
                results = []
                for match in compiled_pattern.finditer(text):
                    groups = match.groupdict()
                    if groups:
                        results.append(groups)
                return results if results else None
            else:
                match = compiled_pattern.search(text)
                if not match:
                    return None
                return match.groupdict()

        except Exception as e:
            self.logger.error(f"Named group extraction failed: {str(e)}")
            return None

    def extract_common(
        self,
        text: str,
        pattern_name: str,
        multiple: bool = True
    ) -> Optional[Union[str, List[str]]]:
        """
        Extract using common predefined pattern

        Args:
            text: Text content to search
            pattern_name: Name of common pattern (e.g., 'email', 'phone_us')
            multiple: Whether to find all matches

        Returns:
            Extracted matches, or None if not found
        """
        if pattern_name not in self.common_patterns:
            self.logger.error(
                f"Unknown pattern: {pattern_name}. "
                f"Available: {', '.join(self.common_patterns.keys())}"
            )
            return None

        pattern = self.common_patterns[pattern_name]
        return self.extract(text, pattern, multiple=multiple)

    def extract_emails(self, text: str) -> Optional[List[str]]:
        """Extract all email addresses"""
        return self.extract_common(text, 'email', multiple=True)

    def extract_urls(self, text: str) -> Optional[List[str]]:
        """Extract all URLs"""
        return self.extract_common(text, 'url', multiple=True)

    def extract_phone_numbers(
        self,
        text: str,
        format: str = 'us'
    ) -> Optional[List[str]]:
        """
        Extract phone numbers

        Args:
            text: Text content
            format: Phone format ('us' or 'intl')

        Returns:
            List of phone numbers
        """
        pattern_name = f'phone_{format}'
        if pattern_name not in self.common_patterns:
            pattern_name = 'phone_us'

        return self.extract_common(text, pattern_name, multiple=True)

    def extract_numbers(
        self,
        text: str,
        integer_only: bool = False
    ) -> Optional[List[str]]:
        """
        Extract numbers from text

        Args:
            text: Text content
            integer_only: Whether to extract integers only (vs floats)

        Returns:
            List of numbers as strings
        """
        pattern_name = 'integer' if integer_only else 'number'
        return self.extract_common(text, pattern_name, multiple=True)

    def extract_dates(
        self,
        text: str,
        format: str = 'iso'
    ) -> Optional[List[str]]:
        """
        Extract dates

        Args:
            text: Text content
            format: Date format ('iso', 'us')

        Returns:
            List of dates
        """
        pattern_name = f'date_{format}'
        if pattern_name not in self.common_patterns:
            pattern_name = 'date_iso'

        return self.extract_common(text, pattern_name, multiple=True)

    def extract_currency(
        self,
        text: str,
        currency: str = 'usd'
    ) -> Optional[List[str]]:
        """
        Extract currency amounts

        Args:
            text: Text content
            currency: Currency code (e.g., 'usd')

        Returns:
            List of currency amounts
        """
        pattern_name = f'currency_{currency}'
        if pattern_name not in self.common_patterns:
            # Try generic number pattern
            return self.extract_numbers(text)

        return self.extract_common(text, pattern_name, multiple=True)

    def extract_with_context(
        self,
        text: str,
        pattern: str,
        before_chars: int = 50,
        after_chars: int = 50
    ) -> Optional[List[dict]]:
        """
        Extract matches with surrounding context

        Args:
            text: Text content
            pattern: Regex pattern
            before_chars: Number of characters to include before match
            after_chars: Number of characters to include after match

        Returns:
            List of dictionaries with 'match', 'before', 'after' keys
        """
        try:
            compiled_pattern = re.compile(pattern)
            results = []

            for match in compiled_pattern.finditer(text):
                start = match.start()
                end = match.end()

                before_start = max(0, start - before_chars)
                after_end = min(len(text), end + after_chars)

                results.append({
                    'match': match.group(0),
                    'before': text[before_start:start],
                    'after': text[end:after_end],
                    'start': start,
                    'end': end
                })

            return results if results else None

        except Exception as e:
            self.logger.error(f"Context extraction failed: {str(e)}")
            return None

    def replace(
        self,
        text: str,
        pattern: str,
        replacement: str,
        count: int = 0
    ) -> str:
        """
        Replace pattern in text

        Args:
            text: Text content
            pattern: Regex pattern
            replacement: Replacement string
            count: Maximum replacements (0 = all)

        Returns:
            Text with replacements
        """
        try:
            return re.sub(pattern, replacement, text, count=count)
        except Exception as e:
            self.logger.error(f"Regex replacement failed: {str(e)}")
            return text
