# Testing New Features - Complete Guide

## ✅ What's Been Implemented (Commit `9b875f1`)

### Frontend Features
1. ✅ **Uploaded Files List** - Shows documents in current session
2. ✅ **Clear Session Button** - Restart conversation from scratch
3. ✅ **Username & Session Display** - Shows in home page header

### Backend API Endpoints
1. ✅ `GET /api/v1/sessions/{session_id}/documents`
2. ✅ `DELETE /api/v1/documents/{document_id}`
3. ✅ `POST /api/v1/sessions/{session_id}/clear`
4. ✅ `GET /api/v1/admin/documents`
5. ✅ `POST /api/v1/admin/users`

---

## 🚨 CRITICAL: Why Your Documents Aren't Working

### The Problem You're Experiencing

You uploaded a document but when you ask "Who is Aadhan?", you get generic answers about Islamic prayer instead of answers from your document.

### Root Cause

**The database tables didn't exist when you uploaded your document!**

Looking at your error:
```
ERROR:  relation "documents" does not exist
```

This means:
1. You uploaded the file → Stored in MinIO ✅
2. Backend tried to save to `documents` table → **Failed** ❌
3. Backend tried to chunk and embed → **Failed** ❌
4. No entries in `document_chunks` table → **Not searchable** ❌

**Result:** File is in MinIO but NOT in the database, so queries can't find it.

---

## 🔧 FIX: Complete Setup Process

### Step 1: Create Database Tables

```bash
./setup-database.sh
```

**What this does:**
- Creates `documents` table (base schema)
- Creates `document_chunks` table (for embeddings)
- Creates `session_documents` table (for short-term memory)
- Creates all enhanced tables (users, sessions, audit logs)

**Expected output:**
```
✓ Base schema applied
✓ Enhanced schema applied
Database tables created:
  documents
  document_chunks
  session_documents
  chat_sessions
  ... (15+ tables total)
```

### Step 2: Restart Services

```bash
docker compose down
docker compose up -d --build

# Wait for services to start
sleep 15
```

### Step 3: Verify Backend is Healthy

```bash
# Check backend logs
docker compose logs backend | tail -30

# Should see:
# ✓ Using Enhanced RAG Service with memory hierarchy
# ✓ Audit service loaded
# Server started successfully
```

### Step 4: Re-Upload Your Document

**IMPORTANT:** Documents uploaded BEFORE the database fix won't work. You must re-upload!

1. Open `http://localhost:3001`
2. Click the paperclip button (📎)
3. Select your file (e.g., "Short Story.txt" about Aadhan)
4. Click Send

**Check browser console (F12):**
```
🆔 Created new session: session-1234567890-abc123
✅ Uploaded Short Story.txt to session session-1234567890-abc123
```

### Step 5: Wait for Processing (10-15 seconds)

The document needs to be:
1. Saved to database
2. Chunked into smaller pieces
3. Embeddings generated
4. Stored in `document_chunks` table

**Check if it's done:**
```bash
./diagnose-documents.sh
```

**Expected output:**
```
Total documents: 1
Total chunks (embeddings): 15  ← Should be > 0!
Documents in sessions: 1
✅ Documents are being processed and linked to sessions!
```

### Step 6: Test Query

**Ask:** `"Who is Aadhan?"`

**Expected Response:**
```
Based on the uploaded document, Aadhan is a character in the story who...
```

**Browser console should show:**
```
📤 Querying with session session-... and 0 context messages
```

**Backend logs should show:**
```
Found 3 chunks in short-term memory
Found 5 chunks in long-term memory
```

---

## 🧪 Testing New Features

### Feature 1: Uploaded Files List

**Where:** Below the chat messages, above the input box

**What to test:**
1. Upload a file → Should appear in the list immediately
2. Shows file size, chunk count, embedding status
3. Green checkmark if embedded (✓ 15 chunks)
4. Yellow hourglass if still processing (⏳ Processing...)
5. Click trash icon → Confirms and deletes document
6. Click refresh icon → Reloads list

**Expected UI:**
```
┌─────────────────────────────────────┐
│ 📄 Uploaded Documents (1)     🔄    │
├─────────────────────────────────────┤
│ 📄 Short Story.txt                  │
│ 15.2 KB • 2m ago • ✓ 15 chunks  🗑 │
└─────────────────────────────────────┘
```

