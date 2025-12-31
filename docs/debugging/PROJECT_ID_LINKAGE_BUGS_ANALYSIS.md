# Project ID Linkage - Root Cause Analysis & Fix Plan

**Date**: 2025-12-31
**Status**: 🔴 CRITICAL - Multiple interconnected bugs affecting file uploads and agent tasks

---

## 🔍 ROOT CAUSES IDENTIFIED

### **Bug #1: Upload Endpoint Missing `project_id` Parameter**
**Location**: `backend/app/main_enhanced.py:176-182`

```python
# CURRENT (BROKEN):
@app.post("/api/v1/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),  # ✅ Has session_id
    # ❌ MISSING: project_id!
    db: AsyncSession = Depends(get_db)
):
```

**Impact**: Frontend sends `project_id`, but backend IGNORES it. All files default to Global project.

**Fix Required**:
```python
@app.post("/api/v1/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    project_id: Optional[str] = Form(None),  # ✅ ADD THIS
    db: AsyncSession = Depends(get_db)
):
    # Pass project_id to document_service.upload_file()
```

---

### **Bug #2: MinIO File Persistence BROKEN**
**Evidence**:
- **Database**: `sales19.txt` exists with path `technology/itm11/sales/admin/documents/sales19.txt`
- **MinIO Reality**: `mc stat` returns "Object does not exist"
- **Entire ITM11 folder**: EMPTY

**Impact**: Files are processed, embeddings created, but original files NEVER saved to MinIO.

**Investigation Needed**:
1. Check `document_service.upload_file()` - does it call MinIO put_object?
2. Check for silent MinIO exceptions being swallowed
3. Verify MinIO client initialization and permissions

---

### **Bug #3: Agent Tasks Use Wrong Project**
**Evidence** from logs:
```
Agent MinIO path: technology/itm11/DEFAULT/admin/agent-tasks/...
Should be:        technology/itm11/SALES/admin/agent-tasks/...
```

**Location**: `backend/app/services/agent_service.py`

**Root Cause**: Agent task creation doesn't retrieve project from session/document context.

**Fix Required**:
1. When creating agent task from Sales project, detect project_id
2. Use actual project name ("sales") instead of hardcoded "default"
3. Sync files to correct project workspace

---

### **Bug #4: Frontend Project Selection Not Propagating**
**Scenarios Broken**:

1. **Scenario A**: Click Sales in sidebar → Upload files
   - **Expected**: Files go to Sales
   - **Actual**: Files go to Global
   - **Cause**: Sidebar click sets `selectedProjectId` but changes `activeTab` to 'projects', not 'upload'

2. **Scenario B**: Upload tab → Select Sales → Upload
   - **Expected**: Files go to Sales
   - **Actual**: Files go to Global
   - **Cause**: Backend ignores `project_id` (Bug #1)

3. **Scenario C**: Sales project detail → "Add Files"
   - **Expected**: Files go to Sales
   - **Actual**: Files go to Global (also seen as "global-project" in agent tasks)
   - **Cause**: `ProjectDetail.tsx` passes `projectId` but backend ignores it (Bug #1)

---

## 🔧 **FIX PRIORITY**

### **P0 - Critical (Fix Immediately)**:
1. ✅ Add `project_id` parameter to upload endpoint
2. ✅ Fix MinIO file persistence
3. ✅ Pass `project_id` to `document_service.upload_file()`

### **P1 - High**:
4. Fix agent task project detection
5. Verify all 3 upload scenarios work correctly

---

## 📊 **CURRENT STATE**

### Files in Database vs MinIO:

| Filename | Project (DB) | MinIO Path (DB) | MinIO Reality |
|----------|--------------|-----------------|---------------|
| sales19.txt | Sales | technology/itm11/sales/admin/documents/ | ❌ NOT FOUND |
| sales20.txt | Global | technology/itm11/global/admin/documents/ | ❌ NOT FOUND |
| sales21.txt | Sales | technology/itm11/sales/admin/documents/ | ❌ NOT FOUND |
| sales22.txt | Sales | technology/itm11/sales/admin/documents/ | ❌ NOT FOUND |
| sales24.txt | Sales | technology/itm11/sales/admin/documents/ | ❌ NOT FOUND |

**Status**: 0 files actually in MinIO despite DB saying they're uploaded!

---

## ✅ **FIXES ALREADY APPLIED**

1. ✅ Added `department_id` and `team_id` to UserResponse schema
2. ✅ Updated auth endpoints to return user's organizational context
3. ✅ Fixed path preview in CreateProjectModal
4. ✅ Added `projectId` prop to ChatInterface component
5. ✅ Activated ITM11 team (was NULL `is_active`)
6. ✅ Moved sales19-24 to Sales project in database (but files still don't exist in MinIO)

---

## 🚨 **NEXT ACTIONS REQUIRED**

### 1. Fix Upload Endpoint (5 min)
Add `project_id` parameter and pass to document_service

### 2. Investigate MinIO Upload (15 min)
- Check `document_service.upload_file()` implementation
- Find where MinIO `put_object()` is called
- Check for exception handling that might be swallowing errors
- Verify MinIO connection and permissions

### 3. Fix Agent Task Project (10 min)
- Modify agent task creation to detect project from context
- Use correct project name instead of "default"

### 4. End-to-End Testing (10 min)
Test all 3 upload scenarios:
- A: Sidebar → Project → Upload
- B: Upload Tab → Select Project → Upload
- C: Project Detail → Add Files → Upload

---

## 📝 **CODE LOCATIONS**

| Component | File | Line |
|-----------|------|------|
| Upload Endpoint | backend/app/main_enhanced.py | 176-256 |
| Document Service | backend/app/services/document_service.py | ? |
| Agent Service | backend/app/services/agent_service.py | ? |
| FileUpload Component | frontend/src/components/FileUpload.tsx | 113-118 |
| ProjectDetail | frontend/src/components/ProjectDetail.tsx | 451-459 |
| ChatInterface | frontend/src/components/ChatInterface.tsx | 137-139 |

---

## 🎯 **SUCCESS CRITERIA**

1. ✅ Upload a file from Upload tab with "Sales" selected → Goes to Sales project
2. ✅ Upload a file from Sales project detail "Add Files" → Goes to Sales project
3. ✅ File exists in MinIO at correct organizational path
4. ✅ Agent task from Sales project uses "sales" not "default" in workspace path
5. ✅ Agent task can find and read uploaded files

---

**End of Analysis**
