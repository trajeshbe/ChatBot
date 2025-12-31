# Frontend Upload/Query Synchronization Fix

**Date**: 2025-12-05
**Issue**: Race condition where queries are sent before document upload/processing completes
**Solution**: Add processing status polling after upload before allowing query

---

## Problem Analysis

### Current Flow (BROKEN):
```
User uploads PDF
  ↓
Frontend: uploadAttachedFiles() → POST /api/v1/upload
  ↓
Backend: Returns { success: true, document_id: "..." }
  ↓
Frontend: Immediately proceeds to send query ❌
  ↓
Backend (in parallel): Processing document...
  ↓
Query arrives → Vision tool: "No documents found"
```

### What Should Happen:
```
User uploads PDF
  ↓
Frontend: uploadAttachedFiles() → POST /api/v1/upload
  ↓
Backend: Returns { success: true, document_id: "uuid", processing_status: "processing" }
  ↓
Frontend: Poll document status every 1 second
  ↓
Backend: { processing_status: "processing" } ... wait ...
  ↓
Backend: { processing_status: "completed" } ✅
  ↓
Frontend: NOW send query
  ↓
Backend: Smart Query Waiting (30s) checks status
  ↓
Vision tool: "Found PDF!" → PyMuPDF → Vision Analysis ✅
```

---

## Solution: Add Poll-for-Completion Logic

### File to Modify
`frontend/src/components/ChatInterfaceEnhanced.tsx`

### Changes Needed

#### 1. Add Helper Function: Wait for Document Processing

Add this function after `uploadAttachedFiles` (around line 803):

```typescript
// Poll document status until processing is complete
const waitForDocumentProcessing = async (
  documentIds: string[],
  maxWaitSeconds = 30
): Promise<boolean> => {
  const startTime = Date.now()
  const pollIntervalMs = 1000 // Check every 1 second

  console.log(`⏳ Waiting for ${documentIds.length} documents to finish processing...`)

  while ((Date.now() - startTime) / 1000 < maxWaitSeconds) {
    try {
      // Check status of all uploaded documents
      const statusChecks = await Promise.all(
        documentIds.map(docId =>
          axios.get(`${API_URL}/api/v1/documents/${docId}/status`)
        )
      )

      const allCompleted = statusChecks.every(response =>
        response.data.processing_status === 'completed'
      )

      if (allCompleted) {
        console.log(`✅ All ${documentIds.length} documents processing complete!`)
        return true
      }

      // Check if any failed
      const anyFailed = statusChecks.some(response =>
        response.data.processing_status === 'failed'
      )

      if (anyFailed) {
        console.error(`❌ Some documents failed to process`)
        return false
      }

      // Still processing, wait and try again
      console.log(`⏳ Still processing... (${Math.floor((Date.now() - startTime) / 1000)}s elapsed)`)
      await new Promise(resolve => setTimeout(resolve, pollIntervalMs))

    } catch (error) {
      console.error('Error checking document status:', error)
      // Continue polling even if status check fails
      await new Promise(resolve => setTimeout(resolve, pollIntervalMs))
    }
  }

  console.warn(`⚠️  Timeout waiting for document processing after ${maxWaitSeconds}s`)
  return false
}
```

#### 2. Update `uploadAttachedFiles` to Track Document IDs

Modify lines 754-802 to collect document IDs:

