# Credit Profile Analyzer

You are an AI assistant specialized in the **Credit Profile Analyzer** prototype, an AI-powered system that automates credit report generation from financial data.

## Project Overview

The Credit Profile Analyzer transforms raw financial data into professional credit reports in minutes instead of hours. It combines AI-powered analysis using OpenAI GPT-4o with structured data processing to generate institution-grade credit reports with comprehensive insights and credit ratings.

**Location**: `/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/credit_profile_analyzer/`

## Core Capabilities

### Three-Step Workflow

1. **Generate Insights**: AI-powered ratio analysis (25+ ratio insights, 7 comprehensive insights, credit rating)
2. **Generate Raw Text**: Structured data template with all ratios and metadata
3. **Generate Final Report**: Polished professional narrative ready for distribution

### Key Features

- 82 financial ratio fields supported
- Dual CSV upload (company info + financial ratios)
- Automatic data validation and cleaning
- AI-powered insights generation
- Professional narrative polishing
- Institution-grade quality output
- Download capability (text files)

## Technology Stack

```
Language: Python 3.11+
Framework: Streamlit 1.46.1+
AI Service: OpenAI GPT-4o API
Data Processing: Pandas 2.3.0+
Template Engine: Jinja2 3.1.6+
PDF Processing: pdfplumber 0.11.7+
Configuration: python-dotenv
```

## Architecture

### Component Structure

```
app.py                  # Main Streamlit application
templates/
  ├── insights_template.jinja2     # Insights generation
  ├── raw_text_template.jinja2     # Raw report template
  └── final_report_template.jinja2 # Polished report
utils/
  ├── data_processor.py  # CSV processing and validation
  ├── ai_generator.py    # AI insights generation
  └── report_builder.py  # Report assembly
attached_assets/
  ├── sample_company_info.csv
  └── sample_financial_ratios.csv
```

### Processing Flow

```
CSV Upload (Company + Ratios)
  ↓
Data Validation & Cleaning
  ↓
[Step 1] Generate AI Insights → 25+ ratio insights
  ↓                              7 comprehensive insights
[Step 2] Generate Raw Text   →  Credit rating + justification
  ↓                              Structured template
[Step 3] Generate Final Report → Professional narrative
  ↓                              Institution formatting
Download Report (TXT)
```

## Common Implementation Tasks

### 1. Running the Application

```bash
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/credit_profile_analyzer/

# Set up environment
export OPENAI_API_KEY="your-api-key"

# Install dependencies
pip install streamlit pandas openai jinja2 pdfplumber python-dotenv

# Run application
streamlit run app.py
```

### 2. Preparing Input Data

**Company Info CSV** (`company_info.csv`):
```csv
company_name,industry,fiscal_year,report_date,analyst_name
Acme Corp,Manufacturing,2024,2024-12-20,John Smith
```

**Financial Ratios CSV** (`financial_ratios.csv`):
```csv
ratio_name,value,unit,period
Current Ratio,2.5,ratio,2024
Quick Ratio,1.8,ratio,2024
Debt to Equity,0.65,ratio,2024
ROE,15.2,%,2024
ROA,8.5,%,2024
Profit Margin,12.3,%,2024
Asset Turnover,1.4,times,2024
...
```

### 3. Generating a Credit Report

```python
from utils.data_processor import DataProcessor
from utils.ai_generator import AIGenerator
from utils.report_builder import ReportBuilder

# Initialize components
processor = DataProcessor()
ai_gen = AIGenerator()
builder = ReportBuilder()

# Load data
company_info = processor.load_company_info('company_info.csv')
ratios = processor.load_financial_ratios('ratios.csv')

# Validate data
validated_data = processor.validate_data(company_info, ratios)

# Step 1: Generate insights
insights = ai_gen.generate_insights(validated_data)
# Returns: {
#   'ratio_insights': [...],  # 25+ insights
#   'comprehensive_insights': [...],  # 7 insights
#   'credit_rating': 'BBB+',
#   'rating_justification': '...'
# }

# Step 2: Generate raw text
raw_report = builder.generate_raw_text(validated_data, insights)

# Step 3: Generate final report
final_report = ai_gen.polish_report(raw_report)

# Save report
with open('credit_report.txt', 'w') as f:
    f.write(final_report)
```

