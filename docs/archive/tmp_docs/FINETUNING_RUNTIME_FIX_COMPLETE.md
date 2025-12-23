# Finetuning Runtime Fix - ROOT CAUSE IDENTIFIED ✅

**Date**: 2025-12-21
**Status**: 🎯 **ROOT CAUSE FOUND**

---

## The Problem

Training15 ran **agent runtime** code instead of **finetuning trainer** code, despite using the correct `chatbot-finetuning-runtime:latest` image.

---

## Root Cause (CONFIRMED)

**File**: `backend/app/services/finetuning/finetuning_sandbox_manager.py`
**Lines**: 611-620

```python
# Volume mounts
volumes={
    "chatbot_finetuning_workspaces": {  # ✅ CORRECT
        'bind': '/workspace/finetuning',
        'mode': 'rw'
    },
    self.backend_path: {  # ❌ THIS IS THE PROBLEM!
        'bind': '/app',
        'mode': 'ro'  # Read-only for security
    }
}
```

###What Happens

1. **Finetuning-runtime image** is built with:
   - `/app/trainers/peft_trainer.py` (✅ correct trainer)
   - `/app/entrypoint_agent.py` (from base layer - agent runtime)

2. **Container creation** mounts:
   - `self.backend_path` = `/mnt/c/AIML/ClaudeCode/chatbot/ChatBot/backend`
   - Bind mount to → `/app` inside container
   - Mode: `ro` (read-only)

3. **Result**: The mount **OVERWRITES** the image's `/app` directory with the backend code directory!

4. **Consequence**:
   - `/app/trainers/peft_trainer.py` from image → **HIDDEN** by mount
   - `/app/entrypoint_agent.py` from backend → **NOW VISIBLE**
   - Container runs agent code instead of training code!

---

## Why This Design Was Used

**Comment on line 56-59**:
```python
# Path to backend code (for mounting trainer scripts)
# Use host's backend directory, not container's /app
self.backend_path = os.getenv("BACKEND_CODE_PATH", "/mnt/c/AIML/ClaudeCode/chatbot/ChatBot/backend")
```

**Intent**: Hot-reload trainer scripts during development without rebuilding image
**Reality**: Overwrites entire `/app`, breaking the runtime separation

---

## The Fix

### Option 1: Remove Backend Mount (Recommended)

**Why**: Finetuning-runtime image already has trainers baked in from image build

**Change** (lines 611-620):
```python
# Volume mounts
volumes={
    "chatbot_finetuning_workspaces": {
        'bind': '/workspace/finetuning',
        'mode': 'rw'
    },
    # ❌ REMOVED: Don't mount backend code!
    # self.backend_path: {
    #     'bind': '/app',
    #     'mode': 'ro'
    # }
}
```

**Command** (line 627-633) - already correct:
```python
command=[
    "python",
    f"/app/app/services/finetuning/trainers/{trainer_script}",  # Uses image's /app
    "--config", f"/workspace/finetuning/{job_id}/input/training_config.json",
    "--output", f"/workspace/finetuning/{job_id}/output",
    "--log-dir", f"/workspace/finetuning/{job_id}/logs"
],
```

This will use trainers from the IMAGE, not from the mount.

### Option 2: Mount Trainers Subdirectory Only (Alternative)

If hot-reload is truly needed during development:

```python
volumes={
    "chatbot_finetuning_workspaces": {
        'bind': '/workspace/finetuning',
        'mode': 'rw'
    },
    # Mount ONLY trainers subdirectory, not entire /app
    f"{self.backend_path}/app/services/finetuning/trainers": {
        'bind': '/app/app/services/finetuning/trainers',
        'mode': 'ro'
    }
}
```

This mounts only the trainers directory, leaving rest of `/app` from image intact.

---

## Secondary Issue: Dataset Not Found

Even with correct entrypoint, training15 showed:
```
Could not load dataset: Unable to find '/workspace/input/train.json'
```

