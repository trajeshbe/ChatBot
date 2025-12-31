# Credit Profile Analyzer - Functional Architecture

## Functional Overview

The Credit Profile Analyzer provides a comprehensive set of business functions organized into a logical workflow that transforms raw financial data into professional credit reports. This document details the functional capabilities, business rules, and process flows.

## Functional Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA INPUT FUNCTIONS                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │   CSV Upload   │  │  PDF Upload    │  │  Manual Entry  │   │
│  │   Function     │  │   Function     │  │   (Future)     │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
│           │                  │                     │            │
│           └──────────────────┴─────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                DATA VALIDATION FUNCTIONS                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │  Column Check  │  │   Data Type    │  │  Completeness  │   │
│  │   Validation   │  │   Validation   │  │     Check      │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              DATA PROCESSING FUNCTIONS                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │   Data         │  │   Numeric      │  │   Default      │   │
│  │  Extraction    │  │  Conversion    │  │   Handling     │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              CALCULATION FUNCTIONS                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │   Financial    │  │    Growth      │  │   Benchmark    │   │
│  │    Ratios      │  │   Metrics      │  │  Comparison    │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│            AI ANALYSIS FUNCTIONS                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │ Ratio Insight  │  │   Financial    │  │    Credit      │   │
│  │  Generation    │  │    Insights    │  │    Rating      │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│            REPORT GENERATION FUNCTIONS                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │  Raw Template  │  │    Report      │  │    Export      │   │
│  │   Generation   │  │   Polishing    │  │   Function     │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              OUTPUT DELIVERY FUNCTIONS                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │    Display     │  │    Download    │  │     Print      │   │
│  │   Function     │  │    Function    │  │   (Future)     │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Core Functional Modules

### 1. Data Input Functions

#### 1.1 CSV File Upload Function

**Function Name**: `file_uploader()`
**Purpose**: Accept and validate CSV file uploads for company and financial data

**Inputs**:
- File type: CSV (.csv extension)
- Upload type: Company Information or Financial Ratios
- File size: No explicit limit (Streamlit default ~200MB)

**Processing Logic**:
```
1. User selects CSV file via file picker
2. System reads file into Pandas DataFrame
3. System displays column count and preview
4. System stores DataFrame in session state
5. System enables next processing step
```

**Outputs**:
- DataFrame stored in session state
- Success/error message displayed
- Preview table shown to user
- Validation status updated

**Business Rules**:
- Two CSV files required for complete report
- Files processed independently
- Preview limited to first 3 rows
- Automatic data type inference

**Error Handling**:
- Invalid file format: Display error message
- Corrupted CSV: Show parsing error
- Empty file: Display warning message
- Missing file: Disable processing

#### 1.2 PDF File Upload Function (Legacy)

**Function Name**: `extract_fields_from_pdf()`
**Purpose**: Extract financial data from PDF annual reports

**Inputs**:
- File type: PDF (.pdf extension)
- Content: Annual reports, financial statements
- Format: Text-based PDF (not scanned images)

**Processing Logic**:
```
1. User uploads PDF file
2. System extracts text using pdfplumber
3. System applies regex patterns for data extraction
4. System extracts:
   - Company name and registration
   - Financial figures (revenue, assets, liabilities)
   - Directors and management
   - Legal structure and country
5. System applies default values for missing fields
6. System calculates financial ratios
7. System displays extracted data summary
```

**Outputs**:
- Dictionary of extracted fields
- Extraction success rate notification
- Missing fields identified
- Calculated ratios

**Business Rules**:
- Text-based PDFs only (no OCR)
- Multi-pattern matching for flexibility
- Default values for extraction failures
- Currency agnostic (supports $, €, £, ₹)

**Limitations**:
- Dependent on PDF structure
- Regex pattern matching limitations
- No table extraction
- No multi-page consolidation

### 2. Data Validation Functions

#### 2.1 Company CSV Validation Function

**Function Name**: `validate_company_csv_columns()`
**Purpose**: Validate company information CSV structure

**Validation Rules**:

**Core Required Columns** (must be present):
1. company_name
2. registration_number
3. country

