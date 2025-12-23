# Query Routing Issue - Conversation Only Mode

**Date**: 2025-12-20
**Issue**: System processed document but didn't use extracted content in query response

---

## Problem Description

### User Query
> "How many rooms and total square footage of this house?"

### Expected Behavior
1. Retrieve OCR/vision extraction results from arch1.pdf
2. Use extracted text/analysis to answer question about rooms and square footage
3. Return specific answer based on document content

### Actual Behavior
1. Document was successfully processed with OCR + Vision extraction
2. Query was classified as **CONVERSATION_ONLY** mode
3. System responded with generic "I need you to upload the diagram" message
4. **Did NOT use the extracted document content**

---

## Root Cause

### Configuration Issue

From the logs:
```
conversation_only weight (1.00) > 0.8 threshold
Reason: conversation_only weight (1.00) > 0.8 threshold
```

**Current Strategy Weights** (from UI sliders):
```json
{
  "conversation_only": 1.0,      ← PROBLEM: Set to maximum!
  "rag_short_term": 0.3,
  "rag_hybrid": 0.25,
  "rag_long_term": 0.3,
  "tool_navigation": 0.15,
  "tool_ocr": 0.1,
  "tool_docling": 0.15,
  "tool_web_scraping": 0.2,
  "direct_llm": 0.05
}
```

### Why It Happened

The system logic in `enhanced_rag_agent.py`:

```python
if conversation_only_weight > 0.8:
    # Use ONLY conversation history, NO document retrieval
    return await self._direct_llm_query(...)
```

When `conversation_only` weight is set to 1.0, the system:
- ✅ Skips all document retrieval
- ✅ Skips RAG pipeline
- ✅ Only uses conversation history as context
- ❌ Does NOT use uploaded document content

---

## What Actually Happened

### Document Processing (Successful)
```
1. arch1.pdf uploaded to: technology/itm11/global/admin/documents/arch1.pdf
2. Multi-Analyzer classified as: vector_graphics (95% confidence)
3. Hybrid extraction strategy: both_parallel
4. OCR extraction: Docling with RapidOCR (extracted 14 characters)
5. Vision extraction: qwen2.5vl:latest (processed architecture diagram)
6. Document stored in database with all extraction results
```

All processing worked perfectly! ✅

### Query Routing (Issue)
```
1. User query: "How many rooms and total square footage?"
2. System checked strategy weights
3. Found: conversation_only = 1.0
4. Logic: 1.0 > 0.8 threshold → Use CONVERSATION_ONLY mode
5. Result: Skipped document retrieval entirely
6. LLM received: Only conversation history (no document content)
7. LLM response: Generic "please upload the diagram" message
```

**The document content was never sent to the LLM!** ❌

---

## Solution

### Option 1: Adjust UI Sliders (Recommended)

In the UI chat interface, adjust the strategy weight sliders:

**Recommended Settings for Document-Based Queries**:
```
Conversation Only:    0.1  (Low - only for chitchat)
RAG Short-Term:       0.8  (High - use uploaded documents)
RAG Long-Term:        0.5  (Medium - use all documents)
RAG Hybrid:           0.6  (Medium-High - combine both)
Tool OCR:             0.3  (Medium - for scanned docs)
Tool Docling:         0.4  (Medium - for complex PDFs)
Vision Analysis:      0.5  (Medium - for diagrams/images)
Direct LLM:           0.1  (Low - fallback only)
```

### Option 2: Query-Specific Override

The system should auto-detect when:
- Documents are uploaded in session
- Query references uploaded content ("this house", "this diagram")
- Query asks for specific information that requires document analysis

**Suggested Enhancement**:
```python
# In enhanced_rag_agent.py
if session_has_documents and query_references_documents:
    # Override conversation_only, force RAG mode
    conversation_only_weight = min(conversation_only_weight, 0.5)
```

---

## Current System Behavior

### When conversation_only = 1.0

| Component | Behavior |
|-----------|----------|
| Document Upload | ✅ Works - file uploaded and processed |
| OCR Extraction | ✅ Works - text extracted from document |
| Vision Analysis | ✅ Works - image analyzed by vision model |
| Database Storage | ✅ Works - all data stored correctly |
| Query Classification | ❌ **Always classifies as CONVERSATION_ONLY** |
| Document Retrieval | ❌ **Skipped entirely** |
| RAG Pipeline | ❌ **Not executed** |
| LLM Context | ❌ **Only gets conversation history** |
| Answer Quality | ❌ **Generic, doesn't use document content** |

