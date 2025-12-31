# Vendor Recommendation System - API Reference

## Table of Contents
1. [Module Overview](#module-overview)
2. [Core Classes](#core-classes)
3. [Configuration](#configuration)
4. [Utility Functions](#utility-functions)
5. [Data Models](#data-models)
6. [Prompt Templates](#prompt-templates)
7. [Error Handling](#error-handling)
8. [Usage Examples](#usage-examples)

## Module Overview

### Module Structure

```
vendor_recommendation/
├── app.py                  # Main application
├── config_reader.py        # Configuration management
├── log_writer.py           # Logging infrastructure
├── utils.py                # Utility functions
├── vendor.py               # Vendor matching logic
├── vendor_prompt.py        # Vendor matching prompt
├── tender_mapping.py       # Tender taxonomy extraction
└── tender_prompt.py        # Tender extraction prompt
```

### Import Hierarchy

```python
# Base modules
from log_writer import CustomLogger
from config_reader import ConfigLoader
from utils import Utils

# Business logic modules
from vendor import VendorProfile, VendorTemplate
from tender_mapping import TenderMapping, TenderTaxonomy

# Application module
from app import App
```

## Core Classes

### CustomLogger

**Module**: `log_writer.py`

**Purpose**: Provides structured logging capabilities with JSON output, rotation, and retention policies.

#### Class Definition

```python
class CustomLogger:
    def __init__(self):
        self.setup_logger()
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `logger` | `loguru.Logger` | Configured logger instance |

#### Methods

##### `setup_logger()`

Configures the logging system with separate handlers for different log levels.

**Signature**:
```python
def setup_logger(self) -> None
```

**Behavior**:
- Creates `./logs` directory if not exists
- Configures INFO logger (`logs/info_logs.json`)
- Configures ERROR logger (`logs/error_logs.json`)
- Sets rotation and retention policies
- Binds logger to "main_logger" name

**Log Configuration**:
```python
# INFO logs
- File: logs/info_logs.json
- Format: JSON
- Rotation: Daily (00:00)
- Retention: 7 days
- Compression: ZIP
- Level: INFO only

# ERROR logs
- File: logs/error_logs.json
- Format: JSON
- Rotation: Daily (00:00)
- Retention: 30 days
- Compression: ZIP
- Level: DEBUG, WARNING, ERROR, CRITICAL
- Backtrace: Enabled
- Diagnose: Enabled
```

**Example**:
```python
logger = CustomLogger()
logger.logger.info("Processing started")
logger.logger.error("Processing failed", exception=e)
```

##### `log_exception(exc_tb)`

Extracts traceback details into a structured format.

**Signature**:
```python
def log_exception(self, exc_tb: traceback) -> List[Dict[str, Any]]
```

**Parameters**:
- `exc_tb` (traceback): Exception traceback object

**Returns**:
- `List[Dict]`: List of traceback frames with file, function, and line information

**Example**:
```python
import sys

try:
    # Some operation
    raise ValueError("Error occurred")
except Exception as e:
    exc_type, exc_value, exc_tb = sys.exc_info()
    traceback_info = logger.log_exception(exc_tb)
    logger.logger.error(f"Exception: {exc_value}", traceback=traceback_info)
```

**Return Format**:
```python
[
    {
        "file": "/path/to/file.py",
        "function": "function_name",
        "line": 42
    },
    # ... more frames
]
```

---

### ConfigLoader

**Module**: `config_reader.py`

**Purpose**: Loads and manages application configuration from YAML file and environment variables.

#### Class Definition

```python
class ConfigLoader(CustomLogger):
    def __init__(self):
        super().__init__()
        load_dotenv()
        self.config_data = self.read_config()
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `config_data` | `Dict[str, Any]` | Parsed configuration dictionary |
| `logger` | `loguru.Logger` | Inherited logger instance |

#### Methods

##### `read_config()`

Reads and parses the `config.yaml` file.

**Signature**:
```python
def read_config(self) -> Dict[str, Any]
```

**Returns**:
- `Dict[str, Any]`: Configuration dictionary

**Raises**:
- `Exception`: If config.yaml not found

**Behavior**:
- Looks for `config.yaml` in current working directory
- Parses YAML content
- Logs critical error and exits if file not found
- Returns configuration dictionary

**Example**:
```python
config_loader = ConfigLoader()
model_name = config_loader.config_data["llm"]["model"]
data_path = config_loader.config_data["data_path"]
```

**Configuration Structure**:
```yaml
data_path: string
llm:
  model: string
  model_provider: string
  temperature: float
```

---

### Utils

**Module**: `utils.py`

**Purpose**: Provides utility functions for file I/O and LLM initialization.

#### Class Definition

```python
class Utils(ConfigLoader):
    def __init__(self):
        super().__init__()
        self.llm = init_chat_model(
            model=self.config_data["llm"]["model"],
            model_provider=self.config_data["llm"]["model_provider"]
        )
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `llm` | `BaseChatModel` | Initialized language model instance |
| `config_data` | `Dict[str, Any]` | Inherited configuration dictionary |
| `logger` | `loguru.Logger` | Inherited logger instance |

#### Methods

##### `read_txt_file(txt_file)`

Reads content from a text file.

**Signature**:
```python
def read_txt_file(self, txt_file: str) -> str
```

**Parameters**:
- `txt_file` (str): Path to text file

**Returns**:
- `str`: File content as string (empty string on error)

**Error Handling**:
- Logs error to logger
- Displays Streamlit warning
- Returns empty string on failure

**Example**:
```python
utils = Utils()
vendor_profile = utils.read_txt_file("data/vendor1.txt")
```

##### `read_pdf_file(pdf_file)`

Extracts text content from a PDF file.

**Signature**:
```python
def read_pdf_file(self, pdf_file: str) -> str
```

**Parameters**:
- `pdf_file` (str): Path to PDF file

**Returns**:
- `str`: Extracted text content (empty string on error)

**Behavior**:
- Opens PDF using PyMuPDF (fitz)
- Extracts text from all pages
- Joins pages with double newlines
- Returns concatenated text

**Error Handling**:
- Logs error to logger
- Displays Streamlit warning
- Returns empty string on failure

**Example**:
```python
utils = Utils()
tender_text = utils.read_pdf_file("data/tender.pdf")
```

---

### VendorProfile

**Module**: `vendor.py`

**Purpose**: Implements vendor-tender matching logic using LLM-based analysis.

#### Class Definition

```python
class VendorProfile(Utils):
    def __init__(self):
        super().__init__()
        self.vendor_parser = JsonOutputParser(pydantic_object=VendorTemplate)
        self.prompt_vendor = PromptTemplate(
            template=vendor_prompt,
            input_variables=["vendor", "tender"],
            partial_variables={
                "format_instruction": self.vendor_parser.get_format_instructions()
            }
        )
        self.procurement_chain = self.prompt_vendor | self.llm
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `vendor_parser` | `JsonOutputParser` | Parser for vendor match output |
| `prompt_vendor` | `PromptTemplate` | Vendor matching prompt template |
| `procurement_chain` | `Chain` | LangChain processing pipeline |
| `llm` | `BaseChatModel` | Inherited language model |

#### Methods

##### `get_match_score_tender(pdf_files, txt_file)`

Analyzes vendor-tender matches for given documents.

**Signature**:
```python
def get_match_score_tender(
    self,
    pdf_files: List[str],
    txt_file: str
) -> List[Dict[str, Any]]
```

**Parameters**:
- `pdf_files` (List[str]): List of paths to tender PDF files
- `txt_file` (str): Path to vendor profile text file

**Returns**:
- `List[Dict[str, Any]]`: List of match results, each containing:
  - `Vendor_Name` (str): Name of the vendor
  - `Tender_Title` (str): Title of the tender
  - `Confidence_Score` (float): Match score (0.1 to 1.0)
  - `Justification` (str): Explanation of the match

**Behavior**:
1. Reads vendor profile from text file
2. For each tender PDF:
   - Extracts text content
   - Invokes LLM chain with vendor and tender
   - Parses structured output
   - Updates progress bar
3. Returns list of all matches

**Error Handling**:
- Logs errors to logger
- Returns empty list on failure
- Catches exceptions during processing

**Example**:
```python
vendor_profile = VendorProfile()

results = vendor_profile.get_match_score_tender(
    pdf_files=["tender1.pdf", "tender2.pdf"],
    txt_file="vendor_profile.txt"
)

for result in results:
    print(f"Tender: {result['Tender_Title']}")
    print(f"Score: {result['Confidence_Score']}")
    print(f"Justification: {result['Justification']}")
```

**Output Format**:
```python
[
    {
        "Vendor_Name": "TechSolutions Ltd",
        "Tender_Title": "Cloud Infrastructure Modernization",
        "Confidence_Score": 0.85,
        "Justification": "Strong alignment due to cloud expertise..."
    },
    # ... more results
]
```

---

### TenderMapping

**Module**: `tender_mapping.py`

**Purpose**: Extracts structured taxonomy information from tender documents.

#### Class Definition

```python
class TenderMapping(Utils):
    def __init__(self):
        super().__init__()
        self.tender_parser = JsonOutputParser(pydantic_object=TenderTaxonomy)
        self.prompt_tender = PromptTemplate(
            template=tender_prompt,
            input_variables=["tender"],
            partial_variables={
                "format_instruction": self.tender_parser.get_format_instructions()
            }
        )
        self.tender_chain = self.prompt_tender | self.llm
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `tender_parser` | `JsonOutputParser` | Parser for taxonomy output |
| `prompt_tender` | `PromptTemplate` | Tender extraction prompt template |
| `tender_chain` | `Chain` | LangChain processing pipeline |

#### Methods

##### `get_tender_taxonomy(txt_content)`

Extracts structured taxonomy from tender text.

**Signature**:
```python
def get_tender_taxonomy(self, txt_content: str) -> Dict[str, str]
```

**Parameters**:
- `txt_content` (str): Tender document text

**Returns**:
- `Dict[str, str]`: Taxonomy dictionary with comma-separated values

**Behavior**:
1. Invokes LLM chain with tender text
2. Parses structured taxonomy output
3. Converts lists to comma-separated strings
4. Returns formatted taxonomy

**Error Handling**:
- Returns empty dictionary on failure
- Catches all exceptions silently

**Example**:
```python
tender_mapping = TenderMapping()

taxonomy = tender_mapping.get_tender_taxonomy(
    txt_content="Healthcare AI tender for NHS..."
)

print(taxonomy)
```

**Output Format**:
```python
{
    "awarding_body": "NHS, UK Department of Health",
    "contract_type": "Fixed-price, Multi-year",
    "product_category": "Healthcare IT, AI Solutions",
    "sector": "Healthcare, Public Sector",
    "solution_type": "AI/ML, Cloud Platform",
    "strategic_needs": "Digital transformation, Patient care improvement",
    "target_region": "United Kingdom, England",
    "tender_qualifiers": "ISO 27001, HIPAA compliance"
}
```

---

### App

**Module**: `app.py`

**Purpose**: Main application class that orchestrates the Streamlit UI and processing logic.

#### Class Definition

```python
class App(VendorProfile, TenderMapping):
    def __init__(self):
        st.set_page_config(page_title="Recommendation System", layout="wide")
        super().__init__()

        if "vendor" not in st.session_state:
            st.session_state["vendor"] = None

        if "taxonomy" not in st.session_state:
            st.session_state["taxonomy"] = None
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `st.session_state["vendor"]` | `List[Dict]` | Stored vendor match results |
| `st.session_state["taxonomy"]` | `Dict` | Stored taxonomy data |

#### Methods

##### `render_ui()`

Renders the Streamlit user interface and handles user interactions.

**Signature**:
```python
def render_ui(self) -> None
```

**Behavior**:
1. Creates page title
2. Renders file upload form:
   - PDF tender document uploader (multiple files)
   - TXT vendor profile uploader (single file)
   - Submit button
3. On submission:
   - Saves uploaded files to data directory
   - Calls `get_match_score_tender()`
   - Stores results in session state
4. Displays results in sortable DataFrame

**UI Components**:
- `st.title()`: Page header
- `st.form()`: File upload form
- `st.file_uploader()`: File upload widgets
- `st.form_submit_button()`: Submit button
- `st.spinner()`: Loading indicator
- `st.dataframe()`: Results display
- `st.warning()`: Error messages

**Example**:
```python
if __name__ == "__main__":
    app = App()
    app.render_ui()
```

## Configuration

### Configuration File Structure

**File**: `config.yaml`

```yaml
# Data directory path
data_path: data

# LLM configuration
llm:
  model: gpt-4o-mini          # Model name
  model_provider: openai       # Provider name
  temperature: 0               # Temperature (0-1)
```

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data_path` | string | `data` | Directory for uploaded files |
| `llm.model` | string | `gpt-4o-mini` | LLM model identifier |
| `llm.model_provider` | string | `openai` | LLM provider name |
| `llm.temperature` | float | `0` | Sampling temperature (0=deterministic) |

### Supported LLM Providers

| Provider | Models | Configuration |
|----------|--------|---------------|
| OpenAI | gpt-4, gpt-4o-mini, gpt-3.5-turbo | `model_provider: openai` |
| Anthropic | claude-3-opus, claude-3-sonnet | `model_provider: anthropic` |
| Azure OpenAI | azure/gpt-4, azure/gpt-35-turbo | `model_provider: azure_openai` |

### Environment Variables

**File**: `.env`

```bash
# Required
OPENAI_API_KEY=sk-proj-...

# Optional (provider-specific)
ANTHROPIC_API_KEY=sk-ant-...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://...
```

## Utility Functions

### File I/O Functions

#### `read_txt_file(txt_file)`

**Module**: `utils.py`

**Purpose**: Read text file with UTF-8 encoding

**Parameters**:
- `txt_file` (str): File path

**Returns**: `str` - File content

**Error Handling**: Returns empty string, logs error, shows warning

#### `read_pdf_file(pdf_file)`

**Module**: `utils.py`

**Purpose**: Extract text from PDF file

**Parameters**:
- `pdf_file` (str): File path

**Returns**: `str` - Extracted text

**Error Handling**: Returns empty string, logs error, shows warning

## Data Models

### VendorTemplate

**Module**: `vendor.py`

**Purpose**: Schema for vendor match results

```python
from pydantic import BaseModel, Field

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

**Field Descriptions**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `Vendor_Name` | str | Required | Vendor's company name |
| `Tender_Title` | str | Required | Tender document title |
| `Confidence_Score` | float | 0.1 ≤ x ≤ 1.0 | Match confidence score |
| `Justification` | str | Required | Detailed explanation |

**Example Instance**:
```python
{
    "Vendor_Name": "TechSolutions Ltd",
    "Tender_Title": "Cloud Migration Project",
    "Confidence_Score": 0.87,
    "Justification": "Strong match based on cloud expertise and certifications..."
}
```

### TenderTaxonomy

**Module**: `tender_mapping.py`

**Purpose**: Schema for tender taxonomy extraction

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class TenderTaxonomy(BaseModel):
    awarding_body: Optional[List[str]] = Field(
        default_factory=list,
        description="List of awarding organizations"
    )
    contract_type: Optional[List[str]] = Field(
        default_factory=list,
        description="List of contract types"
    )
    product_category: Optional[List[str]] = Field(
        default_factory=list,
        description="List of product categories"
    )
    sector: Optional[List[str]] = Field(
        default_factory=list,
        description="List of sectors or industries"
    )
    solution_type: Optional[List[str]] = Field(
        default_factory=list,
        description="List of solution types"
    )
    strategic_needs: Optional[List[str]] = Field(
        default_factory=list,
        description="List of strategic goals"
    )
    target_region: Optional[List[str]] = Field(
        default_factory=list,
        description="List of target regions"
    )
    tender_qualifiers: Optional[List[str]] = Field(
        default_factory=list,
        description="List of eligibility criteria"
    )
```

**Field Descriptions**:

| Field | Type | Optional | Description |
|-------|------|----------|-------------|
| `awarding_body` | List[str] | Yes | Organizations issuing tender |
| `contract_type` | List[str] | Yes | Type of contract (fixed, T&M, etc.) |
| `product_category` | List[str] | Yes | Products/services requested |
| `sector` | List[str] | Yes | Industry sectors |
| `solution_type` | List[str] | Yes | Technology solutions |
| `strategic_needs` | List[str] | Yes | Business objectives |
| `target_region` | List[str] | Yes | Geographic scope |
| `tender_qualifiers` | List[str] | Yes | Requirements for bidders |

**Example Instance**:
```python
{
    "awarding_body": ["NHS", "UK Department of Health"],
    "contract_type": ["Fixed-price", "3-year contract"],
    "product_category": ["Healthcare IT", "Electronic Health Records"],
    "sector": ["Healthcare", "Public Sector"],
    "solution_type": ["Cloud SaaS", "AI/ML Platform"],
    "strategic_needs": ["Digital transformation", "Patient data management"],
    "target_region": ["United Kingdom", "England"],
    "tender_qualifiers": ["ISO 27001", "HIPAA certified"]
}
```

## Prompt Templates

### Vendor Matching Prompt

**Module**: `vendor_prompt.py`

**Variable**: `vendor_prompt`

```python
vendor_prompt = """
You are a vendor evaluation assistant.

Your task is to analyze the relationship between a given **Tender** and
**Vendor Profile**, with a focus on the **core capabilities, features,
and offerings** — not on commercial terms or past performance.

### Inputs:
- **Tender**: A detailed description of a project's needs, expectations,
  and specifications.
- **Vendor Profile**: Information about a vendor's offerings, capabilities,
  technologies, or services.

### Task:
Compare the Tender with the Vendor Profile, focusing primarily on the
**alignment of features, capabilities, and functional relevance**.

- Provide a **confidence score** between **0.1** and **1.0**, indicating
  how well the vendor aligns with the given tender.
- Offer a **justification** explaining the degree of alignment, highlighting
  shared features, matching specifications, or relevant capabilities — not
  based on pricing or contracts.

{format_instruction}
Do not return any preamble or explanations, return only a pure JSON string
surrounded by triple backticks (```).

Tender:
{tender}

Vendor Profile:
{vendor}
"""
```

**Input Variables**:
- `{tender}`: Tender document text
- `{vendor}`: Vendor profile text
- `{format_instruction}`: Auto-generated format instructions from parser

**Output**: JSON string matching VendorTemplate schema

### Tender Taxonomy Prompt

**Module**: `tender_prompt.py`

**Variable**: `tender_prompt`

```python
tender_prompt = """
You are an intelligent information extraction system. Extract structured
taxonomy details from the following tender information. If a value is not
explicitly mentioned, you may infer it if there's enough context, otherwise
mark it as Unknown.

{format_instruction}
Do not return any preamble or explanations, return only a pure JSON string
surrounded by triple backticks (```).

Tender information:
{tender}
"""
```

**Input Variables**:
- `{tender}`: Tender document text
- `{format_instruction}`: Auto-generated format instructions from parser

**Output**: JSON string matching TenderTaxonomy schema

## Error Handling

### Exception Hierarchy

```
Exception (base)
├── FileNotFoundError (config.yaml missing)
├── ValueError (invalid configuration)
├── IOError (file read/write errors)
└── APIError (LLM API failures)
```

### Error Handling Patterns

#### Configuration Errors

```python
try:
    config_data = self.read_config()
except Exception as e:
    self.logger.critical(str(e))
    sys.exit(e)
```

**Behavior**: Log critical error and exit application

#### File I/O Errors

```python
try:
    with open(txt_file, "r", encoding="utf-8") as f:
        txt_content = f.read()
    return txt_content
except Exception as e:
    self.logger.error(e)
    st.warning("Failed to read txt file")
    return ""
```

**Behavior**: Log error, show warning, return empty string

#### Processing Errors

```python
try:
    # Processing logic
    res = self.procurement_chain.invoke({...})
    parsed_res = self.vendor_parser.parse(res.content)
    return parsed_res
except Exception as e:
    self.logger.error(e)
    return []
```

**Behavior**: Log error, return empty result

#### UI-Level Errors

```python
try:
    with st.spinner("Please wait..."):
        # Processing
        st.session_state["vendor"] = self.get_match_score_tender(...)
except Exception:
    st.warning("Server busy...Please try again...")
```

**Behavior**: Show user-friendly warning message

### Error Messages

| Error Type | User Message | Log Level |
|------------|-------------|-----------|
| Config not found | "Config file not found..." | CRITICAL |
| File read error | "Failed to read txt/pdf file" | ERROR |
| Processing error | "Server busy...Please try again..." | ERROR |
| API error | "Server busy...Please try again..." | ERROR |

## Usage Examples

### Basic Usage

```python
# Initialize application
from app import App

app = App()
app.render_ui()
```

### Programmatic Usage

#### Vendor Matching

```python
from vendor import VendorProfile

# Initialize
vendor_profile = VendorProfile()

# Process matches
results = vendor_profile.get_match_score_tender(
    pdf_files=["tender1.pdf", "tender2.pdf"],
    txt_file="vendor_profile.txt"
)

# Analyze results
for result in results:
    if result['Confidence_Score'] >= 0.7:
        print(f"Good match: {result['Tender_Title']}")
        print(f"Score: {result['Confidence_Score']}")
        print(f"Reason: {result['Justification']}\n")
```

#### Tender Taxonomy Extraction

```python
from tender_mapping import TenderMapping

# Initialize
tender_mapping = TenderMapping()

# Extract taxonomy
tender_text = """
Healthcare IT tender from NHS for cloud-based EHR system.
Requirements include HIPAA compliance, ISO 27001 certification.
Target deployment across England. Fixed-price 3-year contract.
"""

taxonomy = tender_mapping.get_tender_taxonomy(tender_text)

# Print taxonomy
for category, values in taxonomy.items():
    print(f"{category}: {values}")
```

#### Custom Configuration

```python
import os
from config_reader import ConfigLoader

# Set custom config path
os.environ['CONFIG_PATH'] = '/path/to/custom/config.yaml'

# Load config
config = ConfigLoader()

# Access config
print(config.config_data['llm']['model'])
```

#### Custom Logging

```python
from log_writer import CustomLogger

logger = CustomLogger()

# Log different levels
logger.logger.info("Processing started")
logger.logger.warning("High confidence score threshold")
logger.logger.error("Failed to process tender", file="tender1.pdf")

# Log with context
logger.logger.info(
    "Match found",
    vendor="TechSolutions",
    tender="Cloud Migration",
    score=0.85
)
```

### Advanced Usage

#### Batch Processing Script

```python
import glob
from vendor import VendorProfile

def batch_process_vendors():
    vendor_profile = VendorProfile()

    # Get all vendor profiles
    vendor_files = glob.glob("data/vendors/*.txt")

    # Get all tenders
    tender_files = glob.glob("data/tenders/*.pdf")

    all_results = []

    for vendor_file in vendor_files:
        results = vendor_profile.get_match_score_tender(
            pdf_files=tender_files,
            txt_file=vendor_file
        )
        all_results.extend(results)

    # Sort by score
    all_results.sort(
        key=lambda x: x['Confidence_Score'],
        reverse=True
    )

    return all_results

# Run batch processing
if __name__ == "__main__":
    results = batch_process_vendors()

    # Export to CSV
    import pandas as pd
    df = pd.DataFrame(results)
    df.to_csv("match_results.csv", index=False)
```

#### Custom LLM Integration

```python
from utils import Utils
from langchain.chat_models import init_chat_model

class CustomUtils(Utils):
    def __init__(self, custom_model="gpt-4"):
        # Override parent init
        super().__init__()

        # Use custom model
        self.llm = init_chat_model(
            model=custom_model,
            model_provider="openai",
            temperature=0.2  # Custom temperature
        )
```

#### Error Recovery

```python
from vendor import VendorProfile
import time

def robust_matching(pdf_files, txt_file, max_retries=3):
    vendor_profile = VendorProfile()

    for attempt in range(max_retries):
        try:
            results = vendor_profile.get_match_score_tender(
                pdf_files=pdf_files,
                txt_file=txt_file
            )

            if results:
                return results
            else:
                print(f"Attempt {attempt + 1} returned no results")

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")

            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

    return []

# Usage
results = robust_matching(
    pdf_files=["tender.pdf"],
    txt_file="vendor.txt"
)
```

## Integration Patterns

### Flask API Wrapper

```python
from flask import Flask, request, jsonify
from vendor import VendorProfile
import tempfile

app = Flask(__name__)
vendor_profile = VendorProfile()

@app.route('/match', methods=['POST'])
def match_vendor():
    # Get files from request
    tender_files = request.files.getlist('tenders')
    vendor_file = request.files['vendor']

    # Save temporarily
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save vendor profile
        vendor_path = f"{tmpdir}/vendor.txt"
        vendor_file.save(vendor_path)

        # Save tender files
        tender_paths = []
        for i, tender in enumerate(tender_files):
            path = f"{tmpdir}/tender_{i}.pdf"
            tender.save(path)
            tender_paths.append(path)

        # Process
        results = vendor_profile.get_match_score_tender(
            pdf_files=tender_paths,
            txt_file=vendor_path
        )

    return jsonify(results)

if __name__ == '__main__':
    app.run(port=5000)
```

### Async Processing

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from vendor import VendorProfile

async def async_process_tender(vendor_profile, pdf_file, txt_file):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(
            executor,
            vendor_profile.get_match_score_tender,
            [pdf_file],
            txt_file
        )
    return result

async def process_multiple_vendors(tender_files, vendor_files):
    vendor_profile = VendorProfile()

    tasks = []
    for tender in tender_files:
        for vendor in vendor_files:
            task = async_process_tender(
                vendor_profile,
                tender,
                vendor
            )
            tasks.append(task)

    results = await asyncio.gather(*tasks)
    return results

# Usage
if __name__ == "__main__":
    results = asyncio.run(
        process_multiple_vendors(
            tender_files=["t1.pdf", "t2.pdf"],
            vendor_files=["v1.txt", "v2.txt"]
        )
    )
```

## Performance Optimization

### Caching LLM Responses

```python
from functools import lru_cache
import hashlib

class CachedVendorProfile(VendorProfile):
    @lru_cache(maxsize=100)
    def cached_match(self, tender_hash, vendor_hash):
        # This would be called with hashed inputs
        pass

    def get_match_score_tender(self, pdf_files, txt_file):
        # Read files
        txt_content = self.read_txt_file(txt_file)

        results = []
        for pdf_file in pdf_files:
            pdf_content = self.read_pdf_file(pdf_file)

            # Create hashes for caching
            tender_hash = hashlib.md5(
                pdf_content.encode()
            ).hexdigest()
            vendor_hash = hashlib.md5(
                txt_content.encode()
            ).hexdigest()

            # Check cache or process
            # Implementation details...

        return results
```

---

This API reference provides comprehensive documentation for all classes, methods, and functions in the Vendor Recommendation System. For implementation examples and best practices, refer to the User Guide and Technical Architecture documentation.
