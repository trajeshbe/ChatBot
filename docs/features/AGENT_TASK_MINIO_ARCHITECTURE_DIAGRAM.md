# Agent Task MinIO Storage - Architecture Diagram

## Current Problem: Shared Workspace

```
┌─────────────────────────────────────────────────────────────┐
│  Agent Runtime Container (rag-agent-runtime)                │
│                                                              │
│  /workspace/                                                 │
│  ├── input/           ← Shared by ALL tasks                 │
│  ├── output/          ← Shared by ALL tasks                 │
│  ├── artifacts/       ← ❌ PROBLEM: Shared by ALL tasks    │
│  │   ├── chart.html           (Task A - Dec 11 06:05)      │
│  │   ├── sales_chart.html     (Task B - Dec 11 06:34)      │
│  │   ├── laptop_sales.html    (Task C - Dec 11 07:36)      │
│  │   └── revenue_chart.png    (Task D - Dec 11 09:22) ❌   │
│  └── temp/            ← Shared by ALL tasks                 │
│                                                              │
│  When Task D scans artifacts/ directory:                    │
│  📎 Finds ALL files from Tasks A, B, C, D                   │
│  ❌ Incorrectly attributes old files to Task D              │
└─────────────────────────────────────────────────────────────┘
```

**Issues**:
- ❌ Artifact cross-contamination between tasks
- ❌ Can't identify which files belong to which task
- ❌ No persistence (lost on container restart)
- ❌ Concurrent tasks conflict with each other

---

## Proposed Solution: Task-Specific Workspaces + MinIO

### Part 1: Isolated Workspaces (Container)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Agent Runtime Container (rag-agent-runtime)                        │
│                                                                      │
│  /workspace/                                                         │
│  ├── task-a81656d4e7e9/      ← Task D (isolated workspace)         │
│  │   ├── input/                                                     │
│  │   │   └── sales2.txt       ← Input file copied here             │
│  │   ├── artifacts/           ← ✅ ONLY Task D's artifacts         │
│  │   │   └── revenue_chart.html                                    │
│  │   └── logs/                                                      │
│  │       └── agent.log        ← Task-specific logs                 │
│  │                                                                  │
│  ├── task-45777df8cd16/      ← Task C (different workspace)        │
│  │   ├── input/                                                     │
│  │   │   └── sales2.txt                                            │
│  │   ├── artifacts/                                                 │
│  │   │   └── laptop_sales_chart.html                               │
│  │   └── logs/                                                      │
│  │                                                                  │
│  └── task-4c2f2f9712c0/      ← Task B (different workspace)        │
│      ├── input/                                                     │
│      ├── artifacts/                                                 │
│      │   └── sales_chart.html                                      │
│      └── logs/                                                      │
│                                                                      │
│  ✅ Each task has isolated workspace                               │
│  ✅ No cross-contamination possible                                │
└─────────────────────────────────────────────────────────────────────┘
```

### Part 2: Persistent MinIO Storage

```
┌──────────────────────────────────────────────────────────────────────┐
│  MinIO (S3-Compatible Object Storage)                               │
│  Bucket: chatbot-bucket                                             │
│                                                                      │
│  projects/                                                           │
│  └── global-project/                    ← Project level            │
│      └── admin/                         ← User level               │
│          └── agent-tasks/               ← Task category            │
│              │                                                       │
│              ├── sales_analysis_chart/  ← Task name (LLM-generated)│
│              │   │                                                   │
│              │   ├── task-a81656d4e7e9/  ← Execution #1            │
│              │   │   ├── input/                                     │
│              │   │   │   └── sales2.txt                             │
│              │   │   ├── artifacts/                                 │
│              │   │   │   └── revenue_chart.html  ✅                 │
│              │   │   ├── logs/                                      │
│              │   │   │   ├── agent.log                              │
│              │   │   │   ├── stdout.log                             │
│              │   │   │   └── stderr.log                             │
│              │   │   └── metadata.json  ← Task info & results      │
│              │   │                                                   │
│              │   └── task-b92847cd32a1/  ← Execution #2 (re-run)   │
│              │       ├── input/                                     │
│              │       ├── artifacts/                                 │
│              │       ├── logs/                                      │
│              │       └── metadata.json                              │
│              │                                                       │
│              ├── data_processing/       ← Different task           │
│              │   └── task-12345678abcd/                             │
│              │       └── ...                                        │
│              │                                                       │
│              └── web_scraping_job/      ← Another task             │
│                  └── task-98765432dcba/                             │
│                      └── ...                                        │
│                                                                      │
│  ✅ Hierarchical organization                                       │
│  ✅ Easy to browse by project/user/task                            │
│  ✅ Supports multiple executions of same task                      │
│  ✅ Persistent storage (survives container restarts)               │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Complete Workflow

