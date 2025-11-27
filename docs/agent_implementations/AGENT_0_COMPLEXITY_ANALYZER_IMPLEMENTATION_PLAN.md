# Agent 0: Sample Complexity Analyzer - Implementation Plan

**Date**: 2025-11-25
**Status**: 🚀 Ready for Implementation

---

## Executive Summary

Implementing **Agent 0: Sample Complexity Analyzer** as the foundational intelligence layer that objectively analyzes uploaded sample files using real extraction tools (Docling, Tesseract, pandas) to determine project complexity. This complexity rating cascades through the entire workflow, intelligently adjusting effort hours, billing rates, skill requirements, and team composition.

---

## Architecture Overview

### New 9-Agent Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ Agent 0: Sample Complexity Analyzer (NEW!)                  │
│ Tools: Docling, Tesseract, pandas, openpyxl                │
│ Output: Complexity Rating (Low/Medium/High) + Multipliers   │
└──────────────────┬──────────────────────────────────────────┘
                   │ complexity_analysis
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ Agent 1: Analyst (Enhanced)                                 │
│ Uses: complexity_rating for requirements context            │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ Agent 2: Team Planner (Enhanced)                            │
│ Uses: complexity_rating to add specialized teams            │
│      (e.g., OCR Engineering if High complexity)             │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ Agent 3: Task Generator (Enhanced)                          │
│ Uses: effort_multiplier to scale task hours                 │
│      (e.g., 40 hours × 1.6 = 64 hours for High complexity) │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ Agent 3.5: Meta-Validator                                   │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ Agent 4: Workflow Agent                                     │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ Agent 5: Rate Assignment (Enhanced)                         │
│ Uses: rate_multiplier and skill_requirements                │
│      (e.g., Senior rate × 1.3 for Medium complexity)        │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ Agent 6: Document Generator (Enhanced)                      │
│ Includes: Complexity Analysis Report section in BRD         │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ Agent 6.5: Document Validator                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Agent 0: Technical Specification

### Input
```python
{
    "uploaded_samples": {
        "brd_files": ["path/to/sample_brd.docx", "path/to/another.pdf"],
        "cost_files": ["path/to/sample_cost.xlsx"],
        "sample_files": ["path/to/data.zip", "path/to/image.png"]
    }
}
```

### Processing Steps

#### 1. PDF Analysis (using Docling)
```python
from docling.document_converter import DocumentConverter

def analyze_pdf_complexity(pdf_path: str) -> dict:
    """
    Analyze PDF structure and complexity using Docling.
    """
    converter = DocumentConverter()
    result = converter.convert(pdf_path)

    return {
        "page_count": len(result.pages),
        "has_tables": result.table_count > 0,
        "has_images": result.image_count > 0,
        "has_forms": result.form_count > 0,
        "layout_complexity": calculate_layout_complexity(result),
        "text_density": result.word_count / len(result.pages),
        "structure_score": rate_document_structure(result)  # 1-10
    }
```

**Complexity Scoring:**
- **Low**: Simple text documents, < 10 pages, no tables/images
- **Medium**: Multi-column layouts, tables, 10-50 pages
- **High**: Scanned documents, complex nested structures, > 50 pages

#### 2. Image/OCR Analysis (using Tesseract)
```python
import pytesseract
from PIL import Image

def analyze_image_complexity(image_path: str) -> dict:
    """
    Analyze image quality and OCR difficulty using Tesseract.
    """
    image = Image.open(image_path)

    # Run OCR with confidence scores
    ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    # Calculate average confidence
    confidences = [int(conf) for conf in ocr_data['conf'] if conf != '-1']
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

    return {
        "resolution": f"{image.width}x{image.height}",
        "ocr_confidence": avg_confidence / 100,  # 0.0 - 1.0
        "text_density": len([w for w in ocr_data['text'] if w.strip()]) / (image.width * image.height / 1000),
        "clarity_rating": "High" if avg_confidence > 90 else "Medium" if avg_confidence > 70 else "Low",
        "estimated_accuracy": avg_confidence / 100
    }
```

