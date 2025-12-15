"""
Codex CLI Engine

Executes agent tasks using OpenAI Codex CLI in Docker sandbox.
Provides autonomous code generation and execution capabilities.

NOTE: OpenAI Codex API has been deprecated. This implementation uses GPT-4
with code interpreter capabilities as a replacement, executed via CLI.
"""

from typing import Dict, Any, Optional, AsyncIterator
from .base import AgentEngine, EngineType
import asyncio
import json
import os
import logging
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CodexCLIEngine(AgentEngine):
    """
    Codex CLI engine for autonomous code generation and execution

    Runs in Docker sandbox with:
    - OpenAI API access (GPT-4 with code capabilities) via SecretsService
    - File system access to /workspace/
    - Python execution environment
    - Internet access (optional, controlled)

    Note: API key is retrieved from database via SecretsService, not environment variables
    """

    def __init__(self, db_session: Optional[AsyncSession] = None):
        """
        Initialize Codex CLI engine

        Args:
            db_session: Database session for retrieving API key from secrets service
        """
        super().__init__(EngineType.CODEX_CLI)
        self.db_session = db_session
        self.model = "gpt-4-turbo-preview"  # Best model for code tasks
        self.provider_name = "openai"  # Provider name in secrets service

    async def _get_api_key(self) -> Optional[str]:
        """
        Retrieve OpenAI API key from secrets service

        Returns:
            API key or None if not found
        """
        if not self.db_session:
            self.logger.error("❌ No database session provided to retrieve API key")
            return None

        try:
            from app.services.secrets_service import get_secrets_service

            secrets_service = get_secrets_service()
            api_key = await secrets_service.get_api_key(
                db=self.db_session,
                provider=self.provider_name
            )

            if not api_key:
                self.logger.warning(f"⚠️ No API key found for provider: {self.provider_name}")
                self.logger.info(f"💡 Please add API key via Admin UI: POST /api/v1/admin/secrets/api-keys")

            return api_key

        except Exception as e:
            self.logger.error(f"❌ Error retrieving API key: {e}")
            return None

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
        Execute task using Codex CLI

        This will:
        1. Retrieve API key from secrets service
        2. Create a task file with the description
        3. Execute openai CLI command in Docker
        4. Monitor output and artifacts
        5. Return results

        Note: API key is retrieved from database, not environment variables
        """
        self.logger.info(f"🤖 [Codex CLI] Executing: {task_description[:100]}")

        # Retrieve API key from secrets service
        api_key = await self._get_api_key()
        if not api_key:
            return {
                "success": False,
                "result": "",
                "artifacts": [],
                "iterations": 0,
                "duration_seconds": 0,
                "error": "OpenAI API key not configured. Please add it via Admin UI at /api/v1/admin/secrets/api-keys",
                "engine": self.engine_type.value,
                "model": model or self.model
            }

        used_model = model or self.model
        start_time = asyncio.get_event_loop().time()

        try:
            # Create task file
            task_file = Path(workspace_path) / "task.txt"
            task_file.write_text(task_description)

            # Build command to execute in agent-runtime container
            # Uses existing sandbox container (rag-agent-runtime) for isolation
            # Pass API key via environment variable
            command = [
                "docker", "exec", "-i",
                "-e", f"OPENAI_API_KEY={api_key}",  # Set API key in container environment
                "rag-agent-runtime",  # Reuse existing sandbox container
                "sh", "-c",  # Execute shell command
                f"echo '{task_description}' | openai api chat.completions.create -m {used_model}"
            ]

            # Execute in existing agent-runtime sandbox container
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,  # For interactive input
                env=os.environ
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_seconds
            )

            duration = asyncio.get_event_loop().time() - start_time

            # Parse output
            output = stdout.decode('utf-8')
            error_output = stderr.decode('utf-8')

            # Check for artifacts
            artifacts = []
            if Path(artifacts_path).exists():
                artifacts = [
                    str(p.relative_to(artifacts_path))
                    for p in Path(artifacts_path).rglob("*")
                    if p.is_file()
                ]

            if process.returncode == 0:
                return {
                    "success": True,
                    "result": output.strip() or "Task completed successfully",
                    "artifacts": artifacts,
                    "iterations": max_iterations,  # TODO: Parse from output
                    "duration_seconds": duration,
                    "error": None,
                    "engine": self.engine_type.value,
                    "model": used_model
                }
            else:
                return {
                    "success": False,
                    "result": "",
                    "artifacts": artifacts,
                    "iterations": 0,
                    "duration_seconds": duration,
                    "error": error_output or "Codex CLI execution failed",
                    "engine": self.engine_type.value,
                    "model": used_model
                }

        except asyncio.TimeoutError:
            duration = asyncio.get_event_loop().time() - start_time
            return {
                "success": False,
                "result": "",
                "artifacts": [],
                "iterations": 0,
                "duration_seconds": duration,
                "error": f"Execution timed out after {timeout_seconds} seconds",
                "engine": self.engine_type.value,
                "model": used_model
            }
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            self.logger.error(f"❌ Codex CLI execution error: {e}")
            return {
                "success": False,
                "result": "",
                "artifacts": [],
                "iterations": 0,
                "duration_seconds": duration,
                "error": str(e),
                "engine": self.engine_type.value,
                "model": used_model
            }

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
        Stream events from Codex CLI execution

        Monitors stdout/stderr and streams events as they occur
        """
        self.logger.info(f"🌊 [Codex CLI] Streaming: {task_description[:100]}")

        yield self._format_event(
            "status",
            status="running",
            message=f"Starting Codex CLI with {model or self.model}"
        )

        used_model = model or self.model

        # Retrieve API key from secrets service (same as execute method)
        api_key = await self._get_api_key()
        if not api_key:
            yield self._format_event(
                "error",
                error="OpenAI API key not configured. Please add it via Admin UI at /api/v1/admin/secrets/api-keys"
            )
            return

        try:
            # Create task file
            task_file = Path(workspace_path) / "task.txt"
            task_file.write_text(task_description)

            # Build command
            command = [
                "python",
                "-m", "codex_cli",
                "--task-file", str(task_file),
                "--workspace", workspace_path,
                "--artifacts", artifacts_path,
                "--model", used_model,
                "--max-iterations", str(max_iterations),
                "--timeout", str(timeout_seconds),
                "--stream"  # Enable streaming mode
            ]

            # Execute with streaming output
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "OPENAI_API_KEY": api_key}
            )

            # Stream stdout line by line
            async for line in process.stdout:
                line_str = line.decode('utf-8').strip()
                if not line_str:
                    continue

                # Try to parse as JSON event
                try:
                    event = json.loads(line_str)
                    yield self._format_event(
                        event.get("type", "log"),
                        **{k: v for k, v in event.items() if k != "type"}
                    )
                except json.JSONDecodeError:
                    # Plain text output - treat as log
                    yield self._format_event(
                        "log",
                        message=line_str
                    )

            # Wait for completion
            await process.wait()

            if process.returncode == 0:
                # Check for artifacts
                artifacts = []
                if Path(artifacts_path).exists():
                    artifacts = [
                        str(p.relative_to(artifacts_path))
                        for p in Path(artifacts_path).rglob("*")
                        if p.is_file()
                    ]

                yield self._format_event(
                    "completed",
                    result="Task completed successfully",
                    artifacts=artifacts,
                    iterations=max_iterations
                )
            else:
                stderr_output = await process.stderr.read()
                yield self._format_event(
                    "error",
                    error=stderr_output.decode('utf-8') or "Execution failed"
                )

        except Exception as e:
            self.logger.error(f"❌ Streaming error: {e}")
            yield self._format_event(
                "error",
                error=str(e)
            )

    async def cancel(self, execution_id: str) -> bool:
        """Cancel Codex CLI execution"""
        self.logger.info(f"🚫 [Codex CLI] Cancelling execution: {execution_id}")
        # TODO: Implement process tracking and cancellation
        return True

    async def health_check(self) -> Dict[str, Any]:
        """Check if Codex CLI is available"""
        try:
            # Check API key availability from database
            api_key = await self._get_api_key()

            # Try to run codex-cli --version
            process = await asyncio.create_subprocess_exec(
                "python", "-m", "codex_cli", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=5.0
            )

            if process.returncode == 0:
                version = stdout.decode('utf-8').strip()
                return {
                    "available": True,
                    "version": version,
                    "message": "Codex CLI is available",
                    "details": {
                        "model": self.model,
                        "api_key_set": bool(api_key),
                        "api_key_source": "database (secrets service)" if api_key else "not configured",
                        "capabilities": [
                            "Code generation",
                            "Code execution",
                            "File operations",
                            "Data analysis"
                        ]
                    }
                }
            else:
                return {
                    "available": False,
                    "version": None,
                    "message": "Codex CLI command failed",
                    "details": {"error": stderr.decode('utf-8')}
                }

        except FileNotFoundError:
            return {
                "available": False,
                "version": None,
                "message": "Codex CLI not installed",
                "details": {
                    "note": "Install with: pip install codex-cli",
                    "fallback": "Can use OpenAI API directly"
                }
            }
        except Exception as e:
            return {
                "available": False,
                "version": None,
                "message": f"Health check failed: {str(e)}",
                "details": {}
            }
