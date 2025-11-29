# Library and Project Management Implementation Guide

**Created**: 2025-11-28
**Priority**: P0
**Status**: 📋 PLANNING
**Related**: P0_UI_UX_RBAC_ENHANCEMENT_REQUEST.md (Enhancement #10, #11)

---

## 🎯 Objective

Implement a ChatGPT-style **Library** feature and **Project Management** system with:

1. **Hierarchical File Organization**: `Username → Role → Department → Project → Files`
2. **Library UI**: Browse all uploaded files across all projects (like ChatGPT)
3. **Project Context**: Every file/chat belongs to a project
4. **Complete Traceability**: Know who uploaded what, when, and for which project
5. **File Management**: Preview, download, delete, search, and filter

---

## 📐 Architecture Overview

### Database Schema Enhancement

```sql
-- Step 1: Add project tracking to documents
ALTER TABLE documents
ADD COLUMN project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
ADD COLUMN uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
ADD COLUMN department VARCHAR(100),
ADD COLUMN minio_path VARCHAR(1024);

CREATE INDEX idx_documents_project_id ON documents(project_id);
CREATE INDEX idx_documents_uploaded_by ON documents(uploaded_by);
CREATE INDEX idx_documents_department ON documents(department);

-- Step 2: Add project tracking to document_chunks
ALTER TABLE document_chunks
ADD COLUMN project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
ADD COLUMN uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX idx_chunks_project_id ON document_chunks(project_id);

-- Step 3: Add project tracking to chat sessions
ALTER TABLE chat_sessions
ADD COLUMN project_id UUID REFERENCES projects(id) ON DELETE SET NULL;

CREATE INDEX idx_sessions_project_id ON chat_sessions(project_id);
```

### MinIO Path Structure

```
minio://ragchatbot/
├── {username}/                    # e.g., "john.doe"
│   ├── {role}/                    # e.g., "admin"
│   │   ├── {department}/          # e.g., "technology"
│   │   │   ├── {project_name}/    # e.g., "chatbot-rag"
│   │   │   │   ├── documents/     # User uploads
│   │   │   │   │   ├── requirements.pdf
│   │   │   │   │   ├── design.docx
│   │   │   │   │   └── data.xlsx
│   │   │   │   ├── extractions/   # Extracted data
│   │   │   │   │   └── output.json
│   │   │   │   └── exports/       # Chat exports, reports
│   │   │   │       ├── conversation_2024.pdf
│   │   │   │       └── report.xlsx
```

**Example Path**:
```
john.doe/admin/technology/chatbot-rag/documents/requirements.pdf
```

---

## 🎨 UI Design

### 1. Enhanced Sidebar (Add Library Menu Item)

```typescript
// frontend/src/components/Sidebar.tsx
const tabs = [
  { id: 'dashboard', icon: Home, label: 'Dashboard' },
  { id: 'chat', icon: MessageSquare, label: 'Chat' },
  { id: 'history', icon: History, label: 'Chat History' },
  { id: 'library', icon: FolderOpen, label: 'Library' },  // 🆕 NEW
  { id: 'upload', icon: Upload, label: 'Upload Files' },
  { id: 'scrape', icon: Globe, label: 'Web Scraping' },
  // ... rest
]
```

### 2. Library Component (Three-Panel Layout)

```typescript
// frontend/src/components/Library.tsx

import { useState } from 'react'
import { FolderOpen, File, Download, Trash2, Eye, Search, Filter } from 'lucide-react'

interface LibraryProps {
  currentUser: User
}

export default function Library({ currentUser }: LibraryProps) {
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const [selectedFile, setSelectedFile] = useState<Document | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState<'all' | 'pdf' | 'docx' | 'xlsx'>('all')

  return (
    <div className="flex h-full">
      {/* LEFT PANEL: Projects */}
      <ProjectListPanel
        currentUser={currentUser}
        selectedProject={selectedProject}
        onSelectProject={setSelectedProject}
      />

      {/* CENTER PANEL: Files Grid */}
      <FileGridPanel
        project={selectedProject}
        searchQuery={searchQuery}
        filterType={filterType}
        selectedFile={selectedFile}
        onSelectFile={setSelectedFile}
        onSearch={setSearchQuery}
        onFilter={setFilterType}
      />

      {/* RIGHT PANEL: File Preview */}
      {selectedFile && (
        <FilePreviewPanel
          file={selectedFile}
          onClose={() => setSelectedFile(null)}
        />
      )}
    </div>
  )
}
```

### 3. Project List Panel (Left Sidebar)

```typescript
// Component shows all projects user has access to
interface ProjectListPanelProps {
  currentUser: User
  selectedProject: Project | null
  onSelectProject: (project: Project) => void
}

function ProjectListPanel({ currentUser, selectedProject, onSelectProject }: ProjectListPanelProps) {
  const [projects, setProjects] = useState<Project[]>([])
  const [showCreateModal, setShowCreateModal] = useState(false)

  return (
    <div className="w-64 border-r bg-slate-50 dark:bg-slate-900 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b">
        <h2 className="font-semibold text-sm">My Projects</h2>
        <button
          onClick={() => setShowCreateModal(true)}
          className="mt-3 w-full btn-primary"
        >
          <Plus className="w-4 h-4" />
          New Project
        </button>
      </div>

      {/* Project List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {projects.map(project => (
          <button
            key={project.id}
            onClick={() => onSelectProject(project)}
            className={`w-full p-3 rounded-lg text-left transition ${
              selectedProject?.id === project.id
                ? 'bg-primary-100 dark:bg-primary-900'
                : 'hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            <div className="flex items-center gap-2">
              <FolderOpen className="w-4 h-4" />
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm truncate">{project.name}</p>
                <p className="text-xs text-slate-500">{project.file_count} files</p>
              </div>
            </div>
          </button>
        ))}
      </div>

      {/* Storage Stats */}
      <div className="p-4 border-t">
        <StorageQuotaDisplay currentUser={currentUser} />
      </div>
    </div>
  )
}
```

### 4. File Grid Panel (Center)

```typescript
interface FileGridPanelProps {
  project: Project | null
  searchQuery: string
  filterType: string
  selectedFile: Document | null
  onSelectFile: (file: Document) => void
  onSearch: (query: string) => void
  onFilter: (type: string) => void
}

