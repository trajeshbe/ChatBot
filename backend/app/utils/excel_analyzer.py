"""
Excel Complexity Analyzer Utility

Uses openpyxl and pandas to analyze Excel files for complexity.
Extracts:
- Formula density
- Pivot tables
- Macros
- Sheet count
- Processing difficulty

Author: Claude Code
Date: 2025-11-25
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


async def analyze_excel_complexity(excel_path: str) -> Dict[str, Any]:
    """
    Analyze Excel file complexity - formulas, pivots, macros.

    Args:
        excel_path: Path to Excel file

    Returns:
        Dictionary with Excel complexity metrics
    """
    try:
        import openpyxl

        # Load workbook
        wb = openpyxl.load_workbook(excel_path, data_only=False)

        formula_count = 0
        cell_count = 0
        has_pivot = False
        has_macros = wb.vba_archive is not None

        # Analyze each sheet
        for sheet in wb.worksheets:
            # Count cells and formulas
            for row in sheet.iter_rows():
                for cell in row:
                    cell_count += 1
                    if cell.value and isinstance(cell.value, str):
                        if cell.value.startswith('='):
                            formula_count += 1

            # Check for pivot tables
            if hasattr(sheet, '_pivots') and sheet._pivots:
                has_pivot = True

        # Calculate formula density
        formula_density = formula_count / cell_count if cell_count > 0 else 0.0

        # Calculate complexity score (1-10)
        complexity_score = _calculate_excel_score(
            len(wb.worksheets),
            formula_density,
            has_pivot,
            has_macros
        )

        return {
            "sheet_count": len(wb.worksheets),
            "total_cells": cell_count,
            "formula_count": formula_count,
            "formula_density": formula_density,
            "has_pivot_tables": has_pivot,
            "has_macros": has_macros,
            "complexity_score": complexity_score
        }

    except ImportError:
        logger.error("openpyxl not installed. Install with: pip install openpyxl")
        return _get_fallback_excel_analysis(excel_path)

    except Exception as e:
        logger.error(f"Error analyzing Excel file: {e}", exc_info=True)
        return _get_fallback_excel_analysis(excel_path)


def _calculate_excel_score(
    sheet_count: int,
    formula_density: float,
    has_pivot: bool,
    has_macros: bool
) -> float:
    """
    Calculate Excel complexity score (1-10).

    Factors:
    - Sheet count (up to 2 points)
    - Formula density (up to 4 points)
    - Pivot tables (up to 2 points)
    - Macros (up to 2 points)
    """
    score = 1.0  # Base score

    # Sheet count contribution (0-2 points)
    if sheet_count <= 2:
        score += 0.5
    elif sheet_count <= 5:
        score += 1.0
    elif sheet_count <= 10:
        score += 1.5
    else:
        score += 2.0

    # Formula density contribution (0-4 points)
    if formula_density < 0.05:  # < 5% formulas
        score += 0.5
    elif formula_density < 0.15:  # 5-15%
        score += 1.5
    elif formula_density < 0.30:  # 15-30%
        score += 2.5
    else:  # > 30%
        score += 4.0

    # Pivot table contribution (0-2 points)
    if has_pivot:
        score += 2.0

    # Macro contribution (0-2 points)
    if has_macros:
        score += 2.0

    return min(score, 10.0)


def _get_fallback_excel_analysis(excel_path: str) -> Dict[str, Any]:
    """
    Fallback Excel analysis using pandas when openpyxl is unavailable.

    Args:
        excel_path: Path to Excel file

    Returns:
        Dictionary with basic Excel metrics
    """
    try:
        import pandas as pd

        # Read Excel file
        xl_file = pd.ExcelFile(excel_path)
        sheet_count = len(xl_file.sheet_names)

        # Estimate complexity based on sheet count alone
        if sheet_count <= 2:
            complexity_score = 2.0
        elif sheet_count <= 5:
            complexity_score = 5.0
        else:
            complexity_score = 7.0

        return {
            "sheet_count": sheet_count,
            "total_cells": 0,  # Unknown
            "formula_count": 0,  # Unknown
            "formula_density": 0.0,  # Unknown
            "has_pivot_tables": False,  # Unknown
            "has_macros": False,  # Unknown
            "complexity_score": complexity_score
        }

    except Exception as e:
        logger.error(f"Fallback Excel analysis failed: {e}")
        return {
            "sheet_count": 1,
            "total_cells": 0,
            "formula_count": 0,
            "formula_density": 0.0,
            "has_pivot_tables": False,
            "has_macros": False,
            "complexity_score": 5.0  # Default medium complexity
        }
