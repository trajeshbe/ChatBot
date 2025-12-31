# Agronomy Decision Support Assistant

You are an AI assistant specialized in the **Agronomy Decision Support Assistant** prototype, a comprehensive AI-powered platform for agricultural decision-making, crop planning, label compliance, and customer relationship management.

## Project Overview

The Agronomy Decision Support Assistant is a Streamlit-based web application featuring three integrated modules that transform agricultural operations through AI and machine learning. It provides field-wise crop recommendations, AI-powered label analysis with compliance validation, and personalized grower dashboards.

**Location**: `/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/agronomy_decision_support/`

## Core Modules

### 1. Smart Crop Planning
Field-wise crop recommendations with multi-factor analysis

**Features**:
- Crop suitability scoring (0-100 scale)
- Historical yield analysis
- Weather forecast integration
- Soil condition assessment
- Rotation planning support
- Risk assessment
- Profitability analysis

**Input**: CSV files with field data (yields, weather, soil)
**Output**: Ranked crop recommendations with scores

### 2. Smart Label Navigator
AI-powered agricultural label analysis and compliance validation

**Features**:
- GPT-4 Vision label image analysis
- Compliance validation engine
- Active ingredient extraction
- Application rate calculation
- Safety information extraction
- REI (Re-Entry Interval) and PHI (Pre-Harvest Interval) detection

**Input**: Label images (JPG, PNG, PDF)
**Output**: Structured label data + compliance report

### 3. Customer Relations
Personalized grower dashboards and communication tools

**Features**:
- Grower-specific dashboards
- Field performance analytics
- Communication history tracking
- Risk assessment calculations
- Recommendation tracking
- Engagement analytics

**Input**: Customer/field CSV data
**Output**: Interactive dashboards and reports

## Technology Stack

```
Framework: Streamlit 1.46.1+
ML Models: Scikit-learn (crop recommendations, yield prediction)
AI Engine: OpenAI GPT-4 Vision (label analysis)
Visualization: Plotly 6.2.0+
Data Processing: Pandas 2.3.1+, NumPy
Configuration: TOML (pyproject.toml)
```

## Architecture

### Module Structure

```
app.py                      # Main application entry point
modules/
  ├── smart_crop_planning/
  │   ├── crop_planner.py   # Crop recommendation engine
  │   └── data_loader.py    # CSV data processing
  ├── smart_label/
  │   ├── label_analyzer.py # GPT-4 Vision integration
  │   └── compliance.py     # Compliance validation
  └── customer_relations/
      ├── dashboard.py      # Grower dashboards
      └── analytics.py      # Performance metrics
models/
  ├── crop_model.pkl       # Trained crop recommendation model
  └── yield_model.pkl      # Yield prediction model
utils/
  ├── config.py            # Configuration management
  └── helpers.py           # Utility functions
```

## Common Implementation Tasks

### 1. Running the Application

```bash
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/agronomy_decision_support/

# Set up environment
export OPENAI_API_KEY="your-api-key"

# Run application
streamlit run app.py
```

### 2. Smart Crop Planning - Generate Recommendations

```python
from modules.smart_crop_planning.crop_planner import CropPlanner

# Initialize planner
planner = CropPlanner()

# Load field data
field_data = planner.load_field_data('field_data.csv')

# Generate recommendations
recommendations = planner.recommend_crops(
    field_id='field_001',
    historical_yields=yields_df,
    weather_forecast=weather_df,
    soil_data=soil_df
)

# Output includes:
# - Crop name
# - Suitability score (0-100)
# - Yield prediction
# - Risk assessment
# - Profitability estimate
```

### 3. Smart Label Navigator - Analyze Label

```python
from modules.smart_label.label_analyzer import LabelAnalyzer

# Initialize analyzer
analyzer = LabelAnalyzer()

# Analyze label image
with open('label.jpg', 'rb') as f:
    label_data = analyzer.analyze_label(f.read())

# Extract compliance info
compliance = analyzer.check_compliance(label_data)

# Results include:
# - Product name
# - Active ingredients
# - Application rates
# - Safety information
# - Compliance status
# - Violations (if any)
```