### Feature 2: Clear Session Button

**Where:** Top right of chat interface (red button next to message count)

**What to test:**
1. Upload files and chat
2. Click "Clear Session"
3. Confirms with warning about what will be cleared
4. After clearing:
   - All messages removed
   - New session ID generated
   - Uploaded files list empty
   - Can start fresh

**Browser console:**
```
🧹 Cleared session: session-old-id
🆕 New session started: session-new-id
```

### Feature 3: Username & Session Display

**Where:** Top right of home page header

**What to test:**
1. Shows "Anonymous" by default
2. Shows session ID (first 16 characters)
3. Set username:
   ```javascript
   // In browser console:
   localStorage.setItem('username', 'John Doe')
   // Refresh page
   ```
4. Should now show "John Doe" instead of "Anonymous"

**Expected UI:**
```
┌─────────────────────────────────────┐
│ Enterprise RAG Chatbot              │
│                    👤 John Doe       │
│                    Session: session-│
│                    1234567890...     │
└─────────────────────────────────────┘
```

### Feature 4: Session Persistence

**What to test:**
1. Upload a document
2. Ask questions about it
3. Refresh the page (F5)
4. Session ID should be the same
5. Uploaded files list should still show documents
6. Continue asking questions → Should still reference the document

**Why this works:**
- Session ID stored in `sessionStorage`
- Documents linked to session in database
- Conversation history sent with each query

### Feature 5: Document Deletion

**What to test:**
1. Upload 2-3 documents
2. Ask questions using all documents
3. Delete one document from the list
4. Ask the same question again
5. Should only reference remaining documents

---

## 🐛 Troubleshooting

### Issue: Documents Still Not Found in Queries

**Check 1: Are documents actually chunked?**
```bash
docker exec rag-postgres psql -U postgres -d rag_chatbot -c \
  "SELECT d.filename, COUNT(dc.id) as chunks
   FROM documents d
   LEFT JOIN document_chunks dc ON d.id = dc.document_id
   GROUP BY d.filename;"
```

**Expected:**
```
    filename     | chunks
-----------------+--------
 Short Story.txt |   15
```

**If chunks = 0:**
- Document wasn't processed correctly
- Check backend logs: `docker compose logs backend | grep -i "process\|error"`
- Delete and re-upload the document

**Check 2: Is session association working?**
```bash
docker exec rag-postgres psql -U postgres -d rag_chatbot -c \
  "SELECT cs.session_id, d.filename, sd.priority
   FROM session_documents sd
   JOIN chat_sessions cs ON sd.session_id = cs.id
   JOIN documents d ON sd.document_id = d.id
   ORDER BY sd.added_at DESC LIMIT 5;"
```

**Expected:**
```
        session_id        |    filename     | priority
--------------------------+-----------------+----------
 session-1234567890-abc12 | Short Story.txt |        1
```

**If empty:**
- Session association failed
- Check if session_id was passed during upload
- Check browser console for upload confirmation

**Check 3: Are embeddings being searched?**

Add this to your query and check backend logs:
```bash
# Make a query, then check logs:
docker compose logs backend --tail=50 | grep -i "found.*chunks\|search"
```

**Should see:**
```
Found 3 chunks in short-term memory
Found 5 chunks in long-term memory
```

**If "Found 0 chunks":**
- Embeddings aren't matching the query
- Try a more direct question: "What is the main topic of the document?"
- Check similarity threshold in config

### Issue: Uploaded Files List Shows "Not embedded"

**Cause:** Document processing failed or is still in progress

**Fix:**
```bash
# Check processing status
docker exec rag-postgres psql -U postgres -d rag_chatbot -c \
  "SELECT filename, processing_status, processing_error
   FROM documents
   ORDER BY created_at DESC LIMIT 5;"
```

**If status = 'failed':**
- Check the `processing_error` column
- Common issues:
  - File type not supported
  - Embedding service unavailable
  - Text extraction failed

**If status = 'processing' for > 1 minute:**
- Backend might be stuck
- Restart backend: `docker compose restart backend`
- Delete and re-upload

