# RAG Document Retrieval Investigation Summary

## Document Not Being Retrieved - Root Causes

### Root Cause Analysis

#### 1. **Memory Hierarchy Implementation**
The system uses TWO memory layers for searching:
- **Short-term memory** (session documents): Only docs uploaded in THIS session
- **Long-term memory** (global): All processed documents in database

**Implication**: Documents uploaded in one session are NOT automatically searchable in other sessions.

#### 2. **Critical Missing Checks in Document Retrieval**

Session documents require a link in the `session_documents` table:
```sql
-- Session-specific search requires:
JOIN session_documents sd ON d.id = sd.document_id
WHERE sd.session_id = :session_id
```

If a document is NOT in `session_documents`, it's only available via global long-term memory.

#### 3. **Processing Pipeline is Asynchronous**
```
Upload → Database record created
  ↓
Process documents (ASYNC - may not be immediate):
  - Extract text
  - Split chunks
  - Generate embeddings
  
If processing fails, document is marked with `processed = FALSE`
and cannot be searched.
```

---

## Document Retrieval Flow

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Query                              │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
                   ┌─────────────────┐
                   │ Cache Hit Check │
                   │  (if enabled)   │
                   └────────┬────────┘
                            │ (Cache Miss or disabled)
                            ▼
              ┌─────────────────────────────┐
              │ Generate Query Embedding    │
              │ (sentence-transformers)     │
              └────────────┬────────────────┘
                           │
                    ┌──────┴──────┐
                    │             │
                    ▼             ▼
         ┌──────────────────┐  ┌──────────────────────┐
         │  SHORT-TERM      │  │   LONG-TERM MEMORY   │
         │  (Session Docs)  │  │   (All Documents)    │
         │                  │  │                      │
         │ 1. Find session  │  │ 1. Query ALL docs    │
         │ 2. Get associated│  │ 2. Hybrid search     │
         │    documents     │  │ 3. Cascading fallback│
         │ 3. Hybrid search │  │ 4. Keyword fallback  │
         │ 4. Cascading     │  │                      │
         │    fallback      │  │ Result: Global docs  │
         │                  │  │                      │
         │ Result: Session  │  └──────────┬───────────┘
         │ docs only        │             │
         └────────┬─────────┘             │
                  │                       │
                  └───────────┬───────────┘
                              │
                              ▼
                   ┌──────────────────────┐
                   │ Combine & Deduplicate│
                   │ (session docs first) │
                   └────────┬─────────────┘
                            │
                            ▼
                   ┌──────────────────────┐
                   │  Generate Response   │
                   │  with LLM Context    │
                   └────────┬─────────────┘
                            │
                            ▼
                   ┌──────────────────────┐
                   │   Format Sources     │
                   │ (with memory type)   │
                   └────────┬─────────────┘
                            │
                            ▼
                   ┌──────────────────────┐
                   │  Return Response     │
                   │  with Citations      │
                   └──────────────────────┘
