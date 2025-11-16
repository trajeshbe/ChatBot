# Testing Document Upload and RAG Pipeline

This guide explains how to thoroughly test the document upload and RAG functionality.

## Quick Test (API-based)

The fastest way to test the upload pipeline is using the API test script:

```bash
# Ensure backend is running
docker-compose up -d

# Run the test
./test_api_upload.sh
```

This script will:
1. ✅ Check backend health
2. ✅ Create a test document
3. ✅ Upload it with a session ID
4. ✅ Verify it was processed and chunked
5. ✅ Check it appears in session documents
6. ✅ Run RAG queries to verify document is used in responses

## Comprehensive Test (Python-based)

For deeper testing including MinIO verification and direct database checks:

```bash
# Ensure backend is running
docker-compose up -d

# Run from project root
python test_upload_pipeline.py
```

This script tests:
1. ✅ MinIO file storage
2. ✅ Database document record
3. ✅ Document chunking
4. ✅ Embedding generation (384-dimensional vectors)
5. ✅ Session association
6. ✅ Vector similarity search
7. ✅ RAG query with document context
8. ✅ Memory hierarchy (short-term vs long-term)

## Manual Testing via UI

### Step 1: Upload a Document

1. Open http://localhost:3001
2. Go to the "Upload" tab
3. Drag and drop a file (PDF, TXT, DOCX, etc.)
4. Wait for "Processed" status (green checkmark)

**Expected behavior:**
- File shows "Uploading..." → "Processed" ✅
- No errors in browser console
- Session ID is logged: `🆔 Created new session: session-xxxxx`

### Step 2: Verify Upload in Backend Logs

```bash
# Watch backend logs
docker-compose logs -f backend | grep -E "(Uploaded|Document|chunks)"
```

**Look for:**
```
✅ Document uploaded successfully
✅ File uploaded to MinIO: <uuid>.txt
✅ Document processed: X chunks created
✅ Document 'filename.txt' (ID: xxx) associated with session session-xxx
📌 This document will be prioritized in queries for session session-xxx
```

### Step 3: Query the Document

1. Go to the "Chat" tab
2. Ask questions about the uploaded document
3. Check the response sources

**Expected behavior:**
- Response includes relevant information from your document
- Sources section shows your uploaded file
- Sources show `memory_type: "short-term"` (session-specific)
- Green indicator shows document was used

### Step 4: Verify in Database

```bash
# Check documents table
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT id, filename, processed, file_size FROM documents ORDER BY upload_date DESC LIMIT 5;"

# Check document chunks
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT d.filename, COUNT(dc.id) as chunk_count,
   COUNT(CASE WHEN dc.embedding IS NOT NULL THEN 1 END) as embedded_count
   FROM documents d
   LEFT JOIN document_chunks dc ON d.id = dc.document_id
   GROUP BY d.id, d.filename
   ORDER BY d.upload_date DESC LIMIT 5;"

# Check session associations
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT cs.session_id, d.filename, sd.priority, sd.added_at
   FROM session_documents sd
   JOIN chat_sessions cs ON sd.session_id = cs.id
   JOIN documents d ON sd.document_id = d.id
   ORDER BY sd.added_at DESC LIMIT 10;"
```

## Troubleshooting

### Issue: File uploads but shows "processing" forever

**Diagnosis:**
```bash
# Check if chunks were created
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT d.filename, d.processed, d.processing_error, COUNT(dc.id) as chunks
   FROM documents d
   LEFT JOIN document_chunks dc ON d.id = dc.document_id
   WHERE d.filename = 'your-file.txt'
   GROUP BY d.id;"
```

**Possible causes:**
1. Embedding service failed → Check backend logs for errors
2. Database transaction not committed → Check for rollback messages
3. Document processing threw exception → Check `processing_error` field

**Fix:**
```bash
# Restart backend to reinitialize services
docker-compose restart backend
```

### Issue: Document uploaded but not used in queries

**Diagnosis:**
```bash
# Check if embeddings exist
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL;"

# Check session association
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT * FROM session_documents WHERE document_id = '<your-doc-id>';"
```

**Possible causes:**
1. No embeddings generated → Embedding service not initialized
2. Session ID mismatch → Frontend and query using different session IDs
3. Similarity threshold too high → No chunks meet the threshold

