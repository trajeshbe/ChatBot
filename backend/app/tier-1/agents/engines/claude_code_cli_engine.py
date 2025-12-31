"""
Claude Code CLI Engine

Executes agent tasks using Anthropic Claude Code CLI in Docker sandbox.
Provides autonomous code generation and execution capabilities using Claude.
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


class ClaudeCodeCLIEngine(AgentEngine):
    """
    Claude Code CLI engine for autonomous code generation and execution

    Runs in Docker sandbox with:
    - Anthropic API access (Claude 3.5 Sonnet) via SecretsService
    - File system access to /workspace/
    - Python execution environment
    - Internet access (optional, controlled)

    Note: API key is retrieved from database via SecretsService, not environment variables
    """

    def __init__(self, db_session: Optional[AsyncSession] = None):
        """
        Initialize Claude Code CLI engine

        Args:
            db_session: Database session for retrieving API key from secrets service
        """
        super().__init__(EngineType.CLAUDE_CODE_CLI)
        self.db_session = db_session
        self.model = "claude-3-5-sonnet-20241022"  # Latest Claude model
        self.provider_name = "anthropic"  # Provider name in secrets service

    async def _get_api_key(self) -> Optional[str]:
        """
        Retrieve Anthropic API key from secrets service

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
        interactive: bool = False,  # ✅ NEW: Enable PTY for interactive sessions
        task_id: Optional[str] = None,  # ✅ NEW: Required for PTY sessions
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute task using Claude Code CLI

        This will:
        1. Retrieve API key from secrets service
        2. Create a task file with the description
        3. Execute claude-code command in Docker (with PTY if interactive=True)
        4. Monitor output and artifacts
        5. Return results

        Args:
            interactive: If True, creates PTY session for bidirectional I/O
            task_id: Required when interactive=True for session management

        Note: API key is retrieved from database, not environment variables
        """
        self.logger.info(f"🤖 [Claude Code] Executing: {task_description[:100]}")

        # Retrieve API key from secrets service (optional - Claude CLI can use OAuth)
        api_key = await self._get_api_key()
        if not api_key:
            self.logger.info("ℹ️ No API key found - Claude CLI will use OAuth authentication")
            self.logger.info("💡 If not authenticated, run: docker exec -it rag-agent-runtime claude login")

        used_model = model or self.model
        start_time = asyncio.get_event_loop().time()

        try:
            # Create task file
            task_file = Path(workspace_path) / "task.txt"
            task_file.write_text(task_description)

            # ✅ NEW: Check if interactive mode is requested
            if interactive:
                return await self._execute_interactive(
                    task_description,
                    api_key,
                    workspace_path,
                    artifacts_path,
                    task_id,
                    timeout_seconds,
                    used_model
                )

            # Build command to execute Claude CLI in agent-runtime container (non-interactive)
            # Uses existing sandbox container (rag-agent-runtime) for isolation
            # Pass API key via environment variable (if available), otherwise use OAuth
            command = ["docker", "exec", "-i"]

            if api_key:
                # Use API key if provided
                command.extend(["-e", f"ANTHROPIC_API_KEY={api_key}"])

            command.extend([
                "-w", "/workspace",  # Set working directory
                "rag-agent-runtime",  # Reuse existing sandbox container
                "claude", ".",  # ✅ Launch Claude in current directory
                task_description  # ✅ Pass task description as prompt argument
            ])

            # Execute in existing agent-runtime sandbox container
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,  # For interactive auth
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
                    "error": error_output or "Claude Code execution failed",
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
            self.logger.error(f"❌ Claude Code execution error: {e}")
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
        Stream events from Claude Code execution

        Monitors stdout/stderr and streams events as they occur
        """
        self.logger.info(f"🌊 [Claude Code] Streaming: {task_description[:100]}")

        yield self._format_event(
            "status",
            status="running",
            message=f"Starting Claude Code with {model or self.model}"
        )

        used_model = model or self.model

        # Retrieve API key from secrets service (optional - Claude CLI can use OAuth)
        api_key = await self._get_api_key()
        if not api_key:
            self.logger.info("ℹ️ No API key found - Claude CLI will use OAuth authentication")
            yield self._format_event(
                "log",
                message="Using Claude CLI OAuth authentication (no API key configured)"
            )

        try:
            # Create task file
            task_file = Path(workspace_path) / "task.txt"
            task_file.write_text(task_description)

            # Build command with optional API key (uses OAuth if not provided)
            command = ["docker", "exec", "-i"]

            if api_key:
                command.extend(["-e", f"ANTHROPIC_API_KEY={api_key}"])

            command.extend([
                "-w", "/workspace",  # Set working directory
                "rag-agent-runtime",
                "claude", ".",  # ✅ Launch Claude in current directory
                task_description  # ✅ Pass task description as prompt argument
            ])

            # Execute with streaming output in existing sandbox
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
                env=os.environ
            )

            # Stream stdout line by line
            # ✅ FIX: Stream as terminal output for interactive Claude display
            async for line in process.stdout:
                line_str = line.decode('utf-8').rstrip('\n')  # Keep formatting but remove trailing newline

                # ✅ NEW: Send as terminal_output event for real-time display
                yield self._format_event(
                    "terminal_output",
                    output=line_str,
                    stream="stdout"
                )

                # Also try to parse as JSON event for structured data
                if line_str.strip():
                    try:
                        event = json.loads(line_str.strip())
                        yield self._format_event(
                            event.get("type", "log"),
                            **{k: v for k, v in event.items() if k != "type"}
                        )
                    except json.JSONDecodeError:
                        # Not JSON, already sent as terminal_output above
                        pass

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
        """Cancel Claude Code execution"""
        self.logger.info(f"🚫 [Claude Code] Cancelling execution: {execution_id}")
        # TODO: Implement process tracking and cancellation
        return True

    async def _check_claude_auth(self) -> bool:
        """
        Check if Claude CLI is authenticated by verifying session files exist

        ✅ FIX: Check for actual session files, not just the directory

        Returns:
            True if authenticated, False otherwise
        """
        try:
            # Check if session files exist (Claude stores auth in ~/.anthropic/)
            # We need to verify there are actual files, not just an empty directory
            process = await asyncio.create_subprocess_exec(
                "docker", "exec", "rag-agent-runtime",
                "bash", "-c", "test -f ~/.anthropic/session || test -f ~/.anthropic/config.json && echo 'authenticated' || echo 'not_authenticated'",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=5.0)
            result = stdout.decode('utf-8').strip()
            return result == 'authenticated'
        except Exception as e:
            self.logger.error(f"Error checking Claude authentication: {e}")
            return False

    async def _execute_interactive(
        self,
        task_description: str,
        api_key: str,
        workspace_path: str,
        artifacts_path: str,
        task_id: str,
        timeout_seconds: int,
        model: str
    ) -> Dict[str, Any]:
        """
        Execute Claude CLI in interactive PTY mode

        Creates a PTY session that allows bidirectional communication via WebSocket.
        User can type responses to Claude's prompts through the terminal UI.

        ✨ NEW: Automatically handles OAuth authentication flow if not authenticated

        Args:
            task_description: Task to execute
            api_key: Anthropic API key (optional - will use OAuth if not provided)
            workspace_path: Working directory
            artifacts_path: Path for generated artifacts
            task_id: Unique task ID for session management
            timeout_seconds: Execution timeout
            model: Claude model to use

        Returns:
            Dict with success status and session info
        """
        from app.services.terminal_session_manager import create_terminal_session

        self.logger.info(f"🖥️ [Claude Code] Starting interactive session for task: {task_id}")

        try:
            # Check if Claude is authenticated (if no API key provided)
            is_authenticated = await self._check_claude_auth()

            # ✅ FIX: Use ptyprocess for true PTY support - Claude CLI needs a real TTY
            # ⚠️ NOTE: Claude CLI syntax is: claude [options] [command] [prompt]
            # NOT: claude . --task "prompt" (--task flag doesn't exist!)

            # ✅ FIX: When using ptyprocess, DON'T use docker exec -it flags
            # ptyprocess creates the PTY on the host, docker should just exec the command

            # ✅ FIX: If not authenticated, start Claude interactively and show message
            # User needs to type /login inside the Claude session to authenticate via OAuth
            # ✅ FIX: Use custom Python PTY wrapper to properly allocate PTY inside container
            # This ensures stdin/stdout are correctly bridged to the PTY for full interactivity

            # Sanitize task description: replace newlines with spaces and escape single quotes
            sanitized_description = task_description.replace('\n', ' ').replace('\r', ' ').replace("'", "'\\''")

            if not api_key and not is_authenticated:
                # Start Claude interactively - user will see "Invalid API key" message
                # and can type /login to start OAuth flow
                self.logger.info("🔐 Claude not authenticated - starting interactive session")
                self.logger.info("💡 User will need to type /login in the terminal to authenticate")
                # Don't use API key, let user login interactively
                # NO pty_wrapper - ptyprocess on host + docker exec -it handles PTY
                bash_cmd = f"cd /workspace && claude . '{sanitized_description}'"
            else:
                # Already authenticated or using API key
                # Pass API key as environment variable
                # NO pty_wrapper - ptyprocess on host + docker exec -it handles PTY
                bash_cmd = f"cd /workspace && ANTHROPIC_API_KEY='{api_key}' claude . '{sanitized_description}'"

            command = [
                "docker", "exec", "-it",  # ✅ Use -it flags with ptyprocess on host
                "rag-agent-runtime",
                "/bin/bash", "-c", bash_cmd
            ]

            # Create terminal session - use ptyprocess on host with docker exec -it
            # ✅ FIX: use_pty=True to use ptyprocess on host
            # ptyprocess allocates PTY on host, docker exec -it allocates TTY in container
            # This creates proper PTY bridge: ptyprocess (host) ↔ docker -it (container) ↔ claude
            session = await create_terminal_session(
                task_id=task_id,
                command=command,
                cwd=workspace_path,
                env={"ANTHROPIC_API_KEY": api_key} if api_key else {},
                use_pty=True  # ✅ Use ptyprocess on host for proper PTY allocation
            )

            self.logger.info(f"✅ Interactive terminal session created for task: {task_id}")

            # Return immediately - execution continues via PTY/WebSocket
            return {
                "success": True,
                "result": "Interactive session started. Connect via WebSocket to interact." +
                         (" OAuth authentication required - follow prompts in terminal." if not api_key and not is_authenticated else ""),
                "artifacts": [],
                "iterations": 0,
                "duration_seconds": 0,
                "error": None,
                "engine": self.engine_type.value,
                "model": model,
                "interactive": True,
                "session_id": task_id,
                "needs_auth": not api_key and not is_authenticated
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to start interactive session: {e}")
            return {
                "success": False,
                "result": "",
                "artifacts": [],
                "iterations": 0,
                "duration_seconds": 0,
                "error": f"Failed to start interactive session: {str(e)}",
                "engine": self.engine_type.value,
                "model": model
            }

    async def health_check(self) -> Dict[str, Any]:
        """Check if Claude Code CLI is available in agent-runtime container"""
        try:
            # Check API key availability from database
            api_key = await self._get_api_key()

            # Check if claude CLI is available in agent-runtime container
            process = await asyncio.create_subprocess_exec(
                "docker", "exec", "rag-agent-runtime",
                "which", "claude",
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
                    "message": "Claude Code CLI is available",
                    "details": {
                        "model": self.model,
                        "api_key_set": bool(api_key),
                        "api_key_source": "database (secrets service)" if api_key else "not configured",
                        "capabilities": [
                            "Code generation",
                            "Code execution",
                            "File operations",
                            "Data analysis",
                            "Long context (200k tokens)",
                            "Advanced reasoning"
                        ]
                    }
                }
            else:
                return {
                    "available": False,
                    "version": None,
                    "message": "Claude Code CLI command failed",
                    "details": {"error": stderr.decode('utf-8')}
                }

        except FileNotFoundError:
            return {
                "available": False,
                "version": None,
                "message": "Claude Code CLI not installed",
                "details": {
                    "note": "Install with: pip install claude-code-cli",
                    "fallback": "Can use Anthropic API directly",
                    "documentation": "https://docs.anthropic.com/claude/docs/claude-code"
                }
            }
        except Exception as e:
            return {
                "available": False,
                "version": None,
                "message": f"Health check failed: {str(e)}",
                "details": {}
            }