```

---

## Key Code Locations

### 1. Main Query Entry Point
**File**: `/home/user/ChatBot/backend/app/services/rag_service_enhanced.py:42-322`

Orchestrates the entire memory hierarchy search:
- Line 158-173: Search session documents first
- Line 176-184: Search global documents as fallback
- Line 188-192: Combine and deduplicate results

### 2. Session Document Search
**File**: `/home/user/ChatBot/backend/app/services/rag_service_enhanced.py:373-479`

Searches ONLY documents in `session_documents` table:
- Line 401-409: Check if session has any documents
- Line 412-428: Verify embeddings exist
- Line 446-460: Execute hybrid search with cascading fallback

**Critical SQL Filter**:
```sql
JOIN session_documents sd ON d.id = sd.document_id
WHERE sd.session_id = :session_id
```

### 3. Global Document Search  
**File**: `/home/user/ChatBot/backend/app/services/document_service.py:335-451`

Searches ALL documents where `processed = TRUE`:
- No session filtering
- Uses cascading fallback
- Keyword-only search as final fallback

### 4. Hybrid Search Implementation
**File**: `/home/user/ChatBot/backend/app/services/document_service.py:453-576`

Combines semantic and keyword matching:
- Semantic: Vector cosine distance (60% weight)
- Keyword: Full-text search (40% weight)
- Formula: `combined = 0.6 * semantic + 0.4 * keyword`

### 5. Document-Session Association
**File**: `/home/user/ChatBot/backend/app/main.py:313-321`

Auto-associates documents with session on upload:
```python
await rag_service.associate_document_with_session(
    session_id=session_id,
    document_id=document.id,
    priority=1  # Higher = prioritized
)
```

Implementation: `/home/user/ChatBot/backend/app/services/rag_service_enhanced.py:324-371`

---

## Configuration Parameters Explained

### Default Settings
**File**: `/home/user/ChatBot/backend/app/core/config.py`

```python
CHUNK_SIZE = 800                    # Size of text chunks (chars)
CHUNK_OVERLAP = 150                 # Overlap between chunks
TOP_K_RESULTS = 5                   # Max chunks to retrieve
SIMILARITY_THRESHOLD = 0.70          # 70% - primary threshold
MIN_SIMILARITY_THRESHOLD = 0.55      # 55% - fallback threshold
NO_RELEVANT_DOCS_THRESHOLD = 0.65    # 65% - relevance check
```

### Pipeline Configuration
**File**: `/home/user/ChatBot/backend/app/rag_pipeline/config.py`

```python
# Retrieval
RETRIEVAL_CANDIDATES = 20            # Initial pool size
RETRIEVAL_ALPHA = 0.7                # 70% semantic, 30% keyword weight

# Reranking
ENABLE_RERANKER = True
RERANK_TOP_K = 5

# Cache
CACHE_SIMILARITY_THRESHOLD = 0.95    # Very high similarity for cache hit
CACHE_TTL_SECONDS = 3600             # 1 hour

# Memory Hierarchy
PRIORITIZE_SESSION_DOCUMENTS = True
SESSION_DOCUMENT_BOOST = 0.2          # Score boost for session docs
FALLBACK_TO_LONG_TERM = True
```

### Frontend RAG Settings
**File**: `/home/user/ChatBot/frontend/src/components/RAGSettings.tsx`

Users can adjust these in the UI:
- **Top K**: 1-20 (how many chunks)
- **Similarity Threshold**: 0-100% (primary threshold)
- **Min Similarity**: 0-100% (fallback threshold)
- **Relevance Threshold**: 0-100% (relevance check)
- **Chunk Size**: 200-2000 chars
- **Chunk Overlap**: 0-500 chars

---

## Why Documents Might Not Be Retrieved

### Scenario 1: Document Uploaded without Session ID
```
Problem: Document is NOT in session_documents table
Session search returns 0 results
Falls back to global search
Document IS found (if processed and has embeddings)
Impact: Document works in all sessions (global memory)
```

### Scenario 2: Document Processing Failed
```
Check: documents.processed = FALSE
Result: document_chunks table is empty
Symptom: "No documents found" in retrieval
Fix: Check processing_error field, reprocess document
```

### Scenario 3: High Similarity Thresholds
```
Default primary threshold: 0.70 (70%)
Default fallback threshold: 0.55 (55%)

If query-document similarity is between 0.55-0.70:
- Primary search fails
- Cascading fallback kicks in
- Document retrieved with lower threshold
- Logged as "threshold reduced to 0.55"
```

### Scenario 4: No Embeddings Generated
```
Check: SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL
If 0: Embeddings failed to generate
Cause: Embedding service error or timeout
Fix: Restart embedding service, reprocess documents
```

### Scenario 5: Semantic Similarity Too Low
```
Query: "What is the project?"
Document: Technical architecture details
Semantic similarity: 0.45 (below 0.55 threshold)

All cascading fallback thresholds tried:
- 0.70: No results
- 0.60: No results  
- 0.55: No results
- Keyword-only: Looks for exact keywords in chunks

Result: Falls back to no-document LLM response
```

---

## Cascading Fallback Strategy

### How It Works

When a search with threshold T finds no results:

```
Threshold 1: 0.70 (primary)
  → No results?
Threshold 2: 0.60 (fallback 1)
  → No results?
Threshold 3: 0.55 (fallback 2)
  → No results?
