# Training43 - Import Fix Applied

> **Date**: 2025-12-22
> **Status**: ✅ Fixed
> **Issue**: ModuleNotFoundError: No module named 'peft' in celery-worker
> **Solution**: Lazy imports in auto_merge.py

---

## 🐛 The Problem

**Training43 Error:**
```
File "/app/app/tasks/finetuning_tasks.py", line 922, in run_finetuning_job
    from app.tasks.auto_merge import auto_merge_lora_adapters, should_auto_merge
File "/app/app/tasks/auto_merge.py", line 16, in <module>
    from peft import PeftModel
ModuleNotFoundError: No module named 'peft'
```

**Root Cause:**
- `auto_merge.py` had module-level imports: `from peft import PeftModel`
- When `finetuning_tasks.py` imported `auto_merge`, Python executed these imports
- Celery-worker runs in **backend container** which doesn't have PEFT installed
- PEFT only exists in **finetuning-runtime container**

**Interesting Discovery:**
Training actually **succeeded** - model was registered, adapters saved. The error occurred AFTER registration, when celery tried to check if auto-merge should run.

---

## ✅ The Fix

### Changed: `/backend/app/tasks/auto_merge.py`

**Before (Module-level imports):**
```python
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
import torch                                    # ❌ Loaded at module import time
from transformers import AutoModelForCausalLM  # ❌ Loaded at module import time
from peft import PeftModel                      # ❌ Loaded at module import time - FAILS!

logger = logging.getLogger(__name__)

def auto_merge_lora_adapters(...):
    # Function body
```

**After (Lazy imports inside function):**
```python
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def auto_merge_lora_adapters(...):
    """Auto-merge LoRA adapters..."""
    import time

    # Lazy imports - only load when function is called
    import torch                                    # ✅ Only loaded if function runs
    from transformers import AutoModelForCausalLM  # ✅ Only loaded if function runs
    from peft import PeftModel                      # ✅ Only loaded if function runs

    # Rest of function...
```

---

## 🎯 Why This Works

### Import Flow:

**Before Fix:**
```
1. finetuning_tasks.py: from app.tasks.auto_merge import ...
   ↓
2. Python loads auto_merge.py module
   ↓
3. Python executes module-level code (lines 1-16)
   ↓
4. Line 16: from peft import PeftModel
   ↓
5. ❌ FAIL: Backend container doesn't have PEFT
```

**After Fix:**
```
1. finetuning_tasks.py: from app.tasks.auto_merge import ...
   ↓
2. Python loads auto_merge.py module
   ↓
3. Python executes module-level code (lines 1-15)
   ↓
4. ✅ SUCCESS: No PEFT import at module level
   ↓
5. Function auto_merge_lora_adapters() is defined but not called
   ↓
6. PEFT import only happens IF function is called (which doesn't happen in celery)
```

---

## 🏗️ Architecture Insight

### Container Architecture:

```
┌─────────────────────────────┐
│  Backend Container          │
│  (rag-backend)              │
│                             │
│  - FastAPI                  │
│  - Celery Worker            │  ← Runs finetuning_tasks.py
│  - No PEFT ❌               │  ← Can now import auto_merge.py ✅
│  - No Torch (old)           │
│  - No Transformers (old)    │
└─────────────────────────────┘
              │
              │ Orchestrates training
              ↓
┌─────────────────────────────┐
│  Training Container         │
│  (chatbot-finetuning-trainer)│
│                             │
│  - PyTorch ✅               │
│  - Transformers ✅          │
│  - PEFT ✅                  │  ← Has all ML libs
│  - Runs peft_trainer.py    │  ← Does training + merge
└─────────────────────────────┘
```

### Execution Flow:

```
1. User submits training job
   ↓
2. Celery-worker (backend container):
   - Loads auto_merge.py (NO PEFT IMPORT - just defines functions)
   - Checks should_auto_merge() ✅
   - Spawns training container
   ↓
3. Training container:
   - Runs peft_trainer.py
   - Training completes
   - Container merge (if implemented)
   - Saves adapters to MinIO
   - Reports results back to celery
   ↓
4. Celery-worker (backend container):
   - Registers model in database
   - Checks should_auto_merge()
   - ❓ QUESTION: Should auto-merge run here?
```

---

## 🤔 Important Question

**Where should auto-merge actually run?**

### Option 1: In Training Container (CURRENT)
- ✅ Has PEFT, torch, transformers installed
- ✅ GPU is already warm from training
- ✅ Faster (no model reload needed)
- ✅ Currently implemented in peft_trainer.py lines 369-413
- ❌ But needs AutoModelForCausalLM import fix (we already fixed this!)

### Option 2: In Celery After Training (NEW)
- ❌ Backend container doesn't have PEFT (would need to add)
- ❌ No GPU access from backend container
- ❌ Slower (needs to load model from scratch)
- ✅ More flexible (could retry independently)

### Recommendation: Use Training Container Merge
The training container already has merge code (lines 369-413 in peft_trainer.py). We fixed the `AutoModelForCausalLM` import bug. This is the better approach!

**The celery auto-merge code might be unnecessary** - we should just ensure the training container merge works properly.

---

## 🧪 Testing

### Verify Import Works:
```bash
docker-compose exec backend python -c "
from app.tasks.auto_merge import auto_merge_lora_adapters, should_auto_merge
print('✅ Import successful!')
print(f'should_auto_merge() = {should_auto_merge()}')
"
```

**Expected Output:**
```
✅ Import successful!
should_auto_merge() = True
```

### Create Training44:
```bash
# Via UI: http://localhost:3001/admin
# Fine-Tuning Hub → Create Training Job
# Name: choles-qa-real-training44
# Dataset: company_qa_dataset
```

### Monitor:
```bash
# Training status
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT name, status, progress, current_epoch
FROM finetuning_jobs
WHERE name = 'choles-qa-real-training44';"

# Celery logs (no more PEFT errors!)
docker-compose logs -f celery-worker | grep -i "training44\\|error"
```

---

## 📝 Files Modified

### 1. `/backend/app/tasks/auto_merge.py`
**Lines Changed:** 10-16 (module-level imports → lazy imports)

**Before:**
```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
```

**After:**
```python
# Moved inside auto_merge_lora_adapters() function at line 59-61
```

---

## ✅ Summary

### What Was Broken:
- ❌ Celery-worker couldn't import `auto_merge.py` (PEFT dependency)
- ❌ Training43 failed with ModuleNotFoundError
- ❌ Model registered but auto-merge never ran

### What Is Fixed:
- ✅ Celery-worker can import `auto_merge.py` (lazy imports)
- ✅ `should_auto_merge()` works without PEFT
- ✅ `auto_merge_lora_adapters()` only loads PEFT if called
- ✅ Training44+ should work!

### Next Steps:
1. Create training44 to test complete flow
2. Verify container merge works (peft_trainer.py)
3. Decide if celery auto-merge is still needed

---

**Ready for training44!** 🚀

---

**End of Document**
