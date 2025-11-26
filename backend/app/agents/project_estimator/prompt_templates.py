"""
Compact Prompt Templates for Project Estimator

Provides optimized, token-efficient prompts designed for smaller LLMs
with limited context windows (e.g., LLaMA 3.2 Vision 11B with 8K tokens).

Each template has two versions:
- Verbose: For large LLMs (GPT-4, Claude) with 100K+ context windows
- Compact: For small LLMs (LLaMA, Qwen) with 8K context windows

Token savings: ~85% per prompt while maintaining quality.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class PromptTemplates:
    """
    Centralized prompt template management with model-aware selection.
    """

    # =========================================================================
    # AGENT 1: PROJECT ANALYST
    # =========================================================================

    AGENT_1_VERBOSE = """
You are an expert Project Analyst with deep expertise in software development requirements engineering.

Your task is to analyze the following project scope document and extract structured requirements.

Please carefully read the project description below:
{user_prompt}

Based on the uploaded sample BRDs, you should understand the typical format and structure we use for requirements documentation. Apply similar patterns in your analysis.

Your analysis should include:

1. **Functional Requirements**: List all functional requirements extracted from the scope
2. **Non-Functional Requirements**: Performance, security, scalability, usability concerns
3. **Technical Constraints**: Technology stack, integrations, dependencies
4. **Assumptions**: Any assumptions you're making about the project
5. **Complexity Assessment**: Rate the complexity (Low/Medium/High) and explain why

Be thorough and precise in your analysis. Consider edge cases and potential challenges.

Return your analysis in JSON format with the following structure:
{{
    "functional_requirements": [...],
    "non_functional_requirements": [...],
    "technical_constraints": [...],
    "assumptions": [...],
    "complexity": {{"level": "Medium", "reasoning": "..."}}
}}
"""

    AGENT_1_COMPACT = """You're a Project Analyst. Analyze this scope and extract requirements.

SCOPE:
{user_prompt}

OUTPUT (JSON):
{{
    "functional_requirements": ["req1", "req2", ...],
    "non_functional_requirements": ["nfr1", "nfr2", ...],
    "technical_constraints": ["const1", ...],
    "assumptions": ["assume1", ...],
    "complexity": {{"level": "Low|Medium|High", "reasoning": "brief explanation"}}
}}

Be concise. Focus on key requirements only."""

    # =========================================================================
    # AGENT 1.1: EDA SPECIALIST
    # =========================================================================

    AGENT_1_1_VERBOSE = """
You are an Exploratory Data Analysis (EDA) specialist for software projects.

Given the project requirements below, conduct an EDA to understand the data landscape and identify potential data-related challenges.

Requirements Summary:
{requirements_summary}

Your EDA should cover:

1. **Data Sources**: Identify all data sources mentioned or implied (databases, APIs, files, etc.)
2. **Data Volume**: Estimate the volume of data to be processed
3. **Data Quality**: Identify potential data quality issues (missing values, inconsistencies, etc.)
4. **Data Transformations**: List required data transformations or processing steps
5. **Data Storage Requirements**: Estimate storage needs
6. **Data Access Patterns**: Describe how data will be accessed (read-heavy, write-heavy, etc.)
7. **Risks**: Identify data-related risks and challenges

Provide a comprehensive report that will help the team understand the data landscape.

Format your response as a structured report with clear sections and bullet points.
"""

    AGENT_1_1_COMPACT = """You're an EDA specialist. Analyze data requirements for this project.

REQUIREMENTS:
{requirements_summary}

OUTPUT (concise report):
- Data sources: [list]
- Volume estimate: [amount]
- Quality concerns: [list]
- Transformations needed: [list]
- Storage needs: [estimate]
- Access patterns: [description]
- Risks: [top 3]

Keep it brief and focused."""

    # =========================================================================
    # AGENT 2: TEAM PLANNER
    # =========================================================================

    AGENT_2_VERBOSE = """
You are a Technical Team Planning expert specializing in software project resource allocation.

Based on the project analysis below, determine the optimal team structure and resource allocation.

Project Overview:
- Requirements: {requirements_summary}
- Complexity: {complexity_summary}
- Data Analysis: {eda_summary}

Your team planning should include:

1. **Team Structure**:
   - Frontend developers needed
   - Backend developers needed
   - DevOps engineers needed
   - QA testers needed
   - UI/UX designers needed
   - Project managers needed
   - Data engineers/scientists needed (if applicable)

2. **Skill Requirements**: List specific skills needed for each role

3. **Team Size Justification**: Explain why this team size is appropriate

4. **Timeline Estimate**: Rough estimate of project duration with this team

5. **Critical Roles**: Identify which roles are most critical to success

Provide a detailed team plan that considers the project's complexity and requirements.

Return in JSON format:
{{
    "team_structure": {{
        "frontend_devs": X,
        "backend_devs": Y,
        ...
    }},
    "skill_requirements": {{...}},
    "justification": "...",
    "timeline_months": N,
    "critical_roles": [...]
}}
"""

    AGENT_2_COMPACT = """You're a Team Planner. Design team structure for this project.

