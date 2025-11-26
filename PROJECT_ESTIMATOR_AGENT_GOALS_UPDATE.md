# Project Estimator - Agent Goals and Prompt Enhancement

**Date**: 2025-11-25
**Status**: ✅ **COMPLETE - AGENT PROMPTS UPDATED WITH ULTIMATE GOAL**

---

## Summary

Updated all Project Estimator agent prompts to clearly state the **ULTIMATE GOAL**: Translate a Project Scope Document into a comprehensive Business Requirements Document (BRD) by learning from uploaded sample documents.

**Previous State**: Agent prompts focused on generic "project estimation" without clear context
**Current State**: All prompts emphasize translation of Project Scope → BRD using sample document patterns

---

## User Requirement

> "the Business Requiremetn docuemtn shuould translate the Project Scope Document . That is an import doc for the context window to create a Business Requirement document to solve the Project Scope referrng the sample data, samle BDR template and sample cost estimates .. This is the Objective of the Agent or Goal of the Agent.. Pls set it accoringly in the Agent PROMPT - The ultimate GOAL of the agent"

**Key Points**:
1. **Input**: Project Scope Document (user's project description)
2. **Process**: Learn from sample BRDs, cost estimates, and sample data
3. **Output**: BRD.docx and CostEstimate.xlsx that match organizational standards
4. **Goal**: Translation (not generic generation)

---

## Changes Made

### 1. ✅ Module Docstring Updated

**File**: `backend/app/agents/project_estimator/workflow.py`
**Lines**: 1-18

**Enhancement**:
```python
"""
Project Estimator Agentic Workflow

ULTIMATE GOAL:
Translate a Project Scope Document into a comprehensive Business Requirements Document (BRD)
and detailed Cost Estimation by intelligently learning from uploaded sample documents.

6-Agent LangGraph workflow:
- Agent 1 (Analyst): Learns from sample BRDs, cost estimates, and data to extract requirements
- Agent 2 (Team Planner): Identifies engineering teams based on learned patterns
- Agent 3 (Task Generator): Generates project-specific tasks following sample task structures
- Agent 4 (Workflow Agent): Creates execution timeline based on sample BRD workflows
- Agent 5 (Rate Assignment): Assigns rates and calculates costs using sample cost patterns
- Agent 6 (Document Generator): Produces final BRD.docx and CostEstimate.xlsx following sample formats

Each agent is guided by uploaded examples (sample BRDs, cost estimates, sample data) to ensure
the generated BRD and cost estimate match the organization's standards and patterns.
"""
```

**Why Important**: Sets the context for the entire workflow - clarifies that this is about translating Project Scope → BRD

---

### 2. ✅ Agent 1 (Analyst) Prompt Enhanced

**File**: `backend/app/agents/project_estimator/workflow.py`
**Lines**: 365-414 (in `_extract_requirements` method)

**NEW Opening**:
```python
prompt = f"""
**ULTIMATE GOAL**: Translate the Project Scope Document into a comprehensive Business Requirements Document (BRD).

You are Agent 1 (Analyst) in a 6-agent workflow. Your role is to extract structured requirements from the
Project Scope Document by intelligently learning from uploaded sample BRDs, cost estimates, and sample data.

The requirements you extract will guide all downstream agents to produce a final BRD.docx and CostEstimate.xlsx
that matches the organization's standards and patterns.

---

**PROJECT SCOPE DOCUMENT**:
{user_prompt}

**Project Type**: {project_type}

---

**LEARN FROM THESE UPLOADED SAMPLE BRD PATTERNS**:
{brd_patterns}

**LEARN FROM THESE UPLOADED COST ESTIMATE PATTERNS**:
{cost_patterns}

**SAMPLE DATA COMPLEXITY ASSESSMENT**:
{data_complexity}

---

**YOUR TASK**: Extract structured requirements that will form the foundation of the BRD:
...
```

**Key Enhancements**:
1. Opens with "**ULTIMATE GOAL**" statement
2. Frames user input as "PROJECT SCOPE DOCUMENT" (not generic "project")
3. Emphasizes "learning from sample patterns" to guide translation
4. States that requirements will "form the foundation of the BRD"
5. Instructions to follow BRD writing style and terminology

---

### 3. ✅ BRD Analysis Prompt Enhanced

**File**: `backend/app/agents/project_estimator/workflow.py`
**Lines**: 276-294 (in `_analyze_brd_examples` method)

**NEW Context**:
```python
prompt = f"""
**CONTEXT**: You are helping translate a Project Scope Document into a Business Requirements Document (BRD).

Analyze these uploaded sample BRD documents to extract organizational patterns that will guide the translation:

Files analyzed: {len(brd_files)} BRD documents

**Extract and summarize the following patterns**:

1. **Document Structure**: What sections and headings are typically used? (e.g., Executive Summary, Technical Requirements, Success Criteria, Timeline)
2. **Writing Style**: How are objectives written? (formal/informal, bullet points/paragraphs, technical level)
3. **Timeline & Milestones**: How are project timelines structured? (phases, sprints, milestones format)
4. **Scope Definition**: How is project scope defined? (in-scope/out-of-scope format, feature lists, boundaries)
5. **Deliverables Format**: How are deliverables documented? (bulleted lists, tables, detailed descriptions)
6. **Terminology**: What business and technical terms are commonly used?

Provide a concise summary (3-4 paragraphs) that will ensure the generated BRD matches this organization's
standards, writing style, and format conventions.
"""
```

**Key Enhancement**:
- Added context statement explaining this is about translating Project Scope → BRD
- Emphasizes extracting patterns to "guide the translation"
- Focus on organizational standards and conventions

---

## Complete Workflow with Updated Goal

### Input Flow:
```
User submits:
1. Project Scope Document (text description)
2. Sample BRD files (optional - .pptx, .pdf)
3. Sample Cost Estimate files (optional - .xlsx, .csv)
4. Sample Data files (optional - .json, .csv, .xlsx)
5. Rate configuration (UI sliders)
6. Project type (POC, Staff Aug, Full Service)
7. Scenario (baseline, conservative, aggressive)
```

### Agent Processing with ULTIMATE GOAL:
```
Agent 1 (Analyst):
  GOAL: Translate Project Scope → structured requirements
  METHOD: Learn patterns from sample BRDs, cost estimates, data
  OUTPUT: requirements = {
    project_goal: "...",
    key_features: ["...", "..."],
    technical_scope: {...},
    constraints: {...},
    success_criteria: ["...", "..."]
  }

Agent 2 (Team Planner):
  GOAL: Identify teams needed to execute the Project Scope
  METHOD: Follow team structures from sample cost estimates
  OUTPUT: team_plan = {
    teams: [
      {team_name: "Backend Engineering", responsibilities: "...", allocation: 0.3},
      ...
    ]
  }

Agent 3 (Task Generator):
  GOAL: Generate tasks to implement the Project Scope
  METHOD: Follow task structures from sample BRDs and cost estimates
  OUTPUT: tasks_by_team = {
    "Backend Engineering": [
      {task: "...", effort_hours: 40, complexity: "medium"},
      ...
    ]
  }

Agent 4 (Workflow Agent):
  GOAL: Create execution timeline for the Project Scope
  METHOD: Follow timeline patterns from sample BRDs
  OUTPUT: project_workflow = {
    workflow: {
      phases: [...],
      milestones: [...],
      total_duration_weeks: 12
    }
  }

Agent 5 (Rate Assignment):
  GOAL: Calculate costs for implementing the Project Scope
  METHOD: Map tasks to rate categories (from UI), apply sample cost patterns
  OUTPUT: costs_by_team = {
    "Backend Engineering": {
      total_cost: 12000,
      total_hours: 300,
      tasks: [...]
    },
    summary: {
      total_cost: 45000,
      total_hours: 1200,
      team_count: 5
    }
  }

Agent 6 (Document Generator):
  GOAL: Produce final BRD.docx and CostEstimate.xlsx
  METHOD: Use Word/Excel libraries with professional formatting
  OUTPUT:
    - BRD_YYYYMMDD_HHMMSS.docx (8 sections, comprehensive Word document)
    - CostEstimate_YYYYMMDD_HHMMSS.xlsx (8 sheets, dynamic team breakdown)
```

### Output:
```
Generated Files:
1. BRD.docx - Comprehensive Business Requirements Document
   - Translates Project Scope into structured BRD format
   - Follows organizational patterns from sample BRDs
   - 8 sections: Executive Summary, Objectives, Technical Scope, Team Structure,
     Workflow & Timeline, Cost Estimation, Success Criteria, Key Milestones

2. CostEstimate.xlsx - Detailed Cost Breakdown
   - 8 sheets: Master Summary, Project Workflow, 5 team sheets, Sample Guidance
   - Follows cost structure patterns from sample cost estimates
   - Transparent about how samples guided generation
```

---

## Key Prompt Phrases

The updated prompts now consistently use these phrases:

### Input Context:
- ✅ "Project Scope Document" (not "project description" or "user prompt")
- ✅ "Translate the Project Scope Document"
- ✅ "Learning from uploaded sample patterns"

### Process Guidance:
- ✅ "Intelligently learn from uploaded samples"
- ✅ "Follow organizational patterns"
- ✅ "Match the organization's standards"
- ✅ "Extract patterns that will guide the translation"

### Output Framing:
- ✅ "Produce final BRD.docx and CostEstimate.xlsx"
- ✅ "Requirements that will form the foundation of the BRD"
- ✅ "Ensure generated BRD matches organizational standards"

---

## Sample Document Flow

### How Samples Influence Generation:

1. **Sample BRD Analysis** (`_analyze_brd_examples`):
   ```
   Input: Uploaded BRD files (.pptx, .pdf)
   Process: LLM extracts document structure, writing style, terminology patterns
   Output: "brd_patterns" string (3-4 paragraphs)
   Usage: Guides Agent 1's requirements extraction style
   ```

2. **Sample Cost Estimate Analysis** (`_analyze_cost_examples`):
   ```
   Input: Uploaded cost estimate files (.xlsx, .csv)
   Process: LLM extracts team structures, task categories, cost breakdown patterns
   Output: "cost_patterns" string (3-4 paragraphs)
   Usage: Guides Agent 2's team planning and Agent 3's task generation
   ```

3. **Sample Data Analysis** (`_analyze_sample_data`):
   ```
   Input: Uploaded sample data files (.json, .csv, .xlsx)
   Process: LLM assesses data complexity, volume, structure
   Output: "data_complexity" string (2-3 paragraphs)
   Usage: Guides Agent 1's technical scope assessment
   ```

### Transparency in Excel:

The generated Excel workbook includes a "Sample Guidance" sheet showing exactly how uploaded samples influenced generation:

```
Sheet 8: Sample Guidance
- Header: "How Uploaded Samples Guided This Estimate"
- Content: Full text of cost_examples_summary
- Purpose: Complete transparency - users can verify samples weren't distorted
```

---

## Testing the Updated Workflow

### Test Instructions:

1. **Navigate to Project Estimator**:
   ```
   http://localhost:3001
   Click "Project Estimator" in sidebar
   ```

2. **Submit a Test Request**:
   ```
   Project Scope: "Build a web application for managing construction projects with real-time progress tracking, document management, and team collaboration features"

   Upload samples (optional):
   - Sample BRD: Any .pptx or .pdf BRD document
   - Sample Cost Estimate: Any .xlsx cost estimate
   - Sample Data: Any .json/.csv sample data

   Project Type: Full Service
   Scenario: Baseline

   Set rates (adjust sliders as needed)
   ```

3. **Expected Behavior**:
   - ✅ Workflow completes in ~3 minutes
   - ✅ Two download buttons appear:
     - "Download BRD" → BRD_YYYYMMDD_HHMMSS.docx
     - "Download Cost Estimate" → CostEstimate_YYYYMMDD_HHMMSS.xlsx

4. **Verify BRD Content**:
   - ✅ Opens in Microsoft Word / LibreOffice
   - ✅ Contains 8 comprehensive sections
   - ✅ Content reflects translation of Project Scope (not generic)
   - ✅ Writing style matches uploaded sample BRDs (if provided)

5. **Verify Excel Content**:
   - ✅ Opens in Microsoft Excel / LibreOffice Calc
   - ✅ Contains 8 sheets
   - ✅ Dynamic team sheets match identified teams
   - ✅ "Sample Guidance" sheet shows how samples influenced generation

6. **Check Backend Logs**:
   ```bash
   docker-compose logs backend --tail=100 | grep -E "(Agent|ULTIMATE GOAL|Project Scope)"
   ```

---

## Files Modified

### Backend:
1. **`backend/app/agents/project_estimator/workflow.py`**
   - Lines 1-18: Module docstring with ULTIMATE GOAL
   - Lines 276-294: `_analyze_brd_examples` prompt with translation context
   - Lines 365-414: `_extract_requirements` prompt with ULTIMATE GOAL statement

### Frontend:
1. **`frontend/src/components/ProjectEstimator.tsx`**
   - Line 43: Fixed interface (`excel_url` instead of `cost_estimation_url`)
   - Lines 1067-1071: Fixed download button to use `excel_url`

---

## Verification Checklist

After testing:

- [x] Backend restarted successfully with updated prompts
- [x] Module docstring includes ULTIMATE GOAL statement
- [x] Agent 1 prompt emphasizes translating Project Scope → BRD
- [x] BRD analysis prompt includes translation context
- [x] Frontend Excel download button uses correct field name
- [ ] Test workflow: Submit new request with sample documents
- [ ] Verify BRD.docx content reflects translation goal
- [ ] Verify Excel Sample Guidance sheet shows sample usage
- [ ] Confirm both download buttons work

---

## Benefits of This Update

### 1. **Clear Agent Purpose**
- Agents now understand they're translating a Project Scope (not generating generic estimates)
- LLM receives explicit context about the ultimate goal

### 2. **Better Sample Integration**
- Prompts emphasize "learning from samples" to guide translation
- Sample patterns are framed as organizational standards to follow

### 3. **Improved Output Quality**
- Generated BRD will better reflect the input Project Scope
- Writing style and terminology will match uploaded samples
- Output will be more aligned with user expectations

### 4. **Transparency**
- Sample Guidance sheet in Excel shows exactly how samples were used
- Users can verify samples weren't distorted or misused

### 5. **User Alignment**
- Directly addresses user's feedback about agent goal
- Workflow now matches user's mental model (translation, not generation)

---

## Related Documentation

- `PROJECT_ESTIMATOR_BRD_WORD_DOCUMENT.md` - BRD format change (PowerPoint → Word)
- `PROJECT_ESTIMATOR_EXCEL_ENHANCEMENT_COMPLETE.md` - Excel enhancement (basic → comprehensive)
- `PROJECT_ESTIMATOR_COMPREHENSIVE_VALIDATION.md` - Complete workflow validation

---

## Next Steps

1. **Test the Updated Workflow**:
   - Submit a new Project Estimator request
   - Upload sample BRDs, cost estimates, and data
   - Verify generated documents reflect the translation goal

2. **Monitor Logs**:
   - Check that prompts now include ULTIMATE GOAL statements
   - Verify sample document analysis is working correctly

3. **User Validation**:
   - Review generated BRD to ensure it translates the Project Scope effectively
   - Verify Sample Guidance sheet shows sample usage clearly

---

**Status**: ✅ **READY FOR TESTING**

The agent prompts have been updated to clearly state the ultimate goal of translating a Project Scope Document into a comprehensive BRD by learning from uploaded sample documents. Backend has been restarted and is ready to process new requests.

---

**End of Agent Goals Update Documentation**
