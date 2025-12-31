# RAG Strategy Routing Guide

**Last Updated**: 2025-11-27
**Status**: ✅ ACTIVE
**Purpose**: Comprehensive guide to understanding and using RAG strategy routing in the Enterprise RAG Chatbot

---

## Table of Contents

1. [Overview](#overview)
2. [Strategy Routing Weights](#strategy-routing-weights)
3. [Available Strategies](#available-strategies)
4. [How to Configure](#how-to-configure)
5. [Strategy Selection Logic](#strategy-selection-logic)
6. [Use Cases](#use-cases)
7. [Technical Implementation](#technical-implementation)

---

## Overview

### What is Strategy Routing?

The Enhanced RAG Agent uses **intelligent strategy routing** to determine the best approach for answering your query. Instead of always using the same retrieval method, the system dynamically chooses from multiple strategies based on:

1. **User-defined weights** (configured in Weights Configuration UI)
2. **Query characteristics** (URLs, navigation keywords, general knowledge, etc.)
3. **Available tools** (navigation, OCR, document processing, etc.)

### Why Multiple Strategies?

Different types of questions require different approaches:

- **General knowledge** → Use LLM directly (no document retrieval needed)
- **Document-specific questions** → Search your uploaded documents
- **URL navigation requests** → Use web scraping tools
- **Image/PDF analysis** → Use OCR and vision models
- **Complex queries** → Combine multiple tools

---

## Strategy Routing Weights

### Weight Configuration

Open **Weights Configuration** page → **Strategy** tab to adjust these weights:

```typescript
strategy_weights: {
  direct_llm: 0.02,           // Use LLM without documents
  rag_short_term: 0.30,       // Search session documents only
  rag_long_term: 0.03,        // Search all documents
  rag_hybrid: 0.25,           // Combine short-term + long-term
  tool_navigation: 0.15,      // Web scraping for URLs
  tool_ocr: 0.10,             // OCR for images/PDFs
  tool_docling: 0.10,         // Advanced document processing
  tool_web_scraping: 0.05     // Generic web scraping
}
```

### How Weights Work

- **Range**: 0.0 to 1.0 (0% to 100%)
- **Threshold**: Weights > 0.8 (80%) **force** that strategy
- **Balanced**: Weights 0.2-0.8 allow intelligent selection
- **Disabled**: Weights < 0.1 rarely used

---

## Available Strategies

### 1. DIRECT_LLM Strategy

**When to use**: General knowledge questions that don't require your documents.

**Activation**:
- User sets `direct_llm` weight > 0.8 (80%)
- System bypasses document retrieval entirely

**Example Queries**:
- "What is machine learning?"
- "Explain Python decorators"
- "Who was Albert Einstein?"

**Behavior**:
```
User Query
    ↓
Direct LLM (ChatGPT/Ollama/etc.)
    ↓
Answer (no sources)
```

**Pros**:
- ✅ Fast (no document search)
- ✅ Good for general knowledge
- ✅ No "document not found" errors

**Cons**:
- ❌ Won't use your uploaded documents
- ❌ No source attribution
- ❌ May hallucinate if documents exist

**UI Configuration**:
```
Weights Configuration → Strategy Tab
→ Direct LLM: Set slider to 0.95 (95%)
→ Click "Apply to My Session"
```

---

### 2. RAG_SHORT_TERM Strategy

**When to use**: Questions about documents you just uploaded in this session.

**Activation**:
- User sets `rag_short_term` weight > 0.8 (80%)
- OR system detects query references recent uploads

**What is "Short-Term"?**
- **Short-term memory** = Documents uploaded in your current session
- Stored in `session_documents` table
- Tied to your `session_id` (stored in browser localStorage)
- Cleared when you refresh or new session starts

**Example Queries**:
- "What is the project scope?" (after uploading project_scope.pdf)
- "Summarize the requirements" (documents from this session)
- "What did I just upload?"

**Behavior**:
```
User Query
    ↓
Search Session Documents ONLY (fast, focused)
    ↓
Retrieve top_k chunks (e.g., top 5)
    ↓
LLM with session context
    ↓
Answer with sources (from your session)
```

**Pros**:
- ✅ Fast (searches fewer documents)
- ✅ Relevant (focused on recent uploads)
- ✅ Good for iterative work
- ✅ Source attribution from your session

**Cons**:
- ❌ Ignores older documents
- ❌ Won't find info from previous sessions
- ❌ Session-dependent

**Technical Details**:
- Uses `session_documents` table join
- Only searches documents with `session_id = current_session`
- Faster vector search (smaller search space)

---

### 3. RAG_LONG_TERM Strategy

**When to use**: Questions that might be answered by any document in your system.

**Activation**:
- User sets `rag_long_term` weight > 0.8 (80%)
- OR system can't find answer in short-term memory

**What is "Long-Term"?**
- **Long-term memory** = ALL documents ever uploaded
- Stored in `documents` and `document_chunks` tables
- No session filtering
- Persists across all sessions

**Example Queries**:
- "Has anyone written about RAG before?" (search all docs)
- "Find all mentions of 'machine learning'" (across all uploads)
- "What documents discuss pricing?" (global search)

**Behavior**:
```
User Query
    ↓
Search ALL Documents (comprehensive)
    ↓
Retrieve top_k chunks (e.g., top 10)
    ↓
LLM with global context
    ↓
Answer with sources (from any document)
```

**Pros**:
- ✅ Comprehensive (searches everything)
- ✅ Finds relevant info across sessions
- ✅ Good for knowledge base queries
- ✅ No missed documents

**Cons**:
- ❌ Slower (searches more documents)
- ❌ May surface irrelevant old docs
- ❌ Less focused than short-term

**Technical Details**:
- Uses full `document_chunks` table
- No session filtering
- Larger vector search space
- May use reranking to improve relevance

---

### 4. RAG_HYBRID Strategy

**When to use**: Best of both worlds - search session docs first, fall back to all docs.

**Activation**:
- User sets `rag_hybrid` weight > 0.8 (80%)
- OR system wants to be thorough

**What is "Hybrid"?**
- **Two-phase search**:
  1. **Phase 1**: Search short-term memory (session documents)
  2. **Phase 2**: If not enough relevant docs, search long-term memory (all documents)
- Intelligent fallback strategy

**Example Queries**:
- "What is the implementation plan?" (might be in session OR old docs)
- "Compare this project to previous ones" (session + historical)
- "Find relevant examples" (cast wide net)

**Behavior**:
```
User Query
    ↓
Search Session Documents (Phase 1)
    ↓
Enough relevant docs? (threshold check)
    ↓ YES → Answer
    ↓ NO
    ↓
Search ALL Documents (Phase 2)
    ↓
Combine results (session + global)
    ↓
LLM with hybrid context
    ↓
Answer with sources (mixed)
```

**Pros**:
- ✅ Best of both worlds
- ✅ Prioritizes recent uploads
- ✅ Falls back to comprehensive search
- ✅ High accuracy
- ✅ Source attribution from both memories

**Cons**:
- ❌ Slower than short-term alone
- ❌ More complex logic
- ❌ May retrieve too many sources

**Technical Details**:
- Two separate vector searches
- Uses `no_relevant_docs_threshold` to decide fallback
- Combines and deduplicates results
- Reranks combined results for quality

---

### 5. TOOL Strategies

#### Tool: Navigation Agent (tool_navigation)

**When to use**: Queries with URLs that need web scraping.

**Activation**:
- User sets `tool_navigation` weight > 0.5 (50%)
- OR system detects URL + navigation keywords

**Example Queries**:
- "Navigate to https://example.com and get the pricing"
- "Scrape this URL: https://docs.python.org"
- "Get details from https://api.github.com/repos/..."

**Behavior**:
```
User Query + URL
    ↓
Playwright Browser Automation
    ↓
Navigate to URL
    ↓
Extract content
    ↓
LLM processes extracted content
    ↓
Answer with URL as source
```

**Keywords that trigger navigation**:
- navigate, scrape, fetch from, get details, access, browse, visit

#### Tool: OCR (tool_ocr)

**When to use**: Analyzing images or scanned PDFs.

**Activation**:
- User sets `tool_ocr` weight > 0.5 (50%)
- OR system detects image/PDF without text layer

**Example Queries**:
- "What does this construction drawing show?"
- "Extract text from this scanned invoice"
- "Analyze this floor plan"

**Behavior**:
```
User uploads image/PDF
    ↓
OCR service (Tesseract)
    ↓
Extract text from image
    ↓
LLM processes OCR text
    ↓
Answer with extracted info
```

#### Tool: Docling (tool_docling)

**When to use**: Advanced document processing (complex PDFs, tables, layouts).

**Activation**:
- User sets `tool_docling` weight > 0.5 (50%)
- OR system detects complex document structure

**Example Queries**:
- "Extract all tables from this financial report"
- "Parse this structured PDF"
- "Get layout information from this document"

**Behavior**:
```
User uploads complex document
    ↓
Docling service
    ↓
Extract structure (tables, layouts)
    ↓
LLM processes structured data
    ↓
Answer with structured info
```

#### Tool: Web Scraping (tool_web_scraping)

**When to use**: Generic web content extraction.

**Activation**:
- User sets `tool_web_scraping` weight > 0.3 (30%)
- OR system needs to fetch web content

**Example Queries**:
- "Get the latest news from https://news.ycombinator.com"
- "Scrape product listings from this site"

---

## How to Configure

### Step-by-Step Configuration

1. **Open Weights Configuration**:
   ```
   http://localhost:3001 → Weights Configuration (sidebar)
   ```

2. **Select Strategy Tab**

3. **Adjust Weight Sliders**:
   - **Direct LLM**: 0.02 (rarely use) to 0.95 (always use)
   - **RAG Short-Term**: 0.30 (default) to 0.90 (prioritize session)
   - **RAG Long-Term**: 0.03 (default) to 0.90 (search everything)
   - **RAG Hybrid**: 0.25 (default) to 0.90 (best of both)
   - **Tool weights**: 0.05-0.50 depending on use case

4. **Apply to Session**:
   ```
   Click "Apply to My Session" button
   ```

5. **Test in Chat**:
   ```
   Navigate to Chat → Submit query → Check routing strategy in metadata
   ```

---

## Strategy Selection Logic

### Decision Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CHECK: Direct LLM Weight                                 │
│    IF direct_llm > 0.8 → DIRECT_LLM (skip RAG)            │
└─────────────────┬───────────────────────────────────────────┘
                  │ NO
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. CHECK: URL + Navigation Keywords                         │
│    IF has_url AND has_navigation_intent → NAVIGATION       │
└─────────────────┬───────────────────────────────────────────┘
                  │ NO
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. CHECK: Force RAG Weights                                 │
│    IF rag_short_term > 0.8 → RAG_SHORT_TERM                │
│    IF rag_long_term > 0.8 → RAG_LONG_TERM                  │
│    IF rag_hybrid > 0.8 → RAG_HYBRID                        │
└─────────────────┬───────────────────────────────────────────┘
                  │ NO FORCE
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. BALANCED ROUTING: Score All Strategies                   │
│    - Query classification (general knowledge vs specific)    │
│    - Tool relevance scoring                                  │
│    - Weight-adjusted scores                                  │
│    - Choose highest-scoring strategy                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. EXECUTE CHOSEN STRATEGY                                  │
│    - Log routing decision                                    │
│    - Execute strategy workflow                               │
│    - Return answer with metadata                             │
└─────────────────────────────────────────────────────────────┘
```

### Code Reference

**Location**: `backend/app/agents/enhanced_rag_agent.py` lines 134-200

**Key Decision Points**:
1. **Line 150**: Check `direct_llm_weight > 0.8`
2. **Line 178**: Check URL + navigation keywords
3. **Line 188**: Check `rag_short_term > 0.8` or `rag_long_term > 0.8`
4. **Lines 200+**: Balanced routing with tool selection

---

## Use Cases

### Use Case 1: General Knowledge Chatbot

**Scenario**: You want to use the chatbot for general questions without uploading documents.

**Configuration**:
```
direct_llm: 0.95 (HIGH - force Direct LLM)
rag_short_term: 0.02 (LOW)
rag_long_term: 0.02 (LOW)
rag_hybrid: 0.01 (LOW)
```

**Example Queries**:
- "Explain quantum computing"
- "Write a Python function to sort a list"
- "What is the capital of France?"

**Expected Behavior**:
- ✅ Fast responses (no document search)
- ✅ General knowledge answers
- ❌ Won't use uploaded documents (even if relevant)

---

### Use Case 2: Session-Focused Document Q&A

**Scenario**: You upload project documents and want answers from ONLY those documents.

**Configuration**:
```
direct_llm: 0.02 (LOW)
rag_short_term: 0.90 (HIGH - force session docs)
rag_long_term: 0.02 (LOW)
rag_hybrid: 0.05 (LOW)
```

**Example Queries**:
- "What is the project scope?"
- "List all requirements from the uploaded BRD"
- "Summarize the technical architecture"

**Expected Behavior**:
- ✅ Searches ONLY session documents
- ✅ Fast, focused answers
- ✅ Source attribution from your uploads
- ❌ Won't find info from older documents

---

### Use Case 3: Comprehensive Knowledge Base

**Scenario**: You have a large document repository and want to search across ALL documents.

**Configuration**:
```
direct_llm: 0.02 (LOW)
rag_short_term: 0.10 (LOW)
rag_long_term: 0.90 (HIGH - force global search)
rag_hybrid: 0.05 (LOW)
```

**Example Queries**:
- "Find all documents mentioning 'customer complaints'"
- "Has anyone written about API design?"
- "What are our pricing policies?" (search all docs)

**Expected Behavior**:
- ✅ Comprehensive search across all docs
- ✅ Finds relevant info from any session
- ✅ Good for knowledge base queries
- ❌ Slower than session-only search

---

### Use Case 4: Smart Hybrid (Recommended Default)

**Scenario**: You want intelligent behavior - check session first, fall back to all docs if needed.

**Configuration**:
```
direct_llm: 0.02 (LOW)
rag_short_term: 0.30 (MEDIUM)
rag_long_term: 0.03 (LOW)
rag_hybrid: 0.80 (HIGH - force hybrid)
tool_navigation: 0.15 (MEDIUM)
```

**Example Queries**:
- "What is the implementation plan?" (hybrid search)
- "Compare this project to previous ones" (session + historical)
- "Navigate to https://docs.example.com" (uses tool)

**Expected Behavior**:
- ✅ Searches session docs first (fast)
- ✅ Falls back to all docs if needed (thorough)
- ✅ Uses tools when appropriate (URLs)
- ✅ Best accuracy overall

---

### Use Case 5: Web Research + Documents

**Scenario**: You want to combine your documents with live web scraping.

**Configuration**:
```
direct_llm: 0.05 (LOW)
rag_short_term: 0.25 (LOW-MEDIUM)
rag_long_term: 0.10 (LOW)
rag_hybrid: 0.30 (MEDIUM)
tool_navigation: 0.70 (HIGH - prioritize web)
tool_web_scraping: 0.40 (MEDIUM)
```

**Example Queries**:
- "Get pricing from https://aws.amazon.com/pricing/"
- "Compare our docs to https://competitor.com/features"
- "Scrape product details from this URL and compare to our catalog"

**Expected Behavior**:
- ✅ Prioritizes web scraping for URLs
- ✅ Uses documents when no URL present
- ✅ Can combine web + doc results
- ✅ Good for research tasks

---

## Technical Implementation

### Backend Architecture

**File**: `backend/app/agents/enhanced_rag_agent.py`

**Class**: `EnhancedRAGAgent`

**Main Method**: `run(query, session_id, user_preferences)`

### Weight Extraction

```python
# Lines 135-139
strategy_weights = user_preferences.get('strategy_weights', {})
direct_llm_weight = strategy_weights.get('direct_llm', 0.02)
rag_short_term_weight = strategy_weights.get('rag_short_term', 0.3)
rag_long_term_weight = strategy_weights.get('rag_long_term', 0.03)
rag_hybrid_weight = strategy_weights.get('rag_hybrid', 0.25)
```

### Strategy Execution

#### Direct LLM (Lines 150-167)
```python
if direct_llm_weight > 0.8:
    logger.info("ROUTING: DIRECT_LLM")
    result = await self._direct_llm_query(
        query=query,
        session_id=session_id,
        user_preferences=user_preferences
    )
    result['metadata']['routing_strategy'] = 'direct_llm'
    return result
```

#### URL Navigation (Lines 178-185)
```python
url_pattern = r'https?://[^\s]+'
navigation_keywords = ['navigate', 'scrape', 'get details', ...]

has_url = re.search(url_pattern, query)
has_navigation_intent = any(keyword in query.lower() for keyword in navigation_keywords)

if has_url and has_navigation_intent:
    logger.info("ROUTING: NAVIGATION")
    # Continue to balanced routing which handles this
```

#### Force RAG (Lines 188-200)
```python
if rag_short_term_weight > 0.8 or rag_long_term_weight > 0.8:
    logger.info("ROUTING: FORCE_RAG")
    # Force RAG tool selection
    tool_params_rag = {
        "top_k": top_k,
        "similarity_threshold": similarity_threshold,
        ...
    }
```

### Metadata Tracking

Every response includes routing metadata:

```python
result['metadata'] = {
    'routing_strategy': 'direct_llm' | 'rag_short_term' | 'rag_long_term' | 'rag_hybrid' | 'navigation',
    'routing_reason': 'User set direct_llm=0.95',
    'strategy_weights': {
        'direct_llm': 0.95,
        'rag_short_term': 0.30,
        ...
    },
    'chunks_retrieved': 5,
    'use_documents': True/False,
    'latency_ms': 3567.89
}
```

---

## Related Documentation

- **Weights Configuration**: `docs/fixes/ALL_WEIGHTS_CONFIG_VALIDATION.md`
- **Backend Parsing**: `docs/fixes/BACKEND_UNIFIED_CONFIG_PARSING_FIX.md`
- **Frontend Config**: `docs/fixes/UI_WEIGHTS_CONFIG_PASSING_TO_BACKEND_FIX.md`
- **Memory Hierarchy**: `docs/architecture/MEMORY_HIERARCHY_GUIDE.md`
- **Multi-Strategy RAG**: `docs/rag_features/MULTI_STRATEGY_RAG_GUIDE.md`

---

## Summary

### Key Takeaways

1. **8 Strategies Available**:
   - direct_llm, rag_short_term, rag_long_term, rag_hybrid
   - tool_navigation, tool_ocr, tool_docling, tool_web_scraping

2. **Weight Control**:
   - Configure in UI: http://localhost:3001 → Weights Configuration
   - Weights > 0.8 **force** that strategy
   - Balanced weights allow intelligent selection

3. **Session vs Global**:
   - **Short-term** = this session's documents (fast, focused)
   - **Long-term** = all documents (comprehensive)
   - **Hybrid** = short-term first, then long-term (best of both)

4. **Routing is Intelligent**:
   - Checks weights first
   - Detects URLs and navigation intent
   - Falls back to balanced scoring
   - Always logs decision in metadata

5. **User Control**:
   - You have full control via weights
   - System respects your preferences
   - Metadata shows what strategy was used

---

**End of RAG Strategy Routing Guide**