```
┌────────────────────────────────────────────────────────────────────────┐
│  Step 1: User Creates Task                                            │
│  ────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  User Input: "use sales2.txt and create a plotly chart"               │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Backend (AgentService)                                          │ │
│  │  1. Generate task_id: "task-a81656d4e7e9"                        │ │
│  │  2. LLM generates task_name: "sales_analysis_chart"              │ │
│  │  3. Build MinIO path:                                            │ │
│  │     projects/global-project/admin/agent-tasks/                   │ │
│  │     sales_analysis_chart/task-a81656d4e7e9/                      │ │
│  │  4. Store in database (agent_tasks table)                        │ │
│  │  5. Launch Docker container with env vars:                       │ │
│  │     - TASK_ID=task-a81656d4e7e9                                  │ │
│  │     - TASK_NAME=sales_analysis_chart                             │ │
│  │     - PROJECT_ID=global-project                                  │ │
│  │     - USERNAME=admin                                             │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│  Step 2: Agent Executes in Isolated Workspace                         │
│  ────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Agent Container (entrypoint_agent.py)                           │ │
│  │                                                                   │ │
│  │  1. Create workspace: /workspace/task-a81656d4e7e9/              │ │
│  │     ├── input/                                                    │ │
│  │     ├── artifacts/   ← Python code saves here                    │ │
│  │     └── logs/                                                     │ │
│  │                                                                   │ │
│  │  2. Agent Loop (THINK → PLAN → ACT → OBSERVE)                    │ │
│  │     - Read sales2.txt from /workspace/task-a81656d4e7e9/input/   │ │
│  │     - Execute Python: fig.write_html('artifacts/chart.html')     │ │
│  │     - File saved to /workspace/task-a81656d4e7e9/artifacts/      │ │
│  │                                                                   │ │
│  │  3. Scan artifacts directory (task-specific, not shared!)        │ │
│  │     ✅ Only finds: revenue_chart.html                            │ │
│  │     ✅ No old files from other tasks                             │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│  Step 3: Upload to MinIO (Persistent Storage)                         │
│  ────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Agent Container (_upload_to_minio)                              │ │
│  │                                                                   │ │
│  │  For each file in workspace:                                     │ │
│  │                                                                   │ │
│  │  /workspace/task-a81656d4e7e9/input/sales2.txt                   │ │
│  │  → MinIO: projects/.../sales_analysis_chart/task-.../input/      │ │
│  │                                                                   │ │
│  │  /workspace/task-a81656d4e7e9/artifacts/revenue_chart.html       │ │
│  │  → MinIO: projects/.../sales_analysis_chart/task-.../artifacts/  │ │
│  │                                                                   │ │
│  │  /workspace/task-a81656d4e7e9/logs/agent.log                     │ │
│  │  → MinIO: projects/.../sales_analysis_chart/task-.../logs/       │ │
│  │                                                                   │ │
│  │  metadata.json (task info, duration, model, status)              │ │
│  │  → MinIO: projects/.../sales_analysis_chart/task-.../            │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ✅ All files persisted to MinIO                                       │
│  ✅ Local workspace can be cleaned up                                  │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│  Step 4: User Downloads Artifact (Frontend)                           │
│  ────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Frontend (AgentTaskMonitor.tsx)                                 │ │
│  │                                                                   │ │
│  │  Task: sales_analysis_chart                                      │ │
│  │  Status: ✅ Completed (45.5s)                                     │ │
│  │  Model: qwen2.5-coder:7b                                         │ │
│  │                                                                   │ │
│  │  Artifacts:                                                       │ │
│  │  📄 revenue_chart.html (3.5 MB)  [Download] [Preview]            │ │
│  │  📄 agent.log (24 KB)            [Download]                      │ │
│  │                                                                   │ │
│  │  Click Download →                                                │ │
│  │    GET /api/v1/agent-tasks/task-a81656d4e7e9/artifacts/download  │ │
│  │    ?path=artifacts/revenue_chart.html                            │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Backend API (agent_routes.py)                                   │ │
│  │                                                                   │ │
│  │  1. Get task from database                                       │ │
│  │  2. Check user permissions (owns task or is admin)               │ │
│  │  3. Build MinIO path from task.minio_base_path + artifact path   │ │
│  │  4. Stream file from MinIO to client                             │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ✅ User downloads correct artifact                                    │
│  ✅ No confusion with other tasks                                      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Benefits Summary

### Before (Shared Workspace)
```
❌ All tasks use /workspace/artifacts/
❌ Task D finds files from Tasks A, B, C
❌ Can't identify which artifact belongs to which task
❌ No persistence (lost on container restart)
❌ Concurrent tasks conflict
```

### After (Isolated Workspace + MinIO)
```
✅ Each task gets /workspace/{task_id}/artifacts/
✅ Task D only sees its own files
✅ Clear artifact attribution
✅ Persistent storage in MinIO
✅ Concurrent tasks fully isolated
✅ Hierarchical organization (project/user/task/execution)
✅ Support for re-running same task (multiple executions)
✅ Complete audit trail
```

---

## Database Schema Changes

```sql
-- Before
CREATE TABLE agent_tasks (
    id UUID PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE,
    task_description TEXT,
    artifacts TEXT[],  -- Just file paths, not clear which are which
    ...
);

