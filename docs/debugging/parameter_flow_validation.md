# UI Parameter Flow Validation Report

## Flow Analysis: UI → Backend → RAG Service

### ✅ Step 1: UI → Backend API (main.py)
**File**: `backend/app/main.py:466-473`
```python
top_k: Optional[int] = Form(None),
similarity_threshold: Optional[float] = Form(None),
min_similarity_threshold: Optional[float] = Form(None),
no_relevant_docs_threshold: Optional[float] = Form(None),
```
**Status**: ✅ ALL parameters received from UI

### ✅ Step 2: Backend API → Enhanced RAG Agent
**File**: `backend/app/main.py:505-516`
```python
user_preferences = {
    "top_k": top_k,
    "similarity_threshold": similarity_threshold,
    "min_similarity_threshold": min_similarity_threshold,
    "no_relevant_docs_threshold": no_relevant_docs_threshold,
    ...
}
```
**Status**: ✅ ALL parameters packaged correctly

### ✅ Step 3: Enhanced RAG Agent → RAG Service (Direct Path)
**File**: `backend/app/agents/enhanced_rag_agent.py:722-725`
```python
top_k=state["user_preferences"].get("top_k"),
similarity_threshold=state["user_preferences"].get("similarity_threshold"),
min_similarity_threshold=state["user_preferences"].get("min_similarity_threshold"),
no_relevant_docs_threshold=state["user_preferences"].get("no_relevant_docs_threshold")
```
**Status**: ✅ ALL parameters passed (direct path)

### ❌ Step 3 ALT: Tool Registry → RAG Service (Tool Path)
**File**: `backend/app/agents/tool_registry.py:513-537`
```python
async def _wrap_document_rag(
    self,
    query: str,
    session_id: Optional[str] = None,
    top_k: int = 5  # ⚠️ Only accepts top_k!
) -> Dict[str, Any]:
    result = await enhanced_rag_service.query(
        query_text=query,
        session_id=session_id,
        top_k=top_k,  # ✅ Passes top_k
        # ❌ MISSING: similarity_threshold
        # ❌ MISSING: min_similarity_threshold
        # ❌ MISSING: no_relevant_docs_threshold
        db=db
    )
```
**Status**: ❌ **INCOMPLETE** - Missing 3 of 4 threshold parameters!

### ✅ Step 4: RAG Service Uses Parameters
**File**: `backend/app/services/rag_service_enhanced.py:123-126`
```python
_top_k = top_k if top_k is not None else settings.TOP_K_RESULTS
_similarity_threshold = similarity_threshold if similarity_threshold is not None else settings.SIMILARITY_THRESHOLD
_min_similarity_threshold = min_similarity_threshold if min_similarity_threshold is not None else settings.MIN_SIMILARITY_THRESHOLD
_no_relevant_docs_threshold = no_relevant_docs_threshold if no_relevant_docs_threshold is not None else settings.NO_RELEVANT_DOCS_THRESHOLD
```
**Status**: ✅ Correctly uses UI params OR config defaults

## ROOT CAUSE

**When GPT-4 fails to select a tool** (logs show: "LLM did not select any tool, defaulting to document_rag"), the system calls `tool_registry._wrap_document_rag()` which:
1. ✅ Accepts `top_k` from enhanced_rag_agent
2. ❌ Does NOT accept threshold parameters
3. ❌ Threshold parameters are lost
4. ⚠️ RAG service falls back to hardcoded config defaults

## Impact

- UI slider changes for thresholds: **NOT WORKING** (when using tool path)
- UI slider changes for top_k: **WORKING** ✅
- Config defaults: **ALWAYS USED** (ignoring UI)

## Fix Required

Update `tool_registry.py:_wrap_document_rag()` signature and call:

```python
async def _wrap_document_rag(
    self,
    query: str,
    session_id: Optional[str] = None,
    top_k: Optional[int] = None,  # Changed to Optional
    similarity_threshold: Optional[float] = None,  # Added
    min_similarity_threshold: Optional[float] = None,  # Added
    no_relevant_docs_threshold: Optional[float] = None  # Added
) -> Dict[str, Any]:
    result = await enhanced_rag_service.query(
        query_text=query,
        session_id=session_id,
        top_k=top_k,
        similarity_threshold=similarity_threshold,  # Pass through
        min_similarity_threshold=min_similarity_threshold,  # Pass through
        no_relevant_docs_threshold=no_relevant_docs_threshold,  # Pass through
        db=db
    )
```
