# Training15 - CRITICAL ROOT CAUSE FOUND

**Date**: 2025-12-21
**Status**: 🚨 **CRITICAL ISSUE DISCOVERED**

---

## Summary

Training15 (choles-qa-real-training15) completed in 4.9 minutes with **MOCK training** despite:
- ✅ Finetuning-runtime image rebuilt with uncommented training code
- ✅ Team path correctly set to ITM11
- ❌ **Dataset file not found in container**
- ❌ **WRONG CONTAINER IMAGE USED** - logs show agent runtime, not finetuning runtime!

---

## Issue #1: Dataset File Not Found

### Error from Logs

```
2025-12-21 10:28:00,450 - Loading dataset from /workspace/input...
2025-12-21 10:28:01,314 - WARNING - Could not load dataset: Unable to find '/workspace/input/train.json'
2025-12-21 10:28:01,314 - INFO - Using dummy dataset for testing
2025-12-21 10:28:01,443 - INFO - ⚠️ No dataset provided, creating mock training result with merge step
```

### Root Cause

The peft_trainer.py expects dataset at `/workspace/input/train.json`, but:
- Dataset is in MinIO at: `technology/itm11/global/admin/finetuning/datasets/company_qa_dataset/added64c-16fd-42a9-9370-e08f2516f198/company_qa_dataset.jsonl`
- Dataset may not have been downloaded to container
- Path mapping may be incorrect

### Evidence

```json
"dataset_id": "added64c-16fd-42a9-9370-e08f2516f198",
"dataset_path": "/workspace/input",
"dataset_minio_path": "technology/itm11/global/admin/finetuning/datasets/company_qa_dataset/added64c-16fd-42a9-9370-e08f2516f198/company_qa_dataset.jsonl"
```

Container expected file at `/workspace/input/train.json` but it wasn't there.

---

## Issue #2: AGENT RUNTIME vs FINETUNING RUNTIME OVERLAP

### **CRITICAL DISCOVERY**: Wrong Image Used

**Logs show**:
```
2025-12-21 10:29:28,515 - __main__ - INFO - 🤖 AGENT CONTAINER STARTING
2025-12-21 10:29:28,515 - __main__ - INFO - 📚 Registered 13 tools (6 core + 7 enhanced + install_package)
2025-12-21 10:29:28,695 - __main__ - INFO - 🤖 Calling Ollama LLM: llama3.2-vision:11b
2025-12-21 10:29:32,510 - __main__ - ERROR - ❌ LLM call failed (both OpenAI and Ollama): [Errno -2] Name or service not known
```

**This is entrypoint_agent.py, NOT peft_trainer.py!**

### User is Correct

> "why is llm call being used in finetuning runtime??"
> "dont mix up agent runtime with finetuning runtime.. hope both exists without overlap and independent"

