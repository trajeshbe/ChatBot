# Project Estimator - Dynamic UI Implementation Plan

**Date**: 2025-11-21
**Purpose**: Complete implementation plan for dynamic UI with BRD and cost estimation generation
**Based on**: Analysis of 6 sample files (3 Excel + 3 PowerPoint)

---

## UI Structure Design

### Section 1: Project Basic Information

```typescript
interface ProjectBasicInfo {
  projectName: string;           // e.g., "Automated Data Extraction Solution"
  clientName: string;            // e.g., "DC Byte"
  projectType: 'POC' | 'Staff Augmentation' | 'Full Service';
  industry: string;              // e.g., "Real Estate", "Private Equity"
  projectDescription: string;    // Long text area - scope summary
  version: string;               // e.g., "1.0"
  date: string;                  // Auto-filled, editable
}
```

**UI Component**:
- Text inputs for name, client, industry
- Radio buttons for project type (triggers dynamic sections)
- Large textarea for project description
- Auto-filled date with override option

---

### Section 2: Project Type Selection (Dynamic Behavior)

**Radio Button Group**: `[POC] [Staff Augmentation] [Full Service]`

**Dynamic Effects**:

#### When "POC" selected:
- ✅ Show: Basic rates, task count, infrastructure setup cost
- ❌ Hide: BAU costs section
- ⚙️ Auto-set: PM/Documentation as FOC (checkbox pre-checked)
- ⚙️ Defaults: contingency_percentage = 0.10, no recurring costs

#### When "Staff Augmentation" selected:
- ✅ Show: Resource roles section, resource rates by role
- ❌ Hide: Infrastructure costs, BAU costs, overhead percentages
- ⚙️ Focus: Team composition, skillsets, hourly rates per role

#### When "Full Service" selected:
- ✅ Show: All sections (rates, overhead, infrastructure, BAU costs)
- ✅ Enable: Monthly recurring costs calculator
- ⚙️ Defaults: BAU section expanded, PM charges optional

---

### Section 3: Scope Details

```typescript
interface ScopeDetails {
  objectives: string[];          // 3-6 bullet points
  dataSourceCategories: {
    webSources: string[];        // List of URLs or types
    emailPDFSources: string[];
    searchMethods: string[];     // SERP API, OpenSearch, etc.
  };
  inScope: string[];             // What's included
  outOfScope: string[];          // What's excluded
  deliverables: string[];        // Expected outputs
}
```

**UI Component**:
- Dynamic list for objectives (Add/Remove buttons)
- Categorized data sources with add/remove capability
- In/Out of scope lists with drag-and-drop
- Deliverables checklist + custom entries

---

### Section 4: Rate Configuration (Dynamic Based on Project Type)

#### A) Simple Rate Structure (POC typically)

```typescript
interface SimpleRates {
  singleHourlyRate: number;      // e.g., $20/hr, $30/hr
  contingencyPercentage: number; // Default: 0.10 (10%)
}
```

**UI**: Single number input + slider for contingency

#### B) Complexity-Based Rates

```typescript
interface ComplexityRates {
  easyRate: number;              // e.g., $30/hr
  mediumRate: number;            // e.g., $30/hr
  hardRate: number;              // e.g., $35/hr
  analysisRate: number;          // e.g., $25/hr
}
```

**UI**: 4 number inputs with labels

#### C) Role-Based Rates (Full Service)

```typescript
interface RoleRates {
  developer: number;             // e.g., $30/hr
  architect: number;             // e.g., $40/hr
  projectManager: number;        // e.g., $35/hr
  businessAnalyst: number;       // e.g., $25/hr
  qaEngineer: number;            // e.g., $26/hr
}
```

**UI**: Table with Role | Rate columns, add custom roles

---

### Section 5: Overhead & Additional Costs (Full Service / POC)

```typescript
interface OverheadCosts {
  solutionArchitect: number;     // Percentage: 0.00-0.15 (0% for POC, 10% for Full Service)
  projectManagement: number;     // Percentage: 0.00-0.15 (0% for POC, 10-15% for Full Service)
  businessAnalyst: number;       // Percentage: 0.00-0.10
  testing: number;               // Percentage: 0.10-0.20

  // Checkboxes for FOC items
  pmFOC: boolean;                // Free of charge (typically true for POC)
  documentationFOC: boolean;     // Free of charge (typically true for POC)
}
```

