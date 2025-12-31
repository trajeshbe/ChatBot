# Detailed Analysis of Sample Cost Estimation Files

**Date**: 2025-11-21
**Purpose**: Extract patterns from real cost estimation examples for Project Estimator implementation

---

## File 1: DC Byte Effort Estimation.xlsx (POC)

### Excel Structure

**Total Sheets**: 7
1. `DC Byte Poc` - Main POC estimate
2. `Scraper_Estimation_POC` - Detailed scraper breakdown
3. `Scraper_Estimation_FullProject` - Full project scraper estimate
4. `Tasks List` - Task reference/lookup
5. `Infrastructure_Details` - Infrastructure cost breakdown
6. `Infrastructure_Details_FullProj` - Full project infrastructure
7. `Sheet1` - Extra/scratch sheet

### Main Sheet Analysis: "DC Byte Poc"

**Total Rows**: 35 rows
**Project Title**: "Robust Solution Development for Finding Land Purchase deals"

#### Column Structure
```
| Col A: S.No | Col B: Task Description | Col C: Cost per hour | Col D: Effort in Hours | Col E: Total Cost |
```

#### Task Breakdown Pattern (20-30 tasks with hierarchical numbering)

**Major Sections** (numbered 1-9):

1. **Planning, Design and System Set up** - 40 hours @ $20/hr = $800
   - 1.2: Solution Approach (System Architecture and Database Design) - 24 hrs
   - 1.3: Infrastructure Setup - 16 hrs

2. **Scraper Development/Configuration** - 2,456 hours @ $20/hr = $49,120
   - 2.1: 2000 Sources (Media sites, land registries, company websites) - 2,400 hrs
   - 2.2: Company-level press releases and annual reports - 8 hrs
   - 2.3: Data scraped from 15 Twitter handles - 24 hrs
   - 2.4: Open Search (Google OpenSearch limited to first 10 pages) - 8 hrs
   - 2.5: LinkedIn Posts Scraping - 16 hrs

3. **Data Transformation, Logging, Alerts, Reports and Delivery** - 28 hours @ $20/hr = $560
   - 3.1: Download and Upload processed files - 8 hrs
   - 3.2: Content DeDuping - 8 hrs
   - 3.3: Multilingual sources (Translation Required) - 8 hrs
   - 3.4: Logging - 4 hrs

4. **Data Quality & Validation** - 12 hours @ $20/hr = $240
   - 4.1: Automated Checks - Data Validation

5. **UAT Issue Fixes** - 246 hours @ $20/hr = $4,920

6. **Integration and Deployment** - 16 hours @ $20/hr = $320

7. **Documentation** - 0 hours (marked as FOC - Free of Charge)

8. **Project Management** - 0 hours (marked as FOC)
   - 8.1: Project Management Charges (PM and BAs)

9. **Infrastructure Charges During Set Up** - $810
   - 9.1: To be paid on actuals

#### Cost Summary

```
Total Estimated Hours:        2,798 hours @ $20/hr = $55,960
Buffer for Contingencies(10%):  279.8 hours @ $20/hr = $5,596
────────────────────────────────────────────────────────────
Total Set Up Costs:           3,077.8 hours         = $62,366
```

### Key Patterns Identified

#### 1. Task Numbering System
- **Hierarchical numbering**: 1, 1.2, 1.3, 2, 2.1, 2.2, 2.3, 2.4, 2.5, 3, 3.1, etc.
- **Main tasks**: Whole numbers (1, 2, 3, 4, 5...)
- **Sub-tasks**: Decimal notation (1.2, 1.3, 2.1, 2.2...)
- **Numbering can be inconsistent**: e.g., "2.2000000000000002" instead of "2.2" (Excel floating point issue)

#### 2. Standard Rate Structure
- **Single hourly rate**: $20/hour used consistently across all development tasks
- No role-based rate differentiation in this POC
- **Infrastructure**: Separate line item, not hourly-based ($810 flat fee)

#### 3. POC-Specific Characteristics
- **No BAU (Business As Usual) costs** - This is a one-time POC
- **PM and Documentation are FOC** (Free of Charge)
- **Focus on setup and validation**, not long-term support
- **Contingency**: 10% buffer added at the end

#### 4. Cost Categories Present
1. **Development Costs** (majority of budget)
2. **Infrastructure Setup** (one-time, actuals-based)
3. **UAT/Testing** (significant: 246 hours for issue fixes)
4. **Integration & Deployment**
5. **Contingency Buffer** (10%)

#### 5. Cost Categories **NOT Present** (POC doesn't need)
- ❌ BAU/Ongoing Support
- ❌ Monthly subscription fees
- ❌ Maintenance costs
- ❌ Training costs

#### 6. Task Detail Level
- **Total unique tasks**: ~18-20 line items
- **Task description length**: 40-60 characters
- **Granularity**: Mix of high-level (e.g., "Scraper Development") and specific (e.g., "LinkedIn Posts Scraping")

