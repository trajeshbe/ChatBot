# Model Selection UI Sync Fix

**Date**: 2025-12-03
**Status**: ✅ Fixed
**Priority**: P0 - Critical UX Issue

---

## Problem Summary

User reported that when selecting "LLM Vision Model" (llama3.2-vision:11b) in the UI dropdown, the response came from "Qwen2.5-Coder-7B" instead. This violated the principle that **chat UI should respect user's model selection**, and coder models should NOT be used for chat.

### Root Cause Analysis

**Issue 1: Automatic Model Fallback for ALL Queries**
- Location: `backend/app/services/llm_service.py` lines 863-886
- When user selected `llama3.2-vision:11b` (7.8 GB), the LLM service performed a memory check
- If the model didn't fit in available memory, it automatically fell back to another model
- **This fallback was happening for BOTH chat UI and agent tasks**

**Issue 2: Coder Models Not Filtered from Fallback**
- Location: `backend/app/services/llm_service.py` lines 192-195
- When selecting a fallback model due to memory constraints, the system:
  1. Found all Ollama models that fit in memory
  2. Selected the LARGEST model (for best quality)
  3. **Did NOT filter out coder-specific models**
- Available models: qwen2.5-coder:7b (4.7 GB), deepseek-coder:6.7b (3.8 GB), qwen2.5:1.5b (986 MB)
- Result: System selected qwen2.5-coder:7b as the "best" fallback

### User's Requirements

1. **Chat UI**: Use EXACT model selected by user - NO automatic fallback
   - If model doesn't fit, show error or use model anyway
   - User controls the model, system respects it

2. **Agent Tasks**: Can use automatic fallback for resource constraints
   - But must EXCLUDE coder models from fallback options
   - Must revert to UI-selected model after agent task completes

3. **Hybrid Services**: Can use any model dynamically
   - But should revert to UI model after completion

---

## Fixes Applied

### Fix 1: Add `allow_fallback` Control Parameter

**File**: `backend/app/services/llm_service.py`

**Changes**:
1. Added `allow_fallback: bool = False` parameter to `generate()` method (line 814)
2. Added `allow_fallback: bool = False` parameter to `generate_with_context()` method (line 1019)
3. Pass `allow_fallback` through to internal calls (line 1077)

**Logic**:
```python
# generate() method
async def generate(
    self,
    prompt: str,
    messages: Optional[List[Dict]] = None,
    max_tokens: int = 512,
    temperature: float = 0.7,
    model_id: Optional[str] = None,
    allow_fallback: bool = False  # 🆕 Default: False for chat UI
) -> Dict:
```

**Memory Check Logic** (lines 866-891):
```python
# ONLY fallback if allow_fallback=True (agent tasks)
if model_info.provider == ModelProvider.OLLAMA and allow_fallback:
    # Perform memory check and fallback if needed
    memory_check_result = await self._select_model_with_memory_check(model_id)
    # ... fallback logic
elif model_info.provider == ModelProvider.OLLAMA and not allow_fallback:
    # For chat UI: Just use the selected model as-is (no fallback)
    logger.info(f"✅ Using user-selected model: {model_id} (fallback disabled for chat UI)")
```

### Fix 2: Filter Coder Models from Fallback Selection

**File**: `backend/app/services/llm_service.py`

**Changes**: Updated `_select_model_with_memory_check()` method (lines 193-214)

**Before**:
```python
# Filter models that fit in memory (with 20% buffer)
fitting_models = [
    m for m in available_models
    if (m["size_mb"] * 1.2) <= available_mb
]

# Select LARGEST model that fits
best_fit = max(fitting_models, key=lambda m: m["size_mb"])
```

**After**:
```python
# Filter models that fit in memory (with 20% buffer)
# 🆕 CRITICAL FIX: Exclude coder-specific models from fallback
excluded_keywords = ['coder', 'code-', '-code']
fitting_models = [
    m for m in available_models
    if (m["size_mb"] * 1.2) <= available_mb and
    not any(keyword in m["name"].lower() for keyword in excluded_keywords)
]

# Select LARGEST chat model that fits (best quality within constraints)
best_fit = max(fitting_models, key=lambda m: m["size_mb"])
logger.info(f"🔍 Filtered out coder models, selected best chat model: {best_fit['name']}")
```

**Excluded Models**:
- `qwen2.5-coder:7b` ✅ Filtered
- `deepseek-coder:6.7b` ✅ Filtered
- `codellama:*` ✅ Filtered (if present)
- `starcoder:*` ✅ Filtered (if present)

