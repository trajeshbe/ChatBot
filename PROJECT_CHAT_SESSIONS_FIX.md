# Project Chat Sessions Fix

## Issue Description

When creating a new chat in a project (e.g., Science project):
1. User clicks "New Chat" button in project
2. Sends a test message
3. Navigates to a different menu (e.g., Evaluation)
4. Returns to the project
5. **❌ The new chat is NOT showing in the project's chat list**
6. Only old chats (e.g., from Dec 9) are visible

## Root Cause

The issue had **TWO separate problems**:

### Problem 1: Frontend State Not Persisting
**File**: `frontend/src/components/ProjectDetail.tsx`

When navigating away from a project and returning:
- The `isInChatMode` state was reset to `false`
- User would see project overview instead of their ongoing chat
- Chat messages existed in localStorage but weren't displayed

**Solution**: Persist chat mode in sessionStorage
```tsx
// Store chat mode per project
const [isInChatMode, setIsInChatMode] = useState(() => {
  const savedMode = sessionStorage.getItem(`project_${projectId}_chat_mode`)
  return savedMode === 'true'
})

// Save whenever it changes
useEffect(() => {
  sessionStorage.setItem(`project_${projectId}_chat_mode`, isInChatMode.toString())
}, [isInChatMode, projectId])
```

### Problem 2: Backend Not Saving project_id (CRITICAL)
**File**: `backend/app/main.py` line 932-953

When the first message was sent in a new chat session:
- Backend created `chat_sessions` record
- But **DID NOT include `project_id`**
- Session existed but wasn't linked to the project
- API call to fetch project chats didn't return the session

**Before (Broken)**:
```python
chat_session = ChatSession(
    id=uuid_lib.uuid4(),
    session_id=session_id,
    user_id=user_id,
    # ❌ project_id missing!
    created_at=datetime.utcnow(),
    last_activity=datetime.utcnow(),
    is_active=True
)
```

**After (Fixed)**:
```python
# Convert project_id to UUID
project_uuid = None
if project_id:
    try:
        project_uuid = uuid_lib.UUID(project_id) if isinstance(project_id, str) else project_id
    except (ValueError, AttributeError) as e:
        logger.warning(f"Invalid project_id format: {project_id}, error: {e}")

chat_session = ChatSession(
    id=uuid_lib.uuid4(),
    session_id=session_id,
    user_id=user_id,
    project_id=project_uuid,  # ✅ Now included!
    created_at=datetime.utcnow(),
    last_activity=datetime.utcnow(),
    is_active=True
)
db.add(chat_session)
await db.flush()
logger.info(f"📝 Created new chat session: {session_id}" + (f" in project {project_id}" if project_id else ""))
```

## Files Changed

### 1. Frontend Changes

**`frontend/src/pages/index.tsx`**
- Added stable component key to prevent React remounting
- Line 139: `key="main-chat-interface"`

**`frontend/src/components/ChatInterfaceEnhanced.tsx`**
- Added visibility change handler to save/restore messages
- Lines 642-673: Tab visibility sync logic

**`frontend/src/components/ProjectDetail.tsx`**
- Persist chat mode state in sessionStorage (lines 49-68)
- Restore chat mode on component mount
- Clear chat mode when clicking "Back" button (line 174)
- Added console logging for debugging (lines 55, 66, 171, 250, 343, 371, 377)

### 2. Backend Changes

**`backend/app/main.py`**
- Line 932-953: Added project_id to chat session creation
- Now properly associates sessions with projects
- Includes error handling for invalid project_id formats

## Testing the Fix

### Test 1: Create New Chat in Project

```
1. Navigate to Projects → Science
2. Click "New Chat" button
3. Console should show: "💬 Entering chat mode for project {id}"
4. Send a test message: "hello"
5. Backend logs: "📝 Created new chat session: {session-id} in project {project-id}"
6. Navigate to Evaluation tab
7. Console: "💾 [Tab Hidden] Saved X messages for session {id}"
8. Return to Projects → Science
9. Console: "📂 Restoring chat mode for project {id}"
10. ✅ Chat should still be visible with your message
```

### Test 2: Verify Chat in Database

```bash
# Check that new session has project_id
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT session_id, project_id, title, created_at
   FROM chat_sessions
   WHERE project_id = (SELECT id FROM projects WHERE name = 'Science')
   ORDER BY created_at DESC LIMIT 5;"
```

Expected: New session appears with project_id set to Science project UUID

### Test 3: Verify Chat Appears in Project List

