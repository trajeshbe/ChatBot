"""
Local Mini Agent

Autonomous coding agent using local LLMs (Ollama):
- Option 1 in hybrid system (free, fast, good for 80% of tasks)
- Uses qwen2.5-coder:7b for code/data tasks
- Uses llama3.2-vision:11b for vision tasks
- Uses deepseek-coder:6.7b as backup

Architecture:
- Runs inside Docker sandbox container
- Uses agentic loop: THINK → PLAN → ACT → OBSERVE
- Communicates via Redis pub/sub
- Stores artifacts in MinIO

Cost: $0 (100% local execution)
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class LocalMiniAgent:
    """
    Local autonomous agent using Ollama models

    Features:
    - Multi-model support (code, vision, reasoning)
    - Agentic loop with self-correction
    - Tool execution (Python, file ops, bash)
    - Real-time event streaming
    - Artifact management
    """

    def __init__(
        self,
        task_id: str,
        session_id: str,
        ollama_base_url: str = "http://rag-ollama:11434",
        max_iterations: int = 20,
        redis_client: Optional[Any] = None
    ):
        """
        Initialize local mini agent

        Args:
            task_id: Unique task identifier
            session_id: User session ID
            ollama_base_url: Ollama API endpoint
            max_iterations: Max agentic loop iterations
            redis_client: Redis client for event streaming
        """
        self.task_id = task_id
        self.session_id = session_id
        self.ollama_base_url = ollama_base_url
        self.max_iterations = max_iterations
        self.redis_client = redis_client

        # Model selection
        self.models = {
            "code": "qwen2.5-coder:7b",           # Code generation, EDA
            "vision": "llama3.2-vision:11b",      # Image analysis, OCR
            "backup": "deepseek-coder:6.7b"       # Fallback model
        }

        # Agent state
        self.iteration = 0
        self.conversation_history = []
        self.artifacts = []
        self.workspace_files = []

        # Tool registry (will be populated by orchestration layer)
        self.available_tools = []

    async def execute_task(
        self,
        query: str,
        task_type: str,
        uploaded_files: List[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point - execute autonomous task

        Args:
            query: User's query/request
            task_type: Type of task (data_analysis, code_generation, vision_task, etc.)
            uploaded_files: List of file paths available in workspace

        Returns:
            Result dictionary with answer, artifacts, and metadata
        """

        logger.info(
            f"🤖 Local Mini Agent starting for task: {self.task_id}\n"
            f"   Task Type: {task_type}\n"
            f"   Query: {query[:100]}..."
        )

        await self._publish_event("agent_started", {
            "agent_type": "local_mini",
            "task_id": self.task_id,
            "task_type": task_type
        })

        # Select appropriate model based on task type
        model = self._select_model(task_type)

        try:
            # Run agentic loop
            result = await self._agentic_loop(
                query=query,
                model=model,
                task_type=task_type,
                uploaded_files=uploaded_files or []
            )

            logger.info(f"✅ Task {self.task_id} completed successfully")

            await self._publish_event("agent_completed", {
                "task_id": self.task_id,
                "iterations": self.iteration,
                "artifacts": len(self.artifacts)
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

    def _select_model(self, task_type: str) -> str:
        """Select best model for task type"""

        task_model_map = {
            "vision_task": "vision",
            "data_analysis": "code",
            "code_generation": "code",
            "document_processing": "code",
            "research": "code",
            "web_automation": "code",
            "conversational": "code"
        }

        model_key = task_model_map.get(task_type, "code")
        model_name = self.models.get(model_key, self.models["backup"])

        logger.info(f"🎯 Selected model: {model_name} for task type: {task_type}")

        return model_name

    async def _agentic_loop(
        self,
        query: str,
        model: str,
        task_type: str,
        uploaded_files: List[str]
    ) -> Dict[str, Any]:
        """
        Main agentic loop: THINK → PLAN → ACT → OBSERVE

        Continues until:
        - Task is complete
        - Max iterations reached
        - Error occurs
        """

        # Initialize context
        system_prompt = self._build_system_prompt(task_type, uploaded_files)

        self.conversation_history.append({
            "role": "system",
            "content": system_prompt
        })

        self.conversation_history.append({
            "role": "user",
            "content": query
        })

        task_complete = False
        final_answer = ""

        while self.iteration < self.max_iterations and not task_complete:
            self.iteration += 1

            logger.info(f"🔄 Iteration {self.iteration}/{self.max_iterations}")

            await self._publish_event("iteration_started", {
                "iteration": self.iteration,
                "max_iterations": self.max_iterations
            })

            # THINK & PLAN: Call LLM to decide next action
            response = await self._call_ollama(
                model=model,
                messages=self.conversation_history
            )

            # Parse response for tool calls or final answer
            action = self._parse_response(response)

            if action["type"] == "final_answer":
                # Task complete!
                task_complete = True
                final_answer = action["content"]

                logger.info(f"✅ Task complete in {self.iteration} iterations")

            elif action["type"] == "tool_call":
                # ACT: Execute tool
                tool_name = action["tool"]
                tool_args = action["args"]

                logger.info(f"🔧 Executing tool: {tool_name}")

                await self._publish_event("tool_execution", {
                    "tool": tool_name,
                    "args": tool_args
                })

                # Execute tool (via orchestration layer)
                tool_result = await self._execute_tool(tool_name, tool_args)

                # OBSERVE: Add result to conversation
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response
                })

                self.conversation_history.append({
                    "role": "user",
                    "content": f"Tool execution result:\n```\n{tool_result}\n```"
                })

            else:
                # Unexpected response format
                logger.warning(f"⚠️ Unexpected response format: {action}")
                task_complete = True
                final_answer = response

        if not task_complete:
            logger.warning(f"⚠️ Max iterations ({self.max_iterations}) reached")
            final_answer = "Task did not complete within iteration limit. Partial results available."

        return {
            "success": task_complete,
            "answer": final_answer,
            "artifacts": self.artifacts,
            "iterations": self.iteration,
            "model_used": model,
            "cost": 0.0  # Free!
        }

    def _build_system_prompt(self, task_type: str, uploaded_files: List[str]) -> str:
        """Build system prompt for the agent"""

        base_prompt = """You are an autonomous coding agent. Your goal is to complete the user's task by breaking it down into steps and executing tools.

Available tools:
- execute_python(code: str) - Run Python code, returns output
- read_file(path: str) - Read file contents
- write_file(path: str, content: str) - Write file
- install_package(package: str) - Install Python package
- run_bash(command: str) - Run bash command

Workspace files:
{files}

Instructions:
1. Break down the task into logical steps
2. Use tools to accomplish each step
3. Review results and iterate if needed
4. When task is complete, provide final answer

Response format:
For tool calls, use JSON:
{{"action": "tool_call", "tool": "execute_python", "args": {{"code": "..."}}}}

For final answer, use:
{{"action": "final_answer", "content": "..."}}

Always think step-by-step and explain your reasoning.
"""

        files_list = "\n".join([f"- {f}" for f in uploaded_files]) if uploaded_files else "No files uploaded"

        return base_prompt.format(files=files_list)

    async def _call_ollama(self, model: str, messages: List[Dict]) -> str:
        """
        Call Ollama API for LLM inference

        Args:
            model: Model name (e.g., "qwen2.5-coder:7b")
            messages: Conversation history

        Returns:
            LLM response text
        """

        url = f"{self.ollama_base_url}/api/chat"

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 2048
            }
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                result = response.json()
                message = result.get("message", {})
                content = message.get("content", "")

                logger.debug(f"📨 Ollama response: {content[:200]}...")

                return content

        except Exception as e:
            logger.error(f"❌ Ollama API call failed: {str(e)}")
            raise

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response to extract action

        Returns:
            {
                "type": "tool_call" | "final_answer",
                "tool": "execute_python",
                "args": {...},
                "content": "..."
            }
        """

        # Try to extract JSON from response
        try:
            # Look for JSON block
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]

                action_data = json.loads(json_str)

                if action_data.get("action") == "tool_call":
                    return {
                        "type": "tool_call",
                        "tool": action_data.get("tool"),
                        "args": action_data.get("args", {})
                    }
                elif action_data.get("action") == "final_answer":
                    return {
                        "type": "final_answer",
                        "content": action_data.get("content", "")
                    }
        except json.JSONDecodeError:
            logger.warning("⚠️ Could not parse JSON from response")

        # Default: treat as final answer
        return {
            "type": "final_answer",
            "content": response
        }

    async def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """
        Execute tool and return result

        NOTE: This is a stub - actual implementation will be in orchestration layer
        Tools will be injected via dependency injection when running in container

        Args:
            tool_name: Name of tool to execute
            args: Tool arguments

        Returns:
            Tool execution result as string
        """

        # TODO: Replace with actual tool execution via orchestration layer
        logger.info(f"🔧 Tool execution stub: {tool_name}({args})")

        return f"Tool {tool_name} executed successfully (stub implementation)"

    async def _publish_event(self, event_type: str, data: Dict[str, Any]):
        """
        Publish event to Redis for frontend streaming

        Args:
            event_type: Event type (agent_started, tool_execution, etc.)
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
            "workspace_files": len(self.workspace_files),
            "cost": 0.0,  # Always free!
            "models_used": list(self.models.values())
        }


# Global factory function
def create_local_mini_agent(
    task_id: str,
    session_id: str,
    **kwargs
) -> LocalMiniAgent:
    """
    Factory function to create local mini agent instance

    Args:
        task_id: Unique task identifier
        session_id: User session ID
        **kwargs: Additional configuration

    Returns:
        LocalMiniAgent instance
    """

    return LocalMiniAgent(
        task_id=task_id,
        session_id=session_id,
        **kwargs
    )
