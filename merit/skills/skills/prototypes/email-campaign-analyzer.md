# Email Campaign Analyzer (Bot Detection)

You are an AI assistant specialized in the **Email Campaign Analyzer**, a bot detection system designed to identify automated email security software and distinguish genuine human engagement from inflated metrics.

## Project Overview

The Email Campaign Analyzer uses machine learning and rule-based detection to identify bot activity in email campaigns. It helps marketers distinguish real engagement from automated security software that inflates open rates and click metrics without genuine human interaction.

**Location**: `/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/email_campaign_analyzer/`

## Core Capabilities

### Bot Detection Methods

**Rule-Based Detection** (Recommended):
- Weighted scoring system (5 detection rules)
- Based on real campaign data
- Fully transparent and explainable
- Customizable weights and thresholds

**ML-Based Detection** (Advanced):
- Custom trained models
- Supports scikit-learn compatible models
- Requires .pkl model file
- Automatic fallback to rule-based

### Detection Rules

1. **Void Link Testing** (35% weight): Clicks without opens
2. **Email Predownloading** (25% weight): Instant opens
3. **Instant Activity** (20% weight): Microsecond timestamps
4. **Unusual Patterns** (15% weight): Repeated identical behaviors
5. **Brief Sessions** (5% weight): No sustained engagement

## Technology Stack

```
Language: Python 3.11+
Framework: Streamlit 1.46.1+
Data Processing: Pandas 2.3.0+, NumPy 2.3.1+
Visualization: Plotly 6.2.0+
Machine Learning: Scikit-learn 1.7.0+
Model Serialization: Joblib 1.5.1+
```

## Architecture

### Component Structure

```
app.py                     # Main Streamlit application
bot_detector.py           # Rule-based detection engine
ml_detector.py            # ML model integration
data_validator.py         # Data validation
visualization.py          # Chart generation
email_bot_detector_model.pkl  # Pre-trained model (optional)
model_features.txt        # ML model features
```

### Processing Pipeline

```
CSV Upload (Email Events)
  ↓
Data Validation & Cleaning
  ↓
Feature Engineering
  ↓
Bot Detection (Rule-based or ML)
  ↓
Campaign Health Assessment
  ↓
Interactive Visualizations
  ↓
Detailed Explanations & Export
```

## Common Implementation Tasks

### 1. Running the Application

```bash
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/email_campaign_analyzer/

# Install dependencies
pip install streamlit pandas numpy plotly scikit-learn joblib

# Run application
streamlit run app.py
```

### 2. Required Data Format

```csv
session_id,event_type,timestamp
session_001,email_sent,2024-01-01 10:00:00
session_001,email_opened,2024-01-01 10:00:02
session_001,link_clicked,2024-01-01 10:00:01
session_002,email_sent,2024-01-01 10:01:00
session_002,email_opened,2024-01-01 10:15:30
```

**Required Columns**:
- `session_id`: Unique identifier for each recipient session
- `event_type`: Event (email_sent, email_opened, link_clicked)
- `timestamp`: Event timestamp (YYYY-MM-DD HH:MM:SS)

**Minimum Requirements**:
- At least 10 rows
- 100+ rows recommended for accuracy
- File formats: CSV, XLSX, XLS
- Size limit: 200MB (default)

### 3. Analyzing a Campaign

```python
from bot_detector import BotDetector
import pandas as pd

# Initialize detector
detector = BotDetector()

# Load campaign data
campaign_data = pd.read_csv('campaign_events.csv')

# Detect bots
results = detector.analyze_campaign(campaign_data)

# Results include:
{
    'bot_score': 0.65,  # 0-1, higher = more bot activity
    'bot_percentage': 65.0,
    'detection_reasons': [
        'High void link testing (40%)',
        'Instant opens detected (30%)'
    ],
    'campaign_health': 'warning',  # good/warning/critical
    'recommendations': [...]
}
```

### 4. Customizing Detection Weights

```python
# Default weights
default_weights = {
    'void_link_testing': 0.35,
    'email_predownloading': 0.25,
    'instant_activity': 0.20,
    'unusual_patterns': 0.15,
    'brief_sessions': 0.05
}

# Custom weights for your campaigns
custom_weights = {
    'void_link_testing': 0.40,  # Increase if you see more void clicks
    'email_predownloading': 0.30,
    'instant_activity': 0.15,
    'unusual_patterns': 0.10,
    'brief_sessions': 0.05
}

# Apply custom weights
detector = BotDetector(weights=custom_weights)
```

### 5. Bot Score Interpretation

```python
def interpret_bot_score(score):
    """
    Interpret campaign bot score

    Score Ranges:
    - 0.0-0.2: Very likely human (healthy)
    - 0.2-0.4: Probably human (good)
    - 0.4-0.6: Uncertain (monitor)
    - 0.6-0.8: Probably bot (warning)
    - 0.8-1.0: Very likely bot (critical)
    """
    if score < 0.2:
        return {
            'category': 'Very Likely Human',
            'health': 'excellent',
            'action': 'Continue current practices'
        }
    elif score < 0.4:
        return {
            'category': 'Probably Human',
            'health': 'good',
            'action': 'Monitor bot indicators'
        }
    elif score < 0.6:
        return {
            'category': 'Uncertain',
            'health': 'fair',
            'action': 'Review detection details'
        }
    elif score < 0.8:
        return {
            'category': 'Probably Bot',
            'health': 'warning',
            'action': 'Improve list hygiene'
        }
    else:
        return {
            'category': 'Very Likely Bot',
            'health': 'critical',
            'action': 'Clean list immediately'
        }
```

