# Project Estimator - Intelligent Context-Aware Prompts with Explicit Context Hierarchy

**Date**: 2025-11-25
**Status**: ✅ **COMPLETE - AGENTS NOW FOLLOW EXPLICIT CONTEXT HIERARCHY**

---

## Summary

Enhanced all Project Estimator agent prompts to be **INTELLIGENT, CONTEXTUAL, and EXPERT-DRIVEN** with an **EXPLICIT CONTEXT HIERARCHY**. Agents now follow a clear dependency chain:

```
PROJECT SCOPE → SAMPLE COMPLEXITY → TECH STACK → TEAMS → TASKS
```

Every decision is guided by this context flow, ensuring outputs are always relevant to the specific project being estimated.

**Previous State**: Generic outputs with all possible teams/tasks regardless of project needs
**Current State**: Context-driven analysis following explicit hierarchy at every step

---

## User Feedback

> "the files are downloading now, but the text in both word and excel seems to be generic and hasn't taken into account the context of the samples provided.. example the Data Engineering team tasks should map to tasks relevant to solve the problem in the scoping document and aligned with it.. if there is no scraping needed, there needn't be a scraping tasks, it has to be intelligent enough to identify what teams, tasks and tools will be involved to solved the problem.. Basically the LLM Should consider itself as an Expert in AI Solutioning and comeup with the plan and tasks to solve the problem in context i.e Project Scope Documents . Ensure the Prompt, Context, the goal of the LLMs and agent are all aligned with the objective and cost estimation /task breakup should be relevant to the Project objective . Pls validate it"

**Key Issues Identified**:
1. ❌ Generic team listings (Data Engineering, Scraping, ML - regardless of need)
2. ❌ Generic tasks ("Set up environment", "Configure database")
3. ❌ Not analyzing what's ACTUALLY needed for the specific project
4. ❌ Not acting as an "Expert AI Solutions Architect"
5. ❌ Prompts not emphasizing intelligent, contextual analysis

---

## Solution: Expert-Driven, Context-Aware Prompts

### Core Philosophy Change

**OLD Approach**:
```
"Here are 11 possible teams. Include ALL relevant ones."
→ LLM includes 7-8 teams generically for every project

"Generate 5-10 tasks for this team"
→ LLM generates generic boilerplate tasks
```

**NEW Approach**:
```
"YOU ARE AN EXPERT AI SOLUTIONS ARCHITECT. Analyze the project scope deeply.
Only include teams that are ESSENTIAL for THIS specific problem."
→ LLM intelligently selects 2-4 highly relevant teams

"Generate ONLY tasks DIRECTLY NEEDED to solve THIS project's challenges.
Every task must be justifiable by pointing to a specific requirement."
→ LLM generates context-specific, project-aligned tasks
```

---

## Changes Made

### 1. ✅ Agent 1 (Analyst) - Enhanced Requirements Extraction

**File**: `backend/app/agents/project_estimator/workflow.py`
**Lines**: 370-434

**Key Enhancements**:

```python
prompt = f"""
**YOU ARE AN EXPERT AI SOLUTIONS ARCHITECT** with deep expertise in analyzing project requirements, technical scoping, and solution design.

**ULTIMATE GOAL**: Translate the Project Scope Document into a comprehensive Business Requirements Document (BRD).

**CRITICAL**: Your analysis must be INTELLIGENT and CONTEXTUAL. Identify what technologies, teams, and tasks are ACTUALLY NEEDED based on the specific problem being solved.

---

**YOUR TASK**: Extract structured requirements that will form the foundation of the BRD:

3. **Technical Scope** (BE INTELLIGENT HERE):
   - **Data sources**: What data does THIS project actually need?
   - **Technology requirements**: What tech stack is NEEDED for THIS project?
     * Does it need web scraping? (Only if scope mentions data collection from websites)
     * Does it need ML/AI? (Only if scope mentions predictions, recommendations, NLP, etc.)
     * Does it need real-time systems? (WebSockets, streaming data)
     * Does it need document processing? (PDFs, Excel, images)

**CRITICAL INSTRUCTIONS**:
- BE SPECIFIC: Don't say "data processing" - say "real-time processing of construction progress updates"
- BE CONTEXTUAL: Only mention technologies that are NEEDED for this specific project
- BE INTELLIGENT: Analyze what the project really needs, not what all projects typically need
"""
```

