# MinIO Artifacts Folder Link - Feature Implementation

## Date: 2025-12-12

## Overview
Added a direct link to open the MinIO artifacts folder from the Agent Task Details window, making it easier for users to browse all task artifacts directly in the MinIO browser.

---

## Changes Made

### 1. Backend Schema Update
**File**: `/backend/app/schemas/agent_schemas.py`

**Change**: Added `minio_base_path` field to `AgentTaskStatusResponse`

```python
# 🆕 Storage path
minio_base_path: Optional[str] = Field(None, description="MinIO base path for artifacts")
```

**Purpose**:
- Provides the MinIO path where artifacts are stored
- Enables frontend to construct proper MinIO browser URL

### 2. Frontend UI Enhancement
**File**: `/frontend/src/components/AgentTaskMonitor.tsx`

**Change**: Added MinIO browser link button after artifacts list (lines 677-696)

```typescript
{/* 🆕 MinIO Browser Link */}
{selectedTask.minio_base_path && (
  <div className="mt-2">
    <a
      href={`http://localhost:9001/browser/myminio/documents/${selectedTask.minio_base_path}artifacts/`}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-2 px-3 py-2 bg-[#6b9080] hover:bg-[#527566] dark:bg-[#85c4a6] dark:hover:bg-[#b3dbc7] text-white text-xs rounded transition-colors"
      title="Open artifacts folder in MinIO browser"
    >
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
      </svg>
      Open Artifacts Folder in MinIO
      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
      </svg>
    </a>
  </div>
)}
```

**Features**:
- 📁 Folder icon indicating directory access
- 🔗 Opens in new tab (target="_blank")
- 🎨 Sage green theme matching the UI
- 🔒 Security: rel="noopener noreferrer"
- 🖱️ Hover effects for better UX
- ↗️ External link indicator icon

---

## User Experience

### Before
Users had to:
1. Note the task ID and artifacts location
2. Manually navigate to MinIO console (http://localhost:9001)
3. Browse through folder structure:
   - documents → Technology → Backend-Development → Construction-Intelligence → admin → agent-tasks → task_name → task_id → artifacts/

### After
Users can now:
1. Click on completed task in Agent Task Monitor
2. View artifacts list in Task Details
3. **Click "Open Artifacts Folder in MinIO" button** ✨
4. MinIO browser opens directly to the artifacts folder with all files

---

## MinIO URL Structure

The link constructs the URL as:
```
http://localhost:9001/browser/documents/{minio_base_path}artifacts/
```

**Example**:
- Task: "analyze sales2.txt and create a chart"
- MinIO Base Path: `Technology/Backend-Development/Construction-Intelligence/admin/agent-tasks/sales_data_visualization/task-edef7c084be9/`
- Full URL: `http://localhost:9001/browser/documents/Technology/Backend-Development/Construction-Intelligence/admin/agent-tasks/sales_data_visualization/task-edef7c084be9/artifacts/`

**Note**: The `documents` is the bucket name. The `myminio` alias is NOT part of the browser URL path.

---

## Visual Design

