# Agent Task MinIO Storage Implementation

> **Created**: 2025-12-11
> **Status**: Design Phase
> **Priority**: High (Solves artifact isolation and traceability)

---

## Problem Statement

**Current Issues**:
1. **Artifact Cross-Contamination**: All agent tasks share `/workspace/artifacts/` directory, causing files from previous tasks to be incorrectly attributed to new tasks
2. **No Traceability**: Can't easily identify which artifacts belong to which task execution
3. **No Persistence**: Artifacts are lost when agent container restarts
4. **Poor Organization**: No hierarchical structure for browsing task results

**Example Issue**:
- Task A creates `chart.html` at 06:05
- Task B runs at 09:22 and scans `/workspace/artifacts/`
- Task B's artifact array includes Task A's `chart.html` ❌

---

## Proposed Solution

### 1. MinIO Hierarchical Structure

```
minio://chatbot-bucket/
├── projects/
│   └── {project_id}/                          # e.g., "00000000-0000-0000-0000-000000000001" (Global Project)
│       └── {username}/                        # e.g., "admin" or "john.doe"
│           └── agent-tasks/
│               └── {task_name}/               # LLM-generated: "sales_analysis_chart"
│                   └── {task_id}/             # Unique execution: "task-a81656d4e7e9"
│                       ├── input/
│                       │   └── sales2.txt     # Input files copied here
│                       ├── artifacts/
│                       │   ├── revenue_chart.html
│                       │   └── revenue_by_product.png
│                       ├── logs/
│                       │   ├── stdout.log
│                       │   └── stderr.log
│                       └── metadata.json      # Task config & results
```

### 2. Benefits

✅ **Perfect Isolation**: Each task execution gets unique workspace
✅ **Full Traceability**: Clear mapping from task → artifacts
✅ **Persistence**: Survives container restarts
✅ **Organization**: Hierarchical structure for easy navigation
✅ **Multi-Run Support**: Same task can be re-run, each execution is separate
✅ **Audit Trail**: Complete history of all task executions

---

## Implementation Plan

### Phase 1: LLM-Based Task Name Generation

**File**: `backend/app/services/agent_service.py`

Add method to generate human-readable task names:

```python
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
        response = await self.llm_service.generate(
            prompt=prompt,
            model="gpt-3.5-turbo",  # Fast and cheap
            max_tokens=50,
            temperature=0.3  # Low temperature for consistency
        )

        # Extract and sanitize
        task_name = response.strip().lower()
        task_name = re.sub(r'[^a-z0-9_]', '', task_name)
        task_name = re.sub(r'_+', '_', task_name).strip('_')

        # Fallback if generation fails
        if not task_name or len(task_name) < 3:
            task_name = "agent_task"

        logger.info(f"Generated task name: '{task_name}' from description: '{task_description[:50]}...'")
        return task_name

    except Exception as e:
        logger.warning(f"Failed to generate task name: {e}, using default")
        return "agent_task"
```

### Phase 2: Update MinIOPathBuilder

**File**: `backend/app/services/minio_path_builder.py`

Add new method for agent task paths:

