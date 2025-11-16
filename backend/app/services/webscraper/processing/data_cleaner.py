"""
Data Cleaner

This module provides data cleaning utilities for web-scraped content.
It handles HTML removal, whitespace normalization, date standardization, and more.
"""

import re
import logging
from typing import List, Optional, Any
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd

logger = logging.getLogger(__name__)


class DataCleaner:
    """
    Data cleaning utilities for scraped content

    Provides methods for cleaning and normalizing data extracted from web pages.
    """

    @staticmethod
    def remove_html_tags(text: str) -> str:
        """
        Remove HTML tags from text

        Args:
            text: Text potentially containing HTML

        Returns:
            Plain text without HTML tags
        """
        if not text or not isinstance(text, str):
            return text

        try:
            soup = BeautifulSoup(text, 'html.parser')
            return soup.get_text()
        except Exception as e:
            logger.warning(f"Error removing HTML tags: {str(e)}")
            return text

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """
        Normalize whitespace in text

        - Removes leading/trailing whitespace
        - Collapses multiple spaces into one
        - Removes excessive newlines

        Args:
            text: Text with irregular whitespace

        Returns:
            Text with normalized whitespace
        """
        if not text or not isinstance(text, str):
            return text

        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    @staticmethod
    def remove_urls(text: str) -> str:
        """
        Remove URLs from text

        Args:
            text: Text potentially containing URLs

        Returns:
            Text without URLs
        """
        if not text or not isinstance(text, str):
            return text

        # Remove URLs
        url_pattern = r'https?://\S+|www\.\S+'
        text = re.sub(url_pattern, '', text)

        return DataCleaner.normalize_whitespace(text)

    @staticmethod
    def remove_emails(text: str) -> str:
        """
        Remove email addresses from text

        Args:
            text: Text potentially containing emails

        Returns:
            Text without email addresses
        """
        if not text or not isinstance(text, str):
            return text

        # Remove email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        text = re.sub(email_pattern, '', text)

        return DataCleaner.normalize_whitespace(text)

    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """
        Extract email addresses from text

        Args:
            text: Text potentially containing emails

        Returns:
            List of email addresses found
        """
        if not text or not isinstance(text, str):
            return []

        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(email_pattern, text, re.IGNORECASE)

    @staticmethod
    def extract_phone_numbers(text: str, country: str = "US") -> List[str]:
        """
        Extract phone numbers from text

        Args:
            text: Text potentially containing phone numbers
            country: Country code for phone number format

        Returns:
            List of phone numbers found
        """
        if not text or not isinstance(text, str):
            return []

        # Simple US phone number pattern
        # Matches: (123) 456-7890, 123-456-7890, 1234567890
        phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        return re.findall(phone_pattern, text)

    @staticmethod
    def extract_numbers(text: str) -> List[float]:
        """
        Extract numbers from text

        Args:
            text: Text containing numbers

        Returns:
            List of numbers found
        """
        if not text or not isinstance(text, str):
            return []

        # Pattern for numbers (including decimals and negatives)
        number_pattern = r'-?\d+\.?\d*'
        matches = re.findall(number_pattern, text)

        # Convert to float
        numbers = []
        for match in matches:
            try:
                numbers.append(float(match))
            except ValueError:
                continue

        return numbers

    @staticmethod
    def parse_number(text: str, locale: str = "en_US") -> Optional[float]:
        """
        Parse numbers with locale support

        Handles different number formats:
        - US: 1,234.56
        - EU: 1.234,56

        Args:
            text: Text containing a number
            locale: Locale for number format

        Returns:
            Parsed number or None
        """
        if not text or not isinstance(text, str):
            return None

        try:
            # Remove currency symbols
            text = re.sub(r'[$€£¥]', '', text)

            # Handle different locales
            if locale.startswith("en"):
                # US/UK format: 1,234.56
                text = text.replace(',', '')
            else:
                # EU format: 1.234,56
                text = text.replace('.', '').replace(',', '.')

            return float(text)
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def standardize_dates(
        date_str: str,
        output_format: str = "%Y-%m-%d"
    ) -> Optional[str]:
        """
        Standardize date formats

        Auto-detects common date formats and converts to standard format

        Args:
            date_str: Date string in various formats
            output_format: Desired output format (strftime format)

        Returns:
            Standardized date string or None
        """
        if not date_str or not isinstance(date_str, str):
            return None

        # Common date formats to try
        formats = [
            "%Y-%m-%d",           # 2024-01-15
            "%d/%m/%Y",           # 15/01/2024
            "%m/%d/%Y",           # 01/15/2024
            "%Y/%m/%d",           # 2024/01/15
            "%d-%m-%Y",           # 15-01-2024
            "%m-%d-%Y",           # 01-15-2024
            "%B %d, %Y",          # January 15, 2024
            "%b %d, %Y",          # Jan 15, 2024
            "%d %B %Y",           # 15 January 2024
            "%d %b %Y",           # 15 Jan 2024
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime(output_format)
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None

    @staticmethod
    def clean_dataframe(
        df: pd.DataFrame,
        remove_html: bool = True,
        normalize_whitespace: bool = True,
        standardize_dates: bool = False
    ) -> pd.DataFrame:
        """
        Clean an entire DataFrame

        Args:
            df: DataFrame to clean
            remove_html: Whether to remove HTML tags
            normalize_whitespace: Whether to normalize whitespace
            standardize_dates: Whether to standardize date columns

        Returns:
            Cleaned DataFrame
        """
        df_cleaned = df.copy()

        # Process string columns
        for col in df_cleaned.select_dtypes(include=['object']).columns:
            if remove_html:
                df_cleaned[col] = df_cleaned[col].apply(
                    lambda x: DataCleaner.remove_html_tags(x) if pd.notna(x) else x
                )

            if normalize_whitespace:
                df_cleaned[col] = df_cleaned[col].apply(
                    lambda x: DataCleaner.normalize_whitespace(x) if pd.notna(x) else x
                )

            # Try to detect and standardize dates
            if standardize_dates and DataCleaner._looks_like_date_column(df_cleaned[col]):
                df_cleaned[col] = df_cleaned[col].apply(
                    lambda x: DataCleaner.standardize_dates(x) if pd.notna(x) else x
                )

        return df_cleaned

    @staticmethod
    def _looks_like_date_column(series: pd.Series) -> bool:
        """
        Check if a column looks like it contains dates

        Args:
            series: Pandas Series to check

        Returns:
            True if column appears to contain dates
        """
        # Sample first few non-null values
        sample = series.dropna().head(10)

        if len(sample) == 0:
            return False

        # Check if values contain common date patterns
        date_indicators = ['-', '/', 'jan', 'feb', 'mar', 'apr', 'may', 'jun',
                          'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

        matching_count = 0
        for value in sample:
            value_lower = str(value).lower()
            if any(indicator in value_lower for indicator in date_indicators):
                matching_count += 1

        # If more than 50% of samples look like dates
        return (matching_count / len(sample)) > 0.5

    @staticmethod
    def remove_duplicates_preserve_order(items: List[Any]) -> List[Any]:
        """
        Remove duplicates from list while preserving order

        Args:
            items: List potentially containing duplicates

        Returns:
            List without duplicates, original order preserved
        """
        seen = set()
        result = []

        for item in items:
            # Use string representation for hashability
            item_key = str(item)
            if item_key not in seen:
                seen.add(item_key)
                result.append(item)

        return result


# Export
__all__ = ['DataCleaner']