**Fix:**
```python
# Lower similarity threshold in query
# In backend/app/services/rag_service_enhanced.py, line 85:
threshold=settings.SIMILARITY_THRESHOLD - 0.1  # Already lowered for session docs
```

### Issue: "No documents found" in response

**Diagnosis:**
```bash
# Check total document count
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT COUNT(*) FROM documents WHERE processed = true;"

# Check chunk count
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL;"
```

**Possible causes:**
1. Documents not processed yet → Wait a few seconds
2. No documents uploaded → Upload a document first
3. Database connection issue → Check database logs

### Issue: File upload returns 500 error

**Diagnosis:**
```bash
# Check backend logs
docker-compose logs backend | tail -50

# Check MinIO connectivity
curl http://localhost:9000/minio/health/live

# Check database connectivity
docker-compose exec postgres pg_isready
```

**Fix:**
```bash
# Restart services in order
docker-compose restart postgres
docker-compose restart minio
docker-compose restart backend
```

## Expected Log Output (Success)

### Backend Logs (Upload)
```
INFO - Processing file upload: test_doc.txt (session: session-xxx)
INFO - Uploaded file to MinIO: <uuid>.txt
INFO - Document created: <uuid> - test_doc.txt
INFO - Extracted 1234 characters from test_doc.txt
INFO - Created 5 chunks
INFO - Successfully processed document <uuid> with 5 chunks
✅ Document 'test_doc.txt' (ID: <uuid>) associated with session session-xxx
📌 This document will be prioritized in queries for session session-xxx
INFO - Transaction committed for document <uuid>
```

### Backend Logs (Query)
```
INFO - Processing query: What is this document about? (session: session-xxx)
INFO - Found 3 chunks in short-term memory (session documents)
✅ Found 3 chunks in short-term memory (session documents)
📄 Session documents used: ['test_doc.txt']
INFO - Found 2 chunks in long-term memory
INFO - Combined to 5 total chunks
🎯 Generating response with 5 chunks and 0 conversation messages
```

### Frontend Console (Upload)
```
🆔 Created new session: session-1699999999-abc123def
✅ Uploaded test_doc.txt to session session-1699999999-abc123def
```

## Performance Benchmarks

Typical performance for a 10KB text file:

| Stage | Expected Time |
|-------|--------------|
| Upload to MinIO | < 100ms |
| Text extraction | < 200ms |
| Chunking | < 50ms |
| Embedding generation (5 chunks) | 200-500ms |
| Database insert | < 100ms |
| **Total** | **< 1 second** |

For larger files (1MB+):
- PDF extraction: 1-5 seconds
- Embedding generation: 1-3 seconds per 100 chunks
- Total: 5-15 seconds

## Success Criteria

✅ **Upload successful if:**
1. API returns `success: true`
2. `chunks_created > 0`
3. File appears in MinIO bucket
4. Document record in database with `processed = true`
5. Document chunks have non-null `embedding` field
6. Session association created in `session_documents` table

✅ **RAG query successful if:**
1. API returns answer with `num_sources > 0`
2. Sources include the uploaded document
3. Sources show `memory_type: "short-term"` for session docs
4. Answer contains relevant information from the document

## Automated Testing

Run the full test suite:

```bash
# API tests
./test_api_upload.sh

# Python integration tests
python test_upload_pipeline.py

# Check results
echo $?  # Should be 0 for success
```

Both scripts will exit with:
- **0** = All tests passed ✅
- **1** = Tests failed ❌

## Next Steps

If all tests pass:
1. ✅ Upload pipeline is working correctly
2. ✅ Document chunking and embedding is functional
3. ✅ RAG queries use uploaded documents
4. ✅ Memory hierarchy (session-based) is working

If tests fail, check:
1. Service health: `docker-compose ps`
2. Backend logs: `docker-compose logs backend`
3. Database state: See troubleshooting SQL queries above
4. Network connectivity: `curl http://localhost:8000/health`

## Additional Resources

- **Architecture Guide**: See `MEMORY_HIERARCHY_GUIDE.md`
- **API Documentation**: http://localhost:8000/api/docs
- **Admin Dashboard**: http://localhost:3001/admin (check session documents)
- **MinIO Console**: http://localhost:9001 (check file storage)
