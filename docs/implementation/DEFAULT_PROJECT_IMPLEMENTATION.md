# Default Project Implementation

**Date**: 2025-11-28
**Status**: In Progress

---

## Overview

Implement a "default" project for every user that automatically receives all uploads unless the user explicitly creates/selects a different project.

## User Feedback

> "believe by default all users should have a 'default' project and all uploads either via chat or upload files should directly go to default unless they create new specific projects.. what say ?"

**Analysis**: Excellent suggestion! This simplifies the user experience by:
1. Eliminating the need to create a project before uploading
2. Providing a fallback location for all uploads
3. Allowing users to organize later by creating specific projects

---

## Implementation Plan

### Phase 1: Database Changes

#### 1.1 Add default_project_id to User Model

**File**: `backend/app/models/database_enhanced.py`

```python
class User(Base):
    """User accounts with RBAC"""
    __tablename__ = "users"

    # ... existing fields ...

    # Default project for uploads
    default_project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True
    )
```

#### 1.2 Migration Script

**File**: `backend/migrations/012_add_default_project.sql`

```sql
-- Add default_project_id to users table
ALTER TABLE users
ADD COLUMN default_project_id UUID REFERENCES projects(id) ON DELETE SET NULL;

-- Create default projects for existing users
INSERT INTO projects (id, name, description, owner_id, department, status)
SELECT
    uuid_generate_v4(),
    'Default',
    'Default project for ' || username || '''s files',
    u.id,
    NULL,
    'active'
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM projects p
    WHERE p.owner_id = u.id
    AND p.name = 'Default'
);

-- Update users to reference their default projects
UPDATE users u
SET default_project_id = p.id
FROM projects p
WHERE p.owner_id = u.id
AND p.name = 'Default';

-- Create index for performance
CREATE INDEX idx_users_default_project ON users(default_project_id);
```

### Phase 2: Service Layer Changes

#### 2.1 Create Default Project Service

**File**: `backend/app/services/project_service.py`

```python
from sqlalchemy.orm import Session
from sqlalchemy import select
import uuid

from app.models.database_enhanced import User, Project, ProjectMember


async def ensure_default_project(user_id: uuid.UUID, db: Session) -> Project:
    """
    Ensure user has a default project. Create if doesn't exist.

    Args:
        user_id: User UUID
        db: Database session

    Returns:
        Project: The user's default project
    """
    # Get user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError(f"User {user_id} not found")

    # Check if user has default project
    if user.default_project_id:
        result = await db.execute(
            select(Project).where(Project.id == user.default_project_id)
        )
        project = result.scalar_one_or_none()
        if project:
            return project

    # Create default project
    project = Project(
        id=uuid.uuid4(),
        name="Default",
        description=f"Default project for {user.username}'s files",
        owner_id=user.id,
        status='active'
    )
    db.add(project)

    # Create project member
    member = ProjectMember(
        id=uuid.uuid4(),
        project_id=project.id,
        user_id=user.id,
        role='owner'
    )
    db.add(member)

    # Update user's default_project_id
    user.default_project_id = project.id

    await db.commit()
    await db.refresh(project)

    return project


async def get_user_upload_project(
    user_id: uuid.UUID,
    project_id: Optional[uuid.UUID],
    db: Session
) -> Project:
    """
    Get the project to use for uploading.

    If project_id is provided, use that.
    Otherwise, use user's default project.

    Args:
        user_id: User UUID
        project_id: Optional specific project UUID
        db: Database session

    Returns:
        Project: Project to use for upload
    """
    if project_id:
        # User specified a project
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        return project

    # Use default project
    return await ensure_default_project(user_id, db)
```

#### 2.2 Update Document Upload Service

**File**: `backend/app/services/document_service.py`

Modify upload functions to use default project:

```python
from app.services.project_service import get_user_upload_project

async def upload_document(
    file: UploadFile,
    user_id: uuid.UUID,
    project_id: Optional[uuid.UUID] = None,  # Now optional!
    db: Session = None
):
    """Upload document to user's project (default if not specified)"""

    # Get project to use
    project = await get_user_upload_project(user_id, project_id, db)

    # Rest of upload logic...
    # Use project.id for all references
```

### Phase 3: API Endpoint Changes

#### 3.1 Update Upload Endpoint

**File**: `backend/app/api/routes/__init__.py` or `backend/app/main.py`

```python
@router.post("/api/v1/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    project_id: Optional[str] = Form(None),  # Now optional!
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload file to project.

    If project_id is not provided, file goes to user's default project.
    """
    project_uuid = uuid.UUID(project_id) if project_id else None

    # Upload will use default project if project_uuid is None
    document = await document_service.upload_document(
        file=file,
        user_id=current_user.id,
        project_id=project_uuid,
        db=db
    )

    return {
        "document_id": str(document.id),
        "project_id": str(document.project_id),
        "project_name": "Default" if not project_id else document.project.name,
        "status": "processing"
    }
```

#### 3.2 Fix Teams Route

**File**: `backend/app/api/routes/teams_projects_routes.py`

The error was: `AttributeError: type object 'User' has no attribute 'team_id'`

Remove the team_id query from User model:

