# GPT-4o-mini Vision Integration - Implementation Plan

**Date**: 2025-12-06
**Status**: ✅ **Step 1 Complete** - GPT-4o-mini added to model registry
**Remaining**: Steps 2-5

---

## Overview

Implement vision analysis with:
1. **Primary**: UI-selected model (e.g., gpt-4o-mini for OpenAI vision)
2. **Fallback**: Ollama LLaMA vision models if primary fails or unavailable

---

## ✅ Step 1: Add GPT-4o-mini to Model Registry - COMPLETE

**File**: `backend/app/models/model_registry.py`

**Added**:
```python
self.register(ModelInfo(
    id="gpt-4o-mini",
    name="GPT-4o Mini",
    provider=ModelProvider.OPENAI,
    model_type=ModelType.PROPRIETARY,
    model_path="gpt-4o-mini",
    context_length=128000,
    cost_per_1k_tokens=0.00015,
    requires_gpu=False,
    min_gpu_memory_gb=0,
    description="Fast, affordable, and multimodal (vision + text). Best for vision tasks and cost-effective queries.",
    recommended=True
))
```

**Benefits**:
- ✅ GPT-4o-mini now appears in model dropdown
- ✅ Marked as recommended for vision tasks
- ✅ Shows multimodal capability in description

---

## 🔄 Step 2: Enhance VisionService to Support Multiple Providers

**Current State**: `vision_service.py` only supports Ollama

**Required Changes**: Add OpenAI and Anthropic vision support

### File: `backend/app/services/vision_service.py`

**New Functionality Needed**:

```python
class VisionService:
    def __init__(self, ollama_base_url: str = "http://ollama:11434"):
        self.ollama_base_url = ollama_base_url
        self.default_ollama_model = "llama3.2-vision:11b"
        self.timeout = 120.0

    async def process_image(
        self,
        image_path: str,
        prompt: Optional[str] = None,
        model_id: Optional[str] = None,  # ← NEW: UI-selected model
        allow_fallback: bool = True      # ← Enable fallback by default
    ) -> Dict[str, Any]:
        """
        Process image with UI-selected model, fallback to Ollama if needed.

        Priority:
        1. Try UI-selected model (OpenAI/Anthropic/Ollama)
        2. If fails → fallback to Ollama vision models
        """

        # Determine provider from model_id
        if model_id and ("gpt" in model_id or "claude" in model_id):
            # Try OpenAI/Anthropic vision first
            result = await self._call_api_vision(model_id, image_path, prompt)
            if result["success"]:
                return result
            elif not allow_fallback:
                return result

            logger.warning(f"API vision failed, falling back to Ollama...")

        # Fallback to Ollama (current implementation)
        return await self._call_ollama_vision(...)

    async def _call_api_vision(
        self,
        model_id: str,
        image_path: str,
        prompt: str
    ) -> Dict[str, Any]:
        """Call OpenAI/Anthropic vision APIs"""

        # Encode image to base64
        image_data = self._encode_image(image_path)

        if "gpt" in model_id:
            # OpenAI Vision API
            from app.services.llm_service import llm_service

            response = await llm_service.call_openai_vision(
                model=model_id,
                prompt=prompt,
                image_base64=image_data
            )

            return {
                "text": response.get("content", ""),
                "model": model_id,
                "method": "openai_vision",
                "success": True,
                "metadata": {
                    "prompt_tokens": response.get("usage", {}).get("prompt_tokens", 0),
                    "completion_tokens": response.get("usage", {}).get("completion_tokens", 0)
                }
            }

        elif "claude" in model_id:
            # Anthropic Vision API
            # Similar implementation for Claude vision
            pass
```

---

## 🔄 Step 3: Add OpenAI Vision Support to LLMService

**File**: `backend/app/services/llm_service.py`

**Add Method**:

```python
async def call_openai_vision(
    self,
    model: str,
    prompt: str,
    image_base64: str,
    max_tokens: int = 1000
) -> Dict[str, Any]:
    """
    Call OpenAI vision models (gpt-4o, gpt-4o-mini, gpt-4-vision-preview)
    """
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        max_tokens=max_tokens
    )

    return {
        "content": response.choices[0].message.content,
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        },
        "model": response.model
    }
```

---

## 🔄 Step 4: Update Tool Registry to Pass UI Model

**File**: `backend/app/agents/tool_registry.py`

**Current**: `_wrap_vision_analysis()` doesn't pass model parameter

**Change**: Pass `model_id` from query to vision service

**Find and update**:
```python
async def _wrap_vision_analysis(
    self,
    query: str,
    image_path: Optional[str] = None,
    session_id: Optional[str] = None,
    model_id: Optional[str] = None,  # ← Pass from query
    db: Any = None
):
    # ...existing PDF conversion code...

    vision_service = get_vision_service()
    result = await vision_service.process_image(
        image_path=image_path,
        prompt=vision_prompt,
        model_id=model_id,  # ← NEW: Pass UI-selected model
        allow_fallback=True  # ← Enable fallback to Ollama
    )
```

---

## 🔄 Step 5: Ensure Model ID Flows Through Query Pipeline

**Files to Check**:
1. `backend/app/main.py` - Query endpoint receives `model_id`
2. `backend/app/services/task_router.py` - Passes `model_id` to tools
3. `backend/app/agents/tool_registry.py` - Uses `model_id` in vision_analysis

