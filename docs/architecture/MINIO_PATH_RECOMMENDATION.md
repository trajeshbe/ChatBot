# MinIO Path Structure - Comprehensive Analysis & Recommendation

**Date**: 2025-11-29
**Context**: Fixing MinIO path generation bug where all files go to "Global" folder

---

## 🔍 Current Situation

### What We Have Now
All uploaded documents are stored at:
```
Unassigned/General/anonymous/Global/filename
```

**Regardless of**:
- Which project they belong to (Construction, Marketing, etc.)
- Which user uploaded them
- Which department/team they belong to

**Example from our tests**:
```
documents/Unassigned/General/anonymous/Global/construction_doc.txt  ❌
documents/Unassigned/General/anonymous/Global/global_doc.txt        ❌
documents/Unassigned/General/anonymous/Global/marketing_doc.txt     ❌
```

---

## 📚 Existing Code Analysis

### Option 1: From `minio_path_builder.py` (Lines 96-151)
```python
def build_document_path(
    role: str,              # admin, user, viewer
    department: str,        # Technology, Data Operations
    team: str,             # Tech Team 1, Data Team 5
    username: str,         # john.doe
    project_name: str,     # ChatBot RAG, ML Pipeline
    filename: str,         # requirements.pdf
    folder: str = "documents"  # documents, extractions, exports, temp
) -> str:
    """
    Returns: admin/technology/tech-team-1/john.doe/chatbot-rag/documents/requirements.pdf
    """
```

**Path Structure**: `{role}/{department}/{team}/{username}/{project}/{folder}/{filename}`

**Example**:
```
admin/technology/tech-team-1/john.doe/construction-intelligence/documents/blueprint.pdf
user/marketing/campaign-team/jane.smith/marketing/documents/budget.pdf
```

### Option 2: From `construct_minio_path()` (document_service.py)
```python
def construct_minio_path(
    department: Optional[str],
    team: Optional[str],
    username: str,
    project: str,
    filename: str
) -> str:
    """
    Returns: Technology/DevOps-Team/admin/Default/document.pdf
    """
```

**Path Structure**: `{department}/{team}/{username}/{project}/{filename}`

**Example**:
```
Technology/Tech-Team-1/admin/Construction-Intelligence/blueprint.pdf
Marketing/Campaign-Team/jane.smith/Marketing/budget.pdf
```

---

## 🎯 User Requirements

Based on your message:
1. **Default to Global if no project chosen** ✅
2. **Use actual project when selected** ✅
3. **Path format**: Department → Team → Project → User (or something that makes sense)
4. **Track who did what** (auditing, ownership)

---

## 💡 RECOMMENDED APPROACH

### Recommended Path Structure

```
{department}/{team}/{project}/{username}/{folder}/{filename}
```

### Why This Order?

**Hierarchy Rationale**:
1. **Department** (Broadest) - Technology, Marketing, Data Ops
2. **Team** (Within Department) - Tech Team 1, Campaign Team
3. **Project** (Shared workspace) - Construction Intelligence, Marketing Campaign
4. **Username** (Individual) - admin, john.doe, jane.smith
5. **Folder** (File type) - documents, extractions, exports
6. **Filename** (Actual file) - blueprint.pdf

### Benefits of This Structure

#### 1. **Project-Centric Organization** ✅
- Files grouped by project first (after dept/team)
- Makes sense: Projects are the primary work unit
- Multiple users can work on same project

#### 2. **Easy Collaboration** ✅
```
Technology/Tech-Team-1/Construction-Intelligence/
    ├── admin/documents/blueprint-v1.pdf
    ├── john.doe/documents/blueprint-v2.pdf
    └── jane.smith/documents/calculations.xlsx
```
- All project files in one place
- Clear ownership (who uploaded what)

#### 3. **Scalable Access Control** ✅
- Grant access at any level:
  - Department level: All Technology files
  - Team level: All Tech Team 1 files
  - Project level: All Construction Intelligence files
  - User level: Only admin's files

#### 4. **Efficient Queries** ✅
- "Show all Construction Intelligence files" → One folder scan
- "Show all admin's Construction files" → One user subfolder
- "Show all Tech Team 1 projects" → One team folder

#### 5. **Clear Auditing** ✅
- Who: Username folder shows who uploaded
- What: Filename shows what was uploaded
- When: File metadata (timestamp)
- Where: Project folder shows context

---

## 📋 Implementation Plan

### Path Examples

#### Scenario 1: Admin uploads to Construction Intelligence project
```
Input:
- Department: Technology
- Team: Tech Team 1
- Project: Construction Intelligence (selected)
- User: admin
- File: blueprint.pdf

Output:
Technology/Tech-Team-1/Construction-Intelligence/admin/documents/blueprint.pdf
```

