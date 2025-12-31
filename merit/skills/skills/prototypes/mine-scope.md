# MineScope CRU - Mining Intelligence Platform

You are an AI assistant specialized in the **MineScope CRU** prototype, an AI-powered mining intelligence platform that automates the extraction of commodity production data from quarterly and annual reports.

## Project Overview

MineScope CRU is a Streamlit-based platform that dramatically reduces the time needed to extract mining production data from PDF reports. It uses AI auto-detection, intelligent extraction, and interactive review capabilities to process reports in 15 minutes instead of 5.5 hours.

**Location**: `/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/mine_scope/`

## Core Capabilities

### Auto-Detection
- Automatic identification of companies, assets, and commodities
- Intelligent parsing of PDF reports
- 200+ variable mappings across 9 commodity types

### Data Extraction
- 10-30 second processing per company-asset-commodity combination
- AI-powered extraction using OpenAI GPT-4o
- Pydantic validation for data quality
- 90%+ accuracy (99%+ after human review)

### Interactive Review
- Field-by-field validation
- Inline editing capabilities
- Data quality indicators
- Asset comparison matrix

### Insights Assistant
- Conversational chatbot for data analysis
- RAG-based on extracted data
- Historical trend analysis
- Production comparison queries

## Technology Stack

```
Language: Python 3.11+
Framework: Streamlit
AI Engine: OpenAI GPT-4o
PDF Processing: PyPDF2
Data Validation: Pydantic
Reference Data: JSON files
Configuration: ConfigParser
```

## Architecture

### Component Structure

```
app.py                          # Main application
modules/
  ├── pdf_extractor.py         # PDF text extraction
  ├── auto_detector.py         # Company/asset/commodity detection
  ├── data_extractor.py        # Variable extraction
  └── insights_chatbot.py      # Conversational AI
reference_data/
  ├── company_list.json
  ├── asset_list.json
  ├── commodity_list.json
  └── variable_mapping.json
config.ini                      # Configuration
```

### User Workflow

```
Tab 1: Upload Source
  ↓ Upload PDF
  ↓ Auto-detect entities
  ↓ Review & select combinations
  ↓
Tab 2: Review Data
  ↓ Extract variables
  ↓ Validate & edit
  ↓ Export to CSV
  ↓
Tab 3: Asset Compare
  ↓ Select assets
  ↓ Compare metrics
  ↓
Tab 4: Insights Assistant
  ↓ Ask questions
  ↓ Get AI-powered insights
```

## Common Implementation Tasks

### 1. Running the Application

```bash
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/mine_scope/

# Set API key
export OPENAI_API_KEY="your-api-key"

# Install dependencies
pip install streamlit openai pandas pydantic pypdf2

# Run application
streamlit run app.py
```

### 2. Auto-Detecting Entities from PDF

```python
from modules.auto_detector import AutoDetector

# Initialize detector
detector = AutoDetector()

# Upload and process PDF
pdf_path = "quarterly_report_Q3_2024.pdf"
detected = detector.detect_entities(pdf_path)

# Results:
{
    "companies": ["Newmont", "Barrick Gold"],
    "assets": ["Boddington Mine", "Cadia Valley"],
    "commodities": ["Gold", "Copper"],
    "period": "Q3 2024"
}

# User reviews and selects combinations:
# - Newmont / Boddington / Gold
# - Newmont / Boddington / Copper
# - Barrick / Cadia Valley / Gold
```

### 3. Extracting Variables

