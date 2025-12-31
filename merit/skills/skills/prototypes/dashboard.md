# KIAA Intelligence Suite Dashboard

You are an AI assistant specialized in the **KIAA Intelligence Suite Dashboard**, a modular AI accelerator platform that transforms unstructured data into actionable insights across diverse domains.

## Project Overview

The KIAA Intelligence Suite is a comprehensive Streamlit-based dashboard featuring 22+ active modules organized into 7 domain categories. It provides a unified interface for accessing specialized AI capabilities including information extraction, recruitment tools, taxonomy classification, profile matching, maritime intelligence, email analysis, and tender intelligence.

**Location**: `/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/dashboard/`

## Module Catalog (22+ Modules)

### 1. Intelligent Information Extraction (3 modules)
- **Flexitag**: Dynamic entity extraction from unstructured text
- **Relationship Extraction**: Entity relationship mapping
- **Extractive Q&A**: Document-based question answering

### 2. Recruiter's Toolkit (3 modules)
- **Map Search**: Semantic candidate discovery
- **Profile Match**: CV-JD matching with scoring
- **Skill Taxonomy**: Skill standardization and mapping

### 3. Taxonomy Tagger (5 modules)
- **News Taxonomy**: Multi-level news categorization
- **Procurement Doc Classifier**: Document classification and routing
- **Crop Insight Tagger**: Agricultural data organization
- **Regulation Classifier**: Compliance framework mapping (coming soon)
- **Policy Tagger**: Governance document organization (coming soon)

### 4. Profile Matcher (4 modules)
- **Training Matcher**: Learning program recommendations
- **Legal Matcher**: Case-precedent alignment
- **Procurement Matcher**: Supplier-requirement matching
- **Tender2Vendor**: Tender opportunity discovery

### 5. Maritime Intelligence (2 modules)
- **Vessel Info Extractor**: Ship registry data extraction
- **Casualty Reporting**: Maritime incident analysis

### 6. Intelligent Email Management (3 modules)
- **Bounce-Back Email Analyzer**: Deliverability diagnostics
- **Bot Detection Assistant**: Campaign metric accuracy
- **Credit Report Generator**: Financial intelligence extraction

### 7. Tender Intelligence (2 modules)
- **Spend Smart**: Public sector spending analysis
- **Bid Radar**: AI-powered tender detection

## Technology Stack

```
Framework: Streamlit (Python)
Architecture: Microservices, modular design
Configuration: JSON (app_info.json)
Deployment: Containerizable, cloud-ready
Module Integration: Dynamic loading
Security: Enterprise-grade considerations
```

## Architecture

### Dashboard Structure

```
dashboard/
├── app.py                  # Main dashboard application
├── app_info.json          # Module configuration
├── modules/               # Individual module implementations
│   ├── flexitag/
│   ├── news_taxonomy/
│   ├── profile_match/
│   └── [22+ modules]
├── utils/
│   ├── module_loader.py   # Dynamic module loading
│   └── navigation.py      # Dashboard navigation
└── documentation/         # Comprehensive docs
```

### Module Configuration (app_info.json)

```json
{
  "modules": [
    {
      "name": "Flexitag",
      "category": "Information Extraction",
      "description": "Dynamic entity extraction",
      "path": "/modules/flexitag/app.py",
      "status": "active",
      "icon": "tag"
    }
  ]
}
```

## Common Implementation Tasks

### 1. Running the Dashboard

```bash
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/dashboard/

# Run dashboard
streamlit run app.py
```

### 2. Adding a New Module

```python
# 1. Create module directory
mkdir modules/new_module

# 2. Create module app
# modules/new_module/app.py
import streamlit as st

def render_module():
    st.title("New Module")
    # Module implementation
    pass

# 3. Add to app_info.json
{
  "name": "New Module",
  "category": "Custom Category",
  "description": "Module description",
  "path": "/modules/new_module/app.py",
  "status": "active",
  "icon": "star"
}
```

### 3. Navigating Between Modules

```python
import streamlit as st

# Display navigation sidebar
selected_module = st.sidebar.selectbox(
    "Select Module",
    options=module_list
)

# Load selected module
if selected_module:
    module_path = get_module_path(selected_module)
    load_module(module_path)
```

### 4. Module Integration Pattern

```python
# Standard module template
import streamlit as st
from typing import Dict, Any

class ModuleName:
    """Module description"""

    def __init__(self):
        self.config = self.load_config()

    def render_ui(self):
        """Render module UI"""
        st.title("Module Title")

        # Input section
        user_input = st.text_area("Input")

        # Processing
        if st.button("Process"):
            result = self.process(user_input)
            st.write(result)

    def process(self, input_data: str) -> Dict[str, Any]:
        """Core processing logic"""
        # Implementation
        return {"result": "processed data"}

# Entry point
if __name__ == "__main__":
    module = ModuleName()
    module.render_ui()
```

### 5. Accessing Module from Dashboard

```python
# Dashboard integration
def load_module(module_path):
    """Dynamically load and execute module"""
    import importlib.util

    spec = importlib.util.spec_from_file_location("module", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Execute module's main function
    if hasattr(module, 'render_module'):
        module.render_module()
```

## Module Development Best Practices

### Module Structure

```
modules/your_module/
├── app.py              # Main application
├── config.yaml         # Module configuration
├── requirements.txt    # Dependencies
├── models/             # ML models if needed
├── utils/              # Utility functions
└── README.md           # Module documentation
```

