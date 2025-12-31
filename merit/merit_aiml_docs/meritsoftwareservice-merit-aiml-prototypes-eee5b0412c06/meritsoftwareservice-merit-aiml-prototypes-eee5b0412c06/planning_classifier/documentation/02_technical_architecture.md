# Planning Document Classifier - Technical Architecture

## System Architecture Overview

The Planning Document Classifier follows a three-tier architecture designed for simplicity, maintainability, and rapid deployment. All components run within a single Python process, making deployment and scaling straightforward.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
│                      (Streamlit App)                         │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   Upload   │  │   Progress   │  │     Results      │   │
│  │   Widget   │  │  Indicators  │  │     Display      │   │
│  └────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Processing Layer                           │
│  ┌───────────────────────┐  ┌──────────────────────────┐   │
│  │   PDF Processor       │  │   Document Classifier    │   │
│  │   (pdf_processor.py)  │  │   (classifier.py)        │   │
│  │                       │  │                          │   │
│  │  • Text Extraction    │  │  • Prompt Engineering    │   │
│  │  • Text Cleaning      │  │  • API Communication     │   │
│  │  • Truncation         │  │  • Result Validation     │   │
│  └───────────────────────┘  └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  External Services Layer                     │
│                     ┌──────────────┐                         │
│                     │  OpenAI API  │                         │
│                     │   (GPT-4o)   │                         │
│                     └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. User Interface Layer (`app.py`)

#### Responsibilities
- Render web interface using Streamlit framework
- Handle file uploads from users
- Orchestrate processing workflow
- Display classification results
- Manage user feedback and error states

#### Key Components

##### Page Configuration
```python
st.set_page_config(
    page_title="Document Classifier",
    page_icon="📋",
    layout="wide"
)
```
- Sets browser title and favicon
- Uses wide layout for optimal space utilization
- Configured for professional appearance

##### Two-Column Layout
```
┌────────────┬────────────────────────────────────────┐
│            │                                        │
│  Upload    │         Classification Results         │
│   Panel    │                                        │
│  (20%)     │              (80%)                     │
│            │                                        │
│  • File    │  • Construction Class                  │
│    Upload  │  • Sub Class                           │
│  • Process │  • Justification                       │
│    Button  │                                        │
│            │                                        │
└────────────┴────────────────────────────────────────┘
```

##### State Management
- Stateless design - no session state persistence
- File processing triggered by button click
- Results displayed immediately after processing
- Error states communicated through Streamlit alerts

#### Design Patterns
- **Single Page Application**: All functionality on one page
- **Progressive Disclosure**: Instructions visible, results shown after processing
- **Error-First Design**: API key validation before allowing uploads
- **Responsive Feedback**: Progress indicators during long operations

### 2. Processing Layer

#### PDF Processor (`pdf_processor.py`)

##### Core Functions

###### `extract_text_from_pdf(uploaded_file)`
**Purpose**: Extract text content from uploaded PDF files

**Process Flow**:
```
1. Convert Streamlit uploaded file to bytes
2. Open PDF using PyMuPDF (fitz)
3. Iterate through all pages
   ├─ Load page
   ├─ Extract text using get_text()
   ├─ Update progress bar
   └─ Handle page-level errors
4. Clean extracted text
5. Return complete text
```

**Technical Details**:
- Uses PyMuPDF's `stream` parameter for in-memory processing
- Progress tracking with Streamlit progress bar
- Page-level error handling (continues on page errors)
- Memory-efficient streaming approach

**Error Handling**:
```python
try:
    # Page extraction
except Exception as e:
    st.warning(f"Error extracting text from page {page_num + 1}: {str(e)}")
    continue  # Continue with other pages
```

###### `clean_text(text)`
**Purpose**: Clean and normalize extracted text

**Operations**:
1. Remove excessive whitespace (multiple spaces → single space)
2. Normalize newlines (multiple newlines → single newline)
3. Strip leading/trailing whitespace

**Regular Expressions Used**:
```python
text = re.sub(r'\s+', ' ', text)      # Collapse whitespace
text = re.sub(r'\n+', '\n', text)     # Normalize newlines
```

###### `truncate_text_for_llm(text, max_chars=50000)`
**Purpose**: Ensure text fits within LLM token limits

**Strategy**:
1. Check if text exceeds limit (default: 50,000 chars)
2. If yes, truncate at character limit
3. Attempt to find sentence boundary in last 20%
4. Add truncation indicator

**Smart Truncation**:
```python
last_period = truncated.rfind('.')
if last_period > max_chars * 0.8:
    truncated = truncated[:last_period + 1]
```
This ensures truncation happens at sentence boundaries when possible, maintaining context coherence.

