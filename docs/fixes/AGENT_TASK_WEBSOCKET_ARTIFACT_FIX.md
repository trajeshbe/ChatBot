# Agent Task WebSocket & Artifact URL Fix

> **Date**: 2025-12-13
> **Status**: ✅ Complete
> **Commits**: 2 (20a71b9, cf5d5b7)

---

## Issues Fixed

### 1. ✅ `iterations_completed` AttributeError

**Problem**: WebSocket failed when task completed with:
```
'AgentTaskStatusResponse' object has no attribute 'iterations_completed'
```

**Root Cause**: `agent_routes.py:1146` tried to access `task_status.iterations_completed` but the schema only has `current_iteration`

**Fix**: Changed line 1146 from:
```python
"iterations": task_status.iterations_completed,
```
to:
```python
"iterations": task_status.current_iteration,
```

**Impact**: Agent task completion now displays properly in UI without WebSocket errors.

---

### 2. ✅ Artifact URLs Not Retained

**Problem**: Artifact information only sent filenames, losing MinIO path and download URLs:
```python
"artifacts": [Path(a).name for a in (task_status.artifacts or [])],  # Only filename!
```

**Root Cause**: WebSocket completion response stripped path information, making artifacts un-downloadable.

**Fix**: Enhanced WebSocket response to build complete artifact objects (lines 1139-1163):

```python
# Build artifact URLs for download
artifacts_with_urls = []
if task_status.artifacts and task_status.minio_base_path:
    for artifact_path in task_status.artifacts:
        artifact_name = Path(artifact_path).name
        # Construct MinIO download URL
        minio_path = f"{task_status.minio_base_path}{artifact_name}"
        download_url = f"/api/v1/agents/tasks/{task_id}/artifacts/{artifact_name}"
        artifacts_with_urls.append({
            "name": artifact_name,
            "path": artifact_path,
            "minio_path": minio_path,
            "download_url": download_url
        })

await websocket.send_json({
    ...
    "artifacts": artifacts_with_urls,
    "minio_base_path": task_status.minio_base_path,
    ...
})
```

**New Artifact Response Structure**:
```json
{
  "artifacts": [
    {
      "name": "sales_chart.html",
      "path": "/workspace/output/sales_chart.html",
      "minio_path": "Technology/Backend-Development/Construction-Intelligence/admin/agent-tasks/generate_sales_report/task-abc123/sales_chart.html",
      "download_url": "/api/v1/agents/tasks/task-abc123/artifacts/sales_chart.html"
    }
  ],
  "minio_base_path": "Technology/Backend-Development/Construction-Intelligence/admin/agent-tasks/generate_sales_report/task-abc123/"
}
```

**Impact**:
- ✅ Artifact downloads now have complete URL information
- ✅ MinIO paths retained for file retrieval
- ✅ Frontend can display downloadable links for all artifacts
- ✅ Preserves organizational hierarchy in MinIO

---

## Files Modified

### `backend/app/api/routes/agent_routes.py`
- **Line 1146**: Fixed `iterations_completed` → `current_iteration`
- **Lines 1139-1163**: Enhanced artifact response with URLs

---

## Testing

### Before Fix:
```
❌ WebSocket error: 'AgentTaskStatusResponse' object has no attribute 'iterations_completed'
❌ Artifacts: ["chart.html"]  # No download information
```

### After Fix:
```
✅ Task completed successfully
✅ Artifacts: [
  {
    "name": "chart.html",
    "path": "/workspace/output/chart.html",
    "minio_path": "Technology/.../task-id/chart.html",
    "download_url": "/api/v1/agents/tasks/task-id/artifacts/chart.html"
  }
]
```

---

## Related Files

- **Schema**: `backend/app/schemas/agent_schemas.py` (has `current_iteration` field)
- **Service**: `backend/app/services/agent_service.py` (stores artifacts and minio_base_path)
- **Frontend**: Will need to update to use new artifact structure

---

## Frontend Integration

The frontend should now parse artifacts as objects instead of strings:

**Before**:
```typescript
artifacts.map(filename => <div>{filename}</div>)
```

**After**:
```typescript
artifacts.map(artifact => (
  <div>
    <a href={artifact.download_url} download={artifact.name}>
      📎 {artifact.name}
    </a>
    <span>MinIO: {artifact.minio_path}</span>
  </div>
))
```

---

## Commits

1. **20a71b9**: Fix FORCE_RAG strategy weight override
2. **cf5d5b7**: Fix agent task WebSocket schema and artifact URLs

---

**Status**: ✅ Both fixes deployed and tested