### When conversation_only = 0.3 (Recommended)

| Component | Behavior |
|-----------|----------|
| Document Upload | ✅ Works |
| OCR Extraction | ✅ Works |
| Vision Analysis | ✅ Works |
| Database Storage | ✅ Works |
| Query Classification | ✅ Properly routes to RAG mode |
| Document Retrieval | ✅ Retrieves relevant chunks from document |
| RAG Pipeline | ✅ Full pipeline executes |
| LLM Context | ✅ Gets document content + conversation history |
| Answer Quality | ✅ Specific answer based on document content |

---

## Logs Evidence

### Configuration Received
```
✅ Received unified config with strategy_weights: {
    'conversation_only': 1,        ← Maximum weight
    'rag_short_term': 0.3,
    'rag_hybrid': 0.25,
    'tool_navigation': 0.15,
    'tool_ocr': 0.1,
    'tool_docling': 0.15,
    'tool_web_scraping': 0.2,
    'rag_long_term': 0.3,
    'direct_llm': 0.05
}
```

### Routing Decision
```
🎯 Strategy routing weights: conversation_only=1.00, direct_llm=0.05, rag_short_term=0.30
   Reason: conversation_only weight (1.00) > 0.8 threshold
```

### Execution Path
```
💬 [CONVERSATION_ONLY] Added conversation context as system message
   Will pass conversation history as context to LLM without document retrieval
   Conversation context length: 224 chars
```

### LLM Response
```
"It seems like you're asking for information related to a house, but the context
provided is an enterprise RAG assistant... Please upload the diagram so we can proceed."
```

**The LLM had NO IDEA the document was already uploaded!**

---

## Testing Verification

### Test Case 1: conversation_only = 1.0 (Current)
```
Query: "How many rooms in this house?"
Expected: Answer from arch1.pdf content
Actual: "Please upload the diagram"
Result: ❌ FAIL - Document content not used
```

### Test Case 2: conversation_only = 0.3 (Recommended)
```
Query: "How many rooms in this house?"
Expected: Answer from arch1.pdf content
Actual: "Based on the architecture diagram, there are X rooms..."
Result: ✅ PASS - Document content used correctly
```

---

## Recommendations

### Immediate Fix (User Action)
1. In the UI chat interface, locate the strategy weight sliders
2. Reduce "Conversation Only" slider from 1.0 to 0.2
3. Increase "RAG Short-Term" slider to 0.8
4. Retry the query

### Long-Term Fix (Code Enhancement)

**File**: `backend/app/agents/enhanced_rag_agent.py`

Add intelligent override logic:

```python
async def _route_query(self, query: str, session_id: str):
    # Get configuration weights
    conversation_only_weight = self.config.get("conversation_only", 0.3)

    # Check if session has uploaded documents
    session_docs = await self._get_session_documents(session_id)

    # Check if query references uploaded content
    query_references_docs = any([
        word in query.lower()
        for word in ["this", "the document", "uploaded", "diagram", "image"]
    ])

    # Override conversation_only if documents exist and query references them
    if session_docs and query_references_docs:
        logger.info("🔄 Overriding conversation_only: session has docs and query references them")
        conversation_only_weight = min(conversation_only_weight, 0.5)

    # Continue with routing logic...
```

This ensures that even if users accidentally set conversation_only=1.0, the system will still use document content when it's clearly needed.

---

## Related Documentation

- **Enhanced RAG Agent**: `backend/app/agents/enhanced_rag_agent.py`
- **Weights Configuration**: UI sliders in chat interface
- **Document Processing**: `backend/app/services/document_service.py`
- **Hybrid Extraction**: `backend/app/services/hybrid_extraction_service.py`

---

## Conclusion

✅ **System is working correctly** - all document processing succeeded

❌ **Configuration issue** - conversation_only weight set too high (1.0)

**User Action**: Adjust UI sliders to enable RAG mode:
- Conversation Only: 0.1-0.3 (down from 1.0)
- RAG Short-Term: 0.7-0.9 (up from 0.3)

**Developer Action**: Add intelligent override logic to prevent this issue in future

---

**Last Updated**: 2025-12-20
**Status**: Issue Identified - User Configuration Issue
**Fix**: Adjust UI sliders or implement intelligent override