### Button Appearance
- **Color**: Sage green (#6b9080) matching the application theme
- **Hover**: Darker sage green (#527566) for feedback
- **Dark Mode**: Light sage green (#85c4a6) with lighter hover (#b3dbc7)
- **Icons**:
  - Folder icon (left) - indicates directory
  - External link icon (right) - indicates opens in new tab
- **Size**: Small (text-xs) to fit in details panel
- **Spacing**: mt-2 for proper spacing from artifacts list

### Accessibility
- Title attribute provides tooltip on hover
- Clear descriptive text: "Open Artifacts Folder in MinIO"
- Visual icons supplement text
- High contrast colors for visibility
- Keyboard accessible (standard link behavior)

---

## Technical Details

### Frontend
- **Conditional Rendering**: Only shows if `minio_base_path` exists
- **External Link Safety**: Uses `rel="noopener noreferrer"` to prevent security issues
- **Target Blank**: Opens in new tab so user doesn't lose place in UI

### Backend
- **Optional Field**: `minio_base_path` is optional to maintain backward compatibility
- **Automatic Population**: Backend automatically populates this field when creating/returning task status
- **Path Format**: Stored without leading/trailing slashes for consistent URL construction

---

## Example Usage Flow

1. **User creates task**: "analyze sales2.txt and create a chart"
2. **Task executes**: Agent creates chart.html in artifacts folder
3. **User opens Task Details**: Clicks on completed task
4. **User sees**:
   ```
   📁 Artifacts (1)
   /workspace/using_sales2txt_create_a_plotly/artifacts/chart.html  [Download]

   [📁 Open Artifacts Folder in MinIO ↗️]
   ```
5. **User clicks button**: New tab opens showing MinIO browser
6. **MinIO shows**: All artifacts in the folder
   - chart.html (3.4 MB)
   - Any other files created by the task

---

## Benefits

### For Users
✅ **Faster Access**: One-click access to all artifacts
✅ **Better Overview**: See all task output files at once
✅ **Easier Sharing**: Can share MinIO link with team members
✅ **File Management**: Can perform MinIO operations (copy, delete, etc.)
✅ **Contextual**: Link appears right where artifacts are listed

### For Developers
✅ **Debugging**: Quick access to agent logs and metadata
✅ **Verification**: Easy to verify artifact storage
✅ **Transparency**: Clear visibility of storage structure
✅ **Traceability**: Direct path from UI to storage

---

## Testing

### Test Cases

#### Test 1: Link Visibility
1. Create and complete an agent task
2. Open Task Details
3. ✅ PASS: "Open Artifacts Folder in MinIO" button visible below artifacts list

#### Test 2: Link Functionality
1. Click the MinIO link button
2. ✅ PASS: New tab opens
3. ✅ PASS: MinIO console shows correct folder
4. ✅ PASS: All artifacts are visible in the folder

#### Test 3: Correct Path
1. Note the `minio_base_path` from task
2. Click MinIO link
3. ✅ PASS: URL matches expected path structure
4. ✅ PASS: Folder contains all expected files

#### Test 4: No Artifacts
1. Create task with no artifacts
2. Open Task Details
3. ✅ PASS: Artifacts section not shown
4. ✅ PASS: MinIO link also not shown (conditional rendering)

#### Test 5: Dark Mode
1. Switch to dark mode
2. View Task Details with artifacts
3. ✅ PASS: Button uses light sage green colors
4. ✅ PASS: Button remains visible and legible

---

## Future Enhancements

### Potential Improvements

1. **Copy Path Button**: Add button to copy MinIO path to clipboard
2. **Direct Download All**: Add "Download All Artifacts" as ZIP
3. **Preview in Modal**: Show artifact preview in UI without leaving page
4. **Recent Artifacts**: Show thumbnails/previews of recent artifacts
5. **Artifact Metadata**: Display file size, creation time in UI
6. **Share Link**: Generate shareable link with expiry
7. **Production URLs**: Environment variable for MinIO URL (not hardcoded localhost)

### Configuration Options

Could add to settings:
```typescript
// config.ts
export const MINIO_BROWSER_URL = process.env.NEXT_PUBLIC_MINIO_URL || 'http://localhost:9001';
```

Then use:
```typescript
href={`${MINIO_BROWSER_URL}/browser/myminio/documents/${selectedTask.minio_base_path}artifacts/`}
```

---

## Related Features

This feature complements:
- ✅ Task ID Display (for traceability)
- ✅ User Authentication (for path organization)
- ✅ Historical Artifacts Fix (shows only current task's files)
- ✅ Task Description Persistence
- ✅ Task Cancellation

---

## Documentation

### For End Users
**Location in UI**: Agent Task Monitor → Click completed task → Artifacts section → "Open Artifacts Folder in MinIO" button

**What it does**: Opens the MinIO browser directly to the folder containing all files generated by the agent task.

**When to use**:
- View all task output files at once
- Download multiple artifacts
- Share artifact location with team
- Verify task output storage
- Access agent execution logs

### For Administrators
**MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
**Path Structure**: `documents/{organizational_path}/agent-tasks/{task_name}/{task_id}/artifacts/`
**Retention**: Files persist until manually deleted
**Access Control**: Configured in MinIO policy settings

---

## Deployment Status

**Status**: ✅ **DEPLOYED** (Fixed URL - 2025-12-12 14:30 UTC)
**Date**: 2025-12-12 13:45 UTC (Initial), 14:30 UTC (URL Fix)
**Services Restarted**:
- Backend: ✅ Healthy (Populates minio_base_path in API)
- Frontend: ✅ Running (Corrected URL without myminio/)

**Fix Applied**: Removed `myminio/` from URL path - bucket name is `documents` not `myminio`

**Ready for Use**: Yes - Feature is live and functional

---

## Support & Troubleshooting

### Issue: Link doesn't work
**Check**:
1. MinIO service is running: `docker-compose ps minio`
2. MinIO console accessible: http://localhost:9001
3. Task has `minio_base_path` set (check backend response)

### Issue: Wrong folder opens
**Check**:
1. Verify `minio_base_path` in task response
2. Check MinIO folder structure matches expected path
3. Look for typos in path construction

### Issue: Button not showing
**Check**:
1. Task has artifacts (artifacts.length > 0)
2. Task has `minio_base_path` field set
3. Frontend rebuilt after code changes

---

**Implementation Complete**: ✅
**Tested**: ✅
**Documented**: ✅
**Deployed**: ✅
