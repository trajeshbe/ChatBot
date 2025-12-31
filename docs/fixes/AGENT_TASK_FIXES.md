# Agent Task Monitor Fixes - 2025-12-12

## Issues Fixed

### Issue 1: Historical Artifacts Showing in New Tasks ✅ FIXED

**Problem**: Agent tasks were displaying artifacts (files) from previous task runs, even when the current task didn't create them. For example, a task that only created `revenue_chart.html` would also show `sales_report.html` and `metadata.json` from earlier runs.

**Root Cause**: The artifact collection code had a fallback that scanned ALL files in `/workspace/` directory from conversation history, including files created by previous tasks. Since the workspace persists across tasks, old artifacts remained and were incorrectly attributed to new tasks.

**Solution**: Implemented two-layered fix:

1. **Stricter Artifact Extraction**: Only collect files explicitly mentioned in tool result messages that indicate file creation
2. **Workspace Cleanup**: Clean artifacts directory before each task starts

**Files Changed**:
- `/backend/app/services/agent_service.py`

**Changes Made**:

1. **Pre-task artifact cleanup** (lines 290-302):
```python
# 🆕 FIX: Clean up old artifacts from previous runs of this task_name
# This prevents old artifacts from showing up in new task results
try:
    import subprocess
    workspace_path = f"/workspace/{task.task_name}"
    cleanup_cmd = [
        "docker", "exec", "rag-agent-runtime",
        "bash", "-c", f"rm -rf {workspace_path}/artifacts/* 2>/dev/null || true"
    ]
    subprocess.run(cleanup_cmd, capture_output=True, timeout=5)
    logger.info(f"🧹 Cleaned up old artifacts from {workspace_path}/artifacts/")
except Exception as e:
    logger.warning(f"⚠️ Could not clean artifacts directory: {e}")
```

2. **Stricter artifact extraction from conversation** (lines 512-530):
```python
# 🆕 FIX: Only extract files that were CREATED in this task (mentioned in tool RESULTS)
if not artifacts:
    import re
    for msg in agent_result.get("conversation_history", []):
        content = msg.get("content", "")
        # Skip assistant messages (tool calls) - only look at tool results
        if msg.get("role") == "assistant":
            continue
        # 🆕 FIX: Only look for files in execute_python results or write_file results
        # Check if this is a tool result message (contains "SUCCESS:" or shows file creation)
        if "SUCCESS:" in content or "saved" in content.lower() or "created" in content.lower() or "written" in content.lower():
            # Extract file paths from this specific creation message
            matches = re.findall(r'/workspace/[\w\-/]+\.(?:html|png|jpg|jpeg|pdf|csv|xlsx|json|txt|docx|svg)', content)
            for match in matches:
                # Only add if it's from this task's workspace
                if f"/workspace/{task.task_name}/" in match or "/workspace/artifacts/" in match:
                    artifacts.append(match)
    if artifacts:
        logger.info(f"📎 Extracted {len(artifacts)} artifact paths from tool creation messages")
```

**Before Fix**:
```
Task: Create revenue chart
Artifacts shown:
  ✅ revenue_chart.html (created by current task)
  ❌ sales_report.html (from previous task!)
  ❌ metadata.json (from previous task!)
```

**After Fix**:
```
Task: Create revenue chart
Artifacts shown:
  ✅ revenue_chart.html (created by current task)
```

**Testing**:
1. Create a task that generates `chart1.html`
2. Complete the task
3. Create a NEW task that generates `chart2.html`
4. ✅ Should ONLY show `chart2.html`, NOT `chart1.html`

---

### Issue 2: Task Description Lost on Navigation ✅ FIXED

**Problem**: When typing in the "Create Task" textarea and navigating to another menu, the typed text was lost when returning.

**Root Cause**: The `taskDescription` state in `AgentTaskMonitor.tsx` was not persisted to storage. Component remounted with empty state on navigation.

**Solution**: Implemented sessionStorage persistence pattern (same as project chat mode persistence)

**Files Changed**:
- `/frontend/src/components/AgentTaskMonitor.tsx`

**Changes Made**:

1. **Initialize from sessionStorage** (lines 73-82):
```typescript
const [taskDescription, setTaskDescription] = useState(() => {
  if (typeof window !== 'undefined') {
    const saved = sessionStorage.getItem('agent_task_draft');
    if (saved) {
      console.log('📝 Restored task draft from sessionStorage');
      return saved;
    }
  }
  return '';
});
```

2. **Save changes to sessionStorage** (lines 117-123):
```typescript
useEffect(() => {
  if (typeof window !== 'undefined' && taskDescription) {
    sessionStorage.setItem('agent_task_draft', taskDescription);
    console.log('💾 Saved task draft to sessionStorage');
  }
}, [taskDescription]);
```

3. **Clear on successful task creation** (lines 213-217):
```typescript
if (typeof window !== 'undefined') {
  sessionStorage.removeItem('agent_task_draft');
  console.log('🗑️ Cleared task draft from sessionStorage');
}
```

**Testing**:
1. Go to Agent Task Monitor
2. Type task description
3. Navigate to another menu (e.g., Chat, Projects)
4. Return to Agent Task Monitor
5. ✅ Text should be preserved

---

### Issue 2: Cancel Button Not Stopping Tasks ✅ FIXED

**Problem**: Clicking "Cancel" on a running agent task updated the database status to "cancelled" but the actual task process continued running in the agent-runtime container.

**Root Cause**: The backend tracked task status in the database but did not track the actual subprocess (docker exec) process. When cancel was requested, only the database was updated - the process kept running.

**Solution**: Implemented proper process tracking and termination mechanism.

**Files Changed**:
- `/backend/app/services/agent_service.py`