**Expected Columns** (total 19):
- Company Profile: generated_date, incorporation_date, legal_structure
- Contact Information: website, email, phone
- Management: directors, shareholding, group_ownership
- Corporate Structure: affiliate_entities, subsidiaries
- Business Information: primary_industry, business_model, product_services
- Market Information: markets_served, geographic_presence

**Validation Process**:
```
1. Check for core required columns
2. Identify present columns
3. List optional missing columns
4. Return validation result dictionary
```

**Output Structure**:
```python
{
    'valid': True/False,
    'missing_core_columns': [],
    'present_columns': [...],
    'optional_missing': [...],
    'expected_columns': [...]
}
```

**Business Rules**:
- Flexible validation (core + optional)
- Graceful handling of missing optional fields
- Clear communication of missing requirements
- No rejection for optional field absence

#### 2.2 Financial CSV Validation Function

**Function Name**: `validate_financial_csv_columns()`
**Purpose**: Validate financial ratios CSV structure

**Validation Rules**:

**Core Required Columns** (must be present):
1. fiscal_year
2. revenue
3. total_assets
4. equity

**Expected Columns** (total 82):

**Financial Summary** (10 fields):
- revenue, net_income, operating_profit
- total_assets, total_liabilities, equity
- current_assets, current_liabilities
- fiscal_year, reporting_currency

**Historical Data** (6 fields):
- revenue_2022, revenue_2023
- net_income_2022, net_income_2023
- roce_2022, roce_2023

**Growth Metrics** (10 fields):
- net_sales_cagr, net_sales_growth
- net_profit_growth, net_worth_growth
- export_sales_ratio, local_sales_ratio
- trading_sales_ratio, mfg_sales_ratio
- opm_cagr, pat_margin_cagr

**Liquidity Ratios** (2 fields):
- current_ratio, quick_ratio

**Efficiency Ratios** (6 fields):
- inv_turnover, debtor_turnover, creditor_turnover
- wc_days, fa_turnover, ta_turnover

**Leverage Ratios** (11 fields):
- debt_equity, tol_tnw, term_debt_cashprofit
- tl_interest_tb, wc_interest_wcb, ibd_ebitda
- nw_adjta, tnw_ta, ibd_tnw
- contingencies_nw, own_assoc_ta

**Coverage Ratios** (4 fields):
- interest_coverage, dscr
- stock_fafa_ltl, debtors_st_debt

**Profitability Ratios** (13 fields):
- matcost_ratio, gross_margin, op_margin
- pbdt_margin, pbdt_margin2, pbt_margin, pat_margin
- roce, roe, interest_sales, net_margin
- retention_ratio, payout_ratio

**Working Capital Detail** (9 fields):
- bank_fb, creditors_lc, total_bank_borrowings
- other_creditors, net_wc, other_cl
- tca, avg_inventory, total_debtors

**Qualitative Fields** (11 fields):
- legal_proceedings, sanctions_status, litigation_notes
- payment_terms, payment_behavior_summary
- credit_history_notes, external_feedback
- market_risks, outlook_summary
- analyst_commentary, risk_rating, credit_guidance

**Validation Process**:
Same structure as company validation with different field requirements

**Business Rules**:
- Core financial metrics required
- Ratio fields optional (calculated if missing)
- Qualitative fields optional
- Historical data optional but recommended

### 3. Data Processing Functions

#### 3.1 Company Data Processing Function

**Function Name**: `process_company_csv_data()`
**Purpose**: Extract and process company information from DataFrame

**Processing Steps**:

```
1. Validate DataFrame is not empty
2. Extract first row (company record)
3. Initialize processed_data dictionary
4. Add report_date timestamp
5. For each expected field:
   a. Check if field exists in DataFrame
   b. Extract value from first row
   c. Clean and validate value
   d. Apply default if missing/invalid
   e. Store in processed_data
6. Return processed_data dictionary
```

**Data Cleaning Rules**:
- Trim whitespace from strings
- Convert pandas NA to 'N/A'
- Handle empty strings as missing
- Preserve original formatting where possible

**Default Values**:
- Text fields: 'N/A'
- Date fields: 'N/A'
- Contact fields: 'N/A'

