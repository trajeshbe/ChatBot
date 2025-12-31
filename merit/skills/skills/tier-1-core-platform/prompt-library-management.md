# Prompt Library Management - Core Platform

**Tier**: 1 (Core Platform)
**Status**: Always Deployed
**Dependencies**: None
**Complexity**: N/A (Infrastructure)

---

## Overview

The Prompt Library is the centralized prompt management system that enables the **Prompt-First Development** approach across all modules and customer implementations. It provides YAML-based prompt storage, Pydantic schema validation, and customer-specific prompt overrides.

**Key Principle**: 80% of AI functionality should be implemented with well-engineered prompts stored in YAML files, not complex code.

---

## Architecture

### Directory Structure

```
project_root/
├── prompt_engineering/
│   ├── prompt/                          # YAML prompt files
│   │   ├── core_rag_prompts.yaml
│   │   ├── extraction_prompts.yaml
│   │   ├── nlp_prompts.yaml
│   │   ├── analytics_prompts.yaml
│   │   ├── financial_prompts.yaml
│   │   └── customer_[id]_prompts.yaml   # Customer overrides
│   │
│   └── template/                        # Pydantic output schemas
│       ├── extraction_schemas.py
│       ├── nlp_schemas.py
│       ├── analytics_schemas.py
│       └── customer_schemas.py
│
├── config/
│   └── common_config.yaml               # Contains prompt_path config
│
└── modules/
    └── [module_name]/
        └── service.py                   # Loads prompts
```

### Configuration

```yaml
# config/common_config.yaml
prompt_path: "prompt_engineering/prompt"
```

---

## Core Capabilities

### 1. YAML-Based Prompt Storage

**Pattern**:
```yaml
# prompt_engineering/prompt/module_prompts.yaml
task_name_prompt: |
  You are an expert [domain] assistant.

  Task: {task_description}
  Input: {input_data}

  Instructions:
  1. Analyze the input carefully
  2. Apply [domain] expertise
  3. Return structured output

  Output format:
  {format_instruction}

another_task_prompt: |
  [Another prompt template]
```

**Benefits**:
- ✅ No code deployment for prompt changes
- ✅ Version controlled independently
- ✅ Easy A/B testing
- ✅ Customer-specific overrides

### 2. Pydantic Schema Validation

**Pattern**:
```python
# prompt_engineering/template/module_schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional

class TaskOutput(BaseModel):
    """Structured output schema for task"""
    field1: str = Field(description="Description of field1")
    field2: float = Field(description="Confidence score 0-1", ge=0, le=1)
    field3: Optional[List[str]] = Field(description="Optional list field")
    reasoning: str = Field(description="Explanation of the result")
```

**Benefits**:
- ✅ Type-safe outputs
- ✅ Automatic validation
- ✅ Clear schema documentation
- ✅ LLM-friendly format instructions

### 3. Customer Prompt Overrides

**Platform Default**:
```yaml
# prompt_engineering/prompt/core_rag_prompts.yaml
generation_prompt: |
  Answer the question based on the provided context.

  Context: {context}
  Question: {question}

  Provide a concise answer with source citations.
```

**Customer Override**:
```yaml
# prompt_engineering/prompt/customer_acme_prompts.yaml
core_rag_prompts:
  generation_prompt: |
    You are the ACME AI Assistant for financial analysis.

    Answer using ACME's internal documents:
    Context: {context}
    Question: {question}

    Use ACME terminology and cite document names.
    Format: [Answer] | Sources: [doc1, doc2]
```

---

## Usage Patterns

### Pattern 1: Prompt-Only Implementation (Tier A)

**Use When**: Single LLM call, structured output, no complex logic

**Example**:
```yaml
# prompt_engineering/prompt/classification_prompts.yaml
classify_document_prompt: |
  Classify the following document into one of these categories:
  Categories: {categories}

  Document: {text}

  Return JSON:
  {
    "category": "selected_category",
    "confidence": 0.0-1.0,
    "reasoning": "why this category"
  }
```

```python
# Implementation (just 5 lines!)
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

prompts = load_yaml_data("prompt_engineering/prompt/classification_prompts.yaml")
llm = ChatOpenAI(model="gpt-4o")
parser = JsonOutputParser(pydantic_object=ClassificationOutput)

result = llm.invoke(prompts["classify_document_prompt"].format(
    categories=", ".join(cats),
    text=document_text
))
parsed = parser.parse(result.content)
```