#### Document Classifier (`classifier.py`)

##### Core Functions

###### `classify_document(extracted_text)`
**Purpose**: Main classification function interfacing with OpenAI API

**Process Flow**:
```
1. Truncate text to fit LLM limits (45,000 chars)
2. Create classification prompt
3. Call OpenAI API with structured parameters
4. Parse JSON response
5. Validate required fields
6. Return classification result
```

**API Configuration**:
```python
response = openai_client.chat.completions.create(
    model="gpt-4o",                        # Latest OpenAI model
    messages=[...],                        # System + user prompts
    response_format={"type": "json_object"}, # Force JSON output
    max_tokens=1000,                       # Limit response length
    temperature=0.3                        # Low temp for consistency
)
```

**Temperature Setting Rationale**:
- Temperature 0.3 provides deterministic, consistent results
- Reduces creative variation in classification
- Ensures repeatability for same documents
- Balances accuracy with slight flexibility

###### `create_classification_prompt(extracted_text)`
**Purpose**: Generate structured prompt for GPT-4o

**Prompt Structure**:
```
1. Role Definition
   └─ "You are an urban planning classification assistant"

2. Classification Taxonomy
   ├─ RESIDENTIAL (6 sub-classes)
   ├─ COMMERCIAL (8 sub-classes)
   ├─ INSTITUTIONAL (5 sub-classes)
   ├─ INFRASTRUCTURE (6 sub-classes)
   └─ RECREATIONAL (4 sub-classes)

3. Response Format Specification
   └─ JSON schema with required fields

4. Document Content
   └─ Extracted text between delimiters

5. Instructions
   └─ "Respond only with valid JSON"
```

**Prompt Engineering Techniques**:
- Clear role assignment for context
- Detailed taxonomy with descriptions
- Explicit format requirements
- Examples for each category
- Structured JSON schema
- Delimiters (===) for text separation

##### Classification Taxonomy

###### Residential
```
• Single-Family Homes: Detached or semi-detached houses
• Multi-Family Housing: Flats, apartments, townhomes
• Affordable Housing: Cost-accessible residential units
• Senior or Assisted Living: Elderly/assisted care facilities
• Student Housing: Student-specific accommodation
• Mixed Use: Residential + commercial components
```

###### Commercial
```
• Office Buildings: Office/administrative buildings
• Retail (High Street or Standalone): Shops, retail units
• Supermarket/Foodstore: Grocery/food stores
• Shopping Centre/Retail Park: Multiple retail units
• Hospitality (Hotels, Hostels): Accommodation services
• Restaurants/Cafes/Drive-thru: Food service facilities
• Warehousing/Distribution: Storage and logistics
• Mixed Use (Retail/Office): Combined retail/office
```

###### Institutional
```
• Healthcare: Hospitals/Clinics - Medical facilities
• Education: Schools/Colleges/Universities
• Government/Civic Buildings: Government structures
• Community Facilities: Libraries, halls, cultural centres
• Religious Institutions: Places of worship
```

###### Infrastructure
```
• Industrial: Manufacturing/Processing plants
• Energy: Renewable/Utility installations
• Transportation: Bus/Rail/Airport terminals
• Parking Structures: Multi-level/surface parking
• Logistics Hubs/Depots: Delivery and fulfillment centres
• Data Centres/Telecom Infrastructure: Server farms
```

###### Recreational
```
• Parks/Green Spaces: Public open spaces
• Sports Facilities/Arenas: Stadiums, gyms, recreation
• Event Venues/Outdoor Structures: Event spaces
• Temporary Structures/Permitted Events: Time-bound installations
```

###### `validate_classification_result(result)`
**Purpose**: Validate classification response structure

**Validation Checks**:
1. Ensure result is a dictionary
2. Verify all required fields present (class, sub_class, justification)
3. Confirm all fields are strings
4. Validate class is from allowed list
5. Check sub-class alignment (flexible matching)

**Flexible Validation Strategy**:
```python
valid_sub = any(
    allowed_sub in sub_class or sub_class in allowed_sub
    for allowed_sub in allowed_subclasses[main_class]
)
```
This allows partial matches, accommodating AI variation while maintaining taxonomy integrity.

### 3. External Services Layer

#### OpenAI API Integration

##### Authentication
```python
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)
```

##### API Communication Flow
```
Application                          OpenAI API
    │                                    │
    ├─ Prepare prompt with text         │
    ├─ Create chat completion request ─→│
    │                                    ├─ Process with GPT-4o
    │                                    ├─ Generate classification
    │                            JSON ←──┤
    ├─ Parse response                    │
    ├─ Validate structure                │
    └─ Return to UI                      │
```

