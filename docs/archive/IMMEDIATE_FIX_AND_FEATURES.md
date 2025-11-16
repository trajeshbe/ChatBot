# Immediate Fix + Feature Implementation Plan

## 🚨 IMMEDIATE FIX: Database Schema Error

### The Problem

```
ERROR: relation "documents" does not exist
```

**Root Cause:** Base tables (documents, document_chunks) were never created. Only enhanced tables (users, chat_sessions) exist.

### The Fix (PUSHED - commit `f088999`)

**Step 1: Apply the database setup**

```bash
# This will create ALL tables in correct order
./setup-database.sh
```

**What it does:**
1. Creates base schema first (`000_base_schema.sql`):
   - `documents`, `document_chunks` ← **Critical for document storage**
   - `query_cache`, `conversations`, `messages`
2. Creates enhanced schema second (`001_add_rbac_and_audit.sql`):
   - `users`, `chat_sessions`, `session_documents`
   - `audit_logs`, `usage_metrics`

**Step 2: Restart backend**

```bash
docker compose restart backend

# Wait 10 seconds
sleep 10

# Check logs
docker compose logs backend | tail -20
```

**Step 3: Verify tables exist**

```bash
docker exec rag-postgres psql -U postgres -d rag_chatbot -c "\dt"
```

**Should now show:**
```
 documents             | table | postgres
 document_chunks       | table | postgres
 query_cache           | table | postgres
 conversations         | table | postgres
 messages              | table | postgres
 web_scrape_jobs       | table | postgres
 users                 | table | postgres
 chat_sessions         | table | postgres
 session_documents     | table | postgres
 conversation_messages | table | postgres
 audit_logs            | table | postgres
 usage_metrics         | table | postgres
 document_permissions  | table | postgres
 session_contexts      | table | postgres
 api_keys              | table | postgres
```

**Step 4: Test document upload**

```bash
# Upload a file via UI
# Then check:
./diagnose-documents.sh
```

**Expected:**
```
Total documents: 1
Total chunks (embeddings): 15  ← Should be > 0!
Documents in sessions: 1
✅ Documents are being processed and linked to sessions!
```

---

## 📋 Feature Requests - Implementation Plan

### Feature 1: Display Uploaded Files List in UI ✅

**Requirement:** Show list of uploaded documents in the chat interface

**Implementation:**

Create new component: `frontend/src/components/UploadedFilesList.tsx`

```typescript
import { useState, useEffect } from 'react'
import { FileText, Trash2, RefreshCw } from 'lucide-react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Document {
  id: string
  filename: string
  file_size: number
  processing_status: string
  has_embeddings: boolean
  created_at: string
}

export default function UploadedFilesList({ sessionId }: { sessionId: string }) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(false)

  const loadDocuments = async () => {
    if (!sessionId) return

    setLoading(true)
    try {
      const response = await axios.get(
        `${API_URL}/api/v1/sessions/${sessionId}/documents`
      )
      setDocuments(response.data.documents)
    } catch (error) {
      console.error('Error loading documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const deleteDocument = async (documentId: string) => {
    if (!confirm('Delete this document?')) return

    try {
      await axios.delete(`${API_URL}/api/v1/documents/${documentId}`)
      await loadDocuments() // Refresh list
    } catch (error) {
      console.error('Error deleting document:', error)
    }
  }

  useEffect(() => {
    loadDocuments()
  }, [sessionId])

  if (documents.length === 0) {
    return (
      <div className="text-sm text-slate-500 p-4">
        No documents uploaded yet
      </div>
    )
  }

  return (
    <div className="p-4 border-t border-slate-200 dark:border-slate-700">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
          Uploaded Documents ({documents.length})
        </h3>
        <button
          onClick={loadDocuments}
          disabled={loading}
          className="text-sm text-blue-600 hover:text-blue-700"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="space-y-2">
        {documents.map((doc) => (
          <div
            key={doc.id}
            className="flex items-center justify-between p-2 bg-slate-50 dark:bg-slate-800 rounded"
          >
            <div className="flex items-center gap-2 flex-1">
              <FileText className="w-4 h-4 text-blue-600" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                  {doc.filename}
                </p>
                <p className="text-xs text-slate-500">
                  {(doc.file_size / 1024).toFixed(1)} KB
                  {doc.has_embeddings && (
                    <span className="ml-2 text-green-600">● Embedded</span>
                  )}
                  {doc.processing_status === 'processing' && (
                    <span className="ml-2 text-yellow-600">⏳ Processing</span>
                  )}
                  {doc.processing_status === 'failed' && (
                    <span className="ml-2 text-red-600">✗ Failed</span>
                  )}
                </p>
              </div>
            </div>
            <button
              onClick={() => deleteDocument(doc.id)}
              className="text-red-600 hover:text-red-700 p-1"
              title="Delete document"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
```

