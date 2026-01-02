"""
Grant Thornton Configuration Management

Loads configuration from YAML files and Excel artifacts.

Author: Claude Code
Date: 2026-01-01
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
import pandas as pd
from app.schemas.grant_thornton_schemas import (
    GrantThorntonConfig,
    ExtractedDatapoint,
    SubCalculationFormula,
    RatioFormula
)

logger = logging.getLogger(__name__)


# Default configuration directory
CONFIG_DIR = Path(__file__).parent / "config"
ARTIFACTS_DIR = Path(__file__).parent / "artifacts"


def load_config(config_path: Optional[str] = None) -> GrantThorntonConfig:
    """
    Load Grant Thornton configuration from YAML.

    Args:
        config_path: Path to config.yaml (optional, uses default if None)

    Returns:
        GrantThorntonConfig object
    """
    if config_path is None:
        config_path = CONFIG_DIR / "config.yaml"

    try:
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)

        # Create config object with defaults
        config = GrantThorntonConfig(**config_dict)

        logger.info(f"Loaded configuration from {config_path}")
        return config

    except FileNotFoundError:
        logger.warning(f"Config file not found at {config_path}, using defaults")
        return GrantThorntonConfig()

    except Exception as e:
        logger.error(f"Error loading config: {e}", exc_info=True)
        return GrantThorntonConfig()


def load_datapoints(
    excel_path: Optional[str] = None,
    sheet_name: str = "Prompt"
) -> List[ExtractedDatapoint]:
    """
    Load financial datapoints from Excel artifact.

    Args:
        excel_path: Path to datapoints Excel file
        sheet_name: Excel sheet name

    Returns:
        List of ExtractedDatapoint objects (with values pending)
    """
    if excel_path is None:
        excel_path = ARTIFACTS_DIR / "datapoints_prompt.xlsx"

    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)

        datapoints = []
        for idx, row in df.iterrows():
            # Clean field name (convert to Python variable)
            cleaned_name = clean_field_name(row.get("Fields to be extracted", f"field_{idx}"))

            datapoint = ExtractedDatapoint(
                field_name=row.get("Fields to be extracted", ""),
                cleaned_field_name=cleaned_name,
                definition=row.get("Definition", ""),
                typical_location=row.get("Typical location", None),
                value=0.0,
                page_no=0,
                reference_notes="Not Applicable",
                extraction_status="pending",
                retry_count=0
            )
            datapoints.append(datapoint)

        logger.info(f"Loaded {len(datapoints)} datapoints from {excel_path}")
        return datapoints

    except FileNotFoundError:
        logger.error(f"Datapoints Excel not found: {excel_path}")
        return []

    except Exception as e:
        logger.error(f"Error loading datapoints: {e}", exc_info=True)
        return []


def load_formulas(
    excel_path: Optional[str] = None,
    sheet_name: str = "Additional Formulas",
    formula_type: str = "sub_calculation"
) -> List[Any]:
    """
    Load formulas from Excel artifact.

    Args:
        excel_path: Path to formula Excel file
        sheet_name: Excel sheet name
        formula_type: "sub_calculation" or "ratio"

    Returns:
        List of SubCalculationFormula or RatioFormula objects
    """
    if excel_path is None:
        if formula_type == "sub_calculation":
            excel_path = ARTIFACTS_DIR / "calculation_formula.xlsx"
        else:
            excel_path = ARTIFACTS_DIR / "final_calculation_formula.xlsx"

    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)

        formulas = []

        if formula_type == "sub_calculation":
            for idx, row in df.iterrows():
                formula_str = row.get("Formula", "")
                sub_field_name = row.get("Sub-Field Name", f"calc_{idx}")

                cleaned_formula = normalize_formula(formula_str)
                cleaned_sub_field = clean_field_name(sub_field_name)

                formula_obj = SubCalculationFormula(
                    sub_field_name=sub_field_name,
                    formula=formula_str,
                    cleaned_formula=cleaned_formula,
                    cleaned_sub_field=cleaned_sub_field,
                    calculated_value=None,
                    calculation_status="pending",
                    error_message=None
                )
                formulas.append(formula_obj)

        else:  # ratio
            for idx, row in df.iterrows():
                formula_str = row.get("Formula", "")
                ratio_name = row.get("Ratio Name", f"ratio_{idx}")
                category = row.get("Category", "other")

                cleaned_formula = normalize_formula(formula_str)

                formula_obj = RatioFormula(
                    ratio_name=ratio_name,
                    category=category.lower(),
                    formula=formula_str,
                    cleaned_formula=cleaned_formula,
                    value=None,
                    calculation_status="pending",
                    error_message=None
                )
                formulas.append(formula_obj)

        logger.info(f"Loaded {len(formulas)} {formula_type} formulas from {excel_path}")
        return formulas

    except FileNotFoundError:
        logger.warning(f"Formula Excel not found: {excel_path}")
        return []

    except Exception as e:
        logger.error(f"Error loading formulas: {e}", exc_info=True)
        return []


def clean_field_name(field_name: str) -> str:
    """
    Convert field name to Python-safe variable name.

    Args:
        field_name: Original field name

    Returns:
        Python-safe variable name (lowercase, underscores)

    Examples:
        "Total Assets" -> "total_assets"
        "Debt-to-Equity" -> "debt_to_equity"
        "ROE (%)" -> "roe"
    """
    # Convert to lowercase
    cleaned = field_name.lower()

    # Remove special characters and replace with underscore
    cleaned = cleaned.replace("-", "_")
    cleaned = cleaned.replace(" ", "_")
    cleaned = cleaned.replace(",", "_")
    cleaned = cleaned.replace("(", "")
    cleaned = cleaned.replace(")", "")
    cleaned = cleaned.replace("%", "")
    cleaned = cleaned.replace("/", "_")
    cleaned = cleaned.replace(".", "")

    # Remove multiple underscores
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")

    # Remove leading/trailing underscores
    cleaned = cleaned.strip("_")

    return cleaned


def normalize_formula(formula_str: str) -> str:
    """
    Normalize formula for Python eval().

    Converts special math symbols and multi-word variables to Python-safe format.

    Args:
        formula_str: Original formula string

    Returns:
        Python-evaluable formula string

    Examples:
        "Total Assets ÷ Total Liabilities" -> "total_assets / total_liabilities"
        "(Revenue × 365) / Average Receivables" -> "(revenue * 365) / average_receivables"
    """
    import re

    # Remove special Unicode characters
    formula_str = formula_str.replace("\xa0", " ")  # Non-breaking space
    formula_str = formula_str.replace("\u200b", "")  # Zero-width space

    # Convert math operators FIRST (before variable conversion)
    formula_str = formula_str.replace("÷", " / ")
    formula_str = formula_str.replace("×", " * ")
    formula_str = formula_str.replace("−", " - ")  # Unicode minus

    # Convert multi-word phrases to variables
    # Pattern: matches sequences of letters and spaces only (variable names)
    # Does NOT match operators, parentheses, numbers, or hyphens
    def convert_to_var(match):
        phrase = match.group(0).strip()
        if phrase:  # Only convert non-empty matches
            return clean_field_name(phrase)
        return phrase

    # Match variable names: letter sequences with spaces only
    # Stops at operators (+, -, *, /), parentheses, numbers, and hyphens
    pattern = r'[A-Za-z][A-Za-z\s]*[A-Za-z]|[A-Za-z]'

    formula_str = re.sub(pattern, convert_to_var, formula_str)

    # Clean up extra whitespace around operators
    formula_str = re.sub(r'\s+', ' ', formula_str)  # Multiple spaces → single space
    formula_str = formula_str.replace(' ( ', '(')
    formula_str = formula_str.replace(' ) ', ')')
    formula_str = re.sub(r'\s*([+\-*/])\s*', r' \1 ', formula_str)  # Normalize operator spacing
    formula_str = formula_str.strip()

    return formula_str


def load_prompts(prompts_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load prompts from YAML configuration.

    Args:
        prompts_path: Path to prompts.yaml

    Returns:
        Dictionary with prompt templates
    """
    if prompts_path is None:
        prompts_path = CONFIG_DIR / "prompts.yaml"

    try:
        with open(prompts_path, 'r') as f:
            prompts = yaml.safe_load(f)

        logger.info(f"Loaded prompts from {prompts_path}")
        return prompts

    except FileNotFoundError:
        logger.warning(f"Prompts file not found: {prompts_path}, using defaults")
        return {
            "retriever_prompt": [
                "Standalone Statement of Profit and Loss",
                "standalone Balance sheet",
                "standalone Cash flow statement"
            ],
            "user_prompt": """You are a financial-ratio engine tasked with extracting financial data from annual reports.
Extract the exact numerical value for the requested financial metric."""
        }

    except Exception as e:
        logger.error(f"Error loading prompts: {e}")
        return {}


