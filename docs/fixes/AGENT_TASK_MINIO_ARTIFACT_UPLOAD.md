# Agent Task MinIO Artifact Upload Implementation

> **Date**: 2025-12-13
> **Status**: ✅ Complete
> **Commit**: f9ec09a

---

## Problem Summary

Agent tasks were generating artifact files (HTML charts, PNGs, CSVs, etc.) but these files were:
- ❌ **NOT uploaded to MinIO** - only stored in agent-runtime container
- ❌ **Lost on cleanup** - deleted when container artifacts directory cleaned
- ❌ **Unavailable for download** - download URLs constructed but files missing

**User Issue**: "i see only the json in the artifacts / minio.. where is the actual html report .. missing."

---

## Root Cause Analysis

### What Was Working ✅
1. Agent successfully created artifacts in `/workspace/artifacts/`
2. result.json listed all artifacts with metadata
3. Artifact paths extracted and stored in database
4. `minio_base_path` generated correctly
5. WebSocket sent artifact URLs to UI

### What Was Missing ❌
**No code to upload artifacts from container to MinIO**

```bash
$ grep -i "minio.*upload\|put_object" backend/app/services/agent_service.py
# No matches found before fix
```

---

## Solution Implemented

### Added MinIO Upload Function

**Location**: `backend/app/services/agent_service.py:673-753`

**Function**: `async def _upload_artifacts_to_minio(task: AgentTask)`

**What it does**:
1. Reads each artifact file from agent-runtime container using `docker exec cat`
2. Determines content type (text/html, image/png, etc.)
3. Uploads to MinIO at `minio_base_path` location
4. Logs progress for each upload

### Integration Point

**Location**: `backend/app/services/agent_service.py:593-595`

Called automatically after artifact extraction in `_process_task_output()`:

```python
logger.info(f"✅ Task {task_id} completed with parsed JSON result")

# 🆕 Upload artifacts to MinIO
if task.artifacts and task.minio_base_path:
    await self._upload_artifacts_to_minio(task)
```

---

## Implementation Details

### Upload Function Logic

```python
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

    # 1. Validate task has artifacts and MinIO path
    if not task.artifacts:
        logger.info(f"No artifacts to upload for task {task.task_id}")
        return

    if not task.minio_base_path:
        logger.warning(f"No minio_base_path set for task {task.task_id}, skipping upload")
        return

    # 2. Initialize MinIO client
    minio_client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE
    )

    # 3. Upload each artifact
    uploaded_count = 0
    for artifact_path in task.artifacts:
        try:
            # Extract filename (e.g., "/workspace/artifacts/chart.html" → "chart.html")
            artifact_name = Path(artifact_path).name

            # Read file from agent-runtime container
            read_cmd = ["docker", "exec", "rag-agent-runtime", "cat", artifact_path]
            result = subprocess.run(read_cmd, capture_output=True, timeout=30)

            if result.returncode != 0:
                logger.error(f"❌ Failed to read {artifact_path}")
                continue

            file_data = result.stdout

            # Determine content type
            content_type, _ = mimetypes.guess_type(artifact_name)
            if not content_type:
                content_type = "application/octet-stream"

            # Construct MinIO path
            minio_object_path = f"{task.minio_base_path}{artifact_name}"

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

        except Exception as e:
            logger.error(f"❌ Failed to upload artifact {artifact_path}: {e}")

    logger.info(f"🎉 Uploaded {uploaded_count}/{len(task.artifacts)} artifacts to MinIO")
```

---

## MinIO Path Structure

### Example Organizational Path

```
{minio_base_path}{artifact_filename}

Technology/Backend-Development/Construction-Intelligence/admin/
agent-tasks/generate_sales_report/task-abc123/chart.html
```

**Breakdown**:
- `Technology/Backend-Development/Construction-Intelligence/admin/` - Organizational hierarchy (inherited from source documents)
- `agent-tasks/` - Agent tasks folder
- `generate_sales_report/` - Task name (sanitized)
- `task-abc123/` - Unique task ID
- `chart.html` - Artifact filename

---

## Download Endpoints

### 1. Container Download (Legacy)
```
GET /api/v1/agent/tasks/{task_id}/artifacts/{filename}
```
Downloads directly from agent-runtime container (only works if file still exists)

### 2. MinIO Download (New - Persistent)
```
GET /api/v1/agent/tasks/{task_id}/download-minio?path=artifacts/chart.html
```
Downloads from MinIO storage (persists even after container cleanup)

### 3. List MinIO Artifacts
```
GET /api/v1/agent/tasks/{task_id}/artifacts-minio
```