```python
@staticmethod
def build_agent_task_path(
    project_id: str,
    username: str,
    task_name: str,
    task_id: str,
    subfolder: str,  # 'input', 'artifacts', 'logs'
    filename: str
) -> str:
    """
    Build hierarchical MinIO path for agent task artifacts.

    Args:
        project_id: Project UUID or 'global-project'
        username: User's username
        task_name: Human-readable task name (e.g., 'sales_analysis_chart')
        task_id: Unique task execution ID (e.g., 'task-a81656d4e7e9')
        subfolder: Folder within task ('input', 'artifacts', 'logs')
        filename: File name

    Returns:
        Full MinIO path string

    Example:
        >>> build_agent_task_path(
        ...     project_id='global-project',
        ...     username='admin',
        ...     task_name='sales_analysis_chart',
        ...     task_id='task-a81656d4e7e9',
        ...     subfolder='artifacts',
        ...     filename='revenue_chart.html'
        ... )
        'projects/global-project/admin/agent-tasks/sales_analysis_chart/task-a81656d4e7e9/artifacts/revenue_chart.html'
    """
    # Sanitize components
    sanitized_project = MinIOPathBuilder.sanitize(project_id)
    sanitized_username = MinIOPathBuilder.sanitize(username)
    sanitized_task_name = MinIOPathBuilder.sanitize(task_name)

    # Validate subfolder
    valid_subfolders = ['input', 'artifacts', 'logs']
    if subfolder not in valid_subfolders:
        logger.warning(f"Invalid subfolder '{subfolder}', defaulting to 'artifacts'")
        subfolder = 'artifacts'

    # Build path
    path = (
        f"projects/{sanitized_project}/{sanitized_username}/agent-tasks/"
        f"{sanitized_task_name}/{task_id}/{subfolder}/{filename}"
    )

    logger.debug(f"Built agent task MinIO path: {path}")
    return path

@staticmethod
def get_agent_task_prefix(
    project_id: str,
    username: str,
    task_name: Optional[str] = None,
    task_id: Optional[str] = None
) -> str:
    """
    Get prefix for listing agent task files.

    Examples:
        # All tasks for user in project
        get_agent_task_prefix('global-project', 'admin')
        → 'projects/global-project/admin/agent-tasks/*'

        # All executions of specific task
        get_agent_task_prefix('global-project', 'admin', 'sales_analysis_chart')
        → 'projects/global-project/admin/agent-tasks/sales_analysis_chart/*'

        # Specific task execution
        get_agent_task_prefix('global-project', 'admin', 'sales_analysis_chart', 'task-123')
        → 'projects/global-project/admin/agent-tasks/sales_analysis_chart/task-123/*'
    """
    sanitized_project = MinIOPathBuilder.sanitize(project_id)
    sanitized_username = MinIOPathBuilder.sanitize(username)

    prefix = f"projects/{sanitized_project}/{sanitized_username}/agent-tasks/"

    if task_name:
        sanitized_task_name = MinIOPathBuilder.sanitize(task_name)
        prefix += f"{sanitized_task_name}/"

        if task_id:
            prefix += f"{task_id}/"

    prefix += "*"
    return prefix
```

### Phase 3: Update Agent Container Workspace

**File**: `backend/entrypoint_agent.py`

Modify workspace creation to use task-specific directory:

```python
class AgentOrchestrator:
    def __init__(
        self,
        task: str,
        task_id: str,
        task_name: str,  # NEW: Human-readable task name
        project_id: str,  # NEW: Project ID
        username: str,    # NEW: Username for MinIO path
        model: str = "gpt-4-turbo",
        max_iterations: int = 20
    ):
        self.task = task
        self.task_id = task_id
        self.task_name = task_name
        self.project_id = project_id
        self.username = username

        # Create task-specific workspace
        self.workspace = Path(f"/workspace/{task_id}")
        self.input_dir = self.workspace / "input"
        self.artifacts_dir = self.workspace / "artifacts"
        self.logs_dir = self.workspace / "logs"

        # Create directories
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.input_dir.mkdir(exist_ok=True)
        self.artifacts_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

        # Setup logging to file
        log_file = self.logs_dir / "agent.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(file_handler)

        logger.info(f"Created task-specific workspace: {self.workspace}")
```

**Update artifact scanning**:

