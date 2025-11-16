# Document Retrieval Issue - Files Upload But Don't Appear in Queries

## Your Issue

Based on your chat history:

1. ✅ **File uploads to MinIO** - Appears at 11:54 IST
2. ❌ **Queries don't use the document** - Gets generic "Islamic prayer" answer for "who is Aadhan?"
3. ❌ **Even "refer to attached document" doesn't work** - Still generic answer
4. ❌ **Can't re-upload the same file** - File input doesn't respond

## Root Causes Identified

### Issue #1: Documents Not Being Chunked/Embedded (MOST LIKELY)

**Symptom:** Files upload to MinIO but queries don't find them

**Cause:** Database tables for enhanced features might not exist yet

**What should happen:**
```
Upload file → Store in MinIO → Chunk text → Generate embeddings → Store in document_chunks table → Link to session
```

**What's probably happening:**
```
Upload file → Store in MinIO → ❌ No document_chunks table → Process fails silently → Not searchable
```

### Issue #2: File Re-upload Blocked

**Symptom:** Can't upload the same file twice

**Cause:** Browser file input not reset after selection

**Status:** ✅ FIXED in latest code

---

## Diagnosis Steps

### Step 1: Run Diagnostic Script

```bash
./diagnose-documents.sh
```

This will check:
- Are database tables created?
- Are documents being chunked?
- Are session associations working?
- Are there any errors in logs?

**Expected output if working correctly:**
```
Total documents: 3
Total chunks (embeddings): 45  ← Should be > 0!
Documents in sessions: 3
✅ Documents are being processed and linked to sessions!
```

**Output if broken:**
```
Total documents: 3
Total chunks (embeddings): 0  ← PROBLEM!
Documents in sessions: 0
⚠️  WARNING: Documents exist but NO CHUNKS found!
```

### Step 2: Check if Enhanced Tables Exist

```bash
docker exec rag-postgres psql -U postgres -d rag_chatbot -c "\dt"
```

**Required tables:**
- `documents` ✅ (base table - always exists)
- `document_chunks` ✅ (MUST exist for vectorization)
- `session_documents` ✅ (MUST exist for short-term memory)
- `chat_sessions` ✅ (MUST exist for session tracking)

**If missing:** Run the database setup script:
```bash
./setup-database.sh
```

### Step 3: Check Backend Logs

```bash
docker compose logs backend --tail=100 | grep -i "process\|chunk\|embed"
```

**Look for:**
- `✓ Using Enhanced RAG Service with memory hierarchy` ✅
- `Associated document ... with session ...` ✅
- `Processing document ...` ✅
- `Chunked document into N chunks` ✅

**Error indicators:**
- `ERROR` in logs
- `table "document_chunks" does not exist`
- `table "session_documents" does not exist`
- No processing messages at all

---

## Fixes

### Fix #1: Create Missing Database Tables

**If tables don't exist, run:**

```bash
./setup-database.sh
```

This creates all required tables:
- `documents`, `document_chunks` (vector store)
- `chat_sessions`, `session_documents` (session management)
- `conversation_messages` (chat history)
- `audit_logs`, `usage_metrics` (tracking)

**After running, restart services:**

```bash
docker compose restart backend
```

### Fix #2: Reprocess Existing Documents

**If documents exist but chunks don't:**

Create a reprocessing script:

```bash
cat > reprocess-documents.sh << 'EOF'
#!/bin/bash
echo "Reprocessing all documents..."

# Get document IDs
docker exec rag-postgres psql -U postgres -d rag_chatbot -t -c \
  "SELECT id FROM documents WHERE id NOT IN (
    SELECT DISTINCT document_id FROM document_chunks
  );" | while read doc_id; do

  doc_id=$(echo "$doc_id" | tr -d ' ')
  if [ ! -z "$doc_id" ]; then
    echo "Reprocessing document: $doc_id"
    # Trigger reprocessing via API
    curl -X POST "http://localhost:8000/api/v1/documents/$doc_id/reprocess"
  fi
done

echo "Done!"
EOF

chmod +x reprocess-documents.sh
./reprocess-documents.sh
```

**Or delete and re-upload:**

```bash
# Delete documents from database (keeps MinIO files)
docker exec rag-postgres psql -U postgres -d rag_chatbot -c \
  "DELETE FROM documents;"

# Re-upload files via UI
```

### Fix #3: File Re-upload (Already Fixed)

**Status:** ✅ Fixed in commit `10c215c`

**What changed:**
```typescript
// frontend/src/components/ChatInterfaceEnhanced.tsx
const handleFileSelect = (e) => {
  const files = Array.from(e.target.files || [])
  setAttachedFiles(prev => [...prev, ...files])

  // 🆕 Reset input to allow re-uploading same file
  if (fileInputRef.current) {
    fileInputRef.current.value = ''
  }
}
```

