# Project Estimator: Agentic Workflow Design using LangGraph

**Date**: 2025-11-21
**Approach**: Agentic AI system leveraging existing LangGraph + LLM infrastructure
**Philosophy**: "Keep the brain in LLM" - Let agents make all decisions

---

## 🎯 Vision: Intelligent Multi-Agent Cost Estimator

### Core Concept
Instead of hardcoded rules, use **specialized AI agents** that collaborate to understand the project, identify needs, and generate accurate estimates.

**Key Innovation**: Each agent is an expert in its domain, agents communicate via LangGraph state machine, and the system learns from uploaded examples.

---

## 🏗️ Agentic Architecture

### Agent Workflow (LangGraph State Machine)

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER INPUT                                   │
│  • Project description prompt                                    │
│  • Uploaded example files (BRDs, cost estimates)                │
│  • Sample data files                                             │
│  • UI configuration (rates, scenario)                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   1. ANALYST AGENT         │
        │   Goal: Extract Intent     │
        │   • Parse user prompt      │
        │   • Analyze examples       │
        │   • Extract requirements   │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   2. CLASSIFIER AGENT      │
        │   Goal: Project Type       │
        │   • Determine: POC/Staff   │
        │     Aug/Full Service       │
        │   • Identify industry      │
        │   • Assess complexity      │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   3. TEAM PLANNER AGENT    │
        │   Goal: Engineering Teams  │
        │   • Scraping team?         │
        │   • Data engineering?      │
        │   • AI/ML engineers?       │
        │   • DevOps/MLOps?          │
        │   • UI/Frontend?           │
        │   • Infrastructure?        │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   4. TASK GENERATOR AGENT  │
        │   Goal: Tasks per Team     │
        │   • Generate task list     │
        │   • Estimate effort        │
        │   • Assign complexity      │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   5. COST ESTIMATOR AGENT  │
        │   Goal: Per-Team Costs     │
        │   • Apply rates            │
        │   • Calculate totals       │
        │   • Add overhead           │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   6. CONSOLIDATOR AGENT    │
        │   Goal: Master Rollup      │
        │   • Aggregate all teams    │
        │   • Add infrastructure     │
        │   • Calculate BAU (if needed)│
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   7. DOCUMENT AGENT        │
        │   Goal: Generate Outputs   │
        │   • Create BRD (PPTX)      │
        │   • Create Cost Sheet (XLS)│
        │   • Per-team sheets        │
        │   • Master rollup sheet    │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   OUTPUTS                  │
        │   • BRD.pptx               │
        │   • CostEstimate.xlsx      │
        │     - Master Sheet         │
        │     - Scraping Team        │
        │     - Data Engineering     │
        │     - AI/ML Team           │
        │     - DevOps/MLOps         │
        │     - UI Team              │
        │     - Infrastructure       │
        │     - BAU (if applicable)  │
        └────────────────────────────┘
