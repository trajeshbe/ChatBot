# MinIO Organizational Path Implementation - Status

**Date**: 2025-11-28
**Status**: ⚠️ Not Yet Implemented
**User Request**: Files uploaded should follow organizational path structure in MinIO

---

## 🔍 Current State

### What's Working ✅
1. **User Management**: Users have department, function, and teams assigned in database
2. **Database Schema**: All organizational fields exist:
   - `users.department_id`
   - `users.function`
   - `user_teams` junction table
3. **Admin UI**: Can assign dept/function/teams to users
4. **File Upload**: Files successfully upload to MinIO
5. **Document Processing**: Files are chunked and embedded correctly

### What's NOT Working ❌
1. **MinIO Path Structure**: Files stored with flat UUID filenames:
   - Current: `36a792de-be5a-485c-b498-b21a65bfee16.pdf`
   - Expected: `/Technology/DevOps-Team/admin/Default/DA_Approval_Document.pdf`
2. **User Context in Upload**: Upload endpoint uses anonymous user, not authenticated user
3. **Organizational Metadata**: document_chunks fields are NULL:
   - `project_id`: NULL
   - `uploaded_by`: NULL
   - `department`: NULL
   - `team`: NULL

---

## 📊 Database Verification

### Current Upload (DA_Approval_Document.pdf)

**Document**:
```sql
SELECT id, filename, file_path, minio_path
FROM documents
WHERE filename='DA_Approval_Document.pdf';

Result:
id: 36a792de-be5a-485c-b498-b21a65bfee16
filename: DA_Approval_Document.pdf
file_path: 36a792de-be5a-485c-b498-b21a65bfee16.pdf
minio_path: NULL ❌
```

**Document Chunks**:
```sql
SELECT project_id, uploaded_by, department, team
FROM document_chunks
WHERE document_id='36a792de-be5a-485c-b498-b21a65bfee16';

Result:
project_id: NULL ❌
uploaded_by: NULL ❌
department: NULL ❌
team: NULL ❌
```

### Admin User Status

```sql
SELECT u.username, u.department_id, u.function, d.name as dept_name
FROM users u
LEFT JOIN departments d ON u.department_id = d.id
WHERE u.username = 'admin';

Result:
username: admin
department_id: c5f6f8e3-432a-47dd-ba80-3b9516e2e174 ✅
function: NULL (needs assignment via UI)
dept_name: Technology ✅
```

**Note**: Admin has department but no function or teams assigned yet.

---

## 🔧 What Needs to Be Implemented

### Phase 1: Add Authentication to Upload Endpoint

**File**: `backend/app/main.py` line 328

**Current Code** (line 341):
```python
user_id = await get_anonymous_user_id(db)
```

**Needs to Change To**:
```python
# Get authenticated user from token/session
current_user = await get_current_user_from_request(request, db)
if not current_user:
    raise HTTPException(status_code=401, detail="Authentication required")

user_id = current_user.id
```

**New Dependency Needed**:
```python
from app.core.security import get_current_user_from_request
```

### Phase 2: Fetch User Organizational Info

**Add to Upload Endpoint** (after getting user):
```python
# Fetch user's organizational details
from app.models.rbac import Department, Team
from app.models.database_enhanced import UserTeam

# Get department
department_name = None
if current_user.department_id:
    dept_query = select(Department).where(Department.id == current_user.department_id)
    dept_result = await db.execute(dept_query)
    dept = dept_result.scalar_one_or_none()
    if dept:
        department_name = dept.name

# Get primary team
team_name = None
teams_query = select(UserTeam, Team).join(
    Team, UserTeam.team_id == Team.id
).where(
    UserTeam.user_id == current_user.id,
    UserTeam.is_primary == True
).limit(1)
teams_result = await db.execute(teams_query)
user_team_data = teams_result.first()
if user_team_data:
    team_name = user_team_data[1].name  # Team.name

# Get user's default project
project_name = "Default"  # Or fetch from current_user.default_project_id

function_name = current_user.function or "General"
```

### Phase 3: Construct MinIO Path

**Proposed Path Structure**:
```
/{department}/{team}/{username}/{project}/{filename}
```

**Example**:
```
/Technology/DevOps-Team/admin/Default/DA_Approval_Document.pdf
```

**Implementation**:
```python
def construct_minio_path(
    department: str,
    team: str,
    username: str,
    project: str,
    filename: str
) -> str:
    """
    Construct hierarchical MinIO path.

    Returns: "Technology/DevOps-Team/admin/Default/DA_Approval_Document.pdf"
    """
    # Sanitize path components
    safe_dept = department.replace(" ", "-") if department else "Unassigned"
    safe_team = team.replace(" ", "-") if team else "General"
    safe_project = project.replace(" ", "-")

    return f"{safe_dept}/{safe_team}/{username}/{safe_project}/{filename}"

# Use in upload
minio_path = construct_minio_path(
    department=department_name or "Unassigned",
    team=team_name or "General",
    username=current_user.username,
    project=project_name,
    filename=file.filename
)
```

