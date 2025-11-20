# Phase 3 Testing Guide - End-to-End Testing

> **Last Updated**: 2025-11-16
> **Phase**: 3 - LangGraph Workflows & Advanced Processing

---

## 🎯 Overview

This guide provides complete instructions for testing the Phase 3 extraction workflow implementation.

**What You'll Test:**
- ✅ LangGraph workflow orchestration
- ✅ Parallel URL scraping
- ✅ Data processing pipeline
- ✅ Multiple output formats (Excel, CSV, JSON, XML, Parquet)
- ✅ Delivery channels (Download, Email, Webhook, Storage)
- ✅ Progress tracking
- ✅ Quality metrics

---

## 📋 Prerequisites

### 1. Backend Running

Make sure the backend is running:

```bash
cd backend
uvicorn app.main:app --reload
```

You should see:
```
✓ Extraction Workflow API router registered (Phase 3: LangGraph workflows)
```

### 2. Dependencies Installed

Make sure all dependencies are installed:

```bash
cd backend
pip install -r requirements.txt
```

**Key dependencies needed:**
- `langgraph>=0.2.16`
- `pandas>=2.0.0`
- `openpyxl>=3.1.2`
- `httpx>=0.27.0`

### 3. Check API is Available

```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy"}`

---

## 🚀 Quick Start - Command Line Testing

### Test 1: Simple Extraction with cURL

```bash
# Create an extraction job
curl -X POST http://localhost:8000/api/v1/extraction/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com", "https://httpbin.org/html"],
    "output_format": "excel",
    "delivery_method": "download",
    "scrape_config": {
      "compliance_level": "balanced",
      "max_concurrent_requests": 2
    }
  }'
```

**Response:**
```json
{
  "job_id": "abc123...",
  "status": "pending",
  "created_at": "2025-11-16T...",
  "urls_count": 2,
  "output_format": "excel",
  "delivery_method": "download"
}
```

### Test 2: Check Job Status

```bash
# Replace JOB_ID with the ID from above
curl http://localhost:8000/api/v1/extraction/jobs/{JOB_ID}
```

**Response:**
```json
{
  "job_id": "abc123...",
  "status": "completed",
  "current_step": "completed",
  "progress_percentage": 100.0,
  "urls_total": 2,
  "urls_processed": 2,
  "successful_scrapes": 2,
  "failed_scrapes": 0,
  "records_extracted": 2,
  "quality_score": 95.5,
  "output_file_path": "/tmp/abc123.xlsx",
  "delivery_success": true,
  "errors": [],
  "warnings": [],
  "total_duration_seconds": 5.23
}
```

### Test 3: Download Result

```bash
# Download the generated file
curl http://localhost:8000/api/v1/extraction/jobs/{JOB_ID}/download \
  -o result.xlsx
```

### Test 4: List All Jobs

```bash
curl http://localhost:8000/api/v1/extraction/jobs
```

---

## 🐍 Python Test Script (Automated)

We've provided a comprehensive test script that tests all features.

### Run the Test Script

```bash
# Make executable
chmod +x test_phase3_extraction.py

# Run all tests
python test_phase3_extraction.py
```

**The script tests:**
1. ✅ Simple extraction (Excel + Download)
2. ✅ Multiple output formats (CSV, JSON, XML, Parquet)
3. ✅ Parallel processing (10 URLs concurrently)
4. ✅ List jobs
5. ✅ Download results
6. ✅ Error handling

**Expected Output:**
```
================================================================================
                Phase 3 Extraction Workflow - End-to-End Test Suite
================================================================================

ℹ Backend URL: http://localhost:8000
✓ Backend is running ✓

================================================================================
                     TEST 1: Simple Extraction (Excel + Download)
================================================================================

ℹ Creating extraction job...
✓ Job created: abc123-456-789
   URLs: 2
   Format: excel
   Delivery: download
ℹ Monitoring job progress...
   Progress:  10.0% - parsing_template
   Progress:  20.0% - planning_extraction
   Progress:  30.0% - scraping_sources
   Progress:  60.0% - consolidating_data
   Progress: 100.0% - completed

✓ Job completed successfully!

Results:
   Status: completed
   URLs Processed: 2/2
   Successful: 2
   Failed: 0
   Records Extracted: 2
   Quality Score: 95.50%
   Duration: 5.23s
   Output File: /tmp/abc123.xlsx

[... more tests ...]

================================================================================
                              Test Summary
================================================================================

✓ Simple Extraction: PASSED
✓ Multiple Formats: PASSED
✓ Parallel Processing: PASSED
✓ List Jobs: PASSED
✓ Download Result: PASSED
✓ Error Handling: PASSED

Overall: 6/6 tests passed
```

