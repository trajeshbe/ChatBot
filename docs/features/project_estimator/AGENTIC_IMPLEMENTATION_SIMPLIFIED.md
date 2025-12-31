# Project Estimator: Simplified Agentic Implementation

**Date**: 2025-11-21
**Refinement**: Clarified scope - rates from UI config, tasks & estimates from LLM

---

## 🎯 Clarified Scope

### What's Fixed (From UI/Config)
- ✅ **Billing rates**: Planning rate, development rate, testing rate, etc. (from UI sliders)
- ✅ **Overhead percentages**: PM, BA, SA, Contingency (from UI config)
- ✅ **Infrastructure costs**: Base costs from config (can be overridden by LLM if needed)

### What's Dynamic (From LLM Agents)
- 🤖 **Engineering teams**: Which teams are needed for this project?
- 🤖 **Tasks**: What specific tasks does each team need to do?
- 🤖 **Effort estimates**: How many hours per task?
- 🤖 **Task categorization**: Which rate category does each task fall into?

---

## 🏗️ Simplified Agent Architecture

### Workflow (5 Agents)

```
User Input + UI Config
          ↓
    [1. Analyst Agent]
    Extract project requirements
          ↓
    [2. Team Planner Agent]
    Identify engineering teams
          ↓
    [3. Task Generator Agent]
    Generate tasks per team
          ↓
    [4. Rate Assignment Agent]
    Map tasks to rate categories
          ↓
    [5. Document Generator Agent]
    Create BRD + Excel with per-team sheets
          ↓
    Outputs (BRD.pptx + CostEstimate.xlsx)
```

---

## 🤖 Agent Implementations

### 1. Analyst Agent
**Input**: User prompt + uploaded examples
**Output**: Structured requirements

```python
analyst_prompt = f"""
Analyze this project request:

User Description: {user_prompt}

Extract and return JSON:
{{
  "project_goal": "Build web scraping solution...",
  "key_requirements": [
    "Extract data from 500 e-commerce sites",
    "Transform and load into database",
    "AI-powered categorization"
  ],
  "complexity": "high",
  "industry": "e-commerce",
  "timeline": "12 weeks"
}}
"""
```

---

### 2. Team Planner Agent
**Input**: Requirements
**Output**: Engineering teams needed

```python
team_planner_prompt = f"""
Based on these requirements, identify which engineering teams are needed:

Requirements: {requirements}

Available Teams:
- Scraping (web scraping, data extraction)
- Data Engineering (ETL, pipelines, transformation)
- AI/ML (model development, categorization)
- Integration (API integrations)
- DevOps (CI/CD, deployment)
- MLOps (model deployment, monitoring)
- UI/Frontend (dashboards, user interface)
- Backend (API development)
- Infrastructure (cloud setup, databases)
- QA (testing, validation)

For each needed team, specify:
- Team name
- Allocation % (10%, 50%, 100%)
- Primary responsibilities

Return JSON:
{{
  "teams": [
    {{
      "name": "Scraping",
      "allocation": 100,
      "responsibilities": [
        "Setup Playwright browser automation",
        "Implement scrapers for 500 e-commerce sites",
        "Handle rate limiting and proxies"
      ]
    }},
    {{
      "name": "Data Engineering",
      "allocation": 80,
      "responsibilities": [
        "Design ETL pipeline",
        "Transform scraped data",
        "Load into database"
      ]
    }},
    {{
      "name": "AI/ML",
      "allocation": 60,
      "responsibilities": [
        "Train product categorization model",
        "Deploy inference pipeline",
        "Monitor model performance"
      ]
    }}
  ]
}}
"""
```

---

### 3. Task Generator Agent
**Input**: Team plan
**Output**: Tasks per team with effort estimates

**Key Innovation**: Tasks and estimates are **project-specific**, not template-based.