```python
async def run(self):
    """Main agent loop with MinIO upload at completion"""

    # ... existing agent loop code ...

    # At the end, after task completion:

    # 1. Scan artifacts directory (now task-specific)
    artifacts = []
    if self.artifacts_dir.exists():
        for artifact_file in self.artifacts_dir.iterdir():
            if artifact_file.is_file():
                artifacts.append({
                    "path": str(artifact_file.relative_to(self.workspace)),
                    "size": artifact_file.stat().st_size,
                    "created_at": datetime.utcnow().isoformat()
                })
                logger.info(f"📎 Found artifact: {artifact_file.name}")

    # 2. Upload all files to MinIO
    await self._upload_to_minio()

    # 3. Build result with MinIO paths
    result = {
        "success": task_complete,
        "final_answer": final_answer,
        "artifacts": artifacts,
        "minio_paths": {
            "input": f"projects/{self.project_id}/{self.username}/agent-tasks/{self.task_name}/{self.task_id}/input/",
            "artifacts": f"projects/{self.project_id}/{self.username}/agent-tasks/{self.task_name}/{self.task_id}/artifacts/",
            "logs": f"projects/{self.project_id}/{self.username}/agent-tasks/{self.task_name}/{self.task_id}/logs/"
        }
    }

    # Print JSON to stdout for backend parsing
    print(json.dumps(result))


async def _upload_to_minio(self):
    """Upload all task files to MinIO"""
    try:
        from minio import Minio

        # Initialize MinIO client
        minio_client = Minio(
            os.getenv("MINIO_ENDPOINT", "minio:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            secure=False
        )

        bucket_name = os.getenv("MINIO_BUCKET", "chatbot-bucket")

        # Upload input files
        for input_file in self.input_dir.iterdir():
            if input_file.is_file():
                minio_path = MinIOPathBuilder.build_agent_task_path(
                    project_id=self.project_id,
                    username=self.username,
                    task_name=self.task_name,
                    task_id=self.task_id,
                    subfolder='input',
                    filename=input_file.name
                )
                minio_client.fput_object(
                    bucket_name,
                    minio_path,
                    str(input_file)
                )
                logger.info(f"📤 Uploaded input: {minio_path}")

        # Upload artifacts
        for artifact_file in self.artifacts_dir.iterdir():
            if artifact_file.is_file():
                minio_path = MinIOPathBuilder.build_agent_task_path(
                    project_id=self.project_id,
                    username=self.username,
                    task_name=self.task_name,
                    task_id=self.task_id,
                    subfolder='artifacts',
                    filename=artifact_file.name
                )
                minio_client.fput_object(
                    bucket_name,
                    minio_path,
                    str(artifact_file)
                )
                logger.info(f"📤 Uploaded artifact: {minio_path}")

        # Upload logs
        for log_file in self.logs_dir.iterdir():
            if log_file.is_file():
                minio_path = MinIOPathBuilder.build_agent_task_path(
                    project_id=self.project_id,
                    username=self.username,
                    task_name=self.task_name,
                    task_id=self.task_id,
                    subfolder='logs',
                    filename=log_file.name
                )
                minio_client.fput_object(
                    bucket_name,
                    minio_path,
                    str(log_file)
                )
                logger.info(f"📤 Uploaded log: {minio_path}")

        # Upload metadata.json
        metadata = {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "task_description": self.task,
            "project_id": self.project_id,
            "username": self.username,
            "model": self.model,
            "max_iterations": self.max_iterations,
            "started_at": self.start_time.isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "duration_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "iterations": self.iteration,
            "status": "completed" if self.task_complete else "failed"
        }

        metadata_path = self.workspace / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        minio_path = f"projects/{self.project_id}/{self.username}/agent-tasks/{self.task_name}/{self.task_id}/metadata.json"
        minio_client.fput_object(
            bucket_name,
            minio_path,
            str(metadata_path)
        )
        logger.info(f"📤 Uploaded metadata: {minio_path}")

    except Exception as e:
        logger.error(f"Failed to upload to MinIO: {e}")
        # Don't fail the task if MinIO upload fails
```

### Phase 4: Update Database Schema

**New Migration**: `backend/migrations/014_add_task_name_and_minio_paths.sql`

```sql
-- Add task_name and minio_paths columns to agent_tasks table
ALTER TABLE agent_tasks
ADD COLUMN task_name VARCHAR(255),
ADD COLUMN minio_base_path TEXT;

-- Add index for task_name (for listing similar tasks)
CREATE INDEX idx_agent_tasks_task_name ON agent_tasks(task_name);

-- Add comment explaining structure
COMMENT ON COLUMN agent_tasks.task_name IS 'Human-readable task name generated by LLM (e.g., sales_analysis_chart)';
COMMENT ON COLUMN agent_tasks.minio_base_path IS 'Base MinIO path for this task execution (e.g., projects/{project_id}/{user}/agent-tasks/{task_name}/{task_id}/)';
```

### Phase 5: Update AgentService

**File**: `backend/app/services/agent_service.py`

Update `create_task` method:

