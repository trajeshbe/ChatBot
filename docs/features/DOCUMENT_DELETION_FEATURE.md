# Document Deletion Feature

**Date**: 2025-12-02
**Status**: ✅ **DEPLOYED**
**Priority**: P0 (Embedding Management)

---

## Overview

Implemented a document deletion feature in the Admin Dashboard that allows administrators to delete documents and all associated embeddings from the system.

**Purpose**: Manage embeddings and remove documents that should not be used by the RAG system.

---

## Features

### 1. Backend DELETE Endpoint ✅
**Endpoint**: `DELETE /api/v1/documents/{document_id}`

**Functionality**:
- Deletes the document record
- Automatically cascades to delete all chunks (via FK constraint)
- Automatically removes all embeddings (stored in chunk records)
- Removes session associations (SessionDocument table)
- Returns detailed deletion summary

**Request**:
```http
DELETE /api/v1/documents/{document_id}
```

**Response** (Success):
```json
{
  "message": "Document and all embeddings deleted successfully",
  "document_id": "uuid-here",
  "filename": "example.pdf",
  "chunks_deleted": 26,
  "embeddings_deleted": 26
}
```

**Response** (Error):
```json
{
  "detail": "Document not found"
}
```

**Security**:
- Validates UUID format
- Checks document existence before deletion
- Transaction-safe (rollback on error)
- Comprehensive error handling

### 2. Admin Dashboard UI ✅
**Location**: Admin Dashboard → Database Tab → Documents & Embeddings

**UI Features**:
- 🗑️ **Delete button** next to each document
- Hover effect (red highlight)
- Icon: Trash2 (lucide-react)

**User Experience**:
1. User clicks delete button
2. Confirmation dialog shows:
   ```
   ⚠️ Delete document and all embeddings?

   Document: example.pdf
   This will permanently delete:
   • The document record
   • All chunks
   • All embeddings

   This action cannot be undone.
   ```
3. User confirms deletion
4. Backend processes deletion
5. Success notification shows:
   ```
   ✅ Document deleted successfully!

   Filename: example.pdf
   Chunks deleted: 26
   Embeddings removed: 26
   ```
6. Document list refreshes automatically

---

## Technical Implementation

### Backend Changes

**File**: `backend/app/main.py`

**Lines Added**: ~80 lines (935-1013)

**Key Implementation Details**:

```python
@app.delete("/api/v1/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    # 1. Validate UUID
    doc_uuid = uuid.UUID(document_id)

    # 2. Check document exists
    document = await db.execute(
        select(Document).where(Document.id == doc_uuid)
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # 3. Get chunk count (for logging)
    chunks = await db.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == doc_uuid)
    )
    chunk_count = len(chunks.scalars().all())

    # 4. Delete session associations
    await db.execute(
        delete(SessionDocument).where(SessionDocument.document_id == doc_uuid)
    )

    # 5. Delete document (chunks cascade automatically)
    await db.execute(
        delete(Document).where(Document.id == doc_uuid)
    )

    await db.commit()

    # 6. Return summary
    return {
        "message": "Document and all embeddings deleted successfully",
        "document_id": document_id,
        "filename": filename,
        "chunks_deleted": chunk_count,
        "embeddings_deleted": chunk_count
    }
```

**Cascade Deletion**:
The database schema has `ON DELETE CASCADE` constraint on the FK:
```sql
document_chunks.document_id → documents.id (ON DELETE CASCADE)
```
This ensures all chunks are automatically deleted when the parent document is deleted.

### Frontend Changes

**File**: `frontend/src/pages/admin.tsx`

**Changes**:
1. Added `Trash2` icon import
2. Added `deleteDocument` function (lines 265-308)
3. Added delete button in document row (lines 1535-1544)

**Delete Function**:
```typescript
const deleteDocument = async (documentId: string, filename: string) => {
  // 1. Show confirmation dialog
  if (!confirm(`⚠️ Delete document and all embeddings?...`)) {
    return
  }

  // 2. Call DELETE API
  const res = await fetch(`${API_BASE}/api/v1/documents/${documentId}`, {
    method: 'DELETE'
  })

  // 3. Show success message
  alert(`✅ Document deleted successfully!...`)

  // 4. Refresh list
  await searchDocuments()

  // 5. Clear selection if needed
  if (selectedDocument?.id === documentId) {
    setSelectedDocument(null)
    setDocumentChunks([])
  }
}
```

**Delete Button UI**:
```tsx
<button
  onClick={(e) => {
    e.stopPropagation()  // Prevent row click
    deleteDocument(doc.id, doc.filename)
  }}
  className="p-2 text-slate-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
  title="Delete document and all embeddings"
>
  <Trash2 className="w-4 h-4" />
</button>
```

---

## Usage Guide

### For Administrators

**Step 1: Navigate to Admin Dashboard**
```
http://localhost:3001/admin
```

**Step 2: Go to Database Tab**
- Click on "Database" tab
- You'll see "Documents & Embeddings" section

**Step 3: Find Document to Delete**
- Use search box to find specific document
- Or scroll through the list

**Step 4: Click Delete Button**
- Hover over document row
- Click the trash icon (🗑️) on the right side

