# Fine-Tuning Training Container Issue - Investigation

**Date**: 2025-12-18
**Status**: 🔧 IN PROGRESS - Container exits immediately without training

---

## Issues Fixed So Far

### ✅ Issue 1: GPU Memory (FIXED)
- Changed `min_gpu_memory_gb` from 12.0GB to 6.0GB for RTX 5060 Laptop GPU (8GB total)

### ✅ Issue 2: Missing Imports (FIXED)
- Added `FineTuningDataset` and `User` model imports in `finetuning_tasks.py`

### ✅ Issue 3: Docker Image (FIXED)
- Changed from `chatbot-finetuning-runtime:latest` to `chatbot-agent-runtime:llm-enabled`

### ✅ Issue 4: Docker Network (FIXED)
- Changed from `chatbot_default` to `chatbot_rag-network` in `agent_sandbox_manager.py:36`

### ✅ Issue 5: Trainer Script Path (FIXED)
- Changed from `python /app/trainers/{script}` to `python -m app.services.finetuning.trainers.{module}`

---

## Current Issue: Container Exits Immediately

### Symptoms
- Container created successfully
- GPU allocated successfully (6GB requirement)
- Network connection works
- But training completes in < 1 second with no actual training

### Container Command
```python
command=[
    "python", "-m", f"app.services.finetuning.trainers.{trainer_script.replace('.py', '')}",
    "--config", "/workspace/input/training_config.json",
    "--output", "/workspace/output",
    "--log-dir", "/workspace/logs"
]
```

### Expected Trainer Module
For SFT training: `app.services.finetuning.trainers.sft_trainer`

### Trainer Location in Backend Container
`/app/app/services/finetuning/trainers/sft_trainer.py`

---

## Hypothesis

The trainer scripts might not be designed to run as standalone modules with CLI arguments. They might need to be invoked differently or need a wrapper script.

### Next Steps
1. Check if trainer scripts have `if __name__ == "__main__":` entry points
2. Check if they support `--config`, `--output`, `--log-dir` arguments
3. May need to create a wrapper script or modify how trainers are invoked
4. Check if training config is being created properly in workspace

---

## Files Modified

1. **backend/app/tasks/finetuning_tasks.py**
   - Lines 30-31: Added imports
   - Line 325: GPU memory configuration

2. **backend/app/services/agent_sandbox_manager.py**
   - Line 36: Changed network name

3. **backend/app/services/finetuning/finetuning_sandbox_manager.py**
   - Line 51: Changed Docker image
   - Lines 299-305: Changed trainer command to Python module

---

## Job Details
- Job ID: `67bf9641-64f8-40d1-8229-40802bd10462`
- Job Name: `short_story_job`
- Dataset: `story8`
- Base Model: `Qwen/Qwen2.5-1.5B`
- Method: `peft` (likely using `sft_trainer.py`)

---

**Next Action**: Check trainer script structure and modify invocation method if needed.
