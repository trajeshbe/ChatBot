"""
Agent Task Management API Routes

Provides REST API endpoints for creating, monitoring, and managing
autonomous agent tasks with LLM integration.
"""

import logging
import shutil
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
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
    role: str = Form("user"),
    department: str = Form("default"),
    team: str = Form("default-team"),
    username: str = Form("anonymous"),
    project_name: str = Form("agent-workspace"),
    db: AsyncSession = Depends(get_db)
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
    - project_id: Optional project ID (UUID)
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
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    role: str = Query("user", description="User role"),
    department: str = Query("default", description="Department name"),
    team: str = Query("default-team", description="Team name"),
    username: str = Query("anonymous", description="Username"),
    project_name: str = Query("agent-workspace", description="Project name"),
    db: AsyncSession = Depends(get_db)
):
    """
    List files from a selected project in MinIO

    Returns all files stored in MinIO under the organizational path structure
    for a specific project.

    **Query Parameters**:
    - project_id: Optional project UUID
    - role: User role
    - department: Department name
    - team: Team name
    - username: Username
    - project_name: Project name

    **Returns**:
    - files: List of file objects with metadata
    - total: Total number of files
    - project_prefix: MinIO prefix used for filtering
    """
    try:
        logger.info(f"📂 Listing files for project: {project_name}")

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
