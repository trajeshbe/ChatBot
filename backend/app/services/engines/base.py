"""
Base Agent Engine

Abstract base class for all agent execution engines.
Defines the interface that all engines (Default, Codex CLI, Claude Code CLI) must implement.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional, AsyncIterator
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EngineType(str, Enum):
    """Available agent execution engines"""
    DEFAULT = "default"  # Our existing LangGraph agent
    CODEX_CLI = "codex-cli"  # OpenAI Codex CLI
    CLAUDE_CODE_CLI = "claude-code-cli"  # Anthropic Claude Code CLI


class AgentEngine(ABC):
    """
    Abstract base class for agent execution engines

    All engines must implement:
    - execute(): Main execution method
    - stream_events(): Stream execution events for real-time updates
    - cancel(): Cancel running execution
    - health_check(): Check if engine is available
    """

    def __init__(self, engine_type: EngineType):
        self.engine_type = engine_type
        self.logger = logging.getLogger(f"{__name__}.{engine_type.value}")

    @abstractmethod
    async def execute(
        self,
        task_description: str,
        workspace_path: str,
        artifacts_path: str,
        max_iterations: int = 20,
        timeout_seconds: int = 600,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the agent task

        Args:
            task_description: What the agent should do
            workspace_path: Path to workspace with files (/workspace/)
            artifacts_path: Path to save artifacts (/workspace/artifacts/)
            max_iterations: Maximum iterations for agent loop
            timeout_seconds: Maximum execution time
            model: LLM model to use (engine-specific)
            **kwargs: Additional engine-specific parameters

        Returns:
            Dict with:
                - success: bool
                - result: str (final result message)
                - artifacts: List[str] (artifact paths)
                - iterations: int (iterations completed)
                - duration_seconds: float
                - error: Optional[str]
        """
        pass

    @abstractmethod
    async def stream_events(
        self,
        task_description: str,
        workspace_path: str,
        artifacts_path: str,
        max_iterations: int = 20,
        timeout_seconds: int = 600,
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Execute and stream events in real-time

        Yields events like:
            {"type": "thinking", "thought": "...", "iteration": 1}
            {"type": "tool_use", "tool_name": "...", "tool_input": "..."}
            {"type": "tool_result", "result": "...", "success": True}
            {"type": "artifact", "artifact_path": "...", "artifact_name": "..."}
            {"type": "completed", "result": "...", "iterations": 5}
            {"type": "error", "error": "..."}
        """
        pass

    @abstractmethod
    async def cancel(self, execution_id: str) -> bool:
        """
        Cancel a running execution

        Args:
            execution_id: Unique identifier for the execution

        Returns:
            True if successfully cancelled, False otherwise
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if the engine is available and healthy

        Returns:
            Dict with:
                - available: bool
                - version: Optional[str]
                - message: str
                - details: Dict[str, Any]
        """
        pass

    def _format_event(
        self,
        event_type: str,
        **data
    ) -> Dict[str, Any]:
        """
        Format an event with standard fields

        Args:
            event_type: Type of event (thinking, tool_use, etc.)
            **data: Event-specific data

        Returns:
            Formatted event dict with timestamp
        """
        return {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "engine": self.engine_type.value,
            **data
        }