```

---

## 🤖 Agent Definitions

### 1. Analyst Agent
**Role**: Project requirements analyst
**Input**: User prompt + uploaded example files
**Output**: Structured project requirements

**Capabilities**:
- Parse natural language project descriptions
- Analyze uploaded BRD examples using embeddings
- Extract key requirements from sample cost estimates
- Identify project goals and constraints

**Tools**:
- `EmbeddingService` - Semantic analysis of examples
- `TemplateParserService` - Extract patterns from samples
- LLM - Natural language understanding

**Decision Making**:
```python
analyst_prompt = """
Analyze this project request and extract structured requirements:

User Prompt: {user_prompt}

Uploaded Examples: {example_summaries}

Return JSON:
{
  "project_goal": "...",
  "key_requirements": [...],
  "estimated_complexity": "low|medium|high",
  "industry": "...",
  "timeline_constraint": "..."
}
"""
```

---

### 2. Classifier Agent
**Role**: Project type classifier
**Input**: Analyst output
**Output**: Project classification

**Capabilities**:
- Classify as POC, Staff Augmentation, or Full Service
- Determine if BAU is needed
- Assess project duration (weeks)
- Identify risk level

**Decision Logic (LLM-Driven)**:
```python
classifier_prompt = """
Based on these requirements, classify the project:

Requirements: {requirements}

Consider:
- Is this a proof-of-concept or production system?
- Will ongoing support be needed?
- Is this resource augmentation or end-to-end delivery?

Return JSON:
{
  "project_type": "POC|Staff Augmentation|Full Service",
  "needs_bau": true|false,
  "estimated_duration_weeks": 8,
  "risk_level": "low|medium|high",
  "justification": "..."
}
"""
```

---

### 3. Team Planner Agent
**Role**: Engineering team identifier
**Input**: Project classification + requirements
**Output**: List of required engineering teams

**Capabilities**:
- Identify which engineering teams are needed
- Determine team sizes
- Suggest skill levels
- Estimate allocation percentages

**Engineering Team Types**:
1. **Scraping Team** - Web scraping, data extraction
2. **Data Engineering Team** - ETL, data pipelines, transformation
3. **AI/ML Team** - Model development, training, inference
4. **Integration Team** - API integrations, system connections
5. **DevOps Team** - CI/CD, deployment, monitoring
6. **MLOps Team** - Model deployment, monitoring, retraining
7. **UI/Frontend Team** - User interface, dashboards
8. **Backend Team** - API development, business logic
9. **Infrastructure Team** - Cloud setup, databases, networking
10. **QA Team** - Testing, quality assurance

**Decision Logic**:
```python
team_planner_prompt = """
Determine which engineering teams are needed for this project:

Project Type: {project_type}
Requirements: {requirements}
Project Goal: {goal}

Available Teams:
- Scraping (web scraping, data extraction)
- Data Engineering (ETL, pipelines)
- AI/ML (model development)
- Integration (API integrations)
- DevOps (CI/CD, deployment)
- MLOps (model operations)
- UI/Frontend (user interfaces)
- Backend (APIs, business logic)
- Infrastructure (cloud, databases)
- QA (testing)

For each needed team, specify:
- Team name
- Allocation % (10%, 50%, 100%)
- Skill level (Junior, Mid, Senior)
- Primary responsibilities

Return JSON:
{
  "teams": [
    {
      "team_name": "Scraping",
      "allocation_percentage": 100,
      "skill_level": "Senior",
      "responsibilities": ["Web scraping", "Data extraction"],
      "justification": "Project requires extracting data from 500 sources"
    },
    ...
  ]
}
"""
```

---

### 4. Task Generator Agent
**Role**: Task breakdown specialist
**Input**: Team plan + project requirements
**Output**: Tasks per team with effort estimates

**Capabilities**:
- Generate task lists for each team
- Estimate effort in hours
- Assign complexity levels
- Create hierarchical numbering (1, 1.1, 1.2, etc.)

**Per-Team Task Generation**:
```python
task_generator_prompt = """
Generate tasks for the {team_name} team:

Team Responsibilities: {responsibilities}
Team Allocation: {allocation}%
Project Type: {project_type}
Project Goal: {goal}

Generate 5-10 specific tasks for this team with:
- Task number (hierarchical: 1, 1.1, 1.2)
- Task description
- Effort estimate (hours)
- Complexity (Easy, Medium, Hard)

Return JSON:
{
  "team": "{team_name}",
  "tasks": [
    {
      "task_number": "1",
      "task_name": "Setup scraping infrastructure",
      "effort_hours": 24,
      "complexity": "Medium"
    },
    {
      "task_number": "1.1",
      "task_name": "Configure Playwright browser automation",
      "effort_hours": 8,
      "complexity": "Easy"
    },
    ...
  ]
}
"""
```

---

### 5. Cost Estimator Agent
**Role**: Financial analyst
**Input**: Tasks per team + rate configuration
**Output**: Cost breakdown per team

**Capabilities**:
- Apply billing rates to tasks
- Calculate team-level costs
- Add overhead (PM, BA, Contingency)
- Compute infrastructure costs

**Cost Calculation Logic**:
```python
cost_estimator_prompt = """
Calculate costs for {team_name}:

Tasks: {tasks}
Rate Configuration: {rates}
Overhead Percentages: {overhead}

For each task, determine the appropriate billing rate based on:
- Task complexity
- Skill level required
- Team type

Available rates:
{rate_options}

Return JSON:
{
  "team": "{team_name}",
  "task_costs": [
    {
      "task_number": "1",
      "effort_hours": 24,
      "rate": 30,
      "cost": 720
    },
    ...
  ],
  "team_subtotal": 5000,
  "overhead": {
    "project_manager": 500,
    "business_analyst": 250,
    "contingency": 575
  },
  "team_total": 6325
}
"""
```

---

### 6. Consolidator Agent
**Role**: Master aggregator
**Input**: All team cost sheets + infrastructure estimates
**Output**: Master consolidated cost sheet

**Capabilities**:
- Aggregate all team costs
- Add infrastructure (one-time + recurring)
- Calculate BAU if applicable
- Generate summary statistics

**Consolidation Logic**:
```python
consolidator_prompt = """
Consolidate all team costs into master sheet:

Team Costs: {all_team_costs}
Project Type: {project_type}
Infrastructure Needs: {infrastructure_needs}

Calculate:
1. Total development cost (all teams)
2. Infrastructure one-time cost
3. Monthly BAU cost (if {needs_bau})
4. Grand total

Also estimate infrastructure based on:
- Project scale: {project_scale}
- Cloud provider: {cloud_provider}
- Database needs: {database_needs}

Return JSON:
{
  "summary": {
    "total_development_hours": 500,
    "total_development_cost": 25000,
    "infrastructure_one_time": 1000,
    "monthly_bau": 1030,
    "grand_total_one_time": 26000
  },
  "by_team": {
    "Scraping": 8000,
    "Data Engineering": 5000,
    ...
  },
  "infrastructure_breakdown": [
    {"item": "Virtual Machines", "cost": 430},
    {"item": "Database", "cost": 200},
    ...
  ],
  "bau_breakdown": [
    {"item": "VM Hosting", "monthly_cost": 170},
    {"item": "Token Costs", "monthly_cost": 110},
    ...
  ]
}
"""
```

---

### 7. Document Generator Agent
**Role**: Output generator
**Input**: All agent outputs
**Output**: BRD (PPTX) + Cost Estimate (XLSX)

**Capabilities**:
- Generate PowerPoint BRD
- Create multi-sheet Excel workbook
- Format professional documents
- Add charts and visualizations

**Excel Structure**:
```
Sheet 1: Master Summary
  - Project overview
  - Total costs
  - Team breakdown

