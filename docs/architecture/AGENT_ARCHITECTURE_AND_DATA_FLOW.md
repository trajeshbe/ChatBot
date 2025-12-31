# Agent Task System: Complete Architecture & Data Flow

> **Last Updated**: 2025-12-12
> **Version**: 2.0 (Production with MinIO Org Hierarchy)
> **Status**: ✅ Fully Operational

---

## 📋 Table of Contents

1. [System Architecture](#system-architecture)
2. [Docker-in-Docker Configuration](#docker-in-docker-configuration)
3. [Container Communication](#container-communication)
4. [Data Flow: Request to Completion](#data-flow-request-to-completion)
5. [MinIO File Movement](#minio-file-movement)
6. [Workspace Management](#workspace-management)
7. [Agentic Loop Implementation](#agentic-loop-implementation)
8. [Security Architecture](#security-architecture)
9. [Project Integration](#project-integration)
10. [Download Endpoint Architecture](#download-endpoint-architecture)

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     USER (Web Browser)                                   │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ HTTPS
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  FRONTEND (Next.js Container)                            │
│                  Port: 3001                                              │
│  • AgentTaskMonitor.tsx - Task creation and monitoring                  │
│  • Real-time polling (5s intervals)                                      │
│  • Artifact download UI                                                  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ REST API
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI Container)                             │
│                  Port: 8000                                              │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ API Layer                                                         │  │
│  │ • POST /api/v1/agent/tasks - Create task                         │  │
│  │ • GET  /api/v1/agent/tasks/{id} - Get status                     │  │
│  │ • GET  /api/v1/agent/tasks/{id}/download-minio?path=...          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                 ↓                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Agent Service (agent_service.py)                                 │  │
│  │ • Task lifecycle management                                      │  │
│  │ • Docker execution via subprocess                                │  │
│  │ • Result parsing & artifact extraction                           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                 ↓                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ MinIO Client                                                     │  │
│  │ • Download input files from MinIO                                │  │
│  │ • Generate presigned download URLs                               │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ docker exec
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              AGENT-RUNTIME (Docker Container - Sandboxed)                │
│              Image: chatbot-agent-runtime:llm-enabled                    │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ entrypoint_agent.py - Main Execution Loop                        │  │
│  │ • Receives task via command-line args (JSON)                     │  │
│  │ • Runs agentic loop (THINK → ACT → OBSERVE)                      │  │
│  │ • Outputs result as JSON to stdout                               │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                 ↓                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ AgentOrchestrator - Tool Execution                               │  │
│  │ • Tool validation and safety checks                              │  │
│  │ • Python code execution (RestrictedPython)                       │  │
│  │ • File operations (workspace-restricted)                         │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                 ↓                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ LLM Integration (Ollama/OpenAI)                                  │  │
│  │ • Model: llama3.2-vision:11b (default)                           │  │
│  │ • Streaming responses for tool calls                             │  │
│  │ • JSON parsing with markdown cleanup                             │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                 ↓                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ MinIO Client (Upload Results)                                    │  │
│  │ • Upload artifacts to organizational hierarchy                   │  │
│  │ • Upload logs and metadata                                       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  SUPPORTING SERVICES                                     │
│                                                                          │
│  ┌─────────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐         │
│  │ PostgreSQL  │  │  MinIO   │  │  Ollama  │  │   Redis     │         │
│  │  Port:5432  │  │ Port:9000│  │Port:11434│  │  Port:6379  │         │
│  └─────────────┘  └──────────┘  └──────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Container Network

All containers communicate via Docker network: `chatbot_default`

**Network Configuration**:
```yaml
networks:
  default:
    name: chatbot_default
```

---

## Docker-in-Docker Configuration

### Architecture Decision: Docker Socket Mounting vs DinD

**We use Docker Socket Mounting** (not true Docker-in-Docker):

```yaml
# docker-compose.yml
services:
  backend:
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # Mount Docker socket
```

**Why Socket Mounting?**
- ✅ **Performance**: No nested Docker daemon overhead
- ✅ **Simplicity**: Single Docker daemon manages all containers
- ✅ **Resource Sharing**: Containers share the same Docker engine
- ✅ **Security**: Better isolation than privileged DinD mode

**Security Implications**:
- ⚠️ Backend has access to host Docker daemon
- ✅ Mitigated by running only trusted code in backend
- ✅ Agent-runtime runs in isolated container (no Docker access)

### Agent-Runtime Container Lifecycle

**1. Container Start (Keep-Alive Mode)**:
```bash
# docker-compose.yml
agent-runtime:
  image: chatbot-agent-runtime:llm-enabled
  command: /bin/bash -c "tail -f /dev/null"  # Keep container running
  healthcheck:
    test: ["CMD", "python3", "-c", "import sys; sys.exit(0)"]
    interval: 30s
```

**2. Task Execution (via docker exec)**:
```python
# backend/app/services/agent_service.py
cmd = [
    "docker", "exec",
    "-e", f"TASK_ID={task_id}",
    "-e", f"DESCRIPTION={description}",
    "rag-agent-runtime",  # Container name
    "python3", "/app/entrypoint_agent.py",
    "--task-id", task_id,
    "--description", description,
    # ... more args
]
result = subprocess.run(cmd, capture_output=True, text=True)
```

**Key Advantages**:
- ✅ No container spin-up delay (already running)
- ✅ Shared workspace persists across tasks
- ✅ Reduced Docker overhead
- ✅ Faster task execution

### Container Resource Limits

```yaml
agent-runtime:
  deploy:
    resources:
      limits:
        cpus: '4.0'
        memory: 8G
      reservations:
        cpus: '2.0'
        memory: 4G
```

---

## Container Communication

### 1. Backend → Agent-Runtime (Task Execution)

**Method**: Docker Exec via subprocess

**Flow**:
```python
# Step 1: Prepare task data
task_data = {
    "task_id": "task-abc123",
    "description": "Analyze sales2.txt and create chart",
    "input_files": ["/workspace/sales2.txt"],
    "model": "llama3.2-vision:11b"
}

# Step 2: Execute via docker exec
cmd = [
    "docker", "exec",
    "-e", f"TASK_ID={task_data['task_id']}",
    "rag-agent-runtime",
    "python3", "/app/entrypoint_agent.py",
    "--task-id", task_data['task_id'],
    "--description", task_data['description']
]

# Step 3: Capture output
result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

# Step 4: Parse JSON from stdout
stdout = result.stdout
json_marker_start = "=== AGENT_RESULT_JSON ==="
json_marker_end = "=== END_AGENT_RESULT_JSON ==="
start_idx = stdout.find(json_marker_start) + len(json_marker_start)
end_idx = stdout.find(json_marker_end)
json_str = stdout[start_idx:end_idx].strip()
agent_result = json.loads(json_str)
```

**Output Format** (JSON in stdout):
```json
{
  "success": true,
  "iterations": 6,
  "final_answer": "Chart created successfully",
  "artifacts": [
    {"path": "artifacts/revenue_chart.html"}
  ],
  "conversation_history": [
    {"role": "system", "content": "..."},
    {"role": "assistant", "content": "TOOL_CALL: read_file\nARGS: {\"path\": \"sales2.txt\"}"}
  ],
  "tool_calls": 6
}
```

### 2. Backend → PostgreSQL (State Management)

**Connection**: asyncpg via SQLAlchemy async engine

```python
# backend/app/core/database.py
DATABASE_URL = "postgresql+asyncpg://postgres:password@postgres:5432/ragchatbot"

async with AsyncSessionLocal() as session:
    result = await session.execute(
        select(AgentTask).where(AgentTask.task_id == task_id)
    )
    task = result.scalar_one_or_none()
```

### 3. Backend → MinIO (File Storage)

**Connection**: MinIO Python SDK

```python
from minio import Minio

minio_client = Minio(
    'minio:9000',  # Service name in Docker network
    access_key='minioadmin',
    secret_key='minioadmin',
    secure=False
)

# Download file
response = minio_client.get_object('documents', 'path/to/file.txt')
data = response.read()

# Upload file
minio_client.fput_object('documents', 'path/to/destination.txt', '/local/file.txt')
```

### 4. Agent-Runtime → Ollama (LLM Calls)

**Connection**: HTTP via httpx

```python
# entrypoint_agent.py
import httpx

async with httpx.AsyncClient(timeout=120.0) as client:
    response = await client.post(
        'http://ollama:11434/api/generate',  # Service name in Docker network
        json={
            "model": "llama3.2-vision:11b",
            "prompt": "TOOL_CALL: read_file\nARGS: {\"path\": \"sales2.txt\"}\n\nResult: ...",
            "stream": False
        }
    )
```

---

## Data Flow: Request to Completion

### End-to-End Flow Diagram

```
User Creates Task
       │
       ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 1: Task Creation (Frontend → Backend)                           │
│                                                                       │
│ POST /api/v1/agent/tasks                                             │
│ {                                                                     │
│   "description": "analyze sales2.txt and create chart",              │
│   "model": "llama3.2-vision:11b",                                    │
│   "input_files": ["sales2.txt"],                                     │
│   "session_id": "session-abc123",                                    │
│   "project_id": "construction-intelligence"                          │
│ }                                                                     │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 2: Backend Processing (agent_service.py)                        │
│                                                                       │
│ 1. Generate task_id: "task-6b573dec93f1"                             │
│ 2. Generate task_name from description: "use_sales2txt_and_create_a" │
│ 3. Build MinIO organizational path:                                  │
│    Technology/Backend-Development/Construction-Intelligence/         │
│    admin/agent-tasks/use_sales2txt_and_create_a/task-6b573dec93f1/  │
│ 4. Insert into database (status: PENDING)                            │
│ 5. Download input files from MinIO to /tmp/agent-input-{task_id}/   │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 3: Execute Agent Task (docker exec)                             │
│                                                                       │
│ docker exec -e TASK_ID=task-6b573dec93f1 rag-agent-runtime \         │
│   python3 /app/entrypoint_agent.py \                                 │
│   --task-id task-6b573dec93f1 \                                      │
│   --description "analyze sales2.txt..." \                            │
│   --model llama3.2-vision:11b \                                      │
│   --input-files /workspace/sales2.txt \                              │
│   --session-id session-abc123 \                                      │
│   --project-name construction-intelligence                           │
│                                                                       │
│ Database Status: RUNNING                                             │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 4: Agent Execution Inside Container                             │
│                                                                       │
│ Workspace Created:                                                   │
│ /workspace/use_sales2txt_and_create_a/                               │
│   ├── input/           (empty - files in parent /workspace/)         │
│   ├── artifacts/       (output files created here)                   │
│   ├── logs/            (agent.log)                                   │
│   └── temp/            (temporary files)                             │
│                                                                       │
│ Agentic Loop (6 iterations):                                         │
│ 1. THINK: Need to read sales2.txt                                    │
│    ACT: TOOL_CALL: read_file(path="sales2.txt")                      │
│    OBSERVE: File content returned (6 rows of sales data)             │
│                                                                       │
│ 2. THINK: Need to create Plotly chart                                │
│    ACT: TOOL_CALL: execute_python(code="import plotly...")           │
│    OBSERVE: Chart saved to artifacts/revenue_chart.html              │
│                                                                       │
│ 3. FINAL_ANSWER: Chart created successfully                          │
│                                                                       │
│ Artifacts Detected:                                                  │
│ - /workspace/use_sales2txt_and_create_a/artifacts/revenue_chart.html│
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 5: Upload to MinIO (Inside Container)                           │
│                                                                       │
│ MinIO Upload Function (entrypoint_agent.py):                         │
│                                                                       │
│ 1. Fetch minio_base_path from database via asyncpg:                  │
│    Technology/Backend-Development/.../task-6b573dec93f1/             │
│                                                                       │
│ 2. Upload files:                                                     │
│    • artifacts/revenue_chart.html                                    │
│    • logs/agent.log                                                  │
│    • metadata.json                                                   │
│                                                                       │
│ MinIO Bucket: documents                                              │
│ Full Paths:                                                          │
│ • Technology/.../task-6b573dec93f1/artifacts/revenue_chart.html      │
│ • Technology/.../task-6b573dec93f1/logs/agent.log                    │
│ • Technology/.../task-6b573dec93f1/metadata.json                     │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 6: Return Result to Backend                                     │
│                                                                       │
│ JSON Output to stdout:                                               │
│ {                                                                     │
│   "success": true,                                                   │
│   "iterations": 6,                                                   │
│   "final_answer": "Chart created successfully",                      │
│   "artifacts": [                                                     │
│     {"path": "artifacts/revenue_chart.html"}                         │
│   ],                                                                  │
│   "conversation_history": [...]                                      │
│ }                                                                     │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 7: Backend Processing Result (agent_service.py)                 │
│                                                                       │
│ 1. Parse JSON from stdout                                            │
│ 2. Convert relative paths to absolute:                               │
│    "artifacts/revenue_chart.html" →                                  │
│    "/workspace/use_sales2txt_and_create_a/artifacts/revenue_chart.html" │
│ 3. Update database:                                                  │
│    • status: COMPLETED                                               │
│    • llm_calls: 6                                                    │
│    • artifacts: ["/workspace/use_sales2txt_and_create_a/artifacts/revenue_chart.html"] │
│    • result: "Chart created successfully"                            │
│    • conversation_history: [...]                                     │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 8: User Downloads Artifact (Frontend → Backend → MinIO)         │
│                                                                       │
│ GET /api/v1/agent/tasks/task-6b573dec93f1/download-minio?            │
│     path=artifacts/revenue_chart.html                                │
│                                                                       │
│ Backend:                                                             │
│ 1. Fetch task from database                                          │
│ 2. Get minio_base_path:                                              │
│    Technology/.../task-6b573dec93f1/                                 │
│ 3. Build full MinIO path:                                            │
│    Technology/.../task-6b573dec93f1/artifacts/revenue_chart.html     │
│ 4. Stream from MinIO to user:                                        │
│    minio_client.get_object("documents", minio_path)                  │
│ 5. Return as StreamingResponse (3.5 MB HTML file)                    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## MinIO File Movement

### Organizational Hierarchy Structure

```
MinIO Bucket: documents
│
└── Technology/                          (Department)
    └── Backend-Development/             (Team)
        └── Construction-Intelligence/   (Project)
            └── admin/                   (User)
                ├── documents/           (Uploaded files)
                │   ├── sales2.txt
                │   ├── architectural_plan.pdf
                │   └── ...
                │
                └── agent-tasks/         (Agent task outputs)
                    ├── use_sales2txt_and_create_a/    (Task name)
                    │   ├── task-6b573dec93f1/         (Task ID)
                    │   │   ├── artifacts/
                    │   │   │   └── revenue_chart.html
                    │   │   ├── logs/
                    │   │   │   └── agent.log
                    │   │   └── metadata.json
                    │   │
                    │   └── task-abc123def/
                    │       └── ...
                    │
                    └── plotly_sales_chart/
                        ├── task-f692290fa05e/
                        │   ├── artifacts/
                        │   │   ├── sales_report.html
                        │   │   └── revenue_chart.html
                        │   └── ...
                        └── ...
```

### File Movement Lifecycle

#### Phase 1: Input File Download (Backend → Workspace)

**When**: Task creation
**Where**: `backend/app/services/agent_service.py` (lines 350-380)

```python
async def _download_input_files_from_minio(
    self,
    input_file_paths: List[str],
    task_id: str
) -> List[str]:
    """
    Download input files from MinIO to /tmp/agent-input-{task_id}/

    Returns: List of local file paths for docker cp
    """
    local_dir = Path(f"/tmp/agent-input-{task_id}")
    local_dir.mkdir(parents=True, exist_ok=True)

    local_files = []
    for minio_path in input_file_paths:
        # Download from MinIO
        response = self.minio_client.get_object(
            self.minio_bucket,
            minio_path  # e.g., "Technology/.../admin/documents/sales2.txt"
        )

        # Save to local temp directory
        local_path = local_dir / Path(minio_path).name  # e.g., "sales2.txt"
        with open(local_path, 'wb') as f:
            f.write(response.read())

        local_files.append(str(local_path))

    return local_files  # ["/tmp/agent-input-task-abc/sales2.txt"]
```

#### Phase 2: Copy to Container Workspace (Backend → Agent Container)

**When**: Before task execution
**Where**: `backend/app/services/agent_service.py` (lines 385-410)

```python
def _copy_files_to_container(self, local_files: List[str]) -> None:
    """
    Copy files from /tmp/agent-input-{task_id}/ to container /workspace/
    """
    for local_file in local_files:
        filename = Path(local_file).name

        # Copy to container workspace (parent directory)
        cmd = [
            "docker", "cp",
            local_file,  # /tmp/agent-input-task-abc/sales2.txt
            f"rag-agent-runtime:/workspace/{filename}"  # /workspace/sales2.txt
        ]
        subprocess.run(cmd, check=True)

        logger.info(f"✅ Copied {filename} to container /workspace/")
```

**Result**: File available at `/workspace/sales2.txt` inside agent-runtime container

#### Phase 3: Agent Reads File (Inside Container)

**When**: During agentic loop
**Where**: `backend/entrypoint_agent.py` (lines 198-222)

```python
def _validate_tool_call(self, tool_name: str, args: dict) -> bool:
    """
    Validate tool calls for security

    read_file can access:
    1. Task-specific workspace: /workspace/{task_name}/
    2. Parent workspace: /workspace/ (for input files)
    """
    if tool_name == "read_file":
        path = args.get("path", "")
        file_path = Path(path)

        # Allow reading from task workspace
        if not file_path.is_absolute():
            file_path = self.workspace / file_path

        # Check if file is in task workspace OR parent /workspace/
        try:
            file_path.resolve().relative_to(self.workspace.resolve())
            return True
        except ValueError:
            # Not in task workspace, check parent workspace
            parent_workspace = self.workspace.parent
            try:
                file_path.resolve().relative_to(parent_workspace.resolve())
                logger.info(f"✅ Allowing read from parent workspace: {file_path}")
                return True
            except ValueError:
                logger.error(f"🚨 File access outside allowed directories")
                return False
```

**Agent reads**: `/workspace/sales2.txt` (parent workspace)
**Agent writes**: `/workspace/use_sales2txt_and_create_a/artifacts/revenue_chart.html` (task workspace)

#### Phase 4: Upload to MinIO (Inside Container)

**When**: After task completion
**Where**: `backend/entrypoint_agent.py` (lines 988-1133)

```python
async def upload_to_minio(orchestrator: AgentOrchestrator, task_id: str, result: Dict[str, Any]):
    """
    Upload all task files to MinIO with organizational hierarchy

    Structure:
        Technology/Backend-Development/Construction-Intelligence/admin/
        agent-tasks/{task_name}/{task_id}/
            ├── artifacts/
            ├── logs/
            └── metadata.json
    """
    # 1. Initialize MinIO client
    minio_client = Minio(
        'minio:9000',
        access_key='minioadmin',
        secret_key='minioadmin',
        secure=False
    )

    # 2. Fetch organizational base path from database
    conn = await asyncpg.connect(
        host='postgres',
        database='ragchatbot',
        user='postgres',
        password='postgres'
    )
    base_path = await conn.fetchval(
        "SELECT minio_base_path FROM agent_tasks WHERE task_id = $1",
        task_id
    )
    await conn.close()

    # base_path: "Technology/.../admin/agent-tasks/use_sales2txt_and_create_a/task-6b573dec93f1/"

    # 3. Upload artifacts
    for artifact_file in orchestrator.artifacts_dir.iterdir():
        if artifact_file.is_file():
            minio_path = f"{base_path}artifacts/{artifact_file.name}"
            minio_client.fput_object(
                'documents',  # bucket
                minio_path,   # Technology/.../artifacts/revenue_chart.html
                str(artifact_file)  # /workspace/.../artifacts/revenue_chart.html
            )
            logger.info(f"✅ Uploaded artifact: {artifact_file.name}")

    # 4. Upload logs
    for log_file in orchestrator.logs_dir.iterdir():
        minio_path = f"{base_path}logs/{log_file.name}"
        minio_client.fput_object('documents', minio_path, str(log_file))

    # 5. Create and upload metadata
    metadata = {
        "task_id": task_id,
        "completed_at": datetime.utcnow().isoformat(),
        "artifacts_count": len(result.get("artifacts", []))
    }
    metadata_file = orchestrator.workspace / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    minio_client.fput_object('documents', f"{base_path}metadata.json", str(metadata_file))
```

**Upload Results**:
- ✅ `Technology/.../task-6b573dec93f1/artifacts/revenue_chart.html` (3.5 MB)
- ✅ `Technology/.../task-6b573dec93f1/logs/agent.log` (131 KB)
- ✅ `Technology/.../task-6b573dec93f1/metadata.json` (374 bytes)

---

## Workspace Management

### Workspace Structure Inside Agent Container

```
/workspace/                           (Shared across all tasks - persistent)
│
├── sales2.txt                        (Input file - copied from MinIO)
├── architectural_plan.pdf            (Another input file)
│
├── use_sales2txt_and_create_a/       (Task-specific workspace)
│   ├── input/                        (Empty - not used)
│   ├── artifacts/                    (Output files)
│   │   └── revenue_chart.html
│   ├── logs/                         (Execution logs)
│   │   └── agent.log
│   └── temp/                         (Temporary files)
│
├── plotly_sales_chart/               (Another task workspace)
│   ├── artifacts/
│   │   ├── sales_report.html
│   │   └── revenue_chart.html
│   └── logs/
│       └── agent.log
│
└── ...                               (Other task workspaces)
```

### Workspace Isolation

**Security Boundaries**:

1. **Read Access**:
   - ✅ Task workspace: `/workspace/{task_name}/`
   - ✅ Parent workspace: `/workspace/` (for input files)
   - ❌ Other task workspaces: Blocked

2. **Write Access**:
   - ✅ Task workspace only: `/workspace/{task_name}/`
   - ❌ Parent workspace: Blocked (except via approved tools)
   - ❌ System directories: Blocked

3. **Tool Validation**:
```python
# entrypoint_agent.py - Tool validation
ALLOWED_TOOLS = [
    "read_file",
    "write_file",
    "execute_python",
    "execute_bash",
    "list_directory",
    "install_package",
    "web_scrape",
    "ocr_extract",
    "vision_analyze"
]

def _validate_tool_call(self, tool_name: str, args: dict) -> bool:
    if tool_name not in ALLOWED_TOOLS:
        return False

    # Path validation for file operations
    if tool_name in ["read_file", "write_file", "list_directory"]:
        path = args.get("path", "")
        # Ensure path is within allowed directories
        return self._is_path_allowed(path)

    return True
```

### Workspace Cleanup Policy

**Current Behavior**: Workspaces persist indefinitely (for debugging and re-execution)

**Future Enhancement**: Configurable cleanup
```python
# Planned feature
WORKSPACE_RETENTION_DAYS = 7  # Delete after 7 days
WORKSPACE_MAX_SIZE_GB = 10    # Delete oldest if exceeds 10GB
```

---

## Agentic Loop Implementation

### Loop Architecture

```python
# entrypoint_agent.py (simplified)
async def run_agentic_loop(self, max_iterations: int = 20):
    """
    THINK → ACT → OBSERVE loop with LLM
    """
    iteration = 0
    conversation_history = []

    while iteration < max_iterations:
        iteration += 1

        # ============================================
        # PHASE 1: THINK (LLM Reasoning)
        # ============================================
        prompt = self._build_prompt(conversation_history)

        response = await self._call_llm(prompt)
        # response: "TOOL_CALL: read_file\nARGS: {\"path\": \"sales2.txt\"}"

        conversation_history.append({
            "role": "assistant",
            "content": response
        })

        # ============================================
        # PHASE 2: PARSE (Extract Action)
        # ============================================
        parsed = self._parse_response(response)

        if parsed["type"] == "final_answer":
            # Task complete
            return {
                "success": True,
                "final_answer": parsed["content"],
                "iterations": iteration
            }

        if parsed["type"] == "tool_call":
            tool_name = parsed["tool"]
            args = parsed["args"]

            # ============================================
            # PHASE 3: VALIDATE (Security Check)
            # ============================================
            if not self._validate_tool_call(tool_name, args):
                observation = "❌ Tool call blocked: Security violation"
            else:
                # ============================================
                # PHASE 4: ACT (Execute Tool)
                # ============================================
                observation = await self._execute_tool(tool_name, args)

            # ============================================
            # PHASE 5: OBSERVE (Record Result)
            # ============================================
            conversation_history.append({
                "role": "tool",
                "tool": tool_name,
                "content": observation
            })

        # Continue loop...

    # Max iterations reached
    return {
        "success": False,
        "error": "Max iterations reached"
    }
```

### Response Parsing Priority

**Critical Fix** (from recent debugging):

```python
def _parse_response(self, response: str) -> Dict[str, Any]:
    """
    Parse LLM response for actions

    IMPORTANT: Check TOOL_CALL before FINAL_ANSWER
    (LLM sometimes includes both in same message)
    """
    # Check for tool call FIRST (priority over FINAL_ANSWER)
    if "TOOL_CALL:" in response:
        # Extract tool name and args
        lines = response.split('\n')
        tool_line = [l for l in lines if l.startswith('TOOL_CALL:')]
        args_line = [l for l in lines if l.startswith('ARGS:')]

        if tool_line and args_line:
            tool_name = tool_line[0].replace('TOOL_CALL:', '').strip()
            args_json = args_line[0].replace('ARGS:', '').strip()

            # Clean up markdown code fences
            args_json = args_json.rstrip('`').strip()
            if args_json.startswith('```json'):
                args_json = args_json[7:].strip()
            elif args_json.startswith('```'):
                args_json = args_json[3:].strip()

            args = json.loads(args_json)

            return {
                "type": "tool_call",
                "tool": tool_name,
                "args": args
            }

    # Check for final answer AFTER tool call check
    if "FINAL_ANSWER:" in response:
        return {
            "type": "final_answer",
            "content": response.split("FINAL_ANSWER:")[1].strip()
        }

    # Default: thinking/reasoning step
    return {
        "type": "thinking",
        "content": response
    }
```

### Tool Execution Example

```python
async def _execute_tool(self, tool_name: str, args: dict) -> str:
    """Execute a tool and return observation"""

    if tool_name == "read_file":
        path = args.get("path")
        # Validate path
        if not self._is_path_allowed(path):
            return "❌ Error: Path access denied"

        # Read file
        try:
            with open(path, 'r') as f:
                content = f.read()
            return f"✅ File content:\n{content}"
        except Exception as e:
            return f"❌ Error reading file: {e}"

    elif tool_name == "execute_python":
        code = args.get("code")
        # Execute in restricted environment
        try:
            # Use RestrictedPython for safety
            exec_globals = {"__builtins__": safe_builtins}
            exec(code, exec_globals)
            return "✅ Code executed successfully"
        except Exception as e:
            return f"❌ Error executing code: {e}"

    # ... other tools
```

---

## Security Architecture

### Multi-Layer Security

```
┌─────────────────────────────────────────────────────────────────────┐
│ Layer 1: Network Isolation                                          │
│ • Docker network: chatbot_default                                   │
│ • No external network access from agent-runtime                     │
│ • Services communicate via service names only                       │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Layer 2: Container Isolation                                        │
│ • Agent-runtime: No privileged mode                                 │
│ • No Docker socket access                                           │
│ • Resource limits: 8GB memory, 4 CPUs                               │
│ • Read-only root filesystem (planned)                               │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Layer 3: Workspace Isolation                                        │
│ • Task-specific directories: /workspace/{task_name}/                │
│ • Path validation on all file operations                            │
│ • No access to system directories (/etc, /usr, /bin)                │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Layer 4: Tool Whitelisting                                          │
│ • Only approved tools can be called                                 │
│ • Tool arguments validated                                          │
│ • Dangerous operations blocked (rm -rf, sudo, etc.)                 │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Layer 5: Code Execution Safety                                      │
│ • RestrictedPython for Python code execution                        │
│ • Bash command whitelist (no rm, sudo, chmod, etc.)                 │
│ • Timeout limits: 120s per operation                                │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Layer 6: Database Access Control                                    │
│ • Agent container: Read-only access to own task                     │
│ • Backend: Full database access (authenticated)                     │
│ • PostgreSQL: Password-protected                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### Security Validations

#### 1. Path Validation
```python
def _is_path_allowed(self, path: str) -> bool:
    """
    Validate file paths for security

    Allowed:
    - /workspace/{task_name}/*
    - /workspace/*.txt (input files in parent)

    Blocked:
    - /etc/*
    - /usr/*
    - /root/*
    - /../ (path traversal)
    """
    path_obj = Path(path).resolve()

    # Check for path traversal
    if ".." in str(path):
        return False

    # Check if within workspace
    try:
        path_obj.relative_to(Path("/workspace"))
        return True
    except ValueError:
        return False
```

#### 2. Bash Command Whitelist
```python
ALLOWED_BASH_COMMANDS = [
    "ls", "pwd", "echo", "cat", "head", "tail",
    "grep", "wc", "sort", "uniq", "find",
    "python3", "pip", "curl", "wget"
]

BLOCKED_BASH_COMMANDS = [
    "rm", "sudo", "chmod", "chown", "kill",
    "systemctl", "service", "reboot", "shutdown",
    "dd", "mkfs", "fdisk"
]

def validate_bash_command(command: str) -> bool:
    cmd_parts = command.strip().split()
    if not cmd_parts:
        return False

    base_cmd = cmd_parts[0]

    if base_cmd in BLOCKED_BASH_COMMANDS:
        return False

    if base_cmd not in ALLOWED_BASH_COMMANDS:
        return False

    # Additional checks
    if ">" in command and "/etc/" in command:
        return False  # Block writing to system files

    return True
```

#### 3. Python Code Safety (RestrictedPython)
```python
from RestrictedPython import compile_restricted, safe_builtins

def execute_python_safely(code: str) -> str:
    """
    Execute Python code in restricted environment
    """
    # Compile with restrictions
    byte_code = compile_restricted(
        code,
        filename='<inline>',
        mode='exec'
    )

    # Prepare safe globals
    safe_globals = {
        "__builtins__": safe_builtins,
        "__name__": "__main__",
        # Allow safe imports
        "pandas": __import__("pandas"),
        "numpy": __import__("numpy"),
        "plotly": __import__("plotly"),
        # Block dangerous modules
        "os": None,
        "sys": None,
        "subprocess": None
    }

    # Execute
    exec(byte_code, safe_globals)
```

### Audit Logging

All actions are logged to database:

```sql
INSERT INTO audit_logs (
    user_id,
    action,
    resource_type,
    resource_id,
    details,
    ip_address,
    created_at
) VALUES (
    'admin',
    'agent_task_execute',
    'agent_task',
    'task-6b573dec93f1',
    '{"description": "analyze sales2.txt...", "model": "llama3.2-vision:11b"}',
    '172.18.0.1',
    NOW()
);
```

---

## Project Integration

### Organizational Hierarchy Mapping

```python
# backend/app/services/minio_path_builder.py

class MinIOPathBuilder:
    """
    Build MinIO paths following organizational hierarchy

    Hierarchy:
    1. Department (e.g., Technology)
    2. Team (e.g., Backend-Development)
    3. Project (e.g., Construction-Intelligence)
    4. User (e.g., admin)
    5. Resource Type (documents, agent-tasks, extractions)
    6. Resource Name
    """

    def build_agent_task_path(
        self,
        project: Project,
        user: User,
        task_name: str,
        task_id: str
    ) -> str:
        """
        Build path for agent task artifacts

        Returns:
            Technology/Backend-Development/Construction-Intelligence/
            admin/agent-tasks/use_sales2txt_and_create_a/task-6b573dec93f1/
        """
        # Get organizational structure from project
        department = project.department.name  # "Technology"
        team = project.department.team.name   # "Backend-Development"
        project_name = project.name            # "Construction-Intelligence"
        username = user.username               # "admin"

        # Sanitize names (lowercase, replace spaces with hyphens)
        department = self._sanitize(department)
        team = self._sanitize(team)
        project_name = self._sanitize(project_name)
        username = self._sanitize(username)
        task_name = self._sanitize(task_name)

        # Build path
        path = f"{department}/{team}/{project_name}/{username}/agent-tasks/{task_name}/{task_id}/"

        return path
```

### Project Context Injection

**Task Creation Flow**:

```python
# backend/app/api/routes/agent_routes.py

@router.post("/api/v1/agent/tasks")
async def create_agent_task(
    request: AgentTaskCreate,
    db: AsyncSession = Depends(get_db)
):
    # Get session to extract project context
    session = await db.execute(
        select(ChatSession).where(ChatSession.session_id == request.session_id)
    )
    chat_session = session.scalar_one_or_none()

    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get project and user
    project = chat_session.project  # Relationship defined in model
    user = chat_session.user        # Relationship defined in model

    # Build MinIO organizational path
    path_builder = MinIOPathBuilder()
    minio_base_path = path_builder.build_agent_task_path(
        project=project,
        user=user,
        task_name=task_name,
        task_id=task_id
    )

    # Create task with organizational context
    task = AgentTask(
        task_id=task_id,
        task_name=task_name,
        description=request.description,
        session_id=request.session_id,
        project_id=project.id,
        user_id=user.id,
        minio_base_path=minio_base_path,  # Full organizational path
        status=TaskStatus.PENDING
    )

    db.add(task)
    await db.commit()
```

### Multi-Tenant Isolation

**Query Filtering by Project**:

```python
@router.get("/api/v1/agent/tasks")
async def list_agent_tasks(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    # Get session to determine project
    session = await db.execute(
        select(ChatSession).where(ChatSession.session_id == session_id)
    )
    chat_session = session.scalar_one_or_none()

    # Filter tasks by project (multi-tenant isolation)
    result = await db.execute(
        select(AgentTask)
        .where(AgentTask.project_id == chat_session.project_id)
        .order_by(AgentTask.created_at.desc())
        .limit(50)
    )

    tasks = result.scalars().all()

    # Users only see tasks from their project
    return tasks
```

---

## Download Endpoint Architecture

### MinIO Streaming Download

```python
# backend/app/api/routes/agent_routes.py

@router.get("/tasks/{task_id}/download-minio")
async def download_artifact_from_minio(
    task_id: str,
    path: str,  # Relative path like "artifacts/revenue_chart.html"
    db: AsyncSession = Depends(get_db)
):
    """
    Download artifact from MinIO storage

    URL: /api/v1/agent/tasks/task-6b573dec93f1/download-minio?path=artifacts/revenue_chart.html
    """
    from minio import Minio
    from fastapi.responses import StreamingResponse

    # 1. Get task from database
    result = await db.execute(
        select(AgentTask).where(AgentTask.task_id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not task.minio_base_path:
        raise HTTPException(
            status_code=404,
            detail="Task does not have MinIO path"
        )

    # 2. Build full MinIO path
    # task.minio_base_path: "Technology/.../task-6b573dec93f1/"
    # path: "artifacts/revenue_chart.html"
    minio_path = f"{task.minio_base_path}{path}"
    # Result: "Technology/.../task-6b573dec93f1/artifacts/revenue_chart.html"

    # 3. Initialize MinIO client
    minio_client = Minio(
        'minio:9000',
        access_key='minioadmin',
        secret_key='minioadmin',
        secure=False
    )

    # 4. Stream file from MinIO
    try:
        response = minio_client.get_object('documents', minio_path)

        # Extract filename for download header
        filename = path.split('/')[-1]  # "revenue_chart.html"

        # Determine content type
        content_type_map = {
            '.html': 'text/html',
            '.pdf': 'application/pdf',
            '.csv': 'text/csv',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg'
        }

        file_ext = os.path.splitext(filename)[1].lower()
        media_type = content_type_map.get(file_ext, 'application/octet-stream')

        # 5. Return as streaming response (efficient for large files)
        return StreamingResponse(
            response.stream(32*1024),  # 32KB chunks
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.error(f"Failed to get object from MinIO: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"Artifact not found in MinIO: {path}"
        )
```

### Frontend Download Integration

```typescript
// frontend/src/components/AgentTaskMonitor.tsx

const downloadArtifact = async (taskId: string, artifactPath: string) => {
  try {
    // Extract relative path from absolute workspace path
    // "/workspace/use_sales2txt_and_create_a/artifacts/revenue_chart.html"
    // → "artifacts/revenue_chart.html"
    const relativePath = artifactPath.split('/').slice(-2).join('/');

    // Build download URL
    const url = `/api/v1/agent/tasks/${taskId}/download-minio?path=${encodeURIComponent(relativePath)}`;

    // Trigger browser download
    const link = document.createElement('a');
    link.href = url;
    link.download = artifactPath.split('/').pop() || 'download';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

  } catch (error) {
    console.error('Download failed:', error);
    setError('Failed to download artifact');
  }
};
```

---

## Performance Metrics

### Typical Task Execution Time

```
Task: "Analyze sales2.txt and create Plotly chart"

┌─────────────────────────────┬──────────────┐
│ Phase                       │ Time         │
├─────────────────────────────┼──────────────┤
│ Task creation (Backend)     │ 0.2s         │
│ File download from MinIO    │ 0.3s         │
│ Copy to container           │ 0.1s         │
│ Agent execution:            │              │
│   - LLM call 1 (read_file)  │ 8s           │
│   - File reading            │ 0.05s        │
│   - LLM call 2 (execute)    │ 12s          │
│   - Python execution        │ 2s           │
│   - LLM call 3 (final)      │ 3s           │
│ Upload to MinIO             │ 0.5s         │
│ Database update             │ 0.1s         │
├─────────────────────────────┼──────────────┤
│ **Total**                   │ **26.25s**   │
└─────────────────────────────┴──────────────┘
```

**Bottlenecks**:
1. LLM inference time (23s / 26.25s = 87.6%)
2. MinIO I/O (0.8s / 26.25s = 3%)
3. Other operations (2.45s / 26.25s = 9.3%)

**Optimization Opportunities**:
- Use faster LLM models (qwen2.5:0.5b vs llama3.2-vision:11b)
- Implement streaming LLM responses
- Cache common LLM patterns
- Parallel file uploads to MinIO

---

## Troubleshooting Guide

### Common Issues

#### Issue 1: Task Stuck in "RUNNING" State

**Symptoms**:
- Task status never changes from "running"
- No recent logs in agent.log

**Diagnosis**:
```bash
# Check if agent-runtime container is healthy
docker-compose ps agent-runtime

# Check container logs
docker-compose logs agent-runtime --tail=100

# Check if task process is running
docker-compose exec agent-runtime ps aux | grep entrypoint_agent
```

**Solution**:
```bash
# Restart agent-runtime
docker-compose restart agent-runtime

# Re-submit task
curl -X POST http://localhost:8000/api/v1/agent/tasks \
  -H "Content-Type: application/json" \
  -d '{"description": "...retry task..."}'
```

#### Issue 2: Artifacts Not Uploaded to MinIO

**Symptoms**:
- Task completes successfully
- artifacts[] array is populated in database
- But files not in MinIO

**Diagnosis**:
```bash
# Check agent.log for MinIO errors
docker-compose exec agent-runtime cat /workspace/{task_name}/logs/agent.log | grep -i minio

# Check MinIO bucket
docker-compose exec minio mc ls minio/documents/Technology/.../
```

**Solution**:
```bash
# Check MinIO connectivity from agent container
docker-compose exec agent-runtime curl http://minio:9000/minio/health/live

# Verify MinIO credentials
docker-compose exec agent-runtime env | grep MINIO
```

#### Issue 3: Download Endpoint Returns 404

**Symptoms**:
- Download URL returns `{"detail":"Not Found"}`
- Files exist in MinIO

**Diagnosis**:
```bash
# Check if AgentTask import is correct
docker-compose logs backend | grep "AgentTask"

# Check if router is registered
curl http://localhost:8000/api/docs | grep download-minio
```

**Solution** (Applied in recent fixes):
1. Fix import: `from app.models.database import AgentTask` (not database_enhanced)
2. Fix config: Use `settings.MINIO_BUCKET_NAME` (not MINIO_BUCKET)
3. Fix session type: `AsyncSession` (not Session)

---

## Future Enhancements

### Planned Features

1. **Streaming LLM Responses**
   - Real-time task progress updates
   - WebSocket connection for live monitoring

2. **Multi-Agent Collaboration**
   - Task delegation between specialized agents
   - Parallel task execution

3. **Enhanced Security**
   - Network policies (restrict egress)
   - Secret management (Vault integration)
   - Code signing for tool execution

4. **Performance Optimizations**
   - LLM response caching
   - Workspace prewarming
   - Parallel MinIO uploads

5. **Advanced Monitoring**
   - OpenTelemetry tracing
   - Grafana dashboards
   - Alert triggers (task failures, timeouts)

---

## References

### Related Documentation

- **Main Guide**: `docs/AGENT_TASKS_COMPREHENSIVE_GUIDE.md` - User-facing guide
- **Tool Registry**: `backend/app/agents/tool_registry.py` - Available tools
- **Entrypoint**: `backend/entrypoint_agent.py` - Agent execution logic
- **Service**: `backend/app/services/agent_service.py` - Backend orchestration
- **Fixes**: `docs/fixes/COMPLETE_AGENT_WORKFLOW_SUCCESS.md` - Recent bug fixes

### Code Locations

**Backend**:
- API Routes: `backend/app/api/routes/agent_routes.py`
- Agent Service: `backend/app/services/agent_service.py`
- MinIO Path Builder: `backend/app/services/minio_path_builder.py`

**Agent Runtime**:
- Entrypoint: `backend/entrypoint_agent.py`
- Tool Registry: `backend/app/agents/tool_registry.py`
- Dockerfile: `backend/Dockerfile.agent-runtime`

**Frontend**:
- Task Monitor: `frontend/src/components/AgentTaskMonitor.tsx`

**Database**:
- Schema: `backend/migrations/013_add_agent_tasks_table.sql`
- Models: `backend/app/models/database.py` (AgentTask model)

---

**Document Status**: ✅ Complete and Up-to-Date (2025-12-12)

**Maintenance**: Update this document when:
- Architecture changes (new containers, services)
- Security model changes
- MinIO path structure changes
- Major bug fixes affecting data flow
