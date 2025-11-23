# Claude Code Prompt: Configurable Project Estimator Application

## Project Overview
Build a web-based **Project Task, Effort Estimation & Cost Calculator** that takes a project scope description as input and generates:
1. **Business Requirement Document (BRD)** - Microsoft Word format
2. **Cost Estimation Sheet** - Excel format with multiple interconnected tabs

## Input
- Project scope description (text input or uploaded document)
- Configurable parameters for billing rates, resource allocation, and infrastructure costs

## Output Documents

### 1. Business Requirement Document (BRD) Structure
Generate a Word document with the following sections:

```
BUSINESS REQUIREMENTS DOCUMENT (BRD)
│
├── 1. Project Information
│   ├── Project Name
│   ├── Version
│   ├── Date
│   └── Prepared By
│
├── 2. Introduction
│   ├── Project Overview
│   └── Purpose Statement
│
├── 3. Current Challenges
│   └── Bullet list of pain points
│
├── 4. Proposed Solution
│   ├── High-level approach
│   ├── Key technologies
│   └── AI/ML components
│
├── 5. Goals and Objectives
│   └── Numbered list of measurable outcomes
│
├── 6. Scope
│   ├── In Scope (bullet list)
│   └── Out of Scope (bullet list)
│
├── 7. Functional Requirements
│   ├── FR1 - [Component Name]
│   ├── FR2 - [Component Name]
│   └── ... (continue for each major feature)
│
├── 8. Non-Functional Requirements
│   ├── Performance
│   ├── Security
│   ├── Scalability
│   └── Reliability
│
├── 9. Technical Architecture
│   ├── System Components
│   ├── Data Flow
│   └── Integration Points
│
├── 10. Assumptions and Constraints
│
├── 11. Dependencies
│
└── 12. Success Criteria
```

### 2. Cost Estimation Excel Workbook Structure

Create an Excel file with the following tabs:

#### **Tab 1: AIML_cost** (Main Calculation Sheet)
This is the detailed breakdown of AI/ML development effort.

**Column Structure:**
- **Column A**: Description (Task/Phase name)
- **Column B**: hrs_simple (Hours for simple complexity)
- **Column C**: hrs_medium (Hours for medium complexity)
- **Column D**: hrs (Actual hours = selected complexity level)
- **Column E**: Cost per hour (from lookup table)
- **Column F**: total_cost (= Column D × Column E)
- **Column G**: Notes
- **Column H**: Type (Scraping/AI/ML/Integration)
- **Column I**: Stage (Planning/Development/Testing/Documentation)
- **Columns J-K+**: Resource allocation by week

**Phase Breakdown:**
1. **Planning Phase**
   - Analysis of Input Sources and Schema Alignment
   - Assess extraction options
   - Design retrieval-augmented extraction flow
   - Analysis of requirements
   - Define confidence scoring logic
   
   *Sub-calculation:*
   - Solution Architect Effort = ROUNDUP(SUM(planning_tasks) × lookup!SA_percentage, 0)
   - PM Effort = ROUNDUP(SUM(planning_tasks) × lookup!PM_percentage, 0)
   - BA Effort = ROUNDUP(SUM(planning_tasks) × lookup!BA_percentage, 0)

2. **Development Phase**
   - Component 1 development
   - Component 2 development
   - API integration
   - Database design and implementation
   - Frontend development
   - Backend development
   
3. **Integration Phase**
   - System integration
   - API integration testing
   - End-to-end workflow testing

4. **Documentation Phase**
   - Technical documentation
   - User manuals
   - API documentation
   - Deployment guides

5. **Testing Phase**
   - Dev Unit Testing = Development_Hours × lookup!DevTest_percentage
   - QA Testing = Development_Hours × lookup!QATest_percentage
   - Integration Testing = Development_Hours × lookup!IntegrationTest_percentage

6. **Project Management & Contingency**
   - PM Effort (ongoing)
   - Contingency = Total_Development_Hours × lookup!Contingency_percentage

7. **Infrastructure Costs**
   - One-time setup costs
   - Cloud services
   - Database hosting
   - API costs
   - Security and monitoring tools

#### **Tab 2: AIML_COST_SUMMARY**
High-level summary view of costs.

