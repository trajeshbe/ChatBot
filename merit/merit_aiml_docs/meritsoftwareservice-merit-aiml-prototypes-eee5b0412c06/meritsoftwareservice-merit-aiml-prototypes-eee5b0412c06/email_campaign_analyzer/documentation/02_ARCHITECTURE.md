# Email Campaign Analyzer - Architecture Guide

## System Architecture Overview

The Email Campaign Analyzer is built using a modular architecture that separates concerns across data processing, feature extraction, prediction, and presentation layers. This document provides a comprehensive technical overview of the system's architecture, design decisions, and component interactions.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit Frontend                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Data Upload  │  │  Analysis    │  │  Dashboard   │      │
│  │     Tab      │  │     Tab      │  │     Tab      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│                        (app.py)                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  - Request Routing                                    │   │
│  │  - Session State Management                           │   │
│  │  - Visualization Orchestration                        │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                      │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │    Utils       │  │    Feature     │  │     Bot      │  │
│  │  (utils.py)    │  │   Extractor    │  │   Detector   │  │
│  │                │  │(feature_ext... │  │(bot_detect...│  │
│  │ - Load Data    │  │                │  │              │  │
│  │ - Validate     │  │ - Column Map   │  │ - Rule-Based │  │
│  │ - Color Code   │  │ - Aggregate    │  │ - ML Based   │  │
│  │ - Export       │  │ - Calculate    │  │ - Explain    │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │  CSV/XLSX      │  │  Session       │  │  ML Models   │  │
│  │  Input Files   │  │  State Cache   │  │  (.pkl)      │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Application Layer (app.py)

**Responsibility**: User interface, routing, and orchestration

#### Core Functions

##### main()
- **Purpose**: Application entry point
- **Features**:
  - Page configuration (title, icon, layout)
  - Sidebar configuration panel
  - Tab-based interface management
  - Model file upload handling

##### handle_data_upload()
- **Purpose**: Manage file upload and initial processing
- **Workflow**:
  1. Accept CSV/XLSX file upload
  2. Load data using utils.load_data()
  3. Display data preview (first 10 rows)
  4. Show column information
  5. Validate data structure
  6. Extract features via FeatureExtractor
  7. Store in session state

##### handle_analysis(prediction_method, model_file)
- **Purpose**: Execute bot detection analysis
- **Parameters**:
  - `prediction_method`: "Rule-based Scoring" or "ML Classifier"
  - `model_file`: Optional uploaded .pkl model
- **Workflow**:
  1. Retrieve processed data from session state
  2. Initialize BotDetector
  3. Apply selected prediction method
  4. Store results in session state
  5. Display results via display_results()

##### display_results(results)
- **Purpose**: Show detection results with filters
- **Features**:
  - Summary metrics (total, bots, humans, avg score)
  - Filter controls (prediction type, score range, sorting)
  - Color-coded results table
  - Bot detection explanations

##### handle_dashboard()
- **Purpose**: Analytics visualization
- **Visualizations**:
  - Campaign health assessment
  - Bot vs human pie chart
  - Bot score histogram
  - Feature distribution box plots
  - Feature correlation matrix

#### Design Decisions

**Session State Management**
- Stores data across tab navigation
- Keys: 'raw_data', 'processed_data', 'results', 'column_mapping', 'prediction_method'
- Enables stateful interaction without database

**Tab-Based Interface**
- Separates upload, analysis, and dashboard
- Progressive workflow (upload → analyze → visualize)
- Prevents premature analysis attempts

**Error Handling**
- Try-catch blocks for file operations
- Graceful fallback for encoding issues
- User-friendly error messages
- Model compatibility warnings

### 2. Feature Extraction Layer (feature_extractor.py)

**Responsibility**: Transform event-level data to session-level features

#### Class: FeatureExtractor

##### Architecture

```python
class FeatureExtractor:
    def __init__(self):
        self.column_mapping = {}  # Dynamic column identification
```

##### Key Methods

###### extract_features(df)
- **Purpose**: Main extraction pipeline
- **Input**: Raw event-level DataFrame
- **Output**: Session-aggregated features DataFrame
- **Process**:
  1. Identify columns dynamically
  2. Clean and prepare data
  3. Group by session ID
  4. Extract session features

###### _identify_columns(df)
- **Purpose**: Dynamic column name detection
- **Strategy**: Pattern matching with flexible naming
- **Patterns**:
  - Session ID: ['report_entry_id', 'session_id', 'entry_id', 'id']
  - Event Type: ['type', 'event', 'action', 'event_type']
  - Timestamp: ['created', 'timestamp', 'time', 'datetime', 'date']
  - Optional: void, fingerprint, user_agent

**Design Rationale**: No hardcoded column names enables compatibility with various email platforms and export formats.

###### _clean_data(df)
- **Purpose**: Data normalization and type conversion
- **Operations**:
  - Convert timestamps to datetime
  - Fill missing void values with 0
  - Lowercase event types
  - Handle conversion errors gracefully

###### _extract_session_features(df)
- **Purpose**: Aggregate events into session-level metrics
- **Features Extracted**:

**Event Counts**:
- `num_events`: Total events per session
- `num_opens`: Open events
- `num_clicks`: Click events
- `num_previews`: Preview events
- `num_voids`: Void/test link events

**Identity Metrics**:
- `unique_user_agents`: Count of distinct user agents
- `has_multiple_user_agents`: Boolean flag
- `unique_fingerprints`: Count of distinct fingerprints
- `has_multiple_fingerprints`: Boolean flag

**Temporal Features**:
- `first_event_time`: Earliest event timestamp
- `last_event_time`: Latest event timestamp
- `open_duration_sec`: Session duration in seconds
- `event_frequency_per_min`: Events per minute

**Derived Metrics**:
- `events_per_second`: Event rate
- `click_to_open_ratio`: Clicks / Opens
- `void_to_total_ratio`: Void events / Total events

#### Design Decisions

**Session-Based Aggregation**
- Groups events by session ID (report_entry_id)
- Provides holistic view of user behavior
- Enables pattern detection across event sequences

**Null Handling**
- Fills numeric columns with 0
- Prevents errors in downstream processing
- Maintains data integrity

**Minimum Duration**
- Sets minimum 1-second duration
- Prevents division by zero
- Provides reasonable frequency calculations

### 3. Bot Detection Layer (bot_detector.py)

**Responsibility**: Classification logic and scoring algorithms

#### Class: BotDetector

##### Architecture

```python
class BotDetector:
    def __init__(self):
        self.threshold = 0.5  # Binary classification threshold
```

##### Key Methods

###### rule_based_prediction(features_df, weights=None, thresholds=None)

**Purpose**: Enhanced rule-based bot detection

**Default Weights** (Based on Real Campaign Data):
```python
weights = {
    'void': 0.35,              # Primary security software indicator
    'opens_only': 0.25,        # Email predownloading pattern
    'instant_activity': 0.20,  # Rapid automated checking
    'unusual_patterns': 0.15,  # Abnormal behavior
    'duration': 0.05           # Brief sessions
}
```

**Default Thresholds**:
```python
thresholds = {
    'frequency': 10.0,         # Events per minute
    'duration': 2.0,           # Session duration in seconds
    'instant_threshold': 1.0   # Instant clustering threshold
}
```

**Detection Rules**:

**Rule 1: Void Events (35% weight)**
- Detects security software testing void/test links
- Triggered when `num_voids > 0`
- Primary indicator of email security tools

**Rule 2: Opens-Only Pattern (25% weight)**
- Pattern 1: Multiple opens (≥2) with zero clicks
- Pattern 2: Very low click-to-open ratio (<2%)
- Based on real data: Bot campaigns show 0.12-3.74% CTO vs normal 2.12-13.78%

**Rule 3: Instant/Rapid Activity (20% weight)**
- Sub-rule 3a: High event frequency (>10 events/min)
- Sub-rule 3b: Event clustering (<1 second apart)
- Detects automated rapid processing

**Rule 4: Unusual Patterns (15% weight)**
- Multiple user agents (inconsistent identity)
- Perfect engagement ratios (0.5, 1.0, 2.0)
- High void ratio (>30%)

**Rule 5: Brief Sessions (5% weight)**
- Session duration <2 seconds
- Typical of security software quick disconnect

**Bonus Rules**:
- Preview-only activity (email security scanning)
- High open rate campaigns (>65%)
- Minimal engagement patterns

**Scoring Process**:
1. Calculate weighted scores for each rule
2. Normalize to 0-1 range
3. Apply 0.5 threshold for binary classification
4. Generate detection reasons
5. Calculate confidence scores

###### ml_prediction(features_df, model)

**Purpose**: Machine learning-based prediction

**Process**:
1. Extract ML-compatible features
2. Handle missing and infinite values
3. Apply model.predict_proba() or model.predict()
4. Normalize scores to 0-1 range
5. Apply threshold for classification
6. Add confidence scores
7. Fallback to rule-based if errors occur

**Error Handling**:
- Version compatibility checks
- Graceful degradation to rule-based
- User-friendly error messages
- Detailed logging

###### _get_ml_features(df)

**Purpose**: Select appropriate features for ML models

**Exclusions**:
- Non-numeric columns
- Identifier columns (session_id)
- Timestamp columns
- Boolean flags (converted to numeric elsewhere)

**Design Rationale**: Ensures ML models receive clean numeric features without identifiers or temporal data that could cause overfitting.

###### explain_prediction(session_data, prediction_method)

**Purpose**: Generate human-readable explanations

**Explanations Generated**:
- Security software indicators
- Email predownloading patterns
- Engagement anomalies
- Temporal anomalies
- Identity inconsistencies

**Format**: Emoji-prefixed bullet points with context and thresholds

#### Design Decisions

**Data-Driven Weights**
- Based on real campaign analysis
- Calibrated for email security patterns
- Balances precision and recall

**Flexible Thresholds**
- User-customizable via UI
- Enables domain-specific tuning
- Adapts to different campaign types

**Transparent Scoring**
- Detailed detection reasons
- Confidence metrics
- Explainable AI approach

**Dual Method Support**
- Rule-based for interpretability
- ML for custom models
- Automatic fallback for reliability

### 4. Utilities Layer (utils.py)

**Responsibility**: Helper functions for data operations

#### Key Functions

##### load_data(uploaded_file)

**Purpose**: Load CSV/XLSX files with encoding fallback

**Encoding Strategy**:
1. Try UTF-8
2. Fallback to Latin-1
3. Final fallback to CP1252

**File Format Support**:
- CSV: Multiple encoding support
- XLSX/XLS: Excel file support

**Data Cleaning**:
- Remove completely empty rows
- Strip whitespace from column names

##### validate_data(df)

**Purpose**: Ensure data meets minimum requirements

**Validation Checks**:
- Non-empty dataset (minimum 10 rows)
- Session ID column present
- At least some identifiable columns
- No completely null columns

**Output**:
```python
{
    'is_valid': bool,
    'issues': list,
    'column_mapping': dict
}
```

##### apply_color_coding(df)

**Purpose**: Visual styling for results DataFrame

**Color Scheme**:
- Likely Bot: Light red background (#ffcccc)
- Likely Human: Light green background (#ccffcc)
- High bot score (>0.7): Red with bold (#ff9999)
- Low bot score (<0.3): Green with bold (#99ff99)
- Uncertain (0.3-0.7): Yellow (#ffff99)

**Formatting**:
- Score columns: 3 decimal places
- Ratio columns: 3 decimal places
- Frequency columns: 2 decimal places
- Duration columns: 1 decimal place
- Count columns: 0 decimal places

##### calculate_summary_stats(results_df)

**Purpose**: Generate summary statistics

**Statistics Calculated**:
- Total/bot/human session counts
- Bot percentage
- Bot score statistics (mean, median, min, max)
- Feature-level statistics (mean, median, std)

#### Design Decisions

**Encoding Resilience**
- Multiple fallback encodings
- Handles international characters
- Prevents encoding errors from blocking analysis

**Flexible Validation**
- Pattern-based column matching
- Minimal hard requirements
- Informative error messages

**Visual Clarity**
- Color coding for quick scanning
- Appropriate numeric precision
- Professional styling

## Data Flow Architecture

### Upload → Processing Flow

```
1. User uploads CSV/XLSX file
   ↓
2. load_data() reads file with encoding fallback
   ↓
3. validate_data() checks structure
   ↓
4. FeatureExtractor.extract_features()
   ├─ _identify_columns() → Dynamic column mapping
   ├─ _clean_data() → Type conversion and normalization
   └─ _extract_session_features() → Aggregation
   ↓
5. Store in session_state['processed_data']
```

### Analysis Flow

```
1. User selects prediction method
   ↓
2. BotDetector initialized
   ↓
3. Prediction method executed
   ├─ Rule-based: rule_based_prediction()
   │  ├─ Apply weighted rules
   │  ├─ Calculate bot scores
   │  ├─ Generate detection reasons
   │  └─ Binary classification
   │
   └─ ML-based: ml_prediction()
      ├─ Load .pkl model
      ├─ Extract ML features
      ├─ Apply model.predict_proba()
      ├─ Normalize scores
      └─ Fallback to rule-based if error
   ↓
4. Store in session_state['results']
   ↓
5. Display results with filters and visualizations
```

### Dashboard Flow

```
1. Retrieve results from session state
   ↓
2. Calculate campaign-level metrics
   ├─ Open rate
   ├─ Click-to-open ratio
   └─ Bot percentage
   ↓
3. Generate visualizations
   ├─ Pie chart (distribution)
   ├─ Histogram (bot scores)
   ├─ Box plots (features)
   └─ Correlation matrix
   ↓
4. Display with Plotly
```

## State Management

### Session State Schema

```python
st.session_state = {
    'raw_data': pd.DataFrame,           # Original uploaded data
    'processed_data': pd.DataFrame,      # Session-aggregated features
    'results': pd.DataFrame,             # Detection results with scores
    'column_mapping': dict,              # Column name mapping
    'prediction_method': str             # Selected method
}
```

### State Lifecycle

1. **Upload Tab**: Populates 'raw_data', 'processed_data', 'column_mapping'
2. **Analysis Tab**: Populates 'results', 'prediction_method'
3. **Dashboard Tab**: Reads 'results' for visualization
4. **Session Reset**: Occurs on page refresh or new upload

## Scalability Considerations

### Performance Optimizations

**Data Processing**:
- Pandas vectorized operations
- Efficient groupby aggregations
- Minimal intermediate copies

**UI Responsiveness**:
- Spinner indicators for long operations
- Progressive data loading
- Streamlit caching (when applicable)

### Limitations

**File Size**:
- Streamlit upload limit: 200MB default
- Memory constraints: RAM-limited
- Recommended: <100K sessions per analysis

**Computation**:
- Single-threaded processing
- No distributed computing
- Suitable for typical campaign sizes

### Future Scalability

**Potential Enhancements**:
- Batch processing for large files
- Database integration for historical data
- Caching frequently-used features
- Parallel processing for ML predictions

## Security Considerations

### Data Privacy

**No Data Persistence**:
- Files not saved to disk
- Session state cleared on refresh
- No database storage

**Model Security**:
- User-uploaded models executed in sandbox
- Version compatibility checks
- Error handling prevents code injection

### Input Validation

**File Upload**:
- Type restrictions (.csv, .xlsx only)
- Size limits enforced
- Malformed data handling

**Data Validation**:
- Schema validation
- Type checking
- Null value handling

## Technology Decisions

### Why Streamlit?

**Advantages**:
- Rapid prototyping
- Python-native development
- Built-in state management
- Easy deployment

**Trade-offs**:
- Limited customization vs Flask/Django
- Single-threaded execution
- Session-based state (no persistence)

### Why Pandas?

**Advantages**:
- Industry standard for data manipulation
- Rich feature set for aggregation
- Excellent CSV/Excel support
- Integration with NumPy and scikit-learn

### Why Plotly?

**Advantages**:
- Interactive visualizations
- Professional appearance
- Streamlit integration
- Responsive charts

**Alternative Considered**: Matplotlib (less interactive)

### Why Rule-Based + ML?

**Rationale**:
- Rule-based: Interpretable, domain-specific, no training data required
- ML: Adaptable, can learn complex patterns, customizable
- Dual approach: Best of both worlds with fallback

## Extensibility

### Adding New Features

**New Detection Rules**:
1. Add feature calculation in FeatureExtractor
2. Implement detection logic in BotDetector.rule_based_prediction()
3. Add weight parameter in UI
4. Update explanation in explain_prediction()

**New Visualizations**:
1. Add to handle_dashboard() in app.py
2. Use Plotly Express or Graph Objects
3. Follow existing color scheme
4. Add explanatory text

**New File Formats**:
1. Extend load_data() in utils.py
2. Add type check in file_uploader
3. Implement format-specific parsing
4. Update validation logic

### Plugin Architecture

**Future Consideration**: Plugin system for custom detectors

```python
class CustomDetector:
    def detect(self, features_df):
        # Custom logic
        return results_df

# Register and use
BotDetector.register_plugin(CustomDetector)
```

## Error Handling Strategy

### Error Categories

**User Errors**:
- Invalid file format → Clear message with examples
- Missing required columns → List expected columns
- Insufficient data → Explain minimum requirements

**System Errors**:
- File encoding issues → Try multiple encodings
- Model compatibility → Fallback to rule-based
- Memory issues → Recommend smaller file

**ML Model Errors**:
- Version mismatch → Detailed compatibility message
- Missing features → Feature alignment attempt
- Prediction failure → Automatic fallback

### Logging Strategy

**Current**: Print statements and Streamlit messages

**Future Enhancement**: Structured logging
```python
import logging

logger = logging.getLogger(__name__)
logger.info("Features extracted: %d sessions", len(features))
logger.error("Model prediction failed: %s", error)
```

## Testing Considerations

### Unit Testing

**Recommended Test Coverage**:
- FeatureExtractor._identify_columns()
- BotDetector.rule_based_prediction()
- Utils validation functions
- Color coding logic

### Integration Testing

**Test Scenarios**:
- End-to-end file upload → results
- Rule-based vs ML predictions
- Various file formats and encodings
- Edge cases (single session, missing columns)

### Test Data

**Sample Datasets**:
- attached_assets/sample1.txt (requirements)
- Generate synthetic data with create_model.py
- Real anonymized campaign data

## Deployment Architecture

### Local Development

```
Python Environment → Streamlit → Browser
     ↑
  app.py + modules
```

### Streamlit Cloud

```
GitHub Repo → Streamlit Cloud → Public URL
    ↑
  Automatic deployment on push
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

### Production Considerations

**Requirements**:
- Environment variables for configuration
- Logging to external service
- Error monitoring (Sentry)
- Usage analytics
- Rate limiting for API access

## Version Control Strategy

### File Structure

```
email_campaign_analyzer/
├── app.py                          # Main application
├── feature_extractor.py            # Feature engineering
├── bot_detector.py                 # Detection logic
├── utils.py                        # Helper functions
├── create_model.py                 # Model training
├── pyproject.toml                  # Dependencies
├── email_bot_detector_model.pkl    # Pre-trained model
├── model_features.txt              # Feature list
├── .streamlit/
│   └── config.toml                 # Streamlit config
├── attached_assets/
│   └── sample1.txt                 # Documentation
└── documentation/
    ├── 01_OVERVIEW.md
    ├── 02_ARCHITECTURE.md
    ├── 03_API_REFERENCE.md
    ├── 04_USER_GUIDE.md
    └── 05_DEPLOYMENT.md
```

### Branching Strategy

**Recommended**:
- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: New features
- `hotfix/*`: Critical fixes

## Monitoring and Observability

### Metrics to Track

**Usage Metrics**:
- Files uploaded per day
- Average file size
- Prediction method distribution
- Error rates

**Performance Metrics**:
- Feature extraction time
- Prediction time
- Dashboard render time
- Memory usage

**Business Metrics**:
- Average bot percentage detected
- Most common detection patterns
- User retention
- Export frequency

### Future Enhancements

**Observability Stack**:
- Prometheus for metrics
- Grafana for dashboards
- ELK stack for log analysis
- Sentry for error tracking

---

**Version**: 1.0
**Last Updated**: December 2025
**Status**: Production Ready