**Output**:
Dictionary with 19+ company information fields ready for template rendering

#### 3.2 Financial Data Processing Function

**Function Name**: `process_ratios_csv_data()`
**Purpose**: Extract and process financial ratios from DataFrame

**Processing Steps**:

```
1. Validate DataFrame is not empty
2. Extract first row (company financials)
3. Initialize processed_data dictionary
4. Process text fields:
   a. Extract value
   b. Clean whitespace
   c. Apply defaults
5. Process numeric fields:
   a. Extract value
   b. Call clean_numeric_value()
   c. Handle conversion errors
   d. Apply 0.0 default
6. Return processed_data dictionary
```

**Numeric Cleaning Function**:

**Function Name**: `clean_numeric_value()`
**Purpose**: Robust conversion of various numeric formats

**Cleaning Process**:
```
Input: "€ 2,500,000.50" or "N/A" or 2500000.5

1. Check if value is NaN/null → return 0.0
2. If string:
   a. Remove currency symbols (€, $, £, %)
   b. Remove commas and spaces
   c. Check for 'N/A', 'none', 'null' → return 0.0
   d. Attempt float conversion
   e. Return 0.0 if conversion fails
3. If numeric:
   a. Convert to float
   b. Return 0.0 if conversion fails
4. Return cleaned numeric value
```

**Supported Formats**:
- Currency symbols: $, €, £, ₹, %
- Thousands separators: commas
- Decimals: periods
- Negative values: supported
- Scientific notation: supported

**Business Rules**:
- Zero as default (conservative approach)
- Preserve precision when possible
- Handle missing data gracefully
- No errors for invalid input

#### 3.3 PDF Data Processing Function

**Function Name**: `process_pdf_data()`
**Purpose**: Process extracted PDF data with defaults

**Processing Steps**:

```
1. Call extract_fields_from_pdf()
2. Define default values dictionary (20+ fields)
3. Merge extracted_data with defaults
4. Calculate financial ratios
5. Update data with calculated ratios
6. Return complete data dictionary
```

**Default Values**:
- Company fields: 'N/A' or 'Not Found'
- Financial figures: 0.0
- Dates: 'N/A'
- All mandatory fields covered

**Business Rules**:
- Never return incomplete data
- All fields have default values
- Calculated ratios handle division by zero
- Extraction failures handled gracefully

### 4. Calculation Functions

#### 4.1 Financial Ratio Calculation Function

**Function Name**: `calculate_financial_ratios()`
**Purpose**: Calculate key financial ratios from raw data

**Calculated Ratios**:

**1. Current Ratio**
```
Formula: Current Assets / Current Liabilities
Purpose: Measures short-term liquidity
Interpretation:
  - > 2.0: Excellent liquidity
  - 1.5-2.0: Good liquidity
  - 1.0-1.5: Adequate liquidity
  - < 1.0: Potential concerns
```

**2. Return on Capital Employed (ROCE)**
```
Formula: (Operating Profit / Capital Employed) × 100
Capital Employed = Total Assets - Current Liabilities
Purpose: Measures profitability and efficiency
Interpretation:
  - > 15%: Excellent returns
  - 10-15%: Good returns
  - 5-10%: Moderate returns
  - < 5%: Low returns
```

**3. Gearing Ratio**
```
Formula: Total Liabilities / Equity
Purpose: Measures financial leverage
Interpretation:
  - 0-0.5: Conservative
  - 0.5-1.0: Moderate
  - 1.0-2.0: High
  - > 2.0: Very high
```

**Division by Zero Handling**:
```python
if denominator != 0:
    ratio = numerator / denominator
else:
    ratio = 0.0
```

**Output**:
Dictionary with calculated ratios ready for analysis

#### 4.2 Growth Rate Calculation Functions

**Function Name**: `calculate_growth_rate()`
**Purpose**: Calculate year-over-year growth rate

```
Formula: ((Current - Previous) / Previous) × 100

Example:
  Current Revenue: $2,500,000
  Previous Revenue: $2,300,000
  Growth Rate: ((2,500,000 - 2,300,000) / 2,300,000) × 100 = 8.7%
```