Sheet 2: Scraping Team
  - Task list
  - Hours and costs
  - Subtotal

Sheet 3: Data Engineering Team
  - Task list
  - Hours and costs
  - Subtotal

Sheet 4: AI/ML Team
  - Task list
  - Hours and costs
  - Subtotal

... (one sheet per team)

Sheet N: Infrastructure
  - One-time costs
  - Monthly recurring (if applicable)

Sheet N+1: BAU Monthly Costs (if Full Service)
  - Infrastructure hosting
  - Token costs
  - Support hours
```

---

## 🔧 LangGraph Implementation

### State Definition
```python
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END

class ProjectEstimatorState(TypedDict):
    # Input
    user_prompt: str
    uploaded_files: List[str]
    rate_config: Dict[str, Any]
    scenario: str

    # Analyst Agent Output
    requirements: Dict[str, Any]

    # Classifier Agent Output
    project_classification: Dict[str, Any]

    # Team Planner Output
    team_plan: Dict[str, Any]

    # Task Generator Output
    tasks_by_team: Dict[str, List[Dict[str, Any]]]

    # Cost Estimator Output
    costs_by_team: Dict[str, Dict[str, Any]]

    # Consolidator Output
    master_cost_sheet: Dict[str, Any]

    # Document Generator Output
    brd_path: str
    excel_path: str

    # Metadata
    errors: List[str]
    processing_time: float
```

### Workflow Graph
```python
from app.services.llm_service import LLMService