##### Response Format
```json
{
    "class": "Main classification category",
    "sub_class": "Specific sub-category",
    "justification": "Detailed explanation with document references"
}
```

##### Error Handling
```python
try:
    # API call
except json.JSONDecodeError as e:
    raise Exception(f"Failed to parse classification response: {str(e)}")
except Exception as e:
    raise Exception(f"Classification failed: {str(e)}")
```

## Data Flow Architecture

### End-to-End Processing Flow

```
┌──────────────┐
│ User Uploads │
│  PDF File    │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────┐
│ Streamlit File Handler       │
│ • Receives UploadedFile obj  │
│ • Validates file type        │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ PDF Text Extraction          │
│ • Convert to bytes           │
│ • Load with PyMuPDF          │
│ • Extract page-by-page       │
│ • Show progress              │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Text Cleaning                │
│ • Remove excess whitespace   │
│ • Normalize newlines         │
│ • Strip formatting           │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Text Truncation              │
│ • Check length (45k chars)   │
│ • Smart sentence truncation  │
│ • Add indicator if truncated │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Prompt Construction          │
│ • Add classification taxonomy│
│ • Format with instructions   │
│ • Include document text      │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ OpenAI API Call              │
│ • Send to GPT-4o             │
│ • Request JSON format        │
│ • Wait for response          │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Response Processing          │
│ • Parse JSON                 │
│ • Validate structure         │
│ • Extract fields             │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Results Display              │
│ • Show class & sub-class     │
│ • Display justification      │
│ • Format for readability     │
└──────────────────────────────┘
```

## Technology Stack

### Core Technologies

#### Python 3.11+
- **Rationale**: Modern Python features, improved performance, type hints support
- **Version Constraint**: >=3.11 (specified in pyproject.toml)

#### Streamlit 1.46.1+
- **Purpose**: Web application framework
- **Benefits**:
  - Rapid prototyping
  - Built-in widgets and components
  - Automatic reruns and state management
  - No HTML/CSS/JavaScript required
- **Configuration**: Custom config in `.streamlit/config.toml`

#### PyMuPDF (fitz) 1.26.3+
- **Purpose**: PDF text extraction
- **Benefits**:
  - Fast and reliable
  - Handles various PDF formats
  - In-memory processing
  - Active development and support
- **Alternative Considered**: PyPDF2 (rejected due to reliability issues)

#### OpenAI Python Client 1.95.1+
- **Purpose**: Interface with OpenAI API
- **Benefits**:
  - Official library
  - Type-safe
  - Comprehensive error handling
  - Regular updates

### Dependencies

#### Direct Dependencies
```toml
[project.dependencies]
fitz = ">=0.0.1.dev2"           # PyMuPDF binding
openai = ">=1.95.1"             # OpenAI API client
pymupdf = ">=1.26.3"            # PDF processing
streamlit = ">=1.46.1"          # Web framework
```

#### Implicit Dependencies
- `python-dotenv`: Environment variable management
- `json`: JSON parsing (standard library)
- `re`: Regular expressions (standard library)
- `os`: System operations (standard library)
- `io`: Byte stream handling (standard library)

### Development Tools

#### Replit Configuration (`.replit`)
```toml
modules = ["python-3.11"]
channel = "stable-24_05"

packages = [
    "freetype",      # Font rendering
    "gumbo",         # HTML parsing
    "harfbuzz",      # Text shaping
    "jbig2dec",      # Image decoder
    "libjpeg_turbo", # JPEG processing
    "mupdf",         # PDF library
    "openjpeg",      # JPEG2000 support
    "swig",          # C/C++ binding
    "xcbuild"        # Build tools
]
```

## Design Patterns and Principles

### Architectural Patterns

#### Separation of Concerns
- **UI Layer**: Only handles user interaction
- **Processing Layer**: Only handles data transformation
- **Service Layer**: Only handles external API communication

#### Single Responsibility Principle
- Each module has one primary responsibility
- Functions are focused and testable
- Clear boundaries between components

#### Dependency Injection
```python
# API key injected via environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)
```

### Code Organization Patterns

#### Module Structure
```
planning_classifier/
├── app.py              # UI orchestration
├── classifier.py       # Classification logic
├── pdf_processor.py    # PDF handling
└── .streamlit/
    └── config.toml     # Streamlit configuration
```

#### Function Naming Convention
- Verbs for actions: `extract_text`, `classify_document`, `create_prompt`
- Clear, descriptive names
- No abbreviations