function FileGridPanel({
  project,
  searchQuery,
  filterType,
  selectedFile,
  onSelectFile,
  onSearch,
  onFilter
}: FileGridPanelProps) {
  const [files, setFiles] = useState<Document[]>([])
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')

  return (
    <div className="flex-1 flex flex-col">
      {/* Toolbar */}
      <div className="p-4 border-b flex items-center gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search files..."
            value={searchQuery}
            onChange={(e) => onSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-lg"
          />
        </div>

        <select
          value={filterType}
          onChange={(e) => onFilter(e.target.value)}
          className="px-3 py-2 border rounded-lg"
        >
          <option value="all">All Files</option>
          <option value="pdf">PDF</option>
          <option value="docx">Word</option>
          <option value="xlsx">Excel</option>
          <option value="txt">Text</option>
        </select>

        <div className="flex gap-1 border rounded-lg p-1">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-1.5 rounded ${viewMode === 'grid' ? 'bg-primary-100' : ''}`}
          >
            <Grid className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-1.5 rounded ${viewMode === 'list' ? 'bg-primary-100' : ''}`}
          >
            <List className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* File Grid/List */}
      <div className="flex-1 overflow-y-auto p-4">
        {!project ? (
          <EmptyState message="Select a project to view files" />
        ) : viewMode === 'grid' ? (
          <FileGrid
            files={files}
            selectedFile={selectedFile}
            onSelectFile={onSelectFile}
          />
        ) : (
          <FileList
            files={files}
            selectedFile={selectedFile}
            onSelectFile={onSelectFile}
          />
        )}
      </div>
    </div>
  )
}
```

### 5. File Preview Panel (Right Sidebar)

```typescript
interface FilePreviewPanelProps {
  file: Document
  onClose: () => void
}