**UI**:
- Percentage sliders (0-20%)
- Checkboxes for FOC items
- "Use Sample Template Defaults" button to auto-fill based on project type

---

### Section 6: Infrastructure Costs

#### A) One-Time Setup (All Project Types)

```typescript
interface InfrastructureSetup {
  virtualMachines: number;       // e.g., $430
  database: number;              // e.g., $200
  storage: number;               // e.g., $50
  proxyServices: number;         // e.g., $100
  customItems: Array<{name: string, cost: number}>;
}
```

**UI**: Pre-filled common items + "Add Custom Item" button

#### B) Monthly Recurring (Full Service Only)

```typescript
interface InfrastructureRecurring {
  virtualMachine: number;        // e.g., $170/month
  database: number;              // e.g., $100/month
  storage: number;               // e.g., $30/month
}
```

**UI**: Same structure, shown only when "Full Service" selected

---

### Section 7: BAU (Business As Usual) Costs (Full Service Only)

```typescript
interface BAUCosts {
  documentVolume: number;        // e.g., 1000 documents/month
  tokenCostPerDoc: number;       // e.g., $0.11
  supportHoursMonthly: number;   // e.g., 25 hours
  supportRate: number;           // e.g., $30/hr

  // Auto-calculated
  monthlyTokenCost: number;      // documentVolume * tokenCostPerDoc
  monthlySupport: number;        // supportHoursMonthly * supportRate
  totalMonthlyBAU: number;       // Sum of all recurring costs
}
```

**UI**:
- Input fields for volume and rates
- Auto-calculated readonly fields showing totals
- Large summary card: "Total Monthly BAU: $X,XXX"

---

### Section 8: Multi-File Upload (Enhanced - Already Implemented)

```typescript
interface ReferenceFiles {
  scopeDocuments: File[];        // PDF, DOCX
  sampleData: File[];            // PDF, CSV, Excel
  brdTemplates: File[];          // PPTX, DOCX
  costTemplates: File[];         // XLSX
}
```

**UI**: 4 separate dropzones with file previews (already built in Phase 1 & 2)

---

### Section 9: Advanced Options (Collapsible)

```typescript
interface AdvancedOptions {
  numberOfTasks: number;         // Range: 15-30, Default: 25
  timelineDuration: number;      // Weeks, e.g., 8 weeks for POC
  customAssumptions: string[];   // Editable list
  customBenefits: string[];      // Editable list
  generatePowerPoint: boolean;   // Default: true
  generateExcel: boolean;        // Default: true
}
```

**UI**:
- Collapsed by default
- Slider for number of tasks
- Duration input with unit selector (weeks/months)
- Dynamic lists for assumptions and benefits
- Output format checkboxes

---

## Backend Services to Implement

### 1. BRD Generation Service

**File**: `backend/app/services/brd_generation_service.py`

