# Path Structure Inconsistency Analysis

**Date**: 2025-12-17
**Status**: ⚠️ CRITICAL ISSUE FOUND
**Priority**: HIGH

---

## Problem: Inconsistent Path Structures Across Modules

After cleaning up old MinIO folders, I discovered that different modules use **completely different path structures**.

---

## Current Path Structures

### 1. Fine-Tuning Dataset Uploads ✅ (CORRECT)
**Path**: `{dept}/{team}/{project}/{username}/finetuning/datasets/{dataset}/{uuid}/{file}`

**Example**:
```
technology/backend-development/construction-intelligence/admin/finetuning/datasets/test4/5d21b327.../file.csv
```

**Why Correct**:
- No redundant "role" prefix
- Clean organizational hierarchy
- User-based (uses user's dept/team, not project's)
- Username provides individual ownership

---

### 2. Chat UI Document Uploads ❌ (INCONSISTENT)
**Path**: `{role}/{dept}/{team}/{username}/{project}/{folder}/{file}`

**Example**:
```
admin/technology/backend-development/admin/construction-intelligence/documents/file.pdf
```

**Issues**:
1. ❌ Has "role" prefix (admin, user, viewer) - unnecessary
2. ❌ Different hierarchy than fine-tuning
3. ❌ Uses PROJECT's dept/team (not user's) in `upload_file_with_project()`
4. ❌ Inconsistent with fine-tuning structure

---

### 3. Agent Task Uploads ❌ (USES OLD STRUCTURE)
**Path**: `projects/{project}/{username}/agent-tasks/{task}/{task-id}/{artifacts|logs}/{file}`

**Example**:
```
projects/global-project/admin/agent-tasks/sales_analysis/task-123/artifacts/chart.html
```

**Issues**:
1. ❌ Uses "projects/" prefix instead of dept/team hierarchy
2. ❌ No organizational structure (dept/team)
3. ❌ Completely different from both document and fine-tuning paths

---

### 4. Web Scraping Uploads ❓ (NEED TO CHECK)
**Need to audit scraper_service.py**

---

## Recommended Unified Structure

### Standard Path Format (All Modules)
```
{dept}/{team}/{project}/{username}/{module}/{...specifics}/{file}
```

### Examples Per Module

#### Documents (Chat UI):
```
technology/backend-development/construction-intelligence/admin/documents/file.pdf
```

#### Extractions (Web Scraping):
```
technology/backend-development/construction-intelligence/admin/extractions/books_mystery/extract.json
```

#### Agent Tasks:
```
technology/backend-development/construction-intelligence/admin/agent-tasks/sales_analysis/task-123/artifacts/chart.html
```

#### Fine-Tuning Datasets:
```
technology/backend-development/construction-intelligence/admin/finetuning/datasets/test4/uuid/file.csv
```

#### Fine-Tuning Checkpoints:
```
technology/backend-development/construction-intelligence/admin/finetuning/checkpoints/job-name/uuid/adapters/model.bin
```

#### Exports:
```
technology/backend-development/construction-intelligence/admin/exports/chat-history.json
```

---

## Why Unification Matters

### Current Problems:
1. **File Discovery**: Different structures make it hard to find files
2. **Access Control**: RBAC rules need to handle multiple path patterns
3. **Migration**: Moving data between modules is complex
4. **User Confusion**: Users don't know where their files are
5. **Code Duplication**: Each module has different path logic

### Benefits of Unified Structure:
1. ✅ **Consistent RBAC**: One permission model for all files
2. ✅ **Easy Discovery**: All user's files under `{dept}/{team}/{project}/{username}/`
3. ✅ **Simple Backup**: Backup by dept/team/project/user
4. ✅ **Clean Code**: One path builder for all modules
5. ✅ **User Experience**: Predictable file locations

---

## Files Requiring Changes

### High Priority:
1. `/backend/app/services/minio_path_builder.py` - Update `build_document_path()`
2. `/backend/app/services/document_service.py` - Fix `upload_file_with_project()` to use user's dept/team
3. `/backend/app/services/agent_service.py` - Update agent task paths
4. `/backend/app/services/scraper_service.py` - Check and update if needed

