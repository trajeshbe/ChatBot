# Training Container Volume Mount Issue - Root Cause

**Date**: 2025-12-18  
**Status**: 🔧 ROOT CAUSE IDENTIFIED - Fix in Progress

---

## Current Status

✅ **FIXED Issues** (7/8):
1. ✅ GPU memory requirement (6GB vs 12GB)
2. ✅ Missing imports (FineTuningDataset, User)
3. ✅ Docker image (using agent-runtime:llm-enabled)
4. ✅ Docker network (chatbot_rag-network)
5. ✅ Trainer script path (as file, not module)
6. ✅ Workspace permissions (mode=0o777)
7. ✅ Workspace path (using FINETUNING_WORKSPACE_BASE env var)

⚠️ **REMAINING Issue** (1/8):
- ❌ Volume mount - Training container can't access workspace files

---

## The Problem

**Error**: `FileNotFoundError: [Errno 2] No such file or directory: '/workspace/input/training_config.json'`

**Where It Occurs**: Inside the training container when the trainer script tries to read the config file.

**Root Cause**: The training container cannot see files created in the workspace because of how Docker volume mounts work from container-to-container.

---

## Technical Details

### Current Architecture

1. **Celery Worker Container**:
   - Has volume mount: `finetuning_workspaces:/workspace/finetuning`
   - Creates workspace at: `/workspace/finetuning/{job_id}/`
   - Creates config file at: `/workspace/finetuning/{job_id}/input/training_config.json`
   - ✅ This works - file exists and can be read by celery worker

2. **Training Container** (created by celery worker):
   - Tries to mount: `str(workspace["base"])` → `/workspace/finetuning/{job_id}` → `/workspace` in container
   - **Problem**: Docker interprets this as a bind mount from HOST, not from celery worker's volume
   - Result: Empty `/workspace` directory in training container
   - File at `/workspace/input/training_config.json` doesn't exist

### Why This Doesn't Work

When Container A (celery worker) creates Container B (training container) with a volume mount:

```python
volumes={
    "/workspace/finetuning/{job_id}": {'bind': '/workspace', 'mode': 'rw'}
}
```

Docker looks for `/workspace/finetuning/{job_id}` on the **HOST filesystem**, NOT inside Container A's mounted volumes.

---

## The Solution

### Option 1: Mount the Same Docker Volume (RECOMMENDED)

Instead of trying to mount a path, mount the same Docker volume to both containers:

**Celery Worker** (docker-compose.yml):
```yaml
volumes:
  - finetuning_workspaces:/workspace/finetuning
```

**Training Container** (created by Python code):
```python
volumes={
    "chatbot_finetuning_workspaces": {  # Volume name from docker-compose
        'bind': '/workspace/finetuning',
        'mode': 'rw'
    }
}
```

Then update the container command to use the full path:
```python
command=[
    "python",
    f"/app/app/services/finetuning/trainers/{trainer_script}",
    "--config", f"/workspace/finetuning/{job_id}/input/training_config.json",
    "--output", f"/workspace/finetuning/{job_id}/output",
    "--log-dir", f"/workspace/finetuning/{job_id}/logs"
],
```

### Option 2: Use Host Bind Mount

Mount a host directory (like `/tmp`) to both containers:

**docker-compose.yml**:
```yaml
celery-worker:
  volumes:
    - /tmp/finetuning_workspaces:/workspace/finetuning
```

**Python code**:
```python
volumes={
    "/tmp/finetuning_workspaces/{job_id}": {'bind': '/workspace', 'mode': 'rw'}
}
```

---

## Implementation Plan

### Step 1: Update finetuning_sandbox_manager.py

Change line 297-306 from:
```python
volumes={
    str(workspace["base"]): {
        'bind': '/workspace',
        'mode': 'rw'
    },
    self.backend_path: {
        'bind': '/app',
        'mode': 'ro'
    }
},
```

To:
```python
volumes={
    "chatbot_finetuning_workspaces": {
        'bind': '/workspace/finetuning',
        'mode': 'rw'
    },
    self.backend_path: {
        'bind': '/app',
        'mode': 'ro'
    }
},
```

### Step 2: Update Container Command

Change line 312-318 from:
```python
command=[
    "python",
    f"/app/app/services/finetuning/trainers/{trainer_script}",
    "--config", "/workspace/input/training_config.json",
    "--output", "/workspace/output",
    "--log-dir", "/workspace/logs"
],
```

To:
```python
command=[
    "python",
    f"/app/app/services/finetuning/trainers/{trainer_script}",
    "--config", f"/workspace/finetuning/{job_id}/input/training_config.json",
    "--output", f"/workspace/finetuning/{job_id}/output",
    "--log-dir", f"/workspace/finetuning/{job_id}/logs"
],
```

### Step 3: Test

1. Restart celery worker
2. Submit training job
3. Verify config file is accessible in training container
4. Verify training starts successfully

---

## Files to Modify

1. **backend/app/services/finetuning/finetuning_sandbox_manager.py**
   - Line 297-306: Volume mount configuration
   - Line 312-318: Container command with file paths

---

## Expected Result

After the fix:
- ✅ Training container mounts the same Docker volume as celery worker
- ✅ Config file visible at `/workspace/finetuning/{job_id}/input/training_config.json`
- ✅ Trainer script can read config and start training
- ✅ Training executes successfully

---

**Next Step**: Apply Option 1 (mount Docker volume by name) and test.

---

**Session**: Volume Mount Fix
**Date**: 2025-12-18