**Formula Structure:**
```
Row 1: Headers [Description | Hours | Cost]

Row 2: Project Name/Description
       Cost = AIML_cost!D5 (reference to total)

Row 3: Planning - Customising Framework
       Hours = VLOOKUP("Planning", AIML_cost!$A:$D, 2, 0)
       Cost = VLOOKUP("Planning", AIML_cost!$A:$D, 4, 0)

Row 4: Development - Framework
       Hours = VLOOKUP("Development", AIML_cost!$A:$D, 2, 0)
       Cost = VLOOKUP("Development", AIML_cost!$A:$D, 4, 0)

Row 5: Integration Effort
       Hours = VLOOKUP("Integration", AIML_cost!$A:$D, 2, 0)
       Cost = VLOOKUP("Integration", AIML_cost!$A:$D, 4, 0)

Row 6: Documentation
       Hours = VLOOKUP("Documentation", AIML_cost!$A:$D, 2, 0)
       Cost = VLOOKUP("Documentation", AIML_cost!$A:$D, 4, 0)

Row 7: Testing
       Hours = VLOOKUP("Testing", AIML_cost!$A:$D, 2, 0)
       Cost = VLOOKUP("Testing", AIML_cost!$A:$D, 4, 0)

Row 8: PM & Contingency
       Hours = VLOOKUP("PM & Contingency", AIML_cost!$A:$D, 2, 0)
       Cost = VLOOKUP("PM & Contingency", AIML_cost!$A:$D, 4, 0)

Row 9: Total Infra cost for initial phase
       Cost = VLOOKUP("Infrastructure", AIML_cost!$A:$D, 4, 0)

Row 10: Total One-time Development Cost
        Cost = SUM(C3:C9)

Row 11: BAU - Ongoing Recurring Cost (monthly)
        Cost = VLOOKUP("BAU", AIML_cost!$A:$D, 4, 0)
```

#### **Tab 3: lookup**
Reference data and percentages for calculations.

**Structure:**
```
Column A: Item Name
Column B: Planning Stage Value
Column C: Development Stage Value
Column D: Testing Stage Value
...
Column H: Role Name
Column I: Effort Percentage

Key Lookup Values:
- Labor cost (planning): 25
- Labor cost (dev): 30
- Labor cost (testing): 25
- UI labor cost (dev): 22

Role Effort Percentages:
- Solution Architect: 0.10 (10%)
- PM: 0.05 (5%)
- BA: 0.05 (5%)
- Contingency: 0.10 (10%)

Testing Percentages (applied to dev hours):
- Dev Unit Testing: 0.20 (20%)
- QA Testing: 0.25 (25%)
- Integration Testing: 0.20 (20%)

Scraping Labor cost:
- Planning: 22
- Development: 22
- Testing: 22
```

#### **Tab 4: unit_cost**
Infrastructure and recurring costs.

**Structure:**
```
Row 1: One time cost | [Value]
Row 2: infra | [Monthly Infrastructure Cost]
Row 3: BAU per month | [Business As Usual monthly cost]
Row 4: BAU per year | [BAU_per_month × 12]
Row 5: Total cost | [One_time + BAU_per_year]
Row 6: # of entries per year | [Expected volume]
Row 7: cost per document | [Total_cost / entries_per_year]
```

**Default Values:**
- One-time infrastructure setup: $280
- Monthly BAU: $1,030
- Annual BAU: $12,360
- Total first-year cost: $30,664 (one-time + annual)

#### **Tab 5: Resource_Loading**
Visual timeline showing resource allocation by week/sprint.

**Structure:**
- Row 1-2: Headers
- Row 3: Week numbers (Week-1, Week-2, ..., Week-16)
- Row 4+: Resource categories
  - Scraper team
  - AI/ML team
  - Frontend team
  - Backend team
  - QA team
  - Project Management
  - Total hours per week

**Calculation Logic:**
- Each cell = hours allocated for that resource in that week
- Derived from AIML_cost sheet: 
  - Week allocation = Task_hours / 7 (convert to weeks)
  - Daily allocation = Week_hours / 2 / 5 (assuming 2 resources, 5 days/week)

## Estimation Logic Algorithm

