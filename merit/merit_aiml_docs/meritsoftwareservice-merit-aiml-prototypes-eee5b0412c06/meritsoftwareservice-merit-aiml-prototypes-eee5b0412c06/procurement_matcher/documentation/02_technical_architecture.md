# Technical Architecture

## Table of Contents
1. [System Design](#system-design)
2. [Component Architecture](#component-architecture)
3. [Class Hierarchy](#class-hierarchy)
4. [Data Models](#data-models)
5. [Integration Points](#integration-points)
6. [Technical Stack](#technical-stack)

## System Design

### Architectural Principles

The Procurement Matcher follows these key architectural principles:

1. **Separation of Concerns**: Each module handles a specific domain (legal, procurement, taxonomy)
2. **Inheritance-based Design**: Common functionality shared through base classes
3. **Configuration-driven**: Externalized configuration for flexibility
4. **Structured Output**: Pydantic models ensure type safety and validation
5. **Modular Prompts**: Domain-specific prompts separated from business logic

### Layer Architecture

```
┌─────────────────────────────────────────────────────┐
│           Presentation Layer (Streamlit UI)         │
│  - app.py (main), legal_ui.py, procurement_ui.py,  │
│    vendor_ui.py                                     │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              Business Logic Layer                   │
│  - legal_profile.py (LegalProfile)                  │
│  - procurement.py (VendorProfile)                   │
│  - vendor_mapping.py (VendorMapping)                │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              Service Layer                          │
│  - utils.py (Utils class)                           │
│  - LLM integration, File I/O                        │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│         Infrastructure Layer                        │
│  - config_reader.py (ConfigLoader)                  │
│  - log_writer.py (CustomLogger)                     │
└─────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Application Entry Point (app.py)

**Purpose**: Unified interface for all three matching functionalities

**Key Components**:
```python
class App(LegalProfile, VendorProfile, VendorMapping):
    """
    Main application class using multiple inheritance
    to combine all three matching capabilities
    """
```

**Responsibilities**:
- Streamlit page configuration
- Session state management
- Tab-based navigation
- File upload handling
- Result display

**Session State Variables**:
- `legal`: Stores legal case matching results
- `procurement`: Stores vendor matching results
- `vendor`: Stores taxonomy classification results

### 2. Legal Profile Module (legal_profile.py)

**Class**: `LegalProfile(Utils)`

**Purpose**: Match precedent legal cases with current cases

**Key Components**:

```python
class LegalTemplate(BaseModel):
    """Pydantic model for structured output"""
    Case_Strategy: str
    Precedent_Case: str
    Confidence_Score: float  # Range: 0.1 to 1.0
    Justification: str
```

**Processing Flow**:
1. Read current case from TXT file
2. Iterate through precedent case PDFs
3. Extract text from each PDF
4. Invoke LLM chain with legal prompt
5. Parse JSON response into LegalTemplate
6. Display progress bar
7. Return list of matches

**LangChain Components**:
- `JsonOutputParser`: Parses LLM output into structured format
- `PromptTemplate`: Formats input with legal_prompt
- `LLM Chain`: `prompt_legal | llm`

### 3. Procurement Module (procurement.py)

**Class**: `VendorProfile(Utils)`

**Purpose**: Match vendor capabilities with procurement requirements

**Key Components**:

```python
class VendorTemplate(BaseModel):
    """Pydantic model for vendor matching output"""
    Current_Requirement: str
    Vendor_Name: str
    Confidence_Score: float  # Range: 0.1 to 1.0
    Justification: str
```

**Processing Flow**:
1. Read requirement from TXT file
2. Iterate through vendor profile PDFs
3. Extract vendor information from PDFs
4. Invoke procurement chain
5. Parse structured response
6. Update progress indicator
7. Return vendor matches sorted by confidence

**Unique Features**:
- Focuses on capabilities, not commercial terms
- Batch processing with visual feedback
- Automatic sorting by confidence score

### 4. Vendor Taxonomy Module (vendor_mapping.py)

**Class**: `VendorMapping(Utils)`

**Purpose**: Extract structured taxonomy from vendor information

**Key Components**:

```python
class VendorTaxonomy(BaseModel):
    """Comprehensive taxonomy model"""
    vendor: str
    category: Optional[str]
    sub_category: Optional[List[str]]
    application: Optional[str]
    function: Optional[List[str]]
    service_flag: Optional[List[str]]
    compliance: Optional[List[str]]
    geography: Optional[List[str]]
    risk_flag: str
    sustainability_flag: Optional[str]
```

**Processing Flow**:
1. Receive vendor text input
2. Invoke vendor taxonomy chain
3. Parse structured taxonomy
4. Convert list fields to comma-separated strings
5. Display as dataframe

**Taxonomy Dimensions**:
- **Category**: High-level classification
- **Sub-category**: Detailed classification
- **Application**: Specific products/services
- **Function**: Business/technical capabilities
- **Service Flags**: Service offerings
- **Compliance**: Standards and certifications
- **Geography**: Operational regions
- **Risk Assessment**: Risk level and type
- **Sustainability**: Environmental/social indicators

### 5. Utils Module (utils.py)

**Class**: `Utils(ConfigLoader)`

**Purpose**: Common utilities for file processing and LLM integration

**Key Methods**:

```python
def __init__(self):
    """Initialize LLM with config-driven parameters"""
    self.llm = init_chat_model(
        model=self.config_data["llm"]["model"],
        model_provider=self.config_data["llm"]["model_provider"],
    )

def read_txt_file(self, txt_file) -> str:
    """Read and return text file content"""

def read_pdf_file(self, pdf_file) -> str:
    """Extract and return PDF text content"""
```

**Features**:
- LLM initialization from configuration
- File reading with error handling
- Streamlit warning integration
- UTF-8 encoding support

### 6. Configuration Module (config_reader.py)

**Class**: `ConfigLoader(CustomLogger)`

**Purpose**: Load and validate configuration from YAML

**Configuration Structure**:
```yaml
data_path: data
llm:
  model: gpt-4o-mini
  model_provider: openai
  temperature: 0
```

**Key Methods**:
```python
def read_config(self) -> dict:
    """
    Reads config.yaml and returns configuration dictionary
    Raises exception if config file not found
    """
```

**Features**:
- YAML-based configuration
- Environment variable loading via dotenv
- Critical error logging
- Graceful failure handling

### 7. Logging Module (log_writer.py)

**Class**: `CustomLogger`

**Purpose**: Structured logging with rotation and compression

**Log Configuration**:

```python
# Info Logs
- Location: ./logs/info_logs.json
- Format: JSON serialized
- Rotation: Daily (00:00)
- Retention: 7 days
- Compression: ZIP

# Error Logs
- Location: ./logs/error_logs.json
- Format: JSON serialized
- Rotation: Daily (00:00)
- Retention: 30 days
- Compression: ZIP
- Additional: Backtrace and diagnostics enabled
```

**Log Format**:
```json
{
  "time": "YYYY-MM-DD HH:mm:ss",
  "level": "INFO/ERROR/DEBUG/CRITICAL",
  "message": "Log message",
  "name": "Logger name",
  "file": "Source file",
  "line": "Line number",
  "function": "Function name"
}
```

**Exception Handling**:
```python
def log_exception(self, exc_tb) -> List[dict]:
    """
    Extract traceback into structured format
    Returns list of {file, function, line} dictionaries
    """
```

## Class Hierarchy

### Inheritance Structure

```
CustomLogger
    │
    └── ConfigLoader
            │
            └── Utils
                    │
                    ├── LegalProfile
                    ├── VendorProfile
                    └── VendorMapping
                            │
                            └── App (multiple inheritance)
```

### Inheritance Benefits

1. **Logging**: All classes inherit structured logging capabilities
2. **Configuration**: Centralized config access throughout the application
3. **Utilities**: Shared LLM and file processing methods
4. **Modularity**: Each domain module can operate independently

## Data Models

### Pydantic Models Overview

All output models use Pydantic for:
- Type validation
- JSON schema generation
- Automatic documentation
- Parsing validation

### LegalTemplate

```python
class LegalTemplate(BaseModel):
    Case_Strategy: str = Field(
        description="Title of the current case"
    )
    Precedent_Case: str = Field(
        description="Title of the given precedent case"
    )
    Confidence_Score: float = Field(
        description="Confidence score of the match between 0.1 and 1.0"
    )
    Justification: str = Field(
        description="Clear justification for the match and score"
    )
```

**Validation Rules**:
- All fields required
- Confidence score must be float
- Description metadata for LLM guidance

### VendorTemplate

```python
class VendorTemplate(BaseModel):
    Current_Requirement: str = Field(
        description="Title of the current requirement"
    )
    Vendor_Name: str = Field(
        description="Name of the given vendor"
    )
    Confidence_Score: float = Field(
        description="Confidence score of the match between 0.1 and 1.0"
    )
    Justification: str = Field(
        description="Clear justification for the match and score"
    )
```

**Validation Rules**:
- All fields required
- Focus on capability alignment
- Score justification required

### VendorTaxonomy

```python
class VendorTaxonomy(BaseModel):
    vendor: str = Field(..., description="Given name of the vendor")
    category: Optional[str] = Field(...)
    sub_category: Optional[List[str]] = Field(...)
    application: Optional[str] = Field(...)
    function: Optional[List[str]] = Field(...)
    service_flag: Optional[List[str]] = Field(default_factory=list, ...)
    compliance: Optional[List[str]] = Field(default_factory=list, ...)
    geography: Optional[List[str]] = Field(default_factory=list, ...)
    risk_flag: str = Field(...)
    sustainability_flag: Optional[str] = Field(None, ...)
```

**Validation Rules**:
- Only vendor and risk_flag required
- Lists have default_factory for empty initialization
- Optional fields support partial extraction

## Integration Points

### LangChain Integration

**Chain Construction Pattern**:
```python
# 1. Define Pydantic model
class OutputModel(BaseModel):
    field: str = Field(description="...")

# 2. Create JSON parser
parser = JsonOutputParser(pydantic_object=OutputModel)

# 3. Build prompt with format instructions
prompt = PromptTemplate(
    template=prompt_text,
    input_variables=["var1", "var2"],
    partial_variables={
        "format_instruction": parser.get_format_instructions()
    }
)

# 4. Create chain
chain = prompt | llm

# 5. Invoke and parse
result = chain.invoke({"var1": val1, "var2": val2})
parsed = parser.parse(result.content)
```

### Streamlit Integration

**Session State Management**:
```python
# Initialize in __init__
if "key" not in st.session_state:
    st.session_state['key'] = None

# Update after processing
st.session_state['key'] = processing_result

# Display from state
if st.session_state['key']:
    st.dataframe(st.session_state['key'])
```

**File Upload Pattern**:
```python
# File upload in form
with st.form("form_name"):
    file = st.file_uploader("Label", type="pdf")
    btn = st.form_submit_button("Submit")

# Process on submit
if btn and file:
    # Save to disk
    file_path = os.path.join(folder, file.name)
    with open(file_path, "wb") as f:
        f.write(file.getvalue())

    # Process file
    result = process_function(file_path)
```

### OpenAI Integration

**LLM Initialization**:
```python
from langchain.chat_models import init_chat_model

llm = init_chat_model(
    model="gpt-4o-mini",
    model_provider="openai"
)
```

**Environment Variables Required**:
- `OPENAI_API_KEY`: OpenAI API authentication

## Technical Stack

### Core Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| streamlit | Latest | Web UI framework |
| langchain | Latest | LLM orchestration |
| langchain-core | Latest | Core LangChain components |
| openai | Latest | OpenAI API client |
| pydantic | Latest | Data validation |
| PyMuPDF (fitz) | Latest | PDF text extraction |
| pandas | Latest | Data manipulation |
| pyyaml | Latest | Configuration parsing |
| python-dotenv | Latest | Environment management |
| loguru | Latest | Structured logging |

### Python Version
- Minimum: Python 3.8
- Recommended: Python 3.10+

### System Dependencies
- UTF-8 locale support
- File system write permissions for logs and data directories

## Performance Considerations

### Processing Time Factors

1. **LLM API Latency**: Typically 2-5 seconds per request
2. **PDF Extraction**: ~100ms per page
3. **File I/O**: Minimal overhead with local storage

### Optimization Strategies

1. **Batch Processing**: Process multiple files in sequence
2. **Progress Feedback**: Visual indicators prevent user anxiety
3. **Session State**: Avoid reprocessing on page refresh
4. **Caching Potential**: LLM responses could be cached based on content hash

### Scalability Limitations

**Current Constraints**:
- Synchronous processing (one document at a time)
- In-memory result storage
- No pagination for large result sets
- LLM rate limits (provider-dependent)

**Scaling Solutions**:
- Implement async processing for batch uploads
- Add database backend for result persistence
- Implement pagination for large datasets
- Add request queuing for rate limit management

## Error Handling Strategy

### Layer-by-Layer Error Handling

```python
# Layer 1: Method level
try:
    result = process()
except Exception as e:
    self.logger.error(e)
    return default_value

# Layer 2: UI level
try:
    with st.spinner("Processing..."):
        result = method_call()
except Exception as e:
    st.error(e)
    st.warning("User-friendly message")

# Layer 3: Critical failures
try:
    config = load_config()
except Exception as e:
    logger.critical(str(e))
    sys.exit(e)
```

### Error Recovery

- **File Reading Errors**: Return empty string, log error
- **LLM Errors**: Return empty list, show warning
- **Config Errors**: Exit application with critical log
- **Validation Errors**: Caught by Pydantic, logged as errors

## Security Architecture

### Current Security Measures

1. **API Key Management**: Environment variables via dotenv
2. **File Upload**: Type validation (PDF, TXT only)
3. **Logging**: Structured logs without sensitive data exposure

### Security Gaps

1. **No file size limits**: Potential DoS via large uploads
2. **No file content validation**: Malicious PDFs not scanned
3. **No authentication**: Open access to application
4. **API keys in logs**: Potential exposure in error traces
5. **No input sanitization**: LLM injection possible via prompts

### Recommended Security Enhancements

1. Implement file size limits (e.g., 10MB per file)
2. Add virus scanning for uploaded files
3. Implement user authentication (OAuth, SAML)
4. Sanitize API keys from all logs
5. Add input validation and sanitization
6. Implement rate limiting per user/session
7. Add HTTPS enforcement in production
8. Implement secure file storage with encryption

## Deployment Architecture

### Local Deployment

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with OPENAI_API_KEY

# Run
streamlit run app.py
```

### Docker Deployment (Recommended)

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

### Cloud Deployment Options

1. **AWS**: EC2 + ECS/EKS for containerized deployment
2. **Azure**: App Service or Container Instances
3. **GCP**: Cloud Run for serverless deployment
4. **Heroku**: Quick deployment with buildpacks

## Monitoring and Observability

### Current Logging

- JSON-formatted logs in `./logs/`
- Separate info and error streams
- Automatic rotation and compression

### Recommended Monitoring

1. **Application Metrics**:
   - Request counts per module
   - Average processing time
   - LLM API response times
   - Error rates

2. **Infrastructure Metrics**:
   - CPU and memory usage
   - Disk I/O for file processing
   - Network latency to LLM API

3. **Business Metrics**:
   - Average confidence scores
   - Documents processed per day
   - User session durations

### Observability Tools

- **Logs**: Centralize with ELK Stack or Splunk
- **Metrics**: Prometheus + Grafana
- **Tracing**: OpenTelemetry for request tracing
- **Alerting**: PagerDuty or Opsgenie for critical errors

## Conclusion

The Procurement Matcher's technical architecture demonstrates a well-structured, modular design suitable for prototype development. The inheritance-based approach provides code reuse while maintaining separation of concerns. Key areas for production readiness include security hardening, performance optimization, and enhanced observability.
