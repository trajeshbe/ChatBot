# API Reference Guide

## Table of Contents
1. [Module Overview](#module-overview)
2. [Class Reference](#class-reference)
3. [Method Reference](#method-reference)
4. [Data Models](#data-models)
5. [Prompt Templates](#prompt-templates)
6. [Configuration Schema](#configuration-schema)

## Module Overview

### File Structure

```
procurement_matcher/
├── app.py                    # Main application entry point
├── legal_profile.py          # Legal case matching module
├── procurement.py            # Vendor profile matching module
├── vendor_mapping.py         # Vendor taxonomy extraction module
├── utils.py                  # Common utilities
├── config_reader.py          # Configuration loader
├── log_writer.py             # Logging setup
├── legal_prompt.py           # Legal domain prompts
├── procurement_prompt.py     # Procurement domain prompts
├── vendor_prompt.py          # Vendor taxonomy prompts
├── legal_ui.py              # Standalone legal UI
├── procurement_ui.py        # Standalone procurement UI
├── vendor_ui.py             # Standalone vendor taxonomy UI
└── config.yaml              # Application configuration
```

---

## Class Reference

### App Class

**Module**: `app.py`

**Inheritance**: `App(LegalProfile, VendorProfile, VendorMapping)`

**Description**: Main application class that combines all three matching functionalities through multiple inheritance.

#### Constructor

```python
def __init__(self)
```

**Purpose**: Initialize Streamlit page configuration and session state

**Side Effects**:
- Sets Streamlit page config with title "Matcher" and wide layout
- Initializes parent class constructors
- Creates session state variables: `legal`, `procurement`, `vendor`

**Example**:
```python
ob = App()
```

#### Methods

##### render_ui()

```python
def render_ui(self) -> None
```

**Purpose**: Render the complete Streamlit user interface with three tabs

**Returns**: None

**Tab Structure**:
1. **Legal Tab**: Case matching interface
2. **Procurement Tab**: Vendor matching interface
3. **Vendor Taxonomy Tab**: Classification interface

**Example**:
```python
ob = App()
ob.render_ui()
```

**UI Components**:

**Tab 1 - Legal**:
- Title: "Case Matcher"
- Form with:
  - `precedent_file`: PDF file uploader (multiple files)
  - `strategy_file`: TXT file uploader (single file)
  - Submit button
- Results dataframe (sorted by Confidence_Score descending)

**Tab 2 - Procurement**:
- Title: "Procurement Matcher"
- Form with:
  - `pdf_file`: PDF file uploader (multiple files)
  - `txt_file`: TXT file uploader (single file)
  - Submit button
- Results dataframe (sorted by Confidence_Score descending)

**Tab 3 - Vendor Taxonomy**:
- Title: "Document Classifier based on Taxonomy"
- Form with:
  - `txt_file`: Text area input
  - Submit button
- Results dataframe

---

### LegalProfile Class

**Module**: `legal_profile.py`

**Inheritance**: `LegalProfile(Utils)`

**Description**: Handles matching of precedent legal cases with current cases

#### Constructor

```python
def __init__(self)
```

**Purpose**: Initialize LangChain components for legal case matching

**Creates**:
- `self.legal_parser`: JsonOutputParser configured with LegalTemplate
- `self.prompt_legal`: PromptTemplate with legal_prompt template
- `self.legal_chain`: LangChain chain (prompt | llm)

**Raises**: Logs exception if initialization fails

**Example**:
```python
legal_matcher = LegalProfile()
```

#### Methods

##### get_match_score_legal()

```python
def get_match_score_legal(
    self,
    precedent_files: List[str],
    strategy_file: str
) -> List[dict]
```

**Purpose**: Match precedent cases against a current case strategy

**Parameters**:
- `precedent_files` (List[str]): List of file paths to precedent case PDFs
- `strategy_file` (str): File path to current case TXT file

**Returns**: List[dict] - List of matching results, each containing:
- `Case_Strategy` (str): Current case title
- `Precedent_Case` (str): Precedent case title
- `Confidence_Score` (float): Match confidence (0.1 to 1.0)
- `Justification` (str): Explanation of the match

**Error Handling**:
- Returns empty list on exception
- Logs errors via logger.error()
- Shows Streamlit progress bar during processing

**Example**:
```python
precedent_files = ["/path/to/case1.pdf", "/path/to/case2.pdf"]
strategy_file = "/path/to/current_case.txt"

results = legal_matcher.get_match_score_legal(precedent_files, strategy_file)

# Results format:
# [
#   {
#     "Case_Strategy": "Current Case Title",
#     "Precedent_Case": "Precedent Case 1",
#     "Confidence_Score": 0.85,
#     "Justification": "Both cases involve similar legal principles..."
#   },
#   ...
# ]
```

**Processing Flow**:
1. Read strategy file content
2. Initialize Streamlit progress bar
3. For each precedent file:
   - Extract PDF content
   - Invoke legal_chain with strategy and precedent content
   - Parse JSON response
   - Append to results
   - Update progress bar
4. Clear progress bar
5. Return results

---

### VendorProfile Class

**Module**: `procurement.py`

**Inheritance**: `VendorProfile(Utils)`

**Description**: Matches vendor capabilities against procurement requirements

#### Constructor

```python
def __init__(self)
```

**Purpose**: Initialize LangChain components for vendor matching

**Creates**:
- `self.vendor_parser`: JsonOutputParser configured with VendorTemplate
- `self.prompt_vendor`: PromptTemplate with vendor_prompt template
- `self.procurement_chain`: LangChain chain (prompt | llm)

**Raises**: Logs exception if initialization fails

**Example**:
```python
vendor_matcher = VendorProfile()
```

#### Methods

##### get_match_score_procurement()

```python
def get_match_score_procurement(
    self,
    pdf_files: List[str],
    txt_file: str
) -> List[dict]
```

**Purpose**: Match vendor profiles against procurement requirements

**Parameters**:
- `pdf_files` (List[str]): List of file paths to vendor profile PDFs
- `txt_file` (str): File path to requirement TXT file

**Returns**: List[dict] - List of vendor matches, each containing:
- `Current_Requirement` (str): Requirement title
- `Vendor_Name` (str): Vendor name
- `Confidence_Score` (float): Match confidence (0.1 to 1.0)
- `Justification` (str): Explanation of capability alignment

**Error Handling**:
- Returns empty list on exception
- Logs errors via logger.error()
- Shows Streamlit progress bar during processing

**Example**:
```python
vendor_files = ["/path/to/vendor1.pdf", "/path/to/vendor2.pdf"]
requirement_file = "/path/to/requirement.txt"

results = vendor_matcher.get_match_score_procurement(vendor_files, requirement_file)

# Results format:
# [
#   {
#     "Current_Requirement": "Cloud Infrastructure Services",
#     "Vendor_Name": "Acme Cloud Solutions",
#     "Confidence_Score": 0.92,
#     "Justification": "Vendor offers comprehensive cloud services including..."
#   },
#   ...
# ]
```

**Processing Flow**:
1. Read requirement file content
2. Initialize Streamlit progress bar
3. For each vendor PDF:
   - Extract PDF content
   - Invoke procurement_chain
   - Parse JSON response
   - Append to results
   - Update progress bar
4. Sleep 1 second (rate limiting)
5. Clear progress bar
6. Return results

---

### VendorMapping Class

**Module**: `vendor_mapping.py`

**Inheritance**: `VendorMapping(Utils)`

**Description**: Extracts structured taxonomy from vendor information

#### Constructor

```python
def __init__(self)
```

**Purpose**: Initialize LangChain components for taxonomy extraction

**Creates**:
- `self.vendor_parser`: JsonOutputParser configured with VendorTaxonomy
- `self.prompt_vendor`: PromptTemplate with vendor_prompt template
- `self.vendor_chain`: LangChain chain (prompt | llm)

**Raises**: Logs exception if initialization fails

**Example**:
```python
taxonomy_extractor = VendorMapping()
```

#### Methods

##### get_vendor_taxonomy()

```python
def get_vendor_taxonomy(
    self,
    txt_content: str
) -> dict
```

**Purpose**: Extract structured taxonomy from vendor text

**Parameters**:
- `txt_content` (str): Raw vendor information text

**Returns**: dict - Taxonomy information with keys:
- `vendor` (str): Vendor name
- `category` (str): High-level category
- `sub_category` (str): Comma-separated sub-categories
- `application` (str): Product/service name
- `function` (str): Comma-separated functions
- `service_flag` (str): Comma-separated services
- `compliance` (str): Comma-separated compliance standards
- `geography` (str): Comma-separated regions
- `risk_flag` (str): Risk assessment
- `sustainability_flag` (str): Sustainability indicator

**Error Handling**:
- Returns empty dict on exception
- No explicit logging (silent failure)

**Example**:
```python
vendor_text = """
Acme Corp provides cloud infrastructure services with
ISO 27001 compliance, operating in US and EU regions.
"""

taxonomy = taxonomy_extractor.get_vendor_taxonomy(vendor_text)

# Result format:
# {
#   "vendor": "Acme Corp",
#   "category": "Technology",
#   "sub_category": "Cloud Services, Infrastructure",
#   "application": "Cloud Infrastructure",
#   "function": "Hosting, Storage, Computing",
#   "service_flag": "IaaS, PaaS",
#   "compliance": "ISO 27001",
#   "geography": "US, EU",
#   "risk_flag": "Low - Established vendor with compliance",
#   "sustainability_flag": "Yes - Energy efficient data centers"
# }
```

**Processing Flow**:
1. Invoke vendor_chain with text content
2. Parse JSON response
3. Convert list fields to comma-separated strings
4. Return formatted dictionary

---

### Utils Class

**Module**: `utils.py`

**Inheritance**: `Utils(ConfigLoader)`

**Description**: Common utility methods for LLM integration and file processing

#### Constructor

```python
def __init__(self)
```

**Purpose**: Initialize LLM client from configuration

**Creates**:
- `self.llm`: LangChain chat model instance

**Configuration Used**:
- `config_data["llm"]["model"]`: Model name (e.g., "gpt-4o-mini")
- `config_data["llm"]["model_provider"]`: Provider (e.g., "openai")

**Example**:
```python
utils = Utils()
llm = utils.llm  # Access initialized LLM
```

#### Methods

##### read_txt_file()

```python
def read_txt_file(self, txt_file: str) -> str
```

**Purpose**: Read text file with UTF-8 encoding

**Parameters**:
- `txt_file` (str): Path to text file

**Returns**: str - File content or empty string on error

**Error Handling**:
- Catches exceptions and logs via logger.error()
- Shows Streamlit warning on failure
- Returns empty string on error

**Example**:
```python
content = utils.read_txt_file("/path/to/file.txt")
if content:
    print(f"Read {len(content)} characters")
```

##### read_pdf_file()

```python
def read_pdf_file(self, pdf_file: str) -> str
```

**Purpose**: Extract text from PDF file

**Parameters**:
- `pdf_file` (str): Path to PDF file

**Returns**: str - Extracted text or empty string on error

**Implementation**:
- Uses PyMuPDF (fitz) for extraction
- Joins pages with double newlines
- UTF-8 text extraction

**Error Handling**:
- Catches exceptions and logs via logger.error()
- Shows Streamlit warning on failure
- Returns empty string on error

**Example**:
```python
pdf_content = utils.read_pdf_file("/path/to/document.pdf")
if pdf_content:
    print(f"Extracted {len(pdf_content)} characters from PDF")
```

---

### ConfigLoader Class

**Module**: `config_reader.py`

**Inheritance**: `ConfigLoader(CustomLogger)`

**Description**: Loads and manages application configuration

#### Constructor

```python
def __init__(self)
```

**Purpose**: Load environment variables and configuration file

**Side Effects**:
- Loads .env file via python-dotenv
- Reads config.yaml
- Sets self.config_data

**Raises**: Exits application with critical log if config not found

**Example**:
```python
config = ConfigLoader()
model_name = config.config_data["llm"]["model"]
```

#### Methods

##### read_config()

```python
def read_config(self) -> dict
```

**Purpose**: Read and parse config.yaml file

**Returns**: dict - Configuration dictionary

**Expected Config Location**: `./config.yaml` (current working directory)

**Raises**:
- Exception if config file not found
- Logs critical error and exits application

**Example**:
```python
config_data = config.read_config()
# {
#   "data_path": "data",
#   "llm": {
#     "model": "gpt-4o-mini",
#     "model_provider": "openai",
#     "temperature": 0
#   }
# }
```

---

### CustomLogger Class

**Module**: `log_writer.py`

**Inheritance**: None (Base class)

**Description**: Sets up structured JSON logging with rotation

#### Constructor

```python
def __init__(self)
```

**Purpose**: Configure loguru logger with dual streams

**Side Effects**:
- Creates `./logs/` directory if not exists
- Configures two log files:
  - `info_logs.json`: INFO level only
  - `error_logs.json`: DEBUG, WARNING, ERROR, CRITICAL levels

**Log Configuration**:

**Info Logs**:
- File: `./logs/info_logs.json`
- Format: JSON serialized
- Rotation: Daily at 00:00
- Retention: 7 days
- Compression: ZIP
- Level Filter: INFO only

**Error Logs**:
- File: `./logs/error_logs.json`
- Format: JSON serialized
- Rotation: Daily at 00:00
- Retention: 30 days
- Compression: ZIP
- Level Filter: All except INFO
- Features: Backtrace and diagnose enabled

**Example**:
```python
logger = CustomLogger()
logger.logger.info("Application started")
logger.logger.error("Error occurred")
```

#### Methods

##### setup_logger()

```python
def setup_logger(self) -> None
```

**Purpose**: Configure loguru logger instance

**Side Effects**:
- Creates logs directory
- Removes default logger
- Adds two file handlers
- Sets self.logger with name binding

**Log Format**:
```
{time:YYYY-MM-DD HH:mm:ss} | {level} | {message} | {name} | {file} | {line} | {function}
```

##### log_exception()

```python
def log_exception(self, exc_tb: traceback) -> List[dict]
```

**Purpose**: Extract traceback into structured format

**Parameters**:
- `exc_tb` (traceback): Exception traceback object

**Returns**: List[dict] - List of traceback frames, each containing:
- `file` (str): Source file path
- `function` (str): Function name
- `line` (int): Line number

**Example**:
```python
try:
    risky_operation()
except Exception as e:
    import sys
    tb_info = logger.log_exception(sys.exc_info()[2])
    logger.logger.error(f"Error: {e}, Traceback: {tb_info}")
```

---

## Data Models

### LegalTemplate

**Module**: `legal_profile.py`

**Base Class**: `pydantic.BaseModel`

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

**Field Descriptions**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Case_Strategy | str | Yes | Current case title/name |
| Precedent_Case | str | Yes | Precedent case title/name |
| Confidence_Score | float | Yes | Match confidence (0.1-1.0) |
| Justification | str | Yes | Explanation for the score |

**Validation**:
- All fields required
- Confidence_Score must be float
- Pydantic enforces type validation

---

### VendorTemplate

**Module**: `procurement.py`

**Base Class**: `pydantic.BaseModel`

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

**Field Descriptions**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Current_Requirement | str | Yes | Requirement title/summary |
| Vendor_Name | str | Yes | Vendor name |
| Confidence_Score | float | Yes | Match confidence (0.1-1.0) |
| Justification | str | Yes | Capability alignment explanation |

---

### VendorTaxonomy

**Module**: `vendor_mapping.py`

**Base Class**: `pydantic.BaseModel`

```python
class VendorTaxonomy(BaseModel):
    vendor: str = Field(..., description="Given name of the vendor")

    category: Optional[str] = Field(
        description="High-level category of the vendor's offering"
    )

    sub_category: Optional[List[str]] = Field(
        description="Sub-category under the main category"
    )

    application: Optional[str] = Field(
        description="Application or product associated with the vendor"
    )

    function: Optional[List[str]] = Field(
        description="All Business or technical function served by the vendor"
    )

    service_flag: Optional[List[str]] = Field(
        default_factory=list,
        description="List of all services offered"
    )

    compliance: Optional[List[str]] = Field(
        default_factory=list,
        description="List of all compliance standards mentioned"
    )

    geography: Optional[List[str]] = Field(
        default_factory=list,
        description="List of all the countries or regions the vendor operates in"
    )

    risk_flag: str = Field(
        description="Is risk involved and What will be the level of risk in this and what the risk is."
    )

    sustainability_flag: Optional[str] = Field(
        None,
        description="Sustainability indicator Yes/No and what it is"
    )
```

**Field Descriptions**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| vendor | str | Yes | - | Vendor name |
| category | str | No | None | High-level category |
| sub_category | List[str] | No | None | Sub-categories |
| application | str | No | None | Product/service name |
| function | List[str] | No | None | Business/technical functions |
| service_flag | List[str] | No | [] | Services offered |
| compliance | List[str] | No | [] | Compliance standards |
| geography | List[str] | No | [] | Operating regions |
| risk_flag | str | Yes | - | Risk assessment |
| sustainability_flag | str | No | None | Sustainability info |

---

## Prompt Templates

### Legal Prompt

**Module**: `legal_prompt.py`

**Variable**: `legal_prompt`

**Purpose**: Guide LLM to compare legal cases based on legal issues and reasoning

**Template**:
```python
legal_prompt = """
You are a legal reasoning assistant.

Your task is to analyze the relationship between a given **Current Case**
and a **Precedent Case**, with a focus on the **core legal issues**
involved - not on the outcomes or judgments.

### Inputs:
- **Precedent Case**: A historical case including background, facts,
  legal issues, and legal reasoning.
- **Current Case**: A brief description of the ongoing or present legal matter.

### Task:
Compare the Precedent Case with the Current Case, focusing primarily on
the **similarity of legal issues and reasoning**.

- Provide a **confidence score** between **0.1** and **1.0**, indicating
  how well the precedent aligns with the legal issues in the current case.
- Offer a **justification** explaining the degree of alignment, highlighting
  shared legal principles or reasoning patterns — not based on the outcome
  of the case.

{format_instruction}
Do not return any preamble or explanations, return only a pure JSON string
surrounded by triple backticks (```).

Current Case:
{strategies}

Precedent Case:
{precedent}
"""
```

**Input Variables**:
- `strategies`: Current case content (from TXT file)
- `precedent`: Precedent case content (from PDF)
- `format_instruction`: JSON schema from Pydantic model

**Key Instructions**:
- Focus on legal issues, not outcomes
- Confidence score 0.1 to 1.0
- JSON output only
- No preamble

---

### Procurement Prompt

**Module**: `procurement_prompt.py`

**Variable**: `vendor_prompt`

**Purpose**: Guide LLM to match vendor capabilities with requirements

**Template**:
```python
vendor_prompt = """
You are a vendor evaluation assistant.

Your task is to analyze the relationship between a given **Requirement**
and **Vendor Information**, with a focus on the **core capabilities,
features, and offerings** — not on commercial terms or past performance.

### Inputs:
- **Requirement**: A detailed description of a project's needs,
  expectations, and specifications.
- **Vendor Information**: Information about a vendor's offerings,
  capabilities, technologies, or services.

### Task:
Compare the Requirement with the Vendor Information, focusing primarily
on the **alignment of features, capabilities, and functional relevance**.

- Provide a **confidence score** between **0.1** and **1.0**, indicating
  how well the vendor aligns with the given requirement.
- Offer a **justification** explaining the degree of alignment, highlighting
  shared features, matching specifications, or relevant capabilities — not
  based on pricing or contracts.

{format_instruction}
Do not return any preamble or explanations, return only a pure JSON string
surrounded by triple backticks (```).

Requirement:
{requirement}

Vendor Information:
{vendor}
"""
```

**Input Variables**:
- `requirement`: Procurement requirement content (from TXT file)
- `vendor`: Vendor profile content (from PDF)
- `format_instruction`: JSON schema from Pydantic model

**Key Instructions**:
- Focus on capabilities, not commercial terms
- Confidence score 0.1 to 1.0
- JSON output only
- No preamble

---

### Vendor Taxonomy Prompt

**Module**: `vendor_prompt.py`

**Variable**: `vendor_prompt`

**Purpose**: Guide LLM to extract structured taxonomy from vendor text

**Template**:
```python
vendor_prompt = """
You are an intelligent information extraction system. Extract structured
taxonomy details from the following vendor information. Use the exact keys
listed below in the output and fill in the most relevant value from the text.
If a value is not explicitly mentioned, you may infer it if there's enough
context, otherwise mark it as Unknown.

{format_instruction}
Do not return any preamble or explanations, return only a pure JSON string
surrounded by triple backticks (```).

Vendor information:
{vendor}
"""
```

**Input Variables**:
- `vendor`: Vendor information text
- `format_instruction`: JSON schema from VendorTaxonomy model

**Key Instructions**:
- Extract exact keys from schema
- Infer values with context
- Mark as "Unknown" if uncertain
- JSON output only

---

## Configuration Schema

### config.yaml

**Location**: Root directory of application

**Schema**:

```yaml
# Data storage directory
data_path: data

# LLM configuration
llm:
  model: gpt-4o-mini           # Model name
  model_provider: openai       # Provider (openai, anthropic, etc.)
  temperature: 0               # Temperature (0-1, 0 = deterministic)
```

**Field Descriptions**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| data_path | string | Yes | "data" | Directory for uploaded files |
| llm.model | string | Yes | - | LLM model identifier |
| llm.model_provider | string | Yes | - | LLM provider name |
| llm.temperature | float | Yes | 0 | Sampling temperature (0-1) |

**Note**: There is a typo in the original config ("temmperature" instead of "temperature") which should be corrected.

**Environment Variables**:

Required in `.env` file:

```bash
OPENAI_API_KEY=sk-...    # OpenAI API key
```

---

## Usage Examples

### Example 1: Running Legal Case Matcher

```python
from legal_profile import LegalProfile

# Initialize
matcher = LegalProfile()

# Prepare files
precedent_cases = [
    "/data/precedent_case1.pdf",
    "/data/precedent_case2.pdf"
]
current_case = "/data/current_case.txt"

# Match cases
results = matcher.get_match_score_legal(precedent_cases, current_case)

# Process results
for match in results:
    print(f"Precedent: {match['Precedent_Case']}")
    print(f"Score: {match['Confidence_Score']}")
    print(f"Reason: {match['Justification']}\n")
```

### Example 2: Running Vendor Matcher

```python
from procurement import VendorProfile

# Initialize
matcher = VendorProfile()

# Prepare files
vendor_profiles = [
    "/data/vendor_a.pdf",
    "/data/vendor_b.pdf",
    "/data/vendor_c.pdf"
]
requirement = "/data/requirement.txt"

# Match vendors
results = matcher.get_match_score_procurement(vendor_profiles, requirement)

# Sort by confidence
sorted_results = sorted(
    results,
    key=lambda x: x['Confidence_Score'],
    reverse=True
)

# Display top matches
for match in sorted_results[:3]:
    print(f"Vendor: {match['Vendor_Name']}")
    print(f"Score: {match['Confidence_Score']:.2f}")
    print(f"Reason: {match['Justification']}\n")
```

### Example 3: Extracting Vendor Taxonomy

```python
from vendor_mapping import VendorMapping

# Initialize
extractor = VendorMapping()

# Vendor description
vendor_info = """
TechCorp Solutions is a leading cloud infrastructure provider offering
IaaS and PaaS solutions. Operating in North America and Europe with
ISO 27001 and SOC 2 certifications. Specializes in enterprise cloud
migration and managed services.
"""

# Extract taxonomy
taxonomy = extractor.get_vendor_taxonomy(vendor_info)

# Display results
print(f"Vendor: {taxonomy['vendor']}")
print(f"Category: {taxonomy['category']}")
print(f"Services: {taxonomy['service_flag']}")
print(f"Compliance: {taxonomy['compliance']}")
print(f"Regions: {taxonomy['geography']}")
print(f"Risk: {taxonomy['risk_flag']}")
```

### Example 4: Running Full Application

```python
from app import App

# Initialize and run
if __name__ == "__main__":
    app = App()
    app.render_ui()
```

Then access via browser at `http://localhost:8501`

---

## Error Codes and Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Config file not found | config.yaml missing | Create config.yaml in root directory |
| Failed to read txt file | File permissions or encoding | Check file exists and is UTF-8 encoded |
| Failed to read pdf file | Corrupt PDF or permissions | Verify PDF is valid and readable |
| LLM API error | Invalid API key or rate limit | Check OPENAI_API_KEY in .env |
| JSON parsing error | LLM returned invalid JSON | Check prompt format instructions |

### Error Handling Pattern

All methods follow this pattern:

```python
try:
    # Operation
    result = operation()
    return result
except Exception as e:
    # Log error
    self.logger.error(e)

    # User feedback (if UI context)
    st.warning("User-friendly message")

    # Return safe default
    return default_value  # [] or {} or ""
```

---

## Performance Considerations

### API Call Optimization

Each LLM invocation takes 2-5 seconds. For batch processing:

```python
# Processing N vendors takes approximately:
# Time = N * (PDF_extraction + LLM_call + parsing)
# Time ≈ N * (0.1s + 3s + 0.1s) = N * 3.2s

# For 10 vendors: ~32 seconds
# For 50 vendors: ~160 seconds (2.7 minutes)
```

### Recommendations

1. **Rate Limiting**: Add delays between API calls (already implemented: 1s sleep)
2. **Parallel Processing**: Use async for independent vendor evaluations
3. **Caching**: Cache LLM responses based on content hash
4. **Batch API**: Use batch API endpoints if available

---

## Testing

### Unit Test Example

```python
import unittest
from utils import Utils

class TestUtils(unittest.TestCase):

    def setUp(self):
        self.utils = Utils()

    def test_read_txt_file(self):
        # Create test file
        with open("/tmp/test.txt", "w") as f:
            f.write("Test content")

        # Read file
        content = self.utils.read_txt_file("/tmp/test.txt")

        # Assert
        self.assertEqual(content, "Test content")

    def test_read_nonexistent_file(self):
        content = self.utils.read_txt_file("/nonexistent.txt")
        self.assertEqual(content, "")

if __name__ == "__main__":
    unittest.main()
```

### Integration Test Example

```python
def test_legal_matching():
    from legal_profile import LegalProfile

    matcher = LegalProfile()

    # Use test fixtures
    precedents = ["/tests/fixtures/precedent1.pdf"]
    current = "/tests/fixtures/current.txt"

    results = matcher.get_match_score_legal(precedents, current)

    assert len(results) > 0
    assert 'Confidence_Score' in results[0]
    assert 0.1 <= results[0]['Confidence_Score'] <= 1.0
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Initial | Initial prototype implementation |

---

## Support

For issues or questions:
1. Check logs in `./logs/error_logs.json`
2. Verify configuration in `config.yaml`
3. Ensure API keys are set in `.env`
4. Review prompt templates for domain-specific adjustments