### Phase 1: Analyze Project Scope
```
INPUT: Project scope description

ANALYZE:
1. Identify key components/modules
2. Classify complexity (Simple/Medium/Complex)
3. Identify technology stack requirements
4. Determine AI/ML components needed
5. Estimate data volume and infrastructure needs
6. Identify integration points

OUTPUT: Structured project breakdown
```

### Phase 2: Generate Task Breakdown
```
FOR EACH component:
  1. Planning tasks
     - Requirements analysis
     - Architecture design
     - Schema design
     
  2. Development tasks
     - Frontend development
     - Backend development
     - AI/ML model development
     - Database implementation
     - API development
     
  3. Integration tasks
     - Component integration
     - API integration
     - Third-party service integration
     
  4. Testing tasks (auto-calculated)
     - Unit testing = Dev_hours × 0.20
     - QA testing = Dev_hours × 0.25
     - Integration testing = Dev_hours × 0.20
     
  5. Documentation tasks
     - Technical docs
     - User manuals
     - API documentation
```

### Phase 3: Calculate Effort
```
FOR EACH task:
  1. Base effort (hours) = complexity_multiplier × base_hours
  2. Add role-based overhead:
     - Solution Architect = total_planning_hours × 0.10
     - PM = total_hours × 0.05
     - BA = total_planning_hours × 0.05
  3. Add testing overhead (auto-calculated from dev hours)
  4. Add contingency = total_hours × 0.10
```

### Phase 4: Calculate Costs
```
FOR EACH task:
  Cost = Hours × Billing_Rate
  
WHERE Billing_Rate is:
  - Planning: $25/hour
  - Development: $30/hour
  - Testing: $25/hour
  - UI Development: $22/hour
  - Solution Architect: $40/hour
  
Total_Project_Cost = 
  SUM(All_Task_Costs) + 
  Infrastructure_One_Time_Cost + 
  (BAU_Monthly_Cost × Project_Duration_Months)
```

### Phase 5: Generate Documents
```
PARALLEL:
  1. Generate BRD (Word)
     - Extract requirements from scope
     - Structure into BRD template
     - Add technical details
     
  2. Generate Cost Estimation (Excel)
     - Populate all tabs with calculations
     - Link formulas between tabs
     - Add resource loading timeline
```

## UI Requirements