#### 7. Side Metadata
The spreadsheet includes project context in side columns:
- **Total Sources(Assumption)**: 2000
- **Category breakdown** with percentages:
  - Common Framework: 90% (1800 sources)
  - Custom Scrapers: 10% (200 sources)
- **Approach descriptions**:
  - Generic crawler framework (Scrapy + Playwright)
  - Site-specific scrapers, form-handling, OCR for PDFs

#### 8. Formula Patterns (Inferred)
```excel
Total Cost (Column E) = Cost per hour (Column C) × Effort in Hours (Column D)
Total Hours = SUM of all Effort in Hours
Contingency Hours = Total Hours × 10%
Grand Total = Total Cost + Contingency Cost + Infrastructure
```

---

## Comparison Matrix: POC vs Full Service (Expected)

| Aspect                  | POC (DC Byte)                  | Full Service (Expected)                |
|-------------------------|--------------------------------|----------------------------------------|
| **BAU Costs**           | ❌ Not included                | ✅ Included (monthly/annual)           |
| **PM Charges**          | FOC (Free of Charge)           | ✅ Percentage-based (10-15%)           |
| **Documentation**       | FOC or minimal                 | ✅ Full documentation package          |
| **Infrastructure**      | Actuals-based, minimal         | ✅ Full setup + ongoing costs          |
| **Support**             | Limited to UAT                 | ✅ Ongoing support contract            |
| **Training**            | ❌ Not included                | ✅ User training included              |
| **Contingency**         | 10% buffer                     | 10-20% buffer                          |
| **Total Duration**      | 3-6 months                     | 6-12+ months                           |

---

## Implementation Recommendations

### 1. Task Breakdown Generation (20-30 tasks)

The LLM should generate tasks following this pattern:

```python
[
    {
        "task_id": "1",
        "task_name": "Planning, Design and System Set up",
        "effort_hours": 40,
        "rate_per_hour": 20,
        "total_cost": 800,
        "category": "planning",
        "is_parent": True
    },
    {
        "task_id": "1.1",
        "task_name": "Requirements Gathering and Analysis",
        "effort_hours": 16,
        "rate_per_hour": 20,
        "total_cost": 320,
        "category": "planning",
        "parent_id": "1"
    },
    {
        "task_id": "1.2",
        "task_name": "Solution Approach (System Architecture and Database Design)",
        "effort_hours": 24,
        "rate_per_hour": 20,
        "total_cost": 480,
        "category": "planning",
        "parent_id": "1"
    },
    # ... continue with 2, 2.1, 2.2, etc.
]
```

### 2. Excel Generation Structure

**Sheet 1: "Summary"**
- Project name and scope
- Total cost breakdown by category
- Timeline summary

**Sheet 2: "Task Breakdown"** (Main Sheet)
- Columns: S.No | Task Description | Cost per hour | Effort in Hours | Total Cost
- Rows: 20-30 tasks with hierarchical numbering
- Totals row at bottom
- Contingency row (10%)
- Grand total row

**Sheet 3: "Lookup" or "Config"**
- Configurable rates by role
- Infrastructure cost parameters
- Overhead percentages (PM, BA, SA)
- Contingency percentage

**Sheet 4: "Infrastructure Details"** (Optional for POC, Required for Full Service)
- Server costs
- Storage costs
- Licensing fees
- Network/bandwidth costs

### 3. Cost Formula Implementation

```python
def calculate_task_cost(task: Dict) -> float:
    return task["effort_hours"] * task["rate_per_hour"]

def calculate_total_hours(tasks: List[Dict]) -> float:
    return sum(task["effort_hours"] for task in tasks)

def calculate_contingency(total_hours: float, rate: float, percentage: float = 0.10) -> float:
    return total_hours * rate * percentage

def calculate_grand_total(
    development_cost: float,
    infrastructure_cost: float,
    contingency_cost: float
) -> float:
    return development_cost + infrastructure_cost + contingency_cost
```

### 4. Project Type Differentiation

**POC Estimation Template:**
```python
{
    "include_bau": False,
    "include_pm_charges": False,  # Or "FOC"
    "include_training": False,
    "contingency_percentage": 0.10,
    "infrastructure_model": "one_time",
    "support_duration": "3_months_uat"
}
```

**Full Service Estimation Template:**
```python
{
    "include_bau": True,
    "include_pm_charges": True,  # 10-15% of total
    "include_training": True,
    "contingency_percentage": 0.15,
    "infrastructure_model": "setup_plus_recurring",
    "support_duration": "12_months_minimum",
    "bau_monthly_cost": calculated_based_on_scope
}
```

---

## Next Steps

1. ✅ DC Byte POC structure analyzed
2. ⏳ Analyze "Real Deals Media" Full Service estimate to understand differences
3. ⏳ Analyze "Ulysses Systems" POC estimate to validate patterns
4. ⏳ Extract PowerPoint proposal structures
5. ⏳ Update implementation plan with specific findings

---

## File 2: Real Deals Media Full Service (cost_estimation_realdealsmedia_v0.xlsx)

### Excel Structure