**Function Name**: `calculate_cagr()`
**Purpose**: Calculate Compound Annual Growth Rate

```
Formula: ((Current / Initial)^(1/Years) - 1) × 100

Example:
  Current Value: $2,500,000
  Initial Value: $2,000,000
  Years: 3
  CAGR: ((2,500,000 / 2,000,000)^(1/3) - 1) × 100 = 7.7%
```

**Business Rules**:
- Return 0.0 if denominator is zero
- Return 0.0 if years is zero
- Handle negative growth rates
- Preserve precision (2 decimal places typical)

### 5. AI Analysis Functions

#### 5.1 Ratio Insight Generation Function

**Function Name**: `generate_ratio_insights()`
**Purpose**: Generate AI-powered insights for financial ratios

**Processing Flow**:

```
1. Extract available ratios from financial data
2. Build ratios_to_analyze dictionary
3. Filter out zero values
4. Create structured prompt with:
   - Ratio values
   - Company context
   - Industry information
   - Ratio definitions
5. Call OpenAI API with JSON response format
6. Parse and return insights dictionary
7. Return default insights on error
```

**Analyzed Ratios** (25 ratios):
- Liquidity: current_ratio, quick_ratio
- Leverage: debt_equity, tol_tnw, ibd_tnw
- Efficiency: inv_turnover, debtor_turnover, creditor_turnover, fa_turnover, ta_turnover
- Coverage: interest_coverage, dscr
- Profitability: gross_margin, op_margin, pbdt_margin, pbt_margin, pat_margin, net_margin, roce, roe
- Others: retention_ratio, payout_ratio, matcost_ratio, interest_sales

**AI Prompt Structure**:
- Role: Senior credit analyst
- Task: Generate 15-30 word insights per ratio
- Format: JSON with ratio keys
- Focus: Credit risk implications
- Temperature: 0.2 (high consistency)
- Max Tokens: 1000

**Output Example**:
```json
{
  "current_ratio": "Strong liquidity position with current ratio of 1.8x indicating good short-term debt coverage capacity.",
  "debt_equity": "Conservative leverage at 0.2x suggests low debt burden and strong financial stability.",
  "roce": "Excellent return on capital employed at 18.5% exceeds industry average of 15.2%, demonstrating effective asset utilization."
}
```

**Business Rules**:
- Only analyze non-zero ratios
- Use exact values from data
- Focus on credit risk perspective
- Include industry benchmarks when available
- One insight per ratio
- Professional financial terminology

#### 5.2 Financial Insights Generation Function

**Function Name**: `generate_financial_insights()`
**Purpose**: Generate comprehensive financial insights across categories

**Processing Flow**:

```
1. Prepare financial data for analysis
2. Create detailed insights prompt
3. Call OpenAI API
4. Parse JSON response
5. Validate all required insights present
6. Return insights dictionary
7. Return default insights on error
```

**Insight Categories** (7 types):

**1. Growth Insight**
- Analyzes revenue and earnings growth trends
- Includes year-over-year percentages
- Compares multi-year performance
- Assesses sustainability

**2. Liquidity Insight**
- Evaluates current and quick ratios
- Assesses short-term solvency
- Identifies liquidity risks
- Benchmarks against norms

**3. Efficiency Insight**
- Analyzes operational efficiency metrics
- Reviews working capital management
- Assesses asset turnover
- Identifies operational trends

**4. Leverage Insight**
- Evaluates debt levels
- Analyzes capital structure
- Compares to industry standards
- Assesses financial risk

**5. Coverage Insight**
- Analyzes interest coverage ratios
- Evaluates debt service capability
- Assesses payment capacity
- Identifies coverage risks

**6. Profitability Insight**
- Analyzes profit margins
- Evaluates return metrics (ROCE, ROE)
- Compares to benchmarks
- Assesses profitability trends

**7. Working Capital Insight**
- Analyzes WC management
- Evaluates cash conversion
- Assesses funding efficiency
- Identifies WC trends