### Main Interface Layout
```
┌─────────────────────────────────────────────────────────────┐
│ PROJECT ESTIMATOR                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ [Tab] Project Scope  [Tab] Configuration  [Tab] Results    │
│                                                             │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ PROJECT SCOPE                                        │   │
│ │                                                      │   │
│ │ Project Name: [_____________________________]       │   │
│ │                                                      │   │
│ │ Scope Description:                                  │   │
│ │ ┌────────────────────────────────────────────────┐ │   │
│ │ │                                                 │ │   │
│ │ │   [Enter or paste project scope...]            │ │   │
│ │ │                                                 │ │   │
│ │ │   OR                                            │ │   │
│ │ │                                                 │ │   │
│ │ │   [Upload Document] 📄                          │ │   │
│ │ │                                                 │ │   │
│ │ └────────────────────────────────────────────────┘ │   │
│ │                                                      │   │
│ │ Complexity: ○ Simple  ⦿ Medium  ○ Complex          │   │
│ │                                                      │   │
│ │ [Generate Estimation] 🚀                            │   │
│ └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Configuration Tab (Editable Parameters)
```
┌─────────────────────────────────────────────────────────────┐
│ CONFIGURATION                                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─ BILLING RATES ─────────────────────────────────────┐   │
│ │ Planning Stage ($/hour):        [25___]            │   │
│ │ Development Stage ($/hour):     [30___]            │   │
│ │ Testing Stage ($/hour):         [25___]            │   │
│ │ UI Development ($/hour):        [22___]            │   │
│ │ Solution Architect ($/hour):    [40___]            │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                             │
│ ┌─ EFFORT PERCENTAGES ────────────────────────────────┐   │
│ │ Solution Architect Effort:      [10___]%           │   │
│ │ PM Effort:                      [5____]%           │   │
│ │ BA Effort:                      [5____]%           │   │
│ │ Contingency:                    [10___]%           │   │
│ │                                                     │   │
│ │ Dev Unit Testing:               [20___]%           │   │
│ │ QA Testing:                     [25___]%           │   │
│ │ Integration Testing:            [20___]%           │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                             │
│ ┌─ INFRASTRUCTURE COSTS ──────────────────────────────┐   │
│ │ One-time Setup Cost ($):        [280__]            │   │
│ │ Monthly BAU Cost ($):           [1030_]            │   │
│ │ Expected Annual Volume:         [12000]            │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                             │
│ [Reset to Defaults]  [Save Configuration]                  │
└─────────────────────────────────────────────────────────────┘
```

### Results Tab
```
┌─────────────────────────────────────────────────────────────┐
│ ESTIMATION RESULTS                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─ SUMMARY ────────────────────────────────────────────┐   │
│ │                                                       │   │
│ │ Total Development Hours:     [456] hours             │   │
│ │ Total Development Cost:      [$13,680]               │   │
│ │ Infrastructure (One-time):   [$280]                  │   │
│ │ Annual BAU Cost:             [$12,360]               │   │
│ │ ─────────────────────────────────────────────────    │   │
│ │ TOTAL FIRST YEAR COST:       [$26,320]              │   │
│ │                                                       │   │
│ │ Estimated Timeline:          [12] weeks              │   │
│ │                                                       │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                             │
│ ┌─ PHASE BREAKDOWN ────────────────────────────────────┐   │
│ │                                                       │   │
│ │ ▼ Planning            [72 hrs]    [$1,800]          │   │
│ │ ▼ Development         [240 hrs]   [$7,200]          │   │
│ │ ▼ Integration         [48 hrs]    [$1,200]          │   │
│ │ ▼ Testing             [96 hrs]    [$2,400]          │   │
│ │ ▼ Documentation       [24 hrs]    [$600]            │   │
│ │ ▼ PM & Contingency    [48 hrs]    [$480]            │   │
│ │                                                       │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                             │
│ ┌─ INTERACTIVE COST TABLE (Editable) ─────────────────┐   │
│ │                                                       │   │
│ │ [Spreadsheet-like view of AIML_cost tab]            │   │
│ │ - Click any cell to edit                             │   │
│ │ - Formulas auto-recalculate                          │   │
│ │                                                       │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                             │
│ [📥 Download BRD (Word)]  [📥 Download Cost Sheet (Excel)] │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Key Features to Implement

### 1. Intelligent Scope Analysis
- Use LLM (Claude API) to analyze project scope
- Extract key components, technologies, and requirements
- Classify complexity automatically
- Identify similar historical projects

### 2. Dynamic Task Generation
- Generate task breakdown based on scope analysis
- Adjust effort based on complexity and technology stack
- Apply industry-standard ratios for testing and overhead

### 3. Editable Estimation
- Allow users to modify any cell in the cost estimation
- Auto-recalculate dependent formulas
- Maintain formula integrity across tabs

### 4. Template Management
- Save and load estimation templates
- Support multiple project types (AI/ML, Web App, Mobile App, Data Engineering)
- Import historical estimation data

### 5. Export Functionality
- Generate Word document with proper formatting
- Generate Excel with all formulas intact
- Preserve cell formatting and styles
- Include charts and visualizations

### 6. Formula Preservation
- All Excel formulas must work in the exported file
- VLOOKUP references between tabs
- SUM, ROUNDUP, and conditional formulas
- Percentage calculations

## Technical Implementation Requirements

### Frontend
- React or Next.js
- Rich text editor for scope input
- Spreadsheet component (e.g., Handsontable, AG Grid)
- File upload/download functionality

### Backend
- API integration with Claude for scope analysis
- Excel generation: `exceljs` or `xlsx` library
- Word generation: `docx` library
- Formula engine for real-time calculations

### Key Libraries
```javascript
// Excel manipulation
import ExcelJS from 'exceljs';

// Word document generation
import { Document, Packer, Paragraph, TextRun } from 'docx';

// Spreadsheet UI
import { HotTable } from '@handsontable/react';
```

### Formula Implementation Examples

**Example 1: Planning Phase Hours**
```javascript
// Cell D4 in AIML_cost sheet
const planningHours = sumRange('D5:D9');
```

**Example 2: Solution Architect Effort**
```javascript
// Cell D11 in AIML_cost sheet
const saEffort = Math.ceil(
  sumRange('$D$5:$D$9') * lookupValue('lookup', 'B', 7)
);
```