Threshold 4: Keyword-only search (final fallback)
  → No results?
Threshold 5: Return empty results → Pure LLM response
```

### Session vs Global Fallback

**Session Documents**:
- Primary: 0.65 (SIMILARITY_THRESHOLD - 0.05)
- Fallback 1: 0.55
- Fallback 2: 0.55
- Final: Keyword-only session search

**Global Documents**:
- Primary: 0.70 (SIMILARITY_THRESHOLD)
- Fallback 1: 0.60
- Fallback 2: 0.55
- Final: Keyword-only global search

---

## Hybrid Search Explained

### Semantic + Keyword Combination

```
Query: "machine learning models"
Document Chunk: "Deep learning neural networks for classification"

1. SEMANTIC SCORE (Vector Similarity)
   - Query embedding: [-0.2, 0.5, 0.3, ...]
   - Chunk embedding: [-0.1, 0.4, 0.35, ...]
   - Cosine distance: 0.1234
   - Score: 1 - 0.1234 = 0.8766 (87.66% similar)

2. KEYWORD SCORE (Full-Text)
   - "machine" in text? No (0.0)
   - "learning" in text? No (0.0)
   - "models" in text? No (0.0)
   - Keywords match? No
   - Score: 0.0

3. COMBINED SCORE
   = (0.8766 * 0.60) + (0.0 * 0.40)
   = 0.5259 (52.59%)

Result: Passes only if threshold < 52.59%
```

### Keyword-Only Search Example

```
Query: "What is PyTorch?"
No semantic matches found with hybrid search.

Keyword extraction: ["pytorch"]
Search: WHERE content ILIKE '%pytorch%'

Result: Any chunk mentioning "pytorch" exactly is returned
Score: 0.1 (low semantic, used as keyword match signal)
```

---

## Database Queries for Debugging

### Check Document Processing Status
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
  SELECT id, filename, processed, processing_error 
  FROM documents 
  ORDER BY upload_date DESC LIMIT 10;
"
```

### Check Embeddings
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
  SELECT 
    COUNT(*) as total_chunks,
    SUM(CASE WHEN embedding IS NOT NULL THEN 1 ELSE 0 END) as with_embeddings,
    SUM(CASE WHEN embedding IS NULL THEN 1 ELSE 0 END) as without_embeddings
  FROM document_chunks;
"
```

### Check Session Documents
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
  SELECT 
    cs.session_id, 
    COUNT(DISTINCT sd.document_id) as doc_count,
    COUNT(DISTINCT dc.id) as chunk_count
  FROM chat_sessions cs
  LEFT JOIN session_documents sd ON cs.id = sd.session_id
  LEFT JOIN document_chunks dc ON sd.document_id = dc.document_id
  GROUP BY cs.session_id
  LIMIT 5;
"
```

### Manual Vector Search Test
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
  -- Replace [...] with actual embedding vector
  SELECT 
    d.filename,
    dc.content,
    1 - (dc.embedding <=> '[...]'::vector) as similarity
  FROM document_chunks dc
  JOIN documents d ON dc.document_id = d.id
  WHERE dc.embedding IS NOT NULL
  ORDER BY dc.embedding <=> '[...]'::vector
  LIMIT 10;
"
```

---

## Summary

### The Problem
Documents sometimes aren't retrieved in RAG queries due to:
1. High similarity thresholds filtering out partial matches
2. Documents not associated with session (not in `session_documents`)
3. Documents not processed (embeddings not generated)
4. Semantic similarity too low for the query

### The Solution
The system has **cascading fallback** built in:
1. Try primary threshold (0.70)
2. Fall back to lower threshold (0.55)
3. Try keyword-only search
4. If still no results, use pure LLM response

### Key Insights
- **Two-tier memory**: Session docs prioritized, then global docs
- **Hybrid search**: 60% semantic, 40% keyword
- **Configurable**: All thresholds adjustable via UI
- **Robust**: Multiple fallback strategies prevent "no results"

### For Debugging
1. Check `documents.processed = TRUE`
2. Verify embeddings exist: `embedding IS NOT NULL`
3. Check session association: `session_documents` table
4. Review logs for threshold and score details
5. Adjust thresholds if needed in RAG Settings

