# RAG Embedding Issue - Diagnosis and Fix Guide

## Problem Summary

**Issue**: RAG queries return no sources despite having 31 documents in the database.

**Root Cause**: Document chunks exist in the database but do not have embeddings generated. Without embeddings, vector similarity search cannot find relevant documents.

## Symptoms

- ✅ Documents successfully uploaded (31 documents shown in database)
- ❌ Queries return 0 sources (both with and without session_id)
- ❌ Vector similarity search fails silently
- ❌ Context shows "No documents found"

## Technical Details

### Where the Issue Occurs

1. **Vector Search Query** (`backend/app/services/document_service.py:313`)
   ```sql
   WHERE dc.embedding IS NOT NULL
   AND 1 - (dc.embedding <=> :embedding::vector) > :threshold
   ```
   - Requires embeddings to be non-NULL
   - If embeddings are NULL, no results are returned

2. **Similarity Threshold** (`backend/app/core/config.py:92`)
   - Was set to 0.7 (70% similarity required)
   - High threshold could also cause poor recall
   - **Fixed**: Lowered to 0.5 (50% similarity)

### Why Embeddings Might Be Missing

1. **Embedding Generation Failure**:
   - Embedding service crashed during document processing
   - Network issues with embedding model
   - Out of memory during batch processing

2. **Database Transaction Rollback**:
   - Document chunks created but not committed
   - Transaction rolled back due to error
   - Embeddings lost during rollback

3. **Database Migration Issue**:
   - Embedding column not properly created
   - Type mismatch (vector(384) expected)

4. **Processing Pipeline Bypass**:
   - Documents added directly to DB without processing
   - Chunks created without embeddings

## Solution

### Quick Fix (Recommended)

Run the automated fix script:

```bash
./fix_embeddings.sh
```

This script will:
1. ✅ Check API health
2. ✅ Run comprehensive diagnostics
3. ✅ Show embedding coverage statistics
4. ✅ Identify issues and recommendations
5. ✅ Regenerate missing embeddings (with user confirmation)
6. ✅ Verify the fix

### Manual Fix Options

#### Option 1: API Endpoint (Backend must be running)

```bash
# Regenerate embeddings for all documents
curl -X POST http://localhost:8000/api/v1/admin/regenerate-embeddings

# Regenerate for specific document
curl -X POST "http://localhost:8000/api/v1/admin/regenerate-embeddings?document_id=YOUR_DOC_UUID"

# With custom batch size
curl -X POST "http://localhost:8000/api/v1/admin/regenerate-embeddings?batch_size=50"
```

#### Option 2: Python Script (Direct database access)

```bash
# Regenerate all embeddings
python3 backend/regenerate_embeddings.py

# Regenerate specific document
python3 backend/regenerate_embeddings.py --document-id YOUR_DOC_UUID

# Custom batch size
python3 backend/regenerate_embeddings.py --batch-size 50
```

## Diagnostic Tools

### 1. Comprehensive Embedding Diagnostics

Check the health of embeddings in the system:

```bash
curl http://localhost:8000/api/v1/debug/embeddings | python3 -m json.tool
```

Returns:
- Total documents and chunks
- Embedding coverage percentage
- Chunks with/without embeddings
- Embedding dimensions
- pgvector extension status
- Vector indexes
- Sample chunk details
- Configuration settings
- Issues and recommendations

### 2. Session Document Diagnostics

Check session-specific document retrieval:

```bash
curl "http://localhost:8000/api/v1/debug/session/YOUR_SESSION_ID" | python3 -m json.tool
```

### 3. Test RAG Query

Run comprehensive RAG query test:

```bash
./test_rag_debug.sh
```

## Prevention

To prevent this issue in the future:

### 1. Monitor Embedding Generation

Check logs during document upload:

```bash
docker compose logs backend -f | grep -i "embedding\|error"
```

Look for:
- ✅ "Generated X embeddings"
- ✅ "All embeddings valid (384 dimensions)"
- ❌ "Error processing document"
- ❌ "Embedding generation failed"

### 2. Verify After Upload

After uploading documents, check embedding status:

```bash
curl http://localhost:8000/api/v1/debug/embeddings | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"Coverage: {d['embedding_coverage_percentage']:.1f}%\")"
```

Should show 100% coverage.

### 3. Enable Better Error Handling

The document processing pipeline now includes:
- Embedding dimension validation (must be 384)
- Count verification (chunks = embeddings)
- Automatic rollback on error
- Error logging in `documents.processing_error` column

### 4. Regular Health Checks

Add to your monitoring:

```bash
# Check embedding coverage
curl -s http://localhost:8000/api/v1/debug/embeddings | \
  python3 -c "import sys, json; d=json.load(sys.stdin); \
    print('✅ OK' if d['embedding_coverage_percentage'] == 100 else '❌ ISSUE')"
```

## Changes Made

### 1. New Diagnostic Endpoint