**Code Reduction**: 90% vs. traditional approach

### Pattern 2: Sequential Prompts (Tier B)

**Use When**: 2-3 step workflow, validation/post-processing needed

**Example**:
```yaml
# prompt_engineering/prompt/extraction_prompts.yaml
extract_data_prompt: |
  Extract the following fields from the document:
  Fields: {field_list}

  Document: {document}

  Return JSON with field names as keys.

validate_extraction_prompt: |
  Validate the extracted data for consistency:

  Data: {extracted_data}

  Check:
  - All required fields present
  - Numeric fields are reasonable
  - Dates are properly formatted

  Return: {"is_valid": true/false, "errors": [...]}
```

```python
# Implementation
def extract_and_validate(document):
    # Step 1: Extract
    extraction = llm.invoke(
        prompts["extract_data_prompt"].format(
            field_list=fields,
            document=document
        )
    )
    data = parser.parse(extraction.content)

    # Step 2: Validate
    validation = llm.invoke(
        prompts["validate_extraction_prompt"].format(
            extracted_data=data.json()
        )
    )

    # Step 3: Handle validation
    if not validation["is_valid"]:
        data = fix_errors(data, validation["errors"])

    return data
```

### Pattern 3: LangGraph with Prompts (Tier C)

**Use When**: Complex workflows, retrieval+generation, branching

**Example**:
```yaml
# prompt_engineering/prompt/rag_prompts.yaml
query_refinement_prompt: |
  Refine this user query for better retrieval:
  Query: {question}
  Return refined query only.

generation_prompt: |
  Answer based ONLY on the provided context.

  Context: {context}
  Question: {question}

  Provide answer with source citations.

critique_prompt: |
  Evaluate this answer for accuracy and completeness:
  Answer: {answer}
  Context: {context}

  Return quality score (0-1) and improvement suggestions.
```

```python
# LangGraph workflow using prompts
from langgraph.graph import StateGraph

def validate_query(state):
    refined = llm.invoke(prompts["query_refinement_prompt"])
    return {"refined_query": refined}

def generate_answer(state):
    answer = llm.invoke(prompts["generation_prompt"])
    return {"answer": answer}

def critique_answer(state):
    critique = llm.invoke(prompts["critique_prompt"])
    return {"quality_score": critique.score}

# Build workflow (prompts are in YAML, not hardcoded)
workflow = StateGraph(RAGState)
workflow.add_node("validate", validate_query)
workflow.add_node("generate", generate_answer)
workflow.add_node("critique", critique_answer)
# ... edges and compilation
```

---

## PromptManager Utility

### Core Implementation

```python
# utils/prompt_manager.py
import yaml
from pathlib import Path
from typing import Dict, Optional
from functools import lru_cache

class PromptManager:
    """
    Centralized prompt management utility.
    Handles loading, caching, and customer overrides.
    """

    def __init__(self, prompt_path: str = "prompt_engineering/prompt"):
        self.prompt_path = Path(prompt_path)
        self._cache: Dict[str, Dict] = {}

    @lru_cache(maxsize=100)
    def load_prompts(self, module_name: str) -> Dict[str, str]:
        """Load prompts for a specific module"""
        yaml_file = self.prompt_path / f"{module_name}_prompts.yaml"

        if not yaml_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {yaml_file}")

        with open(yaml_file, 'r') as f:
            prompts = yaml.safe_load(f)

        self._cache[module_name] = prompts
        return prompts

    def get_prompt(self, module: str, prompt_key: str, customer_id: Optional[str] = None) -> str:
        """
        Get a specific prompt template with optional customer override.

        Args:
            module: Module name (e.g., "core_rag", "extraction")
            prompt_key: Prompt key within module (e.g., "generation_prompt")
            customer_id: Optional customer ID for override

        Returns:
            Prompt template string
        """
        # Load base prompts
        if module not in self._cache:
            self._cache[module] = self.load_prompts(module)

        base_prompts = self._cache[module]

        # Check for customer override
        if customer_id:
            customer_override = self._load_customer_override(customer_id, module, prompt_key)
            if customer_override:
                return customer_override

        # Return base prompt
        if prompt_key not in base_prompts:
            raise KeyError(f"Prompt '{prompt_key}' not found in module '{module}'")

        return base_prompts[prompt_key]

    def _load_customer_override(self, customer_id: str, module: str, prompt_key: str) -> Optional[str]:
        """Load customer-specific prompt override if exists"""
        customer_file = self.prompt_path / f"customer_{customer_id}_prompts.yaml"

        if not customer_file.exists():
            return None

        with open(customer_file, 'r') as f:
            customer_prompts = yaml.safe_load(f)

        # Check if customer has override for this module/prompt
        if module in customer_prompts:
            if isinstance(customer_prompts[module], dict):
                return customer_prompts[module].get(prompt_key)

        return None

    def list_modules(self) -> list[str]:
        """List all available prompt modules"""
        return [
            f.stem.replace("_prompts", "")
            for f in self.prompt_path.glob("*_prompts.yaml")
            if not f.stem.startswith("customer_")
        ]

    def invalidate_cache(self, module: str = None):
        """Invalidate prompt cache for hot-reloading"""
        if module:
            self._cache.pop(module, None)
            self.load_prompts.cache_clear()
        else:
            self._cache.clear()
            self.load_prompts.cache_clear()


# Singleton instance
prompt_manager = PromptManager()
```