**Allowed Models**:
- `qwen2.5:1.5b` ✅ Chat model
- `llama3.2-vision:11b` ✅ Vision model
- `mistral:*` ✅ Chat model

---

## How It Works Now

### Scenario 1: Chat UI (Default Behavior)

```
User selects: llama3.2-vision:11b in UI dropdown
↓
Frontend passes: model_id="llama3.2-vision:11b" to /api/v1/query
↓
RAG Service calls: llm_service.generate(model_id="llama3.2-vision:11b")
↓
LLM Service:
  - allow_fallback = False (default)
  - Uses llama3.2-vision:11b exactly as selected
  - NO memory check, NO fallback
  - Logs: "✅ Using user-selected model: llama3.2-vision:11b (fallback disabled for chat UI)"
↓
Response uses: llama3.2-vision:11b
```

### Scenario 2: Agent Task (Fallback Allowed)

```
Agent task needs LLM inference
↓
Agent calls: llm_service.generate(model_id="llama3.2-vision:11b", allow_fallback=True)
↓
LLM Service:
  - allow_fallback = True
  - Checks memory: llama3.2-vision:11b requires 7987 MB, only 4000 MB available
  - Fallback triggered
  - Finds fitting models: qwen2.5-coder:7b (4.7 GB), qwen2.5:1.5b (986 MB)
  - Filters out coder models: qwen2.5-coder:7b ❌ EXCLUDED
  - Selects: qwen2.5:1.5b ✅ BEST CHAT MODEL
  - Logs: "🔄 MODEL FALLBACK (AGENT TASK ONLY): qwen2.5:1.5b"
↓
Agent uses: qwen2.5:1.5b for this task
↓
After task completes, revert to UI model (handled by agent logic)
```

### Scenario 3: Hybrid Service

Hybrid services (like construction metrics with Vision LLM + OCR + OpenCV) can:
- Use specific models internally as needed
- NOT affected by `allow_fallback` parameter
- Each hybrid service manages its own model selection
- After completion, response uses the UI-selected model for final answer

---

## Testing

### Test 1: Chat UI Model Respect
```bash
# 1. Open chat UI: http://localhost:3001
# 2. Select "Llama3.2-Vision:11B" from model dropdown
# 3. Ask: "tell me about your creator and who are you?"
# 4. Verify response model shows: "llama3.2-vision:11b" (NOT qwen2.5-coder)
```

**Expected Backend Logs**:
```
🎯 Model requested: llama3.2-vision:11b
✅ Routing to: Llama 3.2 Vision 11B via ollama provider
✅ Using user-selected model: llama3.2-vision:11b (fallback disabled for chat UI)
```

### Test 2: Agent Task Fallback (When Enabled)
```bash
# This would require agent code to explicitly set allow_fallback=True
# Currently, all chat queries use allow_fallback=False by default
```

### Test 3: Verify Coder Model Filtering
```bash
# Check that qwen2.5-coder and deepseek-coder are excluded from default selection
docker-compose logs backend | grep "Filtered to.*chat-appropriate models"
```

---

## Files Modified

### Backend
- ✅ `backend/app/services/llm_service.py`
  - Line 814: Added `allow_fallback=False` parameter to `generate()`
  - Lines 866-891: Updated memory check logic to respect `allow_fallback`
  - Lines 193-214: Filter coder models from fallback selection
  - Line 1019: Added `allow_fallback=False` parameter to `generate_with_context()`
  - Line 1077: Pass `allow_fallback` through to `generate()`

### Documentation
- ✅ `docs/fixes/MODEL_SELECTION_UI_SYNC_FIX.md` (NEW - this file)

---

## Impact

✅ **User Experience**: Chat UI now respects exact model selection - no surprises!
✅ **Consistency**: Model shown in UI = Model used for response
✅ **Agent Tasks**: Can still use intelligent fallback when needed
✅ **Coder Models**: Properly excluded from chat UI (reserved for agent tasks)
✅ **Transparency**: Clear logging shows when fallback occurs (agent tasks only)

---

## Related Issues Fixed

1. ✅ Qwen2.5-Coder appearing in chat responses despite Vision model selected
2. ✅ Deepseeker-Coder appearing in default model selection (fixed earlier)
3. ✅ Lack of transparency when model fallback occurs

---

## Future Enhancements

1. **UI Warning**: Show warning if selected model won't fit in memory
2. **Model Memory Info**: Display model memory requirements in dropdown
3. **Fallback Preferences**: Allow user to configure fallback behavior per model
4. **Agent Model Tracking**: Show which model was used by each agent task

---

**End of Document**
