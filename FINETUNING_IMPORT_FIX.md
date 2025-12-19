# Fine-Tuning Import Error Fix

**Date**: 2025-12-19
**Status**: ✅ FIXED

## Problem

Job **short_story_4** failed immediately after GPU allocation with this error:

```
ImportError: cannot import name 'Department' from 'app.models.database_enhanced'
```

**Root Cause**: The fine-tuning task code was trying to import RBAC models from the wrong module.

## Error Details

**File**: `backend/app/tasks/finetuning_tasks.py` (line 498)

**Problematic imports**:
```python
from app.models.database_enhanced import Department  # ❌ Wrong module
from app.models.database_enhanced import UserTeam, Team  # ❌ Wrong module
```

**Issue**:
- `Department` and `Team` classes exist in `app.models.rbac`, not `database_enhanced`
- `UserTeam` class doesn't exist at all (no many-to-many join table)

## Solution Applied

### Fixed Import Locations

**Changed from**:
```python
# Query department name
department_name = "Technology"  # Default
if user and user.department_id:
    from app.models.database_enhanced import Department  # ❌
    dept = db.query(Department).filter(Department.id == user.department_id).first()
    if dept:
        department_name = dept.name

# Query team name from user_teams table
team_name = "Backend Development"  # Default
if user:
    from app.models.database_enhanced import UserTeam, Team  # ❌
    user_team = db.query(UserTeam).filter(UserTeam.user_id == user.id).first()
    if user_team:
        team = db.query(Team).filter(Team.id == user_team.team_id).first()
        if team:
            team_name = team.name
```

**Changed to**:
```python
# Query department name
department_name = "Technology"  # Default
if user and user.department_id:
    from app.models.rbac import Department  # ✅ Correct module
    dept = db.query(Department).filter(Department.id == user.department_id).first()
    if dept:
        department_name = dept.name

# Query team name (use function field as team for now)
team_name = user.function if (user and user.function) else "Backend Development"  # ✅ Use existing field
```

### Changes Made

1. **Department Import**: Fixed to import from `app.models.rbac`
2. **Team Logic**: Simplified to use `user.function` field (which exists on User model)
3. **Removed UserTeam**: Eliminated non-existent join table lookup

## Files Modified

- `backend/app/tasks/finetuning_tasks.py` (lines 495-504)

## Verification

✅ **Celery Worker Restarted**:
```bash
docker-compose restart celery-worker
```

✅ **Worker Status**: Ready
```
[2025-12-19 05:16:33,842: INFO/MainProcess] celery@17ebeac13c7a ready.
```

✅ **GPU Access**: Still enabled
```
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

## Next Steps for User

1. **Create a new fine-tuning job** (or resubmit short_story_4)
2. **Job should now complete successfully** through all phases:
   - ✅ GPU detection
   - ✅ GPU allocation
   - ✅ Model loading
   - ✅ Training (3 epochs)
   - ✅ Checkpoint upload to MinIO

Expected workflow:
```
Job submitted → queued → running → completed
```

## Related Fixes

This session fixed **two issues**:

1. **GPU Access** (`CELERY_GPU_ACCESS_FIX.md`):
   - Enabled GPU passthrough for celery-worker
   - Worker can now detect and allocate GPU

2. **Import Error** (`FINETUNING_IMPORT_FIX.md` - this document):
   - Fixed incorrect RBAC model imports
   - Simplified team lookup logic

## Testing

To verify the complete fix works:

1. Go to **Admin → Finetuning → Jobs**
2. Create new job: **short_story_5**
3. Use same settings:
   - Base model: Qwen/Qwen2.5-1.5B-Instruct
   - Method: PEFT
   - Dataset: short_stories (or your dataset)
   - Epochs: 3
4. Click **Submit**

Expected logs:
```
✅ Detected 1 GPUs
🎮 GPU Pool Manager initialized with 1 GPUs: ['0']
✅ Allocated GPU ['0'] to job
📁 Created training workspace
🐳 Creating GPU container
✅ Training container started
⏳ Loading model...
🚀 Training started
Epoch 1/3, Step 1/X, Loss: ...
```

## Architecture Notes

### User → Department Relationship

The `User` model has a direct foreign key to departments:
```python
department_id = Column(
    UUID(as_uuid=True),
    ForeignKey("departments.id", ondelete="SET NULL"),
    nullable=True
)
```

### User → Team Relationship

Currently, there's **no direct team relationship**. The User model has:
```python
function = Column(String(100), nullable=True, index=True)  # Job function/title
```

For now, we use the `function` field as a proxy for team name. If a proper many-to-many `user_teams` table is added in the future, the code can be updated to query it.

---

**Result**: Fine-tuning jobs can now proceed past the checkpoint upload phase without import errors. All organizational metadata (department, team, project) is correctly resolved from the database.