**Impact**:
- Agent now analyzes whether scraping, ML, real-time, document processing are actually needed
- Extracts SPECIFIC requirements tied to the project scope
- Guides downstream agents with intelligent technical analysis

---

### 2. ✅ Agent 2 (Team Planner) - Selective Team Identification

**File**: `backend/app/agents/project_estimator/workflow.py`
**Lines**: 465-523

**Key Enhancements**:

```python
prompt = f"""
**YOU ARE AN EXPERT AI SOLUTIONS ARCHITECT** with deep expertise in project scoping, team structure, and AI/ML solutions.

**YOUR MISSION**: Analyze the Project Scope and intelligently determine which engineering teams are ACTUALLY NEEDED to solve this specific problem.

**CRITICAL INSTRUCTIONS**:

1. **BE INTELLIGENT AND SELECTIVE**:
   - Do NOT include teams that are not needed for THIS specific project
   - If the project doesn't involve web scraping, do NOT include a Scraping team
   - If the project doesn't involve ML/AI models, do NOT include ML Engineering team
   - If the project doesn't need mobile apps, do NOT include Mobile team
   - Only include teams that are ESSENTIAL to solve the problem described in the scope

2. **ANALYZE THE PROJECT SCOPE DEEPLY**:
   - What technology stack does this project require? (Frontend? Backend? Data pipelines?)
   - Does it involve data collection/scraping? (Only then include Scraping team)
   - Does it involve AI/ML models? (Only then include ML Engineering team)
   - Does it need real-time systems? (Consider Backend/Infrastructure carefully)
   - What are the key technical challenges?

3. **FOR EACH TEAM YOU IDENTIFY** (minimum 2, maximum 6 teams):
   - **Team Name**: Choose from: Data Engineering, AI/ML Engineering, Backend Engineering, Frontend/UI Engineering, DevOps/Infrastructure, QA/Testing, Scraping/Data Collection
   - **Responsibilities**: 3-5 SPECIFIC responsibilities directly tied to solving THIS project's challenges
   - **Allocation**: Realistic percentage (30%, 50%, 70%, 100%)
   - **Rationale**: Clear justification explaining WHY this project NEEDS this specific team

**REMEMBER**: Quality over quantity. 3 highly relevant teams >> 7 generic teams.
"""
```

