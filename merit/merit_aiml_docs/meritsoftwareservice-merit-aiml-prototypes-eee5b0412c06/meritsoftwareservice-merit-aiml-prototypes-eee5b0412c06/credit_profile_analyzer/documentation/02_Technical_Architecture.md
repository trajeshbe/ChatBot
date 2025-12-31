# Credit Profile Analyzer - Technical Architecture

## Architecture Overview

The Credit Profile Analyzer is built as a modern web application using a modular, AI-powered architecture designed for scalability, maintainability, and extensibility.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                        │
│                     (Streamlit Web Interface)                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ File Upload  │  │ Data Preview │  │   Report     │         │
│  │  Component   │  │  Component   │  │  Generator   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                          │
│                      (Business Logic)                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │     CSV      │  │   Financial  │  │     PDF      │         │
│  │  Processing  │  │    Ratio     │  │  Extraction  │         │
│  │    Module    │  │  Calculator  │  │    Module    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        AI SERVICES LAYER                         │
│                    (OpenAI GPT-4o Integration)                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │    Ratio     │  │  Financial   │  │    Credit    │         │
│  │   Insights   │  │   Insights   │  │    Rating    │         │
│  │  Generator   │  │  Generator   │  │  Generator   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  ┌──────────────────────────────────────────────────┐          │
│  │          Report Polishing Module                 │          │
│  │    (Raw Template → Professional Narrative)       │          │
│  └──────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     TEMPLATE ENGINE LAYER                        │
│                        (Jinja2 Templates)                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐                            │
│  │     Raw      │  │   Original   │                            │
│  │   Template   │  │   Template   │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA STORAGE LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Session    │  │   Template   │  │    Sample    │         │
│  │    State     │  │    Files     │  │  Data Files  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## System Components

### 1. Presentation Layer

#### Streamlit Web Application (app.py)

**Technology**: Streamlit 1.46.1+
**Purpose**: User interface and interaction management

**Key Features**:
- Wide layout configuration for optimal data display
- Dual CSV file upload interface
- Real-time data preview with dataframe widgets
- Three-button workflow interface
- Tabbed results display
- Download functionality for all report formats

**Component Architecture**:
```python
main()
├── File Upload Section
│   ├── Company Information CSV Uploader
│   └── Financial Ratios CSV Uploader
├── Auto-Processing Engine
│   └── Session State Management
├── Generation Interface
│   ├── Generate Insights Button
│   ├── Generate Raw Text Button
│   └── Generate Final Report Button
└── Results Display
    ├── Final Report Tab
    ├── Raw Text Tab
    └── Ratio Insights Tab
```

**Session State Management**:
```python
st.session_state = {
    'csv_validated': bool,
    'company_df': DataFrame,
    'ratios_df': DataFrame,
    'ratio_insights': Dict,
    'raw_report_data': Dict,
    'report_data': Dict,
    'raw_report': str,
    'polished_report': str
}
```

**User Workflow**:
1. Upload both CSV files
2. Automatic validation and preview
3. Choose generation step(s):
   - Insights only
   - Raw template (auto-runs insights if needed)
   - Final report (auto-runs all previous steps if needed)
4. View results in tabbed interface
5. Download reports in text format

### 2. Application Layer

#### 2.1 Data Processing Module (utils/data_processor.py)

**Purpose**: CSV validation and data extraction

**Key Functions**:

```python
def validate_company_csv_columns(df) -> Dict
    """
    Validates company CSV structure
    Returns: {
        'valid': bool,
        'missing_core_columns': List[str],
        'present_columns': List[str],
        'optional_missing': List[str],
        'expected_columns': List[str]
    }
    """
    Core Required: company_name, registration_number, country
    Total Expected: 19 columns

def validate_financial_csv_columns(df) -> Dict
    """
    Validates financial CSV structure
    Returns: Same structure as company validation
    """
    Core Required: fiscal_year, revenue, total_assets, equity
    Total Expected: 82 columns

def process_company_csv_data(df) -> Dict
    """
    Extracts and processes company information
    Handles missing values with 'N/A' defaults
    """
    Fields: Company details, ownership, operations, etc.

def process_ratios_csv_data(df) -> Dict
    """
    Extracts and processes financial ratios
    Handles numeric conversion and defaults
    """
    Fields: 68 financial ratios and metrics
```