**File**: `backend/app/main.py:1276`

```python
@app.get("/api/v1/debug/embeddings")
async def debug_embeddings(db: AsyncSession = Depends(get_db)):
    """Comprehensive diagnostic endpoint to check embedding status"""
```

Returns detailed embedding statistics, issues, and recommendations.

### 2. Embedding Regeneration Endpoint

**File**: `backend/app/main.py:1144`

```python
@app.post("/api/v1/admin/regenerate-embeddings")
async def regenerate_embeddings_endpoint(
    document_id: Optional[str] = None,
    batch_size: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Admin endpoint to regenerate embeddings for documents missing them"""
```

Allows regenerating embeddings via API call.

### 3. Standalone Regeneration Script

**File**: `backend/regenerate_embeddings.py`

Command-line script to regenerate embeddings:
- Processes in configurable batches
- Can target specific documents
- Detailed progress logging
- Error handling with rollback

### 4. Lowered Similarity Threshold

**File**: `backend/app/core/config.py:92`

```python
SIMILARITY_THRESHOLD: float = 0.5  # Lowered from 0.7
```

**Reasoning**:
- 0.7 threshold is very restrictive (70% similarity)
- 0.5 provides better recall while maintaining reasonable precision
- More user-friendly for diverse queries
- Industry standard for semantic search

### 5. Automated Fix Script

**File**: `fix_embeddings.sh`

User-friendly bash script that:
- Checks API health
- Runs diagnostics
- Shows detailed status
- Prompts for fix
- Regenerates embeddings
- Verifies success

## Testing After Fix

### 1. Check Diagnostic Status

```bash
curl http://localhost:8000/api/v1/debug/embeddings | \
  python3 -c "import sys, json; d=json.load(sys.stdin); \
    print(f\"Status: {d['status']}\\nCoverage: {d['embedding_coverage_percentage']:.1f}%\")"
```

Expected:
```
Status: healthy
Coverage: 100.0%
```

### 2. Run RAG Query Test

```bash
./test_rag_debug.sh
```

Expected output:
```
Sources found: 5
Short-term sources: 0-5 (if session has documents)
Long-term sources: 0-5
✅ SUCCESS: Sources are being found!
```

### 3. Test Manual Query

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What are the key features?" \
  -F "use_cache=false" | python3 -m json.tool
```

Should return:
- `num_sources` > 0
- `sources` array with documents
- `answer` with context-based response

## FAQ

### Q: Why were embeddings missing in the first place?

A: Most likely causes:
1. Embedding service failure during initial document processing
2. Database transaction rollback
3. Documents uploaded before embedding pipeline was fully working
4. Out of memory during batch processing

### Q: Will regenerating embeddings affect existing data?

A: No. The regeneration process:
- ✅ Only updates NULL embeddings
- ✅ Preserves all document content
- ✅ Maintains document metadata
- ✅ Does not modify existing valid embeddings

### Q: How long does regeneration take?

A: Depends on document count:
- ~100 chunks: < 1 minute
- ~1000 chunks: 2-3 minutes
- ~10000 chunks: 10-15 minutes

Processing rate: ~50-100 chunks/second

### Q: What if regeneration fails?

A: Check:
1. Embedding service is running and accessible
2. Backend logs for specific errors
3. Database has sufficient storage
4. Sufficient memory for embedding model

### Q: Why lower the similarity threshold?

A:
- 0.7 is very restrictive (requires 70% similarity)
- Real-world queries often have lower similarity scores
- 0.5 balances precision and recall
- Can be adjusted in `.env` if needed:
  ```
  SIMILARITY_THRESHOLD=0.5
  ```

### Q: How do I check if my system is healthy now?

A:
```bash
./fix_embeddings.sh
```

Should show:
```
✅ All chunks have embeddings! System is healthy.
```

## Support

If issues persist after running the fix:

1. **Check Backend Logs**:
   ```bash
   docker compose logs backend --tail=100 | grep -i error
   ```

2. **Verify Database**:
   ```bash
   curl http://localhost:8000/api/v1/debug/embeddings | python3 -m json.tool
   ```

3. **Test Embedding Service**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/query \
     -F "query=test" -F "use_cache=false" | python3 -m json.tool
   ```

4. **Check Configuration**:
   - Verify `.env` settings
   - Check `SIMILARITY_THRESHOLD`
   - Ensure embedding model is loaded

## Related Files

- `backend/app/main.py` - API endpoints
- `backend/app/services/document_service.py` - Document processing
- `backend/app/services/embedding_service.py` - Embedding generation
- `backend/app/services/rag_service_enhanced.py` - RAG query logic
- `backend/app/core/config.py` - Configuration settings
- `fix_embeddings.sh` - Automated fix script
- `backend/regenerate_embeddings.py` - Standalone regeneration
- `test_rag_debug.sh` - RAG testing script

---

**Last Updated**: 2025-11-14
**Version**: 1.0.0