```typescript
const uploadAttachedFiles = async (): Promise<{
  success: boolean
  duplicates: string[]
  documentIds: string[]  // 🆕 Return document IDs
}> => {
  if (attachedFiles.length === 0) return { success: true, duplicates: [], documentIds: [] }

  setUploadingFiles(true)
  const duplicates: string[] = []
  const documentIds: string[] = []  // 🆕 Track uploaded document IDs
  let hasErrors = false

  try {
    for (const file of attachedFiles) {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('session_id', sessionId)

      const globalProject = availableProjects.find(p => p.name.toLowerCase() === 'global')
      const activeProjectId = selectedProjectId || projectId || globalProject?.id || ''
      formData.append('project_id', activeProjectId)

      const token = localStorage.getItem('access_token')

      const response = await axios.post(`${API_URL}/api/v1/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        }
      })

      if (response.data.duplicate || !response.data.success) {
        duplicates.push(file.name)
        console.log(`⚠️  Duplicate file skipped: ${file.name}`)
      } else {
        // 🆕 Collect document ID for status polling
        if (response.data.document_id) {
          documentIds.push(response.data.document_id)
        }
        console.log(`✅ Uploaded ${file.name} to session ${sessionId}`)
      }
    }
    setAttachedFiles([])
    setFilesJustUploaded(true)
    return { success: !hasErrors, duplicates, documentIds }  // 🆕 Return IDs
  } catch (error) {
    console.error('Error uploading files:', error)
    hasErrors = true
    return { success: false, duplicates, documentIds }
  } finally {
    setUploadingFiles(false)
  }
}
```

#### 3. Update `handleSendMessage` to Wait for Processing

Modify lines 807-838 to poll for completion:

```typescript
const handleSendMessage = async () => {
  if ((!input.trim() && attachedFiles.length === 0) || isLoading) return

  // 🎯 SMART UPLOAD SYNC: Upload files AND wait for processing
  if (attachedFiles.length > 0) {
    const uploadResult = await uploadAttachedFiles()

    if (!uploadResult.success) {
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, there was an error uploading your files. Please try again.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
      return
    }

    // 🆕 WAIT FOR PROCESSING TO COMPLETE before sending query
    if (uploadResult.documentIds.length > 0 && input.trim()) {
      // Show "processing" indicator to user
      setIsLoading(true)

      const processingComplete = await waitForDocumentProcessing(
        uploadResult.documentIds,
        30 // Wait up to 30 seconds
      )

      setIsLoading(false)

      if (!processingComplete) {
        const warningMessage: Message = {
          role: 'assistant',
          content: 'Warning: Document processing is taking longer than expected. Your query may not have access to all document content yet. You can try asking again in a few moments.',
          timestamp: new Date()
        }
        setMessages(prev => [...prev, warningMessage])
        // Continue with query anyway - backend has its own 30s wait
      } else {
        console.log('✅ Documents ready, proceeding with query')
      }
    }

    // If only files were attached without a message, show success
    if (!input.trim()) {
      let successContent = 'Files uploaded and processed successfully! You can now ask questions about them.'

      if (uploadResult.duplicates.length > 0) {
        successContent += `\n\n**Note:** The following files were already uploaded:\n${uploadResult.duplicates.map(f => `- ${f}`).join('\n')}`
      }

      const successMessage: Message = {
        role: 'assistant',
        content: successContent,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, successMessage])
      return
    }
  }

  // Continue with normal query flow...
  const userMessage: Message = {
    role: 'user',
    content: input,
    timestamp: new Date()
  }

  setMessages(prev => [...prev, userMessage])
  setInput('')
  setIsLoading(true)

  // ... rest of query logic (unchanged)