```python
class BRDGenerationService:
    """Generate BRD PowerPoint documents using LLM + python-pptx"""

    def __init__(self, llm_client):
        self.llm_client = llm_client  # GPT-4 or Claude-3

    async def generate_brd_content(
        self,
        project_info: ProjectBasicInfo,
        scope_details: ScopeDetails,
        project_type: str
    ) -> Dict[str, Any]:
        """
        Generate all BRD sections using LLM.
        Returns structured content for PowerPoint generation.
        """

        # Generate Introduction
        introduction = await self._generate_introduction(project_info)

        # Generate Objectives
        objectives = await self._generate_objectives(
            project_info,
            scope_details
        )

        # Generate Scope section
        scope = await self._generate_scope(scope_details)

        # Generate Workflow/Process
        workflow = await self._generate_workflow(project_type)

        # Generate Deliverables
        deliverables = await self._generate_deliverables(project_type)

        # Generate Assumptions
        assumptions = await self._generate_assumptions(project_type)

        # Generate Benefits
        benefits = await self._generate_benefits(project_type)

        return {
            "introduction": introduction,
            "objectives": objectives,
            "scope": scope,
            "workflow": workflow,
            "deliverables": deliverables,
            "assumptions": assumptions,
            "benefits": benefits
        }

    async def _generate_objectives(
        self,
        project_info: ProjectBasicInfo,
        scope_details: ScopeDetails
    ) -> List[str]:
        """Generate 3-6 objectives using LLM"""

        prompt = f"""
Based on the following project information, generate 3-6 project objectives in the style of professional consulting proposals:

Project Name: {project_info.projectName}
Project Type: {project_info.projectType}
Client Industry: {project_info.industry}
Scope Summary: {project_info.projectDescription}

Format each objective as a complete sentence describing what will be achieved.
Start with action verbs like "To automate", "To streamline", "To demonstrate", "To ensure", "To reduce".
Include specific benefits and outcomes.

Reference style (from sample proposals):
- "To demonstrate capabilities to automate the end-to-end data collection and extraction process from various sources..."
- "Automates data extraction from structured and unstructured sources"
- "Ensures accuracy through validation, deduplication, and confidence scoring"
- "Reduces manual effort by 50-60%"

Generate 3-6 objectives:
"""

        response = await self.llm_client.generate(
            prompt=prompt,
            max_tokens=500,
            temperature=0.7
        )

        # Parse into list
        objectives = [
            obj.strip()
            for obj in response.split('\n')
            if obj.strip() and not obj.strip().startswith('#')
        ]

        return objectives[:6]  # Limit to 6

    def create_powerpoint(
        self,
        brd_content: Dict[str, Any],
        project_info: ProjectBasicInfo,
        output_path: str
    ) -> str:
        """Generate PowerPoint file from BRD content"""

        from pptx import Presentation
        from pptx.util import Inches, Pt

        prs = Presentation()

        # Slide 1: Title
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        title = slide.shapes.title
        title.text = project_info.projectName

        subtitle = slide.placeholders[1]
        subtitle.text = f"""Solution Approach Note and Estimates
For {project_info.clientName}
Version {project_info.version}
{project_info.date}"""

        # Slide 2: Introduction
        self._add_content_slide(
            prs,
            "Introduction",
            brd_content["introduction"]
        )

        # Slide 3: Objectives
        self._add_bullet_slide(
            prs,
            f"{project_info.projectType} Objectives",
            brd_content["objectives"]
        )

        # Slide 4-5: Scope
        self._add_scope_slides(prs, brd_content["scope"])

        # Slide 6-7: Workflow
        self._add_workflow_slides(prs, brd_content["workflow"])

        # Slide 8: Deliverables
        self._add_bullet_slide(
            prs,
            f"{project_info.projectType} Deliverables",
            brd_content["deliverables"]
        )

        # Slide 9: Assumptions
        self._add_bullet_slide(
            prs,
            "Assumptions",
            brd_content["assumptions"]
        )

        # Slide 10: Benefits
        self._add_bullet_slide(
            prs,
            "Key Value Adds",
            brd_content["benefits"]
        )

        # Save
        prs.save(output_path)
        return output_path
```

---

### 2. Task Generation Service

**File**: `backend/app/services/task_generation_service.py`