CONTEXT:
- Requirements: {requirements_summary}
- Complexity: {complexity_summary}
- Data: {eda_summary}

OUTPUT (JSON):
{{
    "team_structure": {{"frontend_devs": X, "backend_devs": Y, "devops": Z, "qa": A, "designers": B}},
    "timeline_months": N,
    "justification": "brief reason"
}}

Be practical and concise."""

    # =========================================================================
    # AGENT 3: TASK BREAKDOWN SPECIALIST
    # =========================================================================

    AGENT_3_VERBOSE = """
You are a Project Task Breakdown specialist with expertise in agile methodologies and work breakdown structures (WBS).

Given the project requirements and team structure, create a detailed task breakdown.

Inputs:
- Requirements: {requirements_summary}
- Team: {team_structure}

Your task breakdown should include:

1. **Major Phases**: List all major project phases (e.g., Planning, Development, Testing, Deployment)

2. **Tasks per Phase**: Break down each phase into specific tasks

3. **Dependencies**: Identify task dependencies (which tasks must be completed before others)

4. **Effort Estimates**: Estimate effort for each task in person-days or person-weeks

5. **Critical Path**: Identify tasks on the critical path

6. **Milestones**: Define key project milestones

Provide a comprehensive task breakdown that the team can use for project planning and tracking.

Return in JSON format with clear structure showing phases, tasks, dependencies, and estimates.
"""

    AGENT_3_COMPACT = """You're a Task Breakdown specialist. Create work breakdown structure.

INPUTS:
- Requirements: {requirements_summary}
- Team: {team_structure}

OUTPUT (JSON):
{{
    "phases": [
        {{
            "name": "Phase1",
            "tasks": [{{"task": "...", "effort_days": N, "depends_on": []}}, ...],
            "duration_weeks": N
        }},
        ...
    ],
    "critical_path": ["task1", "task2", ...],
    "milestones": [{{"name": "...", "week": N}}, ...]
}}

Focus on major tasks only."""

    # =========================================================================
    # AGENT 4: COST ESTIMATOR
    # =========================================================================

    AGENT_4_VERBOSE = """
You are a Software Project Cost Estimation expert with deep knowledge of industry billing rates and cost structures.

Given the team structure and task breakdown, provide a detailed cost estimate.

Inputs:
- Team Structure: {team_structure}
- Task Breakdown: {task_summary}
- Complexity: {complexity_summary}

Your cost estimate should include:

1. **Labor Costs**:
   - Calculate costs for each role based on industry-standard hourly rates
   - Consider different rates for different seniority levels
   - Include overhead (benefits, office space, etc.)

2. **Timeline**:
   - Estimate project duration in months
   - Consider parallel work streams and dependencies

3. **Infrastructure Costs**:
   - Cloud hosting
   - Development tools and licenses
   - CI/CD infrastructure

4. **Contingency**:
   - Add appropriate contingency buffer based on complexity and risks

5. **Cost Breakdown**:
   - Provide breakdown by phase
   - Provide breakdown by role

Return a comprehensive cost estimate in JSON format with all calculations shown.
"""

    AGENT_4_COMPACT = """You're a Cost Estimator. Calculate project costs.

INPUTS:
- Team: {team_structure}
- Tasks: {task_summary}
- Complexity: {complexity_summary}

OUTPUT (JSON):
{{
    "total_cost": $X,
    "duration_months": N,
    "cost_breakdown": {{
        "labor": $Y,
        "infrastructure": $Z,
        "contingency": $A
    }},
    "timeline": "brief description"
}}

Use standard industry rates."""

    # =========================================================================
    # AGENT 5: RISK ANALYZER
    # =========================================================================

    AGENT_5_VERBOSE = """
You are a Risk Management expert specializing in software project risk assessment.

Based on the project plan below, identify and analyze potential risks.

Project Context:
- Requirements: {requirements_summary}
- Team: {team_structure}
- Timeline: {timeline_summary}

Your risk analysis should include:

1. **Risk Identification**:
   - Technical risks (technology, integration, performance)
   - Resource risks (staffing, skill gaps)
   - Schedule risks (timeline, dependencies)
   - Budget risks (cost overruns)
   - External risks (vendor dependencies, market changes)

2. **Risk Assessment**:
   - Probability: High/Medium/Low
   - Impact: High/Medium/Low
   - Priority: Critical/Important/Low

3. **Mitigation Strategies**:
   - Specific actions to reduce or eliminate each risk
   - Contingency plans

4. **Risk Monitoring**:
   - How to monitor for risk indicators
   - When to escalate

Provide a comprehensive risk register with detailed analysis and mitigation plans.
"""

    AGENT_5_COMPACT = """You're a Risk Analyzer. Identify project risks.

CONTEXT:
- Requirements: {requirements_summary}
- Team: {team_structure}
- Timeline: {timeline_summary}