```

---

## Backend Endpoint Needed

### Add Document Status Check Endpoint

**File**: `backend/app/main.py` or `backend/app/api/routes/`

Add this endpoint:

```python
@app.get("/api/v1/documents/{document_id}/status")
async def get_document_status(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get processing status of a document

    Returns:
        - processing_status: "processing", "completed", "failed"
        - filename: str
        - error_message: str (if failed)
    """
    from app.models.database import Document
    from sqlalchemy import select
    from uuid import UUID

    try:
        doc_uuid = UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")

    result = await db.execute(
        select(Document).where(Document.id == doc_uuid)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "document_id": str(document.id),
        "filename": document.filename,
        "processing_status": document.processing_status,
        "error_message": document.error_message
    }
```

---

## Alternative: Simpler Approach Using Fixed Delay

If you don't want to add the status endpoint, use a fixed delay after upload:

```typescript
// After uploadAttachedFiles() in handleSendMessage
if (uploadResult.documentIds.length > 0 && input.trim()) {
  // Simple approach: Wait 10 seconds for processing
  console.log('⏳ Waiting 10s for document processing...')
  setIsLoading(true)

  await new Promise(resolve => setTimeout(resolve, 10000))

  setIsLoading(false)
  console.log('✅ Proceeding with query')
}
```

**Pros**: Simple, no backend changes needed
**Cons**:
- May wait too long for small files
- May not wait long enough for large files
- Less user-friendly (no progress indication)

---

## UI Improvements

### Show Processing Status in UI

Add visual indicators for upload states:

```typescript
// Add state for upload status
const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'processing' | 'ready'>('idle')

// Update during upload flow
const handleSendMessage = async () => {
  if (attachedFiles.length > 0) {
    setUploadStatus('uploading')
    const uploadResult = await uploadAttachedFiles()

    if (uploadResult.documentIds.length > 0) {
      setUploadStatus('processing')
      await waitForDocumentProcessing(uploadResult.documentIds)
      setUploadStatus('ready')
    }
  }

  // ... rest of logic
}

// Update Send button UI
<Button
  onClick={handleSendMessage}
  disabled={isLoading || uploadStatus === 'uploading' || uploadStatus === 'processing'}
>
  {uploadStatus === 'uploading' && (
    <><Loader2 className="animate-spin mr-2" /> Uploading...</>
  )}
  {uploadStatus === 'processing' && (
    <><Loader2 className="animate-spin mr-2" /> Processing...</>
  )}
  {uploadStatus === 'ready' && 'Send ✅'}
  {uploadStatus === 'idle' && <><Send /> Send</>}
</Button>
```

---

## Testing

### Test Scenario 1: Upload with Query (Main Fix)
1. Attach PDF file
2. Type query: "How many floors in this building?"
3. Click Send
4. **Expected**:
   - Shows "Uploading..." (1-2s)
   - Shows "Processing..." (5-10s)
   - Then sends query
   - Backend finds document and analyzes it

### Test Scenario 2: Upload without Query
1. Attach PDF file
2. Click Send (without typing anything)
3. **Expected**:
   - Uploads and processes
   - Shows success message
   - Can then type query and send

### Test Scenario 3: Query without Upload
1. Type query without attaching files
2. Click Send
3. **Expected**:
   - Sends immediately (no waiting)
   - Works for RAG queries or direct LLM

---

## Summary

### Changes Required:

#### Frontend (`ChatInterfaceEnhanced.tsx`):
1. ✅ Add `waitForDocumentProcessing()` helper function
2. ✅ Update `uploadAttachedFiles()` to return document IDs
3. ✅ Update `handleSendMessage()` to poll for completion before sending query
4. ✅ Add UI indicators for upload/processing states (optional but recommended)

#### Backend (Optional but Recommended):
1. ✅ Add GET `/api/v1/documents/{id}/status` endpoint for polling
2. ✅ Ensure upload response includes `document_id`

### Benefits:
- ✅ **No race conditions** - query only sent after documents ready
- ✅ **Works for all file types** - PDFs, images, Word, PowerPoint
- ✅ **User-friendly** - clear status indicators
- ✅ **Backward compatible** - queries without files work immediately
- ✅ **Robust** - uses backend's existing 30s wait as additional safety net

### User Experience:
```
Before Fix:
  Upload PDF → Send query immediately → "No documents found" ❌

After Fix:
  Upload PDF → [Uploading... 2s] → [Processing... 8s] → ✅ Ready! → Send query → Vision analysis works! ✅
```

---

**Date**: 2025-12-05
**Status**: Implementation guide ready
**Priority**: HIGH - Blocks PDF vision analysis feature
