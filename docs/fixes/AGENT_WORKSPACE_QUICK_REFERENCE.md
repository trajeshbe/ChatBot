# Agent Workspace File Upload - Quick Reference

**Date**: 2025-11-30
**Status**: ✅ Production Ready

---

## What Was Fixed

### 🐛 Bug 1: Office Files Failed to Upload
**Error**: `value too long for type character varying(50)`
**Fix**: Expanded `documents.file_type` column from VARCHAR(50) to VARCHAR(255)
**Impact**: .docx, .xlsx, .pptx files now upload successfully

### 🐛 Bug 2: Agent Tasks Couldn't Find Files
**Error**: `[Errno 2] No such file or directory`
**Fix**: Created `AgentWorkspaceFileUpload` component that uploads to `/workspace/` volume
**Impact**: Agent tasks can now access uploaded files

### 🐛 Bug 3: Missing Project Selector
**Error**: User couldn't select project context
**Fix**: Restored ProjectSelector component to AgentTaskMonitor
**Impact**: Users can organize files by project

---

## Quick Test

1. **Navigate**: http://localhost:3001 → Sidebar → "Agent Tasks"
2. **Select Project**: Choose from dropdown (e.g., "Construction Intelligence")
3. **Upload File**: Drag & drop any file (especially .docx, .xlsx, .pptx)
4. **Verify**: Check success message "✅ {filename} uploaded to agent workspace!"
5. **Select File**: Click checkbox next to uploaded file
6. **Create Task**: Enter description "Analyze this document" → Click "🚀 Create Task"
7. **Monitor**: Watch task status change from pending → running → completed
8. **Check Result**: Should show file analysis without "File not found" error

---

## Key Files Changed

### Created
- `/frontend/src/components/AgentWorkspaceFileUpload.tsx` - New upload component
- `/backend/migrations/014_fix_file_type_length.sql` - Database schema fix
- `/docs/fixes/AGENT_WORKSPACE_FILE_UPLOAD_FIX.md` - Full documentation

### Modified
- `/frontend/src/components/AgentTaskMonitor.tsx` - Updated imports and upload section

---

## Technical Details

### File Upload Flow
```
AgentWorkspaceFileUpload Component
  ↓
POST /api/v1/agent/upload-workspace-file
  ↓
Backend stores file in 3 places:
  1. MinIO: {role}/{dept}/{team}/{user}/{project}/documents/{filename}
  2. Database: documents table
  3. Workspace: /workspace/{filename} (shared volume)
  ↓
Agent Runtime accesses /workspace/{filename}
  ✅ File found - Task executes successfully
```

### Database Change
```sql
-- BEFORE
file_type VARCHAR(50)  -- ❌ Too short for Office files

-- AFTER
file_type VARCHAR(255)  -- ✅ Accommodates all MIME types
```

### Component Change
```typescript
// BEFORE
import FileUpload from './FileUpload';
<FileUpload currentUser={currentUser} />

// AFTER
import AgentWorkspaceFileUpload from './AgentWorkspaceFileUpload';
<AgentWorkspaceFileUpload
  sessionId={sessionId}
  projectId={selectedProjectId}
  currentUser={currentUser}
  onUploadComplete={() => setFilesListKey(prev => prev + 1)}
/>
```

---

## Verification Commands

### Check Database Schema
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT column_name, data_type, character_maximum_length
   FROM information_schema.columns
   WHERE table_name = 'documents' AND column_name = 'file_type';"
```
**Expected**: `character varying | 255`

### Check Workspace Volume
```bash
docker-compose exec backend ls -lh /workspace/
docker-compose exec agent-runtime ls -lh /workspace/
```
**Expected**: Files appear in both containers

### Check Upload Endpoint
```bash
curl -X POST http://localhost:8000/api/v1/agent/upload-workspace-file \
  -F "file=@test.docx" \
  -F "project_name=test" \
  -F "role=user"
```
**Expected**: JSON response with `workspace_path: "/workspace/test.docx"`

---

## Component Props Reference

### AgentWorkspaceFileUpload
```typescript
interface AgentWorkspaceFileUploadProps {
  sessionId: string;           // Required: Current chat session
  projectId?: string;          // Optional: Project ID for organization
  currentUser?: {              // Optional: User metadata
    id: string;
    username: string;
    role: string;
    department?: string;
    team?: string;
  };
  onUploadComplete?: () => void; // Optional: Callback after upload
}
```

### ProjectSelector
```typescript
interface ProjectSelectorProps {
  value: string;                              // Currently selected project ID
  onChange: (projectId: string, project: any) => void; // Selection callback
  currentUser?: {                             // User context for filtering
    id: string;
    role: string;
    department?: string;
    team?: string;
  };
}
```

---

## API Endpoint

### POST /api/v1/agent/upload-workspace-file

**Request** (multipart/form-data):
```
file: File (required)
project_id: string (optional)
role: string (default: "user")
department: string (default: "default")
team: string (default: "default-team")
username: string (default: "anonymous")
project_name: string (default: "agent-workspace")
```

**Response**:
```json
{
  "filename": "sales.docx",
  "size": 14785,
  "minio_path": "user/default/default-team/john/test/documents/sales.docx",
  "workspace_path": "/workspace/sales.docx",
  "project_id": "uuid-123",
  "document_id": "uuid-456",
  "message": "File uploaded successfully to MinIO and agent workspace"
}
```

---

## Troubleshooting

### File Not Found in Agent Task
1. Check file in workspace: `docker-compose exec backend ls -lh /workspace/`
2. Verify volume mount: `docker inspect rag-backend | grep Mounts`
3. Check upload logs: `docker-compose logs backend | grep workspace`

### Upload Fails Silently
1. Check backend logs: `docker-compose logs backend --tail 50`
2. Check MinIO: http://localhost:9001 (minioadmin/minioadmin)
3. Check database: `SELECT * FROM documents ORDER BY upload_date DESC LIMIT 1;`

### ProjectSelector Missing
1. Clear browser cache: Ctrl+Shift+R
2. Check console: F12 → Console tab
3. Rebuild frontend: `docker-compose build frontend --no-cache && docker-compose restart frontend`

---

## Success Criteria

✅ Office files (.docx, .xlsx, .pptx) upload without errors
✅ Files appear in MinIO, database, AND /workspace/ volume
✅ Agent tasks can access uploaded files
✅ ProjectSelector appears in UI
✅ Upload progress shows during file transfer
✅ Success/error messages display correctly
✅ File list refreshes after upload
✅ No "File not found" errors in agent tasks

---

**Full Documentation**: `/docs/fixes/AGENT_WORKSPACE_FILE_UPLOAD_FIX.md`
**Component Code**: `/frontend/src/components/AgentWorkspaceFileUpload.tsx`
**Migration Script**: `/backend/migrations/014_fix_file_type_length.sql`
