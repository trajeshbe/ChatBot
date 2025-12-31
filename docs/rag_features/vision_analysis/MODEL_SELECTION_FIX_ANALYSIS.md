# Model Selection Fix - Vision Analysis Tool

**Date**: 2025-12-08
**Issue**: UI-selected model (qwen2.5vl:latest) not being used in vision_analysis tool
**Status**: 🔧 **FIX IDENTIFIED**

---

## 🎯 Problem Summary

User selected **qwen2.5vl:latest** in the UI, but the vision_analysis tool may not be using this model for vision analysis.

**User's Request**:
> "hold on i have selected qwen 2.5 VL model.. can you ensure that the UI model selected is chosen in vision analysis"

---

## 🔍 Root Cause Analysis

### File: `/backend/app/agents/tool_registry.py`

**Lines 1491-1519: `_wrap_vision_analysis` method**

```python
# Extract UI-selected model_id from kwargs (passed from TaskRouter)
model_id = kwargs.get('model_id')

# Analyze with vision model
if question:
    # ❌ PATH 1: Specific question mode - NO model_id passed
    result = await vision_service.describe_image(image_path, question=question)
    text_content = result
else:
    # ✅ PATH 2: General analysis mode - model_id PASSED
    logger.info(f"🎯 Calling vision analysis with model_id: {model_id}")
    result_dict = await vision_service.process_image(
        image_path,
        prompt=None,
        model_id=model_id,  # Pass UI-selected model
        allow_fallback=True
    )
    text_content = result_dict.get("text", "")
```

**Problem**:
- When `question` parameter is provided (line 1495-1498), the code calls `describe_image()` WITHOUT passing `model_id`
- When no `question` (line 1499-1508), the code correctly passes `model_id` to `process_image()`

### File: `/backend/app/services/vision_service.py`

**Lines 290-317: `describe_image` method**

```python
async def describe_image(
    self,
    image_path: str,
    question: Optional[str] = None  # ❌ NO model_id parameter
) -> str:
    """
    Get a description of the image or answer a question about it.
    """
    if question:
        prompt = f"Please answer this question about the image: {question}"
    else:
        prompt = (
            "Please provide a detailed description of this image, including: "
            "1. Main objects and subjects "
            "2. Text content (if any) "
            "3. Overall composition and layout "
            "4. Any notable details"
        )

    result = await self.process_image(image_path, prompt)  # ❌ NO model_id passed
    return result.get("text", "")
```

**Problem**:
- `describe_image()` method signature doesn't accept `model_id` parameter
- Internally calls `process_image()` (line 316) without passing `model_id`
- This means it always uses the default model instead of UI-selected model

---

## ✅ The Fix

### Fix #1: Add `model_id` parameter to `describe_image` method

**File**: `/backend/app/services/vision_service.py`
**Lines**: 290-317

**BEFORE**:
```python
async def describe_image(
    self,
    image_path: str,
    question: Optional[str] = None
) -> str:
    # ... prompt logic ...
    result = await self.process_image(image_path, prompt)
    return result.get("text", "")
```

**AFTER**:
```python
async def describe_image(
    self,
    image_path: str,
    question: Optional[str] = None,
    model_id: Optional[str] = None  # 🆕 ADD THIS
) -> str:
    # ... prompt logic ...
    result = await self.process_image(
        image_path,
        prompt,
        model_id=model_id  # 🆕 PASS TO process_image
    )
    return result.get("text", "")
```

### Fix #2: Pass `model_id` in tool_registry call

**File**: `/backend/app/agents/tool_registry.py`
**Lines**: 1495-1498

**BEFORE**:
```python
if question:
    # Specific question mode
    result = await vision_service.describe_image(image_path, question=question)
    text_content = result
```

**AFTER**:
```python
if question:
    # Specific question mode - now passing model_id
    result = await vision_service.describe_image(
        image_path,
        question=question,
        model_id=model_id  # 🆕 PASS UI-SELECTED MODEL
    )
    text_content = result
```

---

## 🧪 Testing Plan

### Test 1: Verify qwen2.5vl Model Availability

```bash
# Check if qwen2.5vl:latest is available in Ollama
docker-compose exec ollama ollama list | grep qwen
```

**Expected**: qwen2.5vl:latest should be listed

### Test 2: UI Model Selection Test