---

## 🌐 API Documentation

### Base URL
```
http://localhost:8000/api/v1/extraction
```

### Endpoints

#### 1. Create Extraction Job

**POST** `/jobs`

**Request Body:**
```json
{
  "urls": ["https://example.com"],
  "template_id": null,
  "output_format": "excel",
  "delivery_method": "download",
  "delivery_config": {},
  "scrape_config": {
    "compliance_level": "balanced",
    "max_concurrent_requests": 5,
    "enable_smart_scraping": true,
    "scrape_prompt": "Extract pricing and features"
  },
  "session_id": null
}
```

**Output Formats:**
- `excel` - Rich Excel with formatting
- `csv` - CSV file
- `json` - JSON file
- `xml` - XML file
- `parquet` - Parquet for analytics

**Delivery Methods:**
- `download` - Direct file access
- `email` - Send via email (requires SMTP config)
- `webhook` - POST to webhook URL
- `storage` - Upload to cloud storage (S3/MinIO)

**Response:**
```json
{
  "job_id": "uuid",
  "status": "pending",
  "created_at": "datetime",
  "urls_count": 1,
  "output_format": "excel",
  "delivery_method": "download"
}
```

#### 2. Get Job Status

**GET** `/jobs/{job_id}`

**Response:**
```json
{
  "job_id": "uuid",
  "status": "completed",
  "current_step": "completed",
  "progress_percentage": 100.0,
  "urls_total": 5,
  "urls_processed": 5,
  "successful_scrapes": 5,
  "failed_scrapes": 0,
  "records_extracted": 125,
  "quality_score": 92.5,
  "output_file_path": "/path/to/file.xlsx",
  "delivery_success": true,
  "errors": [],
  "warnings": [],
  "started_at": "datetime",
  "completed_at": "datetime",
  "total_duration_seconds": 12.34
}
```

**Status Values:**
- `pending` - Job created, not started
- `running` - Workflow in progress
- `completed` - Successfully completed
- `completed_with_errors` - Completed with some errors
- `failed` - Workflow failed

#### 3. Get Job Result

**GET** `/jobs/{job_id}/result`

**Response:**
```json
{
  "job_id": "uuid",
  "status": "completed",
  "output_file_path": "/path/to/file.xlsx",
  "output_file_size": 12345,
  "records_extracted": 100,
  "quality_score": 95.0,
  "download_url": "/api/v1/extraction/jobs/{job_id}/download"
}
```

#### 4. Download Result File

**GET** `/jobs/{job_id}/download`

Returns the generated file for download.

#### 5. List Jobs

**GET** `/jobs?status={status}&limit={limit}`

**Query Parameters:**
- `status` (optional): Filter by status
- `limit` (optional): Max results (default: 100)

**Response:**
```json
[
  {
    "job_id": "uuid",
    "status": "completed",
    "created_at": "datetime",
    "urls_count": 5,
    "output_format": "excel",
    "delivery_method": "download"
  }
]
```

#### 6. Delete Job

**DELETE** `/jobs/{job_id}`

Deletes job and output file.

**Response:**
```json
{
  "message": "Job {job_id} deleted successfully"
}
```

---

## 📊 Testing Different Features

### Test Parallel Processing

```bash
curl -X POST http://localhost:8000/api/v1/extraction/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://example.com",
      "https://httpbin.org/html",
      "https://httpbin.org/json",
      "https://httpbin.org/uuid",
      "https://httpbin.org/headers",
      "https://www.ietf.org/rfc/rfc2616.txt",
      "https://jsonplaceholder.typicode.com/posts/1",
      "https://jsonplaceholder.typicode.com/users/1"
    ],
    "output_format": "csv",
    "delivery_method": "download",
    "scrape_config": {
      "max_concurrent_requests": 5
    }
  }'
```

