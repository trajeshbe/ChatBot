# Crop Insight Tagger (Agri Taxonomy)

You are an AI assistant specialized in the **Crop Insight Tagger** prototype, an agricultural field inspection taxonomy system that automatically extracts structured data from unstructured field inspection reports.

## Project Overview

The Crop Insight Tagger is an AI-powered web application built with Streamlit that uses Large Language Models (LLMs) to extract structured agricultural taxonomies from natural language field inspection reports. It processes unstructured text and outputs standardized JSON data across 15 agricultural categories.

**Location**: `/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/agri_taxonomy/`

## Core Capabilities

### 15 Agricultural Taxonomy Categories

1. **Crop Establishment**: Growth stage (e.g., "V6 Growth Stage", "R3 Reproductive")
2. **Growth Observation**: Plant health indicators (plant height, leaf development)
3. **Soil Condition**: Physical/chemical properties (alkaline, good tilth)
4. **Soil Nutrient**: Nutrient status (potassium deficiency, nitrogen levels)
5. **Leaf Symptom**: Visible abnormalities (scorching, yellowing, chewing damage)
6. **Physiological Symptom**: Stress indicators (wilting, stunted growth)
7. **Pest**: Insect identifications (armyworm, aphid infestation)
8. **Disease**: Pathogen observations (grey leaf spot, rust)
9. **Weed Pressure**: Infestation levels (moderate, high, low)
10. **Weed Type**: Species/categories (broadleaf, grass weeds)
11. **Fertilizer Applied**: Input tracking (MOP, urea, NPK 15-15-15)
12. **Herbicide Use**: Applications (pre-emergent, post-emergent)
13. **Drainage**: Field conditions (effective, poor, waterlogged)
14. **Weather Pattern**: Recent conditions (warm & humid, dry spell)
15. **Recommendation**: Advisory actions (potassium foliar spray, targeted insecticide)

### Key Features

- Natural language understanding of agricultural terminology
- Multi-category extraction (all 15 categories simultaneously)
- Flexible input handling (narrative, bullets, structured text)
- Rapid processing (2-5 seconds per inspection)
- High accuracy (85%+ extraction accuracy)
- Scalable processing without additional labor
- Unknown value handling for missing information

## Technology Stack

```
Language: Python 3.8+
Web Framework: Streamlit
AI Framework: LangChain
LLM Provider: OpenAI (GPT-4o-mini, temperature=0)
Data Validation: Pydantic
Configuration: PyYAML, python-dotenv
Logging: Loguru
```

## Architecture

### Layered Architecture

```
Presentation Layer (Streamlit UI)
    ↓
Business Logic Layer (AgriTaxonomy Class)
    ↓
Integration Layer (LangChain Framework)
    ↓
External Service Layer (OpenAI API)
    ↓
Infrastructure Layer (Config, Logging)
```

### Key Components

**app.py**: Main Streamlit application and UI
**config_reader.py**: YAML configuration loader
**log_writer.py**: Structured logging with rotation
**prompt.py**: LLM instruction templates
**config.yaml**: System configuration

## Common Implementation Tasks

### 1. Running the Application

```bash
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/agri_taxonomy/

# Ensure .env file has OPENAI_API_KEY
streamlit run app.py
```

### 2. Processing a Field Inspection

```python
from app import AgriTaxonomy

# Initialize
agri = AgriTaxonomy()

# Process inspection text
inspection_text = """
The maize field is at V6 growth stage with good plant height.
Soil appears slightly alkaline with good tilth. Some potassium
deficiency noted. Few armyworm larvae observed. Grey leaf spot
detected on lower leaves. Moderate broadleaf weed pressure.
"""

result = agri.get_agri_taxonomy(inspection_text)
# Returns: Dict with all 15 categories populated
```

### 3. Customizing the Model

Edit `config.yaml`:

```yaml
data_path: data
llm:
  model: gpt-4o-mini  # Change model
  model_provider: openai  # openai, azure, anthropic
  temperature: 0  # 0-1, lower = more deterministic
  max_tokens: 2000  # Maximum response tokens
  timeout: 30  # API timeout in seconds
```

### 4. Modifying the Prompt

Edit `prompt.py` to adjust extraction behavior:

```python
# Add specific instructions for your use case
# Modify field definitions
# Adjust unknown value handling
# Add new taxonomy categories
```

### 5. Adding Logging

```python
from log_writer import CustomLogger

class MyClass(CustomLogger):
    def __init__(self):
        super().__init__()
        self.logger.info("Logging event")
        self.logger.error("Error occurred")
```

## Data Models

### Input Format

Unstructured text (any format):
- Narrative paragraphs
- Bullet points
- Field notes
- Inspection reports

### Output Schema (Pydantic)