## Campaign Health Indicators

### Healthy Campaigns

- Open rates: 19-54%
- Click-to-open ratios: 2.12-13.78%
- Bot contamination: <25%
- Consistent engagement patterns
- Varied timestamp distribution

### Bot-Inflated Campaigns

- Open rates: 68-80%+
- Click-to-open ratios: 0.12-3.74%
- Bot contamination: >50%
- Instant/uniform activity
- Void click patterns

## Detection Algorithms

### Void Link Testing

```python
def detect_void_link_testing(df):
    """Detect clicks that occur before opens"""

    sessions = df.groupby('session_id')

    void_clicks = 0
    total_sessions = 0

    for session_id, events in sessions:
        sent_time = events[events['event_type'] == 'email_sent']['timestamp'].min()
        opened_time = events[events['event_type'] == 'email_opened']['timestamp'].min()
        clicked_time = events[events['event_type'] == 'link_clicked']['timestamp'].min()

        # Check if click occurred before open
        if pd.notna(clicked_time) and pd.notna(opened_time):
            if clicked_time < opened_time:
                void_clicks += 1

        total_sessions += 1

    void_percentage = (void_clicks / total_sessions * 100) if total_sessions > 0 else 0

    return {
        'void_percentage': void_percentage,
        'is_suspicious': void_percentage > 10,  # > 10% is suspicious
        'score': min(void_percentage / 40, 1.0)  # Normalize to 0-1
    }
```

### Email Predownloading

```python
def detect_email_predownloading(df):
    """Detect instant opens (within 1 second)"""

    sessions = df.groupby('session_id')

    instant_opens = 0
    total_opens = 0

    for session_id, events in sessions:
        sent_events = events[events['event_type'] == 'email_sent']
        open_events = events[events['event_type'] == 'email_opened']

        if len(sent_events) > 0 and len(open_events) > 0:
            sent_time = sent_events['timestamp'].iloc[0]
            open_time = open_events['timestamp'].iloc[0]

            time_diff = (open_time - sent_time).total_seconds()

            if time_diff < 1.0:  # Less than 1 second
                instant_opens += 1

            total_opens += 1

    instant_percentage = (instant_opens / total_opens * 100) if total_opens > 0 else 0

    return {
        'instant_percentage': instant_percentage,
        'is_suspicious': instant_percentage > 20,
        'score': min(instant_percentage / 50, 1.0)
    }
```

### Instant Activity

```python
def detect_instant_activity(df):
    """Detect microsecond-precision identical timestamps"""

    timestamp_counts = df['timestamp'].value_counts()

    # Check for suspiciously identical timestamps
    duplicate_timestamps = timestamp_counts[timestamp_counts > 5].count()
    total_events = len(df)

    duplicate_percentage = (duplicate_timestamps / total_events * 100)

    return {
        'duplicate_percentage': duplicate_percentage,
        'is_suspicious': duplicate_percentage > 15,
        'score': min(duplicate_percentage / 30, 1.0)
    }
```

## Best Practices

### Data Collection

1. **Session Tracking**: Maintain consistent session IDs
2. **Timestamp Precision**: Use millisecond precision
3. **Event Completeness**: Capture all email events
4. **Data Quality**: Clean data before analysis
5. **Regular Analysis**: Analyze campaigns post-send

### Bot Prevention

1. **List Hygiene**: Remove confirmed bots regularly
2. **Authentication**: Implement BIMI, DMARC
3. **Engagement Tracking**: Monitor true engagement metrics
4. **Segmentation**: Separate bot-heavy segments
5. **Testing**: Use seed lists for bot detection

### Campaign Optimization

1. **Baseline Metrics**: Establish healthy campaign benchmarks
2. **Trend Monitoring**: Track bot rates over time
3. **A/B Testing**: Test subject lines, content
4. **Timing**: Optimize send times for real humans
5. **Content Quality**: Focus on genuine value

## Business Value

### Key Benefits

- **Accurate Metrics**: True engagement visibility
- **Better Deliverability**: Improved sender reputation
- **Cost Savings**: Don't pay for bot activity
- **Strategic Decisions**: Data-driven campaign planning
- **List Quality**: Cleaner, more engaged lists

### Metrics

- **Detection Accuracy**: 85-90%
- **Processing Speed**: <10 seconds for 10K events
- **False Positive Rate**: <10%

## Documentation References

**Comprehensive Documentation**: `/documentation/` folder
- `README.md`: Documentation index
- `01_OVERVIEW.md`: System overview
- `02_ARCHITECTURE.md`: Technical design
- `03_API_REFERENCE.md`: API documentation
- `04_USER_GUIDE.md`: User instructions
- `05_DEPLOYMENT.md`: Deployment guide

**Project Status**: Production-ready
**Last Updated**: December 2025
