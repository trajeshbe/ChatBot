"""
Dataset Preprocessor - Flexible and Extensible

Automatically preprocesses datasets based on training objective.
Supports custom preprocessing pipelines that can be easily extended.

Supported formats:
- QA: Question-Answer pairs
- Classification: Text-Label pairs
- Instruction: Instruction-Response pairs
- Preference: Prompt with chosen/rejected (for RLHF)
- Summarization: Document-Summary pairs
- Chat: OpenAI/Anthropic chat format with messages (role/content pairs)

Extension mechanism:
- Add new objective types by registering preprocessor functions
- Custom formatters can be added via register_formatter()
"""

from typing import Optional, Dict, Any, List, Callable
from abc import ABC, abstractmethod
import logging
import json
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)


class DatasetFormatter(ABC):
    """
    Abstract base class for dataset formatters

    Each training objective has its own formatter that converts
    raw data into the format expected by the model.
    """

    @abstractmethod
    def format(self, example: Dict[str, Any]) -> str:
        """
        Format a single example

        Args:
            example: Raw example from dataset

        Returns:
            Formatted string ready for tokenization
        """
        pass

    @abstractmethod
    def validate(self, example: Dict[str, Any]) -> bool:
        """
        Validate that example has required fields

        Args:
            example: Raw example from dataset

        Returns:
            True if valid, False otherwise
        """
        pass


class QAFormatter(DatasetFormatter):
    """Formatter for Question-Answer datasets"""

    def __init__(self, question_col: str = "question", answer_col: str = "answer"):
        self.question_col = question_col
        self.answer_col = answer_col
        self.template = """### Question:
{question}

### Answer:
{answer}"""

    def format(self, example: Dict[str, Any]) -> str:
        return self.template.format(
            question=example[self.question_col],
            answer=example[self.answer_col]
        )

    def validate(self, example: Dict[str, Any]) -> bool:
        return (
            self.question_col in example and
            self.answer_col in example and
            example[self.question_col] and
            example[self.answer_col]
        )


class ClassificationFormatter(DatasetFormatter):
    """Formatter for Classification datasets"""

    def __init__(
        self,
        text_col: str = "text",
        label_col: str = "label",
        categories: Optional[List[str]] = None
    ):
        self.text_col = text_col
        self.label_col = label_col
        self.categories = categories
        self.template = """### Task:
Classify the following text{categories_str}.

### Text:
{text}

### Classification:
{label}"""

    def format(self, example: Dict[str, Any]) -> str:
        categories_str = ""
        if self.categories:
            categories_str = f" into one of these categories: {', '.join(self.categories)}"

        return self.template.format(
            categories_str=categories_str,
            text=example[self.text_col],
            label=example[self.label_col]
        )

    def validate(self, example: Dict[str, Any]) -> bool:
        return (
            self.text_col in example and
            self.label_col in example and
            example[self.text_col] and
            example[self.label_col]
        )


class InstructionFormatter(DatasetFormatter):
    """Formatter for Instruction-Following datasets (Alpaca/ShareGPT style)"""

    def __init__(
        self,
        instruction_col: str = "instruction",
        response_col: str = "response",
        input_col: Optional[str] = None
    ):
        self.instruction_col = instruction_col
        self.response_col = response_col
        self.input_col = input_col

    def format(self, example: Dict[str, Any]) -> str:
        instruction = example[self.instruction_col]

        # Include input field if present
        if self.input_col and self.input_col in example and example[self.input_col]:
            template = f"""### Instruction:
{instruction}

### Input:
{example[self.input_col]}

### Response:
{example[self.response_col]}"""
        else:
            template = f"""### Instruction:
{instruction}

### Response:
{example[self.response_col]}"""

        return template

    def validate(self, example: Dict[str, Any]) -> bool:
        return (
            self.instruction_col in example and
            self.response_col in example and
            example[self.instruction_col] and
            example[self.response_col]
        )


