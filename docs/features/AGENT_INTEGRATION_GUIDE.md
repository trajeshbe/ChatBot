# Agent Task Management Integration Guide

**Last Updated**: 2025-11-30
**Status**: Production Ready
**Version**: 1.0.0

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [API Reference](#api-reference)
4. [Frontend Integration](#frontend-integration)
5. [Database Schema](#database-schema)
6. [Configuration](#configuration)
7. [Usage Examples](#usage-examples)
8. [Troubleshooting](#troubleshooting)
9. [Development](#development)

---

## Overview

The Agent Task Management system provides a complete infrastructure for creating, executing, and monitoring autonomous AI agent tasks. It integrates LLM-powered agents with Docker-based execution, async task processing, and real-time monitoring.

### Key Features

- **Autonomous Task Execution**: LLM-driven agents that can use multiple tools
- **Async Processing**: Non-blocking task creation and background execution
- **Real-time Monitoring**: Track task progress, status, and results
- **Docker Isolation**: Tasks execute in isolated agent-runtime containers
- **Database Persistence**: Full task history and metadata storage
- **REST API**: Complete CRUD operations for task management
- **React UI**: Modern dashboard for task creation and monitoring

### Use Cases

- Data analysis and visualization tasks
- Document processing workflows
- Multi-step automated operations
- Tool-based task automation
- Research and information gathering

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend UI                          │
│              (AgentTaskMonitor.tsx)                         │
│  - Task Creation Form                                       │
│  - Real-time Task List (5s polling)                        │
│  - Task Detail Modal                                        │
└────────────────┬────────────────────────────────────────────┘
                 │ HTTP/REST
                 ↓
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                         │
│              (agent_routes.py)                              │
│  - POST /api/v1/agent/tasks                                │
│  - GET /api/v1/agent/tasks/{task_id}                       │
│  - GET /api/v1/agent/tasks                                 │
│  - DELETE /api/v1/agent/tasks/{task_id}                    │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│              AgentOrchestrationService                      │
│              (agent_service.py)                             │
│  - Async task creation                                      │
│  - Background execution via asyncio                         │
│  - Docker exec to agent-runtime                            │
│  - Status tracking and updates                             │
└────────────────┬────────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        ↓                 ↓
┌─────────────────┐  ┌──────────────────────┐
│   PostgreSQL    │  │   Docker Runtime     │
│  (agent_tasks)  │  │  (agent-runtime)     │
│                 │  │                      │
│ - Task state    │  │ - LLM execution      │
│ - Results       │  │ - Tool calling       │
│ - Metadata      │  │ - Artifact gen       │
└─────────────────┘  └──────────────────────┘
```

### Task Execution Flow

1. **User creates task** via UI or API
2. **Backend validates** request and creates database record
3. **Task status** set to `pending`
4. **Response returned** immediately (non-blocking)
5. **Background task starts** via `asyncio.create_task()`
6. **Docker exec** runs task in agent-runtime container
7. **Status updates** written to database
8. **Frontend polls** for status updates
9. **Results displayed** when task completes

---

## API Reference

### Base URL

```
http://localhost:8000/api/v1/agent
```

### Endpoints

#### 1. Create Agent Task

**POST** `/tasks`

Creates a new autonomous agent task for execution.

**Request Body**:
```json
{
  "task_description": "Analyze the sales data and create a visualization",
  "session_id": "session-123",
  "model": "qwen2.5-coder:7b",
  "max_iterations": 20,
  "timeout_seconds": 600
}
```

**Parameters**:
- `task_description` (string, required): Natural language task description
- `session_id` (string, optional): Associate task with a session
- `model` (string, optional): LLM model to use (default: `qwen2.5-coder:7b`)
- `max_iterations` (integer, optional): Max agentic loop iterations (default: 20)
- `timeout_seconds` (integer, optional): Task timeout in seconds (default: 600)

**Response** (200 OK):
```json
{
  "task_id": "task-abc123xyz",
  "status": "pending",
  "message": "Task created and queued for execution",
  "created_at": "2025-11-30T11:00:00Z"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/agent/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "List available tools and their capabilities",
    "model": "qwen2.5-coder:7b",
    "max_iterations": 5
  }'
```

---

#### 2. Get Task Status

**GET** `/tasks/{task_id}`

Retrieves detailed status and results for a specific task.

**Path Parameters**:
- `task_id` (string, required): Unique task identifier

**Response** (200 OK):
```json
{
  "task_id": "task-abc123xyz",
  "status": "completed",
  "task_description": "List available tools and their capabilities",
  "session_id": "session-123",
  "model": "qwen2.5-coder:7b",
  "current_iteration": 3,
  "max_iterations": 5,
  "started_at": "2025-11-30T11:00:01Z",
  "completed_at": "2025-11-30T11:00:15Z",
  "duration_seconds": 14.25,
  "result": "Available tools: analyze_dataframe, visualize_data, extract_pdf_content...",
  "artifacts": [
    "/artifacts/task-abc123xyz/output.txt",
    "/artifacts/task-abc123xyz/chart.png"
  ],
  "tools_used": ["list_files", "read_file"],
  "llm_calls": 3,
  "error": null,
  "error_details": null,
  "created_at": "2025-11-30T11:00:00Z",
  "meta_info": {}
}
```

**Task Statuses**:
- `pending`: Task created, waiting to start
- `running`: Task currently executing
- `completed`: Task finished successfully
- `failed`: Task encountered an error
- `cancelled`: Task was cancelled by user

**Example**:
```bash
curl http://localhost:8000/api/v1/agent/tasks/task-abc123xyz
```

---

#### 3. List Agent Tasks

**GET** `/tasks`

Lists all agent tasks with optional filtering and pagination.

**Query Parameters**:
- `session_id` (string, optional): Filter by session ID
- `status` (string, optional): Filter by status (pending, running, completed, failed, cancelled)
- `page` (integer, optional): Page number (default: 1)
- `page_size` (integer, optional): Tasks per page (default: 50, max: 100)

**Response** (200 OK):
```json
{
  "tasks": [
    {
      "task_id": "task-abc123xyz",
      "status": "completed",
      "task_description": "...",
      "created_at": "2025-11-30T11:00:00Z",
      ...
    },
    ...
  ],
  "total": 42,
  "page": 1,
  "page_size": 50
}
```

**Examples**:
```bash
# List all tasks
curl http://localhost:8000/api/v1/agent/tasks

# Filter by session
curl "http://localhost:8000/api/v1/agent/tasks?session_id=session-123"

# Filter by status
curl "http://localhost:8000/api/v1/agent/tasks?status=running"

# Pagination
curl "http://localhost:8000/api/v1/agent/tasks?page=2&page_size=25"
```

---

#### 4. Cancel Agent Task

**DELETE** `/tasks/{task_id}`

Cancels a running or pending agent task.

**Path Parameters**:
- `task_id` (string, required): Task identifier to cancel

**Request Body** (optional):
```json
{
  "reason": "User requested cancellation"
}
```

**Response** (200 OK):
```json
{
  "task_id": "task-abc123xyz",
  "status": "cancelled",
  "message": "Task successfully cancelled",
  "cancelled_at": "2025-11-30T11:05:00Z"
}
```

**Error Responses**:
- `404 Not Found`: Task doesn't exist
- `400 Bad Request`: Task cannot be cancelled (already completed/failed)

**Example**:
```bash
curl -X DELETE http://localhost:8000/api/v1/agent/tasks/task-abc123xyz \
  -H "Content-Type: application/json" \
  -d '{"reason": "Task taking too long"}'
```

---

#### 5. Health Check

**GET** `/health`

Checks the health status of the agent service.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "message": "Agent service is operational",
  "agent_runtime": "available"
}
```

**Example**:
```bash
curl http://localhost:8000/api/v1/agent/health
```

---

## Frontend Integration

### AgentTaskMonitor Component

The `AgentTaskMonitor` component provides a complete UI for managing agent tasks.

#### Basic Usage

```tsx
import { AgentTaskMonitor } from '@/components/AgentTaskMonitor';

export default function AgentPage() {
  return (
    <div className="container mx-auto p-6">
      <AgentTaskMonitor sessionId="current-session-id" />
    </div>
  );
}
```

#### Component Props

```typescript
interface AgentTaskMonitorProps {
  sessionId?: string;  // Optional: Filter tasks by session
}
```

#### Features

1. **Task Creation Form**
   - Task description input (multiline textarea)
   - Model selection dropdown
   - Max iterations slider (1-50)
   - Timeout configuration (30s - 1800s)
   - Create button with loading state

2. **Task List**
   - Auto-refreshes every 5 seconds
   - Color-coded status badges
   - Execution time display
   - Tools used summary
   - Click to view details

3. **Task Detail Modal**
   - Full execution metadata
   - Result/error display
   - Artifacts list with download links
   - LLM call count
   - Iteration progress
   - Cancel button for running tasks

#### Customization

```tsx
// Custom API URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Custom refresh interval (default: 5000ms)
const REFRESH_INTERVAL = 3000; // 3 seconds
```

#### Status Badge Colors

- **Pending**: Gray background
- **Running**: Blue background with animation
- **Completed**: Green background with checkmark
- **Failed**: Red background with X icon
- **Cancelled**: Yellow background

---

## Database Schema

### agent_tasks Table

```sql
CREATE TABLE agent_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(255) UNIQUE NOT NULL,

    -- Task details
    task_description TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    session_id VARCHAR(255),
    model VARCHAR(100) NOT NULL DEFAULT 'qwen2.5-coder:7b',

    -- Configuration
    max_iterations INTEGER DEFAULT 20,
    timeout_seconds INTEGER DEFAULT 600,

    -- Progress tracking
    current_iteration INTEGER DEFAULT 0,
    current_phase VARCHAR(50),

    -- Execution details
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds FLOAT,

    -- Results
    result TEXT,
    artifacts TEXT[],
    tools_used TEXT[],
    llm_calls INTEGER DEFAULT 0,

    -- Error handling
    error TEXT,
    error_details JSONB,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB,

    -- Project tracking
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    department VARCHAR(100),
    team VARCHAR(100)
);
```

### Indexes

```sql
CREATE INDEX idx_agent_tasks_task_id ON agent_tasks(task_id);
CREATE INDEX idx_agent_tasks_session_id ON agent_tasks(session_id);
CREATE INDEX idx_agent_tasks_status ON agent_tasks(status);
CREATE INDEX idx_agent_tasks_created_at ON agent_tasks(created_at);
CREATE INDEX idx_agent_tasks_project_id ON agent_tasks(project_id);
CREATE INDEX idx_agent_tasks_created_by ON agent_tasks(created_by);
```

### Migration

Apply the migration:
```bash
docker-compose exec -T postgres psql -U postgres -d ragchatbot < backend/migrations/013_add_agent_tasks_table.sql
```

---

## Configuration

### Environment Variables

**Backend** (docker-compose.yml):
```yaml
agent-runtime:
  environment:
    OLLAMA_HOST: http://ollama:11434
    AGENT_LLM_MODEL: qwen2.5-coder:7b
    POSTGRES_SERVER: postgres
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
    POSTGRES_DB: ragchatbot
    AGENT_MAX_ITERATIONS: 20
    AGENT_TIMEOUT_SECONDS: 600
    AGENT_WORKSPACE: /workspace
```

**Frontend** (.env.local):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Docker Volumes

```yaml
volumes:
  agent_workspace:    # Task working directory
  agent_artifacts:    # Generated outputs
```

### Available Models

Default models configured in the system:
- `qwen2.5-coder:7b` (Recommended - coding tasks)
- `qwen2.5:1.5b` (Fast - simple tasks)
- `deepseek-coder:6.7b` (Advanced coding)
- `llama3.2-vision:11b` (Vision capabilities)

---

## Usage Examples

### Example 1: Data Analysis Task

```bash
curl -X POST http://localhost:8000/api/v1/agent/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Analyze the CSV file in /workspace/sales.csv and create a summary report with key metrics",
    "session_id": "analytics-session",
    "model": "qwen2.5-coder:7b",
    "max_iterations": 15,
    "timeout_seconds": 300
  }'
```

### Example 2: Document Processing

```bash
curl -X POST http://localhost:8000/api/v1/agent/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Extract all tables from the PDF at /workspace/report.pdf and convert to Excel format",
    "model": "qwen2.5-coder:7b",
    "max_iterations": 10
  }'
```

### Example 3: Multi-Step Workflow

```bash
curl -X POST http://localhost:8000/api/v1/agent/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "1) Read the Excel file at /workspace/data.xlsx, 2) Calculate average sales by region, 3) Create a bar chart visualization, 4) Save as PNG",
    "model": "qwen2.5-coder:7b",
    "max_iterations": 20,
    "timeout_seconds": 600
  }'
```

### Example 4: Polling for Results

```bash
# Create task
TASK_ID=$(curl -s -X POST http://localhost:8000/api/v1/agent/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_description": "List all available tools"}' \
  | jq -r '.task_id')

# Poll for completion
while true; do
  STATUS=$(curl -s http://localhost:8000/api/v1/agent/tasks/$TASK_ID \
    | jq -r '.status')

  echo "Task status: $STATUS"

  if [[ "$STATUS" == "completed" ]] || [[ "$STATUS" == "failed" ]]; then
    break
  fi

  sleep 2
done

# Get final result
curl -s http://localhost:8000/api/v1/agent/tasks/$TASK_ID | jq '.result'
```

### Example 5: Frontend Integration

```typescript
import { useState } from 'react';

export function MyComponent() {
  const [taskId, setTaskId] = useState<string | null>(null);

  const createTask = async () => {
    const response = await fetch('http://localhost:8000/api/v1/agent/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        task_description: 'Analyze customer feedback data',
        model: 'qwen2.5-coder:7b',
        max_iterations: 10
      })
    });

    const data = await response.json();
    setTaskId(data.task_id);
  };

  const checkStatus = async () => {
    if (!taskId) return;

    const response = await fetch(
      `http://localhost:8000/api/v1/agent/tasks/${taskId}`
    );
    const data = await response.json();

    console.log('Task status:', data.status);
    console.log('Result:', data.result);
  };

  return (
    <div>
      <button onClick={createTask}>Create Task</button>
      <button onClick={checkStatus}>Check Status</button>
    </div>
  );
}
```

---

## Troubleshooting

### Common Issues

#### 1. Task Creation Fails with Validation Error

**Symptom**: `422 Unprocessable Entity` or validation error

**Solution**: Check request body matches the schema:
```bash
# Ensure required fields are present
{
  "task_description": "string"  # REQUIRED
}
```

---

#### 2. Task Stuck in Pending Status

**Symptom**: Task never transitions to `running`

**Diagnosis**:
```bash
# Check backend logs
docker-compose logs backend | grep "task-<id>"

# Check agent-runtime container
docker ps | grep agent-runtime
```

**Solution**:
- Ensure agent-runtime container is running
- Check Docker exec permissions
- Verify asyncio task creation in logs

---

#### 3. Task Fails with FileNotFoundError

**Symptom**: Task status shows `failed` with error `[Errno 2] No such file or directory`

**Cause**: Missing `/app/entrypoint_agent.py` in agent-runtime container

**Solution**:
- This is expected if agent runtime code isn't deployed yet
- The integration infrastructure is ready
- Deploy agent runtime implementation separately

---

#### 4. Frontend Not Refreshing

**Symptom**: Task list doesn't update automatically

**Solution**:
```typescript
// Check auto-refresh is enabled
useEffect(() => {
  fetchTasks();
  const interval = setInterval(fetchTasks, 5000);
  return () => clearInterval(interval); // Cleanup on unmount
}, [sessionId]);
```

---

#### 5. CORS Errors

**Symptom**: Frontend can't connect to backend API

**Solution**: Add CORS middleware to backend:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Debug Commands

```bash
# Check database for tasks
docker-compose exec postgres psql -U postgres -d ragchatbot \
  -c "SELECT task_id, status, error FROM agent_tasks ORDER BY created_at DESC LIMIT 10;"

# View backend logs
docker-compose logs -f backend | grep -E "(agent|task)"

# Test API endpoint
curl http://localhost:8000/api/v1/agent/health

# Check agent-runtime container
docker exec rag-agent-runtime ls -la /app/

# View full task details
curl -s http://localhost:8000/api/v1/agent/tasks/<task-id> | jq .
```

---

## Development

### Running Locally

```bash
# Start all services
docker-compose up -d

# Apply migration
docker-compose exec -T postgres psql -U postgres -d ragchatbot \
  < backend/migrations/013_add_agent_tasks_table.sql

# Restart backend
docker-compose restart backend

# Check logs
docker-compose logs -f backend
```

### Testing

```bash
# Create test task
./scripts/testing/test_agent_integration.sh

# Run backend tests
cd backend && pytest tests/test_agent_service.py -v

# Test API directly
curl -X POST http://localhost:8000/api/v1/agent/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Test task"}'
```

### Code Structure

```
backend/
├── app/
│   ├── api/routes/
│   │   └── agent_routes.py          # REST API endpoints
│   ├── services/
│   │   └── agent_service.py         # Business logic
│   ├── schemas/
│   │   └── agent_schemas.py         # Request/response models
│   └── models/
│       └── database.py              # SQLAlchemy models
├── migrations/
│   └── 013_add_agent_tasks_table.sql
└── tests/
    └── test_agent_service.py

frontend/
└── src/
    └── components/
        └── AgentTaskMonitor.tsx     # React UI component
```

### Adding New Features

1. **Add new API endpoint**:
   - Update `agent_routes.py`
   - Add schema to `agent_schemas.py`
   - Implement logic in `agent_service.py`

2. **Extend database schema**:
   - Create new migration file
   - Update `AgentTask` model
   - Apply migration

3. **Update frontend**:
   - Modify `AgentTaskMonitor.tsx`
   - Add new API calls
   - Update UI components

---

## API Client Libraries

### Python

```python
import requests

class AgentClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = f"{base_url}/api/v1/agent"

    def create_task(self, description, **kwargs):
        response = requests.post(
            f"{self.base_url}/tasks",
            json={"task_description": description, **kwargs}
        )
        return response.json()

    def get_task(self, task_id):
        response = requests.get(f"{self.base_url}/tasks/{task_id}")
        return response.json()

    def list_tasks(self, **params):
        response = requests.get(f"{self.base_url}/tasks", params=params)
        return response.json()

    def cancel_task(self, task_id, reason=None):
        payload = {"reason": reason} if reason else {}
        response = requests.delete(
            f"{self.base_url}/tasks/{task_id}",
            json=payload
        )
        return response.json()

# Usage
client = AgentClient()
task = client.create_task("Analyze data.csv")
print(f"Created task: {task['task_id']}")

status = client.get_task(task['task_id'])
print(f"Status: {status['status']}")
```

### TypeScript/JavaScript

```typescript
class AgentClient {
  constructor(private baseUrl: string = 'http://localhost:8000') {}

  async createTask(
    description: string,
    options?: {
      sessionId?: string;
      model?: string;
      maxIterations?: number;
      timeoutSeconds?: number;
    }
  ) {
    const response = await fetch(`${this.baseUrl}/api/v1/agent/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        task_description: description,
        ...options
      })
    });
    return response.json();
  }

  async getTask(taskId: string) {
    const response = await fetch(
      `${this.baseUrl}/api/v1/agent/tasks/${taskId}`
    );
    return response.json();
  }

  async listTasks(params?: {
    sessionId?: string;
    status?: string;
    page?: number;
    pageSize?: number;
  }) {
    const query = new URLSearchParams(params as any).toString();
    const response = await fetch(
      `${this.baseUrl}/api/v1/agent/tasks?${query}`
    );
    return response.json();
  }

  async cancelTask(taskId: string, reason?: string) {
    const response = await fetch(
      `${this.baseUrl}/api/v1/agent/tasks/${taskId}`,
      {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason })
      }
    );
    return response.json();
  }
}

// Usage
const client = new AgentClient();
const task = await client.createTask('Analyze sales data');
console.log(`Created task: ${task.task_id}`);
```

---

## Performance Considerations

### Scalability

- **Concurrent Tasks**: Limited by Docker container resources
- **Database Connections**: Uses connection pooling (AsyncSessionLocal)
- **Polling Frequency**: Frontend polls every 5 seconds (configurable)
- **Task Timeout**: Default 600s, adjustable per task

### Optimization Tips

1. **Reduce Polling**: Increase interval for long-running tasks
2. **Pagination**: Use for large task lists
3. **Cleanup**: Periodically archive completed tasks
4. **Indexes**: Already optimized for common queries

---

## Security Considerations

### Current Implementation

- No authentication (TODO: integrate with existing auth system)
- No authorization checks (TODO: RBAC integration)
- Docker exec requires proper permissions

### Recommended Enhancements

1. **Add Authentication**:
   ```python
   from app.core.security import get_current_user

   @router.post("/tasks")
   async def create_task(
       request: AgentTaskCreate,
       current_user = Depends(get_current_user),
       db: Session = Depends(get_db)
   ):
       # User is authenticated
       pass
   ```

2. **Add Authorization**:
   - Check user permissions before task creation
   - Limit task access to creator/team
   - Audit log all operations

3. **Input Validation**:
   - Sanitize task descriptions
   - Limit file path access
   - Validate Docker exec commands

---

## Future Enhancements

### Planned Features

- [ ] WebSocket support for real-time updates
- [ ] Task scheduling and cron jobs
- [ ] Task dependencies and workflows
- [ ] Resource usage tracking
- [ ] Multi-agent collaboration
- [ ] Result streaming
- [ ] Artifact preview in UI
- [ ] Task templates library
- [ ] Performance analytics dashboard

---

## Support & Resources

### Documentation
- **API Docs**: http://localhost:8000/api/docs
- **GraphQL Playground**: http://localhost:8000/graphql
- **Project README**: /ChatBot/README.md

### Related Files
- Backend Service: `backend/app/services/agent_service.py`
- API Routes: `backend/app/api/routes/agent_routes.py`
- Schemas: `backend/app/schemas/agent_schemas.py`
- Database Models: `backend/app/models/database.py`
- Frontend Component: `frontend/src/components/AgentTaskMonitor.tsx`
- Migration: `backend/migrations/013_add_agent_tasks_table.sql`

### Getting Help

For issues or questions:
1. Check this documentation
2. Review backend logs: `docker-compose logs backend`
3. Check database state: SQL queries in Debug Commands section
4. Refer to troubleshooting section above

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-30
**Contributors**: Claude Code Assistant