```python
task_generator_prompt = f"""
Generate specific tasks for the {team_name} team:

Team: {team_name}
Responsibilities: {responsibilities}
Allocation: {allocation}%
Project Context: {project_goal}

Generate 5-10 actionable tasks with:
- Task number (hierarchical: 1, 1.1, 1.2)
- Specific task description (not generic)
- Effort estimate (hours)
- Complexity level (Easy, Medium, Hard)

Examples of GOOD task descriptions:
- "Implement Playwright scraper for Amazon product pages"
- "Setup PostgreSQL with pgvector extension for embeddings"
- "Train BERT model for product categorization on e-commerce dataset"

Examples of BAD (too generic) task descriptions:
- "Development work"
- "Setup infrastructure"
- "Testing"

Return JSON:
{{
  "team": "{team_name}",
  "tasks": [
    {{
      "task_number": "1",
      "task_name": "Setup Playwright browser automation with anti-detection",
      "effort_hours": 24,
      "complexity": "Medium",
      "rate_category": "development"
    }},
    {{
      "task_number": "1.1",
      "task_name": "Configure rotating proxies and user agent rotation",
      "effort_hours": 8,
      "complexity": "Easy",
      "rate_category": "development"
    }},
    {{
      "task_number": "2",
      "task_name": "Implement scrapers for 500 e-commerce sites",
      "effort_hours": 400,
      "complexity": "Hard",
      "rate_category": "scraping"
    }}
  ]
}}
"""
```

---

### 4. Rate Assignment Agent
**Input**: Tasks from each team + available rate categories from UI
**Output**: Tasks with assigned rate categories

**Purpose**: Map each task to the correct rate category from UI config.

**UI Rate Categories** (from config):
- `planning_rate`: $30/hr
- `development_rate`: $30/hr
- `testing_rate`: $26/hr
- `ui_development_rate`: $28/hr
- `scraping_development_rate`: $30/hr
- `solution_architect_rate`: $35/hr

```python
rate_assignment_prompt = f"""
Assign rate categories to these tasks:

Tasks: {tasks}

Available rate categories from UI config:
{json.dumps(rate_config.keys())}

For each task, determine which rate category fits best based on:
- Task description
- Complexity
- Skill level required

Return JSON with tasks updated to include "rate_category":
{{
  "tasks": [
    {{
      "task_number": "1",
      "task_name": "Setup Playwright browser automation",
      "effort_hours": 24,
      "complexity": "Medium",
      "rate_category": "development_rate"  ← Added by this agent
    }},
    {{
      "task_number": "2",
      "task_name": "Implement scrapers for 500 sites",
      "effort_hours": 400,
      "complexity": "Hard",
      "rate_category": "scraping_development_rate"  ← Added by this agent
    }},
    {{
      "task_number": "3",
      "task_name": "Write unit tests for scrapers",
      "effort_hours": 40,
      "complexity": "Medium",
      "rate_category": "testing_rate"  ← Added by this agent
    }}
  ]
}}
"""
```

---

### 5. Document Generator Agent
**Input**: All team tasks with rate assignments + UI config
**Output**: BRD.pptx + CostEstimate.xlsx

**Excel Structure**:
```
Sheet 1: Master Summary
  - Total cost: $45,000
  - By team breakdown
  - Infrastructure costs
  - BAU (if applicable)

Sheet 2: Scraping Team Tasks
  Task | Hours | Rate | Cost
  -------------------------
  1. Setup Playwright | 24 | $30 | $720
  2. Implement scrapers | 400 | $30 | $12,000
  ...

Sheet 3: Data Engineering Team Tasks
  Task | Hours | Rate | Cost
  -------------------------
  1. Design ETL pipeline | 40 | $30 | $1,200
  2. Implement transformations | 80 | $30 | $2,400
  ...

Sheet 4: AI/ML Team Tasks
Sheet 5: DevOps Team Tasks
... (one sheet per team)

Sheet N: Infrastructure
Sheet N+1: BAU Monthly Costs (if Full Service)
```

**Cost Calculation** (Simple):
```python
for task in all_tasks:
    rate_category = task["rate_category"]  # e.g., "development_rate"
    rate = rate_config[rate_category]      # e.g., $30/hr from UI
    cost = task["effort_hours"] * rate
```

---

## 📊 Example: E-Commerce Scraping Project

### Input
```json
{
  "project_scope": "Build web scraping solution to extract product data from 500 e-commerce sites, transform and load into database with AI-powered categorization",
  "rate_config": {
    "planning_rate": 30,
    "development_rate": 30,
    "testing_rate": 26,
    "scraping_development_rate": 30,
    "solution_architect_rate": 35
  },
  "overhead_config": {
    "project_manager_percentage": 10,
    "solution_architect_percentage": 5,
    "contingency_percentage": 10
  },
  "scenario": "baseline"
}
```

### Agent 1 Output (Analyst)
```json
{
  "project_goal": "Automated e-commerce data extraction system",
  "key_requirements": [
    "Scrape 500 e-commerce sites",
    "Handle dynamic content with Playwright",
    "Transform and normalize product data",
    "AI-powered product categorization",
    "Load into PostgreSQL database"
  ],
  "complexity": "high",
  "industry": "e-commerce",
  "timeline": "12 weeks"
}
```

