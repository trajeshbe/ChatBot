# MinIO Path Inconsistency Analysis

**Date**: 2025-12-19
**Issue**: Datasets and artifacts stored in different team folders

## The Problem

### Current State
```
documents/technology/
├── backend-development/     ← NEW datasets (✅ CORRECT)
│   └── global/admin/finetuning/datasets/story8/
│
└── system-administrator/    ← OLD checkpoints (❌ WRONG - not a real team)
    └── global/admin/finetuning/datasets/story8/checkpoints/
```

### Why This Happened

**Timeline**:
1. **Before Fix** (Dec 17-18): Code used `user.function` field
   - Admin user has `function = "System Administrator"` (job role, NOT a team)
   - Path builder sanitized this to `system-administrator`
   - Result: `documents/technology/system-administrator/...`

2. **After Fix** (Dec 19): Code now uses proper team lookup
   - Job creation queries `teams` table
   - Admin user's actual team: `Backend Development`
   - Result: `documents/technology/backend-development/...`

### Database Evidence

```sql
-- Admin user's fields
username: admin
department_id: Technology
function: "System Administrator"  ← JOB TITLE (not team!)

-- Actual team structure
teams table:
- Backend Development  ← Real team under Technology dept
- Frontend Development
- DevOps
(NO "System Administrator" team exists!)

-- New jobs (after fix)
SELECT name, department, team FROM finetuning_jobs WHERE name = 'short_story_11';
name           | department | team
short_story_11 | Technology | Backend Development  ✅ CORRECT

-- Old jobs (before fix)
Stored in: system-administrator/ folder  ❌ WRONG
```

### Impact

**Files in `system-administrator/`** (OLD):
```
datasets/story8/checkpoints/short_story_8/.../adapter_model/
datasets/story8/checkpoints/short_story_8/.../config/
```

**Files in `backend-development/`** (NEW):
```
datasets/story3/...
datasets/story4/...
datasets/story5/...
datasets/story6/...
datasets/story8/3b5aebf0-8dcf-423c-aad4-65a8f3dba3b6/  ← New dataset upload
```

**Result**: Same dataset (`story8`) has files in BOTH locations!

## Root Cause

### Before Fix (Bug)

**File**: `backend/app/api/routes/finetuning_routes.py` (old code)

```python
# WRONG: Used user.function instead of querying teams table
team_name = user.function  # "System Administrator"
team_name = team_name.replace(" ", "-").lower()  # "system-administrator"
```

### After Fix (Correct)

**File**: `backend/app/api/routes/finetuning_routes.py` (current code)

```python
# CORRECT: Query actual team from teams table
team = await db.execute(
    select(Team).where(Team.name == "Backend Development")
)
team_name = team.name  # "Backend Development"
```

## Solution Options

### Option 1: Move Old Files (Recommended)

Move old checkpoints from `system-administrator/` to `backend-development/`:

```bash
# Inside MinIO container
mc cp --recursive \
  myminio/documents/technology/system-administrator/global/admin/finetuning/ \
  myminio/documents/technology/backend-development/global/admin/finetuning/

# Then delete old location
mc rm --recursive \
  myminio/documents/technology/system-administrator/
```

**Pros**:
- Clean, consistent structure
- Follows organizational hierarchy
- All data in correct location

**Cons**:
- Requires data migration
- Could break references to old paths

### Option 2: Create Symlink/Alias (Not supported in MinIO)

MinIO doesn't support symlinks.

### Option 3: Update Path Builder to Check Both (Backward Compatibility)

Add fallback logic to check old location if new location doesn't exist:

```python
# In path builder or retrieval logic
def get_checkpoint_path(job_id, team):
    # Try new path first
    new_path = f"documents/technology/{team}/global/admin/finetuning/..."
    if minio_object_exists(new_path):
        return new_path

    # Fallback to old path for backward compatibility
    old_path = f"documents/technology/system-administrator/global/admin/finetuning/..."
    if minio_object_exists(old_path):
        logger.warning(f"Using legacy path for {job_id}: {old_path}")
        return old_path

    raise FileNotFoundError(f"Checkpoint not found in new or legacy paths")
```