**Complexity Scoring:**
- **Low**: Clear text, OCR confidence > 90%, High resolution
- **Medium**: Some noise, OCR confidence 70-90%, Medium resolution
- **High**: Poor quality, OCR confidence < 70%, handwritten text

#### 3. Excel Analysis (using openpyxl/pandas)
```python
import openpyxl
import pandas as pd

def analyze_excel_complexity(excel_path: str) -> dict:
    """
    Analyze Excel file complexity - formulas, pivots, macros.
    """
    wb = openpyxl.load_workbook(excel_path, data_only=False)

    formula_count = 0
    cell_count = 0
    has_pivot = False
    has_macros = wb.vba_archive is not None

    for sheet in wb.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                cell_count += 1
                if cell.value and isinstance(cell.value, str) and cell.value.startswith('='):
                    formula_count += 1

        # Check for pivot tables
        if sheet._pivots:
            has_pivot = True

    formula_density = formula_count / cell_count if cell_count > 0 else 0

    return {
        "sheet_count": len(wb.worksheets),
        "total_cells": cell_count,
        "formula_count": formula_count,
        "formula_density": formula_density,
        "has_pivot_tables": has_pivot,
        "has_macros": has_macros,
        "complexity_score": calculate_excel_score(formula_density, has_pivot, has_macros)
    }
```

**Complexity Scoring:**
- **Low**: Simple data tables, few formulas, no pivots/macros
- **Medium**: Moderate formulas, some pivots, < 5 sheets
- **High**: Heavy formulas (>20% cells), complex pivots, macros, > 5 sheets

#### 4. Overall Complexity Calculation
```python
def calculate_overall_complexity(analysis_results: dict) -> tuple[str, dict]:
    """
    Combine all analysis results to determine overall complexity.

    Returns: (complexity_rating, recommendations)
    """
    scores = []

    # PDF complexity contributes 40%
    for pdf in analysis_results.get("pdf_samples", []):
        scores.append(pdf["structure_score"] * 0.4)

    # Image/OCR complexity contributes 30%
    for img in analysis_results.get("image_samples", []):
        ocr_score = (1 - img["ocr_confidence"]) * 10  # Lower confidence = higher complexity
        scores.append(ocr_score * 0.3)

    # Excel complexity contributes 30%
    for excel in analysis_results.get("excel_samples", []):
        scores.append(excel["complexity_score"] * 0.3)

    avg_score = sum(scores) / len(scores) if scores else 5.0

    # Map score to rating
    if avg_score < 3.5:
        rating = "Low"
        effort_multiplier = 1.0
        rate_multiplier = 1.0
        skill_level = "Mid"
    elif avg_score < 7.0:
        rating = "Medium"
        effort_multiplier = 1.3
        rate_multiplier = 1.15
        skill_level = "Senior"
    else:
        rating = "High"
        effort_multiplier = 1.8
        rate_multiplier = 1.30
        skill_level = "Senior/Expert"

    recommendations = {
        "effort_multiplier": effort_multiplier,
        "rate_multiplier": rate_multiplier,
        "skill_requirements": {
            "minimum_level": skill_level,
            "specialized_skills": determine_specialized_skills(analysis_results)
        },
        "team_recommendations": determine_specialized_teams(rating, analysis_results)
    }

    return rating, recommendations
```