### Agent 2 Output (Team Planner)
```json
{
  "teams": [
    {
      "name": "Scraping",
      "allocation": 100,
      "responsibilities": [
        "Playwright automation setup",
        "Scraper implementation for 500 sites",
        "Anti-detection mechanisms"
      ]
    },
    {
      "name": "Data Engineering",
      "allocation": 80,
      "responsibilities": [
        "ETL pipeline design",
        "Data transformation and normalization",
        "Database schema design"
      ]
    },
    {
      "name": "AI/ML",
      "allocation": 60,
      "responsibilities": [
        "Product categorization model",
        "Model training and evaluation",
        "Inference pipeline"
      ]
    },
    {
      "name": "DevOps",
      "allocation": 30,
      "responsibilities": [
        "CI/CD pipeline",
        "Deployment automation",
        "Monitoring setup"
      ]
    }
  ]
}
```

### Agent 3 Output (Task Generator) - Scraping Team
```json
{
  "team": "Scraping",
  "tasks": [
    {
      "task_number": "1",
      "task_name": "Setup Playwright browser automation framework",
      "effort_hours": 24,
      "complexity": "Medium"
    },
    {
      "task_number": "1.1",
      "task_name": "Configure rotating proxies and user agents",
      "effort_hours": 8,
      "complexity": "Easy"
    },
    {
      "task_number": "1.2",
      "task_name": "Implement rate limiting and retry logic",
      "effort_hours": 16,
      "complexity": "Medium"
    },
    {
      "task_number": "2",
      "task_name": "Develop scrapers for 500 e-commerce sites",
      "effort_hours": 400,
      "complexity": "Hard"
    },
    {
      "task_number": "2.1",
      "task_name": "Implement generic product page scraper",
      "effort_hours": 80,
      "complexity": "Medium"
    },
    {
      "task_number": "2.2",
      "task_name": "Customize scrapers for top 50 sites",
      "effort_hours": 200,
      "complexity": "Hard"
    },
    {
      "task_number": "2.3",
      "task_name": "Handle dynamic content and pagination",
      "effort_hours": 120,
      "complexity": "Hard"
    },
    {
      "task_number": "3",
      "task_name": "Implement error handling and logging",
      "effort_hours": 40,
      "complexity": "Medium"
    }
  ]
}
```

### Agent 4 Output (Rate Assignment) - Scraping Team
```json
{
  "team": "Scraping",
  "tasks": [
    {
      "task_number": "1",
      "task_name": "Setup Playwright browser automation framework",
      "effort_hours": 24,
      "complexity": "Medium",
      "rate_category": "scraping_development_rate"  ← Assigned
    },
    {
      "task_number": "1.1",
      "task_name": "Configure rotating proxies and user agents",
      "effort_hours": 8,
      "complexity": "Easy",
      "rate_category": "development_rate"
    },
    {
      "task_number": "2",
      "task_name": "Develop scrapers for 500 e-commerce sites",
      "effort_hours": 400,
      "complexity": "Hard",
      "rate_category": "scraping_development_rate"
    },
    {
      "task_number": "3",
      "task_name": "Implement error handling and logging",
      "effort_hours": 40,
      "complexity": "Medium",
      "rate_category": "development_rate"
    }
  ]
}
```

### Cost Calculation (Using UI Rates)
```
Scraping Team:
- Task 1: 24 hrs × $30 (scraping_development_rate) = $720
- Task 1.1: 8 hrs × $30 (development_rate) = $240
- Task 2: 400 hrs × $30 (scraping_development_rate) = $12,000
- Task 3: 40 hrs × $30 (development_rate) = $1,200
---
Scraping Team Subtotal: $14,160

Data Engineering Team: $8,000
AI/ML Team: $6,500
DevOps Team: $3,000
---
Total Development: $31,660

Overhead:
- PM (10%): $3,166
- SA (5%): $1,583
- Contingency (10%): $3,166
---
Total with Overhead: $39,575

Infrastructure (one-time): $1,000

GRAND TOTAL: $40,575
```

---

## 🔧 LangGraph Implementation (Simplified)

### State
```python
class ProjectEstimatorState(TypedDict):
    # Input
    user_prompt: str
    rate_config: Dict[str, float]  # From UI
    overhead_config: Dict[str, float]  # From UI
    scenario: str

    # Agent outputs
    requirements: Dict[str, Any]
    team_plan: Dict[str, List[Dict]]
    tasks_by_team: Dict[str, List[Dict]]
    costs_by_team: Dict[str, Dict]

    # Final outputs
    brd_path: str
    excel_path: str
```

