"""
Hybrid Agent Router

Intelligently routes tasks between:
- Option 1: Local mini agent (Ollama - free, fast)
- Option 2: Claude Code CLI (Anthropic - powerful, costly)

Routing logic:
1. Check API budget remaining
2. Evaluate task complexity + type
3. Route to most cost-effective option
4. Fallback if primary option fails
"""

from typing import Dict, Any, Optional, Tuple
from enum import Enum
import logging

from app.services.task_complexity_analyzer import (
    task_complexity_analyzer,
    TaskComplexity,
    TaskType
)

logger = logging.getLogger(__name__)


class AgentOption(str, Enum):
    """Available agent implementations"""
    LOCAL_MINI = "local_mini"      # Option 1: Local LLMs (Ollama)
    CLAUDE_CLI = "claude_cli"      # Option 2: Anthropic CLI
    DIRECT_RAG = "direct_rag"      # Fallback: No agent


class HybridAgentRouter:
    """
    Routes tasks to optimal agent based on:
    - Task complexity & type
    - API budget remaining
    - User preferences
    - Historical success rates
    """

    def __init__(self):
        """Initialize router with default rules"""

        # Routing rules (configurable via settings)
        self.routing_rules = {
            # Option 1 (Local) preferred for these types
            "local_preferred": [
                TaskType.DATA_ANALYSIS,
                TaskType.CODE_GENERATION,
                TaskType.VISION_TASK,
                TaskType.DOCUMENT_PROCESSING
            ],

            # Option 2 (Claude CLI) preferred for these
            "claude_preferred": [
                TaskType.RESEARCH,
                TaskType.WEB_AUTOMATION
            ],

            # Always use local if complexity is MEDIUM
            "local_mandatory_complexity": [
                TaskComplexity.MEDIUM
            ]
        }

    async def route(
        self,
        query: str,
        session_id: str,
        user_preferences: Dict[str, Any] = None
    ) -> Tuple[AgentOption, Dict[str, Any]]:
        """
        Route task to optimal agent

        Args:
            query: User's query
            session_id: Session ID
            user_preferences: User preferences (model, thresholds, etc.)

        Returns:
            Tuple of (agent_option, routing_metadata)
        """

        user_preferences = user_preferences or {}

        # Step 1: Analyze complexity
        complexity, task_type, metadata = task_complexity_analyzer.analyze(
            query=query,
            conversation_history=user_preferences.get("conversation_history"),
            uploaded_files=user_preferences.get("uploaded_files")
        )

        logger.info(
            f"🎯 Complexity Analysis: {complexity.value}, "
            f"Type: {task_type.value}"
        )

        # Step 2: Check if agent mode is enabled
        use_agent_mode = user_preferences.get("use_agent_mode", False)

        if not use_agent_mode:
            return (AgentOption.DIRECT_RAG, {
                "reason": "Agent mode not enabled by user",
                "complexity": complexity.value,
                "task_type": task_type.value
            })

        # Step 2.5: Check for manual agent selection override
        agent_selection = user_preferences.get("agent_selection", "automatic")

        if agent_selection == "local_only":
            # User explicitly wants local agent only
            logger.info("👤 User selected: Local Agent Only")
            return (AgentOption.LOCAL_MINI, {
                "reason": "User manually selected Local Agent Only mode",
                "complexity": complexity.value,
                "task_type": task_type.value,
                "estimated_cost": 0.0,  # Local is free
                "user_override": True
            })

        elif agent_selection == "claude_only":
            # User explicitly wants Claude CLI only
            logger.info("👤 User selected: Claude CLI Only")

            # Check budget for Claude CLI
            from app.services.api_usage_tracker import api_usage_tracker
            daily_budget_remaining = await api_usage_tracker.get_daily_budget_remaining()
            task_estimated_cost = self._estimate_cost(complexity, task_type, AgentOption.CLAUDE_CLI)

            if daily_budget_remaining >= task_estimated_cost:
                return (AgentOption.CLAUDE_CLI, {
                    "reason": "User manually selected Claude CLI Only mode",
                    "complexity": complexity.value,
                    "task_type": task_type.value,
                    "estimated_cost": task_estimated_cost,
                    "budget_remaining": daily_budget_remaining,
                    "user_override": True
                })
            else:
                # Budget insufficient - inform user
                logger.warning(
                    f"⚠️ User selected Claude CLI but budget insufficient: "
                    f"${daily_budget_remaining:.2f} < ${task_estimated_cost:.2f}"
                )
                return (AgentOption.LOCAL_MINI, {
                    "reason": f"Claude CLI requested but budget insufficient (${daily_budget_remaining:.2f} remaining, task needs ${task_estimated_cost:.2f}). Falling back to Local Agent.",
                    "complexity": complexity.value,
                    "task_type": task_type.value,
                    "estimated_cost": 0.0,
                    "budget_warning": True
                })

        # For 'automatic' mode, continue with normal routing logic below

        # Simple tasks don't need agent (unless user forced it)
        if complexity == TaskComplexity.SIMPLE and agent_selection == "automatic":
            return (AgentOption.DIRECT_RAG, {
                "reason": "Task is simple, direct RAG sufficient",
                "complexity": complexity.value,
                "task_type": task_type.value
            })

        # Step 3: Check API budget (for Claude CLI)
        from app.services.api_usage_tracker import api_usage_tracker

        daily_budget_remaining = await api_usage_tracker.get_daily_budget_remaining()
        task_estimated_cost = self._estimate_cost(complexity, task_type, AgentOption.CLAUDE_CLI)

        can_afford_claude = daily_budget_remaining >= task_estimated_cost

        logger.info(
            f"💰 Budget check: Remaining ${daily_budget_remaining:.2f}, "
            f"Task estimate ${task_estimated_cost:.2f}, "
            f"Can afford Claude: {can_afford_claude}"
        )

        # Step 4: Apply routing logic
        selected_option, reason = self._apply_routing_rules(
            complexity=complexity,
            task_type=task_type,
            can_afford_claude=can_afford_claude,
            user_preferences=user_preferences
        )

        # Step 5: Build routing metadata
        routing_metadata = {
            "complexity": complexity.value,
            "task_type": task_type.value,
            "selected_option": selected_option.value,
            "reason": reason,
            "estimated_cost": self._estimate_cost(complexity, task_type, selected_option),
            "budget_remaining": daily_budget_remaining,
            "indicators": metadata.get("indicators", []),
            "estimated_steps": metadata.get("estimated_steps", 1)
        }

        logger.info(
            f"✅ Routing decision: {selected_option.value} "
            f"(Reason: {reason})"
        )

        return (selected_option, routing_metadata)

    def _apply_routing_rules(
        self,
        complexity: TaskComplexity,
        task_type: TaskType,
        can_afford_claude: bool,
        user_preferences: Dict[str, Any]
    ) -> Tuple[AgentOption, str]:
        """Apply routing rules to select agent"""

        # Rule 1: MEDIUM complexity → Always local (cost-effective)
        if complexity in self.routing_rules["local_mandatory_complexity"]:
            return (
                AgentOption.LOCAL_MINI,
                f"Medium complexity tasks use local agent for cost efficiency"
            )

        # Rule 2: User explicitly requests Claude (via preference)
        force_claude = user_preferences.get("force_claude_cli", False)
        if force_claude:
            if can_afford_claude:
                return (
                    AgentOption.CLAUDE_CLI,
                    "User explicitly requested Claude CLI"
                )
            else:
                logger.warning("⚠️ User requested Claude but budget exhausted, falling back to local")
                return (
                    AgentOption.LOCAL_MINI,
                    "User requested Claude but daily budget exhausted, using local fallback"
                )

        # Rule 3: COMPLEX + Research/Web Automation → Prefer Claude (if budget allows)
        if (complexity == TaskComplexity.COMPLEX and
            task_type in self.routing_rules["claude_preferred"]):

            if can_afford_claude:
                return (
                    AgentOption.CLAUDE_CLI,
                    f"Research/Web tasks benefit from Claude CLI's advanced capabilities"
                )
            else:
                return (
                    AgentOption.LOCAL_MINI,
                    f"Research task but daily budget reached, falling back to local agent"
                )

        # Rule 4: COMPLEX + Data/Code/Vision → Prefer Local (faster, free, good enough)
        if (complexity == TaskComplexity.COMPLEX and
            task_type in self.routing_rules["local_preferred"]):

            return (
                AgentOption.LOCAL_MINI,
                f"{task_type.value} tasks work well with local models (Qwen/Llama Vision)"
            )

        # Rule 5: Default to local for cost efficiency
        return (
            AgentOption.LOCAL_MINI,
            "Default to local agent for cost efficiency"
        )

    def _estimate_cost(
        self,
        complexity: TaskComplexity,
        task_type: TaskType,
        agent_option: AgentOption
    ) -> float:
        """
        Estimate cost for this task

        Based on Claude Sonnet 4.5 pricing:
        - Input: $3/MTok
        - Output: $15/MTok
        """

        if agent_option == AgentOption.LOCAL_MINI:
            return 0.0  # Free! Runs on local Ollama

        elif agent_option == AgentOption.CLAUDE_CLI:
            # Estimate token usage based on complexity
            if complexity == TaskComplexity.SIMPLE:
                estimated_tokens = 5_000
            elif complexity == TaskComplexity.MEDIUM:
                estimated_tokens = 20_000
            elif complexity == TaskComplexity.COMPLEX:
                estimated_tokens = 50_000
            else:
                estimated_tokens = 10_000

            # Assume 70% input, 30% output
            input_tokens = estimated_tokens * 0.7
            output_tokens = estimated_tokens * 0.3

            # Calculate cost
            cost = (input_tokens / 1_000_000 * 3.0) + (output_tokens / 1_000_000 * 15.0)
            return round(cost, 2)

        else:
            return 0.0  # Direct RAG is free


# Global instance
hybrid_agent_router = HybridAgentRouter()