### Output Format
```python
{
    "complexity_analysis": {
        "overall_rating": "Medium",  # Low | Medium | High
        "confidence_score": 0.85,

        "detailed_analysis": {
            "pdf_complexity": {
                "average_pages": 35,
                "has_complex_layouts": True,
                "structure_rating": "Medium"
            },
            "ocr_requirements": {
                "average_confidence": 0.78,
                "estimated_accuracy": "Medium",
                "requires_specialized_ocr": False
            },
            "data_complexity": {
                "excel_formula_density": 0.15,
                "has_advanced_features": True,
                "processing_difficulty": "Medium"
            }
        },

        "impact_on_estimation": {
            "effort_multiplier": 1.3,
            "rate_multiplier": 1.15,
            "skill_requirements": {
                "minimum_level": "Senior",
                "specialized_skills": ["Document Processing", "Data Analysis"]
            },
            "recommended_teams": [
                "Document Processing Team",
                "Data Engineering Team"
            ]
        },

        "reasoning": "Based on analysis of uploaded samples: 2 PDF files with moderate complexity (avg 35 pages, tables present), 1 Excel file with formula density 15%, OCR confidence 78%. Recommending 30% effort increase and Senior-level resources."
    }
}
```

---

## Integration Points

### 1. State Management
```python
class State(TypedDict):
    # ... existing fields ...
    complexity_analysis: Optional[dict]  # NEW
    effort_multiplier: float  # NEW - cascades from Agent 0
    rate_multiplier: float  # NEW - cascades from Agent 0
    skill_requirements: dict  # NEW - used by Agent 2 & 5
```

### 2. Agent 1 Enhancement
```python
# In analyst_agent method
complexity_context = state.get("complexity_analysis", {})
complexity_rating = complexity_context.get("overall_rating", "Low")

prompt = f"""
...existing prompt...

## COMPLEXITY ANALYSIS:
Based on uploaded sample analysis, this project is rated as **{complexity_rating} complexity**.

Key factors:
- {complexity_context.get("reasoning", "No samples provided")}

Consider this complexity in your requirements analysis.
"""
```

### 3. Agent 2 Enhancement (Team Planner)
```python
# In team_planner_agent method
recommended_teams = state.get("complexity_analysis", {}).get(
    "impact_on_estimation", {}
).get("recommended_teams", [])

prompt = f"""
...existing prompt...

## RECOMMENDED SPECIALIZED TEAMS:
Based on complexity analysis: {recommended_teams}

IMPORTANT: Only include these specialized teams if the project scope requires them.
- If High complexity with OCR requirements → Include "Document Processing Team"
- If High data complexity → Include "Data Engineering Team"
"""
```

### 4. Agent 3 Enhancement (Task Generator)
```python
# In task_generator_agent method
effort_multiplier = state.get("effort_multiplier", 1.0)

prompt = f"""
...existing prompt...

## EFFORT ADJUSTMENT:
Apply effort multiplier of {effort_multiplier}x to all task estimates.

Example:
- Base estimate: 40 hours
- With multiplier: {40 * effort_multiplier} hours

This accounts for {state.get("complexity_analysis", {}).get("overall_rating", "standard")} complexity.
"""
```

### 5. Agent 5 Enhancement (Rate Assignment)
```python
# In rate_assignment_agent method
rate_multiplier = state.get("rate_multiplier", 1.0)
skill_requirements = state.get("skill_requirements", {})

# Apply rate multipliers
for task in tasks_with_rates:
    base_rate = rate_config.get(task["rate_category"], 30)
    adjusted_rate = base_rate * rate_multiplier
    task["rate_value"] = adjusted_rate
    task["skill_level"] = skill_requirements.get("minimum_level", "Mid")
```

---

## Implementation Files

### Files to Create:
1. `backend/app/services/complexity_analyzer_service.py` - Core analysis logic
2. `backend/app/utils/docling_analyzer.py` - PDF analysis with Docling
3. `backend/app/utils/ocr_analyzer.py` - Image/OCR analysis with Tesseract
4. `backend/app/utils/excel_analyzer.py` - Excel complexity analysis

### Files to Modify:
1. `backend/app/agents/project_estimator/workflow.py` - Add Agent 0, update graph, enhance other agents
2. `backend/app/services/project_estimator/brd_generation_service.py` - Add complexity section to BRD
3. `backend/requirements.txt` - Add pytesseract, python-docx if not present

---

## Complexity Rating Examples