#### Scenario 2: Admin uploads without selecting project (defaults to Global)
```
Input:
- Department: Technology
- Team: Tech Team 1
- Project: Global (default)
- User: admin
- File: notes.txt

Output:
Technology/Tech-Team-1/Global/admin/documents/notes.txt
```

#### Scenario 3: Marketing user uploads to Marketing project
```
Input:
- Department: Marketing
- Team: Campaign Team
- Project: Marketing
- User: jane.smith
- File: budget.xlsx

Output:
Marketing/Campaign-Team/Marketing/jane.smith/documents/budget.xlsx
```

#### Scenario 4: Anonymous user (no authentication)
```
Input:
- Department: None → "Unassigned"
- Team: None → "General"
- Project: Global
- User: anonymous
- File: public.pdf

Output:
Unassigned/General/Global/anonymous/documents/public.pdf
```

### Fallback Rules

```python
def build_minio_path(
    department: Optional[str],
    team: Optional[str],
    project_name: Optional[str],  # NEW: Can be None
    username: str,
    filename: str,
    folder: str = "documents"
) -> str:
    # Apply fallbacks
    safe_dept = sanitize(department) if department else "Unassigned"
    safe_team = sanitize(team) if team else "General"
    safe_project = sanitize(project_name) if project_name else "Global"  # ← DEFAULT TO GLOBAL
    safe_username = sanitize(username) if username else "anonymous"
    safe_folder = folder if folder in VALID_FOLDERS else "documents"

    # Construct path
    return f"{safe_dept}/{safe_team}/{safe_project}/{safe_username}/{safe_folder}/{filename}"
```

---

## 🔧 Code Changes Needed

### 1. Update Upload Endpoint (`app/main.py` lines 365-418)

**Current Issue** (Line 370):
```python
project_name = "Global"  # ← Always defaults to Global
```

**Fix**:
```python
# Fetch user's organizational details
department_name = None
team_name = None
project_name = "Global"  # Default

# If user is authenticated
if current_user:
    # ... fetch department, team ...

    # Check if user's default project exists
    if current_user.default_project_id:
        project_id = current_user.default_project_id
        # Fetch project name
        from app.models.database_enhanced import Project
        project_query = select(Project).where(Project.id == project_id)
        project_result = await db.execute(project_query)
        project = project_result.scalar_one_or_none()
        if project:
            project_name = project.name

# NEW: If project_id was provided via form parameter, USE IT (override default)
if project_id:  # From Form(None) parameter
    from app.models.database_enhanced import Project
    try:
        project_uuid = uuid.UUID(project_id)
        project_query = select(Project).where(Project.id == project_uuid)
        project_result = await db.execute(project_query)
        project = project_result.scalar_one_or_none()
        if project:
            project_name = project.name
            logger.info(f"📂 Project (from form): {project_name}")
    except (ValueError, Exception) as e:
        logger.warning(f"Invalid project_id from form: {project_id}, using default: {e}")
        # Keep default project_name

# Construct MinIO path with correct project
minio_path = construct_minio_path(
    department=department_name,
    team=team_name,
    project=project_name,  # ← Now uses correct project!
    username=username,
    filename=file.filename
)
```

### 2. Update `construct_minio_path()` Function

**Recommended Implementation**:
```python
def construct_minio_path(
    department: Optional[str],
    team: Optional[str],
    project: str,  # Always provided (defaults to "Global")
    username: str,
    filename: str,
    folder: str = "documents"
) -> str:
    """
    Construct hierarchical MinIO path for file organization

    Format: {department}/{team}/{project}/{username}/{folder}/{filename}
    Example: Technology/Tech-Team-1/Construction-Intelligence/admin/documents/blueprint.pdf

    Args:
        department: Department name (or None → "Unassigned")
        team: Team name (or None → "General")
        project: Project name (defaults to "Global" if not provided)
        username: Username (or "anonymous")
        filename: Original filename
        folder: Folder type (documents, extractions, exports, temp)

    Returns:
        Full MinIO path
    """
    # Valid folder types
    VALID_FOLDERS = ['documents', 'extractions', 'exports', 'temp']

    # Sanitize all components
    safe_dept = sanitize_path_component(department) if department else "Unassigned"
    safe_team = sanitize_path_component(team) if team else "General"
    safe_project = sanitize_path_component(project) if project else "Global"
    safe_username = sanitize_path_component(username) if username else "anonymous"
    safe_folder = folder if folder in VALID_FOLDERS else "documents"

    # DON'T sanitize filename - preserve original name
    # MinIO/S3 handles special chars in filenames

    # Construct path: dept/team/project/user/folder/file
    path = f"{safe_dept}/{safe_team}/{safe_project}/{safe_username}/{safe_folder}/{filename}"

    logger.debug(f"Built MinIO path: {path}")
    return path
```