**AI Configuration**:
- Model: GPT-4o
- Temperature: 0.3 (balanced)
- Max Tokens: 1500
- Response Format: JSON object
- Prompt: Structured with financial data and guidance

**Output Example**:
```json
{
  "growth_insight": "Revenue grew 8.7% year-over-year from $2.3M to $2.5M while net income increased 11.1%, demonstrating improving profitability.",
  "liquidity_insight": "Current ratio of 2.32x and quick ratio of 1.85x indicate strong short-term liquidity position well above industry norms.",
  "leverage_insight": "Conservative debt-to-equity ratio of 0.71x compares favorably to industry average of 0.85x, indicating prudent financial management."
}
```

**Business Rules**:
- All 7 insights required
- Include specific numbers and percentages
- Compare to industry benchmarks
- Focus on creditworthiness
- Single sentence per insight
- Professional analytical tone

#### 5.3 Credit Rating Generation Function

**Function Name**: `generate_credit_rating()`
**Purpose**: Assign credit rating with detailed justification

**Processing Flow**:

```
1. Extract key financial metrics from data
2. Calculate additional metrics (debt-to-assets, net margin)
3. Create credit rating prompt with:
   - All financial metrics
   - Company and industry context
   - Credit rating scale
   - Analysis instructions
4. Call OpenAI API
5. Parse and validate response
6. Return rating and justification
7. Return default rating on error
```

**Credit Rating Scale**:
```
AAA - Highest credit quality, minimal risk
AA  - High credit quality, very low risk
A   - Good credit quality, low risk
BBB - Adequate credit quality, moderate risk (Investment Grade cutoff)
BB  - Speculative, higher risk
B   - Highly speculative, high risk
CCC - Substantial risk, very high risk
CC  - Extremely speculative
C   - Near default
D   - Default
```

**Key Metrics Analyzed**:
- Current Ratio (liquidity)
- Debt-to-Equity (leverage)
- Interest Coverage (debt service)
- ROCE (profitability)
- Revenue and Net Income (scale and performance)
- Total Assets and Liabilities (size and structure)
- Working Capital (operational health)
- Debt-to-Assets percentage
- Net Margin percentage

**AI Configuration**:
- Model: GPT-4o
- Temperature: 0.2 (high consistency)
- Max Tokens: 800
- Role: Senior credit analyst at rating agency
- Focus: Use exact values, professional assessment

**Output Example**:
```json
{
  "credit_rating": "A",
  "justification": "The company demonstrates strong financial health with excellent liquidity (current ratio of 2.32x), conservative leverage (debt-to-equity of 0.71x), and robust profitability (ROCE of 18.5% exceeding industry average). Strong interest coverage of 12.5x indicates comfortable debt service capacity. These factors support a solid investment-grade rating of A."
}
```

**Business Rules**:
- Use exact numerical values from data
- Provide 3-4 sentence justification
- Consider liquidity, leverage, profitability, stability
- Professional rating agency perspective
- Clear rationale for rating assigned
- Industry context when available

### 6. Report Generation Functions

#### 6.1 Raw Template Generation Function

**Function Name**: `generate_raw_report()`
**Purpose**: Populate Jinja2 template with structured data

**Processing Flow**:

```
1. Load raw_credit_report_template.txt
2. Create Jinja2 Template object
3. Render template with data dictionary:
   - Company information
   - Financial metrics
   - Calculated ratios
   - AI-generated insights
   - Historical trends
   - Qualitative assessments
4. Return populated template text
```

**Template Structure** (10 sections):

**Section 1: Company Overview**
- Company name, registration, country
- Incorporation date, legal structure
- Contact information (website, email, phone)

**Section 2: Ownership & Management**
- Directors and management team
- Shareholding structure
- Group ownership
- Affiliate entities and subsidiaries

**Section 3: Business Operations**
- Primary industry
- Business model
- Products and services
- Markets served
- Geographic presence

**Section 4: Financial Summary**
- Reporting currency and fiscal year
- Revenue, net income, operating profit
- Assets, liabilities, equity
- Current assets and liabilities

**Section 5: Multi-Year Financial Trends**
- Table format showing 3 years
- Revenue progression
- Net income trends
- ROCE evolution

