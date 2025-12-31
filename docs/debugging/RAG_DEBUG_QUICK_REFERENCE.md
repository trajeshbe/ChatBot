# RAG Document Retrieval - Quick Reference Guide

## File Locations (Absolute Paths)

### Core Services

| Component | File Path |
|-----------|-----------|
| **RAG Service** (main orchestrator) | `/home/user/ChatBot/backend/app/services/rag_service_enhanced.py` |
| Session document search | Lines 373-479 |
| Hybrid search for global docs | Lines 176-184 |
| Document-session association | Lines 324-371 |
| **Document Service** | `/home/user/ChatBot/backend/app/services/document_service.py` |
| Global document search | Lines 335-451 |
| Hybrid search execution | Lines 453-576 |
| Keyword extraction | Lines 640-714 |
| **LLM Service** | `/home/user/ChatBot/backend/app/services/llm_service_enhanced.py` |
| **Embedding Service** | `/home/user/ChatBot/backend/app/services/embedding_service.py` |

### Configuration

| Setting | File Path |
|---------|-----------|
| **Main Config** | `/home/user/ChatBot/backend/app/core/config.py` |
| RAG thresholds | Lines 88-97 |
| **RAG Pipeline Config** | `/home/user/ChatBot/backend/app/rag_pipeline/config.py` |
| Memory hierarchy settings | Lines 141-156 |
| Model context windows | Lines 87-113 |

### API Endpoints

| Endpoint | File Path |
|----------|-----------|
| **Main Query API** | `/home/user/ChatBot/backend/app/main.py` |
| Query endpoint | Line 382 |
| Upload endpoint | Line 231 |
| **RAG Pipeline API** | `/home/user/ChatBot/backend/app/api/routes/rag_pipeline_routes.py` |
| Pipeline query | Line 86 |

### Database Models

| Table | File Path |
|-------|-----------|
| **Core Models** | `/home/user/ChatBot/backend/app/models/database.py` |
| Document | Line 11 |
| DocumentChunk | Line 27 |
| Conversation | Line 39 |
| **Enhanced Models** | `/home/user/ChatBot/backend/app/models/database_enhanced.py` |
| ChatSession | Line 75 |
| SessionDocument (KEY!) | Line 90 |
| ConversationMessage | Line 103 |

### Frontend

| Component | File Path |
|-----------|-----------|
| **Chat Interface** | `/home/user/ChatBot/frontend/src/components/ChatInterfaceEnhanced.tsx` |
| **RAG Settings** | `/home/user/ChatBot/frontend/src/components/RAGSettings.tsx` |
| Config defaults | Lines 19-26 |
| Settings items | Lines 63-124 |

---

## Document Retrieval Sequence

### Step 1: Query Received
**File**: `/home/user/ChatBot/backend/app/main.py:382`
```python
@app.post("/api/v1/query")
async def query_endpoint(
    query: str,
    session_id: Optional[str],
    top_k: Optional[int],
    similarity_threshold: Optional[float],
    ...
)
```

### Step 2: Enhanced RAG Service Called
**File**: `/home/user/ChatBot/backend/app/services/rag_service_enhanced.py:42`
```python
async def query(
    query_text: str,
    session_id: Optional[str],
    db: AsyncSession,
    top_k: Optional[int] = None,
    similarity_threshold: Optional[float] = None,
    ...
)
```

### Step 3: Search Short-Term Memory (Session)
**File**: `/home/user/ChatBot/backend/app/services/rag_service_enhanced.py:158-173`
- Calls `_search_session_documents()`
- Filters by `session_documents` table
- Returns session-specific chunks

### Step 4: Search Long-Term Memory (Global)
**File**: `/home/user/ChatBot/backend/app/services/rag_service_enhanced.py:176-184`
- Calls `document_service.search_similar_chunks()`
- NO session filtering
- Returns all matching documents

### Step 5: Combine Results
**File**: `/home/user/ChatBot/backend/app/services/rag_service_enhanced.py:188-192`
```python
combined_chunks = self._combine_memory_results(
    short_term_chunks,
    long_term_chunks,
    max_chunks=_top_k
)
```