---

## 📊 Comparison Table

| Aspect | Option 1 (Role-First) | Option 2 (Dept-First) | **RECOMMENDED (Project-First)** |
|--------|----------------------|----------------------|--------------------------------|
| **Path** | `role/dept/team/user/project/folder/file` | `dept/team/user/project/file` | `dept/team/project/user/folder/file` |
| **Example** | `admin/tech/team1/john/proj-a/docs/file.pdf` | `Tech/Team1/john/Proj-A/file.pdf` | `Tech/Team1/Proj-A/john/docs/file.pdf` |
| **Collaboration** | ❌ Hard (users separated) | ⚠️ Medium | ✅ Easy (project-centric) |
| **Project View** | ❌ Scattered across users | ⚠️ Scattered across users | ✅ Single folder per project |
| **Access Control** | ✅ Role-based (complex) | ✅ Team-based | ✅ Team + Project-based |
| **Scalability** | ⚠️ Role changes = move files | ✅ Good | ✅ Excellent |
| **Auditing** | ✅ Good | ✅ Good | ✅ Excellent |
| **Folder Type** | ✅ Separate (docs/extractions) | ❌ Not supported | ✅ Separate (docs/extractions) |

---

## 🎯 Expected Results After Fix

### Database (Already Correct)
```sql
SELECT filename, project_id::text, p.name as project_name
FROM documents d
JOIN projects p ON d.project_id = p.id
ORDER BY filename;

filename              | project_id                           | project_name
----------------------|--------------------------------------|---------------------------
construction_doc.txt  | 9c881e30-9265-446e-8b8a-6e4ef0617422 | Construction Intelligence ✅
global_doc.txt        | 99a868cc-4292-42c7-9197-81319a793377 | Global                    ✅
marketing_doc.txt     | a1b2c3d4-e5f6-4a5b-9c8d-7e6f5a4b3c2d | Marketing                 ✅
```

### MinIO Paths (After Fix)
```
Unassigned/General/Construction-Intelligence/anonymous/documents/construction_doc.txt ✅
Unassigned/General/Global/anonymous/documents/global_doc.txt                           ✅
Unassigned/General/Marketing/anonymous/documents/marketing_doc.txt                     ✅
```

### With Authenticated User (Future)
```
Technology/Tech-Team-1/Construction-Intelligence/admin/documents/blueprint.pdf
Technology/Tech-Team-1/Global/admin/documents/notes.txt
Marketing/Campaign-Team/Marketing/jane.smith/documents/budget.xlsx
```

---

## 🚀 Implementation Steps

1. **Update `construct_minio_path()` function** (document_service.py)
   - Change signature to include `folder` parameter
   - Reorder path components: `dept/team/project/user/folder/file`

2. **Fix upload endpoint** (main.py lines 365-418)
   - Add logic to fetch project name when `project_id` is provided via form
   - Ensure `project_name` defaults to "Global" if not provided
   - Pass `project_name` to `construct_minio_path()`

3. **Test with existing data**
   - Re-upload test documents
   - Verify MinIO paths are correct
   - Verify database project_id still correct

4. **Update documentation**
   - Document the new path structure
   - Add examples for common scenarios

---

## ✅ Acceptance Criteria

1. **Default Project Behavior**:
   - No project selected → Files go to "Global" folder ✅
   - Project selected → Files go to project folder ✅

2. **Path Structure**:
   - Format: `{dept}/{team}/{project}/{user}/{folder}/{filename}` ✅
   - Fallbacks work: Unassigned/General/Global/anonymous ✅

3. **Organizational Clarity**:
   - Easy to find project files ✅
   - Clear ownership (who uploaded) ✅
   - Supports collaboration ✅

4. **Database Consistency**:
   - `documents.project_id` matches path project name ✅
   - `documents.minio_path` stored correctly ✅

---

## 📝 Summary

**Current Problem**: All files stored in `Unassigned/General/anonymous/Global/` regardless of project

**Root Cause**: Upload endpoint always defaults `project_name = "Global"` and never fetches actual project name from `project_id` form parameter

**Recommended Solution**:
- Path structure: `{department}/{team}/{project}/{username}/{folder}/{filename}`
- Fetch project name from database when `project_id` provided
- Default to "Global" when no project selected
- Benefits: Project-centric, supports collaboration, clear auditing

**Implementation**: ~1 hour (update 2 functions + test)

**Priority**: Medium (RAG works via database, but MinIO organization is important for long-term)

---

Would you like me to implement this fix now?