**To apply:** Restart frontend
```bash
docker compose restart frontend
```

---

## Testing After Fixes

### Step 1: Verify Tables Exist

```bash
docker exec rag-postgres psql -U postgres -d rag_chatbot -c "\dt" | grep -E "document_chunks|session_documents"
```

Should show:
```
 public | document_chunks     | table | postgres
 public | session_documents   | table | postgres
```

### Step 2: Upload a Test Document

1. **Open** `http://localhost:3001`
2. **Click paperclip** (📎) button
3. **Select a file** (e.g., text file with "Aadhan is a character...")
4. **Click Send**

**Check console:**
```
✅ Uploaded yourfile.txt to session session-abc123
```

### Step 3: Wait 5-10 Seconds

Document processing takes a few seconds:
- Extract text from file
- Chunk into smaller pieces
- Generate embeddings for each chunk
- Store in database

### Step 4: Query the Document

**Ask:** `"who is Aadhan?"`

**Expected response:**
- Answer from YOUR document (not generic Islamic prayer answer)
- Sources section showing your filename
- Relevance score > 0.7

**Check console:**
```
📤 Querying with session session-abc123 and 2 context messages
```

**Check backend logs:**
```bash
docker compose logs backend --tail=20 | grep -i "short-term\|session"
```

Should show:
```
Found 3 chunks in short-term memory
Found 5 chunks in long-term memory
```

### Step 5: Verify Database

```bash
# Check chunks were created
docker exec rag-postgres psql -U postgres -d rag_chatbot -c \
  "SELECT d.filename, COUNT(dc.id) as chunks
   FROM documents d
   JOIN document_chunks dc ON d.id = dc.document_id
   GROUP BY d.filename;"
```

Should show:
```
    filename     | chunks
-----------------+--------
 yourfile.txt    |   15
```

---

## Common Issues & Solutions

### Issue: "table document_chunks does not exist"

**Cause:** Database migration not run

**Fix:**
```bash
./setup-database.sh
docker compose restart backend
```

### Issue: Documents upload but chunks = 0

**Causes:**
1. Embedding service not working
2. Document processing failing silently
3. Database connection issues

**Fix:**
```bash
# Check backend logs for errors
docker compose logs backend --tail=100 | grep -i "error\|exception"

# Check if embedding service is accessible
docker compose ps embedding

# Restart all services
docker compose restart
```

### Issue: Session documents = 0

**Causes:**
1. session_id not being passed during upload
2. Enhanced RAG service not loaded
3. session_documents table doesn't exist

**Fix:**
```bash
# Check if session_id is in upload request (browser DevTools Network tab)
# Should see: session_id: session-...

# Check backend logs
docker compose logs backend | grep -i "enhanced rag"
# Should see: ✓ Using Enhanced RAG Service with memory hierarchy

# Verify table exists
docker exec rag-postgres psql -U postgres -d rag_chatbot -c "\d session_documents"
```

### Issue: Generic answers even with documents uploaded

**Causes:**
1. Query not passing session_id
2. Embeddings not being generated
3. Similarity threshold too high

**Fix:**
```bash
# Check query includes session_id (browser console)
# Should see: 📤 Querying with session session-... and N context messages

# Check backend logs during query
docker compose logs backend --tail=20

# Should see:
# - "Found N chunks in short-term memory"
# - If 0 chunks, document not processed or not in session

# Lower similarity threshold temporarily (backend/app/core/config.py)
# SIMILARITY_THRESHOLD = 0.5  # Was 0.7
```

---

## Understanding the Flow

### Complete Document Upload → Query Flow

