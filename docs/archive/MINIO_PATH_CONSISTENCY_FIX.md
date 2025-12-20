# MinIO Path Consistency Fix

**Date**: 2025-12-19
**Status**: 🔧 SOLUTION IDENTIFIED

## The Inconsistency

### Current State (Two Different Formats)

**Document Uploads** (Standard):
```
Technology/Backend-Development/Global/admin/documents/Short Story3.txt
                                      ↑
                               Title-Case, hyphenated
```

**Fine-Tuning** (Different):
```
technology/backend-development/global/admin/finetuning/datasets/story8/...
     ↑
lowercase, sanitized
```

## Root Cause

**Path Builder Logic** (`minio_path_builder.py` line 135-144):

```python
# Sanitize all components
sanitized_dept = MinIOPathBuilder.sanitize(department)    # "Technology" → "technology"
sanitized_team = MinIOPathBuilder.sanitize(team)          # "Backend Development" → "backend-development"

path = f"{sanitized_dept}/{sanitized_team}/..."
```

The `sanitize()` method **lowercases and replaces spaces** with hyphens.

**But look at actual MinIO storage**:
```bash
$ mc ls myminio/documents/
Technology/      ← Title-Case exists!
technology/      ← lowercase also exists! (inconsistency)
```

**Document upload uses**: `Technology/Backend-Development/` (stored in DB, written to MinIO)
**Fine-tuning uses**: `technology/backend-development/` (path builder sanitizes)

## The Standard

Looking at the `documents` table, the **official standard** is:

```
{Department}/{Team}/{Project}/{Username}/{Folder}/{Filename}

Department: Title-Case (Technology, AI-ML, Data-Operations)
Team:       Title-Case with hyphens (Backend-Development, Tech-Team-1)
Project:    Title-Case with hyphens (Global, ChatBot-RAG)
Username:   lowercase (admin, john.doe)
```

**Example**:
```
Technology/Backend-Development/Global/admin/documents/file.txt
```

## The Fix

**Option**: Use team/dept names **as-is from database** without sanitizing case.

### Why This Works

1. **Database already stores proper format**:
   ```sql
   departments.name = "Technology"  (not "technology")
   teams.name = "Backend Development" (not "backend-development")
   ```

2. **Just replace spaces with hyphens**, keep case:
   ```python
   "Backend Development" → "Backend-Development" (not "backend-development")
   ```

3. **MinIO/S3 is case-sensitive** - using consistent case avoids duplicates like:
   - `Technology/...` (correct)
   - `technology/...` (wrong, duplicate folder)

### Implementation

**File**: `backend/app/services/minio_path_builder.py`

**Current** (line 78-93):
```python
@staticmethod
def sanitize(name: str) -> str:
    """Sanitize a name for use in MinIO paths"""
    if not name:
        return "unknown"

    # Lowercase, replace spaces/special chars
    sanitized = name.lower()
    sanitized = sanitized.replace(' ', '-')
    sanitized = re.sub(r'[^a-z0-9\-_.]', '', sanitized)

    if not sanitized:
        return "unknown"

    return sanitized
```

**Should Be**:
```python
@staticmethod
def sanitize(name: str, preserve_case: bool = True) -> str:
    """
    Sanitize a name for use in MinIO paths.

    Args:
        name: The name to sanitize
        preserve_case: If True, keeps original case (for dept/team/project).
                      If False, lowercases (for usernames).

    Returns:
        Sanitized name suitable for MinIO paths
    """
    if not name:
        return "unknown"

    # Replace spaces with hyphens
    sanitized = name.replace(' ', '-')

    # Remove special characters (keep alphanumeric, hyphens, underscores, dots)
    if preserve_case:
        # Keep case for departments, teams, projects
        sanitized = re.sub(r'[^a-zA-Z0-9\-_.]', '', sanitized)
    else:
        # Lowercase for usernames
        sanitized = sanitized.lower()
        sanitized = re.sub(r'[^a-z0-9\-_.]', '', sanitized)

    if not sanitized:
        return "unknown"

    return sanitized
```

**Update `build_document_path()`** (line 135-138):
```python
# Before
sanitized_dept = MinIOPathBuilder.sanitize(department)
sanitized_team = MinIOPathBuilder.sanitize(team)
sanitized_username = MinIOPathBuilder.sanitize(username)
sanitized_project = MinIOPathBuilder.sanitize(project_name)

# After
sanitized_dept = MinIOPathBuilder.sanitize(department, preserve_case=True)
sanitized_team = MinIOPathBuilder.sanitize(team, preserve_case=True)
sanitized_username = MinIOPathBuilder.sanitize(username, preserve_case=False)  # lowercase
sanitized_project = MinIOPathBuilder.sanitize(project_name, preserve_case=True)
```

## Result After Fix

**All paths will be consistent**:

```
Technology/Backend-Development/Global/admin/documents/file.txt
Technology/Backend-Development/Global/admin/finetuning/datasets/story8/...
Technology/Backend-Development/Global/admin/finetuning/datasets/story8/checkpoints/...
```

**No more**:
- ❌ `technology/...` (lowercase dept)
- ❌ `backend-development/...` (lowercase team)
- ❌ Duplicate folders

## Migration Plan

Since changing the path format, we need to handle existing files:

### Option 1: Move All Files to New Format (Clean)

```bash
# Move lowercase to Title-Case
mc cp --recursive \
  myminio/documents/technology/ \
  myminio/documents/Technology/

# Delete old lowercase folder
mc rm --recursive myminio/documents/technology/
```

### Option 2: Add Fallback Logic (Backward Compatible)

Keep old code that checks both paths temporarily:

```python
def get_file_path_with_fallback(dept, team, project, user, filename):
    # Try new format first (Title-Case)
    new_path = f"Technology/{team}/{project}/{user}/documents/{filename}"
    if minio_exists(new_path):
        return new_path

    # Fallback to old format (lowercase)
    old_path = f"technology/{team.lower()}/.../{filename}"
    if minio_exists(old_path):
        logger.warning(f"Using legacy path: {old_path}")
        return old_path

    raise FileNotFoundError(...)
```

## Recommendation

**Go with Option 1 (Clean Move)**:

1. **Immediate**: Update `sanitize()` method to preserve case
2. **Background**: Move existing files from `technology/` to `Technology/`
3. **Result**: Clean, consistent structure

This ensures:
- ✅ All paths use same format
- ✅ No duplicate folders (`Technology/` AND `technology/`)
- ✅ Consistent with database naming
- ✅ Easier to understand and maintain

---

**Status**: Solution designed, ready to implement
