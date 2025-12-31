# Email Campaign Analyzer - API Reference

## Table of Contents

1. [Module Overview](#module-overview)
2. [app.py - Main Application](#apppy---main-application)
3. [feature_extractor.py - Feature Engineering](#feature_extractorpy---feature-engineering)
4. [bot_detector.py - Detection Logic](#bot_detectorpy---detection-logic)
5. [utils.py - Utility Functions](#utilspy---utility-functions)
6. [create_model.py - Model Training](#create_modelpy---model-training)
7. [Data Structures](#data-structures)
8. [Constants and Configuration](#constants-and-configuration)

---

## Module Overview

### Dependencies

```python
# Core Data Processing
import pandas as pd
import numpy as np

# Streamlit Framework
import streamlit as st

# Visualization
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Machine Learning
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib

# Utilities
from datetime import datetime
import io
import os
import re
```

---

## app.py - Main Application

### Functions

#### main()

```python
def main() -> None
```

**Description**: Main application entry point and orchestrator.

**Features**:
- Configures Streamlit page settings
- Initializes sidebar controls
- Manages tab-based interface
- Handles model file uploads

**Page Configuration**:
```python
st.set_page_config(
    page_title="Bot Detection Assistant",
    page_icon="🤖",
    layout="wide"
)
```

**Sidebar Controls**:
- Prediction method selector (Rule-based / ML Classifier)
- Model file uploader (.pkl files)
- Sample model download option
- Configuration instructions

**Tab Structure**:
- Tab 1: Data Upload
- Tab 2: Analysis
- Tab 3: Dashboard

**Returns**: None (Streamlit rendering)

**Side Effects**:
- Modifies session state
- Renders UI elements

---

#### handle_data_upload()

```python
def handle_data_upload() -> None
```

**Description**: Manages file upload and initial data processing.

**Workflow**:
1. Display file uploader widget
2. Load uploaded file
3. Show data preview (first 10 rows)
4. Display column information
5. Validate data structure
6. Extract features
7. Store in session state

**Session State Keys Modified**:
- `raw_data`: Original DataFrame
- `processed_data`: Feature-extracted DataFrame
- `column_mapping`: Column name mappings

**File Types Supported**:
- CSV (.csv)
- Excel (.xlsx, .xls)

**Error Handling**:
- File loading errors
- Validation failures
- Feature extraction errors

**UI Elements**:
- File uploader
- Data preview table
- Column information table
- Success/error messages

**Returns**: None (Streamlit rendering)

---

#### handle_analysis(prediction_method: str, model_file: Optional[UploadedFile])

```python
def handle_analysis(
    prediction_method: str,
    model_file: Optional[UploadedFile]
) -> None
```

**Description**: Executes bot detection analysis based on selected method.

**Parameters**:
- `prediction_method` (str): Either "Rule-based Scoring" or "ML Classifier (.pkl model)"
- `model_file` (Optional[UploadedFile]): Uploaded .pkl model file (for ML method)

**Rule-Based Method Workflow**:
1. Display detection strategy overview
2. Show customizable weight sliders
3. Show threshold configuration
4. Execute rule-based prediction
5. Store and display results

**ML Method Workflow**:
1. Validate model file uploaded
2. Load model with joblib
3. Execute ML prediction
4. Handle compatibility errors
5. Store and display results

**Weight Customization Options** (Rule-Based):
- Void Link Testing: 0.0 - 0.5 (default: 0.35)
- Email Predownloading: 0.0 - 0.5 (default: 0.25)
- Instant Activity: 0.0 - 0.5 (default: 0.20)
- Unusual Patterns: 0.0 - 0.3 (default: 0.15)
- Brief Sessions: 0.0 - 0.2 (default: 0.05)

**Threshold Customization Options**:
- Rapid Activity: 5.0 - 30.0 events/min (default: 10.0)
- Brief Session: 1.0 - 10.0 seconds (default: 2.0)

**Session State Keys Modified**:
- `results`: Detection results DataFrame
- `prediction_method`: Selected method name

**Error Handling**:
- Model version compatibility issues
- Model loading errors
- Prediction failures
- Missing model file

**Returns**: None (Streamlit rendering)

**Raises**:
- Displays error messages for model compatibility issues

---

#### display_results(results: pd.DataFrame)

```python
def display_results(results: pd.DataFrame) -> None
```

**Description**: Display detection results with filtering and explanations.

**Parameters**:
- `results` (pd.DataFrame): Results from bot detection with columns:
  - `session_id`: Session identifier
  - `bot_score`: Bot probability (0-1)
  - `prediction`: "Likely Bot" or "Likely Human"
  - `detection_reasons`: Semicolon-separated reasons
  - (Plus all feature columns)

**Summary Metrics Displayed**:
- Total Sessions
- Likely Bots (count and percentage)
- Likely Humans (count and percentage)
- Average Bot Score

**Filter Options**:
- Prediction filter: All / Likely Bot / Likely Human
- Bot score range: Min and Max sliders (0.0 - 1.0)
- Sort by: bot_score, num_events, event_frequency_per_min, open_duration_sec
- Sort order: Ascending / Descending

**Results Table Features**:
- Color-coded rows (red for bots, green for humans)
- Formatted numeric values
- 400px height with scrolling
- Full-width responsive layout

**Bot Explanation Section**:
- Shows first 10 bot sessions
- Expandable detail cards
- Formatted detection reasons
- Bot score in header

**Returns**: None (Streamlit rendering)

---

#### handle_dashboard()

```python
def handle_dashboard() -> None
```

**Description**: Display analytics dashboard with visualizations.

**Campaign Health Assessment**:

**Metrics Calculated**:
- Campaign Open Rate: (Sessions with opens / Total sessions) × 100
- Click-to-Open Ratio: (Total clicks / Total opens) × 100
- Bot Detection Rate: (Bot sessions / Total sessions) × 100

**Health Status Indicators**:

*Open Rate*:
- > 65%: "Likely Bot-Inflated" (red)
- > 55%: "Potentially Inflated" (orange)
- ≤ 55%: "Healthy Range" (green)

*Click-to-Open Ratio*:
- < 2%: "Very Low (Bot Pattern)" (red)
- < 5%: "Below Normal" (orange)
- ≥ 5%: "Healthy Range" (green)

*Bot Detection Rate*:
- > 50%: "High Bot Activity" (red)
- > 25%: "Moderate Bot Activity" (orange)
- ≤ 25%: "Low Bot Activity" (green)

**Visualizations**:

1. **Bot vs Human Pie Chart**
   - Distribution of predictions
   - Color-coded (red/green)
   - Percentage labels

2. **Bot Score Histogram**
   - 20 bins
   - Vertical line at threshold (0.5)
   - Blue bars

3. **Feature Distribution Box Plots** (2×2 grid)
   - Event Frequency
   - Session Duration
   - Number of Events
   - Void Events
   - Grouped by prediction

4. **Feature Correlation Matrix**
   - Heatmap of numeric features
   - Red-Blue diverging color scale
   - Square aspect ratio

**Benchmark Comparison**:
- Healthy campaigns: 19-54% opens, 2.12-13.78% CTO
- Bot-inflated campaigns: 68-80% opens, 0.12-3.74% CTO

**Returns**: None (Streamlit rendering)

---

## feature_extractor.py - Feature Engineering

### Class: FeatureExtractor

```python
class FeatureExtractor:
    """
    Extracts session-level features from event-level email campaign data.

    Supports dynamic column identification for various email platform formats.
    """
```

#### Constructor

```python
def __init__(self) -> None
```

**Description**: Initialize feature extractor.

**Attributes**:
- `column_mapping` (dict): Maps standard names to actual column names

**Example**:
```python
extractor = FeatureExtractor()
features = extractor.extract_features(df)
```

---

#### extract_features()

```python
def extract_features(self, df: pd.DataFrame) -> pd.DataFrame
```

**Description**: Main feature extraction pipeline.

**Parameters**:
- `df` (pd.DataFrame): Raw event-level data

**Returns**:
- `pd.DataFrame`: Session-aggregated features

**Columns Returned**:
- `session_id`: Session identifier
- `num_events`: Total events
- `num_opens`: Open events
- `num_clicks`: Click events
- `num_previews`: Preview events
- `num_voids`: Void/test events
- `unique_user_agents`: Distinct user agents
- `has_multiple_user_agents`: Boolean flag
- `unique_fingerprints`: Distinct fingerprints
- `has_multiple_fingerprints`: Boolean flag
- `first_event_time`: Earliest timestamp
- `last_event_time`: Latest timestamp
- `open_duration_sec`: Session duration
- `event_frequency_per_min`: Events per minute
- `events_per_second`: Event rate
- `click_to_open_ratio`: Clicks / Opens
- `void_to_total_ratio`: Voids / Total events

**Workflow**:
1. Identify columns dynamically
2. Clean and prepare data
3. Group by session ID
4. Extract features per session
5. Fill missing values

**Raises**:
- `ValueError`: If session ID column cannot be identified

**Example**:
```python
extractor = FeatureExtractor()
features_df = extractor.extract_features(raw_data)
print(features_df.columns)
```

---

#### _identify_columns()

```python
def _identify_columns(self, df: pd.DataFrame) -> None
```

**Description**: Dynamically identify column names using pattern matching.

**Parameters**:
- `df` (pd.DataFrame): Input DataFrame

**Side Effects**:
- Populates `self.column_mapping` dictionary

**Column Patterns**:

| Standard Name | Patterns |
|--------------|----------|
| session_id | report_entry_id, session_id, entry_id, id |
| event_type | type, event, action, event_type |
| timestamp | created, timestamp, time, datetime, date |
| void | void, is_void |
| fingerprint | fingerprint, fp, device_id |
| user_agent | user_agent, useragent, agent, ua |

**Matching Strategy**:
- Case-insensitive substring matching
- First match wins
- Required: session_id
- Optional: all others

**Example**:
```python
# Given columns: ['Report_Entry_ID', 'Type', 'Created']
# Mapping: {'session_id': 'Report_Entry_ID', 'event_type': 'Type', 'timestamp': 'Created'}
```

---

#### _clean_data()

```python
def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame
```

**Description**: Clean and normalize data types.

**Parameters**:
- `df` (pd.DataFrame): Input DataFrame

**Returns**:
- `pd.DataFrame`: Cleaned DataFrame

**Operations**:
1. Convert timestamp columns to datetime
2. Fill void column nulls with 0
3. Convert event types to lowercase
4. Handle conversion errors gracefully

**Timestamp Conversion Strategy**:
1. Try direct pd.to_datetime()
2. Fallback: pd.to_datetime() with errors='coerce'
3. If both fail: Keep original column

**Example**:
```python
# Before: created='2024-01-01 10:30:00', void=NaN, type='OPEN'
# After:  created=Timestamp('2024-01-01 10:30:00'), void=0, type='open'
```

---

#### _extract_session_features()

```python
def _extract_session_features(self, df: pd.DataFrame) -> pd.DataFrame
```

**Description**: Aggregate events into session-level features.

**Parameters**:
- `df` (pd.DataFrame): Cleaned event-level data

**Returns**:
- `pd.DataFrame`: Session-aggregated features

**Aggregation Logic**:

**Event Counts**:
```python
num_opens = sum(event_type in ['open', 'email_open', 'opened'])
num_clicks = sum(event_type in ['click', 'clicked', 'link_click'])
num_previews = sum(event_type in ['preview', 'previewed'])
num_voids = sum(void == 1)
```

**Identity Metrics**:
```python
unique_user_agents = nunique(user_agent)
has_multiple_user_agents = unique_user_agents > 1
```

**Temporal Features**:
```python
first_event_time = min(timestamp)
last_event_time = max(timestamp)
duration = (last - first).total_seconds()
open_duration_sec = max(duration, 1)  # Minimum 1 second
event_frequency_per_min = (num_events / duration) * 60
```

**Derived Ratios**:
```python
click_to_open_ratio = num_clicks / max(num_opens, 1)
void_to_total_ratio = num_voids / num_events
events_per_second = num_events / open_duration_sec
```

**Null Handling**:
- All numeric columns filled with 0
- Prevents downstream errors
- Maintains data integrity

**Example**:
```python
# Input: 5 events for session 'abc123'
# Output: Single row with 17+ feature columns
```

---

## bot_detector.py - Detection Logic

### Class: BotDetector

```python
class BotDetector:
    """
    Bot detection classifier supporting rule-based and ML approaches.

    Calibrated for email security software patterns based on real campaign data.
    """
```

#### Constructor

```python
def __init__(self) -> None
```

**Description**: Initialize bot detector.

**Attributes**:
- `threshold` (float): Binary classification threshold (0.5)

**Example**:
```python
detector = BotDetector()
results = detector.rule_based_prediction(features)
```

---

#### rule_based_prediction()

```python
def rule_based_prediction(
    self,
    features_df: pd.DataFrame,
    weights: Optional[Dict[str, float]] = None,
    thresholds: Optional[Dict[str, float]] = None
) -> pd.DataFrame
```

**Description**: Apply rule-based bot detection with weighted scoring.

**Parameters**:
- `features_df` (pd.DataFrame): Session features from FeatureExtractor
- `weights` (Optional[Dict[str, float]]): Rule weights (default shown below)
- `thresholds` (Optional[Dict[str, float]]): Detection thresholds (default shown below)

**Default Weights**:
```python
weights = {
    'void': 0.35,              # Void link testing
    'opens_only': 0.25,        # Email predownloading
    'instant_activity': 0.20,  # Rapid/clustered events
    'unusual_patterns': 0.15,  # Abnormal behavior
    'duration': 0.05           # Brief sessions
}
```

**Default Thresholds**:
```python
thresholds = {
    'frequency': 10.0,         # Events per minute
    'duration': 2.0,           # Seconds
    'instant_threshold': 1.0   # Seconds
}
```

**Returns**:
- `pd.DataFrame`: Input features plus:
  - `bot_score` (float): 0-1 normalized score
  - `prediction` (str): "Likely Bot" or "Likely Human"
  - `confidence` (float): 0-1 confidence score
  - `detection_reasons` (str): Semicolon-separated reasons

**Detection Rules**:

**Rule 1: Void Events (35% weight)**
```python
if num_voids > 0:
    bot_score += weights['void']
    reasons += 'Void-link-testing; '
```

**Rule 2: Opens-Only Pattern (25% weight)**
```python
# Pattern 1: Multiple opens, no clicks
if num_opens >= 2 and num_clicks == 0:
    bot_score += weights['opens_only']
    reasons += 'Multiple-opens-zero-clicks; '

# Pattern 2: Very low click-to-open ratio
if num_opens > 0 and (num_clicks / num_opens) < 0.02:
    bot_score += weights['opens_only'] * 0.7
    reasons += 'Very-low-click-rate; '
```

**Rule 3: Instant/Rapid Activity (20% weight)**
```python
# Sub-rule 3a: High frequency
if event_frequency_per_min > thresholds['frequency']:
    instant_score += 0.7
    reasons += 'High-frequency-events; '

# Sub-rule 3b: Instant clustering
if num_events > 1 and open_duration_sec < thresholds['instant_threshold']:
    instant_score += 0.3
    reasons += 'Instant-event-cluster; '
```

**Rule 4: Unusual Patterns (15% weight)**
```python
# Multiple user agents
if has_multiple_user_agents:
    unusual_score += 0.4
    reasons += 'Multiple-user-agents; '

# Perfect ratios
if click_to_open_ratio in [0.5, 1.0, 2.0]:
    unusual_score += 0.3
    reasons += 'Perfect-engagement-ratio; '

# High void ratio
if void_to_total_ratio > 0.3:
    unusual_score += 0.3
    reasons += 'High-void-ratio; '
```

**Rule 5: Brief Sessions (5% weight)**
```python
if open_duration_sec < thresholds['duration']:
    bot_score += weights['duration']
    reasons += 'Brief-session; '
```

**Bonus Rules**:
- Preview-only activity: +0.15
- High open rate campaign (>65%): +0.10
- Minimal engagement pattern: +0.12

**Normalization**:
```python
max_possible_score = sum(weights.values()) + 0.15  # Including bonus
normalized_score = clip(bot_score / max_possible_score, 0, 1)
```

**Classification**:
```python
prediction = 'Likely Bot' if bot_score > 0.5 else 'Likely Human'
```

**Confidence Calculation**:
```python
confidence = min(
    abs(bot_score - 0.5) * 2,  # Distance from boundary
    len(detection_reasons.split(';')) / 10  # Number of reasons
)
```

**Example**:
```python
detector = BotDetector()
results = detector.rule_based_prediction(
    features_df,
    weights={'void': 0.4, 'opens_only': 0.3, ...},
    thresholds={'frequency': 15.0, 'duration': 1.5}
)
print(results[['session_id', 'bot_score', 'prediction']])
```

---

#### ml_prediction()

```python
def ml_prediction(
    self,
    features_df: pd.DataFrame,
    model: Any
) -> pd.DataFrame
```

**Description**: Apply machine learning model for bot detection.

**Parameters**:
- `features_df` (pd.DataFrame): Session features
- `model` (Any): Trained model loaded from .pkl file

**Returns**:
- `pd.DataFrame`: Input features plus:
  - `bot_score` (float): Model probability
  - `prediction` (str): "Likely Bot" or "Likely Human"
  - `confidence` (float): 0-1 confidence score
  - `detection_reasons` (str): "ML-model-prediction"

**Workflow**:
1. Extract ML-compatible features
2. Fill missing values with 0
3. Replace infinite values with 0
4. Apply model prediction
5. Normalize scores to 0-1
6. Apply threshold
7. Calculate confidence

**Feature Selection**:
- Includes all numeric columns
- Excludes: session_id, timestamps, boolean flags (converted elsewhere)

**Model Compatibility**:

*Supported Model Types*:
- Classifiers with `predict_proba()` (RandomForest, XGBoost, etc.)
- Classifiers with `predict()` only
- Regressors (scores normalized to 0-1)

*Probability Extraction*:
```python
if hasattr(model, 'predict_proba'):
    probabilities = model.predict_proba(X)
    bot_score = probabilities[:, 1]  # Positive class probability
else:
    scores = model.predict(X)
    bot_score = (scores - min) / (max - min)  # Normalize
```

**Error Handling**:
- Version compatibility issues → Fallback to rule-based
- Missing features → Attempt alignment
- Prediction failures → Fallback to rule-based
- Detailed error messages for debugging

**Example**:
```python
import joblib
model = joblib.load('email_bot_detector_model.pkl')
detector = BotDetector()
results = detector.ml_prediction(features_df, model)
```

**Raises**:
- Prints errors but does not raise exceptions
- Falls back to rule_based_prediction() on any error

---

#### _get_ml_features()

```python
def _get_ml_features(self, df: pd.DataFrame) -> List[str]
```

**Description**: Select appropriate features for ML models.

**Parameters**:
- `df` (pd.DataFrame): Feature DataFrame

**Returns**:
- `List[str]`: Column names suitable for ML

**Exclusion Criteria**:
- Non-numeric columns
- Identifier columns: session_id
- Timestamp columns: first_event_time, last_event_time
- Boolean flags: has_multiple_user_agents, has_multiple_fingerprints

**Inclusion Criteria**:
- Numeric data type (int, float)
- Not in exclusion list

**Example**:
```python
features = detector._get_ml_features(features_df)
# Returns: ['num_events', 'num_opens', 'num_clicks', 'click_to_open_ratio', ...]
```

---

#### explain_prediction()

```python
def explain_prediction(
    self,
    session_data: Dict[str, Any],
    prediction_method: str = 'rule_based'
) -> List[str]
```

**Description**: Generate human-readable explanations for predictions.

**Parameters**:
- `session_data` (Dict[str, Any]): Single session's feature values
- `prediction_method` (str): 'rule_based' or 'ml_based'

**Returns**:
- `List[str]`: Explanation strings with emojis and context

**Explanation Patterns**:

```python
# Void events
if num_voids > 0:
    "🔍 Security software detected: {num_voids} void/test link events"

# Email predownloading
if num_opens >= 2 and num_clicks == 0:
    "📧 Email predownloading pattern: {num_opens} opens with no clicks"

# Low click-to-open ratio
if cto_ratio < 0.02:
    "📊 Extremely low engagement: {cto_ratio}% click-to-open ratio (normal: 2-14%)"

# Rapid activity
if event_frequency_per_min > 10:
    "⚡ Rapid automated activity: {frequency} events/min"

# Instant clustering
if num_events > 1 and duration < 1:
    "🤖 Instant event cluster: {num_events} events in {duration} seconds"

# Brief session
if open_duration_sec < 2:
    "⏱️ Brief session: {duration} seconds (security software quick disconnect)"

# Multiple identities
if has_multiple_user_agents:
    "🔄 Multiple identities: {unique_user_agents} different user agents"

# Perfect ratios
if click_to_open_ratio in [0.5, 1.0, 2.0]:
    "📊 Perfect ratio pattern: {ratio} click-to-open ratio"

# High void ratio
if void_to_total_ratio > 0.3:
    "🧪 High testing ratio: {ratio} of events were void/test links"

# Preview only
if num_previews > 0 and num_opens == 0 and num_clicks == 0:
    "👁️ Preview-only scanning: {num_previews} preview events"
```

**Fallback Explanation**:
```python
if no patterns detected and prediction == 'Likely Bot':
    "⚠️ Multiple weak indicators combined (bot score: {score})"
```

**Example**:
```python
session = {
    'num_voids': 2,
    'num_opens': 5,
    'num_clicks': 0,
    'event_frequency_per_min': 15.3
}
explanations = detector.explain_prediction(session)
for exp in explanations:
    print(exp)
# Output:
# 🔍 Security software detected: 2 void/test link events
# 📧 Email predownloading pattern: 5 opens with no clicks
# ⚡ Rapid automated activity: 15.3 events/min
```

---

#### get_feature_importance()

```python
def get_feature_importance(
    self,
    model: Any,
    feature_names: List[str]
) -> Dict[str, float]
```

**Description**: Extract feature importance from ML model.

**Parameters**:
- `model` (Any): Trained ML model
- `feature_names` (List[str]): Feature column names

**Returns**:
- `Dict[str, float]`: Feature name → importance mapping

**Supported Model Types**:

*Tree-Based Models*:
```python
if hasattr(model, 'feature_importances_'):
    importance = model.feature_importances_  # RandomForest, XGBoost, etc.
```

*Linear Models*:
```python
if hasattr(model, 'coef_'):
    importance = abs(model.coef_[0])  # LogisticRegression, LinearSVC, etc.
```

**Example**:
```python
importance = detector.get_feature_importance(model, feature_names)
sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)
for feature, score in sorted_features[:5]:
    print(f"{feature}: {score:.4f}")
```

---

## utils.py - Utility Functions

### load_data()

```python
def load_data(uploaded_file: UploadedFile) -> Optional[pd.DataFrame]
```

**Description**: Load CSV or XLSX file with encoding fallback.

**Parameters**:
- `uploaded_file` (UploadedFile): Streamlit uploaded file object

**Returns**:
- `pd.DataFrame`: Loaded data
- `None`: If loading fails

**File Format Support**:
- CSV: UTF-8, Latin-1, CP1252 encodings
- XLSX/XLS: Excel files

**Encoding Fallback Strategy**:
```python
try:
    df = pd.read_csv(uploaded_file, encoding='utf-8')
except UnicodeDecodeError:
    try:
        df = pd.read_csv(uploaded_file, encoding='latin-1')
    except UnicodeDecodeError:
        df = pd.read_csv(uploaded_file, encoding='cp1252')
```

**Data Cleaning**:
1. Remove completely empty rows
2. Strip whitespace from column names

**Error Handling**:
- Displays Streamlit error messages
- Returns None on failure

**Example**:
```python
uploaded = st.file_uploader("Upload CSV", type=['csv'])
if uploaded:
    df = load_data(uploaded)
    if df is not None:
        st.write(df.head())
```

---

### validate_data()

```python
def validate_data(df: pd.DataFrame) -> Dict[str, Any]
```

**Description**: Validate data structure and identify issues.

**Parameters**:
- `df` (pd.DataFrame): Loaded data

**Returns**:
```python
{
    'is_valid': bool,           # True if passes validation
    'issues': List[str],        # List of validation issues
    'column_mapping': Dict      # Identified column mappings
}
```

**Validation Checks**:

1. **Non-Empty Data**:
   - Minimum 10 rows required
   - Issue: "Dataset too small (minimum 10 rows required)"

2. **Session ID Column**:
   - Patterns: report_entry_id, session_id, entry_id, id
   - Issue: "No session ID column found"

3. **Identifiable Columns**:
   - Patterns: type, event, action, created, timestamp, time
   - Issue: "No recognizable event or timestamp columns found"

4. **Data Quality**:
   - Check for completely null columns
   - Issue: "Completely empty columns found: {columns}"

**Success Criteria**:
- No issues found → `is_valid = True`

**Example**:
```python
result = validate_data(df)
if result['is_valid']:
    print("Validation passed!")
else:
    for issue in result['issues']:
        print(f"❌ {issue}")
```

---

### apply_color_coding()

```python
def apply_color_coding(df: pd.DataFrame) -> pd.io.formats.style.Styler
```

**Description**: Apply visual styling to results DataFrame.

**Parameters**:
- `df` (pd.DataFrame): Results DataFrame with predictions and scores

**Returns**:
- `Styler`: Styled DataFrame for display

**Color Scheme**:

*Prediction Column*:
```python
'Likely Bot': '#ffcccc'    # Light red
'Likely Human': '#ccffcc'  # Light green
```

*Bot Score Column*:
```python
score > 0.7: '#ff9999', font-weight: bold  # Red, bold
score < 0.3: '#99ff99', font-weight: bold  # Green, bold
0.3 ≤ score ≤ 0.7: '#ffff99'              # Yellow
```

**Numeric Formatting**:

| Column Type | Format | Example |
|------------|--------|---------|
| Score/Ratio | `.3f` | 0.567 |
| Frequency | `.2f` | 12.34 |
| Duration/Seconds | `.1f` | 5.2 |
| Counts | `.0f` | 42 |

**Example**:
```python
styled_df = apply_color_coding(results_df)
st.dataframe(styled_df, use_container_width=True)
```

---

### calculate_summary_stats()

```python
def calculate_summary_stats(results_df: pd.DataFrame) -> Dict[str, Any]
```

**Description**: Calculate summary statistics for results.

**Parameters**:
- `results_df` (pd.DataFrame): Detection results

**Returns**:
```python
{
    # Session counts
    'total_sessions': int,
    'bot_sessions': int,
    'human_sessions': int,
    'bot_percentage': float,

    # Bot score statistics
    'avg_bot_score': float,
    'median_bot_score': float,
    'min_bot_score': float,
    'max_bot_score': float,

    # Feature statistics
    'feature_stats': {
        'feature_name': {
            'mean': float,
            'median': float,
            'std': float
        },
        ...
    }
}
```

**Example**:
```python
stats = calculate_summary_stats(results_df)
print(f"Bot Percentage: {stats['bot_percentage']:.1f}%")
print(f"Average Bot Score: {stats['avg_bot_score']:.3f}")
```

---

### generate_sample_data()

```python
def generate_sample_data(n_sessions: int = 100) -> pd.DataFrame
```

**Description**: Generate synthetic sample data for testing.

**Parameters**:
- `n_sessions` (int): Number of sessions to generate (default: 100)

**Returns**:
- `pd.DataFrame`: Synthetic event-level data

**Generated Columns**:
- `report_entry_id`: Session ID (1 to n_sessions)
- `type`: Event type (open, click, preview)
- `void`: Void indicator (0 or 1)
- `fingerprint`: Device fingerprint
- `user_agent`: Browser user agent
- `created`: Timestamp

**Event Distribution**:
- Opens: 60%
- Clicks: 30%
- Previews: 10%
- Void probability: 10%

**Example**:
```python
sample_df = generate_sample_data(n_sessions=50)
print(sample_df.head())
```

---

### export_results_to_csv()

```python
def export_results_to_csv(results_df: pd.DataFrame) -> str
```

**Description**: Convert results to CSV string.

**Parameters**:
- `results_df` (pd.DataFrame): Results to export

**Returns**:
- `str`: CSV-formatted string

**Example**:
```python
csv_string = export_results_to_csv(results_df)
st.download_button(
    "Download CSV",
    data=csv_string,
    file_name="bot_detection_results.csv",
    mime="text/csv"
)
```

---

### export_results_to_excel()

```python
def export_results_to_excel(results_df: pd.DataFrame) -> bytes
```

**Description**: Convert results to Excel bytes.

**Parameters**:
- `results_df` (pd.DataFrame): Results to export

**Returns**:
- `bytes`: Excel file bytes

**Sheet Name**: "Bot Detection Results"

**Example**:
```python
excel_bytes = export_results_to_excel(results_df)
st.download_button(
    "Download Excel",
    data=excel_bytes,
    file_name="bot_detection_results.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
```

---

## create_model.py - Model Training

### generate_training_data()

```python
def generate_training_data(n_samples: int = 5000) -> pd.DataFrame
```

**Description**: Generate synthetic training data based on real email patterns.

**Parameters**:
- `n_samples` (int): Number of training samples (default: 5000)

**Returns**:
- `pd.DataFrame`: Training data with features and labels

**Bot Patterns** (30% of data):
- Multiple opens (1-8), very few clicks (0-1)
- Void events (1-5 with 70% probability)
- High event frequency (5-30 events/min)
- Brief sessions (0.1-3.0 seconds)
- Multiple user agents (1-4)
- Perfect ratios (40% probability)

**Human Patterns** (70% of data):
- Normal opens (1-4), normal clicks (0-5)
- Rare void events (0-1 with 10% probability)
- Normal activity pace (0.5-8.0 events/min)
- Longer sessions (2-300 seconds)
- Single user agent
- Natural ratios

**Columns Generated**:
- All features from FeatureExtractor
- `is_bot` label (0 or 1)

---

### train_model()

```python
def train_model() -> Tuple[RandomForestClassifier, List[str]]
```

**Description**: Train a Random Forest model for bot detection.

**Returns**:
- `RandomForestClassifier`: Trained model
- `List[str]`: Feature names

**Model Configuration**:
```python
RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    class_weight='balanced'
)
```

**Training Process**:
1. Generate 5000 samples
2. Split 80/20 train/test
3. Train Random Forest
4. Evaluate on test set
5. Print classification report
6. Display feature importance

**Output Metrics**:
- Training accuracy
- Test accuracy
- Precision, Recall, F1-score
- Confusion matrix
- Feature importance

---

### main()

```python
def main() -> None
```

**Description**: Main function to create and save model.

**Process**:
1. Generate training data
2. Train model
3. Save as `email_bot_detector_model.pkl`
4. Save feature list as `model_features.txt`

**Output Files**:
- `email_bot_detector_model.pkl`: Trained model
- `model_features.txt`: Feature names

---

## Data Structures

### Session Features DataFrame

```python
pd.DataFrame({
    'session_id': str,                    # Session identifier
    'num_events': int,                    # Total events
    'num_opens': int,                     # Open events
    'num_clicks': int,                    # Click events
    'num_previews': int,                  # Preview events
    'num_voids': int,                     # Void events
    'unique_user_agents': int,            # Distinct UAs
    'has_multiple_user_agents': bool,     # >1 UA flag
    'unique_fingerprints': int,           # Distinct FPs
    'has_multiple_fingerprints': bool,    # >1 FP flag
    'first_event_time': datetime,         # First timestamp
    'last_event_time': datetime,          # Last timestamp
    'open_duration_sec': float,           # Duration in seconds
    'event_frequency_per_min': float,     # Events per minute
    'events_per_second': float,           # Event rate
    'click_to_open_ratio': float,         # Clicks / Opens
    'void_to_total_ratio': float          # Voids / Total
})
```

### Detection Results DataFrame

```python
pd.DataFrame({
    # All features from Session Features DataFrame
    # Plus:
    'bot_score': float,                   # 0-1 probability
    'prediction': str,                    # "Likely Bot" or "Likely Human"
    'confidence': float,                  # 0-1 confidence
    'detection_reasons': str              # Semicolon-separated
})
```

### Validation Result

```python
{
    'is_valid': bool,                     # Validation passed
    'issues': List[str],                  # Validation issues
    'column_mapping': {                   # Column mappings
        'session_id': str,                # Actual column name
        'event_type': str,
        'timestamp': str,
        'void': str,                      # Optional
        'fingerprint': str,               # Optional
        'user_agent': str                 # Optional
    }
}
```

---

## Constants and Configuration

### Detection Weights (Default)

```python
DEFAULT_WEIGHTS = {
    'void': 0.35,
    'opens_only': 0.25,
    'instant_activity': 0.20,
    'unusual_patterns': 0.15,
    'duration': 0.05
}
```

### Detection Thresholds (Default)

```python
DEFAULT_THRESHOLDS = {
    'frequency': 10.0,         # Events per minute
    'duration': 2.0,           # Seconds
    'instant_threshold': 1.0   # Seconds
}
```

### Classification Threshold

```python
CLASSIFICATION_THRESHOLD = 0.5  # Bot if score > 0.5
```

### Campaign Health Thresholds

```python
CAMPAIGN_THRESHOLDS = {
    'high_open_rate': 0.65,           # 65%
    'medium_open_rate': 0.55,         # 55%
    'low_cto_ratio': 0.02,            # 2%
    'medium_cto_ratio': 0.05,         # 5%
    'high_bot_percentage': 0.50,      # 50%
    'medium_bot_percentage': 0.25     # 25%
}
```

### Benchmark Data

```python
BENCHMARKS = {
    'healthy_campaigns': {
        'open_rate': (0.19, 0.54),          # 19-54%
        'click_to_open': (0.0212, 0.1378)   # 2.12-13.78%
    },
    'bot_inflated_campaigns': {
        'open_rate': (0.68, 0.80),          # 68-80%
        'click_to_open': (0.0012, 0.0374)   # 0.12-3.74%
    }
}
```

### Color Palette

```python
COLORS = {
    'bot': '#ff4444',           # Red
    'human': '#44ff44',         # Green
    'bot_light': '#ffcccc',     # Light red
    'human_light': '#ccffcc',   # Light green
    'uncertain': '#ffff99',     # Yellow
    'primary': '#3366cc'        # Blue
}
```

### File Upload Limits

```python
MAX_FILE_SIZE = 200  # MB (Streamlit default)
SUPPORTED_FORMATS = ['csv', 'xlsx', 'xls']
MIN_ROWS = 10
```

---

**Version**: 1.0
**Last Updated**: December 2025
**Status**: Production Ready