class SummarizationFormatter(DatasetFormatter):
    """Formatter for Summarization datasets"""

    def __init__(self, document_col: str = "document", summary_col: str = "summary"):
        self.document_col = document_col
        self.summary_col = summary_col
        self.template = """### Document:
{document}

### Summary:
{summary}"""

    def format(self, example: Dict[str, Any]) -> str:
        return self.template.format(
            document=example[self.document_col],
            summary=example[self.summary_col]
        )

    def validate(self, example: Dict[str, Any]) -> bool:
        return (
            self.document_col in example and
            self.summary_col in example and
            example[self.document_col] and
            example[self.summary_col]
        )


class PreferenceFormatter(DatasetFormatter):
    """Formatter for RLHF Preference datasets (chosen/rejected pairs)"""

    def __init__(
        self,
        prompt_col: str = "prompt",
        chosen_col: str = "chosen",
        rejected_col: str = "rejected"
    ):
        self.prompt_col = prompt_col
        self.chosen_col = chosen_col
        self.rejected_col = rejected_col

    def format(self, example: Dict[str, Any]) -> Dict[str, str]:
        """
        For preference datasets, we return a dict instead of string
        because we need both chosen and rejected responses
        """
        return {
            "prompt": example[self.prompt_col],
            "chosen": example[self.chosen_col],
            "rejected": example[self.rejected_col]
        }

    def validate(self, example: Dict[str, Any]) -> bool:
        return (
            self.prompt_col in example and
            self.chosen_col in example and
            self.rejected_col in example and
            example[self.prompt_col] and
            example[self.chosen_col] and
            example[self.rejected_col]
        )


class ChatFormatter(DatasetFormatter):
    """
    Formatter for Chat datasets (OpenAI/Anthropic chat format)

    Expects data in format:
    {"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}

    This is the standard format for instruction tuning models.
    """

    def __init__(self, messages_col: str = "messages"):
        self.messages_col = messages_col

    def format(self, example: Dict[str, Any]) -> Dict[str, Any]:
        """
        For chat datasets, we return the messages as-is
        because the trainer handles the chat template formatting
        """
        messages = example[self.messages_col]

        # If messages is a string (JSON), parse it
        if isinstance(messages, str):
            import json
            messages = json.loads(messages)

        return {"messages": messages}

    def validate(self, example: Dict[str, Any]) -> bool:
        """
        Validate that example has messages field with proper structure
        """
        if self.messages_col not in example:
            return False

        messages = example[self.messages_col]

        # Handle JSON string
        if isinstance(messages, str):
            try:
                import json
                messages = json.loads(messages)
            except:
                return False

        # Must be a list
        if not isinstance(messages, list):
            return False

        # Must have at least one message
        if len(messages) == 0:
            return False

        # Each message must have role and content
        for msg in messages:
            if not isinstance(msg, dict):
                return False
            if "role" not in msg or "content" not in msg:
                return False
            if not msg["role"] or not msg["content"]:
                return False

        return True


