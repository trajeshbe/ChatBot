# Agent Task MinIO Path Issue - Analysis

**Date**: 2025-12-21
**Issue**: Agent task artifacts use wrong MinIO path (backend-development instead of user's team)

---

## Problem Statement

### Issue 1: Unable to Download Artifacts
User cannot download `sales_report.html` from `/workspace/sales_data_plot/artifacts/`

### Issue 2: Wrong MinIO Path
**Current Path**:
```
documents/technology/backend-development/construction-intelligence/admin/agent-tasks/sales_data_plot/task-c773a3adb072/artifacts
```

**Expected Path** (for admin user in ITM11 team):
```
documents/technology/itm11/construction-intelligence/admin/agent-tasks/sales_data_plot/task-c773a3adb072/artifacts
```

---

## Root Cause Analysis

### Database Investigation

```sql
SELECT task_id, task_name, team, department, minio_base_path
FROM agent_tasks
WHERE task_name LIKE '%sales%'
ORDER BY created_at DESC
LIMIT 2;
```

**Results**:
```
task_id: task-c773a3adb072
task_name: sales_data_plot
team: NULL  ❌
department: NULL  ❌
minio_base_path: technology/backend-development/construction-intelligence/admin/agent-tasks/sales_data_plot/task-c773a3adb072/
```

**Problem**: `team` and `department` columns are NULL, causing MinIO path builder to use hardcoded "backend-development"

---

## Code Analysis

### Files with "backend-development" Hardcoded

Found 8 files with case-insensitive matches:
1. `backend/app/tasks/finetuning_tasks.py` (already fixed)
2. `backend/app/services/document_service.py`
3. **`backend/app/services/minio_path_builder.py`** ⚠️ Key file
4. **`backend/app/services/agent_service.py`** ⚠️ Creates agent tasks
5. **`backend/app/api/routes/agent_routes.py`** ⚠️ Entry point
6. `backend/app/services/terminal_session_manager.py`
7. `backend/app/agents/tool_registry.py`
8. `backend/app/agents/project_estimator/workflow.py`

### Key Code Flow

```
1. Frontend → POST /api/v1/agent/tasks
2. agent_routes.py:create_agent_task()
   - Gets current_user ✅ (already implemented)
   - Calls service.create_task(user_id=user_id)
3. agent_service.py:create_task()
   - Creates agent_task record
   - Sets team=? department=? ❌ (likely NULL or hardcoded)
4. MinIO path builder
   - Builds path using team/department
   - Falls back to "backend-development" if NULL
```

---

## Comparison with Finetuning Fix

### What We Fixed for Finetuning

**File**: `app/api/routes/finetuning_routes.py`
```python
# Query user's primary team from user_teams junction table
team_query = text("""
    SELECT t.name
    FROM teams t
    JOIN user_teams ut ON t.id = ut.team_id
    WHERE ut.user_id = :user_id
    ORDER BY ut.assigned_at DESC
    LIMIT 1
""")
team_result = await db.execute(team_query, {"user_id": str(user.id)})
team_row = team_result.first()
team_name = team_row[0] if team_row else "General"
```

**Result**: Finetuning jobs now correctly use `ITM11` instead of `backend-development`

### Same Fix Needed for Agent Tasks

Need to apply similar fix in:
1. `agent_service.py:create_task()` - Query user's team before creating task
2. Populate `team` and `department` columns in agent_tasks table
3. MinIO path builder will use correct team

---

## minio_path_builder.py Analysis

From grep results, this file contains examples like:
```python
# Line 218: team='Backend Development'
# Line 226: Path example with backend-development
'technology/backend-development/construction-intelligence/admin/agent-tasks/sales_analysis_chart/task-a81656d4e7e9/artifacts/revenue_chart.html'
```

**This file is the path builder - it's downstream from agent_service.py**

The root fix is in `agent_service.py` where the task is created!

---

## Proposed Fix

### Step 1: Update agent_service.py

**Location**: `app/services/agent_service.py:create_task()`

**Add team query** (similar to finetuning_routes.py):
```python
from sqlalchemy import text

async def create_task(self, request, user_id=None, project_id=None):
    # Get user's primary team if user_id provided
    team_name = None
    department_name = None

    if user_id:
        # Query user's primary team
        team_query = text("""
            SELECT t.name, d.name as dept_name
            FROM teams t
            JOIN user_teams ut ON t.id = ut.team_id
            LEFT JOIN departments d ON t.department_id = d.id
            WHERE ut.user_id = :user_id
            ORDER BY ut.assigned_at DESC
            LIMIT 1
        """)
        team_result = await self.db.execute(team_query, {"user_id": str(user_id)})
        team_row = team_result.first()
        if team_row:
            team_name = team_row[0]
            department_name = team_row[1] if team_row[1] else "Technology"

    # Create agent_task with team and department
    agent_task = AgentTask(
        task_id=task_id,
        task_description=request.task_description,
        team=team_name,  # ✅ Now populated!
        department=department_name,  # ✅ Now populated!
        created_by=user_id,
        ...
    )
```

### Step 2: Restart Backend

```bash
docker-compose restart backend
```

### Step 3: Test with New Agent Task

Create a new agent task (e.g., sales_data_plot2) and verify:
- Team = ITM11
- Department = Technology
- MinIO path = `technology/itm11/...`

---

## Files to Fix

### Critical Files (Must Fix)

1. **`backend/app/services/agent_service.py`**
   - Add team/department query in `create_task()`
   - Similar to finetuning_routes.py fix

### Documentation Files (Just Examples)

2. `backend/app/services/minio_path_builder.py`
   - Update docstring examples to use "ITM11" instead of "Backend Development"
   - Not critical, just examples in comments

### Other Files (May Need Review)

3. `backend/app/services/document_service.py` - May have similar hardcoded team
4. `backend/app/services/terminal_session_manager.py` - May have similar issue
5. `backend/app/agents/tool_registry.py` - May have similar issue
6. `backend/app/agents/project_estimator/workflow.py` - May have similar issue

---

## Testing Plan

### 1. Create Test Agent Task

```bash
curl -X POST http://localhost:8000/api/v1/agent/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Test task for ITM11 path verification",
    "max_iterations": 5
  }'
```

### 2. Verify Database

```sql
SELECT task_id, task_name, team, department, minio_base_path
FROM agent_tasks
WHERE task_description LIKE '%Test task for ITM11%'
ORDER BY created_at DESC
LIMIT 1;
```

**Expected**:
```
team: ITM11
department: Technology
minio_base_path: technology/itm11/.../
```

### 3. Verify MinIO Path

Check that artifacts are uploaded to correct path:
```bash
docker-compose exec backend python3 << 'EOF'
from minio import Minio
client = Minio("minio:9000", access_key="minioadmin", secret_key="minioadmin", secure=False)
objects = client.list_objects("documents", prefix="technology/itm11/", recursive=True)
for obj in objects:
    print(f"✅ {obj.object_name}")
EOF
```

### 4. Verify Download Works

Try downloading artifact from UI and verify it works.

---

## Artifact Download Issue

This may be a SEPARATE issue from the path problem. The download might fail due to:

1. **Incorrect artifact path in database**
   - Artifact path: `/workspace/sales_data_plot/artifacts/sales_report.html`
   - MinIO path: `technology/backend-development/.../artifacts/sales_report.html`
   - Mismatch between local workspace path and MinIO path

2. **MinIO upload not completing**
   - Check if artifacts are actually uploaded to MinIO
   - Agent may generate file locally but not upload it

3. **Download route issue**
   - Frontend download link may not match backend expectation
   - Need to check artifact download route implementation

---

## Summary

### Root Cause

Agent tasks have `team` and `department` columns set to NULL, causing MinIO path builder to use hardcoded "backend-development" instead of user's actual team ("ITM11").

### Solution

Apply same fix as finetuning jobs:
1. Query `user_teams` table in `agent_service.py:create_task()`
2. Populate `team` and `department` columns
3. MinIO path builder will automatically use correct path

### Priority

**High** - This affects:
- All agent task artifact paths
- Organizational hierarchy in MinIO
- Artifact download functionality
- Multi-tenant data isolation

---

## Status

⏳ **Issue Identified** - Not yet fixed (requires separate session)

**Related to**: Finetuning MinIO path fix (FIX #2) - same root cause

**Next Steps**:
1. Fix `agent_service.py` with team query
2. Restart backend
3. Create test agent task
4. Verify team/path
5. Test artifact download

---

**Date**: 2025-12-21 10:10 UTC

---