1. Open UI at http://localhost:3001
2. Select **qwen2.5vl:latest** from model dropdown
3. Upload a visual document (e.g., arch1.pdf)
4. Ask a question: "Describe what you see in this diagram"
5. Check backend logs for:
   ```
   🎯 Calling vision analysis with model_id: qwen2.5vl:latest
   🎯 Attempting vision analysis with UI-selected model: qwen2.5vl:latest
   ```

### Test 3: Verify Ollama Vision Model Used

```bash
# Monitor logs for Ollama API calls
docker logs rag-backend --follow --tail=100 2>&1 | grep -E "(qwen|model_id|vision)" --line-buffered
```

**Expected Logs**:
- Log showing `model_id: qwen2.5vl:latest`
- Ollama API call with qwen model
- Vision analysis response from qwen model

---

## 📊 Impact Analysis

### What Gets Fixed:
1. ✅ **User Control**: Users can now select their preferred vision model in the UI
2. ✅ **Model Consistency**: The selected model is used throughout the vision pipeline
3. ✅ **qwen2.5vl Support**: Properly supports qwen2.5vl and other Ollama vision models
4. ✅ **Both Code Paths**: Fixes BOTH `describe_image()` and `process_image()` paths

### What Stays the Same:
- ✅ Session document filtering (already working)
- ✅ Vision routing (already fixed)
- ✅ Fallback mechanisms (already implemented)
- ✅ API vision models (OpenAI/Claude) still work

---

## 🎯 Implementation Steps

1. **Modify VisionService**:
   - Add `model_id` parameter to `describe_image()` method
   - Pass `model_id` to internal `process_image()` call

2. **Modify Tool Registry**:
   - Update `_wrap_vision_analysis` to pass `model_id` to `describe_image()`
   - Ensure model_id is extracted from kwargs

3. **Rebuild Backend**:
   ```bash
   docker-compose build backend && docker-compose restart backend
   ```

4. **Test with User's Model**:
   - Verify qwen2.5vl:latest is available
   - Test UI model selection
   - Verify logs show correct model being used

---

## 🚀 Expected User Experience After Fix

### Scenario: User selects qwen2.5vl:latest

**Query**: "How many rooms are in the arch1 architecture diagram?"

**BEFORE (Broken)**:
```
Vision Analysis:
  Model ID from UI: qwen2.5vl:latest
  Model Actually Used: llama3.2-vision:11b (default) ❌

Logs:
  ⚠️  No log showing model_id being passed to describe_image
```

**AFTER (Fixed)**:
```
Vision Analysis:
  Model ID from UI: qwen2.5vl:latest
  Model Actually Used: qwen2.5vl:latest ✅

Logs:
  🎯 Calling vision analysis with model_id: qwen2.5vl:latest
  🎯 Attempting vision analysis with UI-selected model: qwen2.5vl:latest
  ✅ Vision analysis succeeded with qwen2.5vl:latest
```

---

## 📝 Code Changes Summary

### Modified Files:
1. `/backend/app/services/vision_service.py`
   - Lines 290-294: Add `model_id` parameter to `describe_image` signature
   - Line 316: Pass `model_id` to `process_image` call

2. `/backend/app/agents/tool_registry.py`
   - Lines 1495-1498: Pass `model_id` to `describe_image` call

### Lines of Code Changed:
- **Total Lines Modified**: 2 files, ~5 lines
- **New Parameters Added**: 1 (`model_id` to `describe_image`)
- **New Methods**: 0
- **Breaking Changes**: None (backward compatible)

---

## ⚠️  Verification Checklist

- [ ] qwen2.5vl:latest model is available in Ollama
- [ ] `describe_image()` method accepts `model_id` parameter
- [ ] `_wrap_vision_analysis` passes `model_id` to `describe_image()`
- [ ] Backend rebuilt and restarted
- [ ] Logs show UI-selected model being used
- [ ] Vision analysis works with qwen2.5vl:latest
- [ ] No memory errors (qwen2.5vl fits in available memory)

---

## 🔗 Related Documents

- **Vision Routing Fix**: `/tmp/VISION_ROUTING_FIX_COMPLETE.md`
- **Document Retrieval Analysis**: `/tmp/DOCUMENT_RETRIEVAL_ROOT_CAUSE_ANALYSIS.md`
- **Ollama Memory Issue**: Solved by using smaller models

---

**Next Step**: Implement the fix by modifying the two files as described above.
