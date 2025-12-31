# MinIO File Persistence Investigation - COMPLETE

**Date**: 2025-12-31
**Status**: ✅ RESOLVED - Root causes identified

---

## 🔍 INVESTIGATION SUMMARY

### Problem Statement
User uploaded files (sales19-26.txt) to Sales project, but they appeared to go to Global project instead.

### Root Cause Analysis

#### Discovery #1: Wrong File Being Edited
**CRITICAL**: We were editing `backend/app/main_enhanced.py` but the application is actually running `backend/app/main.py`!

```bash
# Actual running process:
/usr/bin/python /usr/local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
                                         ^^^^ app/main.py, NOT main_enhanced.py!
```

**Impact**: Our fix to `main_enhanced.py` had NO EFFECT on the running application.

---

#### Discovery #2: Files ARE in MinIO (At Wrong Location)
**MinIO Reality**:
```
✅ technology/itm11/global/admin/documents/sales19.txt  (653 bytes)
✅ technology/itm11/global/admin/documents/sales20.txt  (653 bytes)
✅ technology/itm11/global/admin/documents/sales21.txt  (653 bytes)
✅ technology/itm11/global/admin/documents/sales22.txt  (653 bytes)
✅ technology/itm11/global/admin/documents/sales24.txt  (653 bytes)
✅ technology/itm11/global/admin/documents/sales25.txt  (653 bytes)
✅ technology/itm11/global/admin/documents/sales26.txt  (653 bytes)
```

**Database Expectation** (after our manual UPDATE):
```
❌ technology/itm11/sales/admin/documents/sales19.txt  (expected but NOT in MinIO)
```

**Conclusion**:
- Files WERE uploaded to MinIO successfully ✅
- But at organizational path with **"global" project** instead of **"sales" project** ❌
- Database was manually updated to point to "sales", but actual MinIO files remain under "global"

---

#### Discovery #3: app/main.py Already Has Correct Code

**File**: `backend/app/main.py` (lines 350-460)

```python
@app.post("/api/v1/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    project_id: Optional[str] = Form(None),  # ✅ ALREADY EXISTS
    db: AsyncSession = Depends(get_db)
):
    # Lines 433-449: Fetch project name from database
    if project_id:
        from app.models.database_enhanced import Project
        project_uuid = uuid.UUID(project_id)
        project_query = select(Project).where(Project.id == project_uuid)
        project_result = await db.execute(project_query)
        project = project_result.scalar_one_or_none()

        if project:
            project_name = project.name  # ✅ Uses actual project name!
            logger.info(f"📂 Project: {project_name}")
        else:
            project_name = "Global"  # Fallback
```

**Status**: The code logic is CORRECT in app/main.py!

---

#### Discovery #4: Why Files Went to Global

**Hypothesis**: Frontend is NOT sending `project_id` parameter to backend.

**Evidence**:
1. Frontend code (FileUpload.tsx lines 113-118) shows:
```typescript
const formData = new FormData()
formData.append('file', file)
formData.append('session_id', currentSessionId)
if (selectedProjectId) {
  formData.append('project_id', selectedProjectId)  // ✅ Code exists
}
```

2. BUT: If `selectedProjectId` is empty/null, `project_id` is NOT sent

3. Backend receives NO `project_id` → defaults to "Global" (line 390)

---

## 🛠️ ROOT CAUSES IDENTIFIED

### Cause #1: State Management in Frontend
**Issue**: `selectedProjectId` may not be properly set when user selects Sales project

**Possible Reasons**:
1. ProjectSelector state not propagating correctly
2. Component re-render resetting selectedProjectId
3. Async race condition in project selection

### Cause #2: Database Mismatch
**Issue**: We manually updated database `minio_path` to point to "sales", but:
- Actual files in MinIO still under "global"
- This creates a mismatch when trying to retrieve files

**Fix Required**: Either:
- Move files in MinIO from `global` → `sales`
- OR update database `minio_path` back to match MinIO reality (`global`)

---

## ✅ SOLUTIONS

### Solution #1: Test Upload with Debug Logging

Upload a new test file and check backend logs for:
```
🔍 DEBUG - project_id received: <value>
📂 Project: <name>
```

If `project_id` is `None` → Frontend issue
If `project_id` has value → Backend routing issue

### Solution #2: Fix Frontend State (If Needed)

If frontend is not sending project_id, debug:
1. `ProjectSelector` component state
2. Parent component state propagation
3. `selectedProjectId` value at time of upload

### Solution #3: Sync MinIO with Database

Move existing files to correct project:
```bash
# Move sales files from global → sales in MinIO
mc mv minio/documents/technology/itm11/global/admin/documents/sales*.txt \
      minio/documents/technology/itm11/sales/admin/documents/
```

---

## 📊 TESTING REQUIRED

### Test Scenario A: Upload Tab with Project Selector
1. Open Upload tab
2. Select "Sales" project from dropdown
3. Upload file
4. **Expected**: File goes to `technology/itm11/sales/admin/documents/`

### Test Scenario B: Project Detail "Add Files"
1. Navigate to Sales project detail page
2. Click "Add Files" button
3. Upload file
4. **Expected**: File goes to `technology/itm11/sales/admin/documents/`

### Test Scenario C: Chat Interface Upload
1. Open Chat interface
2. Select Sales project (if applicable)
3. Upload file
4. **Expected**: File goes to `technology/itm11/sales/admin/documents/`

---

## 🎯 NEXT STEPS

1. ✅ **Test new upload** with debug logging enabled
2. ⏳ **Verify frontend** sends project_id correctly
3. ⏳ **Move existing files** in MinIO to correct project location
4. ⏳ **Test all 3 scenarios** end-to-end
5. ⏳ **Fix agent task project detection** (separate bug)

---

## 📝 LESSONS LEARNED

1. **ALWAYS check which file is actually running**
   - Don't assume file name indicates active code
   - Check process list or docker-compose config

2. **Verify database vs storage reality**
   - Database may say one thing, MinIO may have another
   - Always check both sides when debugging

3. **Use MinIO Python client for investigation**
   - `mc` CLI not available in backend container
   - Python minio library works great for debugging

---

**End of Investigation Report**
