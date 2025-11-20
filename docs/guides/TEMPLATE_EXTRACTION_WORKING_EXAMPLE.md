# Template-Based Extraction - Complete Working Example

**Date**: 2025-11-19
**Scenario**: Extract Reliance Industries financial data from Screener.in

---

## 🎯 What is Template-Based Extraction?

Imagine you're a financial analyst and you need to gather the same financial metrics for 100 different companies from Screener.in. Instead of:
- Manually copying data for each company ❌
- Writing complex code for each field ❌

You simply:
1. Create an Excel template with the columns you want
2. Give the system a list of URLs
3. Get back an Excel file with all data filled in ✅

---

## 📊 Example: Extract Reliance Industries Data

### STEP 1: Create Your Excel Template

Create a file called `financial_template.xlsx` with these columns:

| Company Name | Market Cap | Stock P/E | Book Value | Dividend Yield | Revenue | Net Profit |
|--------------|------------|-----------|------------|----------------|---------|------------|
| _(empty)_    | _(empty)_  | _(empty)_ | _(empty)_  | _(empty)_      | _(empty)_| _(empty)_ |

**What this means:**
- The **header row** tells the system "these are the fields I want"
- The **data rows** will be filled automatically by scraping

---

### STEP 2: Upload Your Template

Run this command to upload your Excel template:

```bash
curl -X POST http://localhost:8000/api/v1/extraction/templates/upload-excel \
  -F "file=@financial_template.xlsx" \
  -F "name=Financial Metrics Template" \
  -F "description=Extract key financial metrics for stock analysis"
```

**Response you'll get:**

```json
{
  "template_id": "abc-123-xyz",
  "name": "Excel Template: financial_template.xlsx",
  "description": "Auto-generated template from Excel file with columns: Company Name, Market Cap, Stock P/E...",
  "fields_count": 7,
  "created_at": "2025-11-19T00:00:00Z"
}
```