```python
class TaskGenerationService:
    """Generate 20-30 detailed tasks using LLM"""

    async def generate_tasks(
        self,
        project_scope: str,
        project_type: str,
        num_tasks: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Generate detailed task breakdown with effort estimates.

        Returns list of tasks with:
        - task_number: hierarchical numbering (1, 1.1, 1.2, 2, 2.1...)
        - task_name: specific task description
        - category: Planning, Development, Testing, Infrastructure, etc.
        - effort_hours: estimated hours
        - complexity: Easy, Medium, Hard (affects rate)
        - dependencies: list of prerequisite task numbers
        """

        prompt = f"""
Generate a detailed task breakdown for the following project:

Project Type: {project_type}
Scope: {project_scope}
Number of Tasks: {num_tasks}

Follow these patterns from real project estimates:

**Task Categories** (include tasks from each):
1. Planning, Design and System Setup (15-40 hours total)
   - Solution approach and architecture
   - Database design
   - Infrastructure setup

2. Scraper Development/Configuration (largest section, 40-60% of effort)
   - Specific source scrapers
   - Data extraction modules
   - API integrations

3. Data Transformation & Processing (10-15% of effort)
   - Data cleaning
   - Deduplication
   - Logging and alerts
   - File delivery

4. Data Quality & Validation (5-10% of effort)
   - Automated checks
   - Validation rules

5. UAT Issue Fixes (10-15% of effort)
   - Buffer for bug fixes

6. Integration and Deployment (5-10% of effort)
   - System integration
   - Deployment automation

**Task Numbering**: Use hierarchical format
- Main phases: 1, 2, 3, 4, 5, 6
- Sub-tasks: 1.1, 1.2, 2.1, 2.2, 2.3, etc.

**Effort Estimation**:
- Simple tasks: 8-16 hours
- Medium tasks: 24-40 hours
- Complex tasks: 40-80 hours

**Example Output Format**:
1 | Planning, Design and System Setup | Planning | 40 | Medium
1.1 | Solution Approach (System Architecture and Database Design) | Planning | 24 | Medium
1.2 | Infrastructure Setup (VMs, DB, Storage) | Infrastructure | 16 | Easy
2 | Scraper Development/Configuration | Development | 2456 | Hard
2.1 | Media sites and land registries scraping (2000 sources) | Development | 2400 | Hard
2.2 | Company-level press releases scraper | Development | 8 | Easy
...

Generate {num_tasks} tasks following this pattern:
"""

        response = await self.llm_client.generate(
            prompt=prompt,
            max_tokens=2000,
            temperature=0.7
        )

        # Parse response into structured tasks
        tasks = self._parse_task_response(response)

        return tasks

    def _parse_task_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured task list"""
        tasks = []

        for line in response.split('\n'):
            if '|' in line and line.strip():
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 4:
                    try:
                        tasks.append({
                            "task_number": parts[0],
                            "task_name": parts[1],
                            "category": parts[2],
                            "effort_hours": float(parts[3]),
                            "complexity": parts[4] if len(parts) > 4 else "Medium"
                        })
                    except:
                        continue

        return tasks
```

---

### 3. Enhanced Excel Generation Service

**File**: `backend/app/services/excel_generation_service.py`

```python
class ExcelGenerationService:
    """Generate multi-sheet Excel cost estimation"""

    def generate_cost_estimate(
        self,
        project_info: ProjectBasicInfo,
        tasks: List[Dict[str, Any]],
        rates: Union[SimpleRates, ComplexityRates, RoleRates],
        overhead: OverheadCosts,
        infrastructure: InfrastructureSetup,
        bau: Optional[BAUCosts] = None,
        output_path: str = None
    ) -> str:
        """Generate complete Excel cost estimation with multiple sheets"""

        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment

        wb = Workbook()

        # Sheet 1: Task Breakdown
        ws_tasks = wb.active
        ws_tasks.title = "Task Breakdown"
        self._create_task_breakdown_sheet(
            ws_tasks,
            tasks,
            rates,
            overhead
        )

        # Sheet 2: Summary
        ws_summary = wb.create_sheet("Summary")
        self._create_summary_sheet(
            ws_summary,
            project_info,
            tasks,
            rates,
            overhead,
            infrastructure,
            bau
        )

        # Sheet 3: Lookup/Config
        ws_config = wb.create_sheet("Configuration")
        self._create_config_sheet(
            ws_config,
            rates,
            overhead
        )

        # Sheet 4: Infrastructure Details
        ws_infra = wb.create_sheet("Infrastructure")
        self._create_infrastructure_sheet(
            ws_infra,
            infrastructure,
            bau
        )

        # Sheet 5: BAU Costs (Full Service only)
        if bau and project_info.projectType == "Full Service":
            ws_bau = wb.create_sheet("BAU Monthly Costs")
            self._create_bau_sheet(ws_bau, bau)

        # Save
        wb.save(output_path)
        return output_path

    def _create_task_breakdown_sheet(
        self,
        ws,
        tasks,
        rates,
        overhead
    ):
        """Create main task breakdown sheet"""

        # Headers
        headers = [
            "S.No",
            "Task Description",
            "Category",
            "Complexity/Role",
            "Effort (Hours)",
            "Rate ($/hr)",
            "Cost ($)"
        ]

        ws.append(headers)

        # Style headers
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")

        # Add tasks
        total_hours = 0
        total_cost = 0

        for task in tasks:
            # Determine rate
            if isinstance(rates, SimpleRates):
                rate = rates.singleHourlyRate
            elif isinstance(rates, ComplexityRates):
                complexity = task.get("complexity", "Medium").lower()
                rate = {
                    "easy": rates.easyRate,
                    "medium": rates.mediumRate,
                    "hard": rates.hardRate,
                    "analysis": rates.analysisRate
                }.get(complexity, rates.mediumRate)
            else:  # Role-based
                role = task.get("role", "developer").lower()
                rate = getattr(rates, role, rates.developer)

            hours = task["effort_hours"]
            cost = hours * rate

            ws.append([
                task["task_number"],
                task["task_name"],
                task["category"],
                task.get("complexity", "Medium"),
                hours,
                rate,
                cost
            ])

            total_hours += hours
            total_cost += cost

        # Add overhead rows
        current_row = len(tasks) + 2

        # Contingency
        contingency_hours = total_hours * 0.10
        contingency_cost = total_cost * 0.10

        ws.append([
            "",
            "Buffer for Contingencies (10%)",
            "Overhead",
            "",
            contingency_hours,
            "",
            contingency_cost
        ])

        # Solution Architect (if applicable)
        if overhead.solutionArchitect > 0:
            sa_cost = total_cost * overhead.solutionArchitect
            ws.append([
                "",
                f"Solution Architect ({overhead.solutionArchitect*100}%)",
                "Overhead",
                "",
                "",
                "",
                sa_cost
            ])
            total_cost += sa_cost

        # Total row
        ws.append([
            "",
            "TOTAL PROJECT COST",
            "",
            "",
            total_hours + contingency_hours,
            "",
            total_cost + contingency_cost
        ])

        # Bold and highlight total row
        total_row = ws.max_row
        for cell in ws[total_row]:
            cell.font = Font(bold=True, size=12)
            cell.fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
```