class DatasetPreprocessor:
    """
    Flexible dataset preprocessor with extensible formatters

    Usage:
        preprocessor = DatasetPreprocessor()

        # Process a dataset
        processed = preprocessor.process(
            dataset_path="dataset.csv",
            format_type="qa",
            columns={"question": "user_query", "answer": "agent_response"}
        )

        # Or register custom formatter
        preprocessor.register_formatter("custom", MyCustomFormatter())
    """

    def __init__(self):
        # Registry of formatters
        self._formatters: Dict[str, type] = {
            "qa": QAFormatter,
            "classification": ClassificationFormatter,
            "instruction": InstructionFormatter,
            "summarization": SummarizationFormatter,
            "preference": PreferenceFormatter,
            "chat": ChatFormatter
        }

        logger.info("Initialized DatasetPreprocessor with default formatters")

    def register_formatter(self, name: str, formatter_class: type):
        """
        Register a custom formatter

        Args:
            name: Name to register formatter under
            formatter_class: DatasetFormatter subclass

        Example:
            preprocessor.register_formatter("my_format", MyCustomFormatter)
        """
        if not issubclass(formatter_class, DatasetFormatter):
            raise ValueError(f"Formatter must extend DatasetFormatter, got {formatter_class}")

        self._formatters[name] = formatter_class
        logger.info(f"Registered custom formatter: {name}")

    def load_dataset(self, dataset_path: str) -> pd.DataFrame:
        """
        Load dataset from file

        Supports: CSV, JSON, JSONL, Parquet

        Args:
            dataset_path: Path to dataset file

        Returns:
            DataFrame with dataset
        """
        path = Path(dataset_path)

        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")

        file_extension = path.suffix.lower()

        if file_extension == ".csv":
            df = pd.read_csv(dataset_path)
        elif file_extension == ".json":
            df = pd.read_json(dataset_path)
        elif file_extension == ".jsonl":
            df = pd.read_json(dataset_path, lines=True)
        elif file_extension == ".parquet":
            df = pd.read_parquet(dataset_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

        logger.info(f"Loaded dataset from {dataset_path}: {len(df)} samples")
        return df

    def validate_dataset(
        self,
        df: pd.DataFrame,
        format_type: str,
        columns: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Enhanced validation with auto-detection and preprocessing

        Args:
            df: DataFrame to validate
            format_type: Dataset format type
            columns: Column mapping

        Returns:
            Validation results dictionary with diagnostics and suggestions
        """
        errors = []
        warnings = []
        suggestions = []
        auto_fix_applied = False
        original_columns = columns.copy()

        # Check format type is supported
        if format_type not in self._formatters:
            errors.append(f"Unsupported format type: {format_type}")
            return {
                "is_valid": False,
                "errors": errors,
                "warnings": warnings,
                "suggestions": [f"Supported formats: {', '.join(self._formatters.keys())}"]
            }

        # Get expected column names for this format
        expected_cols = self._get_expected_columns(format_type)
        actual_cols = list(df.columns)

        logger.info(f"Validating dataset: format={format_type}, expected_cols={expected_cols}, actual_cols={actual_cols}")

        # Auto-detect and fix column mapping if empty or missing
        if not columns or len(columns) == 0:
            logger.info("No column mapping provided, attempting auto-detection")
            detected_mapping = self._auto_detect_columns(df, format_type, expected_cols)

            if detected_mapping:
                columns = detected_mapping
                auto_fix_applied = True
                suggestions.append(f"✅ Auto-detected column mapping: {detected_mapping}")
                logger.info(f"Auto-detected columns: {detected_mapping}")
            else:
                errors.append(f"❌ Could not auto-detect column mapping")
                errors.append(f"   Expected columns for '{format_type}': {expected_cols}")
                errors.append(f"   Available columns in CSV: {actual_cols}")
                suggestions.append(f"💡 Please map your CSV columns to the expected format:")
                suggestions.append(f"   - Expected: {expected_cols}")
                suggestions.append(f"   - Your CSV has: {actual_cols}")

                # Suggest fuzzy matches
                fuzzy_suggestions = self._suggest_column_mapping(actual_cols, expected_cols)
                if fuzzy_suggestions:
                    suggestions.append(f"💡 Suggested mapping based on column names:")
                    for expected, suggested in fuzzy_suggestions.items():
                        suggestions.append(f"   - {expected} → {suggested}")

                return {
                    "is_valid": False,
                    "errors": errors,
                    "warnings": warnings,
                    "suggestions": suggestions,
                    "diagnostics": {
                        "format_type": format_type,
                        "expected_columns": expected_cols,
                        "actual_columns": actual_cols,
                        "provided_mapping": original_columns
                    }
                }

        # Verify mapped columns exist in DataFrame
        missing_cols = []
        for col_name, col_key in columns.items():
            if col_key not in df.columns:
                missing_cols.append(col_key)

        if missing_cols:
            errors.append(f"❌ Mapped columns not found in CSV: {missing_cols}")
            errors.append(f"   Available columns: {actual_cols}")
            suggestions.append(f"💡 Check your column mapping - these columns don't exist in the CSV")
            return {
                "is_valid": False,
                "errors": errors,
                "warnings": warnings,
                "suggestions": suggestions,
                "diagnostics": {
                    "format_type": format_type,
                    "expected_columns": expected_cols,
                    "actual_columns": actual_cols,
                    "provided_mapping": columns,
                    "missing_columns": missing_cols
                }
            }

        # Get formatter class and instantiate
        formatter_class = self._formatters[format_type]
        try:
            formatter = formatter_class(**columns)
        except Exception as e:
            errors.append(f"❌ Failed to initialize formatter: {str(e)}")
            return {
                "is_valid": False,
                "errors": errors,
                "warnings": warnings,
                "suggestions": suggestions
            }

        # Validate each row with detailed error tracking
        invalid_rows = []
        empty_value_rows = []
        error_examples = []

        for idx, row in df.iterrows():
            row_dict = row.to_dict()

            # Check if row has the required columns
            is_valid = formatter.validate(row_dict)

            if not is_valid:
                invalid_rows.append(idx)

                # Track specific reasons for invalidity
                if idx < 5:  # Only collect first 5 examples
                    row_errors = []
                    for col_name, col_key in columns.items():
                        value = row_dict.get(col_key)
                        if pd.isna(value) or value == "" or value is None:
                            row_errors.append(f"{col_name} ({col_key}) is empty")

                    if row_errors:
                        empty_value_rows.append(idx)
                        error_examples.append({
                            "row": int(idx),
                            "issues": row_errors,
                            "data": {k: str(row_dict.get(v, ""))[:50] for k, v in columns.items()}
                        })

        # Build detailed error messages
        if invalid_rows:
            errors.append(f"❌ Invalid rows found: {len(invalid_rows)}/{len(df)} rows failed validation")

            if error_examples:
                errors.append(f"   Example errors from first {len(error_examples)} invalid rows:")
                for example in error_examples:
                    errors.append(f"   • Row {example['row']}: {', '.join(example['issues'])}")

            if len(empty_value_rows) > 0:
                suggestions.append(f"💡 {len(empty_value_rows)} rows have empty values in required columns")
                suggestions.append(f"   Please fill in all required fields or remove incomplete rows")

        # Check for empty values in columns
        for col_name, col_key in columns.items():
            if col_key in df.columns:
                empty_count = df[col_key].isna().sum()
                if empty_count > 0:
                    warnings.append(f"⚠️  Column '{col_key}' (mapped from '{col_name}') has {empty_count} empty values")
                    suggestions.append(f"💡 Consider filling or removing rows with empty '{col_key}' values")

        # Size checks
        if len(df) < 10:
            warnings.append(f"⚠️  Dataset is very small ({len(df)} samples)")
            suggestions.append(f"💡 Minimum 10-20 samples recommended. Consider adding more data for better training.")
        elif len(df) < 100:
            warnings.append(f"⚠️  Dataset is small ({len(df)} samples)")
            suggestions.append(f"💡 50-100+ samples recommended for better model performance.")

        is_valid = len(errors) == 0

        result = {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
            "num_samples": len(df),
            "valid_samples": len(df) - len(invalid_rows),
            "invalid_samples": len(invalid_rows),
            "diagnostics": {
                "format_type": format_type,
                "expected_columns": expected_cols,
                "actual_columns": actual_cols,
                "applied_mapping": columns,
                "auto_fix_applied": auto_fix_applied
            }
        }

        if error_examples:
            result["diagnostics"]["error_examples"] = error_examples

        return result

    def _get_expected_columns(self, format_type: str) -> List[str]:
        """Get list of expected column names for a format type"""
        column_map = {
            "qa": ["question", "answer"],
            "instruction": ["instruction", "response", "input"],  # input is optional
            "classification": ["text", "label"],
            "summarization": ["document", "summary"],
            "preference": ["prompt", "chosen", "rejected"],
            "chat": ["messages"]
        }
        return column_map.get(format_type, [])

    def _auto_detect_columns(
        self,
        df: pd.DataFrame,
        format_type: str,
        expected_cols: List[str]
    ) -> Optional[Dict[str, str]]:
        """
        Attempt to auto-detect column mapping based on column names

        Returns column mapping dict or None if detection fails
        """
        actual_cols_lower = {col.lower(): col for col in df.columns}
        detected = {}

        # Format-specific detection logic
        if format_type == "qa":
            # Look for question/answer columns
            # QAFormatter expects 'question_col' and 'answer_col' parameters
            if "question" in actual_cols_lower:
                detected["question_col"] = actual_cols_lower["question"]
            elif "q" in actual_cols_lower:
                detected["question_col"] = actual_cols_lower["q"]
            elif "query" in actual_cols_lower:
                detected["question_col"] = actual_cols_lower["query"]

            if "answer" in actual_cols_lower:
                detected["answer_col"] = actual_cols_lower["answer"]
            elif "a" in actual_cols_lower:
                detected["answer_col"] = actual_cols_lower["a"]
            elif "response" in actual_cols_lower:
                detected["answer_col"] = actual_cols_lower["response"]

        elif format_type == "instruction":
            # Try to map question/answer to instruction/response
            if "instruction" in actual_cols_lower:
                detected["instruction_col"] = actual_cols_lower["instruction"]
            elif "question" in actual_cols_lower:
                detected["instruction_col"] = actual_cols_lower["question"]
            elif "prompt" in actual_cols_lower:
                detected["instruction_col"] = actual_cols_lower["prompt"]

            if "response" in actual_cols_lower:
                detected["response_col"] = actual_cols_lower["response"]
            elif "answer" in actual_cols_lower:
                detected["response_col"] = actual_cols_lower["answer"]
            elif "output" in actual_cols_lower:
                detected["response_col"] = actual_cols_lower["output"]

            # Optional input field
            if "input" in actual_cols_lower:
                detected["input_col"] = actual_cols_lower["input"]

        elif format_type == "classification":
            if "text" in actual_cols_lower:
                detected["text_col"] = actual_cols_lower["text"]
            elif "content" in actual_cols_lower:
                detected["text_col"] = actual_cols_lower["content"]

            if "label" in actual_cols_lower:
                detected["label_col"] = actual_cols_lower["label"]
            elif "category" in actual_cols_lower:
                detected["label_col"] = actual_cols_lower["category"]

        elif format_type == "summarization":
            if "document" in actual_cols_lower:
                detected["document_col"] = actual_cols_lower["document"]
            elif "text" in actual_cols_lower:
                detected["document_col"] = actual_cols_lower["text"]

            if "summary" in actual_cols_lower:
                detected["summary_col"] = actual_cols_lower["summary"]

        elif format_type == "preference":
            if "prompt" in actual_cols_lower:
                detected["prompt_col"] = actual_cols_lower["prompt"]
            if "chosen" in actual_cols_lower:
                detected["chosen_col"] = actual_cols_lower["chosen"]
            if "rejected" in actual_cols_lower:
                detected["rejected_col"] = actual_cols_lower["rejected"]

        elif format_type == "chat":
            # Look for messages column
            if "messages" in actual_cols_lower:
                detected["messages_col"] = actual_cols_lower["messages"]

        # Return mapping only if we found all required columns
        required_count = len([col for col in expected_cols if col != "input"])  # input is optional
        if len(detected) >= required_count:
            logger.info(f"Successfully auto-detected {len(detected)} columns: {detected}")
            return detected

        logger.warning(f"Auto-detection incomplete: found {len(detected)}/{required_count} required columns")
        return None

    def _suggest_column_mapping(
        self,
        actual_cols: List[str],
        expected_cols: List[str]
    ) -> Dict[str, str]:
        """Suggest possible column mappings based on fuzzy matching"""
        suggestions = {}
        actual_cols_lower = {col.lower(): col for col in actual_cols}

        for expected in expected_cols:
            # Simple fuzzy matching - look for partial matches
            for actual_lower, actual_original in actual_cols_lower.items():
                if expected in actual_lower or actual_lower in expected:
                    suggestions[expected] = actual_original
                    break

        return suggestions

    def process(
        self,
        dataset_path: str,
        format_type: str,
        columns: Dict[str, str],
        train_split: float = 0.8,
        max_samples: Optional[int] = None,
        shuffle: bool = True
    ) -> Dict[str, Any]:
        """
        Process and prepare dataset for training

        Args:
            dataset_path: Path to dataset file
            format_type: Format type (qa, classification, etc.)
            columns: Column mapping
            train_split: Train/validation split ratio
            max_samples: Maximum number of samples to use
            shuffle: Whether to shuffle before splitting

        Returns:
            Dictionary with train/val datasets and metadata
        """
        logger.info(f"Processing dataset: {dataset_path} (format: {format_type})")

        # Load dataset
        df = self.load_dataset(dataset_path)

        # Limit samples if requested
        if max_samples and len(df) > max_samples:
            df = df.sample(n=max_samples, random_state=42)
            logger.info(f"Limited to {max_samples} samples")

        # Validate
        validation_results = self.validate_dataset(df, format_type, columns)
        if not validation_results["is_valid"]:
            raise ValueError(f"Dataset validation failed: {validation_results['errors']}")

        # Shuffle if requested
        if shuffle:
            df = df.sample(frac=1, random_state=42).reset_index(drop=True)

        # Get formatter
        formatter_class = self._formatters[format_type]
        formatter = formatter_class(**columns)

        # Format all examples
        formatted_data = []
        for idx, row in df.iterrows():
            try:
                formatted = formatter.format(row.to_dict())
                formatted_data.append(formatted)
            except Exception as e:
                logger.warning(f"Failed to format row {idx}: {e}")

        # Split train/val
        split_idx = int(len(formatted_data) * train_split)
        train_data = formatted_data[:split_idx]
        val_data = formatted_data[split_idx:]

        logger.info(f"Dataset processed: {len(train_data)} train, {len(val_data)} val samples")

        return {
            "train": train_data,
            "validation": val_data,
            "metadata": {
                "total_samples": len(df),
                "train_samples": len(train_data),
                "val_samples": len(val_data),
                "format_type": format_type,
                "columns": columns,
                "validation_results": validation_results
            }
        }

    def get_sample_preview(
        self,
        dataset_path: str,
        format_type: str,
        columns: Dict[str, Any],
        num_samples: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get a preview of formatted samples

        Args:
            dataset_path: Path to dataset
            format_type: Format type
            columns: Column mapping
            num_samples: Number of samples to preview

        Returns:
            List of formatted samples
        """
        df = self.load_dataset(dataset_path)
        df = df.head(num_samples)

        formatter_class = self._formatters[format_type]
        formatter = formatter_class(**columns)

        samples = []
        for idx, row in df.iterrows():
            try:
                formatted = formatter.format(row.to_dict())
                samples.append({
                    "index": int(idx),
                    "raw": row.to_dict(),
                    "formatted": formatted
                })
            except Exception as e:
                logger.warning(f"Failed to format sample {idx}: {e}")

        return samples


# ============================================================================
# Utility Functions
# ============================================================================

def infer_format_type(df: pd.DataFrame) -> Optional[str]:
    """
    Attempt to infer dataset format type from column names

    Args:
        df: DataFrame to analyze

    Returns:
        Inferred format type or None
    """
    columns = set(col.lower() for col in df.columns)

    # Chat detection (check first as it's very specific)
    if "messages" in columns:
        return "chat"

    # QA detection
    if ("question" in columns and "answer" in columns):
        return "qa"

    # Classification detection
    if ("text" in columns and "label" in columns):
        return "classification"

    # Instruction detection
    if ("instruction" in columns and "response" in columns):
        return "instruction"

    # Preference detection
    if ("prompt" in columns and "chosen" in columns and "rejected" in columns):
        return "preference"

    # Summarization detection
    if ("document" in columns and "summary" in columns):
        return "summarization"

    logger.warning("Could not infer format type from columns")
    return None
