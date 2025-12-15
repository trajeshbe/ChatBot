"""
Agent Task Management API Routes

Provides REST API endpoints for creating, monitoring, and managing
autonomous agent tasks with LLM integration.
"""

import logging
import shutil
import os
import asyncio  # ✅ FIX: Added for terminal WebSocket
import json  # ✅ FIX: Added for terminal WebSocket JSON parsing
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, WebSocket, WebSocketDisconnect, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from minio import Minio
from minio.error import S3Error

from app.core.database import get_db
from app.core.config import settings
from app.services.agent_service import AgentOrchestrationService
from app.api.routes.auth import get_current_user_optional  # 🆕 FIX: Import auth dependency
from app.services.minio_path_builder import MinIOPathBuilder
from app.models.database import Document, AgentTask
from app.schemas.agent_schemas import (
    AgentTaskCreate,
    AgentTaskResponse,
    AgentTaskStatusResponse,
    AgentTaskList,
    AgentTaskCancel,
    AgentTaskCancelResponse,
    TaskStatus
)
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agent", tags=["Agent Tasks"])


@router.post("/tasks", response_model=AgentTaskResponse)
async def create_agent_task(
    request: AgentTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_optional)  # 🆕 FIX: Get authenticated user
):
    """
    Create a new autonomous agent task

    The agent will execute the task using the agentic loop (THINK → PLAN → ACT → OBSERVE)
    with access to 13 tools including data analysis, document processing, and vision capabilities.

    **Document Access**:
    The agent can access documents in three ways (priority order):
    1. **Selected Documents** (document_ids): Specify document UUIDs to mount
    2. **Session Documents** (session_id): Auto-mount all session documents
    3. **Pre-uploaded Files**: Files already in /workspace/ from /upload-workspace-file

    **Examples**:

    With selected documents:
    ```json
    {
      "task_description": "Analyze sales1.docx and create visualizations",
      "document_ids": ["3f204a1c-d21d-4dac-b6a8-44d80e8d1215"],
      "max_iterations": 15,
      "timeout_seconds": 300,
      "model": "qwen2.5-coder:7b"
    }
    ```

    With session documents:
    ```json
    {
      "task_description": "Analyze all uploaded files",
      "session_id": "session-1764521122462-xf65ytwba",
      "max_iterations": 15,
      "timeout_seconds": 300,
      "model": "qwen2.5-coder:7b"
    }
    ```

    **Returns**:
    - task_id: Unique identifier for tracking the task
    - status: Current task status (pending, running, completed, failed, cancelled)
    - message: Status message
    - created_at: Task creation timestamp
    """
    try:
        service = AgentOrchestrationService(db)

        # 🆕 FIX: Use authenticated user if available
        user_id = None
        if current_user:
            user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
            logger.info(f"👤 Agent task created by user: {current_user.username if hasattr(current_user, 'username') else current_user.get('username')}")

        response = await service.create_task(
            request=request,
            user_id=user_id,
            project_id=None  # 🆕 FIX: Use default project (global-project) for now
        )

        logger.info(f"✅ Created agent task: {response.task_id}")
        return response

    except Exception as e:
        logger.error(f"❌ Error creating agent task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.get("/tasks/{task_id}", response_model=AgentTaskStatusResponse)
async def get_agent_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed status of an agent task

    Returns comprehensive information about task execution including:
    - Current status and progress
    - Execution details (duration, iterations)
    - Results and generated artifacts
    - Tools used and LLM calls made
    - Error information if task failed

    **Returns**:
    - Full task details with all execution metadata
    """
    try:
        service = AgentOrchestrationService(db)
        task_status = await service.get_task_status(task_id)

        if not task_status:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

        return task_status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting task status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.get("/tasks", response_model=AgentTaskList)
async def list_agent_tasks(
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Number of tasks per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    List agent tasks with optional filtering and pagination

    Retrieve a paginated list of agent tasks, optionally filtered by session ID or status.

    **Query Parameters**:
    - session_id: Filter tasks belonging to a specific session
    - status: Filter by task status (pending, running, completed, failed, cancelled)
    - page: Page number (default: 1)
    - page_size: Tasks per page (default: 50, max: 100)

    **Returns**:
    - tasks: List of task status objects
    - total: Total number of tasks matching filter
    - page: Current page number
    - page_size: Number of tasks per page
    """
    try:
        service = AgentOrchestrationService(db)

        task_list = await service.list_tasks(
            session_id=session_id,
            status=status,
            page=page,
            page_size=page_size
        )

        return task_list

    except Exception as e:
        logger.error(f"❌ Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")


@router.delete("/tasks/{task_id}", response_model=AgentTaskCancelResponse)
async def cancel_agent_task(
    task_id: str,
    cancel_request: Optional[AgentTaskCancel] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel a running or pending agent task

    Cancels an agent task that is currently running or pending execution.
    Completed or failed tasks cannot be cancelled.

    **Example**:
    ```json
    {
      "reason": "User requested cancellation"
    }
    ```

    **Returns**:
    - task_id: Task identifier
    - status: New task status (cancelled)
    - message: Cancellation status message
    - cancelled_at: Cancellation timestamp
    """
    try:
        service = AgentOrchestrationService(db)

        reason = None
        if cancel_request:
            reason = cancel_request.reason

        success = await service.cancel_task(task_id, reason=reason)

        if not success:
            # Check if task exists
            task_status = await service.get_task_status(task_id)
            if not task_status:
                raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot cancel task with status: {task_status.status}"
                )

        logger.info(f"🚫 Cancelled task: {task_id}")

        return AgentTaskCancelResponse(
            task_id=task_id,
            status=TaskStatus.CANCELLED,
            message="Task successfully cancelled",
            cancelled_at=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error cancelling task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


@router.post("/upload-workspace-file")
async def upload_workspace_file(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    role: str = Form("user"),
    department: str = Form("default"),
    team: str = Form("default-team"),
    username: str = Form("anonymous"),
    project_name: str = Form("agent-workspace"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """
    Upload a file to MinIO with organizational path structure and copy to agent workspace

    The file will be:
    1. Stored in MinIO at: {role}/{dept}/{team}/{username}/{project}/documents/{filename}
    2. Copied to agent workspace volume at: /workspace/{filename}

    This makes the file accessible both for:
    - Agent task execution (/workspace/)
    - Project management (MinIO with organizational structure)

    **Form Data**:
    - file: File to upload (multipart/form-data)
    - project_id: Optional project ID (UUID) - will be derived from session if not provided
    - session_id: Optional session ID - used to derive project_id if not explicitly provided
    - role: User role (default: "user")
    - department: Department name (default: "default")
    - team: Team name (default: "default-team")
    - username: Username (default: "anonymous")
    - project_name: Project name (default: "agent-workspace")

    **Returns**:
    - filename: Original filename
    - size: File size in bytes
    - minio_path: Full MinIO path with organizational structure
    - workspace_path: Path in agent workspace (/workspace/filename)
    - project_id: Associated project ID (if provided)
    - message: Status message
    """
    try:
        logger.info(f"📤 Uploading file to agent workspace: {file.filename}")
        logger.info(f"📁 Received project_id from form: {project_id}")

        # 🆕 PROJECT ID RESOLUTION (same as main upload endpoint)
        # Priority: 1. Form data  2. User default  3. Session project  4. Fallback to "Global"

        # Get user's default project if not overridden by form
        if not project_id and current_user and hasattr(current_user, 'default_project_id') and current_user.default_project_id:
            project_id = str(current_user.default_project_id)
            logger.info(f"📂 Using user's default project_id: {project_id}")

        # 🆕 FALLBACK: Get project_id from session if not provided
        if not project_id and session_id:
            from app.models.database_enhanced import ChatSession, Project
            session_query = select(ChatSession).where(ChatSession.session_id == session_id)
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()
            if session and session.project_id:
                project_id = str(session.project_id)
                logger.info(f"📂 Using session's project_id: {project_id}")

                # Also derive project_name from project_id
                project_query = select(Project).where(Project.id == session.project_id)
                project_result = await db.execute(project_query)
                project = project_result.scalar_one_or_none()
                if project:
                    project_name = project.name
                    logger.info(f"📂 Project (from session): {project_name}")

        # Initialize MinIO client
        minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )

        # Ensure bucket exists
        bucket_name = settings.MINIO_BUCKET_NAME
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            logger.info(f"✅ Created MinIO bucket: {bucket_name}")

        # Build organizational MinIO path
        minio_path = MinIOPathBuilder.build_document_path(
            role=role,
            department=department,
            team=team,
            username=username,
            project_name=project_name,
            filename=file.filename,
            folder="documents"
        )

        logger.info(f"📁 MinIO path: {minio_path}")

        # Upload to MinIO
        file.file.seek(0)  # Reset file pointer
        file_content = file.file.read()
        file_size = len(file_content)

        from io import BytesIO
        minio_client.put_object(
            bucket_name,
            minio_path,
            BytesIO(file_content),
            length=file_size,
            content_type=file.content_type or "application/octet-stream"
        )

        logger.info(f"✅ Uploaded to MinIO: {minio_path}")

        # Copy to agent workspace volume
        # The backend and agent-runtime containers share the agent_workspace volume
        workspace_path = f"/workspace/{file.filename}"
        local_workspace_path = Path(workspace_path)

        # Ensure workspace directory exists
        local_workspace_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file to workspace
        with open(local_workspace_path, "wb") as f:
            f.write(file_content)

        logger.info(f"✅ Copied to agent workspace: {workspace_path}")

        # Create document record in database
        # Convert project_id string to UUID if provided
        from uuid import UUID
        project_uuid = None
        if project_id:
            try:
                project_uuid = UUID(project_id)
            except (ValueError, AttributeError):
                logger.warning(f"Invalid project_id format: {project_id}")

        doc = Document(
            filename=file.filename,
            file_path=minio_path,
            file_type=file.content_type or "application/octet-stream",
            file_size=file_size,
            source_type="upload",
            project_id=project_uuid,  # ✅ FIX: Save project_id to enable project-scoped queries
            department=department,     # ✅ FIX: Save department
            team=team,                 # ✅ FIX: Save team
            user_role=role,            # ✅ FIX: Save user role
            minio_path=minio_path,     # ✅ FIX: Save MinIO path for reference
            meta_info={
                "uploaded_via": "agent_workspace",
                "role": role,
                "department": department,
                "team": team,
                "username": username,
                "project_name": project_name,
                "workspace_path": workspace_path
            },
            processed=False
        )

        db.add(doc)
        await db.commit()
        await db.refresh(doc)

        logger.info(f"✅ Created document record: {doc.id}")

        return {
            "filename": file.filename,
            "size": file_size,
            "minio_path": minio_path,
            "workspace_path": workspace_path,
            "project_id": project_id,
            "document_id": str(doc.id),
            "message": "File uploaded successfully to MinIO and agent workspace"
        }

    except S3Error as e:
        logger.error(f"❌ MinIO error: {e}")
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.get("/project-files")
async def list_project_files(
    session_id: Optional[str] = Query(None, description="Session ID for context"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    role: str = Query(None, description="User role"),
    department: str = Query(None, description="Department name"),
    team: str = Query(None, description="Team name"),
    username: str = Query(None, description="Username"),
    project_name: str = Query(None, description="Project name"),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """
    List files from a selected project in MinIO

    Returns all files stored in MinIO under the organizational path structure
    for a specific project.

    **Query Parameters**:
    - session_id: Session ID (will derive organizational context from session)
    - project_id: Optional project UUID
    - role: User role (optional, derived from user)
    - department: Department name (optional, derived from user)
    - team: Team name (optional, derived from user)
    - username: Username (optional, derived from user)
    - project_name: Project name (optional, derived from session/project)

    **Returns**:
    - files: List of file objects with metadata
    - total: Total number of files
    - project_prefix: MinIO prefix used for filtering
    """
    try:
        # 🆕 Get organizational context from session and user
        from app.core.security import get_current_user_from_request
        from app.models.rbac import Department, Team
        from app.models.database_enhanced import UserTeam, ChatSession, Project

        # Try to get authenticated user
        current_user = None
        if request:
            current_user = await get_current_user_from_request(request, db)

        # Get department from user if not provided
        if not department and current_user and current_user.department_id:
            dept_query = select(Department).where(Department.id == current_user.department_id)
            dept_result = await db.execute(dept_query)
            dept = dept_result.scalar_one_or_none()
            if dept:
                department = dept.name
                logger.info(f"📁 Department from user: {department}")

        # Get team from user if not provided
        if not team and current_user:
            teams_query = select(UserTeam, Team).join(
                Team, UserTeam.team_id == Team.id
            ).where(
                UserTeam.user_id == current_user.id,
                UserTeam.is_primary == True
            ).limit(1)
            teams_result = await db.execute(teams_query)
            user_team_data = teams_result.first()
            if user_team_data:
                team = user_team_data[1].name
                logger.info(f"👥 Team from user: {team}")

        # Get username if not provided
        if not username:
            if current_user:
                username = current_user.username
            else:
                username = "admin"  # Default for anonymous

        # Get project from session if not provided
        if not project_name and session_id:
            session_query = select(ChatSession).where(ChatSession.session_id == session_id)
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()
            if session and session.project_id:
                project_query = select(Project).where(Project.id == session.project_id)
                project_result = await db.execute(project_query)
                project = project_result.scalar_one_or_none()
                if project:
                    project_name = project.name
                    logger.info(f"📂 Project from session: {project_name}")

        # Fallback defaults
        if not department:
            department = "Technology"
        if not team:
            team = "Backend-Development"
        if not project_name:
            project_name = "Global"
        if not role:
            role = "admin"

        logger.info(f"📂 Listing files for project: {project_name} (dept={department}, team={team}, user={username})")

        # Initialize MinIO client
        minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )

        bucket_name = settings.MINIO_BUCKET_NAME

        # Build project prefix
        project_prefix = MinIOPathBuilder.get_project_prefix(
            role=role,
            department=department,
            team=team,
            username=username,
            project_name=project_name
        )

        logger.info(f"📁 Project prefix: {project_prefix}")

        # List objects in MinIO
        files = []
        try:
            objects = minio_client.list_objects(bucket_name, prefix=project_prefix, recursive=True)

            for obj in objects:
                # Parse path to get components
                try:
                    path_components = MinIOPathBuilder.parse_path(obj.object_name)

                    files.append({
                        "filename": path_components.filename,
                        "minio_path": obj.object_name,
                        "size": obj.size,
                        "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
                        "etag": obj.etag,
                        "folder": path_components.folder,
                        "department": path_components.department,
                        "team": path_components.team,
                        "username": path_components.username,
                        "project": path_components.project
                    })
                except ValueError as e:
                    logger.warning(f"⚠️ Could not parse path: {obj.object_name} - {e}")
                    continue

        except S3Error as e:
            if e.code == "NoSuchBucket":
                logger.warning(f"⚠️ Bucket does not exist: {bucket_name}")
                files = []
            else:
                raise

        logger.info(f"✅ Found {len(files)} files in project")

        return {
            "files": files,
            "total": len(files),
            "project_prefix": project_prefix,
            "project_name": project_name
        }

    except S3Error as e:
        logger.error(f"❌ MinIO error: {e}")
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Error listing files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.get("/tasks/{task_id}/artifacts/{filename}")
async def download_artifact(
    task_id: str,
    filename: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Download an artifact generated by an agent task

    Downloads a file artifact from the agent-runtime container's /artifacts/ directory.

    **Path Parameters**:
    - task_id: Task identifier
    - filename: Artifact filename to download

    **Returns**:
    - File stream with appropriate content-type header

    **Example**:
    ```
    GET /api/v1/agent/tasks/task-abc123/artifacts/visualization.png
    ```
    """
    try:
        import subprocess
        import tempfile
        from fastapi.responses import FileResponse

        logger.info(f"📥 Downloading artifact: {filename} from task: {task_id}")

        # Verify task exists
        service = AgentOrchestrationService(db)
        task_status = await service.get_task_status(task_id)

        if not task_status:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

        # Check if artifact exists in task artifacts list
        # Artifacts are stored as full paths like /workspace/artifacts/filename.html
        # Extract just the filenames for comparison
        from pathlib import Path
        available_artifacts = task_status.artifacts or []
        artifact_filenames = [Path(art).name for art in available_artifacts]

        if filename not in artifact_filenames:
            raise HTTPException(
                status_code=404,
                detail=f"Artifact '{filename}' not found in task {task_id}. Available artifacts: {artifact_filenames}"
            )

        # Find the full path of the matching artifact
        artifact_full_path = None
        for artifact in available_artifacts:
            if Path(artifact).name == filename:
                artifact_full_path = artifact
                break

        # Create temporary file to store artifact
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as tmp_file:
            tmp_path = tmp_file.name

        # Copy artifact from agent-runtime container to temporary file
        # Use the full path from the database (e.g., /workspace/artifacts/filename.html)
        artifact_path = artifact_full_path if artifact_full_path else f"/workspace/artifacts/{filename}"
        docker_command = [
            "docker", "cp",
            f"rag-agent-runtime:{artifact_path}",
            tmp_path
        ]

        logger.info(f"🐳 Copying artifact from container: {artifact_path}")
        result = subprocess.run(
            docker_command,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            logger.error(f"❌ Failed to copy artifact: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to copy artifact from container: {result.stderr}"
            )

        logger.info(f"✅ Successfully copied artifact to: {tmp_path}")

        # Determine content type based on file extension
        content_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.csv': 'text/csv',
            '.json': 'application/json',
            '.html': 'text/html',
            '.xml': 'text/xml',
            '.zip': 'application/zip'
        }

        file_ext = os.path.splitext(filename)[1].lower()
        media_type = content_type_map.get(file_ext, 'application/octet-stream')

        # Return file response with cleanup
        return FileResponse(
            path=tmp_path,
            media_type=media_type,
            filename=filename,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        logger.error(f"⏱️ Timeout copying artifact: {filename}")
        raise HTTPException(status_code=504, detail="Timeout copying artifact from container")
    except Exception as e:
        logger.error(f"❌ Error downloading artifact: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download artifact: {str(e)}")


@router.get("/tasks/{task_id}/artifacts-minio")
async def list_task_artifacts_from_minio(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    List all artifacts for a task from MinIO storage

    **Returns**:
    - List of artifact files with metadata

    **Example Response**:
    ```json
    {
        "task_id": "task-abc123",
        "task_name": "sales_analysis_chart",
        "minio_base_path": "projects/global-project/admin/agent-tasks/sales_analysis_chart/task-abc123/",
        "artifacts": [
            {
                "name": "revenue_chart.html",
                "size": 3607088,
                "last_modified": "2025-12-11T09:23:07Z",
                "path": "artifacts/revenue_chart.html",
                "download_url": "/api/v1/agent/tasks/task-abc123/download-minio?path=artifacts/revenue_chart.html"
            }
        ]
    }
    ```
    """
    try:
        from minio import Minio
        from app.core.config import settings

        # Get task
        service = AgentOrchestrationService(db)
        task_status = await service.get_task_status(task_id)

        if not task_status:
            raise HTTPException(status_code=404, detail="Task not found")

        # Get task details from database to get minio_base_path
        result = await db.execute(
            select(AgentTask).where(AgentTask.task_id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task or not task.minio_base_path:
            raise HTTPException(
                status_code=404,
                detail="Task not found or MinIO path not available"
            )

        # Initialize MinIO client
        minio_client = Minio(
            settings.MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )

        # List artifacts folder
        artifacts = []
        prefix = f"{task.minio_base_path}artifacts/"

        try:
            objects = minio_client.list_objects(
                settings.MINIO_BUCKET,
                prefix=prefix,
                recursive=True
            )

            for obj in objects:
                artifacts.append({
                    "name": obj.object_name.replace(prefix, ""),
                    "size": obj.size,
                    "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
                    "path": obj.object_name.replace(task.minio_base_path, ""),
                    "download_url": f"/api/v1/agent/tasks/{task_id}/download-minio?path={obj.object_name.replace(task.minio_base_path, '')}"
                })
        except Exception as e:
            logger.warning(f"No artifacts found in MinIO: {e}")

        return {
            "task_id": task_id,
            "task_name": task.task_name,
            "minio_base_path": task.minio_base_path,
            "artifacts": artifacts
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list artifacts from MinIO: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/download-minio")
async def download_artifact_from_minio(
    task_id: str,
    path: str,  # Relative path like "artifacts/revenue_chart.html"
    db: AsyncSession = Depends(get_db)
):
    """
    Download artifact from MinIO storage

    **Query Parameters**:
    - path: Relative path to artifact (e.g., "artifacts/revenue_chart.html")

    **Example**:
    ```
    GET /api/v1/agent/tasks/task-abc123/download-minio?path=artifacts/revenue_chart.html
    ```
    """
    try:
        from minio import Minio
        from app.core.config import settings
        from fastapi.responses import StreamingResponse
        import io

        logger.info(f"📥 Download request for task_id={task_id}, path={path}")

        # Get task
        result = await db.execute(
            select(AgentTask).where(AgentTask.task_id == task_id)
        )
        task = result.scalar_one_or_none()

        logger.info(f"📝 Task found: {task.task_id if task else 'None'}, minio_base_path={task.minio_base_path if task else 'N/A'}")

        if not task:
            logger.error(f"❌ Task not found: {task_id}")
            raise HTTPException(status_code=404, detail="Task not found")

        if not task.minio_base_path:
            raise HTTPException(
                status_code=404,
                detail="Task does not have MinIO path (may be old task)"
            )

        # Build full MinIO path
        minio_path = f"{task.minio_base_path}{path}"

        # Initialize MinIO client
        minio_client = Minio(
            settings.MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )

        # Get object from MinIO
        try:
            response = minio_client.get_object(settings.MINIO_BUCKET_NAME, minio_path)

            # Extract filename
            filename = path.split('/')[-1]

            # Determine content type
            content_type_map = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.pdf': 'application/pdf',
                '.txt': 'text/plain',
                '.csv': 'text/csv',
                '.json': 'application/json',
                '.html': 'text/html',
                '.xml': 'text/xml',
                '.zip': 'application/zip'
            }

            file_ext = os.path.splitext(filename)[1].lower()
            media_type = content_type_map.get(file_ext, 'application/octet-stream')

            # Stream file to client
            return StreamingResponse(
                response.stream(32*1024),
                media_type=media_type,
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )

        except Exception as e:
            logger.error(f"Failed to get object from MinIO: {e}")
            raise HTTPException(
                status_code=404,
                detail=f"Artifact not found in MinIO: {path}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download from MinIO: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def agent_service_health():
    """
    Health check endpoint for agent service

    Verifies that the agent service is operational and can communicate
    with the agent-runtime container.

    **Returns**:
    - status: Service health status
    - message: Health check message
    """
    try:
        # TODO: Add actual health check (e.g., ping agent-runtime container)
        return {
            "status": "healthy",
            "message": "Agent service is operational",
            "agent_runtime": "available"
        }
    except Exception as e:
        logger.error(f"❌ Agent service health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": str(e),
            "agent_runtime": "unavailable"
        }


@router.websocket("/tasks/{task_id}/ws")
async def agent_task_websocket(
    websocket: WebSocket,
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time agent task execution streaming

    Provides Claude Code-like interactive visualization of agent execution.
    Streams events in real-time as the agent thinks, uses tools, and completes tasks.

    **Connection URL**:
    ```
    ws://localhost:8000/api/v1/agent/tasks/{task_id}/ws
    ```

    **Event Types Streamed**:

    1. **connection** - Initial connection confirmation
    ```json
    {
      "type": "connection",
      "task_id": "task-abc123",
      "status": "connected",
      "timestamp": "2025-12-13T10:30:00Z"
    }
    ```

    2. **status_update** - Task status changes
    ```json
    {
      "type": "status_update",
      "status": "running",
      "message": "Agent task started",
      "timestamp": "2025-12-13T10:30:01Z"
    }
    ```

    3. **thinking** - Agent's thought process
    ```json
    {
      "type": "thinking",
      "thought": "I need to analyze the sales data using pandas",
      "iteration": 1,
      "timestamp": "2025-12-13T10:30:02Z"
    }
    ```

    4. **tool_use** - When agent calls a tool
    ```json
    {
      "type": "tool_use",
      "tool_name": "python_repl_tool",
      "tool_input": "import pandas as pd\ndf = pd.read_csv('sales.csv')",
      "iteration": 1,
      "timestamp": "2025-12-13T10:30:03Z"
    }
    ```

    5. **tool_result** - Tool execution result
    ```json
    {
      "type": "tool_result",
      "tool_name": "python_repl_tool",
      "result": "DataFrame loaded successfully with 1000 rows",
      "success": true,
      "iteration": 1,
      "timestamp": "2025-12-13T10:30:04Z"
    }
    ```

    6. **artifact** - Artifact generated
    ```json
    {
      "type": "artifact",
      "artifact_path": "/workspace/artifacts/visualization.png",
      "artifact_name": "visualization.png",
      "artifact_type": "image/png",
      "download_url": "/api/v1/agent/tasks/task-abc123/artifacts/visualization.png",
      "timestamp": "2025-12-13T10:30:05Z"
    }
    ```

    7. **completed** - Task completion
    ```json
    {
      "type": "completed",
      "status": "completed",
      "result": "Successfully analyzed sales data and created visualization",
      "artifacts": ["visualization.png", "report.html"],
      "duration_seconds": 45.3,
      "iterations": 5,
      "timestamp": "2025-12-13T10:30:45Z"
    }
    ```

    8. **error** - Error occurred
    ```json
    {
      "type": "error",
      "error": "Failed to read file: sales.csv not found",
      "iteration": 2,
      "timestamp": "2025-12-13T10:30:10Z"
    }
    ```

    **Usage Example (JavaScript/TypeScript)**:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/agent/tasks/task-abc123/ws');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch(data.type) {
        case 'thinking':
          console.log('Agent thinking:', data.thought);
          break;
        case 'tool_use':
          console.log('Using tool:', data.tool_name, data.tool_input);
          break;
        case 'tool_result':
          console.log('Tool result:', data.result);
          break;
        case 'completed':
          console.log('Task completed:', data.result);
          ws.close();
          break;
      }
    };
    ```

    **Connection Lifecycle**:
    1. Client connects to WebSocket
    2. Server sends 'connection' event
    3. Server polls task status every 1 second
    4. Server streams events as they occur
    5. Server sends 'completed' or 'error' event when task finishes
    6. Connection closes automatically on completion
    """
    import json
    import asyncio
    from datetime import datetime

    await websocket.accept()
    logger.info(f"🔌 WebSocket connected for task: {task_id}")

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "task_id": task_id,
            "status": "connected",
            "timestamp": datetime.now().isoformat()
        })

        # Initialize service
        service = AgentOrchestrationService(db)

        # Verify task exists
        task_status = await service.get_task_status(task_id)
        if not task_status:
            await websocket.send_json({
                "type": "error",
                "error": f"Task not found: {task_id}",
                "timestamp": datetime.now().isoformat()
            })
            await websocket.close()
            return

        # Send initial status
        await websocket.send_json({
            "type": "status_update",
            "status": task_status.status,
            "message": f"Task status: {task_status.status}",
            "timestamp": datetime.now().isoformat()
        })

        # Track last known state to detect changes
        last_status = task_status.status
        last_iteration = 0
        sent_artifacts = set()

        # Poll task status and stream updates
        while True:
            # Check if client disconnected
            try:
                # Non-blocking check for disconnect
                await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
            except asyncio.TimeoutError:
                pass  # No message received, continue polling
            except WebSocketDisconnect:
                logger.info(f"🔌 WebSocket disconnected for task: {task_id}")
                break

            # Get latest task status
            task_status = await service.get_task_status(task_id)

            if not task_status:
                await websocket.send_json({
                    "type": "error",
                    "error": "Task status unavailable",
                    "timestamp": datetime.now().isoformat()
                })
                break

            # Status changed
            if task_status.status != last_status:
                await websocket.send_json({
                    "type": "status_update",
                    "status": task_status.status,
                    "message": f"Task status changed to: {task_status.status}",
                    "timestamp": datetime.now().isoformat()
                })
                last_status = task_status.status

            # New iteration started
            if task_status.current_iteration and task_status.current_iteration > last_iteration:
                last_iteration = task_status.current_iteration

                # Send thinking event
                await websocket.send_json({
                    "type": "thinking",
                    "thought": f"Iteration {last_iteration} in progress",
                    "iteration": last_iteration,
                    "timestamp": datetime.now().isoformat()
                })

            # Parse execution_log for detailed events
            if task_status.execution_log:
                try:
                    # Extract recent tool uses from execution log
                    # The execution log contains detailed step-by-step execution data
                    # For now, we'll send a summary event

                    # Check for new execution details
                    if "tool_calls" in task_status.execution_log:
                        tool_calls = task_status.execution_log.get("tool_calls", [])
                        for tool_call in tool_calls[-3:]:  # Send last 3 tool calls
                            await websocket.send_json({
                                "type": "tool_use",
                                "tool_name": tool_call.get("name", "unknown"),
                                "tool_input": tool_call.get("input", ""),
                                "iteration": last_iteration,
                                "timestamp": datetime.now().isoformat()
                            })
                except Exception as e:
                    logger.warning(f"Failed to parse execution log: {e}")

            # Check for new artifacts
            if task_status.artifacts:
                for artifact in task_status.artifacts:
                    if artifact not in sent_artifacts:
                        sent_artifacts.add(artifact)

                        from pathlib import Path
                        artifact_name = Path(artifact).name

                        # Determine artifact type
                        artifact_type = "application/octet-stream"
                        if artifact_name.endswith('.png'):
                            artifact_type = "image/png"
                        elif artifact_name.endswith('.html'):
                            artifact_type = "text/html"
                        elif artifact_name.endswith('.csv'):
                            artifact_type = "text/csv"
                        elif artifact_name.endswith('.json'):
                            artifact_type = "application/json"

                        await websocket.send_json({
                            "type": "artifact",
                            "artifact_path": artifact,
                            "artifact_name": artifact_name,
                            "artifact_type": artifact_type,
                            "download_url": f"/api/v1/agent/tasks/{task_id}/artifacts/{artifact_name}",
                            "timestamp": datetime.now().isoformat()
                        })

            # Task completed or failed
            if task_status.status in ["completed", "failed", "cancelled"]:
                # Build artifact URLs for download
                artifacts_with_urls = []
                if task_status.artifacts and task_status.minio_base_path:
                    for artifact_path in task_status.artifacts:
                        artifact_name = Path(artifact_path).name
                        # Construct MinIO download URL (with artifacts/ subfolder)
                        minio_path = f"{task_status.minio_base_path}artifacts/{artifact_name}"
                        download_url = f"/api/v1/agent/tasks/{task_id}/download-minio?path=artifacts/{artifact_name}"
                        artifacts_with_urls.append({
                            "name": artifact_name,
                            "path": artifact_path,
                            "minio_path": minio_path,
                            "download_url": download_url
                        })

                await websocket.send_json({
                    "type": "completed",
                    "status": task_status.status,
                    "result": task_status.result or "",
                    "error": task_status.error if task_status.status == "failed" else None,
                    "artifacts": artifacts_with_urls,
                    "minio_base_path": task_status.minio_base_path,
                    "duration_seconds": task_status.duration_seconds,
                    "iterations": task_status.current_iteration,
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"✅ Task {task_id} {task_status.status}, closing WebSocket")
                break

            # Wait 1 second before next poll
            await asyncio.sleep(1.0)

        # Close connection
        await websocket.close()
        logger.info(f"🔌 WebSocket closed for task: {task_id}")

    except WebSocketDisconnect:
        logger.info(f"🔌 Client disconnected WebSocket for task: {task_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket error for task {task_id}: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        except:
            pass  # Connection may already be closed


@router.websocket("/tasks/{task_id}/terminal")
async def agent_task_terminal_websocket(
    websocket: WebSocket,
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Interactive Terminal WebSocket endpoint for Claude CLI

    Provides bidirectional communication with a PTY (pseudo-terminal)
    running Claude CLI. Enables user to type responses to Claude's prompts.

    **Connection URL**:
    ```
    ws://localhost:8000/api/v1/agent/tasks/{task_id}/terminal
    ```

    **Client → Server Messages** (User Input):
    ```json
    {
      "type": "terminal_input",
      "data": "user typed text\\n"
    }
    ```

    **Server → Client Messages** (Terminal Output):
    ```json
    {
      "type": "terminal_output",
      "data": "output from Claude CLI"
    }
    ```

    **Features**:
    - Full TTY support with ANSI escape codes
    - Real-time bidirectional I/O
    - Keyboard input forwarding (including Ctrl+C, Tab, etc.)
    - Terminal resizing support
    """
    await websocket.accept()
    logger.info(f"🖥️ Interactive terminal WebSocket connected for task: {task_id}")

    try:
        # Get task from database
        query = select(AgentTask).where(AgentTask.task_id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            await websocket.send_json({
                "type": "error",
                "error": f"Task {task_id} not found"
            })
            await websocket.close()
            return

        # Get task's terminal session manager
        from app.services.terminal_session_manager import get_terminal_session

        session = await get_terminal_session(task_id)

        if not session:
            await websocket.send_json({
                "type": "error",
                "error": f"No terminal session found for task {task_id}"
            })
            await websocket.close()
            return

        # Start background task to stream terminal output
        async def stream_output():
            """Stream terminal output to WebSocket"""
            try:
                async for output in session.read_output():
                    await websocket.send_json({
                        "type": "terminal_output",
                        "data": output
                    })
            except Exception as e:
                logger.error(f"Error streaming terminal output: {e}")

        # Start output streaming task
        output_task = asyncio.create_task(stream_output())

        try:
            # Handle incoming WebSocket messages (user input)
            while True:
                message = await websocket.receive_text()

                try:
                    data = json.loads(message)

                    if data.get("type") == "terminal_input":
                        # Forward user input to terminal stdin
                        user_input = data.get("data", "")
                        logger.info(f"📝 Terminal input received ({len(user_input)} bytes): {repr(user_input[:50])}")
                        await session.write_input(user_input)

                    elif data.get("type") == "resize":
                        # Handle terminal resize
                        rows = data.get("rows", 24)
                        cols = data.get("cols", 80)
                        await session.resize(rows, cols)

                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON message: {message}")

        except WebSocketDisconnect:
            logger.info(f"🖥️ Terminal WebSocket disconnected for task: {task_id}")
        finally:
            # Cancel output streaming task
            output_task.cancel()
            try:
                await output_task
            except asyncio.CancelledError:
                pass

            # Notify frontend of disconnection
            try:
                await websocket.send_json({
                    "type": "disconnected",
                    "message": "Terminal session ended"
                })
            except:
                pass

    except Exception as e:
        logger.error(f"❌ Terminal WebSocket error for task {task_id}: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "error": str(e)
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
        logger.info(f"🖥️ Terminal WebSocket closed for task: {task_id}")
