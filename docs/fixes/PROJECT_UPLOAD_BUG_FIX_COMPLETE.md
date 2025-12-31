# Project Upload Bug Fix - Complete

**Date**: 2025-12-31  
**Status**: ✅ **FIXED**

---

## 🐛 The Problem

When uploading files from **Projects → Sales → "Add Files"**, files were landing in **Global** project instead of **Sales**.

### User Report
> "I was in Project -> Sales and uploaded the file task(1).txt and it landed in global.. i think the UI chat project selector drives the file location"

**User's Theory**: ✅ CORRECT - The chat UI project selector was overriding the project-specific upload context.

---

## 🔍 Root Cause Analysis

### Technical Issue: **React Stale Closure Bug**

**Location**: `frontend/src/components/FileUpload.tsx`

The `onDrop` callback had a **stale closure** problem:

```tsx
// ❌ BEFORE (Line 83-210)
const onDrop = useCallback(async (acceptedFiles: File[]) => {
  // ...
  if (selectedProjectId) {
    formData.append('project_id', selectedProjectId)  // Uses stale value!
  }
}, [files])  // ❌ Missing selectedProjectId in dependencies!
```

### Why This Broke

1. **User Context**:
   - User had "Global" selected in main chat UI
   - `localStorage.selected_project_id = "global-uuid"`

2. **Navigation**:
   - User goes to **Projects → Sales → "Add Files"**
   - ProjectDetail passes `projectId={salesId}` to FileUpload component

3. **State Update**:
   - useEffect runs, sets `selectedProjectId` state to Sales ID ✅
   
4. **Callback Closure** (THE BUG):
   - The `onDrop` callback was created with dependency `[files]` only
   - Callback captured `selectedProjectId` in its closure
   - **BUT** the closure had the OLD value (Global or empty)
   - Callback doesn't re-create when `selectedProjectId` changes

5. **Upload Execution**:
   - User drags file to upload
   - onDrop executes with **STALE** `selectedProjectId` value
   - Backend receives wrong project_id ❌

---

## ✅ The Fix

### Changes Made to `FileUpload.tsx`

#### 1. Use External Project ID with Priority (Lines 86-88)
```tsx
// ✅ AFTER
const onDrop = useCallback(async (acceptedFiles: File[]) => {
  const currentSessionId = getSessionId()

  // ✅ FIX: Use externalProjectId with priority over internal state
  const projectIdToUse = externalProjectId || selectedProjectId
  console.log(`📁 [FileUpload.onDrop] Using project ID: ${projectIdToUse} (external: ${externalProjectId}, internal: ${selectedProjectId})`)
```

**Benefit**: Prioritizes the project ID passed from parent component (ProjectDetail) over localStorage state.

#### 2. Updated FormData to Use Prioritized Value (Lines 120-123)
```tsx
if (projectIdToUse) {
  formData.append('project_id', projectIdToUse) // ✅ FIX: Use prioritized project ID!
  console.log(`📁 [FileUpload] Uploading ${file.name} to project: ${projectIdToUse}`)
}
```

#### 3. Fixed Dependency Array (Line 215)
```tsx
}, [files, selectedProjectId, externalProjectId])  // ✅ FIX: Add project IDs to dependencies!
```

**Benefit**: Ensures callback is recreated whenever project IDs change, preventing stale closures.

---

## 🎯 How It Works Now

### Correct Flow (After Fix)

1. **User navigates**: Projects → Sales → "Add Files"

2. **ProjectDetail component**:
   ```tsx
   <FileUpload
     projectId={projectId}  // ✅ Passes Sales project ID
     hideProjectSelector={true}
     onUploadComplete={() => loadProjectData()}
   />
   ```

3. **FileUpload component**:
   - Receives `externalProjectId` prop (Sales ID)
   - Sets internal `selectedProjectId` state
   - Creates `onDrop` callback with **both** IDs in dependency array

4. **Upload execution**:
   - User drags file
   - onDrop uses: `const projectIdToUse = externalProjectId || selectedProjectId`
   - **Priority**: External prop > internal state > localStorage
   - Sends correct project_id to backend ✅

5. **Backend stores**:
   - File goes to: `technology/itm11/sales/admin/documents/file.txt` ✅

---

## 🧪 Testing the Fix

### Test Scenario 1: Upload from Project Detail Page
```
1. Navigate: Projects → View All → Sales
2. Click: "Add Files" button
3. Upload: any file (e.g., task.txt)
4. Expected: File goes to Sales project
5. Verify: Check MinIO path contains /sales/
```

### Test Scenario 2: Upload from Main Chat with Project Selector
```
1. Go to main chat page
2. Select: "Global" from project selector
3. Upload: file via Upload tab
4. Expected: File goes to Global project
5. Verify: Check MinIO path contains /global/
```

### Test Scenario 3: Switch Between Projects
```
1. Chat page: Select "Global", upload file1.txt → goes to Global ✅
2. Navigate: Projects → Sales → "Add Files"
3. Upload: file2.txt → should go to Sales ✅ (NOT Global!)
4. Navigate back to chat
5. Upload tab: Should still use Global (last selection)
```

---

## 📊 Verification

### Check Browser Console
After uploading from **Projects → Sales**, you should see:
```
📁 [FileUpload] Using external project ID: 1afbec62-a132-4c52-8b87-4905c39d652b
📁 [FileUpload.onDrop] Using project ID: 1afbec62-a132-4c52-8b87-4905c39d652b (external: 1afbec62..., internal: 1afbec62...)
📁 [FileUpload] Uploading task.txt to project: 1afbec62-a132-4c52-8b87-4905c39d652b
```

### Check Database
```sql
SELECT filename, minio_path, project_id 
FROM documents 
WHERE filename = 'task.txt' 
ORDER BY created_at DESC LIMIT 1;
```

**Expected**:
```
filename: task.txt
minio_path: technology/itm11/sales/admin/documents/task.txt
project_id: 1afbec62-a132-4c52-8b87-4905c39d652b (Sales)
```

### Check MinIO
```bash
docker-compose exec minio mc ls minio/documents/technology/itm11/sales/admin/documents/
```

**Expected**: File should exist at correct organizational path.

---

## 🎉 Summary

### What Was Fixed
✅ **Stale closure bug** - Added project IDs to callback dependency array  
✅ **Priority logic** - External prop now takes precedence over internal state  
✅ **Debug logging** - Added console logs to trace project ID selection  

### Impact
- **Projects → Sales uploads** now correctly go to Sales project
- **Chat UI project selector** still works for main upload tab
- **No interference** between project detail uploads and chat uploads

### User Experience
When you're inside a specific project view, uploads will **always** use that project, regardless of what's selected in the main chat UI project selector.

---

## 🔗 Related Files

- `frontend/src/components/FileUpload.tsx` - Fixed component
- `frontend/src/components/ProjectDetail.tsx` - Calls FileUpload with projectId prop
- `backend/app/main.py` - Upload endpoint (already correct)
- `FILE_UPLOAD_PROJECT_MAPPING_TEST_REPORT.md` - Original test documentation

---

**Status**: ✅ Fix applied, frontend restarted, ready for testing.

---

**End of Fix Report**
