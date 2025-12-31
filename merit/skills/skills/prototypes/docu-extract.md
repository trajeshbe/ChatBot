# Document Intelligence Extraction (docu_extract)

You are an AI assistant specialized in the **Document Intelligence Extraction System**, an AI-powered tool for extracting structured data from planning documents, architectural diagrams, and construction-related files.

## Project Overview

The Document Intelligence Extraction System automates extraction of 18 structured data fields from planning documents and architectural drawings using OpenAI's GPT-4o Vision model. It supports PDF, DOCX, PNG, and JPEG formats with dual implementations (React/TypeScript and Python/Streamlit).

**Location**: `/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/docu_extract/`

## Core Capabilities

### 18 Extracted Data Fields

**Project Metadata** (11 fields):
1. Project Name
2. Address
3. Project Status
4. Storeys
5. Gross Floor Area (GFA)
6. Site Area
7. Zoning
8. Heritage Designation
9. Architect
10. Developer
11. Planning Consultant

**Building Information** (7 fields):
12. Residential Units
13. Unit Types
14. Commercial Uses
15. Amenities
16. Parking Levels
17. Parking Spaces
18. Public Realm Features

### Key Features

- Multi-format support (PDF, DOCX, PNG, JPEG)
- AI-powered extraction (GPT-4o vision and text models)
- Smart page selection for large documents
- Data export (CSV and JSON formats)
- High accuracy (85-95% field extraction)
- Processing time: 30-120 seconds per document

## Technology Stack

**Streamlit Version**:
```
Language: Python 3.11+
Framework: Streamlit 1.47+
AI: OpenAI GPT-4o
Document Processing: PyMuPDF, python-docx, Pillow
```

**React Version**:
```
Frontend: React 18.3 + TypeScript
Backend: Express.js 4.21, Node.js
Database: PostgreSQL with Drizzle ORM
Build: Vite, esbuild
```

## Architecture

### Component Structure

```
streamlit_app.py           # Python/Streamlit version
server/                    # Express.js backend
  ├── index.ts            # Main server
  ├── routes.ts           # API routes
  └── ai.ts               # AI processing
client/                    # React frontend
  ├── src/
  │   ├── App.tsx        # Main component
  │   ├── components/    # UI components
  │   └── lib/           # Utilities
  └── public/
shared/
  └── schema.ts          # Data schemas
```

### Processing Pipeline

```
Document Upload (PDF/DOCX/Image)
  ↓
Format Detection & Validation
  ↓
Document Parsing (Text/Image extraction)
  ↓
AI Analysis (GPT-4o Vision/Text)
  ↓
Structured Data Extraction (18 fields)
  ↓
Validation & Post-processing
  ↓
Export (CSV/JSON)
```

## Common Implementation Tasks

### 1. Running the Streamlit Version

```bash
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/docu_extract/

# Install dependencies
pip install streamlit openai pandas pillow pymupdf python-docx

# Set API key
export OPENAI_API_KEY="your-api-key"

# Run application
streamlit run streamlit_app.py
```

### 2. Running the React/Express Version

```bash
# Install dependencies
npm install

# Set environment variables
echo "OPENAI_API_KEY=your-key" > .env

# Run development server
npm run dev

# Build for production
npm run build
```

### 3. Extracting Data from a Document

```python
from document_extractor import DocumentExtractor

# Initialize extractor
extractor = DocumentExtractor()

# Process PDF
with open('planning_document.pdf', 'rb') as f:
    result = extractor.extract_data(f.read(), 'pdf')

# Result structure:
{
    'project_name': 'Downtown Residential Tower',
    'address': '123 Main Street',
    'storeys': 45,
    'gfa': 50000,
    'residential_units': 450,
    'parking_spaces': 350,
    ...
}

# Export to CSV
extractor.export_csv(result, 'output.csv')

# Export to JSON
extractor.export_json(result, 'output.json')
```

### 4. Customizing Extraction Fields

```python
# Add new field to extraction schema
new_field = {
    'name': 'Construction Cost',
    'type': 'currency',
    'required': False,
    'extraction_hint': 'Total estimated construction cost in dollars'
}

# Update AI prompt
prompt = f"""
Extract the following information from the document:
...
- Construction Cost: {new_field['extraction_hint']}
"""

# Update schema validation
from pydantic import BaseModel

class ProjectData(BaseModel):
    project_name: Optional[str]
    construction_cost: Optional[float]
    # ... other fields
```

### 5. Handling Large Documents

