# Fashion Image Tagger - Technical Architecture

## System Architecture Overview

The Fashion Image Tagger is built using a modular three-tier architecture that separates concerns between presentation, business logic, and data management. This design promotes maintainability, testability, and scalability.

### Architectural Diagram

```
┌────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                         │
│                    (Web Browser)                           │
└────────────────┬───────────────────────────────────────────┘
                 │ HTTPS
                 │
┌────────────────▼───────────────────────────────────────────┐
│              PRESENTATION LAYER                            │
│                   (app.py)                                 │
│  ┌──────────────────────────────────────────────────┐    │
│  │  Streamlit Framework                              │    │
│  │  - Page configuration & layout                    │    │
│  │  - Session state management                       │    │
│  │  - File upload handling                           │    │
│  │  - Results display & formatting                   │    │
│  │  - Export button controls                         │    │
│  └──────────────────────────────────────────────────┘    │
└────────────────┬───────────────────────────────────────────┘
                 │ Python Function Calls
                 │
┌────────────────▼───────────────────────────────────────────┐
│              BUSINESS LOGIC LAYER                          │
│            (fashion_analyzer.py)                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │  FashionAnalyzer Class                            │    │
│  │  - Image encoding (Base64)                        │    │
│  │  - Prompt generation                              │    │
│  │  - AI vision analysis                             │    │
│  │  - Result validation                              │    │
│  │  - Attribute normalization                        │    │
│  │  - Consistency rule application                   │    │
│  │  - Export formatting (JSON/CSV)                   │    │
│  └──────────────────────────────────────────────────┘    │
└────────┬───────────────────────────┬────────────────────────┘
         │                           │
         │ API Calls                 │ File I/O
         │                           │
┌────────▼──────────┐     ┌─────────▼──────────────────────┐
│   EXTERNAL API    │     │      DATA LAYER                │
│   (OpenAI)        │     │  (fashion_ontology.json)       │
│                   │     │                                │
│  ┌─────────────┐  │     │  ┌──────────────────────┐     │
│  │  GPT-4o     │  │     │  │  Fashion Taxonomy    │     │
│  │  Vision     │  │     │  │  - Gender values     │     │
│  │  Model      │  │     │  │  - Product types     │     │
│  │             │  │     │  │  - Key attributes    │     │
│  │             │  │     │  │  - Specific attrs    │     │
│  └─────────────┘  │     │  └──────────────────────┘     │
└───────────────────┘     └────────────────────────────────┘
```

## Layer-by-Layer Analysis

### 1. Presentation Layer (app.py)

#### Responsibilities
- User interface rendering and interaction handling
- Session state persistence across user interactions
- Image upload and preview functionality
- Results display and formatting
- Export functionality coordination

#### Key Components

**Page Configuration**
```python
st.set_page_config(
    page_title="Fashion Image Tagger",
    page_icon="👗",
    layout="wide"
)
```
- Sets up Streamlit application metadata
- Configures wide layout for better space utilization
- Establishes branding with custom page title and icon

**Session State Management**
```python
if "analyzer" not in st.session_state:
    st.session_state.analyzer = FashionAnalyzer()
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None
```
- Maintains analyzer instance across reruns
- Persists analysis results for display
- Stores uploaded image bytes for processing

**UI Layout Structure**
1. **Header Section**: Title and description
2. **Top Row** (2 columns):
   - Left: Image upload control
   - Right: Analyze button
3. **Bottom Row** (2 columns):
   - Left: Image preview (300px width)
   - Right: Analysis results with export options
4. **Footer**: Information section explaining functionality

**Error Handling**
- Graceful degradation on initialization failure
- User-friendly error messages for analysis failures
- Try-catch blocks around image loading and export operations

#### Data Flow
1. User uploads image → stored in session state
2. User clicks "Analyze" → triggers analysis workflow
3. Results received → stored in session state
4. Results displayed → with export options
5. User exports → download button triggered

### 2. Business Logic Layer (fashion_analyzer.py)

#### FashionAnalyzer Class Architecture

**Class Initialization**
```python
class FashionAnalyzer:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.ontology = self._load_ontology()
```
- Initializes OpenAI client with API key from environment
- Loads fashion ontology from JSON file
- Raises exceptions if dependencies unavailable

