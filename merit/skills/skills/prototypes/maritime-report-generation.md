# Maritime Report Generation

You are an AI assistant specialized in the **Maritime Report Generation** prototype, an AI-powered system for automating and standardizing maritime casualty reports and incident documentation.

## Project Overview

The Maritime Report Generation system provides two AI-powered applications: Maritime Casualty Reporting (data extraction) and Maritime Report Generation (report standardization). It transforms unstructured incident reports into structured data and professional Lloyd's-style reports.

**Location**: `/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/maritime_report_generation/`

## Core Applications

### 1. Maritime Casualty Reporting
**Purpose**: Extract 25+ structured data points from unstructured incident reports

**Output**: CSV file with structured data
**Processing Time**: 5-15 seconds

### 2. Maritime Report Generation
**Purpose**: Transform raw reports into professional, standardized formats

**Features**:
- Automatic vessel information enrichment (IMO, gross tonnage)
- Industry house style application
- Lloyd's-style formatting
- Professional narrative polish

**Output**: Standardized TXT report
**Processing Time**: 20-30 seconds

## Technology Stack

```
Language: Python 3.8+
Framework: Streamlit
AI/ML: LangChain + OpenAI GPT-4o-mini
Data Processing: Pandas, Pydantic
Search: SearX meta-search engine
Configuration: ConfigParser, python-dotenv
```

## Architecture

### Component Structure

```
maritime_casualty_reporting.py    # Data extraction app
maritime_report_generation.py     # Report standardization app
pipeline/
  ├── datapoint_extractor.py      # Extraction logic
  ├── content_generator.py        # Report generation
  ├── datapoints.py               # Pydantic models
  ├── prompts.py                  # Extraction prompts
  └── generator_prompt.py         # Generation prompts
utils/
  ├── config_reader.py
  ├── helper.py
  └── log_writer.py
config.ini                        # Configuration
```

### Processing Flow

**Casualty Reporting**:
```
Raw Incident Report
  ↓
Text Parsing
  ↓
AI Extraction (25 data points)
  ↓
Pydantic Validation
  ↓
CSV Export
```

**Report Generation**:
```
Raw Incident Report
  ↓
Vessel Information Enrichment (SearX search)
  ↓
AI Analysis & Structuring
  ↓
House Style Application
  ↓
Professional Narrative Generation
  ↓
TXT Report Export
```

## Common Implementation Tasks

### 1. Running the Applications

```bash
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/maritime_report_generation/

# Set API key
export OPENAI_API_KEY="your-api-key"

# Install dependencies
pip install streamlit langchain openai pandas pydantic python-dotenv

# Run Casualty Reporting
streamlit run maritime_casualty_reporting.py

# Run Report Generation
streamlit run maritime_report_generation.py
```

### 2. Extracting Data from Incident Report

```python
from pipeline.datapoint_extractor import DatapointExtractor

# Initialize extractor
extractor = DatapointExtractor()

# Sample incident report
report = """
On 15 March 2024 at 1430 UTC, the container vessel MV OCEAN PRIDE
(IMO 9876543, 45,000 GT) experienced engine failure while transiting
Singapore Strait at position 01°15'N 103°50'E. The vessel was carrying
2,500 TEU and crew of 24. No injuries or pollution. Tug assistance
requested and vessel towed to anchorage for repairs.
"""

# Extract data
data = extractor.extract(report)

# Result (Pydantic model):
{
    "vessel_name": "MV OCEAN PRIDE",
    "imo_number": "9876543",
    "gross_tonnage": "45000",
    "incident_date": "2024-03-15",
    "incident_time": "1430",
    "latitude": "01°15'N",
    "longitude": "103°50'E",
    "incident_nature": "Engine failure",
    "crew_number": "24",
    "cargo_description": "2500 TEU",
    "casualties": "0",
    "pollution": "None",
    "actions_taken": "Tug assistance, towed to anchorage",
    ...
}

# Export to CSV
data.to_csv('casualty_data.csv')
```

### 3. Generating Standardized Report

```python
from pipeline.content_generator import ContentGenerator

# Initialize generator
generator = ContentGenerator()

# Generate report
standardized_report = generator.generate_report(report)

# Output (Lloyd's-style):
"""
MV OCEAN PRIDE (FLAG)
Engine Failure - Singapore Strait

Singapore, 15 March 2024

The container vessel MV OCEAN PRIDE (IMO 9876543, 45,000 GT) came in
contact with mechanical difficulties at position 01°15'N 103°50'E in
Singapore Strait on 15 March 2024 at 1430 UTC.

The vessel, carrying 2,500 TEU with crew of 24, sustained engine failure
during transit. No casualties were reported and no pollution occurred.

Tug assistance was arranged and the vessel was towed to anchorage for
repairs. Investigation ongoing.

Reported by: [Authority]
"""

# Save report
with open('standardized_report.txt', 'w') as f:
    f.write(standardized_report)
```