### Phase 4: Update Document Service

**File**: `backend/app/services/document_service.py`

**Update `upload_file()` method**:
```python
async def upload_file(
    self,
    file_data: bytes,
    filename: str,
    file_type: str,
    source_type: str,
    db: AsyncSession,
    user_id: Optional[UUID] = None,  # ← Add
    department: Optional[str] = None,  # ← Add
    team: Optional[str] = None,  # ← Add
    project_id: Optional[UUID] = None,  # ← Add
    minio_path: Optional[str] = None  # ← Add
) -> Document:
    # ... existing code ...

    # Store with MinIO path
    document = Document(
        filename=filename,
        file_path=stored_filename,  # UUID.pdf (for backward compat)
        minio_path=minio_path,  # ← NEW: hierarchical path
        # ... other fields ...
    )
```

**Update `process_document()` method**:
```python
async def process_document(
    self,
    document_id: UUID,
    db: AsyncSession,
    user_id: Optional[UUID] = None,  # ← Add
    department: Optional[str] = None,  # ← Add
    team: Optional[str] = None,  # ← Add
    project_id: Optional[UUID] = None  # ← Add
) -> List[DocumentChunk]:
    # When creating chunks
    chunk = DocumentChunk(
        document_id=document_id,
        chunk_index=i,
        content=chunk_text,
        embedding=chunk_embedding,
        project_id=project_id,  # ← Set
        uploaded_by=user_id,  # ← Set
        department=department,  # ← Set
        team=team  # ← Set
    )
```

### Phase 5: Update Upload Endpoint to Pass Org Info

**File**: `backend/app/main.py` line 392

**Current**:
```python
document = await document_service.upload_file(
    file_data=file_data,
    filename=file.filename,
    file_type=file.content_type,
    source_type="upload",
    db=db
)
```

**Updated**:
```python
document = await document_service.upload_file(
    file_data=file_data,
    filename=file.filename,
    file_type=file.content_type,
    source_type="upload",
    db=db,
    user_id=user_id,
    department=department_name,
    team=team_name,
    project_id=current_user.default_project_id,
    minio_path=minio_path
)
```

**Line 404** (process_document):
```python
chunks = await document_service.process_document(
    document.id,
    db,
    user_id=user_id,
    department=department_name,
    team=team_name,
    project_id=current_user.default_project_id
)
```

---

## 🎯 Proposed MinIO Directory Structure

### Example Hierarchy

```
chatbot/
├── Technology/
│   ├── DevOps-Team/
│   │   ├── admin/
│   │   │   ├── Default/
│   │   │   │   ├── DA_Approval_Document.pdf
│   │   │   │   └── Technical_Spec.docx
│   │   │   └── Project-Alpha/
│   │   │       └── Requirements.pdf
│   │   └── john.doe/
│   │       └── Default/
│   │           └── Report.pdf
│   ├── Platform-Team/
│   │   └── jane.smith/
│   │       └── Default/
│   │           └── Architecture.pdf
│   └── Data-Engineering-Team/
│       └── bob.wilson/
│           └── Default/
│               └── ETL_Pipeline.pdf
├── Data-Operations/
│   └── Analytics-Team/
│       └── alice.johnson/
│           └── Default/
│               └── Dashboard_Design.pdf
└── Unassigned/
    └── General/
        └── anonymous/
            └── Default/
                └── public_upload.pdf
```

### Benefits

1. **Organizational Clarity**: Easy to see who uploaded what
2. **Access Control**: Can implement team-based permissions
3. **Auditing**: Clear ownership trail
4. **Cleanup**: Easy to remove files by dept/team/user
5. **Reporting**: Can analyze usage by organization
6. **Backup**: Can backup by department or team

---

## 🔐 Security Considerations

### Authentication Required

The upload endpoint will need to:
1. Require authentication (Bearer token or session)
2. Validate user has permission to upload
3. Ensure user can only upload to their own path
4. Prevent path traversal attacks

### Path Sanitization

```python
def sanitize_path_component(component: str) -> str:
    """Remove dangerous characters from path components"""
    # Remove: / \ .. : * ? " < > |
    sanitized = re.sub(r'[/\\:*?"<>|]', '', component)
    sanitized = sanitized.replace('..', '')
    return sanitized.strip()
```

### Fallback for Unassigned Users

Users without department/team should still be able to upload:
```
/Unassigned/General/{username}/Default/{filename}
```

