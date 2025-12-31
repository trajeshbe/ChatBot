# Vendor Recommendation System - Technical Architecture

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Component Design](#component-design)
3. [Data Flow](#data-flow)
4. [Class Hierarchy](#class-hierarchy)
5. [AI/ML Components](#aiml-components)
6. [Data Models](#data-models)
7. [Integration Points](#integration-points)
8. [Performance Considerations](#performance-considerations)
9. [Security Architecture](#security-architecture)

## System Architecture Overview

### High-Level Architecture

The Vendor Recommendation System follows a layered architecture pattern:

```
┌─────────────────────────────────────────────┐
│         Presentation Layer                   │
│         (Streamlit UI)                       │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         Application Layer                    │
│    (Business Logic & Controllers)            │
│  - VendorProfile                            │
│  - TenderMapping                            │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         Service Layer                        │
│    (LangChain, LLM Services)                │
│  - Prompt Templates                         │
│  - Output Parsers                           │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         Infrastructure Layer                 │
│  - Config Management                        │
│  - Logging                                  │
│  - File I/O                                 │
└─────────────────────────────────────────────┘
```

### Architecture Patterns

1. **Layered Architecture**: Separation of concerns across layers
2. **Inheritance Hierarchy**: Code reuse through class inheritance
3. **Dependency Injection**: Configuration and LLM injection
4. **Template Method Pattern**: Prompt template processing
5. **Strategy Pattern**: Interchangeable LLM models

## Component Design

### Core Components

#### 1. Application Controller (`app.py`)

**Purpose**: Main entry point and UI orchestration

**Responsibilities**:
- Initialize Streamlit application
- Manage UI components
- Handle user interactions
- Coordinate file uploads
- Display results
- Manage session state

**Key Methods**:
```python
class App(VendorProfile, TenderMapping):
    def __init__(self):
        # Initialize Streamlit config
        # Set up session state

    def render_ui(self):
        # Create UI components
        # Handle file uploads
        # Process submissions
        # Display results
```

**Design Decisions**:
- Multiple inheritance from VendorProfile and TenderMapping
- Session state management for data persistence
- Progress indicators for user feedback
- Form-based input handling

#### 2. Configuration Manager (`config_reader.py`)

**Purpose**: Centralized configuration management

**Responsibilities**:
- Load YAML configuration
- Manage environment variables
- Validate configuration
- Provide config access to other components

**Key Methods**:
```python
class ConfigLoader(CustomLogger):
    def __init__(self):
        # Load environment variables
        # Initialize logger

    def read_config(self):
        # Read config.yaml
        # Validate configuration
        # Return config dictionary
```

**Configuration Schema**:
```yaml
data_path: string          # Path to data directory
llm:
  model: string           # LLM model name
  model_provider: string  # Provider (openai, anthropic, etc.)
  temperature: float      # Temperature parameter (0-1)
```

#### 3. Utility Services (`utils.py`)

**Purpose**: Common utility functions and LLM initialization

**Responsibilities**:
- Initialize language model
- Read PDF documents
- Read text files
- Provide common utilities

**Key Methods**:
```python
class Utils(ConfigLoader):
    def __init__(self):
        # Initialize LLM from config

    def read_txt_file(txt_file):
        # Read and return text content

    def read_pdf_file(pdf_file):
        # Extract and return PDF text
```

**Dependencies**:
- PyMuPDF (fitz) for PDF processing
- LangChain for LLM initialization
- ConfigLoader for settings

#### 4. Vendor Matching Engine (`vendor.py`)

**Purpose**: Core vendor-tender matching logic

**Responsibilities**:
- Define vendor data model
- Create matching prompt
- Process tender-vendor pairs
- Parse and return results

**Key Components**:

**Data Model**:
```python
class VendorTemplate(BaseModel):
    Vendor_Name: str
    Tender_Title: str
    Confidence_Score: float  # Range: 0.1 to 1.0
    Justification: str
```

**Processing Class**:
```python
class VendorProfile(Utils):
    def __init__(self):
        # Initialize parser and prompt
        # Create processing chain

    def get_match_score_tender(pdf_files, txt_file):
        # Read vendor profile
        # Process each tender
        # Return match results
```

**Processing Flow**:
1. Read vendor profile (TXT)
2. For each tender PDF:
   - Extract text content
   - Invoke LLM with prompt
   - Parse structured output
   - Update progress bar
3. Return list of matches

#### 5. Tender Taxonomy Extractor (`tender_mapping.py`)

**Purpose**: Extract structured taxonomy from tenders

**Responsibilities**:
- Define taxonomy data model
- Extract tender metadata
- Categorize tender information
- Return structured taxonomy

**Data Model**:
```python
class TenderTaxonomy(BaseModel):
    awarding_body: Optional[List[str]]
    contract_type: Optional[List[str]]
    product_category: Optional[List[str]]
    sector: Optional[List[str]]
    solution_type: Optional[List[str]]
    strategic_needs: Optional[List[str]]
    target_region: Optional[List[str]]
    tender_qualifiers: Optional[List[str]]
```

**Processing Class**:
```python
class TenderMapping(Utils):
    def __init__(self):
        # Initialize parser and prompt
        # Create processing chain

    def get_tender_taxonomy(txt_content):
        # Invoke LLM with tender text
        # Parse taxonomy output
        # Format and return results
```

#### 6. Logging System (`log_writer.py`)

**Purpose**: Structured logging and monitoring

**Responsibilities**:
- Configure log handlers
- Separate log levels
- Rotate log files
- Format log entries
- Exception tracking

**Configuration**:
```python
class CustomLogger:
    def setup_logger(self):
        # Create log directory
        # Configure info logger (JSON format)
        # Configure error logger (JSON format)
        # Set rotation and retention policies
```

**Log Files**:
- `logs/info_logs.json`: INFO level events
- `logs/error_logs.json`: DEBUG, WARNING, ERROR, CRITICAL

**Retention Policy**:
- INFO logs: 7 days retention, daily rotation
- ERROR logs: 30 days retention, daily rotation
- Compression: ZIP format for old logs

## Data Flow

### End-to-End Processing Flow

```
┌──────────────┐
│ User uploads │
│ PDF + TXT    │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ App.render_ui()  │
│ Validates files  │
└──────┬───────────┘
       │
       ▼
┌──────────────────────┐
│ Save files to disk   │
│ (data/ directory)    │
└──────┬───────────────┘
       │
       ▼
┌───────────────────────────┐
│ get_match_score_tender()  │
│ Reads vendor profile      │
└──────┬────────────────────┘
       │
       ▼
┌──────────────────────┐
│ For each PDF:        │
│ - Extract text       │
│ - Create prompt      │
│ - Invoke LLM         │
│ - Parse response     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Collect all results  │
│ Return to UI         │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Display in DataFrame │
│ Sort by score        │
└──────────────────────┘
```

### Detailed Component Interactions

```
app.py
  │
  ├─> __init__() ──> VendorProfile.__init__()
  │                    │
  │                    ├─> Utils.__init__()
  │                    │     │
  │                    │     └─> ConfigLoader.__init__()
  │                    │           │
  │                    │           └─> CustomLogger.__init__()
  │                    │
  │                    └─> Create LLM chain
  │
  └─> render_ui() ──> get_match_score_tender()
                        │
                        ├─> read_txt_file()
                        ├─> read_pdf_file()
                        ├─> procurement_chain.invoke()
                        └─> vendor_parser.parse()
```

## Class Hierarchy

### Inheritance Structure

```
CustomLogger
    │
    └─> ConfigLoader
            │
            └─> Utils
                    │
                    ├─> VendorProfile
                    │
                    └─> TenderMapping
                            │
                            └─> App (also inherits from VendorProfile)
```

### Detailed Class Diagram

```
┌───────────────────┐
│  CustomLogger     │
│  ───────────────  │
│  - logger         │
│  + setup_logger() │
│  + log_exception()│
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  ConfigLoader     │
│  ───────────────  │
│  - config_data    │
│  + read_config()  │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  Utils            │
│  ───────────────  │
│  - llm            │
│  + read_txt_file()│
│  + read_pdf_file()│
└─────────┬─────────┘
          │
          ├────────────────────┐
          │                    │
          ▼                    ▼
┌──────────────────┐  ┌────────────────┐
│  VendorProfile   │  │ TenderMapping  │
│  ──────────────  │  │ ───────────── │
│  - vendor_parser │  │ - tender_parser│
│  - prompt_vendor │  │ - prompt_tender│
│  - procurement_  │  │ - tender_chain │
│    chain         │  │                │
│  + get_match_    │  │ + get_tender_  │
│    score_tender()│  │   taxonomy()   │
└────────┬─────────┘  └────────┬───────┘
         │                     │
         └──────────┬──────────┘
                    │
                    ▼
           ┌────────────────┐
           │     App        │
           │  ────────────  │
           │  + render_ui() │
           └────────────────┘
```

## AI/ML Components

### LangChain Integration

#### LLM Initialization

```python
from langchain.chat_models import init_chat_model

llm = init_chat_model(
    model="gpt-4o-mini",
    model_provider="openai"
)
```

**Supported Providers**:
- OpenAI (gpt-4, gpt-4o-mini, gpt-3.5-turbo)
- Anthropic (claude-3, claude-2)
- Azure OpenAI
- Custom providers via LangChain

#### Prompt Templates

**Vendor Matching Prompt** (`vendor_prompt.py`):
```python
vendor_prompt = """
You are a vendor evaluation assistant.

Your task is to analyze the relationship between:
- Tender: {tender}
- Vendor Profile: {vendor}

Focus on core capabilities, features, and offerings.

{format_instruction}

Return JSON with:
- Vendor_Name
- Tender_Title
- Confidence_Score (0.1 to 1.0)
- Justification
"""
```

**Tender Taxonomy Prompt** (`tender_prompt.py`):
```python
tender_prompt = """
Extract structured taxonomy from tender information.

{format_instruction}

Extract:
- awarding_body
- contract_type
- product_category
- sector
- solution_type
- strategic_needs
- target_region
- tender_qualifiers

Tender information:
{tender}
"""
```

#### Output Parsing

**Structured Output with Pydantic**:
```python
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# Define schema
class VendorTemplate(BaseModel):
    Vendor_Name: str
    Tender_Title: str
    Confidence_Score: float
    Justification: str

# Create parser
parser = JsonOutputParser(pydantic_object=VendorTemplate)

# Get format instructions
format_instructions = parser.get_format_instructions()

# Parse LLM output
result = parser.parse(llm_response.content)
```

#### Processing Chain

```python
# Create prompt template
prompt = PromptTemplate(
    template=vendor_prompt,
    input_variables=["vendor", "tender"],
    partial_variables={
        "format_instruction": parser.get_format_instructions()
    }
)

# Create chain
chain = prompt | llm

# Invoke chain
response = chain.invoke({
    "vendor": vendor_text,
    "tender": tender_text
})
```

### Document Processing

#### PDF Text Extraction

```python
import fitz  # PyMuPDF

def read_pdf_file(pdf_file):
    doc = fitz.open(pdf_file)

    # Extract text from all pages
    pdf_content = "\n\n".join([
        page.get_text()
        for page in doc
    ])

    return pdf_content
```

**Features**:
- Multi-page support
- Layout preservation
- Unicode text handling
- Error handling for corrupted PDFs

#### Text File Processing

```python
def read_txt_file(txt_file):
    with open(txt_file, "r", encoding="utf-8") as f:
        txt_content = f.read()
    return txt_content
```

**Features**:
- UTF-8 encoding support
- Error handling
- Whitespace preservation

## Data Models

### Vendor Match Model

```python
class VendorTemplate(BaseModel):
    Vendor_Name: str = Field(
        description="Name of the given vendor"
    )
    Tender_Title: str = Field(
        description="Title of the tender"
    )
    Confidence_Score: float = Field(
        description="Confidence score between 0.1 and 1.0"
    )
    Justification: str = Field(
        description="Clear justification for the match and score"
    )
```

**Validation Rules**:
- All fields required
- Confidence_Score: 0.1 ≤ score ≤ 1.0
- Vendor_Name: Non-empty string
- Tender_Title: Non-empty string
- Justification: Descriptive text

### Tender Taxonomy Model

```python
class TenderTaxonomy(BaseModel):
    awarding_body: Optional[List[str]] = Field(
        default_factory=list,
        description="Awarding organizations and tender types"
    )
    contract_type: Optional[List[str]] = Field(
        default_factory=list,
        description="Type of contracts"
    )
    product_category: Optional[List[str]] = Field(
        default_factory=list,
        description="Product categories in tender"
    )
    sector: Optional[List[str]] = Field(
        default_factory=list,
        description="Relevant sectors or industries"
    )
    solution_type: Optional[List[str]] = Field(
        default_factory=list,
        description="Solution types or technologies"
    )
    strategic_needs: Optional[List[str]] = Field(
        default_factory=list,
        description="Strategic goals or problem areas"
    )
    target_region: Optional[List[str]] = Field(
        default_factory=list,
        description="Target regions or buyer locations"
    )
    tender_qualifiers: Optional[List[str]] = Field(
        default_factory=list,
        description="Eligibility criteria"
    )
```

**Validation Rules**:
- All fields optional (with defaults)
- List values for multi-item categories
- Empty list if not found
- String normalization

## Integration Points

### External Services

#### OpenAI API

**Endpoint**: https://api.openai.com/v1/chat/completions

**Authentication**:
```python
# Via environment variable
OPENAI_API_KEY=sk-...

# Via LangChain
from langchain.chat_models import init_chat_model
llm = init_chat_model(
    model="gpt-4o-mini",
    model_provider="openai"
)
```

**API Parameters**:
- Model: gpt-4o-mini
- Temperature: 0 (deterministic)
- Max tokens: Auto
- Response format: JSON

**Rate Limits**:
- Tier-dependent (check OpenAI dashboard)
- Retry logic recommended
- Error handling for 429 errors

### File System

**Directory Structure**:
```
vendor_recommendation/
├── data/              # Uploaded files
├── logs/              # Log files
│   ├── info_logs.json
│   └── error_logs.json
└── config.yaml        # Configuration
```

**File Operations**:
- Read: PDF, TXT files
- Write: Uploaded files, logs
- Permissions: Read/write access required

## Performance Considerations

### Optimization Strategies

#### 1. Caching

**Streamlit Caching**:
```python
@st.cache_resource
def load_llm():
    return init_chat_model(
        model="gpt-4o-mini",
        model_provider="openai"
    )
```

**Benefits**:
- Reduces initialization overhead
- Reuses LLM connections
- Faster subsequent requests

#### 2. Batch Processing

**Multiple Tenders**:
```python
for idx, pdf_file in enumerate(pdf_files):
    # Process each tender
    # Update progress: (idx + 1) / total
```

**Benefits**:
- Single vendor profile read
- Parallel processing potential
- Progress feedback

#### 3. Response Time

**Typical Performance**:
- Single tender: 10-30 seconds
- Multiple tenders (5): 1-2 minutes
- Depends on: document size, API latency, model load

**Bottlenecks**:
- API call latency (majority of time)
- PDF text extraction (minimal)
- JSON parsing (negligible)

### Scalability Considerations

#### Horizontal Scaling

**Strategies**:
- Multiple Streamlit instances
- Load balancer distribution
- Shared configuration

#### Vertical Scaling

**Resource Requirements**:
- CPU: Minimal (I/O bound)
- Memory: ~500MB per instance
- Network: Bandwidth for API calls

## Security Architecture

### Authentication & Authorization

**Current State**: No built-in authentication

**Recommendations for Production**:
```python
import streamlit_authenticator as stauth

authenticator = stauth.Authenticate(
    credentials,
    cookie_name,
    cookie_key,
    cookie_expiry_days
)

name, authentication_status, username = authenticator.login()

if authentication_status:
    # Show application
else:
    # Show login form
```

### API Key Management

**Current Approach**:
```python
# .env file
OPENAI_API_KEY=sk-...

# Load in code
from dotenv import load_dotenv
load_dotenv()
```

**Production Recommendations**:
- Use secrets management (AWS Secrets Manager, Azure Key Vault)
- Rotate keys regularly
- Audit key usage
- Implement key rotation

### Data Security

**Sensitive Data Handling**:
1. **Uploaded Files**:
   - Temporary storage
   - Cleanup after processing
   - No long-term retention

2. **API Communications**:
   - HTTPS encryption
   - No logging of sensitive content
   - OpenAI privacy policy applies

3. **Logs**:
   - Sanitize sensitive information
   - Secure log storage
   - Access controls

### Input Validation

**File Upload Validation**:
```python
# File type check
if file.type == "application/pdf":
    # Process PDF
elif file.type == "text/plain":
    # Process TXT

# File size check
max_size_mb = 10
if file.size > max_size_mb * 1024 * 1024:
    st.error("File too large")
```

**Content Validation**:
- UTF-8 encoding check
- Malformed PDF detection
- Empty file rejection

## Monitoring and Observability

### Logging Strategy

**Log Levels**:
- INFO: Normal operations, processing events
- ERROR: Processing failures, API errors
- CRITICAL: System failures, config errors

**Log Format**:
```json
{
  "time": "2024-12-20 10:30:45",
  "level": "INFO",
  "message": "Processing tender: contract_xyz.pdf",
  "name": "main_logger",
  "file": "vendor.py",
  "line": 45,
  "function": "get_match_score_tender"
}
```

### Error Tracking

**Exception Handling**:
```python
try:
    # Process tender
except Exception as e:
    self.logger.error(f"Processing failed: {str(e)}")
    st.warning("Server busy...Please try again...")
```

**Traceback Logging**:
```python
def log_exception(self, exc_tb):
    nested_td = []
    while exc_tb:
        tb = {
            "file": exc_tb.tb_frame.f_code.co_filename,
            "function": exc_tb.tb_frame.f_code.co_name,
            "line": exc_tb.tb_lineno,
        }
        nested_td.append(tb)
        exc_tb = exc_tb.tb_next
    return nested_td
```

## Extension Points

### Adding New LLM Providers

```python
# In utils.py
llm = init_chat_model(
    model=self.config_data["llm"]["model"],
    model_provider=self.config_data["llm"]["model_provider"]
)

# Support: openai, anthropic, azure, cohere, etc.
```

### Custom Prompt Templates

**Create new prompt file**:
```python
# custom_prompt.py
custom_prompt = """
Your custom prompt template here
{input_variables}
{format_instruction}
"""
```

**Use in processing**:
```python
from custom_prompt import custom_prompt

prompt = PromptTemplate(
    template=custom_prompt,
    input_variables=[...],
    partial_variables={...}
)
```

### Additional Data Models

```python
# Define new schema
class CustomModel(BaseModel):
    field1: str
    field2: List[str]
    field3: float

# Create parser
parser = JsonOutputParser(pydantic_object=CustomModel)

# Use in chain
chain = prompt | llm
result = parser.parse(chain.invoke({...}))
```

## Conclusion

The Vendor Recommendation System demonstrates a well-architected, modular approach to AI-powered document matching. Key architectural strengths include:

- Clear separation of concerns
- Reusable component design
- Flexible LLM integration
- Comprehensive error handling
- Structured logging

Future enhancements should focus on:
- Scalability improvements
- Enhanced security
- API development
- Database integration
- Advanced analytics