**Pros**:
- No data migration needed
- Backward compatible
- Gradual deprecation possible

**Cons**:
- More complex code
- Technical debt
- Two possible locations to check

### Option 4: Leave As-Is and Document (Not Recommended)

Accept that old data is in `system-administrator/` and new data is in `backend-development/`.

**Pros**:
- No work required

**Cons**:
- Confusing for users
- Inconsistent path structure
- Violates organizational hierarchy

## Recommended Action

**Option 3: Backward Compatibility** + **Gradual Migration**

1. **Immediate**: Add fallback logic to check both paths
2. **Background**: Migrate old files to new structure
3. **Cleanup**: Remove old paths after migration completes
4. **Document**: Log warnings when old paths are used

## Implementation Plan

### Phase 1: Add Fallback Logic (Immediate)

**File**: `backend/app/services/finetuning/finetuning_service.py`

Add helper method:

```python
async def _get_checkpoint_path_with_fallback(
    self,
    job: FineTuningJob,
    checkpoint_type: str = "final"
) -> str:
    """
    Get checkpoint path with backward compatibility.
    Checks new team-based path first, falls back to legacy path.
    """
    # Build new path using job's team field
    new_path = self.path_builder.build_finetuning_checkpoint_path(
        username=job.created_by_username,
        department_name=job.department,
        team_name=job.team,  # "Backend Development"
        project_id=str(job.project_id),
        dataset_name=job.dataset_name,
        job_name=job.name,
        job_id=str(job.id),
        checkpoint_stage=checkpoint_type,
        model_type="merged_model"
    )

    if await self._check_minio_path_exists(new_path):
        return new_path

    # Fallback to legacy "system-administrator" path
    legacy_path = new_path.replace("/backend-development/", "/system-administrator/")

    if await self._check_minio_path_exists(legacy_path):
        logger.warning(
            f"Using legacy path for job {job.name} ({job.id}): {legacy_path}. "
            f"Consider migrating to new path: {new_path}"
        )
        return legacy_path

    raise FileNotFoundError(
        f"Checkpoint not found in new path ({new_path}) or legacy path ({legacy_path})"
    )
```

### Phase 2: Migration Script (Background)

Create admin script to migrate old files:

```python
# backend/scripts/migrate_minio_paths.py
import asyncio
from minio import Minio

async def migrate_old_paths():
    """Migrate files from system-administrator/ to backend-development/"""

    old_prefix = "documents/technology/system-administrator/global/admin/finetuning/"
    new_prefix = "documents/technology/backend-development/global/admin/finetuning/"

    # List all objects in old path
    objects = minio_client.list_objects("documents", prefix=old_prefix, recursive=True)

    for obj in objects:
        old_path = obj.object_name
        new_path = old_path.replace(old_prefix, new_prefix)

        # Copy to new location
        minio_client.copy_object(
            "documents", new_path,
            f"documents/{old_path}"
        )

        print(f"Migrated: {old_path} -> {new_path}")

    print("Migration complete. Review and then delete old paths manually.")
```

### Phase 3: Cleanup (After Migration)

```bash
# Verify all files migrated
mc ls --recursive myminio/documents/technology/backend-development/global/admin/finetuning/

# Delete old location
mc rm --recursive myminio/documents/technology/system-administrator/
```

## Verification

After implementing Option 3:

```python
# Test with old job
old_job = get_job_by_name("short_story_8")  # Created before fix
path = await _get_checkpoint_path_with_fallback(old_job)
# Should return: documents/technology/system-administrator/... (with warning)

# Test with new job
new_job = get_job_by_name("short_story_11")  # Created after fix
path = await _get_checkpoint_path_with_fallback(new_job)
# Should return: documents/technology/backend-development/...
```

## Summary

**Current State**: Inconsistent paths (old = `system-administrator/`, new = `backend-development/`)

**Root Cause**: Code previously used `user.function` instead of querying `teams` table

**Fix Applied**: Now correctly uses team name from database

**Remaining Issue**: Old files still in wrong location

**Recommendation**: Implement backward-compatible fallback + gradual migration

---

**Status**: Analysis complete, awaiting decision on migration approach
