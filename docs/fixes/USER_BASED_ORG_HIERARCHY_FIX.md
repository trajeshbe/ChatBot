# User-Based Organizational Hierarchy Fix

**Date**: 2025-12-16 (Updated: 2025-12-17)
**Issue**: Path structure using project's dept/team instead of user's
**Status**: ✅ FIXED

---

## Important Note on Path Structure

**MinIO Bucket**: `documents`

All paths shown in this document are stored in the `documents` MinIO bucket. When you see:
```
documents/Technology/Backend-Development/...
```

This means:
- **Bucket**: `documents`
- **Path inside bucket**: `Technology/Backend-Development/...`

**Update 2025-12-17**: Removed redundant "documents/" prefix from paths since "documents" is the bucket name, not a directory in the path.

---

## Problem Identified

The original implementation used the **project's** department and team for the MinIO path structure:

```
documents/{project.department}/{project.team}/{project.name}/finetuning/...
```

This was **incorrect** because:
1. ❌ Projects can be in different departments than the user
2. ❌ Doesn't align with user's actual organizational membership
3. ❌ Makes RBAC confusing (user in one dept, files in another)
4. ❌ Inconsistent with user's access control context

---

## Correct Approach (User-Based)

The path should be based on the **user's** department, team, and username:

```
documents/{user.department}/{user.team}/{project.name}/{username}/finetuning/...
```

**Why This Makes Sense**:
1. ✅ User belongs to an organizational unit (department → team)
2. ✅ All user's projects live under their organizational context
3. ✅ Username provides clear individual ownership
4. ✅ Aligns with RBAC and access control
5. ✅ Clear ownership and security boundaries

---

## Example: Admin User

### User's Organizational Membership
```
Technology (Department)
  └── Backend Development (Team)
       └── admin (User)
            ├── Construction Intelligence (Project)
            ├── Science (Project)
            └── Global (Project)
```

### Correct MinIO Paths

**All projects under user's organizational context with username**:

**Project 1: Construction Intelligence**
```
documents/Technology/Backend-Development/Construction-Intelligence/admin/finetuning/datasets/...
```

**Project 2: Science**
```
documents/Technology/Backend-Development/Science/admin/finetuning/datasets/...
```

**Project 3: Global**
```
documents/Technology/Backend-Development/Global/admin/finetuning/datasets/...
```

**All under**: `documents/Technology/Backend-Development/{project}/admin/` ✅

---

## What Changed

### Before (Wrong)

```python
# Fetch department/team from PROJECT
if project.department_id:
    dept_query = text("SELECT name FROM departments WHERE id = :dept_id")
    dept_result = await db.execute(dept_query, {"dept_id": str(project.department_id)})
    department_name = dept_row[0]

if project.team_id:
    team_query = text("SELECT name FROM teams WHERE id = :team_id")
    team_result = await db.execute(team_query, {"team_id": str(project.team_id)})
    team_name = team_row[0]
```

**Result**: `documents/{PROJECT.dept}/{PROJECT.team}/{project}/...` ❌

---

### After (Correct)

```python
# Fetch department/team from USER
if user.department_id:
    dept_query = text("SELECT name FROM departments WHERE id = :dept_id")
    dept_result = await db.execute(dept_query, {"dept_id": str(user.department_id)})
    department_name = dept_row[0]

# Get user's team from user_teams junction table
team_query = text("""
    SELECT t.name
    FROM teams t
    JOIN user_teams ut ON t.id = ut.team_id
    WHERE ut.user_id = :user_id
    ORDER BY ut.assigned_at DESC
    LIMIT 1
""")
team_result = await db.execute(team_query, {"user_id": str(user.id)})
team_name = team_row[0]

# Then get project name
if project_id:
    project = await db.execute(select(Project).where(Project.id == project_id))
    project_name = project.name

# Pass username to path builder
username = user.username
```

**Result**: `documents/{USER.dept}/{USER.team}/{project}/{username}/...` ✅

---

## Code Changes

**File**: `/backend/app/api/routes/finetuning_routes.py`
**Lines**: 121-163

### Key Changes:
1. **Get department from user.department_id** (not project.department_id)
2. **Get team from user_teams table** (user can be member of team)
3. **Get project name separately** (only used as folder name, not org hierarchy)
4. **Updated log message**: "Using user org: {dept}/{team} with project: {name}"

---

## Organizational Logic

### User Assignment
```sql
SELECT u.username, d.name as dept, t.name as team
FROM users u
LEFT JOIN departments d ON u.department_id = d.id
LEFT JOIN user_teams ut ON u.id = ut.user_id
LEFT JOIN teams t ON ut.team_id = t.id
WHERE u.username = 'admin';

Result:
username | dept       | team
admin    | Technology | Backend Development
```

