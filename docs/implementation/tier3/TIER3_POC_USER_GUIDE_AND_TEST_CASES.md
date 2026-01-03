# Tier 3 Customer POCs - User Guide & Test Cases

**Date:** 2026-01-02
**Version:** 1.0
**Status:** All POCs Operational

---

## Table of Contents

1. [Overview](#overview)
2. [Accessing the POCs](#accessing-the-pocs)
3. [British Council POC](#british-council-poc)
4. [CRU Mining Intelligence POC](#cru-mining-intelligence-poc)
5. [Grant Thornton POC](#grant-thornton-poc)
6. [Test Cases](#test-cases)
7. [Troubleshooting](#troubleshooting)

---

## Overview

This document provides comprehensive user guides and test cases for all three Tier 3 Customer POCs:

| POC | Purpose | Primary Use Case |
|-----|---------|------------------|
| **British Council** | AI-powered course recommendations | Match learners with optimal courses based on profile and goals |
| **CRU** | Mining intelligence Q&A | Answer questions from mining documents with multi-pipeline RAG |
| **Grant Thornton** | Financial audit automation | Extract financial data from annual reports and calculate ratios |

### System Requirements

- **Frontend URL:** http://localhost:3001
- **Backend URL:** http://localhost:8000
- **Browser:** Modern browser (Chrome, Firefox, Safari, Edge)
- **Network:** Access to local Docker containers

---

## Accessing the POCs

### 1. Navigate to Frontend

```bash
# Open in browser
http://localhost:3001
```

### 2. Locate POCs in Sidebar

All three POCs are visible in the left sidebar under **"Customer Solutions (Tier 3)"**:

- 📚 British Council POC
- ⛏️ CRU POC
- 📊 Grant Thornton POC

### 3. Click to Select

Click on any POC name in the sidebar to load its dedicated interface.

---

## British Council POC

### Purpose

AI-powered course recommendation system that analyzes user profiles and matches them with the most suitable British Council courses using hybrid RAG (60% semantic matching + 40% profile matching).

### UI Components

1. **User Input Textarea** - Enter learning goals and preferences
2. **Analyze Profile Button** - Extract user profile from text
3. **Get Recommendations Button** - Get top 10 course recommendations
4. **Profile Display** - Shows extracted skills, interests, education level, etc.
5. **Recommendations Cards** - Displays matched courses with scores and reasons

### Step-by-Step Usage

#### Step 1: Enter Your Learning Goals

In the text area, describe your learning goals and preferences. Example:

```text
I am a software developer with 5 years of experience in Python and JavaScript.
I want to improve my leadership skills and learn about project management.
I prefer online courses with flexible schedules. My goal is to transition
into a tech lead role within the next year. I have a bachelor's degree in
computer science and am proficient in English.
```

#### Step 2: Analyze Profile (Optional)

Click **"Analyze Profile"** to see how the system interprets your input:

- **Skills:** Python, JavaScript, Software Development
- **Interests:** Leadership, Project Management
- **Education Level:** Bachelor's Degree
- **Career Goals:** Tech Lead
- **Preferred Format:** Online
- **Language Proficiency:** English

#### Step 3: Get Recommendations

Click **"Get Recommendations"** to receive top 10 course matches.

#### Step 4: Review Results

Each recommendation card shows:

- **Course Name** and description
- **Match Score** (0.0 - 1.0) - Overall match quality
- **Semantic Score** - Content relevance
- **Profile Score** - Profile alignment
- **Match Reasons** - Why this course was recommended
- **Level Badge** - Beginner, Intermediate, Advanced

### API Endpoints

```bash
# Analyze user profile
POST http://localhost:8000/api/v1/british-council/profile/analyze
{
  "user_input": "I want to learn project management..."
}

# Get course recommendations
POST http://localhost:8000/api/v1/british-council/courses/recommend
{
  "user_input": "I want to learn project management...",
  "top_k": 10
}

# Check POC status
GET http://localhost:8000/api/v1/customer/british_council/status
```

### Expected Behavior

✅ **Success Indicators:**
- Profile is extracted with relevant fields populated
- Recommendations are returned with match scores > 0.5
- Top recommendations have detailed "reasons" lists
- Courses are sorted by match score (highest first)

❌ **Error Indicators:**
- "Failed to analyze profile" - Backend connection issue
- Empty recommendations - No courses in database yet
- Low match scores (<0.3) - Input too vague or no relevant courses

### Tips for Best Results

1. **Be Specific:** Include concrete skills, goals, and preferences
2. **Provide Context:** Mention your current level and experience
3. **State Preferences:** Specify format (online/in-person), schedule, language
4. **Multiple Attributes:** Include 3-5 different aspects (skills, interests, goals)

---

## CRU Mining Intelligence POC

### Purpose

Multi-pipeline RAG system for querying mining documents with automatic query type classification and intelligent routing to optimal search pipeline (semantic, keyword, hybrid, or table data).

### UI Components

1. **Query Input** - Enter your mining-related question
2. **Query Button** - Execute standard query
3. **Compare Pipelines Button** - Compare all pipeline results
4. **Sample Queries** - Pre-filled example questions
5. **Results Display** - Shows answer, confidence, sources, pipeline used
6. **Comparison View** - Side-by-side pipeline comparison

### Step-by-Step Usage

#### Step 1: Enter Query or Use Sample

**Option A - Custom Query:**
```text
What is the estimated capex for the Gold Valley project?
```

**Option B - Click Sample Query:**
- "What is the estimated capex for the Gold Valley project?"
- "What are the key environmental risks?"
- "Compare iron ore grades across all drilling sites"
- "Find documents mentioning feasibility studies"

#### Step 2: Execute Query

Click **"Query"** to get an answer using auto-selected pipeline.

#### Step 3: Review Results

The response includes:

- **Answer:** Natural language answer with citations [1], [2], [3]
- **Confidence:** 0.0 - 1.0 (with level: Low, Medium, High)
- **Confidence Description:** Interpretation of confidence level
- **Pipeline Used:** Which pipeline was selected (pgvector, elasticsearch, hybrid)
- **Query Type:** Classified type (SEMANTIC, KEYWORD, HYBRID, TABLE_DATA)
- **Sources:** Top 3-5 source documents with snippets
- **Processing Time:** Milliseconds to complete

#### Step 4 (Optional): Compare Pipelines

Click **"Compare Pipelines"** to see results from all available pipelines side-by-side:

- **pgvector (Semantic):** Meaning-based search
- **Elasticsearch (Keyword):** BM25 keyword search (if available)
- **Hybrid (RRF):** Reciprocal Rank Fusion (if available)

**Note:** If Elasticsearch is unavailable, CRU runs in pgvector-only mode.

### API Endpoints

```bash
# Execute mining query
POST http://localhost:8000/api/v1/cru/query
{
  "query": "What are the key environmental risks?",
  "top_k": 5
}

# Compare pipeline results
POST http://localhost:8000/api/v1/cru/compare-pipelines
{
  "query": "What are the key environmental risks?",
  "top_k": 5
}

# Check POC status and mode
GET http://localhost:8000/api/v1/customer/cru/status
```

### Query Types and Routing

| Query Type | Example | Optimal Pipeline |
|------------|---------|------------------|
| **SEMANTIC** | "What are environmental risks?" | pgvector (semantic search) |
| **KEYWORD** | "Find Gold Valley documents" | Elasticsearch (BM25) |
| **HYBRID** | "Capex for Gold Valley 2024" | Both + RRF fusion |
| **TABLE_DATA** | "Iron ore grades by site" | Elasticsearch (structured data) |

### Expected Behavior

✅ **Success Indicators:**
- Query is classified correctly
- Answer includes specific citations [1], [2], [3]
- Confidence matches answer quality (e.g., specific facts = high confidence)
- Sources are relevant to query
- Pipeline selection matches query type

❌ **Error Indicators:**
- "No documents found in database yet" - Upload mining documents first
- Very low confidence (<0.3) - Documents don't contain relevant information
- Generic answer without citations - Poor retrieval quality

### Current Limitations

⚠️ **Elasticsearch Mode:**
- CRU is currently running in **pgvector-only mode**
- Elasticsearch is OPTIONAL and not yet started
- All query types fallback to pgvector (semantic search)
- To enable full multi-pipeline: See `BRITISH_COUNCIL_CRU_POC_ENABLEMENT.md`

### Tips for Best Results

1. **Upload Documents First:** CRU works best with mining documents uploaded
2. **Be Specific:** Include project names, locations, metrics
3. **Use Keywords:** For exact term searches, include specific document names
4. **Try Comparison:** Use "Compare Pipelines" to see which works best

---

## Grant Thornton POC

### Purpose

Automated financial audit and compliance tool that extracts 15 key financial datapoints from annual report PDFs, calculates sub-totals, computes 15+ financial ratios, and exports results to Excel.

### UI Components

1. **Company Name Input** (optional) - Enter company name for reference
2. **PDF Upload Button** - Select annual report PDF
3. **Progress Indicator** - Shows extraction progress (0-100%)
4. **Current Stage Display** - What the system is doing
5. **Results Tabs:**
   - **Datapoints** - 15 extracted financial values
   - **Calculations** - Sub-calculations (e.g., Total Assets)
   - **Ratios** - 15+ financial ratios
6. **Download Excel Button** - Export all results

### Step-by-Step Usage

#### Step 1: Prepare Annual Report

Ensure you have:
- **File Format:** PDF only
- **Content:** Company annual report with financial statements
- **Quality:** Clear text (not scanned image - OCR not guaranteed)
- **Size:** Reasonable size (< 50MB recommended)

#### Step 2: Enter Company Name (Optional)

```text
Company Name: Merit Software Services Pvt. Ltd.
```

This helps with organization and Excel export naming.

#### Step 3: Upload PDF

1. Click **"Upload Annual Report PDF"** button
2. Select PDF file from your computer
3. Wait for upload to complete

#### Step 4: Monitor Progress

The UI shows:
- **Progress Bar:** 0% → 100%
- **Current Stage:**
  - "Uploading PDF..."
  - "Extracting datapoints... (3/15)"
  - "Calculating sub-totals..."
  - "Computing financial ratios..."
  - "Exporting to Excel..."

**Typical Duration:** 30-90 seconds depending on PDF size

#### Step 5: Review Extracted Data

Once extraction completes, navigate through three tabs:

##### Tab 1: Datapoints (15 Total)

| Field Name | Value | Page No. | Status | Reference Notes |
|------------|-------|----------|--------|-----------------|
| total_revenue | 1,234,567 | 12 | ✓ Found | From Income Statement |
| total_assets | 5,678,901 | 15 | ✓ Found | From Balance Sheet |
| total_equity | 2,345,678 | 15 | ✓ Found | From Balance Sheet |
| ... | ... | ... | ... | ... |

**15 Datapoints Extracted:**
1. total_revenue
2. total_expenses
3. net_income
4. total_assets
5. current_assets
6. non_current_assets
7. total_liabilities
8. current_liabilities
9. non_current_liabilities
10. total_equity
11. cash_and_equivalents
12. accounts_receivable
13. inventory
14. accounts_payable
15. long_term_debt

##### Tab 2: Sub-Calculations

Calculated fields derived from extracted datapoints:

| Sub-Field | Calculated Value | Status |
|-----------|------------------|--------|
| Total Operating Expenses | 987,654 | ✓ Calculated |
| EBITDA | 246,913 | ✓ Calculated |
| Working Capital | 123,456 | ✓ Calculated |
| ... | ... | ... |

##### Tab 3: Financial Ratios (15+ Ratios)

Comprehensive financial health analysis:

**Liquidity Ratios:**
- Current Ratio: 2.15 (✓ Healthy if > 1.0)
- Quick Ratio: 1.80
- Cash Ratio: 0.95

**Leverage Ratios:**
- Debt-to-Equity: 0.65
- Debt Ratio: 0.40
- Equity Ratio: 0.60
- Interest Coverage: 5.2

**Profitability Ratios:**
- Return on Equity (ROE): 12.5%
- Return on Assets (ROA): 8.3%
- Net Profit Margin: 15.2%
- EBITDA Margin: 22.1%

**Efficiency Ratios:**
- Asset Turnover: 1.45
- Days Sales Outstanding (DSO): 45 days
- Days Inventory Outstanding (DIO): 60 days
- Cash Conversion Cycle: 30 days

#### Step 6: Download Excel Report

Click **"Download Excel Report"** to export all results:

**Excel File Contents:**
- **Sheet 1: Extracted Datapoints** - All 15 values with metadata
- **Sheet 2: Sub-Calculations** - Derived calculations
- **Sheet 3: Financial Ratios** - Complete ratio analysis
- **Sheet 4: Summary** - Company name, extraction date, success rate

### API Endpoints

```bash
# Extract financial data from PDF
POST http://localhost:8000/api/v1/grant-thornton/extract
Content-Type: multipart/form-data

Form Data:
- pdf_file: <annual_report.pdf>
- company_name: "Merit Software Services"  # optional
- session_id: <session_id>  # optional

# Check POC status
GET http://localhost:8000/api/v1/customer/grant_thornton/status
```

### Expected Behavior

✅ **Success Indicators:**
- All 15 datapoints extracted with status "✓ Found"
- Page numbers populated for each datapoint
- Reference notes describe where value was found
- Financial ratios calculated (no null values)
- Excel file downloads successfully
- Success rate: 90-100%

✅ **Partial Success:**
- 10-14 datapoints extracted (success rate: 67-93%)
- Some ratios null due to missing dependent datapoints
- Still useful for analysis

❌ **Error Indicators:**
- "Please upload a PDF file" - Wrong file type
- "Extraction failed" - Processing error
- < 10 datapoints extracted (success rate < 67%)
- No Excel file generated

### Extraction Quality Factors

**High Quality Results (90-100% success):**
- Well-formatted annual report
- Clear financial statement tables
- Standard accounting terminology
- Recent PDF (not scanned image)

**Medium Quality Results (60-90% success):**
- Non-standard formatting
- Some tables as images
- Unconventional field names
- Older PDF format

**Low Quality Results (<60% success):**
- Scanned image PDF (no text layer)
- Heavily formatted/styled tables
- Missing financial statements
- Non-English or mixed language

### Tips for Best Results

1. **Use Official Reports:** Annual reports from company websites work best
2. **Check PDF Text:** Open PDF and try to copy text - if you can't, OCR may fail
3. **Standard Format:** IFRS/GAAP formatted statements preferred
4. **Complete Statements:** Ensure Income Statement, Balance Sheet, and Cash Flow present
5. **Company Name:** Always enter for better Excel organization

---

## Test Cases

### Test Case Format

Each test case includes:
- **TC ID:** Unique test case identifier
- **Objective:** What we're testing
- **Prerequisites:** Required setup
- **Steps:** Numbered steps to execute
- **Expected Result:** What should happen
- **Actual Result:** What actually happened (to be filled during testing)
- **Status:** Pass/Fail/Blocked

---

### British Council POC - Test Cases

#### TC-BC-001: Profile Analysis - Valid Input

**Objective:** Verify profile extraction from natural language input

**Prerequisites:**
- Frontend accessible at http://localhost:3001
- Backend operational
- British Council POC selected in sidebar

**Steps:**
1. Navigate to British Council POC
2. Enter input:
   ```
   I am a marketing professional with 3 years of experience.
   I want to learn digital marketing and data analytics.
   I prefer online courses and have intermediate English proficiency.
   ```
3. Click "Analyze Profile"
4. Wait for response

**Expected Result:**
- Profile extracted successfully
- Skills include: Marketing, Digital Marketing, Data Analytics
- Preferred format: Online
- Language proficiency: Intermediate
- No errors displayed

**Actual Result:** _[To be filled during testing]_

**Status:** _[Pass/Fail]_

---

#### TC-BC-002: Course Recommendations - Technical Skills

**Objective:** Verify course matching for technical skills

**Prerequisites:**
- Frontend accessible
- Backend operational
- British Council courses uploaded to database

**Steps:**
1. Navigate to British Council POC
2. Enter input:
   ```
   Software developer, 5 years Python experience, want to learn AI/ML,
   prefer online, bachelor's degree, English fluent
   ```
3. Click "Get Recommendations"
4. Wait for results

**Expected Result:**
- 10 course recommendations returned
- Top 3 recommendations have match score > 0.6
- Recommended courses related to AI/ML/Python
- Each course has "reasons" list populated
- Courses sorted by match score (descending)

**Actual Result:** _[To be filled during testing]_

**Status:** _[Pass/Fail]_

---

#### TC-BC-003: Error Handling - Empty Input

**Objective:** Verify error handling for empty input

**Prerequisites:**
- Frontend accessible
- Backend operational

**Steps:**
1. Navigate to British Council POC
2. Leave text area empty
3. Click "Get Recommendations"

**Expected Result:**
- Error message displayed: "Please enter your learning goals and preferences"
- No API call made
- No recommendations shown

**Actual Result:** _[To be filled during testing]_

**Status:** _[Pass/Fail]_

---

#### TC-BC-004: Match Score Calculation

**Objective:** Verify hybrid scoring (60% semantic + 40% profile)

**Prerequisites:**
- Backend operational with courses in database

**Steps:**
1. Navigate to British Council POC
2. Enter very specific input matching known course:
   ```
   I want to learn IELTS preparation, intermediate English,
   online format preferred, goal is to score 7.5 band
   ```
3. Click "Get Recommendations"
4. Review top recommendation

**Expected Result:**
- Top recommendation is IELTS-related course
- Match score > 0.75
- Both semantic_score and profile_score > 0.6
- Match score = (0.6 × semantic_score) + (0.4 × profile_score)

**Actual Result:** _[To be filled during testing]_

**Status:** _[Pass/Fail]_

---

### CRU Mining Intelligence POC - Test Cases

#### TC-CRU-001: Semantic Query - Environmental Risks

**Objective:** Verify semantic search pipeline for conceptual query

**Prerequisites:**
- Frontend accessible
- CRU POC selected
- Mining documents uploaded (optional - test with empty database too)

**Steps:**
1. Navigate to CRU POC
2. Enter query: "What are the key environmental risks?"
3. Click "Query"
4. Wait for response

**Expected Result (with documents):**
- Query classified as "SEMANTIC"
- Pipeline used: "pgvector" or "pgvector (ES unavailable)"
- Answer returned with citations [1], [2], [3]
- Confidence score populated
- 3-5 source documents listed

**Expected Result (without documents):**
- Message: "No documents found in database yet. Upload mining documents to enable queries."
- Confidence: 0.3 (low)

**Actual Result:** _[To be filled during testing]_

**Status:** _[Pass/Fail]_

---

#### TC-CRU-002: Keyword Query - Document Finding

**Objective:** Verify keyword search routing for exact term queries

**Prerequisites:**
- Mining documents with "Gold Valley" project uploaded

**Steps:**
1. Navigate to CRU POC
2. Click sample query: "Find documents mentioning feasibility studies"
3. Click "Query"

**Expected Result:**
- Query classified as "KEYWORD" or "HYBRID"
- Pipeline used shows keyword pipeline preference
- Documents containing exact phrase "feasibility studies" returned
- Source snippets highlight matching keywords

**Actual Result:** _[To be filled during testing]_

**Status:** _[Pass/Fail]_

---

#### TC-CRU-003: Pipeline Comparison

**Objective:** Verify pipeline comparison functionality

**Prerequisites:**
- Mining documents uploaded
- Multiple pipelines available (or test pgvector-only fallback)

**Steps:**
1. Navigate to CRU POC
2. Enter query: "What is the estimated capex for the Gold Valley project?"
3. Click "Compare Pipelines"
4. Wait for results

**Expected Result:**
- Comparison view displayed
- Multiple pipeline results shown side-by-side
- Each result shows: pipeline name, answer, confidence, num_sources, processing_time
- Can compare quality across pipelines

**Expected Result (pgvector-only mode):**
- Only pgvector result shown
- Clear indication that ES unavailable
- Comparison still functional with single pipeline

**Actual Result:** _[To be filled during testing]_

**Status:** _[Pass/Fail]_

---

#### TC-CRU-004: Confidence Scoring Accuracy

**Objective:** Verify confidence score reflects answer quality

**Prerequisites:**
- Mining documents uploaded with specific project data

**Steps:**
1. Test Query 1 (should have HIGH confidence):
   - "What is the estimated capex for Gold Valley?"
   - If document has specific capex value, expect high confidence (>0.7)

2. Test Query 2 (should have MEDIUM confidence):
   - "What are general mining best practices?"
   - Broad topic, expect medium confidence (0.4-0.7)

3. Test Query 3 (should have LOW confidence):
   - "What is the weather forecast for mining sites?"
   - Irrelevant query, expect low confidence (<0.4)

**Expected Result:**
- Query 1: Confidence > 0.7, specific answer with numbers
- Query 2: Confidence 0.4-0.7, general answer
- Query 3: Confidence < 0.4, generic or no answer

**Actual Result:** _[To be filled during testing]_

**Status:** _[Pass/Fail]_

---

#### TC-CRU-005: Status Endpoint - Mode Detection

**Objective:** Verify POC status correctly reflects operational mode

**Prerequisites:**
- Backend operational

**Steps:**
1. Execute API call:
   ```bash
   curl http://localhost:8000/api/v1/customer/cru/status | jq '.'
   ```
2. Review response

**Expected Result (pgvector-only mode):**
```json
{
  "status": "operational",
  "description": "Single-pipeline RAG for mining intelligence (pgvector-only mode)",
  "tier_2_modules_used": [
    "intelligent-retrieval (pgvector)",
    "reranker (BAAI/bge-reranker-large)",
    "confidence-scorer",
    "llm-service (GPT-4o-mini)"
  ],
  "capabilities": [
    "LLM-based query classification (4 types)",
    "pgvector semantic search",
    "Cross-encoder reranking",
    "Calibrated confidence scoring",
    "Automatic query routing (pgvector fallback)",
    "MinIO path: cru/mining_intelligence/{doc_id}",
    "⚠️ Elasticsearch unavailable - running in degraded mode"
  ]
}
```

**Actual Result:** _[To be filled during testing]_

**Status:** _[Pass/Fail]_

---

### Grant Thornton POC - Test Cases

#### TC-GT-001: Full Extraction - High Quality PDF

**Objective:** Verify complete extraction from well-formatted annual report

**Prerequisites:**
- Frontend accessible
- Grant Thornton POC selected
- High-quality annual report PDF available (e.g., Fortune 500 company)

**Steps:**
1. Navigate to Grant Thornton POC
2. Enter company name: "Merit Software Services"
3. Click "Upload Annual Report PDF"
4. Select test PDF file
5. Wait for extraction (30-90 seconds)
6. Review all three tabs

**Expected Result:**
- Progress bar reaches 100%
- All 15 datapoints extracted (success_rate: 100%)
- Each datapoint has:
  - ✓ Found status
  - Page number populated
  - Reference notes describing location
- All sub-calculations completed
- All 15+ financial ratios calculated (no null values)
- Excel file downloadable
- Processing time < 2 minutes

**Actual Result:** _[To be filled during testing]_

**Status:** _[Pass/Fail]_

---

#### TC-GT-002: Partial Extraction - Medium Quality PDF

**Objective:** Verify graceful degradation with imperfect PDF

**Prerequisites:**
- Medium-quality PDF (some formatting issues)

**Steps:**
1. Navigate to Grant Thornton POC
2. Upload medium-quality PDF
3. Wait for extraction
4. Review results

**Expected Result:**
- 10-14 datapoints extracted (success_rate: 67-93%)
- Some datapoints have "⚠️ Not Found" status
- Sub-calculations completed where possible
- Some financial ratios null due to missing dependencies
- Excel still downloadable with partial data
- Clear indication of which datapoints were not found

**Actual Result:** _[To be filled during testing]_

**Status:** _[Pass/Fail]_

---

#### TC-GT-003: Error Handling - Wrong File Type

**Objective:** Verify file type validation

**Prerequisites:**
- Grant Thornton POC accessible

**Steps:**
1. Navigate to Grant Thornton POC
2. Attempt to upload .docx file
3. Observe response

**Expected Result:**
- Error message: "Please upload a PDF file (annual report)"
- No extraction initiated
- No API call made

**Actual Result:** _[To be filled during testing]_

**Status:** _[Pass/Fail]_

---

#### TC-GT-004: Financial Ratios - Formula Validation

**Objective:** Verify financial ratio calculations are mathematically correct

**Prerequisites:**
- PDF with known financial values

**Test Data:**
```
total_assets: 1,000,000
current_assets: 600,000
total_liabilities: 400,000
current_liabilities: 200,000
total_equity: 600,000
net_income: 120,000
total_revenue: 800,000
```

**Steps:**
1. Upload test PDF
2. Wait for extraction
3. Navigate to "Ratios" tab
4. Manually verify calculations:
   - Current Ratio = current_assets / current_liabilities = 600,000 / 200,000 = 3.0
   - Debt-to-Equity = total_liabilities / total_equity = 400,000 / 600,000 = 0.67
   - Net Profit Margin = (net_income / total_revenue) × 100 = (120,000 / 800,000) × 100 = 15%
   - ROA = (net_income / total_assets) × 100 = (120,000 / 1,000,000) × 100 = 12%

**Expected Result:**
- All calculated ratios match manual calculations
- Ratios displayed with 2 decimal precision
- Percentages show % symbol

**Actual Result:** _[To be filled during testing]_

**Status:** _[Pass/Fail]_

---

#### TC-GT-005: Excel Export - Content Validation

**Objective:** Verify Excel export contains all data correctly formatted

**Prerequisites:**
- Successful extraction completed

**Steps:**
1. Complete extraction
2. Click "Download Excel Report"
3. Open downloaded Excel file
4. Verify sheets and content

**Expected Result:**
- Excel file downloads successfully
- File name format: `grant_thornton_<company>_<timestamp>.xlsx`
- Contains 4 sheets:
  1. **Datapoints** - All 15 rows with columns: field_name, value, page_no, status, reference_notes
  2. **Sub_Calculations** - Calculated values with columns: sub_field_name, calculated_value, status
  3. **Financial_Ratios** - All ratios with columns: ratio_name, value, category
  4. **Summary** - Metadata: company_name, extraction_date, success_rate, total_datapoints
- All values formatted correctly (numbers, percentages, currency)
- No #REF or #VALUE errors

**Actual Result:** _[To be filled during testing]_

**Status:** _[Pass/Fail]_

---

#### TC-GT-006: Progress Tracking - Real-time Updates

**Objective:** Verify progress bar updates during extraction

**Prerequisites:**
- Grant Thornton POC accessible

**Steps:**
1. Upload PDF
2. Observe progress bar and stage messages
3. Record timestamps for each stage

**Expected Result:**
- Progress bar animates smoothly 0% → 100%
- Stage messages update in sequence:
  1. "Uploading PDF..." (0-10%)
  2. "Extracting datapoints... (1/15)" (10-60%)
  3. "Extracting datapoints... (15/15)" (60%)
  4. "Calculating sub-totals..." (60-70%)
  5. "Computing financial ratios..." (70-90%)
  6. "Exporting to Excel..." (90-100%)
- Each stage transition visible
- No progress bar jumps or freezes

**Actual Result:** _[To be filled during testing]_

**Status:** _[Pass/Fail]_

---

### Cross-POC Integration Test Cases

#### TC-INT-001: Sidebar Navigation

**Objective:** Verify seamless navigation between POCs

**Steps:**
1. Navigate to British Council POC
2. Enter some data
3. Click CRU POC in sidebar
4. Verify CRU interface loads
5. Click Grant Thornton POC
6. Verify Grant Thornton interface loads
7. Click back to British Council
8. Verify previous data is NOT persisted (expected - each POC is stateless)

**Expected Result:**
- All POCs load successfully
- No errors during navigation
- UI transitions smoothly
- Each POC shows its unique interface

**Actual Result:** _[To be filled during testing]_

**Status:** _[Pass/Fail]_

---

#### TC-INT-002: All POCs Status Check

**Objective:** Verify all POC endpoints are operational

**Steps:**
```bash
# Check all three POCs
curl http://localhost:8000/api/v1/customer/british_council/status
curl http://localhost:8000/api/v1/customer/cru/status
curl http://localhost:8000/api/v1/customer/grant_thornton/status
```

**Expected Result:**
- All three endpoints return 200 OK
- All three return `"status": "operational"`
- Each has unique description and capabilities
- Response time < 500ms for each

**Actual Result:** _[To be filled during testing]_

**Status:** _[Pass/Fail]_

---

#### TC-INT-003: Frontend Display - All POCs Visible

**Objective:** Verify all three POCs appear in sidebar

**Steps:**
1. Open frontend: http://localhost:3001
2. Locate "Customer Solutions (Tier 3)" section in sidebar
3. Count POCs listed

**Expected Result:**
- 6 POCs total visible:
  1. British Council POC
  2. CRU POC
  3. **Grant Thornton POC** ← Previously missing, now visible
  4. GT Motive POC
  5. Solera POC
  6. Construction Monitor POC
- All have status: "live"
- All are clickable

**Actual Result:** _[To be filled during testing]_

**Status:** _[Pass/Fail]_

---

## Troubleshooting

### Common Issues and Solutions

#### British Council POC

**Issue:** No recommendations returned
**Cause:** No courses uploaded to database
**Solution:** Upload British Council course catalog to system first

**Issue:** All match scores are very low (<0.3)
**Cause:** Input too vague or no relevant courses
**Solution:** Be more specific with skills, goals, and preferences

---

#### CRU POC

**Issue:** "No documents found in database yet"
**Cause:** No mining documents uploaded
**Solution:** Upload mining documents (PDFs, reports) to system

**Issue:** All queries show "pgvector (ES unavailable)"
**Cause:** Elasticsearch service not started
**Solution:** This is expected behavior - CRU runs in degraded mode. To enable full mode:
```bash
docker-compose up -d elasticsearch
docker-compose restart backend
```

**Issue:** Low confidence scores for specific queries
**Cause:** Documents don't contain specific information
**Solution:** Upload more comprehensive mining documents or rephrase query

---

#### Grant Thornton POC

**Issue:** Very low success rate (<50%)
**Cause:** PDF is scanned image without text layer
**Solution:** Use text-based PDF, not scanned images

**Issue:** Excel download fails
**Cause:** Backend storage issue or MinIO unavailable
**Solution:** Check backend logs and MinIO service status

**Issue:** Some financial ratios are null
**Cause:** Missing dependent datapoints
**Solution:** Normal behavior when not all 15 datapoints are found. Review which datapoints are missing.

---

### Backend Connectivity Issues

**Symptom:** All POCs show "Failed to connect" errors

**Diagnosis:**
```bash
# Check backend status
docker-compose ps backend

# Check backend logs
docker-compose logs backend --tail=50

# Check backend health
curl http://localhost:8000/health
```

**Solutions:**
1. Restart backend: `docker-compose restart backend`
2. Check if ports are available: `netstat -an | grep 8000`
3. Verify Docker containers running: `docker-compose ps`

---

### Frontend Loading Issues

**Symptom:** POCs not appearing in sidebar

**Diagnosis:**
```bash
# Check frontend status
docker-compose ps frontend

# Check frontend logs
docker-compose logs frontend --tail=50

# Check browser console for JavaScript errors
```

**Solutions:**
1. Hard refresh browser: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)
2. Clear browser cache
3. Restart frontend: `docker-compose restart frontend`
4. Rebuild frontend: `docker-compose build frontend && docker-compose restart frontend`

---

## Test Execution Checklist

### Pre-Test Setup

- [ ] All Docker containers running (`docker-compose ps`)
- [ ] Backend healthy (`curl http://localhost:8000/health`)
- [ ] Frontend accessible (`http://localhost:3001`)
- [ ] All three POCs visible in sidebar
- [ ] Test data prepared (PDFs, sample queries)

### Test Execution

- [ ] Execute all British Council test cases (TC-BC-001 to TC-BC-004)
- [ ] Execute all CRU test cases (TC-CRU-001 to TC-CRU-005)
- [ ] Execute all Grant Thornton test cases (TC-GT-001 to TC-GT-006)
- [ ] Execute integration test cases (TC-INT-001 to TC-INT-003)

### Post-Test

- [ ] Record all actual results
- [ ] Mark all test cases as Pass/Fail
- [ ] Document any bugs found
- [ ] Update this document with findings
- [ ] Report critical issues

---

## Test Results Summary Template

**Test Date:** _____________
**Tester:** _____________
**Environment:** Local Docker (http://localhost:3001)

| POC | Total Tests | Passed | Failed | Blocked | Pass Rate |
|-----|-------------|--------|--------|---------|-----------|
| British Council | 4 | | | | |
| CRU | 5 | | | | |
| Grant Thornton | 6 | | | | |
| Integration | 3 | | | | |
| **TOTAL** | **18** | | | | |

**Critical Issues Found:**
_[List any blocking issues]_

**Recommendations:**
_[Any suggestions for improvement]_

---

## Additional Resources

- **POC Enablement Doc:** `BRITISH_COUNCIL_CRU_POC_ENABLEMENT.md`
- **Backend Logs:** `docker-compose logs backend`
- **Frontend Logs:** `docker-compose logs frontend`
- **API Documentation:** http://localhost:8000/api/docs
- **GraphQL Playground:** http://localhost:8000/graphql

---

**End of User Guide and Test Cases**