class ProjectEstimatorWorkflow:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(ProjectEstimatorState)

        # Add nodes (agents)
        workflow.add_node("analyst", self.analyst_agent)
        workflow.add_node("classifier", self.classifier_agent)
        workflow.add_node("team_planner", self.team_planner_agent)
        workflow.add_node("task_generator", self.task_generator_agent)
        workflow.add_node("cost_estimator", self.cost_estimator_agent)
        workflow.add_node("consolidator", self.consolidator_agent)
        workflow.add_node("document_generator", self.document_generator_agent)

        # Define edges (flow)
        workflow.set_entry_point("analyst")
        workflow.add_edge("analyst", "classifier")
        workflow.add_edge("classifier", "team_planner")
        workflow.add_edge("team_planner", "task_generator")
        workflow.add_edge("task_generator", "cost_estimator")
        workflow.add_edge("cost_estimator", "consolidator")
        workflow.add_edge("consolidator", "document_generator")
        workflow.add_edge("document_generator", END)

        return workflow.compile()

    async def analyst_agent(self, state: ProjectEstimatorState) -> ProjectEstimatorState:
        """Analyze project requirements from user input"""
        prompt = f"""
        Analyze this project request and extract requirements:

        User Prompt: {state['user_prompt']}

        Return structured requirements as JSON.
        """

        response = await self.llm_service.generate(
            prompt=prompt,
            response_format={"type": "json_object"}
        )

        state["requirements"] = json.loads(response)
        return state

    async def classifier_agent(self, state: ProjectEstimatorState) -> ProjectEstimatorState:
        """Classify project type"""
        requirements = state["requirements"]

        prompt = f"""
        Classify this project:

        Requirements: {json.dumps(requirements)}

        Determine:
        - Project type (POC, Staff Augmentation, Full Service)
        - Needs BAU?
        - Duration
        - Risk level

        Return JSON.
        """

        response = await self.llm_service.generate(
            prompt=prompt,
            response_format={"type": "json_object"}
        )

        state["project_classification"] = json.loads(response)
        return state

    async def team_planner_agent(self, state: ProjectEstimatorState) -> ProjectEstimatorState:
        """Identify required engineering teams"""
        requirements = state["requirements"]
        classification = state["project_classification"]

        prompt = f"""
        Determine engineering teams needed:

        Project Type: {classification['project_type']}
        Requirements: {json.dumps(requirements)}

        Available teams: Scraping, Data Engineering, AI/ML, Integration,
                        DevOps, MLOps, UI/Frontend, Backend, Infrastructure, QA

        For each team needed, specify allocation % and responsibilities.
        Return JSON.
        """

        response = await self.llm_service.generate(
            prompt=prompt,
            response_format={"type": "json_object"}
        )

        state["team_plan"] = json.loads(response)
        return state

    async def task_generator_agent(self, state: ProjectEstimatorState) -> ProjectEstimatorState:
        """Generate tasks for each team"""
        team_plan = state["team_plan"]
        requirements = state["requirements"]

        tasks_by_team = {}

        for team in team_plan["teams"]:
            prompt = f"""
            Generate tasks for {team['team_name']} team:

            Responsibilities: {team['responsibilities']}
            Allocation: {team['allocation_percentage']}%
            Project Goal: {requirements['project_goal']}

            Generate 5-10 tasks with effort estimates.
            Return JSON.
            """

            response = await self.llm_service.generate(
                prompt=prompt,
                response_format={"type": "json_object"}
            )

            tasks_by_team[team['team_name']] = json.loads(response)["tasks"]

        state["tasks_by_team"] = tasks_by_team
        return state

    async def cost_estimator_agent(self, state: ProjectEstimatorState) -> ProjectEstimatorState:
        """Calculate costs per team"""
        tasks_by_team = state["tasks_by_team"]
        rate_config = state["rate_config"]

        costs_by_team = {}

        for team_name, tasks in tasks_by_team.items():
            prompt = f"""
            Calculate costs for {team_name}:

            Tasks: {json.dumps(tasks)}
            Available rates: {json.dumps(rate_config)}

            Assign appropriate rate to each task and calculate total.
            Return JSON.
            """

            response = await self.llm_service.generate(
                prompt=prompt,
                response_format={"type": "json_object"}
            )

            costs_by_team[team_name] = json.loads(response)

        state["costs_by_team"] = costs_by_team
        return state

    async def consolidator_agent(self, state: ProjectEstimatorState) -> ProjectEstimatorState:
        """Consolidate all costs into master sheet"""
        costs_by_team = state["costs_by_team"]
        classification = state["project_classification"]

        prompt = f"""
        Consolidate all team costs:

        Team Costs: {json.dumps(costs_by_team)}
        Project Type: {classification['project_type']}
        Needs BAU: {classification['needs_bau']}

        Calculate:
        - Total development cost
        - Infrastructure costs
        - BAU costs (if applicable)

        Return JSON with master summary.
        """

        response = await self.llm_service.generate(
            prompt=prompt,
            response_format={"type": "json_object"}
        )

        state["master_cost_sheet"] = json.loads(response)
        return state

    async def document_generator_agent(self, state: ProjectEstimatorState) -> ProjectEstimatorState:
        """Generate BRD and Excel outputs"""
        # Use existing services
        from app.services.project_estimator.brd_generation_service import BRDGenerationService
        from app.services.project_estimator.excel_generation_service import ExcelGenerationService

        brd_service = BRDGenerationService(self.llm_service)
        excel_service = ExcelGenerationService()

        # Generate BRD
        brd_content = await brd_service.generate_brd_content(
            project_info=state["requirements"],
            scope_details=state["requirements"],
            project_type=state["project_classification"]["project_type"]
        )

        brd_path = f"/tmp/brd_{state['requirements']['project_name']}.pptx"
        brd_service.create_powerpoint(brd_content, brd_path)

        # Generate Excel with per-team sheets
        excel_path = f"/tmp/cost_{state['requirements']['project_name']}.xlsx"
        self._generate_multi_team_excel(
            excel_service,
            state["tasks_by_team"],
            state["costs_by_team"],
            state["master_cost_sheet"],
            excel_path
        )

        state["brd_path"] = brd_path
        state["excel_path"] = excel_path

        return state

    def _generate_multi_team_excel(self, excel_service, tasks_by_team, costs_by_team,
                                   master_sheet, output_path):
        """Generate Excel with one sheet per team + master sheet"""
        from openpyxl import Workbook

        wb = Workbook()

        # Sheet 1: Master Summary
        self._create_master_summary_sheet(wb, master_sheet)

        # Sheets 2+: One per team
        for team_name, tasks in tasks_by_team.items():
            team_costs = costs_by_team[team_name]
            self._create_team_sheet(wb, team_name, tasks, team_costs)

        # Save
        wb.save(output_path)

    async def run(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Run the complete workflow"""
        initial_state = {
            "user_prompt": user_input["project_scope"],
            "uploaded_files": user_input.get("uploaded_files", []),
            "rate_config": user_input["rate_config"],
            "scenario": user_input["scenario"],
            "errors": [],
            "processing_time": 0
        }

        result = await self.graph.ainvoke(initial_state)

        return {
            "brd_path": result["brd_path"],
            "excel_path": result["excel_path"],
            "master_summary": result["master_cost_sheet"],
            "project_classification": result["project_classification"],
            "team_plan": result["team_plan"]
        }
```

---

## 📊 Excel Output Structure (Per-Team Sheets)

### Sheet 1: Master Summary
```
┌────────────────────────────────────────────────┐
│ PROJECT: Data Extraction Solution              │
│ TYPE: Full Service                             │
│ SCENARIO: Baseline                             │
├────────────────────────────────────────────────┤
│                                                 │
│ COST SUMMARY                                   │
│ ────────────                                   │
│ Total Development:        $45,000              │
│ Infrastructure One-Time:  $1,000               │
│ Monthly BAU:             $1,030                │
│ ────────────                                   │
│ GRAND TOTAL:             $46,000               │
│                                                 │
├────────────────────────────────────────────────┤
│ BY ENGINEERING TEAM                            │
│ ───────────────────                            │
│ Scraping Team:            $15,000    (33%)     │
│ Data Engineering:         $10,000    (22%)     │
│ AI/ML Team:               $8,000     (18%)     │
│ Integration Team:         $5,000     (11%)     │
│ DevOps/MLOps:            $4,000     (9%)      │
│ UI/Frontend:             $3,000     (7%)      │
└────────────────────────────────────────────────┘
```

### Sheet 2: Scraping Team
```
┌─────┬──────────────────────┬──────────┬──────┬────────┐
│ S.No│ Task Description     │ Hours    │ Rate │ Cost   │
├─────┼──────────────────────┼──────────┼──────┼────────┤
│ 1   │ Scraping Setup       │ 40       │ $30  │ $1,200 │
│ 1.1 │ Playwright config    │ 8        │ $30  │ $240   │
│ 1.2 │ Proxy setup          │ 16       │ $30  │ $480   │
│ 1.3 │ Rate limiting        │ 16       │ $30  │ $480   │
│ 2   │ Source Scrapers      │ 300      │ $30  │ $9,000 │
│ 2.1 │ Website scraper      │ 200      │ $30  │ $6,000 │
│ 2.2 │ API integrations     │ 100      │ $30  │ $3,000 │
│ ... │ ...                  │ ...      │ ...  │ ...    │
├─────┼──────────────────────┼──────────┼──────┼────────┤
│     │ TEAM SUBTOTAL        │ 500      │      │ $15,000│
└─────┴──────────────────────┴──────────┴──────┴────────┘
```

### Sheet 3: Data Engineering Team
*(Similar structure)*

### Sheet 4: AI/ML Team
*(Similar structure)*

... *(One sheet per team)*

### Sheet N: Infrastructure
```
┌────────────────────────┬────────────┐
│ ONE-TIME COSTS         │ Amount     │
├────────────────────────┼────────────┤
│ Virtual Machines       │ $430       │
│ Database Setup         │ $200       │
│ Storage Setup          │ $50        │
│ Network Config         │ $100       │
├────────────────────────┼────────────┤
│ TOTAL ONE-TIME         │ $780       │
└────────────────────────┴────────────┘

┌────────────────────────┬────────────┐
│ MONTHLY RECURRING      │ Amount     │
├────────────────────────┼────────────┤
│ VM Hosting             │ $170       │
│ Database Hosting       │ $100       │
│ Storage                │ $30        │
├────────────────────────┼────────────┤
│ TOTAL MONTHLY          │ $300       │
└────────────────────────┴────────────┘
```

### Sheet N+1: BAU Monthly Costs (Full Service only)
```
┌────────────────────────┬────────────┐
│ BAU COMPONENT          │ Monthly    │
├────────────────────────┼────────────┤
│ Infrastructure         │ $300       │
│ Token Costs (1000 docs)│ $110       │
│ Support Hours (25h)    │ $750       │
│ Monitoring             │ $50        │
├────────────────────────┼────────────┤
│ TOTAL MONTHLY BAU      │ $1,210     │
└────────────────────────┴────────────┘
```

---

## 🚀 Benefits of Agentic Approach

### 1. ✅ **True LLM-First Architecture**
- Agents make all decisions
- No hardcoded categories or rules
- Adapts to any industry/project type

### 2. ✅ **Modular and Extensible**
- Add new agent types easily
- Swap agent implementations
- Customize per industry

### 3. ✅ **Leverages Existing Stack**
- Uses LangGraph (already in stack)
- Uses LLMService (multi-provider)
- Uses EmbeddingService for example analysis
- Uses TemplateParser for sample files

### 4. ✅ **Intelligent and Adaptive**
- Learns from uploaded examples
- Adjusts to project context
- Handles edge cases gracefully

### 5. ✅ **Clear Outputs**
- One sheet per engineering team
- Master rollup sheet
- Professional BRD
- Easy to understand

---

## 🛠️ Implementation Plan

### Phase 1: Core Workflow (Week 1)
1. Create `ProjectEstimatorWorkflow` class
2. Implement 7 agent functions
3. Test LangGraph state machine
4. Validate agent outputs

### Phase 2: Excel Generator Enhancement (Week 1-2)
1. Modify `ExcelGenerationService` for per-team sheets
2. Add master rollup logic
3. Add charts and visualizations
4. Test with sample data

### Phase 3: Integration (Week 2)
1. Create API endpoint `/api/v1/project-estimator/generate-agentic`
2. Integrate with frontend
3. Handle file uploads
4. Return download URLs

### Phase 4: Testing & Refinement (Week 2-3)
1. Test with various project types
2. Refine agent prompts
3. Optimize performance
4. Add error handling

---

## 📝 Example Usage

### API Request
```json
POST /api/v1/project-estimator/generate-agentic

{
  "project_scope": "Build a web scraping solution to extract data from 500 e-commerce sites, transform and load into database, with AI-powered categorization",
  "rate_config": {
    "development_rate": 30,
    "planning_rate": 30,
    "testing_rate": 26
  },
  "scenario": "baseline",
  "uploaded_files": [
    "sample_brd_1.pptx",
    "sample_cost_estimate.xlsx"
  ]
}
```

### API Response
```json
{
  "success": true,
  "brd_url": "https://minio/brds/project_brd_12345.pptx",
  "cost_estimation_url": "https://minio/costs/project_cost_12345.xlsx",
  "project_classification": {
    "project_type": "Full Service",
    "needs_bau": true,
    "duration_weeks": 12,
    "risk_level": "medium"
  },
  "team_plan": {
    "teams": [
      {"name": "Scraping", "allocation": 100},
      {"name": "Data Engineering", "allocation": 80},
      {"name": "AI/ML", "allocation": 60},
      {"name": "DevOps", "allocation": 30},
      {"name": "UI", "allocation": 40}
    ]
  },
  "master_summary": {
    "total_cost": 46000,
    "total_hours": 1200,
    "by_team": {
      "Scraping": 15000,
      "Data Engineering": 10000,
      "AI/ML": 8000,
      "DevOps": 4000,
      "UI": 3000
    }
  }
}
```

---

## 🎓 Key Innovations

### 1. **Example-Guided Learning**
Agents analyze uploaded sample BRDs and cost estimates to understand patterns and styles.

### 2. **Dynamic Team Identification**
No hardcoded teams - agents determine which engineering teams are needed based on project requirements.

### 3. **Per-Team Cost Sheets**
Clearer breakdown - one Excel sheet per engineering team + master rollup.

### 4. **Context-Aware Rate Assignment**
LLM assigns rates based on task complexity and context, not keyword matching.

### 5. **Agentic Collaboration**
Agents pass state through LangGraph, building on each other's outputs.

---

## 📚 File Structure

```
backend/app/
├── agents/
│   └── project_estimator/
│       ├── __init__.py
│       ├── workflow.py                      # Main LangGraph workflow
│       ├── analyst_agent.py                 # Agent 1: Analyst
│       ├── classifier_agent.py              # Agent 2: Classifier
│       ├── team_planner_agent.py            # Agent 3: Team Planner
│       ├── task_generator_agent.py          # Agent 4: Task Generator
│       ├── cost_estimator_agent.py          # Agent 5: Cost Estimator
│       ├── consolidator_agent.py            # Agent 6: Consolidator
│       └── document_generator_agent.py      # Agent 7: Document Generator
│
├── api/routes/
│   └── project_estimator_agentic_routes.py  # API endpoint
│
└── services/
    └── project_estimator/
        ├── brd_generation_service.py        # Reuse for BRD
        └── excel_generation_service.py      # Enhanced for per-team sheets
```

---

## 🔗 Leveraging Existing Stack

### LangGraph (already in stack)
- `backend/app/agents/` - Agent framework
- State management
- Graph execution

### LLM Service
- `backend/app/services/llm_service.py`
- Multi-provider (OpenAI, Anthropic, Ollama)
- JSON response mode

### Embedding Service
- `backend/app/services/embedding_service.py`
- Analyze uploaded examples
- Semantic similarity

### Template Parser
- `backend/app/services/template_parser_service.py`
- Extract patterns from sample files

---

## ✨ Summary

This agentic approach:
- ✅ **Keeps the brain in LLM** - All decisions made by agents
- ✅ **No hardcoded rules** - Adapts to any project type
- ✅ **Leverages existing stack** - Uses LangGraph, LLM Service, etc.
- ✅ **Clear outputs** - Per-team sheets + master rollup
- ✅ **Innovative** - Example-guided, context-aware, collaborative agents
- ✅ **Simple to use** - User provides prompt + examples, system does the rest

**Philosophy**: Let specialized AI agents collaborate to understand, plan, estimate, and document projects - just like a real consulting team would.

---

**Next Steps**: Implement Phase 1 (Core Workflow) using LangGraph.
