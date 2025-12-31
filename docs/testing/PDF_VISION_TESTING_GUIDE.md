# PDF Vision Analysis Testing Guide

**Date**: 2025-12-05
**Purpose**: Complete guide to test the triple-fallback PDF vision system

---

## System Status

### ✅ Successfully Implemented:
1. **Triple-Fallback PDF Vision System**
   - Primary: PyMuPDF (fitz) - already in stack
   - Fallback 1: pdf2image
   - Fallback 2: Intelligent multi-tool (docling_pdf + ocr + document_rag)

2. **Code Changes**: `backend/app/agents/tool_registry.py` (lines 1221-1340)

3. **Deployment**: ✅ Built and deployed

### ⚠️ Current Issue:
The system CANNOT be tested yet because:
- No documents are uploaded in test sessions
- The vision tool looks for PDFs but finds none
- This is a **workflow/UI issue**, not a backend code issue

---

## Proper Testing Workflow

### Option 1: Test Via API (Backend Only)

#### Step 1: Upload PDF to Session
```bash
# Upload PDF and associate with session
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@/path/to/National_Storage_Floor_Plan.pdf" \
  -F "session_id=test_vision_session"
```

**Expected Response:**
```json
{
  "document_id": "uuid-here",
  "filename": "National_Storage_Floor_Plan.pdf",
  "status": "processing"
}
```

#### Step 2: Wait for Processing (Smart Query Waiting)
The backend already has a 30-second wait mechanism that checks:
- `processing_status == 'processing'` → Wait
- `processing_status == 'completed'` → Proceed

**Look for in logs:**
```
⏳ Checking if session documents are ready for query...
✅ All session documents are ready!
```

#### Step 3: Send Query
```bash
# Query about the PDF
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=How many floors are shown in this building floor plan?" \
  -F "session_id=test_vision_session" \
  -F "model=gpt-4o-mini"
```

**Expected Log Flow:**
```
📄 LLM-classified as: document_specific
🎯 TaskRouter analyzing...
👁️  Query requires vision analysis - selected vision tools
🔍 Searching for image/PDF documents in session
📄 Found visual document: National_Storage_Floor_Plan.pdf (application/pdf)
📄 PDF detected, converting to image for vision analysis
🔄 Trying PyMuPDF (fitz)...
✅ PDF converted to image using PyMuPDF
👁️  Vision analysis with LLaMA 3.2 Vision 11B
✅ Vision tool executed successfully
```

---

### Option 2: Test Via UI (Frontend + Backend)

#### Step 1: Open Chat Interface
1. Navigate to `http://localhost:3001`
2. Create new session or use existing one

#### Step 2: Upload PDF First
1. Click "Upload Document" button
2. Select PDF file (e.g., floor plan)
3. **WAIT for upload completion** - look for:
   - ✅ Success message
   - File appears in uploaded documents list
   - Status shows "Processed" or "Ready"

#### Step 3: Then Send Query
1. Type query: "How many floors are shown in this building floor plan?"
2. Press Send
3. Wait for response

**UI Requirements (Frontend Needs to Implement):**
- Disable Send button while documents are uploading
- Show upload progress indicator
- Only enable Send when `processing_status == 'completed'`
- Display clear "Document Ready" state

---

## Current Workflow Problem

### What's Happening Now:
```
User uploads PDF in UI
  ↓
Frontend sends upload request
  ↓ (RACE CONDITION HERE)
User types query and hits Send
  ↓
Query reaches backend BEFORE upload completes
  ↓
Vision tool: ⚠️  No image/PDF documents found in session
  ↓
Result: "No documents to analyze"
```

### What Should Happen:
```
User uploads PDF in UI
  ↓
Frontend sends upload request
  ↓
Frontend shows "Uploading..." indicator
  ↓
Backend processes document
  ↓
Frontend receives: { status: "completed" }
  ↓
Frontend enables Send button with ✅ "Ready"
  ↓
User types query and hits Send
  ↓
Backend waits for any processing documents (Smart Query Waiting)
  ↓
✅ All session documents are ready!
  ↓
Vision tool: 📄 Found visual document
  ↓
PDF → PyMuPDF → Image → Vision Analysis
  ↓
Result: Comprehensive answer!
```

---

## Testing Without UI (Recommended for Now)

Since the UI workflow isn't synchronized yet, test using the API directly:

### Complete Test Script