**Data Cleaning**:
```python
def clean_numeric_value(value):
    """
    Robust numeric conversion:
    - Removes currency symbols (€, $, £, %)
    - Handles commas and spaces
    - Manages N/A and null values
    - Returns 0.0 for invalid data
    """
```

**CSV Structure**:

Company Information CSV (19 columns):
- Company Profile: name, registration_number, country, incorporation_date
- Legal Structure: legal_structure, website, email, phone
- Management: directors, shareholding, group_ownership
- Business Operations: primary_industry, business_model, products/services
- Market Information: markets_served, geographic_presence

Financial Ratios CSV (82 columns):
- Financial Summary: fiscal_year, revenue, net_income, assets, liabilities
- Historical Data: Multi-year revenue and income trends
- Growth Metrics: CAGR, year-over-year growth rates
- Liquidity Ratios: current_ratio, quick_ratio
- Efficiency Ratios: turnover ratios for inventory, debtors, creditors
- Leverage Ratios: debt_equity, gearing metrics
- Coverage Ratios: interest_coverage, DSCR
- Profitability Ratios: margins, ROCE, ROE
- Working Capital: detailed funding and utilization metrics

#### 2.2 Ratio Calculator Module (utils/ratio_calculator.py)

**Purpose**: Calculate financial ratios from raw data

**Key Functions**:

```python
def calculate_financial_ratios(data) -> Dict:
    """
    Calculates key financial ratios:
    - Current Ratio = Current Assets / Current Liabilities
    - ROCE = Operating Profit / Capital Employed
    - Gearing = Total Liabilities / Equity

    Handles division by zero gracefully
    """

def get_ratio_interpretation(ratio_name, ratio_value) -> str:
    """
    Provides human-readable interpretation
    Categories: Excellent, Good, Adequate, Poor
    Industry benchmarks included
    """
```

**Ratio Interpretation Framework**:
```python
interpretations = {
    'current_ratio': {
        'excellent': (2.0, ∞),
        'good': (1.5, 2.0),
        'adequate': (1.0, 1.5),
        'poor': (0.0, 1.0)
    },
    'roce': {
        'excellent': (15.0, ∞),
        'good': (10.0, 15.0),
        'moderate': (5.0, 10.0),
        'poor': (0.0, 5.0)
    },
    # Similar structures for other ratios
}
```

#### 2.3 PDF Extraction Module (utils/extract_pdf.py)

**Purpose**: Extract financial data from PDF annual reports

**Technology**: pdfplumber 0.11.7+

**Key Functions**:

```python
def extract_fields_from_pdf(pdf_file) -> Dict:
    """
    Main orchestrator for PDF extraction
    Extracts: company info, financials, directors
    Uses pattern-based matching with regex
    """

def extract_company_name(text) -> str:
    """
    Patterns: "Company Name:", "Name:", etc.
    Fallback handling for extraction failures
    """

def extract_financial_figures(text) -> Dict:
    """
    Patterns for financial data:
    - Revenue: "Revenue:", "Sales:", "Turnover:"
    - Profit: "Net Income:", "Profit:", "Earnings:"
    - Assets/Liabilities: Balance sheet terms
    Currency handling: $, €, £, ₹
    """

def extract_company_details(text) -> Dict:
    """
    Registration number, country, legal structure
    Multi-pattern matching for flexibility
    """

def extract_directors(text) -> str:
    """
    Director and management information
    List extraction and formatting
    """
```

