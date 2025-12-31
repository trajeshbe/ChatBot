# Tier 2: Use-Case Modules

**Status**: Selectively Enabled
**Purpose**: Reusable capability modules that can be mixed and matched per customer

---

## Overview

Tier 2 modules provide specific capabilities that can be enabled or disabled based on customer requirements. Each module is self-contained and can be configured independently.

---

## Module Categories

### Core Modules (20 skills)

| Module | Skills | Complexity | Description |
|--------|--------|------------|-------------|
| [**core-rag**](core-rag/) | 4 | 🔴 Tier C | Retrieval-Augmented Generation pipelines |
| [**data-extraction**](data-extraction/) | 4 | 🟡 Tier B | Structured data extraction from documents |
| [**nlp-processing**](nlp-processing/) | 5 | 🟢 Tier A | NER, classification, tagging capabilities |
| [**analytics-engine**](analytics-engine/) | 4 | 🟡 Tier B | Metrics extraction and insights |
| [**query-engine**](query-engine/) | 3 | 🔴 Tier C | Natural language to SQL translation |

### Domain Verticals (12 skills)

| Vertical | Skills | Industries | Description |
|----------|--------|-----------|-------------|
| [**financial**](domain-verticals/financial/) | 3 | Banking, Insurance, Accounting | Financial analysis & compliance |
| [**supply-chain**](domain-verticals/supply-chain/) | 3 | Manufacturing, Logistics | Procurement & vendor management |
| [**mining**](domain-verticals/mining/) | 2 | Mining, Resources | Operations & compliance |
| [**agriculture**](domain-verticals/agriculture/) | 2 | Farming, AgTech | Agronomy & crop management |
| [**human-resources**](domain-verticals/human-resources/) | 2 | HR, Recruiting | Talent search & skill matching |

---

## Module Selection Guide

### By Use Case

| Use Case | Required Modules | Optional Modules |
|----------|------------------|------------------|
| **Chatbot/Q&A** | core-rag | nlp-processing, analytics-engine |
| **Document Processing** | data-extraction | nlp-processing, analytics-engine |
| **Content Tagging** | nlp-processing | - |
| **Data Analytics** | analytics-engine | data-extraction, query-engine |
| **Database Querying** | query-engine | core-rag |
| **Financial Analysis** | analytics-engine, domain-verticals/financial | data-extraction |
| **Procurement** | domain-verticals/supply-chain | data-extraction, analytics-engine |

### By Complexity

**🟢 Simple (Prompt-Only)**:
- nlp-processing (classification, tagging, NER)
- analytics-engine (metric extraction)
- data-extraction (schema extraction, table extraction)

**🟡 Medium (Prompt + Logic)**:
- data-extraction (validation, form filling)
- analytics-engine (aggregation, comparison)
- nlp-processing (relation extraction, entity linking)

**🔴 Complex (LangGraph)**:
- core-rag (full RAG pipeline)
- query-engine (NL2SQL workflows)
- domain-verticals (multi-stage pipelines)

---

## Module Configuration

### Standard Module Structure

```yaml
# module.yaml example
name: module-name
version: "1.0.0"
description: "Module description"

dependencies:
  - core-platform  # Tier 1 dependencies

routes_prefix: "/api/v1/module"

config:
  setting1: value1
  setting2: value2

capabilities:
  - name: capability_name
    description: What this capability does
    input_schema: {...}
    output_schema: {...}

langgraph_nodes:
  - node_name_1
  - node_name_2
```

### Enabling Modules for Customers

```yaml
# customers/acme-corp.yaml
modules:
  enabled_modules:
    - core-rag
    - data-extraction
    - nlp-processing
    - domain-verticals/financial

  module_configs:
    core-rag:
      retrieval:
        top_k: 10
        similarity_threshold: 0.7

    data-extraction:
      extraction:
        confidence_threshold: 0.85

    nlp-processing:
      ner:
        custom_entities:
          - ACME_PRODUCT
          - COMPETITOR
```

---

## Module Development Guidelines

### Prompt-First Approach

**80%** of module functionality should be implemented with prompts:

```yaml
# prompt_engineering/prompt/module_prompts.yaml
task_prompt: |
  You are an expert in [domain].

  Task: {task_description}
  Input: {input_data}

  Output format: {format_instruction}
```

```python
# Simple module implementation
class Module(BaseModule):
    def initialize(self):
        self.prompts = load_yaml_data("prompt_engineering/prompt/module_prompts.yaml")
        self.llm = get_llm_provider()

    def execute(self, input_data):
        result = self.llm.invoke(
            self.prompts["task_prompt"].format(input_data=input_data)
        )
        return parse_result(result)
```

### Only Use LangGraph When Needed

Reserve LangGraph for:
- Multi-step retrieval + generation
- Workflows with conditional branching
- Iterative refinement loops
- Complex state management

---

## Core Modules Deep Dive

### 1. Core RAG Module