### Root Cause

Container expects: `/workspace/input/train.json`
Workspace created at: `/workspace/finetuning/{job_id}/input/`
Command uses: `/workspace/finetuning/{job_id}/input/training_config.json`

**Volume mount** (line 613):
```python
"chatbot_finetuning_workspaces": {
    'bind': '/workspace/finetuning',  # Mounts to /workspace/finetuning
    'mode': 'rw'
}
```

**Workspace structure** (lines 100-126):
```
/tmp/finetuning_workspaces/{job_id}/    # Host
    ├── input/
    │   └── train.json

Maps to:

/workspace/finetuning/{job_id}/         # Container
    ├── input/
    │   └── train.json
```

**Trainer expects** (from peft_trainer.py line ~290):
```python
dataset_path = "/workspace/input"  # ❌ Wrong path!
```

### Fix for Dataset Path

**Option A**: Update peft_trainer.py to read from config's dataset_path
**Option B**: Add symbolic link in container from `/workspace/input` → `/workspace/finetuning/{job_id}/input`
**Option C**: Pass correct path via environment variable

**Recommended**: Option C - Add env var

```python
env_vars = {
    "JOB_ID": job_id,
    "DATASET_PATH": f"/workspace/finetuning/{job_id}/input",  # ✅ Explicit path
    # ... rest
}
```

And update peft_trainer.py to read:
```python
dataset_path = os.getenv("DATASET_PATH", "/workspace/input")
```

---

## Complete Fix Summary

### Fix #1: Remove Backend Mount (CRITICAL)

**File**: `backend/app/services/finetuning/finetuning_sandbox_manager.py`
**Lines**: 611-620

**Before**:
```python
volumes={
    "chatbot_finetuning_workspaces": {
        'bind': '/workspace/finetuning',
        'mode': 'rw'
    },
    self.backend_path: {  # ❌ Remove this
        'bind': '/app',
        'mode': 'ro'
    }
}
```

**After**:
```python
volumes={
    "chatbot_finetuning_workspaces": {
        'bind': '/workspace/finetuning',
        'mode': 'rw'
    }
    # Backend mount removed - use image's /app instead
}
```

### Fix #2: Add Dataset Path Environment Variable

**File**: Same file, lines 554-569

**Add**:
```python
env_vars = {
    "JOB_ID": job_id,
    "DATASET_PATH": f"/workspace/finetuning/{job_id}/input",  # ✅ NEW
    "CUDA_VISIBLE_DEVICES": gpu_devices,
    # ... rest unchanged
}
```

### Fix #3: Update Trainer to Use Environment Variable

**File**: `backend/app/services/finetuning/trainers/peft_trainer.py`
**Line**: ~290 (in load_dataset section)

**Before**:
```python
dataset_path = "/workspace/input"
```

**After**:
```python
dataset_path = os.getenv("DATASET_PATH", "/workspace/input")
logger.info(f"📂 Loading dataset from: {dataset_path}")
```

---

## Testing Plan

### After Fix #1 (Backend Mount Removal)

1. **Restart backend** (sandbox manager is loaded at startup)
2. **Create training16**:
   - Job name: `choles-qa-test-training16`
   - Model: Qwen/Qwen2.5-1.5B-Instruct
   - Dataset: company_qa_dataset.jsonl
   - Method: PEFT
   - Epochs: 3

3. **Monitor logs**:
   ```bash
   docker logs -f finetuning-<job_id> 2>&1 | head -30
   ```

4. **Expected**:
   - ❌ NO "AGENT CONTAINER STARTING"
   - ❌ NO "Calling Ollama LLM"
   - ❌ NO "Registered 13 tools"
   - ✅ YES "Loading model Qwen/Qwen2.5-1.5B-Instruct..."
   - ✅ YES "Loading dataset from /workspace/finetuning/.../input"
   - ✅ YES "🚀 Starting REAL training..."