#### Core Methods

**1. _load_ontology()**
- **Purpose**: Load and parse fashion taxonomy from JSON
- **Returns**: Dictionary containing complete ontology structure
- **Error Handling**: FileNotFoundError, JSONDecodeError exceptions
- **Usage**: Called during initialization

**2. _encode_image_to_base64()**
```python
def _encode_image_to_base64(self, image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode('utf-8')
```
- **Purpose**: Convert image bytes to base64 string for API transmission
- **Input**: Raw image bytes
- **Output**: Base64-encoded string
- **Note**: Required format for OpenAI Vision API

**3. _create_analysis_prompt()**
- **Purpose**: Generate comprehensive analysis prompt with ontology
- **Output**: 230-line detailed prompt with methodology and rules
- **Sections**:
  - Analysis methodology (5 steps)
  - Basic attributes (Gender, ProductType)
  - Key attributes (Color, Pattern, Material, Style)
  - Product-specific attributes (7 categories)
  - Critical accuracy rules
  - Special attention guidelines
  - Mandatory JSON structure

**Prompt Engineering Strategy**:
- Step-by-step analysis methodology
- Detailed value definitions with examples
- Mandatory attribute requirements
- Special attention sections for problematic attributes
- JSON structure enforcement
- Zero-shot learning approach with explicit instructions

**4. analyze_image()**
```python
def analyze_image(self, image_bytes: bytes) -> Dict[str, Any]:
```
- **Purpose**: Main analysis orchestration method
- **Steps**:
  1. Encode image to base64
  2. Create analysis prompt
  3. Call OpenAI Vision API
  4. Parse JSON response
  5. Validate and clean results
- **API Parameters**:
  - model: "gpt-4o"
  - response_format: {"type": "json_object"}
  - max_tokens: 1500
  - temperature: 0.1 (low for consistency)
  - top_p: 0.9
  - detail: "high" (for image processing)

**5. _validate_and_clean_result()**
- **Purpose**: Ensure all attributes match ontology values
- **Process**:
  1. Initialize validated structure with all required fields
  2. Validate Gender against allowed values
  3. Validate ProductType against allowed values
  4. Validate each KeyAttribute
  5. Validate ProductSpecificAttributes based on ProductType
  6. Apply normalization for variations
  7. Apply consistency rules
- **Output**: Fully validated result dictionary

**6. _normalize_attribute_value()**
```python
def _normalize_attribute_value(self, value: str, valid_options: list) -> Optional[str]:
```
- **Purpose**: Handle attribute value variations and synonyms
- **Strategy**:
  1. Exact match (case-insensitive)
  2. Common mapping lookup (42 predefined mappings)
  3. Partial match with similarity threshold (>50%)
  4. Return None if no match
- **Examples**:
  - "short sleeve" → "Short"
  - "navy blue" → "Blue"
  - "checkered" → "Checked"
  - "cotton blend" → "Cotton"

**Common Mappings Table**:
| Input Variation | Normalized Value | Category |
|----------------|------------------|----------|
| short sleeve, half sleeve | Short | Sleeve |
| long sleeve, full sleeve | Full | Sleeve |
| 3/4 sleeve, three quarter | 3/4th | Sleeve |
| navy, navy blue | Blue | Color |
| gray, silver | Grey | Color |
| plain | Solid | Pattern |
| checkered, check | Checked | Pattern |
| cotton blend | Cotton | Material |

**7. _apply_consistency_rules_new_schema()**
- **Purpose**: Apply logical consistency corrections
- **Rules by Product Type**:
  - **Topwear**: Convert "Polo" neckline to "Collared"
  - **Dresses**: Ensure SleeveType is provided
  - **Footwear**: Infer ToeStyle from HeelType if missing
  - **Outerwear**: Convert "Sports" style to "Casual"

**8. export_to_json()**
- **Purpose**: Serialize analysis result to JSON format
- **Parameters**: Indentation, non-ASCII support
- **Output**: Formatted JSON string

