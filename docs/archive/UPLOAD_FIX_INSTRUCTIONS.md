# Document Upload Fix - Testing Instructions

## Problem Fixed

The document upload endpoint was experiencing a transaction management issue where:
- API returned HTTP 200 success
- Response indicated successful processing
- **BUT** documents and chunks were not persisting to the database (0 documents, 0 chunks)

## Root Cause

The issue was caused by improper transaction management:
1. `upload_file()` was committing the document in a separate transaction
2. `process_document()` was committing chunks in another transaction
3. `get_db()` dependency was auto-committing at the end
4. Multiple commits within a single request created inconsistent transaction states

## Changes Made

### 1. document_service.py
- Changed `await db.commit()` to `await db.flush()` in `upload_file()` (line 112)
- Changed `await db.commit()` to `await db.flush()` in `process_document()` (line 220 & 230)
- Added better logging with chunk counts

### 2. main.py (upload endpoint)
- Added explicit `await db.commit()` after all operations succeed (line 230)
- Added explicit `await db.rollback()` on error (line 264)
- Added detailed logging at each step
- Added `chunks_created` to response for verification

### 3. database.py
- Removed auto-commit from `get_db()` dependency
- Endpoints now handle commits explicitly for better control

## How to Test

### 1. Restart Backend

```bash
# Rebuild and restart backend to load the changes
docker compose down
docker compose up -d --build backend
```

### 2. Run the Test Script

```bash
# Test document upload
./test-upload-endpoint.sh
```

### 3. Expected Results (AFTER FIX)

```
✓ Upload endpoint working!
Checking database...
Documents: 1
Chunks: > 0 (depending on file size)
Session documents: 1 (if session_id provided)

✓ Document uploaded AND processed successfully!
```

### 4. Verify Response Includes Chunks

The API response should now include:
```json
{
  "success": true,
  "document_id": "...",
  "filename": "...",
  "chunks_created": 5,  // <-- NEW FIELD
  "message": "File uploaded and processed successfully"
}
```

### 5. Check Backend Logs

```bash
# Watch backend logs for detailed processing info
docker compose logs -f backend

# Look for these log lines:
# - "Document created: <id> - <filename>"
# - "Document processed: X chunks created"
# - "Transaction committed for document <id>"
```

## What Was Fixed

✅ **Atomic Transactions**: All operations (document creation + chunk creation + session association) now happen in a single transaction
✅ **Proper Rollback**: If any step fails, the entire transaction rolls back cleanly
✅ **Better Logging**: Detailed logs at each step for debugging
✅ **Verification**: Response includes chunk count to confirm processing

## Testing Different Scenarios

### Test 1: Successful Upload
```bash
./test-upload-endpoint.sh
# Should see: Documents: 1, Chunks: >0
```

### Test 2: Large File Upload
```bash
# Create a larger test file
echo "Lorem ipsum dolor sit amet..." > /tmp/large-test.txt
for i in {1..100}; do cat /tmp/large-test.txt >> /tmp/large-test.txt; done

# Upload it
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@/tmp/large-test.txt" \
  -F "session_id=test-session-123"
```

### Test 3: Check Database Directly
```bash
# If you have psql access
docker compose exec postgres psql -U postgres -d chatbot -c \
  "SELECT id, filename, processed, upload_date FROM documents ORDER BY upload_date DESC LIMIT 5;"

docker compose exec postgres psql -U postgres -d chatbot -c \
  "SELECT document_id, COUNT(*) as chunks FROM document_chunks GROUP BY document_id;"
```

## Rollback Plan

If the fix causes issues:

```bash
# Revert the commit
git revert c202688

# Push the revert
git push origin claude/enterprise-rag-chatbot-stack-011CV55YJHaUYhTQVqsEU4iK

# Rebuild backend
docker compose down
docker compose up -d --build backend
```

## Additional Notes

- The fix maintains backward compatibility with existing code
- Audit logging is handled in a separate transaction to ensure it persists even if not critical
- The get_db dependency still handles rollback on exceptions
- Explicit commits give better control over transaction boundaries