### Step 6: Generate Response
**File**: `/home/user/ChatBot/backend/app/services/rag_service_enhanced.py:209-214`
- Uses LLM service with combined context
- Formats sources with memory type (short-term/long-term)

---

## Configuration Parameter Flow

### Setting Default Values
1. **Backend Config** (`/home/user/ChatBot/backend/app/core/config.py`)
   - Default: `SIMILARITY_THRESHOLD = 0.70`

2. **RAG Pipeline Config** (`/home/user/ChatBot/backend/app/rag_pipeline/config.py`)
   - Default: `GOOD_SIMILARITY_THRESHOLD = 0.6`

3. **Frontend Config** (`/home/user/ChatBot/frontend/src/components/RAGSettings.tsx`)
   - Default: `similarity_threshold: 0.70`

### Using Overrides in Query
**Query Endpoint** (`/home/user/ChatBot/backend/app/main.py:391-394`)
```python
top_k: Optional[int] = Form(None),
similarity_threshold: Optional[float] = Form(None),
min_similarity_threshold: Optional[float] = Form(None),
no_relevant_docs_threshold: Optional[float] = Form(None),
```

**RAG Service** (`/home/user/ChatBot/backend/app/services/rag_service_enhanced.py:52-55`)
```python
top_k: Optional[int] = None,
similarity_threshold: Optional[float] = None,
min_similarity_threshold: Optional[float] = None,
no_relevant_docs_threshold: Optional[float] = None
```

**Apply Defaults** (`/home/user/ChatBot/backend/app/services/rag_service_enhanced.py:69-72`)
```python
_top_k = top_k if top_k is not None else settings.TOP_K_RESULTS
_similarity_threshold = similarity_threshold if similarity_threshold is not None else settings.SIMILARITY_THRESHOLD
_min_similarity_threshold = min_similarity_threshold if min_similarity_threshold is not None else settings.MIN_SIMILARITY_THRESHOLD
_no_relevant_docs_threshold = no_relevant_docs_threshold if no_relevant_docs_threshold is not None else settings.NO_RELEVANT_DOCS_THRESHOLD
```

---

## SQL Queries for Debugging

### Check if Document Has Embeddings
```sql
SELECT COUNT(*) as chunks_with_embeddings
FROM document_chunks
WHERE document_id = 'YOUR_DOC_ID' AND embedding IS NOT NULL;
```

### Check Session-Document Association
```sql
SELECT sd.*, d.filename
FROM session_documents sd
JOIN documents d ON sd.document_id = d.id
WHERE sd.session_id = (
  SELECT id FROM chat_sessions WHERE session_id = 'YOUR_SESSION_ID'
);
```

### Find Session ID UUID from String ID
```sql
SELECT id FROM chat_sessions WHERE session_id = 'YOUR_SESSION_ID';
```

### Test Vector Similarity (Manual)
```sql
-- First, get embedding for a chunk
SELECT embedding FROM document_chunks LIMIT 1;

-- Then use that embedding to test similarity
SELECT 
  d.filename,
  1 - (dc.embedding <=> '[PASTE_EMBEDDING_HERE]'::vector) as similarity
FROM document_chunks dc
JOIN documents d ON dc.document_id = d.id
WHERE dc.embedding IS NOT NULL
ORDER BY similarity DESC
LIMIT 10;
```

### Check Processing Status
```sql
SELECT id, filename, processed, processing_error 
FROM documents 
ORDER BY upload_date DESC;
```

---

## Log Analysis

### Look for These Patterns

**Session Document Search**:
```
🔍 Searching session documents for session SESSION_ID
📊 Session SESSION_ID: X documents, Y chunks with embeddings
✅ Found N chunks with threshold=0.65
⚠️ No session-specific documents found for session SESSION_ID
```

**Fallback Thresholds**:
```
🔍 Session search with threshold=0.65
✅ Found N session chunks with threshold=0.65
🔍 Searching all documents (threshold: 0.60)
✅ Found N chunks in long-term memory - hybrid search
```

**Relevance Checks**:
```
✅ N high-quality chunks (best score: 0.85)
⚠️ Best match score 0.45 below threshold 0.65, treating as no relevant docs
```

**Embedding Issues**:
```
❌ No embeddings found! X chunks exist but none have embeddings
Generating embeddings for X chunks...
```

