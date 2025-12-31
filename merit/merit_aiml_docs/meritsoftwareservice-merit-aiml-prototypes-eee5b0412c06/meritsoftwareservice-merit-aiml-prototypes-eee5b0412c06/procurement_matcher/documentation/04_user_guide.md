# User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Legal Case Matcher](#legal-case-matcher)
4. [Procurement Matcher](#procurement-matcher)
5. [Vendor Taxonomy Classifier](#vendor-taxonomy-classifier)
6. [Understanding Results](#understanding-results)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Introduction

### What is Procurement Matcher?

Procurement Matcher is an AI-powered web application that helps you:

1. **Find Relevant Legal Precedents**: Match historical legal cases with your current case based on legal issues and reasoning
2. **Evaluate Vendors**: Compare vendor capabilities against your procurement requirements
3. **Classify Vendors**: Extract structured information from vendor descriptions automatically

### Who Should Use This?

- **Legal Professionals**: Lawyers, paralegals, and legal researchers looking for relevant precedents
- **Procurement Managers**: Teams evaluating multiple vendors for projects
- **Business Analysts**: Professionals who need to categorize and analyze vendor information

### Key Benefits

- **Save Time**: Process multiple documents in minutes instead of hours
- **Objective Analysis**: Get AI-driven confidence scores with clear explanations
- **Structured Data**: Transform unstructured PDFs into organized, sortable tables
- **Easy to Use**: Simple web interface with drag-and-drop file upload

## Getting Started

### Prerequisites

Before using the application, ensure you have:

1. **System Requirements**:
   - Modern web browser (Chrome, Firefox, Safari, Edge)
   - Internet connection
   - Files ready for upload (PDF and TXT formats)

2. **File Preparation**:
   - **PDF files**: Vendor profiles or legal precedent cases
   - **TXT files**: Current requirements or case descriptions
   - Ensure files are not password-protected
   - Maximum recommended file size: 10MB per file

### Accessing the Application

#### Local Installation

If running locally, follow these steps:

1. **Install Dependencies**:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install requirements
pip install streamlit langchain langchain-core openai pydantic pymupdf pandas pyyaml python-dotenv loguru
```

2. **Configure API Key**:

Create a `.env` file in the application directory:
```bash
OPENAI_API_KEY=your_api_key_here
```

Replace `your_api_key_here` with your actual OpenAI API key.

3. **Start the Application**:
```bash
streamlit run app.py
```

4. **Access in Browser**:

The application will open automatically, or navigate to:
```
http://localhost:8501
```

### Application Interface Overview

When you open the application, you'll see three tabs:

```
┌─────────────────────────────────────────────────────┐
│  Legal  │  Procurement  │  Vendor Taxonomy          │
└─────────────────────────────────────────────────────┘
```

Each tab provides a different matching or classification function.

## Legal Case Matcher

### Purpose

The Legal Case Matcher helps you find relevant precedent cases by comparing them with your current case. The AI analyzes legal issues and reasoning patterns, not just keywords.

### Step-by-Step Instructions

#### Step 1: Navigate to Legal Tab

Click on the "Legal" tab at the top of the page.

#### Step 2: Prepare Your Files

You need two types of files:

1. **Precedent Cases** (PDF format):
   - Historical legal cases you want to compare
   - Can upload multiple files (e.g., 5-10 cases)
   - Each file should contain case details, facts, and legal reasoning

2. **Current Case** (TXT format):
   - Your current case description
   - Should include key facts and legal issues
   - Plain text format (.txt)

**Example Current Case File (current_case.txt)**:
```
Case: Smith v. TechCorp Employment Discrimination

Facts:
- Employee terminated after 15 years
- Claims age discrimination
- Company cited performance issues
- No prior performance warnings documented

Legal Issues:
- Age Discrimination in Employment Act (ADEA) violation
- Burden of proof for discriminatory intent
- Sufficiency of employer's stated reason
```

#### Step 3: Upload Files

1. **Upload Precedent Cases**:
   - Click "Browse files" under "Please upload the precedent case(s)"
   - Select one or more PDF files
   - You can select multiple files at once

2. **Upload Current Case**:
   - Click "Browse files" under "Please upload the current case"
   - Select your TXT file with the case description

#### Step 4: Submit and Wait

1. Click the "Submit" button
2. Wait while the system processes your files
3. A progress bar will show the analysis progress
4. Processing time: approximately 3-5 seconds per precedent case

#### Step 5: Review Results

Results appear as a sortable table with these columns:

| Column | Description |
|--------|-------------|
| Case_Strategy | Your current case title |
| Precedent_Case | Name of the precedent case |
| Confidence_Score | Match score from 0.1 (weak) to 1.0 (strong) |
| Justification | Explanation of why cases match |

**Results are automatically sorted by Confidence_Score (highest first).**

### Example Workflow

**Scenario**: You're working on an employment discrimination case and want to find relevant precedents.

1. **Gather Precedent Cases**: Collect 10 PDF files of employment law cases
2. **Write Current Case**: Create a TXT file describing your case
3. **Upload Both**: Use the file uploaders to submit all files
4. **Review Top Matches**: Focus on cases with scores above 0.7
5. **Read Justifications**: Understand why each case is relevant

### Interpreting Results

**Confidence Score Ranges**:

- **0.9 - 1.0**: Highly relevant, very similar legal issues
- **0.7 - 0.89**: Relevant, shares key legal principles
- **0.5 - 0.69**: Somewhat relevant, partial overlap
- **0.3 - 0.49**: Limited relevance, tangential connection
- **0.1 - 0.29**: Minimal relevance, different issues

**Focus on**:
1. Top 3-5 highest scoring cases
2. Read justifications to understand the connection
3. Use these as starting points for deeper research

## Procurement Matcher

### Purpose

The Procurement Matcher evaluates vendor capabilities against your requirements, helping you identify the best-fit vendors objectively.

### Step-by-Step Instructions

#### Step 1: Navigate to Procurement Tab

Click on the "Procurement" tab at the top of the page.

#### Step 2: Prepare Your Files

You need two types of files:

1. **Vendor Profiles** (PDF format):
   - Vendor capability statements
   - Product brochures or service descriptions
   - Can upload multiple vendor files
   - Should focus on capabilities, not pricing

2. **Requirement Document** (TXT format):
   - Your project or procurement requirements
   - Technical specifications
   - Expected capabilities and features
   - Plain text format (.txt)

**Example Requirement File (requirement.txt)**:
```
Project: Enterprise Cloud Migration

Requirements:
- Infrastructure as a Service (IaaS) platform
- Support for hybrid cloud architecture
- Multi-region deployment capabilities
- 24/7 technical support
- Compliance: ISO 27001, SOC 2, GDPR
- Experience with enterprise-scale migrations (5000+ users)
- Integration with existing Active Directory
- Database migration tools included
- Disaster recovery and backup solutions
- Minimum 99.9% uptime SLA
```

#### Step 3: Upload Files

1. **Upload Vendor Profiles**:
   - Click "Browse files" under "Please upload the vendor profile(s)"
   - Select one or more PDF files
   - Tip: Upload 5-15 vendors for best results

2. **Upload Requirement Document**:
   - Click "Browse files" under "Please upload the current requirement"
   - Select your TXT file with requirements

#### Step 4: Submit and Wait

1. Click the "Submit" button
2. Monitor the progress bar
3. Processing time: approximately 3-5 seconds per vendor
4. The system analyzes capabilities, not pricing or contracts

#### Step 5: Review Results

Results appear as a sortable table:

| Column | Description |
|--------|-------------|
| Current_Requirement | Your requirement title/summary |
| Vendor_Name | Name of the vendor |
| Confidence_Score | Match score from 0.1 (poor fit) to 1.0 (excellent fit) |
| Justification | Explanation of capability alignment |

**Results are automatically sorted by Confidence_Score (highest first).**

### Example Workflow

**Scenario**: You need to select a cloud provider for enterprise migration.

1. **Define Requirements**: Create detailed requirements.txt
2. **Collect Vendor Info**: Gather capability PDFs from 10 cloud vendors
3. **Upload and Process**: Submit all files through the interface
4. **Shortlist Vendors**: Select top 3-4 with scores above 0.8
5. **Review Justifications**: Understand strengths and gaps
6. **Make Decision**: Use results to inform vendor selection

### Interpreting Results

**Confidence Score Ranges**:

- **0.9 - 1.0**: Excellent fit, meets nearly all requirements
- **0.8 - 0.89**: Strong fit, meets most key requirements
- **0.6 - 0.79**: Good fit, meets core requirements with some gaps
- **0.4 - 0.59**: Moderate fit, meets some requirements
- **0.1 - 0.39**: Poor fit, significant gaps in capabilities

**What the AI Considers**:
- Technical capability alignment
- Feature matching
- Service offering relevance
- Technology stack compatibility
- Industry experience (if mentioned)

**What the AI Ignores**:
- Pricing and cost information
- Contract terms
- Past performance metrics
- Subjective marketing language

### Best Use Cases

1. **Initial Vendor Screening**: Quickly narrow down from 20+ vendors to 5-10
2. **RFP Evaluation**: Supplement manual review with AI analysis
3. **Capability Gaps**: Identify which vendors miss critical requirements
4. **Objective Comparison**: Remove bias from vendor selection

## Vendor Taxonomy Classifier

### Purpose

The Vendor Taxonomy Classifier extracts structured information from unstructured vendor descriptions, creating a standardized categorization.

### Step-by-Step Instructions

#### Step 1: Navigate to Vendor Taxonomy Tab

Click on the "Vendor Taxonomy" tab at the top of the page.

#### Step 2: Prepare Vendor Information

You can input vendor information directly as text. Include details such as:

- Vendor name
- Products and services offered
- Business categories
- Geographic presence
- Compliance certifications
- Sustainability initiatives
- Technology platforms

**Example Input**:
```
CloudTech Solutions is a leading provider of enterprise cloud infrastructure
services. We offer Infrastructure as a Service (IaaS) and Platform as a
Service (PaaS) solutions for large organizations. Our services include cloud
hosting, managed databases, application deployment, and DevOps automation.

We operate globally with data centers in North America, Europe, and Asia-Pacific.
CloudTech is certified for ISO 27001, SOC 2 Type II, and complies with GDPR,
HIPAA, and PCI-DSS requirements.

Our platform supports multi-cloud deployments and integrates with AWS, Azure,
and Google Cloud. We serve enterprise customers in finance, healthcare, retail,
and technology sectors.

CloudTech is committed to sustainability with carbon-neutral data centers
powered by 100% renewable energy. Risk assessment: Low operational risk,
established vendor with strong financial backing.
```

#### Step 3: Enter Text

1. Click in the text area under "Please give the vendor information"
2. Paste or type vendor information
3. Recommended length: 100-1000 words for best results

#### Step 4: Submit

1. Click the "Submit" button
2. Processing is fast (1-2 seconds)
3. No progress bar needed for single-vendor classification

#### Step 5: Review Taxonomy

Results appear as a single-row table with these fields:

| Field | Description | Example |
|-------|-------------|---------|
| vendor | Vendor name | "CloudTech Solutions" |
| category | High-level category | "Technology" |
| sub_category | Detailed categories | "Cloud Services, Infrastructure" |
| application | Specific product/service | "Cloud Infrastructure Platform" |
| function | Business/technical functions | "Hosting, Database Management, DevOps" |
| service_flag | Service types | "IaaS, PaaS, Managed Services" |
| compliance | Standards/certifications | "ISO 27001, SOC 2, GDPR, HIPAA, PCI-DSS" |
| geography | Operating regions | "North America, Europe, Asia-Pacific" |
| risk_flag | Risk assessment | "Low - Established vendor, strong financials" |
| sustainability_flag | Sustainability info | "Yes - Carbon neutral, 100% renewable energy" |

### Example Workflow

**Scenario**: You need to categorize 50 vendor descriptions for a procurement database.

1. **Prepare Vendor Descriptions**: Compile text descriptions of each vendor
2. **Process One by One**: Enter each vendor's information and submit
3. **Export Results**: Copy table data to Excel or CSV
4. **Build Database**: Use structured taxonomy for searchable database

### Interpreting Results

**Category Examples**:
- Technology, Professional Services, Manufacturing, Healthcare, Finance, Retail

**Sub-category Examples**:
- Cloud Services, Cybersecurity, Consulting, Legal Services, Supply Chain

**Service Flags**:
- SaaS, IaaS, PaaS, Consulting, Managed Services, Support, Training

**Compliance Standards**:
- ISO 27001, SOC 2, GDPR, HIPAA, PCI-DSS, CCPA, FedRAMP

**Risk Flag Interpretation**:
- **Low**: Established vendor, strong compliance, financial stability
- **Medium**: Some gaps in compliance or newer vendor
- **High**: Significant concerns about stability, compliance, or security

**Sustainability Flag**:
- **Yes**: Active sustainability programs, certifications, or commitments
- **No**: No mentioned sustainability initiatives
- **Partial**: Some sustainability efforts but not comprehensive

### Best Use Cases

1. **Vendor Database Creation**: Build searchable, structured vendor databases
2. **RFP Categorization**: Automatically categorize incoming vendor responses
3. **Market Analysis**: Understand vendor landscape by category and capability
4. **Compliance Tracking**: Identify vendors by compliance requirements
5. **Geographic Filtering**: Find vendors operating in specific regions

## Understanding Results

### Confidence Scores Explained

All matching functions return a confidence score between 0.1 and 1.0.

**How Scores are Calculated**:

The AI analyzes semantic similarity, not just keywords:
- Concept alignment
- Functional overlap
- Domain-specific relevance
- Contextual understanding

**What Scores Mean**:

```
1.0 ────────────────── Perfect Match
│
0.9 ─┐
│   │ Strong Match
0.8 ─┘ (Highly Recommended)
│
0.7 ─┐
│   │ Good Match
0.6 ─┘ (Recommended)
│
0.5 ─┐
│   │ Moderate Match
0.4 ─┘ (Consider)
│
0.3 ─┐
│   │ Weak Match
0.2 ─┘ (Unlikely fit)
│
0.1 ────────────────── Minimal Match
```

**Decision Thresholds**:

- **Legal Cases**: Consider scores above 0.6
- **Vendor Matching**: Shortlist scores above 0.7
- **Critical Requirements**: Focus on scores above 0.8

### Justification Text

Every match includes a justification explaining the score.

**Good Justification Example**:
```
"This vendor demonstrates strong alignment with the requirements. They offer
comprehensive cloud infrastructure services including IaaS and PaaS, which
directly match the stated needs. Their multi-region capabilities cover all
required geographies. Compliance certifications (ISO 27001, SOC 2) align
with requirements. Strong evidence of enterprise-scale experience with
similar migrations. Minor gap: no explicit mention of Active Directory
integration, though their identity management services suggest compatibility."
```

**How to Use Justifications**:

1. **Verify Alignment**: Check that mentioned capabilities actually match your needs
2. **Identify Gaps**: Look for what's missing or weak
3. **Follow-up Questions**: Use gaps as basis for vendor questions
4. **Validate Claims**: Cross-reference justifications with actual vendor documentation

### Sorting and Filtering Results

**Default Sorting**: Results are sorted by Confidence_Score (highest first)

**Manual Sorting**:
1. Click any column header to sort by that column
2. Click again to reverse sort order
3. Useful for alphabetical sorting by vendor name

**Filtering** (using Streamlit dataframe features):
1. Hover over column header
2. Use filter icon to set conditions
3. Filter by score range, text contains, etc.

**Export Results**:
- Right-click on dataframe
- Select "Download as CSV"
- Open in Excel for further analysis

## Best Practices

### File Preparation

#### PDF Files

**Quality Matters**:
- Use text-based PDFs, not scanned images
- If scanned, ensure OCR has been applied
- Test: Can you select and copy text from the PDF?

**Structure Recommendations**:
- Include clear headings and sections
- For legal cases: Include case name, facts, issues, reasoning
- For vendors: Include company overview, services, capabilities
- Avoid overly formatted documents (excessive tables, graphics)

**File Naming**:
```
Good:
- ABC_Corp_Vendor_Profile.pdf
- Smith_v_Jones_Precedent.pdf
- TechVendor_Cloud_Services.pdf

Bad:
- document1.pdf
- temp.pdf
- untitled.pdf
```

#### TXT Files

**Format Guidelines**:
- Use plain text (.txt) format
- UTF-8 encoding
- Clear section headings
- Bullet points or numbered lists work well

**Content Structure**:

**For Legal Cases**:
```
Case Title: [Name]

Background:
- [Context]

Facts:
- [Fact 1]
- [Fact 2]

Legal Issues:
- [Issue 1]
- [Issue 2]

Arguments:
- [Argument 1]
```

**For Requirements**:
```
Project: [Name]

Overview:
[Brief description]

Requirements:
1. [Requirement 1]
2. [Requirement 2]

Technical Specifications:
- [Spec 1]
- [Spec 2]

Compliance:
- [Standard 1]
```

### Optimizing Batch Processing

**Recommended Batch Sizes**:

- **Legal Cases**: 5-15 precedent cases per run
- **Vendor Matching**: 10-20 vendor profiles per run
- **Taxonomy**: Process one vendor at a time

**Why Limit Batch Size**:
- Faster results (less waiting)
- Easier to review results
- Less impact from API rate limits

**Processing Large Sets**:

If you have 50+ vendors:
1. Split into batches of 20
2. Process each batch separately
3. Combine results in Excel or database
4. Consider category-based batching (e.g., cloud vendors, consulting firms)

### Writing Effective Requirements

**Be Specific**:
```
❌ Bad: "We need cloud services"

✅ Good: "We need Infrastructure as a Service (IaaS) with support for
containerized applications using Kubernetes, multi-region deployment
in US and EU, and 99.9% uptime SLA"
```

**Include Context**:
```
❌ Bad: "Database required"

✅ Good: "Managed PostgreSQL database service capable of handling
100,000 transactions per second, with automatic failover and point-in-time
recovery for financial transaction data"
```

**List Priorities**:
```
Critical Requirements:
- ISO 27001 certification
- GDPR compliance
- 24/7 support

Preferred Features:
- Multi-cloud support
- DevOps integration
- Training programs
```

### Interpreting Low Scores

**When All Scores Are Low** (< 0.5):

This might mean:
1. **Poor Vendor Fit**: None of the vendors match your requirements
2. **Unclear Requirements**: Rewrite requirements with more detail
3. **Wrong Vendor Pool**: You're evaluating the wrong category of vendors

**Actions to Take**:
1. Review and clarify your requirements document
2. Verify vendor PDFs contain capability information
3. Consider broadening or narrowing your requirements
4. Evaluate a different set of vendors

### Review and Validation

**Don't Trust Scores Blindly**:

1. **Read Justifications**: Always review the explanation
2. **Verify Claims**: Check vendor documentation for mentioned capabilities
3. **Human Judgment**: Use AI as a tool, not a replacement for expertise
4. **Cross-Reference**: Compare AI results with manual review

**Red Flags**:

- Score seems too high for obvious mismatch
- Justification is vague or generic
- Mentioned capabilities not in vendor document
- Missing critical requirements not mentioned in justification

**When This Happens**:
1. Re-read the vendor document carefully
2. Check if requirement was stated clearly
3. Consider reprocessing with revised inputs
4. Flag for manual review

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Config file not found"

**Cause**: Application can't find config.yaml

**Solution**:
1. Ensure config.yaml exists in application directory
2. Check file name spelling (case-sensitive on Linux/Mac)
3. Verify you're running from correct directory

```bash
# Check if config.yaml exists
ls -l config.yaml

# If missing, create it:
cat > config.yaml << EOF
data_path: data

llm:
  model: gpt-4o-mini
  model_provider: openai
  temperature: 0
EOF
```

#### Issue: "Failed to read PDF file"

**Cause**: PDF is corrupted, password-protected, or scanned image

**Solutions**:
1. **Test PDF**: Try opening in Adobe Reader or browser
2. **Remove Password**: Unlock password-protected PDFs
3. **OCR Scanned PDFs**: Use OCR software to make text selectable
4. **Re-save PDF**: Open and re-save in different PDF editor
5. **Convert Format**: Try converting to PDF/A format

#### Issue: "Server busy... Please try again"

**Cause**: OpenAI API error, rate limit, or network issue

**Solutions**:
1. **Check API Key**: Verify OPENAI_API_KEY in .env file
2. **Check Quota**: Ensure you have API credits available
3. **Wait and Retry**: Rate limits reset after a short time
4. **Reduce Batch Size**: Process fewer files at once
5. **Check Network**: Verify internet connection

#### Issue: "No results appear after submission"

**Cause**: Processing error, empty files, or session state issue

**Solutions**:
1. **Check Files**: Ensure files contain actual content
2. **Refresh Page**: Reload the browser page
3. **Check Logs**: Look in ./logs/error_logs.json
4. **Restart App**: Stop and restart Streamlit

```bash
# View recent errors
tail -20 ./logs/error_logs.json

# Restart application
# Press Ctrl+C to stop, then:
streamlit run app.py
```

#### Issue: "Results seem inaccurate or irrelevant"

**Cause**: Unclear inputs, poor document quality, or wrong expectations

**Solutions**:
1. **Improve Requirements**: Make requirements more specific and detailed
2. **Check Document Quality**: Ensure PDFs have clear, extractable text
3. **Review Prompts**: Consider if documents match expected format
4. **Adjust Expectations**: Remember AI provides assistance, not perfection
5. **Provide More Context**: Add background information to requirements

#### Issue: "Low confidence scores across all results"

**Cause**: Mismatch between requirements and vendor pool

**Solutions**:
1. **Verify Vendor Match**: Are you comparing the right type of vendors?
2. **Broaden Requirements**: Try less restrictive requirements
3. **Different Vendor Pool**: Evaluate different vendors
4. **Clarify Requirements**: Ensure requirements are clearly stated

#### Issue: "Processing is very slow"

**Cause**: Large files, many files, or API latency

**Solutions**:
1. **Reduce File Size**: Compress or trim large PDFs
2. **Smaller Batches**: Process fewer files at once
3. **Check Network**: Slow internet can increase API latency
4. **Be Patient**: Processing 10 vendors takes ~30-40 seconds normally

### Error Messages Reference

| Error Message | Meaning | Solution |
|---------------|---------|----------|
| "Config file not found" | config.yaml missing | Create config.yaml |
| "Failed to read txt file" | Can't read TXT file | Check file exists and permissions |
| "Failed to read pdf file" | Can't extract PDF text | Verify PDF quality and format |
| "Server busy" | API or network error | Check API key and retry |
| No message but no results | Silent error occurred | Check error logs |

### Getting Help

**Check Logs**:

```bash
# View info logs
cat ./logs/info_logs.json

# View error logs
cat ./logs/error_logs.json

# View most recent errors
tail -50 ./logs/error_logs.json | jq '.'
```

**Diagnostic Checklist**:

- [ ] config.yaml exists and is valid
- [ ] .env file has OPENAI_API_KEY
- [ ] Files are readable (not corrupted)
- [ ] Files are in correct format (PDF, TXT)
- [ ] Internet connection is working
- [ ] API key has available quota
- [ ] Application started without errors

## Tips and Tricks

### Efficiency Tips

**Reuse Session State**:
- Results persist during your session
- You can switch tabs without losing results
- Refresh the page to clear all results

**Keyboard Shortcuts**:
- `Ctrl + K`: Streamlit command palette
- `R`: Rerun the application
- `C`: Clear cache

**Download Results**:
1. Right-click on results table
2. Select "Download as CSV"
3. Open in Excel for further analysis

### Advanced Usage

**Comparing Multiple Requirement Sets**:
1. Process vendors with Requirement A
2. Download results as CSV
3. Refresh page
4. Process same vendors with Requirement B
5. Download second results
6. Compare in Excel

**Building a Vendor Database**:
1. Use Vendor Taxonomy for each vendor
2. Export each result to CSV
3. Combine in master spreadsheet
4. Use as searchable database

**Legal Research Workflow**:
1. Start with broad precedent search
2. Review top 5 matches
3. Refine current case description based on findings
4. Rerun with focused precedent set
5. Iterate until you find best matches

### Quality Assurance

**Validate Sample Results**:
1. Manually review 3-5 results
2. Verify confidence scores make sense
3. Check justifications against actual documents
4. Build confidence in AI before full deployment

**Cross-Validation**:
- Compare AI results with manual evaluation
- Use AI to supplement, not replace, human judgment
- Flag discrepancies for investigation

**Continuous Improvement**:
- Note which inputs produce better results
- Refine document formats over time
- Share best practices with team

## Conclusion

This user guide should help you effectively use all three functions of the Procurement Matcher application. Remember:

- **Prepare quality inputs** for best results
- **Review justifications**, not just scores
- **Use AI as a tool** to augment human judgment
- **Iterate and refine** your approach based on results

For technical issues, consult the troubleshooting section or review application logs. For questions about specific features, refer to the API Reference documentation.