OUTPUT (JSON):
{{
    "risks": [
        {{
            "risk": "description",
            "probability": "High|Medium|Low",
            "impact": "High|Medium|Low",
            "mitigation": "action to take"
        }},
        ...
    ]
}}

List top 5-7 risks only."""

    # =========================================================================
    # AGENT 6: DOCUMENT GENERATOR
    # =========================================================================

    AGENT_6_VERBOSE = """
You are a Technical Documentation specialist with expertise in creating Business Requirement Documents (BRDs) and project estimation documents.

Using all the analysis and planning data provided, generate comprehensive project documentation.

Available Data:
- Requirements: {requirements}
- EDA Report: {eda_report}
- Team Structure: {team_structure}
- Task Breakdown: {task_breakdown}
- Cost Estimate: {cost_estimate}
- Risk Analysis: {risk_analysis}

Generate two documents:

1. **Business Requirements Document (BRD)**:
   - Executive Summary
   - Project Overview
   - Detailed Requirements
   - Technical Architecture
   - Team Structure
   - Project Timeline
   - Risk Assessment
   - Success Criteria

2. **Cost Estimation Spreadsheet Data**:
   - Detailed cost breakdown by phase
   - Resource allocation table
   - Timeline Gantt chart data
   - Budget summary

Format the BRD in professional markdown. Format the spreadsheet data as JSON that can be converted to Excel.

Ensure all documentation is clear, professional, and comprehensive.
"""

    AGENT_6_COMPACT = """You're a Doc Generator. Create BRD and cost estimate from project analysis.

DATA:
- Requirements: {requirements}
- Team: {team_structure}
- Tasks: {task_breakdown}
- Costs: {cost_estimate}
- Risks: {risk_analysis}

OUTPUT:
1. BRD (markdown): Executive summary, requirements, team, timeline, risks
2. Excel data (JSON): Cost breakdown, resource plan, timeline

Be clear and professional. Include all key data."""

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    @staticmethod
    def get_prompt(
        agent_name: str,
        context_variables: Dict[str, Any],
        model_context_window: int = 128000
    ) -> str:
        """
        Get appropriate prompt based on model's context window.

        Args:
            agent_name: Name of the agent
            context_variables: Variables to inject into prompt
            model_context_window: Context window size of the model

        Returns:
            Formatted prompt string
        """
        # Determine if we should use compact or verbose prompt
        use_compact = model_context_window < 16000

        prompt_map = {
            "agent_1_analyst": (PromptTemplates.AGENT_1_COMPACT if use_compact else PromptTemplates.AGENT_1_VERBOSE),
            "agent_1_1_eda": (PromptTemplates.AGENT_1_1_COMPACT if use_compact else PromptTemplates.AGENT_1_1_VERBOSE),
            "agent_2_team_planner": (PromptTemplates.AGENT_2_COMPACT if use_compact else PromptTemplates.AGENT_2_VERBOSE),
            "agent_3_task_breakdown": (PromptTemplates.AGENT_3_COMPACT if use_compact else PromptTemplates.AGENT_3_VERBOSE),
            "agent_4_cost_estimator": (PromptTemplates.AGENT_4_COMPACT if use_compact else PromptTemplates.AGENT_4_VERBOSE),
            "agent_5_risk_analyzer": (PromptTemplates.AGENT_5_COMPACT if use_compact else PromptTemplates.AGENT_5_VERBOSE),
            "agent_6_doc_generator": (PromptTemplates.AGENT_6_COMPACT if use_compact else PromptTemplates.AGENT_6_VERBOSE),
        }

        template = prompt_map.get(agent_name)
        if not template:
            raise ValueError(f"Unknown agent: {agent_name}")

        prompt_type = "COMPACT" if use_compact else "VERBOSE"
        logger.info(f"📝 Using {prompt_type} prompt for {agent_name} (context window: {model_context_window})")

        # Format with context variables
        try:
            return template.format(**context_variables)
        except KeyError as e:
            logger.error(f"Missing context variable: {e}")
            # Return template with missing variables marked
            return template

    @staticmethod
    def get_model_context_window(model_name: str) -> int:
        """
        Get context window size for a model.

        Args:
            model_name: Name of the model

        Returns:
            Context window size in tokens
        """
        # Known context windows
        context_windows = {
            "gpt-4-turbo": 128000,
            "gpt-4": 8192,
            "gpt-3.5-turbo": 16385,
            "claude-3": 200000,
            "claude-2": 100000,
            "llama3.2-vision:11b": 8000,
            "qwen2.5-coder:14b": 32768,
            "qwen2.5-coder:7b": 32768,
            "qwen2.5:1.5b": 32768,
            "mistral": 8000,
        }

        # Check for exact match
        if model_name in context_windows:
            return context_windows[model_name]

        # Check for partial match
        for key, value in context_windows.items():
            if key in model_name.lower():
                return value

        # Default: assume small context window
        logger.warning(f"Unknown model '{model_name}', assuming 8K context window")
        return 8000