```python
def smart_page_selection(pdf_path, max_pages=10):
    """Select most relevant pages from large PDF"""
    import fitz  # PyMuPDF

    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    if total_pages <= max_pages:
        return list(range(total_pages))

    # Select key pages
    selected = [
        0,  # Cover page
        1,  # Table of contents
        total_pages // 2,  # Middle
        total_pages - 1  # Last page
    ]

    # Add pages with keywords
    keywords = ['site plan', 'floor plan', 'elevation', 'summary']
    for i, page in enumerate(doc):
        text = page.get_text().lower()
        if any(kw in text for kw in keywords):
            selected.append(i)

        if len(selected) >= max_pages:
            break

    return sorted(set(selected))[:max_pages]
```

## Data Extraction Strategies

### Text-Based Documents (PDF, DOCX)

```python
def extract_from_text(text_content):
    """Extract data from text-based documents"""
    prompt = """
    Analyze the following planning document and extract:

    1. Project identification (name, address, status)
    2. Building metrics (storeys, GFA, site area)
    3. Zoning and heritage information
    4. Project team (architect, developer, consultant)
    5. Unit details (residential units, types)
    6. Commercial and amenity information
    7. Parking details (levels, spaces)
    8. Public realm features

    Document text:
    {text}

    Return as JSON with exact field names.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt.format(text=text_content)}]
    )

    return json.loads(response.choices[0].message.content)
```

### Image-Based Documents (Scans, Drawings)

```python
def extract_from_image(image_data):
    """Extract data from architectural drawings"""
    import base64

    # Encode image
    image_base64 = base64.b64encode(image_data).decode()

    prompt = """
    Analyze this architectural drawing/site plan and extract:

    - Project name and location
    - Building dimensions and storeys
    - Unit layout and counts
    - Parking configuration
    - Site features and amenities

    Focus on text labels, dimension annotations, and plan views.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}"
                }}
            ]
        }]
    )

    return parse_extraction_result(response.choices[0].message.content)
```

## Best Practices

### Document Preparation

1. **Quality**: Use high-resolution scans (300+ DPI)
2. **Completeness**: Include all relevant pages
3. **Orientation**: Ensure correct page orientation
4. **OCR**: Pre-process scanned documents with OCR if needed
5. **Format**: Prefer searchable PDF over image-only PDF

### Data Validation

1. **Required Fields**: Verify critical fields are extracted
2. **Data Types**: Validate numeric fields (storeys, GFA, units)
3. **Ranges**: Check values are within reasonable ranges
4. **Consistency**: Cross-check related fields (units vs. GFA)
5. **Manual Review**: Always review AI extractions

### Performance Optimization

1. **Page Selection**: Process only relevant pages
2. **Image Compression**: Reduce image size for API calls
3. **Caching**: Cache results for repeated documents
4. **Batch Processing**: Process multiple documents sequentially
5. **Async Processing**: Use asynchronous API calls

## Common Issues and Solutions

**Issue**: Low extraction accuracy
```python
# Improve prompt specificity
prompt = """
Extract the EXACT text for each field.
- Project Name: Look for "Project:", "Development:", or building name
- Address: Complete street address including city
- Storeys: Number of floors (e.g., "45 storeys" → 45)
"""

# Add examples
prompt += """
Example:
Input: "The Parkview Tower project at 123 Main St will have 30 storeys."
Output: {"project_name": "Parkview Tower", "address": "123 Main St", "storeys": 30}
"""
```

**Issue**: Processing timeout for large documents
```python
# Implement timeout handling
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Processing timeout")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(120)  # 2 minute timeout

try:
    result = extractor.extract_data(document)
except TimeoutError:
    # Process in chunks
    result = extractor.extract_data_chunked(document)
finally:
    signal.alarm(0)
```

**Issue**: Missing fields in extraction
```python
# Implement field-specific extraction
def extract_missing_fields(document, missing_fields):
    """Re-extract specific missing fields"""
    for field in missing_fields:
        prompt = f"Extract only the {field} from this document: {document}"
        value = call_ai_api(prompt)

        if value:
            result[field] = value
```

## Business Value

### Time and Cost Savings

- **Manual Processing**: 2-4 hours per document
- **Automated Processing**: 2-5 minutes per document
- **Time Savings**: 70-90%
- **Annual Savings**: $50,000-$500,000 (organization dependent)

### Productivity Impact

- **5-6x** productivity increase per staff member
- **15-30%** reduction in data entry errors
- Enables data-driven decision making
- Facilitates market intelligence gathering

## Documentation References

**Comprehensive Documentation**: `/documentation/` folder
- `README.md`: Overview
- `01_Business_Use_Case_and_Objectives.md`: Business case
- `02_Technical_Architecture.md`: System architecture
- `03_Functional_Architecture.md`: Features
- `04_User_Guide.md`: Usage guide
- `05_Business_Value.md`: ROI analysis

**Project Status**: Production-ready prototype
**Last Updated**: December 2025
