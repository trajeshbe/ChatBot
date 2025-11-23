"""
Project Estimator Agentic Workflow

6-Agent LangGraph workflow for intelligent project cost estimation.
Each agent is guided by uploaded examples (BRDs, cost estimates, sample data).
"""

import json
import logging
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from app.services.llm_service import LLMService
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)


# ============================================================================
# State Definition
# ============================================================================

class ProjectEstimatorState(TypedDict):
    """
    State shared across all agents in the workflow.

    Input fields are populated by the API endpoint.
    Each agent reads relevant fields and populates its output fields.
    """
    # ========== INPUT (from API) ==========
    user_prompt: str                          # Project description
    uploaded_brd_files: List[str]             # Paths to BRD examples
    uploaded_cost_files: List[str]            # Paths to cost estimate examples
    uploaded_sample_data: List[str]           # Paths to sample data files
    rate_config: Dict[str, float]             # UI rate configuration
    overhead_config: Dict[str, float]         # Overhead percentages
    scenario: str                             # baseline/conservative/aggressive
    project_type: str                         # POC/Staff Augmentation/Full Service

    # ========== ANALYZED EXAMPLES (for guiding LLM) ==========
    brd_examples_summary: str                 # Extracted patterns from BRDs
    cost_examples_summary: str                # Extracted patterns from costs
    sample_data_complexity: str               # Complexity analysis from samples

    # ========== AGENT 1: ANALYST OUTPUT ==========
    requirements: Dict[str, Any]              # Parsed requirements

    # ========== AGENT 2: TEAM PLANNER OUTPUT ==========
    team_plan: Dict[str, List[Dict]]          # Engineering teams identified

    # ========== AGENT 3: TASK GENERATOR OUTPUT ==========
    tasks_by_team: Dict[str, List[Dict]]      # Tasks per team

    # ========== AGENT 4: WORKFLOW AGENT OUTPUT ==========
    project_workflow: Dict[str, Any]          # Execution phases and timeline

    # ========== AGENT 5: RATE ASSIGNMENT OUTPUT ==========
    costs_by_team: Dict[str, Dict]            # Cost calculations per team

    # ========== AGENT 6: DOCUMENT GENERATOR OUTPUT ==========
    brd_path: str                             # Generated BRD.pptx path
    excel_path: str                           # Generated Excel path

    # ========== METADATA ==========
    errors: List[str]                         # Error messages
    processing_time: float                    # Total processing time
    timestamp: str                            # ISO timestamp


# ============================================================================
# Main Workflow Class
# ============================================================================

