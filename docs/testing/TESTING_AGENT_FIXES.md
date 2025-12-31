# Testing Guide: Agent Task Monitor Fixes

## Quick Test Checklist

### Test 1: Task Description Persistence ✅
```
1. Navigate to Agent Task Monitor tab
2. Type in the task description: "Analyze sales data and create visualizations"
3. Navigate to "Chat" tab
4. Navigate back to "Agent Task Monitor" tab
5. ✅ PASS: Task description should still be there
6. Click "Create Task" button
7. Navigate away and back
8. ✅ PASS: Task description should be empty (cleared after creation)
```

### Test 2: Agent Task Cancellation ✅
```
1. Navigate to Agent Task Monitor
2. Upload a test file or select existing files
3. Create a task: "Create 10 different visualization charts from the data"
4. Wait for status to change from "pending" to "running"
5. Click the "Cancel" button on the running task
6. ✅ PASS: Task should immediately show "cancelled" status
7. Check backend logs: docker-compose logs backend --tail=20
8. ✅ PASS: Should see "🔪 Killing process" and "✅ Successfully killed process"
```

## Detailed Testing Procedures

### Test 1: Persistence Across Navigation

**Objective**: Verify task description survives navigation between menus

**Steps**:
1. Open browser console (F12)
2. Navigate to Agent Task Monitor
3. Type a long task description (multiple lines)
4. In console, check storage:
   ```javascript
   sessionStorage.getItem('agent_task_draft')
   ```
   Should return your text

5. Navigate to different tabs:
   - Chat
   - Projects
   - Admin
   - Back to Agent Task Monitor

6. Verify text is restored each time

**Expected Console Logs**:
```
💾 Saved task draft to sessionStorage
📝 Restored task draft from sessionStorage
```

**Success Criteria**:
- ✅ Text preserved across all navigation
- ✅ Text preserved even after browser refresh (if not submitted)
- ✅ Text cleared after successful task creation

---

### Test 2: Task Cancellation Kills Process

**Objective**: Verify cancel button actually stops the running agent

**Setup**:
1. Ensure backend and agent-runtime containers are running:
   ```bash
   docker-compose ps
   ```

2. Open two terminal windows:
   - Terminal 1: Backend logs
     ```bash
     docker-compose logs -f backend | grep -E "(📍|🔪|🧹|✅|⚙️)"
     ```
   - Terminal 2: Agent runtime logs
     ```bash
     docker-compose logs -f agent-runtime | tail -50
     ```

**Test Procedure**:

1. Create a long-running task:
   ```
   Task: "Perform 100 iterations of complex calculations and create visualizations for each iteration"
   Max Iterations: 50
   Timeout: 600
   ```

2. Click "Create Task"

3. Watch Terminal 1 for:
   ```
   📍 Stored process for task abc123, PID: 12345
   ⚙️ Task abc123 status: running
   ```

4. Wait 5-10 seconds (let it start executing)

5. Click "Cancel" button in UI

6. Watch Terminal 1 for:
   ```
   🚫 Task abc123 cancelled in database
   🔪 Killing process for task abc123, PID: 12345
   ✅ Successfully killed process for task abc123
   🧹 Removed process reference for cancelled task abc123
   ```

7. Watch Terminal 2 - agent execution should stop immediately

**Success Criteria**:
- ✅ Task status changes to "cancelled" in UI
- ✅ Backend logs show process killed
- ✅ Agent-runtime stops executing (no more iteration logs)
- ✅ No zombie processes left behind

**Failure Indicators**:
- ❌ Task shows "cancelled" but agent keeps logging iterations
- ❌ Process kill logs not appearing
- ❌ Error messages in backend logs

---

### Test 3: Cancel Pending Task

**Objective**: Verify cancellation works for tasks that haven't started

**Steps**:
1. Create 5 tasks quickly (without waiting)
2. All should show "pending" status
3. Click "Cancel" on a pending task
4. ✅ PASS: Status changes to "cancelled"
5. ✅ PASS: Backend logs show: "ℹ️ No running process found for task {id} (may not have started yet)"

---

### Test 4: Cancel Already Completed Task

**Objective**: Verify cancel button is hidden for completed tasks

**Steps**:
1. Wait for a task to complete
2. ✅ PASS: Cancel button should not be visible
3. Task should show "completed" status with green indicator

---

### Test 5: Multiple Tasks Cancellation

**Objective**: Verify cancelling multiple tasks works correctly

**Steps**:
1. Create 3 tasks simultaneously
2. Wait for all to start running
3. Cancel them one by one
4. ✅ PASS: Each cancellation should work independently
5. ✅ PASS: Backend logs should show separate kill messages for each

---

## Backend Verification Commands

### Check Running Processes
```bash
# View process tracking dictionary
docker-compose exec backend python -c "
from app.services.agent_service import AgentOrchestrationService
print('Running processes:', AgentOrchestrationService._running_processes)
"
```

### Monitor Cancellation Events
```bash
# Real-time cancellation monitoring
docker-compose logs -f backend | grep -E "(cancel|kill|CANCEL|KILL)" --color=always
```

### Check Task Status in Database
```bash
# View recent tasks
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT
  task_id,
  status,
  LEFT(task_description, 50) as description,
  error,
  created_at,
  started_at,
  completed_at
FROM agent_tasks
ORDER BY created_at DESC
LIMIT 10;
"
```

---

## Troubleshooting

### Issue: Task description not persisting

**Check**:
```javascript
// In browser console
localStorage.getItem('agent_task_draft')
sessionStorage.getItem('agent_task_draft')
```

**Solution**: Ensure frontend container was rebuilt

### Issue: Cancel not killing process

**Check**:
```bash
# Backend logs should show process tracking
docker-compose logs backend | grep "📍 Stored process"
```

**Solution**:
1. Ensure backend was rebuilt: `docker-compose build backend`
2. Restart backend: `docker-compose restart backend`

### Issue: Process still running after cancel

**Check**:
```bash
# Check if docker exec processes are still running
docker exec agent-runtime ps aux | grep python
```

**Solution**:
1. Check if process.kill() succeeded in backend logs
2. May need to manually kill: `docker restart agent-runtime`

---

## Performance Testing

### Stress Test: Multiple Concurrent Tasks
```
1. Create 10 tasks simultaneously
2. Wait for all to start running
3. Cancel 5 of them randomly
4. Let remaining 5 complete
5. Verify:
   - No memory leaks (_running_processes dictionary cleaned up)
   - All cancelled tasks actually stopped
   - Remaining tasks completed successfully
```

### Memory Leak Test
```bash
# Before creating tasks
docker stats agent-runtime --no-stream

# Create and cancel 20 tasks

# After cancellation
docker stats agent-runtime --no-stream

# Memory should return to baseline
```

---

## Success Metrics

All tests should pass with these metrics:
- ✅ 100% task description persistence rate
- ✅ 100% cancellation success rate
- ✅ 0% zombie processes
- ✅ <2 second cancellation response time
- ✅ No memory leaks after 20+ cancel operations

---

## Documentation

See `AGENT_TASK_FIXES.md` for:
- Architecture details
- Code changes
- Implementation notes

---

**Last Updated**: 2025-12-12
**Tested By**: [Your Name]
**Test Status**: Ready for QA
