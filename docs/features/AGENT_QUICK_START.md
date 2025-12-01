# Agent Integration - Quick Start Guide

**5-Minute Setup** | **Updated**: 2025-11-30

## Prerequisites

- Docker & Docker Compose running
- Backend and agent-runtime containers up
- PostgreSQL database running

## Quick Setup

### 1. Apply Database Migration (One-time)

```bash
cd /mnt/c/AIML/ClaudeCode/chatbot/ChatBot

docker-compose exec -T postgres psql -U postgres -d ragchatbot \
  < backend/migrations/013_add_agent_tasks_table.sql
```

### 2. Restart Backend

```bash
docker-compose restart backend
```

### 3. Verify Services

```bash
# Check agent routes registered
docker-compose logs backend | grep "Agent Task Management"
# Should see: "✓ Agent Task Management API router registered"

# Test health endpoint
curl http://localhost:8000/api/v1/agent/health
```

## Quick Test

### Create a Task

```bash
curl -X POST http://localhost:8000/api/v1/agent/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "List available tools",
    "model": "qwen2.5-coder:7b",
    "max_iterations": 5
  }'
```

**Expected Response**:
```json
{
  "task_id": "task-abc123",
  "status": "pending",
  "message": "Task created and queued for execution",
  "created_at": "2025-11-30T..."
}
```

### Check Task Status

```bash
# Replace with your task_id
curl http://localhost:8000/api/v1/agent/tasks/task-abc123
```

### List All Tasks

```bash
curl http://localhost:8000/api/v1/agent/tasks
```

## Frontend Integration

Add to any page:

```tsx
import { AgentTaskMonitor } from '@/components/AgentTaskMonitor';

export default function MyPage() {
  return <AgentTaskMonitor sessionId="my-session" />;
}
```

## Common Commands

```bash
# View backend logs
docker-compose logs -f backend | grep agent

# Check database
docker-compose exec postgres psql -U postgres -d ragchatbot \
  -c "SELECT task_id, status FROM agent_tasks ORDER BY created_at DESC LIMIT 5;"

# Restart services
docker-compose restart backend agent-runtime
```

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/agent/tasks` | Create task |
| GET | `/api/v1/agent/tasks/{id}` | Get status |
| GET | `/api/v1/agent/tasks` | List tasks |
| DELETE | `/api/v1/agent/tasks/{id}` | Cancel task |
| GET | `/api/v1/agent/health` | Health check |

## Task Statuses

- `pending` → Task queued
- `running` → Currently executing
- `completed` → Finished successfully
- `failed` → Encountered error
- `cancelled` → User cancelled

## Troubleshooting

### Task stuck in pending?
```bash
# Check agent-runtime container
docker ps | grep agent-runtime

# View logs
docker-compose logs agent-runtime
```

### Task fails immediately?
```bash
# Check backend logs
docker-compose logs backend --tail 50 | grep ERROR

# Verify migration applied
docker-compose exec postgres psql -U postgres -d ragchatbot \
  -c "\d agent_tasks"
```

### Frontend not updating?
- Check browser console for errors
- Verify API_URL environment variable
- Ensure auto-refresh is working (5s interval)

## Next Steps

- Read full documentation: `docs/features/AGENT_INTEGRATION_GUIDE.md`
- Explore API: http://localhost:8000/api/docs
- Customize frontend component in `src/components/AgentTaskMonitor.tsx`

---

**Need Help?** Check the full guide or backend logs!