```python
async def create_task(
    self,
    task_description: str,
    session_id: Optional[str] = None,
    model: str = "gpt-4-turbo",
    max_iterations: int = 20,
    timeout_seconds: int = 600,
    project_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> AgentTask:
    """Create new agent task with LLM-generated name and MinIO storage"""

    # 1. Generate human-readable task name
    task_name = await self._generate_task_name(task_description)

    # 2. Get user info for MinIO path
    username = "unknown"
    if user_id:
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            username = user.username

    # 3. Get project ID (default to global project)
    if not project_id:
        global_project = self.db.query(Project).filter(
            Project.name == "Global Project"
        ).first()
        project_id = str(global_project.id) if global_project else "global-project"

    # 4. Generate task ID
    task_id = f"task-{str(uuid.uuid4())[:12]}"

    # 5. Build MinIO base path
    minio_base_path = (
        f"projects/{MinIOPathBuilder.sanitize(project_id)}/"
        f"{MinIOPathBuilder.sanitize(username)}/agent-tasks/"
        f"{MinIOPathBuilder.sanitize(task_name)}/{task_id}/"
    )

    # 6. Create database record
    task = AgentTask(
        task_id=task_id,
        task_name=task_name,  # NEW
        task_description=task_description,
        session_id=session_id,
        model=model,
        max_iterations=max_iterations,
        timeout_seconds=timeout_seconds,
        project_id=project_id,
        created_by=user_id,
        minio_base_path=minio_base_path,  # NEW
        status=TaskStatus.PENDING
    )

    self.db.add(task)
    self.db.commit()
    self.db.refresh(task)

    logger.info(
        f"Created task {task_id} with name '{task_name}' "
        f"at MinIO path: {minio_base_path}"
    )

    # 7. Execute task asynchronously
    asyncio.create_task(self._execute_task_async(task_id))

    return task
```

Update `_execute_task_async` to pass new parameters:

```python
async def _execute_task_async(self, task_id: str):
    """Execute agent task in Docker container"""

    # Get task from DB
    task = self.db.query(AgentTask).filter(AgentTask.task_id == task_id).first()

    # ... existing code ...

    # Build Docker run command with new env vars
    env_vars = {
        "TASK_B64": base64.b64encode(task.task_description.encode()).decode(),
        "TASK_ID": task.task_id,
        "TASK_NAME": task.task_name,  # NEW
        "PROJECT_ID": task.project_id or "global-project",  # NEW
        "USERNAME": username,  # NEW (get from user_id)
        "MODEL": task.model,
        "MAX_ITERATIONS": str(task.max_iterations),
        # ... other env vars ...
    }

    # ... rest of execution code ...
```

### Phase 6: Frontend Updates

**Component**: `frontend/src/components/AgentTaskMonitor.tsx`

Add artifact download functionality:

```typescript
const downloadArtifact = async (taskId: string, artifactPath: string) => {
  try {
    const response = await axios.get(
      `${API_URL}/api/v1/agent-tasks/${taskId}/artifacts/download`,
      {
        params: { path: artifactPath },
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
        responseType: 'blob'
      }
    );

    // Extract filename from path
    const filename = artifactPath.split('/').pop();

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();

  } catch (error) {
    console.error('Failed to download artifact:', error);
  }
};
```

**New API Endpoint**: `backend/app/api/routes/agent_routes.py`