```python
@router.get("/teams", response_model=List[TeamResponse])
async def get_teams(
    department_id: Optional[str] = Query(None, description="Filter by department"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all teams, optionally filtered by department."""
    query = select(Team).where(Team.is_active == True)

    if department_id:
        query = query.where(Team.department_id == department_id)

    query = query.order_by(Team.name)

    result = await db.execute(query)
    teams = result.scalars().all()

    # Enrich with department names and member counts
    enriched_teams = []
    for team in teams:
        # Get department name
        dept_result = await db.execute(
            select(Department).where(Department.id == team.department_id)
        )
        dept = dept_result.scalar_one_or_none()

        # Get team lead username
        team_lead_username = None
        if team.team_lead_id:
            lead_result = await db.execute(
                select(User).where(User.id == team.team_lead_id)
            )
            lead = lead_result.scalar_one_or_none()
            if lead:
                team_lead_username = lead.username

        # REMOVED: User.team_id query - Users don't belong to teams directly
        # Projects belong to teams, not users
        # Count projects in this team instead
        from app.models.database_enhanced import Project
        project_count_result = await db.execute(
            select(func.count(Project.id))
            .where(Project.team_id == team.id)
        )
        project_count = project_count_result.scalar() or 0

        enriched_teams.append(TeamResponse(
            id=str(team.id),
            name=team.name,
            code=team.code,
            department_id=str(team.department_id),
            department_name=dept.name if dept else None,
            description=team.description,
            team_lead_id=str(team.team_lead_id) if team.team_lead_id else None,
            team_lead_username=team_lead_username,
            member_count=project_count,  # Changed to project_count
            is_active=team.is_active
        ))

    return enriched_teams
```

### Phase 4: Frontend Changes

#### 4.1 Update FileUpload Component

**File**: `frontend/src/components/FileUpload.tsx`

Make project selection optional:

```typescript
export const FileUpload: React.FC = () => {
  const [selectedProject, setSelectedProject] = useState<string | null>(null);

  const handleUpload = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);

    // Only add project_id if user selected one
    if (selectedProject) {
      formData.append('project_id', selectedProject);
    }
    // If no project selected, backend will use default project

    const response = await axios.post('/api/v1/upload', formData);
    // Show success message
  };

  return (
    <div>
      {/* Make project selector optional */}
      <div className="mb-4">
        <label className="text-sm text-gray-400">
          Project (optional - defaults to "Default")
        </label>
        <ProjectSelector
          value={selectedProject}
          onChange={setSelectedProject}
          allowEmpty={true}  // Allow no selection
        />
      </div>

      {/* File upload UI */}
    </div>
  );
};
```

#### 4.2 Update Chat Upload

When uploading via chat, always use default project:

```typescript
// In ChatInterface.tsx
const handleFileUploadInChat = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('session_id', sessionId);
  // Don't specify project_id - will use default

  await axios.post('/api/v1/upload', formData);
};
```

### Phase 5: User Flow

#### 5.1 New User Registration

When new user is created:

```python
# In auth service or user creation
async def create_user(username: str, email: str, password: str, db: Session):
    # Create user
    user = User(
        id=uuid.uuid4(),
        username=username,
        email=email,
        # ... other fields
    )
    db.add(user)
    await db.flush()  # Get user ID

    # Create default project
    from app.services.project_service import ensure_default_project
    await ensure_default_project(user.id, db)

    await db.commit()
    return user
```

#### 5.2 Existing Users

Migration script already handles this - creates default projects for all existing users.

---

## Benefits

1. **Simplified UX**: Users can upload immediately without creating projects
2. **Backward Compatible**: Existing explicit project selection still works
3. **Organization**: Users can organize files into specific projects later
4. **Consistent**: Chat uploads and file uploads behave the same way
5. **Flexible**: Users can still create specific projects when needed

---

## Testing Plan

1. **New User Test**:
   - Create new user
   - Verify "Default" project is auto-created
   - Verify user.default_project_id is set

2. **Upload Test (No Project)**:
   - Upload file without specifying project
   - Verify file goes to default project
   - Check documents table has correct project_id

3. **Upload Test (With Project)**:
   - Create specific project
   - Upload file with project_id specified
   - Verify file goes to specified project, not default

4. **Chat Upload Test**:
   - Upload file via chat interface
   - Verify file goes to default project
   - Verify file is searchable in RAG

5. **Library View Test**:
   - View library
   - Verify "Default" project appears in project list
   - Verify files show up under default project

---

## Implementation Steps

### Immediate (Now):
1. ✅ Create implementation document
2. ⏳ Add default_project_id to User model
3. ⏳ Create and run migration
4. ⏳ Create project_service.py
5. ⏳ Fix teams route (remove User.team_id query)

### Next:
6. Update document upload service
7. Update API endpoints
8. Update frontend components
9. Test complete flow
10. Document in BUILD_AND_TEST_RESULTS.md

---

## Files to Modify

### Backend:
- [x] `backend/app/models/database_enhanced.py` - Add default_project_id
- [x] `backend/migrations/012_add_default_project.sql` - Migration
- [ ] `backend/app/services/project_service.py` - New file
- [ ] `backend/app/services/document_service.py` - Update upload
- [ ] `backend/app/api/routes/teams_projects_routes.py` - Fix teams route
- [ ] `backend/app/api/routes/__init__.py` or `main.py` - Update upload endpoint
- [ ] `backend/app/api/routes/auth.py` - Update user creation

### Frontend:
- [ ] `frontend/src/components/FileUpload.tsx` - Make project optional
- [ ] `frontend/src/components/ChatInterface.tsx` - Use default project
- [ ] `frontend/src/components/ProjectSelector.tsx` - Add allowEmpty prop

---

## Current Status

**In Progress**: Adding default_project_id to User model and creating migration

**Next Action**: Apply migration and create project_service.py

---
