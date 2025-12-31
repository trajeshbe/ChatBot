# Project Upload Bug Analysis

## Issue
User uploaded `task(1).txt` while viewing **Projects → Sales**, but file landed in **Global** project.

## Root Cause: Stale Closure in FileUpload Component

### The Bug

**Location**: `frontend/src/components/FileUpload.tsx`

**Line 83-210**: The `onDrop` callback:
```tsx
const onDrop = useCallback(async (acceptedFiles: File[]) => {
  // ...
  if (selectedProjectId) {
    formData.append('project_id', selectedProjectId)  // ❌ Uses selectedProjectId
  }
  // ...
}, [files])  // ❌ BUG: Missing selectedProjectId in dependencies!
```

### Why This Breaks

1. **Initial State**: User has "Global" selected in chat UI → `localStorage.selected_project_id = "global-id"`

2. **Navigation**: User goes to Projects → Sales → "Add Files"

3. **Component Mount**: 
   - ProjectDetail passes `projectId={salesId}` to FileUpload
   - useEffect runs (line 66-81), sets `selectedProjectId` state to Sales ID ✅
   
4. **Callback Creation**:
   - `onDrop` callback is created with dependency `[files]`
   - Callback captures `selectedProjectId` in closure
   - **IF** the callback was created BEFORE useEffect completed, it has STALE value
   
5. **File Upload**:
   - User drags file
   - onDrop executes with STALE `selectedProjectId` (Global or empty)
   - Backend receives wrong project_id ❌

## The Fix

Add `selectedProjectId` to the dependency array:

```tsx
}, [files, selectedProjectId])  // ✅ FIX: Add selectedProjectId
```

This ensures the callback is recreated whenever `selectedProjectId` changes.

## Additional Issue: Race Condition

Even with the fix above, there's a potential race condition:

**Line 248-264**: ProjectSelector onChange handler writes to localStorage:
```tsx
onChange={(projectId, project) => {
  setSelectedProjectId(projectId)
  setSelectedProject(project)
  if (projectId) {
    localStorage.setItem('selected_project_id', projectId)  // ⚠️ Overwrites!
  }
```

If the main chat UI's ProjectSelector is active WHILE the user is in the ProjectDetail modal, changes to that selector could overwrite localStorage and affect the upload.

## Recommended Solution

**Option 1**: Fix the dependency array (minimal change)
**Option 2**: Don't rely on localStorage when `externalProjectId` is provided (safer)

```tsx
const projectIdToUse = externalProjectId || selectedProjectId

// In onDrop:
if (projectIdToUse) {
  formData.append('project_id', projectIdToUse)
}
```

**Option 3**: Use `externalProjectId` directly in onDrop without state (best)
```tsx
const onDrop = useCallback(async (acceptedFiles: File[]) => {
  const projectId = externalProjectId || selectedProjectId  // Priority to external!
  // ...
  if (projectId) {
    formData.append('project_id', projectId)
  }
}, [files, externalProjectId, selectedProjectId])
```