### 4. Customer Relations - Generate Dashboard

```python
from modules.customer_relations.dashboard import GrowerDashboard

# Initialize dashboard
dashboard = GrowerDashboard()

# Load grower data
grower_data = dashboard.load_grower_data('grower_001')

# Generate dashboard
dashboard.render_dashboard(
    grower_id='grower_001',
    fields=grower_data['fields'],
    season='2024'
)

# Dashboard includes:
# - Field performance map
# - Yield trends
# - Recommendations status
# - Risk indicators
# - Communication log
```

### 5. Customizing Crop Recommendation Algorithm

```python
# Modify crop_planner.py

def calculate_suitability_score(field, crop):
    """Custom suitability calculation"""

    # Weight factors (customize these)
    weights = {
        'historical_yield': 0.30,
        'soil_match': 0.25,
        'weather_suitability': 0.20,
        'rotation_benefit': 0.15,
        'market_price': 0.10
    }

    # Calculate component scores
    yield_score = calculate_yield_score(field, crop)
    soil_score = calculate_soil_match(field, crop)
    weather_score = calculate_weather_fit(field, crop)
    rotation_score = calculate_rotation_benefit(field, crop)
    market_score = calculate_market_potential(crop)

    # Weighted average
    total_score = (
        weights['historical_yield'] * yield_score +
        weights['soil_match'] * soil_score +
        weights['weather_suitability'] * weather_score +
        weights['rotation_benefit'] * rotation_score +
        weights['market_price'] * market_score
    )

    return total_score
```

## Data Formats

### Crop Planning CSV Format

```csv
field_id,crop,yield,year,soil_type,ph,weather_days
field_001,corn,185,2023,loam,6.5,120
field_001,soybeans,52,2022,loam,6.4,110
field_002,wheat,78,2023,clay,7.1,95
```

### Weather Forecast CSV Format

```csv
field_id,date,temp_min,temp_max,precipitation,growing_days
field_001,2024-05-01,55,75,0.5,150
field_002,2024-05-01,52,72,0.3,140
```

### Soil Data CSV Format

```csv
field_id,soil_type,ph,organic_matter,nitrogen,phosphorus,potassium
field_001,loam,6.5,3.2,high,medium,high
field_002,clay,7.1,2.8,medium,high,medium
```

## Algorithms and Logic

### Crop Suitability Scoring (0-100)

```
Score = Σ(weight_i × component_score_i)

Components:
1. Historical Yield (30%): Performance in similar conditions
2. Soil Match (25%): Soil type compatibility
3. Weather Suitability (20%): Climate fit for crop
4. Rotation Benefit (15%): Agronomic rotation value
5. Market Price (10%): Economic potential
```

### Compliance Validation Rules

```python
compliance_rules = {
    'active_ingredients': 'Must be clearly listed',
    'application_rate': 'Must specify rate per acre',
    'rei': 'Re-Entry Interval must be stated',
    'phi': 'Pre-Harvest Interval if applicable',
    'epa_number': 'EPA registration required',
    'signal_word': 'DANGER, WARNING, or CAUTION',
    'precautionary_statements': 'Required safety info'
}
```

### Risk Assessment Calculation

```python
def calculate_field_risk(field_data):
    """Calculate risk score (0-100, higher = more risk)"""
    risk_factors = {
        'weather_variability': 30,  # % weight
        'pest_pressure': 25,
        'soil_issues': 20,
        'market_volatility': 15,
        'disease_history': 10
    }

    risk_score = sum(
        weight * assess_factor(field_data, factor)
        for factor, weight in risk_factors.items()
    )

    return risk_score
```

## Best Practices

### Smart Crop Planning

1. **Data Quality**: Ensure 3+ years of historical data for accuracy
2. **Update Regularly**: Refresh weather forecasts weekly
3. **Soil Testing**: Annual soil tests for accurate recommendations
4. **Local Calibration**: Adjust weights based on regional performance
5. **Validation**: Compare recommendations with agronomist expertise

### Smart Label Navigator

1. **Image Quality**: Use high-resolution label images (300+ DPI)
2. **Complete Labels**: Capture full label including all text panels
3. **Clear Photos**: Ensure good lighting and focus
4. **Verify Results**: Always review AI-extracted data
5. **Compliance Database**: Maintain up-to-date compliance rules