**Total Sheets**: 13 (Much more complex than POC)
1. `AIML_cost` - Main line items
2. `lookup` - Rate configuration and overhead calculations
3. `consolidated_sheet` - Main cost summary
4. `unit_cost` - Unit cost details
5. `DataHarvesting_cost` - Data harvesting breakdown
6. `Consolidated Cost for Proposal` - Proposal summary
7. `Sources Details` - Source data details
8. `Infrastructure_Details` - Infrastructure costs
9. `Call - Queries and Answers` - Project Q&A
10. `Resource Loading Sheet` - Resource allocation
11. `AIML_workflow` - Workflow documentation
12. `Resource Loading` - Alternative resource view
13. Additional calculation sheets

### Main Sheet Analysis: "consolidated_sheet"

**Total Rows**: 56 rows (more detailed than POC)

#### Task Structure (Stage | Task | Description format)

**Major Phases**:

1. **Planning - Customising AIML Framework** - 88 hrs @ $25/hr = $2,200
   - Analysis of Input Sources and Schema Alignment - 16 hrs
   - Evaluation of Parsing Options - 24 hrs
   - RAG Pipeline Planning and Architecture - 16 hrs
   - Analysis of Editorial Summary Requirements - 24 hrs
   - Confidence Framework & Validation Rules - 24 hrs

2. **Development - AIML Framework** - 248 hrs @ $30/hr = $7,440
   - Document Pre-processing Pipeline Setup - 16 hrs
   - Embedding and Indexing for RAG - 24 hrs
   - Schema-Guided RAG Extraction Setup - 56 hrs
   - Prompt Engineering and Schema Validation - 32 hrs
   - Post-processing and Field Normalization - 24 hrs
   - Auto-Summary Template Creation (Stage 1) - 24 hrs
   - Editorial Refinement Model (Stage 2) - 24 hrs
   - Integration Setup with CMS & Database - 24 hrs
   - Evaluation and Fine-tuning - 24 hrs

3. **Integration Effort** - 96 hrs @ $30/hr = $2,880
   - Azure SQL Database integration - 64 hrs
   - Integration testing - 32 hrs

4. **Testing - AIML Framework** - 100 hrs @ $25/hr = $2,500
   - Unit testing - 50 hrs
   - Data quality validation - 50 hrs

#### Cost Summary Breakdown

```
Total Production Man Hours:           532 hours
Total Development Cost:           $15,020

Overhead Calculations:
- Solution Architect Effort @ 10%:   $1,502
- PM Effort @ 0%:                        $0
- BA Effort @ 0%:                        $0
- Contingency @ 10%:                 $1,502
────────────────────────────────────────────
Grand Total - One time setup:      $18,024
```

#### Infrastructure Costs (Detailed)

**Initial Phase Infrastructure**: $430 total
- Virtual Machine (Ubuntu) - AMD EPYC 9554, 8 Cores, 16 GB RAM: $320
- OpenAI token cost (1000 documents @ $0.11 each): $110

#### ✅ BAU - Ongoing Recurring Cost (MONTHLY)

**This is the KEY difference from POC!**

```
BAU Monthly Costs:
- Virtual Machine (Ubuntu):              $170/month
- OpenAI tokens (1000 docs/month):       $110/month
- Support and Maintenance:               $750/month
────────────────────────────────────────────────────
Total BAU - Ongoing Monthly Cost:      $1,030/month
```

### Key Patterns Identified (Full Service)

#### 1. Multi-Sheet Architecture
- **Lookup sheet**: Contains rate tables, overhead percentages, margin calculations
- **Consolidated sheet**: Main cost summary with all calculations
- **Specialized sheets**: Infrastructure, resource loading, workflow diagrams

#### 2. Role-Based Rate Structure
- Analysis/Planning: $25/hour
- Standard Development: $30/hour
- Complex Development: $35/hour
- Different rates for different complexity levels

#### 3. Overhead Calculations
- **Solution Architect**: 10% of total cost
- **PM/BA**: 0% (FOC in this case, but structure supports percentage-based)
- **Contingency**: 10% of total cost

#### 4. Full Service Characteristics
- ✅ **BAU costs included** (~$1,030/month recurring)
- ✅ Infrastructure costs detailed (initial + recurring)
- ✅ Token/API costs calculated
- ✅ Support and Maintenance included
- ✅ Virtual Machine costs (ongoing)
- ✅ Resource loading sheets for project planning

#### 5. Categories Present (Full Service)
1. Development Costs (detailed breakdown)
2. Infrastructure Setup (one-time)
3. Infrastructure Recurring (monthly)
4. Project Management Overhead (percentage-based)
5. Solution Architecture (percentage-based)
6. Testing & QA
7. Integration & Deployment
8. **BAU Support** (monthly recurring)
9. Token/API usage costs (per document)
10. Contingency Buffer (10%)

---

## File 3: Ulysses Effort Estimation.xlsx (POC)

### Excel Structure

**Total Sheets**: 2 (Simplest structure)
1. `Estimation` - Main estimate
2. `Architecture_Diagram` - Technical architecture

### Main Sheet Analysis: "Estimation"