**You're absolutely right!** The container logs show:
- Agent container starting ❌ (should be finetuning trainer)
- LLM calls being made ❌ (finetuning doesn't need this)
- Agent tools registered ❌ (finetuning doesn't need this)
- Network errors resolving 'minio' ❌ (wrong entrypoint)

### What Should Have Happened

**Finetuning container should**:
1. Run `peft_trainer.py` as entrypoint
2. Load dataset from `/workspace/input/`
3. Load model with PEFT/QLoRA
4. Run training loop (Epoch 1, 2, 3...)
5. Save adapter weights
6. Merge model (optional)
7. Upload to MinIO

**Should NOT**:
- ❌ Start agent orchestrator
- ❌ Call LLM for task routing
- ❌ Register agent tools
- ❌ Run agentic loop

---

## Root Cause Analysis

### Architecture Confusion

**Two SEPARATE runtimes should exist**:

1. **Agent Runtime** (`chatbot-agent-runtime:llm-enabled`)
   - Purpose: Execute agentic tasks (file operations, code execution, tool use)
   - Entrypoint: `entrypoint_agent.py`
   - Tools: read_file, write_file, execute_code, web_search, etc.
   - LLM: Yes (for task orchestration)
   - Network: Needs to connect to backend, MinIO, Ollama

2. **Finetuning Runtime** (`chatbot-finetuning-runtime:latest`)
   - Purpose: Train/finetune LLMs with PEFT/LoRA
   - Entrypoint: Should be `peft_trainer.py` (or wrapper script)
   - Tools: None (just training libraries: PEFT, transformers, TRL)
   - LLM: No (IT IS the model being trained!)
   - Network: Minimal (just MinIO for dataset download and model upload)

### What's Wrong

**Finetuning containers are using AGENT entrypoint!**

Check Dockerfile.finetuning-runtime:
```dockerfile
# Current (line 45)
CMD ["python", "/app/trainers/peft_trainer.py", "--help"]

# But container logs show entrypoint_agent.py running!
```

**Hypothesis**: The finetuning_sandbox_manager.py might be:
1. Mounting /app from backend (which has entrypoint_agent.py)
2. Not properly setting entrypoint to peft_trainer.py
3. Using wrong base image (agent-runtime instead of clean base)

---

## Files to Investigate

### 1. Finetuning Sandbox Manager

**File**: `backend/app/services/finetuning/finetuning_sandbox_manager.py`

**Check**:
- Container creation command (lines ~150-200)
- Volume mounts (is /app being mounted from backend?)
- Entrypoint override (is it setting CMD correctly?)
- Base image (should be chatbot-finetuning-runtime, not agent-runtime)

### 2. Dockerfile.finetuning-runtime

**File**: `backend/Dockerfile.finetuning-runtime`

**Current**:
```dockerfile
FROM chatbot-agent-runtime:llm-enabled  # ⚠️ May be the issue!

CMD ["python", "/app/trainers/peft_trainer.py", "--help"]
```

**Question**: Why does it extend agent-runtime? Should it have its own clean base?

### 3. Docker Compose

**File**: `docker-compose.yml`

**Check**: How is finetuning-runtime service defined? Does it have correct entrypoint?

---

## Dataset Download Issue

### Expected Flow

1. **Celery task** (finetuning_tasks.py):
   - Downloads dataset from MinIO
   - Saves to `/workspace/input/train.json`
   - Creates container with volume mount

2. **Finetuning container**:
   - Reads from `/workspace/input/train.json`
   - Loads into datasets.Dataset
   - Trains model

### Actual Behavior

Container logs show:
```
"dataset_path": "/workspace/input"
"dataset_minio_path": "technology/itm11/.../company_qa_dataset.jsonl"

# But then:
Could not load dataset: Unable to find '/workspace/input/train.json'
```

**Possible causes**:
1. Dataset not downloaded from MinIO
2. Downloaded but to wrong path
3. Downloaded with wrong filename (company_qa_dataset.jsonl vs train.json)
4. Volume mount not working

---

## Action Items

### Priority 1: Separate Agent and Finetuning Runtimes

1. **Read finetuning_sandbox_manager.py**:
   - Check container creation logic
   - Verify entrypoint is set to peft_trainer.py
   - Confirm base image is finetuning-runtime

2. **Verify Dockerfile.finetuning-runtime**:
   - Should it extend agent-runtime? (Probably not!)
   - Consider creating clean base with just training deps
   - Ensure CMD points to peft_trainer.py

3. **Test with fixed entrypoint**:
   - Create training16 with explicit entrypoint
   - Verify no "AGENT CONTAINER STARTING" logs
   - Verify peft_trainer.py runs

### Priority 2: Fix Dataset Download

1. **Read finetuning_tasks.py**:
   - Check `download_dataset_from_minio()` function
   - Verify it saves to `/workspace/input/train.json`
   - Check if filename conversion happens (jsonl → json)

2. **Check dataset preprocessing**:
   - Does dataset_preprocessor.py handle company_qa_dataset.jsonl?
   - Is it converting to train.json format?

3. **Verify volume mounts**:
   - Check if `/workspace/input` is correctly mounted
   - Test with manual file placement

### Priority 3: Update Documentation

User is correct about separation concerns:
- Agent runtime: For agentic tasks
- Finetuning runtime: For model training
- **NO OVERLAP** should exist

---

## Next Steps (Immediate)

1. **Read finetuning_sandbox_manager.py** to understand container creation
2. **Identify why agent entrypoint is running** instead of training entrypoint
3. **Fix entrypoint** to use peft_trainer.py
4. **Investigate dataset download** from MinIO
5. **Create training16** with fixes applied

---

## User's Correct Concerns

✅ "why is llm call being used in finetuning runtime??"
- **You're right!** Finetuning should NOT call LLM
- Logs show entrypoint_agent.py running (wrong!)
- Should be peft_trainer.py

✅ "dont mix up agent runtime with finetuning runtime.. hope both exists without overlap and independent"
- **Absolutely correct!**
- They should be independent
- Finetuning-runtime extends agent-runtime (may be the issue)
- Need to verify separation of concerns

---

## Summary

**Two critical issues**:

1. **Wrong entrypoint**: Container is running entrypoint_agent.py (agent runtime) instead of peft_trainer.py (finetuning runtime)

2. **Dataset not found**: Even if entrypoint was correct, dataset file missing from `/workspace/input/train.json`

**Root cause**: Likely in finetuning_sandbox_manager.py container creation logic.

**User is correct**: Agent and finetuning runtimes should be completely independent with no overlap.

---

**Status**: ❌ CRITICAL - Requires immediate investigation

**Next**: Read finetuning_sandbox_manager.py to understand container creation

---

**Date**: 2025-12-21 10:35 UTC

---