```python
from modules.data_extractor import DataExtractor

# Initialize extractor
extractor = DataExtractor()

# Extract for specific combination
combination = {
    "company": "Newmont",
    "asset": "Boddington Mine",
    "commodity": "Gold",
    "period": "Q3 2024"
}

# Extract variables
data = extractor.extract_variables(pdf_text, combination)

# Result (200+ variables possible):
{
    # Supply Variables
    "production_tonnes": 125000,
    "production_units": "tonnes",
    "ore_mined": 2500000,
    "ore_grade": 0.95,
    "recovery_rate": 92.3,
    ...

    # Cost Variables
    "cash_cost_per_unit": 850,
    "aisc_per_unit": 1150,
    "capex": 25000000,
    ...

    # ESG Variables
    "water_consumption": 1200000,
    "energy_consumption": 450000,
    "co2_emissions": 125000,
    ...

    # Guidance Variables
    "production_guidance": "450-500k oz",
    "cost_guidance": "$900-950/oz",
    ...
}
```

### 4. Interactive Review and Validation

```python
import streamlit as st

# Display extracted data for review
for variable, value in extracted_data.items():
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        st.write(variable)

    with col2:
        # Editable field
        edited_value = st.text_input(
            f"edit_{variable}",
            value=str(value),
            key=f"edit_{variable}"
        )

    with col3:
        # Confidence indicator
        confidence = data_quality_check(variable, value)
        st.write(f"✓ {confidence}%" if confidence > 80 else f"⚠ {confidence}%")

    # Update if edited
    if edited_value != str(value):
        extracted_data[variable] = edited_value
```

### 5. Using the Insights Assistant

```python
from modules.insights_chatbot import InsightsChatbot

# Initialize chatbot with extracted data
chatbot = InsightsChatbot(extracted_data)

# Ask questions
questions = [
    "What was the gold production in Q3?",
    "How does the cash cost compare to last quarter?",
    "Show me the top 3 producing assets",
    "What are the environmental metrics?"
]

for question in questions:
    answer = chatbot.ask(question)
    print(f"Q: {question}")
    print(f"A: {answer}\n")

# Example output:
# Q: What was the gold production in Q3?
# A: Boddington Mine produced 125,000 ounces of gold in Q3 2024,
#    which is 5% higher than Q2 2024 (119,000 oz).
```

## Supported Commodities (9)

### Major Commodities (Full Variable Set)
1. **Gold**: 26 variables (13 supply, 4 cost, 6 ESG, 3 guidance)
2. **Copper**: 33 variables (17 supply, 7 cost, 7 ESG, 2 guidance)
3. **Nickel**: 30 variables (14 supply, 7 cost, 7 ESG, 2 guidance)
4. **Lead-Zinc**: 27 variables (11 supply, 7 cost, 7 ESG, 2 guidance)

### Minor Commodities (Basic Variables)
5. **Silver**: 2 variables
6. **Cobalt**: 2 variables
7. **Platinum**: 2 variables
8. **Palladium**: 2 variables
9. **Molybdenum**: 2 variables

## Variable Categories

### Supply Variables (Production Metrics)
- Production volume (tonnes/ounces)
- Ore mined, processed
- Head grade, recovery rate
- Concentrate grade
- Stockpile levels

### Cost Variables (Financial Metrics)
- Cash cost per unit
- AISC (All-in Sustaining Cost)
- Total cost of production
- CAPEX, OPEX
- Revenue per unit

### ESG Variables (Environmental/Social)
- Water consumption
- Energy consumption
- CO2 emissions
- Waste generated
- Safety metrics (TRIFR, LTIFR)
- Community investment

### Guidance Variables (Forward-Looking)
- Production guidance
- Cost guidance
- Capital expenditure plans

## Best Practices

### PDF Upload and Detection

1. **File Quality**: Use text-searchable PDFs (not scanned images)
2. **Complete Reports**: Quarterly/annual reports with full data
3. **Standard Format**: Official company reports work best
4. **File Size**: <50MB recommended
5. **Review Auto-Detection**: Always verify detected entities

### Data Extraction

1. **Select Carefully**: Choose relevant combinations only
2. **One at a Time**: Process combinations sequentially
3. **Monitor Progress**: Watch for extraction status
4. **API Limits**: Be aware of OpenAI rate limits
5. **Save Frequently**: Export data regularly