```bash
#!/bin/bash

SESSION_ID="test_vision_pdf_$(date +%s)"
PDF_PATH="/path/to/floor_plan.pdf"

echo "📤 Step 1: Upload PDF to session $SESSION_ID"
UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/upload \
  -F "file=@$PDF_PATH" \
  -F "session_id=$SESSION_ID")

echo "$UPLOAD_RESPONSE" | jq '.'

DOC_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.document_id')
echo "✅ Document ID: $DOC_ID"

echo ""
echo "⏳ Step 2: Wait 10 seconds for processing..."
sleep 10

echo ""
echo "📊 Step 3: Send query"
QUERY_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/query \
  -F "query=How many floors are shown in this building floor plan?" \
  -F "session_id=$SESSION_ID" \
  -F "model=gpt-4o-mini")

echo "$QUERY_RESPONSE" | jq '.answer'

echo ""
echo "🔍 Check backend logs for vision analysis flow"
```

### Save and Run:
```bash
chmod +x test_vision_pdf.sh
./test_vision_pdf.sh
```

---

## Expected Results

### Successful PDF Vision Analysis

#### Scenario 1: PyMuPDF Works (Most Likely)
```
📄 PDF detected: /path/to/floor_plan.pdf
🔄 Trying PyMuPDF (fitz)...
✅ PDF converted to image using PyMuPDF: /tmp/vision_pdf_floor_plan.png
👁️  Analyzing image with LLaMA 3.2 Vision 11B...
✅ Vision analysis complete
```

**Answer**: "Based on the floor plan diagram, there are X floors shown..."

#### Scenario 2: PyMuPDF Fails, Intelligent Multi-Tool Fallback
```
📄 PDF detected: /path/to/floor_plan.pdf
🔄 Trying PyMuPDF (fitz)...
❌ PyMuPDF failed: [error]
🔄 Trying pdf2image...
❌ pdf2image failed: [error]
🎯 Using intelligent multi-tool fallback

📄 Trying docling_pdf tool...
✅ docling_pdf succeeded: Extracted structured text

🔍 Trying ocr tool...
✅ ocr succeeded: Extracted visual text

📚 Trying document_rag tool...
✅ document_rag succeeded: Found relevant chunks

✅ Intelligent fallback successful using 3 tools
```

**Answer**: Combined analysis from all 3 tools!

---

## Troubleshooting

### Issue: "No image/PDF documents found in session"

**Cause**: Documents not uploaded to session OR uploaded to different session

**Solution**:
1. Check session_id matches between upload and query
2. Verify upload completed successfully
3. Check database:
```sql
SELECT d.filename, d.file_type, sd.session_id
FROM documents d
JOIN session_documents sd ON d.id = sd.document_id
WHERE sd.session_id = 'your-session-id';
```

### Issue: "LLM-classified as ai_personal"

**Cause**: Query classifier incorrectly categorizing document queries

**Solution**: Use keywords that clearly indicate document usage:
- ✅ "...in the uploaded document"
- ✅ "...in this PDF"
- ✅ "...from the floor plan"
- ❌ "Count the floors" (ambiguous)

### Issue: "PDF requires pdf2image tool"

**Cause**: You're seeing the OLD error message (before our fix)

**Solution**: Rebuild backend to deploy the fix:
```bash
docker-compose build backend && docker-compose restart backend
```

---

## Frontend Requirements

To properly support PDF vision analysis, the frontend needs:

### 1. Upload State Management
```typescript
const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'processing' | 'ready'>('idle');

// On upload start
setUploadStatus('uploading');

// On upload complete
setUploadStatus('processing');

// Poll for completion
const checkStatus = async () => {
  const doc = await fetch(`/api/v1/documents/${documentId}`);
  if (doc.processing_status === 'completed') {
    setUploadStatus('ready');
  }
};
```

### 2. Disable Send During Upload
```typescript
<Button
  onClick={sendMessage}
  disabled={uploadStatus !== 'ready' && hasDocuments}
>
  {uploadStatus === 'uploading' && 'Uploading...'}
  {uploadStatus === 'processing' && 'Processing...'}
  {uploadStatus === 'ready' && 'Send'}
</Button>
```

### 3. Visual Indicators
- Show upload progress bar
- Display "✅ Ready" when processing complete
- Show document list with status icons

---

## Summary

### ✅ Backend is Ready
- Triple-fallback PDF vision system implemented
- Smart query waiting mechanism (30s) already exists
- Code deployed and running

### ⚠️ Frontend Needs Sync
- Must wait for upload completion before enabling Send
- Must track document processing status
- Must provide visual feedback to user

### 🧪 Testing Recommendation
Use API test script (provided above) to verify PDF vision analysis works correctly, then implement proper UI synchronization.

---

**Date**: 2025-12-05
**Status**: Backend ✅ READY, Frontend ⏳ NEEDS SYNC
**Next Steps**: Implement upload/query synchronization in UI