function FilePreviewPanel({ file, onClose }: FilePreviewPanelProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  return (
    <div className="w-96 border-l bg-white dark:bg-slate-900 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b flex items-center justify-between">
        <h3 className="font-semibold text-sm">File Details</h3>
        <button onClick={onClose}>
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Preview */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Thumbnail/Preview */}
        <div className="aspect-video bg-slate-100 dark:bg-slate-800 rounded-lg flex items-center justify-center">
          {previewUrl ? (
            <img src={previewUrl} alt={file.filename} className="max-w-full max-h-full" />
          ) : (
            <File className="w-16 h-16 text-slate-400" />
          )}
        </div>

        {/* Metadata */}
        <div className="space-y-2 text-sm">
          <div>
            <span className="text-slate-500">Filename:</span>
            <p className="font-medium break-all">{file.filename}</p>
          </div>
          <div>
            <span className="text-slate-500">Size:</span>
            <p className="font-medium">{formatFileSize(file.file_size)}</p>
          </div>
          <div>
            <span className="text-slate-500">Type:</span>
            <p className="font-medium">{file.file_type}</p>
          </div>
          <div>
            <span className="text-slate-500">Uploaded:</span>
            <p className="font-medium">{formatDate(file.upload_date)}</p>
          </div>
          <div>
            <span className="text-slate-500">Project:</span>
            <p className="font-medium">{file.project?.name || 'N/A'}</p>
          </div>
          <div>
            <span className="text-slate-500">Uploaded by:</span>
            <p className="font-medium">{file.uploaded_by?.username || 'Unknown'}</p>
          </div>
          <div>
            <span className="text-slate-500">Status:</span>
            <span className={`inline-flex px-2 py-1 rounded text-xs ${
              file.processed ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
            }`}>
              {file.processed ? '✓ Processed' : '⏳ Processing'}
            </span>
          </div>
          {file.chunk_count > 0 && (
            <div>
              <span className="text-slate-500">Chunks:</span>
              <p className="font-medium">{file.chunk_count} embeddings</p>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="space-y-2">
          <button className="w-full btn-secondary">
            <Download className="w-4 h-4" />
            Download
          </button>
          <button className="w-full btn-secondary">
            <Eye className="w-4 h-4" />
            View Content
          </button>
          <button className="w-full btn-danger">
            <Trash2 className="w-4 h-4" />
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}
```

---

## 🔧 Backend Implementation

### 1. MinIO Path Builder Service

```python
# backend/app/services/minio_path_builder.py

from typing import Optional
from app.models.database_enhanced import User
from app.models.database import Document

class MinIOPathBuilder:
    """Build hierarchical MinIO paths: username/role/department/project/folder/filename"""

    @staticmethod
    def build_document_path(
        username: str,
        role: str,
        department: str,
        project_name: str,
        filename: str,
        folder: str = "documents"
    ) -> str:
        """
        Build MinIO object path.

        Example: john.doe/admin/technology/chatbot-rag/documents/requirements.pdf
        """
        # Sanitize components (remove special chars, spaces)
        username = MinIOPathBuilder._sanitize(username)
        role = MinIOPathBuilder._sanitize(role)
        department = MinIOPathBuilder._sanitize(department)
        project_name = MinIOPathBuilder._sanitize(project_name)

        return f"{username}/{role}/{department}/{project_name}/{folder}/{filename}"

    @staticmethod
    def _sanitize(component: str) -> str:
        """Sanitize path component (remove special chars, lowercase)"""
        import re
        # Replace spaces with hyphens, lowercase, remove special chars
        sanitized = component.lower().strip()
        sanitized = re.sub(r'\s+', '-', sanitized)
        sanitized = re.sub(r'[^a-z0-9\-_.]', '', sanitized)
        return sanitized

    @staticmethod
    def parse_path(minio_path: str) -> dict:
        """
        Parse MinIO path back into components.

        Returns: {username, role, department, project, folder, filename}
        """
        parts = minio_path.split('/')
        if len(parts) < 6:
            raise ValueError(f"Invalid MinIO path format: {minio_path}")

        return {
            'username': parts[0],
            'role': parts[1],
            'department': parts[2],
            'project': parts[3],
            'folder': parts[4],
            'filename': '/'.join(parts[5:])  # Handle filenames with slashes
        }
```

### 2. Updated Document Service

```python
# backend/app/services/document_service.py (update upload_file method)

async def upload_file(
    self,
    file_data: bytes,
    filename: str,
    file_type: str,
    user: User,  # 🆕 NEW: User object
    project_id: str,  # 🆕 NEW: Project ID
    source_type: str = "upload",
    source_url: Optional[str] = None,
    session_id: Optional[str] = None,
    db: AsyncSession = None
) -> Document:
    """Upload file to MinIO with hierarchical path and create database record"""
    if not self._initialized:
        await self.initialize()

    try:
        # Get project details
        from app.models.database import Project
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Build hierarchical MinIO path
        from app.services.minio_path_builder import MinIOPathBuilder
        object_name = MinIOPathBuilder.build_document_path(
            username=user.username,
            role=user.role,
            department=user.department or 'default',
            project_name=project.name,
            filename=filename,
            folder='documents'
        )

        # Upload to MinIO
        self.minio_client.put_object(
            settings.MINIO_BUCKET_NAME,
            object_name,
            io.BytesIO(file_data),
            length=len(file_data),
            content_type=file_type
        )

        logger.info(f"Uploaded file to MinIO: {object_name}")

        # Create database record with full traceability
        document = Document(
            id=uuid.uuid4(),
            filename=filename,
            file_path=object_name,  # Full hierarchical path
            minio_path=object_name,  # Store path for reference
            file_type=file_type,
            file_size=len(file_data),
            source_type=source_type,
            source_url=source_url,
            project_id=project_id,  # 🆕 NEW
            uploaded_by=user.id,  # 🆕 NEW
            department=user.department,  # 🆕 NEW
            processed=False
        )

        db.add(document)
        await db.flush()
        await db.refresh(document)

        # Associate with session if provided
        if session_id:
            # ... existing session association logic ...
            pass

        return document

    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise
```

### 3. Library API Endpoints

```python
# backend/app/api/routes/library_routes.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from app.core.database import get_db
from app.models.database import Document, Project
from app.models.database_enhanced import User
from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/library", tags=["library"])

@router.get("/projects")
async def get_user_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all projects accessible by current user"""
    result = await db.execute(
        select(Project)
        .where(
            or_(
                Project.owner_id == current_user.id,
                Project.department == current_user.department
            )
        )
        .order_by(Project.updated_at.desc())
    )
    projects = result.scalars().all()

    # Enrich with file counts
    enriched = []
    for project in projects:
        file_count_result = await db.execute(
            select(func.count(Document.id))
            .where(Document.project_id == project.id)
        )
        file_count = file_count_result.scalar()

        enriched.append({
            **project.__dict__,
            'file_count': file_count
        })

    return {"projects": enriched}

@router.get("/projects/{project_id}/files")
async def get_project_files(
    project_id: str,
    search: Optional[str] = Query(None),
    file_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all files in a project with optional search and filter"""
    query = select(Document).where(Document.project_id == project_id)

    if search:
        query = query.where(Document.filename.ilike(f"%{search}%"))

    if file_type and file_type != 'all':
        query = query.where(Document.file_type == file_type)

    query = query.order_by(Document.upload_date.desc())

    result = await db.execute(query)
    files = result.scalars().all()

    return {"files": files}

@router.get("/files/{file_id}/download-url")
async def get_file_download_url(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate presigned URL for file download"""
    from app.services.document_service import document_service

    # Get document
    result = await db.execute(select(Document).where(Document.id == file_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="File not found")

    # Generate presigned URL (valid for 1 hour)
    url = document_service.minio_client.presigned_get_object(
        settings.MINIO_BUCKET_NAME,
        document.minio_path,
        expires=timedelta(hours=1)
    )

    return {"download_url": url}

@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete file from both MinIO and database"""
    from app.services.document_service import document_service

    # Get document
    result = await db.execute(select(Document).where(Document.id == file_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="File not found")

    # Check permissions
    if document.uploaded_by != current_user.id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized to delete this file")

    # Delete from MinIO
    try:
        document_service.minio_client.remove_object(
            settings.MINIO_BUCKET_NAME,
            document.minio_path
        )
    except Exception as e:
        logger.warning(f"Could not delete from MinIO: {e}")

    # Delete from database (cascade will delete chunks)
    await db.delete(document)
    await db.commit()

    return {"message": "File deleted successfully"}

@router.get("/storage/stats")
async def get_storage_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get storage usage statistics for current user"""
    # Total files
    total_files_result = await db.execute(
        select(func.count(Document.id))
        .where(Document.uploaded_by == current_user.id)
    )
    total_files = total_files_result.scalar()

    # Total size
    total_size_result = await db.execute(
        select(func.sum(Document.file_size))
        .where(Document.uploaded_by == current_user.id)
    )
    total_size = total_size_result.scalar() or 0

    # By project
    by_project_result = await db.execute(
        select(
            Project.name,
            func.count(Document.id).label('file_count'),
            func.sum(Document.file_size).label('total_size')
        )
        .join(Document, Document.project_id == Project.id)
        .where(Document.uploaded_by == current_user.id)
        .group_by(Project.id, Project.name)
    )
    by_project = [
        {
            'project': row.name,
            'file_count': row.file_count,
            'total_size': row.total_size
        }
        for row in by_project_result
    ]

    return {
        'total_files': total_files,
        'total_size': total_size,
        'by_project': by_project
    }
```

### 4. Project Management API

```python
# backend/app/api/routes/project_routes.py

@router.post("/projects")
async def create_project(
    name: str,
    description: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new project"""
    project = Project(
        id=uuid.uuid4(),
        name=name,
        description=description,
        owner_id=current_user.id,
        department=current_user.department,
        status='active'
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    return {"project": project}
```

---

## 📋 Implementation Checklist

### Phase 1: Database & Backend (Week 1)
- [ ] Create migration 007: Add project tracking to documents/chunks/sessions
- [ ] Update Document model in database.py
- [ ] Create MinIOPathBuilder service
- [ ] Update document_service.py upload_file method
- [ ] Create library_routes.py API
- [ ] Create project_routes.py API
- [ ] Add audit logging for library actions

### Phase 2: Frontend Components (Week 2)
- [ ] Create Library.tsx main component
- [ ] Create ProjectListPanel.tsx
- [ ] Create FileGridPanel.tsx
- [ ] Create FilePreviewPanel.tsx
- [ ] Create ProjectSelector.tsx (reusable)
- [ ] Update Sidebar.tsx (add Library menu item)
- [ ] Update FileUpload.tsx (add project selector)

### Phase 3: Integration & Testing (Week 3)
- [ ] Integrate library with existing upload flow
- [ ] Add project context to chat sessions
- [ ] Test file upload with hierarchical paths
- [ ] Test file download/delete
- [ ] Test search and filtering
- [ ] Add loading states and error handling
- [ ] Performance testing with large file counts

---

## 🎨 UI/UX Features

### Library Features (ChatGPT-style)
1. **Three-panel layout**: Projects | Files | Preview
2. **Grid and List views**: Toggle between visualizations
3. **Search**: Real-time file search
4. **Filters**: By type, date, project
5. **Actions**: Download, Preview, Delete
6. **Storage stats**: Visual quota display
7. **Drag & drop**: Upload directly to project
8. **Breadcrumbs**: Navigate folder hierarchy

### Project Selector (Everywhere)
- File Upload → Select project before upload
- New Chat → Select project context
- Web Scraping → Select project for scraped data
- Project Estimator → Link to project

---

## 🔒 Security & Permissions

### Access Control
- Users can only see their own files + shared project files
- Department admins can see department files
- System admins can see all files
- File deletion requires ownership or admin role

### Audit Trail
Every action logged:
- File upload: who, what, when, which project
- File download: who accessed what
- File delete: who deleted what
- Project create/update/delete

---

## 📊 Success Metrics

1. **Traceability**: 100% of files have project/user association
2. **Usability**: Users find files in <5 seconds
3. **Adoption**: 80%+ users use Library vs. old upload list
4. **Storage**: 20% reduction through cleanup
5. **Performance**: Library loads <2 seconds with 1000+ files

---

## 🚀 Quick Start (After Implementation)

### For Users:
1. Create a project: Library → New Project
2. Upload files: Upload Files → Select Project → Upload
3. Browse files: Library → Select Project → View Files
4. Preview/Download: Click file → View details → Download

### For Admins:
1. View all files: Library → All Projects
2. Monitor storage: Library → Storage Stats
3. Cleanup: Library → Select files → Delete

---

**END OF DOCUMENT**
