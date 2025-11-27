# RAG Vector Search Failure - Root Cause Analysis

**Date**: 2025-11-24
**Status**: 🔴 CRITICAL - Documents exist but vector search returns 0 results
**Impact**: System gives hallucinated answers instead of using uploaded documents

---

## Problem Statement

When users query "Who is Aadhan?" or similar questions about uploaded documents:
- ✅ Documents exist in database with valid embeddings
- ✅ Tool selection works (document_rag is selected)
- ✅ Tool execution succeeds (no errors)
- ❌ **Vector search returns 0 chunks** (chunks_retrieved: 0)
- ❌ System hallucinates answers instead of using documents

---

## Investigation Completed

### 1. Tool Selection ✅ WORKING
- Enhanced RAG Agent uses GPT-4 for LLM-based tool selection
- GPT-4 correctly selects `document_rag` tool
- Tool selection method: `llm_based`, Intent: `document_qa`

### 2. Tool Execution ✅ WORKING
- `document_rag` tool executes successfully (no errors)
- Execution time: ~2000ms

### 3. Query Classification 🔍 INVESTIGATING
**Location**: `backend/app/services/rag_service_enhanced.py:157-215`

The RAG service classifies queries BEFORE retrieval and may skip RAG entirely if classified as general/ai_personal with confidence >= 0.75.

### 4. Vector Search 🔴 LIKELY ROOT CAUSE
**Location**: `backend/app/services/rag_service_enhanced.py:285-293`

Calls `document_service.search_similar_chunks()` with `_similarity_threshold` parameter.

**Possible Issues**:
1. Similarity threshold too high
2. Embedding model mismatch
3. SQL vector search bug
4. Cascade fallback not working

---

## Next Steps

1. Check `backend/app/core/config.py` for SIMILARITY_THRESHOLD value
2. Add debug logging to vector search
3. Test with threshold=0.0 to get ANY results
4. Verify embedding model consistency