```
┌─────────────────────────────────────────┐
│  USER: Upload document via paperclip    │
└───────────────┬─────────────────────────┘
                │
                ▼
    ┌───────────────────────────┐
    │  FRONTEND                 │
    │  - Generate session_id    │
    │  - FormData with file +   │
    │    session_id             │
    └───────────┬───────────────┘
                │
                ▼
    ┌───────────────────────────────────┐
    │  BACKEND /api/v1/upload           │
    │  1. Save to MinIO                 │
    │  2. Create in documents table     │
    │  3. process_document():           │
    │     - Extract text                │
    │     - Chunk (500 chars, 50 overlap)│
    │     - Generate embeddings         │
    │     - Save to document_chunks     │
    │  4. Associate with session:       │
    │     - Create session if not exist │
    │     - Link in session_documents   │
    └───────────┬───────────────────────┘
                │
                ▼
    ┌──────────────────────────────────┐
    │  DATABASE STATE                  │
    │  documents: 1 row                │
    │  document_chunks: 15 rows        │ ← CRITICAL!
    │  session_documents: 1 row        │ ← CRITICAL!
    │  chat_sessions: 1 row            │
    └──────────────────────────────────┘
                │
                ▼
    ┌──────────────────────────────────┐
    │  USER: Query "who is Aadhan?"    │
    └───────────┬──────────────────────┘
                │
                ▼
    ┌──────────────────────────────────────┐
    │  FRONTEND                            │
    │  - Send query + session_id +         │
    │    conversation_history              │
    └───────────┬──────────────────────────┘
                │
                ▼
    ┌───────────────────────────────────────────┐
    │  BACKEND /api/v1/query                    │
    │  1. Generate query embedding              │
    │  2. Search SHORT-TERM memory:             │
    │     SELECT from document_chunks           │
    │     JOIN documents                        │
    │     JOIN session_documents                │
    │     WHERE session_id = '...'              │
    │     → Find 3 chunks with >0.6 similarity  │
    │  3. Search LONG-TERM memory:              │
    │     SELECT from all document_chunks       │
    │     → Find 2 more chunks                  │
    │  4. Combine (short-term prioritized)      │
    │  5. Send to LLM with:                     │
    │     - Query: "who is Aadhan?"             │
    │     - Context: [5 document excerpts]      │
    │     - History: [previous messages]        │
    └───────────┬───────────────────────────────┘
                │
                ▼
    ┌──────────────────────────────────┐
    │  LLM RESPONSE                    │
    │  "Based on your document,        │
    │   Aadhan is a character..."      │
    │  Sources: [yourfile.txt]         │
    └──────────────────────────────────┘
```

### Where It Can Break

**Break Point #1: document_chunks not created**
```
Upload → MinIO ✅ → documents table ✅ → process_document() ❌
Result: File stored but not searchable
```

**Break Point #2: session_documents not created**
```
Upload → process_document() ✅ → associate_with_session() ❌
Result: Document in long-term memory only, not prioritized
```

**Break Point #3: Query missing session_id**
```
Query ❌ session_id → Only searches long-term memory
Result: Your documents have low priority
```

---

## Quick Fixes Summary

### Fix #1: Database Tables Missing
```bash
./setup-database.sh
docker compose restart backend
```

### Fix #2: Documents Not Chunked
```bash
# Delete and re-upload
docker exec rag-postgres psql -U postgres -d rag_chatbot -c "DELETE FROM documents;"
# Then re-upload via UI
```

### Fix #3: File Re-upload Not Working
```bash
# Already fixed, just restart
docker compose restart frontend
```

### Fix #4: Still Not Working
```bash
# Full reset
docker compose down
docker compose up -d --build
./setup-database.sh
# Wait 30 seconds
# Re-upload documents
```

---

## Verification Checklist

After applying fixes, verify:

- [ ] Tables exist:
  ```bash
  docker exec rag-postgres psql -U postgres -d rag_chatbot -c "\dt" | grep -E "document_chunks|session_documents"
  ```

- [ ] Enhanced RAG loaded:
  ```bash
  docker compose logs backend | grep "Enhanced RAG"
  # Should see: ✓ Using Enhanced RAG Service with memory hierarchy
  ```

- [ ] Upload creates chunks:
  ```bash
  # Upload file, then:
  docker exec rag-postgres psql -U postgres -d rag_chatbot -c "SELECT COUNT(*) FROM document_chunks;"
  # Should be > 0
  ```

- [ ] Session association works:
  ```bash
  docker exec rag-postgres psql -U postgres -d rag_chatbot -c "SELECT COUNT(*) FROM session_documents;"
  # Should be > 0
  ```

- [ ] Query finds documents:
  ```bash
  # Ask question, check backend logs:
  docker compose logs backend --tail=20 | grep "Found.*chunks"
  # Should see: Found N chunks in short-term memory
  ```

- [ ] File re-upload works:
  - Try uploading same file twice
  - Both should succeed

---

## Next Steps

1. **Run diagnostics:**
   ```bash
   ./diagnose-documents.sh
   ```

2. **If tables missing:**
   ```bash
   ./setup-database.sh
   docker compose restart backend
   ```

3. **Re-upload your document**

4. **Test query:**
   - Ask: "who is Aadhan?"
   - Should get answer from YOUR document

5. **Check verification checklist above**

---

## Getting Help

If still not working after these steps, share:

1. Output of `./diagnose-documents.sh`
2. Backend logs: `docker compose logs backend --tail=100`
3. Browser console logs (F12)
4. Screenshot of upload attempt

The most common issue is **database tables not created** → Run `./setup-database.sh`!
