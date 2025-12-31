"""
Claude CLI Agent

Autonomous coding agent using official Claude Code CLI:
- Option 2 in hybrid system (powerful, costly, good for complex tasks)
- Uses Anthropic's official CLI with all built-in tools
- Runs in Docker-in-Docker sandbox
- Subject to API budget caps ($10/day, $200/month)

Architecture:
- Spawns Claude Code CLI in isolated container
- Parses CLI output for streaming events
- Enforces budget limits before execution
- Stores artifacts in MinIO

Cost: ~$0.60 - $1.50 per task (depending on complexity)
"""

import asyncio
import json
import logging
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx

from app.services.api_usage_tracker import api_usage_tracker

logger = logging.getLogger(__name__)


class ClaudeCliAgent:
    """
    Official Claude Code CLI agent

    Features:
    - Full Claude Code CLI capabilities
    - 50+ iteration support (vs 20 for local)
    - Pre-built tools (Bash, Read, Write, Edit, Grep, Glob, etc.)
    - Self-correction and debugging
    - Real-time output streaming
    - API budget enforcement
    """

    def __init__(
        self,
        task_id: str,
        session_id: str,
        anthropic_api_key: str,
        max_iterations: int = 50,
        timeout_seconds: int = 600,  # 10 minutes
        redis_client: Optional[Any] = None
    ):
        """
        Initialize Claude CLI agent

        Args:
            task_id: Unique task identifier
            session_id: User session ID
            anthropic_api_key: Anthropic API key
            max_iterations: Max CLI iterations (default 50)
            timeout_seconds: Max execution time
            redis_client: Redis client for event streaming
        """
        self.task_id = task_id
        self.session_id = session_id
        self.anthropic_api_key = anthropic_api_key
        self.max_iterations = max_iterations
        self.timeout_seconds = timeout_seconds
        self.redis_client = redis_client

        # Agent state
        self.iteration = 0
        self.artifacts = []
        self.total_tokens = 0
        self.total_cost = 0.0

        # CLI process
        self.cli_process = None

    async def execute_task(
        self,
        query: str,
        task_type: str,
        uploaded_files: List[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point - execute task with Claude Code CLI

        Args:
            query: User's query/request
            task_type: Type of task (research, web_automation, etc.)
            uploaded_files: List of file paths available in workspace

        Returns:
            Result dictionary with answer, artifacts, and metadata
        """

        logger.info(
            f"🎩 Claude CLI Agent starting for task: {self.task_id}\n"
            f"   Task Type: {task_type}\n"
            f"   Query: {query[:100]}..."
        )

        # CRITICAL: Check budget before starting
        budget_check = await self._check_budget(task_type)

        if not budget_check["can_proceed"]:
            logger.warning(
                f"⚠️ Budget limit reached: {budget_check['reason']}"
            )

            await self._publish_event("budget_limit_reached", {
                "reason": budget_check["reason"],
                "daily_remaining": budget_check["daily_remaining"],
                "monthly_remaining": budget_check["monthly_remaining"]
            })

            return {
                "success": False,
                "error": f"Budget limit: {budget_check['reason']}",
                "answer": f"Cannot proceed: {budget_check['reason']}. Please try local mini agent instead.",
                "artifacts": []
            }

        await self._publish_event("agent_started", {
            "agent_type": "claude_cli",
            "task_id": self.task_id,
            "task_type": task_type,
            "estimated_cost": budget_check["estimated_cost"]
        })

        try:
            # Execute task with Claude Code CLI
            result = await self._run_claude_cli(
                query=query,
                task_type=task_type,
                uploaded_files=uploaded_files or []
            )

            # Record API usage
            await api_usage_tracker.record_usage(
                cost=self.total_cost,
                task_id=self.task_id,
                agent_option="claude_cli",
                tokens_used=self.total_tokens,
                model_name="claude-sonnet-4.5"
            )

            logger.info(
                f"✅ Task {self.task_id} completed\n"
                f"   Cost: ${self.total_cost:.2f}\n"
                f"   Tokens: {self.total_tokens:,}\n"
                f"   Iterations: {self.iteration}"
            )

            await self._publish_event("agent_completed", {
                "task_id": self.task_id,
                "iterations": self.iteration,
                "artifacts": len(self.artifacts),
                "cost": self.total_cost,
                "tokens": self.total_tokens
            })

            return result

        except Exception as e:
            logger.error(f"❌ Task {self.task_id} failed: {str(e)}")

            await self._publish_event("agent_failed", {
                "task_id": self.task_id,
                "error": str(e)
            })

            return {
                "success": False,
                "error": str(e),
                "answer": f"Task failed: {str(e)}",
                "artifacts": self.artifacts
            }

    async def _check_budget(self, task_type: str) -> Dict[str, Any]:
        """
        Check if we have budget to run this task

        Args:
            task_type: Type of task (for cost estimation)

        Returns:
            {
                "can_proceed": bool,
                "reason": str,
                "estimated_cost": float,
                "daily_remaining": float,
                "monthly_remaining": float
            }
        """

        # Get budget status
        daily_remaining = await api_usage_tracker.get_daily_budget_remaining()
        monthly_remaining = await api_usage_tracker.get_monthly_budget_remaining()

        # Estimate cost for this task
        estimated_cost = self._estimate_task_cost(task_type)

        # Check if we can afford it
        can_proceed = (
            daily_remaining >= estimated_cost and
            monthly_remaining >= estimated_cost
        )

        reason = ""
        if daily_remaining < estimated_cost:
            reason = f"Daily budget exhausted (${daily_remaining:.2f} remaining, need ${estimated_cost:.2f})"
        elif monthly_remaining < estimated_cost:
            reason = f"Monthly budget exhausted (${monthly_remaining:.2f} remaining, need ${estimated_cost:.2f})"
        else:
            reason = f"Budget OK (Daily: ${daily_remaining:.2f}, Monthly: ${monthly_remaining:.2f})"

        logger.info(
            f"💰 Budget check: {reason}\n"
            f"   Estimated cost: ${estimated_cost:.2f}\n"
            f"   Can proceed: {can_proceed}"
        )

        return {
            "can_proceed": can_proceed,
            "reason": reason,
            "estimated_cost": estimated_cost,
            "daily_remaining": daily_remaining,
            "monthly_remaining": monthly_remaining
        }

    def _estimate_task_cost(self, task_type: str) -> float:
        """
        Estimate cost for task type

        Based on Claude Sonnet 4.5 pricing:
        - Input: $3/MTok
        - Output: $15/MTok

        Args:
            task_type: Type of task

        Returns:
            Estimated cost in USD
        """

        # Task type complexity mapping
        task_complexity_tokens = {
            "research": 80_000,          # High token usage
            "web_automation": 60_000,    # Medium-high
            "code_generation": 50_000,   # Medium
            "data_analysis": 40_000,     # Medium
            "vision_task": 30_000,       # Lower
            "document_processing": 30_000,
            "conversational": 20_000     # Low
        }

        estimated_tokens = task_complexity_tokens.get(task_type, 50_000)

        # Assume 70% input, 30% output
        input_tokens = estimated_tokens * 0.7
        output_tokens = estimated_tokens * 0.3

        # Calculate cost
        cost = (input_tokens / 1_000_000 * 3.0) + (output_tokens / 1_000_000 * 15.0)

        return round(cost, 2)

    async def _run_claude_cli(
        self,
        query: str,
        task_type: str,
        uploaded_files: List[str]
    ) -> Dict[str, Any]:
        """
        Run Claude Code CLI and parse output

        NOTE: This is a stub - actual implementation will:
        1. Spawn Docker container with Claude CLI
        2. Mount workspace volume
        3. Stream CLI output
        4. Parse for tool usage and iterations
        5. Extract artifacts

        Args:
            query: User query
            task_type: Task type
            uploaded_files: Available files

        Returns:
            Result dictionary
        """

        logger.info(f"🎩 Starting Claude Code CLI for task: {self.task_id}")

        # TODO: Actual implementation
        # For now, return stub response

        await self._publish_event("cli_starting", {
            "query": query[:100],
            "task_type": task_type,
            "files": len(uploaded_files)
        })

        # Simulate CLI execution
        await asyncio.sleep(2)

        # Stub result
        result = {
            "success": True,
            "answer": f"Claude Code CLI executed successfully (stub implementation).\n\nQuery: {query}\n\nThis is where the actual Claude CLI response would appear.",
            "artifacts": [],
            "iterations": 5,
            "model_used": "claude-sonnet-4.5",
            "cost": self._estimate_task_cost(task_type)
        }

        # Update stats
        self.iteration = result["iterations"]
        self.total_cost = result["cost"]
        self.total_tokens = int(self.total_cost / 0.000015)  # Rough estimate

        return result

    async def _publish_event(self, event_type: str, data: Dict[str, Any]):
        """
        Publish event to Redis for frontend streaming

        Args:
            event_type: Event type
            data: Event data
        """

        if not self.redis_client:
            return

        event = {
            "type": event_type,
            "task_id": self.task_id,
            "session_id": self.session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }

        try:
            channel = f"agent_events:{self.session_id}"
            await self.redis_client.publish(
                channel,
                json.dumps(event)
            )
        except Exception as e:
            logger.warning(f"⚠️ Failed to publish event: {str(e)}")

    def get_stats(self) -> Dict[str, Any]:
        """Get agent execution statistics"""

        return {
            "task_id": self.task_id,
            "session_id": self.session_id,
            "iterations": self.iteration,
            "max_iterations": self.max_iterations,
            "artifacts_generated": len(self.artifacts),
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "cost_per_iteration": round(self.total_cost / self.iteration, 2) if self.iteration > 0 else 0,
            "model": "claude-sonnet-4.5"
        }


# Global factory function
def create_claude_cli_agent(
    task_id: str,
    session_id: str,
    anthropic_api_key: str,
    **kwargs
) -> ClaudeCliAgent:
    """
    Factory function to create Claude CLI agent instance

    Args:
        task_id: Unique task identifier
        session_id: User session ID
        anthropic_api_key: Anthropic API key
        **kwargs: Additional configuration

    Returns:
        ClaudeCliAgent instance
    """

    return ClaudeCliAgent(
        task_id=task_id,
        session_id=session_id,
        anthropic_api_key=anthropic_api_key,
        **kwargs
    )