**Total Rows**: 52 rows
**Project Focus**: Automated Data Mapping POC

#### Column Structure
```
| Task Description | Effort in Hours | Cost per Hour | Total Cost | Remarks |
```

#### Task Breakdown by Complexity

**1. Analysis and Planning** - 112 hrs total
- Analyze PDF documents and categorize - 16 hrs @ $25/hr = $400
- Research open-source libraries - 16 hrs @ $25/hr = $400
- Explore image enhancement techniques - 24 hrs @ $25/hr = $600
- Implement OCR post-processing - 32 hrs @ $25/hr = $800
- Identify document types - 24 hrs @ $25/hr = $600

**2. Development - De-duplication** - 40 hrs @ $30/hr = $1,200

**3. Development - Easy Level Spare Parts Mapping** - 72 hrs @ $30/hr = $2,160
- Perform OCR - 16 hrs
- LLM validation and restructuring - 32 hrs
- Data transformation - 24 hrs

**4. Development - Medium Level Spare Parts Mapping** - 52 hrs @ $30/hr = $1,560
- Table detection and extraction - 12 hrs
- LLM validation - 16 hrs
- Transformation - 24 hrs

**5. Development - Hard Level Activity Mapping** - 166 hrs @ $35/hr = $5,810
- Table detection and extraction - 32 hrs
- LLM validation - 16 hrs
- Content extraction with OCR - 8 hrs
- Spare parts image detection - 40 hrs
- Complex transformation - 70 hrs

**6. Integration and QA** - 72 hrs @ $25-30/hr = $1,920
- Module integration - 24 hrs @ $30/hr
- Data quality check (Human-in-the-loop) - 48 hrs @ $25/hr

**7. Testing - Pipeline** - 16 hrs @ $25/hr = $400

**8. Project Management** - **FOC** (0 hours listed)

**9. Infrastructure Cost** - $1,400 (flat fee)

#### Cost Summary

```
Total Hours:                 570 hours
Total Development Cost:  $17,050
Infra Cost:               $1,400
────────────────────────────────────
Grand Total:             $18,450
```

### Key Patterns Identified (Ulysses POC)

#### 1. Complexity-Based Pricing
- **Easy tasks**: $30/hour
- **Medium tasks**: $30/hour
- **Hard/Complex tasks**: $35/hour
- **Analysis/Planning**: $25/hour

#### 2. POC Characteristics (Validated)
- ❌ No BAU costs
- ❌ PM marked as FOC (Free of Charge)
- ✅ Infrastructure as flat fee
- ✅ Simple 2-sheet structure
- ✅ Focus on development and validation only

#### 3. Parallel Execution Notes
- Tasks marked "can go in parallel" for resource planning
- Helps with timeline estimation

---

## Comprehensive Comparison: POC vs Full Service

| Aspect                        | POC (DC Byte)          | POC (Ulysses)         | Full Service (Real Deals) |
|-------------------------------|------------------------|-----------------------|---------------------------|
| **Total Sheets**              | 7                      | 2                     | 13                        |
| **Total Hours**               | 2,798                  | 570                   | 532                       |
| **Total One-Time Cost**       | $62,366                | $18,450               | $18,024 + $430 infra      |
| **BAU Monthly Cost**          | ❌ None                | ❌ None               | ✅ $1,030/month           |
| **PM Charges**                | FOC                    | FOC                   | FOC (but structure exists)|
| **Rate Structure**            | Flat $20/hr            | $25-35/hr by role     | $25-35/hr by role         |
| **Infrastructure**            | $810 flat              | $1,400 flat           | $430 + $170/month         |
| **Contingency**               | 10%                    | None explicit         | 10%                       |
| **Documentation**             | FOC                    | Not listed            | FOC                       |
| **Token/API Costs**           | Not listed             | Not listed            | ✅ $110/month             |
| **Support & Maintenance**     | ❌ Not included        | ❌ Not included       | ✅ $750/month             |
| **Overhead Calculations**     | Simple                 | Simple                | ✅ Percentage-based       |
| **Task Count**                | ~20 tasks              | ~25 tasks             | ~16 major tasks           |
| **Complexity Levels**         | No                     | ✅ Easy/Medium/Hard   | Yes (implicit)            |

---

## Updated Implementation Recommendations

### 1. Task Breakdown Generation (20-30 tasks)

The LLM should generate tasks with complexity-aware pricing:

```python
[
    {
        "task_id": "1",
        "task_name": "Analysis and Planning",
        "effort_hours": 88,
        "complexity": "analysis",  # NEW: complexity level
        "rate_per_hour": 25,
        "total_cost": 2200,
        "category": "planning",
        "is_parent": True
    },
    {
        "task_id": "1.1",
        "task_name": "Analysis of Input Sources and Schema Alignment",
        "effort_hours": 16,
        "complexity": "easy",
        "rate_per_hour": 25,
        "total_cost": 400,
        "category": "planning",
        "parent_id": "1",
        "remarks": ""
    },
    {
        "task_id": "2.5",
        "task_name": "Hard - Complex Data Transformation",
        "effort_hours": 70,
        "complexity": "hard",
        "rate_per_hour": 35,  # Higher rate for complex work
        "total_cost": 2450,
        "category": "development",
        "parent_id": "2",
        "remarks": "can go in parallel"
    },
]
```