**Extraction Strategy**:
- Text-based extraction (not OCR-dependent)
- Pattern-based matching using regex
- Graceful fallback to default values
- Multi-currency support
- Robust error handling

### 3. AI Services Layer

#### 3.1 Insight Generator Module (utils/insight_generator.py)

**Purpose**: AI-powered financial analysis and insights

**Technology**: OpenAI GPT-4o API

**Key Functions**:

```python
def generate_ratio_insights(financial_data) -> Dict[str, str]:
    """
    Generates one-liner insights for 25+ financial ratios

    Process:
    1. Extract available ratios from financial data
    2. Create structured prompt with ratio definitions
    3. Call OpenAI API with JSON response format
    4. Return ratio-to-insight mapping

    Returns: {
        'current_ratio': 'Insight text...',
        'debt_equity': 'Insight text...',
        ...
    }
    """

def generate_financial_insights(financial_data) -> Dict[str, str]:
    """
    Generates comprehensive financial insights

    Categories:
    - Growth Insight: Revenue/earnings trends
    - Liquidity Insight: Short-term solvency
    - Efficiency Insight: Operational efficiency
    - Leverage Insight: Capital structure
    - Coverage Insight: Debt service capability
    - Profitability Insight: Margins and returns
    - Working Capital Insight: WC management

    Returns: Dict with 7 insight types
    """

def generate_credit_rating(financial_data) -> Dict[str, str]:
    """
    AI-powered credit rating assignment

    Rating Scale: AAA, AA, A, BBB, BB, B, CCC, CC, C, D

    Returns: {
        'credit_rating': 'A',
        'justification': 'Detailed explanation...'
    }
    """
```

**AI Prompt Engineering**:

Ratio Insights Prompt Structure:
```
Role: Senior credit analyst specializing in ratio analysis
Task: Generate 15-30 word insights for each ratio
Focus: Credit risk implications, exact values
Format: JSON with ratio names as keys
Temperature: 0.2 (low for consistency)
Max Tokens: 1000
```

Financial Insights Prompt Structure:
```
Role: Financial analyst expert in credit analysis
Task: Generate single-sentence insights for 7 categories
Include: Specific numbers, percentages, trends
Compare: Industry benchmarks when available
Format: JSON with insight type keys
Temperature: 0.3
Max Tokens: 1500
```

Credit Rating Prompt Structure:
```
Role: Senior credit analyst at major rating agency
Task: Assign credit rating with detailed justification
Consider: Liquidity, leverage, profitability, stability
Use: Exact numerical values from data
Format: JSON with rating and justification
Temperature: 0.2
Max Tokens: 800
```

**OpenAI Configuration**:
```python
openai_client = OpenAI(api_key=OPENAI_API_KEY)

response = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    response_format={"type": "json_object"},
    max_tokens=1000,
    temperature=0.2
)
```

**Fallback Mechanisms**:
- Default insights when API fails
- Error handling and logging
- Graceful degradation
- User notification of failures

#### 3.2 Report Polisher Module (utils/report_polisher.py)

**Purpose**: Transform raw data into professional narrative

**Technology**: OpenAI GPT-4o API + Jinja2 Templates

**Key Functions**:

```python
def generate_raw_report(data) -> str:
    """
    Populates Jinja2 template with structured data

    Process:
    1. Load raw_credit_report_template.txt
    2. Create Jinja2 Template object
    3. Render template with data dictionary
    4. Return structured text report
    """

def polish_credit_report(raw_report, company_data) -> str:
    """
    Transforms raw report into polished narrative

    Process:
    1. Generate credit rating using raw data
    2. Create polishing prompt with rating
    3. Call OpenAI API for narrative generation
    4. Return professional analyst-quality report

    Temperature: 0.4 (balanced creativity)
    Max Tokens: 4000 (long-form content)
    """

def generate_two_step_report(data) -> Dict[str, str]:
    """
    Complete workflow for dual report generation

    Returns: {
        'raw_report': 'Structured data report...',
        'polished_report': 'Professional narrative...'
    }
    """
```

