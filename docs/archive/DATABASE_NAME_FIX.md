# Database Name Mismatch Fix

**Date:** 2025-11-15
**Issue:** Documents visible in database console but diagnostic scripts report 0 documents
**Root Cause:** Database name inconsistency between configuration and diagnostic scripts

---

## Problem Summary

The user reported seeing document chunks (including TCS results data) in the database console, but:
1. Diagnostic scripts (`diagnose-documents.sh`, `check-documents.sh`) reported 0 documents
2. RAG queries weren't retrieving the uploaded documents
3. System was returning irrelevant results (e.g., Wikipedia articles instead of uploaded documents)

---

## Root Cause Analysis

### Database Name Mismatch

**Correct database name (from docker-compose.yml and config.py):**
```
ragchatbot  (no underscore)
```

**Wrong database name (in diagnostic/setup scripts):**
```
rag_chatbot  (with underscore)
```

### Evidence

1. **docker-compose.yml:10, 236**
   ```yaml
   POSTGRES_DB: ragchatbot
   ```

2. **backend/app/core/config.py:24**
   ```python
   POSTGRES_DB: str = "ragchatbot"
   ```

3. **Setup scripts (BEFORE fix)**
   ```bash
   # setup-database.sh, diagnose-documents.sh, check-documents.sh, etc.
   psql -d rag_chatbot  # WRONG!
   ```

This caused:
- Setup scripts to create tables in the wrong database (`rag_chatbot`)
- Diagnostic scripts to query the wrong database (showing 0 documents)
- Backend connecting to the correct database (`ragchatbot`) but scripts not seeing it

---

## Files Fixed

Fixed database name from `rag_chatbot` → `ragchatbot` in the following files:

### Diagnostic Scripts
1. ✅ `diagnose-documents.sh` - Main diagnostic tool
2. ✅ `check-documents.sh` - Document verification tool

### Setup Scripts
3. ✅ `setup-database.sh` - Database initialization script
4. ✅ `apply-migrations.sh` - Migration application script
5. ✅ `fix-embedding-dimensions.sh` - Embedding dimension fix

### Test Scripts
6. ✅ `test-document-flow.sh` - Document flow testing
7. ✅ `test-upload-endpoint.sh` - Upload endpoint testing
8. ✅ `test-upload-now.sh` - Quick upload test
9. ✅ `verify-complete-setup.sh` - Complete setup verification

### Other Scripts
10. ✅ `quick-setup-and-fix.sh` - Quick setup script

**Total files updated:** 10 shell scripts

---

## Impact on RAG Query Issue

The database name mismatch explains why diagnostics failed, but there's a **second issue** affecting document retrieval:

### Memory Hierarchy and Session Management

The application has TWO RAG service implementations:

1. **Basic RAG Service** (`rag_service.py`)
   - Searches ALL documents in the database
   - No session awareness
   - No memory hierarchy

2. **Enhanced RAG Service** (`rag_service_enhanced.py`)
   - **Memory Hierarchy:**
     - Short-term memory: Session-specific documents (searched FIRST)
     - Long-term memory: All documents (searched as fallback)
   - Session-aware search
   - Document prioritization

### How It Works

When a query is made with a `session_id`:

```python
# Enhanced RAG query flow (rag_service_enhanced.py:156-193)
1. Search session documents FIRST (short-term memory)
   └─ Query: JOIN session_documents WHERE session_id = :session_id

2. Search ALL documents (long-term memory)
   └─ Fallback to global document pool

3. Combine results (session docs have priority)
   └─ Deduplicate and rank by relevance
```

### Why TCS Results Might Not Be Retrieved

**Possible causes:**

1. **TCS document not linked to session**
   - Document uploaded but not associated with `session_id` in `session_documents` table
   - Solution: Re-upload with `session_id` parameter

2. **No session_id provided in query**
   - Frontend not passing `session_id` parameter
   - System falls back to global search

3. **Similarity threshold too high**
   - Current thresholds:
     - `SIMILARITY_THRESHOLD = 0.70` (70%)
     - `NO_RELEVANT_DOCS_THRESHOLD = 0.65` (65%)
   - TCS query might score below threshold