### 2. Rate Configuration (Lookup Table)

```python
RATE_CONFIG = {
    "analysis_planning": 25,
    "development_easy": 30,
    "development_medium": 30,
    "development_hard": 35,
    "testing_qa": 25,
    "project_management": 25,
    "solution_architect": 35,
}

OVERHEAD_CONFIG = {
    "solution_architect_percentage": 0.10,  # 10% of total
    "pm_percentage": 0.00,  # Often FOC for POC
    "ba_percentage": 0.00,  # Often FOC for POC
    "contingency_percentage": 0.10,  # 10% buffer
}
```

### 3. BAU Cost Calculation (Full Service Only)

```python
def calculate_bau_monthly_cost(
    project_type: str,
    document_volume: int = 1000,
    vm_type: str = "standard"
) -> Dict[str, float]:
    """Calculate Business As Usual monthly costs"""

    if project_type != "full_service":
        return {"total_monthly": 0, "breakdown": {}}

    # Token costs
    token_cost_per_doc = 0.11
    monthly_token_cost = document_volume * token_cost_per_doc

    # Infrastructure
    vm_costs = {
        "standard": 170,
        "premium": 320,
    }
    monthly_vm_cost = vm_costs.get(vm_type, 170)

    # Support and Maintenance (calculated as hours)
    support_hours_monthly = 25
    support_rate = 30
    monthly_support = support_hours_monthly * support_rate  # $750

    return {
        "total_monthly": monthly_token_cost + monthly_vm_cost + monthly_support,
        "breakdown": {
            "token_costs": monthly_token_cost,
            "virtual_machine": monthly_vm_cost,
            "support_maintenance": monthly_support,
        }
    }
```

### 4. Project Type Configuration

**POC Configuration:**
```python
{
    "include_bau": False,
    "include_pm_charges": False,  # FOC
    "include_documentation": False,  # FOC or minimal
    "include_training": False,
    "contingency_percentage": 0.10,
    "infrastructure_model": "one_time_flat_fee",
    "support_duration": "3_months_uat_only",
    "overhead": {
        "solution_architect": 0.00,  # Often FOC
        "pm": 0.00,  # FOC
        "ba": 0.00,  # FOC
    }
}
```

**Full Service Configuration:**
```python
{
    "include_bau": True,
    "include_pm_charges": True,  # Can be percentage-based
    "include_documentation": True,
    "include_training": True,
    "contingency_percentage": 0.10,
    "infrastructure_model": "setup_plus_monthly_recurring",
    "support_duration": "12_months_minimum",
    "bau_monthly_cost": 1030,  # Calculated
    "overhead": {
        "solution_architect": 0.10,  # 10% of total
        "pm": 0.00,  # Can be 0.10-0.15 if needed
        "ba": 0.00,  # Can be 0.05-0.10 if needed
    }
}
```

---

## Part 2: PowerPoint BRD Document Analysis

**Files Analyzed**:
1. `Merit_DC Byte_Automated Data Extraction_Solution, Workflow, Tech Architecture and POC Costs_v1.0_16Oct2025 1.pptx` - POC Proposal (20 slides)
2. `Merit_Real Deals Media_Automated Data Extraction Approach note and Estimates_v1.0_28Oct2025 1.pptx` - Full Service Proposal (20 slides)
3. `Merit_Ulysses Systems_Automated Data Mapping Approach note and POC Estimates_v1.0_04Nov2025 1.pptx` - POC Proposal (14 slides)

---

### Common BRD Document Structure Pattern

Based on analysis of all 3 PowerPoint proposals, the following structure is consistent:

#### Standard Proposal Sections (in order):

1. **Title Slide** (Slide 1)
   - Project title with descriptive subtitle
   - Client name ("For [Client Name]")
   - Version number and date
   - Example: "Automated Data Extraction Solution for Real Estate Transactions / Solution Workflow, Architecture & POC Costs / For DC Byte / Version 1.0 / 16Oct2025"

2. **Introduction/Background** (Slides 2-4)
   - About the client company
   - Current situation/pain points
   - Why automation is needed
   - Example: "Real Deals Media (RDM) is a UK-based B2B intelligence publisher focused on private equity and M&A deal intelligence..."

3. **Objectives** (Slides 5-7)
   - Project objectives (bulleted list, 3-6 items)
   - POC objectives (if POC)
   - What the solution will achieve
   - Example: "To demonstrate Merit capabilities to automate the end-to-end data collection and extraction process..."
   - Key objectives typically include:
     - Automate data extraction
     - Improve accuracy and consistency
     - Reduce manual effort
     - Demonstrate scalability
     - Ensure data quality

