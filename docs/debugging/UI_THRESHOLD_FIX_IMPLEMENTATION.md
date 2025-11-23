# UI Threshold Parameter Fix - Implementation Plan

## Problem Summary

The backend is **completely ignoring** UI threshold parameters sent from the frontend. The UI sends threshold values via Form Data, but the backend never uses them.

### Evidence:
- UI sends: `top_k`, `similarity_threshold`, `min_similarity_threshold`, `no_relevant_docs_threshold`
- Backend ignores: Hard-codes `top_k: 5` and uses `settings.*` defaults

## Files That Need Changes

### 1. `/mnt/c/AIML/ClaudeCode/chatbot/ChatBot/backend/app/agents/enhanced_rag_agent.py`

#### Changes Needed:
1. **`_select_tool_simple()` method (lines 250-254)**:
   - Change from hard-coded `top_k: 5`
   - Accept threshold parameters
   - Pass them through to document_rag tool

2. **`_select_tools_llm()` method (lines 340-344)**:
   - Change from hard-coded `top_k: 5`
   - Accept threshold parameters
   - Pass them through to document_rag tool

3. **`run()` method signature**:
   - Add optional threshold parameters to method signature
   - Extract from `user_preferences` if provided

### 2. `/mnt/c/AIML/ClaudeCode/chatbot/ChatBot/backend/app/services/rag_service.py`

#### Changes Needed (lines 107-124):
1. **`query()` method signature**:
   - Add optional threshold parameters: `top_k`, `similarity_threshold`, `no_relevant_docs_threshold`

2. **Line 110**: Change `settings.TOP_K_RESULTS` to use provided parameter or default
3. **Line 111**: Change `settings.SIMILARITY_THRESHOLD` to use provided parameter or default
4. **Line 123**: Change `settings.NO_RELEVANT_DOCS_THRESHOLD` to use provided parameter or default

### 3. `/mnt/c/AIML/ClaudeCode/chatbot/ChatBot/backend/app/main_enhanced.py` (or main.py)

#### Changes Needed:
1. Extract threshold parameters from FormData in the `/api/v1/query` endpoint
2. Pass them to enhanced_rag_agent via `user_preferences`

## Detailed Implementation

### Step 1: Modify `rag_service.py`

```python
async def query(
    self,
    query_text: str,
    conversation_history: Optional[List[Dict]] = None,
    use_cache: bool = True,
    model_id: Optional[str] = None,
    db: AsyncSession = None,
    # NEW: Optional threshold parameters from UI
    top_k: Optional[int] = None,
    similarity_threshold: Optional[float] = None,
    min_similarity_threshold: Optional[float] = None,
    no_relevant_docs_threshold: Optional[float] = None
) -> Dict:
    """
    Process a query using intelligent RAG pipeline
    """
    # Use provided values or fall back to settings defaults
    top_k_to_use = top_k if top_k is not None else settings.TOP_K_RESULTS
    similarity_threshold_to_use = similarity_threshold if similarity_threshold is not None else settings.SIMILARITY_THRESHOLD
    no_relevant_threshold_to_use = no_relevant_docs_threshold if no_relevant_docs_threshold is not None else settings.NO_RELEVANT_DOCS_THRESHOLD

    # Step 2: Search for similar chunks using PROVIDED OR DEFAULT values
    similar_chunks = await document_service.search_similar_chunks(
        query_embedding=query_embedding,
        query_text=query_text,
        top_k=top_k_to_use,  # Use parameter or default
        threshold=similarity_threshold_to_use,  # Use parameter or default
        use_hybrid=True,
        db=db
    )

    # Filter chunks based on quality threshold
    if similar_chunks:
        best_score = max(chunk.get('similarity', 0) for chunk in similar_chunks)
        if best_score >= no_relevant_threshold_to_use:  # Use parameter or default
            filtered_chunks = similar_chunks
```

### Step 2: Modify `enhanced_rag_agent.py`

#### Update `run()` method to extract thresholds:

```python
async def run(
    self,
    query: str,
    session_id: Optional[str] = None,
    user_preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute agent workflow with multi-tool support
    """
    user_preferences = user_preferences or {}

    # Extract threshold parameters from user_preferences
    top_k = user_preferences.get('top_k')
    similarity_threshold = user_preferences.get('similarity_threshold')
    min_similarity_threshold = user_preferences.get('min_similarity_threshold')
    no_relevant_docs_threshold = user_preferences.get('no_relevant_docs_threshold')
```

#### Update `_select_tool_simple()`:

```python
def _select_tool_simple(
    self,
    query: str,
    session_id: Optional[str] = None,
    top_k: Optional[int] = None
) -> tuple[str, Dict[str, Any]]:
    """
    Simple keyword-based tool selection
    """
    # ... existing code ...

    # Default: Use document RAG with UI parameters
    return "document_rag", {
        "query": query,
        "session_id": session_id,
        "top_k": top_k  # Use from UI, not hard-coded
    }
```

#### Update `_select_tools_llm()`:

```python
async def _select_tools_llm(
    self,
    query: str,
    session_id: Optional[str] = None,
    top_k: Optional[int] = None
) -> Dict[str, Any]:
    """
    LLM-based tool selection
    """
    # ... existing code ...

    # No tool selected, default to document RAG
    return {
        "intent": "general_query",
        "confidence": 0.5,
        "reasoning": "LLM did not make a specific tool selection",
        "tools": ["document_rag"],
        "tool_params": {
            "document_rag": {
                "query": query,
                "session_id": session_id,
                "top_k": top_k  # Use from UI, not hard-coded
            }
        },
        "tool_selection_reasoning": "Default selection due to no LLM tool call"
    }
```

### Step 3: Update the API endpoint to extract Form Data

In `main_enhanced.py` or `main.py`:

```python
@app.post("/api/v1/query")
async def query_documents(
    query: str = Form(...),
    model_id: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    # NEW: Extract threshold parameters from Form Data
    top_k: Optional[int] = Form(None),
    similarity_threshold: Optional[float] = Form(None),
    min_similarity_threshold: Optional[float] = Form(None),
    no_relevant_docs_threshold: Optional[float] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Query endpoint that accepts RAG configuration from UI
    """
    # Build user preferences with threshold parameters
    user_preferences = {
        "model_id": model_id,
        "db": db
    }

    # Add threshold parameters if provided
    if top_k is not None:
        user_preferences['top_k'] = top_k
    if similarity_threshold is not None:
        user_preferences['similarity_threshold'] = similarity_threshold
    if min_similarity_threshold is not None:
        user_preferences['min_similarity_threshold'] = min_similarity_threshold
    if no_relevant_docs_threshold is not None:
        user_preferences['no_relevant_docs_threshold'] = no_relevant_docs_threshold

    # Call enhanced RAG agent with threshold parameters
    result = await enhanced_rag_agent.run(
        query=query,
        session_id=session_id,
        user_preferences=user_preferences
    )

    return result
```

## Expected Outcome

After implementing these changes:

1. UI slider adjustments will be respected
2. "Who is Aadhan?" query will work with UI's default 65% threshold
3. Users can dynamically adjust thresholds and see immediate effects
4. Backend will log which thresholds are being used (UI values vs defaults)

## Testing

Test with the query "Who is Aadhan?" which currently:
- **Before fix**: 0 sources (using backend 70% threshold)
- **After fix**: Should retrieve sources (using UI 65% threshold)