### Usage in Modules

```python
# modules/my_module/service.py
from utils.prompt_manager import prompt_manager
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser

class MyModuleService:
    def __init__(self, customer_id: Optional[str] = None):
        self.customer_id = customer_id
        self.llm = ChatOpenAI(model="gpt-4o")

    def execute_task(self, input_data):
        # Get prompt (with customer override if applicable)
        prompt = prompt_manager.get_prompt(
            module="my_module",
            prompt_key="task_prompt",
            customer_id=self.customer_id
        )

        # Format and invoke
        response = self.llm.invoke(
            prompt.format(input_data=input_data)
        )

        return JsonOutputParser(pydantic_object=TaskOutput).parse(response.content)
```

---

## Customer Override Strategy

### Override Levels

1. **Module-Level Override**: Replace all prompts for a module
2. **Prompt-Level Override**: Replace specific prompts within a module
3. **Template Variable Override**: Change default variables

### Example: Prompt-Level Override

```yaml
# prompt_engineering/prompt/customer_acme_prompts.yaml
# Override specific prompts for ACME Corp

core_rag_prompts:
  # Override generation prompt only
  generation_prompt: |
    You are the ACME Financial AI Assistant.
    [ACME-specific instructions]

nlp_prompts:
  # Override NER prompt with ACME entities
  ner_prompt: |
    Extract entities including ACME-specific types:
    - ACME_PRODUCT
    - ACME_DIVISION
    - COMPETITOR
    [ACME-specific instructions]

# Analytics prompts use defaults (not overridden)
```

---

## Prompt Engineering Best Practices

### 1. Clear Instructions

✅ **Good**:
```yaml
classification_prompt: |
  Classify the document into exactly ONE of these categories:
  Categories: {categories}

  Document: {text}

  Return JSON: {"category": "...", "confidence": 0.0-1.0, "reasoning": "..."}
```

❌ **Bad**:
```yaml
classification_prompt: |
  Classify this: {text}
  Categories: {categories}
```

### 2. Structured Outputs

✅ **Good**:
```yaml
extraction_prompt: |
  Extract data and return JSON with these exact fields:
  {{
    "project_name": "string",
    "address": "string",
    "storeys": number,
    "gfa": number
  }}

  Document: {document}
```

❌ **Bad**:
```yaml
extraction_prompt: |
  Get the project name, address, storeys, and GFA from: {document}
```

### 3. Examples When Helpful

✅ **Good**:
```yaml
analysis_prompt: |
  Analyze the financial data.

  Example:
  Input: "Q1 Revenue: $5M, Q2 Revenue: $7M"
  Output: {{
    "growth_rate": 0.4,
    "trend": "increasing",
    "insight": "40% quarter-over-quarter growth"
  }}

  Input: {financial_data}
```

### 4. Domain Context