4. **Scope** (Slides 8-10)
   - POC Scope vs Full Project Scope
   - Data sources included (categorized by type)
   - Search & Discovery Methods (SERP API, OpenSearch, web scraping, etc.)
   - In Scope vs Out of Scope (explicit boundaries)
   - Example: "POC Input: 3 identified web sources of varied complexities / Email & PDF Ingestion / Taxonomy Mapping..."

5. **Workflow/Process** (Slides 11-13)
   - Detailed workflow diagram or flowchart
   - Step-by-step process description
   - Common stages:
     1. Collect (Web scraping, data ingestion)
     2. Process (Parsing, cleaning, structuring)
     3. Extract (AI-powered extraction, field mapping)
     4. Validate (Quality checks, deduplication)
     5. Deliver (SFTP, database, CMS integration)
     6. Output (Structured data, reports)

6. **Technical Architecture** (Slides 14-15)
   - Architecture diagram
   - Technology stack mentions (KIAA Framework, ScrapeX, etc.)
   - Infrastructure components
   - Note: "Note: ScrapeX platform components help reduce timeline by 30-40%"

7. **Deliverables** (Slide 16)
   - POC deliverables list
   - Output format (CSV, Excel, JSON, etc.)
   - Data records count
   - Documentation included
   - Example: "Output: Unique data records (both complete and partial) delivered as CSV / Excel"

8. **Costs** (Slides 17-19)
   - **POC Costs** (single slide with table)
     - Task breakdown summary
     - Total cost
   - **Full Project Costs** (if applicable)
     - Detailed cost breakdown
     - Phase-wise costs
   - **BAU Recurring Costs** (Full Service only)
     - Monthly recurring costs
     - Breakdown: Infrastructure, Tokens, Support

9. **Timeline/Milestones** (Slide 20+)
   - Key milestones table
   - Estimated duration for each phase
   - Total project duration
   - Example: "Discovery & Planning: 1-2 weeks / Development: 4-6 weeks / UAT: 2 weeks"

10. **Assumptions** (typically Slide 3-5 or near end)
    - Access to data sources provided
    - SMEs available for feedback
    - English-only documents (or multilingual specified)
    - Templates will be consistent
    - Example: "Access will be provided to client database for deduplication"

11. **Benefits/Value Adds** (typically Slide 4-6)
    - Key value propositions
    - What's included Free of Cost (FOC)
    - PM and BA included
    - Documentation included
    - Timeline reduction using accelerator platforms
    - Example: "A dedicated Project Manager and Business Analyst will be assigned FOC / Documentation is FOC / Timeline reduced by 30-40% using accelerator platforms"

12. **Appendices** (remaining slides)
    - Appendix I: Data sources list
    - Appendix II: Data points to be extracted
    - Appendix III: Infrastructure details
    - Appendix IV: SME contacts
    - Appendix V: Additional reference materials

---

### BRD Content Patterns and Language Style

#### 1. Objectives Writing Style

**Pattern**: Each objective is a complete sentence describing what will be achieved, often starting with action verbs.

**Examples from samples**:

```
DC Byte POC:
- "To demonstrate Merit capabilities to automate the end-to-end data collection and extraction process from various online sources and enrichment of data through primary and secondary manual research"
- "Monitor sources and aggregate data at scale"
- "Automated extraction of structured and unstructured data"

Real Deals Media:
- "To perform a Proof of Concept (POC) on a selected set of sources of different complexities to demonstrate Merit's capability to automate and streamline Real Deals Media's (RDM) data extraction and editorial workflows enabling faster, more accurate, and scalable publishing of Private Equity and M&A deal intelligence"
- "Automates data extraction from structured and unstructured deal announcements, press releases, and company updates"
- "Streamlines editorial workflows by converting raw content into structured deal records aligned with RDM's taxonomy"
- "Ensures accuracy and traceability through validation, deduplication, and confidence scoring"
- "Reduces manual effort by leveraging AI-driven parsing and enrichment with human-in-the-loop verification"

Ulysses Systems:
- "The primary objective of the POC is to demonstrate Merit's capabilities in deduplication, data extraction from PDFs, and automated mapping of spare part and activity sheet data to Ulysses' defined schema"
- "Data Extraction Automation: Automate the extraction, parsing, and structuring of data from OEM manuals to align with Ulysses' target schema"
- "Improved Data Accuracy and Consistency: Enhance data reliability and reduce human errors through semi-automated validation and standardisation steps"
- "Reduce Manual Effort"
```

**Template for objective generation**:
```
"To [ACTION VERB] [WHAT] in order to [BENEFIT/OUTCOME]"
Examples:
- "To automate data extraction from [SOURCE] in order to reduce manual effort by X%"
- "To demonstrate [COMPANY]'s capability to [ACHIEVE WHAT] enabling [BUSINESS VALUE]"
- "To streamline [PROCESS] by [METHOD] ensuring [QUALITY/OUTCOME]"
```

#### 2. Scope Writing Style

**Pattern**: Categorized lists with specific examples and quantification where possible.