### Path Structure
```
documents/
  └── Technology/                    ← User's department
      └── Backend-Development/       ← User's team
          ├── Construction-Intelligence/   ← Project 1
          │   └── finetuning/
          ├── Science/                     ← Project 2
          │   └── finetuning/
          └── Global/                      ← Project 3
              └── finetuning/
```

---

## Security & RBAC Implications

### User-Based Hierarchy (Correct) ✅

**Scenario**: Admin (Technology/Backend Development) uploads dataset to "Science" project

**Path**: `documents/Technology/Backend-Development/Science/finetuning/...`

**Access Control**:
- ✅ Admin has access (it's under their organizational unit)
- ✅ Technology department admins can access
- ✅ Backend Development team members can access
- ✅ Clear ownership boundary

### Project-Based Hierarchy (Wrong) ❌

**Scenario**: Same upload with old logic

**Path**: `documents/Data-Operations/Data-Science-Team/Science/finetuning/...`

**Access Control**:
- ❌ Admin's files scattered across different departments
- ❌ Data Operations team sees admin's files (confusing)
- ❌ Admin can't find their own files easily
- ❌ RBAC becomes complex and inconsistent

---

## Real-World Example

### Jane (Data Scientist)
- **Department**: Data Operations
- **Team**: Data Science Team
- **Projects**: ML Models, Analytics, Research

**Her MinIO Structure**:
```
documents/Data-Operations/Data-Science-Team/
  ├── ML-Models/finetuning/...
  ├── Analytics/finetuning/...
  └── Research/finetuning/...
```

### John (Backend Developer)
- **Department**: Technology
- **Team**: Backend Development
- **Projects**: API, Microservices, Integration

**His MinIO Structure**:
```
documents/Technology/Backend-Development/
  ├── API/finetuning/...
  ├── Microservices/finetuning/...
  └── Integration/finetuning/...
```

**Result**: ✅ Clean separation, easy to manage permissions per department/team

---

## Testing

### Test Upload with "Construction Intelligence" Project

**User**: admin (Technology/Backend Development)
**Project**: Construction Intelligence
**Dataset**: test-dataset.csv

**Expected Path**:
```
documents/Technology/Backend-Development/Construction-Intelligence/admin/finetuning/datasets/test-dataset/{uuid}/file.csv
```

**Verify**:
```sql
SELECT name, minio_path
FROM finetuning_datasets
ORDER BY uploaded_at DESC
LIMIT 1;
```

**Expected in logs**:
```
INFO: Using user org: Technology/Backend-Development with project: Construction-Intelligence
```

---

## Fallback Logic

### User Not Assigned to Department/Team

**Scenario**: User has no department_id or team membership

**Fallback Values**:
```python
department_name = "Global"   # Default
team_name = "General"        # Default
project_name = "Default"     # If no project selected
```

**Path**: `documents/Global/General/Default/finetuning/...`

---

## Migration Considerations

### For Existing Datasets

If you have datasets uploaded with the old (project-based) logic, you may want to migrate them:

```python
# Migration script (pseudo-code)
for dataset in old_datasets:
    old_path = dataset.minio_path  # documents/{project.dept}/{project.team}/...

    # Get user who uploaded
    user = dataset.uploaded_by

    # Build new path with user's org
    new_path = f"documents/{user.dept}/{user.team}/{project}/..."

    # Move in MinIO
    minio_client.copy_object(bucket, new_path, bucket, old_path)
    minio_client.remove_object(bucket, old_path)

    # Update database
    dataset.minio_path = new_path
```

---

## Summary

### What Was Wrong
- ❌ Paths used project's department/team
- ❌ User's files scattered across different organizational units
- ❌ Confusing for RBAC and access control

### What's Fixed
- ✅ Paths use user's department/team/username
- ✅ All user's projects under their organizational unit
- ✅ Username provides individual user ownership
- ✅ Clear ownership and security boundaries
- ✅ Consistent with user's access context

### Files Modified
- `/backend/app/api/routes/finetuning_routes.py` (lines 121-175)
- `/backend/app/services/minio_path_builder.py` (lines 287-336)

### Backend Status
- ✅ Restarted and healthy
- ✅ Ready for testing

---

## Try It Now!

1. Upload a dataset to **Construction Intelligence** project
2. Check the MinIO path in database
3. Verify it's under: `documents/Technology/Backend-Development/Construction-Intelligence/admin/...`

**All your projects will now be organized under your organizational unit with your username!** 🎯

---

**Status**: ✅ FIXED AND DEPLOYED
**Date**: 2025-12-16
**Backend**: Healthy and ready