```
1. In Science project, after creating chat and sending message
2. Click "Back to Project" button
3. Project overview should now show the new chat
4. Chat count should have increased
5. Click on the new chat from the list
6. ✅ Chat should load with all messages
```

### Test 4: Multiple Projects

```
1. Create chat in Science → send messages
2. Navigate away and back
3. ✅ Science chat persists
4. Navigate to Construction project
5. Create new chat → send messages
6. Navigate away and back
7. ✅ Construction chat persists
8. Return to Science project
9. ✅ Science chat still there (separate sessions)
```

## Database Schema

Chat sessions are linked to projects via foreign key:

```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE,
    user_id UUID REFERENCES users(id),
    project_id UUID REFERENCES projects(id),  -- ✅ Now properly populated
    title VARCHAR(255),
    created_at TIMESTAMP,
    last_activity TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_chat_sessions_project ON chat_sessions(project_id);
```

## API Endpoints Affected

### POST /api/v1/query
**What changed**: Now saves `project_id` when creating new chat session

**Request includes**:
```json
{
  "query": "test message",
  "session_id": "session-1234567890-abc123",
  "project_id": "ae17d425-0fe5-404f-a71e-5b20c261433c"  // Science project
}
```

**Backend behavior**:
1. Checks if session exists
2. If not, creates new `ChatSession` WITH `project_id`
3. Saves user message and assistant response
4. Session is now queryable via `/api/v1/sessions?project_id={id}`

### GET /api/v1/sessions?project_id={id}
**No changes required** - Already filters by project_id

This endpoint returns all sessions where `chat_sessions.project_id = {id}`

## Console Debug Output

When working correctly, you'll see:

```javascript
// Frontend console
💬 Entering chat mode for project ae17d425-0fe5-404f-a71e-5b20c261433c
💾 Saved chat mode for project ae17d425-0fe5-404f-a71e-5b20c261433c: true
💾 [Tab Hidden] Saved 2 messages for session session-1234567890-abc123
📂 Restoring chat mode for project ae17d425-0fe5-404f-a71e-5b20c261433c
🔄 [Tab Visible] Reloaded 2 messages (had 2)
```

```python
# Backend logs
📝 Created new chat session: session-1234567890-abc123 in project ae17d425-0fe5-404f-a71e-5b20c261433c
💾 Saved 1 user message and 1 assistant message to database
```

## Verification Queries

### Check session is linked to project
```sql
SELECT
    cs.session_id,
    cs.project_id,
    p.name as project_name,
    cs.title,
    cs.created_at,
    (SELECT COUNT(*) FROM conversation_messages WHERE session_id = cs.id) as message_count
FROM chat_sessions cs
JOIN projects p ON cs.project_id = p.id
WHERE p.name = 'Science'
ORDER BY cs.created_at DESC
LIMIT 10;
```

### Check messages are saved
```sql
SELECT
    cm.role,
    LEFT(cm.content, 50) as content_preview,
    cm.created_at,
    cs.session_id,
    p.name as project_name
FROM conversation_messages cm
JOIN chat_sessions cs ON cm.session_id = cs.id
JOIN projects p ON cs.project_id = p.id
WHERE p.name = 'Science'
ORDER BY cm.created_at DESC
LIMIT 20;
```

## Impact

**Before Fix**:
- ❌ New chats created in projects were "lost"
- ❌ Only showed old chats from database
- ❌ Sessions existed in localStorage but not in project's database records
- ❌ Navigating away lost chat interface state

**After Fix**:
- ✅ New chats immediately appear in project chat list (after first message)
- ✅ Sessions properly linked to projects in database
- ✅ Chat interface state persists when navigating between menus
- ✅ All chats are queryable via project API
- ✅ Multi-project chat isolation working correctly

## Related Issues Fixed

1. **Chat History Not Loading**: Now loads from database correctly
2. **Project Chat Isolation**: Each project has separate chat sessions
3. **Session Persistence**: Chat state survives navigation
4. **Tab Switching**: Messages saved/restored when switching tabs

## Future Enhancements

Potential improvements (not critical):
1. Real-time chat list updates (WebSocket)
2. Batch session creation API (create before first message)
3. Session title auto-generation from first message
4. Chat search within project
5. Export project chats

## Testing Status

✅ **Frontend persistence**: Verified working
✅ **Backend project_id**: Verified working
✅ **Database schema**: Confirmed correct
✅ **API endpoints**: Tested and working
✅ **Multi-project**: Tested with Science and Construction

**Last tested**: 2025-12-12
**Status**: ✅ FIXED AND VERIFIED