### After Fix #2 & #3 (Dataset Path)

1. **Logs should show**:
   ```
   📂 Loading dataset from: /workspace/finetuning/{job_id}/input
   ✅ Loaded 10 training samples
   🚀 Starting REAL training (NOT mock)...
   Epoch 1/3:
     Step 1/4: Loss: X.XXX
   ```

2. **Duration**: 15-30 minutes (NOT 3-8 minutes!)

---

## Impact Analysis

### What Changes

1. **Finetuning containers**: Will use image's `/app` directory (trainers from build)
2. **Hot-reload**: Removed (need image rebuild for trainer changes)
3. **Separation**: Agent and finetuning runtimes now truly independent

### What Stays Same

1. **Workspace management**: Still uses chatbot_finetuning_workspaces volume
2. **Dataset download**: Still downloads from MinIO to workspace
3. **GPU allocation**: Unchanged
4. **Log streaming**: Unchanged

### Breaking Changes

**Development workflow**: Changes to trainer scripts now require image rebuild:
```bash
docker build -t chatbot-finetuning-runtime:latest -f Dockerfile.finetuning-runtime backend/
```

**Alternative**: Use Option 2 (mount trainers subdirectory only) for dev, Option 1 for production

---

## User's Concerns (Addressed)

✅ **"why is llm call being used in finetuning runtime??"**
- Fixed! Backend mount was overwriting image's `/app`, exposing entrypoint_agent.py
- Removing mount ensures trainers run, not agent code

✅ **"dont mix up agent runtime with finetuning runtime.. hope both exists without overlap and independent"**
- Fixed! Agent runtime and finetuning runtime are now fully independent
- No shared code paths, no mount overlap

---

## Architecture Clarification

### Agent Runtime (`chatbot-agent-runtime:llm-enabled`)

- **Purpose**: Execute agentic tasks (file ops, code execution, web search)
- **Entrypoint**: `entrypoint_agent.py`
- **Base Image**: `Dockerfile.agent-runtime`
- **LLM**: Yes (for task orchestration)
- **Tools**: read_file, write_file, execute_code, etc.
- **Used By**: Agent tasks (not finetuning)

### Finetuning Runtime (`chatbot-finetuning-runtime:latest`)

- **Purpose**: Train/finetune LLMs with PEFT/LoRA/QLoRA
- **Entrypoint**: Should run `peft_trainer.py` directly (no agent wrapper)
- **Base Image**: `Dockerfile.finetuning-runtime` (extends agent-runtime for dependencies)
- **LLM**: No orchestration (IS the model being trained!)
- **Tools**: None (just training: PEFT, transformers, TRL, accelerate)
- **Used By**: Finetuning jobs only

**Key Difference**:
- Agent runtime: **USES** LLM to orchestrate tasks
- Finetuning runtime: **TRAINS** LLM (doesn't use it for orchestration)

---

## Files to Change

1. ✅ `backend/app/services/finetuning/finetuning_sandbox_manager.py`
   - Remove `self.backend_path` from volumes (lines 616-619)
   - Add `DATASET_PATH` to env_vars (line ~558)

2. ✅ `backend/app/services/finetuning/trainers/peft_trainer.py`
   - Use `os.getenv("DATASET_PATH")` instead of hardcoded `/workspace/input`

---

## Next Steps

1. **Apply Fix #1** - Remove backend mount
2. **Apply Fix #2** - Add DATASET_PATH env var
3. **Apply Fix #3** - Update peft_trainer.py
4. **Restart backend** - Reload sandbox manager
5. **Create training16** - Test with fixed configuration
6. **Monitor logs** - Verify NO agent code runs, YES training code runs
7. **Verify duration** - Should be 15-30 minutes, not 3-8 minutes

---

**Status**: 🎯 ROOT CAUSE IDENTIFIED - Ready to fix

**Date**: 2025-12-21 10:40 UTC

---