```python
@router.get("/agent-tasks/{task_id}/artifacts/download")
async def download_artifact(
    task_id: str,
    path: str = Query(..., description="Artifact path to download"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Download artifact file from MinIO"""

    # Get task
    task = db.query(AgentTask).filter(AgentTask.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check permissions
    if task.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    # Build MinIO path
    minio_path = f"{task.minio_base_path}{path}"

    # Get file from MinIO
    try:
        from app.core.config import settings
        from minio import Minio

        minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )

        # Get object
        response = minio_client.get_object(settings.MINIO_BUCKET, minio_path)

        # Stream to client
        return StreamingResponse(
            response.stream(32*1024),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={path.split('/')[-1]}"
            }
        )

    except Exception as e:
        logger.error(f"Failed to download artifact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent-tasks/{task_id}/artifacts")
async def list_artifacts(
    task_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all artifacts for a task from MinIO"""

    # Get task
    task = db.query(AgentTask).filter(AgentTask.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check permissions
    if task.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    # List files in MinIO
    try:
        from app.core.config import settings
        from minio import Minio

        minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )

        artifacts = []

        # List artifacts folder
        prefix = f"{task.minio_base_path}artifacts/"
        objects = minio_client.list_objects(
            settings.MINIO_BUCKET,
            prefix=prefix,
            recursive=True
        )

        for obj in objects:
            artifacts.append({
                "name": obj.object_name.replace(prefix, ""),
                "size": obj.size,
                "last_modified": obj.last_modified.isoformat(),
                "path": obj.object_name.replace(task.minio_base_path, "")
            })

        return {"artifacts": artifacts}

    except Exception as e:
        logger.error(f"Failed to list artifacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Migration Strategy

### Step 1: Deploy Backend Changes
1. Add new columns to `agent_tasks` table
2. Deploy updated `AgentService` with task name generation
3. Deploy updated `MinIOPathBuilder` with agent task methods

### Step 2: Update Agent Container
1. Rebuild agent-runtime image with updated `entrypoint_agent.py`
2. Test workspace isolation with multiple concurrent tasks
3. Verify MinIO uploads work correctly

### Step 3: Update Frontend
1. Add artifact download buttons to AgentTaskMonitor
2. Add task name display
3. Add MinIO path display for debugging

### Step 4: Backfill Existing Tasks (Optional)
```sql
-- Generate task names for existing tasks without names
UPDATE agent_tasks
SET task_name = 'legacy_task_' || substring(task_id from 6)
WHERE task_name IS NULL;
```

---

## Testing Plan

### Test Case 1: Single Task Execution
1. Create task: "analyze sales2.txt and create a chart"
2. Verify task name generated: "sales_analysis_chart"
3. Verify workspace created: `/workspace/task-{id}/`
4. Verify artifacts uploaded to MinIO at correct path
5. Verify artifact download works from frontend

### Test Case 2: Multiple Concurrent Tasks
1. Start Task A: "analyze sales2.txt"
2. Start Task B: "analyze customers.csv"
3. Verify workspaces are isolated (`/workspace/task-A/` vs `/workspace/task-B/`)
4. Verify artifacts don't cross-contaminate
5. Verify both MinIO paths are correct

### Test Case 3: Task Re-Execution
1. Run task: "sales analysis" → creates `sales_analysis/task-123/`
2. Re-run same task → creates `sales_analysis/task-456/`
3. Verify both executions preserved separately

### Test Case 4: MinIO Cleanup
1. Run task that creates 100MB of artifacts
2. Verify files uploaded to MinIO
3. Verify local workspace cleaned up after upload
4. Verify artifacts still downloadable from MinIO

---

## Performance Considerations

### 1. MinIO Upload Speed
- Upload happens AFTER task completion (non-blocking)
- Use async uploads for better performance
- Consider compression for large artifacts

### 2. Workspace Cleanup
- Clean up local `/workspace/{task_id}/` after MinIO upload
- Implement retention policy (keep last N tasks locally)
- Background cleanup job for old workspaces

### 3. LLM Task Name Generation
- Use fast model (gpt-3.5-turbo) to minimize latency
- Cache common patterns (optional)
- Fallback to default name if generation fails

---

## Security Considerations

### 1. Path Traversal Prevention
- Sanitize all path components
- Validate task_id format (only alphanumeric + hyphens)
- Restrict file types allowed in artifacts

### 2. Access Control
- Verify user owns task before allowing download
- Implement MinIO policies per project/user
- Admin can access all tasks

### 3. Storage Quotas
- Implement per-user storage limits
- Alert when approaching quota
- Auto-cleanup old task executions

---

## Monitoring & Observability

### Metrics to Track
- Task executions per day
- Average artifact size per task
- MinIO upload success/failure rate
- Task name generation latency
- Workspace cleanup efficiency

### Logging
- Log all MinIO uploads with size and duration
- Log task name generation results
- Log workspace creation/cleanup operations

---

## Future Enhancements

### Phase 2: UI for Browsing Tasks
- Tree view of all tasks by project/user
- Filter by task name
- Preview artifacts inline (images, charts)
- Compare multiple task executions

### Phase 3: Artifact Sharing
- Share task results with team members
- Generate shareable links
- Public/private artifact visibility

### Phase 4: Task Templates
- Save successful task workflows as templates
- One-click re-run with different data
- Template marketplace

---

## Summary

This implementation provides:

✅ **Perfect Artifact Isolation** - Each task gets unique workspace
✅ **Full Traceability** - Clear mapping from task → artifacts
✅ **Persistence** - MinIO storage survives restarts
✅ **Organization** - Hierarchical structure with LLM-generated names
✅ **Scalability** - Supports unlimited concurrent tasks
✅ **Auditability** - Complete history of all executions

**Estimated Implementation Time**: 2-3 days
- Day 1: Backend changes (task name generation, MinIO paths)
- Day 2: Agent container updates (workspace isolation, MinIO upload)
- Day 3: Frontend updates (artifact download UI), testing

---

**Status**: Ready for implementation 🚀