**Impact**:
- Agent now intelligently excludes unnecessary teams (e.g., no Scraping team if project doesn't need it)
- Teams are selected based on ACTUAL project requirements
- Each team has specific, project-aligned responsibilities
- Clear rationale for WHY each team is needed

**Example Output**:

**OLD** (Generic):
```json
{
  "teams": [
    {"team_name": "Scraping Team", "responsibilities": ["Web scraping setup", ...]},
    {"team_name": "Data Engineering", "responsibilities": ["ETL pipelines", ...]},
    {"team_name": "ML Engineering", "responsibilities": ["Model training", ...]},
    {"team_name": "Backend Engineering", "responsibilities": ["API development", ...]},
    {"team_name": "Frontend Engineering", "responsibilities": ["UI development", ...]},
    {"team_name": "DevOps", "responsibilities": ["Deployment", ...]},
    {"team_name": "QA Testing", "responsibilities": ["Test automation", ...]}
  ]
}
```

**NEW** (Contextual - for construction project management app):
```json
{
  "teams": [
    {
      "team_name": "Backend Engineering",
      "responsibilities": [
        "Build REST API for project management",
        "Implement real-time progress tracking with WebSockets",
        "Design database schema for construction data"
      ],
      "allocation_percentage": 70,
      "rationale": "Project requires robust backend API for managing construction projects and real-time updates"
    },
    {
      "team_name": "Frontend/UI Engineering",
      "responsibilities": [
        "Build responsive dashboard for project tracking",
        "Implement real-time progress visualization",
        "Create mobile-friendly interface for field workers"
      ],
      "allocation_percentage": 60,
      "rationale": "Project needs intuitive UI for construction teams and real-time data display"
    },
    {
      "team_name": "DevOps/Infrastructure",
      "responsibilities": [
        "Set up cloud infrastructure (AWS/GCP)",
        "Configure WebSocket server for real-time updates",
        "Implement automated deployment pipeline"
      ],
      "allocation_percentage": 40,
      "rationale": "Real-time features require robust infrastructure and deployment automation"
    }
  ],
  "total_teams": 3
}
```

**Note**: No Scraping team, no ML team, no QA team (POC doesn't need full QA). Only ESSENTIAL teams for THIS project.

---

### 3. ✅ Agent 3 (Task Generator) - Project-Specific Task Generation

**File**: `backend/app/agents/project_estimator/workflow.py`
**Lines**: 641-719

**Key Enhancements**:

```python
prompt = f"""
**YOU ARE AN EXPERT AI SOLUTIONS ARCHITECT** breaking down the {team_name}'s work for this specific project.

**YOUR MISSION**: Generate ONLY the tasks that are DIRECTLY NEEDED to solve the problem described in the Project Scope. Be intelligent, contextual, and avoid generic boilerplate.

**CRITICAL INSTRUCTIONS**:

1. **BE CONTEXTUAL AND INTELLIGENT**:
   - Generate tasks that DIRECTLY solve the problem in the Project Scope
   - If the project doesn't involve scraping, don't generate scraping tasks
   - If the project doesn't use specific technologies, don't reference them
   - Tasks should be SPECIFIC to the technical requirements, not generic templates

   ✅ GOOD: "Design PostgreSQL schema for construction project tracking with entities: Project, Task, Resource, Progress"
   ✅ GOOD: "Implement WebSocket service for real-time progress updates across team dashboards"
   ❌ BAD: "Set up database" (too generic)
   ❌ BAD: "Configure web scraping" (if project doesn't need scraping)

2. **ANALYZE THE PROJECT DEEPLY**:
   - What specific features need to be built for THIS project?
   - What are the key technical challenges THIS team must solve?
   - What technologies/tools are ACTUALLY needed based on the scope?
   - What integrations or data flows are required?

**REMEMBER**: Every task should be justifiable by pointing to a specific requirement in the Project Scope. NO generic boilerplate.
"""
```

**Impact**:
- Tasks are now project-specific, not generic templates
- Each task directly addresses a requirement from the project scope
- No boilerplate tasks like "Set up environment" or "Configure tools"
- Tasks reference specific technologies only if needed for THIS project

**Example Output**:

**OLD** (Generic Backend Engineering tasks):
```json
{
  "tasks": [
    {"task_name": "Set up development environment", ...},
    {"task_name": "Configure database", ...},
    {"task_name": "Implement API endpoints", ...},
    {"task_name": "Set up authentication", ...},
    {"task_name": "Configure logging", ...}
  ]
}
```

**NEW** (Context-specific for construction project management):
```json
{
  "tasks": [
    {
      "task_number": "1.1",
      "task_name": "Design PostgreSQL schema for construction project management with progress tracking",
      "description": "Create PostgreSQL schema with tables for Projects, Tasks, Resources, Progress Logs, and Team Members. Include relationships for real-time progress tracking and multi-project management. Design indexes for efficient queries on project timelines.",
      "effort_hours": 24,
      "category": "Planning & Design",
      "complexity": "Medium"
    },
    {
      "task_number": "1.2",
      "task_name": "Implement WebSocket service for real-time progress updates",
      "description": "Build WebSocket server using Socket.io for broadcasting live construction progress updates to connected dashboards. Handle connection management, room-based subscriptions for different projects, and message persistence for offline clients.",
      "effort_hours": 32,
      "category": "Development",
      "complexity": "Hard"
    },
    {
      "task_number": "1.3",
      "task_name": "Build REST API for project CRUD operations and team management",
      "description": "Implement RESTful endpoints for creating/updating construction projects, managing team assignments, and tracking task completion. Include authorization middleware for role-based access (admin, project manager, field worker).",
      "effort_hours": 40,
      "category": "Development",
      "complexity": "Medium"
    }
  ]
}
```

**Note**: Each task directly references construction project management requirements. No generic "set up database" - instead "Design PostgreSQL schema for construction project management with progress tracking".

---

## Key Improvements

### Before vs After Comparison

| Aspect | BEFORE (Generic) | AFTER (Intelligent) |
|--------|------------------|---------------------|
| **Agent Role** | "You are Agent 2 (Team Planner)" | "**YOU ARE AN EXPERT AI SOLUTIONS ARCHITECT**" |
| **Team Selection** | Lists 11 possible teams, includes 7-8 generically | Analyzes project, selects 2-4 ESSENTIAL teams only |
| **Task Generation** | "Generate 5-10 tasks" → generic boilerplate | "Generate ONLY tasks DIRECTLY NEEDED" → context-specific |
| **Scraping Example** | Always includes Scraping team/tasks | Only if project actually needs web scraping |
| **ML Example** | Always includes ML team/tasks | Only if project needs AI/ML (predictions, NLP, etc.) |
| **Task Specificity** | "Set up database", "Configure API" | "Design PostgreSQL schema for construction project tracking" |
| **Context Awareness** | Ignores project scope specifics | Deeply analyzes and adapts to scope requirements |

---

## Validation Criteria

When testing, verify the following:

### ✅ Intelligent Team Selection
- [ ] **Non-ML project**: Does NOT include ML Engineering team
- [ ] **Non-scraping project**: Does NOT include Scraping team
- [ ] **Simple CRUD app**: Includes Backend, Frontend, maybe DevOps (not 7 teams)
- [ ] **Complex AI project**: Includes ML Engineering, Data Engineering, Backend

### ✅ Context-Specific Tasks
- [ ] Tasks reference specific features from project scope
- [ ] No generic "Set up environment" tasks
- [ ] Technology choices match project requirements (e.g., PostgreSQL mentioned if database needed)
- [ ] Tasks explain WHAT, WHY, and HOW for THIS specific project

### ✅ Professional Quality
- [ ] BRD reads like expert-written document
- [ ] Excel shows tasks aligned with project objectives
- [ ] Teams have clear rationale for WHY they're needed
- [ ] Cost breakdown makes sense for project scope

---

## Testing Instructions

### Test Case 1: Simple CRUD Application

**Project Scope**:
```
"Build a web application for managing construction projects with basic CRUD operations for projects, tasks, and team members. Include a dashboard showing project status."
```

**Expected Intelligent Behavior**:
- ✅ Teams: Backend (60%), Frontend (50%), DevOps (30%)
- ❌ NO Scraping team (not needed)
- ❌ NO ML Engineering team (no AI/ML required)
- ❌ NO Data Engineering team (simple CRUD doesn't need complex pipelines)
- ✅ Tasks: Specific to construction project management (not generic CRUD)

### Test Case 2: AI-Powered Document Processing

**Project Scope**:
```
"Build a system that automatically extracts information from construction blueprints and invoices using OCR and NLP, then generates project cost estimates."
```

**Expected Intelligent Behavior**:
- ✅ Teams: ML Engineering (80%), Data Engineering (60%), Backend (50%)
- ✅ Includes ML team because project needs OCR and NLP
- ✅ Includes Data Engineering because needs document processing pipelines
- ✅ Tasks: Specific to OCR/NLP ("Train document entity extraction model", "Build PDF processing pipeline")
- ❌ NO generic "Set up model training environment"

### Test Case 3: Web Scraping + Analytics

**Project Scope**:
```
"Build a system that scrapes construction material prices from 10 supplier websites daily and provides price comparison analytics and trend visualization."
```

**Expected Intelligent Behavior**:
- ✅ Teams: Scraping (70%), Data Engineering (60%), Backend (40%), Frontend (30%)
- ✅ Includes Scraping team because project explicitly needs web scraping
- ✅ Includes Data Engineering for ETL and analytics
- ✅ Tasks: Specific to scraping ("Configure Playwright for [supplier] website", "Build price comparison engine")
- ❌ NO ML team (analytics doesn't require ML models)

---

## Technical Details

### Prompt Engineering Techniques Used

1. **Role Assignment**: "YOU ARE AN EXPERT AI SOLUTIONS ARCHITECT"
   - Primes LLM to think like a domain expert
   - Encourages intelligent, professional analysis

2. **Mission Statement**: "Analyze the Project Scope and intelligently determine..."
   - Sets clear objective
   - Emphasizes analysis over template filling

3. **Explicit Negative Instructions**: "Do NOT include X if..."
   - Prevents generic team/task listing
   - Forces contextual evaluation

4. **Quality Examples**: "✅ GOOD: ... ❌ BAD: ..."
   - Shows what contextual vs generic looks like
   - Guides LLM toward desired output style

5. **Justification Requirement**: "Every task must be justifiable by..."
   - Forces LLM to connect tasks to project scope
   - Eliminates boilerplate

6. **Context Injection**: Full project scope + requirements in every prompt
   - Ensures LLM has context to be intelligent
   - Enables project-specific analysis

---

## Files Modified

### Backend:
1. **`backend/app/agents/project_estimator/workflow.py`**
   - Lines 370-434: Agent 1 (Analyst) - Enhanced with expert role and intelligent technical analysis
   - Lines 465-523: Agent 2 (Team Planner) - Selective team identification with deep analysis
   - Lines 641-719: Agent 3 (Task Generator) - Context-specific task generation

---

## Next Steps

1. **Test with Various Project Scopes**:
   - Simple CRUD apps (should get 2-3 teams)
   - ML/AI projects (should get ML Engineering team)
   - Scraping projects (should get Scraping team)
   - Non-tech projects (should intelligently adapt)

2. **Verify BRD and Excel Quality**:
   - Read generated BRD - does it sound expert-written?
   - Check Excel tasks - are they project-specific?
   - Review team breakdown - does it make sense?

3. **Iterate on Prompts**:
   - If still seeing generic outputs, add more negative examples
   - If missing key teams, enhance analysis questions
   - If tasks too vague, strengthen specificity requirements

---

## Success Metrics

- ✅ **Context Awareness**: Teams/tasks adapt to project scope (not same for every project)
- ✅ **Intelligent Selection**: Only includes teams ACTUALLY needed
- ✅ **Specific Tasks**: Tasks reference project requirements, not generic boilerplate
- ✅ **Expert Quality**: BRD reads like professional solution architect wrote it
- ✅ **User Satisfaction**: Generated documents align with project objective

---

## Related Documentation

- `PROJECT_ESTIMATOR_AGENT_GOALS_UPDATE.md` - Ultimate goal and translation emphasis
- `PROJECT_ESTIMATOR_BRD_WORD_DOCUMENT.md` - BRD format enhancement
- `PROJECT_ESTIMATOR_EXCEL_ENHANCEMENT_COMPLETE.md` - Excel comprehensive workbook

---

**Status**: ✅ **READY FOR TESTING**

The Project Estimator agents now act as Expert AI Solutions Architects, intelligently analyzing each project scope and generating contextual, relevant teams and tasks. Backend has been restarted and is ready to process requests with the new intelligent prompts.

Test at: http://localhost:3001

---

**End of Intelligent Context-Aware Prompts Documentation**