### Data Validation

1. **Check Units**: Verify units match (tonnes vs. ounces)
2. **Range Validation**: Ensure values are reasonable
3. **Cross-Check**: Compare with previous periods
4. **Edit Immediately**: Fix errors during review
5. **Flag Uncertainties**: Mark low-confidence fields

### Asset Comparison

1. **Like-for-Like**: Compare similar asset types
2. **Same Period**: Use consistent time periods
3. **Same Commodity**: Compare same commodity metrics
4. **Normalize**: Consider asset size when comparing
5. **Context**: Account for geography, ore type

## Processing Time Breakdown

| Operation | Duration | Notes |
|-----------|----------|-------|
| PDF Upload | <5 sec | Depends on file size |
| Auto-Detection | 10-30 sec | 1 OpenAI API call |
| Data Extraction (per combo) | 10-30 sec | 1 API call each |
| Review & Validation | 5-10 min | Human time |
| **Total (typical report)** | **~15 min** | Average for 10 combos |

### Cost per Report

| Component | Cost | Annual (200 reports) |
|-----------|------|---------------------|
| OpenAI API | $1.08 | $216 |
| Analyst time (0.25h) | $7.50 | $1,500 |
| Infrastructure | $0.50 | $100 |
| **Total** | **$9.08** | **$1,816** |
| **vs. Manual** | **Save $155.92** | **Save $31,184** |

## Business Value

### Time Savings

- **Before**: 5.5 hours per report
- **After**: 15 minutes per report
- **Savings**: 95% (5.25 hours saved)

### Cost Savings

- **Cost per Report**: $155.92 saved
- **Annual Savings** (200 reports): $31,184
- **ROI**: 2,813% (first year)
- **Payback Period**: 2 weeks

### Quality Improvement

- **AI Accuracy**: 90%+
- **After Review**: 99%+
- **Consistency**: 100% (standardized format)
- **Completeness**: 95%+ fields populated

## Debugging Guide

### Common Issues

**Issue**: Auto-detection not finding entities
```python
# Check PDF text extraction
from modules.pdf_extractor import extract_text
text = extract_text(pdf_path)
print(f"Extracted {len(text)} characters")
print(text[:500])  # Check first 500 chars

# Verify reference data loaded
from modules.auto_detector import load_reference_data
ref_data = load_reference_data()
print(f"Companies: {len(ref_data['companies'])}")
print(f"Assets: {len(ref_data['assets'])}")
```

**Issue**: Extraction failing or returning empty
```python
# Check API key
import os
print(f"API Key set: {'OPENAI_API_KEY' in os.environ}")

# Verify PDF text contains data
if "production" not in text.lower():
    print("Warning: PDF may not contain production data")

# Try with smaller text sample
sample = text[:5000]  # First 5000 characters
result = extractor.extract_variables(sample, combination)
```

**Issue**: Data quality low
```python
# Provide more context in extraction
context = {
    "company": company,
    "asset": asset,
    "commodity": commodity,
    "period": period,
    "previous_data": load_previous_quarter_data()
}

# Use previous data for validation
def validate_against_previous(new_value, prev_value, tolerance=0.3):
    """Check if new value is within reasonable range of previous"""
    if prev_value and new_value:
        diff = abs(new_value - prev_value) / prev_value
        return diff < tolerance
```

## Documentation References

**Comprehensive Documentation**: `/documentation/` folder
- `README.md`: Documentation index
- `01_PROJECT_OVERVIEW.md`: Project overview
- `02_TECHNICAL_ARCHITECTURE.md`: Technical architecture
- `03_BUSINESS_VALUE_ANALYSIS.md`: ROI analysis
- `04_USER_GUIDE.md`: Complete user guide
- `05_API_REFERENCE.md`: Developer reference

**Project Status**: Production-ready prototype
**Last Updated**: December 2025