class ProjectEstimatorWorkflow:
    """
    6-Agent LangGraph workflow for project cost estimation.

    Workflow:
    User Input → Analyst → Team Planner → Task Generator → Workflow Agent
                 → Rate Assignment → Document Generator → Output
    """

    def __init__(self, llm_service: LLMService, db: Session):
        """
        Initialize workflow with LLM service and database session.

        Args:
            llm_service: Multi-provider LLM service
            db: SQLAlchemy database session
        """
        self.llm_service = llm_service
        self.db = db
        self.document_service = DocumentService(db)
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Build LangGraph state machine with 6 agents.

        Returns:
            Compiled LangGraph workflow
        """
        workflow = StateGraph(ProjectEstimatorState)

        # Add agents as nodes
        workflow.add_node("analyst", self.analyst_agent)
        workflow.add_node("team_planner", self.team_planner_agent)
        workflow.add_node("task_generator", self.task_generator_agent)
        workflow.add_node("workflow_agent", self.workflow_agent)
        workflow.add_node("rate_assignment", self.rate_assignment_agent)
        workflow.add_node("document_generator", self.document_generator_agent)

        # Define edges (sequential flow)
        workflow.set_entry_point("analyst")
        workflow.add_edge("analyst", "team_planner")
        workflow.add_edge("team_planner", "task_generator")
        workflow.add_edge("task_generator", "workflow_agent")
        workflow.add_edge("workflow_agent", "rate_assignment")
        workflow.add_edge("rate_assignment", "document_generator")
        workflow.add_edge("document_generator", END)

        return workflow.compile()

    async def run(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the workflow with given initial state.

        Args:
            initial_state: Input parameters from API

        Returns:
            Final state with all agent outputs
        """
        start_time = datetime.utcnow()

        # Initialize state with defaults
        state = {
            "errors": [],
            "timestamp": start_time.isoformat(),
            **initial_state
        }

        try:
            # Run LangGraph workflow
            final_state = await self.graph.ainvoke(state)

            # Calculate processing time
            end_time = datetime.utcnow()
            final_state["processing_time"] = (end_time - start_time).total_seconds()

            return final_state

        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
            state["errors"].append(f"Workflow error: {str(e)}")
            return state

    # ========================================================================
    # AGENT 1: ANALYST
    # ========================================================================

    async def analyst_agent(self, state: ProjectEstimatorState) -> Dict[str, Any]:
        """
        Agent 1: Analyze user prompt and uploaded examples to extract requirements.

        Input:
            - user_prompt
            - uploaded_brd_files (for learning patterns)
            - uploaded_cost_files (for learning patterns)
            - uploaded_sample_data (for complexity assessment)

        Output:
            - requirements: Structured requirements
            - brd_examples_summary: Summary of BRD patterns
            - cost_examples_summary: Summary of cost patterns
            - sample_data_complexity: Complexity assessment
        """
        logger.info("Agent 1: Analyst - Analyzing requirements and examples")

        try:
            # Step 1: Analyze uploaded BRD examples
            brd_summary = await self._analyze_brd_examples(state["uploaded_brd_files"])

            # Step 2: Analyze uploaded cost estimate examples
            cost_summary = await self._analyze_cost_examples(state["uploaded_cost_files"])

            # Step 3: Analyze sample data for complexity
            data_complexity = await self._analyze_sample_data(state["uploaded_sample_data"])

            # Step 4: Extract requirements from user prompt guided by examples
            requirements = await self._extract_requirements(
                user_prompt=state["user_prompt"],
                brd_patterns=brd_summary,
                cost_patterns=cost_summary,
                data_complexity=data_complexity,
                project_type=state["project_type"]
            )

            return {
                **state,
                "brd_examples_summary": brd_summary,
                "cost_examples_summary": cost_summary,
                "sample_data_complexity": data_complexity,
                "requirements": requirements
            }

        except Exception as e:
            logger.error(f"Analyst agent failed: {str(e)}", exc_info=True)
            state["errors"].append(f"Analyst: {str(e)}")
            return state

    async def _analyze_brd_examples(self, brd_files: List[str]) -> str:
        """Analyze uploaded BRD examples to extract structure patterns."""
        if not brd_files:
            return "No BRD examples provided."

        prompt = f"""
Analyze these uploaded BRD (Business Requirements Document) examples to extract common patterns:

Files analyzed: {len(brd_files)} BRD documents

Extract and summarize:
1. Common document structure (sections, headings)
2. How objectives are typically written
3. Timeline and milestone patterns
4. Scope definition style
5. Deliverables format

Provide a concise summary (3-4 paragraphs) that will guide the generation of a new BRD.
"""

        response = await self.llm_service.generate(
            prompt=prompt,
            model="gpt-4",
            temperature=0.3
        )

        return response.get("content", "Unable to analyze BRD examples.")

    async def _analyze_cost_examples(self, cost_files: List[str]) -> str:
        """Analyze uploaded cost estimate examples to extract task patterns."""
        if not cost_files:
            return "No cost estimate examples provided."

        prompt = f"""
Analyze these uploaded cost estimate examples to extract task breakdown patterns:

Files analyzed: {len(cost_files)} cost estimate documents

Extract and summarize:
1. How tasks are categorized and numbered
2. Typical effort estimation patterns (hours/days)
3. Team composition patterns
4. Infrastructure and overhead patterns
5. Task granularity (high-level vs detailed)

Provide a concise summary (3-4 paragraphs) that will guide task generation.
"""

        response = await self.llm_service.generate(
            prompt=prompt,
            model="gpt-4",
            temperature=0.3
        )

        return response.get("content", "Unable to analyze cost examples.")

    async def _analyze_sample_data(self, sample_files: List[str]) -> str:
        """Analyze sample data to assess complexity."""
        if not sample_files:
            return "No sample data provided. Assume medium complexity."

        prompt = f"""
Analyze these sample data files to assess project complexity:

Files analyzed: {len(sample_files)} sample data files

Assess and describe:
1. Data structure complexity (simple key-value, nested JSON, complex hierarchies)
2. Data volume indicators
3. Data quality and consistency
4. Required transformations
5. Overall complexity rating (Low, Medium, High)

Provide a concise assessment (2-3 paragraphs).
"""

        response = await self.llm_service.generate(
            prompt=prompt,
            model="gpt-4",
            temperature=0.3
        )

        return response.get("content", "Medium complexity assumed.")

    async def _extract_requirements(
        self,
        user_prompt: str,
        brd_patterns: str,
        cost_patterns: str,
        data_complexity: str,
        project_type: str
    ) -> Dict[str, Any]:
        """Extract structured requirements from user prompt guided by examples."""

        prompt = f"""
Extract structured requirements from the user's project description, guided by example patterns.

**User Prompt**:
{user_prompt}

**Project Type**: {project_type}

**Learn from these BRD patterns**:
{brd_patterns}

**Learn from these cost estimate patterns**:
{cost_patterns}

**Data Complexity Assessment**:
{data_complexity}

Extract and structure the following:

1. **Project Goal** (1-2 sentences)
2. **Key Features** (bullet list, 3-7 items)
3. **Technical Scope**:
   - Data sources
   - Technology requirements
   - Scale (number of items, sites, users, etc.)
4. **Constraints**:
   - Timeline expectations
   - Budget considerations (if mentioned)
   - Technical constraints
5. **Success Criteria** (3-5 measurable outcomes)

Return ONLY a valid JSON object with these keys: project_goal, key_features (array), technical_scope (object), constraints (object), success_criteria (array).
"""

        response = await self.llm_service.generate(
            prompt=prompt,
            model="gpt-4",
            temperature=0.4,
            response_format={"type": "json_object"}
        )

        try:
            return json.loads(response.get("content", "{}"))
        except json.JSONDecodeError:
            logger.error("Failed to parse requirements JSON")
            return {
                "project_goal": user_prompt,
                "key_features": [],
                "technical_scope": {},
                "constraints": {},
                "success_criteria": []
            }

    # ========================================================================
    # AGENT 2: TEAM PLANNER
    # ========================================================================

    async def team_planner_agent(self, state: ProjectEstimatorState) -> Dict[str, Any]:
        """
        Agent 2: Identify required engineering teams based on requirements.

        Input:
            - requirements (from Analyst)
            - cost_examples_summary (for learning team structures)

        Output:
            - team_plan: Dictionary of teams with responsibilities
        """
        logger.info("Agent 2: Team Planner - Identifying engineering teams")

        try:
            requirements = state["requirements"]
            cost_patterns = state["cost_examples_summary"]
            project_type = state["project_type"]

            prompt = f"""
Identify the engineering teams required for this project, learning from historical patterns.

**Requirements**:
{json.dumps(requirements, indent=2)}

**Project Type**: {project_type}

**Learn from historical team structures**:
{cost_patterns}

Identify ALL relevant engineering teams from these categories (only include if needed):
- Scraping/Data Collection Team
- Data Engineering Team
- AI/ML Engineering Team
- Backend Engineering Team
- Frontend/UI Engineering Team
- Mobile Engineering Team
- DevOps/Infrastructure Team
- MLOps Team
- QA/Testing Team
- Security Team
- Integration Team

For EACH identified team, provide:
1. **Team Name**
2. **Responsibilities** (3-5 specific responsibilities for THIS project)
3. **Allocation** (percentage: 30%, 50%, 100% - how much of the team's capacity is needed)
4. **Why Needed** (1-2 sentences explaining why this project needs this team)

For **POC projects**: Reduce team count, focus on core functionality teams only.
For **Staff Augmentation**: Focus on requested skill areas.
For **Full Service**: Include all necessary teams including DevOps, QA, ongoing support.

Return ONLY a valid JSON object with structure:
{{
  "teams": [
    {{
      "team_name": "string",
      "responsibilities": ["string", ...],
      "allocation_percentage": 50,
      "rationale": "string"
    }}
  ],
  "total_teams": 5
}}
"""

            response = await self.llm_service.generate(
                prompt=prompt,
                model="gpt-4",
                temperature=0.4,
                response_format={"type": "json_object"}
            )

            team_plan = json.loads(response.get("content", "{}"))

            return {
                **state,
                "team_plan": team_plan
            }

        except Exception as e:
            logger.error(f"Team Planner agent failed: {str(e)}", exc_info=True)
            state["errors"].append(f"Team Planner: {str(e)}")
            return state

    # ========================================================================
    # AGENT 3: TASK GENERATOR
    # ========================================================================

    async def task_generator_agent(self, state: ProjectEstimatorState) -> Dict[str, Any]:
        """
        Agent 3: Generate project-specific tasks for each team.

        Input:
            - requirements (from Analyst)
            - team_plan (from Team Planner)
            - cost_examples_summary (for learning task structures)
            - sample_data_complexity (for effort calibration)

        Output:
            - tasks_by_team: Dictionary mapping team names to task lists
        """
        logger.info("Agent 3: Task Generator - Generating project-specific tasks")

        try:
            requirements = state["requirements"]
            team_plan = state["team_plan"]
            cost_patterns = state["cost_examples_summary"]
            complexity = state["sample_data_complexity"]
            project_type = state["project_type"]

            tasks_by_team = {}

            # Generate tasks for each team
            for team_idx, team in enumerate(team_plan.get("teams", [])):
                team_name = team["team_name"]
                responsibilities = team["responsibilities"]
                allocation = team["allocation_percentage"]

                logger.info(f"Generating tasks for {team_name}")

                team_tasks = await self._generate_team_tasks(
                    team_name=team_name,
                    team_number=team_idx + 1,
                    responsibilities=responsibilities,
                    allocation=allocation,
                    requirements=requirements,
                    cost_patterns=cost_patterns,
                    complexity=complexity,
                    project_type=project_type
                )

                tasks_by_team[team_name] = team_tasks

            return {
                **state,
                "tasks_by_team": tasks_by_team
            }

        except Exception as e:
            logger.error(f"Task Generator agent failed: {str(e)}", exc_info=True)
            state["errors"].append(f"Task Generator: {str(e)}")
            return state

    async def _generate_team_tasks(
        self,
        team_name: str,
        team_number: int,
        responsibilities: List[str],
        allocation: int,
        requirements: Dict[str, Any],
        cost_patterns: str,
        complexity: str,
        project_type: str
    ) -> List[Dict[str, Any]]:
        """Generate specific tasks for a single team."""

        prompt = f"""
Generate project-specific tasks for the {team_name}, learning from historical patterns.

**Team**: {team_name}
**Team Number**: {team_number}
**Allocation**: {allocation}% of team capacity
**Responsibilities**:
{json.dumps(responsibilities, indent=2)}

**Project Requirements**:
{json.dumps(requirements, indent=2)}

**Project Type**: {project_type}

**Data Complexity**: {complexity}

**Learn from historical task patterns**:
{cost_patterns}

Generate 5-10 specific, actionable tasks for THIS team on THIS project.

**Task Numbering**: Use hierarchical numbering starting with team number:
- {team_number}.1, {team_number}.2 for main tasks
- {team_number}.1.1, {team_number}.1.2 for subtasks

**Task Requirements**:
1. **Specific to THIS project** (not generic "Set up environment")
   ✅ Good: "Configure Playwright for Amazon product scraping"
   ❌ Bad: "Set up development environment"

2. **Effort Estimates** in hours (realistic based on complexity)
   - Simple tasks: 4-16 hours
   - Medium tasks: 16-40 hours
   - Complex tasks: 40-80 hours

3. **Category** (choose ONE that fits):
   - Planning & Design
   - Development
   - Configuration
   - Testing & QA
   - Deployment
   - Documentation
   - Training

4. **Complexity**: Easy, Medium, or Hard

For **POC projects**: Fewer tasks (5-7), focus on MVP features only.
For **Staff Augmentation**: Match requested work scope.
For **Full Service**: Include full lifecycle tasks (design, dev, test, deploy, maintain).

Return ONLY a valid JSON object:
{{
  "tasks": [
    {{
      "task_number": "{team_number}.1",
      "task_name": "Specific task description",
      "description": "Detailed description (2-3 sentences)",
      "effort_hours": 24,
      "category": "Development",
      "complexity": "Medium",
      "dependencies": []
    }}
  ]
}}
"""

        response = await self.llm_service.generate(
            prompt=prompt,
            model="gpt-4",
            temperature=0.5,
            response_format={"type": "json_object"}
        )

        try:
            result = json.loads(response.get("content", "{}"))
            return result.get("tasks", [])
        except json.JSONDecodeError:
            logger.error(f"Failed to parse tasks for {team_name}")
            return []

    # ========================================================================
    # AGENT 4: WORKFLOW AGENT (NEW!)
    # ========================================================================

    async def workflow_agent(self, state: ProjectEstimatorState) -> Dict[str, Any]:
        """
        Agent 4: Create project execution workflow from start to completion.

        Input:
            - requirements (from Analyst)
            - team_plan (from Team Planner)
            - tasks_by_team (from Task Generator)
            - brd_examples_summary (for learning timeline structures)

        Output:
            - project_workflow: Execution phases, dependencies, milestones
        """
        logger.info("Agent 4: Workflow Agent - Creating execution workflow")

        try:
            requirements = state["requirements"]
            team_plan = state["team_plan"]
            tasks_by_team = state["tasks_by_team"]
            brd_patterns = state["brd_examples_summary"]
            project_type = state["project_type"]

            # Flatten all tasks for workflow planning
            all_tasks = []
            for team_name, tasks in tasks_by_team.items():
                for task in tasks:
                    all_tasks.append({
                        "team": team_name,
                        "task_number": task["task_number"],
                        "task_name": task["task_name"],
                        "category": task.get("category", "Development"),
                        "effort_hours": task.get("effort_hours", 20)
                    })

            prompt = f"""
Create a project execution workflow showing how this project flows from kickoff to final deliverables.

**Requirements**:
{json.dumps(requirements, indent=2)}

**Teams Involved**:
{json.dumps([t["team_name"] for t in team_plan.get("teams", [])], indent=2)}

**All Tasks** ({len(all_tasks)} tasks total):
{json.dumps(all_tasks[:30], indent=2)}
{f"... and {len(all_tasks) - 30} more tasks" if len(all_tasks) > 30 else ""}

**Project Type**: {project_type}

**Learn from BRD timeline structures**:
{brd_patterns}

Create a **4-6 phase** execution workflow with:

1. **Phase Naming**: Descriptive names showing what happens (e.g., "Planning & Setup", "Development - Core Features", "Testing & UAT")

2. **Phase Duration**: Realistic weeks (POC: 4-8 weeks total, Staff Aug: varies, Full Service: 8-16 weeks)

3. **Task Assignment**: Which task numbers execute in each phase (group by category and dependencies)

4. **Deliverables**: 2-4 concrete deliverables per phase

5. **Dependencies**: Which phases must complete before this phase starts

6. **Milestones**: Key checkpoints (Kickoff, Design Complete, MVP, UAT, Go-Live)

**Typical Phase Flow**:
- Phase 1: Planning, Design, Setup (architecture, schemas, infrastructure)
- Phase 2-3: Development phases (core features, split by functional area)
- Phase 4: Testing & QA (integration tests, UAT)
- Phase 5: Deployment & Handoff (production deploy, documentation, training)

Return ONLY a valid JSON object:
{{
  "workflow": {{
    "phases": [
      {{
        "phase_number": 1,
        "phase_name": "Planning & Setup",
        "duration_weeks": 2,
        "tasks": ["1.1", "1.2", "2.1"],
        "deliverables": ["Architecture document", "Database schema", "Infrastructure setup"],
        "dependencies": []
      }}
    ],
    "total_duration_weeks": 12,
    "milestones": [
      {{"name": "Kickoff", "week": 0}},
      {{"name": "Go-Live", "week": 12}}
    ]
  }}
}}
"""

            response = await self.llm_service.generate(
                prompt=prompt,
                model="gpt-4",
                temperature=0.4,
                response_format={"type": "json_object"}
            )

            workflow = json.loads(response.get("content", "{}"))

            return {
                **state,
                "project_workflow": workflow
            }

        except Exception as e:
            logger.error(f"Workflow agent failed: {str(e)}", exc_info=True)
            state["errors"].append(f"Workflow Agent: {str(e)}")
            return state

    # ========================================================================
    # AGENT 5: RATE ASSIGNMENT
    # ========================================================================

    async def rate_assignment_agent(self, state: ProjectEstimatorState) -> Dict[str, Any]:
        """
        Agent 5: Assign UI rate categories to tasks and calculate costs.

        Input:
            - tasks_by_team (from Task Generator)
            - rate_config (from UI)
            - overhead_config (from UI)
            - scenario (baseline/conservative/aggressive)

        Output:
            - costs_by_team: Cost calculations for each team
        """
        logger.info("Agent 5: Rate Assignment - Mapping tasks to rate categories")

        try:
            tasks_by_team = state["tasks_by_team"]
            rate_config = state["rate_config"]
            overhead_config = state.get("overhead_config", {})
            scenario = state["scenario"]

            costs_by_team = {}

            for team_name, tasks in tasks_by_team.items():
                logger.info(f"Assigning rates for {team_name}")

                team_costs = await self._assign_team_rates(
                    team_name=team_name,
                    tasks=tasks,
                    rate_config=rate_config,
                    overhead_config=overhead_config,
                    scenario=scenario
                )

                costs_by_team[team_name] = team_costs

            # Calculate totals
            total_cost = sum(team["total_cost"] for team in costs_by_team.values())
            total_hours = sum(team["total_hours"] for team in costs_by_team.values())

            return {
                **state,
                "costs_by_team": {
                    **costs_by_team,
                    "summary": {
                        "total_cost": total_cost,
                        "total_hours": total_hours,
                        "team_count": len(costs_by_team)
                    }
                }
            }

        except Exception as e:
            logger.error(f"Rate Assignment agent failed: {str(e)}", exc_info=True)
            state["errors"].append(f"Rate Assignment: {str(e)}")
            return state

    async def _assign_team_rates(
        self,
        team_name: str,
        tasks: List[Dict[str, Any]],
        rate_config: Dict[str, float],
        overhead_config: Dict[str, float],
        scenario: str
    ) -> Dict[str, Any]:
        """Assign rate categories to team tasks using LLM."""

        # Extract available rate categories from UI config
        available_rates = list(rate_config.keys())

        prompt = f"""
Map each task to the appropriate billing rate category from the UI configuration.

**Team**: {team_name}

**Tasks**:
{json.dumps(tasks, indent=2)}

**Available Rate Categories** (from UI):
{json.dumps(available_rates, indent=2)}

**Example Rate Mappings**:
{json.dumps(rate_config, indent=2)}

For EACH task, determine which rate category applies based on:
- Task category (Planning, Development, Testing, etc.)
- Task complexity
- Required skill level

Common mappings:
- "planning_rate" → Planning, Design, Architecture tasks
- "development_rate" → Core development tasks
- "scraping_development_rate" → Web scraping specific tasks
- "testing_rate" → QA, Testing, Validation tasks
- "devops_rate" → Infrastructure, Deployment tasks

Return ONLY a valid JSON object:
{{
  "task_rates": [
    {{
      "task_number": "1.1",
      "rate_category": "development_rate",
      "rate_value": 30,
      "justification": "Core development task"
    }}
  ]
}}
"""

        response = await self.llm_service.generate(
            prompt=prompt,
            model="gpt-4",
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        try:
            result = json.loads(response.get("content", "{}"))
            task_rates = result.get("task_rates", [])

            # Calculate costs
            tasks_with_costs = []
            total_hours = 0
            total_cost = 0

            for i, task in enumerate(tasks):
                task_rate_info = task_rates[i] if i < len(task_rates) else {}
                rate_category = task_rate_info.get("rate_category", "development_rate")
                rate_value = rate_config.get(rate_category, 30)

                effort_hours = task.get("effort_hours", 20)
                task_cost = effort_hours * rate_value

                tasks_with_costs.append({
                    **task,
                    "rate_category": rate_category,
                    "rate_value": rate_value,
                    "task_cost": task_cost
                })

                total_hours += effort_hours
                total_cost += task_cost

            # Apply overhead
            overhead_rate = overhead_config.get("overhead_percentage", 0.15)
            overhead_cost = total_cost * overhead_rate
            final_cost = total_cost + overhead_cost

            return {
                "team_name": team_name,
                "tasks": tasks_with_costs,
                "total_hours": total_hours,
                "subtotal_cost": total_cost,
                "overhead_cost": overhead_cost,
                "total_cost": final_cost
            }

        except json.JSONDecodeError:
            logger.error(f"Failed to parse rate assignments for {team_name}")
            # Fallback: use development_rate for all
            default_rate = rate_config.get("development_rate", 30)
            total_hours = sum(t.get("effort_hours", 20) for t in tasks)
            total_cost = total_hours * default_rate

            return {
                "team_name": team_name,
                "tasks": tasks,
                "total_hours": total_hours,
                "subtotal_cost": total_cost,
                "overhead_cost": 0,
                "total_cost": total_cost
            }

    # ========================================================================
    # AGENT 6: DOCUMENT GENERATOR
    # ========================================================================

    async def document_generator_agent(self, state: ProjectEstimatorState) -> Dict[str, Any]:
        """
        Agent 6: Generate final BRD.pptx and CostEstimate.xlsx outputs.

        Input:
            - ALL previous agent outputs
            - brd_examples_summary (for style guidance)

        Output:
            - brd_path: Path to generated BRD.pptx
            - excel_path: Path to generated CostEstimate.xlsx
        """
        logger.info("Agent 6: Document Generator - Creating BRD and Excel outputs")

        try:
            # Import generation services
            from app.services.project_estimator.brd_generation_service import BRDGenerationService
            from app.services.project_estimator.excel_generation_service import ExcelGenerationService

            # TODO: Enhance these services to use the state data
            # For now, return placeholder paths

            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            brd_path = f"/tmp/BRD_{timestamp}.pptx"
            excel_path = f"/tmp/CostEstimate_{timestamp}.xlsx"

            # TODO: Call BRD generation service
            # brd_service = BRDGenerationService(self.llm_service)
            # brd_path = await brd_service.generate(state)

            # TODO: Call Excel generation service
            # excel_service = ExcelGenerationService()
            # excel_path = await excel_service.generate(state)

            logger.info(f"Documents generated: {brd_path}, {excel_path}")

            return {
                **state,
                "brd_path": brd_path,
                "excel_path": excel_path
            }

        except Exception as e:
            logger.error(f"Document Generator agent failed: {str(e)}", exc_info=True)
            state["errors"].append(f"Document Generator: {str(e)}")
            return state

    # ========================================================================
    # VISUALIZATION
    # ========================================================================

    def get_graph_visualization(self) -> Dict[str, Any]:
        """
        Generate visualization data for the LangGraph workflow.

        Returns:
            Dictionary containing Mermaid diagram and graph metadata
        """
        try:
            # Generate Mermaid diagram
            mermaid_diagram = self._generate_mermaid_diagram()

            # Get graph metadata
            metadata = {
                "total_agents": 6,
                "agents": [
                    {
                        "name": "Analyst",
                        "purpose": "Analyze examples and extract requirements",
                        "input": ["user_prompt", "uploaded_files"],
                        "output": ["requirements", "example_summaries"]
                    },
                    {
                        "name": "Team Planner",
                        "purpose": "Identify required engineering teams",
                        "input": ["requirements", "cost_patterns"],
                        "output": ["team_plan"]
                    },
                    {
                        "name": "Task Generator",
                        "purpose": "Generate project-specific tasks",
                        "input": ["requirements", "team_plan", "complexity"],
                        "output": ["tasks_by_team"]
                    },
                    {
                        "name": "Workflow Agent",
                        "purpose": "Create execution phases and timeline",
                        "input": ["requirements", "team_plan", "tasks"],
                        "output": ["project_workflow"]
                    },
                    {
                        "name": "Rate Assignment",
                        "purpose": "Map tasks to UI rate categories",
                        "input": ["tasks_by_team", "rate_config"],
                        "output": ["costs_by_team"]
                    },
                    {
                        "name": "Document Generator",
                        "purpose": "Generate BRD.pptx and Excel outputs",
                        "input": ["all_agent_outputs"],
                        "output": ["brd_path", "excel_path"]
                    }
                ],
                "execution_flow": "Sequential: Analyst → Team Planner → Task Generator → Workflow Agent → Rate Assignment → Document Generator",
                "key_features": [
                    "LLM-First: All decisions made by LLM",
                    "Example-Guided: Learns from uploaded references",
                    "Dynamic Teams: No hardcoded team list",
                    "Project-Specific Tasks: Adaptive to context",
                    "LLM Rate Assignment: No keyword matching"
                ]
            }

            return {
                "mermaid_diagram": mermaid_diagram,
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"Visualization generation failed: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "mermaid_diagram": self._get_fallback_diagram(),
                "metadata": {}
            }

    def _generate_mermaid_diagram(self) -> str:
        """
        Generate Mermaid flowchart diagram for the workflow.

        Returns:
            Mermaid diagram as string
        """
        mermaid = """
graph TD
    Start([User Input]) --> Analyst[Agent 1: Analyst<br/>Analyze Examples & Extract Requirements]
    
    Analyst --> AnalystOutput{{"
        ✓ BRD Examples Summary<br/>
        ✓ Cost Examples Summary<br/>
        ✓ Data Complexity<br/>
        ✓ Requirements
    "}}
    
    AnalystOutput --> TeamPlanner[Agent 2: Team Planner<br/>Identify Engineering Teams]
    
    TeamPlanner --> TeamOutput{{"
        ✓ Teams Identified<br/>
        ✓ Allocation %<br/>
        ✓ Responsibilities
    "}}
    
    TeamOutput --> TaskGen[Agent 3: Task Generator<br/>Generate Project-Specific Tasks]
    
    TaskGen --> TaskOutput{{"
        ✓ Tasks by Team<br/>
        ✓ Effort Estimates<br/>
        ✓ Hierarchical Numbering
    "}}
    
    TaskOutput --> WorkflowAgent[Agent 4: Workflow Agent<br/>Create Execution Plan]
    
    WorkflowAgent --> WorkflowOutput{{"
        ✓ Execution Phases<br/>
        ✓ Dependencies<br/>
        ✓ Milestones<br/>
        ✓ Timeline
    "}}
    
    WorkflowOutput --> RateAssign[Agent 5: Rate Assignment<br/>Map Tasks to Rate Categories]
    
    RateAssign --> CostOutput{{"
        ✓ Costs by Team<br/>
        ✓ Rate Categories<br/>
        ✓ Total Cost
    "}}
    
    CostOutput --> DocGen[Agent 6: Document Generator<br/>Generate BRD & Excel]
    
    DocGen --> End([BRD.pptx + Excel])
    
    style Start fill:#e1f5e1
    style End fill:#e1f5e1
    style Analyst fill:#e3f2fd
    style TeamPlanner fill:#e3f2fd
    style TaskGen fill:#e3f2fd
    style WorkflowAgent fill:#fff9c4
    style RateAssign fill:#e3f2fd
    style DocGen fill:#e3f2fd
    style AnalystOutput fill:#f3e5f5
    style TeamOutput fill:#f3e5f5
    style TaskOutput fill:#f3e5f5
    style WorkflowOutput fill:#ffe0b2
    style CostOutput fill:#f3e5f5
"""
        return mermaid.strip()

    def _get_fallback_diagram(self) -> str:
        """Fallback diagram if visualization fails."""
        return """
graph LR
    A[Start] --> B[Analyst]
    B --> C[Team Planner]
    C --> D[Task Generator]
    D --> E[Workflow Agent]
    E --> F[Rate Assignment]
    F --> G[Document Generator]
    G --> H[End]
"""
