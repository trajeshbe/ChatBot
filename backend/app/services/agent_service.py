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
from datetime import datetime
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

logger = logging.getLogger(__name__)


class AgentOrchestrationService:
    """Service for orchestrating agent task execution"""

    def __init__(self, db: AsyncSession):
        self.db = db

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

        # Create database record
        agent_task = AgentTask(
            task_id=task_id,
            task_description=request.task_description,
            status=TaskStatus.PENDING,
            session_id=request.session_id,
            model=request.model or "qwen2.5-coder:7b",
            max_iterations=request.max_iterations or 20,
            timeout_seconds=request.timeout_seconds or 600,
            created_by=user_id,
            project_id=project_id,
            created_at=datetime.now()  # Set explicitly for immediate response
        )

        self.db.add(agent_task)
        await self.db.commit()
        await self.db.refresh(agent_task)

        logger.info(f"📝 Created agent task: {task_id}")

        # Execute task asynchronously (non-blocking)
        asyncio.create_task(self._execute_task_async(task_id))

        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message="Task created and queued for execution",
            created_at=agent_task.created_at
        )

    async def _execute_task_async(self, task_id: str):
        """
        Execute agent task asynchronously in agent-runtime container

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

                logger.info(f"🚀 Executing agent task: {task_id}")

                # Build docker exec command to run task in agent-runtime container
                # SECURITY: Properly escape task description for shell safety
                # Base64 encode to avoid shell escaping issues with newlines and special chars
                import base64
                task_description_b64 = base64.b64encode(task.task_description.encode('utf-8')).decode('utf-8')

                docker_command = [
                    "docker", "exec",
                    "-e", f"TASK_B64={task_description_b64}",
                    "-e", f"TASK_ID={task_id}",
                    "-e", f"SESSION_ID={task.session_id or 'default'}",
                    "-e", f"AGENT_LLM_MODEL={task.model}",
                    "-e", f"AGENT_MAX_ITERATIONS={task.max_iterations}",
                    "-e", f"AGENT_TIMEOUT_SECONDS={task.timeout_seconds}",
                    "rag-agent-runtime",  # Container name from docker-compose
                    "python", "/app/entrypoint_agent.py"
                ]

                # Execute command with timeout
                process = await asyncio.create_subprocess_exec(
                    *docker_command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

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

        # Determine success/failure based on return code
        if return_code == 0:
            task.status = TaskStatus.COMPLETED

            # IMPORTANT: Agent writes to stderr (Python logging default), so parse BOTH stdout and stderr
            combined_output = stdout + "\n" + stderr

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
                    if '.txt' in line or '.csv' in line or '.png' in line:
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
                        if tool_name not in tools:
                            tools.append(tool_name)

            if tools:
                task.tools_used = tools

            # Count LLM calls
            llm_calls = combined_output.count('Calling LLM') or combined_output.count('🤖')
            if llm_calls > 0:
                task.llm_calls = llm_calls

            logger.info(f"✅ Task {task_id} completed successfully")

        else:
            task.status = TaskStatus.FAILED
            task.error = f"Task failed with return code {return_code}"

            # Capture error details from stderr
            if stderr:
                task.error_details = {"stderr": stderr[:1000]}  # Limit size

            logger.error(f"❌ Task {task_id} failed with return code {return_code}")

        await db.commit()

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
            .where(SessionDocument.session_id == session.id)
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
            meta_info=task.meta_info
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
                meta_info=task.meta_info
            ))

        return AgentTaskList(
            tasks=task_responses,
            total=total,
            page=page,
            page_size=page_size
        )

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
        task.completed_at = datetime.now()

        if task.started_at:
            task.duration_seconds = (task.completed_at - task.started_at).total_seconds()

        task.error = reason or "Task cancelled by user"
        await self.db.commit()

        logger.info(f"🚫 Task {task_id} cancelled")

        # TODO: Kill the docker exec process if task is running
        # This would require tracking the process ID

        return True