**Response**:
```json
{
  "task_id": "task-abc123",
  "task_name": "generate_sales_report",
  "minio_base_path": "Technology/.../task-abc123/",
  "artifacts": [
    {
      "name": "chart.html",
      "size": 3607088,
      "last_modified": "2025-12-13T14:30:00Z",
      "path": "artifacts/chart.html",
      "download_url": "/api/v1/agent/tasks/task-abc123/download-minio?path=artifacts/chart.html"
    }
  ]
}
```

---

## WebSocket Artifact Response

### Enhanced Artifact Structure

**Before** (only filenames):
```json
{
  "artifacts": ["chart.html", "report.png"]
}
```

**After** (complete metadata):
```json
{
  "artifacts": [
    {
      "name": "chart.html",
      "path": "/workspace/artifacts/chart.html",
      "minio_path": "Technology/.../task-abc123/chart.html",
      "download_url": "/api/v1/agents/tasks/task-abc123/artifacts/chart.html"
    }
  ],
  "minio_base_path": "Technology/.../task-abc123/"
}
```

---

## Testing

### Before Fix
```bash
$ docker exec rag-agent-runtime ls -la /workspace/artifacts/
# Files exist in container

$ # But checking MinIO:
$ curl "http://localhost:8000/api/v1/agents/tasks/task-b8d50285810b/artifacts-minio"
{
  "artifacts": []  # Empty - files not uploaded ❌
}
```

### After Fix
```bash
# Run agent task
$ curl -X POST "http://localhost:8000/api/v1/agent/tasks" \
  -F "task_description=create a sales chart from sales.txt"

# Check logs
$ docker-compose logs backend | grep "Upload"
📤 Uploading 4 artifact(s) to MinIO for task task-xyz789
📥 Reading artifact from container: /workspace/artifacts/chart.html
✅ Uploaded chart.html to MinIO: Technology/.../chart.html (3607088 bytes)
🎉 Uploaded 4/4 artifacts to MinIO

# Verify in MinIO
$ curl "http://localhost:8000/api/v1/agents/tasks/task-xyz789/artifacts-minio"
{
  "artifacts": [
    {
      "name": "chart.html",
      "size": 3607088,
      "download_url": "/api/v1/agent/tasks/task-xyz789/download-minio?path=artifacts/chart.html"
    }
  ]
}  # ✅ Files now in MinIO!
```

---

## Files Modified

### `backend/app/services/agent_service.py`

**Line 593-595**: Call upload function after artifact extraction
```python
# 🆕 Upload artifacts to MinIO
if task.artifacts and task.minio_base_path:
    await self._upload_artifacts_to_minio(task)
```

**Line 673-753**: Upload function implementation
```python
async def _upload_artifacts_to_minio(self, task: AgentTask):
    # Implementation
```

---

## Related Documentation

- **WebSocket Fix**: `docs/fixes/AGENT_TASK_WEBSOCKET_ARTIFACT_FIX.md`
- **Agent Routes**: `backend/app/api/routes/agent_routes.py:508-630, 729-790`
- **MinIO Path Builder**: `backend/app/services/minio_path_builder.py`
- **Document Service**: `backend/app/services/document_service.py:188-206` (upload pattern)

---

## Impact

### ✅ Benefits

1. **Artifact Persistence**: Files survive container cleanup
2. **Downloadable Results**: Users can download HTML charts, PNGs, reports
3. **MinIO Storage**: Leverages existing MinIO infrastructure
4. **Organizational Hierarchy**: Artifacts organized by department/team/project
5. **Audit Trail**: Complete path traceability

### 🔄 Workflow

```
Agent Task Created
  ↓
Agent Generates Artifacts in /workspace/artifacts/
  ↓
Artifact Paths Extracted from result.json
  ↓
🆕 _upload_artifacts_to_minio() Called
  ↓
Files Read from Container via docker exec
  ↓
Files Uploaded to MinIO at minio_base_path
  ↓
Task Completed - Artifacts Persisted in MinIO ✅
```

---

## Future Enhancements

1. **Background Upload**: Use asyncio to upload artifacts in parallel
2. **Retry Logic**: Retry failed uploads with exponential backoff
3. **Cleanup Policy**: Delete container artifacts after successful upload
4. **Compression**: Compress large artifacts before upload
5. **Metadata Storage**: Store artifact metadata (type, size, created_at) in database

---

**Status**: ✅ Complete - Artifacts now uploaded to MinIO automatically after task completion

**Commit**: f9ec09a - "feat: add MinIO artifact upload for agent tasks"
