# Web Scraper Job Monitor Guide

## Table of Contents

1. [Overview](#overview)
2. [What is the Job Monitor?](#what-is-the-job-monitor)
3. [Getting Started](#getting-started)
4. [Features](#features)
5. [Job Lifecycle](#job-lifecycle)
6. [Monitoring Jobs](#monitoring-jobs)
7. [Understanding Job Status](#understanding-job-status)
8. [Downloading Results](#downloading-results)
9. [Troubleshooting](#troubleshooting)
10. [API Reference](#api-reference)

---

## Overview

The **Job Monitor** is a real-time dashboard for tracking and managing large-scale web scraping and data extraction jobs. It provides comprehensive visibility into job progress, status, and results, making it easy to monitor long-running extraction workflows.

### Key Benefits

- **Real-time Tracking**: Monitor job progress with live updates
- **Detailed Metrics**: View URLs processed, success rates, quality scores, and more
- **Auto-refresh**: Automatically updates running jobs every 10 seconds
- **Download Results**: Easily download extracted data in multiple formats
- **Error Visibility**: See warnings and errors for debugging

---

## What is the Job Monitor?

The Job Monitor is the third tab in the Enterprise Web Scraper interface. It displays all extraction jobs created through the **Template Extraction** tab, providing a centralized view of:

- All extraction jobs (past and present)
- Current job status and progress
- Detailed job metrics and statistics
- Output files ready for download
- Errors and warnings for troubleshooting

### When to Use the Job Monitor

Use the Job Monitor when you:
- Have created an extraction job and want to track its progress
- Need to download results from completed jobs
- Want to monitor multiple jobs simultaneously
- Need to troubleshoot failed extractions
- Want to review historical job performance

---

## Getting Started

### Accessing the Job Monitor

1. Navigate to the **Enterprise Web Scraper** in your application
2. Click on the **Job Monitor** tab (third tab with the chart icon)
3. The monitor will automatically load all recent jobs

### First Time Use

When you first open the Job Monitor:
1. If you haven't created any jobs yet, you'll see an empty state
2. Create a job in the **Template Extraction** tab first
3. Return to the Job Monitor to see your job's progress
4. The list will automatically refresh if auto-refresh is enabled

---

## Features

### 1. Job List View

The main view shows all extraction jobs in a card-based layout:

- **Job ID**: Unique identifier for each job
- **Status Badge**: Visual indicator (Pending, Running, Completed, Failed)
- **Progress Bar**: Visual progress indicator (0-100%)
- **Key Metrics**: URLs processed, success rate, records extracted
- **Timestamps**: Created and completed times
- **Actions**: View details, download, delete

### 2. Auto-Refresh

- **Toggle**: Enable/disable auto-refresh in the top-right corner
- **Interval**: Updates every 10 seconds when enabled
- **Smart Refresh**: Only refreshes jobs with `pending` or `running` status
- **Performance**: Doesn't refresh if all jobs are completed/failed

### 3. Job Details Panel

Click on any job card to view detailed information:

#### Overview Section
- Full job status and current workflow step
- Progress percentage and time estimates
- URLs total vs. processed
- Success and failure counts

#### Extraction Metrics
- Records extracted from all URLs
- Quality score (0-1 scale)
- Average processing time per URL
- Data validation results

#### Configuration
- Output format (Excel, CSV, JSON, etc.)
- Delivery method (Download, Email, Webhook, Storage)
- Compliance level used
- Template applied (if any)

#### Errors & Warnings
- List of all errors encountered
- Warnings for potential issues
- Timestamps for debugging
- Suggested fixes

#### Download Section
- File path and size information
- Direct download button
- Format-specific options

### 4. Job Actions

#### View Details
Click on a job card to expand the details panel with comprehensive information.

#### Download Results
- Click the **Download** button on completed jobs
- Supports multiple formats: Excel, CSV, JSON, XML, Parquet
- File is downloaded directly to your browser's download folder
- File naming: `extraction_results_{timestamp}.{format}`

#### Delete Job
- Click the **Trash** icon to delete a job
- Confirmation prompt prevents accidental deletion
- Deletes both job metadata and output files
- Cannot be undone

#### Refresh
- Manual refresh button updates all jobs immediately
- Use when auto-refresh is disabled
- Useful for checking latest status

---

## Job Lifecycle

Understanding the job lifecycle helps you know what to expect:

### 1. **Pending**
- Job created but not yet started
- Waiting in queue for processing
- Usually brief (seconds)

### 2. **Running**
The job is actively executing through multiple steps:

#### Step 1: Initialization
- Setting up workflow
- Validating configuration
- Loading templates (if used)

#### Step 2: URL Scraping
- Fetching content from all URLs
- Parallel processing (up to max_concurrent)
- Compliance checks applied

#### Step 3: Data Extraction
- Extracting structured data using template
- Applying CSS selectors, XPath, or LLM extraction
- Field validation

#### Step 4: Data Processing
- Cleaning and normalizing data
- Applying preprocessing rules
- Quality scoring

#### Step 5: Output Generation
- Converting to requested format
- Creating Excel/CSV/JSON file
- Calculating file size

#### Step 6: Delivery
- Saving file to storage
- Sending via email (if configured)
- Calling webhook (if configured)

### 3. **Completed**
- All steps finished successfully
- Output file ready for download
- Final metrics calculated

### 4. **Failed**
- Job encountered unrecoverable error
- Partial results may be available
- Error details visible in details panel

---

## Monitoring Jobs

### Real-Time Progress Tracking

For running jobs, you can monitor:

#### Progress Percentage
- Visual progress bar shows 0-100% completion
- Calculated based on current step and URLs processed
- Updates every 10 seconds with auto-refresh

#### Current Step
- Shows which workflow step is executing
- Examples: "Scraping URLs", "Extracting Data", "Generating Output"
- Helps estimate remaining time

#### URLs Processed
- Shows: "15/50 URLs processed"
- Success vs. failure breakdown
- Individual URL status available in details

#### Real-Time Metrics
- Records extracted so far
- Quality score (updates as data is processed)
- Estimated time remaining

### Understanding Quality Scores

The quality score (0.0 - 1.0) indicates data extraction quality:

- **0.9 - 1.0**: Excellent - All required fields extracted
- **0.7 - 0.9**: Good - Most fields extracted, minor issues
- **0.5 - 0.7**: Fair - Significant missing data
- **< 0.5**: Poor - Major extraction failures

Quality is calculated based on:
- Required fields successfully extracted
- Data validation rule compliance
- Extraction confidence scores
- Missing or malformed data

---

## Understanding Job Status

### Status Badges

Jobs display colored status badges for quick identification:

#### Pending (Yellow)
- **Meaning**: Job created, waiting to start
- **Action**: Wait, typically starts within seconds
- **Icon**: Clock icon

#### Running (Blue)
- **Meaning**: Job actively executing
- **Action**: Monitor progress, check current step
- **Icon**: Loader animation

#### Completed (Green)
- **Meaning**: Job finished successfully
- **Action**: Download results
- **Icon**: Checkmark

#### Failed (Red)
- **Meaning**: Job encountered error
- **Action**: Review errors in details panel
- **Icon**: X circle

### Progress Indicators

#### Progress Bar
- Shows visual completion percentage
- Color matches status badge
- Animates during execution

#### Step Indicator
- Shows current workflow step name
- Example: "Step 3/6: Extracting Data"
- Helps understand what's happening

#### Time Tracking
- **Started At**: When job began executing
- **Completed At**: When job finished (if completed)
- **Duration**: Total time elapsed
- **Estimated Completion**: Time remaining (for running jobs)

---

## Downloading Results

### Download Process

1. **Locate Completed Job**
   - Look for jobs with green "Completed" badge
   - Check that "Records Extracted" count is > 0

2. **Access Download Options**
   - Click job card to open details panel
   - Scroll to "Download Results" section
   - Verify file size and format

3. **Download File**
   - Click blue **"Download Results"** button
   - File downloads to browser's download folder
   - Filename format: `extraction_results_{timestamp}.{ext}`

4. **Open Results**
   - Excel: Open in Microsoft Excel, Google Sheets, LibreOffice
   - CSV: Import into spreadsheet or data tools
   - JSON: Use in code, APIs, or JSON viewers
   - XML: Parse with XML tools
   - Parquet: Load into data analysis tools (Pandas, Spark)

### Output Formats

#### Excel (.xlsx)
- **Best For**: Manual review, business users
- **Features**: Multiple sheets, formatting, formulas
- **Tools**: Excel, Google Sheets, Numbers

#### CSV (.csv)
- **Best For**: Data import, simple analysis
- **Features**: Plain text, universal compatibility
- **Tools**: Any spreadsheet or text editor

#### JSON (.json)
- **Best For**: APIs, web applications, code integration
- **Features**: Structured, nested data, machine-readable
- **Tools**: Code editors, jq, JSON viewers

#### XML (.xml)
- **Best For**: Legacy systems, SOAP APIs
- **Features**: Hierarchical structure, schema validation
- **Tools**: XML parsers, browsers

#### Parquet (.parquet)
- **Best For**: Big data, analytics, data lakes
- **Features**: Columnar storage, compression, fast queries
- **Tools**: Pandas, Spark, BigQuery

### Delivery Methods

Besides direct download, jobs can deliver results via:

#### Email Delivery
- Configure recipient emails in job creation
- Receives attachment with results file
- Email sent upon job completion

#### Webhook Delivery
- POST results to specified webhook URL
- Includes job metadata and download link
- Useful for automation workflows

#### Cloud Storage
- Upload to S3, GCS, Azure Blob
- Configure bucket and path
- Automatic upload on completion

---

## Troubleshooting

### Common Issues

#### Job Stuck in "Pending"
**Symptoms**: Job shows "Pending" for more than 30 seconds

**Possible Causes**:
- Server overloaded with other jobs
- Background worker not running
- Database connection issues

**Solutions**:
1. Wait a few minutes and refresh
2. Check server logs for errors
3. Verify backend services are running
4. Contact administrator if persists

#### Job Failed Immediately
**Symptoms**: Job goes from "Pending" to "Failed" in seconds

**Possible Causes**:
- Invalid URLs provided
- Template not found
- Configuration error
- Authentication failed

**Solutions**:
1. Click job to view error details
2. Check URL format and accessibility
3. Verify template ID is correct
4. Review delivery configuration
5. Check compliance settings

#### Low Quality Score
**Symptoms**: Job completes but quality score < 0.7

**Possible Causes**:
- Template selectors don't match page structure
- Required fields missing from pages
- LLM extraction failed
- Data validation rules too strict

**Solutions**:
1. Review template configuration
2. Test selectors on target pages
3. Adjust required vs. optional fields
4. Update validation rules
5. Use LLM extraction as fallback

#### Download Button Disabled
**Symptoms**: Cannot click download button on completed job

**Possible Causes**:
- Output file not generated
- File deleted from storage
- No records extracted
- Browser permissions issue

**Solutions**:
1. Check "Records Extracted" count
2. Review job errors in details
3. Verify storage configuration
4. Try different browser
5. Re-run extraction job

#### Auto-Refresh Not Working
**Symptoms**: Job status doesn't update automatically

**Possible Causes**:
- Auto-refresh toggle is off
- Browser tab inactive (browser throttling)
- Network connectivity issues

**Solutions**:
1. Check auto-refresh toggle (top-right)
2. Keep browser tab active
3. Use manual refresh button
4. Check network connection

### Error Messages

#### "Template {template_id} not found"
- The template was deleted after job creation
- Upload template again or create job without template

#### "Failed to scrape URL: {url}"
- URL is inaccessible or returns error
- Check URL validity and server status
- Review compliance settings (may be blocking access)

#### "Extraction failed: No selectors matched"
- CSS/XPath selectors in template don't match page
- Inspect page structure and update template
- Consider using LLM extraction instead

#### "Validation failed: Required field missing"
- Required field in template not found in scraped data
- Make field optional or fix extraction selectors

#### "Delivery failed: {error}"
- Email sending failed
- Webhook URL unreachable
- Storage upload error
- Check delivery configuration and credentials

---

## API Reference

### List All Jobs

```bash
GET /api/v1/extraction/jobs
```

**Query Parameters**:
- `status` (optional): Filter by status (pending, running, completed, failed)
- `limit` (optional): Max number of jobs to return (default: 100)

**Response**:
```json
{
  "jobs": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "created_at": "2024-01-15T10:30:00Z",
      "urls_count": 50,
      "output_format": "excel",
      "delivery_method": "download"
    }
  ]
}
```

### Get Job Details

```bash
GET /api/v1/extraction/jobs/{job_id}
```

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "current_step": "Extracting Data",
  "progress_percentage": 65.0,
  "urls_total": 50,
  "urls_processed": 32,
  "successful_scrapes": 30,
  "failed_scrapes": 2,
  "records_extracted": 450,
  "quality_score": 0.85,
  "errors": [],
  "warnings": [
    {
      "step": "scraping",
      "url": "https://example.com/page3",
      "warning": "Rate limit warning",
      "timestamp": "2024-01-15T10:35:00Z"
    }
  ],
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": null,
  "total_duration_seconds": null
}
```

### Download Job Results

```bash
GET /api/v1/extraction/jobs/{job_id}/download
```

**Response**: Binary file download

**Content-Type**: Depends on output format
- Excel: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- CSV: `text/csv`
- JSON: `application/json`
- XML: `application/xml`
- Parquet: `application/octet-stream`

### Delete Job

```bash
DELETE /api/v1/extraction/jobs/{job_id}
```

**Response**:
```json
{
  "message": "Job 550e8400-e29b-41d4-a716-446655440000 deleted successfully"
}
```

---

## Best Practices

### 1. Job Naming & Organization
- Use descriptive job configurations
- Track jobs by created_at timestamp
- Delete old jobs regularly to reduce clutter

### 2. Monitoring Strategy
- Enable auto-refresh for active monitoring
- Disable auto-refresh when reviewing historical jobs
- Use manual refresh for on-demand updates

### 3. Error Handling
- Always review errors on failed jobs
- Check warnings even on successful jobs
- Update templates based on error patterns

### 4. Performance Optimization
- Use appropriate max_concurrent_requests (5-10)
- Balance compliance level vs. speed
- Monitor quality scores and adjust templates

### 5. Data Quality
- Set realistic quality thresholds
- Use validation rules appropriately
- Review extracted data samples
- Iterate on template improvements

---

## Advanced Features

### Custom Delivery Webhooks

Configure webhooks for automation:

```json
{
  "delivery_method": "webhook",
  "delivery_config": {
    "webhook_url": "https://your-api.com/webhook",
    "headers": {
      "Authorization": "Bearer YOUR_TOKEN"
    },
    "include_data": true
  }
}
```

Webhook receives POST request:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "records_extracted": 450,
  "quality_score": 0.85,
  "download_url": "https://api.example.com/download/...",
  "metadata": {
    "urls_total": 50,
    "successful_scrapes": 48
  }
}
```

### Email Notifications

```json
{
  "delivery_method": "email",
  "delivery_config": {
    "email_to": ["analyst@company.com", "manager@company.com"],
    "subject": "Extraction Job Complete: Product Data",
    "include_attachment": true
  }
}
```

### Cloud Storage Integration

```json
{
  "delivery_method": "storage",
  "delivery_config": {
    "storage_provider": "s3",
    "storage_bucket": "my-data-bucket",
    "storage_path": "extractions/products/2024-01-15/"
  }
}
```

---

## Frequently Asked Questions

### How long do jobs remain in the monitor?
Jobs persist indefinitely until manually deleted. Clean up old jobs periodically.

### Can I re-run a failed job?
Not directly. Create a new job with the same configuration from the Template Extraction tab.

### What's the maximum number of URLs per job?
Currently limited to 100 URLs per job. For larger batches, create multiple jobs.

### How are concurrent requests controlled?
Set `max_concurrent_requests` in job configuration (1-20). Default is 5.

### Can I pause a running job?
Not currently supported. You can delete the job to stop it.

### What happens if my browser closes during a job?
Jobs run on the server, so they continue even if you close the browser. Return to the Job Monitor to check progress.

### How do I know if a job is stuck?
If progress percentage doesn't change after 5+ minutes and status is "Running", the job may be stuck. Check server logs.

### Can I export job metrics for reporting?
Yes, use the API endpoints to fetch job data programmatically and build custom reports.

---

## Support

For additional help:
- Check backend logs for detailed error traces
- Review the API documentation at `/api/docs`
- Contact your system administrator
- Report bugs via GitHub Issues

---

**Last Updated**: 2024-11-16
**Version**: 1.0.0