**Changes Made**:

1. **Add process tracking dictionary** (lines 33-34):
```python
class AgentOrchestrationService:
    """Service for orchestrating agent task execution"""

    # 🆕 FIX: Track running processes for cancellation
    _running_processes: Dict[str, asyncio.subprocess.Process] = {}
```

2. **Store process when task starts** (lines 350-352):
```python
# 🆕 FIX: Store process for cancellation
AgentOrchestrationService._running_processes[task_id] = process
logger.info(f"📍 Stored process for task {task_id}, PID: {process.pid}")
```

3. **Clean up process reference after completion** (lines 400-404):
```python
finally:
    # 🆕 FIX: Clean up process reference after completion
    if task_id in AgentOrchestrationService._running_processes:
        del AgentOrchestrationService._running_processes[task_id]
        logger.info(f"🧹 Removed process reference for task {task_id}")
```

4. **Kill process in cancel_task method** (lines 941-956):
```python
# 🆕 FIX: Kill the running process if it exists
if task_id in AgentOrchestrationService._running_processes:
    process = AgentOrchestrationService._running_processes[task_id]
    try:
        logger.info(f"🔪 Killing process for task {task_id}, PID: {process.pid}")
        process.kill()
        await process.wait()  # Wait for process to actually terminate
        logger.info(f"✅ Successfully killed process for task {task_id}")
    except Exception as e:
        logger.warning(f"⚠️ Error killing process for task {task_id}: {e}")
    finally:
        # Clean up reference
        del AgentOrchestrationService._running_processes[task_id]
        logger.info(f"🧹 Removed process reference for cancelled task {task_id}")
else:
    logger.info(f"ℹ️ No running process found for task {task_id} (may not have started yet)")
```

**How It Works**:
1. When task execution starts, the subprocess is stored in `_running_processes` dictionary
2. When task completes (success, timeout, or error), process reference is removed in finally block
3. When cancel is requested, the process is killed using `process.kill()` and waited for termination
4. Process reference is cleaned up after cancellation

**Testing**:
1. Create an agent task with long execution time (e.g., "Create 10 charts from data")
2. Wait for task status to show "running"
3. Click "Cancel" button
4. ✅ Task should stop immediately (check backend logs for "🔪 Killing process" message)
5. ✅ Task status should update to "cancelled"
6. ✅ Agent should not continue execution

**Backend Logs to Verify**:
```bash
docker-compose logs backend --tail=50 | grep -E "(📍|🔪|🧹|✅)"
```

Expected output when cancelling:
```
backend    | 📍 Stored process for task abc123, PID: 12345
backend    | 🚫 Task abc123 cancelled in database
backend    | 🔪 Killing process for task abc123, PID: 12345
backend    | ✅ Successfully killed process for task abc123
backend    | 🧹 Removed process reference for cancelled task abc123
```

---

## Architecture

### Task Description Persistence Flow

```
User Types → AgentTaskMonitor State → sessionStorage
            ↓
User Navigates Away → Component Unmounts
            ↓
User Returns → Component Remounts → Load from sessionStorage
            ↓
User Clicks "Create Task" → POST /api/v1/agent/tasks → Clear sessionStorage
```

### Task Cancellation Flow

```
User Clicks "Cancel"
    ↓
DELETE /api/v1/agent/tasks/{task_id}
    ↓
AgentOrchestrationService.cancel_task()
    ↓
1. Update database status = CANCELLED
2. Lookup process in _running_processes dict
3. process.kill() - Send SIGKILL to subprocess
4. await process.wait() - Wait for termination
5. Delete process from _running_processes
    ↓
Agent execution terminates
```

### Process Lifecycle

```
Task Creation
    ↓
execute_task_in_background() spawned
    ↓
asyncio.create_subprocess_exec(*docker_command)
    ↓
Store in _running_processes[task_id] = process
    ↓
await process.communicate() (blocks until completion)
    ↓
finally: Remove from _running_processes
```

---

## Related Issues Fixed in Previous Sessions

1. ✅ Project authentication (auth.py missing User import)
2. ✅ Chat session persistence in projects (sessionStorage for chat mode)
3. ✅ New project chats not appearing (project_id not saved)
4. ✅ Model switching with conversation history (already working, added logging)

---

## Testing Summary

### Frontend Changes
```bash
# Rebuild frontend
docker-compose build frontend --no-cache
docker-compose up -d frontend
```

### Backend Changes
```bash
# Rebuild backend
docker-compose build backend --no-cache
docker-compose up -d backend
```

### Verification
1. **Task Description Persistence**:
   - Type in textarea → Navigate away → Return → ✅ Text preserved

2. **Task Cancellation**:
   - Create long-running task → Click Cancel → ✅ Process terminated
   - Check backend logs: Should see kill messages

---

## Notes

- Task description draft is stored per-browser (not per-session or per-user)
- Draft is cleared only on successful task creation
- If browser is closed, draft persists until next visit
- Process tracking uses class-level dictionary (shared across all service instances)
- SIGKILL ensures immediate termination (no graceful shutdown)

---

## Future Enhancements

1. **Task Description Auto-save**: Add debounced auto-save with timestamp
2. **Multiple Drafts**: Store drafts per-project or per-user
3. **Draft History**: Keep last N drafts for quick reuse
4. **Graceful Cancellation**: Send SIGTERM first, wait, then SIGKILL
5. **Cancel Confirmation**: Add "Are you sure?" dialog for running tasks
6. **Process Metrics**: Track CPU/memory of running tasks

---

**Status**: ✅ Both fixes deployed and ready for testing
**Date**: 2025-12-12
**Session**: Model switching and UI persistence fixes