### Customer Relations

1. **Data Privacy**: Secure grower information appropriately
2. **Regular Updates**: Update dashboards at least weekly
3. **Communication Log**: Track all interactions systematically
4. **Actionable Insights**: Focus on decisions, not just data
5. **Custom Views**: Tailor dashboards to grower preferences

## Debugging Guide

### Common Issues

**Issue**: Crop recommendations seem inaccurate
```python
# Check data quality
print(field_data.isnull().sum())  # Missing values
print(field_data.describe())  # Data ranges

# Verify model performance
from sklearn.metrics import r2_score
predictions = model.predict(X_test)
print(f"R² Score: {r2_score(y_test, predictions)}")

# Retrain if needed
model.fit(X_train, y_train)
```

**Issue**: Label analysis failing
```python
# Check image format and size
from PIL import Image
img = Image.open('label.jpg')
print(f"Size: {img.size}, Format: {img.format}")

# Verify API key
import os
print(f"API Key set: {'OPENAI_API_KEY' in os.environ}")

# Test with simpler image
# Reduce image size if > 20MB
```

**Issue**: Dashboard not loading
```python
# Check data dependencies
required_files = ['growers.csv', 'fields.csv', 'recommendations.csv']
for file in required_files:
    if not os.path.exists(file):
        print(f"Missing: {file}")

# Verify CSV format
import pandas as pd
df = pd.read_csv('growers.csv')
print(df.head())
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
COPY pyproject.toml .
RUN pip install -e .
COPY . .
ENV OPENAI_API_KEY=""
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

### Cloud Deployment (Streamlit Cloud)
```toml
# .streamlit/config.toml
[server]
headless = true
port = 8501

[theme]
primaryColor = "#4CAF50"
backgroundColor = "#FFFFFF"
```

## Business Value

### Key Metrics

**Smart Crop Planning**:
- 5-10% yield improvement potential
- 90% reduction in planning time
- $500-2000/field/year value

**Smart Label Navigator**:
- 87% faster compliance review
- <1% error rate
- 95%+ regulation compliance

**Customer Relations**:
- 60% increase in client capacity per agronomist
- 4.8/5 satisfaction rating
- 50% reduction in communication time

### ROI

**Agricultural Service Provider** (10 agronomists):
- Investment: $84,000
- Year 1 Benefits: $673,500
- Year 1 ROI: 1,147%
- Payback: <1 month

## Documentation References

**Comprehensive Documentation**: `/documentation/` folder
- `README.md`: Documentation index
- `01_Business_Use_Case_and_Objectives.md`: Use cases and objectives
- `02_Technical_Architecture.md`: System architecture
- `03_Functional_Architecture.md`: Module specifications
- `04_User_Guide.md`: User instructions
- `05_Business_Value.md`: ROI and value analysis

## Extension Points

### Adding New Crops

```python
# Add to crop database
new_crop = {
    'name': 'quinoa',
    'suitable_soils': ['loam', 'sandy_loam'],
    'optimal_ph': (6.0, 8.5),
    'growing_days': 120,
    'water_needs': 'moderate',
    'rotation_benefits': {'legume': 10, 'grain': 5}
}

crop_database.add(new_crop)
```

### Custom Compliance Rules

```python
# Add industry-specific rules
custom_rules = {
    'organic_certification': {
        'required_fields': ['omri_listed', 'organic_approved'],
        'prohibited_ingredients': ['synthetic_pesticides'],
        'validation': lambda label: check_organic_compliance(label)
    }
}
```

### API Integration

```python
# Expose as REST API
from fastapi import FastAPI
app = FastAPI()

@app.post("/api/crop-recommendations")
def get_recommendations(field_id: str):
    planner = CropPlanner()
    return planner.recommend_crops(field_id)

@app.post("/api/label-analysis")
def analyze_label(image: UploadFile):
    analyzer = LabelAnalyzer()
    return analyzer.analyze_label(image.file.read())
```

**Project Status**: Production-ready prototype
**Last Updated**: December 2025