**Example structure**:
```markdown
### POC Scope

**POC Input:**
- **Web Sources**: 3 identified sources of varied complexities (Easy, Medium, Hard)
- **Email & PDF Ingestion**: Parsing of deal-related press releases from editorial inboxes (Gmail or Outlook)
- **Search & Discovery Methods**: SERP API (Google/Bing), OpenSearch (up to 10 pages)
- **Sample Data**: 90 Spare Part Manuals + 10 Activity Sheets (to be supplied by customer)

**Data Points to Extract:**
[List of 10-20 specific fields to be extracted]

**Out of Scope:**
- Non-English documents
- Integration with production systems (POC phase only)
- Real-time processing requirements
```

#### 3. Workflow Description Style

**Pattern**: Stage-by-stage process with 4-6 main stages, each with 2-4 sub-points.

**Example from Real Deals Media**:
```
1. Web & Document Collection
   - Automatically capture deal announcements, press releases from company websites and emails
   - Support multiple formats (.eml, .pdf, .docx, .html)
   - Record key source metadata (URL, publication date, document type)

2. Content Parsing & Structuring
   - Extract readable text from varied file types using automated parsing tools
   - Clean and organize content to remove disclaimers, footers, hyperlinks
   - Segment text into logical sections (company background, deal rationale, financials)

3. AI-Powered Data Extraction
   - Apply Retrieval-Augmented Generation (RAG) pipeline aligned to pre-defined schema
   - Automatically identify and extract key entities (Target, Sponsor, Fund, Seller)
   - Generate structured JSON output with confidence scores for each field

4. Validation & Taxonomy Alignment
   - Match extracted entities against controlled vocabularies/picklist values
   - Standardize numeric values, currency formats, naming conventions
   - Flag low-confidence data for editorial review and prevent duplicates

5. Summarisation & Content Generation
   - Stage 1 - Auto Summary: Fill predefined deal template using extracted fields
   - Stage 2 - Editorial Summary: Refine draft into polished article matching editorial tone

6. Integration & Publishing
   - Push validated structured data into SFTP/Azure SQL for long-term storage
   - Upload deal summaries into CMS as draft articles for editorial review
```

#### 4. Deliverables Writing Style

**Pattern**: Clear categorization with specific formats and quantification.

**Example structure**:
```markdown
### POC Deliverables

**Output:**
- Unique data records (both complete and partial) delivered as CSV/Excel
- Estimated XX-XX records covering [data points]
- Confidence scores for each extracted field

**Documentation:**
- Technical documentation (approach, architecture, data flow) - FOC
- User guide for reviewing and validating extracted data
- Source code and scripts (if applicable)

**Post-POC:**
- Presentation of findings and recommendations
- Scalability assessment for full implementation
```

#### 5. Assumptions and Constraints Style

**Pattern**: Bullet list of assumptions, typically 3-8 items, stated as facts.

**Examples from samples**:
```
DC Byte:
- Access will be provided to required data sources
- Client will provide sample data for testing
- POC duration: 6-8 weeks
- SMEs available for timely feedback

Real Deals Media:
- The current estimation covers 40 identified sources, subject to confirmation
- Client will provide access to Gmail/Outlook inbox for email ingestion testing
- Taxonomy and controlled vocabularies will be provided by RDM

Ulysses Systems:
- Access will be provided to Ulysses database for deduplication
- PDF templates will be consistent across the company for future releases
- English-only manuals for the POC
- SMEs available for timely feedback and validation
```

#### 6. Benefits/Value Adds Style

**Pattern**: Bullet list highlighting FOC items, efficiency gains, and unique value propositions.

**Examples**:
```
DC Byte:
- A dedicated Project Manager and Business Analyst assigned FOC
- Documentation efforts included Free of Cost
- Accelerator platform components reduce timeline by 30-40%

Real Deals Media:
- PM and BA oversight at no additional cost
- Ensures smooth delivery and stakeholder alignment
- Documentation de-risks knowledge transfer gaps due to personnel changes

Ulysses Systems:
- End-to-end easily scalable semi-automated solution
- Reduces manual effort by 50-60%
- Guarantees significant increase in output volume, coverage, completeness, and accuracy
- PM and BA assigned FOC
- Documentation is FOC
- Timeline reduced from 2.5 months to 2 months using accelerator platforms
```

---

### BRD Document Generation Implementation Guidance

#### 1. Section-by-Section Content Generation

Use GPT-4 or Claude-3 to generate each section based on:
- Project scope input from user
- Project type (POC / Staff Aug / Full Service)
- Sample data analysis (if provided)
- Reference BRD template (if uploaded)

**Example prompt for Objectives section**:
```python
prompt = f"""
Based on the following project information, generate 3-5 project objectives in the style of professional consulting proposals:

Project Name: {project_name}
Project Type: {project_type}  # POC, Staff Augmentation, Full Service
Client Industry: {industry}
Key Challenges: {challenges}
Scope Summary: {scope_summary}

Format each objective as a complete sentence describing what will be achieved.
Start with action verbs like "Automate", "Streamline", "Demonstrate", "Ensure", "Reduce".
Include specific benefits and outcomes.

Reference style (from sample proposals):
- "To demonstrate Merit capabilities to automate the end-to-end data collection and extraction process..."
- "Automates data extraction from structured and unstructured sources"
- "Ensures accuracy through validation, deduplication, and confidence scoring"

Generate objectives:
"""
```