4. **Embedding dimension mismatch** (less likely if chunks visible in DB)
   - Expected: 384 dimensions
   - Actual: Check `document_chunks.embedding` column

---

## Verification Steps

After applying these fixes, run:

```bash
# 1. Verify diagnostic scripts now work
./diagnose-documents.sh

# Expected output:
# Total documents: [number > 0]
# Total chunks (embeddings): [number > 0]

# 2. Check if TCS document is in the database
docker exec rag-postgres psql -U postgres -d ragchatbot -c \
  "SELECT id, filename, processed FROM documents WHERE filename LIKE '%tcs%';"

# 3. Check if TCS chunks have embeddings
docker exec rag-postgres psql -U postgres -d ragchatbot -c \
  "SELECT COUNT(*) FROM document_chunks dc
   JOIN documents d ON dc.document_id = d.id
   WHERE d.filename LIKE '%tcs%' AND dc.embedding IS NOT NULL;"

# 4. Check session document associations
docker exec rag-postgres psql -U postgres -d ragchatbot -c \
  "SELECT cs.session_id, d.filename, sd.added_at
   FROM session_documents sd
   JOIN documents d ON sd.document_id = d.id
   JOIN chat_sessions cs ON sd.session_id = cs.id
   WHERE d.filename LIKE '%tcs%';"
```

---

## Recommendations

### Immediate Actions

1. **Verify enhanced RAG service is loaded**
   ```bash
   docker compose logs backend | grep "Enhanced RAG"
   # Should see: "✓ Using Enhanced RAG Service with memory hierarchy"
   ```

2. **Check if TCS document is linked to a session**
   - If not, re-upload the TCS document with a `session_id`
   - Or manually insert into `session_documents` table

3. **Test with session_id**
   ```bash
   # Upload with session_id
   curl -X POST http://localhost:8000/api/v1/upload \
     -F "file=@tcs1.pdf" \
     -F "session_id=test-session-123"

   # Query with same session_id
   curl -X POST http://localhost:8000/api/v1/query \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Tell me about TCS Results",
       "session_id": "test-session-123"
     }'
   ```

### Long-term Improvements

1. **Standardize database naming**
   - Document the canonical name in README.md
   - Add validation in setup scripts

2. **Add database name validation**
   ```bash
   # In setup scripts
   EXPECTED_DB="ragchatbot"
   if [ "$POSTGRES_DB" != "$EXPECTED_DB" ]; then
     echo "ERROR: Database name mismatch!"
     exit 1
   fi
   ```

3. **Improve error messages**
   - If session not found, provide clear guidance
   - If no session documents, explain memory hierarchy

4. **Add debugging endpoints**
   ```python
   @app.get("/api/v1/debug/session/{session_id}")
   async def debug_session(session_id: str):
       # Return session documents, chunks, etc.
   ```

---

## Related Files

- **Config:** `backend/app/core/config.py` (defines `POSTGRES_DB`)
- **Docker:** `docker-compose.yml` (sets database environment)
- **Enhanced RAG:** `backend/app/services/rag_service_enhanced.py`
- **Basic RAG:** `backend/app/services/rag_service.py`
- **Main:** `backend/app/main.py` (selects which RAG service to use)

---

## Git Commit Message

```
fix: correct database name mismatch in diagnostic and setup scripts

- Changed database name from 'rag_chatbot' to 'ragchatbot' in 10 shell scripts
- Aligns with database name defined in docker-compose.yml and config.py
- Fixes issue where diagnostic scripts reported 0 documents despite data existing
- Ensures all scripts query the correct database used by the backend

Files modified:
- diagnose-documents.sh
- check-documents.sh
- setup-database.sh
- apply-migrations.sh
- fix-embedding-dimensions.sh
- test-document-flow.sh
- test-upload-endpoint.sh
- test-upload-now.sh
- verify-complete-setup.sh
- quick-setup-and-fix.sh

Related to: Document retrieval issues, RAG query not finding uploaded files
```

---

## Notes

- The backend was already using the correct database name (`ragchatbot`)
- This fix ensures diagnostic and setup scripts are aligned with the backend
- Users should verify documents are linked to sessions for hierarchical memory to work
- The enhanced RAG service provides better document retrieval through session-based prioritization

**Status:** ✅ Fixed - Ready for commit