### 4. Customizing Report Templates

Edit Jinja2 templates in `/templates/`:

```jinja2
{# insights_template.jinja2 #}
CREDIT ANALYSIS FOR {{ company_name }}

FINANCIAL RATIO INSIGHTS:
{% for insight in ratio_insights %}
- {{ insight.ratio_name }}: {{ insight.analysis }}
{% endfor %}

COMPREHENSIVE ASSESSMENT:
{% for insight in comprehensive_insights %}
{{ loop.index }}. {{ insight.category }}: {{ insight.analysis }}
{% endfor %}

CREDIT RATING: {{ credit_rating }}
Justification: {{ rating_justification }}
```

### 5. Adding New Financial Ratios

```python
# Add to supported ratios list
new_ratio = {
    'name': 'Interest Coverage Ratio',
    'category': 'Solvency',
    'formula': 'EBIT / Interest Expense',
    'healthy_range': (3.0, float('inf')),
    'interpretation': {
        'high': 'Strong ability to cover interest payments',
        'medium': 'Adequate interest coverage',
        'low': 'Potential difficulty meeting interest obligations'
    }
}

# Update ratio mapping
ratio_mapping['Interest Coverage'] = new_ratio

# Add to insights generation prompt
insights_prompt += """
Analyze the Interest Coverage Ratio and provide insights on
the company's ability to meet its interest obligations.
"""
```

## Key Financial Ratio Categories

### Liquidity Ratios (Short-term solvency)
- Current Ratio
- Quick Ratio
- Cash Ratio
- Working Capital

### Solvency Ratios (Long-term viability)
- Debt to Equity
- Debt to Assets
- Interest Coverage
- Equity Ratio

### Profitability Ratios
- ROE (Return on Equity)
- ROA (Return on Assets)
- Profit Margin
- Gross Margin
- Operating Margin

### Efficiency Ratios
- Asset Turnover
- Inventory Turnover
- Receivables Turnover
- Payables Turnover

### Market Ratios
- P/E Ratio
- Price to Book
- Dividend Yield
- EPS

## AI Insights Generation

### Ratio-Level Insights (25+)

```python
# Example AI-generated insights
insights = {
    "Current Ratio (2.5)": "Strong liquidity position with current assets 2.5x current liabilities, indicating robust short-term financial health.",
    "Debt to Equity (0.65)": "Conservative leverage with debt at 65% of equity, suggesting low financial risk and strong balance sheet.",
    "ROE (15.2%)": "Above-average return on equity indicates efficient use of shareholder capital."
}
```

### Comprehensive Insights (7 categories)

1. **Financial Position**: Overall balance sheet strength
2. **Profitability Analysis**: Earnings quality and trends
3. **Liquidity Assessment**: Short-term payment capacity
4. **Solvency Evaluation**: Long-term financial stability
5. **Operational Efficiency**: Asset utilization effectiveness
6. **Risk Assessment**: Key financial risks identified
7. **Strategic Outlook**: Future performance expectations

### Credit Rating Scale

```
AAA: Exceptionally strong
AA+, AA, AA-: Very strong
A+, A, A-: Strong
BBB+, BBB, BBB-: Adequate (Investment Grade threshold)
BB+, BB, BB-: Speculative
B+, B, B-: Highly speculative
CCC and below: Substantial risk
```

## Best Practices

### Data Preparation

1. **Completeness**: Include all available financial ratios
2. **Accuracy**: Verify ratio calculations before upload
3. **Consistency**: Use standard ratio names and units
4. **Timeliness**: Use most recent fiscal period data
5. **Context**: Include industry and company information

### Report Generation

1. **Step-by-Step**: Follow the three-step workflow sequentially
2. **Review Insights**: Validate AI-generated insights for accuracy
3. **Edit Raw Text**: Modify raw report before final generation
4. **Quality Check**: Review final report for coherence
5. **Human Oversight**: Always review AI outputs before distribution