### 4. Vessel Information Enrichment

```python
from utils.helper import enrich_vessel_info

# Enrich with missing vessel data
vessel_name = "OCEAN PRIDE"

# Search for IMO and GT
enriched_data = enrich_vessel_info(vessel_name)

# Returns:
{
    "imo_number": "9876543",
    "gross_tonnage": "45000",
    "flag": "Panama",
    "built": "2015",
    "vessel_type": "Container Ship"
}
```

### 5. Customizing House Style Rules

```python
# House style transformations
HOUSE_STYLE_RULES = {
    # Neutral language
    "collided": "came in contact with",
    "hit": "came in contact with",
    "suffered": "sustained",
    "crashed": "came in contact with",

    # Professional terminology
    "broke down": "sustained mechanical failure",
    "sank": "foundered",
    "caught fire": "sustained fire damage",

    # Title formatting
    "title_format": "{VESSEL_NAME} ({FLAG})",

    # Structure
    "sections": [
        "Dateline",
        "Summary",
        "Details",
        "Actions Taken",
        "Current Status",
        "Reported By"
    ]
}
```

## 25 Extracted Data Points

**Vessel Information**:
1. Vessel Name
2. IMO Number
3. Flag State
4. Vessel Type
5. Gross Tonnage
6. Operator/Owner
7. Crew Number

**Incident Details**:
8. Incident Date
9. Incident Time
10. Incident Nature (collision, grounding, fire, etc.)
11. Cause/Contributing Factors
12. Location Description
13. Latitude
14. Longitude
15. Reference Point

**Impact Assessment**:
16. Casualties (injuries/fatalities)
17. Vessel Damage Description
18. Cargo Description
19. Cargo Impact
20. Environmental Impact
21. Pollution Type/Amount

**Response & Status**:
22. Actions Taken
23. Current Status
24. Reporting Authority
25. Report Date/Time

## House Style Guidelines

### Formatting Rules

**Title Format**:
```
VESSEL NAME (FLAG STATE)
Incident Type - Location
```

**Dateline Format**:
```
Location, Date (e.g., "Singapore, 15 March 2024")
```

**Language Standards**:
- Neutral tone: "came in contact with" not "collided with"
- Professional: "sustained damage" not "suffered damage"
- Precise: "foundered" not "sank"
- Factual: State observations, avoid speculation

**Structure**:
1. Title block
2. Dateline
3. Summary paragraph (who, what, when, where)
4. Details paragraph (circumstances)
5. Actions taken
6. Current status
7. Sign-off (Reported by)

## Best Practices

### Data Extraction

1. **Complete Information**: Include all available details
2. **Precise Timing**: Use UTC for timestamps
3. **Accurate Positions**: Verify coordinates format
4. **Vessel Details**: IMO number is critical
5. **Structured Format**: Follow incident report standards

### Report Generation

1. **Verify Vessel Info**: Cross-check IMO and GT
2. **House Style**: Apply consistently
3. **Factual Language**: Avoid assumptions
4. **Complete Narrative**: Cover all key points
5. **Review Output**: Always human review before publication

### Search Optimization (Vessel Enrichment)

1. **Multiple Sources**: SearX queries multiple search engines
2. **Verification**: Cross-check vessel data
3. **Fallback**: Manual entry if search fails
4. **Cache Results**: Store vessel info for future use

## Use Cases

### Lloyd's Agent Reporting
Transform incident notifications into standardized Lloyd's-style reports

### Insurance Claims
Extract structured data for claims processing systems

### Port Authority Documentation
Standardize incident reports across jurisdictions

### Compliance Reporting
Generate regulatory-compliant incident documentation

### Incident Database Population
Convert unstructured reports to structured CSV data for analysis

## Business Value

### Time Savings

**Manual Process**:
- Data extraction: 2-3 hours
- Report writing: 3-4 hours
- Total: 5-7 hours per incident

**Automated Process**:
- Data extraction: 15 seconds
- Report generation: 30 seconds
- Review: 15 minutes
- Total: ~15 minutes

**Savings**: 87% time reduction

### Cost Savings

- **Cost per Report**: $16.90 saved
- **Annual Savings** (100 reports): $1,690
- **Capacity Increase**: 7.5x more reports per person per day

### ROI

- **Year 1 ROI**: 168%
- **Ongoing ROI**: 900%+
- **Payback Period**: <6 months

## Documentation References

**Comprehensive Documentation**: `/documentation/` folder
- `README.md`: Documentation overview
- `01_Business_Use_Case_and_Objectives.md`: Use cases
- `02_Technical_Architecture.md`: System architecture
- `03_Functional_Architecture.md`: Functional specs
- `04_User_Guide.md`: User guide
- `05_Business_Value.md`: ROI analysis

**Project Status**: Production-ready prototype
**Last Updated**: December 2024
