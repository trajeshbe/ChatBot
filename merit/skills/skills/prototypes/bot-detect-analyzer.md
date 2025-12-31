# Bot Intervention Predictor

You are an AI assistant specialized in the **Bot Intervention Predictor** prototype, an AI-powered tool for detecting automated bot interventions in email engagement data.

## Project Overview

The Bot Intervention Predictor is a Streamlit-based machine learning application that identifies automated email security software (bots) that inflate open rates and click metrics without genuine human engagement. It helps marketers distinguish real engagement from bot activity to improve campaign analysis and deliverability.

**Location**: `/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/bot_detect_analyzer/`

## Core Capabilities

### Bot Detection Features

1. **Automated Bot Classification**: ML-powered identification of bot interventions
2. **Behavioral Pattern Analysis**: 16+ engineered features for comprehensive analysis
3. **Explainable AI**: Clear reasoning for every classification decision
4. **Interactive Analytics**: Real-time visualizations and data exploration
5. **High Accuracy**: 95%+ detection accuracy with <5% false positive rate
6. **Fast Processing**: Analyze 10,000 records in under 30 seconds
7. **CSV Export**: Download results for further analysis

### Detection Capabilities

**Bot Types Detected**:
- Email firewalls and security scanners
- Email predownloading systems
- Link testing software
- Spam filters with preview functionality
- Automated security tools

**Key Indicators**:
- Void link testing (clicks without opens)
- Email predownloading (instant opens)
- Instant activity (microsecond timestamps)
- Unusual patterns (repeated identical behaviors)
- Brief sessions (no sustained engagement)

## Technology Stack

```
Language: Python 3.11+
Framework: Streamlit
ML Model: Random Forest Classifier (200 trees)
Data Processing: Pandas, NumPy
Visualization: Plotly
Feature Engineering: 16+ behavioral features
ML Library: Scikit-learn
```

## Architecture

### Component Structure

```
app.py                  # Streamlit UI and orchestration
bot_detector.py         # Bot detection logic and ML model
data_processor.py       # Data validation and preprocessing
sample_data.csv         # Sample dataset for testing
pyproject.toml          # Dependencies and configuration
```

### Data Processing Pipeline

```
CSV Upload
  ↓
Data Validation (9 required columns)
  ↓
Feature Engineering (16+ features)
  ↓
ML Model Classification
  ↓
Explainable Results
  ↓
Interactive Visualizations
```

## Common Implementation Tasks

### 1. Running the Application

```bash
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/bot_detect_analyzer/

# Install dependencies
pip install streamlit pandas scikit-learn plotly

# Run application
streamlit run app.py
```

### 2. Analyzing Email Campaign Data

```python
from bot_detector import BotDetector
import pandas as pd

# Load detector
detector = BotDetector()

# Load campaign data
campaign_data = pd.read_csv('campaign_data.csv')

# Detect bots
results = detector.detect_bots(campaign_data)

# Results include:
# - bot_probability: 0-1 score
# - is_bot: binary classification
# - detection_reasons: list of indicators
# - confidence: classification confidence
```

### 3. Understanding Required Data Format

```csv
recipient_domain,time_to_open_sec,num_opens,user_agent,ip_type,time_to_click_sec,click_sequence_entropy,fast_opener_flag,multiple_opens_30s
gmail.com,2.5,3,Mozilla/5.0,residential,120.5,0.8,0,0
corporate.com,0.1,1,LinkChecker,datacenter,0.05,0.0,1,1
yahoo.com,45.0,2,Chrome/120,residential,180.0,0.6,0,0
```

**Required Columns**:
1. **recipient_domain**: Email domain (e.g., gmail.com)
2. **time_to_open_sec**: Seconds from send to first open
3. **num_opens**: Total number of opens
4. **user_agent**: Email client identifier
5. **ip_type**: IP address type (residential/datacenter/mobile)
6. **time_to_click_sec**: Seconds from send to first click
7. **click_sequence_entropy**: Randomness of click patterns
8. **fast_opener_flag**: 1 if opened within 1 second, else 0
9. **multiple_opens_30s**: 1 if multiple opens within 30 seconds

### 4. Interpreting Bot Scores

```python
def interpret_bot_score(probability):
    """
    Interpret bot probability score

    Score Ranges:
    - 0.0-0.2: Very likely human
    - 0.2-0.4: Probably human
    - 0.4-0.6: Uncertain
    - 0.6-0.8: Probably bot
    - 0.8-1.0: Very likely bot
    """
    if probability < 0.2:
        return "Very Likely Human"
    elif probability < 0.4:
        return "Probably Human"
    elif probability < 0.6:
        return "Uncertain"
    elif probability < 0.8:
        return "Probably Bot"
    else:
        return "Very Likely Bot"
```

### 5. Feature Engineering

