# Claude Code Integration - Quick Start Checklist

> **Ready to build?** Follow this checklist to get started.

---

## ✅ Pre-Implementation Checklist

### 1. Review Documentation (15 minutes)
- [ ] Read `CLAUDE_CODE_INTEGRATION_SUMMARY.md` (this gives you the big picture)
- [ ] Skim `CLAUDE_CODE_CORRECT_ARCHITECTURE.md` (understand the 3-layer structure)
- [ ] Note: You can skip the other docs for now (reference later)

### 2. Make Decisions (5 minutes)
- [ ] **Option**: Confirm Option 1 (Mini Agent) as starting point ✅
- [ ] **Priority Use Cases**: Check what you need most:
  - [ ] EDA on CSV/Excel files
  - [ ] Vision tasks (image analysis, OCR)
  - [ ] Code generation (Python scripts)
  - [ ] Other: ________________
- [ ] **Timeline**: 2 weeks (MVP) or 3 weeks (polished)?
- [ ] **Budget**: Confirm ~$60/month for 100 complex tasks is acceptable

### 3. Technical Prerequisites (10 minutes)
- [ ] **Docker-in-Docker**: Verify it works
  ```bash
  docker run --rm -v /var/run/docker.sock:/var/run/docker.sock docker:latest docker ps
  ```
  Expected: Should list running containers ✅

- [ ] **Redis**: Confirm accessible from containers
  ```bash
  docker run --rm --network chatbot_default redis:alpine redis-cli -h redis ping
  ```
  Expected: PONG ✅

- [ ] **MinIO**: Verify upload works
  ```bash
  # Test MinIO is running
  curl http://localhost:9000/minio/health/live
  ```
  Expected: HTTP 200 ✅

---

## 🚀 Week 1: Foundation

### Day 1-2: Sandbox Container Setup

**Goal**: Create the base image that runs all 3 layers

#### Step 1: Create Directory Structure
```bash
cd backend
mkdir -p agent_runtime/{orchestration,agentic_loop,execution,communication}
mkdir -p sandbox-runtime
```

#### Step 2: Create Dockerfile
```bash
cat > sandbox-runtime/Dockerfile <<'EOF'
FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ curl git \
    && rm -rf /var/lib/apt/lists/*

# Python packages
RUN pip install --no-cache-dir \
    pandas numpy scipy matplotlib seaborn plotly \
    scikit-learn pillow opencv-python \
    requests beautifulsoup4 \
    redis anthropic python-dotenv

# Agent code
WORKDIR /app
COPY agent_runtime/ /app/agent_runtime/
COPY entrypoint.py /app/entrypoint.py

# Security: non-root user
RUN useradd -m -u 1000 sandbox && \
    mkdir -p /app/workspace && \
    chown -R sandbox:sandbox /app

USER sandbox
WORKDIR /app/workspace

ENTRYPOINT ["python", "/app/entrypoint.py"]
EOF
```

#### Step 3: Build Base Image
```bash
docker build -t chatbot-agent-runtime:latest sandbox-runtime/
```

**Verification**:
```bash
docker run --rm chatbot-agent-runtime:latest --version
# Should show Python version
```

**Checkpoint**: ✅ Base image builds successfully

---

### Day 3-4: Agent Runtime Skeleton

**Goal**: Create empty skeleton for all 3 layers

#### Step 1: Orchestration Layer
```bash
# Create session manager
cat > agent_runtime/orchestration/session_manager.py <<'EOF'
"""Session Manager - Handles workspace and state"""

class SessionManager:
    def __init__(self, task_id: str, session_id: str):
        self.task_id = task_id
        self.session_id = session_id
        self.workspace = "/app/workspace"

    def list_workspace_files(self) -> str:
        """List all files in workspace"""
        # TODO: Implement
        return "No files yet"

    def list_output_files(self) -> list:
        """List generated artifacts"""
        # TODO: Implement
        return []
EOF

# Create tool registry
cat > agent_runtime/orchestration/tool_registry.py <<'EOF'
"""Tool Registry - Available tools for the agent"""

def get_tool_registry():
    """Return tool registry instance"""
    # TODO: Implement
    pass
EOF
```

#### Step 2: Agentic Loop
```bash
cat > agent_runtime/agentic_loop/agent_loop.py <<'EOF'
"""Agentic Loop - THINK → PLAN → ACT → OBSERVE"""

class AgentLoop:
    def __init__(self, session_manager, event_publisher, max_iterations=50):
        self.session_manager = session_manager
        self.event_publisher = event_publisher
        self.max_iterations = max_iterations

    async def run(self, user_query: str):
        """Main agentic loop"""
        # TODO: Implement
        return {"success": False, "error": "Not implemented yet"}
EOF
```

#### Step 3: Execution Layer
```bash
cat > agent_runtime/execution/python_executor.py <<'EOF'
"""Python Executor - Run Python code in sandbox"""

async def execute_python(code: str) -> dict:
    """Execute Python code"""
    # TODO: Implement
    return {"success": False, "error": "Not implemented yet"}
EOF
```

#### Step 4: Entry Point
```bash
cat > backend/entrypoint.py <<'EOF'
"""Container entry point"""

import os
import sys

async def main():
    task_id = os.getenv("TASK_ID")
    user_query = os.getenv("USER_QUERY")

    print(f"🚀 Agent starting for task: {task_id}")
    print(f"📝 Query: {user_query}")

    # TODO: Initialize and run agent
    print("✅ Agent skeleton loaded")
    sys.exit(0)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
EOF
```

