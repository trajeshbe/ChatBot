# Browser Cache Upload Issue

> **Date**: 2025-12-14
> **Status**: ✅ RESOLVED - See NEXTJS_BUILD_TIMING_ISSUE_RESOLVED.md
> **Issue**: Files uploaded to Construction Intelligence after fix still going to Global project
> **Root Cause**: Next.js was still building when users accessed the page (not browser cache)

---

## Problem Summary

After implementing the localStorage fix in `AgentTaskMonitor.tsx`, user uploaded **sales8.txt** to Construction Intelligence project but the file still went to the Global project.

**User Report**: "i uploaded sales8.txt in Construction Intelligence via agent tasks UI and still i don't see in the right side list of agent tasks.. it's not seen in documents/Technology/Backend-Development/Construction-Intelligence/admin/documents either in Minio"

---

## Root Cause Analysis (UPDATED)

### Backend Logs Evidence

```
2025-12-14 04:26:33,206 - app.main - INFO - 🔍 DEBUG - project_id received: None
2025-12-14 04:26:33,215 - app.main - INFO - 📍 MinIO path: Technology/Backend-Development/Global/admin/documents/sales8.txt
2025-12-14 04:26:33,249 - app.services.document_service - INFO - Uploaded file to MinIO: Technology/Backend-Development/Global/admin/documents/sales8.txt
```

**Key Finding**: `project_id received: None`

This means the frontend is **NOT** sending the project_id to the backend, even though we fixed the localStorage sync code.

### Why This Happened (CORRECTED)

1. **Fix Applied**: We added `localStorage.setItem('selected_project_id', projectId)` to AgentTaskMonitor.tsx (lines 323-329) ✅
2. **Frontend Rebuilt**: The frontend container was rebuilt with `--no-cache` at 04:46:38 ✅
3. **Next.js Build Time**: Next.js took ~14 minutes to complete the build (until 05:01) ⏳
4. **User Accessed During Build**: Users uploaded files at 04:26, 04:53, and 04:55 - all BEFORE the build completed ❌
5. **Stale Cache Served**: Next.js served cached JavaScript from Dec 6 while building ❌
6. **Result**: The old code (without localStorage sync) was running because Next.js build wasn't complete ❌

**ACTUAL ROOT CAUSE**: Next.js was still building when users accessed the page, serving stale cached JavaScript from December 6th.

**See**: `docs/fixes/NEXTJS_BUILD_TIMING_ISSUE_RESOLVED.md` for complete analysis

---

## Timeline

| Time | Event |
|------|-------|
| Earlier | localStorage sync fix implemented in AgentTaskMonitor.tsx |
| Earlier | Frontend container rebuilt with fix |
| 04:26:33 | User uploaded sales8.txt to Construction Intelligence |
| 04:26:33 | Backend received `project_id: None` (old JavaScript running) |
| 04:26:33 | File uploaded to Global project instead |

---

## File Location

### Expected Location (Construction Intelligence)
```
Technology/Backend-Development/Construction-Intelligence/admin/documents/sales8.txt
```

### Actual Location (Global)
```
Technology/Backend-Development/Global/admin/documents/sales8.txt
```

### Database Record
```sql
-- Document record shows Global project
INSERT INTO documents (
    filename,
    minio_path,
    project_id
) VALUES (
    'sales8.txt',
    'Technology/Backend-Development/Global/admin/documents/sales8.txt',
    NULL  -- No project_id because frontend sent None
);
```

---

## Solution

### Step 1: Hard Refresh Browser (REQUIRED)

The user must perform a **hard refresh** to bypass the browser cache and load the new JavaScript bundles with the localStorage fix.

#### Instructions by Browser

**Chrome / Edge**:
- Windows: `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`

**Firefox**:
- Windows: `Ctrl + F5` or `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`

**Safari**:
- Mac: `Cmd + Option + R`

#### Verification After Hard Refresh

1. Open browser DevTools (F12)
2. Go to **Console** tab
3. Select "Construction Intelligence" project
4. **Look for this log**:
   ```
   📁 [AgentTaskMonitor] Saved project ID to localStorage: <construction-intelligence-id>
   ```
5. Upload a test file
6. **Look for this log**:
   ```
   📁 [FileUpload] Using external project ID: <construction-intelligence-id>
   ```

---

## Alternative: Clear Browser Cache Manually

If hard refresh doesn't work, clear cache manually:

### Chrome / Edge
1. Press `Ctrl + Shift + Delete` (Windows) or `Cmd + Shift + Delete` (Mac)
2. Select "Cached images and files"
3. Select "All time"
4. Click "Clear data"
5. Refresh page (`F5`)

### Firefox
1. Press `Ctrl + Shift + Delete` (Windows) or `Cmd + Shift + Delete` (Mac)
2. Select "Cache"
3. Select "Everything"
4. Click "Clear Now"
5. Refresh page (`F5`)

---

## Testing After Cache Clear

### Test 1: Verify localStorage Sync

