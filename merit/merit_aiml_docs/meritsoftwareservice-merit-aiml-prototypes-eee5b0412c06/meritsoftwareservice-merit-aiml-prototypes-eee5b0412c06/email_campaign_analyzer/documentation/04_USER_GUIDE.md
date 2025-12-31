# Email Campaign Analyzer - User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Understanding Your Data](#understanding-your-data)
3. [Uploading Data](#uploading-data)
4. [Choosing a Detection Method](#choosing-a-detection-method)
5. [Running Analysis](#running-analysis)
6. [Interpreting Results](#interpreting-results)
7. [Using the Dashboard](#using-the-dashboard)
8. [Customizing Detection](#customizing-detection)
9. [Exporting Results](#exporting-results)
10. [Common Use Cases](#common-use-cases)
11. [Troubleshooting](#troubleshooting)
12. [Best Practices](#best-practices)
13. [FAQs](#faqs)

---

## Getting Started

### What You'll Need

**Required**:
- Email campaign tracking data (CSV or XLSX format)
- Web browser (Chrome, Firefox, Safari, or Edge)
- Basic understanding of your email campaign metrics

**Optional**:
- Pre-trained machine learning model (.pkl file)
- Campaign performance benchmarks for comparison

### Quick Start Guide

1. **Launch the Application**
   - Open your web browser
   - Navigate to the application URL
   - You'll see the "Bot Detection Assistant" interface

2. **Upload Your Data**
   - Go to the "Data Upload" tab
   - Click "Choose a CSV or XLSX file"
   - Select your campaign data file
   - Wait for data preview to load

3. **Run Detection**
   - Navigate to the "Analysis" tab
   - Keep default "Rule-based Scoring" method
   - Click or wait for automatic analysis
   - Review the results table

4. **View Insights**
   - Go to the "Dashboard" tab
   - Check campaign health assessment
   - Explore visualizations
   - Compare to benchmarks

### First-Time Setup

**No installation required** if accessing a hosted instance. For local setup:

```bash
# Install dependencies
pip install streamlit pandas numpy plotly scikit-learn joblib openpyxl

# Run the application
streamlit run app.py

# Open browser to displayed URL (typically http://localhost:8501)
```

---

## Understanding Your Data

### Required Data Structure

Your data should contain **event-level tracking** from your email campaign. Each row represents a single event (open, click, preview, etc.).

#### Minimum Required Columns

The system uses **flexible column naming**. Your file needs at least:

**1. Session Identifier** (one of):
- `report_entry_id`
- `session_id`
- `entry_id`
- `id`

**2. Event Type** (one of):
- `type`
- `event`
- `action`
- `event_type`

**3. Timestamp** (one of):
- `created`
- `timestamp`
- `time`
- `datetime`
- `date`

#### Optional But Recommended Columns

**Void Indicator** (one of):
- `void`
- `is_void`

Values: 0 (normal) or 1 (void/test link)

**Device Fingerprint** (one of):
- `fingerprint`
- `fp`
- `device_id`

**User Agent** (one of):
- `user_agent`
- `useragent`
- `agent`
- `ua`

### Example Data Format

#### CSV Example

```csv
report_entry_id,type,created,void,user_agent,fingerprint
12345,open,2024-01-15 09:30:00,0,Mozilla/5.0...,fp_abc123
12345,click,2024-01-15 09:30:15,0,Mozilla/5.0...,fp_abc123
12346,open,2024-01-15 09:31:00,1,SecurityBot/1.0,fp_xyz789
12346,open,2024-01-15 09:31:01,0,SecurityBot/1.0,fp_xyz789
```

#### Expected Event Types

Common event types the system recognizes:
- `open` / `email_open` / `opened` - Email opened
- `click` / `clicked` / `link_click` - Link clicked
- `preview` / `previewed` - Email previewed
- Any custom types (counted as events)

### Data Quality Checklist

Before uploading, ensure:
- ✅ Minimum 10 rows (preferably 100+ for meaningful analysis)
- ✅ Session IDs present and consistent
- ✅ Timestamps in parseable format (ISO 8601 recommended)
- ✅ Event types consistent and lowercase-compatible
- ✅ No completely empty columns
- ✅ File size under 200MB

---

## Uploading Data

### Step-by-Step Upload Process

#### 1. Navigate to Data Upload Tab

Click on the **"Data Upload"** tab at the top of the interface.

#### 2. Choose Your File

Click the **"Choose a CSV or XLSX file"** button and select your data file.

**Supported Formats**:
- CSV (.csv) - Multiple encodings supported (UTF-8, Latin-1, CP1252)
- Excel (.xlsx, .xls) - Standard Excel formats

#### 3. Review Data Preview

After upload, you'll see:

**Data Preview Section**:
- First 10 rows of your data
- All columns displayed
- Quick visual check of data quality

**Column Information Table**:
- Column names
- Data types
- Non-null counts
- Null counts

#### 4. Check Validation Status

The system automatically validates your data:

**Success Message** (Green):
```
✅ Data validation passed!
✅ Features extracted! X unique sessions found.
```

**Error Message** (Red):
```
❌ Data validation failed:
• No session ID column found (expected: report_entry_id, session_id, ...)
• Dataset too small (minimum 10 rows required)
```

#### 5. Review Processed Features

After successful validation, you'll see a **"Processed Features Preview"** showing:
- Session-level aggregated data
- All extracted features
- Number of unique sessions

### Handling Upload Errors

#### File Format Issues

**Problem**: "Unsupported file format"
**Solution**:
- Ensure file extension is .csv, .xlsx, or .xls
- Save Excel files in compatible format (not .xlsm or .xlsb)

#### Encoding Issues

**Problem**: Strange characters in text
**Solution**:
- System automatically tries UTF-8, Latin-1, and CP1252
- If issues persist, save CSV as UTF-8 in Excel or text editor

#### File Size Issues

**Problem**: File won't upload or browser freezes
**Solution**:
- Streamlit limit is typically 200MB
- For larger files, filter to specific campaigns or date ranges
- Consider splitting into multiple analyses

#### Column Not Found

**Problem**: "No session ID column found"
**Solution**:
- Check that at least one column matches expected patterns
- Rename columns if needed: `session_id`, `report_entry_id`, `entry_id`, or `id`
- Column names are case-insensitive

---

## Choosing a Detection Method

The system offers two detection approaches. Choose based on your needs.

### Rule-Based Scoring (Recommended)

**Best For**:
- First-time users
- Understanding why sessions are flagged
- Email security software detection
- No ML expertise required

**How It Works**:
- Applies weighted rules based on real campaign data
- Detects patterns like void testing, predownloading, rapid activity
- Provides detailed explanations for each detection

**Advantages**:
- ✅ Fully transparent and explainable
- ✅ No training data needed
- ✅ Calibrated for email security patterns
- ✅ Customizable weights and thresholds
- ✅ Works immediately

**To Use**:
1. Select **"Rule-based Scoring"** in the sidebar
2. Optionally customize weights and thresholds
3. Proceed to Analysis tab

### ML Classifier (Advanced)

**Best For**:
- Users with trained models
- Custom detection patterns
- Large-scale operations
- Advanced users

**How It Works**:
- Loads pre-trained .pkl model file
- Applies machine learning predictions
- Falls back to rule-based if errors occur

**Advantages**:
- ✅ Can learn complex patterns
- ✅ Customizable to your data
- ✅ Potentially higher accuracy with good training

**Requirements**:
- Trained model file (.pkl format)
- Model trained with scikit-learn 1.7.0
- Compatible features

**To Use**:
1. Select **"ML Classifier (.pkl model)"** in sidebar
2. Download sample model (optional - for testing)
3. Upload your trained model (.pkl file)
4. Proceed to Analysis tab

### Comparison Table

| Feature | Rule-Based | ML Classifier |
|---------|-----------|---------------|
| Ease of Use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Explainability | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Setup Time | Instant | Requires training |
| Customization | Weights/Thresholds | Full model retraining |
| Accuracy | High for email security | Varies by training |
| Dependencies | None | Trained model |

---

## Running Analysis

### Rule-Based Analysis

#### 1. Configure Detection (Optional)

Expand **"Customize Detection Weights"** to adjust:

**Primary Indicators**:
- **Void Link Testing** (0.0 - 0.5, default 0.35)
  - Weight for security software testing links
  - Increase if void events are strong indicator

- **Email Predownloading** (0.0 - 0.5, default 0.25)
  - Weight for opens without clicks
  - Increase if low engagement is common bot pattern

- **Instant Activity** (0.0 - 0.5, default 0.20)
  - Weight for rapid/clustered events
  - Increase if bots act very quickly

- **Unusual Patterns** (0.0 - 0.3, default 0.15)
  - Weight for perfect ratios and multiple identities
  - Adjust based on normal user behavior variance

- **Brief Sessions** (0.0 - 0.2, default 0.05)
  - Weight for very short sessions
  - Increase if session duration is reliable indicator

**Thresholds**:
- **Rapid Activity Threshold** (5-30 events/min, default 10)
  - Events per minute considered automated
  - Lower = more sensitive, Higher = less sensitive

- **Brief Session Threshold** (1-10 seconds, default 2)
  - Duration below which suggests automation
  - Lower = more aggressive detection

#### 2. Review Detection Strategy

The **"Detection Strategy Overview"** explains:
- Real campaign data benchmarks
- Detection patterns
- Campaign-level indicators

**Benchmarks**:
- **Normal Campaigns**: 19-54% opens, 2.12-13.78% click-to-open
- **Bot-Inflated Campaigns**: 68-80% opens, 0.12-3.74% click-to-open

#### 3. Execute Analysis

The system automatically:
1. Applies weighted rules to each session
2. Calculates bot scores (0-1)
3. Classifies as "Likely Bot" or "Likely Human"
4. Generates detection reasons
5. Displays results

### ML-Based Analysis

#### 1. Upload Model

- Click **"Upload trained model (.pkl)"** in sidebar
- Select your .pkl file
- Wait for success message

**Compatibility Note**: Model must be trained with scikit-learn 1.7.0

#### 2. Execute Analysis

The system automatically:
1. Loads the model
2. Extracts compatible features
3. Applies model predictions
4. Normalizes scores to 0-1
5. Displays results

**Error Handling**: If model incompatible, automatically falls back to rule-based

---

## Interpreting Results

### Summary Metrics

At the top of the Analysis tab, you'll see:

**Total Sessions**:
- Total unique sessions analyzed
- Based on session ID grouping

**Likely Bots**:
- Number classified as bots
- Percentage of total (green delta)

**Likely Humans**:
- Number classified as humans
- Percentage of total (green delta)

**Avg Bot Score**:
- Mean bot probability across all sessions
- 0 = definitely human, 1 = definitely bot
- Typical ranges: <0.3 (mostly human), >0.7 (mostly bot)

### Results Table

#### Column Descriptions

**Session Identification**:
- `session_id`: Unique session identifier from your data

**Event Counts**:
- `num_events`: Total events in session
- `num_opens`: Number of open events
- `num_clicks`: Number of click events
- `num_previews`: Number of preview events
- `num_voids`: Number of void/test link events

**Identity Metrics**:
- `unique_user_agents`: Count of different user agents
- `has_multiple_user_agents`: True if >1 user agent
- `unique_fingerprints`: Count of different fingerprints
- `has_multiple_fingerprints`: True if >1 fingerprint

**Temporal Metrics**:
- `first_event_time`: Timestamp of first event
- `last_event_time`: Timestamp of last event
- `open_duration_sec`: Session duration in seconds
- `event_frequency_per_min`: Events per minute rate

**Derived Metrics**:
- `events_per_second`: Event rate
- `click_to_open_ratio`: Clicks divided by opens
- `void_to_total_ratio`: Void events divided by total

**Detection Results**:
- `bot_score`: Probability score (0-1)
- `prediction`: "Likely Bot" or "Likely Human"
- `confidence`: Confidence in prediction (0-1)
- `detection_reasons`: Why flagged (semicolon-separated)

#### Color Coding

**Prediction Column**:
- 🔴 Light Red: Likely Bot
- 🟢 Light Green: Likely Human

**Bot Score Column**:
- 🔴 Red + Bold: High bot score (>0.7)
- 🟡 Yellow: Uncertain (0.3-0.7)
- 🟢 Green + Bold: Low bot score (<0.3)

### Filtering Results

Use filters to focus on specific sessions:

**By Prediction**:
- **All**: Show all sessions
- **Likely Bot**: Only bot sessions
- **Likely Human**: Only human sessions

**By Bot Score**:
- **Min Bot Score**: Minimum score to display (0.0-1.0)
- **Max Bot Score**: Maximum score to display (0.0-1.0)
- Example: 0.7-1.0 shows only high-confidence bots

**Sorting**:
- **Sort by**: Choose metric to sort
- **Order**: Ascending or Descending
- Tip: Sort by `bot_score` descending to see most suspicious sessions first

### Bot Detection Explanations

For sessions flagged as "Likely Bot", expand the explanation cards to see why:

**Example Explanations**:

🔍 **Void Link Testing**
- "Security software detected: 3 void/test link events"
- Indicates email security tools testing link safety

📧 **Email Predownloading**
- "Email predownloading pattern: 5 opens with no clicks"
- "Extremely low engagement: 0.8% click-to-open ratio"
- Indicates automated email content fetching

⚡ **Rapid Activity**
- "Rapid automated activity: 25.3 events/min"
- Indicates events happening too fast for humans

🤖 **Instant Clustering**
- "Instant event cluster: 4 events in 0.3 seconds"
- Indicates multiple events nearly simultaneous

⏱️ **Brief Sessions**
- "Brief session: 1.2 seconds (security software quick disconnect)"
- Indicates automated tool disconnecting quickly

🔄 **Multiple Identities**
- "Multiple identities: 3 different user agents"
- Indicates inconsistent identity markers

📊 **Perfect Ratios**
- "Perfect ratio pattern: 1.0 click-to-open ratio"
- Indicates unnaturally precise behavior

### Understanding Bot Scores

**Score Interpretation**:

| Score Range | Interpretation | Typical Pattern |
|-------------|----------------|-----------------|
| 0.0 - 0.2 | Very likely human | Normal engagement, varied behavior |
| 0.2 - 0.4 | Probably human | Some suspicious signals, mostly normal |
| 0.4 - 0.6 | Uncertain | Mixed signals, manual review recommended |
| 0.6 - 0.8 | Probably bot | Multiple bot indicators present |
| 0.8 - 1.0 | Very likely bot | Strong bot patterns, high confidence |

**What Drives Scores Higher**:
- Void events present (+35%)
- Multiple opens, no clicks (+25%)
- Very low click-to-open ratio (<2%) (+17.5%)
- Rapid activity (>10 events/min) (+20%)
- Instant event clustering (<1 sec apart) (+20%)
- Multiple user agents (+15%)
- Perfect engagement ratios (+15%)
- Brief session (<2 seconds) (+5%)
- Campaign-level patterns (+10-27%)

---

## Using the Dashboard

### Campaign Health Assessment

Located at the top of the Dashboard tab, this section provides overall campaign quality indicators.

#### Campaign Open Rate

**Metric**: (Sessions with opens / Total sessions) × 100

**Status Indicators**:
- 🟢 **Healthy Range** (≤55%)
  - Normal human engagement levels
  - Typical of genuine campaigns

- 🟠 **Potentially Inflated** (55-65%)
  - May have some bot activity
  - Review bot detection results

- 🔴 **Likely Bot-Inflated** (>65%)
  - Strong indicator of security software
  - Compare to benchmark: Normal campaigns 19-54%

**Interpretation**:
- High open rates aren't always good - may indicate bot inflation
- Compare to your historical campaigns
- Consider industry benchmarks

#### Click-to-Open Ratio

**Metric**: (Total clicks / Total opens) × 100

**Status Indicators**:
- 🟢 **Healthy Range** (≥5%)
  - Good engagement quality
  - Normal human click behavior

- 🟠 **Below Normal** (2-5%)
  - Lower than typical engagement
  - May indicate some bot opens

- 🔴 **Very Low (Bot Pattern)** (<2%)
  - Strong bot inflation indicator
  - Compare to benchmark: Normal campaigns 2.12-13.78%

**Interpretation**:
- Low CTO with high opens suggests bots opening without engaging
- Bot-inflated campaigns show 0.12-3.74% CTO
- Focus on improving engagement for human sessions

#### Bot Detection Rate

**Metric**: (Bot sessions / Total sessions) × 100

**Status Indicators**:
- 🟢 **Low Bot Activity** (≤25%)
  - Most sessions are human
  - Campaign health is good

- 🟠 **Moderate Bot Activity** (25-50%)
  - Significant bot presence
  - Review detection patterns

- 🔴 **High Bot Activity** (>50%)
  - Majority sessions are bots
  - Campaign severely impacted

**Action Items by Status**:
- **Low**: Focus on optimizing human engagement
- **Moderate**: Investigate bot sources, consider list cleaning
- **High**: Urgent list review, check email security practices

### Visualizations

#### 1. Bot vs Human Distribution (Pie Chart)

**What It Shows**:
- Proportion of bot vs human sessions
- Visual representation of detection results

**How to Use**:
- Quick assessment of campaign contamination
- Hover for exact counts and percentages
- Compare across different campaigns

**Interpretation**:
- Ideal: 80%+ human (green), <20% bot (red)
- Concerning: 50/50 or bot majority
- Action: If >50% bot, urgent list cleaning needed

#### 2. Bot Score Distribution (Histogram)

**What It Shows**:
- Frequency distribution of bot scores
- Vertical red line at threshold (0.5)

**How to Use**:
- See score clustering patterns
- Identify clearly bot vs clearly human sessions
- Spot ambiguous middle range

**Patterns to Notice**:
- **Bimodal distribution**: Clear separation of bots (right) and humans (left) - Good
- **Centered around 0.5**: Many uncertain sessions - May need threshold tuning
- **Heavy right tail**: Lots of high-confidence bots - Campaign issues
- **Heavy left tail**: Mostly human - Healthy campaign

#### 3. Feature Distribution Box Plots (2×2 Grid)

**Metrics Displayed**:
1. **Event Frequency** (events per minute)
2. **Session Duration** (seconds)
3. **Number of Events** (count)
4. **Void Events** (count)

**How to Read**:
- Red boxes: Likely Bot sessions
- Green boxes: Likely Human sessions
- Box shows interquartile range (25th-75th percentile)
- Line in box is median
- Whiskers show min/max (excluding outliers)
- Dots are outliers

**What to Look For**:
- **Large separation**: Clear bot vs human distinction - Good detection
- **Overlap**: Similar patterns - Ambiguous cases
- **Outliers**: Unusual sessions worth investigating

**Example Insights**:
- Bots often have higher event frequency (red box higher)
- Bots often have shorter duration (red box lower)
- Bots may have more void events (red box higher)

#### 4. Feature Correlation Matrix (Heatmap)

**What It Shows**:
- Correlation between all numeric features
- Red = positive correlation, Blue = negative correlation
- Intensity shows strength

**How to Use**:
- Understand feature relationships
- Identify redundant features
- Spot unexpected patterns

**Common Patterns**:
- `num_opens` and `num_events`: Strong positive (expected)
- `open_duration_sec` and `event_frequency_per_min`: Negative (expected - longer sessions have lower frequency)
- `bot_score` and `num_voids`: Positive (void events increase bot score)

### Benchmark Comparison

**Reference Table**:

| Campaign Type | Open Rate | Click-to-Open Ratio |
|--------------|-----------|---------------------|
| Healthy Campaigns | 19-54% | 2.12-13.78% |
| Bot-Inflated Campaigns | 68-80% | 0.12-3.74% |

**How to Use**:
1. Compare your metrics to benchmarks
2. If metrics match "Bot-Inflated" pattern, review:
   - Bot detection results
   - Email list quality
   - Email security software impact
3. If metrics match "Healthy" pattern:
   - Focus on human engagement optimization
   - Monitor for changes over time

---

## Customizing Detection

### When to Customize

**Scenarios**:
- Default weights don't match your campaign patterns
- You want more or less aggressive detection
- Specific indicators are more reliable in your context
- Testing different configurations

### Adjusting Weights

**Access**: Expand "Customize Detection Weights" in Analysis tab

#### Weight Parameters

**Void Link Testing** (0.0 - 0.5, default 0.35):
- **Increase (0.4-0.5)** if:
  - Void events strongly indicate bots in your campaigns
  - You have many confirmed bot sessions with void events
  - Few false positives with current setting

- **Decrease (0.2-0.3)** if:
  - Some humans trigger void events
  - Too many false positives
  - Void events less reliable indicator

**Email Predownloading** (0.0 - 0.5, default 0.25):
- **Increase (0.3-0.4)** if:
  - Low click rates strongly indicate bots
  - Campaign focuses on click-through engagement
  - Few legitimate "opener-only" users

- **Decrease (0.15-0.2)** if:
  - Many humans open without clicking (newsletter format)
  - Content doesn't require clicks
  - High false positives on low engagement

**Instant Activity** (0.0 - 0.5, default 0.20):
- **Increase (0.25-0.35)** if:
  - Bots consistently act very quickly
  - Speed is reliable indicator
  - Humans engage more slowly

- **Decrease (0.10-0.15)** if:
  - Some humans click rapidly
  - Mobile users act quickly
  - Too many fast humans flagged

**Unusual Patterns** (0.0 - 0.3, default 0.15):
- **Increase (0.20-0.25)** if:
  - Multiple user agents common in bots
  - Perfect ratios frequently appear
  - Pattern variations are reliable

- **Decrease (0.05-0.10)** if:
  - Users legitimately switch devices
  - Natural behavior varies widely
  - High false positive rate

**Brief Sessions** (0.0 - 0.2, default 0.05):
- **Increase (0.10-0.15)** if:
  - Session duration very reliable indicator
  - Humans typically engage longer
  - Quick exits rare for humans

- **Decrease (0.01-0.03)** if:
  - Some human sessions are brief
  - Mobile users have short sessions
  - Duration less predictive

### Adjusting Thresholds

**Rapid Activity Threshold** (5-30 events/min, default 10):
- **Lower (5-8)**: More sensitive - flags more rapid activity
  - Use if bots act very quickly
  - Increases bot detection
  - May increase false positives

- **Higher (12-20)**: Less sensitive - allows faster activity
  - Use if humans can act quickly
  - Reduces false positives
  - May miss some bots

**Brief Session Threshold** (1-10 seconds, default 2):
- **Lower (1-1.5)**: More aggressive - only very brief sessions flagged
  - Use if humans sometimes disconnect quickly
  - Reduces false positives
  - May miss bots with slightly longer sessions

- **Higher (3-5)**: More lenient - longer sessions still flagged
  - Use if bot sessions consistently brief
  - Increases bot detection
  - May flag quick human sessions

### Testing Different Configurations

**Recommended Approach**:
1. Start with defaults
2. Review results and false positives/negatives
3. Adjust one weight at a time
4. Re-run analysis
5. Compare results
6. Iterate until satisfied

**Documentation**:
- Record configurations that work well
- Note campaign-specific patterns
- Share learnings across team

---

## Exporting Results

### Export Options

Currently, results can be exported by:

1. **Copy-Paste from Table**:
   - Select rows in results table
   - Copy to clipboard
   - Paste into Excel or other tools

2. **Screenshot Dashboard**:
   - Use browser screenshot tools
   - Capture visualizations
   - Include in reports

3. **Manual Export** (via code):
   - Use utility functions: `export_results_to_csv()` or `export_results_to_excel()`
   - Add download button to interface if needed

### What to Export

**For Analysis**:
- Complete results table with all features
- Bot scores and predictions
- Detection reasons

**For Reporting**:
- Summary metrics
- Dashboard visualizations
- Campaign health assessment
- Benchmark comparisons

**For Further Processing**:
- Session IDs of bots for list cleaning
- Human sessions for engagement analysis
- Feature data for custom modeling

---

## Common Use Cases

### 1. Campaign Performance Analysis

**Goal**: Understand true engagement in completed campaign

**Steps**:
1. Export campaign data from email platform
2. Upload to bot detector
3. Run rule-based analysis
4. Review campaign health metrics
5. Filter to human sessions only
6. Calculate true engagement rates
7. Compare to total campaign metrics

**Key Insights**:
- True open rate = Human opens / Total recipients
- True click rate = Human clicks / Total recipients
- Engagement quality = Human CTO ratio
- Bot contamination percentage

### 2. Email List Cleaning

**Goal**: Identify and remove bot/security software addresses

**Steps**:
1. Upload campaign data
2. Run bot detection
3. Filter to "Likely Bot" with score >0.7
4. Review detection reasons
5. Export bot session IDs
6. Map to email addresses in your platform
7. Segment or remove from active lists

**Considerations**:
- Use high confidence threshold (0.7-0.8+)
- Review a sample before mass removal
- Consider separate segment for bots vs removal
- Monitor impact on future campaigns

### 3. A/B Test Validation

**Goal**: Ensure test groups have clean, comparable data

**Steps**:
1. Run bot detection on both groups
2. Compare bot percentages
3. If similar, proceed with comparison
4. If different, filter to human sessions
5. Re-run statistical tests on human-only data
6. Ensure valid conclusions

**Why It Matters**:
- Bots can skew test results
- Uneven bot distribution invalidates tests
- Human-only comparison more reliable

### 4. Deliverability Diagnosis

**Goal**: Understand if security software is checking emails

**Steps**:
1. Upload data from campaign with suspected deliverability issues
2. Run bot detection
3. Check campaign open rate
4. Review void event patterns
5. Analyze instant activity patterns
6. Identify security software signatures

**Red Flags**:
- High open rates (>65%) with low engagement
- Many void events
- Instant event clustering
- User agents matching security software

### 5. Benchmark Establishment

**Goal**: Create baseline metrics for future comparison

**Steps**:
1. Analyze multiple campaigns
2. Record bot percentages
3. Track true engagement rates
4. Note seasonal patterns
5. Establish acceptable ranges
6. Use for ongoing monitoring

**Metrics to Track**:
- Average bot percentage by campaign type
- True open rates by audience segment
- True click rates by content type
- Campaign health score trends

### 6. Platform Comparison

**Goal**: Compare email service providers or sending methods

**Steps**:
1. Run same campaign through different platforms
2. Analyze bot detection results for each
3. Compare bot percentages
4. Review security software patterns
5. Identify platform-specific issues

**Comparison Metrics**:
- Bot percentage
- Security software detection rate
- True engagement rates
- Campaign health scores

---

## Troubleshooting

### Upload Issues

**Problem**: File won't upload
- **Solution 1**: Check file size (<200MB)
- **Solution 2**: Try different browser
- **Solution 3**: Check file isn't corrupted (open in Excel first)
- **Solution 4**: Remove special characters from filename

**Problem**: "Unsupported file format" error
- **Solution 1**: Ensure .csv, .xlsx, or .xls extension
- **Solution 2**: Re-save in Excel as .xlsx
- **Solution 3**: Check file isn't password protected

**Problem**: "No session ID column found"
- **Solution 1**: Check column names match expected patterns
- **Solution 2**: Rename column to "session_id" or "report_entry_id"
- **Solution 3**: Review column mapping in error message

### Analysis Issues

**Problem**: All sessions flagged as bots
- **Cause**: Detection too aggressive or data quality issue
- **Solution 1**: Review default thresholds
- **Solution 2**: Decrease weight values
- **Solution 3**: Check if data actually contains many bots
- **Solution 4**: Review detection reasons for patterns

**Problem**: No sessions flagged as bots (but you expect some)
- **Cause**: Detection not sensitive enough
- **Solution 1**: Increase weight values
- **Solution 2**: Lower threshold values
- **Solution 3**: Check if void events are present in data
- **Solution 4**: Review specific sessions manually

**Problem**: Inconsistent results across runs
- **Cause**: Session state or data issues
- **Solution 1**: Refresh page and re-upload
- **Solution 2**: Clear browser cache
- **Solution 3**: Ensure data file hasn't changed

### Model Issues

**Problem**: "Model version compatibility issue"
- **Cause**: Model trained with different scikit-learn version
- **Solution 1**: Use rule-based detection instead
- **Solution 2**: Retrain model with scikit-learn 1.7.0
- **Solution 3**: Download and use sample model
- **Solution 4**: Contact model provider for updated version

**Problem**: ML prediction fails silently
- **Check**: Results table for "ML-model-prediction" in detection reasons
- **Note**: System automatically falls back to rule-based
- **Action**: Check console for error messages

### Dashboard Issues

**Problem**: Dashboard shows "Please complete analysis first"
- **Cause**: No results in session state
- **Solution**: Navigate to Analysis tab and run detection

**Problem**: Visualizations not displaying
- **Solution 1**: Refresh page
- **Solution 2**: Check browser JavaScript enabled
- **Solution 3**: Try different browser
- **Solution 4**: Ensure Plotly loading correctly

### Data Quality Issues

**Problem**: Strange timestamp formats
- **Solution 1**: System tries automatic parsing
- **Solution 2**: Pre-format in Excel as ISO 8601: YYYY-MM-DD HH:MM:SS
- **Solution 3**: Check timezone consistency

**Problem**: Missing void column
- **Impact**: Void detection rule won't apply (system continues)
- **Solution**: Add void column to data export from email platform
- **Workaround**: Other rules still effective

**Problem**: Duplicate session IDs with different data
- **Cause**: Session ID not unique identifier
- **Solution**: Use different column as session ID
- **Impact**: Features will aggregate incorrectly

---

## Best Practices

### Data Preparation

1. **Clean Before Upload**:
   - Remove test sends
   - Filter to target date range
   - Ensure consistent formatting
   - Remove completely empty rows/columns

2. **Include All Available Columns**:
   - Void indicators crucial for detection
   - User agents help identify patterns
   - Fingerprints improve accuracy
   - Timestamps enable temporal analysis

3. **Maintain Data Quality**:
   - Consistent session ID format
   - Valid timestamps
   - Standardized event types
   - Complete records (minimize nulls)

### Detection Configuration

1. **Start with Defaults**:
   - Rule-based method recommended first
   - Default weights based on real data
   - Adjust only if needed for your use case

2. **Iterate Based on Results**:
   - Review sample of flagged sessions
   - Check for false positives
   - Adjust weights incrementally
   - Document what works

3. **Consider Campaign Context**:
   - Newsletter campaigns may have lower click rates (adjust opens_only weight)
   - Promotional campaigns expect higher clicks (keep or increase)
   - Different audiences have different behaviors

### Analysis Workflow

1. **Review Summary First**:
   - Check campaign health metrics
   - Compare to benchmarks
   - Identify red flags
   - Assess overall quality

2. **Examine High-Confidence Bots**:
   - Filter to bot_score > 0.7
   - Review detection reasons
   - Validate patterns
   - Identify common themes

3. **Investigate Uncertain Cases**:
   - Filter to 0.4 < bot_score < 0.6
   - Manual review recommended
   - Look for edge cases
   - Consider context

4. **Validate Human Sessions**:
   - Spot-check low bot scores
   - Ensure genuine human patterns
   - Check for false negatives
   - Adjust if needed

### Reporting and Action

1. **Document Findings**:
   - Campaign health scores
   - Bot percentage trends
   - Common bot patterns
   - Action items

2. **Take Targeted Actions**:
   - High-confidence bots (>0.8): Consider removal
   - Medium confidence (0.6-0.8): Segment for monitoring
   - Low confidence (<0.6): Keep but review
   - Humans: Focus engagement efforts here

3. **Monitor Over Time**:
   - Track bot percentage trends
   - Identify increasing contamination
   - Measure impact of cleaning
   - Adjust strategies

### Privacy and Security

1. **Data Handling**:
   - No data persisted to disk
   - Session state cleared on page refresh
   - Upload files not saved
   - Export and delete locally when done

2. **Sensitive Information**:
   - Data may contain user information
   - Handle according to privacy policies
   - Export securely
   - Delete when no longer needed

3. **Model Security**:
   - Only upload trusted .pkl models
   - Verify model source
   - Test with sample data first
   - Monitor for unexpected behavior

---

## FAQs

### General Questions

**Q: What is a "bot" in this context?**
A: Email security software, firewalls, spam filters, and email predownloading systems that automatically check email content, not actual human engagement.

**Q: Why do I care about bots in my email campaigns?**
A: Bots inflate open rates without real engagement, making your campaigns appear more successful than they are. This leads to poor decision-making and wasted budget.

**Q: Is rule-based or ML better?**
A: Rule-based is recommended for most users. It's transparent, requires no training, and is calibrated for email security patterns. ML is better if you have custom requirements and trained models.

**Q: Can I use this for SMS or push notifications?**
A: The system is designed for email campaigns but principles apply to other channels. You'd need to adapt detection rules for channel-specific patterns.

### Data Questions

**Q: How many sessions do I need for meaningful analysis?**
A: Minimum 10, but 100+ recommended. Larger campaigns (1000+) provide better statistical confidence.

**Q: What if my columns have different names?**
A: The system uses flexible pattern matching. As long as columns contain key words like "id", "type", "timestamp", they should be detected. If not, rename to match expected patterns.

**Q: Can I analyze multiple campaigns at once?**
A: Yes, if they're in the same file. The analysis will treat it as one combined campaign. For separate campaign comparison, analyze individually.

**Q: What if I don't have void events in my data?**
A: The system still works but void detection rule won't apply. Other rules (rapid activity, low engagement, etc.) still effective.

### Detection Questions

**Q: What bot score indicates a bot?**
A: Scores >0.5 are classified as "Likely Bot" by default. However, high-confidence bots are typically >0.7, and very likely bots >0.8.

**Q: Why are some bots scored low?**
A: They may only trigger weak indicators or few indicators. Bot score reflects strength and number of signals. Manual review recommended for uncertain cases.

**Q: Can humans be mistakenly flagged?**
A: Yes, false positives are possible. Users who act quickly, open without clicking (legitimate behavior), or have technical issues may be flagged. Review detection reasons and adjust weights if seeing many false positives.

**Q: What's a typical bot percentage?**
A: Varies widely: 5-15% typical for clean lists, 20-40% moderate contamination, 50%+ indicates serious bot inflation or deliverability issues.

### Technical Questions

**Q: Can I integrate this into my email platform?**
A: Currently standalone. Future enhancements may include API endpoints for programmatic access.

**Q: Can I download the source code?**
A: Yes, the code is available in the project directory. All components are Python-based and open source libraries.

**Q: What machine learning algorithms does it use?**
A: Sample model uses Random Forest, but any scikit-learn compatible model works (.pkl format). Rule-based doesn't use ML.

**Q: How do I train my own ML model?**
A: Use `create_model.py` as template. Generate training data, label sessions, train with scikit-learn 1.7.0, save as .pkl.

### Results Questions

**Q: Why is my campaign flagged as "Bot-Inflated"?**
A: Open rate >65% suggests security software inflation. Real healthy campaigns typically have 19-54% opens. High opens with low clicks (<2% CTO) is classic bot pattern.

**Q: What should I do if 50%+ sessions are bots?**
A: Review detection reasons, validate with sample, identify common patterns, segment or remove bot addresses, improve list quality.

**Q: How do I get true engagement rates?**
A: Filter to "Likely Human" sessions only, calculate open/click rates on that subset. This represents genuine human engagement.

**Q: Can I trust the bot detection?**
A: Detection is based on real campaign data patterns and industry benchmarks. High-confidence bots (>0.7) are very reliable. Medium confidence (0.5-0.7) should be reviewed. The system is a powerful tool but not 100% perfect - always validate a sample.

---

**Version**: 1.0
**Last Updated**: December 2025
**Status**: Production Ready
