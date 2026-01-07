"""
Agent Orchestration Service

Manages creation, execution, and monitoring of autonomous agent tasks.
Executes tasks in the agent-runtime container via Docker.
"""

import logging
import uuid
import subprocess
import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.database import AgentTask
from app.schemas.agent_schemas import (
    AgentTaskCreate,
    AgentTaskResponse,
    AgentTaskStatusResponse,
    AgentTaskList,
    TaskStatus
)
from app.services.system_config_service import SystemConfigService

logger = logging.getLogger(__name__)


class AgentOrchestrationService:
    """Service for orchestrating agent task execution"""

    # 🆕 FIX: Track running processes for cancellation
    _running_processes: Dict[str, asyncio.subprocess.Process] = {}

    def __init__(self, db: AsyncSession):
        self.db = db
        self.config_service = SystemConfigService(db)

    async def _generate_task_name(self, task_description: str) -> str:
        """
        Generate a concise, human-readable name for a task using LLM.

        Args:
            task_description: Full task description from user

        Returns:
            Short name (e.g., "sales_analysis_chart", "data_processing_pipeline")

        Examples:
            "use sales2.txt and create a plotly chart" → "sales_analysis_chart"
            "analyze customer data and generate report" → "customer_analysis_report"
            "scrape website and extract product info" → "website_product_scraper"
        """
        import re
        from app.services.llm_service import LLMService

        prompt = f"""Generate a short, descriptive name (3-5 words, snake_case) for this task:

Task: {task_description}

Requirements:
- Use snake_case (lowercase with underscores)
- Be specific and descriptive
- 3-5 words maximum
- No special characters
- Focus on the main action and output

Examples:
"analyze sales data" → "sales_data_analysis"
"create chart from CSV" → "csv_chart_generation"
"scrape news articles" → "news_article_scraper"

Task name:"""

        try:
            # Use lightweight model for quick response
            from app.core.config import settings
            import httpx

            # Try Ollama first (free, fast)
            try:
                # Get default model from system config
                default_model = await self.config_service.get(
                    'agent.runtime.default_model',
                    default='qwen2.5-coder:7b'
                )

                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        f"{settings.OLLAMA_BASE_URL}/api/generate",
                        json={
                            "model": default_model,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.3,
                                "num_predict": 50
                            }
                        }
                    )
                    if response.status_code == 200:
                        result = response.json()
                        task_name = result.get("response", "").strip().lower()
                    else:
                        raise Exception("Ollama request failed")
            except Exception as e:
                logger.warning(f"Ollama task name generation failed: {e}, using fallback")
                # Fallback: Simple rule-based generation
                task_name = task_description.lower()
                task_name = re.sub(r'[^a-z0-9\s]', '', task_name)
                words = task_name.split()[:5]  # Take first 5 words
                task_name = '_'.join(words)

            # Sanitize
            task_name = re.sub(r'[^a-z0-9_]', '', task_name)
            task_name = re.sub(r'_+', '_', task_name).strip('_')

            # Fallback if generation fails
            if not task_name or len(task_name) < 3:
                task_name = "agent_task"

            logger.info(f"✅ Generated task name: '{task_name}' from description: '{task_description[:50]}...'")
            return task_name

        except Exception as e:
            logger.warning(f"Failed to generate task name: {e}, using default")
            # Fallback: Use first few words
            import re
            task_name = task_description.lower()
            task_name = re.sub(r'[^a-z0-9\s]', '', task_name)
            words = task_name.split()[:3]
            return '_'.join(words) if words else "agent_task"

    async def create_task(
        self,
        request: AgentTaskCreate,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> AgentTaskResponse:
        """
        Create a new agent task

        Args:
            request: Task creation request
            user_id: ID of user creating the task
            project_id: ID of associated project

        Returns:
            AgentTaskResponse with task details
        """
        # Generate unique task ID
        task_id = f"task-{uuid.uuid4().hex[:12]}"

        # 🆕 Generate human-readable task name using LLM
        task_name = await self._generate_task_name(request.task_description)
        logger.info(f"📝 Generated task name: '{task_name}' for task {task_id}")

        # 🆕 Build MinIO base path - use current user's organizational structure
        from app.services.minio_path_builder import MinIOPathBuilder
        from app.models.database import Document
        from uuid import UUID

        # ✅ FIX: Always use current user's team, not outdated document paths
        # Build organizational path from user's current team association
        organizational_path = None
        from app.models.database_enhanced import User, Project
        from sqlalchemy import text

        username = "unknown"
        department_name = "Global"
        team_name = "General"
        project_name = "Default"

        # Get user details
        if user_id:
            try:
                result = await self.db.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                if user:
                    username = user.username

                    # Get user's department name
                    if user.department_id:
                        dept_query = text("SELECT name FROM departments WHERE id = :dept_id")
                        dept_result = await self.db.execute(dept_query, {"dept_id": str(user.department_id)})
                        dept_row = dept_result.first()
                        if dept_row:
                            department_name = dept_row[0]

                    # Get user's team name
                    team_query = text("""
                        SELECT t.name
                        FROM teams t
                        JOIN user_teams ut ON t.id = ut.team_id
                        WHERE ut.user_id = :user_id
                        ORDER BY ut.assigned_at DESC
                        LIMIT 1
                    """)
                    team_result = await self.db.execute(team_query, {"user_id": str(user.id)})
                    team_row = team_result.first()
                    if team_row:
                        team_name = team_row[0]
            except Exception as e:
                logger.warning(f"Failed to get user details: {e}")

        # Get project name
        if project_id:
            try:
                result = await self.db.execute(
                    select(Project).where(Project.id == project_id)
                )
                project = result.scalar_one_or_none()
                if project:
                    project_name = project.name
            except Exception as e:
                logger.warning(f"Failed to get project name: {e}")

        # Build organizational path: {dept}/{team}/{project}/{username}
        organizational_path = (
            f"{MinIOPathBuilder.sanitize(department_name)}/"
            f"{MinIOPathBuilder.sanitize(team_name)}/"
            f"{MinIOPathBuilder.sanitize(project_name)}/"
            f"{MinIOPathBuilder.sanitize(username)}"
        )
        logger.info(f"📁 Using user-based organizational path: {organizational_path}")

        # Build MinIO base path with organizational structure
        minio_base_path = (
            f"{organizational_path}/agent-tasks/"
            f"{MinIOPathBuilder.sanitize(task_name)}/{task_id}/"
        )
        logger.info(f"📦 MinIO base path: {minio_base_path}")

        # 🆕 Sync documents to agent workspace
        # Priority 1: Explicitly selected documents (document_ids)
        # Priority 2: Session documents (if session_id provided)
        try:
            if request.document_ids:
                logger.info(f"📂 Syncing {len(request.document_ids)} selected document(s) to workspace")
                await self._sync_documents_by_ids_to_workspace(request.document_ids)
            elif request.session_id:
                logger.info(f"📂 Syncing session documents to workspace for session: {request.session_id}")
                await self._sync_session_documents_to_workspace(request.session_id)
            else:
                logger.info("ℹ️ No documents specified - agent will use files already in /workspace/")
        except Exception as e:
            logger.warning(f"⚠️ Failed to sync documents to workspace: {e}")
            # Continue task creation - agent can still access workspace files uploaded via /upload-workspace-file

        # Validate and normalize engine selection
        engine = (request.engine or "default").lower()
        valid_engines = ["default", "codex-cli", "claude-code-cli"]
        if engine not in valid_engines:
            logger.warning(f"⚠️ Invalid engine '{engine}', defaulting to 'default'")
            engine = "default"

        # ✅ FIX: Store team and department for proper MinIO path structure
        # Extract from organizational_path if derived from documents, otherwise use queried values
        final_department = None
        final_team = None

        if organizational_path and request.document_ids:
            # Path was inherited from document - extract team/dept from it
            # Format: "technology/itm11/construction-intelligence/admin"
            path_parts = organizational_path.split('/')
            if len(path_parts) >= 2:
                final_department = path_parts[0]  # technology
                final_team = path_parts[1]  # itm11
        else:
            # Path was built from user details - use the queried values
            final_department = department_name
            final_team = team_name

        logger.info(f"🏢 Agent task organizational details: dept={final_department}, team={final_team}")

        # Get default model and configuration from system config
        default_model = await self.config_service.get(
            'agent.runtime.default_model',
            default='qwen2.5-coder:7b'
        )
        default_max_iterations = await self.config_service.get_int(
            'agent.runtime.max_iterations',
            default=20
        )
        default_timeout = await self.config_service.get_int(
            'agent.runtime.timeout_seconds',
            default=600
        )

        # Create database record
        agent_task = AgentTask(
            task_id=task_id,
            task_name=task_name,  # 🆕 NEW
            minio_base_path=minio_base_path,  # 🆕 NEW
            task_description=request.task_description,
            status=TaskStatus.PENDING,
            session_id=request.session_id,
            model=request.model or default_model,  # ✅ Dynamic from DB
            max_iterations=request.max_iterations or default_max_iterations,  # ✅ Dynamic from DB
            timeout_seconds=request.timeout_seconds or default_timeout,  # ✅ Dynamic from DB
            created_by=user_id,
            project_id=project_id,
            department=final_department,  # ✅ FIX: Populate department
            team=final_team,  # ✅ FIX: Populate team
            created_at=datetime.now()  # Set explicitly for immediate response
        )

        self.db.add(agent_task)
        await self.db.commit()
        await self.db.refresh(agent_task)

        logger.info(f"📝 Created agent task: {task_id} with engine: {engine}")

        # Execute task asynchronously (non-blocking) with selected engine
        asyncio.create_task(self._execute_task_async(task_id, engine))

        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message="Task created and queued for execution",
            created_at=agent_task.created_at
        )

    async def _execute_task_async(self, task_id: str, engine: str = "default"):
        """
        Execute agent task asynchronously using specified engine

        Args:
            task_id: Task identifier
            engine: Execution engine (default, codex-cli, or claude-code-cli)
        """
        # Route to appropriate engine
        if engine == "default":
            await self._execute_task_default_engine(task_id)
        elif engine in ["codex-cli", "claude-code-cli"]:
            await self._execute_task_cli_engine(task_id, engine)
        else:
            logger.error(f"❌ Unknown engine: {engine}")
            await self._execute_task_default_engine(task_id)  # Fallback

    async def _execute_task_default_engine(self, task_id: str):
        """
        Execute agent task asynchronously in agent-runtime container (DEFAULT engine)

        Args:
            task_id: Task identifier
        """
        # Create new database session for async task
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            try:
                # Get task from database
                result = await db.execute(
                    select(AgentTask).filter(AgentTask.task_id == task_id)
                )
                task = result.scalar_one_or_none()
                if not task:
                    logger.error(f"❌ Task not found: {task_id}")
                    return

                # Update status to running
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                await db.commit()

                logger.info(f"🚀 Executing agent task with DEFAULT engine: {task_id}")

                # 🆕 FIX: Clean up old artifacts from previous runs of this task_name
                # This prevents old artifacts from showing up in new task results
                try:
                    import subprocess
                    workspace_path = f"/workspace/{task.task_name}"
                    cleanup_cmd = [
                        "docker", "exec", "rag-agent-runtime",
                        "bash", "-c", f"rm -rf {workspace_path}/artifacts/* 2>/dev/null || true"
                    ]
                    subprocess.run(cleanup_cmd, capture_output=True, timeout=5)
                    logger.info(f"🧹 Cleaned up old artifacts from {workspace_path}/artifacts/")
                except Exception as e:
                    logger.warning(f"⚠️ Could not clean artifacts directory: {e}")

                # Build docker exec command to run task in agent-runtime container
                # SECURITY: Properly escape task description for shell safety
                # Base64 encode to avoid shell escaping issues with newlines and special chars
                import base64
                task_description_b64 = base64.b64encode(task.task_description.encode('utf-8')).decode('utf-8')

                # Get OpenAI API key from environment if available
                import os
                openai_api_key = os.getenv('OPENAI_API_KEY', '')

                # 🆕 Get username and project for MinIO paths
                username = "unknown"
                project_name = "global-project"
                if task.created_by:
                    try:
                        from app.models.database_enhanced import User
                        result = await session.execute(
                            select(User).where(User.id == task.created_by)
                        )
                        user = result.scalar_one_or_none()
                        if user:
                            username = user.username
                    except Exception as e:
                        logger.warning(f"Failed to get username: {e}")

                if task.project_id:
                    try:
                        from app.models.database_enhanced import Project
                        result = await session.execute(
                            select(Project).where(Project.id == task.project_id)
                        )
                        project = result.scalar_one_or_none()
                        if project:
                            project_name = project.name
                    except Exception as e:
                        logger.warning(f"Failed to get project: {e}")

                docker_command = [
                    "docker", "exec",
                    "-e", f"TASK_B64={task_description_b64}",
                    "-e", f"TASK_ID={task_id}",
                    "-e", f"TASK_NAME={task.task_name or 'agent_task'}",  # 🆕 NEW
                    "-e", f"USERNAME={username}",  # 🆕 NEW
                    "-e", f"PROJECT_NAME={project_name}",  # 🆕 NEW
                    "-e", f"SESSION_ID={task.session_id or 'default'}",
                    "-e", f"AGENT_LLM_MODEL={task.model}",
                    "-e", f"AGENT_MAX_ITERATIONS={task.max_iterations}",
                    "-e", f"AGENT_TIMEOUT_SECONDS={task.timeout_seconds}",
                    "-e", f"OPENAI_API_KEY={openai_api_key}",  # Pass OpenAI API key
                    "rag-agent-runtime",  # Container name from docker-compose
                    "python", "/app/entrypoint_agent.py"
                ]

                # Execute command with timeout
                process = await asyncio.create_subprocess_exec(
                    *docker_command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                # 🆕 FIX: Store process for cancellation
                AgentOrchestrationService._running_processes[task_id] = process
                logger.info(f"📍 Stored process for task {task_id}, PID: {process.pid}")

                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=task.timeout_seconds
                    )

                    # Decode output
                    stdout_str = stdout.decode('utf-8')
                    stderr_str = stderr.decode('utf-8')

                    # DEBUG: Log raw output to diagnose empty stdout issue
                    logger.info(f"🔍 DEBUG Task {task_id} - stdout length: {len(stdout_str)} chars")
                    logger.info(f"🔍 DEBUG Task {task_id} - stderr length: {len(stderr_str)} chars")
                    if stdout_str:
                        logger.info(f"🔍 DEBUG Task {task_id} - stdout preview: {stdout_str[:500]}")
                    if stderr_str:
                        logger.info(f"🔍 DEBUG Task {task_id} - stderr preview: {stderr_str[:500]}")

                    # Parse output and update task
                    await self._process_task_output(
                        db=db,
                        task_id=task_id,
                        stdout=stdout_str,
                        stderr=stderr_str,
                        return_code=process.returncode
                    )

                except asyncio.TimeoutError:
                    logger.error(f"⏱️ Task {task_id} timed out after {task.timeout_seconds}s")

                    # Kill the process
                    process.kill()
                    await process.wait()

                    # Update task as failed due to timeout
                    result = await db.execute(
                        select(AgentTask).filter(AgentTask.task_id == task_id)
                    )
                    task = result.scalar_one_or_none()
                    if task:
                        task.status = TaskStatus.FAILED
                        task.error = f"Task timed out after {task.timeout_seconds} seconds"
                        task.completed_at = datetime.now()
                        task.duration_seconds = (task.completed_at - task.started_at).total_seconds()
                        await db.commit()

                finally:
                    # 🆕 FIX: Clean up process reference after completion
                    if task_id in AgentOrchestrationService._running_processes:
                        del AgentOrchestrationService._running_processes[task_id]
                        logger.info(f"🧹 Removed process reference for task {task_id}")

            except Exception as e:
                logger.error(f"❌ Error executing task {task_id}: {e}")

                # Update task as failed
                result = await db.execute(
                    select(AgentTask).filter(AgentTask.task_id == task_id)
                )
                task = result.scalar_one_or_none()
                if task:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    task.error_details = {"exception": str(type(e).__name__)}
                    task.completed_at = datetime.now()
                    if task.started_at:
                        task.duration_seconds = (task.completed_at - task.started_at).total_seconds()
                    await db.commit()

    async def _process_task_output(
        self,
        db: AsyncSession,
        task_id: str,
        stdout: str,
        stderr: str,
        return_code: int
    ):
        """
        Process task execution output and update database

        Args:
            db: Database session
            task_id: Task identifier
            stdout: Standard output from execution
            stderr: Standard error from execution
            return_code: Process return code
        """
        result = await db.execute(
            select(AgentTask).filter(AgentTask.task_id == task_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            return

        task.completed_at = datetime.now()
        if task.started_at:
            task.duration_seconds = (task.completed_at - task.started_at).total_seconds()

        # IMPORTANT: Agent writes to stderr (Python logging default), so parse BOTH stdout and stderr
        combined_output = stdout + "\n" + stderr

        # NEW: Try to parse JSON result from stdout first (preferred method)
        agent_result = None
        if "AGENT_RESULT_JSON_START" in stdout and "AGENT_RESULT_JSON_END" in stdout:
            try:
                # Extract JSON between markers
                start_marker = "AGENT_RESULT_JSON_START"
                end_marker = "AGENT_RESULT_JSON_END"
                start_idx = stdout.find(start_marker) + len(start_marker)
                end_idx = stdout.find(end_marker)
                json_str = stdout[start_idx:end_idx].strip()

                # Parse JSON
                agent_result = json.loads(json_str)
                logger.info(f"✅ Successfully parsed agent result JSON from stdout")

                # Update task from parsed result
                # Always mark as COMPLETED (ChatGPT behavior - complete with whatever progress was made)
                # Store success flag in meta_info for tracking
                task.status = TaskStatus.COMPLETED
                task.result = agent_result.get("final_answer", "Task completed")
                task.llm_calls = agent_result.get("iterations", 0)

                # Extract artifacts from JSON result (primary source)
                artifacts = []
                if "artifacts" in agent_result and agent_result["artifacts"]:
                    # Artifacts are provided as list of dicts with 'path' key
                    for artifact in agent_result["artifacts"]:
                        if isinstance(artifact, dict):
                            path = artifact.get("path", "")
                        else:
                            path = str(artifact)
                        if path:
                            # Convert relative path to task-specific workspace path
                            if not path.startswith("/workspace/"):
                                # Use task_name for task-specific workspace
                                path = f"/workspace/{task.task_name}/{path}"
                            artifacts.append(path)
                    logger.info(f"📎 Extracted {len(artifacts)} artifacts from JSON result")

                # Fallback: Extract from final_answer if not in result
                if not artifacts:
                    import re
                    final_answer = agent_result.get("final_answer", "")
                    if final_answer:
                        # Extract file paths from final_answer (handles both absolute and relative paths)
                        # Match: /workspace/artifacts/file.html OR artifacts/file.html
                        matches = re.findall(r'(?:/workspace/)?(?:artifacts/)([\w\-\.]+\.(html|png|jpg|jpeg|pdf|csv|xlsx|json|txt|docx|svg))', final_answer)
                        for match_tuple in matches:
                            # match_tuple is (filename, extension), we want the full filename
                            filename = match_tuple[0]
                            # Use task_name for task-specific workspace
                            artifact_path = f"/workspace/{task.task_name}/artifacts/{filename}"
                            artifacts.append(artifact_path)
                        if matches:
                            logger.info(f"📎 Extracted {len(matches)} artifact paths from final_answer: {artifacts}")

                # Additional fallback: Extract from conversation history if still nothing
                # 🆕 FIX: Only extract files that were CREATED in this task (mentioned in tool RESULTS)
                if not artifacts:
                    import re
                    for msg in agent_result.get("conversation_history", []):
                        content = msg.get("content", "")
                        # Skip assistant messages (tool calls) - only look at tool results
                        if msg.get("role") == "assistant":
                            continue
                        # 🆕 FIX: Only look for files in execute_python results or write_file results
                        # Check if this is a tool result message (contains "SUCCESS:" or shows file creation)
                        if "SUCCESS:" in content or "saved" in content.lower() or "created" in content.lower() or "written" in content.lower():
                            # Extract file paths from this specific creation message
                            matches = re.findall(r'/workspace/[\w\-/]+\.(?:html|png|jpg|jpeg|pdf|csv|xlsx|json|txt|docx|svg)', content)
                            for match in matches:
                                # Only add if it's from this task's workspace
                                if f"/workspace/{task.task_name}/" in match or "/workspace/artifacts/" in match:
                                    artifacts.append(match)
                    if artifacts:
                        logger.info(f"📎 Extracted {len(artifacts)} artifact paths from tool creation messages")

                if artifacts:
                    task.artifacts = list(set(artifacts))  # Remove duplicates

                # Extract tools used from conversation history
                tools = []
                for msg in agent_result.get("conversation_history", []):
                    content = msg.get("content", "")
                    if content.startswith("TOOL_CALL:"):
                        tool_name = content.split("\n")[0].replace("TOOL_CALL:", "").strip()
                        if tool_name and tool_name not in tools:
                            tools.append(tool_name)
                if tools:
                    task.tools_used = tools

                # Store conversation_history in meta_info for UI access (code viewer)
                conversation_history = agent_result.get("conversation_history", [])
                if conversation_history:
                    task.meta_info = task.meta_info or {}
                    task.meta_info["conversation_history"] = conversation_history
                    logger.info(f"💾 Stored conversation_history ({len(conversation_history)} messages) in meta_info")

                logger.info(f"✅ Task {task_id} completed with parsed JSON result")

                # 🆕 Upload artifacts to MinIO
                if task.artifacts and task.minio_base_path:
                    await self._upload_artifacts_to_minio(task)

            except Exception as e:
                logger.warning(f"⚠️ Failed to parse agent result JSON: {e}, falling back to log parsing")
                agent_result = None

        # FALLBACK: If JSON parsing failed or not available, use legacy log parsing
        if agent_result is None:
            # Determine success/failure based on return code
            if return_code == 0:
                task.status = TaskStatus.COMPLETED

                # Parse output for results
                # Look for completion markers in order of preference:
                # 1. "✅ Task completed" with result
                # 2. Last tool execution result
                # 3. Success message with iteration count
                task.result = "Task completed successfully"

                if "✅ Task completed" in combined_output:
                    # Extract result after completion marker
                    lines = combined_output.split('\n')
                    for i, line in enumerate(lines):
                        if '✅ Task completed' in line and i + 1 < len(lines):
                            # Get next non-empty line as result
                            for j in range(i + 1, len(lines)):
                                if lines[j].strip() and not lines[j].strip().startswith('2025-'):
                                    task.result = lines[j].strip()
                                    break
                            break
                elif "📊 Iterations:" in combined_output:
                    # Agent completed all iterations - extract summary
                    iteration_count = combined_output.count('📍 Iteration')
                    tool_calls = combined_output.count('TOOL_CALL:')
                    task.result = f"Agent completed {iteration_count} iterations with {tool_calls} tool calls"

                # Extract artifacts (look for artifact paths in output)
                artifacts = []
                for line in combined_output.split('\n'):
                    if '/artifacts/' in line or '/workspace/' in line:
                        # Simple extraction - can be enhanced
                        if '.txt' in line or '.csv' in line or '.png' in line or '.html' in line:
                            artifacts.append(line.strip())

                if artifacts:
                    task.artifacts = artifacts

                # Extract tools used (look for TOOL_CALL mentions)
                tools = []
                for line in combined_output.split('\n'):
                    if 'TOOL_CALL:' in line or 'Executing tool:' in line:
                        parts = line.split(':')
                        if len(parts) > 1:
                            tool_name = parts[1].strip()
                            if tool_name and tool_name not in tools:
                                tools.append(tool_name)

                if tools:
                    task.tools_used = tools

                # Count LLM calls
                llm_calls = combined_output.count('Calling LLM') or combined_output.count('🤖')
                if llm_calls > 0:
                    task.llm_calls = llm_calls

                logger.info(f"✅ Task {task_id} completed successfully (legacy parsing)")
            else:
                task.status = TaskStatus.FAILED
                task.error = f"Task failed with return code {return_code}"

                # Capture error details from stderr
                if stderr:
                    task.error_details = {"stderr": stderr[:1000]}  # Limit size

                logger.error(f"❌ Task {task_id} failed with return code {return_code}")

        await db.commit()

    async def _upload_artifacts_to_minio(self, task: AgentTask):
        """
        Upload agent task artifacts from container to MinIO storage

        Reads artifact files from the agent-runtime container and uploads them to MinIO
        at the task's minio_base_path location.

        Args:
            task: AgentTask with artifacts list and minio_base_path
        """
        import subprocess
        import io
        import mimetypes
        from pathlib import Path
        from minio import Minio
        from app.core.config import settings

        if not task.artifacts:
            logger.info(f"No artifacts to upload for task {task.task_id}")
            return

        if not task.minio_base_path:
            logger.warning(f"No minio_base_path set for task {task.task_id}, skipping upload")
            return

        logger.info(f"📤 Uploading {len(task.artifacts)} artifact(s) to MinIO for task {task.task_id}")

        # Initialize MinIO client
        minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )

        uploaded_count = 0
        for artifact_path in task.artifacts:
            try:
                # Extract filename from path (e.g., "/workspace/artifacts/chart.html" → "chart.html")
                artifact_name = Path(artifact_path).name

                # Read file from agent-runtime container
                logger.info(f"📥 Reading artifact from container: {artifact_path}")
                read_cmd = [
                    "docker", "exec", "rag-agent-runtime",
                    "cat", artifact_path
                ]
                result = subprocess.run(read_cmd, capture_output=True, timeout=30)

                if result.returncode != 0:
                    logger.error(f"❌ Failed to read {artifact_path} from container: {result.stderr.decode()}")
                    continue

                file_data = result.stdout

                # Determine content type
                content_type, _ = mimetypes.guess_type(artifact_name)
                if not content_type:
                    content_type = "application/octet-stream"

                # Construct MinIO path with artifacts/ subfolder (e.g., "projects/.../task-id/artifacts/chart.html")
                minio_object_path = f"{task.minio_base_path}artifacts/{artifact_name}"

                # Upload to MinIO
                minio_client.put_object(
                    settings.MINIO_BUCKET_NAME,
                    minio_object_path,
                    io.BytesIO(file_data),
                    length=len(file_data),
                    content_type=content_type
                )

                logger.info(f"✅ Uploaded {artifact_name} to MinIO: {minio_object_path} ({len(file_data)} bytes)")
                uploaded_count += 1

            except subprocess.TimeoutExpired:
                logger.error(f"⏱️ Timeout reading artifact {artifact_path} from container")
            except Exception as e:
                logger.error(f"❌ Failed to upload artifact {artifact_path}: {e}")

        logger.info(f"🎉 Uploaded {uploaded_count}/{len(task.artifacts)} artifacts to MinIO")

    async def _sync_session_documents_to_workspace(self, session_id: str):
        """
        Sync all session documents from MinIO to agent workspace

        Downloads all documents associated with a session from MinIO and copies them
        to the /workspace/ directory so the agent can access them.

        Args:
            session_id: Session ID to sync documents for
        """
        from minio import Minio
        from app.core.config import settings
        from app.models.database_enhanced import ChatSession, SessionDocument
        from app.models.database import Document
        from pathlib import Path
        import io

        logger.info(f"🔄 Syncing session documents to workspace for session: {session_id}")

        # Get session from database
        session_query = select(ChatSession).where(ChatSession.session_id == session_id)
        session_result = await self.db.execute(session_query)
        session = session_result.scalar_one_or_none()

        if not session:
            logger.warning(f"Session not found: {session_id}")
            return

        # Get all documents for this session
        documents_query = (
            select(Document)
            .join(SessionDocument, Document.id == SessionDocument.document_id)
            .where(SessionDocument.session_id == session.session_id)
        )
        documents_result = await self.db.execute(documents_query)
        documents = documents_result.scalars().all()

        if not documents:
            logger.info(f"No documents found for session: {session_id}")
            return

        logger.info(f"📁 Found {len(documents)} document(s) to sync")

        # Initialize MinIO client
        minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )

        # Sync each document
        synced_count = 0
        for doc in documents:
            try:
                # Download from MinIO
                response = minio_client.get_object(
                    settings.MINIO_BUCKET_NAME,
                    doc.minio_path or doc.file_path
                )
                file_content = response.read()
                response.close()
                response.release_conn()

                # Write to workspace
                workspace_path = Path(f"/workspace/{doc.filename}")
                workspace_path.parent.mkdir(parents=True, exist_ok=True)

                with open(workspace_path, "wb") as f:
                    f.write(file_content)

                logger.info(f"✅ Synced {doc.filename} to workspace ({len(file_content)} bytes)")
                synced_count += 1

            except Exception as e:
                logger.error(f"❌ Failed to sync {doc.filename}: {e}")

        logger.info(f"🎉 Synced {synced_count}/{len(documents)} documents to workspace")

    async def _sync_documents_by_ids_to_workspace(self, document_ids: List[str]):
        """
        Sync specific documents by their IDs from MinIO to agent workspace

        Downloads specified documents from MinIO and copies them to the /workspace/
        directory so the agent can access them.

        Args:
            document_ids: List of document IDs (UUIDs as strings) to sync
        """
        from minio import Minio
        from app.core.config import settings
        from app.models.database import Document
        from pathlib import Path
        from uuid import UUID

        if not document_ids:
            logger.info("No document IDs provided for syncing")
            return

        logger.info(f"🔄 Syncing {len(document_ids)} selected document(s) to workspace")

        # Convert string IDs to UUIDs
        uuid_list = []
        for doc_id in document_ids:
            try:
                uuid_list.append(UUID(doc_id))
            except ValueError:
                logger.warning(f"Invalid document ID format: {doc_id}")

        if not uuid_list:
            logger.warning("No valid document IDs to sync")
            return

        # Get documents from database
        documents_query = select(Document).where(Document.id.in_(uuid_list))
        documents_result = await self.db.execute(documents_query)
        documents = documents_result.scalars().all()

        if not documents:
            logger.warning(f"No documents found for IDs: {document_ids}")
            return

        logger.info(f"📁 Found {len(documents)} document(s) in database")

        # Initialize MinIO client
        minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )

        # Sync each document
        synced_count = 0
        for doc in documents:
            try:
                # Download from MinIO
                minio_path = doc.minio_path or doc.file_path
                logger.info(f"📥 Downloading {doc.filename} from MinIO: {minio_path}")

                response = minio_client.get_object(
                    settings.MINIO_BUCKET_NAME,
                    minio_path
                )
                file_content = response.read()
                response.close()
                response.release_conn()

                # Write to workspace
                workspace_path = Path(f"/workspace/{doc.filename}")
                workspace_path.parent.mkdir(parents=True, exist_ok=True)

                with open(workspace_path, "wb") as f:
                    f.write(file_content)

                logger.info(f"✅ Synced {doc.filename} to /workspace/ ({len(file_content)} bytes)")
                synced_count += 1

            except Exception as e:
                logger.error(f"❌ Failed to sync {doc.filename}: {e}")

        logger.info(f"🎉 Synced {synced_count}/{len(documents)} selected documents to workspace")

    async def get_task_status(self, task_id: str) -> Optional[AgentTaskStatusResponse]:
        """
        Get detailed status of an agent task

        Args:
            task_id: Task identifier

        Returns:
            AgentTaskStatusResponse or None if not found
        """
        result = await self.db.execute(
            select(AgentTask).filter(AgentTask.task_id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            return None

        # 🆕 FIX: Use minio_base_path from database, or construct from task_name if available
        minio_base_path = task.minio_base_path  # Use stored path if available
        if not minio_base_path and task.task_name:
            # Fallback: construct from database fields
            username = "unknown"  # Default until user auth is fully integrated
            project_name = "global-project"  # Default project
            # Path format: projects/{project}/{user}/agent-tasks/{task_name}/{task_id}/
            minio_base_path = f"projects/{project_name}/{username}/agent-tasks/{task.task_name}/{task.task_id}/"

        return AgentTaskStatusResponse(
            task_id=task.task_id,
            status=task.status,
            task_description=task.task_description,
            session_id=task.session_id,
            model=task.model,
            current_iteration=task.current_iteration,
            max_iterations=task.max_iterations,
            started_at=task.started_at,
            completed_at=task.completed_at,
            duration_seconds=task.duration_seconds,
            result=task.result,
            artifacts=task.artifacts or [],
            tools_used=task.tools_used or [],
            llm_calls=task.llm_calls,
            error=task.error,
            error_details=task.error_details,
            created_at=task.created_at,
            meta_info=task.meta_info,
            minio_base_path=minio_base_path  # 🆕 FIX: Include MinIO path
        )

    async def list_tasks(
        self,
        session_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        page: int = 1,
        page_size: int = 50
    ) -> AgentTaskList:
        """
        List agent tasks with optional filtering

        Args:
            session_id: Filter by session ID
            status: Filter by task status
            page: Page number (1-indexed)
            page_size: Number of tasks per page

        Returns:
            AgentTaskList with tasks and pagination info
        """
        # Build query
        query = select(AgentTask)

        # Apply filters
        if session_id:
            query = query.filter(AgentTask.session_id == session_id)

        if status:
            query = query.filter(AgentTask.status == status)

        # Get total count
        count_query = select(AgentTask.id)
        if session_id:
            count_query = count_query.filter(AgentTask.session_id == session_id)
        if status:
            count_query = count_query.filter(AgentTask.status == status)

        count_result = await self.db.execute(count_query)
        total = len(count_result.all())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(desc(AgentTask.created_at)).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        tasks = result.scalars().all()

        # Convert to response schema
        task_responses = []
        for task in tasks:
            # 🆕 FIX: Use minio_base_path from database, or construct from task_name if available
            minio_base_path = task.minio_base_path  # Use stored path if available
            if not minio_base_path and task.task_name:
                # Fallback: construct from database fields
                username = "unknown"  # Default until user auth is fully integrated
                project_name = "global-project"  # Default project
                # Path format: projects/{project}/{user}/agent-tasks/{task_name}/{task_id}/
                minio_base_path = f"projects/{project_name}/{username}/agent-tasks/{task.task_name}/{task.task_id}/"

            task_responses.append(AgentTaskStatusResponse(
                task_id=task.task_id,
                status=task.status,
                task_description=task.task_description,
                session_id=task.session_id,
                model=task.model,
                current_iteration=task.current_iteration,
                max_iterations=task.max_iterations,
                started_at=task.started_at,
                completed_at=task.completed_at,
                duration_seconds=task.duration_seconds,
                result=task.result,
                artifacts=task.artifacts or [],
                tools_used=task.tools_used or [],
                llm_calls=task.llm_calls,
                error=task.error,
                error_details=task.error_details,
                created_at=task.created_at,
                meta_info=task.meta_info,
                minio_base_path=minio_base_path  # 🆕 FIX: Include MinIO path
            ))

        return AgentTaskList(
            tasks=task_responses,
            total=total,
            page=page,
            page_size=page_size
        )

    async def _execute_task_cli_engine(self, task_id: str, engine: str):
        """
        Execute agent task using CLI engine (Codex CLI or Claude Code CLI)

        Args:
            task_id: Task identifier
            engine: Engine name (codex-cli or claude-code-cli)
        """
        from app.core.database import AsyncSessionLocal
        from app.services.engines import CodexCLIEngine, ClaudeCodeCLIEngine, EngineType
        from pathlib import Path

        async with AsyncSessionLocal() as db:
            try:
                # Get task from database
                result = await db.execute(
                    select(AgentTask).filter(AgentTask.task_id == task_id)
                )
                task = result.scalar_one_or_none()
                if not task:
                    logger.error(f"❌ Task not found: {task_id}")
                    return

                # Update status to running
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                await db.commit()

                logger.info(f"🚀 Executing agent task with {engine.upper()} engine: {task_id}")

                # Create workspace and artifacts directories
                workspace_path = f"/workspace/{task.task_name or task_id}"
                artifacts_path = f"{workspace_path}/artifacts"

                Path(workspace_path).mkdir(parents=True, exist_ok=True)
                Path(artifacts_path).mkdir(parents=True, exist_ok=True)

                # Instantiate the appropriate engine with database session
                # Database session is required to retrieve API keys from secrets service
                if engine == "codex-cli":
                    cli_engine = CodexCLIEngine(db_session=db)
                elif engine == "claude-code-cli":
                    cli_engine = ClaudeCodeCLIEngine(db_session=db)
                else:
                    raise ValueError(f"Unknown engine: {engine}")

                # Execute task using the CLI engine
                # ✅ For Claude Code CLI, use interactive mode for terminal UI
                if engine == "claude-code-cli":
                    result_dict = await cli_engine.execute(
                        task_description=task.task_description,
                        workspace_path=workspace_path,
                        artifacts_path=artifacts_path,
                        max_iterations=task.max_iterations,
                        timeout_seconds=task.timeout_seconds,
                        model=task.model,
                        interactive=True,  # Enable PTY for interactive terminal
                        task_id=task_id    # Required for WebSocket terminal session
                    )
                else:
                    result_dict = await cli_engine.execute(
                        task_description=task.task_description,
                        workspace_path=workspace_path,
                        artifacts_path=artifacts_path,
                        max_iterations=task.max_iterations,
                        timeout_seconds=task.timeout_seconds,
                        model=task.model
                    )

                # Update task with results
                # ✅ FIX: For interactive tasks, keep status as RUNNING (don't mark as completed)
                if result_dict.get("interactive"):
                    # Interactive task - terminal session is active, keep status as RUNNING
                    task.status = TaskStatus.RUNNING
                    task.result = result_dict.get("result", "Interactive session started")

                    # Store engine and interactive flag in meta_info for UI
                    task.meta_info = task.meta_info or {}
                    task.meta_info["engine"] = engine.replace("-", "_")  # claude-code-cli -> claude_code_cli
                    task.meta_info["interactive"] = True
                    task.meta_info["session_id"] = result_dict.get("session_id")
                    task.meta_info["needs_auth"] = result_dict.get("needs_auth", False)

                    logger.info(f"🖥️ Interactive terminal session started for task {task_id}")
                    logger.info(f"💡 Status: RUNNING (terminal active) - will complete when terminal session ends")
                else:
                    # Non-interactive task - mark as completed or failed
                    task.completed_at = datetime.now()
                    if task.started_at:
                        task.duration_seconds = (task.completed_at - task.started_at).total_seconds()

                    if result_dict.get("success"):
                        task.status = TaskStatus.COMPLETED
                        task.result = result_dict.get("result", "Task completed")
                        task.artifacts = result_dict.get("artifacts", [])
                        task.llm_calls = result_dict.get("iterations", 0)
                        logger.info(f"✅ Task {task_id} completed with {engine}")
                    else:
                        task.status = TaskStatus.FAILED
                        task.error = result_dict.get("error", "Task failed")
                        logger.error(f"❌ Task {task_id} failed with {engine}: {task.error}")

                await db.commit()

            except Exception as e:
                logger.error(f"❌ Error executing task {task_id} with {engine}: {e}")

                # Update task as failed
                result = await db.execute(
                    select(AgentTask).filter(AgentTask.task_id == task_id)
                )
                task = result.scalar_one_or_none()
                if task:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    task.error_details = {"exception": str(type(e).__name__), "engine": engine}
                    task.completed_at = datetime.now()
                    if task.started_at:
                        task.duration_seconds = (task.completed_at - task.started_at).total_seconds()
                    await db.commit()

    async def cancel_task(self, task_id: str, reason: Optional[str] = None) -> bool:
        """
        Cancel a running agent task

        Args:
            task_id: Task identifier
            reason: Cancellation reason

        Returns:
            True if cancelled, False if task not found or already completed
        """
        result = await self.db.execute(
            select(AgentTask).filter(AgentTask.task_id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            return False

        # Can only cancel pending or running tasks
        if task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            logger.warning(f"⚠️ Cannot cancel task {task_id} with status {task.status}")
            return False

        # Update task status
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now(timezone.utc)

        if task.started_at:
            task.duration_seconds = (task.completed_at - task.started_at).total_seconds()

        task.error = reason or "Task cancelled by user"
        await self.db.commit()

        logger.info(f"🚫 Task {task_id} cancelled in database")

        # 🆕 FIX: Kill the running process if it exists
        if task_id in AgentOrchestrationService._running_processes:
            process = AgentOrchestrationService._running_processes[task_id]
            try:
                logger.info(f"🔪 Killing process for task {task_id}, PID: {process.pid}")
                process.kill()
                await process.wait()  # Wait for process to actually terminate
                logger.info(f"✅ Successfully killed process for task {task_id}")
            except Exception as e:
                logger.warning(f"⚠️ Error killing process for task {task_id}: {e}")
            finally:
                # Clean up reference
                del AgentOrchestrationService._running_processes[task_id]
                logger.info(f"🧹 Removed process reference for cancelled task {task_id}")
        else:
            logger.info(f"ℹ️ No running process found for task {task_id} (may not have started yet)")

        # ✨ NEW: Close terminal session gracefully (triggers artifact scanning)
        from app.services.terminal_session_manager import close_terminal_session
        try:
            logger.info(f"🔌 Closing terminal session for cancelled task: {task_id}")
            await close_terminal_session(task_id, scan_artifacts=True)
        except Exception as e:
            logger.warning(f"⚠️ Error closing terminal session: {e}")

        return True