### Credit Analysis

1. **Comparative Analysis**: Compare ratios to industry benchmarks
2. **Trend Analysis**: Consider historical ratio trends
3. **Qualitative Factors**: Supplement with non-financial insights
4. **Risk Factors**: Identify and highlight key risks
5. **Recommendations**: Provide actionable recommendations

## Debugging Guide

### Common Issues

**Issue**: CSV upload failing
```python
# Verify CSV format
import pandas as pd
df = pd.read_csv('company_info.csv')
print(df.head())
print(df.columns.tolist())

# Check for required columns
required = ['company_name', 'industry', 'fiscal_year']
missing = set(required) - set(df.columns)
if missing:
    print(f"Missing columns: {missing}")
```

**Issue**: AI insights generation failing
```python
# Check API key
import os
if not os.getenv('OPENAI_API_KEY'):
    print("OpenAI API key not set")

# Verify data format
print(f"Data type: {type(financial_data)}")
print(f"Data keys: {financial_data.keys()}")

# Test with minimal data
test_data = {'Current Ratio': 2.5}
insights = ai_gen.generate_insights(test_data)
```

**Issue**: Report formatting issues
```python
# Check template rendering
from jinja2 import Template
template = Template(open('templates/final_report_template.jinja2').read())
output = template.render(company_name='Test Corp', ratios={})
print(output[:500])  # Check first 500 characters
```

## Business Value

### Time and Cost Savings

**Manual Process**:
- Time: 5-7 hours per report
- Cost: $150-200 (analyst time)

**Automated Process**:
- Time: 30 minutes (5 min AI + 25 min review)
- Cost: $24 ($1 API + $23 analyst review)

**Savings**: 95% time reduction, 88% cost reduction

### Productivity Impact

- **Before**: 20 reports/analyst/month
- **After**: 200 reports/analyst/month
- **Increase**: 10x productivity

### ROI

**Investment**: $35,000 (Year 1)
**Annual Benefits**: $360,000 (10 analysts)
**ROI**: 239% (Year 1)
**Payback**: 3.5 months

## Documentation References

**Comprehensive Documentation**: `/documentation/` folder
- `README.md`: Documentation index
- `01_Business_Use_Case_and_Objectives.md`: Business case
- `02_Technical_Architecture.md`: System design
- `03_Functional_Architecture.md`: Functional specs
- `04_User_Guide.md`: User instructions
- `05_Business_Value.md`: ROI analysis

## Extension Points

### Adding Database Storage

```python
import sqlite3

def save_report_to_db(company_name, report_data):
    """Save generated report to database"""
    conn = sqlite3.connect('credit_reports.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO reports
        (company_name, fiscal_year, credit_rating, report_text, generated_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (company_name, report_data['fiscal_year'],
          report_data['credit_rating'], report_data['report_text'],
          datetime.now()))

    conn.commit()
    conn.close()
```

### API Endpoints

```python
from fastapi import FastAPI, UploadFile

app = FastAPI()

@app.post("/api/generate-report")
async def generate_report(
    company_info: UploadFile,
    financial_ratios: UploadFile
):
    """API endpoint for credit report generation"""
    # Process files
    processor = DataProcessor()
    company_data = processor.load_company_info(company_info.file)
    ratios_data = processor.load_financial_ratios(financial_ratios.file)

    # Generate report
    builder = ReportBuilder()
    report = builder.generate_full_report(company_data, ratios_data)

    return {"report": report, "status": "success"}
```

### Batch Processing

```python
def batch_generate_reports(companies_dir):
    """Generate reports for multiple companies"""
    for company_folder in os.listdir(companies_dir):
        company_path = os.path.join(companies_dir, company_folder)

        company_info = os.path.join(company_path, 'info.csv')
        ratios = os.path.join(company_path, 'ratios.csv')

        try:
            report = generate_report(company_info, ratios)
            save_report(report, company_folder)
            print(f"✓ Generated report for {company_folder}")
        except Exception as e:
            print(f"✗ Failed for {company_folder}: {e}")
```

**Project Status**: Production-ready prototype
**Last Updated**: December 2025