**Section 6: Ratio Dashboard**
- 6.1 Growth & Composition (10 metrics)
- 6.2 Liquidity (2 metrics)
- 6.3 Turnover/Efficiency (6 metrics)
- 6.4 Leverage (11 metrics)
- 6.5 Coverage (4 metrics)
- 6.6 Profitability (12 metrics)
- 6.7 Current-Asset Funding (9 metrics)
- 6.8 Ratio Insights (7 AI insights)

**Section 7: Legal & Compliance**
- Legal proceedings status
- Sanctions status
- Litigation notes

**Section 8: Credit History & Feedback**
- Payment terms
- Payment behavior
- Credit history notes
- External feedback

**Section 9: Analyst Commentary & Outlook**
- Market risks assessment
- Outlook summary
- Analyst commentary

**Section 10: Credit Assessment**
- Risk rating
- Credit guidance
- Recommendation

**Template Features**:
- Variable substitution with defaults
- Conditional field handling
- Professional formatting with ASCII borders
- Table formatting for trends
- Hierarchical section organization

**Output**:
Structured text report (approximately 200 lines) ready for review or polishing

#### 6.2 Report Polishing Function

**Function Name**: `polish_credit_report()`
**Purpose**: Transform raw template into professional narrative

**Processing Flow**:

```
1. Generate credit rating using raw numerical data
2. Create comprehensive polishing prompt with:
   - Raw report content
   - Credit rating information
   - Company context
   - Formatting instructions
   - Tone and style guidelines
3. Call OpenAI API for long-form narrative generation
4. Return professional analyst-quality report
5. Return fallback template on error
```

**Polishing Instructions**:

**Structure Requirements**:
1. Company name as main title
2. Credit rating as subtitle
3. Rating justification section
4. Executive summary
5. Company profile and operations
6. Financial analysis
7. Risk assessment
8. Recommendation/conclusion

**Writing Style**:
- Sophisticated financial terminology
- Analytical frameworks referenced
- Confident, authoritative tone
- Present tense throughout
- Professional analyst perspective

**Content Requirements**:
- Market context and positioning
- Industry peer comparisons
- Forward-looking assessments
- Risk considerations
- Covenant compliance references
- Capital adequacy discussion
- Liquidity position analysis

**Formatting**:
- Section headers with lines/borders
- Bullet points for key metrics
- Professional report layout
- Disclaimer at end
- Institutional presentation quality

**AI Configuration**:
- Model: GPT-4o
- Temperature: 0.4 (balanced creativity)
- Max Tokens: 4000 (long-form content)
- Role: Senior analyst at top-tier rating agency
- Style: Moody's/S&P/Fitch quality

**Output Example Structure**:
```
TECHCORP INDUSTRIES LTD
Credit Rating: A

Rating Justification
[3-4 sentence explanation of credit rating...]

Executive Summary
[Comprehensive overview of credit assessment...]

Company Profile & Operations
[Detailed business description and market position...]

Financial Analysis
[In-depth analysis of financial metrics and trends...]

Risk Assessment
[Evaluation of key risks and mitigating factors...]

Recommendation
[Final credit recommendation and monitoring guidance...]

[Disclaimer]
```

**Business Rules**:
- Professional institutional quality
- Comprehensive coverage of all aspects
- Balanced assessment (strengths and weaknesses)
- Data-driven conclusions
- Clear credit recommendation
- Board presentation ready

#### 6.3 Two-Step Report Generation Function

**Function Name**: `generate_two_step_report()`
**Purpose**: Complete workflow for dual report generation

**Processing Flow**:

```
1. Generate raw report using template
2. Check for errors in raw generation
3. Polish raw report into narrative
4. Return both versions in dictionary
5. Handle errors at each step
```

**Output Structure**:
```python
{
    'raw_report': 'Structured template output...',
    'polished_report': 'Professional narrative...'
}
```

**Error Handling**:
- Template not found: Return error message
- Raw generation fails: Return error in both fields
- Polishing fails: Return raw report + fallback polished
- API error: Return raw report + error message

**Business Rules**:
- Both reports always generated
- Independent error handling
- Raw report never fails (template-based)
- Polished report has fallback
- User always receives output

