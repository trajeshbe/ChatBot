# Agent Task Monitor - File Management Integration

**Date**: 2025-11-30
**Status**: 🚧 Backend Complete | Frontend In Progress
**Feature**: Upload files to MinIO with organizational structure + Agent workspace access

---

## Overview

This enhancement adds comprehensive file management capabilities to the Agent Task Monitor, allowing users to:

1. **Upload files** directly from Agent UI to MinIO with full organizational path structure
2. **Browse existing project files** from MinIO
3. **Automatic workspace sync** - Files uploaded are automatically available in `/workspace/` for agent tasks
4. **Project-based organization** - Files organized by Role → Dept → Team → User → Project → Folder → File
5. **Inherit project context** from chat UI via Project Selector

---

## ✅ What's Been Implemented (Backend)

### 1. New API Endpoints

**File Upload Endpoint** (`/api/v1/agent/upload-workspace-file`)
**Method**: `POST`
**Purpose**: Upload file to MinIO + Agent workspace

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
  "filename": "sales.csv",
  "size": 1024,
  "minio_path": "user/default/default-team/anonymous/agent-workspace/documents/sales.csv",
  "workspace_path": "/workspace/sales.csv",
  "project_id": "uuid-123",
  "document_id": "uuid-456",
  "message": "File uploaded successfully to MinIO and agent workspace"
}
```

**What it does**:
- Stores file in MinIO with organizational path structure
- Writes same file to `/workspace/` volume (shared between backend and agent-runtime)
- Creates document record in database
- Maintains full audit trail

---

**File List Endpoint** (`/api/v1/agent/project-files`)
**Method**: `GET`
**Purpose**: List all files from a selected project

**Query Parameters**:
```
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
  "files": [
    {
      "filename": "requirements.pdf",
      "minio_path": "user/default/default-team/anonymous/chatbot-rag/documents/requirements.pdf",
      "size": 204800,
      "last_modified": "2025-11-30T12:00:00Z",
      "etag": "abc123",
      "folder": "documents",
      "department": "default",
      "team": "default-team",
      "username": "anonymous",
      "project": "chatbot-rag"
    }
  ],
  "total": 1,
  "project_prefix": "user/default/default-team/anonymous/chatbot-rag/*",
  "project_name": "chatbot-rag"
}
```

---

### 2. Infrastructure Changes

**docker-compose.yml** - Backend service now has access to agent_workspace volume:

```yaml
backend:
  volumes:
    - ./backend:/app
    - agent_workspace:/workspace  # NEW: Shared with agent-runtime
```

**File Flow**:
```
User Upload → Backend API → MinIO + /workspace/ → Agent Runtime reads from /workspace/
```

---

### 3. Organizational Path Structure

All files follow enterprise organization pattern:

```
MinIO Path: {role}/{department}/{team}/{username}/{project}/{folder}/{filename}
```

**Example**:
```
admin/technology/tech-team-1/john.doe/chatbot-rag/documents/requirements.pdf
```

**Benefits**:
- Aligns with existing RBAC model
- Easy department/team-wide file operations
- Scalable for multi-tenancy
- Efficient role-based access control

---

## 🚧 What Remains (Frontend)

### Frontend Implementation Tasks

The AgentTaskMonitor.tsx component needs the following enhancements:

#### 1. **Add Project Selector** (Inherit from Chat UI)

```typescript
import ProjectSelector from './ProjectSelector'

// State
const [selectedProjectId, setSelectedProjectId] = useState<string>('')
const [selectedProject, setSelectedProject] = useState<Project | null>(null)

// Sync with localStorage (same as chat UI)
useEffect(() => {
  const savedProjectId = localStorage.getItem('selected_project_id')
  if (savedProjectId) {
    setSelectedProjectId(savedProjectId)
  }
}, [])

// When project changes, fetch its files
useEffect(() => {
  if (selectedProject) {
    fetchProjectFiles()
  }
}, [selectedProject])
```

---

#### 2. **Add File Upload Section** (Drag & Drop)

Similar to FileUpload.tsx pattern:

```typescript
import { useDropzone } from 'react-dropzone'

const onDrop = useCallback(async (acceptedFiles: File[]) => {
  for (const file of acceptedFiles) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('project_id', selectedProjectId)
    formData.append('role', currentUser?.role || 'user')
    formData.append('department', currentUser?.department || 'default')
    formData.append('team', currentUser?.team || 'default-team')
    formData.append('username', currentUser?.username || 'anonymous')
    formData.append('project_name', selectedProject?.name || 'agent-workspace')

    const response = await axios.post(
      `${API_URL}/api/v1/agent/upload-workspace-file`,
      formData
    )

    console.log('✅ File uploaded:', response.data)
    // Refresh file list
    fetchProjectFiles()
  }
}, [selectedProjectId, selectedProject, currentUser])

const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop })
```

---

#### 3. **Add File Browser** (Select Existing Files)

Fetch and display project files:

```typescript
const [projectFiles, setProjectFiles] = useState<any[]>([])
const [selectedFiles, setSelectedFiles] = useState<string[]>([])  // workspace paths

const fetchProjectFiles = async () => {
  if (!selectedProject) return

  const response = await axios.get(`${API_URL}/api/v1/agent/project-files`, {
    params: {
      project_id: selectedProjectId,
      role: currentUser?.role,
      department: currentUser?.department,
      team: currentUser?.team,
      username: currentUser?.username,
      project_name: selectedProject.name
    }
  })

  setProjectFiles(response.data.files)
}

