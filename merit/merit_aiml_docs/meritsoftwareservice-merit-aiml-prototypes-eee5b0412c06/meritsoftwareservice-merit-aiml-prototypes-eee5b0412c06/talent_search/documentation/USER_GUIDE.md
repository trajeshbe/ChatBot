# TalentSearch - User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [User Interface Overview](#user-interface-overview)
4. [Upload Tab](#upload-tab)
5. [Search Tab](#search-tab)
6. [Alerts Tab](#alerts-tab)
7. [Advanced Features](#advanced-features)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)
10. [FAQs](#faqs)

---

## Introduction

TalentSearch is an AI-powered recruitment platform that helps you organize, search, and manage job postings efficiently. The system automatically extracts metadata from job postings, matches them with appropriate recruiters, and provides powerful search capabilities.

### Who Is This For?

- **Recruitment Agencies**: Manage large volumes of job postings and route them to specialized recruiters
- **HR Departments**: Organize internal job postings and track recruitment efforts
- **Talent Acquisition Teams**: Quickly find relevant positions and match them with recruiter expertise
- **Job Board Administrators**: Enhance job categorization and search capabilities

### Key Benefits

- **Time Savings**: Automated metadata extraction eliminates manual tagging
- **Better Matching**: AI-powered recruiter assignments based on expertise
- **Powerful Search**: Natural language and semantic search capabilities
- **Advanced Filtering**: Multi-criteria filtering for precise results
- **Scalable**: Handle hundreds of job postings efficiently

---

## Getting Started

### Prerequisites

Before using TalentSearch, ensure you have:

1. **Access to the Application**: URL or local installation
2. **Job Data**: Excel (.xlsx) or CSV (.csv) file with job postings
3. **Basic Understanding**: Familiarity with job posting terminology

### First-Time Setup

1. **Launch the Application**
   ```bash
   streamlit run app.py
   ```
   The application will open in your browser at `http://localhost:8501`

2. **Verify Configuration**
   - Check that the title "TalentSearch" appears at the top
   - Verify three tabs are visible: Search, Alerts, Upload

3. **Prepare Your Data**
   - Ensure your job data is in Excel or CSV format
   - Include columns like job_title, company, location, description, etc.

---

## User Interface Overview

TalentSearch features a three-tab interface designed for different workflows:

```
┌─────────────────────────────────────────────────────────┐
│                     TalentSearch                         │
├─────────────────────────────────────────────────────────┤
│  [Search]  [Alerts]  [Upload]                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Tab Content Area                                        │
│                                                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Navigation

- **Tab Selection**: Click on tab names to switch between sections
- **Sidebar**: Appears on the left for search filters and options
- **Main Area**: Displays content specific to the active tab

---

## Upload Tab

The Upload tab is your starting point for adding job data to the system.

### Step-by-Step Upload Process

#### Step 1: Prepare Your Data File

**Supported Formats:**
- Excel (.xlsx)
- CSV (.csv)

**Required Columns for Raw Data:**
- company
- corporate_title
- job_title
- job_function
- city
- state
- country
- division
- jobType
- time_type
- description
- category
- job_posted_date
- salaryRange

**Example Data Structure:**

| company | job_title | description | city | country | salaryRange |
|---------|-----------|-------------|------|---------|-------------|
| Citibank | Software Engineer | Develop applications... | New York | USA | 80000-120000 |
| Citibank | Data Analyst | Analyze business data... | London | UK | 50000-70000 |

#### Step 2: Upload the File

1. **Click "Browse files"** in the Upload tab
2. **Select your file** from your computer
3. **Choose data type**:
   - **Uncheck "Use tagged data"** if uploading raw job postings (system will generate metadata)
   - **Check "Use tagged data"** if your file already has all metadata fields

#### Step 3: Submit

1. **Click "Submit"** button
2. **Wait for processing**:
   - "Uploading..." spinner appears
   - For raw data: "Creating Meta Information" spinner shows
   - For tagged data: Direct import

3. **Verify success**:
   - "Upload Completed" message appears in green
   - Data is now ready for searching

### Understanding Tagged vs. Untagged Data

#### Untagged (Raw) Data
**When to use:** You have basic job posting information

**What happens:**
1. System extracts metadata using AI:
   - Domain and business sector
   - Work arrangement (Remote/Hybrid/On-site)
   - Seniority level
   - Location details
   - Contract type
2. Matches with appropriate recruiter
3. Generates relevance score and justification

**Processing time:** ~30 seconds for 2 records

#### Tagged Data
**When to use:** You already have complete metadata

**What happens:**
1. Direct import to database
2. No AI processing needed
3. Immediate availability for search

**Processing time:** ~2 seconds

### Upload Examples

#### Example 1: Uploading Raw Job Postings

```
File: jobs_raw.xlsx
Columns: company, job_title, description, city, country, job_posted_date

Action:
1. Click Upload tab
2. Select jobs_raw.xlsx
3. Leave "Use tagged data" UNCHECKED
4. Click Submit
5. Wait for "Creating Meta Information"
6. See "Upload Completed" message

Result:
- 2 jobs processed and tagged
- Metadata automatically generated
- Ready for search
```

#### Example 2: Uploading Pre-Tagged Data

```
File: jobs_tagged.xlsx
Columns: All metadata fields including domain, sector, recruiter_name, etc.

Action:
1. Click Upload tab
2. Select jobs_tagged.xlsx
3. CHECK "Use tagged data"
4. Click Submit
5. Brief upload process

Result:
- Jobs imported directly
- No AI processing
- Immediately searchable
```

### Upload Tips

1. **Sample Data First**: Test with a small file to verify format
2. **Check Column Names**: Ensure they match expected structure
3. **Clean Data**: Remove duplicate entries before upload
4. **Date Format**: Use standard date formats (YYYY-MM-DD)
5. **Salary Format**: Use numeric ranges (e.g., "80000-120000")

### Common Upload Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "Server Issue. Try again..." | Invalid file format or corrupt data | Check file format and data integrity |
| Processing takes too long | Large file size | Currently processes 2 records per upload |
| No metadata generated | LLM API issue | Check API keys and internet connection |
| Wrong company name | Hardcoded default | System sets company to "citibank" by default |

---

## Search Tab

The Search tab provides powerful search and filtering capabilities for finding relevant job postings.

### Search Interface Components

```
┌─────────────────────────────────────────────────────────┐
│ Sidebar                    │ Main Area                   │
│                           │                             │
│ [Keyword Search Field]    │  [Results DataFrame]        │
│ [Search Button]           │                             │
│ [Clear Button]            │  ┌──────────────────┐       │
│                           │  │ JOB TITLE 1      │       │
│ [Filter Fields]           │  └──────────────────┘       │
│  - Domain                 │  ┌──────────────────┐       │
│  - Sector                 │  │ JOB TITLE 2      │       │
│  - Location               │  └──────────────────┘       │
│  - Seniority              │                             │
│  - Date Range             │                             │
└───────────────────────────┴─────────────────────────────┘
```

### How to Search

#### Basic Keyword Search

1. **Go to Search tab**
2. **Enter keywords** in the sidebar search field
   - Example: "software engineer"
   - Example: "finance analyst New York"
3. **Click "Search" button**
4. **View results** in the main area

#### Semantic Search

Natural language queries are supported:

**Examples:**
- "Find python developer jobs in California"
- "Show me senior finance positions"
- "Remote data science roles"
- "Investment banking jobs posted last month"

**How it works:**
1. Your query is converted to SQL using AI
2. Database is queried
3. Results are displayed

#### Search Results

**Results Display:**
- **DataFrame view**: Tabular format with all columns
- **Expandable cards**: Click to see detailed information

**Result Fields:**
- Job Title
- Description
- Company Name
- Domain
- Sector
- Work Arrangement
- Location (City, Country, Region)
- Contract Type
- Seniority
- Date Posted
- Salary Range
- Job Type
- Assigned Recruiter
- Relevance Score
- Justification

### Using Filters

Filters allow you to narrow down search results based on specific criteria.

#### Accessing Filters

1. **After search**, click "Choose Filter Field(s)" in sidebar
2. **Select fields** to filter by (multi-select)
3. **Set filter values** for each selected field
4. **Results update automatically**

#### Filter Types

##### 1. Categorical Filters
**Used for:** Domain, Sector, Work Arrangement, Contract Type, Seniority

**Example:**
```
Field: Domain
Options: [Finance, IT, Engineering]
Action: Select one or multiple
```

##### 2. Numeric Filters
**Used for:** Salary ranges

**Example:**
```
Field: salary_low
Range slider: 50,000 - 150,000
Action: Drag to set range
```

##### 3. Date Filters
**Used for:** Date Posted

**Example:**
```
Field: date_posted
Date picker: 2024-01-01 to 2024-12-31
Action: Select date range
```

##### 4. Text Filters
**Used for:** Job Title, Description

**Example:**
```
Field: job_title
Input: "senior"
Action: Shows jobs with "senior" in title
```

**Supports regex:**
```
Field: description
Input: "python|java"
Action: Shows jobs mentioning Python OR Java
```

### Search Examples

#### Example 1: Find All IT Jobs

```
1. In sidebar: Enter "IT jobs"
2. Click Search
3. Results show all IT domain positions
4. Add filter:
   - Choose Filter Field: domain
   - Select: IT
5. Refined results displayed
```

#### Example 2: Senior Finance Roles in New York

```
1. Enter: "senior finance New York"
2. Click Search
3. Add filters:
   - Seniority: Senior
   - Domain: Finance
   - Location City: New York
4. View filtered results
5. Expand cards for details
```

#### Example 3: Remote Jobs Posted Recently

```
1. Enter: "remote jobs"
2. Click Search
3. Add filters:
   - Work Arrangement: Remote
   - Date Posted: Last 30 days
4. See current remote opportunities
```

### Clearing Search Results

**To reset and reload all data:**

1. **Click "Clear" button** in sidebar
2. **Filters are cleared**
3. **Original dataset reloaded** from database
4. **Toast notification**: "Filter(s) cleared"

### Search Tips

1. **Start Broad**: Begin with general terms, then filter
2. **Use Filters**: More effective than complex search queries
3. **Combine Methods**: Use keyword search + filters together
4. **Check Expandables**: Click job titles for full details
5. **Clear Regularly**: Reset filters when starting new search

### Search Best Practices

| Goal | Best Approach |
|------|---------------|
| Find specific role | Use job title in search + seniority filter |
| Location-based search | Use location in query + location filters |
| Industry-specific | Filter by domain and sector |
| Recent postings | Use date filter with range |
| Salary range | Use numeric filters on salary fields |
| Multiple criteria | Combine search with multiple filters |

---

## Alerts Tab

The Alerts tab displays recruiter-specific job assignments and allows filtering by recruiter.

### Interface Overview

```
┌─────────────────────────────────────────────────────────┐
│  [Recruiter Dropdown: All Recruiters ▼]                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Job Listings DataFrame                                 │
│                                                          │
│  | Job Title | Company | Domain | Recruiter | Score |   │
│  | Software  | Citibank| IT     | Riley A.  | 92    |   │
│  | Analyst   | Citibank| Finance| Alex M.   | 88    |   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### How to Use Alerts

#### View All Recruiter Assignments

1. **Go to Alerts tab**
2. **Select "All Recruiters"** in dropdown
3. **View complete list** of jobs with assigned recruiters

**Table includes:**
- All job details
- Assigned recruiter name
- Relevance score
- Justification for match

#### Filter by Specific Recruiter

1. **Click recruiter dropdown**
2. **Select a recruiter name**:
   - Alex Morgan (Finance)
   - Jordan Lee (Engineering)
   - Taylor Brooks (Supply Chain)
   - Casey Blake (Life Sciences)
   - Riley Anderson (IT)
   - Morgan Bennett (Legal)
3. **View jobs assigned to that recruiter**

### Understanding Recruiter Profiles

#### Alex Morgan - Finance Specialist
**Industries:** Finance, Investment Banking, Fintech
**Regions:** Global (New York, London, Hong Kong)
**Seniority:** Mid to Senior, C-level

**Assigned when job involves:**
- Financial analysis
- Banking operations
- Fintech products
- Investment roles

#### Jordan Lee - Engineering & Infrastructure
**Industries:** Engineering, Renewable Energy, Construction
**Regions:** North America, Europe, APAC
**Seniority:** Entry to Senior

**Assigned when job involves:**
- Engineering roles
- Infrastructure projects
- Energy sector
- Construction management

#### Taylor Brooks - Supply Chain & Logistics
**Industries:** Supply Chain, Logistics, Procurement
**Regions:** North America, Europe, Asia-Pacific
**Seniority:** Mid to Senior

**Assigned when job involves:**
- Supply chain management
- Logistics coordination
- Procurement processes
- Operations management

#### Casey Blake - Life Sciences Specialist
**Industries:** Pharmaceuticals, Biotechnology, Medical Devices
**Regions:** Global (biotech hubs)
**Seniority:** Entry to Senior

**Assigned when job involves:**
- R&D positions
- Regulatory affairs
- Biotech research
- Medical devices

#### Riley Anderson - IT & Technology
**Industries:** IT, Cybersecurity, Software Development
**Regions:** North America, Europe, Asia
**Seniority:** Mid to Senior

**Assigned when job involves:**
- Software development
- IT infrastructure
- Cybersecurity
- Technology management

#### Morgan Bennett - Legal & Regulatory
**Industries:** Legal, Compliance, Corporate Law
**Regions:** Global (major legal markets)
**Seniority:** Mid to Senior

**Assigned when job involves:**
- Legal advisory
- Compliance roles
- Corporate law
- Regulatory affairs

### Relevance Scoring

Each job-recruiter match includes a relevance score (0-100):

**Score Ranges:**
- **90-100**: Perfect match (industry, location, seniority align)
- **80-89**: Strong match (most criteria align)
- **70-79**: Good match (key criteria align)
- **60-69**: Moderate match (some criteria align)
- **Below 60**: Weak match (limited alignment)

**Justification Field:**
Explains why the recruiter was chosen:
- Industry expertise match
- Geographic coverage
- Seniority level handling
- Specific skills alignment

### Alerts Examples

#### Example 1: View Alex Morgan's Jobs

```
1. Go to Alerts tab
2. Select "Alex Morgan" from dropdown
3. See all Finance/Banking jobs
4. Review relevance scores
5. Read justifications

Sample Result:
Job: Investment Analyst
Score: 95
Justification: "Perfect match - Finance sector, New York location,
               Mid-senior level aligns with Alex Morgan's expertise
               in investment banking and financial hubs"
```

#### Example 2: Check All IT Assignments

```
1. Go to Alerts tab
2. Select "Riley Anderson"
3. View all IT/Tech jobs
4. Sort by relevance score
5. Identify top matches

Use case: Review Riley's workload and prioritize high-scoring positions
```

#### Example 3: Compare Assignments

```
1. View "All Recruiters"
2. Identify jobs with similar scores across recruiters
3. Review justifications
4. Make manual adjustments if needed

Use case: Quality check AI assignments
```

### Alerts Best Practices

1. **Regular Review**: Check alerts daily for new assignments
2. **Prioritize by Score**: Focus on high-scoring matches first
3. **Read Justifications**: Understand why matches were made
4. **Track Workload**: Monitor distribution across recruiters
5. **Verify Assignments**: Confirm AI matches make sense

---

## Advanced Features

### Multi-Criteria Filtering

Combine multiple filters for precise results:

**Example: Find specific role type**
```
Filters:
- Domain: IT
- Sector: Software Development
- Seniority: Senior
- Work Arrangement: Remote
- Salary Low: > 100,000
- Date Posted: Last 60 days

Result: Senior remote software positions with high salary, posted recently
```

### Regex Search in Text Fields

Use regular expressions for advanced text matching:

**Examples:**
```
Pattern: "senior|lead"
Matches: Jobs with "senior" OR "lead" in field

Pattern: "^Senior.*Engineer$"
Matches: Titles starting with "Senior" and ending with "Engineer"

Pattern: "python|java|javascript"
Matches: Jobs mentioning any of these programming languages
```

### Date Range Analysis

Find jobs within specific timeframes:

**Examples:**
```
Last week: date_posted between (today - 7 days) and today
This month: date_posted in current month
Q1 2024: date_posted between 2024-01-01 and 2024-03-31
```

### Salary Range Queries

Filter by compensation:

**Examples:**
```
High-paying: salary_low > 120,000
Mid-range: salary_low between 60,000 and 100,000
Entry-level: salary_low < 50,000
```

### Exporting Results

While not built-in, you can:

1. **Copy data** from displayed DataFrame
2. **Use browser tools** to save table
3. **Screenshot** results for sharing

---

## Best Practices

### Data Management

1. **Regular Updates**: Upload new jobs consistently
2. **Data Quality**: Ensure clean, complete data before upload
3. **Avoid Duplicates**: Remove duplicate entries
4. **Standardize Formats**: Use consistent date and salary formats
5. **Verify Uploads**: Check "Upload Completed" message

### Search Strategies

1. **Start Simple**: Begin with basic keywords
2. **Refine Gradually**: Add filters incrementally
3. **Use Appropriate Filters**: Match filter type to search goal
4. **Clear Between Searches**: Reset filters for new queries
5. **Save Common Queries**: Document frequently used searches

### Recruiter Assignments

1. **Review Scores**: Check relevance scores make sense
2. **Verify Matches**: Confirm recruiter expertise aligns
3. **Monitor Distribution**: Ensure balanced workload
4. **Read Justifications**: Understand matching logic
5. **Provide Feedback**: Note any mismatches for improvement

### Performance Optimization

1. **Smaller Batches**: Upload smaller files for faster processing
2. **Filter Early**: Apply filters before extensive browsing
3. **Clear Cache**: Clear browser cache if slow
4. **Limit Results**: Use date filters to reduce result size
5. **Close Tabs**: Keep only necessary browser tabs open

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Please upload the Job List"

**Cause:** No data has been uploaded yet

**Solution:**
1. Go to Upload tab
2. Select and upload a job data file
3. Click Submit and wait for completion

---

#### Issue: "No Relevant Postings"

**Cause:** Search returned no matching results

**Solutions:**
1. **Broaden search terms**: Use more general keywords
2. **Remove filters**: Clear some restrictive filters
3. **Check spelling**: Verify search terms are correct
4. **Try different terms**: Use synonyms or related terms
5. **Clear and reload**: Click Clear button to reset

---

#### Issue: Slow Processing During Upload

**Cause:** AI processing takes time for metadata generation

**Solutions:**
1. **Be patient**: Processing 2 records takes ~30 seconds
2. **Use tagged data**: If metadata exists, check "Use tagged data"
3. **Check connection**: Ensure stable internet for API calls
4. **Verify API keys**: Confirm OpenAI key is valid

---

#### Issue: Search Not Working

**Cause:** Database or session state issue

**Solutions:**
1. **Refresh page**: Reload the browser
2. **Re-upload data**: Upload data file again
3. **Clear filters**: Click Clear button
4. **Check console**: Look for error messages

---

#### Issue: Filters Not Applying

**Cause:** Filter state issue

**Solutions:**
1. **Deselect and reselect**: Clear filter and reapply
2. **Click Clear**: Reset all filters
3. **Refresh page**: Reload application
4. **Check filter values**: Ensure valid values selected

---

#### Issue: Wrong Recruiter Assignments

**Cause:** AI interpretation variation

**Solutions:**
1. **Check justification**: Read why recruiter was chosen
2. **Review job details**: Ensure metadata is accurate
3. **Consider edge cases**: Some jobs may fit multiple recruiters
4. **Manual override**: Document and adjust as needed

---

#### Issue: Upload Fails with "Server Issue"

**Cause:** File format or data error

**Solutions:**
1. **Check file format**: Ensure .xlsx or .csv
2. **Verify columns**: Confirm required columns exist
3. **Remove special characters**: Clean data entries
4. **Test with sample**: Try uploading 2-3 rows first
5. **Check file size**: Ensure reasonable file size

---

## FAQs

### General Questions

**Q: How many jobs can I upload at once?**
A: The system currently processes 2 records per upload batch due to sampling in the code. For larger datasets, you may need to modify the sample size or upload multiple times.

**Q: What file formats are supported?**
A: Excel (.xlsx) and CSV (.csv) files are supported.

**Q: Is my data stored securely?**
A: Data is stored in a local SQLite database (example.db). For production use, implement additional security measures.

**Q: Can I delete uploaded data?**
A: Currently, new uploads replace existing data in the database. There's no built-in delete function for specific records.

**Q: How accurate are the AI-generated tags?**
A: Accuracy depends on the quality of input data and job descriptions. Review generated metadata for verification.

### Search Questions

**Q: What's the difference between keyword and semantic search?**
A: Keyword search looks for exact matches, while semantic search understands intent and meaning, converting natural language to SQL queries.

**Q: How many results are returned per search?**
A: By default, searches are limited to 20 results. This is configurable in the SQL query generation.

**Q: Can I search across multiple fields simultaneously?**
A: Yes, semantic search automatically searches across the 'content' field, which concatenates all job fields.

**Q: How do I clear my search history?**
A: Search history is not persisted. Clicking Clear resets the current search.

### Recruiter Questions

**Q: Can I add new recruiters?**
A: Yes, edit the `recruiter.json` file to add new recruiter profiles.

**Q: Can a job be assigned to multiple recruiters?**
A: Currently, each job is assigned to one best-fit recruiter. The system chooses the highest relevance match.

**Q: What if I disagree with a recruiter assignment?**
A: Review the justification field. The assignment is AI-generated and may be manually overridden in your workflow.

**Q: How is the relevance score calculated?**
A: The LLM evaluates job characteristics against recruiter profiles and assigns a 0-100 score based on alignment.

### Technical Questions

**Q: What LLM model is used?**
A: OpenAI GPT-4o-mini is the default model, configurable in config.ini.

**Q: Where is data stored?**
A: Data is stored in example.db (SQLite database) in the application directory.

**Q: Can I run this offline?**
A: No, the application requires internet connectivity for LLM API calls to OpenAI.

**Q: What are the API costs?**
A: Costs depend on usage. Approximately 6 API calls per 2 jobs uploaded, plus 1 call per search query. Check OpenAI pricing for current rates.

**Q: Can I customize the metadata fields?**
A: Yes, modify `output_columns` in config.ini and update the Pydantic models in custom_templates.py.

### Workflow Questions

**Q: What's the recommended workflow for new job postings?**
A:
1. Upload new jobs via Upload tab
2. Review assignments in Alerts tab
3. Use Search tab to find specific roles
4. Export or note relevant matches

**Q: How often should I upload new data?**
A: Upload frequency depends on your needs. Daily or weekly uploads are common for active recruitment.

**Q: Can multiple users access the system simultaneously?**
A: The current SQLite implementation supports single-user access. For multi-user, consider migrating to PostgreSQL or MySQL.

**Q: How do I backup my data?**
A: Copy the example.db file regularly. Also maintain backups of your original upload files.

---

## Getting Help

### Resources

1. **Documentation**:
   - README.md - Project overview
   - ARCHITECTURE.md - Technical details
   - API_REFERENCE.md - Developer reference
   - DEPLOYMENT.md - Setup and configuration

2. **Logs**:
   - Check `./logs/DD-MM-YY/HH.log` for error details

3. **Sample Data**:
   - Review `data/samples.xlsx` for format examples
   - Check `data/meta_sample.xlsx` for tagged data format

### Support Workflow

1. **Check this guide** for common issues
2. **Review logs** for error messages
3. **Verify configuration** in config.ini and .env
4. **Test with sample data** to isolate issues
5. **Contact support** with specific error details

### Reporting Issues

When reporting problems, include:
- Description of the issue
- Steps to reproduce
- Error messages from logs
- Screenshot if applicable
- Data format sample (if relevant)

---

## Appendix

### Keyboard Shortcuts (Streamlit)

- **Ctrl+R** / **Cmd+R**: Refresh application
- **Tab**: Navigate between UI elements
- **Enter**: Submit forms

### Column Reference

**Job Posting Fields:**
- job_title
- description
- company_name
- domain
- sector
- work_arrangement
- location_city
- location_country
- location_region
- contract_type
- seniority
- date_posted
- salary_low
- salary_high
- type_of_job
- recruiter_name
- relevence_score
- justification

### Domain and Sector Examples

**Finance Domain:**
- Investment Banking
- Retail Banking
- Fintech

**IT Domain:**
- Software Development
- Cybersecurity
- IT Infrastructure

**Engineering Domain:**
- Civil Engineering
- Renewable Energy
- Construction

**Life Sciences Domain:**
- Pharmaceuticals
- Biotechnology
- Medical Devices

**Legal Domain:**
- Corporate Law
- Compliance
- Regulatory Affairs

### Seniority Levels

1. Intern
2. Junior
3. Mid-senior
4. Senior
5. Senior Leadership

### Work Arrangements

- On-site
- Remote
- Flexible/Hybrid

### Contract Types

- Permanent
- Contract
- Temporary
- Internship

---

## Quick Reference Card

### Essential Tasks

| Task | Tab | Action |
|------|-----|--------|
| Upload jobs | Upload | Select file → Submit |
| Search jobs | Search | Enter query → Search |
| Filter results | Search | Choose filters → Select values |
| View by recruiter | Alerts | Select recruiter from dropdown |
| Clear search | Search | Click Clear button |
| Reset filters | Search | Clear button → Filter(s) cleared |

### Common Searches

```
General role: "software engineer"
Location-specific: "analyst New York"
Remote work: "remote developer"
Senior positions: "senior finance"
Recent postings: Use date filter
Salary range: Use salary_low filter
```

### Quick Tips

1. Always upload data first
2. Start searches broad, then filter
3. Check relevance scores in Alerts
4. Use Clear to reset between searches
5. Review justifications for recruiter assignments

---

**End of User Guide**

For technical details, see ARCHITECTURE.md and API_REFERENCE.md.
For deployment instructions, see DEPLOYMENT.md.