-- After
CREATE TABLE agent_tasks (
    id UUID PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE,
    task_name VARCHAR(255),         -- NEW: "sales_analysis_chart"
    task_description TEXT,
    artifacts TEXT[],               -- Relative paths: "artifacts/chart.html"
    minio_base_path TEXT,           -- NEW: Full MinIO prefix path
    ...
);

-- Example row:
{
  "task_id": "task-a81656d4e7e9",
  "task_name": "sales_analysis_chart",
  "task_description": "use sales2.txt and create a plotly chart",
  "artifacts": ["artifacts/revenue_chart.html"],
  "minio_base_path": "projects/global-project/admin/agent-tasks/sales_analysis_chart/task-a81656d4e7e9/"
}
```

---

## API Changes

### New Endpoints

```
GET  /api/v1/agent-tasks/{task_id}/artifacts
     → List all artifacts for a task

GET  /api/v1/agent-tasks/{task_id}/artifacts/download?path={path}
     → Download specific artifact

GET  /api/v1/agent-tasks/{task_id}/logs
     → View task execution logs

GET  /api/v1/agent-tasks?task_name={name}
     → Find all executions of a task by name
```

### Enhanced Task Response

```json
{
  "task_id": "task-a81656d4e7e9",
  "task_name": "sales_analysis_chart",
  "task_description": "use sales2.txt and create a plotly chart",
  "status": "completed",
  "model": "qwen2.5-coder:7b",
  "duration_seconds": 45.5,
  "artifacts": [
    {
      "name": "revenue_chart.html",
      "size": 3607088,
      "last_modified": "2025-12-11T09:23:07Z",
      "path": "artifacts/revenue_chart.html",
      "download_url": "/api/v1/agent-tasks/task-a81656d4e7e9/artifacts/download?path=artifacts/revenue_chart.html"
    }
  ],
  "minio_paths": {
    "base": "projects/global-project/admin/agent-tasks/sales_analysis_chart/task-a81656d4e7e9/",
    "input": "projects/.../input/",
    "artifacts": "projects/.../artifacts/",
    "logs": "projects/.../logs/"
  }
}
```

---

## Implementation Checklist

### Phase 1: Backend Foundation
- [ ] Add LLM task name generation function
- [ ] Extend MinIOPathBuilder with agent task methods
- [ ] Add migration for task_name and minio_base_path columns
- [ ] Update AgentService.create_task() to generate name and path

### Phase 2: Agent Container
- [ ] Update entrypoint_agent.py to use task-specific workspace
- [ ] Implement MinIO upload after task completion
- [ ] Update artifact scanning to use task workspace
- [ ] Add metadata.json generation

### Phase 3: API Layer
- [ ] Add /agent-tasks/{id}/artifacts endpoint
- [ ] Add /agent-tasks/{id}/artifacts/download endpoint
- [ ] Add /agent-tasks/{id}/logs endpoint
- [ ] Update task response schema

### Phase 4: Frontend
- [ ] Update AgentTaskMonitor to show task name
- [ ] Add artifact download buttons
- [ ] Add log viewer
- [ ] Add MinIO path display for debugging

### Phase 5: Testing
- [ ] Test single task execution
- [ ] Test concurrent tasks (isolation)
- [ ] Test task re-execution
- [ ] Test artifact download
- [ ] Test MinIO cleanup

---

## Timeline

- **Day 1**: Backend changes (task name, MinIO paths, database)
- **Day 2**: Agent container (workspace isolation, MinIO upload)
- **Day 3**: API endpoints & Frontend (download UI)
- **Day 4**: Testing & bug fixes
- **Day 5**: Documentation & deployment

**Total**: ~1 week for full implementation and testing

---

**Status**: Ready for implementation 🚀