### Workflow
```python
workflow = StateGraph(ProjectEstimatorState)

# Add agents
workflow.add_node("analyst", analyst_agent)
workflow.add_node("team_planner", team_planner_agent)
workflow.add_node("task_generator", task_generator_agent)
workflow.add_node("rate_assignment", rate_assignment_agent)
workflow.add_node("document_generator", document_generator_agent)

# Flow
workflow.set_entry_point("analyst")
workflow.add_edge("analyst", "team_planner")
workflow.add_edge("team_planner", "task_generator")
workflow.add_edge("task_generator", "rate_assignment")
workflow.add_edge("rate_assignment", "document_generator")
workflow.add_edge("document_generator", END)

graph = workflow.compile()
```

### Rate Assignment Agent (No Keyword Matching!)
```python
async def rate_assignment_agent(state: ProjectEstimatorState) -> ProjectEstimatorState:
    """Assign rate categories using LLM"""
    tasks_by_team = state["tasks_by_team"]
    rate_config = state["rate_config"]

    for team_name, tasks in tasks_by_team.items():
        prompt = f"""
        Assign rate categories to these tasks:

        Tasks: {json.dumps(tasks)}

        Available rate categories: {list(rate_config.keys())}

        For each task, choose the most appropriate rate category.
        Return JSON with "rate_category" added to each task.
        """

        response = await llm_service.generate(
            prompt=prompt,
            response_format={"type": "json_object"}
        )

        # Update tasks with rate categories
        tasks_by_team[team_name] = json.loads(response)["tasks"]

    state["tasks_by_team"] = tasks_by_team

    # Calculate costs (simple multiplication)
    costs_by_team = {}
    for team_name, tasks in tasks_by_team.items():
        team_cost = 0
        for task in tasks:
            rate = rate_config[task["rate_category"]]
            cost = task["effort_hours"] * rate
            task["cost"] = cost
            team_cost += cost

        costs_by_team[team_name] = {
            "tasks": tasks,
            "subtotal": team_cost
        }

    state["costs_by_team"] = costs_by_team
    return state
```

---

## ✨ Key Benefits of This Approach

### 1. **Best of Both Worlds**
- ✅ **Fixed rates** (from UI) = Predictable, user-controlled
- ✅ **Dynamic tasks** (from LLM) = Adaptive, project-specific

### 2. **No Keyword Matching**
- ❌ No `if 'planning' in category: return planning_rate`
- ✅ LLM decides which rate category applies to each task

### 3. **Project-Specific Tasks**
- Not generic "Development work"
- Specific: "Implement Playwright scraper for Amazon product pages"

### 4. **Per-Team Cost Sheets**
- Clear breakdown by engineering team
- Master rollup for total cost

### 5. **Leverages Existing Stack**
- LangGraph for agent orchestration
- LLM Service for decision-making
- Existing Excel/BRD generators for output

---

## 📂 File Structure

```
backend/app/agents/project_estimator/
├── __init__.py
├── workflow.py                  # Main LangGraph workflow
├── analyst_agent.py
├── team_planner_agent.py
├── task_generator_agent.py
├── rate_assignment_agent.py     # NEW: LLM-based rate assignment
└── document_generator_agent.py
```

---

## 🚀 Implementation Plan (3-5 Days)

### Day 1: Core Agents
- Implement Analyst Agent
- Implement Team Planner Agent
- Test agent prompts

### Day 2: Task Generation
- Implement Task Generator Agent
- Implement Rate Assignment Agent (LLM-based, not keywords)
- Test task generation quality

### Day 3: Excel Generator
- Enhance Excel service for per-team sheets
- Add master rollup logic
- Test with sample data

### Day 4: Integration
- Create API endpoint
- Integrate with LangGraph workflow
- Test end-to-end

### Day 5: Testing & Refinement
- Test with various project types
- Refine agent prompts
- Document usage

---

## Summary

**Simplified Approach**:
- **Rates**: From UI config (fixed per scenario) ← User controls
- **Tasks**: From LLM agents (dynamic) ← LLM adapts
- **Estimates**: From LLM agents (adaptive) ← LLM decides

**No More**:
- ❌ Hardcoded task categories
- ❌ Keyword matching for rates
- ❌ Fixed task templates

**Result**: A truly adaptive system where tasks and estimates are project-specific, while rates remain user-configurable via UI.