### Issue: Clear Session Doesn't Work

**Check backend logs:**
```bash
docker compose logs backend | grep -i "clear"
```

**Should see:**
```
Cleared session session-abc123
```

**If error:**
- Check if database tables exist
- Run `./setup-database.sh` again

### Issue: Username Not Showing

**Check localStorage:**
```javascript
// In browser console:
localStorage.getItem('username')
// Should return your username or null
```

**Set username:**
```javascript
localStorage.setItem('username', 'Your Name')
// Refresh page
```

---

## 📊 Verification Checklist

After completing all steps above, verify:

- [ ] Database tables exist (`./setup-database.sh` ran successfully)
- [ ] Backend is healthy (logs show "Enhanced RAG Service")
- [ ] Document uploaded and visible in uploaded files list
- [ ] Chunks > 0 in diagnostic script output
- [ ] Query returns answer from YOUR document (not generic)
- [ ] Clear session works (new session ID generated)
- [ ] Username displays in header
- [ ] Session ID displays in header
- [ ] Refresh page keeps same session
- [ ] Can delete documents from list
- [ ] Documents available in new sessions (long-term memory)

---

## 🎯 Expected Behavior After Full Setup

### Upload Flow
```
1. Click paperclip → Select file
2. File appears in "Attached Files" preview
3. Click Send
4. Browser console: "✅ Uploaded file.txt to session session-..."
5. File appears in "Uploaded Documents" list
6. After ~10 seconds: Shows "✓ 15 chunks"
```

### Query Flow
```
1. Type: "Who is Aadhan?"
2. Browser console: "📤 Querying with session ... and 0 context messages"
3. Backend searches short-term memory (session docs) FIRST
4. Response references YOUR document:
   "Based on the uploaded document, Aadhan is a character..."
5. Sources section shows: "Short Story.txt (70% match)"
```

### Memory Hierarchy
```
┌─────────────────────────────────────┐
│ SHORT-TERM MEMORY (Session Docs)    │
│ - Documents you uploaded this       │
│   session                           │
│ - Checked FIRST (high priority)     │
│ - Lower similarity threshold        │
│   (more inclusive)                  │
└─────────────────────────────────────┘
              ↓ (if not found)
┌─────────────────────────────────────┐
│ LONG-TERM MEMORY (All Docs)         │
│ - All documents across all sessions │
│ - Checked SECOND (standard priority)│
│ - Standard similarity threshold     │
└─────────────────────────────────────┘
```

### Conversation Context
```
Query 1: "Who is Aadhan?"
→ Response: "Aadhan is a character..."

Query 2: "What did he do?"  ← "he" = Aadhan (from context!)
→ Response: "Aadhan partnered with bad people..."

Query 3: "Tell me about the kingdom"
→ Response: "The kingdom is Kandigai..."

Query 4: "When did this happen?"  ← "this" = events in Kandigai
→ Response: "In the story timeline..."
```

All these follow-up questions work because:
- Conversation history is sent with each query (last 10 messages)
- Document context is maintained via session memory
- Model can reference previous exchanges

---

## 🔑 Key Points

1. **Database setup is MANDATORY** - Run `./setup-database.sh` before uploading documents

2. **Re-upload required** - Documents uploaded before DB setup won't work

3. **Processing takes time** - Wait 10-15 seconds after upload for chunking/embedding

4. **Session persistence** - Session ID in sessionStorage, survives page refresh

5. **Memory hierarchy** - Session docs (short-term) checked before all docs (long-term)

6. **Conversation context** - Last 10 messages sent with each query

7. **Clear session** - Removes associations but keeps documents in global store

---

## 🚀 Next Steps

1. **Run database setup:**
   ```bash
   ./setup-database.sh
   docker compose restart backend frontend
   ```

2. **Re-upload your documents** (old uploads won't work)

3. **Test the flow:**
   - Upload → Wait → Query → Check response

4. **If still not working:**
   - Run `./diagnose-documents.sh`
   - Share output for debugging

5. **After verification:**
   - Test all new features (files list, clear session, etc.)
   - Explore admin UI features
   - Set up proper authentication

---

Your documents should now work correctly! The key was setting up the database tables first. 🎉