### Medium Priority:
5. All upload endpoints that call these services
6. All download/retrieval functions
7. File listing functions

---

## Proposed Changes

### 1. Remove "role" from document paths

**Before**:
```python
path = f"{sanitized_role}/{sanitized_dept}/{sanitized_team}/{sanitized_username}/{sanitized_project}/{folder}/{filename}"
```

**After**:
```python
path = f"{sanitized_dept}/{sanitized_team}/{sanitized_project}/{sanitized_username}/{folder}/{filename}"
```

### 2. Use user's dept/team (not project's)

**Before** (document_service.py line 1373-1376):
```python
dept_name, team_name = await self._get_dept_team_names(
    department_id=project_dict.get('department_id'),  # ❌ WRONG
    team_id=project_dict.get('team_id'),              # ❌ WRONG
    db=db
)
```

**After**:
```python
dept_name, team_name = await self._get_dept_team_names(
    department_id=user_dict.get('department_id'),     # ✅ CORRECT
    team_id=user_dict.get('team_id'),                 # ✅ CORRECT
    db=db
)
```

### 3. Update agent task paths

**Before**:
```python
organizational_path = f"projects/{MinIOPathBuilder.sanitize(project_name)}/{MinIOPathBuilder.sanitize(username)}"
```

**After**:
```python
# Need dept/team from user, not project
from app.services.minio_path_builder import MinIOPathBuilder
minio_path = MinIOPathBuilder.build_agent_task_path(
    department_name=user_dept,  # From user
    team_name=user_team,        # From user
    project_name=project_name,
    username=username,
    task_name=task_name,
    task_id=task_id,
    artifact_type=artifact_type,
    filename=filename
)
```

---

## Migration Strategy

### Option 1: Big Bang (Not Recommended)
- Fix all paths at once
- Migrate all existing files
- High risk, complex

### Option 2: Gradual (Recommended) ✅
1. **Phase 1**: Fix fine-tuning (✅ DONE)
2. **Phase 2**: Fix document uploads (IN PROGRESS)
3. **Phase 3**: Fix agent tasks
4. **Phase 4**: Fix web scraping
5. **Phase 5**: Migrate old files (optional)

### For Existing Files:
- **Option A**: Leave old files as-is, only fix new uploads
- **Option B**: Create migration script to move files to new structure
- **Option C**: Create symlinks/aliases in MinIO

---

## Testing Plan

### 1. Document Upload Test
- Upload file via Chat UI
- Verify path: `technology/backend-development/{project}/{username}/documents/{file}`

### 2. Agent Task Test
- Run agent task
- Verify path: `technology/backend-development/{project}/{username}/agent-tasks/{task}/...`

### 3. Web Scraping Test
- Scrape a website
- Verify path: `technology/backend-development/{project}/{username}/extractions/{site}/...`

### 4. Fine-Tuning Test (Already Working)
- Upload dataset
- Verify path: `technology/backend-development/{project}/{username}/finetuning/datasets/...`

---

## Next Steps

1. ✅ Audit document_service.py (IN PROGRESS)
2. ⏳ Fix `build_document_path()` to remove "role" prefix
3. ⏳ Fix `upload_file_with_project()` to use user's dept/team
4. ⏳ Audit agent_service.py
5. ⏳ Audit scraper_service.py
6. ⏳ Test all upload/download operations
7. ⏳ Document final unified structure

---

## Questions for User

1. **Migration**: Should we migrate old files to the new structure, or leave them as-is?
2. **Breaking Changes**: New paths will break any external references to old paths. Acceptable?
3. **Timing**: Should we fix all modules now, or one at a time?

---

**Status**: ⚠️ ANALYSIS COMPLETE, AWAITING USER DECISION
**Recommendation**: Fix all modules to use unified structure, leave old files as-is for now
**Risk**: Medium (only affects new uploads, not existing files)

