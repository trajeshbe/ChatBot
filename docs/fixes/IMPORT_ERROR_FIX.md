# Import Error Fix - Department and Team Models

**Date**: 2025-12-16
**Error**: `cannot import name 'Department' from 'app.models.database_enhanced'`
**Status**: ✅ FIXED

---

## Problem

When uploading a dataset with project selection, the backend threw an ImportError:

```
Upload failed: Dataset upload failed: cannot import name 'Department' from 'app.models.database_enhanced'
```

### Root Cause

The code tried to import ORM models that don't exist:
```python
from app.models.database_enhanced import Project, Department, Team  # ❌ Department and Team don't exist
```

**Available Models** in `database_enhanced.py`:
- `Project` ✅
- `User` ✅
- `APICredential`, `AuditLog`, `ChatSession`, etc. ✅
- `Department` ❌ (not defined)
- `Team` ❌ (not defined)

**Database Reality**:
- `departments` table exists in PostgreSQL ✅
- `teams` table exists in PostgreSQL ✅
- BUT no SQLAlchemy ORM models defined for them

---

## Solution

Changed from ORM joins to direct SQL queries for department and team names.

### Before (Broken)

```python
from app.models.database_enhanced import Project, Department, Team
from sqlalchemy import select

query = select(Project, Department, Team).join(
    Department, Project.department_id == Department.id, isouter=True
).join(
    Team, Project.team_id == Team.id, isouter=True
).where(Project.id == uuid.UUID(project_id))

result = await db.execute(query)
row = result.first()

if row:
    project, department, team = row
    project_name = project.name
    department_name = department.name if department else "Global"
    team_name = team.name if team else "General"
```

### After (Fixed)

```python
from app.models.database_enhanced import Project
from sqlalchemy import select, text

# Fetch project
query = select(Project).where(Project.id == uuid.UUID(project_id))
result = await db.execute(query)
project = result.scalar_one_or_none()

if project:
    project_name = project.name
    project_uuid = project.id

    # Fetch department name if department_id exists
    if project.department_id:
        dept_query = text("SELECT name FROM departments WHERE id = :dept_id")
        dept_result = await db.execute(dept_query, {"dept_id": str(project.department_id)})
        dept_row = dept_result.first()
        if dept_row:
            department_name = dept_row[0]

    # Fetch team name if team_id exists
    if project.team_id:
        team_query = text("SELECT name FROM teams WHERE id = :team_id")
        team_result = await db.execute(team_query, {"team_id": str(project.team_id)})
        team_row = team_result.first()
        if team_row:
            team_name = team_row[0]

    logger.info(f"Using project: {project_name} in {department_name}/{team_name}")
```

---

## Key Changes

1. **Removed ORM imports**: Only import `Project` (which exists)
2. **Added `text()` import**: For raw SQL queries
3. **Query project first**: Get project using ORM
4. **Query dept/team separately**: Use raw SQL with parameter binding
5. **Safe fallbacks**: If department_id or team_id is NULL, keeps default "Global/General"

---

## Why This Approach?

### Option 1: Create ORM Models (Not chosen)
**Pros**:
- Type-safe
- Follows ORM pattern

**Cons**:
- Need to define models in database_enhanced.py
- Need to update imports throughout codebase
- More complex for simple lookup

### Option 2: Raw SQL Queries (Chosen) ✅
**Pros**:
- Works immediately
- No model definition needed
- Simple and direct
- Parameter binding prevents SQL injection

**Cons**:
- Not type-safe
- Less elegant than ORM

---

## File Modified

**`/backend/app/api/routes/finetuning_routes.py`**
- Lines 122-156: Updated project/department/team fetch logic

---

## Testing

### Test 1: Upload Without Project
```bash
# Navigate to Admin → Fine-tuning → Datasets
# Leave Project dropdown empty
# Upload a file
```

**Expected Result**: ✅
- Falls back to `documents/Global/General/Default/finetuning/...`
- No errors

### Test 2: Upload With Project (Construction Intelligence)
```bash
# Navigate to Admin → Fine-tuning → Datasets
# Select "Construction Intelligence" from Project dropdown
# Upload a file
```

**Expected Result**: ✅
- Queries project, department, and team names
- Builds path: `documents/Technology/Frontend-Development/Construction-Intelligence/finetuning/...`
- Logs: "Using project: Construction Intelligence in Technology/Frontend-Development"

### Verification
```sql
-- Check uploaded dataset
SELECT name, minio_path, project_id
FROM finetuning_datasets
ORDER BY uploaded_at DESC
LIMIT 1;

-- Verify project details
SELECT p.name, d.name as dept, t.name as team
FROM projects p
LEFT JOIN departments d ON p.department_id = d.id
LEFT JOIN teams t ON p.team_id = t.id
WHERE p.id = '<project_id>';
```

---

## Backend Status

```bash
docker-compose ps backend

NAME          STATUS
rag-backend   Up 29 seconds (healthy) ✅
```

---

## Related Documentation

- **FINETUNING_PROJECT_SELECTOR_COMPLETE.md** - Main implementation guide
- **DATASET_DROPDOWN_FIX.md** - Earlier dropdown fix

---

## Prevention

### Future ORM Model Additions

If Department and Team ORM models are needed later, define them in `database_enhanced.py`:

```python
class Department(Base):
    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    # ... other fields

class Team(Base):
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    # ... other fields
```

Then the original ORM join approach would work.

---

**Status**: ✅ FIXED
**Backend**: Restarted and healthy
**Ready for Testing**: YES

**Try uploading a dataset now**: http://localhost:3001/admin → Fine-tuning → Datasets