**Polishing Prompt Architecture**:

```
System Role:
- Senior financial analyst at top-tier rating agency
- Transform raw data into polished narrative
- Use sophisticated financial terminology
- Write in confident, authoritative tone
- Include market context and peer comparisons

Instructions:
1. Start with company name as title
2. Include credit rating as subtitle
3. Add rating justification section
4. Structure with clear sections
5. Use present tense, professional language
6. Include forward-looking assessments

Required Structure:
1. Company Name (Title)
2. Credit Rating (Subtitle)
3. Rating Justification
4. Executive Summary
5. Company Profile & Operations
6. Financial Analysis
7. Risk Assessment
8. Recommendation/Conclusion

Tone: Professional, authoritative, analytical
Terminology: Covenant compliance, capital adequacy, etc.
```

**Fallback Report**:
- Template-based fallback if AI fails
- Professional structure maintained
- Includes raw data at end
- User-friendly error messaging

### 4. Template Engine Layer

#### Jinja2 Template System

**Technology**: Jinja2 3.1.6+

**Templates**:

1. **raw_credit_report_template.txt**
   - Structured data presentation
   - 10 main sections
   - 168 lines of formatted content
   - Variable substitution with defaults
   - Comprehensive ratio dashboard

2. **credit_report_template.txt**
   - Original template format
   - Alternative presentation style
   - Legacy compatibility

**Template Features**:

Variable Substitution:
```jinja2
{{ company_name }}
{{ revenue | default("N/A") }}
{{ current_ratio | default(0.0) }}
```

Conditional Rendering:
```jinja2
{{ debt_equity | default(debt_to_equity) }}
```

Formatting:
- Consistent section headers with separators
- Table formatting for multi-year data
- Hierarchical section numbering
- Professional layout with ASCII borders

**Template Sections**:

1. Company Overview (6 fields)
2. Ownership & Management (5 fields)
3. Business Operations (5 fields)
4. Financial Summary (9 fields)
5. Multi-Year Trends (table format)
6. Ratio Dashboard (7 subsections, 60+ ratios)
7. Legal & Compliance (3 fields)
8. Credit History & Feedback (4 fields)
9. Analyst Commentary & Outlook (3 fields)
10. Credit Assessment (2 fields + recommendation)

### 5. Data Storage Layer

#### Session State Storage

**Technology**: Streamlit Session State

**Purpose**: Maintain state across user interactions

**Stored Data**:
```python
{
    'csv_validated': bool,           # Validation status
    'company_df': pd.DataFrame,      # Company CSV data
    'ratios_df': pd.DataFrame,       # Financial CSV data
    'ratio_insights': Dict,          # AI-generated insights
    'raw_report_data': Dict,         # Original numeric data
    'report_data': Dict,             # Processed report data
    'raw_report': str,               # Raw template output
    'polished_report': str           # Final polished report
}
```

**Persistence**:
- Data persists during user session
- Clears on browser refresh
- No server-side storage required
- In-memory processing only

#### File Storage

**Template Files**:
```
templates/
├── raw_credit_report_template.txt    (7.8 KB)
└── credit_report_template.txt        (8.6 KB)
```

**Sample Data Files**:
```
sample_company_info.csv               (758 bytes)
sample_financial_ratios.csv           (1.8 KB)
sample_company_data.csv               (2.4 KB)

attached_assets/
├── Reordered_Company_Information_Sample_*.csv
├── Financial_Information_Sample_*.csv
├── sample1.txt through sample5.txt
└── image_*.png (UI screenshots)
```

## Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | Streamlit | 1.46.1+ | Web application framework |
| Data Processing | Pandas | 2.3.0+ | CSV handling and data manipulation |
| Template Engine | Jinja2 | 3.1.6+ | Report template rendering |
| PDF Processing | pdfplumber | 0.11.7+ | PDF text extraction |
| AI Service | OpenAI | 1.95.0+ | GPT-4o API integration |
| Language | Python | 3.11+ | Core programming language |

### Supporting Libraries

- **io**: File handling and in-memory operations
- **json**: JSON parsing for API responses
- **datetime**: Timestamp generation
- **typing**: Type hints for code clarity
- **os**: Environment variable management
- **dotenv**: Environment configuration

### External Services

**OpenAI GPT-4o API**:
- Model: gpt-4o (latest as of May 2024)
- Use Cases:
  - Ratio insight generation
  - Financial analysis
  - Credit rating assignment
  - Report narrative polishing
- Configuration:
  - API Key via environment variable
  - JSON response format
  - Temperature: 0.2-0.4 (consistency vs. creativity)
  - Max Tokens: 800-4000 (based on task)

## Data Flow Architecture

### Three-Step Generation Process

#### Step 1: Generate Insights

```
Input: company_df, ratios_df
  ↓
process_company_csv_data(company_df)
  ↓
process_ratios_csv_data(ratios_df)
  ↓
Combine data → report_data
  ↓
generate_ratio_insights(report_data) → OpenAI API
  ↓
Store: ratio_insights, raw_report_data, report_data
  ↓
Output: Session state updated
```

#### Step 2: Generate Raw Text

```
Input: report_data, ratio_insights (from Step 1)
  ↓
Update report_data with ratio_insights
  ↓
generate_financial_insights(report_data) → OpenAI API
  ↓
Update report_data with comprehensive insights
  ↓
generate_raw_report(report_data) → Jinja2 template
  ↓
Store: raw_report, updated report_data
  ↓
Output: Structured text report
```

#### Step 3: Generate Final Report

```
Input: raw_report, report_data (from Step 2)
  ↓
generate_credit_rating(raw_report_data) → OpenAI API
  ↓
create_polishing_prompt(raw_report, company_data, credit_rating)
  ↓
polish_credit_report() → OpenAI API (long-form narrative)
  ↓
Store: polished_report
  ↓
Output: Professional credit analysis
```

### Cascading Execution

The system implements intelligent cascading:
- Step 2 auto-runs Step 1 if not completed
- Step 3 auto-runs Steps 1 & 2 if not completed
- User can execute any step independently
- Previous results cached in session state

## Security Architecture

### API Security

**OpenAI API Key Management**:
```python
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)
```

Best Practices:
- API key stored in environment variable
- Never hardcoded in source code
- Loaded via dotenv for development
- Secure secret management in production

### Data Security

**Data Privacy**:
- No persistent storage of uploaded data
- Session-based data lifecycle
- In-memory processing only
- Automatic cleanup on session end

**Input Validation**:
- CSV column validation
- Numeric value sanitization
- File type restrictions (.csv, .pdf)
- Error handling for malformed data

### Error Handling

**Defensive Programming**:
```python
try:
    # Operation
except Exception as e:
    st.error(f"Error: {str(e)}")
    return default_value
```

**Fallback Mechanisms**:
- Default values for missing data
- Generic insights when AI fails
- Template-based reports if polishing fails
- User-friendly error messages

## Scalability Architecture

### Current Limitations

**Single-User Session Model**:
- One user session at a time per instance
- In-memory state storage
- Synchronous processing
- Limited by single Python process

**Performance Constraints**:
- OpenAI API rate limits
- Single-threaded Streamlit execution
- No caching of AI responses
- Manual file upload (no batch processing)

### Scalability Enhancements (Future)

**Multi-User Support**:
- Database-backed session storage
- User authentication and authorization
- Session isolation and security
- Concurrent request handling

**Performance Optimization**:
- Caching layer for common queries
- Async API calls for parallel processing
- Batch processing capability
- Queue-based job management

