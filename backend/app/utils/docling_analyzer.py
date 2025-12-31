"""
Docling PDF Analyzer Utility

Uses Docling to analyze PDF files for structure complexity.
Extracts:
- Page count
- Tables
- Images
- Forms
- Layout complexity

Author: Claude Code
Date: 2025-11-25
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


async def analyze_pdf_complexity(pdf_path: str) -> Dict[str, Any]:
    """
    Analyze PDF structure and complexity using Docling.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Dictionary with PDF complexity metrics
    """
    try:
        # Import Docling
        from docling.document_converter import DocumentConverter

        # Create converter
        converter = DocumentConverter()

        # Convert PDF
        result = converter.convert(pdf_path)

        # Extract metrics
        page_count = len(result.pages) if hasattr(result, 'pages') else 0

        # Count tables
        table_count = 0
        if hasattr(result, 'tables'):
            table_count = len(result.tables)

        # Count images
        image_count = 0
        if hasattr(result, 'pictures'):
            image_count = len(result.pictures)

        # Check for forms
        has_forms = False
        if hasattr(result, 'document') and hasattr(result.document, 'form'):
            has_forms = result.document.form is not None

        # Calculate layout complexity score (1-10)
        structure_score = _calculate_structure_score(
            page_count,
            table_count,
            image_count,
            has_forms
        )

        # Calculate text density (words per page)
        word_count = 0
        if hasattr(result, 'document') and hasattr(result.document, 'text'):
            word_count = len(result.document.text.split())

        text_density = word_count / page_count if page_count > 0 else 0

        return {
            "page_count": page_count,
            "has_tables": table_count > 0,
            "table_count": table_count,
            "has_images": image_count > 0,
            "image_count": image_count,
            "has_forms": has_forms,
            "layout_complexity": "High" if structure_score >= 7 else "Medium" if structure_score >= 4 else "Low",
            "text_density": round(text_density, 2),
            "structure_score": structure_score
        }

    except ImportError:
        logger.error("Docling not installed. Install with: pip install docling")
        return _get_fallback_pdf_analysis(pdf_path)

    except Exception as e:
        logger.error(f"Error analyzing PDF with Docling: {e}", exc_info=True)
        return _get_fallback_pdf_analysis(pdf_path)


def _calculate_structure_score(
    page_count: int,
    table_count: int,
    image_count: int,
    has_forms: bool
) -> float:
    """
    Calculate PDF structure complexity score (1-10).

    Factors:
    - Page count (up to 3 points)
    - Table presence (up to 2.5 points)
    - Image presence (up to 2 points)
    - Form presence (up to 2.5 points)
    """
    score = 1.0  # Base score

    # Page count contribution (0-3 points)
    if page_count <= 5:
        score += 0.5
    elif page_count <= 20:
        score += 1.5
    elif page_count <= 50:
        score += 2.5
    else:
        score += 3.0

    # Table contribution (0-2.5 points)
    if table_count > 0:
        if table_count <= 3:
            score += 1.0
        elif table_count <= 10:
            score += 1.5
        else:
            score += 2.5

    # Image contribution (0-2 points)
    if image_count > 0:
        if image_count <= 5:
            score += 0.8
        elif image_count <= 15:
            score += 1.2
        else:
            score += 2.0

    # Form contribution (0-2.5 points)
    if has_forms:
        score += 2.5

    return min(score, 10.0)


def _get_fallback_pdf_analysis(pdf_path: str) -> Dict[str, Any]:
    """
    Fallback PDF analysis using PyPDF2 when Docling is unavailable.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Dictionary with basic PDF metrics
    """
    try:
        import PyPDF2

        with open(pdf_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            page_count = len(reader.pages)

            # Estimate complexity based on page count alone
            if page_count <= 10:
                structure_score = 2.0
            elif page_count <= 30:
                structure_score = 5.0
            else:
                structure_score = 7.0

            return {
                "page_count": page_count,
                "has_tables": False,  # Unknown
                "table_count": 0,
                "has_images": False,  # Unknown
                "image_count": 0,
                "has_forms": False,
                "layout_complexity": "Unknown",
                "text_density": 0,
                "structure_score": structure_score
            }

    except Exception as e:
        logger.error(f"Fallback PDF analysis failed: {e}")
        return {
            "page_count": 0,
            "has_tables": False,
            "table_count": 0,
            "has_images": False,
            "image_count": 0,
            "has_forms": False,
            "layout_complexity": "Unknown",
            "text_density": 0,
            "structure_score": 5.0  # Default medium complexity
        }