---

## 📋 Implementation Checklist

### Backend Changes

- [ ] Add authentication helper function `get_current_user_from_request()`
- [ ] Update `/api/v1/upload` endpoint to get authenticated user
- [ ] Fetch user's department, team, project from database
- [ ] Create `construct_minio_path()` utility function
- [ ] Update `document_service.upload_file()` signature
- [ ] Update `document_service.process_document()` signature
- [ ] Pass organizational info when creating documents
- [ ] Pass organizational info when creating document_chunks
- [ ] Add path sanitization for security
- [ ] Handle users without department/team (fallback)

### Frontend Changes

- [ ] Ensure upload component sends authentication token
- [ ] Update FileUpload.tsx to include auth header
- [ ] Display upload path to user after successful upload
- [ ] Show organizational context in uploaded files list

### Database Migration

- [ ] Verify `documents.minio_path` column exists (already exists)
- [ ] Verify `document_chunks` organizational columns exist (already exist)
- [ ] No new migration needed (schema ready)

### Testing

- [ ] Test upload with admin user (has dept, no function/teams)
- [ ] Test upload after assigning function/teams to admin
- [ ] Test upload with user without dept/team (fallback)
- [ ] Test MinIO paths are correct
- [ ] Test document_chunks have organizational fields populated
- [ ] Verify files are accessible at new paths
- [ ] Test path sanitization (special characters)

---

## 🧪 Testing Steps (After Implementation)

### 1. Assign Admin User Organizational Fields
```bash
# Via UI at http://localhost:3001/admin
1. Click "Edit" on admin user
2. Department: Technology (already set)
3. Function: System Administrator
4. Teams: Select DevOps Team (primary)
5. Save
```

### 2. Upload a Test File
```bash
# Via UI at http://localhost:3001
1. Login as admin
2. Upload DA_Approval_Document.pdf
3. Should see success message with path
```

### 3. Verify MinIO Path
```sql
SELECT id, filename, file_path, minio_path
FROM documents
WHERE filename='DA_Approval_Document.pdf'
ORDER BY upload_date DESC LIMIT 1;

Expected minio_path:
Technology/DevOps-Team/admin/Default/DA_Approval_Document.pdf
```

### 4. Verify Document Chunks
```sql
SELECT project_id, uploaded_by, department, team
FROM document_chunks
WHERE document_id = '<document_id>';

Expected:
project_id: <admin's default_project_id>
uploaded_by: <admin's user_id>
department: Technology
team: DevOps Team
```

### 5. Verify MinIO File Location
```bash
# Access MinIO console: http://localhost:9001
# Login: minioadmin / minioadmin
# Navigate to: ragchatbot bucket
# Path should be: Technology/DevOps-Team/admin/Default/DA_Approval_Document.pdf
```

---

## 🚧 Current Limitations

1. **No Authentication on Upload**: Anyone can upload without logging in
2. **Anonymous User Default**: Upload uses generic anonymous user ID
3. **No Organizational Context**: Files don't capture who uploaded them
4. **Flat MinIO Structure**: All files stored as UUID.pdf in bucket root
5. **No Access Control**: Can't restrict files by team/department
6. **No Usage Tracking**: Can't see uploads by org unit

---

## 💡 Future Enhancements

1. **Team-based Access Control**: Only team members can see team's files
2. **Department Quotas**: Limit storage per department
3. **Retention Policies**: Auto-delete old files per org policy
4. **Usage Analytics**: Dashboard showing uploads by dept/team
5. **Shared Projects**: Multiple teams can access same project folder
6. **File Versioning**: Keep version history with org context

---

## 📝 Summary

### Current Status
- ✅ Database schema ready (all columns exist)
- ✅ User organizational management working
- ✅ Admin UI for assigning dept/function/teams working
- ❌ Upload doesn't use authenticated user
- ❌ MinIO paths are flat (UUID filenames)
- ❌ Organizational metadata not populated

### Required Work
1. Add authentication to upload endpoint
2. Fetch user organizational details
3. Construct hierarchical MinIO paths
4. Update document service to accept org info
5. Pass org info when creating documents/chunks
6. Test and verify

### Estimated Effort
- **Backend Changes**: ~2-3 hours
- **Frontend Changes**: ~1 hour
- **Testing**: ~1 hour
- **Total**: ~4-5 hours

---

**Next Steps**:
1. Assign admin user's function and teams via UI
2. Implement authentication in upload endpoint
3. Implement organizational path construction
4. Update document service
5. Test complete flow

**Priority**: Medium-High (requested by user, but not blocking)

---

**Last Updated**: 2025-11-28
**Status**: Analysis Complete - Implementation Needed
**Blocked By**: Nothing - ready to implement
