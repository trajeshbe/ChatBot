# Agent Workspace File Upload Fix

**Date**: 2025-11-30
**Status**: ✅ Complete
**Issue**: Agent tasks failing with "File not found" errors after file upload

---

## Problem Summary

Users were experiencing two critical issues when uploading files for agent tasks:

### Issue 1: Database Schema Limitation
**Error Message**:
```
sqlalchemy.dialects.postgresql.asyncpg.Error: value too long for type character varying(50)
```

**Root Cause**:
- The `documents.file_type` column was limited to VARCHAR(50)
- Microsoft Office files have MIME types up to 74 characters long
- Example: `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (74 chars)

**Impact**:
- .docx, .xlsx, .pptx files could not be uploaded
- Upload silently failed without proper user feedback

### Issue 2: Wrong Upload Endpoint
**Error Message**:
```
Error: [Errno 2] No such file or directory
```

**Root Cause**:
- AgentTaskMonitor was using the standard `FileUpload` component
- Standard component uploads to `/api/v1/upload` endpoint
- This endpoint stores files in MinIO + Database BUT NOT in `/workspace/` volume
- Agent tasks run in `agent-runtime` container which only accesses `/workspace/` volume

**Impact**:
- Files uploaded successfully to database
- But agent tasks couldn't find them when executing
- Users received cryptic "File not found" errors

### Issue 3: Missing Project Selector
**User Report**: "the project selctor is missing"

**Root Cause**:
- ProjectSelector component was accidentally removed during refactoring
- When replacing FileUpload import with AgentWorkspaceFileUpload, the ProjectSelector import was lost

**Impact**:
- Users couldn't select project context for file uploads
- No way to organize files by project

---

## Solutions Implemented

### Solution 1: Database Schema Fix

**Migration File**: `/backend/migrations/014_fix_file_type_length.sql`

```sql
-- Migration: Fix file_type column length for long MIME types
-- Date: 2025-11-30
-- Issue: Microsoft Office files have very long MIME types
-- Previous: VARCHAR(50)
-- Updated: VARCHAR(255)

ALTER TABLE documents
ALTER COLUMN file_type TYPE VARCHAR(255);
```

**Applied**:
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -f /migrations/014_fix_file_type_length.sql
```

**Verification**:
```sql
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns
WHERE table_name = 'documents' AND column_name = 'file_type';

-- Result: character varying | 255 ✅
```

### Solution 2: Agent Workspace Upload Component

**New Component**: `/frontend/src/components/AgentWorkspaceFileUpload.tsx`

**Key Features**:
- Uses `/api/v1/agent/upload-workspace-file` endpoint (instead of `/api/v1/upload`)
- Uploads file to THREE locations:
  1. **MinIO** (S3-compatible object storage)
  2. **Database** (documents table)
  3. **Agent Workspace** (`/workspace/` volume shared with agent-runtime)
- Includes organizational context (role, department, team, username, project_id)
- Shows upload progress
- Provides success/error feedback
- Triggers file list refresh via callback

**Component Structure**:
```typescript
interface AgentWorkspaceFileUploadProps {
  sessionId: string;
  projectId?: string;
  currentUser?: {
    id: string;
    username: string;
    role: string;
    department?: string;
    team?: string;
  };
  onUploadComplete?: () => void;
}

export const AgentWorkspaceFileUpload: React.FC<AgentWorkspaceFileUploadProps> = ({
  sessionId,
  projectId,
  currentUser,
  onUploadComplete
}) => {
  // Drag-and-drop file upload with progress tracking
  // Uploads to /api/v1/agent/upload-workspace-file
  // Calls onUploadComplete() to refresh file list
};
```

**Upload Flow**:
```
User drops file
  ↓
FormData creation (file + metadata)
  ↓
POST /api/v1/agent/upload-workspace-file
  ↓
Backend processes:
  1. Store in MinIO: {role}/{dept}/{team}/{user}/{project}/documents/{filename}
  2. Create database record
  3. Copy to /workspace/{filename} volume
  ↓
Response: { filename, workspace_path, minio_path, document_id }
  ↓
onUploadComplete() callback
  ↓
File list refreshes
```

### Solution 3: Restore ProjectSelector

**Modified Component**: `/frontend/src/components/AgentTaskMonitor.tsx`

**Changes**:

1. **Added Import**:
```typescript
import ProjectSelector from './ProjectSelector';
```

2. **Added State**:
```typescript
const [selectedProject, setSelectedProject] = useState<any>(null);
```