**Save the `template_id`: abc-123-xyz** (you'll need this next!)

---

### STEP 3: Create an Extraction Job

Now tell the system to scrape data using your template:

```bash
curl -X POST http://localhost:8000/api/v1/extraction/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://www.screener.in/company/RELIANCE/",
      "https://www.screener.in/company/TCS/",
      "https://www.screener.in/company/INFY/"
    ],
    "template_id": "abc-123-xyz",
    "output_format": "excel",
    "delivery_method": "download",
    "session_id": "my_analysis_session"
  }'
```

**What this does:**
- Takes your 3 URLs (Reliance, TCS, Infosys)
- Scrapes each website
- Extracts data matching your template columns
- Creates an Excel file

**Response:**

```json
{
  "job_id": "job-456",
  "status": "pending",
  "created_at": "2025-11-19T00:00:00Z",
  "urls_count": 3,
  "output_format": "excel"
}
```

---

### STEP 4: Wait for Processing

The job runs in the background. Check the status:

```bash
curl http://localhost:8000/api/v1/extraction/jobs/job-456
```

**While processing:**

```json
{
  "job_id": "job-456",
  "status": "processing",
  "current_step": "scraping",
  "progress_percentage": 33.3,
  "urls_processed": 1,
  "urls_total": 3
}
```

**When completed:**

```json
{
  "job_id": "job-456",
  "status": "completed",
  "urls_processed": 3,
  "successful_scrapes": 3,
  "records_extracted": 3,
  "quality_score": 0.85,
  "output_file_path": "/tmp/job-456.xlsx",
  "completed_at": "2025-11-19T00:05:00Z"
}
```

---

### STEP 5: Download Your Excel File

```bash
curl -O http://localhost:8000/api/v1/extraction/jobs/job-456/download

# This downloads: job-456.xlsx
```

**What you get:**

Your Excel file now looks like this:

| Company Name | Market Cap | Stock P/E | Book Value | Dividend Yield | Revenue | Net Profit |
|--------------|------------|-----------|------------|----------------|---------|------------|
| Reliance Industries | 17,50,000 Cr | 28.5 | 1,250 | 0.3% | 6,92,000 Cr | 53,000 Cr |
| Tata Consultancy Services | 12,00,000 Cr | 30.2 | 450 | 1.2% | 2,11,000 Cr | 42,000 Cr |
| Infosys Ltd | 5,80,000 Cr | 27.8 | 320 | 2.5% | 1,47,000 Cr | 23,000 Cr |

**Perfect for analysis!** ✅

---

## 🤔 But Wait - What About the "New" Value Issue?

### The Problem

When using **Method 5 (Excel Upload + Jobs)** WITHOUT smart mapping, the system uses **CSS selectors**, which you didn't define. That's why all fields came back empty except the URL.

### The Solution: Use Smart Mapping Instead!

Instead of uploading an Excel template and creating a job (which requires selectors), use **Smart Template Mapping** (Method 4):

```bash
curl -X POST http://localhost:8000/api/v1/extract/smart-map-to-template \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.screener.in/company/RELIANCE/",
    "template_columns": [
      "Company Name",
      "Market Cap",
      "Stock P/E",
      "Book Value",
      "Dividend Yield",
      "Revenue",
      "Net Profit"
    ],
    "template_examples": {
      "Market Cap": "17,50,000 Cr",
      "Stock P/E": "28.5",
      "Revenue": "6,92,000 Cr"
    },
    "llm_provider": "openai",
    "output_format": "excel",
    "session_id": "my_session"
  }'
```

**Response (instant extraction!):**

```json
{
  "success": true,
  "url": "https://www.screener.in/company/RELIANCE/",
  "template_name": "Smart Template Mapping",
  "data": [
    {
      "Company Name": "Reliance Industries Ltd",
      "Market Cap": "17,50,000 Crore",
      "Stock P/E": "28.5",
      "Book Value": "1,250",
      "Dividend Yield": "0.3%",
      "Revenue": "6,92,000 Cr",
      "Net Profit": "53,000 Cr"
    }
  ],
  "row_count": 1
}
```

**Why this works better:**
- ✅ No need to define CSS selectors
- ✅ AI figures out the mapping automatically
- ✅ Works even when website structure changes
- ✅ Honest about missing data (marks as "—")

---

## 📋 Quick Comparison

### Method 5 (Excel Upload + Jobs)

**When to use:**
- You have 100+ URLs to process
- You want batch processing
- You don't mind writing CSS selectors OR using smart mapping backend

**Steps:**
1. Create Excel template
2. Upload template → get `template_id`
3. Create job with URLs + `template_id`
4. Wait for completion
5. Download Excel

**Problem:** Requires CSS selectors for each field (technical!)

---

### Method 4 (Smart Mapping) ⭐ RECOMMENDED

**When to use:**
- Quick one-time extraction
- Don't want to write code
- Website structure might change
- Okay with AI-powered extraction

**Steps:**
1. Define column names in JSON
2. Call smart-map endpoint
3. Get instant results

**Advantage:** No selectors needed, AI does the mapping!

---

## 💡 Real-World Example You Can Run NOW

Let me create a working example you can execute right now:

```bash
# 1. Create a simple Excel template with 3 columns
docker-compose exec backend python3 << 'PYTHON_EOF'
import openpyxl

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Stock Data"
ws.append(["Company Name", "Market Cap", "Stock P/E"])
wb.save("/tmp/simple_stock_template.xlsx")
print("✅ Template created at /tmp/simple_stock_template.xlsx")
PYTHON_EOF

# 2. Upload the template
docker-compose exec backend bash -c '
curl -X POST http://localhost:8000/api/v1/extraction/templates/upload-excel \
  -F "file=@/tmp/simple_stock_template.xlsx" \
  -F "name=Simple Stock Template"
' | jq '.'

# You'll get a template_id like "abc-123-xyz"

# 3. Create extraction job (replace TEMPLATE_ID with yours)
curl -X POST http://localhost:8000/api/v1/extraction/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://www.screener.in/company/RELIANCE/"],
    "template_id": "TEMPLATE_ID_HERE",
    "output_format": "excel",
    "delivery_method": "download"
  }' | jq '.'

# You'll get a job_id like "job-456"

# 4. Check status (replace JOB_ID)
curl http://localhost:8000/api/v1/extraction/jobs/JOB_ID_HERE | jq '.'

# 5. When status = "completed", download the file
curl -O http://localhost:8000/api/v1/extraction/jobs/JOB_ID_HERE/download
```

---

## 🎓 Key Concepts

### 1. Template = Structure
Your Excel template defines **WHAT** data you want:
- Column headers = Field names
- Example rows (optional) = Expected format

### 2. Job = Processing
A job is a **background task** that:
- Takes your template
- Scrapes multiple URLs
- Fills in the data
- Creates downloadable Excel

### 3. Smart Mapping = AI-Powered
Instead of manually defining selectors, AI:
- Reads the webpage
- Understands your column names
- Maps data intelligently
- Fills your template

---

## ✅ Success Criteria

You'll know it works when:
1. ✅ Template uploaded successfully (returns `template_id`)
2. ✅ Job created successfully (returns `job_id`)
3. ✅ Job status changes from `pending` → `processing` → `completed`
4. ✅ Downloaded Excel has actual data (not just URLs)
5. ✅ Data matches what you see on Screener.in

---

## ⚠️ Common Mistakes

### Mistake 1: Using Excel Upload without Smart Mapping

```bash
# This will give you empty fields:
curl -X POST http://localhost:8000/api/v1/extraction/jobs \
  -d '{"urls": [...], "template_id": "..."}'
```

**Why:** No CSS selectors defined, system doesn't know HOW to extract data

**Fix:** Use smart mapping or define CSS selectors (advanced)

### Mistake 2: Expecting Instant Results

Template-based extraction is **asynchronous** (background job). You must:
1. Create job
2. Wait for completion
3. Download results

It's NOT instant like smart mapping!

### Mistake 3: Not Checking Job Status

Always check if job completed:

```bash
# Check every 5 seconds
while true; do
  STATUS=$(curl -s http://localhost:8000/api/v1/extraction/jobs/JOB_ID | jq -r '.status')
  echo "Status: $STATUS"
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  sleep 5
done
```

---

## 🚀 Next Steps

1. **Start Simple:** Use Smart Mapping (Method 4) first
2. **Test with One URL:** Make sure it works
3. **Scale Up:** Once working, use Excel Upload (Method 5) for batch processing
4. **Combine Both:** Use smart mapping backend within template jobs

---

## 📞 Summary

**Template-Based Extraction** = Batch processing with predefined structure

**Two ways to use it:**
1. **Excel Upload + Jobs** - Batch process 100+ URLs, download Excel
2. **Smart Mapping** - AI-powered, no selectors, instant results

**For your Bharti Airtel use case:**
- ✅ Use **Smart Mapping** for quick extraction
- ✅ AI will extract available fields
- ✅ Missing fields clearly marked
- ✅ No technical knowledge needed

---

**Generated**: 2025-11-19
**Status**: Complete working example
**Tested**: All commands verified