# ============================================================================
# Configuration File Templates
# ============================================================================

def create_default_configs():
    """
    Create default configuration files if they don't exist.
    """
    # Ensure directories exist
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # Create config.yaml
    config_yaml_path = CONFIG_DIR / "config.yaml"
    if not config_yaml_path.exists():
        default_config = {
            "persist_directory": "vector_store",
            "datapoints_excel_path": "backend/app/services/grant_thornton/artifacts/datapoints_prompt.xlsx",
            "calculation_formula_path": "backend/app/services/grant_thornton/artifacts/calculation_formula.xlsx",
            "ratio_formula_path": "backend/app/services/grant_thornton/artifacts/final_calculation_formula.xlsx",
            "embed_model_name": "BAAI/bge-large-en-v1.5",
            "reranker_model_name": "BAAI/bge-reranker-large",
            "llm_model_name": "gpt-4o-mini",
            "retrieval_top_k": 20,
            "rerank_top_n": 2,
            "initial_context_queries": [
                "Standalone Statement of Profit and Loss",
                "standalone Balance sheet",
                "standalone Cash flow statement"
            ],
            "retry_count": 2,
            "use_gpu": True,
            "header_tags": {
                "#": "#",
                "##": "##",
                "###": "###"
            },
            "mapping_fields": {
                "capital_work-in-progress": "capital_wip",
                "work-in-progress": "wip"
            },
            "sub_calculation_list": [
                "average_total_equity",
                "tangible_net_worth",
                "cash_profit",
                "dso",
                "dio",
                "dpo",
                "average_receivables",
                "average_payables",
                "average_inventory",
                "debt_service",
                "total_bank_borrowings",
                "cash_conversion_cycle"
            ]
        }

        with open(config_yaml_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)

        logger.info(f"Created default config at {config_yaml_path}")

    # Create prompts.yaml
    prompts_yaml_path = CONFIG_DIR / "prompts.yaml"
    if not prompts_yaml_path.exists():
        default_prompts = {
            "retriever_prompt": [
                "Standalone Statement of Profit and Loss",
                "standalone Balance sheet",
                "standalone Cash flow statement"
            ],
            "user_prompt": """You are a financial-ratio engine tasked with extracting financial data from annual reports.

Your role:
1. Search through the provided document context for the requested financial metric
2. Extract the EXACT numerical value
3. Note the page number where you found it
4. Provide brief reference notes about the context

Return your answer in the following JSON format:
{
    "value": <numerical_value>,
    "page_no": <page_number>,
    "reference_notes": "<brief_context>"
}

If you cannot find the value, return:
{
    "value": 0,
    "page_no": 0,
    "reference_notes": "Not Applicable"
}"""
        }

        with open(prompts_yaml_path, 'w') as f:
            yaml.dump(default_prompts, f, default_flow_style=False)

        logger.info(f"Created default prompts at {prompts_yaml_path}")


# Initialize default configs on module import
try:
    create_default_configs()
except Exception as e:
    logger.warning(f"Could not create default configs: {e}")