**Verification**:
```bash
# Rebuild image
docker build -t chatbot-agent-runtime:latest sandbox-runtime/

# Test entry point
docker run --rm \
    -e TASK_ID=test-123 \
    -e USER_QUERY="Hello world" \
    chatbot-agent-runtime:latest

# Expected output:
# 🚀 Agent starting for task: test-123
# 📝 Query: Hello world
# ✅ Agent skeleton loaded
```

**Checkpoint**: ✅ Container runs and loads skeleton

---

### Day 5: Backend Integration

**Goal**: Create backend service to launch containers

#### Step 1: Create Sandbox Manager
```bash
cat > backend/app/services/agent_sandbox_manager.py <<'EOF'
"""Agent Sandbox Manager - Launches containers"""

import docker
from pathlib import Path

class AgentSandboxManager:
    def __init__(self):
        self.docker_client = docker.from_env()

    async def create_and_run_agent(
        self,
        task_id: str,
        session_id: str,
        query: str
    ):
        """Launch agent in container"""

        # Prepare workspace
        workspace = Path(f"/tmp/agent_workspaces/{task_id}")
        workspace.mkdir(parents=True, exist_ok=True)

        # Environment variables
        env_vars = {
            "TASK_ID": task_id,
            "SESSION_ID": session_id,
            "USER_QUERY": query,
        }

        # Start container
        container = self.docker_client.containers.run(
            "chatbot-agent-runtime:latest",
            environment=env_vars,
            volumes={
                str(workspace): {"bind": "/app/workspace", "mode": "rw"}
            },
            detach=True,
            remove=True
        )

        return {"task_id": task_id, "container_id": container.id}

agent_sandbox_manager = AgentSandboxManager()
EOF
```

#### Step 2: Test from Backend
```bash
cd backend

# Create test script
cat > test_agent_sandbox.py <<'EOF'
import asyncio
from app.services.agent_sandbox_manager import agent_sandbox_manager

async def test():
    result = await agent_sandbox_manager.create_and_run_agent(
        task_id="test-123",
        session_id="session-abc",
        query="Test query"
    )
    print(f"Result: {result}")

asyncio.run(test())
EOF

# Run test
python test_agent_sandbox.py
```

**Expected**: Container starts and completes

**Checkpoint**: ✅ Backend can launch containers

---

## 🚀 Week 2: Core Implementation

### Day 1-3: Implement Agentic Loop

**Tasks**:
- [ ] Implement Claude API integration in agentic loop
- [ ] Add tool registry with 5 tools:
  - [ ] execute_python
  - [ ] read_file
  - [ ] write_file
  - [ ] install_package
  - [ ] run_bash
- [ ] Implement THINK → PLAN → ACT → OBSERVE cycle
- [ ] Add Redis event publishing

**Detailed implementation**: See `CLAUDE_CODE_CORRECT_ARCHITECTURE.md`

---

### Day 4-5: Implement Tools

**Tasks**:
- [ ] Python executor (write to temp file, execute, capture output)
- [ ] File operations (read/write with path validation)
- [ ] Bash executor (with command filtering)
- [ ] Package installer (pip install with validation)
- [ ] Test each tool independently

---

## 🚀 Week 3: Frontend & Polish

### Day 1-2: UI Components

**Tasks**:
- [ ] Add checkbox to ChatInterface: "☑️ Use Claude Code"
- [ ] Create StreamingTerminal component
- [ ] Create AgentResultsViewer component
- [ ] Wire up WebSocket for real-time events

---

### Day 3-4: End-to-End Testing

**Test Cases**:
- [ ] EDA on CSV file
- [ ] Simple code generation
- [ ] Vision task (if prioritized)
- [ ] Error handling
- [ ] Cancellation

---

### Day 5: Documentation & Demo

**Tasks**:
- [ ] User guide
- [ ] Demo video/screenshots
- [ ] Cost tracking setup
- [ ] Monitoring dashboard

---

## ✅ Success Criteria

### MVP Complete When:
- ✅ User can check "Use Claude Code" checkbox
- ✅ Complex tasks trigger agent
- ✅ Streaming terminal shows tool execution
- ✅ Artifacts are downloadable
- ✅ At least 1 use case works end-to-end (EDA recommended)

---

## 🆘 Troubleshooting

### Container Won't Start
```bash
# Check Docker daemon
docker ps

# Check image exists
docker images | grep chatbot-agent-runtime

# View logs
docker logs <container_id>
```

### Docker-in-Docker Not Working
```bash
# Verify socket is mounted
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    docker:latest docker version
```

### Redis Connection Failed
```bash
# Check Redis is running
docker ps | grep redis

# Test connection
docker exec chatbot-redis-1 redis-cli ping
```

---

## 📞 Need Help?

If you get stuck:

1. **Check the docs**:
   - `CLAUDE_CODE_CORRECT_ARCHITECTURE.md` - Architecture details
   - `CLAUDE_CODE_INTEGRATION_IMPLEMENTATION_PLAN.md` - Full implementation

2. **Common issues**:
   - Docker-in-Docker permissions
   - Redis connection from container
   - File path validation

3. **Ask me**: I'm here to help debug! 🚀

---

## 🎯 Next Steps After MVP

### Month 2: Production Hardening
- [ ] Scale testing (50 concurrent tasks)
- [ ] Security audit
- [ ] Cost optimization
- [ ] Error recovery improvements

### Month 3: Advanced Features (Optional)
- [ ] Add Option 2 (Claude Code CLI) for research tasks
- [ ] Multi-language support (not just Python)
- [ ] Advanced tooling (git, web scraping)

---

**Ready to start?** Let me know and I'll begin building the implementation! 🚀