```python
# 16+ Engineered Features

def engineer_features(df):
    """Create behavioral features for bot detection"""

    # Temporal Features
    df['very_fast_open'] = (df['time_to_open_sec'] < 1).astype(int)
    df['instant_click'] = (df['time_to_click_sec'] < 2).astype(int)

    # Behavioral Features
    df['unusual_user_agent'] = df['user_agent'].str.contains(
        'bot|crawler|spider|checker', case=False, na=False
    ).astype(int)

    df['datacenter_ip'] = (df['ip_type'] == 'datacenter').astype(int)

    # Pattern Features
    df['void_click'] = (
        (df['time_to_click_sec'] < df['time_to_open_sec']) &
        (df['time_to_click_sec'] > 0)
    ).astype(int)

    df['low_entropy'] = (df['click_sequence_entropy'] < 0.3).astype(int)

    # Engagement Features
    df['excessive_opens'] = (df['num_opens'] > 10).astype(int)

    return df
```

## Best Practices

### Data Preparation

1. **Complete Data**: Ensure all 9 required columns are present
2. **Clean Data**: Remove duplicates and invalid records
3. **Sufficient Volume**: Minimum 100 records recommended
4. **Representative Sample**: Include diverse recipient types
5. **Time Zones**: Normalize timestamps to UTC

### Bot Detection

1. **Threshold Tuning**: Default 0.7, adjust based on false positive tolerance
2. **Multiple Indicators**: Don't rely on single feature
3. **Domain Analysis**: Check patterns by email domain
4. **Temporal Analysis**: Look for bot activity spikes
5. **Human Review**: Validate bot classifications periodically

### Campaign Analysis

1. **Baseline Metrics**: Establish healthy campaign benchmarks
2. **Trend Monitoring**: Track bot rates over time
3. **Segmentation**: Analyze bots by recipient domain, IP type
4. **Action Thresholds**: Define when to take corrective action
5. **List Hygiene**: Remove confirmed bot addresses

## Metrics and Benchmarks

### Healthy vs Bot-Inflated Campaigns

**Healthy Campaigns**:
- Open rates: 19-54%
- Click-to-open ratios: 2.12-13.78%
- Bot contamination: <25%

**Bot-Inflated Campaigns**:
- Open rates: 68-80%
- Click-to-open ratios: 0.12-3.74%
- Bot contamination: >50%

### Model Performance

```
Detection Accuracy: 95%+
False Positive Rate: <5%
False Negative Rate: <5%
Processing Speed: <30 seconds for 10K records
```

## Debugging Guide

### Common Issues

**Issue**: High false positive rate
```python
# Adjust classification threshold
detector.threshold = 0.8  # Increase from 0.7 to reduce false positives

# Check feature distributions
import matplotlib.pyplot as plt
df['bot_probability'].hist(bins=50)
plt.show()
```

**Issue**: CSV upload failing
```python
# Verify column names (case-sensitive)
required_cols = [
    'recipient_domain', 'time_to_open_sec', 'num_opens',
    'user_agent', 'ip_type', 'time_to_click_sec',
    'click_sequence_entropy', 'fast_opener_flag', 'multiple_opens_30s'
]

df_cols = df.columns.tolist()
missing = set(required_cols) - set(df_cols)
print(f"Missing columns: {missing}")
```

**Issue**: Slow processing
```python
# Process in batches for large datasets
batch_size = 5000
results = []

for i in range(0, len(df), batch_size):
    batch = df[i:i+batch_size]
    batch_results = detector.detect_bots(batch)
    results.append(batch_results)

final_results = pd.concat(results)
```

## Business Value

### Key Benefits

**For Email Marketers**:
- Reduce bounce rates by 30-50%
- Improve sender reputation scores
- Increase email deliverability
- Save time on manual analysis

**Annual Value** ($219,000):
- Time savings: $144,000
- Improved deliverability: $50,000
- Better targeting: $25,000

**ROI**: 1,725% first year, 2.7 week payback

## Documentation References

**Comprehensive Documentation**: `/documentation/` folder
- `README.md`: Documentation overview
- `01_Business_Use_Case_and_Objectives.md`: Business context
- `02_Technical_Architecture.md`: System architecture
- `03_Functional_Architecture.md`: Features and workflows
- `04_User_Guide.md`: User instructions
- `05_Business_Value.md`: ROI analysis

## Extension Points

### Custom ML Models

```python
# Train custom model with your data
from sklearn.ensemble import RandomForestClassifier

# Prepare features and labels
X = feature_engineered_data
y = labeled_bot_data

# Train model
model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X, y)

# Save model
import joblib
joblib.dump(model, 'custom_bot_model.pkl')
```

### API Integration

```python
from fastapi import FastAPI, UploadFile
import pandas as pd

app = FastAPI()

@app.post("/api/detect-bots")
async def detect_bots(file: UploadFile):
    """API endpoint for bot detection"""
    df = pd.read_csv(file.file)
    detector = BotDetector()
    results = detector.detect_bots(df)
    return results.to_dict(orient='records')
```

### Real-Time Detection

```python
# Stream processing for real-time detection
from kafka import KafkaConsumer

consumer = KafkaConsumer('email_events')
detector = BotDetector()

for message in consumer:
    event = json.loads(message.value)
    is_bot = detector.predict_single(event)

    if is_bot:
        alert_system.notify(event)
```

**Project Status**: Production-ready prototype
**Last Updated**: December 2025