---

## Implementation Steps

1. ✅ **Create dynamic UI structure** (Sections 1-9 above)
2. **Enhance backend services**:
   - BRD Generation Service with LLM
   - Task Generation Service
   - Enhanced Excel Generation Service
3. **Integrate file upload** (already working from Phase 2)
4. **Test end-to-end flow**
5. **Add download functionality** for both PPTX and XLSX

---

## API Endpoint Enhancement

**Current**: `POST /api/v1/project-estimator/generate`

**Enhanced Request Schema**:
```python
class EnhancedProjectEstimatorRequest(BaseModel):
    # Basic Info
    projectName: str
    clientName: str
    projectType: Literal["POC", "Staff Augmentation", "Full Service"]
    industry: str
    projectDescription: str

    # Scope
    objectives: List[str] = []
    dataSourceCategories: Dict[str, List[str]] = {}
    inScope: List[str] = []
    outOfScope: List[str] = []
    deliverables: List[str] = []

    # Rates (union type based on projectType)
    rateStructure: Union[SimpleRates, ComplexityRates, RoleRates]

    # Overhead
    overhead: OverheadCosts

    # Infrastructure
    infrastructure: InfrastructureSetup
    infrastructureRecurring: Optional[InfrastructureRecurring] = None

    # BAU (Full Service only)
    bau: Optional[BAUCosts] = None

    # Advanced
    numberOfTasks: int = 25
    timelineDuration: int = 8
    customAssumptions: List[str] = []
    customBenefits: List[str] = []

    # File references (from Phase 2 upload)
    scopeDocumentIds: List[str] = []
    sampleDataIds: List[str] = []
    brdTemplateIds: List[str] = []
    costTemplateIds: List[str] = []
```

**Response**:
```python
class EnhancedProjectEstimatorResponse(BaseModel):
    brd_document_url: str           # Download URL for PPTX
    cost_estimation_url: str        # Download URL for XLSX
    project_summary: Dict[str, Any]
    total_cost: float
    total_effort_hours: float
    timeline_weeks: int
    generated_tasks_count: int
```

---

**Status**: Implementation plan complete. Ready to build.
**Next**: Implement frontend dynamic UI component
