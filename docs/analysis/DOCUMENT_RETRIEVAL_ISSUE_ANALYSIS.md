# Document Retrieval Issue in vision_analysis Tool - Analysis

**Date**: 2025-12-08
**Status**: 🔍 **INVESTIGATING**
**Issue**: vision_analysis tool retrieves wrong documents despite correct routing

---

## 🎯 Problem Summary

### What's WORKING ✅:
1. **Vision routing fix**: Query correctly routed to vision_analysis tool
2. **LLM classification**: Documents classified as vector_graphics (95% confidence)
3. **FORCE_RAG bypass**: Visual queries bypass FORCE_RAG correctly
4. **TaskRouter integration**: vision_analysis tool is selected properly

###What's NOT WORKING ❌:
- **Document retrieval within vision_analysis tool**: Retrieves wrong documents
- **Expected**: arch1.pdf from session
- **Actual**: Documents about airports, Python (wrong context)

---

## 📊 Evidence

### From Logs:
```
✅ 🎨 Visual query detected by LLM: The user's query mentions an 'arch1 architecture diagram'...
✅ Bypassing FORCE_RAG to use vision_analysis via TaskRouter
✅ Using TaskRouter decision: vision_analysis
✅ Executing tool: vision_analysis
```

### From User's Response:
```
"I don't have the relevant information to answer the question. The provided context
documents do not contain any information about an 'arch1 architecture diagram' or a
house with rooms and square footage. The documents appear to be about airports,
Python programming language, and its history..."
```

### From Database Query:
```sql
SELECT d.filename, sd.session_id, sd.added_at
FROM session_documents sd
JOIN documents d ON sd.document_id = d.id
WHERE sd.session_id LIKE 'session-1765178685304%'

Result:
filename  |           session_id            |           added_at
-----------+---------------------------------+-------------------------------
 arch1.pdf | session-1765178685304-tfhx2zh89 | 2025-12-08 07:26:03.701844+00
```

**Conclusion**: arch1.pdf IS in the session, but vision_analysis tool doesn't find it

---

## 🔍 Root Cause Hypothesis

The vision_analysis tool likely does ONE of these:

### Hypothesis 1: No session_id parameter
vision_analysis tool definition may not accept session_id parameter, so it searches ALL documents instead of session documents

### Hypothesis 2: session_id not passed to retrieval
vision_analysis tool accepts session_id but doesn't pass it to the document retrieval logic

### Hypothesis 3: Different retrieval logic
vision_analysis uses different retrieval method than document_rag that doesn't filter by session

---

## 🛠️ Investigation Steps Needed

### Step 1: Check vision_analysis tool signature
```python
# Find in tool_registry.py around line 285
function=self._wrap_vision_analysis,
input_schema={
    "type": "object",
    "properties": {
        "image_path": {...},
        "question": {...},
        # ❓ Is there a session_id parameter?
    }
}
```

### Step 2: Check _wrap_vision_analysis implementation
```python
# Find in tool_registry.py
async def _wrap_vision_analysis(
    self,
    image_path: str,
    question: Optional[str] = None,
    # ❓ Does it accept session_id?
    # ❓ Does it pass session_id to vision_service?
):
```

### Step 3: Check how vision_service retrieves documents
```python
# /backend/app/services/vision_service.py
# Check if it uses session_id for document filtering
```

### Step 4: Compare with document_rag tool
```python
# document_rag in tool_registry.py correctly uses session_id
# We should mimic this pattern
```

---

## 💡 Expected Fix

### Option A: Add session_id parameter to vision_analysis

**File**: `/backend/app/agents/tool_registry.py`

1. Add session_id to input_schema (around line 285-300)
2. Add session_id parameter to _wrap_vision_analysis method
3. Pass session_id to vision_service or document retrieval

### Option B: Modify vision_service to prioritize session documents

**File**: `/backend/app/services/vision_service.py`

1. Accept optional session_id parameter
2. If session_id provided, filter documents to session only
3. Use session_documents JOIN like document_rag does

---

## 📝 Comparison: document_rag vs vision_analysis

### document_rag (WORKING correctly):
```python
# Has session_id in input_schema
"session_id": {
    "type": "string",
    "description": "Session ID for document scope (optional)"
}

# Uses session filtering in RAG service
await rag_service.query(
    query_text=query,
    session_id=session_id,  # ✅ Passed to RAG service
    # ...
)
```

### vision_analysis (NEEDS FIX):
```python
# ❓ Check if it has session_id parameter
# ❓ Check if it passes session_id to vision_service
# ❓ Check if vision_service filters by session
```

---

## 🎯 Next Step

**Immediate Action**: Examine vision_analysis tool implementation

**Files to investigate**:
1. `/backend/app/agents/tool_registry.py` - vision_analysis registration and wrapper
2. `/backend/app/services/vision_service.py` - document retrieval logic
3. Compare with document_rag tool implementation (working reference)

**Goal**: Add session document filtering to vision_analysis tool

---

## 🔗 Related Documents

- Vision Routing Fix: `/tmp/VISION_ROUTING_FIX_COMPLETE.md`
- Vision Routing Analysis: `/tmp/VISION_ROUTING_FIX_MINIMAL_OPTIMIZATION.md`
- Regression Analysis: `/tmp/vision_routing_regression_analysis.md`
- Query Analysis: `/tmp/query_analysis.md`

---

**Status**: Ready for detailed code investigation to implement session filtering in vision_analysis tool
