# Agent Task Monitor UI Testing Guide

**Date**: 2025-11-30
**Status**: ✅ READY TO TEST

---

## What Was Integrated

The **Agent Task Monitor** component has been successfully integrated into the main application UI. You can now:

1. ✅ Create agent tasks from the UI
2. ✅ Monitor task execution in real-time
3. ✅ View task status, results, and errors
4. ✅ Cancel running tasks
5. ✅ View task history with auto-refresh

---

## How to Access the Agent Task Monitor

### Step 1: Open the Application

Navigate to: **http://localhost:3001**

### Step 2: Login

Use your credentials to log in to the application.

### Step 3: Click "Agent Tasks" in Sidebar

In the left sidebar, you'll see a new menu item:

```
🤖 Agent Tasks
```

Click on it to open the Agent Task Monitor.

---

## UI Components Integrated

### Files Modified

1. **`frontend/src/pages/index.tsx`**
   - Imported `AgentTaskMonitor` component
   - Added `'agent'` to activeTab state type
   - Added rendering section for agent tab

2. **`frontend/src/components/SidebarModern.tsx`**
   - Imported `Bot` icon from lucide-react
   - Added `'agent'` to Props interface
   - Added "Agent Tasks" menu item to `secondaryNavItems`

### Component Location

**Path**: `frontend/src/components/AgentTaskMonitor.tsx`

**Features**:
- Task creation form with validation
- Model selection (4 LLM models available)
- Max iterations slider (1-50)
- Timeout configuration (30s - 1800s)
- Auto-refreshing task list (updates every 5 seconds)
- Color-coded status badges
- Task detail modal with full metadata
- Cancel button for running tasks

---

## How to Test

### Test 1: Create a Simple Task

1. Click on **"Agent Tasks"** in the sidebar
2. In the "Create New Task" form:
   - **Task Description**: `List the available tools and describe what each tool does`
   - **Model**: `qwen2.5-coder:7b` (default)
   - **Max Iterations**: `5`
   - **Timeout**: `120` seconds
3. Click **"Create Task"**
4. Watch the task list update automatically

**Expected Result**:
- Task appears in the list with status "pending"
- Status should transition: `pending` → `running` → `failed` or `completed`
- The task list auto-refreshes every 5 seconds

### Test 2: View Task Details

1. After creating a task, wait for it to execute
2. Click on the task row in the task list
3. A modal will open showing:
   - Full task description
   - Model used
   - Execution timeline (started, completed, duration)
   - Current iteration / max iterations
   - Result (if completed)
   - Tools used
   - LLM calls made
   - Error details (if failed)

### Test 3: Create Multiple Tasks

1. Create 3-5 tasks with different descriptions:
   - "What is the current date and time?"
   - "List all files in the workspace"
   - "Analyze the structure of the codebase"
2. Watch them execute concurrently
3. Observe the real-time status updates

### Test 4: Cancel a Task

1. Create a task with a long timeout (e.g., 300 seconds)
2. While it's running (status = "running"), click the **Cancel** button
3. Task status should change to "cancelled"

### Test 5: Filter by Session

1. Create tasks from different chat sessions
2. Use the session_id filter in the component to view tasks from a specific session
3. Verify filtering works correctly

---

## Expected Behavior

### Task Statuses

| Status | Badge Color | Meaning |
|--------|------------|---------|
| `pending` | Yellow | Task queued, waiting to execute |
| `running` | Blue | Currently executing |
| `completed` | Green | Finished successfully |
| `failed` | Red | Encountered an error |
| `cancelled` | Gray | User cancelled the task |

### Auto-Refresh

- Task list refreshes automatically every **5 seconds**
- No need to manually reload the page
- Real-time status updates

### Task Metadata

Each task displays:
- **Task ID**: Unique identifier (e.g., `task-abc123`)
- **Description**: What the task is supposed to do
- **Model**: Which LLM model is being used
- **Status**: Current execution state
- **Created At**: When the task was created
- **Duration**: How long it took to execute (if completed)

---

## Current Limitations

### ⚠️ Expected Failures

Currently, tasks will **fail immediately** because the agent runtime code is not yet deployed. You'll see:

**Error Message**:
```
Task failed with return code 1
```

**This is expected!** The infrastructure is working correctly:
1. ✅ Task creation works
2. ✅ Task is stored in database
3. ✅ Task execution is triggered
4. ✅ Status updates work
5. ❌ Agent runtime code not yet implemented

The failure happens in the `agent-runtime` container because `/app/entrypoint_agent.py` doesn't exist yet.

---

## Backend API Endpoints (Working)

All backend endpoints are fully functional:

| Endpoint | Method | Status |
|----------|--------|--------|
| `/api/v1/agent/tasks` | POST | ✅ Working |
| `/api/v1/agent/tasks/{id}` | GET | ✅ Working |
| `/api/v1/agent/tasks` | GET | ✅ Working |
| `/api/v1/agent/tasks/{id}` | DELETE | ✅ Working |
| `/api/v1/agent/health` | GET | ✅ Working |

---

## Testing Checklist

- [ ] Can access Agent Tasks menu in sidebar
- [ ] Task creation form is visible and functional
- [ ] Can create a new task
- [ ] Task appears in task list
- [ ] Task list auto-refreshes every 5 seconds
- [ ] Can click on task to view details
- [ ] Task detail modal shows all metadata
- [ ] Status badges display correct colors
- [ ] Can cancel a running task
- [ ] Multiple tasks can be created and monitored
- [ ] UI is responsive and doesn't freeze

---

## Troubleshooting

### Issue: "Agent Tasks" menu not visible

**Solution**:
1. Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)
2. Check frontend container is running: `docker-compose ps frontend`
3. Restart frontend: `docker-compose restart frontend`

### Issue: Task creation fails

**Solution**:
1. Check backend logs: `docker-compose logs backend --tail 50`
2. Verify database migration was applied:
   ```bash
   docker-compose exec postgres psql -U postgres -d ragchatbot -c "\d agent_tasks"
   ```
3. Check API health: `curl http://localhost:8000/api/v1/agent/health`

### Issue: Tasks stuck in "pending" forever

**Solution**:
This is normal for now - the agent runtime is not deployed yet. The task will eventually transition to "failed" after attempting to execute.

### Issue: Task list not updating

**Solution**:
1. Check browser console for errors (F12)
2. Verify API endpoint is accessible: `curl http://localhost:8000/api/v1/agent/tasks`
3. Check network tab in browser dev tools

---

## Next Steps

After UI testing is complete:

1. **Deploy Agent Runtime Code**
   - Implement `/app/entrypoint_agent.py` in agent-runtime container
   - Integrate LLM-driven tool calling
   - Test end-to-end task execution

2. **Add Authentication**
   - Integrate with existing auth system
   - Filter tasks by user_id
   - Add permission checks

3. **Enhance UI**
   - Add WebSocket support for real-time updates
   - Add result visualization
   - Add task templates

4. **Production Readiness**
   - Add error boundaries
   - Implement retry logic
   - Add monitoring and alerts

---

## Support

If you encounter issues:
1. Check this guide first
2. Review backend logs: `docker-compose logs backend`
3. Review frontend logs: `docker-compose logs frontend`
4. Check database: `docker-compose exec postgres psql -U postgres -d ragchatbot`
5. Refer to comprehensive documentation:
   - `docs/features/AGENT_INTEGRATION_GUIDE.md`
   - `docs/features/AGENT_QUICK_START.md`

---

**Happy Testing!** 🚀