#### Error Handling Strategy
```python
try:
    # Primary operation
except SpecificException as e:
    # Handle specific case
    raise Exception(f"Context: {str(e)}")
except Exception as e:
    # Handle general case
    raise Exception(f"Operation failed: {str(e)}")
```

## Performance Considerations

### Processing Performance

#### PDF Extraction
- **Speed**: ~1-2 seconds per page
- **Memory**: O(n) where n = number of pages
- **Optimization**: Page-by-page processing prevents memory spikes

#### AI Classification
- **Speed**: 10-20 seconds per document
- **Bottleneck**: OpenAI API latency
- **Token Usage**: ~500-1000 tokens per classification

#### Text Truncation
- **Threshold**: 45,000 characters
- **Rationale**: Approximately 11,000 tokens (GPT-4o limit: ~128k tokens)
- **Strategy**: Smart sentence-boundary truncation

### Scalability

#### Vertical Scaling
- Single-process design limits vertical scaling
- Streamlit handles multiple concurrent sessions
- Memory usage: ~100-200MB per active session

#### Horizontal Scaling
- Stateless design enables horizontal scaling
- No session persistence required
- Can deploy multiple instances behind load balancer

### Optimization Opportunities

#### Current Optimizations
- In-memory PDF processing (no disk I/O)
- Smart text truncation (preserves context)
- Low temperature for faster API responses

#### Future Optimizations
- Caching of API responses for duplicate documents
- Batch processing API calls
- Asynchronous processing for multiple files
- Text compression before API transmission

## Security Architecture

### API Key Management
```python
# Environment variable validation
if not os.getenv("OPENAI_API_KEY"):
    st.error("⚠️ OpenAI API key not found")
    st.stop()
```

### Data Security
- **No Persistent Storage**: Documents not saved
- **In-Memory Processing**: All data in RAM only
- **No Logging**: Sensitive data not logged
- **Session Isolation**: Streamlit sessions independent

### Input Validation
- File type validation (PDF only)
- Text extraction verification
- JSON response validation
- API response sanitization

## Configuration Management

### Environment Variables
```bash
OPENAI_API_KEY=sk-...    # Required
```

### Streamlit Configuration
```toml
[server]
headless = true          # No browser UI needed
address = "0.0.0.0"      # Accept all connections
port = 8523              # Custom port
```

### Deployment Configuration
```toml
[deployment]
deploymentTarget = "autoscale"
run = ["streamlit", "run", "app.py", "--server.port", "5000"]
```

## Error Handling Architecture

### Error Categories

#### User Errors
- Invalid file upload → Warning message
- No text in PDF → Error with guidance
- Missing API key → Error with setup instructions

#### Processing Errors
- PDF extraction failure → Specific error message
- Text cleaning issues → Continue with raw text
- Truncation problems → Use hard truncation

#### API Errors
- Network failure → Retry suggestion
- Invalid response → Parse error details
- Rate limiting → Informative message

### Error Display Strategy
```python
st.error("❌ Error message")      # Critical errors
st.warning("⚠️ Warning message")  # Non-critical issues
st.info("ℹ️ Info message")        # Informational
```

## Testing Considerations

### Unit Testing Targets
- `clean_text()`: Text normalization
- `truncate_text_for_llm()`: Length handling
- `validate_classification_result()`: Structure validation

### Integration Testing Targets
- PDF extraction with various formats
- API communication with mock responses
- End-to-end classification workflow

### Manual Testing Checklist
- Various PDF formats (scanned, native, forms)
- Long documents (truncation testing)
- Error conditions (invalid PDFs, network issues)
- UI responsiveness across browsers

## Deployment Architecture

### Deployment Options

#### Replit (Current)
- Configuration in `.replit` file
- Auto-scaling support
- Built-in environment management

#### Docker (Alternative)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "app.py", "--server.port", "5000"]
```

#### Cloud Platforms
- **Heroku**: Procfile-based deployment
- **AWS**: EC2 or ECS deployment
- **GCP**: Cloud Run deployment
- **Azure**: App Service deployment

### Resource Requirements

#### Minimum
- CPU: 1 core
- RAM: 512MB
- Disk: 100MB
- Network: Outbound HTTPS

#### Recommended
- CPU: 2 cores
- RAM: 1GB
- Disk: 500MB
- Network: Low-latency connection

## Monitoring and Observability

### Logging Strategy
- Streamlit built-in logging
- Error tracking via exception handling
- User feedback via UI messages

### Metrics to Monitor
- Document processing time
- API response time
- Error rates
- Classification distribution

### Health Checks
- API key validation on startup
- PDF library availability
- Network connectivity to OpenAI

---

**Document Version**: 1.0
**Last Updated**: December 2025
**Architecture Review Date**: December 2025
