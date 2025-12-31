# 🎯 ROOT CAUSE ANALYSIS - LLM Extraction Failing

**Date**: 2025-11-19
**Issue**: Ultra-Smart extraction returns "---" instead of actual data

---

## ✅ CONFIRMED ROOT CAUSES

### 1. ❌ Using BASIC LLM Service Instead of ENHANCED

**File**: `backend/app/api/routes/template_extraction_routes.py:108`

```python
from app.services.llm_service import llm_service  # ← BASIC SERVICE
```

**Working Chat Uses**:
```python
# Uses enhanced service with model registry and dynamic model selection
# Logs show: {"query": "you there?", "model_id": "gpt-4-turbo"}
```

**Impact**: Basic service doesn't support model_id parameter, uses fallback chain without proper model selection.

---

### 2. ❌ Request Schema Missing model_id Field

**File**: `backend/app/api/routes/template_extraction_routes.py:1556`

```python
class UltraSmartExtractRequest(BaseModel):
    llm_provider: str = Field(default="openai", description="LLM provider: openai, anthropic, ollama")
    # ← NO model_id field!
```

**Working Chat Has**:
```python
class RagQueryRequest(BaseModel):
    model_name: Optional[str] = Field(default="gpt-4-turbo", ...)  # ← model_name field
```

**Impact**: Even if we wanted to pass a specific model, the API doesn't accept it.

---

### 3. ❌ NOT Passing model_id to LLM generate() Call

**File**: `backend/app/services/webscraper/extractors/llm_extractor.py:577`

```python
llm_result = await self.llm_service.generate(
    prompt=extraction_prompt,
    messages=messages,
    max_tokens=3000,
    temperature=0.0
    # ← NO model_id parameter!
)
```

**Enhanced Service Accepts**:
```python
async def generate(
    self,
    prompt: str,
    messages: Optional[List[Dict]] = None,
    max_tokens: int = 512,
    temperature: float = 0.7,
    model_id: Optional[str] = None  # ← Should be passed here!
) -> Dict:
```

**Impact**: Even with enhanced service, we're not telling it which model to use.

---

### 4. ❌ Hardcoded llm_provider Instead of Using Request

**File**: `backend/app/api/routes/template_extraction_routes.py:135`

```python
mapping_result = await extractor.map_to_custom_template(
    scraped_data=scraped_data,
    template_columns=template_columns,
    template_examples=None,
    llm_provider="openai"  # ← HARDCODED! Ignores request.llm_provider
)
```

**Should Be**:
```python
llm_provider=request.llm_provider  # ← Use from request
```

**Impact**: User's llm_provider selection is ignored.

---

## 📊 COMPARISON: Working Chat vs Broken Extraction

| Aspect | Chat (Working) | Extraction (Broken) |
|--------|----------------|---------------------|
| **LLM Service** | `llm_service_enhanced` | `llm_service` (basic) |
| **Request Schema** | Has `model_name` field | Only has `llm_provider` |
| **Model Selection** | Dynamic via `model_name` | Hardcoded, no model_id |
| **generate() Call** | Passes `model_id` | No `model_id` parameter |
| **Logs Show** | `"model_id": "gpt-4-turbo"` | No model_id in logs |

---

## 🔍 EVIDENCE FROM LOGS

### Chat Request (Working):
```json
{
  "query": "you there?",
  "model_id": "gpt-4-turbo"  ← Dynamic model selection
}
```

### Chat Response Metadata:
```
model_id: gpt-4-turbo
model_name: GPT-4 Turbo
```

### Extraction Request:
```json
{
  "url": "https://books.toscrape.com/...",
  "llm_provider": "openai"  ← Only provider, no specific model
}
```

### Extraction Flow:
1. Uses basic llm_service
2. No model_id accepted
3. No model_id passed to generate()
4. OpenAI fallback uses wrong or misconfigured model

---

## 🛠️ REQUIRED FIXES

### Fix 1: Switch to Enhanced LLM Service

**File**: `backend/app/api/routes/template_extraction_routes.py`

**Change Line 108**:
```python
# OLD
from app.services.llm_service import llm_service

# NEW
from app.services.llm_service_enhanced import EnhancedLLMService
```

**Change Line 128-129**:
```python
# OLD
await llm_service.initialize()
extractor = LLMExtractor(llm_service=llm_service)

# NEW
llm_service = EnhancedLLMService()
await llm_service.initialize()
extractor = LLMExtractor(llm_service=llm_service)
```

---

### Fix 2: Add model_id to Request Schema

**File**: `backend/app/api/routes/template_extraction_routes.py`

**Add to UltraSmartExtractRequest (after line 1556)**:
```python
class UltraSmartExtractRequest(BaseModel):
    url: Optional[str] = ...
    user_instructions: Optional[str] = ...
    source_type: str = ...
    llm_provider: str = Field(default="openai", description="LLM provider: openai, anthropic, ollama")
    model_id: Optional[str] = Field(default="gpt-4-turbo", description="Specific model ID (e.g., gpt-4-turbo, gpt-4o, claude-3-opus)")  # ← ADD THIS
    vision_provider: str = ...
    session_id: Optional[str] = None
```

---

### Fix 3: Pass model_id to LLM Extractor

**File**: `backend/app/services/webscraper/extractors/llm_extractor.py`

**Add model_id Parameter to map_to_custom_template() (around line 455)**:
```python
async def map_to_custom_template(
    self,
    scraped_data: str,
    template_columns: List[str],
    template_examples: Optional[Dict[str, str]] = None,
    llm_provider: str = "openai",
    model_id: Optional[str] = None  # ← ADD THIS
) -> Optional[Dict[str, Any]]:
```

**Pass model_id to generate() (line 577)**:
```python
llm_result = await self.llm_service.generate(
    prompt=extraction_prompt,
    messages=messages,
    max_tokens=3000,
    temperature=0.0,
    model_id=model_id  # ← ADD THIS
)
```

---

### Fix 4: Use Request Parameters in Route

**File**: `backend/app/api/routes/template_extraction_routes.py`

**Change Line 131-135**:
```python
# OLD
mapping_result = await extractor.map_to_custom_template(
    scraped_data=scraped_data,
    template_columns=template_columns,
    template_examples=None,
    llm_provider="openai"  # ← HARDCODED
)

# NEW
mapping_result = await extractor.map_to_custom_template(
    scraped_data=scraped_data,
    template_columns=template_columns,
    template_examples=None,
    llm_provider=request.llm_provider,  # ← From request
    model_id=request.model_id  # ← From request
)
```

---

## 🎯 SUMMARY

**The extraction is failing because**:
1. It uses a basic LLM service without dynamic model selection
2. It doesn't accept or pass model_id
3. OpenAI is being called without a specific model or with wrong configuration
4. The working chat uses EnhancedLLMService with dynamic model_id selection

**To fix**: Switch to EnhancedLLMService, add model_id to request schema, and pass it through the entire chain like the chat does.

---

## ✅ VALIDATION FROM DEBUGGING SESSION

From `/tmp/DEBUGGING_SESSION_SUMMARY.md`:
- ✅ Data IS in scraped content
- ✅ Prompt construction IS correct
- ✅ OpenAI API IS working (RAG chat proves it)
- ❌ Model selection and service usage is the root cause

The prompt improvements were good, but the fundamental issue is using the wrong LLM service without model selection.
