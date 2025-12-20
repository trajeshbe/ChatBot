# Streaming Endpoint Project ID Fix

**Date**: 2025-12-18
**Status**: ✅ FIXED

## Problem

When using streaming mode, the wrong project documents were being retrieved:

- **User selected**: "Construction Intelligence" project
- **Documents retrieved**: "Global" project documents (Wikipedia, etc.)
- **Expected**: Children Books from Construction Intelligence project

## Root Cause

1. **Frontend state issue**: The `selectedProjectId` state was stale/incorrect, sending Global project ID even though the session was on Construction Intelligence
2. **Backend trusted parameter**: The streaming endpoint used the `project_id` parameter from the frontend without validating against the session

## Solution Applied

### Backend Fix (main.py lines 694-710)

**Changed streaming endpoint to prioritize session's project_id over parameter:**

```python
# 🔧 FIX: Load project_id from session instead of parameter (frontend state may be stale)
resolved_project_id = None
if session_id:
    # Query the session to get its project_id
    session_query = select(ChatSession).where(ChatSession.session_id == session_id)
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()
    if session and session.project_id:
        resolved_project_id = str(session.project_id)
        logger.info(f"📁 Streaming: Using project_id from session: {resolved_project_id}")
    elif project_id:
        # Fallback to parameter if session has no project
        resolved_project_id = project_id
elif project_id:
    # No session, use parameter
    resolved_project_id = project_id

# Use resolved_project_id instead of parameter
user_preferences = {
    "project_id": resolved_project_id,  # Not 'project_id' parameter
    ...
}
```

**Logic:**
1. If `session_id` provided → Load project_id from session (source of truth)
2. Fallback to parameter only if session has no project
3. Prevents stale frontend state from causing wrong project

### Frontend Debug Logs Added

**ChatInterfaceEnhanced.tsx (lines 1228-1230)**:
```typescript
console.log('🔍 Streaming: selectedProjectId =', selectedProjectId)
console.log('🔍 Streaming: projectId =', projectId)
console.log('🔍 Streaming: activeProjectId =', activeProjectId)
```

**useStreamingChat.ts (lines 97, 123)**:
```typescript
console.log('🔍 useStreamingChat: config.projectId =', config.projectId);
console.log('🔍 project_id in params:', params.get('project_id'));
```

These logs will help diagnose frontend state issues.

## Testing

**To verify the fix:**

1. Start a chat in "Construction Intelligence" project
2. Enable streaming mode
3. Ask: "can you list all children books? all 29 books"

**Expected logs:**
```
📁 Streaming: Using project_id from session: 03eae60b-c0d4-4f07-bb40-0d3980a2c540
📄 Project documents used: ['Children_Books_All - smart']
```

**Expected response:**
- ✅ Lists books from Children_Books_All document
- ✅ Shows sources from Construction Intelligence project
- ❌ NO Wikipedia or Global documents

## Files Modified

1. **backend/app/main.py** - Added project_id resolution from session
2. **frontend/src/components/ChatInterfaceEnhanced.tsx** - Added debug logs
3. **frontend/src/hooks/useStreamingChat.ts** - Added debug logs

## Impact

- ✅ **Streaming mode now respects session's project** instead of trusting frontend state
- ✅ **Consistent behavior** across page refreshes and state changes
- ✅ **Prevents wrong documents** from being retrieved
- ⚠️ **Temporary fix**: Frontend state management should still be investigated

## Future Work

**Frontend state synchronization** (not urgent, backend fix is reliable):
- Investigate why `selectedProjectId` doesn't update when session changes
- Consider loading project from session API on mount instead of localStorage
- Add project change detection in useEffect

## Related Issues

- Frontend project selector state may not sync with session
- localStorage `selected_project_id` may be stale
- Project dropdown hidden when `projectId` prop is provided

---

**Result**: Users will now get correct project-scoped documents in streaming mode, matching the non-streaming behavior.