**9. export_to_csv_format()**
- **Purpose**: Flatten nested structure for CSV export
- **Process**:
  1. Flatten Gender and ProductType
  2. Prefix KeyAttributes with "KeyAttributes_"
  3. Prefix ProductSpecificAttributes with "ProductSpecific_"
  4. Create header row and value row
- **Output**: CSV string with header and data

### 3. Data Layer (fashion_ontology.json)

#### Structure Overview

```json
{
  "Gender": [...],
  "ProductType": [...],
  "KeyAttributes": {
    "Color": [...],
    "Pattern": [...],
    "Material": [...],
    "Style": [...]
  },
  "ProductSpecificAttributes": {
    "Topwear": {...},
    "Bottomwear": {...},
    "Dresses": {...},
    "Jumpsuits": {...},
    "Footwear": {...},
    "Outerwear": {...},
    "Accessories": {}
  }
}
```

#### Taxonomy Details

**Gender Classification (5 values)**
- Man, Woman, Boy, Girl, Unisex

**Product Types (7 categories)**
- Topwear, Bottomwear, Dresses, Jumpsuits, Footwear, Outerwear, Accessories

**Key Attributes**
- **Color** (28 values): Specific shades included (Burgundy, Navy, Magenta, etc.)
- **Pattern** (5 values): Solid, Striped, Printed, Checked, Floral
- **Material** (11 values): Natural and synthetic fabrics
- **Style** (5 values): Casual, Formal, Party, Sports, Ethnic

**Product-Specific Attributes**

| Product Type | Attributes | Value Count |
|-------------|------------|-------------|
| Topwear | SleeveLength, Neckline, Fit | 4, 5, 3 |
| Bottomwear | Length, Fit, WaistRise | 3, 4, 3 |
| Dresses | DressLength, SleeveType | 4, 7 |
| Jumpsuits | SleeveType, Neckline, Length, Fit | 4, 6, 3, 3 |
| Footwear | HeelType, ToeStyle, ClosureType | 4, 4, 4 |
| Outerwear | ClosureType, CollarStyle | 3, 4 |
| Accessories | (none) | 0 |

## Data Flow Sequence

### Complete Analysis Workflow

```
┌─────────────┐
│  User       │
│  Uploads    │
│  Image      │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  app.py: File Uploader              │
│  - Receives image file               │
│  - Stores bytes in session state    │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  User Clicks "Analyze" Button       │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  app.py: Trigger Analysis           │
│  - Call analyzer.analyze_image()    │
│  - Pass image bytes                 │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  FashionAnalyzer:                   │
│  _encode_image_to_base64()          │
│  - Convert bytes to base64 string   │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  FashionAnalyzer:                   │
│  _create_analysis_prompt()          │
│  - Generate 230-line prompt         │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  OpenAI API Call                    │
│  - Model: gpt-4o                    │
│  - System prompt + user prompt      │
│  - Base64 image + text              │
│  - Temperature: 0.1                 │
│  - Response format: JSON            │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  OpenAI Vision Model                │
│  - Analyzes image                   │
│  - Extracts attributes              │
│  - Returns JSON response            │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  FashionAnalyzer:                   │
│  Parse JSON Response                │
│  - json.loads()                     │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  FashionAnalyzer:                   │
│  _validate_and_clean_result()       │
│  - Validate against ontology        │
│  - Normalize variations             │
│  - Apply consistency rules          │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Return Validated Result            │
│  to app.py                          │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  app.py: Store in Session State     │
│  - st.session_state.analysis_result │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  app.py: Display Results            │
│  - Format attributes in columns     │
│  - Show export buttons              │
│  - Expandable full JSON view        │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  User Exports (Optional)            │
│  - Click JSON or CSV button         │
│  - Download formatted file          │
└─────────────────────────────────────┘
```

## Configuration Management

### Environment Variables
```bash
OPENAI_API_KEY=sk-...
```
- Loaded via python-dotenv
- Required for OpenAI API authentication
- Must have GPT-4o access enabled

### Streamlit Configuration
File: `.streamlit/config.toml`
```toml
[server]
headless = true
address = "0.0.0.0"
port = 8525
```
- Headless mode for deployment
- Binds to all network interfaces
- Custom port configuration

