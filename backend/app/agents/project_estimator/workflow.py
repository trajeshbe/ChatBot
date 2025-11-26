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

import json
import logging
import os
from typing import TypedDict, List, Dict, Any, Optional, Tuple
from datetime import datetime

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from app.services.llm_service import LLMService
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions
# ============================================================================

def extract_json_from_response(response_text: str) -> str:
    """
    Extract JSON from LLM response that may be wrapped in markdown code blocks.

    Handles:
    - Pure JSON
    - JSON wrapped in ```json...```
    - JSON wrapped in ```...```
    - Text before/after JSON
    """
    if not response_text:
        return "{}"

    # Try to find JSON in markdown code blocks
    import re

    # Pattern 1: ```json ... ```
    json_match = re.search(r'```json\s*\n(.*?)\n```', response_text, re.DOTALL)
    if json_match:
        return json_match.group(1).strip()

    # Pattern 2: ``` ... ```
    code_match = re.search(r'```\s*\n(.*?)\n```', response_text, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()

    # Pattern 3: Find JSON object by braces
    brace_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if brace_match:
        return brace_match.group(0).strip()

    # Pattern 4: Find JSON array by brackets
    bracket_match = re.search(r'\[.*\]', response_text, re.DOTALL)
    if bracket_match:
        return bracket_match.group(0).strip()

    # Fallback: return as-is and hope for the best
    return response_text.strip()


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
    model_id: str                             # LLM model to use (from UI or Model Registry)

    # ========== ANALYZED EXAMPLES (for guiding LLM) ==========
    brd_examples_summary: str                 # Extracted patterns from BRDs
    cost_examples_summary: str                # Extracted patterns from costs
    sample_data_complexity: str               # Complexity analysis from samples

    # ========== AGENT 1: ANALYST OUTPUT ==========
    requirements: Dict[str, Any]              # Parsed requirements

    # ========== AGENT 1.1: SAMPLE COMPLEXITY ANALYZER OUTPUT ==========
    complexity_analysis: Dict[str, Any]       # File complexity analysis and multipliers

    # ========== AGENT 1.2: DEBATE COORDINATOR OUTPUT ==========
    consensus_analysis: Dict[str, Any]        # Alignment validation between scope & data

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

    # ========== AGENT 6.5: DOCUMENT VALIDATOR OUTPUT ==========
    document_validation_report: Dict[str, Any]   # Validation results
    document_validation_decision: str            # PASS or RESTART_WORKFLOW
    validation_history: List[Dict[str, Any]]     # Mistakes from previous iterations
    iteration_count: int                         # Current iteration number

    # ========== METADATA ==========
    errors: List[str]                         # Error messages
    processing_time: float                    # Total processing time
    timestamp: str                            # ISO timestamp


# ============================================================================
# Main Workflow Class
# ============================================================================

class ProjectEstimatorWorkflow:
    """
    7-Agent LangGraph workflow for project cost estimation with validation.

    Workflow:
    User Input → Analyst → Team Planner → Task Generator → Validator
                 → Workflow Agent → Rate Assignment → Document Generator → Output

    The Validator agent acts as a "senior architect reviewer" ensuring all outputs
    are aligned with the project scope before proceeding.
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
        self.document_service = DocumentService()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Build LangGraph state machine with 9 agents (including feedback loop).

        Workflow:
        Agent 1 → Agent 1.1 → Agent 2 → Agent 3 → Agent 3.5 → Agent 4 → Agent 5 → Agent 6 → Agent 6.5
                                                                                                  ↓
                                                                                        [PASS or RESTART]
                                                                                                  ↓
                                                                                  If RESTART → Agent 1
                                                                                  If PASS → END

        Returns:
            Compiled LangGraph workflow
        """
        workflow = StateGraph(ProjectEstimatorState)

        # Add agents as nodes
        workflow.add_node("analyst", self.analyst_agent)
        workflow.add_node("sample_complexity_analyzer", self.sample_complexity_analyzer)  # Agent 1.1: Analyzes sample files
        workflow.add_node("debate_coordinator", self.debate_coordinator)  # Agent 1.2: Validates alignment
        workflow.add_node("team_planner", self.team_planner_agent)
        workflow.add_node("task_generator", self.task_generator_agent)
        workflow.add_node("validator", self.validator_agent)  # Agent 3.5: Validates teams/tasks
        workflow.add_node("workflow_agent", self.workflow_agent)
        workflow.add_node("rate_assignment", self.rate_assignment_agent)
        workflow.add_node("document_generator", self.document_generator_agent)
        workflow.add_node("document_validator", self.document_validator_agent)  # Agent 6.5: Validates final documents

        # Define conditional routing function for document validator
        def should_restart_workflow(state: ProjectEstimatorState) -> str:
            """
            Decide whether to restart workflow or proceed to END based on document validation.

            Returns:
                "restart" if validation found critical issues (max 3 iterations)
                "end" if validation passed or max iterations reached
            """
            decision = state.get("document_validation_decision", "PASS")
            iteration_count = state.get("iteration_count", 0)

            if decision == "RESTART_WORKFLOW" and iteration_count < 3:
                logger.warning(f"Document validation failed - restarting workflow (iteration {iteration_count + 1}/3)")
                return "restart"
            else:
                if iteration_count >= 3:
                    logger.warning("Max iterations (3) reached - proceeding to END despite validation issues")
                return "end"

        # Define edges (sequential flow with two validation gates + feedback loop)
        workflow.set_entry_point("analyst")
        workflow.add_edge("analyst", "sample_complexity_analyzer")  # Agent 1 → Agent 1.1
        workflow.add_edge("sample_complexity_analyzer", "debate_coordinator")  # Agent 1.1 → Agent 1.2
        workflow.add_edge("debate_coordinator", "team_planner")  # Agent 1.2 → Agent 2
        workflow.add_edge("team_planner", "task_generator")
        workflow.add_edge("task_generator", "validator")  # Agent 3.5: Validate teams/tasks
        workflow.add_edge("validator", "workflow_agent")
        workflow.add_edge("workflow_agent", "rate_assignment")
        workflow.add_edge("rate_assignment", "document_generator")
        workflow.add_edge("document_generator", "document_validator")  # Agent 6.5: Validate final documents

        # Conditional edge: restart workflow or end
        workflow.add_conditional_edges(
            "document_validator",
            should_restart_workflow,
            {
                "restart": "analyst",  # Loop back to beginning with mistake context
                "end": END             # Proceed to output
            }
        )

        # Note: recursion_limit parameter not supported in LangGraph 0.2.16
        # Using default recursion behavior
        return workflow.compile(checkpointer=None)

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
            "iteration_count": 0,
            "validation_history": [],
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

        response = await self.llm_service.generate(
            prompt=prompt,
            model_id="gpt-4",
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
            model_id="gpt-4",
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
            model_id="gpt-4",
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
**YOU ARE AN EXPERT AI SOLUTIONS ARCHITECT** with deep expertise in analyzing project requirements, technical scoping, and solution design.

**ULTIMATE GOAL**: Translate the Project Scope Document into a comprehensive Business Requirements Document (BRD).

You are Agent 1 (Analyst) in a 6-agent workflow. Your role is to deeply analyze the Project Scope and extract structured requirements that will guide downstream agents to produce an intelligent, contextual solution.

**CRITICAL**: Your analysis must be INTELLIGENT and CONTEXTUAL. Identify what technologies, teams, and tasks are ACTUALLY NEEDED based on the specific problem being solved.

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

**YOUR TASK**: Extract structured requirements following this CONTEXT HIERARCHY:

**STEP 1: Analyze the Project Scope Deeply**
- What SPECIFIC problem is being solved?
- What are the EXACT features requested?
- What data will the system work with?

**STEP 2: Assess Complexity from Sample Data**
- How complex is the data based on the samples provided?
- What data volume/scale should we plan for?
- What performance requirements does this imply?

**STEP 3: Determine Tech Stack from Scope + Complexity**
- Based on STEP 1 & 2, what technologies are ACTUALLY needed?
- Don't assume - derive from the specific requirements

---

Now extract:

1. **Project Goal** (1-2 sentences summarizing the SPECIFIC objective - what problem is being solved?)
   - Reference EXACT details from the Project Scope Document

2. **Key Features** (3-7 bullet points):
   - Extract ONLY features explicitly mentioned or clearly implied in the scope
   - Be SPECIFIC to this project (not generic "user management" but "multi-role access for construction teams with real-time permissions")
   - Follow the writing style from uploaded BRD patterns
   - Calibrate feature complexity based on sample data assessment

3. **Technical Scope** (DERIVE FROM PROJECT SCOPE + SAMPLE COMPLEXITY):
   - **Data sources**: What data does THIS project actually need? (analyze the Project Scope to determine)
   - **Technology requirements**: What tech stack is NEEDED for THIS project?
     * Web scraping? → ONLY if Project Scope mentions collecting data from websites
     * ML/AI? → ONLY if Project Scope mentions predictions, recommendations, NLP, classification, etc.
     * Real-time systems? → ONLY if Project Scope mentions live updates, streaming, real-time collaboration
     * Document processing? → ONLY if Project Scope mentions PDFs, Excel, images, OCR
     * Database type? → Determined by data complexity from samples (simple CRUD vs complex relations)
   - **Scale**: How many users, items, data volume? (extract from scope AND calibrate with sample data complexity)

4. **Constraints**:
   - Timeline expectations (extract from scope or infer based on project type)
   - Budget considerations (if mentioned)
   - Technical constraints (specific technologies mentioned, compliance requirements, etc.)

5. **Success Criteria** (3-5 measurable outcomes):
   - What does "success" look like for THIS specific project?
   - How will we know if the solution solves the problem?

**CRITICAL INSTRUCTIONS**:
- BE SPECIFIC: Don't say "data processing" - say "real-time processing of construction progress updates"
- BE CONTEXTUAL: Only mention technologies that are NEEDED for this specific project
- BE INTELLIGENT: Analyze what the project really needs, not what all projects typically need
- Follow the writing style and structure from the uploaded BRD patterns
- Ensure extracted features align with the complexity indicated by sample data
- Match the level of detail and terminology used in the cost estimate patterns

Return ONLY a valid JSON object with these keys: project_goal, key_features (array), technical_scope (object), constraints (object), success_criteria (array).
"""

        response = await self.llm_service.generate(
            prompt=prompt,
            model_id="gpt-4",
            temperature=0.4,
            max_tokens=1500  # Increased to prevent truncation
        )

        try:
            json_text = extract_json_from_response(response.get("content", "{}"))
            logger.info(f"Analyst extracted JSON (first 300 chars): {json_text[:300]}")
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse requirements JSON: {str(e)}")
            logger.error(f"Malformed JSON: {json_text if 'json_text' in locals() else 'N/A'}")
            return {
                "project_goal": user_prompt,
                "key_features": [],
                "technical_scope": {},
                "constraints": {},
                "success_criteria": []
            }

    # ========================================================================
    # AGENT 1.1: SAMPLE COMPLEXITY ANALYZER
    # ========================================================================

    async def sample_complexity_analyzer(self, state: ProjectEstimatorState) -> Dict[str, Any]:
        """
        Agent 1.1: Analyze uploaded sample files to determine project complexity.

        NOW WITH:
        - Comprehensive EDA (Exploratory Data Analysis)
        - AI/ML tech stack recommendations
        - ChatBot tool mapping
        - 5-10MB file size validation

        Input:
            - uploaded_brd_files (sample BRDs/PDFs)
            - uploaded_cost_files (sample Excel files)
            - uploaded_sample_data (images, other files)

        Output:
            - complexity_analysis: {
                overall_rating, effort_multiplier, rate_multiplier,
                skill_requirements, recommended_teams, reasoning,
                eda_report (NEW),
                recommended_tech_stack (NEW)
              }
        """
        logger.info("Agent 1.1: Sample Complexity Analyzer (with EDA) - Analyzing uploaded samples")

        try:
            from app.services.eda_analyzer import EDAAnalyzer
            import yaml
            from pathlib import Path

            eda_analyzer = EDAAnalyzer()

            # Step 1: Collect all sample file paths
            sample_files_paths = []

            for brd_file in state.get("uploaded_brd_files", []):
                sample_files_paths.append(brd_file)

            for cost_file in state.get("uploaded_cost_files", []):
                sample_files_paths.append(cost_file)

            for sample_file in state.get("uploaded_sample_data", []):
                sample_files_paths.append(sample_file)

            if not sample_files_paths:
                logger.warning("No sample files provided for EDA")
                return self._generate_fallback_analysis(state, "No sample files")

            # Step 2: Analyze each file with EDA
            logger.info(f"Performing EDA on {len(sample_files_paths)} file(s)...")
            files_analysis = []

            for file_path in sample_files_paths:
                try:
                    file_ext = Path(file_path).suffix.lower()

                    if file_ext in ['.xlsx', '.xls']:
                        analysis = await eda_analyzer.analyze_excel_file(file_path)
                    elif file_ext == '.pdf':
                        analysis = await eda_analyzer.analyze_pdf_file(file_path)
                    elif file_ext in ['.jpg', '.jpeg', '.png']:
                        analysis = await eda_analyzer.analyze_image_file(file_path)
                    else:
                        logger.warning(f"Unsupported file type: {file_ext}")
                        continue

                    files_analysis.append(analysis)
                except Exception as e:
                    logger.error(f"Failed to analyze {file_path}: {e}")
                    continue

            if not files_analysis:
                logger.error("No files successfully analyzed")
                return self._generate_fallback_analysis(state, "EDA analysis failed")

            # Step 3: Generate comprehensive EDA report
            eda_report = await eda_analyzer.generate_eda_report(files_analysis)

            logger.info(f"EDA Complete: Domain={eda_report.get('domain')}, "
                       f"Data Quality={eda_report.get('overall_data_quality'):.2f}")

            # Step 4: Load tech stack knowledge base
            tech_stack_yaml_path = Path(__file__).parent.parent.parent / "config" / "tech_stack_patterns.yaml"

            with open(tech_stack_yaml_path, 'r') as f:
                tech_stack_kb = yaml.safe_load(f)

            # Step 5: Map detected data types to AI/ML tools
            detected_data_types = eda_report.get("detected_data_types", [])
            recommended_tools = self._map_data_types_to_tools(detected_data_types, tech_stack_kb)

            # Step 6: Determine complexity based on EDA insights
            complexity_rating, effort_mult, rate_mult = self._determine_complexity_from_eda(eda_report)

            logger.info(f"Complexity: {complexity_rating}, Effort: {effort_mult}x, Rate: {rate_mult}x")

            # Step 7: Build enhanced complexity analysis
            enhanced_analysis = {
                "overall_rating": complexity_rating,
                "confidence_score": eda_report.get("confidence_score", 0.8),
                "impact_on_estimation": {
                    "effort_multiplier": effort_mult,
                    "rate_multiplier": rate_mult,
                    "skill_requirements": {
                        "minimum_level": "Senior" if complexity_rating == "High" else "Mid-level",
                        "specialized_skills": self._extract_required_skills(eda_report, recommended_tools)
                    },
                    "recommended_teams": self._recommend_teams_from_eda(eda_report)
                },
                "reasoning": self._generate_reasoning(eda_report, recommended_tools),

                # NEW: Include full EDA report
                "eda_report": eda_report,

                # NEW: Include recommended tech stack
                "recommended_tech_stack": recommended_tools
            }

            logger.info(f"Agent 1.1 complete with EDA report and tech stack recommendations")

            return {
                **state,
                "complexity_analysis": enhanced_analysis
            }

        except Exception as e:
            logger.error(f"Sample Complexity Analyzer with EDA failed: {str(e)}", exc_info=True)
            return self._generate_fallback_analysis(state, str(e))

    # ========================================================================
    # AGENT 2: TEAM PLANNER
    # ========================================================================

    async def debate_coordinator(self, state: ProjectEstimatorState) -> Dict[str, Any]:
        """
        Agent 1.2: Debate Coordinator - Validates alignment between scope and data.

        Uses 1-2 LLM calls to achieve simple consensus without debate overhead.

        Input:
            - user_prompt (original project scope)
            - requirements (from Agent 1)
            - complexity_analysis (from Agent 1.1)

        Output:
            - consensus_analysis: Alignment validation result
        """
        logger.info("Agent 1.2: Debate Coordinator - Validating scope/data alignment")

        try:
            user_prompt = state.get("user_prompt", "")
            requirements = state.get("requirements", {})
            complexity_analysis = state.get("complexity_analysis", {})
            eda_report = complexity_analysis.get("eda_report", {})

            # Check if we have sample data to validate against
            if not eda_report or eda_report.get("total_files_analyzed", 0) == 0:
                logger.info("No sample files to validate - skipping alignment check")
                consensus_analysis = {
                    "alignment_score": 100,
                    "status": "ALIGNED",
                    "issues": [],
                    "recommendation": "No sample files provided - proceeding based on scope alone",
                    "requires_clarification": False
                }
                return {
                    **state,
                    "consensus_analysis": consensus_analysis
                }

            # Single LLM call for alignment validation
            prompt = f"""You are validating alignment between project scope and uploaded sample data.

**PROJECT SCOPE** (from user):
{user_prompt[:1500]}

**REQUIREMENTS ANALYSIS** (from Agent 1):
- Technical Scope: {json.dumps(requirements.get('technical_scope', {}), indent=2)[:800]}
- Functional Requirements: {requirements.get('functional_requirements', [])[:3]}

**SAMPLE DATA ANALYSIS** (from Agent 1.1):
- Files analyzed: {eda_report.get('total_files_analyzed', 0)}
- Data types detected: {', '.join(eda_report.get('detected_data_types', []))}
- Domain: {eda_report.get('domain', 'Unknown')}
- Data quality: {eda_report.get('overall_data_quality', 0):.1%}
- Data volume: {eda_report.get('total_data_volume_mb', 0):.1f} MB

**YOUR TASK**: Validate if the uploaded sample data aligns with the project scope.

**VALIDATION CRITERIA**:
1. **Data Type Match**: Do the detected data types (Excel, PDFs, images) match what the scope describes?
2. **Domain Match**: Does the detected domain match the project's intended domain?
3. **Completeness**: Is the sample data representative of what the project needs?

**RESPOND IN JSON FORMAT**:
{{
  "alignment_score": <0-100, where 100 = perfect alignment>,
  "status": "<ALIGNED or MISALIGNED>",
  "issues": [<list any misalignment issues, empty array if none>],
  "recommendation": "<brief recommendation in 1-2 sentences>",
  "requires_clarification": <true if user needs to provide better samples, false otherwise>
}}

**SCORING GUIDE**:
- 90-100: Perfect alignment, proceed confidently
- 70-89: Good alignment with minor gaps
- 50-69: Moderate misalignment, some issues
- <50: Significant misalignment, clarification needed"""

            response = await self.llm_service.generate(
                prompt=prompt,
                model_id="gpt-4",
                temperature=0.2,
                max_tokens=500
            )

            response_text = response.get("content", "{}")

            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                consensus_analysis = json.loads(json_match.group(0))
            else:
                # Fallback if JSON extraction fails
                logger.warning("Failed to parse LLM response as JSON, using fallback")
                consensus_analysis = {
                    "alignment_score": 75,
                    "status": "ALIGNED",
                    "issues": ["Could not parse LLM response"],
                    "recommendation": "Proceeding with moderate confidence based on available data",
                    "requires_clarification": False
                }

            logger.info(f"Consensus: {consensus_analysis.get('status')} (score: {consensus_analysis.get('alignment_score')}%)")

            # If alignment is low (<50), optionally make a second LLM call for detailed analysis
            if consensus_analysis.get("alignment_score", 100) < 50 and consensus_analysis.get("requires_clarification", False):
                logger.info("Low alignment score - requesting detailed analysis (2nd LLM call)")

                clarification_prompt = f"""The initial alignment validation scored {consensus_analysis['alignment_score']}/100.

**ISSUES IDENTIFIED**:
{json.dumps(consensus_analysis.get('issues', []), indent=2)}

**YOUR TASK**: Provide specific recommendations to improve alignment.

**RESPOND IN JSON**:
{{
  "specific_actions": [<list of 2-3 specific actions user should take>],
  "alternative_approach": "<suggest alternative if sample data is fundamentally mismatched>"
}}"""

                clarification_response = await self.llm_service.generate(
                    prompt=clarification_prompt,
                    model_id="gpt-4",
                    temperature=0.3,
                    max_tokens=300
                )

                clarification_text = clarification_response.get("content", "{}")
                clarification_match = re.search(r'\{.*\}', clarification_text, re.DOTALL)
                if clarification_match:
                    clarification_data = json.loads(clarification_match.group(0))
                    consensus_analysis["clarification"] = clarification_data
                    logger.info("Added detailed clarification to consensus_analysis")

            return {
                **state,
                "consensus_analysis": consensus_analysis
            }

        except Exception as e:
            logger.error(f"Debate Coordinator failed: {str(e)}", exc_info=True)
            # Fallback: proceed with moderate confidence
            fallback_analysis = {
                "alignment_score": 70,
                "status": "ALIGNED",
                "issues": [f"Validation error: {str(e)}"],
                "recommendation": "Proceeding with moderate confidence - validation encountered error",
                "requires_clarification": False
            }
            state["errors"].append(f"Agent 1.2 (Debate Coordinator): {str(e)}")
            return {
                **state,
                "consensus_analysis": fallback_analysis
            }

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
**YOU ARE AN EXPERT AI SOLUTIONS ARCHITECT** with deep expertise in project scoping, team structure, and AI/ML solutions.

**YOUR MISSION**: Based on the analyzed requirements and tech stack, determine which engineering teams are ACTUALLY NEEDED.

---

**CONTEXT HIERARCHY - YOU MUST FOLLOW THIS ORDER**:

1. **PROJECT REQUIREMENTS** (from Agent 1 - Analyst):
{json.dumps(requirements, indent=2)}

2. **Project Type**: {project_type}

3. **Complexity Analysis** (from Agent 1.1 - Sample Complexity Analyzer):
{json.dumps(state.get("complexity_analysis", {}), indent=2) if state.get("complexity_analysis") else "No sample files analyzed"}

4. **Historical Team Patterns** (for format/style reference):
{cost_patterns}

---

**CRITICAL INSTRUCTIONS - CONTEXT-DRIVEN TEAM SELECTION**:

**STEP 1: Analyze the Tech Stack from Requirements**
Look at requirements["technical_scope"]["technology_requirements"]:
- What technologies are explicitly listed as NEEDED?
- Does it mention scraping? → Consider Scraping team
- Does it mention ML/AI? → Consider ML Engineering team
- Does it mention real-time systems? → Backend + Infrastructure teams critical
- Does it mention document processing? → May need specialized team

**STEP 2: Map Tech Stack → Teams**
Based on what YOU SEE in the technical requirements above:

---

**NOW, YOUR CRITICAL INSTRUCTIONS**:

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

4. **PROJECT TYPE GUIDANCE**:
   - **POC**: 2-3 core teams only (focus on MVP)
   - **Staff Augmentation**: Teams based on requested skills
   - **Full Service**: 3-6 teams (include DevOps, QA for production readiness)

**REMEMBER**: Quality over quantity. 3 highly relevant teams >> 7 generic teams.

Return ONLY a valid JSON object with structure:
{{
  "teams": [
    {{
      "team_name": "Backend Engineering",
      "responsibilities": ["Build REST API for project management", "Implement real-time progress tracking", "Design database schema for construction data"],
      "allocation_percentage": 70,
      "rationale": "Project requires robust backend API for managing construction projects and real-time updates"
    }}
  ],
  "total_teams": 3
}}
"""

            response = await self.llm_service.generate(
                prompt=prompt,
                model_id="gpt-4",
                temperature=0.4,
                max_tokens=2000  # Increase to allow complete team plan JSON
            )

            json_text = extract_json_from_response(response.get("content", "{}"))
            logger.info(f"Team Planner extracted JSON (first 500 chars): {json_text[:500]}")

            team_plan = json.loads(json_text)

            return {
                **state,
                "team_plan": team_plan
            }

        except json.JSONDecodeError as e:
            logger.error(f"Team Planner JSON parsing failed: {str(e)}")
            logger.error(f"Malformed JSON: {json_text if 'json_text' in locals() else 'N/A'}")

            # Fallback: create a default team plan
            logger.warning("Using fallback team plan")
            fallback_team_plan = {
                "teams": [
                    {
                        "team_name": "Development Team",
                        "responsibilities": ["Core development", "Feature implementation"],
                        "allocation_percentage": 100,
                        "rationale": "Default team (LLM response was malformed)"
                    }
                ],
                "total_teams": 1
            }

            state["team_plan"] = fallback_team_plan
            state["errors"].append(f"Team Planner: JSON parsing error, using fallback")
            return state

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
                    project_type=project_type,
                    state=state  # Pass state to access complexity_analysis from Agent 1.1
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
        project_type: str,
        state: ProjectEstimatorState  # Add state parameter to access complexity_analysis
    ) -> List[Dict[str, Any]]:
        """Generate specific tasks for a single team."""

        # Get complexity analysis from Agent 1.1
        complexity_analysis = state.get("complexity_analysis", {})
        effort_multiplier = complexity_analysis.get("impact_on_estimation", {}).get("effort_multiplier", 1.0)

        # Log that we're applying the complexity multiplier
        logger.info(f"Agent 3: Task Generator for {team_name} - Applying effort multiplier: {effort_multiplier}x")

        prompt = f"""
**YOU ARE AN EXPERT AI SOLUTIONS ARCHITECT** breaking down the {team_name}'s work for this specific project.

**YOUR MISSION**: Generate ONLY the tasks that are DIRECTLY NEEDED to solve the problem, guided by the context hierarchy.

---

**CONTEXT HIERARCHY - FOLLOW THIS ORDER**:

**1. PROJECT SCOPE** (Original Problem Statement):
{json.dumps(requirements.get("project_goal", ""), indent=2)}

**2. KEY FEATURES TO IMPLEMENT**:
{json.dumps(requirements.get("key_features", []), indent=2)}

**3. TECH STACK REQUIREMENTS** (from requirements analysis):
{json.dumps(requirements.get("technical_scope", {}), indent=2)}

**4. DATA COMPLEXITY ASSESSMENT** (calibrates effort):
{complexity}

**4.5. COMPLEXITY MULTIPLIER GUIDANCE** (from Agent 1.1 - Sample Complexity Analyzer):
Based on sample file analysis, apply a **{effort_multiplier}x complexity multiplier** to effort estimates.

- Low complexity (1.0x): Standard effort estimates
- Medium complexity (1.3x): 30% more effort than standard
- High complexity (1.8x): 80% more effort than standard

**IMPORTANT**: When estimating task hours, factor in this **{effort_multiplier}x** adjustment to the base estimates.
For example, if a standard task would take 20 hours, with a 1.3x multiplier it should be estimated as 26 hours.

**5. THIS TEAM'S ROLE**:
- **Team**: {team_name}
- **Team Number**: {team_number}
- **Allocation**: {allocation}% of team capacity
- **Responsibilities**:
{json.dumps(responsibilities, indent=2)}

**6. PROJECT TYPE**: {project_type}

**7. HISTORICAL TASK PATTERNS** (for format/style reference):
{cost_patterns}

---

**YOUR TASK GENERATION APPROACH**:

**STEP 1: Review Project Scope (context #1)**
- What is the SPECIFIC problem being solved?

**STEP 2: Review Key Features (context #2)**
- What features must THIS team implement?

**STEP 3: Check Tech Stack (context #3)**
- What technologies are ACTUALLY needed (already determined by requirements analysis)?
- Only generate tasks for technologies that are IN the tech stack

**STEP 4: Calibrate with Complexity (context #4)**
- Simple data → smaller effort estimates
- Complex data → larger effort estimates

**STEP 5: Map to Team Responsibilities (context #5)**
- Generate tasks that align with THIS team's specific responsibilities

---

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

3. **TASK GENERATION (5-10 tasks per team)**:
   - **Task Numbering**: {team_number}.1, {team_number}.2, etc.
   - **Task Name**: Specific, actionable (8-15 words)
   - **Description**: 2-3 sentences explaining WHAT, WHY, and HOW for THIS project
   - **Effort Hours**: Realistic estimates
     * Simple: 4-16 hours
     * Medium: 16-40 hours
     * Complex: 40-80 hours
   - **Category**: Planning & Design | Development | Configuration | Testing & QA | Deployment | Documentation
   - **Complexity**: Easy | Medium | Hard

4. **PROJECT TYPE GUIDANCE**:
   - **POC**: 5-7 tasks focused on MVP/proof of concept
   - **Staff Augmentation**: Tasks matching requested work scope
   - **Full Service**: 8-10 tasks covering full lifecycle (design → deployment)

**REMEMBER**: Every task should be justifiable by pointing to a specific requirement in the Project Scope. NO generic boilerplate.

Return ONLY a valid JSON object:
{{
  "tasks": [
    {{
      "task_number": "{team_number}.1",
      "task_name": "Design database schema for construction project management with progress tracking",
      "description": "Create PostgreSQL schema with tables for Projects, Tasks, Resources, Progress Logs, and Team Members. Include relationships for real-time progress tracking and multi-project management. Design indexes for efficient queries on project timelines.",
      "effort_hours": 24,
      "category": "Planning & Design",
      "complexity": "Medium",
      "dependencies": []
    }}
  ]
}}
"""

        response = await self.llm_service.generate(
            prompt=prompt,
            model_id="gpt-4",
            temperature=0.5,
            max_tokens=2500  # Increased to prevent truncation
        )

        try:
            json_text = extract_json_from_response(response.get("content", "{}"))
            logger.info(f"Task Generator for {team_name} extracted JSON (first 300 chars): {json_text[:300]}")
            result = json.loads(json_text)
            return result.get("tasks", [])
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse tasks for {team_name}: {str(e)}")
            logger.error(f"Malformed JSON: {json_text if 'json_text' in locals() else 'N/A'}")
            return []

    # ========================================================================
    # AGENT 3.5: VALIDATOR (META-VALIDATION LAYER)
    # ========================================================================

    async def validator_agent(self, state: ProjectEstimatorState) -> Dict[str, Any]:
        """
        Agent 3.5: META-VALIDATOR - Senior Architect Reviewer

        Acts as a "quality gate" to ensure all generated outputs (teams, tasks, tech stack)
        are truly aligned with the project scope. This is like having a senior architect
        review the work before proceeding.

        Validates:
            - Are the selected teams ACTUALLY needed for this project?
            - Are the tasks contextual and aligned with project scope?
            - Is the tech stack justified by the requirements?
            - Any generic/boilerplate content that should be removed?

        Output:
            - validation_report: Issues found and corrections made
            - Updated teams/tasks if misalignments detected
        """
        logger.info("Agent 3.5: Validator - Performing meta-validation of outputs")

        try:
            user_prompt = state["user_prompt"]
            requirements = state["requirements"]
            team_plan = state["team_plan"]
            tasks_by_team = state["tasks_by_team"]

            prompt = f"""
**YOU ARE A SENIOR AI SOLUTIONS ARCHITECT** performing a final quality review before approving the project plan.

**YOUR MISSION**: Validate that all generated outputs (teams, tasks, tech stack) are TRULY ALIGNED with the project scope. Flag any misalignments, generic content, or unnecessary elements.

---

**CONTEXT FOR VALIDATION**:

**1. ORIGINAL PROJECT SCOPE** (What the user actually needs):
{user_prompt}

**2. EXTRACTED REQUIREMENTS** (Agent 1's analysis):
{json.dumps(requirements, indent=2)}

**3. PROPOSED TEAMS** (Agent 2's selection):
{json.dumps(team_plan, indent=2)}

**4. GENERATED TASKS** (Agent 3's breakdown):
{json.dumps(tasks_by_team, indent=2)}

---

**YOUR VALIDATION CHECKLIST**:

**STEP 1: Validate Teams Against Scope**
For each team in the proposed teams:
- Question: Is this team ACTUALLY needed based on the project scope?
- Check: Does the project scope mention features that require this team?
- Examples:
  * Scraping Team → ONLY if scope mentions "web scraping", "data collection from websites"
  * ML Engineering Team → ONLY if scope mentions "predictions", "recommendations", "NLP", "classification"
  * Data Engineering Team → ONLY if scope mentions "ETL", "data pipelines", "data warehousing"

**STEP 2: Validate Tasks Against Features**
For each team's tasks:
- Question: Do these tasks DIRECTLY solve a problem mentioned in the project scope?
- Check: Can you point to a specific feature in the scope that justifies this task?
- Red flags:
  * Generic tasks like "Set up environment", "Configure tools" (no project context)
  * Technology mentions not in the tech stack (e.g., scraping tasks when no scraping needed)
  * Boilerplate tasks that could apply to any project

**STEP 3: Validate Tech Stack Consistency**
- Question: Are all mentioned technologies consistent with the requirements?
- Check: Do task descriptions match the tech stack from requirements?
- Example: If requirements say "no ML needed", tasks shouldn't mention "model training"

---

**YOUR OUTPUT** (return as JSON):

Analyze thoroughly and return:

{{
  "validation_status": "PASS" or "ISSUES_FOUND",
  "issues": [
    {{
      "severity": "critical" | "warning" | "info",
      "category": "team_misalignment" | "task_generic" | "tech_stack_mismatch",
      "description": "Clear description of the issue",
      "affected_item": "Team name or task number",
      "reasoning": "Why this is misaligned with project scope"
    }}
  ],
  "recommendations": [
    {{
      "action": "remove_team" | "remove_task" | "modify_task",
      "target": "Specific team/task to modify",
      "justification": "Why this change improves alignment"
    }}
  ],
  "alignment_score": 85,  // 0-100, how well outputs align with scope
  "summary": "1-2 sentence overall assessment"
}}

**IMPORTANT**: Be strict. If something feels generic or unnecessary, flag it. The goal is maximum alignment with the ACTUAL project needs.
"""

            response = await self.llm_service.generate(
                prompt=prompt,
                model_id="gpt-4",
                temperature=0.3,  # Lower temperature for consistent validation
                max_tokens=2000
            )

            json_text = extract_json_from_response(response.get("content", "{}"))
            validation_report = json.loads(json_text)

            logger.info(f"Validation complete: {validation_report.get('validation_status')}")
            logger.info(f"Alignment score: {validation_report.get('alignment_score')}/100")

            if validation_report.get("issues"):
                logger.warning(f"Validation found {len(validation_report['issues'])} issues")
                for issue in validation_report["issues"]:
                    logger.warning(f"  - [{issue['severity']}] {issue['description']}")

            return {
                **state,
                "validation_report": validation_report
            }

        except Exception as e:
            logger.error(f"Validator agent failed: {str(e)}", exc_info=True)
            # Don't block workflow on validation errors, but log them
            return {
                **state,
                "validation_report": {
                    "validation_status": "ERROR",
                    "issues": [],
                    "alignment_score": 0,
                    "summary": f"Validation error: {str(e)}"
                }
            }

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
                model_id="gpt-4",
                temperature=0.4,
                max_tokens=3000  # Increased to prevent truncation
            )

            json_text = extract_json_from_response(response.get("content", "{}"))
            logger.info(f"Workflow Agent extracted JSON (first 500 chars): {json_text[:500]}")

            try:
                workflow = json.loads(json_text)
                return {
                    **state,
                    "project_workflow": workflow
                }
            except json.JSONDecodeError as e:
                logger.error(f"Workflow Agent JSON parsing failed: {str(e)}")
                logger.error(f"Malformed JSON: {json_text if 'json_text' in locals() else 'N/A'}")

                # Fallback: create a default workflow
                logger.warning("Using fallback workflow")
                project_type = state.get("project_type", "Full Service")

                # Estimate duration based on project type
                duration_map = {
                    "POC": 6,
                    "Staff Augmentation": 12,
                    "Full Service": 14
                }
                total_weeks = duration_map.get(project_type, 12)

                fallback_workflow = {
                    "workflow": {
                        "phases": [
                            {
                                "phase_number": 1,
                                "phase_name": "Planning & Setup",
                                "duration_weeks": max(2, total_weeks // 4),
                                "tasks": [],
                                "deliverables": ["Project plan", "Technical architecture", "Environment setup"],
                                "dependencies": []
                            },
                            {
                                "phase_number": 2,
                                "phase_name": "Development",
                                "duration_weeks": max(4, total_weeks // 2),
                                "tasks": [],
                                "deliverables": ["Core features", "API implementation", "Database schema"],
                                "dependencies": [1]
                            },
                            {
                                "phase_number": 3,
                                "phase_name": "Testing & Deployment",
                                "duration_weeks": max(2, total_weeks // 4),
                                "tasks": [],
                                "deliverables": ["Test results", "Production deployment", "Documentation"],
                                "dependencies": [2]
                            }
                        ],
                        "total_duration_weeks": total_weeks,
                        "milestones": [
                            {"name": "Kickoff", "week": 0},
                            {"name": "Design Complete", "week": total_weeks // 4},
                            {"name": "Development Complete", "week": total_weeks * 3 // 4},
                            {"name": "Go-Live", "week": total_weeks}
                        ]
                    }
                }

                state["project_workflow"] = fallback_workflow
                state["errors"].append(f"Workflow Agent: JSON parsing error, using fallback")
                return state

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
                    scenario=scenario,
                    complexity_analysis=state.get("complexity_analysis", {})
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
        scenario: str,
        complexity_analysis: Dict[str, Any] = None
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
            model_id="gpt-4",
            temperature=0.3
        )

        try:
            json_text = extract_json_from_response(response.get("content", "{}"))
            result = json.loads(json_text)
            task_rates = result.get("task_rates", [])

            # Get complexity analysis from Agent 1.1 to apply rate multiplier
            complexity_analysis = complexity_analysis or {}
            rate_multiplier = complexity_analysis.get("impact_on_estimation", {}).get("rate_multiplier", 1.0)

            # Log that we're applying the rate multiplier
            logger.info(f"Agent 5: Rate Assignment for {team_name} - Applying rate multiplier: {rate_multiplier}x")

            # Calculate costs with rate multiplier applied
            tasks_with_costs = []
            total_hours = 0
            total_cost = 0

            for i, task in enumerate(tasks):
                task_rate_info = task_rates[i] if i < len(task_rates) else {}
                rate_category = task_rate_info.get("rate_category", "development_rate")
                base_rate_value = rate_config.get(rate_category, 30)

                # Apply complexity rate multiplier to the base rate
                rate_value = base_rate_value * rate_multiplier

                effort_hours = task.get("effort_hours", 20)
                task_cost = effort_hours * rate_value

                tasks_with_costs.append({
                    **task,
                    "rate_category": rate_category,
                    "rate_value": rate_value,  # This now includes the multiplier
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

            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

            # Use persistent directory (Docker volume mounted at /app)
            import os
            output_dir = "/app/uploads/project_estimator"
            os.makedirs(output_dir, exist_ok=True)

            brd_path = f"{output_dir}/BRD_{timestamp}.docx"
            excel_path = f"{output_dir}/CostEstimate_{timestamp}.xlsx"

            # Create comprehensive BRD Word document
            from docx import Document
            from docx.shared import Pt, Inches, RGBColor
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            from openpyxl import Workbook

            # Create BRD Word Document
            doc = Document()

            # Title Page
            title = doc.add_heading('Business Requirements Document', 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER

            subtitle = doc.add_paragraph(state.get("user_prompt", "Project Estimation")[:200])
            subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER

            info = doc.add_paragraph()
            info.add_run(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n").bold = True
            info.add_run(f"Project Type: {state.get('project_type', 'N/A')}\n").bold = True
            info.add_run(f"Scenario: {state.get('scenario', 'baseline')}").bold = True
            info.alignment = WD_ALIGN_PARAGRAPH.CENTER

            doc.add_page_break()

            # Executive Summary
            doc.add_heading('1. Executive Summary', 1)
            requirements = state.get("requirements", {})
            doc.add_paragraph(requirements.get("project_goal", "Project goals to be defined."))

            # Objectives
            doc.add_heading('2. Project Objectives', 1)
            key_features = requirements.get("key_features", [])
            if key_features:
                for feature in key_features:
                    doc.add_paragraph(feature, style='List Bullet')
            else:
                doc.add_paragraph("Project objectives to be defined.")

            # Complexity Analysis Section (from Agent 1.1)
            doc.add_heading('2.5 Sample Complexity Analysis', 1)
            complexity_analysis = state.get("complexity_analysis", {})

            if complexity_analysis and complexity_analysis.get("overall_rating"):
                # Overall Rating
                p_rating = doc.add_paragraph()
                p_rating.add_run("Overall Complexity Rating: ").bold = True
                p_rating.add_run(complexity_analysis.get("overall_rating", "N/A"))

                # Confidence Score
                confidence = complexity_analysis.get("confidence_score", 0)
                p_conf = doc.add_paragraph()
                p_conf.add_run("Confidence Score: ").bold = True
                p_conf.add_run(f"{confidence:.1%}")

                doc.add_paragraph()  # Spacing

                # Impact on Estimation
                impact = complexity_analysis.get("impact_on_estimation", {})
                doc.add_paragraph("Impact on Estimation:", style='Heading 2')

                # Effort Multiplier
                effort_mult = impact.get("effort_multiplier", 1.0)
                p_effort = doc.add_paragraph()
                p_effort.add_run("Effort Multiplier: ").bold = True
                p_effort.add_run(f"{effort_mult}x")
                p_effort.add_run(" - Applied to task hour estimates")

                # Rate Multiplier
                rate_mult = impact.get("rate_multiplier", 1.0)
                p_rate = doc.add_paragraph()
                p_rate.add_run("Rate Multiplier: ").bold = True
                p_rate.add_run(f"{rate_mult}x")
                p_rate.add_run(" - Applied to billing rates")

                doc.add_paragraph()  # Spacing

                # Skill Requirements
                skill_req = impact.get("skill_requirements", {})
                p_skill = doc.add_paragraph()
                p_skill.add_run("Minimum Skill Level Required: ").bold = True
                p_skill.add_run(skill_req.get("minimum_level", "Senior"))

                specialized_skills = skill_req.get("specialized_skills", [])
                if specialized_skills:
                    p_spec = doc.add_paragraph()
                    p_spec.add_run("Specialized Skills Required:").bold = True
                    for skill in specialized_skills:
                        doc.add_paragraph(skill, style='List Bullet 2')

                # Recommended Teams
                recommended_teams = impact.get("recommended_teams", [])
                if recommended_teams:
                    doc.add_paragraph()
                    p_teams = doc.add_paragraph()
                    p_teams.add_run("Recommended Specialized Teams:").bold = True
                    for team in recommended_teams:
                        doc.add_paragraph(team, style='List Bullet 2')

                doc.add_paragraph()  # Spacing

                # Analysis Reasoning
                reasoning = complexity_analysis.get("reasoning", "")
                if reasoning:
                    doc.add_paragraph("Analysis Reasoning:", style='Heading 2')
                    doc.add_paragraph(reasoning)

                # NEW SECTION 2.6: EDA Report Summary
                eda_report = complexity_analysis.get("eda_report")
                if eda_report:
                    doc.add_page_break()
                    doc.add_heading('2.6 Exploratory Data Analysis (EDA) Report', 1)

                    # Files Analyzed
                    total_files = eda_report.get("total_files_analyzed", 0)
                    p_files = doc.add_paragraph()
                    p_files.add_run("Files Analyzed: ").bold = True
                    p_files.add_run(f"{total_files}")

                    # Domain Detected
                    domain = eda_report.get("domain", "Unknown")
                    p_domain = doc.add_paragraph()
                    p_domain.add_run("Domain Detected: ").bold = True
                    p_domain.add_run(domain)

                    # Data Quality
                    data_quality = eda_report.get("overall_data_quality", 0)
                    p_quality = doc.add_paragraph()
                    p_quality.add_run("Overall Data Quality: ").bold = True
                    p_quality.add_run(f"{data_quality:.1%}")

                    # Data Volume
                    data_volume = eda_report.get("total_data_volume_mb", 0)
                    p_volume = doc.add_paragraph()
                    p_volume.add_run("Total Data Volume: ").bold = True
                    p_volume.add_run(f"{data_volume:.2f} MB")

                    # Detected Data Types
                    data_types = eda_report.get("detected_data_types", [])
                    if data_types:
                        doc.add_paragraph("Detected Data Types:", style='Heading 2')
                        for data_type in data_types:
                            doc.add_paragraph(
                                data_type.replace("_", " ").title(),
                                style='List Bullet'
                            )

                    # Key Insights
                    insights = eda_report.get("insights", [])
                    if insights:
                        doc.add_paragraph("Key Insights:", style='Heading 2')
                        for insight in insights:
                            doc.add_paragraph(insight, style='List Bullet')

                    # Detailed File Analysis
                    files_analysis = eda_report.get("files_analysis", [])
                    if files_analysis:
                        doc.add_paragraph("Detailed File Analysis:", style='Heading 2')

                        for idx, file_data in enumerate(files_analysis, 1):
                            file_type = file_data.get("file_type", "Unknown")
                            doc.add_paragraph(f"File {idx}: {file_type.upper()}", style='Heading 3')

                            # Excel-specific details
                            if file_type == "excel":
                                sheets = file_data.get("sheets", 0)
                                rows = file_data.get("total_rows", 0)
                                cols = file_data.get("total_columns", 0)
                                file_quality = file_data.get("overall_data_quality", 0)

                                p_excel = doc.add_paragraph()
                                p_excel.add_run(f"Sheets: {sheets}, Rows: {rows}, Columns: {cols}")
                                p_excel.add_paragraph()
                                p_quality_file = doc.add_paragraph()
                                p_quality_file.add_run("Data Quality: ").bold = True
                                p_quality_file.add_run(f"{file_quality:.1%}")

                                # Statistical summary
                                stats_summary = file_data.get("statistical_summary", [])
                                if stats_summary:
                                    doc.add_paragraph("Statistical Summary:", style='List Bullet')
                                    for stat in stats_summary[:5]:  # Top 5
                                        doc.add_paragraph(stat, style='List Bullet 2')

                            # PDF-specific details
                            elif file_type == "pdf":
                                pages = file_data.get("total_pages", 0)
                                doc_type = file_data.get("document_type", "Unknown")
                                has_images = file_data.get("has_images", False)

                                p_pdf = doc.add_paragraph()
                                p_pdf.add_run(f"Pages: {pages}, Type: {doc_type}")
                                if has_images:
                                    p_pdf.add_paragraph()
                                    p_pdf.add_run("Contains Images/Diagrams: Yes")

                            # Image-specific details
                            elif file_type == "image":
                                format_type = file_data.get("format", "Unknown")
                                size_mb = file_data.get("file_size_mb", 0)

                                p_img = doc.add_paragraph()
                                p_img.add_run(f"Format: {format_type}, Size: {size_mb:.2f} MB")

                                vision_analysis = file_data.get("vision_analysis", "")
                                if vision_analysis:
                                    doc.add_paragraph("Vision Analysis:", style='List Bullet')
                                    doc.add_paragraph(vision_analysis, style='List Bullet 2')

                            # File-specific insights
                            file_insights = file_data.get("insights", [])
                            if file_insights:
                                doc.add_paragraph("Insights:", style='List Bullet')
                                for file_insight in file_insights[:3]:  # Top 3
                                    doc.add_paragraph(file_insight, style='List Bullet 2')

                # NEW SECTION 2.7: Recommended AI/ML Tech Stack
                tech_stack = complexity_analysis.get("recommended_tech_stack")
                if tech_stack:
                    doc.add_page_break()
                    doc.add_heading('2.7 Recommended AI/ML Tech Stack', 1)

                    # Primary Tools by Data Type
                    primary_tools = tech_stack.get("primary_tools", {})
                    if primary_tools:
                        doc.add_paragraph(
                            "Recommended AI/ML Tools by Data Type:",
                            style='Heading 2'
                        )

                        for data_type, tools_info in primary_tools.items():
                            # Data type heading
                            doc.add_paragraph(
                                data_type.replace("_", " ").title(),
                                style='Heading 3'
                            )

                            # Data Processing Tools
                            data_processing = tools_info.get("data_processing", [])
                            if data_processing:
                                doc.add_paragraph("Data Processing:", style='List Bullet')
                                for tool in data_processing[:5]:  # Top 5
                                    doc.add_paragraph(tool, style='List Bullet 2')

                            # PDF Processing Tools
                            pdf_processing = tools_info.get("pdf_processing", [])
                            if pdf_processing:
                                doc.add_paragraph("PDF Processing:", style='List Bullet')
                                for tool in pdf_processing[:5]:
                                    doc.add_paragraph(tool, style='List Bullet 2')

                            # OCR Tools
                            ocr_tools = tools_info.get("ocr", [])
                            if ocr_tools:
                                doc.add_paragraph("OCR Engines:", style='List Bullet')
                                for tool in ocr_tools[:5]:
                                    doc.add_paragraph(tool, style='List Bullet 2')

                            # Vision Models
                            vision_models = tools_info.get("vision_models", [])
                            if vision_models:
                                doc.add_paragraph("Vision Models:", style='List Bullet')
                                for tool in vision_models[:5]:
                                    doc.add_paragraph(tool, style='List Bullet 2')

                            # Web Scraping Tools
                            web_scraping = tools_info.get("web_scraping", [])
                            if web_scraping:
                                doc.add_paragraph("Web Scraping:", style='List Bullet')
                                for tool in web_scraping[:5]:
                                    doc.add_paragraph(tool, style='List Bullet 2')

                    # ChatBot's Own Tools
                    chatbot_tools = tech_stack.get("chatbot_tools", {})
                    if chatbot_tools:
                        doc.add_page_break()
                        doc.add_paragraph(
                            "ChatBot Platform Capabilities (Recommended for This Project):",
                            style='Heading 2'
                        )

                        # Document Intelligence Tools
                        doc_intelligence = chatbot_tools.get("document_intelligence", [])
                        if doc_intelligence:
                            doc.add_paragraph("Document Intelligence:", style='Heading 3')
                            for tool_info in doc_intelligence:
                                tool_name = tool_info.get("name", "Unknown Tool")
                                description = tool_info.get("description", "")
                                service = tool_info.get("service", "")
                                applicable = tool_info.get("applicable", False)
                                reason = tool_info.get("reason", "")

                                if applicable:
                                    p_tool = doc.add_paragraph()
                                    p_tool.add_run(f"✓ {tool_name}").bold = True
                                    doc.add_paragraph(f"   {description}", style='List Bullet 2')
                                    if service:
                                        doc.add_paragraph(
                                            f"   Service: {service}",
                                            style='List Bullet 2'
                                        )
                                    if reason:
                                        doc.add_paragraph(
                                            f"   Why: {reason}",
                                            style='List Bullet 2'
                                        )

                        # Vision Analysis Tools
                        vision_analysis_tools = chatbot_tools.get("vision_analysis", [])
                        if vision_analysis_tools:
                            doc.add_paragraph("Vision Analysis:", style='Heading 3')
                            for tool_info in vision_analysis_tools:
                                tool_name = tool_info.get("name", "Unknown Tool")
                                description = tool_info.get("description", "")
                                applicable = tool_info.get("applicable", False)
                                reason = tool_info.get("reason", "")

                                if applicable:
                                    p_tool = doc.add_paragraph()
                                    p_tool.add_run(f"✓ {tool_name}").bold = True
                                    doc.add_paragraph(f"   {description}", style='List Bullet 2')
                                    if reason:
                                        doc.add_paragraph(
                                            f"   Why: {reason}",
                                            style='List Bullet 2'
                                        )

                        # Navigation and Extraction Tools
                        nav_extraction = chatbot_tools.get("navigation_and_extraction", [])
                        if nav_extraction:
                            doc.add_paragraph(
                                "Navigation and Extraction:",
                                style='Heading 3'
                            )
                            for tool_info in nav_extraction:
                                tool_name = tool_info.get("name", "Unknown Tool")
                                description = tool_info.get("description", "")
                                applicable = tool_info.get("applicable", False)
                                reason = tool_info.get("reason", "")

                                if applicable:
                                    p_tool = doc.add_paragraph()
                                    p_tool.add_run(f"✓ {tool_name}").bold = True
                                    doc.add_paragraph(f"   {description}", style='List Bullet 2')
                                    if reason:
                                        doc.add_paragraph(
                                            f"   Why: {reason}",
                                            style='List Bullet 2'
                                        )

                    # Use Cases
                    use_cases = tech_stack.get("use_cases", [])
                    if use_cases:
                        doc.add_paragraph(
                            "Recommended Use Cases for This Project:",
                            style='Heading 2'
                        )
                        for use_case in use_cases[:10]:  # Top 10 use cases
                            doc.add_paragraph(use_case, style='List Bullet')

            else:
                doc.add_paragraph("No sample files were provided for complexity analysis.")
                doc.add_paragraph("Cost estimates are based on standard effort and rate multipliers (1.0x).")

            # Technical Scope
            doc.add_heading('3. Technical Scope', 1)
            technical_scope = requirements.get("technical_scope", {})
            if technical_scope:
                for key, value in technical_scope.items():
                    p = doc.add_paragraph()
                    p.add_run(f"{key.replace('_', ' ').title()}: ").bold = True
                    if isinstance(value, list):
                        p.add_run(", ".join(str(v) for v in value))
                    else:
                        p.add_run(str(value))
            else:
                doc.add_paragraph("Technical scope to be defined.")

            # Team Structure
            doc.add_heading('4. Team Structure', 1)
            team_plan = state.get("team_plan", {})
            teams = team_plan.get("teams", [])
            if teams:
                table = doc.add_table(rows=1, cols=3)
                table.style = 'Light Grid Accent 1'
                hdr_cells = table.rows[0].cells
                hdr_cells[0].text = 'Team Name'
                hdr_cells[1].text = 'Responsibilities'
                hdr_cells[2].text = 'Allocation'

                for team in teams:
                    row_cells = table.add_row().cells
                    row_cells[0].text = team.get("team_name", "Unknown")
                    responsibilities = team.get("responsibilities", [])
                    row_cells[1].text = ", ".join(responsibilities) if responsibilities else "N/A"
                    row_cells[2].text = f"{team.get('allocation_percentage', 0)}%"
            else:
                doc.add_paragraph("Team structure to be defined.")

            # Project Workflow
            doc.add_heading('5. Project Workflow & Timeline', 1)
            project_workflow = state.get("project_workflow", {})
            workflow = project_workflow.get("workflow", {})
            phases = workflow.get("phases", [])

            if phases:
                doc.add_paragraph(f"Total Duration: {workflow.get('total_duration_weeks', 0)} weeks")
                doc.add_paragraph()

                for phase in phases:
                    phase_heading = doc.add_heading(
                        f"Phase {phase.get('phase_number', '?')}: {phase.get('phase_name', 'Unknown')}",
                        2
                    )
                    doc.add_paragraph(f"Duration: {phase.get('duration_weeks', 0)} weeks")

                    deliverables = phase.get("deliverables", [])
                    if deliverables:
                        doc.add_paragraph("Deliverables:", style='List Bullet')
                        for deliverable in deliverables:
                            doc.add_paragraph(deliverable, style='List Bullet 2')
            else:
                doc.add_paragraph("Project workflow to be defined.")

            # Cost Summary
            doc.add_heading('6. Cost Estimation', 1)
            costs_by_team = state.get("costs_by_team", {})
            summary = costs_by_team.get("summary", {})

            if summary:
                doc.add_paragraph(f"Total Project Cost: ${summary.get('total_cost', 0):,.2f}")
                doc.add_paragraph(f"Total Hours: {summary.get('total_hours', 0):,.0f}")
                doc.add_paragraph(f"Number of Teams: {summary.get('team_count', 0)}")
                doc.add_paragraph()

                # Cost breakdown by team
                doc.add_paragraph("Cost Breakdown by Team:", style='List Bullet')
                for team_name, team_data in costs_by_team.items():
                    if team_name != "summary" and isinstance(team_data, dict):
                        team_name_clean = team_data.get("team_name", team_name)
                        team_cost = team_data.get("total_cost", 0)
                        team_hours = team_data.get("total_hours", 0)
                        doc.add_paragraph(
                            f"{team_name_clean}: ${team_cost:,.2f} ({team_hours:.0f} hours)",
                            style='List Bullet 2'
                        )
            else:
                doc.add_paragraph("Cost estimation to be calculated.")

            # Success Criteria
            doc.add_heading('7. Success Criteria', 1)
            success_criteria = requirements.get("success_criteria", [])
            if success_criteria:
                for criterion in success_criteria:
                    doc.add_paragraph(criterion, style='List Bullet')
            else:
                doc.add_paragraph("Success criteria to be defined.")

            # Milestones
            milestones = workflow.get("milestones", [])
            if milestones:
                doc.add_heading('8. Key Milestones', 1)
                table = doc.add_table(rows=1, cols=2)
                table.style = 'Light Grid Accent 1'
                hdr_cells = table.rows[0].cells
                hdr_cells[0].text = 'Milestone'
                hdr_cells[1].text = 'Week'

                for milestone in milestones:
                    row_cells = table.add_row().cells
                    row_cells[0].text = milestone.get("name", "Unknown")
                    row_cells[1].text = str(milestone.get("week", "?"))

            doc.save(brd_path)

            # Create comprehensive Excel workbook with dynamic team sheets
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

            wb = Workbook()

            # Remove default sheet
            if 'Sheet' in wb.sheetnames:
                wb.remove(wb['Sheet'])

            # Get workflow data
            costs_by_team = state.get("costs_by_team", {})
            summary = costs_by_team.get("summary", {})
            team_plan = state.get("team_plan", {})
            teams = team_plan.get("teams", [])
            project_workflow = state.get("project_workflow", {})
            workflow = project_workflow.get("workflow", {})
            tasks_by_team = state.get("tasks_by_team", {})
            cost_examples_summary = state.get("cost_examples_summary", "")

            # Define styles
            header_font = Font(bold=True, size=12, color="FFFFFF")
            header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            subheader_font = Font(bold=True, size=11)
            subheader_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
            border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )

            # =================================================================
            # SHEET 1: MASTER SUMMARY
            # =================================================================
            ws_summary = wb.create_sheet("Master Summary")

            # Title
            ws_summary['A1'] = "PROJECT COST ESTIMATION - MASTER SUMMARY"
            ws_summary['A1'].font = Font(bold=True, size=14)
            ws_summary.merge_cells('A1:F1')

            # Project Info
            row = 3
            ws_summary[f'A{row}'] = "Project Type:"
            ws_summary[f'B{row}'] = state.get('project_type', 'N/A')
            ws_summary[f'A{row}'].font = subheader_font
            row += 1
            ws_summary[f'A{row}'] = "Scenario:"
            ws_summary[f'B{row}'] = state.get('scenario', 'baseline')
            ws_summary[f'A{row}'].font = subheader_font
            row += 1
            ws_summary[f'A{row}'] = "Generated:"
            ws_summary[f'B{row}'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            ws_summary[f'A{row}'].font = subheader_font
            row += 2

            # Cost Summary (formulas will be added after team rows are populated)
            ws_summary[f'A{row}'] = "COST SUMMARY"
            ws_summary[f'A{row}'].font = Font(bold=True, size=12)
            row += 1

            # Save row numbers for formula references
            total_cost_row = row
            ws_summary[f'A{row}'] = "Total Project Cost:"
            # Formula will be set after team rows are populated
            row += 1

            total_hours_row = row
            ws_summary[f'A{row}'] = "Total Hours:"
            # Formula will be set after team rows are populated
            row += 1

            ws_summary[f'A{row}'] = "Number of Teams:"
            ws_summary[f'B{row}'] = summary.get('team_count', 0)
            row += 2

            # Team Breakdown Table
            ws_summary[f'A{row}'] = "COST BREAKDOWN BY TEAM"
            ws_summary[f'A{row}'].font = Font(bold=True, size=12)
            row += 1

            # Table headers
            headers = ['Team Name', 'Total Cost', 'Total Hours', 'Average Rate', 'Allocation %']
            for col, header in enumerate(headers, start=1):
                cell = ws_summary.cell(row, col)
                cell.value = header
                cell.font = header_font
                cell.fill = header_fill
                cell.border = border
                cell.alignment = Alignment(horizontal='center')
            row += 1

            # Team data rows - Track row numbers for SUM formulas
            first_team_row = row
            for team_name, team_data in costs_by_team.items():
                if team_name != "summary" and isinstance(team_data, dict):
                    ws_summary.cell(row, 1, team_data.get("team_name", team_name))
                    ws_summary.cell(row, 2, team_data.get("total_cost", 0)).number_format = '$#,##0.00'
                    ws_summary.cell(row, 3, team_data.get("total_hours", 0)).number_format = '#,##0'

                    total_hours = team_data.get("total_hours", 0)
                    total_cost = team_data.get("total_cost", 0)
                    avg_rate = total_cost / total_hours if total_hours > 0 else 0
                    ws_summary.cell(row, 4, avg_rate).number_format = '$#,##0.00'

                    # Find allocation from team_plan
                    allocation = 0
                    for team in teams:
                        if team.get("team_name") == team_data.get("team_name"):
                            allocation = team.get("allocation_percentage", 0)
                            break
                    ws_summary.cell(row, 5, allocation / 100).number_format = '0%'

                    # Apply borders
                    for col in range(1, 6):
                        ws_summary.cell(row, col).border = border
                    row += 1
            last_team_row = row - 1  # Last team row (row was incremented after last team)

            # Now set the SUM formulas for total cost and hours (using formula instead of hardcoded values)
            if first_team_row <= last_team_row:
                # Total Project Cost formula
                ws_summary[f'B{total_cost_row}'] = f'=SUM(B{first_team_row}:B{last_team_row})'
                ws_summary[f'B{total_cost_row}'].number_format = '$#,##0.00'
                ws_summary[f'B{total_cost_row}'].font = Font(bold=True, size=11)

                # Total Hours formula
                ws_summary[f'B{total_hours_row}'] = f'=SUM(C{first_team_row}:C{last_team_row})'
                ws_summary[f'B{total_hours_row}'].number_format = '#,##0'
            else:
                # Fallback if no teams (shouldn't happen, but safe handling)
                ws_summary[f'B{total_cost_row}'] = summary.get('total_cost', 0)
                ws_summary[f'B{total_cost_row}'].number_format = '$#,##0.00'
                ws_summary[f'B{total_cost_row}'].font = Font(bold=True, size=11)

                ws_summary[f'B{total_hours_row}'] = summary.get('total_hours', 0)
                ws_summary[f'B{total_hours_row}'].number_format = '#,##0'

            # Column widths
            ws_summary.column_dimensions['A'].width = 30
            ws_summary.column_dimensions['B'].width = 15
            ws_summary.column_dimensions['C'].width = 15
            ws_summary.column_dimensions['D'].width = 15
            ws_summary.column_dimensions['E'].width = 15

            # =================================================================
            # SHEET 2: PROJECT WORKFLOW
            # =================================================================
            ws_workflow = wb.create_sheet("Project Workflow")

            # Title
            ws_workflow['A1'] = "PROJECT WORKFLOW & TIMELINE"
            ws_workflow['A1'].font = Font(bold=True, size=14)
            ws_workflow.merge_cells('A1:E1')

            row = 3
            ws_workflow[f'A{row}'] = "Total Duration:"
            ws_workflow[f'B{row}'] = f"{workflow.get('total_duration_weeks', 0)} weeks"
            ws_workflow[f'A{row}'].font = subheader_font
            row += 2

            # Phases
            phases = workflow.get("phases", [])
            if phases:
                ws_workflow[f'A{row}'] = "EXECUTION PHASES"
                ws_workflow[f'A{row}'].font = Font(bold=True, size=12)
                row += 1

                for phase in phases:
                    # Phase header
                    phase_title = f"Phase {phase.get('phase_number', '?')}: {phase.get('phase_name', 'Unknown')}"
                    ws_workflow[f'A{row}'] = phase_title
                    ws_workflow[f'A{row}'].font = Font(bold=True, size=11, color="4472C4")
                    row += 1

                    ws_workflow[f'A{row}'] = "Duration:"
                    ws_workflow[f'B{row}'] = f"{phase.get('duration_weeks', 0)} weeks"
                    row += 1

                    # Deliverables
                    deliverables = phase.get("deliverables", [])
                    if deliverables:
                        ws_workflow[f'A{row}'] = "Deliverables:"
                        ws_workflow[f'A{row}'].font = subheader_font
                        row += 1
                        for deliverable in deliverables:
                            ws_workflow[f'B{row}'] = f"• {deliverable}"
                            row += 1

                    # Dependencies
                    dependencies = phase.get("dependencies", [])
                    if dependencies:
                        ws_workflow[f'A{row}'] = "Dependencies:"
                        ws_workflow[f'B{row}'] = f"Phase(s) {', '.join(map(str, dependencies))}"
                        row += 1

                    row += 1

            row += 1

            # Milestones
            milestones = workflow.get("milestones", [])
            if milestones:
                ws_workflow[f'A{row}'] = "KEY MILESTONES"
                ws_workflow[f'A{row}'].font = Font(bold=True, size=12)
                row += 1

                # Table headers
                ws_workflow.cell(row, 1, "Milestone").font = header_font
                ws_workflow.cell(row, 1).fill = header_fill
                ws_workflow.cell(row, 1).border = border
                ws_workflow.cell(row, 2, "Week").font = header_font
                ws_workflow.cell(row, 2).fill = header_fill
                ws_workflow.cell(row, 2).border = border
                row += 1

                for milestone in milestones:
                    ws_workflow.cell(row, 1, milestone.get("name", "Unknown")).border = border
                    ws_workflow.cell(row, 2, milestone.get("week", "?")).border = border
                    row += 1

            ws_workflow.column_dimensions['A'].width = 30
            ws_workflow.column_dimensions['B'].width = 40

            # =================================================================
            # DYNAMIC TEAM SHEETS
            # =================================================================
            for team_name, team_data in costs_by_team.items():
                if team_name == "summary" or not isinstance(team_data, dict):
                    continue

                # Sanitize sheet name (max 31 chars, no special chars)
                sheet_name = team_data.get("team_name", team_name)
                sheet_name = sheet_name.replace("/", "-").replace("\\", "-")[:31]

                ws_team = wb.create_sheet(sheet_name)

                # Title
                ws_team['A1'] = f"{sheet_name.upper()} - COST BREAKDOWN"
                ws_team['A1'].font = Font(bold=True, size=14)
                ws_team.merge_cells('A1:F1')

                row = 3

                # Team Summary
                ws_team[f'A{row}'] = "Total Cost:"
                ws_team[f'B{row}'] = team_data.get("total_cost", 0)
                ws_team[f'B{row}'].number_format = '$#,##0.00'
                ws_team[f'B{row}'].font = Font(bold=True)
                row += 1

                ws_team[f'A{row}'] = "Total Hours:"
                ws_team[f'B{row}'] = team_data.get("total_hours", 0)
                ws_team[f'B{row}'].number_format = '#,##0'
                ws_team[f'B{row}'].font = Font(bold=True)
                row += 2

                # Tasks breakdown
                team_tasks = tasks_by_team.get(team_name, [])
                if team_tasks:
                    ws_team[f'A{row}'] = "TASK BREAKDOWN"
                    ws_team[f'A{row}'].font = Font(bold=True, size=12)
                    row += 1

                    # Table headers
                    task_headers = ['Task', 'Phase', 'Effort (hrs)', 'Rate', 'Cost']
                    for col, header in enumerate(task_headers, start=1):
                        cell = ws_team.cell(row, col)
                        cell.value = header
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.border = border
                        cell.alignment = Alignment(horizontal='center')
                    row += 1

                    # Task rows
                    for task in team_tasks:
                        ws_team.cell(row, 1, task.get("task_name", "Unknown Task")).border = border
                        ws_team.cell(row, 2, task.get("phase", "N/A")).border = border

                        effort = task.get("effort_hours", 0)
                        rate = task.get("rate", 0)
                        cost = effort * rate

                        ws_team.cell(row, 3, effort).number_format = '#,##0'
                        ws_team.cell(row, 3).border = border
                        ws_team.cell(row, 4, rate).number_format = '$#,##0.00'
                        ws_team.cell(row, 4).border = border
                        ws_team.cell(row, 5, cost).number_format = '$#,##0.00'
                        ws_team.cell(row, 5).border = border
                        row += 1
                else:
                    ws_team[f'A{row}'] = "No detailed tasks available for this team."
                    row += 1

                # Column widths
                ws_team.column_dimensions['A'].width = 40
                ws_team.column_dimensions['B'].width = 20
                ws_team.column_dimensions['C'].width = 15
                ws_team.column_dimensions['D'].width = 15
                ws_team.column_dimensions['E'].width = 15

            # =================================================================
            # SHEET: SAMPLE DOCUMENT GUIDANCE
            # =================================================================
            if cost_examples_summary and cost_examples_summary != "No cost estimate examples provided.":
                ws_guidance = wb.create_sheet("Sample Guidance")
                ws_guidance['A1'] = "GUIDANCE FROM UPLOADED SAMPLE DOCUMENTS"
                ws_guidance['A1'].font = Font(bold=True, size=14)
                ws_guidance.merge_cells('A1:D1')

                row = 3
                ws_guidance[f'A{row}'] = "This estimation was guided by the patterns extracted from your uploaded sample cost estimate documents:"
                ws_guidance.merge_cells(f'A{row}:D{row}')
                row += 2

                # Split summary into lines and add to sheet
                for line in cost_examples_summary.split('\n'):
                    if line.strip():
                        ws_guidance[f'A{row}'] = line.strip()
                        ws_guidance.merge_cells(f'A{row}:D{row}')
                        row += 1

                ws_guidance.column_dimensions['A'].width = 100

            wb.save(excel_path)

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
    # AGENT 6.5: DOCUMENT VALIDATOR - Final Quality Gate
    # ========================================================================

    async def document_validator_agent(self, state: ProjectEstimatorState) -> Dict[str, Any]:
        """
        Agent 6.5: META-VALIDATOR for Final Documents - Document Quality Assurance

        Validates the generated BRD and Excel cost estimate against the original project scope
        to ensure perfect alignment. This is the FINAL quality gate before output.

        Key Validation Checks:
        1. BRD Content Alignment - Does the BRD content accurately reflect project scope?
        2. Cost Estimate Accuracy - Are costs reasonable and teams aligned with needs?
        3. Technical Consistency - Are tech stack mentions consistent across documents?
        4. Completeness - Are all project requirements addressed?

        If validation fails, can trigger workflow restart with mistake context.

        Input:
            - user_prompt (original project scope)
            - requirements (extracted requirements)
            - brd_path (generated BRD document path)
            - excel_path (generated Excel cost estimate path)
            - team_plan (selected teams)
            - tasks_by_team (generated tasks)
            - validation_history (mistakes from previous iterations)

        Output:
            - document_validation_report: Detailed validation results
            - document_validation_decision: "PASS" or "RESTART_WORKFLOW"
            - updated validation_history: Mistakes to avoid in retry
        """
        logger.info("Agent 6.5: Document Validator - Final quality gate for generated documents")

        try:
            # Extract inputs
            user_prompt = state.get("user_prompt", "")
            requirements = state.get("requirements", {})
            brd_path = state.get("brd_path", "")
            excel_path = state.get("excel_path", "")
            team_plan = state.get("team_plan", {})
            tasks_by_team = state.get("tasks_by_team", {})
            validation_history = state.get("validation_history", [])
            iteration_count = state.get("iteration_count", 0)

            # Read BRD content (first 3000 chars for validation)
            brd_content_sample = ""
            try:
                from docx import Document
                if brd_path and os.path.exists(brd_path):
                    doc = Document(brd_path)
                    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                    brd_content_sample = "\n".join(paragraphs[:50])  # First 50 paragraphs
            except Exception as e:
                logger.warning(f"Could not read BRD for validation: {e}")
                brd_content_sample = "[BRD content not available for validation]"

            # Read Excel summary data
            excel_summary = ""
            try:
                from openpyxl import load_workbook
                if excel_path and os.path.exists(excel_path):
                    wb = load_workbook(excel_path, read_only=True)
                    if "Master Summary" in wb.sheetnames:
                        ws = wb["Master Summary"]
                        rows_data = []
                        for row in list(ws.rows)[:30]:  # First 30 rows
                            row_text = " | ".join([str(cell.value) if cell.value else "" for cell in row])
                            if row_text.strip():
                                rows_data.append(row_text)
                        excel_summary = "\n".join(rows_data)
                    wb.close()
            except Exception as e:
                logger.warning(f"Could not read Excel for validation: {e}")
                excel_summary = "[Excel content not available for validation]"

            # Build validation prompt
            prompt = f"""
You are a SENIOR PROJECT MANAGER reviewing the final project estimation documents.

Your job: Validate that the BRD and Cost Estimate accurately reflect the client's project scope.

**ORIGINAL PROJECT SCOPE** (What the client actually requested):
{user_prompt[:2000]}

**EXTRACTED REQUIREMENTS**:
{json.dumps(requirements, indent=2)[:1500]}

**TEAMS SELECTED**:
{json.dumps([t.get("team_name") for t in team_plan.get("teams", [])], indent=2)}

**BRD DOCUMENT CONTENT** (Sample):
{brd_content_sample[:2000]}

**EXCEL COST ESTIMATE** (Master Summary):
{excel_summary[:1500]}

**TASK SUMMARY** (First 10 tasks):
{json.dumps(dict(list(tasks_by_team.items())[:10]), indent=2)[:1500]}

---

**PREVIOUS MISTAKES TO AVOID** (if any):
{json.dumps(validation_history, indent=2) if validation_history else "No previous mistakes - first iteration"}

---

**YOUR VALIDATION CHECKLIST**:

**STEP 1: Scope Alignment**
- Question: Does the BRD Executive Summary accurately describe the project from the scope?
- Question: Are all key features from the original scope mentioned in the BRD?
- Red Flag: BRD talks about features NOT mentioned in the project scope

**STEP 2: Team Justification**
- Question: Are the selected teams ACTUALLY needed for this specific project?
- Question: Are there teams included that don't align with project requirements?
- Example: If scope says "dashboard for existing data", why include Scraping or ML teams?

**STEP 3: Cost Reasonableness**
- Question: Do the costs seem reasonable for the project complexity?
- Question: Are any teams over/under-allocated compared to project needs?
- Red Flag: Costs that seem inflated or deflated compared to scope complexity

**STEP 4: Technical Consistency**
- Question: Are technologies mentioned in BRD consistent with requirements?
- Question: Do task descriptions match the tech stack defined in requirements?
- Red Flag: BRD mentions Python but tasks reference Java

**STEP 5: Completeness**
- Question: Are all major project objectives addressed in deliverables?
- Question: Are critical features from scope reflected in task breakdown?
- Red Flag: Key feature mentioned in scope but no tasks address it

**STEP 6: Mistake Repetition Check**
- Question: Have we repeated any mistakes from previous iterations?
- Question: Did we address all recommendations from validation_history?

---

**YOUR OUTPUT** (return as JSON):

Analyze CRITICALLY and return:

{{
  "validation_status": "PASS" or "ISSUES_FOUND",
  "decision": "PASS" or "RESTART_WORKFLOW",
  "quality_score": 85,  // 0-100, overall document quality
  "issues": [
    {{
      "severity": "critical" | "major" | "minor",
      "category": "scope_misalignment" | "unnecessary_team" | "missing_feature" | "cost_unreasonable" | "tech_inconsistency" | "repeated_mistake",
      "description": "Clear description of the problem",
      "evidence": "Specific quote or reference from documents showing the issue",
      "impact": "Why this matters / what could go wrong"
    }}
  ],
  "recommendations": [
    {{
      "action": "remove_team" | "add_feature_coverage" | "adjust_costs" | "fix_brd_content" | "align_tech_stack",
      "target": "What specifically needs to be fixed",
      "reason": "Why this fix will improve alignment"
    }}
  ],
  "mistakes_for_history": [
    // NEW mistakes to add to validation_history for next iteration
    {{
      "iteration": {iteration_count + 1},
      "mistake": "Description of what went wrong",
      "correct_approach": "What should be done instead"
    }}
  ],
  "summary": "1-3 sentence assessment of document quality and alignment"
}}

**DECISION CRITERIA**:
- **PASS**: If quality_score >= 80 AND no critical issues
- **RESTART_WORKFLOW**: If quality_score < 80 OR any critical issues found

**BE STRICT**: The client is paying for this. Documents must be accurate and aligned.
If there are CRITICAL misalignments, choose "RESTART_WORKFLOW".
"""

            # Generate validation
            response = await self.llm_service.generate(
                prompt=prompt,
                model_id="gpt-4",
                temperature=0.2,  # Low temperature for consistent validation
                max_tokens=3000
            )

            json_text = extract_json_from_response(response.get("content", "{}"))
            validation_report = json.loads(json_text)

            decision = validation_report.get("decision", "PASS")
            quality_score = validation_report.get("quality_score", 0)
            issues = validation_report.get("issues", [])

            logger.info(f"Document validation complete: {decision}")
            logger.info(f"Quality score: {quality_score}/100")

            if issues:
                logger.warning(f"Document validation found {len(issues)} issues")
                for issue in issues:
                    logger.warning(f"  - [{issue.get('severity')}] {issue.get('description')}")

            # Update validation history with new mistakes
            new_mistakes = validation_report.get("mistakes_for_history", [])
            updated_history = validation_history + new_mistakes

            # Limit history to last 5 iterations to avoid prompt bloat
            if len(updated_history) > 5:
                updated_history = updated_history[-5:]

            return {
                **state,
                "document_validation_report": validation_report,
                "document_validation_decision": decision,
                "validation_history": updated_history,
                "iteration_count": iteration_count + 1
            }

        except Exception as e:
            logger.error(f"Document Validator agent failed: {str(e)}", exc_info=True)
            # Don't block workflow on validation errors, but log them
            return {
                **state,
                "document_validation_report": {
                    "validation_status": "ERROR",
                    "decision": "PASS",  # Continue on error
                    "quality_score": 0,
                    "issues": [],
                    "summary": f"Validation error: {str(e)}"
                },
                "document_validation_decision": "PASS"
            }

    # ========================================================================
    # HELPER METHODS FOR AGENT 1.1 (EDA-ENHANCED COMPLEXITY ANALYZER)
    # ========================================================================

    def _map_data_types_to_tools(self, data_types: List[str], tech_stack_kb: Dict) -> Dict:
        """
        Map detected data types to AI/ML tool recommendations.

        Args:
            data_types: List of detected data types (e.g., ["tabular_excel", "pdf_text", "images"])
            tech_stack_kb: Tech stack knowledge base loaded from YAML

        Returns:
            Dictionary with primary_tools, chatbot_tools, and use_cases
        """
        recommended_tools = {
            "primary_tools": {},
            "chatbot_tools": {},
            "use_cases": []
        }

        data_type_mapping = tech_stack_kb.get("data_type_ai_tools", {})
        chatbot_tools = tech_stack_kb.get("chatbot_llm_tools", {})

        # Map each detected data type to tools
        for data_type in data_types:
            if data_type in data_type_mapping:
                tools_info = data_type_mapping[data_type]
                recommended_tools["primary_tools"][data_type] = tools_info.get("recommended_ai_tools", {})
                recommended_tools["use_cases"].extend(tools_info.get("use_cases", []))

        # Map applicable ChatBot tools based on data types
        if any("pdf" in dt for dt in data_types) or "complex_pdfs" in data_types:
            recommended_tools["chatbot_tools"]["document_intelligence"] = [
                {
                    "name": "DocumentService (with Docling)",
                    "description": "Enterprise PDF processing with superior layout understanding",
                    "service": "app.services.document_service.DocumentService",
                    "applicable": True,
                    "reason": "Complex PDFs detected in sample files"
                },
                {
                    "name": "OCRService",
                    "description": "Hybrid Docling + Tesseract OCR for text extraction",
                    "service": "app.services.ocr_service.OCRService",
                    "applicable": True,
                    "reason": "PDF text extraction required"
                }
            ]

        if any("image" in dt for dt in data_types) or "images" in data_types:
            recommended_tools["chatbot_tools"]["vision_analysis"] = [
                {
                    "name": "VisionService",
                    "description": "Technical drawing and image analysis with Vision LLMs",
                    "service": "app.services.vision_service.VisionService",
                    "applicable": True,
                    "reason": "Images/drawings detected in sample files"
                }
            ]

        if any("tabular" in dt for dt in data_types) or "structured_data" in data_types:
            recommended_tools["chatbot_tools"]["rag_pipeline"] = [
                {
                    "name": "RAG Pipeline (Multi-Strategy)",
                    "description": "Hybrid retrieval for document Q&A with source attribution",
                    "service": "app.services.rag_service.RAGService",
                    "applicable": True,
                    "reason": "Structured data suitable for knowledge base search"
                }
            ]

        # Remove duplicate use cases
        recommended_tools["use_cases"] = list(set(recommended_tools["use_cases"]))

        return recommended_tools

    def _determine_complexity_from_eda(self, eda_report: Dict) -> Tuple[str, float, float]:
        """
        Determine complexity rating and multipliers from EDA report insights.

        Args:
            eda_report: EDA report from EDAAnalyzer.generate_eda_report()

        Returns:
            Tuple of (complexity_rating, effort_multiplier, rate_multiplier)
            - complexity_rating: "Low", "Medium", or "High"
            - effort_multiplier: 1.0, 1.3, or 1.8
            - rate_multiplier: 1.0, 1.15, or 1.30
        """
        data_quality = eda_report.get("overall_data_quality", 0.5)
        data_volume_mb = eda_report.get("total_data_volume_mb", 0)
        detected_types = eda_report.get("detected_data_types", [])

        # High complexity indicators
        has_images = any("image" in dt for dt in detected_types)
        has_technical_drawings = any("technical" in dt or "cad" in dt for dt in detected_types)
        has_complex_pdfs = "complex_pdfs" in detected_types
        large_volume = data_volume_mb > 5
        low_quality = data_quality < 0.7

        # Calculate complexity score
        complexity_score = 0
        if has_technical_drawings:
            complexity_score += 3  # Technical drawings require specialized skills
        if has_images:
            complexity_score += 2  # Image processing requires vision models
        if has_complex_pdfs:
            complexity_score += 2  # Complex PDFs require advanced extraction
        if large_volume:
            complexity_score += 1  # Large volume requires optimization
        if low_quality:
            complexity_score += 1  # Low quality requires data cleaning

        # Determine rating and multipliers
        if complexity_score >= 5:
            return "High", 1.8, 1.30
        elif complexity_score >= 2:
            return "Medium", 1.3, 1.15
        else:
            return "Low", 1.0, 1.0

    def _extract_required_skills(self, eda_report: Dict, recommended_tools: Dict) -> List[str]:
        """
        Extract required specialized skills from EDA report and recommended tools.

        Args:
            eda_report: EDA report with domain and data types
            recommended_tools: Recommended AI/ML tech stack

        Returns:
            List of specialized skill requirements
        """
        skills = []

        domain = eda_report.get("domain", "")
        detected_types = eda_report.get("detected_data_types", [])

        # Domain-specific skills
        if "Engineering" in domain or "CAD" in domain:
            skills.append("CAD/Technical Drawing Analysis")
        if "Analytics" in domain or "BI" in domain:
            skills.append("Data Analytics and Business Intelligence")
        if "Finance" in domain:
            skills.append("Financial Data Analysis")

        # Data type-specific skills
        if any("image" in dt or "technical" in dt for dt in detected_types):
            skills.append("Computer Vision and Image Processing")
        if any("pdf" in dt for dt in detected_types):
            skills.append("Document Processing and OCR")
        if any("tabular" in dt or "structured" in dt for dt in detected_types):
            skills.append("Data Engineering and ETL")

        # Tool-specific skills
        chatbot_tools = recommended_tools.get("chatbot_tools", {})
        if "vision_analysis" in chatbot_tools:
            skills.append("Vision LLM Integration (GPT-4V, Claude Vision)")
        if "document_intelligence" in chatbot_tools:
            skills.append("Advanced PDF Processing (Docling)")

        return list(set(skills))  # Remove duplicates

    def _recommend_teams_from_eda(self, eda_report: Dict) -> List[str]:
        """
        Recommend specialized teams based on EDA findings.

        Args:
            eda_report: EDA report with domain and complexity

        Returns:
            List of recommended specialized teams
        """
        teams = []

        domain = eda_report.get("domain", "")
        detected_types = eda_report.get("detected_data_types", [])
        data_quality = eda_report.get("overall_data_quality", 1.0)

        # Always need core teams
        teams.append("Backend Development Team")
        teams.append("Frontend Development Team")

        # Data-specific teams
        if any("tabular" in dt or "structured" in dt for dt in detected_types):
            teams.append("Data Engineering Team")

        # ML/AI teams
        if any("image" in dt or "technical" in dt for dt in detected_types):
            teams.append("ML/AI Team (Computer Vision)")
        elif any("pdf" in dt for dt in detected_types):
            teams.append("ML/AI Team (NLP and Document Intelligence)")

        # Data quality team if needed
        if data_quality < 0.7:
            teams.append("Data Quality and Cleaning Team")

        # Domain expertise
        if "Engineering" in domain or "CAD" in domain:
            teams.append("Domain Expert Team (Engineering/CAD)")
        elif "Finance" in domain:
            teams.append("Domain Expert Team (Finance)")

        return teams

    def _generate_reasoning(self, eda_report: Dict, recommended_tools: Dict) -> str:
        """
        Generate natural language reasoning for complexity assessment.

        Args:
            eda_report: EDA report with analysis insights
            recommended_tools: Recommended AI/ML tech stack

        Returns:
            Human-readable reasoning string
        """
        total_files = eda_report.get("total_files_analyzed", 0)
        domain = eda_report.get("domain", "Unknown")
        data_quality = eda_report.get("overall_data_quality", 0)
        detected_types = eda_report.get("detected_data_types", [])
        insights = eda_report.get("insights", [])

        reasoning_parts = []

        # File analysis summary
        reasoning_parts.append(
            f"Analysis based on {total_files} sample file(s) with {data_quality:.0%} overall data quality."
        )

        # Domain context
        reasoning_parts.append(f"Project domain detected as: {domain}.")

        # Data type complexity
        if detected_types:
            types_str = ", ".join(detected_types[:3])  # Show first 3
            if len(detected_types) > 3:
                types_str += f", and {len(detected_types) - 3} more"
            reasoning_parts.append(f"Detected data types include: {types_str}.")

        # Key insights
        if insights:
            reasoning_parts.append("Key findings:")
            for insight in insights[:3]:  # Top 3 insights
                reasoning_parts.append(f"• {insight}")

        # Tool recommendations summary
        chatbot_tools = recommended_tools.get("chatbot_tools", {})
        if chatbot_tools:
            tool_categories = list(chatbot_tools.keys())
            reasoning_parts.append(
                f"Recommended specialized capabilities: {', '.join(tool_categories)}."
            )

        return " ".join(reasoning_parts)

    def _generate_fallback_analysis(self, state: Dict, reason: str) -> Dict:
        """
        Generate fallback complexity analysis when EDA fails or no samples provided.

        Args:
            state: Current workflow state
            reason: Reason for fallback (e.g., "No sample files", "EDA analysis failed")

        Returns:
            Updated state with fallback complexity_analysis
        """
        # Fix: Handle None reason parameter to prevent format string errors
        if reason is None:
            reason = "Unknown error"

        fallback_analysis = {
            "overall_rating": "Medium",
            "confidence_score": 0.5,
            "impact_on_estimation": {
                "effort_multiplier": 1.0,
                "rate_multiplier": 1.0,
                "skill_requirements": {
                    "minimum_level": "Mid-level",
                    "specialized_skills": []
                },
                "recommended_teams": [
                    "Backend Development Team",
                    "Frontend Development Team"
                ]
            },
            "reasoning": f"EDA analysis unavailable: {reason}. Using default multipliers (1.0x effort, 1.0x rate). "
                        f"For more accurate estimates, please upload sample files that represent project complexity "
                        f"(PDFs, Excel sheets, images, etc.).",
            "eda_report": None,
            "recommended_tech_stack": None
        }

        # Log the fallback reason
        logger.warning(f"Agent 1.1 using fallback analysis: {reason}")

        # Add error to state
        errors = state.get("errors", [])
        errors.append(f"Sample Complexity Analyzer (EDA): {reason}")

        return {
            **state,
            "complexity_analysis": fallback_analysis,
            "errors": errors
        }

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
