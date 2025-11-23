# Vector Search Issue - Root Cause & Fix

**Date**: 2025-11-23
**Status**: ❌ CRITICAL - Document retrieval broken

---

## 🔍 Investigation Summary

### What Works:
✅ **Metrics UI Implementation** - Settings panel and metrics fields are working
✅ **Backend returns performance metrics** - latency_ms, tokens_used, num_sources are present
✅ **Documents exist with embeddings** - Short Story3.txt has 23 chunks with 384-dim vectors

### What's Broken:
❌ **Vector search returns 0 sources** - No documents retrieved for "Who is Aadhan?" query
❌ **Sources display shows "N/A"** - Because sources_count = 0
❌ **RAG metrics appear empty** - No data to display when source count is zero

---

## 🎯 Root Cause

**Short Story3.txt is NOT associated with any active session**

The system has a **memory hierarchy** that:
1. First checks **short-term memory** (session-specific documents)
2. Should fallback to **long-term memory** (all documents) if session search fails

**Problem:** The fallback mechanism is not working OR queries without a session_id are only searching session documents.

### Evidence:
```
Test Query: "Who is Aadhan?" (no session_id provided)
Result:
  - tool_used: "document_rag"
  - sources_count: 0  ❌
  - answer: "I'm an AI model... Aadhan is actually a brand of contactless payment..." (hallucinated)
```

```sql
-- Short Story3.txt exists with proper embeddings
File name: Short Story3.txt
Uploaded: 2025-11-16 17:05:03
Processed: TRUE
Chunks: 23
Embeddings: 23/23 (100%)
Content: "Once upon a time, there lived a king named Aadhan..."
```

```sql
-- But only 6 session documents exist total (none is Short Story3.txt)
SELECT COUNT(*) FROM session_documents;
Result: 6
```

---

## 🔧 Immediate Fixes

### Fix 1: Query WITH a Session ID (Test if session filtering is the issue)

Test if providing a session ID helps:

```bash
# Create a new session and upload Short Story3.txt to it
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@/path/to/Short Story3.txt" \
  -F "session_id=test-session-001"

# Then query with that session_id
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=Who is King Aadhan?" \
  -F "model_id=gpt-4" \
  -F "session_id=test-session-001"
```

### Fix 2: Associate Short Story3.txt with an Active Session

```sql
-- Get document ID for Short Story3.txt
SELECT id FROM documents WHERE filename = 'Short Story3.txt';

-- Create a new session
INSERT INTO chat_sessions (id, session_id, title, created_at, last_activity, is_active)
VALUES (
    gen_random_uuid(),
    'global-session-001',
    'Global Documents Session',
    NOW(),
    NOW(),
    TRUE
);

-- Associate Short Story3.txt with the session
INSERT INTO session_documents (id, session_id, document_id, added_at)
SELECT
    gen_random_uuid(),
    'global-session-001',
    id,
    NOW()
FROM documents
WHERE filename = 'Short Story3.txt';
```

### Fix 3: Modify RAG Service to Always Include Global Documents

**Location:** `backend/app/services/rag_service.py` OR `backend/app/agents/rag_agent.py`

**Problem Area:** The vector search query likely has this pattern:

```python
# Current (BROKEN) - Only searches session documents
if session_id:
    # Search only session-specific documents
    chunks = search_session_documents(session_id, query_embedding)
else:
    # Search returns nothing or defaults to empty
    chunks = []
```

**Should be:**

```python
# Fixed - Searches session FIRST, then falls back to all documents
chunks = []

if session_id:
    # 1. Try session-specific documents FIRST
    chunks = search_session_documents(session_id, query_embedding, top_k=5)

if len(chunks) < 3:  # If too few results
    # 2. Fallback to ALL documents (long-term memory)
    all_chunks = search_all_documents(query_embedding, top_k=5)
    chunks.extend(all_chunks)
    chunks = sorted(chunks, key=lambda x: x['similarity'], reverse=True)[:5]
```

---

## 📊 Test Results

### Current State (BEFORE FIX):
```
Query: "Who is Aadhan?"
Session ID: None
Tool: document_rag
Sources: 0  ❌
Latency: 27342ms
Answer: Hallucinated (talks about "Aadhan contactless payment card")
```

### Expected State (AFTER FIX):
```
Query: "Who is Aadhan?"
Session ID: None OR "global-session-001"
Tool: document_rag
Sources: 2-5  ✅
Latency: <5000ms
Answer: "King Aadhan ruled a county named Kandigai in southern part of Tamil nadu..."
Source: Short Story3.txt
```

---

## 🔍 Next Steps

1. **Immediate** - Associate Short Story3.txt with a global session (Fix 2)
2. **Short-term** - Modify RAG service fallback logic (Fix 3)
3. **Test** - Verify Aadhan queries return correct sources
4. **Validate** - Confirm metrics display with actual data

---

## 📝 Notes

- The metrics UI implementation from the previous session IS working correctly
- The issue is NOT with the metrics display, but with the underlying document retrieval
- Once vector search is fixed, sources and metrics will display properly
- User reported "everything was working a couple of days early" - likely because the old session had Short Story3.txt associated with it

---

**Status**: Issue identified, awaiting fix implementation