**Purpose**: Retrieval-Augmented Generation for chatbots and Q&A

**Skills**:
- [retrieval-semantic-search.md](core-rag/retrieval-semantic-search.md)
- [generation-response.md](core-rag/generation-response.md)
- [conversation-management.md](core-rag/conversation-management.md)
- [rag-pipeline-workflows.md](core-rag/rag-pipeline-workflows.md)

**Workflow**: Query → Retrieve → Rerank → Generate → Cite

### 2. Data Extraction Module

**Purpose**: Extract structured data from unstructured documents

**Skills**:
- [schema-extraction.md](data-extraction/schema-extraction.md) - JSON/structured extraction
- [table-extraction.md](data-extraction/table-extraction.md) - Table data extraction
- [form-filling.md](data-extraction/form-filling.md) - Template population
- [validation-quality.md](data-extraction/validation-quality.md) - Data quality checks

**Pattern**: Parse → Extract → Validate → Format

### 3. NLP Processing Module

**Purpose**: Natural language processing capabilities

**Skills**:
- [named-entity-recognition.md](nlp-processing/named-entity-recognition.md) - Extract entities
- [relation-extraction.md](nlp-processing/relation-extraction.md) - Find relationships
- [text-classification.md](nlp-processing/text-classification.md) - Classify documents
- [tagging-labeling.md](nlp-processing/tagging-labeling.md) - Multi-label tagging
- [entity-linking.md](nlp-processing/entity-linking.md) - Link to knowledge bases

**Pattern**: Text → Analysis → Classification/Extraction

### 4. Analytics Engine Module

**Purpose**: Extract metrics and generate insights

**Skills**:
- [metric-extraction.md](analytics-engine/metric-extraction.md) - Extract numeric metrics
- [aggregation-statistics.md](analytics-engine/aggregation-statistics.md) - Statistical analysis
- [period-comparison.md](analytics-engine/period-comparison.md) - Period-over-period analysis
- [visualization-reporting.md](analytics-engine/visualization-reporting.md) - Charts and reports

**Pattern**: Extract → Aggregate → Analyze → Visualize

### 5. Query Engine Module

**Purpose**: Natural language to SQL translation

**Skills**:
- [natural-language-to-sql.md](query-engine/natural-language-to-sql.md) - NL2SQL translation
- [schema-discovery.md](query-engine/schema-discovery.md) - Database introspection
- [query-optimization.md](query-engine/query-optimization.md) - Query performance tuning

**Pattern**: NL Query → SQL → Execute → Format Results

---

## Domain Verticals

### Financial Services

Specialized capabilities for financial industry:
- Financial metric extraction
- Financial document analysis
- Compliance standards (GAAP, IFRS)

### Supply Chain

Procurement and logistics capabilities:
- Procurement matching
- Vendor recommendation
- Tender intelligence

### Mining Industry

Mining-specific operations:
- Mine scope operations
- Mining compliance

### Agriculture

Agricultural decision support:
- Agronomy decision support
- Agricultural taxonomy

### Human Resources

Recruiting and talent management:
- Talent search and matching
- Resume parsing

---

## Module Integration Patterns

### Module-to-Module Communication

```python
# Module A uses Module B's capability
from app.modules.registry import registry

nlp_module = registry.get_module("nlp-processing")
entities = nlp_module.instance.extract_entities(text)

# Module A continues with entities
analysis = self.analyze_entities(entities)
```

### Module Composition

```yaml
# Compose modules for complex use cases
use_case:
  name: "Document Intelligence"
  modules:
    - data-extraction  # Extract structured data
    - nlp-processing   # Extract entities
    - analytics-engine # Analyze metrics

  workflow:
    1. data-extraction.extract_schema(document)
    2. nlp-processing.extract_entities(document)
    3. analytics-engine.extract_metrics(extracted_data)
    4. Return combined results
```

---

## Testing Modules

### Unit Testing

```python
# Test individual module capabilities
def test_classification():
    module = ClassificationModule(config)
    result = module.classify(text="Sample text")

    assert result.category in ["urgent", "normal", "low"]
    assert 0.0 <= result.confidence <= 1.0
```

### Integration Testing

```python
# Test module with platform
def test_module_with_platform():
    registry.enable_module("nlp-processing")

    result = registry.get_module("nlp-processing").execute(input_data)

    assert result is not None
```

---

## Related Documentation

- [Prompt Library Integration](../../SKILLS_PROMPT_LIBRARY_INTEGRATION.md)
- [Quick Start: Prompt-First Skills](../../QUICK_START_PROMPT_FIRST_SKILLS.md)
- [Tier 1 Core Platform](../tier-1-core-platform/)
- [Tier 3 Customer Implementations](../tier-3-customer-implementations/)

---

**Last Updated**: 2025-12-23
**Total Modules**: 10 (5 core + 5 domain verticals)
**Total Skills**: 32
**Status**: Production Ready