const toggleFileSelection = (filename: string) => {
  setSelectedFiles(prev =>
    prev.includes(`/workspace/${filename}`)
      ? prev.filter(f => f !== `/workspace/${filename}`)
      : [...prev, `/workspace/${filename}`]
  )
}
```

**UI Component**:
```tsx
<div className="file-browser">
  <h3>📂 Project Files ({projectFiles.length})</h3>
  <div className="file-list">
    {projectFiles.map(file => (
      <div key={file.filename} className="file-item">
        <input
          type="checkbox"
          checked={selectedFiles.includes(`/workspace/${file.filename}`)}
          onChange={() => toggleFileSelection(file.filename)}
        />
        <span>{file.filename}</span>
        <span>{(file.size / 1024).toFixed(2)} KB</span>
      </div>
    ))}
  </div>
</div>
```

---

#### 4. **Display Selected Files**

Show which files will be available to the agent:

```tsx
<div className="selected-files-summary">
  <h4>📎 Files Available to Agent: ({selectedFiles.length})</h4>
  <ul>
    {selectedFiles.map(filePath => (
      <li key={filePath}>
        <code>{filePath}</code>
        <button onClick={() => setSelectedFiles(prev => prev.filter(f => f !== filePath))}>
          Remove
        </button>
      </li>
    ))}
  </ul>
</div>
```

---

#### 5. **Update Task Creation** (Pass File Context)

Enhance task description with file context:

```typescript
const createTask = async () => {
  let enhancedDescription = taskDescription

  // Append file context if files are selected
  if (selectedFiles.length > 0) {
    enhancedDescription += `\n\nAvailable files in /workspace/:\n${selectedFiles.map(f => `- ${f}`).join('\n')}`
  }

  const payload = {
    task_description: enhancedDescription,
    session_id: sessionId || undefined,
    model,
    max_iterations: maxIterations,
    timeout_seconds: timeoutSeconds,
    project_id: selectedProjectId,  // Include project context
    meta_info: {
      files_available: selectedFiles,
      project_name: selectedProject?.name
    }
  }

  await axios.post(`${API_URL}/api/v1/agent/tasks`, payload)
}
```

---

## UI Layout Recommendation

Suggested layout for enhanced AgentTaskMonitor:

```
┌─────────────────────────────────────────────────────────┐
│ 🤖 AI Agent Task Monitor                                │
├─────────────────────────────────────────────────────────┤
│ 📁 Project Context                                      │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [Project Selector Dropdown ▼]                       │ │
│ │ Selected: ChatBot RAG (Tech Team 1)                 │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ 📤 Upload Files for Agent Tasks                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │  Drag & drop files here or click to browse          │ │
│ │  Files will be stored in MinIO + Agent workspace    │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ 📂 Browse Project Files (3 files)                       │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ☑ requirements.pdf          (200 KB)                │ │
│ │ ☐ sales.csv                 (1 KB)                  │ │
│ │ ☐ architecture.png          (500 KB)                │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ 📎 Files Available to Agent (1 selected)                │
│ • /workspace/requirements.pdf                 [Remove]  │
├─────────────────────────────────────────────────────────┤
│ 🎯 Create New Task                                      │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Task Description:                                    │ │
│ │ Analyze requirements.pdf and create summary         │ │
│ │                                                      │ │
│ │ Model: [qwen2.5-coder:7b ▼]                         │ │
│ │ Max Iterations: [20]  Timeout: [600s]               │ │
│ │ [Create Task]                                        │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ 📋 Task List (Auto-refresh every 5s)                    │
│ ... (existing task list)                                │
└─────────────────────────────────────────────────────────┘
```

---

## Testing Guide

### Test Backend Endpoints

**Test File Upload**:
```bash
curl -X POST http://localhost:8000/api/v1/agent/upload-workspace-file \
  -F "file=@/tmp/sales.csv" \
  -F "project_name=test-project" \
  -F "role=user" \
  -F "department=technology" \
  -F "team=tech-team-1" \
  -F "username=john.doe"
```

**Expected Response**:
```json
{
  "filename": "sales.csv",
  "size": 597,
  "minio_path": "user/technology/tech-team-1/john.doe/test-project/documents/sales.csv",
  "workspace_path": "/workspace/sales.csv",
  "message": "File uploaded successfully to MinIO and agent workspace"
}
```

**Test File List**:
```bash
curl "http://localhost:8000/api/v1/agent/project-files?project_name=test-project&role=user&department=technology&team=tech-team-1&username=john.doe"
```

**Verify in Workspace**:
```bash
docker exec rag-agent-runtime ls -lah /workspace/
```

---

## Frontend Implementation Reference

See these existing components for patterns:

1. **FileUpload.tsx** - File upload with drag-and-drop pattern
2. **ProjectSelector.tsx** - Project selection dropdown
3. **UploadedFilesList.tsx** - File list display pattern
4. **ChatInterface.tsx** - Project context integration

---

## Next Steps

1. Implement frontend enhancements in AgentTaskMonitor.tsx
2. Add currentUser prop to AgentTaskMonitor (for organizational context)
3. Test file upload flow end-to-end
4. Test file selection and task creation with file context
5. Verify files persist across agent task executions
6. Add error handling for failed uploads
7. Add progress indicators for file uploads

---

## Benefits of This Integration

1. **Unified File Management**: One system for both chat uploads and agent workspace files
2. **Organizational Compliance**: All files follow enterprise path structure
3. **RBAC Integration**: File access controlled by role/department/team
4. **Persistence**: Files stored in MinIO (permanent) + workspace (for agent tasks)
5. **Project Isolation**: Each project has its own file namespace
6. **Audit Trail**: All uploads tracked in database
7. **User Experience**: Drag-and-drop + browse existing files in one place

---

**Status**: Backend complete and tested. Frontend implementation guide provided above.

**Priority**: High - Enables file-based agent tasks with proper organizational structure

**Estimated Frontend Work**: 2-3 hours for full implementation
