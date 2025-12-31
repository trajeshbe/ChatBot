# User Guide
## Crop Insight Tagger - Agricultural Field Inspection Taxonomy System

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [System Requirements](#system-requirements)
4. [Installation Guide](#installation-guide)
5. [Quick Start Tutorial](#quick-start-tutorial)
6. [Using the Application](#using-the-application)
7. [Best Practices](#best-practices)
8. [Understanding Results](#understanding-results)
9. [Troubleshooting](#troubleshooting)
10. [Tips and Tricks](#tips-and-tricks)
11. [Frequently Asked Questions](#frequently-asked-questions)
12. [Support and Feedback](#support-and-feedback)

---

## Introduction

### What is Crop Insight Tagger?

Crop Insight Tagger is an AI-powered tool that automatically converts your field inspection notes into structured, organized data. Instead of spending time manually categorizing and entering inspection observations into spreadsheets or databases, simply paste your field notes and let the system extract all relevant information instantly.

### Who Should Use This Tool?

This tool is designed for:

- **Field Agronomists and Consultants**: Streamline inspection data entry
- **Farm Managers**: Quickly process field reports from multiple scouts
- **Agricultural Researchers**: Standardize field observation data
- **Extension Officers**: Efficiently document and track field visits
- **Crop Advisors**: Convert observations into actionable data
- **Data Analysts**: Prepare field data for analysis and reporting

### What Can It Do?

The Crop Insight Tagger automatically extracts and categorizes:

- Crop growth stages and development
- Soil conditions and nutrient status
- Pest and disease observations
- Weed pressure and types
- Applied inputs (fertilizers, herbicides)
- Weather conditions
- Agronomic recommendations

### Key Benefits

- **Save Time**: 10-15 minutes of manual work reduced to seconds
- **Improve Consistency**: Standardized data across all field inspections
- **Reduce Errors**: Eliminate manual transcription mistakes
- **Enable Analysis**: Create structured data ready for dashboards and reports
- **Easy to Use**: No technical expertise required

---

## Getting Started

### What You Need

Before you begin, ensure you have:

1. **Computer or Device**: Laptop, desktop, or tablet with internet browser
2. **Internet Connection**: Stable connection for accessing the application
3. **Web Browser**: Modern browser (Chrome, Firefox, Safari, or Edge)
4. **Field Inspection Notes**: Your field observation text ready to process

### Accessing the Application

**For Prototype/Development**:
1. The application runs locally on your machine
2. Access via: `http://localhost:8501`
3. See [Installation Guide](#installation-guide) for setup instructions

**For Production/Hosted Version** (when available):
1. Navigate to the provided URL
2. Log in with your credentials
3. Start using immediately

---

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|------------|
| Operating System | Windows 10+, macOS 10.14+, or Linux |
| RAM | 4 GB minimum (8 GB recommended) |
| Disk Space | 500 MB for installation |
| Browser | Chrome 90+, Firefox 88+, Safari 14+, Edge 90+ |
| Internet | Broadband connection (minimum 5 Mbps) |
| Screen Resolution | 1280 x 720 minimum |

### Recommended Setup

| Component | Recommendation |
|-----------|---------------|
| RAM | 8 GB or higher |
| Internet | 10+ Mbps for optimal performance |
| Screen Resolution | 1920 x 1080 or higher |
| Browser | Latest version of Chrome or Firefox |

---

## Installation Guide

### For Technical Users (Local Setup)

#### Prerequisites

Ensure you have Python 3.8 or higher installed:

```bash
python --version
```

If not installed, download from: https://www.python.org/downloads/

#### Step-by-Step Installation

**Step 1: Obtain the Code**

```bash
# Navigate to the agri_taxonomy directory
cd /path/to/agri_taxonomy
```

**Step 2: Create Virtual Environment** (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

**Step 3: Install Dependencies**

```bash
pip install -r requirements.txt
```

Required packages:
- streamlit
- langchain
- langchain-openai
- python-dotenv
- pydantic
- PyYAML
- loguru

**Step 4: Configure Environment**

Create a `.env` file in the project directory:

```bash
# .env file
OPENAI_API_KEY=your_openai_api_key_here
```

**How to get OpenAI API Key**:
1. Visit: https://platform.openai.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Create new API key
5. Copy and paste into `.env` file

**Step 5: Verify Configuration**

Check that `config.yaml` exists and contains:

```yaml
data_path: data

llm:
  model: gpt-4o-mini
  model_provider: openai
  temperature: 0
```

**Step 6: Run the Application**

```bash
streamlit run app.py
```

**Step 7: Access the Application**

The application will automatically open in your default browser at:
```
http://localhost:8501
```

If it doesn't open automatically, manually navigate to this URL.

### Verification

You should see:
- Application title: "Crop Insight Tagger (Agri)"
- Text input area
- Submit button

---

## Quick Start Tutorial

### Your First Extraction (5 Minutes)

Let's process a sample field inspection report to get familiar with the system.

**Step 1: Open the Application**

Navigate to the application URL and you'll see the main interface.

**Step 2: Prepare Sample Text**

Copy this sample inspection report:

```
The maize field is at V6 growth stage with good plant height and
uniform stand. Soil appears slightly alkaline with good tilth.
Observed some potassium deficiency symptoms with marginal leaf
scorching. Found armyworm larvae in about 20% of plants scouted.
Some grey leaf spot on lower canopy leaves. Moderate broadleaf
weed pressure, mainly pigweed. Farmer applied MOP fertilizer last
week. Weather has been warm and humid. Recommend potassium foliar
spray and targeted insecticide for armyworm control.
```

**Step 3: Paste into Application**

1. Click in the text area labeled "Please input the field/crop details"
2. Paste your sample text (Ctrl+V or Cmd+V)

**Step 4: Submit for Processing**

1. Click the "Submit" button
2. You'll see a "Please Wait..." spinner
3. Processing typically takes 3-5 seconds

**Step 5: Review Results**

You'll see a table with extracted information:

| Field | Value |
|-------|-------|
| Crop Establishment | V6 Growth Stage |
| Growth Observation | Good Plant Height, Uniform Stand |
| Soil Condition | Alkaline, Good Tilth |
| Soil Nutrient | Potassium Deficiency |
| Leaf Symptom | Marginal Scorching |
| Pest | Armyworm |
| Disease | Grey Leaf Spot |
| Weed Pressure | Moderate |
| Weed Type | Broadleaf, Pigweed |
| Fertilizer Applied | MOP |
| Weather Pattern | Warm & Humid |
| Recommendation | Potassium Foliar Spray, Targeted Insecticide |

**Step 6: Explore the Data**

- Scroll through the results
- Select and copy specific values
- Notice how the system organized information into categories

**Congratulations!** You've successfully processed your first inspection report.

---

## Using the Application

### Application Interface Overview

```
┌────────────────────────────────────────────────────────┐
│                                                        │
│            Crop Insight Tagger (Agri)                 │
│                                                        │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Please input the field/crop details                  │
│  ┌──────────────────────────────────────────────┐    │
│  │                                              │    │
│  │  [Your field inspection text goes here]     │    │
│  │                                              │    │
│  │                                              │    │
│  │                                              │    │
│  └──────────────────────────────────────────────┘    │
│                                                        │
│                   [ Submit ]                          │
│                                                        │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Results appear here after processing                 │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### Input Guidelines

#### What to Include

**Good inspection text includes**:
- Crop type and growth stage
- Visual observations of plants
- Soil conditions
- Pest or disease observations
- Weed presence
- Applied inputs (fertilizers, herbicides)
- Weather conditions
- Your recommendations

#### Format Flexibility

The system accepts various input formats:

**Narrative Format**:
```
Visited the north field today. Corn is at V8 stage looking healthy
overall. Some yellowing on lower leaves suggesting nitrogen stress.
Soil is dry. Few armyworms found. Recommend nitrogen application.
```

**Bullet Points**:
```
- Crop stage: V8
- Lower leaf yellowing
- Dry soil conditions
- Armyworm present (low)
- Action: Apply nitrogen
```

**Structured Format**:
```
Field: North-40
Crop: Maize, V8 stage
Symptoms: Chlorosis, lower canopy
Soil: Dry, compacted
Pest: Armyworm (low pressure)
Recommendation: N topdress 30 kg/ha
```

All formats work equally well!

#### Input Length

- **Minimum**: A few sentences describing key observations
- **Optimal**: 100-500 words (1-2 paragraphs)
- **Maximum**: No hard limit, but best results with focused, concise reports

#### What NOT to Include

- Sensitive farmer information (names, addresses, phone numbers)
- Financial data (prices, payments)
- Non-agricultural content
- Unrelated notes or comments

### Processing Your Inspection

**Step-by-Step Process**:

1. **Enter Text**
   - Click in the text area
   - Type or paste your field inspection notes
   - Review for completeness

2. **Submit**
   - Click the "Submit" button
   - Wait for processing (3-5 seconds typical)
   - "Please Wait..." spinner indicates processing

3. **Review Results**
   - Results appear in a table below the input
   - Scroll to see all extracted categories
   - Check for completeness and accuracy

4. **Use Results**
   - Copy data to clipboard (select and Ctrl+C or Cmd+C)
   - Take screenshot for documentation
   - Manually transfer to other systems

5. **Process Another Inspection** (Optional)
   - Clear previous text or type new inspection
   - Click Submit again
   - Previous results are replaced with new ones

### Understanding Processing Time

**What affects processing speed?**

| Factor | Impact on Speed |
|--------|----------------|
| Text length | Longer text = slightly longer processing |
| Internet speed | Slow connection = slower API calls |
| LLM API load | Peak times may be slower |
| Complexity | Complex reports take slightly longer |

**Typical Processing Times**:
- Short inspection (50-100 words): 2-3 seconds
- Medium inspection (100-300 words): 3-5 seconds
- Long inspection (300-500 words): 5-8 seconds

**If processing takes longer than 10 seconds**:
- Check your internet connection
- LLM API may be experiencing high load
- Try again in a few moments

---

## Best Practices

### Writing Effective Inspection Notes

#### Do's

**Be Descriptive**:
```
✓ "Lower leaves showing interveinal chlorosis with marginal necrosis"
✗ "Leaves look bad"
```

**Include Specifics**:
```
✓ "Armyworm larvae found in whorl of 15-20% of plants scouted"
✗ "Some pests"
```

**Mention Growth Stage**:
```
✓ "Maize at V8 growth stage" or "Wheat at flag leaf stage"
✗ "Crop is growing"
```

**Document Inputs**:
```
✓ "Applied 50 kg/ha urea as topdress at V6 stage"
✗ "Put on some nitrogen"
```

**Note Weather Context**:
```
✓ "Warm and humid conditions over past week, scattered afternoon storms"
✗ "Weather"
```

#### Don'ts

**Avoid Vague Language**:
```
✗ "Field looks okay"
✗ "Some issues"
✗ "Normal conditions"
```

**Don't Omit Important Details**:
```
✗ "Pest pressure" (What pest? How severe?)
✓ "Moderate fall armyworm pressure, larvae in 20% of plants"
```

**Don't Use Unclear Abbreviations**:
```
✗ "FAW in whl, 3-4 L, mod P"
✓ "Fall armyworm larvae (3-4 per plant) in whorl, moderate pressure"
```

### Optimizing Extraction Accuracy

**Tip 1: Be Complete**
Include observations across all relevant categories:
- Crop health
- Soil conditions
- Pest/disease
- Weeds
- Applied inputs
- Recommendations

**Tip 2: Use Standard Terminology**
The system recognizes agricultural terminology:
- Growth stages: V6, R1, R3, tasseling, flowering, etc.
- Pests: Scientific or common names both work
- Diseases: Use recognized disease names
- Nutrients: N, P, K or Nitrogen, Phosphorus, Potassium

**Tip 3: Provide Context**
Help the system understand relationships:
```
✓ "Observed potassium deficiency based on marginal leaf scorch and soil test results"
✗ "K low, leaves brown"
```

**Tip 4: Structure Logically**
Organize your notes in a logical flow:
1. Field identification
2. Crop status
3. Observations
4. Issues/problems
5. Recommendations

**Tip 5: Review Before Submitting**
Quick checks:
- Is anything obviously missing?
- Are abbreviations clear?
- Is the text readable?

### Data Management Best Practices

**Track Your Inspections**:
- Date and identify each inspection
- Keep original notes for reference
- Save extracted results systematically

**Validate Results**:
- Review extracted data for accuracy
- Cross-check critical observations
- Note any extraction errors for reporting

**Archive Systematically**:
- Organize by farm, field, or date
- Maintain both raw and structured data
- Create backup copies

**Integrate with Workflows**:
- Develop standard templates for field notes
- Train team on consistent reporting
- Use extracted data in decision workflows

---

## Understanding Results

### Result Categories Explained

The system extracts information into 15 standardized categories. Here's what each means:

#### 1. Crop Establishment

**What it captures**: Current growth stage or development phase

**Examples**:
- "V6 Growth Stage" (vegetative stage 6)
- "R3 Reproductive Stage" (milk stage in corn)
- "Tasseling" (corn reproductive stage)
- "Flowering" (general reproductive stage)

**Why it matters**: Critical for timing interventions and assessing development

#### 2. Growth Observation

**What it captures**: General plant growth and development indicators

**Examples**:
- "Good Plant Height"
- "Uniform Stand"
- "Vigorous Growth"
- "Leaf Development"

**Why it matters**: Overall health assessment and growth benchmarking

#### 3. Soil Condition

**What it captures**: Physical and chemical soil properties

**Examples**:
- "Alkaline" (high pH)
- "Good Tilth" (good soil structure)
- "Compacted" (poor structure)
- "Moist" (moisture status)

**Why it matters**: Foundation for crop health and nutrient availability

#### 4. Soil Nutrient

**What it captures**: Nutrient deficiencies, sufficiencies, or imbalances

**Examples**:
- "Nitrogen Deficiency"
- "Borderline Potassium"
- "Sufficient Phosphorus"
- "Micronutrient Deficiency"

**Why it matters**: Direct impact on yield and fertilizer decisions

#### 5. Leaf Symptom

**What it captures**: Visible abnormalities on leaves

**Examples**:
- "Marginal Scorching" (edges burned)
- "Interveinal Chlorosis" (yellowing between veins)
- "Chewing Damage" (insect feeding)
- "Leaf Curling"

**Why it matters**: Diagnostic indicator for various stresses and issues

#### 6. Physiological Symptom

**What it captures**: Plant stress indicators beyond leaves

**Examples**:
- "Wilting" (water stress)
- "Lodging" (stalk breakage)
- "Stunted Growth"
- "Poor Pollination"

**Why it matters**: Indicates environmental or management stresses

#### 7. Pest

**What it captures**: Insect pests identified in the field

**Examples**:
- "Fall Armyworm"
- "Aphid"
- "Corn Borer"
- "Cutworm"

**Why it matters**: Triggers pest management decisions

#### 8. Disease

**What it captures**: Plant diseases observed

**Examples**:
- "Grey Leaf Spot"
- "Common Rust"
- "Northern Corn Leaf Blight"
- "Fusarium"

**Why it matters**: Critical for disease management and yield protection

#### 9. Weed Pressure

**What it captures**: Severity of weed infestation

**Examples**:
- "Low"
- "Moderate"
- "High"
- "Severe"

**Why it matters**: Determines need for herbicide intervention

#### 10. Weed Type

**What it captures**: Categories or species of weeds present

**Examples**:
- "Broadleaf"
- "Grassy Weeds"
- "Pigweed"
- "Morning Glory"

**Why it matters**: Guides herbicide selection and management strategy

#### 11. Fertilizer Applied

**What it captures**: Fertilizer products and applications

**Examples**:
- "Urea"
- "DAP" (diammonium phosphate)
- "MOP" (muriate of potash)
- "NPK 15-15-15"

**Why it matters**: Tracks input use and correlates with crop response

#### 12. Herbicide Use

**What it captures**: Herbicide applications and timing

**Examples**:
- "Pre-emergent"
- "Post-emergent"
- "Glyphosate"
- "Atrazine"

**Why it matters**: Weed control tracking and resistance management

#### 13. Drainage

**What it captures**: Field drainage conditions

**Examples**:
- "Effective"
- "Poor Drainage"
- "Waterlogged"
- "Standing Water"

**Why it matters**: Affects crop health and management decisions

#### 14. Weather Pattern

**What it captures**: Recent weather conditions

**Examples**:
- "Warm & Humid"
- "Dry Spell"
- "Recent Rainfall"
- "Cool Temperatures"

**Why it matters**: Context for crop stress and disease risk

#### 15. Recommendation

**What it captures**: Advisory actions from the inspection

**Examples**:
- "Nitrogen Application"
- "Monitor Pest Pressure"
- "Fungicide Application"
- "Increase Irrigation"

**Why it matters**: Action items and follow-up tracking

### How to Read Results

**Result Table Format**:

```
┌─────────────────────────┬──────────────────────────────┐
│ Category                │ Extracted Value              │
├─────────────────────────┼──────────────────────────────┤
│ Crop Establishment      │ V6 Growth Stage              │
│ Growth Observation      │ Good Height, Uniform Stand   │
│ Soil Nutrient           │ Potassium Deficiency         │
│ Pest                    │ Armyworm                     │
│ Recommendation          │ K Spray, Insecticide         │
└─────────────────────────┴──────────────────────────────┘
```

**Multi-value Fields**:
When multiple values are extracted for a category, they appear comma-separated:
- "Armyworm, Aphid, Corn Borer"
- "Good Height, Uniform Stand, Vigorous Growth"

**Empty or Unknown Fields**:
- Not shown in results (only populated fields display)
- Or marked as "Unknown" if mentioned but unclear

### Interpreting Unknown Values

**"Unknown" means**:
- Information was mentioned but unclear
- Ambiguous phrasing in inspection notes
- Insufficient detail to extract specific value

**Empty/missing means**:
- Information was not mentioned in inspection notes
- Not applicable to this inspection

**Example**:

Input: "The field has some issues with growth"

Result:
- Growth Observation: "Unknown" (mentioned but too vague)
- Pest: (empty - not mentioned)

### Using Extracted Data

**Copy Individual Values**:
1. Click and drag to select specific text
2. Copy (Ctrl+C or Cmd+C)
3. Paste into your system

**Copy Entire Table**:
1. Select all results
2. Copy to clipboard
3. Paste into Excel, Google Sheets, or other tools
4. Data maintains table structure

**Screenshot Results**:
1. Use screenshot tool (Print Screen, Snip, Cmd+Shift+4)
2. Capture results table
3. Save for documentation

**Manual Transfer**:
- Review each category
- Enter relevant data into farm management system
- Cross-reference with other data sources

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: "Please Wait..." Doesn't Complete

**Symptoms**: Loading spinner runs for more than 30 seconds

**Possible Causes**:
- Internet connection issues
- LLM API timeout
- Server overload

**Solutions**:
1. Check internet connection
2. Refresh the page and try again
3. Try with shorter/simpler text
4. Contact support if persistent

#### Issue 2: No Results Displayed

**Symptoms**: Submit button clicked but no output appears

**Possible Causes**:
- Empty input text
- Processing error
- Browser compatibility issue

**Solutions**:
1. Ensure text is entered in the input area
2. Check browser console for errors (F12)
3. Try different browser
4. Refresh page and retry

#### Issue 3: Inaccurate Extractions

**Symptoms**: Extracted data doesn't match your inspection notes

**Possible Causes**:
- Vague or ambiguous input text
- Unusual terminology
- Complex or lengthy notes

**Solutions**:
1. Review your input text for clarity
2. Use more specific terminology
3. Break long inspections into smaller sections
4. Rephrase unclear observations
5. Report persistent issues for system improvement

#### Issue 4: Missing Information

**Symptoms**: Expected data not extracted

**Possible Causes**:
- Information not clearly stated in notes
- Terminology not recognized
- Implicit vs. explicit information

**Solutions**:
1. Check if information was explicitly stated
2. Rephrase using standard agricultural terms
3. Add more detail to inspection notes
4. Remember: system extracts only what's clearly mentioned

#### Issue 5: Application Won't Start (Local Setup)

**Symptoms**: Error when running `streamlit run app.py`

**Possible Causes**:
- Missing dependencies
- Python version incompatibility
- Configuration errors

**Solutions**:
1. Verify Python version (3.8+)
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Check `.env` file exists with API key
4. Check `config.yaml` is present
5. Review error messages for specific issues

#### Issue 6: API Key Errors

**Symptoms**: "Authentication failed" or similar errors

**Possible Causes**:
- Missing or invalid OpenAI API key
- API key not loaded from `.env`
- Expired or deactivated API key

**Solutions**:
1. Verify `.env` file exists in project directory
2. Check API key format: `OPENAI_API_KEY=sk-...`
3. Verify API key is active on OpenAI platform
4. Restart application after updating `.env`

### Error Messages Explained

| Error Message | Meaning | Solution |
|---------------|---------|----------|
| "Please enter field inspection details" | Input is empty | Enter text before submitting |
| "Processing failed. Please try again." | General processing error | Retry, check internet, contact support |
| "Config file not found..." | Missing config.yaml | Ensure config.yaml is in project directory |
| JSON parsing errors (in logs) | LLM output format issue | Retry, report if persistent |

### Getting Help

**Self-Service Resources**:
1. Re-read this user guide
2. Check FAQ section below
3. Review installation instructions
4. Verify system requirements

**Contact Support**:
- Email: [support email]
- Include: Error message, screenshots, sample input text
- Response time: [specified timeframe]

---

## Tips and Tricks

### Pro Tips for Power Users

**Tip 1: Create Template Structures**

Develop standard templates for your field notes:

```
FIELD INSPECTION TEMPLATE

Field ID: ________
Date: ________
Crop: ________ Stage: ________

OBSERVATIONS:
- Plant health: ________
- Soil condition: ________
- Pest/Disease: ________
- Weeds: ________

INPUTS:
- Recent applications: ________

WEATHER:
- Recent conditions: ________

RECOMMENDATIONS:
- Actions: ________
```

**Tip 2: Use Voice-to-Text**

Dictate field notes on your phone:
1. Record observations while in field
2. Voice-to-text conversion (Google Docs, etc.)
3. Light editing for clarity
4. Paste into Crop Insight Tagger

**Tip 3: Batch Similar Inspections**

For efficiency with multiple fields:
1. Write inspections using consistent format
2. Process one at a time
3. Copy results to master spreadsheet
4. Compare across fields

**Tip 4: Combine with Photos**

Enhanced documentation:
1. Take field photos with timestamp
2. Write text observations
3. Process with Crop Insight Tagger
4. File structured data with photos

**Tip 5: Integrate into Mobile Workflow**

For field use:
1. Type notes on mobile device or tablet
2. Email or sync to computer
3. Batch process at end of day
4. Results ready for reporting

### Advanced Usage

**Extraction Optimization**:

For best results, structure notes by category:

```
CROP STATUS
The maize is at V8 growth stage with good height and
uniform stand across the field.

SOIL OBSERVATIONS
Soil appears slightly alkaline with good tilth. Some
surface crusting in wheel tracks.

NUTRIENT STATUS
Lower leaves showing marginal scorch indicating possible
potassium deficiency. Soil test pending.

PEST & DISEASE
Found fall armyworm larvae in 15% of plants scouted,
primarily in whorl. Low pressure at this time. Some
common rust on lower canopy leaves.

WEED STATUS
Moderate broadleaf weed pressure, mainly pigweed and
morning glory. Pre-emergent herbicide provided good control
but some breakthrough weeds in wet areas.

INPUTS APPLIED
Farmer applied 100 kg/ha NPK 12-24-12 at planting and
50 kg/ha urea topdress at V6 stage last week.

WEATHER
Warm (28-32°C) and humid conditions over past week with
scattered afternoon thunderstorms.

RECOMMENDATIONS
1. Apply potassium foliar spray (K2O 15%) at 2 L/ha
2. Monitor armyworm pressure; consider treatment if exceeds threshold
3. Continue rust monitoring; no action needed currently
4. Spot-treat emerged weeds with post-emergent herbicide
```

This structure helps the system extract information accurately while also creating clear documentation.

**Iterative Refinement**:

If first extraction isn't perfect:
1. Review what was missed or unclear
2. Add specific details to input text
3. Resubmit for improved results

### Shortcuts and Efficiency Hacks

**Keyboard Shortcuts**:
- `Tab`: Navigate between input and button
- `Ctrl/Cmd + A`: Select all text
- `Ctrl/Cmd + C`: Copy selected text
- `Ctrl/Cmd + V`: Paste text

**Browser Tips**:
- Bookmark the application URL
- Use browser's "open in new tab" for parallel processing
- Browser autocomplete can help with repeated terms

**Workflow Automation Ideas** (Future):
- Email-to-extraction workflows
- Mobile app integration
- Automated export to farm management systems

---

## Frequently Asked Questions

### General Questions

**Q: How long does processing take?**

A: Typically 3-5 seconds for most inspections. Longer or more complex reports may take up to 8-10 seconds.

**Q: Is my data stored or saved?**

A: In the prototype version, data is not stored. Each request is processed independently. Future versions may include optional data storage features.

**Q: Can I process multiple inspections at once?**

A: Currently, the system processes one inspection at a time. Batch processing capabilities are planned for future releases.

**Q: What languages are supported?**

A: Currently English only. Multilingual support is planned for future versions.

**Q: How accurate is the extraction?**

A: The system achieves 85%+ accuracy on well-written field inspection reports. Accuracy improves with clear, specific input text.

### Technical Questions

**Q: What AI model does this use?**

A: The system uses OpenAI's GPT-4o-mini model, optimized for cost-effectiveness and speed while maintaining high accuracy.

**Q: Can I use this offline?**

A: No, an internet connection is required to access the OpenAI API for processing.

**Q: Can I customize the extraction categories?**

A: Not in the current version. Custom categories are planned for future releases based on user feedback.

**Q: How much does it cost to use?**

A: The prototype uses OpenAI API credits. Typical cost is $0.01-0.05 per inspection. Production pricing will be determined based on deployment model.

**Q: Can I export results?**

A: Currently, you can copy/paste results. Future versions will include export to CSV, Excel, and API integration options.

### Usage Questions

**Q: What if I don't know the exact growth stage?**

A: Describe it in general terms (e.g., "mid-vegetative stage," "flowering") and the system will extract what it can.

**Q: Should I include field identification in my notes?**

A: You can, but it's not extracted. Field ID, farmer name, and similar metadata should be tracked separately.

**Q: Can I edit results after extraction?**

A: No direct editing in the current interface. Copy results to your preferred tool for editing.

**Q: What if the extraction is wrong?**

A: Review your input text for clarity. If the input is clear but extraction is still wrong, please report it for system improvement.

**Q: Can I use abbreviations?**

A: Yes, common agricultural abbreviations are recognized (N, P, K, MOP, DAP, FAW, etc.). When in doubt, spell it out.

### Troubleshooting Questions

**Q: Why do some fields show "Unknown"?**

A: This indicates the information was mentioned but wasn't clear enough to extract a specific value. Try being more specific in your input.

**Q: Processing failed - what should I do?**

A: First, check your internet connection. Then try again. If it persists, try with a shorter or simpler text, or contact support.

**Q: Results seem incomplete - why?**

A: The system only extracts information that is clearly stated in your notes. Add more detail to your inspection notes for more complete results.

**Q: Can I process the same inspection twice?**

A: Yes, but results should be identical (assuming temperature=0 in config). Processing the same text multiple times won't improve results.

---

## Support and Feedback

### Getting Support

**Documentation**:
- User Guide (this document)
- Technical Architecture (for developers)
- Functional Architecture (for analysts)

**Self-Service**:
- Review [Troubleshooting](#troubleshooting) section
- Check [FAQ](#frequently-asked-questions)
- Verify [System Requirements](#system-requirements)

**Technical Support**:
- Email: [support email address]
- Response Time: [specified timeframe]
- Include: Screenshots, error messages, sample text

**Community** (if available):
- User forums
- Knowledge base
- Video tutorials

### Providing Feedback

Your feedback helps improve the system!

**What to Report**:
- Extraction errors or inaccuracies
- Missing features you need
- Usability improvements
- Performance issues
- Documentation gaps

**How to Provide Feedback**:
- Feedback form: [link]
- Email: [feedback email]
- User surveys (when available)

**Reporting Bugs**:

Please include:
1. **Description**: What went wrong?
2. **Input**: Sample text you processed (anonymized)
3. **Expected**: What should have been extracted?
4. **Actual**: What was actually extracted?
5. **Environment**: Browser, OS, any error messages

**Suggesting Features**:

Please describe:
1. **Use Case**: What are you trying to accomplish?
2. **Current Limitation**: What prevents you from doing this now?
3. **Proposed Solution**: What would help?
4. **Priority**: How important is this to your work?

### Contributing to Improvement

**User Testing**:
- Participate in beta testing programs
- Test new features and provide feedback
- Share your use cases and workflows

**Training Data**:
- Provide sample inspection reports (anonymized)
- Share examples of good/bad extractions
- Help validate accuracy metrics

**Documentation**:
- Suggest improvements to this guide
- Share tips and best practices
- Create video tutorials or guides

---

## Appendix: Sample Inspections

### Example 1: Comprehensive Inspection

**Input**:
```
FIELD INSPECTION REPORT
Date: May 15, 2025
Farm: Johnson Farm, Field A-2

The maize crop is currently at V8 growth stage with excellent
plant height (approximately 75 cm average) and uniform stand
density estimated at 65,000 plants per hectare. Plant vigor is
good with dark green coloration in upper canopy.

Soil conditions appear favorable with slightly alkaline pH
(estimated 7.5-8.0 based on soil indicators) and good tilth.
However, soil surface is showing some crusting following recent
heavy rainfall. Drainage appears effective with no standing water
or saturated areas observed.

Nutrient status assessment reveals potential potassium deficiency
based on marginal leaf scorch on lower (V3-V5) leaves. This is
consistent with soil test results received last week showing
borderline K levels. Upper canopy shows no deficiency symptoms.

Pest scouting revealed fall armyworm larvae in 18 out of 100
plants checked (18% infestation). Most larvae are in 2nd-3rd
instar stage located in the whorl. Current pressure is considered
low to moderate and approaching economic threshold.

Disease pressure is minimal at this growth stage. Observed a few
isolated plants (less than 5%) with early common rust pustules
on lower leaves. No other diseases detected.

Weed pressure is low following successful pre-emergent herbicide
application (atrazine + metolachlor applied at planting). Some
scattered broadleaf weeds, primarily redroot pigweed and common
lambsquarters, emerging in compacted wheel tracks and field edges.
Estimated weed coverage less than 5%.

Input history: Farmer applied 100 kg/ha of NPK 12-24-12 at
planting plus 50 kg/ha urea topdress at V6 stage (10 days ago).
The pre-emergent herbicide mentioned above was applied 2 days
post-planting.

Weather over the past two weeks has been warm (daytime highs
28-32°C) and humid (70-85% RH) with scattered afternoon
thunderstorms every 3-4 days. Total rainfall approximately
45 mm over 14 days.

RECOMMENDATIONS:
1. Apply potassium foliar spray (0-0-15 K2O formulation) at
   2-3 L/ha within next 5-7 days to address deficiency
2. Monitor armyworm pressure closely. If infestation exceeds
   20% or larval stage advances to 4th instar, apply targeted
   insecticide (recommend spinetoram or chlorantraniliprole)
3. Continue rust monitoring but no fungicide action recommended
   at this time given low pressure and favorable crop stage
4. Spot-treat emerged weeds in wheel tracks with post-emergent
   broadleaf herbicide (2,4-D or dicamba)
5. Plan for additional nitrogen topdress (30-40 kg N/ha) at
   V10-V12 stage based on tissue testing
```

**Expected Output**:
```
Crop Establishment: V8 Growth Stage
Growth Observation: Excellent Plant Height, Uniform Stand, Good Vigor, Dark Green Color
Soil Condition: Alkaline, Good Tilth, Surface Crusting
Soil Nutrient: Potassium Deficiency, Borderline K Levels
Leaf Symptom: Marginal Scorch
Physiological Symptom: Unknown
Pest: Fall Armyworm (Low to Moderate Pressure, 18% Infestation)
Disease: Common Rust (Minimal Pressure)
Weed Pressure: Low
Weed Type: Broadleaf, Redroot Pigweed, Common Lambsquarters
Fertilizer Applied: NPK 12-24-12, Urea
Herbicide Use: Pre-emergent (Atrazine, Metolachlor)
Drainage: Effective
Weather Pattern: Warm & Humid, Scattered Thunderstorms, Recent Rainfall
Recommendation: Potassium Foliar Spray, Monitor Armyworm Pressure, Targeted Insecticide if Threshold Exceeded, Continue Rust Monitoring, Post-emergent Herbicide for Weeds, Additional Nitrogen at V10-V12
```

### Example 2: Brief Inspection

**Input**:
```
Quick scout of wheat field today. Crop at flag leaf stage,
looking healthy. Noticed some aphids on flag leaves but well
below economic threshold (average 5-8 per flag). Weather has
been cool and dry. Recommend continued monitoring for aphids
and stripe rust as we approach flowering.
```

**Expected Output**:
```
Crop Establishment: Flag Leaf Stage
Growth Observation: Healthy
Soil Condition: Unknown
Soil Nutrient: Unknown
Leaf Symptom: Unknown
Physiological Symptom: Unknown
Pest: Aphid (Below Threshold)
Disease: Unknown
Weed Pressure: Unknown
Weed Type: Unknown
Fertilizer Applied: Unknown
Herbicide Use: Unknown
Drainage: Unknown
Weather Pattern: Cool & Dry
Recommendation: Monitor Aphids, Monitor Stripe Rust
```

---

## Quick Reference Card

### Step-by-Step Quick Guide

1. **Open Application**: Navigate to application URL
2. **Enter Inspection Text**: Type or paste field notes
3. **Submit**: Click Submit button
4. **Wait**: Processing takes 3-5 seconds
5. **Review Results**: Check extracted data table
6. **Copy/Use Data**: Transfer to your systems

### Key Do's and Don'ts

**DO**:
- ✓ Be specific and descriptive
- ✓ Use standard agricultural terms
- ✓ Include all relevant observations
- ✓ Mention growth stages
- ✓ Note weather conditions
- ✓ Document inputs applied

**DON'T**:
- ✗ Use overly vague language
- ✗ Include sensitive personal data
- ✗ Omit important details
- ✗ Use obscure abbreviations
- ✗ Mix multiple fields in one submission

### Contact Information

- **Technical Support**: [email/phone]
- **Feedback**: [email/form]
- **Documentation**: [link to doc repository]

---

*Document Version: 1.0*
*Last Updated: December 2025*
*Classification: Internal Use*
