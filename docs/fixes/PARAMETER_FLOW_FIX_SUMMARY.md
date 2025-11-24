# Parameter Flow Fix - Complete Solution

## Bugs Identified

### Bug #1: Enhanced RAG Agent - Default Tool Params Incomplete
**File**: `backend/app/agents/enhanced_rag_agent.py:388-393`
**Issue**: When GPT-4 doesn't select a tool, default params only include query, session_id, and top_k

### Bug #2: Tool Registry - Function Signature Incomplete  
**File**: `backend/app/agents/tool_registry.py:513-537`
**Issue**: _wrap_document_rag() doesn't accept threshold parameters

## Required Fixes

### Fix #1: Enhanced RAG Agent (Lines 387-393)

**Current Code:**
```python
default_params = {
    "query": query,
    "session_id": session_id
}
if top_k is not None:
    default_params["top_k"] = top_k
```

**Fixed Code:**
```python
default_params = {
    "query": query,
    "session_id": session_id
}
# Add all threshold parameters from user_preferences
if top_k is not None:
    default_params["top_k"] = top_k
if similarity_threshold is not None:
    default_params["similarity_threshold"] = similarity_threshold
if min_similarity_threshold is not None:
    default_params["min_similarity_threshold"] = min_similarity_threshold
if no_relevant_docs_threshold is not None:
    default_params["no_relevant_docs_threshold"] = no_relevant_docs_threshold
```

### Fix #2: Tool Registry (Lines 513-537)

**Current Signature:**
```python
async def _wrap_document_rag(
    self,
    query: str,
    session_id: Optional[str] = None,
    top_k: int = 5
) -> Dict[str, Any]:
```

**Fixed Signature:**
```python
async def _wrap_document_rag(
    self,
    query: str,
    session_id: Optional[str] = None,
    top_k: Optional[int] = None,
    similarity_threshold: Optional[float] = None,
    min_similarity_threshold: Optional[float] = None,
    no_relevant_docs_threshold: Optional[float] = None
) -> Dict[str, Any]:
```

**Current Call:**
```python
result = await enhanced_rag_service.query(
    query_text=query,
    session_id=session_id,
    top_k=top_k,
    db=db
)
```

**Fixed Call:**
```python
result = await enhanced_rag_service.query(
    query_text=query,
    session_id=session_id,
    conversation_history=[],
    use_cache=True,
    top_k=top_k,
    similarity_threshold=similarity_threshold,
    min_similarity_threshold=min_similarity_threshold,
    no_relevant_docs_threshold=no_relevant_docs_threshold,
    db=db
)
```

## Expected Outcome

After these fixes:
- ✅ UI threshold sliders will affect backend (no hardcoding)
- ✅ Defaults come from config.py when UI doesn't specify
- ✅ Both code paths work (direct and tool registry)
- ✅ No parameters lost in transit

## Validation: yes I'm ready for you to implement these fixes

Let me know if you're ready for me to implement these fixes!
