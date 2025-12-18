# Global Project Architecture

**Date**: 2025-12-17
**Purpose**: Document how the "Global" project system works

---

## Overview

The system has a **default "Global" project** that is automatically created during database setup and serves as the fallback project for all documents, datasets, and resources that don't belong to a specific user-created project.

---

## How Global Project is Created

### Migration: `013_create_default_global_project.sql`

**Location**: `/backend/migrations/013_create_default_global_project.sql`

**Key Features**:

1. **Idempotent Creation**:
   ```sql
   INSERT INTO projects (id, name, description, owner_id, created_at, updated_at)
   SELECT
       gen_random_uuid(),  -- Random UUID (not hardcoded)
       'Global',
       'Default global project for documents not assigned to specific projects',
       (SELECT id FROM users WHERE role = 'admin' ORDER BY created_at LIMIT 1),
       NOW(),
       NOW()
   WHERE NOT EXISTS (
       SELECT 1 FROM projects WHERE name = 'Global'
   );
   ```

2. **Auto-Membership**: All users are automatically added as members:
   ```sql
   INSERT INTO project_members (id, project_id, user_id, role, joined_at)
   SELECT
       uuid_generate_v4(),
       (SELECT id FROM projects WHERE name = 'Global' LIMIT 1),
       u.id,
       'member',
       NOW()
   FROM users u
   WHERE NOT EXISTS (
       SELECT 1 FROM project_members pm
       WHERE pm.project_id = (SELECT id FROM projects WHERE name = 'Global' LIMIT 1)
       AND pm.user_id = u.id
   );
   ```

3. **Orphan Document Migration**: Any documents with NULL project_id are assigned to Global:
   ```sql
   UPDATE documents
   SET project_id = (SELECT id FROM projects WHERE name = 'Global' LIMIT 1)
   WHERE project_id IS NULL;
   ```

---

## Current Global Project

```bash
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "
SELECT id, name, description, created_at
FROM projects
WHERE name = 'Global';"
```

**Result**:
```
id                                   | name   | description                            | created_at
-------------------------------------+--------+----------------------------------------+----------------------------
997968df-c164-4697-90d5-3e7a01929dc2 | Global | Default project for anonymous's files  | 2025-11-30 14:13:53.331591
```

---

## How Fine-Tuning Upload Uses Global Project

### Code: `/backend/app/api/routes/finetuning_routes.py` (Lines 134-178)

**Default Behavior (No project_id provided)**:
```python
project_name = "Global"  # Default to Global
project_uuid = None

# ... get user's dept/team ...

if project_id:
    # User explicitly provided project_id → use that project
    query = select(Project).where(Project.id == uuid.UUID(project_id))
    result = await db.execute(query)
    project = result.scalar_one_or_none()

    if project:
        project_name = project.name
        project_uuid = project.id
else:
    # No project_id → Default to Global project
    global_query = select(Project).where(Project.name == "Global")
    global_result = await db.execute(global_query)
    global_project = global_result.scalar_one_or_none()

    if global_project:
        project_name = global_project.name  # "Global"
        project_uuid = global_project.id     # UUID from database
```

**MinIO Path Structure**:
```
technology/backend-development/global/admin/finetuning/datasets/...
                               ^^^^^^
                               Uses project name in lowercase
```

---

## Benefits of Global Project

### 1. **Guaranteed Default Project**
- Every upload has a project (never NULL)
- No orphaned datasets or documents
- All users can access Global by default

### 2. **Flexible Project Assignment**
- Users can override by providing `project_id` in upload request
- UI can show project dropdown (Global, Construction Intelligence, Science, etc.)
- Backend automatically uses Global if no selection made

### 3. **Organizational Hierarchy**
```
MinIO Path: {department}/{team}/{project}/{user}/...

Examples:
- Global (default):     technology/backend-development/global/admin/...
- Specific project:     technology/backend-development/construction-intelligence/admin/...
- Science project:      technology/backend-development/science/admin/...
```

### 4. **Automatic Cleanup**
- Migration ensures orphaned documents get assigned to Global
- New users automatically get Global project membership
- System always has a fallback project

---

## Project Selection Flow

```
User uploads dataset via UI
    ↓
Did user select a project?
    ↓
YES → Use selected project_id
    ↓
NO → Query database for Global project
    ↓
Build MinIO path: {dept}/{team}/{project.name.lower()}/{username}/finetuning/datasets/...
    ↓
Store dataset with project_uuid in database
```

---

## Database Queries for Global Project

### Get Global Project ID:
```sql
SELECT id, name FROM projects WHERE name = 'Global';
```

### Check User Membership:
```sql
SELECT pm.role
FROM project_members pm
JOIN projects p ON pm.project_id = p.id
WHERE p.name = 'Global'
AND pm.user_id = '<user-uuid>';
```

### Count Global Project Datasets:
```sql
SELECT COUNT(*)
FROM finetuning_datasets fd
JOIN projects p ON fd.project_id = p.id
WHERE p.name = 'Global';
```

---

## Why Not Hardcode Global Project UUID?

**Current Approach** (Query by name):
```python
global_query = select(Project).where(Project.name == "Global")
global_result = await db.execute(global_query)
global_project = global_result.scalar_one_or_none()
```

**Alternative** (Hardcode UUID):
```python
GLOBAL_PROJECT_ID = uuid.UUID("997968df-c164-4697-90d5-3e7a01929dc2")
```

**Why Query is Better**:
1. ✅ **Migration uses `gen_random_uuid()`** - UUID is different per installation
2. ✅ **Database is source of truth** - If Global project is recreated, code still works
3. ✅ **Portable** - Works across dev/staging/prod without hardcoding IDs
4. ✅ **Idempotent** - Migration can run multiple times safely

**Performance**: Query happens once per upload (negligible overhead)

---

## Testing Global Project Assignment

### Test 1: Upload without project_id
```bash
# Upload dataset without specifying project
curl -X POST http://localhost:8000/api/v1/finetuning/datasets/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@story3.csv" \
  -F "name=story3" \
  -F "format_type=qa" \
  -F "training_objective=qa"
```

**Expected MinIO Path**:
```
technology/backend-development/global/admin/finetuning/datasets/story3/...
```

### Test 2: Upload with explicit Global project_id
```bash
# Upload dataset with Global project UUID
curl -X POST http://localhost:8000/api/v1/finetuning/datasets/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@story4.csv" \
  -F "name=story4" \
  -F "format_type=qa" \
  -F "training_objective=qa" \
  -F "project_id=997968df-c164-4697-90d5-3e7a01929dc2"
```

**Expected**: Same path as Test 1 (both go to Global)

### Test 3: Upload with different project
```bash
# Upload to Construction Intelligence project
curl -X POST http://localhost:8000/api/v1/finetuning/datasets/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@story5.csv" \
  -F "name=story5" \
  -F "format_type=qa" \
  -F "training_objective=qa" \
  -F "project_id=03eae60b-c0d4-4f07-bb40-0d3980a2c540"
```

**Expected MinIO Path**:
```
technology/backend-development/construction-intelligence/admin/finetuning/datasets/story5/...
```

---

## Summary

✅ **Global project is created automatically** via migration
✅ **All users are members** of Global project by default
✅ **Fine-tuning uploads default to Global** when no project_id provided
✅ **MinIO paths include project name** for organizational structure
✅ **System is flexible** - users can override with specific projects

**Result**: Clean, maintainable architecture with guaranteed fallback project! 🎉

---

**End of Documentation**