#### 2. Dynamic Section Inclusion Based on Project Type

```python
def get_brd_sections(project_type: str) -> List[str]:
    """Return list of sections to include based on project type"""

    base_sections = [
        "title_slide",
        "introduction",
        "objectives",
        "scope",
        "workflow",
        "technical_architecture",
        "deliverables",
        "costs",
        "timeline",
        "assumptions"
    ]

    if project_type == "POC":
        return base_sections + [
            "poc_costs",  # Single cost table
            "potential_full_project_costs"  # Optional preview
        ]

    elif project_type == "Full Service":
        return base_sections + [
            "poc_costs",
            "full_project_costs",
            "bau_recurring_costs",  # REQUIRED for Full Service
            "benefits",  # More detailed for full service
            "appendix_data_sources",
            "appendix_data_points",
            "appendix_infrastructure"
        ]

    elif project_type == "Staff Augmentation":
        return [
            "title_slide",
            "introduction",
            "objectives",  # Focused on resource augmentation
            "scope",  # Resource roles and responsibilities
            "team_composition",  # Roles, skillsets, rates
            "timeline",
            "costs",  # Resource-based costs only
            "assumptions"
        ]
```

#### 3. python-pptx Implementation for PowerPoint Generation

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN

def generate_brd_powerpoint(brd_content: Dict[str, Any], output_path: str):
    """Generate PowerPoint BRD document from content dictionary"""

    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    # Slide 1: Title Slide
    slide = prs.slides.add_slide(prs.slide_layouts[0])  # Title layout
    title = slide.shapes.title
    title.text = brd_content["project_title"]
    subtitle = slide.placeholders[1]
    subtitle.text = f"{brd_content['subtitle']}\nFor {brd_content['client_name']}\nVersion {brd_content['version']}\n{brd_content['date']}"

    # Slide 2: Introduction
    slide = prs.slides.add_slide(prs.slide_layouts[1])  # Title + Content
    title = slide.shapes.title
    title.text = "Introduction"
    content = slide.placeholders[1].text_frame
    for para in brd_content["introduction_paragraphs"]:
        p = content.add_paragraph()
        p.text = para
        p.level = 0

    # Slide 3: Objectives
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = f"{brd_content['project_type']} Objectives"
    content = slide.placeholders[1].text_frame
    for objective in brd_content["objectives"]:
        p = content.add_paragraph()
        p.text = objective
        p.level = 0

    # Slide 4-5: Scope (may need 2 slides)
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Scope and Data Source Categories"
    content = slide.placeholders[1].text_frame

    # Add scope sections
    p = content.add_paragraph()
    p.text = f"{brd_content['project_type']} Input"
    p.level = 0
    p.font.bold = True

    for scope_item in brd_content["scope_items"]:
        p = content.add_paragraph()
        p.text = scope_item
        p.level = 1

    # Continue for other slides...

    # Final slide: Timeline
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # Blank for table
    title = slide.shapes.title
    title.text = "Key Milestones and Projected Timelines"

    # Add table for timeline
    rows = len(brd_content["milestones"]) + 1
    cols = 2
    left = Inches(1)
    top = Inches(2)
    width = Inches(8)
    height = Inches(0.5 * rows)

    table = slide.shapes.add_table(rows, cols, left, top, width, height).table
    table.cell(0, 0).text = "Milestones"
    table.cell(0, 1).text = "Estimated Duration"

    for i, milestone in enumerate(brd_content["milestones"], 1):
        table.cell(i, 0).text = milestone["name"]
        table.cell(i, 1).text = milestone["duration"]

    prs.save(output_path)
```

---

**Status**: ✅ **COMPLETE ANALYSIS** - All 6 sample files analyzed (3 Excel + 3 PowerPoint)

**Files Analyzed**:

**Excel Cost Estimates:**
- DC Byte POC ✅
- Real Deals Media Full Service ✅
- Ulysses POC ✅

**PowerPoint BRD Proposals:**
- DC Byte POC ✅ (20 slides)
- Real Deals Media Full Service ✅ (20 slides)
- Ulysses POC ✅ (14 slides)

**Key Findings Summary**:
1. **POC projects**: 14-20 slides, no BAU costs, PM/Docs FOC, simpler appendices
2. **Full Service projects**: 20+ slides, BAU costs included, comprehensive appendices, detailed workflows
3. **Common structure**: Title → Intro → Objectives → Scope → Workflow → Architecture → Deliverables → Costs → Timeline → Assumptions → Benefits → Appendices
4. **Cost estimation**: 20-30 tasks, hierarchical numbering, $25-35/hr rates, 10% contingency
5. **Project type differentiation**: Clear patterns for POC vs Full Service in both BRD and cost structure

**Next Step**: Ready for implementation with complete understanding of:
- BRD document generation patterns and content style
- Excel cost estimation structure and formulas
- Project type differentiation logic
- Multi-file template processing