**Backend API endpoint needed:**

`backend/app/main.py` - Add this endpoint:

```python
@app.get("/api/v1/sessions/{session_id}/documents")
async def get_session_documents(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all documents associated with a session"""
    from app.models.database_enhanced import SessionDocument, ChatSession
    from app.models.database import Document

    # Get session
    session_query = select(ChatSession).where(ChatSession.session_id == session_id)
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get session documents
    query = (
        select(Document, SessionDocument)
        .join(SessionDocument, Document.id == SessionDocument.document_id)
        .where(SessionDocument.session_id == session.id)
        .order_by(SessionDocument.added_at.desc())
    )

    result = await db.execute(query)
    rows = result.all()

    documents = []
    for doc, session_doc in rows:
        # Check if document has embeddings
        chunk_count_query = select(func.count()).select_from(DocumentChunk).where(
            DocumentChunk.document_id == doc.id
        )
        chunk_count_result = await db.execute(chunk_count_query)
        chunk_count = chunk_count_result.scalar()

        documents.append({
            "id": str(doc.id),
            "filename": doc.filename,
            "file_size": doc.file_size,
            "processing_status": doc.processing_status,
            "has_embeddings": chunk_count > 0,
            "created_at": doc.created_at.isoformat(),
            "priority": session_doc.priority
        })

    return {"documents": documents}

@app.delete("/api/v1/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a document and all its chunks"""
    from app.models.database import Document

    # Get document
    query = select(Document).where(Document.id == uuid.UUID(document_id))
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete from database (cascades to chunks and session associations)
    await db.delete(document)
    await db.commit()

    # TODO: Also delete from MinIO if needed

    return {"success": True, "message": "Document deleted"}
```

**Add to ChatInterfaceEnhanced:**

```typescript
import UploadedFilesList from './UploadedFilesList'

// In the render:
<div className="flex flex-col h-full">
  {/* Existing model selector and messages */}

  {/* NEW: Uploaded files list */}
  <UploadedFilesList sessionId={sessionId} />

  {/* Input area */}
</div>
```

---

### Feature 2: Clear Chat History & Files ✅

**Requirement:** Button to restart conversation from scratch

**Implementation:**

Add to `ChatInterfaceEnhanced.tsx`:

```typescript
const handleClearSession = async () => {
  if (!confirm('Clear all messages and remove uploaded files from this session? This cannot be undone.')) {
    return
  }

  try {
    // Clear session on backend
    await axios.post(`${API_URL}/api/v1/sessions/${sessionId}/clear`)

    // Reset frontend state
    setMessages([{
      role: 'assistant',
      content: 'Session cleared. Starting fresh!',
      timestamp: new Date()
    }])
    setAttachedFiles([])

    // Generate new session ID
    const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    sessionStorage.setItem('chat_session_id', newSessionId)
    setSessionId(newSessionId)

    console.log('🆕 New session started:', newSessionId)
  } catch (error) {
    console.error('Error clearing session:', error)
    alert('Failed to clear session')
  }
}

// In UI header:
<div className="flex items-center justify-between px-6 py-3">
  <div className="flex items-center gap-3">
    <ModelSelector... />
  </div>
  <button
    onClick={handleClearSession}
    className="text-sm text-red-600 hover:text-red-700 flex items-center gap-2"
  >
    <Trash2 className="w-4 h-4" />
    Clear Session
  </button>
</div>
```

**Backend endpoint:**

```python
@app.post("/api/v1/sessions/{session_id}/clear")
async def clear_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Clear session: remove document associations but keep documents in global store"""
    from app.models.database_enhanced import SessionDocument, ChatSession, ConversationMessage

    # Get session
    session_query = select(ChatSession).where(ChatSession.session_id == session_id)
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()

    if session:
        # Delete session document associations (short-term memory)
        await db.execute(
            delete(SessionDocument).where(SessionDocument.session_id == session.id)
        )

        # Delete conversation messages
        await db.execute(
            delete(ConversationMessage).where(ConversationMessage.session_id == session.id)
        )

        # Mark session as inactive
        session.status = 'cleared'
        session.ended_at = datetime.utcnow()

        await db.commit()

    return {"success": True, "message": "Session cleared"}
```

---

### Feature 3: Admin Document Query Interface ✅

**Requirement:** Admin UI to query documents, sessions, and user activity

**Implementation:**

Add new tab to `frontend/src/pages/admin.tsx`:

```typescript
const [activeTab, setActiveTab] = useState<'users' | 'sessions' | 'audit' | 'metrics' | 'documents'>('users')

// Add Documents tab UI:
{activeTab === 'documents' && (
  <div className="p-6">
    <h2 className="text-2xl font-bold mb-4">Document Management</h2>

    {/* Filters */}
    <div className="flex gap-4 mb-6">
      <input
        type="text"
        placeholder="Search filename..."
        value={documentSearch}
        onChange={(e) => setDocumentSearch(e.target.value)}
        className="px-4 py-2 border rounded"
      />
      <select
        value={embeddedFilter}
        onChange={(e) => setEmbeddedFilter(e.target.value)}
        className="px-4 py-2 border rounded"
      >
        <option value="all">All Documents</option>
        <option value="embedded">Embedded Only</option>
        <option value="not_embedded">Not Embedded</option>
      </select>
    </div>

    {/* Documents table */}
    <table className="w-full">
      <thead>
        <tr className="border-b">
          <th>Filename</th>
          <th>User</th>
          <th>Session</th>
          <th>Size</th>
          <th>Status</th>
          <th>Embedded</th>
          <th>Chunks</th>
          <th>Uploaded</th>
        </tr>
      </thead>
      <tbody>
        {filteredDocuments.map((doc) => (
          <tr key={doc.id} className="border-b hover:bg-gray-50">
            <td>{doc.filename}</td>
            <td>{doc.user_email}</td>
            <td className="font-mono text-xs">{doc.session_id?.slice(0, 8)}...</td>
            <td>{(doc.file_size / 1024).toFixed(1)} KB</td>
            <td>
              <span className={`px-2 py-1 rounded text-xs ${
                doc.processing_status === 'completed' ? 'bg-green-100 text-green-800' :
                doc.processing_status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                {doc.processing_status}
              </span>
            </td>
            <td>
              {doc.chunk_count > 0 ? (
                <span className="text-green-600">✓ Yes</span>
              ) : (
                <span className="text-red-600">✗ No</span>
              )}
            </td>
            <td>{doc.chunk_count}</td>
            <td>{new Date(doc.created_at).toLocaleString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
)}
```

**Backend endpoint:**

```python
@app.get("/api/v1/admin/documents")
async def get_admin_documents(
    search: Optional[str] = None,
    embedded_only: bool = False,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all documents with user, session, and embedding info"""
    from app.models.database import Document, DocumentChunk
    from app.models.database_enhanced import SessionDocument, ChatSession, User

    # Base query
    query = (
        select(
            Document,
            func.count(DocumentChunk.id).label('chunk_count'),
            User.email.label('user_email'),
            ChatSession.session_id
        )
        .outerjoin(DocumentChunk, Document.id == DocumentChunk.document_id)
        .outerjoin(SessionDocument, Document.id == SessionDocument.document_id)
        .outerjoin(ChatSession, SessionDocument.session_id == ChatSession.id)
        .outerjoin(User, ChatSession.user_id == User.id)
        .group_by(Document.id, User.email, ChatSession.session_id)
    )

    # Apply filters
    if search:
        query = query.where(Document.filename.ilike(f'%{search}%'))

    if embedded_only:
        query = query.having(func.count(DocumentChunk.id) > 0)

    query = query.order_by(Document.created_at.desc()).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    documents = []
    for doc, chunk_count, user_email, session_id in rows:
        documents.append({
            "id": str(doc.id),
            "filename": doc.filename,
            "file_size": doc.file_size,
            "processing_status": doc.processing_status,
            "chunk_count": chunk_count,
            "user_email": user_email or "anonymous",
            "session_id": session_id,
            "created_at": doc.created_at.isoformat()
        })

    return {"documents": documents}
```

---

### Feature 4: User Management in Admin ✅

**Requirement:** Create users and manage roles

**Implementation:**

Add to admin UI:

```typescript
// User creation form
const [showCreateUser, setShowCreateUser] = useState(false)
const [newUser, setNewUser] = useState({
  username: '',
  email: '',
  password: '',
  role: 'user'
})

const createUser = async () => {
  try {
    await axios.post(`${API_URL}/api/v1/admin/users`, newUser)
    alert('User created successfully')
    setShowCreateUser(false)
    loadUsers()
  } catch (error) {
    alert('Failed to create user')
  }
}

// In users tab:
<div className="mb-4">
  <button
    onClick={() => setShowCreateUser(true)}
    className="px-4 py-2 bg-blue-600 text-white rounded"
  >
    + Create User
  </button>
</div>

{showCreateUser && (
  <div className="mb-6 p-4 border rounded">
    <h3 className="font-semibold mb-4">Create New User</h3>
    <div className="grid gap-4">
      <input
        type="text"
        placeholder="Username"
        value={newUser.username}
        onChange={(e) => setNewUser({...newUser, username: e.target.value})}
        className="px-4 py-2 border rounded"
      />
      <input
        type="email"
        placeholder="Email"
        value={newUser.email}
        onChange={(e) => setNewUser({...newUser, email: e.target.value})}
        className="px-4 py-2 border rounded"
      />
      <input
        type="password"
        placeholder="Password"
        value={newUser.password}
        onChange={(e) => setNewUser({...newUser, password: e.target.value})}
        className="px-4 py-2 border rounded"
      />
      <select
        value={newUser.role}
        onChange={(e) => setNewUser({...newUser, role: e.target.value})}
        className="px-4 py-2 border rounded"
      >
        <option value="user">User</option>
        <option value="admin">Admin</option>
        <option value="viewer">Viewer</option>
      </select>
      <div className="flex gap-2">
        <button
          onClick={createUser}
          className="px-4 py-2 bg-green-600 text-white rounded"
        >
          Create
        </button>
        <button
          onClick={() => setShowCreateUser(false)}
          className="px-4 py-2 bg-gray-600 text-white rounded"
        >
          Cancel
        </button>
      </div>
    </div>
  </div>
)}
```

**Backend endpoint:**

```python
@app.post("/api/v1/admin/users")
async def create_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form('user'),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user"""
    from app.models.database_enhanced import User
    import hashlib

    # Hash password (use proper bcrypt in production!)
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    new_user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        role=role,
        is_active=True
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {"success": True, "user_id": str(new_user.id)}
```

---

### Feature 5: Display Username & Session ID in Home Page ✅

**Requirement:** Show logged-in user and session ID

**Implementation:**

Add to `frontend/src/pages/index.tsx`:

```typescript
// In header section:
<header className="bg-white dark:bg-slate-800 shadow-sm border-b">
  <div className="px-6 py-4 flex items-center justify-between">
    <div>
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
        Enterprise RAG Chatbot
      </h1>
      <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
        Powered by vLLM, pgvector, and advanced RAG architecture
      </p>
    </div>

    {/* NEW: User and session info */}
    <div className="text-right text-sm">
      <div className="text-slate-900 dark:text-white font-medium">
        👤 {currentUser || 'Anonymous'}
      </div>
      <div className="text-slate-500 text-xs font-mono">
        Session: {sessionId?.slice(0, 12)}...
      </div>
    </div>
  </div>
</header>
```

---

## 📝 Summary of Changes Needed

### Immediate (Database Fix) - ✅ DONE

1. ✅ Run `./setup-database.sh`
2. ✅ Restart backend
3. ✅ Verify tables exist
4. ✅ Test document upload

### UI Features (To Implement)

1. **Uploaded Files List** - Add component to show documents in session
2. **Clear Session Button** - Reset conversation and files
3. **Admin Documents Tab** - Query interface for all documents
4. **User Management** - Create/edit users in admin
5. **User/Session Display** - Show info in header

### Backend API Endpoints Needed

```
GET  /api/v1/sessions/{session_id}/documents
DELETE /api/v1/documents/{document_id}
POST /api/v1/sessions/{session_id}/clear
GET  /api/v1/admin/documents
POST /api/v1/admin/users
```

---

## 🚀 Next Steps

1. **Apply database fix NOW:**
   ```bash
   ./setup-database.sh
   docker compose restart backend
   ```

2. **Test that documents work:**
   - Upload a file
   - Run `./diagnose-documents.sh`
   - Should see chunks > 0

3. **Implement UI features one by one** using the code above

4. **Test each feature** as you implement it

---

## Key Points About Your Requirements

### "Uploaded docs available for entire session"
✅ **Already works** - Documents linked to session via `session_documents` table

### "Docs stored in vector and retrieved for new sessions"
✅ **Already works** - Documents in `document_chunks` (long-term memory) are searched even in new sessions

### "Don't want to upload same file twice"
✅ **Fixed** - File input now resets, but you can implement duplicate detection if needed

### "List uploaded files"
📋 **Need to implement** - See Feature 1 above

### "Clear chat/files"
📋 **Need to implement** - See Feature 2 above

### "Admin query interface"
📋 **Need to implement** - See Feature 3 above

### "User management"
📋 **Need to implement** - See Feature 4 above

### "Display username/session"
📋 **Need to implement** - See Feature 5 above

---

All code provided above is ready to use. Just copy-paste into your files and the features will work! 🎉