### Standard Module Interface

```python
class ModuleInterface:
    """Standard interface for all modules"""

    def __init__(self, config: Dict = None):
        """Initialize module"""
        pass

    def render_ui(self):
        """Render Streamlit UI"""
        pass

    def process(self, input_data: Any) -> Any:
        """Process input data"""
        pass

    def export_results(self, results: Any, format: str = 'csv'):
        """Export results"""
        pass
```

### UI/UX Guidelines

1. **Consistent Header**: Module name and description
2. **Input Section**: Clear input areas with examples
3. **Processing Feedback**: Loading indicators and progress
4. **Results Display**: Formatted output with visualizations
5. **Export Options**: Download capabilities
6. **Help Section**: Usage instructions and examples

## Dashboard Configuration

### app_info.json Schema

```json
{
  "dashboard": {
    "title": "KIAA Intelligence Suite",
    "version": "1.0",
    "description": "Modular AI Accelerator Platform"
  },
  "categories": [
    {
      "name": "Information Extraction",
      "icon": "extract",
      "order": 1
    }
  ],
  "modules": [
    {
      "id": "flexitag",
      "name": "Flexitag",
      "category": "Information Extraction",
      "description": "Dynamic entity extraction",
      "path": "/modules/flexitag/app.py",
      "status": "active",
      "version": "1.0",
      "dependencies": ["openai", "spacy"],
      "icon": "tag",
      "author": "KIAA Team",
      "last_updated": "2025-01-15"
    }
  ]
}
```

### Module Status Values

- **active**: Available for use
- **beta**: Testing phase
- **deprecated**: Scheduled for removal
- **maintenance**: Temporarily unavailable
- **coming_soon**: Planned future module

## Common Use Cases

### Information Extraction Workflow

```python
# Use Flexitag to extract entities
entities = flexitag.extract_entities(text)

# Use Relationship Extraction to find connections
relationships = relationship_extractor.find_relationships(entities)

# Use Extractive Q&A to answer questions
answers = extractive_qa.answer_questions(text, questions)
```

### Recruitment Workflow

```python
# Use Skill Taxonomy to standardize skills
standardized_skills = skill_taxonomy.standardize(resume_skills)

# Use Map Search to find candidates
candidates = map_search.find_candidates(job_requirements)

# Use Profile Match to rank candidates
scores = profile_match.score_candidates(candidates, job_description)
```

### Maritime Intelligence Workflow

```python
# Extract vessel information
vessel_info = vessel_extractor.extract_info(incident_report)

# Generate casualty report
casualty_report = casualty_reporting.generate_report(vessel_info)
```

## Business Value

### Key Metrics by Module Category

**Recruitment Tools**:
- 60% reduction in time-to-hire
- 45% improvement in candidate match quality
- $2.9M+ annual value

**Procurement Intelligence**:
- 3% procurement cost reduction
- Improved supplier selection
- $4.6M+ annual value

**Maritime Operations**:
- 20% reduction in casualties
- 10% lower insurance premiums
- $3M+ annual value

### Platform ROI

- **Year 1 ROI**: 300-500%
- **Payback Period**: <2 months
- **Annual Value**: $10-40M+ (depending on scale)
- **Efficiency Gains**: 40-60% reduction in processing time

## Debugging Guide

### Common Issues

**Issue**: Module not loading
```python
# Check module path in app_info.json
import os
module_path = config['modules'][0]['path']
print(f"Exists: {os.path.exists(module_path)}")

# Verify module status
print(f"Status: {config['modules'][0]['status']}")
```

**Issue**: Dashboard not displaying modules
```python
# Validate app_info.json
import json
with open('app_info.json') as f:
    config = json.load(f)
    print(f"Modules: {len(config['modules'])}")
    print(f"Active: {sum(1 for m in config['modules'] if m['status'] == 'active')}")
```

**Issue**: Module dependencies missing
```bash
# Install module dependencies
cd modules/your_module
pip install -r requirements.txt

# Or install all
pip install -r requirements.txt
```

## Deployment Options

### Local Development
```bash
streamlit run app.py --server.port 8501
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kiaa-dashboard
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: dashboard
        image: kiaa-dashboard:latest
        ports:
        - containerPort: 8501
```

## Documentation References

**Comprehensive Documentation**: `/documentation/` folder
- `README.md`: Dashboard overview
- `01_Business_Use_Case_and_Objectives.md`: Business case
- `02_Technical_Architecture.md`: System architecture
- `03_Functional_Architecture.md`: Module specifications
- `04_User_Guide.md`: User guide
- `05_Business_Value.md`: ROI analysis

## Extension Points

### Creating Custom Categories

```json
{
  "categories": [
    {
      "name": "Custom Intelligence",
      "icon": "custom",
      "order": 8,
      "description": "Custom AI modules"
    }
  ]
}
```

### Module Analytics Integration

```python
def track_module_usage(module_name, user_id, action):
    """Track module usage for analytics"""
    analytics.log_event({
        'module': module_name,
        'user': user_id,
        'action': action,
        'timestamp': datetime.now()
    })
```

### API Gateway Integration

```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/api/{module_name}/process")
def process_via_module(module_name: str, data: dict):
    """API endpoint for module processing"""
    module = load_module(module_name)
    result = module.process(data)
    return result
```

**Project Status**: Production deployment ready
**Last Updated**: December 2025