3. **Added UI Section**:
```typescript
<div className="bg-white dark:bg-slate-800 rounded shadow-sm p-2 mb-2 border border-slate-200 dark:border-slate-700">
  <h2 className="text-xs font-semibold mb-2 text-slate-700 dark:text-slate-300">
    📁 Project Context
  </h2>
  <ProjectSelector
    value={selectedProjectId}
    onChange={(projectId, project) => {
      setSelectedProject(project);
      setSelectedProjectId(projectId);
      setSelectedFiles(new Set());
      setUploadedDocuments([]);
      setFilesListKey(prev => prev + 1);
    }}
    currentUser={currentUser}
  />
</div>
```

4. **Updated Upload Component**:
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
  onUploadComplete={() => {
    setFilesListKey(prev => prev + 1);
  }}
/>
```

---

## File Upload Architecture

### Before (BROKEN)

```
┌─────────────────────────────────────────────────────────────────┐
│ Frontend: AgentTaskMonitor                                      │
│   └─ FileUpload component                                       │
│       └─ POST /api/v1/upload                                    │
└──────────────────────────────┬──────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│ Backend: /api/v1/upload endpoint                                │
│   ✅ Store in MinIO                                             │
│   ✅ Create document record in database                         │
│   ❌ NOT copied to /workspace/ volume                           │
└──────────────────────────────┬──────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│ Agent Runtime Container                                         │
│   Looks for file in /workspace/                                 │
│   ❌ FILE NOT FOUND ERROR                                       │
└─────────────────────────────────────────────────────────────────┘
```

### After (FIXED)

```
┌─────────────────────────────────────────────────────────────────┐
│ Frontend: AgentTaskMonitor                                      │
│   ├─ ProjectSelector (select project context)                   │
│   └─ AgentWorkspaceFileUpload component                         │
│       └─ POST /api/v1/agent/upload-workspace-file               │
└──────────────────────────────┬──────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│ Backend: /api/v1/agent/upload-workspace-file endpoint           │
│   ✅ Store in MinIO (hierarchical path)                         │
│   ✅ Create document record in database                         │
│   ✅ Copy to /workspace/{filename} volume                       │
└──────────────────────────────┬──────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│ Agent Runtime Container                                         │
│   Looks for file in /workspace/                                 │
│   ✅ FILE FOUND - Task executes successfully                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Docker Volume Configuration

The `agent_workspace` volume is shared between backend and agent-runtime:

**docker-compose.yml**:
```yaml
services:
  backend:
    volumes:
      - agent_workspace:/workspace  # Write access

  agent-runtime:
    volumes:
      - agent_workspace:/workspace  # Read access

volumes:
  agent_workspace:
    driver: local
```

**File Persistence**:
- Files uploaded via `/api/v1/agent/upload-workspace-file` are written to `/workspace/` in backend container
- Same files are immediately available in agent-runtime container at `/workspace/`
- Files persist across container restarts (Docker volume)

---

## Testing Guide

### Test Database Schema Fix

1. **Upload Office File**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/agent/upload-workspace-file \
     -F "file=@sales.docx" \
     -F "project_name=test-project" \
     -F "role=user"
   ```

2. **Verify Upload Success**:
   ```bash
   docker-compose exec postgres psql -U postgres -d ragchatbot -c \
     "SELECT filename, file_type FROM documents ORDER BY upload_date DESC LIMIT 1;"
   ```

   **Expected**:
   ```
   filename   | file_type
   -----------+------------------------------------------------------------------------
   sales.docx | application/vnd.openxmlformats-officedocument.wordprocessingml.document
   ```

### Test Agent Workspace Upload

1. **Navigate to Agent Tasks**:
   ```
   http://localhost:3001 → Sidebar → "Agent Tasks"
   ```

2. **Select Project**:
   - Click ProjectSelector dropdown
   - Select a project (e.g., "Construction Intelligence")

3. **Upload File**:
   - Drag and drop a file into "📤 Upload to Agent Workspace" area
   - Or click to browse and select file
   - Verify success message: "✅ {filename} uploaded to agent workspace!"

4. **Verify File in Database**:
   ```bash
   docker-compose exec postgres psql -U postgres -d ragchatbot -c \
     "SELECT filename, file_type FROM documents ORDER BY upload_date DESC LIMIT 1;"
   ```

5. **Verify File in Workspace Volume**:
   ```bash
   docker-compose exec backend ls -lh /workspace/
   ```

6. **Verify File in MinIO**:
   - Open http://localhost:9001
   - Login: minioadmin / minioadmin
   - Navigate to `ragchatbot-documents` bucket
   - Check for file in hierarchical path: `{role}/{dept}/{team}/{user}/{project}/documents/`

### Test Agent Task Execution

1. **Create Agent Task**:
   - Select uploaded file from "Select Files" list (checkbox)
   - Enter task description: "Analyze this document and summarize it"
   - Click "🚀 Create Task"

2. **Monitor Task Execution**:
   - Task should show status: "pending" → "running" → "completed"
   - Result should include file analysis
   - No "File not found" errors

3. **Check Backend Logs**:
   ```bash
   docker-compose logs backend --tail 50 | grep -i workspace
   ```

   **Expected logs**:
   ```
   INFO: File uploaded to MinIO: user/default/default-team/john/test-project/documents/sales.docx
   INFO: File copied to workspace: /workspace/sales.docx
   ```

---

## Files Modified/Created

### Created Files
1. `/frontend/src/components/AgentWorkspaceFileUpload.tsx` - New upload component
2. `/backend/migrations/014_fix_file_type_length.sql` - Database migration
3. `/docs/fixes/AGENT_WORKSPACE_FILE_UPLOAD_FIX.md` - This documentation

### Modified Files
1. `/frontend/src/components/AgentTaskMonitor.tsx`:
   - Import changed: `FileUpload` → `AgentWorkspaceFileUpload`
   - Added ProjectSelector import and usage
   - Added selectedProject state
   - Updated upload section props

### Backend Endpoint (Already Existed)
- `/backend/app/api/routes/agent_routes.py` - `/api/v1/agent/upload-workspace-file` endpoint

---

## API Endpoint Reference

### POST /api/v1/agent/upload-workspace-file

**Purpose**: Upload file to MinIO, database, AND agent workspace volume

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
  "minio_path": "user/default/default-team/john/test-project/documents/sales.docx",
  "workspace_path": "/workspace/sales.docx",
  "project_id": "uuid-123",
  "document_id": "uuid-456",
  "message": "File uploaded successfully to MinIO and agent workspace"
}
```