### Example 1: Simple Project
**Samples**: Clean text PDF (5 pages), Simple Excel (2 sheets, no formulas)

**Agent 0 Output:**
```json
{
    "overall_rating": "Low",
    "effort_multiplier": 1.0,
    "rate_multiplier": 1.0,
    "skill_requirements": {
        "minimum_level": "Mid",
        "specialized_skills": []
    }
}
```

**Impact on Estimation:**
- Base estimate: 120 hours
- Final estimate: 120 hours (1.0x)
- Rates: Standard (Baseline)
- Teams: Standard (Backend, Frontend, QA, DevOps)

### Example 2: Medium Project
**Samples**: Multi-column PDF (25 pages, tables), Excel with formulas (15% density)

**Agent 0 Output:**
```json
{
    "overall_rating": "Medium",
    "effort_multiplier": 1.3,
    "rate_multiplier": 1.15,
    "skill_requirements": {
        "minimum_level": "Senior",
        "specialized_skills": ["Document Processing"]
    },
    "recommended_teams": ["Document Processing Team"]
}
```

**Impact on Estimation:**
- Base estimate: 120 hours
- Final estimate: 156 hours (1.3x)
- Rates: +15% (Senior resources)
- Teams: + Document Processing Team

### Example 3: High Complexity Project
**Samples**: Scanned PDF (OCR conf: 0.68), Complex Excel (pivots, macros, 8 sheets)

**Agent 0 Output:**
```json
{
    "overall_rating": "High",
    "effort_multiplier": 1.8,
    "rate_multiplier": 1.30,
    "skill_requirements": {
        "minimum_level": "Senior/Expert",
        "specialized_skills": ["OCR Engineering", "Advanced Data Processing"]
    },
    "recommended_teams": ["OCR Engineering Team", "Data Science Team"]
}
```

**Impact on Estimation:**
- Base estimate: 120 hours
- Final estimate: 216 hours (1.8x)
- Rates: +30% (Expert resources)
- Teams: + OCR Engineering Team + Data Science Team

---

## Benefits

✅ **Objective Complexity Assessment** - Uses actual tools instead of guessing
✅ **Data-Driven Multipliers** - Effort and rate adjustments based on real analysis
✅ **Cascading Intelligence** - Complexity influences all downstream agents
✅ **Specialized Team Detection** - Automatically adds OCR/Data teams when needed
✅ **Transparent Reasoning** - Shows exact complexity factors in BRD
✅ **Accurate Estimates** - Accounts for real project challenges (poor OCR, complex Excel)

---

## Testing Strategy

### Unit Tests
```python
def test_low_complexity_pdf():
    result = analyze_pdf_complexity("simple_text.pdf")
    assert result["structure_score"] < 3.5

def test_high_complexity_ocr():
    result = analyze_image_complexity("scanned_doc.png")
    assert result["ocr_confidence"] < 0.70
    assert result["clarity_rating"] == "Low"
```

### Integration Test
```python
def test_agent_0_in_workflow():
    state = {
        "uploaded_samples": {
            "brd_files": ["test_brd.pdf"],
            "cost_files": ["test_cost.xlsx"]
        }
    }

    result = sample_complexity_analyzer(state)

    assert "complexity_analysis" in result
    assert result["effort_multiplier"] >= 1.0
    assert result["overall_rating"] in ["Low", "Medium", "High"]
```

---

## Next Steps

1. ✅ Create complexity analyzer service
2. ✅ Implement Docling PDF analysis
3. ✅ Implement Tesseract OCR analysis
4. ✅ Implement Excel complexity analysis
5. ✅ Add Agent 0 to workflow graph
6. ✅ Update Agent 1, 2, 3, 5 with complexity context
7. ✅ Add complexity section to BRD template
8. ✅ Test with sample files
9. ✅ Document complexity rating system

---

**Status**: Ready for implementation! 🚀

This will make your Project Estimator truly intelligent - using real tool analysis to drive accurate, data-driven estimates!