**Verify Flow**:
```
UI (gpt-4o-mini selected)
    ↓
POST /api/v1/query (model_id="gpt-4o-mini")
    ↓
TaskRouter.route_and_execute(model_id="gpt-4o-mini")
    ↓
ToolRegistry.vision_analysis(model_id="gpt-4o-mini")
    ↓
VisionService.process_image(model_id="gpt-4o-mini")
    ↓
Try OpenAI Vision → Success ✅
OR
Try OpenAI Vision → Fail → Fallback to Ollama ✅
```

---

## Complete Flow After Implementation

### Test Query:
```
Query: "Can you give a detail analysis of this Architecture Diagram?"
Model: gpt-4o-mini (selected in UI)
Document: S1 and S1 EMG Industralight_VTND.pdf
```

### Expected Flow:

```
User Query (gpt-4o-mini selected in UI)
    ↓
📝 Query Classification: document_specific (visual)
    ↓
🎯 Primary Tool: vision_analysis
    ↓
📥 MinIO Download: Technology/.../S1 and S1 EMG Industralight_VTND.pdf
    ↓
🔄 PDF → PNG Conversion (pdf2image)
    ↓
🚀 Vision Analysis with gpt-4o-mini:
   ┌─────────────────────────────────────┐
   │ Try GPT-4o-mini (OpenAI Vision)     │
   │ ├─ Encode image to base64           │
   │ ├─ Call OpenAI Vision API            │
   │ ├─ Prompt: "Analyze architecture..." │
   │ └─ Response: Detailed analysis ✅     │
   └─────────────────────────────────────┘
         │
         ├─ Success? → Return analysis ✅
         │
         └─ Failed/Out of memory/API limit?
             ↓
   ┌─────────────────────────────────────┐
   │ Fallback to Ollama Vision           │
   │ ├─ Try llama3.2-vision:11b          │
   │ │   ├─ Success → Return ✅            │
   │ │   └─ Memory error → Next fallback  │
   │ ├─ Try llama3.2-vision:3b           │
   │ └─ Try qwen2.5:1.5b                 │
   └─────────────────────────────────────┘
    ↓
✅ Return analysis to user
```

---

## Benefits

### 1. UI Model Selection Works ✅
- User selects gpt-4o-mini → Uses OpenAI vision
- User selects claude-3.5-sonnet → Uses Anthropic vision
- User selects llama3.2-vision → Uses Ollama directly

### 2. Automatic Fallback ✅
- OpenAI rate limit → Ollama fallback
- Ollama memory error → Smaller Ollama model
- No API key → Ollama only

### 3. Cost Optimization ✅
- gpt-4o-mini: $0.00015/1K tokens (very cheap)
- Ollama: Free (but slower/less capable)
- User controls cost vs quality

### 4. No Breaking Changes ✅
- Existing Ollama vision still works
- Backward compatible with current code
- Gradual enhancement

---

## Testing Plan

### Test 1: GPT-4o-mini Vision Analysis
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=Can you give a detail analysis of this Architecture Diagram?" \
  -F "session_id=test_gpt4o_vision" \
  -F "model=gpt-4o-mini"
```

**Expected**:
- ✅ Uses OpenAI Vision API
- ✅ Returns detailed analysis
- ✅ Logs show "openai_vision" method

### Test 2: Fallback to Ollama
```bash
# Test with invalid OpenAI key or rate limit
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=Analyze this diagram" \
  -F "session_id=test_fallback" \
  -F "model=gpt-4o-mini"
```

**Expected**:
- ⚠️ OpenAI fails (rate limit/invalid key)
- ✅ Falls back to Ollama vision
- ✅ Returns analysis from Ollama

### Test 3: Direct Ollama Selection
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=Analyze this diagram" \
  -F "session_id=test_ollama_direct" \
  -F "model=llama3.2-vision:11b"
```

**Expected**:
- ✅ Uses Ollama directly (no OpenAI attempt)
- ✅ Returns analysis

---

## Implementation Status

| Step | Task | Status | File |
|------|------|--------|------|
| 1 | Add gpt-4o-mini to registry | ✅ Done | `model_registry.py` |
| 2 | Enhance VisionService | ⏳ Pending | `vision_service.py` |
| 3 | Add OpenAI vision to LLMService | ⏳ Pending | `llm_service.py` |
| 4 | Update tool_registry to pass model | ⏳ Pending | `tool_registry.py` |
| 5 | Verify model flow through pipeline | ⏳ Pending | Multiple files |

---

## Next Steps (For User or Next Session)

### Option 1: Complete Implementation Now
Continue with Steps 2-5 to fully implement the feature

### Option 2: Quick Fix (Use What Works Now)
Since gpt-4o-mini is now in the dropdown, you can:
1. Rebuild backend: `docker-compose build backend && docker-compose restart backend`
2. Select gpt-4o-mini from dropdown
3. It will work for text queries immediately
4. Vision will still use Ollama until Steps 2-5 are done

### Option 3: Session Summary
Document current progress and continue in next session

---

**Recommendation**: Option 1 (complete now) if time permits, or Option 3 (document and continue later) for comprehensive testing.