**Behavior**:
1. Validates file upload
2. Generates unique filename if needed
3. Constructs hierarchical MinIO path: `{role}/{dept}/{team}/{user}/{project}/documents/{filename}`
4. Uploads to MinIO bucket
5. Writes file to `/workspace/{filename}` volume
6. Creates document record in database
7. Returns metadata with all paths

---

## Known MIME Types for Office Files

| File Extension | MIME Type | Length |
|----------------|-----------|--------|
| .docx | application/vnd.openxmlformats-officedocument.wordprocessingml.document | 74 |
| .xlsx | application/vnd.openxmlformats-officedocument.spreadsheetml.sheet | 70 |
| .pptx | application/vnd.openxmlformats-officedocument.presentationml.presentation | 79 |
| .pdf | application/pdf | 15 |
| .txt | text/plain | 10 |
| .csv | text/csv | 8 |
| .json | application/json | 16 |

**All now supported** with VARCHAR(255) column length ✅

---

## Success Metrics

✅ **Database Schema**: file_type column expanded to VARCHAR(255)
✅ **Component Created**: AgentWorkspaceFileUpload.tsx with drag-and-drop
✅ **Component Integrated**: AgentTaskMonitor uses new upload component
✅ **ProjectSelector Restored**: Users can select project context
✅ **Upload Endpoint**: Files copied to /workspace/ volume
✅ **Agent Tasks**: Can access uploaded files successfully
✅ **Office Files**: .docx, .xlsx, .pptx files upload without errors
✅ **Frontend Compiled**: No build errors
✅ **Services Running**: Backend, Frontend, Postgres all healthy

---

## Troubleshooting

### Issue: File still not found in agent task

**Check 1 - Verify file in workspace**:
```bash
docker-compose exec backend ls -lh /workspace/
docker-compose exec agent-runtime ls -lh /workspace/
```

**Check 2 - Verify volume mount**:
```bash
docker inspect rag-backend | grep -A 5 "Mounts"
docker inspect rag-agent-runtime | grep -A 5 "Mounts"
```

**Check 3 - Check backend logs**:
```bash
docker-compose logs backend | grep -i "workspace"
```

### Issue: Upload fails silently

**Check backend logs for errors**:
```bash
docker-compose logs backend --tail 50
```

**Check MinIO connectivity**:
```bash
docker-compose exec backend curl -I http://minio:9000
```

### Issue: ProjectSelector not appearing

**Check frontend console**:
- Open http://localhost:3001
- Press F12 → Console tab
- Look for React errors

**Rebuild frontend**:
```bash
docker-compose build frontend --no-cache
docker-compose restart frontend
```

---

## Related Documentation

- **Backend Implementation**: `/docs/features/AGENT_FILE_MANAGEMENT_INTEGRATION.md`
- **Frontend Implementation**: `/docs/features/AGENT_TASK_MONITOR_FINAL_IMPLEMENTATION.md`
- **API Documentation**: `/backend/app/api/routes/agent_routes.py`
- **Database Migrations**: `/backend/migrations/README.md`

---

**Status**: ✅ All issues resolved and tested
**Deployment**: Ready for production
**User Impact**: Agent tasks can now access uploaded files without errors