✅ **Good**:
```yaml
financial_analysis_prompt: |
  You are a financial analyst expert in GAAP standards.

  Analyze this financial statement following GAAP principles:
  - Revenue recognition rules
  - Accrual accounting
  - Materiality thresholds

  Statement: {statement}
```

---

## Prompt Versioning

### Strategy

```
prompt_engineering/prompt/
├── core_rag_prompts.yaml          # Current version
├── core_rag_prompts_v1.yaml       # Previous version (archived)
└── core_rag_prompts_v2.yaml       # New version (testing)
```

### Version Configuration

```yaml
# config/prompt_versions.yaml
modules:
  core-rag:
    version: "v2"  # Use v2 prompts
    fallback: "v1"  # Fallback if v2 fails

  data-extraction:
    version: "v1"  # Stable version
```

---

## Testing Prompts

### Unit Testing

```python
# tests/test_prompts.py
def test_prompt_loading():
    """Test prompts load correctly"""
    prompts = prompt_manager.load_prompts("core_rag")

    assert "generation_prompt" in prompts
    assert "{context}" in prompts["generation_prompt"]
    assert "{question}" in prompts["generation_prompt"]

def test_customer_override():
    """Test customer overrides work"""
    base_prompt = prompt_manager.get_prompt("core_rag", "generation_prompt")
    acme_prompt = prompt_manager.get_prompt("core_rag", "generation_prompt", customer_id="acme")

    assert base_prompt != acme_prompt
    assert "ACME" in acme_prompt
```

### A/B Testing

```python
def ab_test_prompts():
    """Compare two prompt versions"""
    prompt_v1 = prompt_manager.load_prompts("module_v1")["task_prompt"]
    prompt_v2 = prompt_manager.load_prompts("module_v2")["task_prompt"]

    results_v1 = [test_case(prompt_v1, data) for data in test_data]
    results_v2 = [test_case(prompt_v2, data) for data in test_data]

    print(f"V1 Accuracy: {accuracy(results_v1)}")
    print(f"V2 Accuracy: {accuracy(results_v2)}")
```

---

## Performance Considerations

### Caching

Prompts are cached in memory with `@lru_cache`:
- First load: ~10ms (file I/O)
- Subsequent calls: <1ms (memory)

### Hot Reloading

```python
# Invalidate cache to reload prompts (development only)
prompt_manager.invalidate_cache("core_rag")

# Reload specific prompt
new_prompt = prompt_manager.get_prompt("core_rag", "generation_prompt")
```

---

## Migration from Hardcoded Prompts

### Before (Hardcoded):

```python
# Bad: Prompt hardcoded in Python
system_prompt = """
You are a data extraction assistant.
Extract fields from the document.
Return JSON.
"""

prompt = PromptTemplate(template=system_prompt, input_variables=["document"])
```

### After (YAML-Based):

```yaml
# Good: Prompt in YAML
# prompt_engineering/prompt/extraction_prompts.yaml
extract_fields_prompt: |
  You are a data extraction assistant.
  Extract fields from the document.
  Return JSON.

  Document: {document}
```

```python
# Simple usage
prompts = prompt_manager.load_prompts("extraction")
result = llm.invoke(prompts["extract_fields_prompt"].format(document=doc))
```

**Benefits**:
- ✅ 12x faster iteration (no code deployment)
- ✅ Easy customer customization
- ✅ Version controlled separately
- ✅ A/B testing without code changes

---

## Related Skills

- [LLM Providers](llm-providers.md) - LLM abstraction layer
- [Tier 2: Core RAG](../tier-2-modules/core-rag/) - Uses prompt library extensively
- [Tier 2: Data Extraction](../tier-2-modules/data-extraction/) - Prompt-first extraction
- [Tier 3: Customer Implementations](../tier-3-customer-implementations/) - Customer overrides

---

## Reference Documentation

- [Prompt Library Integration](../../SKILLS_PROMPT_LIBRARY_INTEGRATION.md)
- [Quick Start: Prompt-First Skills](../../QUICK_START_PROMPT_FIRST_SKILLS.md)
- [Merit ML Platform Skill](../../prototypes/merit-ml-platform.md) (Legacy reference)

---

**Last Updated**: 2025-12-23
**Status**: Production Ready
**Complexity**: Infrastructure (Foundation)