```python
class FieldInspectionTaxonomy(BaseModel):
    crop_establishment: Optional[str]
    growth_observation: Optional[List[str]]
    soil_condition: Optional[List[str]]
    soil_nutrient: Optional[List[str]]
    leaf_symptom: Optional[List[str]]
    physiological_symptom: Optional[List[str]]
    pest: Optional[List[str]]
    disease: Optional[List[str]]
    weed_pressure: Optional[List[str]]
    weed_type: Optional[List[str]]
    fertilizer_applied: Optional[List[str]]
    herbicide_use: Optional[List[str]]
    drainage: Optional[List[str]]
    weather_pattern: Optional[List[str]]
    recommendation: Optional[List[str]]
```

### Transformation Rules

1. List fields → comma-separated strings
2. Snake_case keys → Title Case
3. Missing/unclear values → "Unknown"

## Best Practices

### Writing Effective Inspection Notes

1. **Be specific**: Use precise terminology (e.g., "V6 growth stage" not "mid-season")
2. **Include details**: Mention severity, location, extent
3. **Use standard terms**: Agricultural industry terminology
4. **Be comprehensive**: Cover all relevant observations
5. **Avoid ambiguity**: Clear descriptions over vague statements

### Input Examples

**Good**:
```
Field shows V8 growth stage with excellent stand uniformity.
Soil pH appears slightly acidic (estimated 6.2) with moderate tilth.
Minor nitrogen deficiency visible in older leaves (yellowing).
Light aphid pressure noted on lower leaf surfaces.
Applied urea (46-0-0) at 100 lbs/acre last week.
Recommend foliar zinc application and scout for armyworm.
```

**Avoid**:
```
Plants look okay. Some bugs. Need fertilizer maybe.
```

## Debugging Guide

### Common Issues

**Issue**: "Config file not found"
```python
# Verify config.yaml exists in project root
import os
print(os.path.exists('config.yaml'))
```

**Issue**: API timeout
```yaml
# Increase timeout in config.yaml
llm:
  timeout: 60  # Increase from 30 to 60 seconds
```

**Issue**: Low extraction accuracy
```python
# Check prompt clarity in prompt.py
# Verify temperature is set to 0 for consistency
# Review LLM model selection (GPT-4o-mini vs GPT-4)
```

**Issue**: Missing taxonomy categories
```python
# Verify Pydantic schema includes all fields
# Check prompt template includes all categories
# Review LLM response for parsing errors
```

## Deployment Options

### Local Development
```bash
streamlit run app.py
# Access at http://localhost:8501
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501"]
```

### Cloud Deployment (AWS ECS, GCP Cloud Run, Azure Container Instances)
- Containerize application
- Set environment variables (OPENAI_API_KEY)
- Configure load balancer
- Enable auto-scaling
- Set up monitoring

## Business Metrics

### Value Delivered

| Metric | Value |
|--------|-------|
| Time Savings per Inspection | 10-15 minutes |
| Cost per Inspection | $0.02-0.05 |
| Data Consistency Improvement | 90%+ |
| Extraction Accuracy | 85%+ |
| Processing Time | 2-5 seconds |

### ROI Examples

**Medium Organization** (500 inspections/month):
- Investment: $15,000 + $8,000/year
- Annual Benefit: $96,000
- Year 1 ROI: 487%
- Payback: 2.1 months

## Documentation References

**Comprehensive Documentation**: `/documentation/` folder
- `README.md`: Documentation index and quick start
- `01_Business_Use_Case_and_Objectives.md`: Business context and objectives
- `02_Technical_Architecture.md`: System design and implementation
- `03_Functional_Architecture.md`: Feature specifications and workflows
- `04_User_Guide.md`: End-user instructions
- `05_Business_Value.md`: ROI analysis and business value

## Extension Points

### Adding New Taxonomy Categories

1. Update Pydantic schema in code
2. Modify prompt template to include new category
3. Update UI to display new field
4. Test with sample data
5. Document the new category

### Integrating with Farm Management Systems

```python
# Example: Export to Farm ERP
def export_to_farm_erp(taxonomy_data):
    """Export taxonomy to external farm management system"""
    import requests
    response = requests.post(
        'https://farm-erp.example.com/api/inspections',
        json=taxonomy_data,
        headers={'Authorization': 'Bearer TOKEN'}
    )
    return response.json()
```

### Adding Database Persistence

```python
import sqlite3

def save_to_database(taxonomy_data):
    """Save extraction results to SQLite database"""
    conn = sqlite3.connect('inspections.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO inspections
        (crop_establishment, soil_condition, ...)
        VALUES (?, ?, ...)
    ''', tuple(taxonomy_data.values()))
    conn.commit()
    conn.close()
```

## Support and Feedback

For issues or improvements:
1. Review troubleshooting in User Guide
2. Check system requirements
3. Verify installation steps
4. Consult technical architecture for advanced issues

**Project Status**: Prototype - Ready for pilot deployment
**Last Updated**: December 2025