### 7. User Interface Functions

#### 7.1 Display Functions

**Main Interface Display**:
```python
def main():
    - Display title and description
    - Show file upload section
    - Display data previews
    - Show generation buttons
    - Display results tabs
```

**Generation Interface**:
```python
def show_generation_interface():
    - Display validation status
    - Show three action buttons
    - Handle button clicks
    - Manage workflow cascading
    - Display results
```

**Results Display**:
```python
def display_generated_results():
    - Check available results
    - Create dynamic tabs
    - Display each result type
    - Provide download buttons
    - Format insights display
```

**Instructions Display**:
```python
def show_instructions():
    - Show upload requirements
    - Display CSV format information
    - List sample data files
    - Provide usage guidance
```

#### 7.2 Workflow Management Functions

**Step 1: Generate Insights**:
```python
def generate_insights_step():
    1. Process company CSV data
    2. Process ratios CSV data
    3. Combine into report_data
    4. Generate ratio insights (AI)
    5. Store in session state
    6. Display success message
```

**Step 2: Generate Raw Text**:
```python
def generate_raw_text_step():
    1. Retrieve stored data
    2. Update with ratio insights
    3. Generate comprehensive insights (AI)
    4. Update report_data
    5. Generate raw template (Jinja2)
    6. Store raw_report
    7. Display success message
```

**Step 3: Generate Final Report**:
```python
def generate_final_report_step():
    1. Retrieve raw_report and data
    2. Generate credit rating (AI)
    3. Polish report into narrative (AI)
    4. Store polished_report
    5. Display success message
```

**Cascading Logic**:
- Step 2 checks for Step 1 completion
- Step 3 checks for Steps 1 & 2 completion
- Auto-run missing prerequisites
- Inform user of auto-execution
- Cache all intermediate results

#### 7.3 Download Functions

**Download Raw Report**:
```python
st.download_button(
    label="Download Raw Template Report",
    data=raw_report_text,
    file_name=f"raw_credit_report_{company_name}.txt",
    mime="text/plain"
)
```

**Download Polished Report**:
```python
st.download_button(
    label="Download Polished Credit Report",
    data=polished_report_text,
    file_name=f"polished_credit_report_{company_name}.txt",
    mime="text/plain"
)
```

**Download Ratio Insights**:
```python
insights_text = format_insights(ratio_insights)
st.download_button(
    label="Download Ratio Insights",
    data=insights_text,
    file_name=f"ratio_insights_{company_name}.txt",
    mime="text/plain"
)
```

**File Naming Convention**:
- Include report type prefix
- Include company name (spaces replaced with underscores)
- Use .txt extension
- Timestamp optional (future enhancement)

## Business Process Flows

### Process Flow 1: Standard Credit Report Generation

```
Start
  ↓
User uploads company_info.csv
  ↓
System validates CSV structure
  ↓
User uploads financial_ratios.csv
  ↓
System validates CSV structure
  ↓
System displays data preview
  ↓
User clicks "Generate Insights"
  ↓
System processes both CSVs
  ↓
System generates 25+ ratio insights (AI)
  ↓
System displays insights
  ↓
User clicks "Generate Raw Text"
  ↓
System generates 7 comprehensive insights (AI)
  ↓
System populates Jinja2 template
  ↓
System displays raw report
  ↓
User clicks "Generate Final Report"
  ↓
System generates credit rating (AI)
  ↓
System polishes report into narrative (AI)
  ↓
System displays polished report
  ↓
User reviews all three outputs
  ↓
User downloads desired report(s)
  ↓
End
```

**Time Estimate**: 3-5 minutes total
**User Actions**: 5 (2 uploads, 3 button clicks, review)
**AI API Calls**: 4 (ratio insights, comprehensive insights, credit rating, polishing)

### Process Flow 2: Quick Report Generation

```
Start
  ↓
User uploads both CSV files
  ↓
System auto-validates
  ↓
User clicks "Generate Final Report"
  ↓
System auto-runs Step 1: Insights (AI)
  ↓
System auto-runs Step 2: Raw Template (AI + Jinja2)
  ↓
System runs Step 3: Final Report (AI)
  ↓
System displays all results in tabs
  ↓
User downloads final report
  ↓
End
```