**Infrastructure Scaling**:
- Container-based deployment (Docker)
- Load balancing across instances
- Cloud storage for templates and data
- CDN for static assets

## Deployment Architecture

### Current Deployment: Replit

**Platform**: Replit Cloud IDE
**Configuration**: .replit file

```toml
[project]
name = "repl-nix-workspace"
version = "0.1.0"
requires-python = ">=3.11"
```

**Advantages**:
- Quick prototyping and testing
- Integrated development environment
- Easy sharing and collaboration
- Automatic dependency management

**Limitations**:
- Single-user instance
- Limited computational resources
- Public accessibility constraints
- Not production-grade

### Production Deployment Options

#### Option 1: Streamlit Cloud

**Advantages**:
- Native Streamlit hosting
- Easy GitHub integration
- Automatic deployments
- Free tier available

**Requirements**:
- GitHub repository
- requirements.txt or pyproject.toml
- Secrets management for API keys
- Public or private app settings

#### Option 2: Docker + Cloud Platform

**Container Architecture**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

**Deployment Platforms**:
- AWS ECS/Fargate
- Google Cloud Run
- Azure Container Instances
- Heroku Container Registry

**Advantages**:
- Portable across platforms
- Scalable infrastructure
- Enterprise-grade reliability
- Full control over environment

#### Option 3: Traditional Server Deployment

**Stack**:
- Nginx reverse proxy
- Gunicorn/Uvicorn application server
- Streamlit application
- Systemd service management

**Requirements**:
- Linux server (Ubuntu/CentOS)
- SSL certificate for HTTPS
- Firewall configuration
- Monitoring and logging

## Monitoring and Logging

### Current Logging

**Console Logging**:
```python
print(f"Error generating insights: {e}")
st.error(f"Error: {str(e)}")
```

**Streamlit Debug Mode**:
- Built-in error display
- Stack trace visualization
- Session state inspection

### Production Monitoring (Recommended)

**Application Monitoring**:
- OpenAI API usage tracking
- Response time metrics
- Error rate monitoring
- User session analytics

**Infrastructure Monitoring**:
- CPU and memory utilization
- Network I/O metrics
- API latency tracking
- Database performance (if added)

**Logging Framework**:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

## Integration Architecture

### Current Integrations

**OpenAI API Integration**:
- REST API via Python SDK
- JSON request/response format
- Synchronous API calls
- Error handling and retries

### Future Integration Opportunities

**Enterprise System Integrations**:
- Core Banking Systems (CBS)
- Credit Management Systems
- Document Management Systems (DMS)
- Business Intelligence (BI) platforms

**Data Source Integrations**:
- Financial data aggregators
- Credit bureaus
- Market data providers
- Regulatory databases

**Authentication Integrations**:
- LDAP/Active Directory
- SAML/OAuth 2.0
- Multi-factor authentication (MFA)
- Role-based access control (RBAC)

## Maintenance and Updates

### Version Control

**Current Status**: Prototype version
**Recommended Practice**:
- Git version control
- Semantic versioning (1.0.0)
- Change log maintenance
- Branch strategy (main, develop, feature)

### Update Strategy

**Application Updates**:
- OpenAI model version monitoring
- Streamlit framework updates
- Security patches
- Dependency updates

**Template Updates**:
- Version-controlled templates
- A/B testing for changes
- User feedback integration
- Regulatory compliance updates

## Conclusion

The Credit Profile Analyzer demonstrates a modern, AI-powered architecture that balances simplicity with sophisticated functionality. The modular design enables easy maintenance, testing, and future enhancements while the AI integration provides intelligent, value-added analysis capabilities.

Key architectural strengths:
- Modular, maintainable codebase
- Robust error handling and fallbacks
- Scalable foundation for growth
- Industry-standard technologies
- Cloud-ready deployment model

---

**Document Version**: 1.0
**Last Updated**: December 2025
**Document Owner**: Technology Architecture Team