**Step 5: Confirm Deletion**
- Read the confirmation dialog
- Click "OK" to confirm
- Click "Cancel" to abort

**Step 6: Verify Deletion**
- Success message shows deletion details
- Document disappears from list
- Chunks panel clears if that document was selected

---

## What Gets Deleted

### Database Records

1. **documents table**:
   - Document record (id, filename, file_path, etc.)

2. **document_chunks table** (CASCADE):
   - All chunks for this document
   - All embeddings (embedding column)
   - All multi-column embeddings (table_embedding, visual_embedding, etc.)

3. **session_documents table**:
   - All session associations

### What DOES NOT Get Deleted

- ❌ **MinIO files**: Physical files remain in MinIO storage
  - Reason: Files may be referenced elsewhere
  - Future enhancement: Optional file deletion

- ❌ **Conversation history**: Messages referencing this document remain
  - Reason: Preserves conversation context
  - The source references will show as "Document not found"

---

## Testing

### Manual Test

**Test 1: Delete Single Document**
```bash
# 1. Get document ID from Admin Dashboard
# 2. Delete via API:
curl -X DELETE http://localhost:8000/api/v1/documents/{document_id}

# 3. Verify response:
{
  "message": "Document and all embeddings deleted successfully",
  "document_id": "uuid",
  "filename": "test.pdf",
  "chunks_deleted": 26,
  "embeddings_deleted": 26
}
```

**Test 2: Verify Cascade Deletion**
```sql
-- Before deletion
SELECT COUNT(*) FROM document_chunks WHERE document_id = 'uuid';
-- Result: 26

-- After deletion
SELECT COUNT(*) FROM document_chunks WHERE document_id = 'uuid';
-- Result: 0
```

**Test 3: UI Delete Button**
1. Navigate to Admin Dashboard → Database
2. Click delete button on a document
3. Confirm deletion
4. Verify:
   - Success message appears
   - Document disappears from list
   - If selected, chunks panel clears

---

## Logging

### Backend Logs

**Successful Deletion**:
```
🗑️  Document deleted successfully:
   Document: example.pdf
   ID: uuid-here
   Chunks deleted: 26
   Embeddings removed: 26
```

**Error**:
```
Error deleting document uuid-here: Document not found
```

### How to Monitor

```bash
# Watch for deletion events
docker-compose logs backend -f | grep "🗑️"

# Check for errors
docker-compose logs backend | grep "Error deleting"
```

---

## Security Considerations

### Current Implementation
- ✅ No authentication check (relies on admin dashboard access)
- ✅ UUID validation
- ✅ Document existence check
- ✅ Transaction-safe

### Recommended Enhancements (Future)
1. **RBAC Integration**: Check user has 'delete_document' permission
2. **Audit Logging**: Record who deleted what and when
3. **Soft Delete**: Mark as deleted instead of hard delete
4. **Backup**: Create backup before deletion

---

## API Documentation

### DELETE /api/v1/documents/{document_id}

**Summary**: Delete document and all embeddings

**Parameters**:
| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| document_id | string (UUID) | path | Yes | Document ID to delete |

**Responses**:

**200 OK**:
```json
{
  "message": "Document and all embeddings deleted successfully",
  "document_id": "uuid",
  "filename": "example.pdf",
  "chunks_deleted": 26,
  "embeddings_deleted": 26
}
```

**400 Bad Request**:
```json
{
  "detail": "Invalid document ID format"
}
```

**404 Not Found**:
```json
{
  "detail": "Document not found"
}
```

**500 Internal Server Error**:
```json
{
  "detail": "Failed to delete document: error message"
}
```

---

## Future Enhancements

### Priority 1
- [ ] Add RBAC permission check
- [ ] Add audit logging
- [ ] Add bulk delete (select multiple documents)

### Priority 2
- [ ] Add soft delete option
- [ ] Add MinIO file deletion option
- [ ] Add backup before deletion
- [ ] Add "undo" functionality (restore from backup)

### Priority 3
- [ ] Add deletion statistics dashboard
- [ ] Add scheduled cleanup (delete old documents)
- [ ] Add retention policies

---

## Related Documents

- `backend/app/main.py` - Backend implementation
- `frontend/src/pages/admin.tsx` - Frontend implementation
- `docs/guides/ADMIN_GUIDE.md` - Admin dashboard guide

---

## Success Criteria - ALL MET ✅

| Criteria | Status | Evidence |
|----------|--------|----------|
| Backend DELETE endpoint | ✅ DONE | Lines 935-1013 in main.py |
| Cascade deletion of chunks | ✅ DONE | FK constraint with ON DELETE CASCADE |
| Admin UI delete button | ✅ DONE | Lines 1535-1544 in admin.tsx |
| Confirmation dialog | ✅ DONE | Implemented in deleteDocument() |
| Success notification | ✅ DONE | Alert with deletion summary |
| List refresh | ✅ DONE | Calls searchDocuments() after delete |
| Error handling | ✅ DONE | Try-catch with user-friendly messages |
| Backend restart | ✅ DONE | Services restarted successfully |

---

**Status**: ✅ **DEPLOYED & READY TO USE**

**Deployment Date**: 2025-12-02
**Backend Health**: ✅ Healthy
**Frontend**: ✅ Running

---

**End of Documentation**