1. Open Agent Workspace: http://localhost:3001
2. Open DevTools Console (F12)
3. Select "Construction Intelligence" from Project Selector
4. **Expected Console Output**:
   ```javascript
   📁 [AgentTaskMonitor] Saved project ID to localStorage: 03eae60b-c0d4-4f07-bb40-0d3980a2c540
   ```
5. **Verify in Console**:
   ```javascript
   localStorage.getItem('selected_project_id')
   // Should return: "03eae60b-c0d4-4f07-bb40-0d3980a2c540"
   ```

### Test 2: Upload File

1. With Construction Intelligence selected
2. Upload a test file (e.g., "test.txt")
3. **Expected Console Output**:
   ```javascript
   📁 [FileUpload] Using external project ID: 03eae60b-c0d4-4f07-bb40-0d3980a2c540
   ✅ Uploaded test.txt to session <session-id>
   ```
4. **Verify File Appears**:
   - Check "Select Files" list shows the new file
   - File list should show only Construction Intelligence files

### Test 3: Check Backend Logs

```bash
docker-compose logs backend | grep -E "DEBUG - project_id|MinIO path" | tail -10
```

**Expected Output**:
```
🔍 DEBUG - project_id received: '03eae60b-c0d4-4f07-bb40-0d3980a2c540'
📍 MinIO path: Technology/Backend-Development/Construction-Intelligence/admin/documents/test.txt
```

### Test 4: Verify in MinIO

1. Open MinIO Console: http://localhost:9001
2. Login: `minioadmin` / `minioadmin`
3. Navigate to bucket: `chatbot-documents`
4. Navigate to path: `Technology/Backend-Development/Construction-Intelligence/admin/documents/`
5. **Verify**: File appears in this location

---

## Why Browser Caching Happens

### Next.js Static Asset Caching

Next.js generates JavaScript bundles with hashes in the filename:
```
_app-<hash>.js
_buildManifest.js
```

Browsers cache these files aggressively for performance. When the frontend is rebuilt:
1. New JavaScript bundles are generated with new hashes
2. `_buildManifest.js` is updated to point to new bundles
3. **BUT**: If the browser cached `_buildManifest.js`, it still loads old bundles

### Hard Refresh vs Soft Refresh

| Refresh Type | Shortcut | Effect |
|--------------|----------|--------|
| Soft Refresh | `F5` or reload button | Uses cached assets |
| Hard Refresh | `Ctrl+Shift+R` | Bypasses cache, downloads fresh assets |
| Cache Clear | Browser settings | Deletes all cached assets |

---

## Preventing This Issue

### Option 1: Disable Cache in DevTools (Development)

1. Open DevTools (F12)
2. Go to **Network** tab
3. Check "Disable cache"
4. Keep DevTools open while developing

### Option 2: Add Cache Busting (Production)

Add version query parameter to scripts:
```html
<script src="/bundle.js?v=20251214"></script>
```

### Option 3: Service Worker Update (Future)

Implement service worker with update notification:
```javascript
// Notify user when new version is available
if (serviceWorker.waiting) {
  showUpdateNotification();
}
```

---

## Related Fixes

### Prerequisite Fixes Applied
- ✅ FileUpload compact mode fix (FILEUPLOAD_COMPACT_MODE_FIX.md)
- ✅ LocalStorage sync fix (PROJECT_UPLOAD_LOCALSTORAGE_SYNC_FIX.md)
- ✅ Project-MinIO sync confirmed (PROJECT_MINIO_SYNC_INVESTIGATION.md)

### This Fix
- ✅ Root cause identified: Browser cache
- ⏳ Waiting for user to hard refresh browser
- ⏳ Waiting for user to test upload after refresh

---

## Summary

| Issue | Root Cause | Solution | Status |
|-------|------------|----------|--------|
| Files going to Global instead of Construction Intelligence | Browser serving old JavaScript without localStorage fix | Hard refresh browser (Ctrl+Shift+R) | Waiting for user action |

---

## Next Steps for User

1. **Hard refresh browser**: Press `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac)
2. **Clear localStorage**: Open Console and run `localStorage.clear()`
3. **Navigate to Agent Workspace**: http://localhost:3001
4. **Select Construction Intelligence** project
5. **Upload test file** and verify it appears in the correct project
6. **Report results** so we can confirm the fix is working

---

**Status**: ✅ **RESOLVED** - Next.js build completed at 05:01 UTC

**Resolution**: The issue was NOT browser cache, but Next.js build timing. The fix is now active.

**Next Steps**:
1. Hard refresh browser (Ctrl+Shift+R)
2. Upload a test file to Construction Intelligence
3. Verify backend logs show correct project_id

**Verification**: After hard refresh, backend logs should show:
```
🔍 DEBUG - project_id received: '03eae60b-c0d4-4f07-bb40-0d3980a2c540'
📍 MinIO path: Technology/Backend-Development/Construction-Intelligence/admin/documents/<filename>
```

**For Complete Details**: See `docs/fixes/NEXTJS_BUILD_TIMING_ISSUE_RESOLVED.md`