**Example 3: Total Cost**
```javascript
// Cell F5 in AIML_cost sheet
const totalCost = getCell('D5') * getCell('E5');
```

**Example 4: Summary VLOOKUP**
```javascript
// Cell C3 in AIML_COST_SUMMARY
const planningCost = vlookup(
  'Planning',
  'AIML_cost!$A:$D',
  4,
  false
);
```

## AI Analysis Prompts

### Scope Analysis Prompt Template
```
Analyze the following project scope and extract:

1. Project Type: [AI/ML, Web Application, Mobile App, Data Engineering, etc.]
2. Key Components: List all major system components
3. Technologies Required: Frontend, backend, database, AI/ML frameworks
4. Complexity Level: Simple/Medium/Complex based on:
   - Number of integrations
   - AI/ML sophistication
   - Data volume
   - Custom development required
5. Estimated Phases: Planning, Development, Integration, Testing timeframes
6. Risk Factors: Technical, timeline, or resource risks

Project Scope:
{user_input}

Provide structured output in JSON format.
```

### BRD Generation Prompt Template
```
Generate a comprehensive Business Requirements Document for the following project:

Project Name: {project_name}
Scope: {scope_description}
Complexity: {complexity_level}
Key Components: {components}

Include all standard BRD sections:
- Introduction and business context
- Current challenges being addressed
- Proposed solution with technical approach
- Functional requirements (categorized by component)
- Non-functional requirements
- Technical architecture overview
- Assumptions and constraints
- Success criteria

Use professional consulting language. Be specific and detailed.
```

## Validation Rules

### Data Validation
- All hour estimates must be positive numbers
- Billing rates must be > 0
- Percentages must be between 0-100
- Total hours = sum of all phase hours
- Testing hours = derived from development hours

### Formula Validation
- Check circular references
- Validate VLOOKUP ranges exist
- Ensure SUM ranges are valid
- Test formula recalculation

### Document Validation
- BRD must have all required sections
- Cost sheet must have all required tabs
- All formulas must be preserved in export
- File sizes must be reasonable (<5MB)

## Example Workflow

```
1. User enters project scope:
   "Build an AI-powered document extraction system that processes 
    construction drawings and extracts key information like floor levels, 
    GFA, and external areas."

2. System analyzes scope with Claude:
   - Identifies: AI/ML project with document processing
   - Components: PDF parsing, ML classification, data extraction, API
   - Complexity: Medium
   - Estimates: 12 weeks, 3 developers

3. System generates task breakdown:
   Planning (72 hrs)
   ├── Requirements analysis (16 hrs)
   ├── Architecture design (24 hrs)
   └── Schema design (32 hrs)
   
   Development (240 hrs)
   ├── PDF parser (40 hrs)
   ├── ML classification (80 hrs)
   ├── Extraction engine (60 hrs)
   ├── API development (40 hrs)
   └── Frontend (20 hrs)
   
   Testing (96 hrs) [Auto-calculated: 240 × 0.40]
   
   PM & Contingency (48 hrs) [Auto-calculated: 408 × 0.15]

4. System calculates costs:
   Development: 408 hrs × $28.50 avg = $11,628
   Infrastructure: $280 one-time
   BAU: $1,030/month × 12 = $12,360
   Total: $24,268

5. System generates documents:
   - BRD with all sections populated
   - Excel with all tabs and working formulas

6. User reviews, edits costs interactively

7. User downloads both documents
```

## Success Criteria

✅ Accurate scope analysis (>85% accuracy compared to manual)
✅ Complete BRD generation with all sections
✅ Excel file with all formulas working
✅ Interactive editing without breaking formulas
✅ Export preserves all formatting and calculations
✅ Processing time < 30 seconds for typical project
✅ Support for projects ranging from $5K to $500K
✅ Editable configuration that persists

## Deliverables

1. Fully functional web application
2. API endpoint for programmatic access
3. Documentation for configuration and usage
4. Sample project templates (3-5 examples)
5. Unit tests for formula engine
6. Integration tests for document generation

---

**Note**: This application should leverage Claude's API for intelligent scope analysis and requirement extraction while maintaining Excel-like precision for all calculations and formula preservation.