### Replit Configuration
File: `.replit`
```toml
modules = ["python-3.11"]
channel = "stable-25_05"
deploymentTarget = "autoscale"
run = ["streamlit", "run", "app.py", "--server.port", "5000"]
```
- Python 3.11 environment
- Autoscaling deployment
- Port 5000 for web service

## API Integration Details

### OpenAI API Interaction

**Request Structure**
```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "system",
            "content": "You are a professional fashion analyst..."
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                        "detail": "high"
                    }
                }
            ]
        }
    ],
    response_format={"type": "json_object"},
    max_tokens=1500,
    temperature=0.1,
    top_p=0.9
)
```

**Response Handling**
```python
response_content = response.choices[0].message.content
result = json.loads(response_content)
```

**Error Handling**
- JSONDecodeError: Invalid response format
- API exceptions: Network issues, rate limits
- Null content: Empty API response

## Performance Optimization Strategies

### Current Optimizations
1. **Low Temperature (0.1)**: Consistent, deterministic outputs
2. **High Detail Mode**: Maximum image analysis quality
3. **JSON Response Format**: Structured output enforcement
4. **Session State**: Avoids re-initialization on reruns
5. **Lazy Loading**: Ontology loaded once at startup

### Potential Future Optimizations
1. **Response Caching**: Cache results for identical images
2. **Batch Processing**: Analyze multiple images in parallel
3. **Prompt Compression**: Reduce token usage while maintaining accuracy
4. **Streaming Responses**: Progressive result display
5. **Image Preprocessing**: Resize/compress before API call

## Security Considerations

### Current Security Measures
1. **Environment Variable Storage**: API key not hardcoded
2. **No Persistent Storage**: Images not saved to disk
3. **HTTPS**: Secure transmission to OpenAI
4. **Session Isolation**: Browser-based session data

### Security Recommendations
1. **API Key Rotation**: Regular key updates
2. **Rate Limiting**: Prevent abuse
3. **Input Validation**: File type and size restrictions
4. **Content Filtering**: Block inappropriate images
5. **Audit Logging**: Track API usage and costs

## Scalability Considerations

### Current Limitations
- Single-threaded processing
- No queueing system
- Session-based state (not distributed)
- Synchronous API calls

### Scalability Path
1. **Horizontal Scaling**: Multiple Streamlit instances
2. **Load Balancer**: Distribute traffic
3. **Redis Session Store**: Shared session state
4. **Message Queue**: Asynchronous processing (Celery, RabbitMQ)
5. **CDN**: Static asset caching
6. **Database**: Persistent result storage

## Error Handling Architecture

### Error Types and Handling

| Error Type | Location | Handling Strategy |
|-----------|----------|------------------|
| Missing API Key | FashionAnalyzer.__init__ | Exception with user message |
| Ontology File Not Found | _load_ontology() | FileNotFoundError exception |
| Invalid JSON Ontology | _load_ontology() | JSONDecodeError exception |
| Image Upload Failure | app.py | Try-catch with error display |
| API Call Failure | analyze_image() | Exception with error message |
| JSON Parse Failure | analyze_image() | JSONDecodeError with context |
| Invalid Attributes | _validate_and_clean_result() | Normalize or set to None |
| Export Failure | export methods | Exception with failure message |

### User-Facing Error Messages
- Friendly, non-technical language
- Actionable guidance where possible
- No sensitive information exposure
- Logged for debugging purposes

## Testing Considerations

### Recommended Test Coverage

**Unit Tests**
- `_encode_image_to_base64()`: Encoding correctness
- `_normalize_attribute_value()`: Mapping accuracy
- `_validate_and_clean_result()`: Validation logic
- `export_to_json()`: JSON formatting
- `export_to_csv_format()`: CSV formatting

**Integration Tests**
- OpenAI API integration
- Ontology loading
- End-to-end analysis workflow

**UI Tests**
- Image upload functionality
- Button interactions
- Results display
- Export downloads

## Conclusion

The Fashion Image Tagger's technical architecture prioritizes simplicity, maintainability, and extensibility. The three-tier design cleanly separates concerns, while the comprehensive prompt engineering and validation logic ensure reliable, accurate results. The system is designed for easy deployment and operation, with clear extension points for future enhancements such as batch processing, custom ontologies, and multi-language support.