### Get Logs
```bash
# Last 50 lines
docker-compose logs -f backend --tail=50

# With grep
docker-compose logs backend | grep "Session"
docker-compose logs backend | grep "Found.*chunks"
docker-compose logs backend | grep "threshold"
docker-compose logs backend | grep "No documents"

# With context
docker-compose logs backend | grep -A5 -B5 "search_session_documents"
```

---

## Common Debugging Commands

### Verify Embeddings Exist
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL;"
```

### Check Document Processing
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT filename, processed FROM documents LIMIT 5;"
```

### List Session Documents
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT cs.session_id, COUNT(sd.document_id) as docs 
   FROM chat_sessions cs 
   LEFT JOIN session_documents sd ON cs.id = sd.session_id 
   GROUP BY cs.session_id;"
```

### Backend Shell
```bash
docker-compose exec backend bash
cd /app/backend
python -c "from app.services.document_service import document_service; import asyncio; asyncio.run(document_service.initialize())"
```

### Database Shell
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot
# Then run SQL queries directly
```

---

## Key Code Snippets

### How Session Association Works
```python
# From main.py:313-321
await rag_service.associate_document_with_session(
    session_id=session_id,
    document_id=document.id,
    priority=1,  # Higher = prioritized
    db=db
)

# Implementation in rag_service_enhanced.py:359-365
session_doc = SessionDocument(
    session_id=session.id,
    document_id=document_id,
    priority=priority
)
db.add(session_doc)
await db.flush()
```

### Session Document SQL Filter
```sql
-- From rag_service_enhanced.py:518-520
JOIN session_documents sd ON d.id = sd.document_id
WHERE sd.session_id = :session_id
    AND dc.embedding IS NOT NULL
```

### Hybrid Search Scoring
```sql
-- From document_service.py:519
(ss.semantic_score * 0.6 + COALESCE(ks.keyword_score, 0) * 0.4) as combined_score

-- 60% semantic weight + 40% keyword weight
```

### Cascading Fallback
```python
# From rag_service_enhanced.py:431-437
thresholds_to_try = [threshold]
if use_cascading_fallback:
    if threshold > settings.MIN_SIMILARITY_THRESHOLD + 0.1:
        thresholds_to_try.append(threshold - 0.1)
    if threshold > settings.MIN_SIMILARITY_THRESHOLD:
        thresholds_to_try.append(settings.MIN_SIMILARITY_THRESHOLD)
```

---

## Parameter Adjustment Guide

### If Getting No Results

1. **Lower Similarity Threshold**
   - Current: 0.70 (70%)
   - Try: 0.60 (60%)
   - Effect: More documents retrieved (less strict)

2. **Lower Min Similarity Threshold**
   - Current: 0.55 (55%)
   - Try: 0.45 (45%)
   - Effect: Fallback threshold more lenient

3. **Increase Top K**
   - Current: 5
   - Try: 10-15
   - Effect: Retrieve more chunks per query

### If Getting Irrelevant Results

1. **Increase Similarity Threshold**
   - Current: 0.70 (70%)
   - Try: 0.75 (75%)
   - Effect: Only very similar documents returned

2. **Increase Relevance Threshold**
   - Current: 0.65 (65%)
   - Try: 0.70 (70%)
   - Effect: Stricter check for document relevance

3. **Decrease Top K**
   - Current: 5
   - Try: 3
   - Effect: Only best matches returned

---

## Testing Workflow

### 1. Upload a Document
- Use UI or API: `POST /api/v1/upload`
- Include `session_id` in form data
- Document should appear in `documents` table

### 2. Verify Processing
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT id, filename, processed FROM documents WHERE filename LIKE '%test%';"
```

### 3. Check Embeddings
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT COUNT(*) FROM document_chunks WHERE document_id = 'PASTE_DOC_ID';"
```

### 4. Check Session Association
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT * FROM session_documents WHERE document_id = 'PASTE_DOC_ID';"
```

### 5. Query with Debugging
- Set similarity_threshold low (0.5) for testing
- Check logs for "Found X chunks"
- Verify session vs global retrieval

### 6. Analyze Results
- Check similarity scores in logs
- Verify sources in response
- Check memory_type (short-term/long-term)

