"""
Grant Thornton Calculation Engine

Evaluates sub-calculations and financial ratios using extracted datapoints.

Two-stage calculation:
1. Sub-Calculations: Intermediate values (e.g., average_total_equity)
2. Financial Ratios: Final metrics (e.g., ROE, debt_to_equity)

Uses Python eval() for formula evaluation with safe namespace.

Author: Claude Code
Date: 2026-01-01
"""

import logging
from typing import Dict, Any, List, Optional
import re

from app.schemas.grant_thornton_schemas import (
    ExtractedDatapoint,
    SubCalculationFormula,
    RatioFormula,
    FinancialRatios
)
from .config import load_formulas, load_config

logger = logging.getLogger(__name__)


class CalculationEngine:
    """
    Engine for evaluating financial calculations.

    Features:
    - Safe eval() with controlled namespace
    - Error handling (ZeroDivisionError, NameError, etc.)
    - Formula normalization (already done in config.py)
    - Dependency resolution (sub-calculations before ratios)
    """

    def __init__(self):
        self.config = load_config()
        self._initialized = False

    async def initialize(self):
        """Initialize calculation engine"""
        if self._initialized:
            return

        logger.info("✅ Calculation engine ready")
        self._initialized = True

    def _create_namespace(
        self,
        datapoints: List[ExtractedDatapoint],
        sub_calculations: Optional[List[SubCalculationFormula]] = None
    ) -> Dict[str, float]:
        """
        Create namespace for eval() with all extracted values.

        Args:
            datapoints: List of extracted datapoints
            sub_calculations: Optional list of calculated sub-calculations

        Returns:
            Dictionary mapping variable names to values
        """
        namespace = {}

        # Add extracted datapoints
        for datapoint in datapoints:
            var_name = datapoint.cleaned_field_name
            namespace[var_name] = float(datapoint.value)

        # Add sub-calculations (if provided)
        if sub_calculations:
            for sub_calc in sub_calculations:
                if sub_calc.calculation_status == "success" and sub_calc.calculated_value is not None:
                    var_name = sub_calc.cleaned_sub_field
                    namespace[var_name] = float(sub_calc.calculated_value)

        logger.debug(f"Created namespace with {len(namespace)} variables")
        return namespace

    def _safe_eval(
        self,
        formula: str,
        namespace: Dict[str, float]
    ) -> Optional[float]:
        """
        Safely evaluate formula using eval().

        Args:
            formula: Normalized formula string
            namespace: Dictionary of variable name → value

        Returns:
            Calculated value or None on error
        """
        try:
            # Evaluate formula in controlled namespace
            result = eval(formula, {"__builtins__": {}}, namespace)

            # Ensure result is numeric
            if isinstance(result, (int, float)):
                return float(result)
            else:
                logger.warning(f"Formula returned non-numeric result: {type(result)}")
                return None

        except ZeroDivisionError:
            logger.debug(f"Division by zero in formula: {formula}")
            return 0.0  # Return 0 for division by zero (per GT spec)

        except NameError as e:
            logger.warning(f"Missing variable in formula '{formula}': {e}")
            return None

        except Exception as e:
            logger.error(f"Error evaluating formula '{formula}': {e}")
            return None

    async def calculate_sub_calculations(
        self,
        datapoints: List[ExtractedDatapoint],
        formulas_excel_path: Optional[str] = None
    ) -> List[SubCalculationFormula]:
        """
        Calculate all sub-calculations from formulas.

        Args:
            datapoints: List of extracted datapoints
            formulas_excel_path: Optional path to calculation_formula.xlsx

        Returns:
            List of SubCalculationFormula with calculated values
        """
        if not self._initialized:
            await self.initialize()

        logger.info("🧮 Calculating sub-calculations...")

        # Load formulas from Excel
        formulas = load_formulas(
            excel_path=formulas_excel_path,
            sheet_name="Additional Formulas",
            formula_type="sub_calculation"
        )

        if not formulas:
            logger.warning("No sub-calculation formulas found")
            return []

        logger.info(f"Loaded {len(formulas)} sub-calculation formulas")

        # Create namespace from datapoints
        namespace = self._create_namespace(datapoints)

        # Calculate each formula
        success_count = 0
        failed_count = 0

        for formula_obj in formulas:
            logger.debug(f"Calculating: {formula_obj.sub_field_name}")

            # Evaluate formula
            result = self._safe_eval(formula_obj.cleaned_formula, namespace)

            if result is not None:
                formula_obj.calculated_value = round(result, 2)
                formula_obj.calculation_status = "success"
                success_count += 1

                # Add to namespace for dependent calculations
                namespace[formula_obj.cleaned_sub_field] = result

                logger.debug(
                    f"✅ {formula_obj.sub_field_name} = {formula_obj.calculated_value}"
                )
            else:
                formula_obj.calculation_status = "failed"
                formula_obj.error_message = "Formula evaluation failed"
                failed_count += 1

                logger.warning(f"❌ Failed: {formula_obj.sub_field_name}")

        logger.info(
            f"✅ Sub-calculations complete: {success_count} success, {failed_count} failed"
        )

        return formulas

    async def calculate_financial_ratios(
        self,
        datapoints: List[ExtractedDatapoint],
        sub_calculations: List[SubCalculationFormula],
        formulas_excel_path: Optional[str] = None
    ) -> FinancialRatios:
        """
        Calculate all financial ratios.

        Args:
            datapoints: List of extracted datapoints
            sub_calculations: List of calculated sub-calculations
            formulas_excel_path: Optional path to final_calculation_formula.xlsx

        Returns:
            FinancialRatios object with all calculated ratios
        """
        if not self._initialized:
            await self.initialize()

        logger.info("📊 Calculating financial ratios...")

        # Load ratio formulas from Excel
        formulas = load_formulas(
            excel_path=formulas_excel_path,
            sheet_name="Ratios",  # FIXED: Changed from "formulas" to "Ratios"
            formula_type="ratio"
        )

        if not formulas:
            logger.warning("No ratio formulas found")
            return FinancialRatios()

        logger.info(f"Loaded {len(formulas)} ratio formulas")

        # Create namespace with datapoints + sub-calculations
        namespace = self._create_namespace(datapoints, sub_calculations)

        # Calculate each ratio
        ratio_values = {}
        success_count = 0
        failed_count = 0

        for formula_obj in formulas:
            logger.debug(f"Calculating: {formula_obj.ratio_name}")

            # Evaluate formula
            result = self._safe_eval(formula_obj.cleaned_formula, namespace)

            if result is not None:
                formula_obj.value = round(result, 2)
                formula_obj.calculation_status = "success"
                success_count += 1

                # Map to FinancialRatios field
                # Convert "Current Ratio" → "current_ratio"
                field_name = formula_obj.ratio_name.lower().replace(" ", "_").replace("-", "_")
                field_name = re.sub(r'[^\w_]', '', field_name)  # Remove special chars

                ratio_values[field_name] = formula_obj.value

                logger.debug(f"✅ {formula_obj.ratio_name} = {formula_obj.value}")
            else:
                formula_obj.calculation_status = "failed"
                formula_obj.error_message = "Formula evaluation failed"
                failed_count += 1

                logger.warning(f"❌ Failed: {formula_obj.ratio_name}")

        logger.info(
            f"✅ Financial ratios complete: {success_count} success, {failed_count} failed"
        )

        # Create FinancialRatios object
        financial_ratios = FinancialRatios(**ratio_values)

        return financial_ratios

    async def calculate_all(
        self,
        datapoints: List[ExtractedDatapoint],
        sub_calc_excel_path: Optional[str] = None,
        ratio_excel_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate both sub-calculations and financial ratios.

        Args:
            datapoints: List of extracted datapoints
            sub_calc_excel_path: Optional path to calculation_formula.xlsx
            ratio_excel_path: Optional path to final_calculation_formula.xlsx

        Returns:
            Dictionary with sub_calculations and financial_ratios
        """
        if not self._initialized:
            await self.initialize()

        logger.info("🔢 Starting complete calculation pipeline...")

        # Step 1: Calculate sub-calculations
        sub_calculations = await self.calculate_sub_calculations(
            datapoints=datapoints,
            formulas_excel_path=sub_calc_excel_path
        )

        # Step 2: Calculate financial ratios (uses sub-calculations)
        financial_ratios = await self.calculate_financial_ratios(
            datapoints=datapoints,
            sub_calculations=sub_calculations,
            formulas_excel_path=ratio_excel_path
        )

        logger.info("✅ Complete calculation pipeline finished")

        return {
            "sub_calculations": sub_calculations,
            "financial_ratios": financial_ratios
        }


# Singleton instance
_calculation_engine = None


async def get_calculation_engine() -> CalculationEngine:
    """
    Get or create calculation engine singleton.

    Returns:
        Initialized CalculationEngine
    """
    global _calculation_engine

    if _calculation_engine is None:
        _calculation_engine = CalculationEngine()
        await _calculation_engine.initialize()

    return _calculation_engine


# Convenience functions

async def calculate_sub_calculations(
    datapoints: List[ExtractedDatapoint],
    formulas_excel_path: Optional[str] = None
) -> List[SubCalculationFormula]:
    """
    Calculate sub-calculations from extracted datapoints.

    Args:
        datapoints: List of extracted datapoints
        formulas_excel_path: Optional path to Excel file

    Returns:
        List of calculated sub-calculations
    """
    engine = await get_calculation_engine()
    return await engine.calculate_sub_calculations(datapoints, formulas_excel_path)


async def calculate_financial_ratios(
    datapoints: List[ExtractedDatapoint],
    sub_calculations: List[SubCalculationFormula],
    formulas_excel_path: Optional[str] = None
) -> FinancialRatios:
    """
    Calculate financial ratios from datapoints and sub-calculations.

    Args:
        datapoints: List of extracted datapoints
        sub_calculations: List of calculated sub-calculations
        formulas_excel_path: Optional path to Excel file

    Returns:
        FinancialRatios object
    """
    engine = await get_calculation_engine()
    return await engine.calculate_financial_ratios(
        datapoints, sub_calculations, formulas_excel_path
    )


async def calculate_all(
    datapoints: List[ExtractedDatapoint],
    sub_calc_excel_path: Optional[str] = None,
    ratio_excel_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate both sub-calculations and financial ratios.

    Args:
        datapoints: List of extracted datapoints
        sub_calc_excel_path: Optional path to calculation_formula.xlsx
        ratio_excel_path: Optional path to final_calculation_formula.xlsx

    Returns:
        Dictionary with sub_calculations and financial_ratios
    """
    engine = await get_calculation_engine()
    return await engine.calculate_all(datapoints, sub_calc_excel_path, ratio_excel_path)