### Test Different Output Formats

**Excel (rich formatting):**
```json
{
  "urls": ["https://example.com"],
  "output_format": "excel",
  "delivery_method": "download"
}
```

**CSV (simple):**
```json
{
  "urls": ["https://example.com"],
  "output_format": "csv",
  "delivery_method": "download"
}
```

**JSON (API-friendly):**
```json
{
  "urls": ["https://example.com"],
  "output_format": "json",
  "delivery_method": "download"
}
```

**Parquet (analytics):**
```json
{
  "urls": ["https://example.com"],
  "output_format": "parquet",
  "delivery_method": "download"
}
```

### Test Email Delivery

**Prerequisites:** Set these environment variables:
```bash
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=your-email@gmail.com
export SMTP_PASSWORD=your-app-password
```

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/extraction/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "output_format": "excel",
    "delivery_method": "email",
    "delivery_config": {
      "to": "recipient@example.com",
      "subject": "Data Extraction Results",
      "body": "Please find attached the extraction results."
    }
  }'
```

### Test Webhook Delivery

```bash
curl -X POST http://localhost:8000/api/v1/extraction/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "output_format": "json",
    "delivery_method": "webhook",
    "delivery_config": {
      "url": "https://webhook.site/your-unique-url",
      "method": "POST",
      "send_as": "json"
    }
  }'
```

---

## 🐛 Troubleshooting

### Issue: "Module 'langgraph' not found"

**Solution:**
```bash
cd backend
pip install langgraph>=0.2.16
```

### Issue: "Cannot generate Excel file"

**Solution:**
```bash
pip install openpyxl>=3.1.2
```

### Issue: "Job stuck in 'pending' status"

**Cause:** Background tasks may not be processing.

**Solution:** Check backend logs for errors:
```bash
# In backend terminal, look for errors
```

### Issue: "All URLs failed"

**Possible causes:**
1. URLs are invalid or unreachable
2. Network connectivity issues
3. Compliance rules blocking access

**Solution:** Check job errors:
```bash
curl http://localhost:8000/api/v1/extraction/jobs/{JOB_ID}
```

Look at the `errors` array for details.

### Issue: "Quality score is low"

**Cause:** Data extraction or validation issues.

**Solution:**
- Check the `warnings` array for details
- Try different URLs with more structured content
- Use templates for better extraction (Phase 2)

---

## 📈 Performance Benchmarks

Expected performance metrics:

| URLs | Concurrent | Time | Throughput |
|------|-----------|------|-----------|
| 1 | 1 | 2-5s | 0.2-0.5 URL/s |
| 10 | 5 | 5-15s | 0.67-2 URL/s |
| 50 | 5 | 25-60s | 0.83-2 URL/s |
| 100 | 10 | 40-120s | 0.83-2.5 URL/s |

**Factors affecting performance:**
- URL response time
- Content size
- Scraping strategy (Playwright is slower)
- Data processing complexity
- Output format (Excel is slower than CSV)

---

## ✅ Verification Checklist

After running tests, verify:

- [ ] Jobs are created successfully
- [ ] Progress tracking works (0% → 100%)
- [ ] All output formats generate correctly
- [ ] Files can be downloaded
- [ ] Excel files have proper formatting
- [ ] Quality scores are calculated
- [ ] Error handling works for failed URLs
- [ ] Concurrent scraping works
- [ ] Jobs can be listed
- [ ] Jobs can be deleted

---

## 🔗 Next Steps

### UI Integration (Optional)

To integrate with the frontend:
1. Create a new React component for extraction jobs
2. Add job creation form
3. Add progress monitoring
4. Add result download button

### Advanced Testing

1. **Load Testing:** Test with 100+ URLs
2. **Template Testing:** Use Phase 2 templates for structured extraction
3. **Delivery Testing:** Test email and webhook delivery
4. **Storage Testing:** Test cloud storage upload (MinIO/S3)

---

## 📚 Additional Resources

- **Phase 3 Implementation Summary:** `PHASE_3_IMPLEMENTATION_SUMMARY.md`
- **API Documentation:** http://localhost:8000/docs (Swagger UI)
- **Workflow Visualization:** See `extraction_workflow.py` for DAG diagram

---

**End of Testing Guide**