**Time Estimate**: 2-3 minutes total
**User Actions**: 3 (2 uploads, 1 button click, download)
**AI API Calls**: 4 (cascaded automatically)

### Process Flow 3: Insights Only Generation

```
Start
  ↓
User uploads both CSV files
  ↓
System auto-validates
  ↓
User clicks "Generate Insights"
  ↓
System generates ratio insights
  ↓
System displays insights in columns
  ↓
User reviews insights
  ↓
User downloads insights (optional)
  ↓
End
```

**Time Estimate**: 1-2 minutes
**User Actions**: 3 (2 uploads, 1 button click)
**AI API Calls**: 1 (ratio insights only)
**Use Case**: Quick financial ratio analysis without full report

## Function Integration Map

```
Main Application (app.py)
├── File Upload
│   ├── company_file_uploader()
│   └── ratios_file_uploader()
├── Validation
│   ├── validate_company_csv_columns()
│   └── validate_financial_csv_columns()
├── Processing
│   ├── process_company_csv_data()
│   ├── process_ratios_csv_data()
│   └── clean_numeric_value()
├── Generation Workflow
│   ├── generate_insights_step()
│   │   ├── process_company_csv_data()
│   │   ├── process_ratios_csv_data()
│   │   └── generate_ratio_insights() [AI]
│   ├── generate_raw_text_step()
│   │   ├── generate_financial_insights() [AI]
│   │   └── generate_raw_report() [Jinja2]
│   └── generate_final_report_step()
│       ├── generate_credit_rating() [AI]
│       └── polish_credit_report() [AI]
└── Display & Download
    ├── display_generated_results()
    ├── download_raw_report()
    ├── download_polished_report()
    └── download_insights()
```

## Quality Assurance Functions

### Data Quality Checks

1. **CSV Structure Validation**
   - Column presence verification
   - Data type checking
   - Completeness assessment

2. **Numeric Value Validation**
   - Range checking (future)
   - Reasonableness tests (future)
   - Outlier detection (future)

3. **Ratio Consistency Checks** (future)
   - Cross-ratio validation
   - Balance sheet equation verification
   - Mathematical consistency

### Output Quality Checks

1. **Template Rendering**
   - All placeholders filled
   - No missing sections
   - Proper formatting

2. **AI Output Validation**
   - JSON format compliance
   - Required fields present
   - Content reasonableness

3. **Report Completeness**
   - All sections populated
   - Minimum content length
   - Professional formatting maintained

## Error Handling Strategy

### Function-Level Error Handling

All functions implement try-except blocks:
```python
try:
    # Function logic
except Exception as e:
    logger.error(f"Error in function_name: {e}")
    return default_value
```

### User-Facing Error Messages

- Clear, non-technical language
- Specific actionable guidance
- Suggested remediation steps
- Contact information (if applicable)

### Fallback Mechanisms

1. **Data Processing**: Default values
2. **AI Functions**: Default insights
3. **Template Rendering**: Fallback template
4. **Report Polishing**: Structured fallback

## Future Functional Enhancements

### Planned Functions

1. **Batch Processing**
   - Multi-company upload
   - Parallel processing
   - Consolidated reporting

2. **Custom Templates**
   - User-defined templates
   - Industry-specific formats
   - Regional variations

3. **Advanced Analytics**
   - Trend analysis
   - Peer benchmarking
   - What-if scenarios

4. **Export Options**
   - PDF generation
   - Excel output
   - Word document export

5. **Collaboration Features**
   - Comment and annotation
   - Approval workflows
   - Version control

## Conclusion

The functional architecture of the Credit Profile Analyzer demonstrates a well-designed, modular system that efficiently transforms raw financial data into professional credit reports through a combination of data processing, AI-powered analysis, and template-based report generation. The three-step workflow provides flexibility while the cascading execution ensures ease of use.

---

**Document Version**: 1.0
**Last Updated**: December 2025
**Document Owner**: Product Management & Development Team
