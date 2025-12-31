# Planning Document Classifier - API Reference

## Overview

This document provides comprehensive API documentation for all modules, functions, and classes in the Planning Document Classifier application. Each function includes detailed parameter descriptions, return values, exceptions, and usage examples.

---

## Table of Contents

1. [PDF Processor Module](#pdf-processor-module)
2. [Classifier Module](#classifier-module)
3. [Application Module](#application-module)
4. [Data Structures](#data-structures)
5. [Constants and Configuration](#constants-and-configuration)

---

## PDF Processor Module

**Module**: `pdf_processor.py`

**Purpose**: Handles all PDF document processing operations including text extraction, cleaning, and truncation.

**Dependencies**:
- `fitz` (PyMuPDF) - PDF processing
- `streamlit` - UI feedback
- `io.BytesIO` - Byte stream handling
- `re` - Regular expressions

### Functions

#### extract_text_from_pdf()

Extracts text content from an uploaded PDF file using PyMuPDF.

**Signature**:
```python
def extract_text_from_pdf(uploaded_file) -> str
```

**Parameters**:
- `uploaded_file` (UploadedFile): Streamlit uploaded file object
  - Type: `streamlit.runtime.uploaded_file_manager.UploadedFile`
  - Must be a PDF file
  - Contains file data and metadata

**Returns**:
- `str`: Extracted and cleaned text from the PDF
  - Empty string if no text could be extracted
  - Cleaned of excessive whitespace and normalized

**Raises**:
- `Exception`: If PDF processing fails
  - Message format: "Failed to extract text from PDF: {error_details}"
  - Common causes:
    - Corrupted PDF file
    - Unsupported PDF format
    - Permission-restricted PDF
    - Memory allocation failure

**Side Effects**:
- Creates and updates a Streamlit progress bar
- Displays status text during processing
- Shows warnings for page-level extraction errors
- Cleans up UI elements after completion

**Processing Steps**:
1. Reads uploaded file to bytes
2. Opens PDF with PyMuPDF in stream mode
3. Iterates through all pages
4. Extracts text from each page
5. Updates progress indicators
6. Handles page-level errors gracefully
7. Cleans extracted text
8. Returns complete text

**Example Usage**:
```python
import streamlit as st
from pdf_processor import extract_text_from_pdf

uploaded_file = st.file_uploader("Upload PDF", type=['pdf'])
if uploaded_file:
    try:
        text = extract_text_from_pdf(uploaded_file)
        print(f"Extracted {len(text)} characters")
    except Exception as e:
        print(f"Error: {e}")
```

**Performance**:
- Time complexity: O(n) where n = number of pages
- Space complexity: O(m) where m = total text length
- Average processing time: 1-2 seconds per page

**Notes**:
- Progress bar automatically updates during processing
- Individual page errors do not stop overall extraction
- Returns empty string if no text can be extracted
- Automatically closes PDF document after processing

---

#### clean_text()

Cleans and preprocesses extracted text by removing excessive whitespace and normalizing formatting.

**Signature**:
```python
def clean_text(text: str) -> str
```

**Parameters**:
- `text` (str): Raw extracted text from PDF
  - Can contain multiple spaces, tabs, newlines
  - May have inconsistent formatting
  - Can be empty string

**Returns**:
- `str`: Cleaned and normalized text
  - Single spaces between words
  - Single newlines between paragraphs
  - No leading/trailing whitespace
  - Empty string if input is empty

**Raises**:
- None (gracefully handles all inputs)

**Processing Operations**:
1. Collapses multiple spaces to single space
2. Converts multiple newlines to single newline
3. Strips leading and trailing whitespace

**Regular Expressions Used**:
```python
r'\s+' → ' '      # Collapse all whitespace to single space
r'\n+' → '\n'     # Normalize multiple newlines
```

**Example Usage**:
```python
from pdf_processor import clean_text

raw_text = "This  is    some\n\n\n\ntext   with    issues"
cleaned = clean_text(raw_text)
# Result: "This is some\ntext with issues"
```

**Performance**:
- Time complexity: O(n) where n = text length
- Space complexity: O(n) for output string
- Very fast regex operations

**Notes**:
- Safe for empty or None inputs (returns empty string)
- Preserves single newlines for paragraph structure
- Does not modify actual word content
- Idempotent (running twice gives same result)

---

#### truncate_text_for_llm()

Truncates text to fit within LLM token limits using smart sentence-boundary detection.

**Signature**:
```python
def truncate_text_for_llm(text: str, max_chars: int = 50000) -> str
```

**Parameters**:
- `text` (str): Input text to potentially truncate
  - Can be any length
  - Should be cleaned text (recommended)

- `max_chars` (int, optional): Maximum character count
  - Default: 50,000 characters
  - Roughly equivalent to ~12,500 tokens
  - Should be set based on model limits

**Returns**:
- `str`: Truncated text with indicator if truncated
  - Original text if under limit
  - Smartly truncated text if over limit
  - Includes "[TEXT TRUNCATED DUE TO LENGTH]" marker if truncated

**Raises**:
- None

**Algorithm**:
```python
if len(text) <= max_chars:
    return text  # No truncation needed

# Initial truncation
truncated = text[:max_chars]

# Smart boundary detection
last_period = truncated.rfind('.')
if last_period > max_chars * 0.8:
    # Truncate at sentence boundary if period found in last 20%
    truncated = truncated[:last_period + 1]

return truncated + "\n\n[TEXT TRUNCATED DUE TO LENGTH]"
```

**Example Usage**:
```python
from pdf_processor import truncate_text_for_llm

# Long document
long_text = "..." * 100000  # Very long text

# Truncate for API
truncated = truncate_text_for_llm(long_text, max_chars=45000)

# Check if truncated
if "[TEXT TRUNCATED" in truncated:
    print("Document was truncated")
```

**Performance**:
- Time complexity: O(1) if under limit, O(n) if over
- Space complexity: O(n) for truncated output
- Very fast string operations

**Smart Truncation Logic**:
- Searches for last period (.) in final 20% of allowed text
- If found, truncates at sentence end
- If not found, uses hard truncation at character limit
- Preserves context better than hard truncation

**Notes**:
- Configurable max_chars for different model limits
- Adds clear indicator when truncation occurs
- Preserves complete sentences when possible
- Used before sending to LLM for classification

---

## Classifier Module

**Module**: `classifier.py`

**Purpose**: Handles document classification using OpenAI's GPT-4o model, including prompt engineering, API communication, and result validation.

**Dependencies**:
- `openai` - OpenAI API client
- `json` - JSON parsing
- `os` - Environment variables
- `dotenv` - Environment management
- `pdf_processor` - Text truncation

**Module-Level Variables**:
```python
OPENAI_API_KEY: str          # API key from environment
openai_client: OpenAI        # Initialized OpenAI client
```

### Functions

#### classify_document()

Main classification function that analyzes document text and returns structured classification results.

**Signature**:
```python
def classify_document(extracted_text: str) -> dict
```

**Parameters**:
- `extracted_text` (str): Text extracted from PDF document
  - Should be cleaned text
  - Can be any length (will be truncated internally)
  - Should contain planning document content

**Returns**:
- `dict`: Classification results with structure:
  ```python
  {
      "class": str,           # Main category (e.g., "Residential")
      "sub_class": str,       # Sub-category (e.g., "Single-Family Homes")
      "justification": str    # Detailed explanation
  }
  ```

**Raises**:
- `Exception`: For JSON parsing failures
  - Message: "Failed to parse classification response: {error}"

- `Exception`: For API or processing failures
  - Message: "Classification failed: {error}"

**API Configuration**:
```python
model = "gpt-4o"
response_format = {"type": "json_object"}
max_tokens = 1000
temperature = 0.3
```

**Processing Flow**:
1. Truncate text to 45,000 characters
2. Create classification prompt
3. Call OpenAI API with system and user messages
4. Parse JSON response
5. Validate required fields
6. Return structured result

**Example Usage**:
```python
from classifier import classify_document

document_text = "Planning application for residential development..."

try:
    result = classify_document(document_text)
    print(f"Class: {result['class']}")
    print(f"Sub-class: {result['sub_class']}")
    print(f"Justification: {result['justification']}")
except Exception as e:
    print(f"Classification error: {e}")
```

**API Response Example**:
```json
{
    "class": "Residential",
    "sub_class": "Multi-Family Housing",
    "justification": "The document describes a planning application for a 24-unit apartment building with ground-floor commercial space. References to 'affordable housing units' and 'mixed-use development' indicate multi-family residential with commercial components."
}
```

**Performance**:
- API latency: 10-20 seconds typical
- Token usage: ~500-1000 tokens per request
- Cost: ~$0.005-$0.015 per classification (GPT-4o pricing)

**Error Handling**:
- Missing fields automatically set to "Not provided"
- JSON parse errors caught and reported
- Network errors propagated with context
- All exceptions include descriptive messages

**Notes**:
- Uses GPT-4o (latest model as of May 2024)
- Temperature 0.3 for consistent results
- Forces JSON output format
- Automatically validates response structure

---

#### create_classification_prompt()

Generates the structured prompt for document classification including taxonomy and instructions.

**Signature**:
```python
def create_classification_prompt(extracted_text: str) -> str
```

**Parameters**:
- `extracted_text` (str): Cleaned and truncated document text
  - Should be preprocessed
  - Will be embedded in prompt

**Returns**:
- `str`: Complete formatted prompt ready for API
  - Includes role definition
  - Contains full taxonomy
  - Specifies response format
  - Embeds document text

**Raises**:
- None

**Prompt Structure**:
```
1. Role Assignment
   "You are an urban planning classification assistant..."

2. Classification Taxonomy
   RESIDENTIAL:
   - Single-Family Homes: [description]
   - Multi-Family Housing: [description]
   ...

   COMMERCIAL:
   - Office Buildings: [description]
   ...

   [All 5 main categories with 27 sub-classes]

3. Instructions
   "Analyze the document content carefully..."

4. Response Format
   JSON schema with required fields

5. Document Text
   ===
   {extracted_text}
   ===

6. Final Instruction
   "Respond only with valid JSON."
```

**Example Usage**:
```python
from classifier import create_classification_prompt

text = "Planning application text..."
prompt = create_classification_prompt(text)

# Use in API call
response = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "System prompt..."},
        {"role": "user", "content": prompt}
    ]
)
```

**Prompt Engineering Techniques**:
- **Clear Role**: Defines AI as expert classifier
- **Detailed Taxonomy**: Provides comprehensive categories
- **Examples**: Shows expected output format
- **Delimiters**: Uses === to separate text
- **Explicit Format**: Requires JSON response
- **Structured Schema**: Shows exact JSON structure

**Taxonomy Details**:
- 5 main categories
- 27 detailed sub-classes
- Clear descriptions for each
- Examples and use cases

**Performance**:
- String concatenation: O(n)
- Negligible processing time
- Large prompt (~2000 tokens)

**Notes**:
- Prompt is critical for classification accuracy
- Taxonomy version 2.0 (updated July 2025)
- Static taxonomy (no runtime customization)
- Designed for UK planning context

---

#### validate_classification_result()

Validates the structure and content of classification results.

**Signature**:
```python
def validate_classification_result(result: dict) -> bool
```

**Parameters**:
- `result` (dict): Classification result to validate
  - Should contain class, sub_class, justification
  - Can be any dictionary structure

**Returns**:
- `bool`: Validation result
  - `True` if structure is valid
  - `False` if validation fails

**Raises**:
- None (returns False on validation failure)

**Validation Checks**:

1. **Type Check**:
   ```python
   if not isinstance(result, dict):
       return False
   ```

2. **Required Fields**:
   ```python
   required_fields = ["class", "sub_class", "justification"]
   for field in required_fields:
       if field not in result or not isinstance(result[field], str):
           return False
   ```

3. **Class Validation**:
   ```python
   allowed_classes = [
       "Residential",
       "Commercial",
       "Institutional",
       "Infrastructure",
       "Recreational"
   ]
   if result["class"] not in allowed_classes:
       return False
   ```

4. **Sub-Class Validation** (Flexible):
   ```python
   # Allows partial matches
   valid_sub = any(
       allowed_sub in sub_class or sub_class in allowed_sub
       for allowed_sub in allowed_subclasses[main_class]
   )
   ```

**Example Usage**:
```python
from classifier import validate_classification_result

result = {
    "class": "Residential",
    "sub_class": "Multi-Family Housing",
    "justification": "Document describes apartments..."
}

if validate_classification_result(result):
    print("Valid classification")
else:
    print("Invalid structure")
```

**Validation Logic**:
- Strict on required fields (must be present)
- Strict on field types (must be strings)
- Strict on main class (must match exactly)
- Flexible on sub-class (allows partial matching)

**Allowed Classes and Sub-Classes**:

```python
allowed_subclasses = {
    "Residential": [
        "Single-Family Homes",
        "Multi-Family Housing",
        "Affordable Housing",
        "Senior or Assisted Living",
        "Student Housing",
        "Mixed Use"
    ],
    "Commercial": [
        "Office Buildings",
        "Retail (High Street or Standalone)",
        "Supermarket/Foodstore",
        "Shopping Centre/Retail Park",
        "Hospitality (Hotels, Hostels)",
        "Restaurants/Cafes/Drive-thru",
        "Warehousing/Distribution",
        "Mixed Use (Retail/Office)"
    ],
    "Institutional": [
        "Healthcare",
        "Education",
        "Government/Civic Buildings",
        "Community Facilities",
        "Religious Institutions"
    ],
    "Infrastructure": [
        "Industrial",
        "Energy",
        "Transportation",
        "Parking Structures",
        "Logistics Hubs/Depots",
        "Data Centres/Telecom Infrastructure"
    ],
    "Recreational": [
        "Parks/Green Spaces",
        "Sports Facilities/Arenas",
        "Event Venues/Outdoor Structures",
        "Temporary Structures/Permitted Events"
    ]
}
```

**Notes**:
- Currently not used in main flow (defensive coding)
- Could be integrated for additional validation
- Flexible sub-class matching accommodates AI variation
- Logs mismatches but doesn't fail (lenient approach)

---

## Application Module

**Module**: `app.py`

**Purpose**: Main Streamlit application providing user interface and workflow orchestration.

**Dependencies**:
- `streamlit` - Web framework
- `os` - Environment access
- `pdf_processor` - Text extraction
- `classifier` - Document classification

### Functions

#### main()

Main application entry point that sets up UI and handles user interactions.

**Signature**:
```python
def main() -> None
```

**Parameters**:
- None

**Returns**:
- None

**Raises**:
- None (all exceptions caught and displayed to user)

**Application Flow**:

1. **Page Configuration**:
   ```python
   st.set_page_config(
       page_title="Document Classifier",
       page_icon="📋",
       layout="wide"
   )
   ```

2. **API Key Validation**:
   ```python
   if not os.getenv("OPENAI_API_KEY"):
       st.error("⚠️ OpenAI API key not found")
       st.stop()
   ```

3. **UI Layout**:
   - Display title and instructions
   - Create two-column layout (20% / 80%)
   - Left column: Upload and process button
   - Right column: Results display

4. **File Processing**:
   ```python
   if uploaded_file and process_button:
       # Extract text
       extracted_text = extract_text_from_pdf(uploaded_file)

       # Classify
       result = classify_document(extracted_text)

       # Display results
   ```

5. **Error Handling**:
   ```python
   try:
       # Processing logic
   except Exception as e:
       st.error(f"❌ An error occurred: {str(e)}")
   ```

**Example Execution**:
```bash
# Run application
streamlit run app.py --server.port 5000

# Application starts
# User uploads PDF
# Clicks "Classify Document"
# Views results
```

**UI Components**:

1. **Header Section**:
   - Title: "📋 Document Classifier"
   - Description
   - Instructions
   - Classification types reference

2. **Upload Panel** (Left Column):
   - File uploader widget
   - Process button (conditional)

3. **Results Panel** (Right Column):
   - Classification class display
   - Sub-class display
   - Justification text
   - Status messages

**State Management**:
- Stateless design
- Button click triggers processing
- Results displayed immediately
- No session persistence

**Error Messages**:
- "⚠️ OpenAI API key not found" - Configuration error
- "❌ No text could be extracted" - Empty PDF
- "❌ An error occurred: {details}" - Processing error

**Notes**:
- Entry point: `if __name__ == "__main__":`
- Single-page application
- No authentication required
- Suitable for internal tools

---

## Data Structures

### ClassificationResult

**Type**: Dictionary

**Structure**:
```python
{
    "class": str,           # Main classification category
    "sub_class": str,       # Detailed sub-category
    "justification": str    # Explanation with evidence
}
```

**Field Descriptions**:

#### class
- **Type**: `str`
- **Required**: Yes
- **Allowed Values**:
  - "Residential"
  - "Commercial"
  - "Institutional"
  - "Infrastructure"
  - "Recreational"
- **Example**: "Commercial"

#### sub_class
- **Type**: `str`
- **Required**: Yes
- **Allowed Values**: See validation function for complete list
- **Example**: "Office Buildings"

#### justification
- **Type**: `str`
- **Required**: Yes
- **Format**: Free text explanation
- **Length**: Typically 100-500 characters
- **Example**: "The document describes a planning application for a 5-story office building with 10,000 sq ft of workspace. References to 'commercial lease' and 'business park' confirm office use."

**Example Complete Result**:
```python
{
    "class": "Infrastructure",
    "sub_class": "Data Centres/Telecom Infrastructure",
    "justification": "The planning statement details a 50,000 sq ft data center facility with backup power systems, cooling infrastructure, and telecommunications equipment. The document explicitly mentions 'server hosting' and 'colocation services', confirming this is a data center development."
}
```

---

## Constants and Configuration

### Environment Variables

#### OPENAI_API_KEY
- **Type**: `str`
- **Required**: Yes
- **Format**: `sk-...` (OpenAI API key format)
- **Usage**: Authentication for OpenAI API
- **Validation**: Checked on application startup
- **Example**: `OPENAI_API_KEY=sk-proj-abc123...`

**Configuration**:
```bash
# .env file
OPENAI_API_KEY=sk-your-key-here

# Or export
export OPENAI_API_KEY=sk-your-key-here
```

### Application Constants

#### MAX_CHARS_FOR_LLM
- **Value**: 45,000
- **Type**: `int`
- **Purpose**: Character limit for text sent to LLM
- **Rationale**: ~11,250 tokens (well under GPT-4o limit)
- **Location**: `classifier.py`, `truncate_text_for_llm()` call

#### API_MODEL
- **Value**: `"gpt-4o"`
- **Type**: `str`
- **Purpose**: OpenAI model identifier
- **Note**: Latest model as of May 2024
- **Location**: `classifier.py`, `classify_document()`

#### API_TEMPERATURE
- **Value**: `0.3`
- **Type**: `float`
- **Purpose**: Control response randomness
- **Range**: 0.0 (deterministic) to 2.0 (creative)
- **Rationale**: Low value for consistent classifications
- **Location**: `classifier.py`, `classify_document()`

#### API_MAX_TOKENS
- **Value**: `1000`
- **Type**: `int`
- **Purpose**: Limit response length
- **Rationale**: Sufficient for classification + justification
- **Location**: `classifier.py`, `classify_document()`

### Streamlit Configuration

**File**: `.streamlit/config.toml`

```toml
[server]
headless = true        # Run without browser UI
address = "0.0.0.0"    # Listen on all interfaces
port = 8523            # Default port
```

### Deployment Configuration

**File**: `.replit`

```toml
[deployment]
deploymentTarget = "autoscale"
run = ["streamlit", "run", "app.py", "--server.port", "5000"]
```

---

## Usage Examples

### Complete Workflow Example

```python
import os
from pdf_processor import extract_text_from_pdf, truncate_text_for_llm
from classifier import classify_document

# Set API key
os.environ["OPENAI_API_KEY"] = "sk-your-key"

# Simulate file upload (in real app, this comes from Streamlit)
with open("planning_doc.pdf", "rb") as f:
    pdf_bytes = f.read()

# Create mock uploaded file object
class MockUploadedFile:
    def __init__(self, data):
        self.data = data
    def read(self):
        return self.data

uploaded_file = MockUploadedFile(pdf_bytes)

# Extract text
try:
    text = extract_text_from_pdf(uploaded_file)
    print(f"Extracted {len(text)} characters")

    # Classify
    if text.strip():
        result = classify_document(text)

        # Display results
        print(f"\nClassification Results:")
        print(f"Class: {result['class']}")
        print(f"Sub-class: {result['sub_class']}")
        print(f"Justification: {result['justification']}")
    else:
        print("No text extracted from PDF")

except Exception as e:
    print(f"Error: {e}")
```

### Text Processing Example

```python
from pdf_processor import clean_text, truncate_text_for_llm

# Raw text with issues
raw = """This    is   some


planning   text    with

excessive    whitespace."""

# Clean it
cleaned = clean_text(raw)
print(cleaned)
# Output: "This is some\nplanning text with\nexcessive whitespace."

# Truncate for LLM
truncated = truncate_text_for_llm(cleaned, max_chars=50)
print(truncated)
# Output: "This is some\nplanning text with\nexcessive whi...[TEXT TRUNCATED DUE TO LENGTH]"
```

### Direct API Call Example

```python
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "system",
            "content": "You are an expert urban planning classifier."
        },
        {
            "role": "user",
            "content": "Classify this: [document text]"
        }
    ],
    response_format={"type": "json_object"},
    max_tokens=1000,
    temperature=0.3
)

result = response.choices[0].message.content
print(result)
```

---

## Error Reference

### Common Exceptions

#### PDF Processing Errors

**Exception**: `Exception("Failed to extract text from PDF: ...")`
- **Cause**: PDF file corrupted or unsupported format
- **Solution**: Try different PDF or convert to standard format

**Exception**: `Exception("No text could be extracted")`
- **Cause**: Scanned PDF without OCR layer
- **Solution**: Run OCR on PDF before upload

#### Classification Errors

**Exception**: `Exception("Failed to parse classification response: ...")`
- **Cause**: API returned invalid JSON
- **Solution**: Retry classification, check API status

**Exception**: `Exception("Classification failed: ...")`
- **Cause**: API error, network issue, or rate limiting
- **Solution**: Check API key, network connection, usage limits

#### Configuration Errors

**Error**: "OpenAI API key not found"
- **Cause**: OPENAI_API_KEY environment variable not set
- **Solution**: Set environment variable with valid API key

---

## Version History

### API Version 1.0
- Initial release
- Basic classification functionality
- 5 main categories, 27 sub-classes

### Taxonomy Version 2.0 (July 2025)
- Updated classification taxonomy
- Added detailed sub-class descriptions
- Improved prompt engineering

---

**Document Version**: 1.0
**Last Updated**: December 2025
**API Stability**: Prototype (subject to change)
