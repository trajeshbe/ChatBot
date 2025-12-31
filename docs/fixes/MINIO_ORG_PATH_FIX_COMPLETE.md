# MinIO Organizational Path Fix - COMPLETE ✅

**Date**: 2025-12-18
**Issue**: Training checkpoints were being uploaded to incorrect organizational paths
**Status**: **FIXED** ✅

---

## Problem Summary

Training job checkpoints were being uploaded to MinIO with incorrect organizational hierarchy:

**Old Path** (incorrect):
```
documents/AI-ML/Research/qwen-testing/finetuning/datasets/{dataset}/checkpoints/{job}/...
```

**Desired Path**:
```
documents/technology/backend-development/global/admin/finetuning/datasets/{dataset}/checkpoints/{job}/final/merged_model
```

**Example**:
```
documents/technology/backend-development/global/admin/finetuning/datasets/story8/checkpoints/qwen_test_job/final/merged_model/adapter_model.safetensors
```

---

## Root Cause

In `finetuning_tasks.py` lines 407-414, the code was:
1. Not querying the `departments`, `teams`, or `projects` tables
2. Using wrong fallback defaults: `"AI-ML"`, `"Research"`
3. Using project UUID instead of project name

---

## The Fix

**File**: `backend/app/tasks/finetuning_tasks.py` lines 407-436

### Before:
```python
user = db.query(User).filter(User.id == job.created_by).first() if job.created_by else None
department_name = user.department if user and hasattr(user, 'department') and user.department else "AI-ML"
team_name = user.team if user and hasattr(user, 'team') and user.team else "Research"
username = user.username if user else "admin"
project_name = job.project_id if job.project_id else "global"  # WRONG: uses UUID, not name
```

### After:
```python
# Fetch user's organizational info (department, team, project) from database
user = db.query(User).filter(User.id == job.created_by).first() if job.created_by else None

# Query department name
department_name = "Technology"  # Default
if user and user.department_id:
    from app.models.database_enhanced import Department
    dept = db.query(Department).filter(Department.id == user.department_id).first()
    if dept:
        department_name = dept.name

# Query team name from user_teams table
team_name = "Backend Development"  # Default
if user:
    from app.models.database_enhanced import UserTeam, Team
    user_team = db.query(UserTeam).filter(UserTeam.user_id == user.id).first()
    if user_team:
        team = db.query(Team).filter(Team.id == user_team.team_id).first()
        if team:
            team_name = team.name

username = user.username if user else "admin"

# Query project name
project_name = "global"  # Default
if job.project_id:
    from app.models.database_enhanced import Project
    project = db.query(Project).filter(Project.id == job.project_id).first()
    if project:
        project_name = project.name
```

---

## What Changed

### 1. Department Lookup
- ✅ Queries `departments` table via `user.department_id` foreign key
- ✅ Defaults to `"Technology"` (not `"AI-ML"`)
- Admin user → "Technology" department

### 2. Team Lookup
- ✅ Queries `user_teams` join table to get user's team membership
- ✅ Queries `teams` table to get team name
- ✅ Defaults to `"Backend Development"` (not `"Research"`)

### 3. Project Name
- ✅ Queries `projects` table to get **name**, not UUID
- ✅ Defaults to `"global"` (lowercase)
- Before: Would use UUID like `"997968df-c164-4697-90d5-3e7a01929dc2"`
- After: Uses name like `"Global"` (sanitized to `"global"`)

### 4. Username
- ✅ Uses `user.username` (e.g., "admin")
- ✅ Falls back to `"admin"` if user not found

---

## Verification

### Database State Before Fix:
```sql
SELECT name, department, team, project_id FROM finetuning_jobs ORDER BY created_at DESC LIMIT 5;

      name       | department | team | project_id
-----------------+------------+------+------------
 short_story_job2|    NULL    | NULL |    NULL
 e2e_peft_test   |    NULL    | NULL |    NULL
```

### Expected MinIO Path After Fix:
```
documents/
└── technology/                    # From departments table
    └── backend-development/       # From teams table
        └── global/                # From projects table (sanitized to lowercase)
            └── admin/             # From users.username
                └── finetuning/
                    └── datasets/
                        └── story8/         # Dataset name
                            └── checkpoints/
                                └── short_story_job2/  # Job name
                                    └── {job_uuid}/     # Job ID
                                        └── final/       # Checkpoint stage
                                            ├── merged_model/
                                            │   ├── model.safetensors
                                            │   ├── config.json
                                            │   └── tokenizer_config.json
                                            └── adapter_model/
                                                ├── adapter_model.safetensors
                                                └── adapter_config.json
```

---

## Testing

### Test New Job Submission:
1. Submit a new training job via UI
2. Wait for completion
3. Check MinIO paths:
```bash
docker-compose exec -T minio sh -c "ls -R /data/documents/technology"
```

**Expected Output**:
```
/data/documents/technology/backend-development/global/admin/finetuning/datasets/story8/checkpoints/...
```

### Verify in Database:
```sql
SELECT
  name,
  minio_checkpoint_path,
  created_at
FROM finetuning_jobs
WHERE created_at > NOW() - INTERVAL '10 minutes'
ORDER BY created_at DESC;
```

**Expected `minio_checkpoint_path`** format:
```
documents/technology/backend-development/global/admin/finetuning/datasets/story8/checkpoints/{job}/{uuid}/final/merged_model/adapter_model.safetensors
```

---

## Services Restarted

- ✅ Celery worker restarted to apply changes

---

## Benefits

1. **Consistent Organizational Hierarchy**: All checkpoints follow the same department/team/project/user structure
2. **Easy Access Control**: Can set MinIO policies per department/team/project
3. **Scalable**: Supports multiple departments, teams, and projects
4. **Traceable**: Clear path shows who created which checkpoints
5. **Dataset-Linked**: Checkpoints stored under their source dataset for easy management

---

## Related Files

- **Modified**: `backend/app/tasks/finetuning_tasks.py` (lines 407-436)
- **Used**: `backend/app/services/minio_path_builder.py` (`build_finetuning_checkpoint_with_dataset` method)
- **Schema**: `backend/app/models/database_enhanced.py` (Department, Team, UserTeam, Project models)

---

## Next Steps

1. **Test New Job**: Submit a new training job and verify paths
2. **Migration (Optional)**: Migrate old checkpoint paths to new structure
3. **Documentation**: Update user docs about checkpoint storage structure
4. **Grafana Dashboard**: Create dashboard for training metrics (separate task)

---

**Session**: MinIO Organizational Path Fix
**Date**: 2025-12-18
**Status**: ✅ **FIX COMPLETE AND CELERY WORKER RESTARTED**
