"""
Data Transformer

This module provides data transformation utilities for converting and
transforming extracted data based on template transformation rules.
"""

import re
import logging
from typing import Any, Optional, Dict, List, Callable
import pandas as pd

logger = logging.getLogger(__name__)


class DataTransformer:
    """
    Data transformation utilities

    Provides methods for transforming data values based on rules defined in templates.
    """

    # Built-in transformations registry
    TRANSFORMATIONS: Dict[str, Callable] = {}

    @classmethod
    def register_transformation(cls, name: str):
        """
        Decorator to register a transformation function

        Args:
            name: Name of the transformation
        """
        def decorator(func: Callable):
            cls.TRANSFORMATIONS[name] = func
            return func
        return decorator

    @staticmethod
    def apply_transformation(value: Any, transformation: str) -> Any:
        """
        Apply a transformation to a value

        Args:
            value: Value to transform
            transformation: Name of transformation to apply

        Returns:
            Transformed value
        """
        if value is None or pd.isna(value):
            return value

        transformation_func = DataTransformer.TRANSFORMATIONS.get(transformation)

        if transformation_func:
            try:
                return transformation_func(value)
            except Exception as e:
                logger.warning(
                    f"Error applying transformation '{transformation}': {str(e)}"
                )
                return value
        else:
            logger.warning(f"Unknown transformation: {transformation}")
            return value

    @staticmethod
    def apply_transformations_to_dataframe(
        df: pd.DataFrame,
        field_transformations: Dict[str, str]
    ) -> pd.DataFrame:
        """
        Apply transformations to DataFrame columns

        Args:
            df: DataFrame to transform
            field_transformations: Dictionary mapping field names to transformation names

        Returns:
            Transformed DataFrame
        """
        df_transformed = df.copy()

        for field_name, transformation in field_transformations.items():
            if field_name in df_transformed.columns:
                df_transformed[field_name] = df_transformed[field_name].apply(
                    lambda x: DataTransformer.apply_transformation(x, transformation)
                )

        return df_transformed


# ============================================================================
# Built-in Transformations
# ============================================================================

@DataTransformer.register_transformation("to_lowercase")
def to_lowercase(value: Any) -> str:
    """Convert value to lowercase"""
    return str(value).lower() if value is not None else value


@DataTransformer.register_transformation("to_uppercase")
def to_uppercase(value: Any) -> str:
    """Convert value to uppercase"""
    return str(value).upper() if value is not None else value


@DataTransformer.register_transformation("to_titlecase")
def to_titlecase(value: Any) -> str:
    """Convert value to title case"""
    return str(value).title() if value is not None else value


@DataTransformer.register_transformation("strip")
def strip_whitespace(value: Any) -> str:
    """Strip leading/trailing whitespace"""
    return str(value).strip() if value is not None else value


@DataTransformer.register_transformation("extract_number")
def extract_number(value: Any) -> Optional[float]:
    """
    Extract first number from string

    Examples:
        "Price: $1,234.56" -> 1234.56
        "123 Main St" -> 123.0
    """
    if value is None or pd.isna(value):
        return None

    # Remove common currency symbols and commas
    text = str(value)
    text = re.sub(r'[$€£¥,]', '', text)

    # Extract first number (including decimals)
    match = re.search(r'-?\d+\.?\d*', text)

    if match:
        try:
            return float(match.group())
        except ValueError:
            return None

    return None


@DataTransformer.register_transformation("extract_integer")
def extract_integer(value: Any) -> Optional[int]:
    """Extract first integer from string"""
    number = extract_number(value)
    return int(number) if number is not None else None


@DataTransformer.register_transformation("remove_punctuation")
def remove_punctuation(value: Any) -> str:
    """Remove punctuation from string"""
    if value is None or pd.isna(value):
        return value

    return re.sub(r'[^\w\s]', '', str(value))


@DataTransformer.register_transformation("remove_digits")
def remove_digits(value: Any) -> str:
    """Remove digits from string"""
    if value is None or pd.isna(value):
        return value

    return re.sub(r'\d+', '', str(value))


@DataTransformer.register_transformation("extract_domain")
def extract_domain(value: Any) -> Optional[str]:
    """
    Extract domain from URL

    Example:
        "https://www.example.com/path" -> "example.com"
    """
    if value is None or pd.isna(value):
        return None

    # Extract domain from URL
    match = re.search(r'https?://(?:www\.)?([^/]+)', str(value))

    if match:
        return match.group(1)

    return value


@DataTransformer.register_transformation("boolean")
def to_boolean(value: Any) -> Optional[bool]:
    """
    Convert value to boolean

    Recognizes: yes/no, true/false, 1/0, y/n
    """
    if value is None or pd.isna(value):
        return None

    value_str = str(value).lower().strip()

    true_values = ['yes', 'true', '1', 'y', 't']
    false_values = ['no', 'false', '0', 'n', 'f']

    if value_str in true_values:
        return True
    elif value_str in false_values:
        return False

    return None


@DataTransformer.register_transformation("truncate_50")
def truncate_50(value: Any) -> str:
    """Truncate string to 50 characters"""
    if value is None or pd.isna(value):
        return value

    text = str(value)
    return text[:50] + '...' if len(text) > 50 else text


@DataTransformer.register_transformation("truncate_100")
def truncate_100(value: Any) -> str:
    """Truncate string to 100 characters"""
    if value is None or pd.isna(value):
        return value

    text = str(value)
    return text[:100] + '...' if len(text) > 100 else text


@DataTransformer.register_transformation("first_word")
def first_word(value: Any) -> Optional[str]:
    """Extract first word from string"""
    if value is None or pd.isna(value):
        return None

    words = str(value).split()
    return words[0] if words else None


@DataTransformer.register_transformation("last_word")
def last_word(value: Any) -> Optional[str]:
    """Extract last word from string"""
    if value is None or pd.isna(value):
        return None

    words = str(value).split()
    return words[-1] if words else None


@DataTransformer.register_transformation("reverse")
def reverse_string(value: Any) -> str:
    """Reverse string"""
    if value is None or pd.isna(value):
        return value

    return str(value)[::-1]


@DataTransformer.register_transformation("remove_html")
def remove_html(value: Any) -> str:
    """Remove HTML tags"""
    if value is None or pd.isna(value):
        return value

    from bs4 import BeautifulSoup
    return BeautifulSoup(str(value), 'html.parser').get_text()


@DataTransformer.register_transformation("url_encode")
def url_encode(value: Any) -> str:
    """URL encode string"""
    if value is None or pd.isna(value):
        return value

    from urllib.parse import quote
    return quote(str(value))


@DataTransformer.register_transformation("slugify")
def slugify(value: Any) -> str:
    """
    Convert string to URL-friendly slug

    Example:
        "Hello World!" -> "hello-world"
    """
    if value is None or pd.isna(value):
        return value

    text = str(value).lower()

    # Remove special characters
    text = re.sub(r'[^\w\s-]', '', text)

    # Replace whitespace with hyphens
    text = re.sub(r'[\s_]+', '-', text)

    # Remove leading/trailing hyphens
    text = text.strip('-')

    return text


# Export
__all__ = ['DataTransformer']
