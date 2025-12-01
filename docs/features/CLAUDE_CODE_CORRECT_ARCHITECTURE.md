# Claude Code Integration - Corrected Architecture

> **Key Insight**: Orchestration, Agentic Loop, and Execution layers ALL run inside the sandbox container for maximum isolation and portability.

---

## 🏗️ Corrected Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND (FastAPI)                                      │
│                           Host Environment                                       │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │                      Enhanced RAG Agent                                 │    │
│  │                      (Request Router)                                   │    │
│  │                                                                          │    │
│  │  - Receives user query                                                  │    │
│  │  - Classifies complexity (SIMPLE/MEDIUM/COMPLEX)                        │    │
│  │  - Routes to appropriate handler                                        │    │
│  └────────────────────────────┬───────────────────────────────────────────┘    │
│                                │                                                │
│                    ┌───────────┴───────────┐                                    │
│                    │                       │                                    │
│             SIMPLE/No Agent          COMPLEX/Agent Mode                         │
│                    │                       │                                    │
│            ┌───────▼────────┐    ┌────────▼──────────┐                         │
│            │  Direct RAG    │    │  Sandbox Manager  │                         │
│            │  /LLM Response │    │                   │                         │
│            └────────────────┘    │  - Create sandbox │                         │
│                                  │  - Copy files     │                         │
│                                  │  - Start agent    │                         │
│                                  │  - Monitor        │                         │
│                                  │  - Cleanup        │                         │
│                                  └────────┬──────────┘                         │
└───────────────────────────────────────────┼────────────────────────────────────┘
                                            │
                                            │ Docker API
                                            │ docker run --rm -v workspace:/app/workspace
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    🐳 SANDBOX CONTAINER (Isolated Environment)                   │
│                    Image: chatbot-agent-runtime:latest                          │
│                    Network: isolated / User: sandbox (non-root)                 │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │                    📊 ORCHESTRATION LAYER                               │    │
│  │                    (Session & Context Management)                       │    │
│  │                                                                          │    │
│  │  Components:                                                            │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │    │
│  │  │  Session     │  │   Context    │  │    Tool      │  │  Safety  │  │    │
│  │  │  Manager     │  │   Manager    │  │   Registry   │  │  Layer   │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘  │    │
│  │                                                                          │    │
│  │  Responsibilities:                                                      │    │
│  │  • Manage conversation state                                            │    │
│  │  • Track workspace files                                                │    │
│  │  • Build context for LLM                                                │    │
│  │  • Register available tools                                             │    │
│  │  • Enforce security policies                                            │    │
│  │  • Stream events to backend                                             │    │
│  └────────────────────────────┬───────────────────────────────────────────┘    │
│                                │                                                │
│                                ▼                                                │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │                    🤖 AGENTIC LOOP                                      │    │
│  │                    (Think → Plan → Act → Observe)                      │    │
│  │                                                                          │    │
│  │  Main Loop (max 50 iterations):                                        │    │
│  │                                                                          │    │
│  │  while not complete and iterations < max_iterations:                   │    │
│  │                                                                          │    │
│  │      1️⃣ THINK (Analyze current state)                                   │    │
│  │         • What have we accomplished so far?                             │    │
│  │         • What errors/obstacles occurred?                               │    │
│  │         • What's the next logical step?                                 │    │
│  │                                                                          │    │
│  │      2️⃣ PLAN (Decide on tools)                                          │    │
│  │         • Call Claude API with available tools                          │    │
│  │         • Get tool selection + parameters                               │    │
│  │         • Validate safety constraints                                   │    │
│  │                                                                          │    │
│  │      3️⃣ ACT (Execute tools)                                             │    │
│  │         • Route to execution layer                                      │    │
│  │         • Execute tool with parameters                                  │    │
│  │         • Capture stdout/stderr/return value                            │    │
│  │                                                                          │    │
│  │      4️⃣ OBSERVE (Process results)                                       │    │
│  │         • Add results to conversation history                           │    │
│  │         • Stream event to backend (via Redis)                           │    │
│  │         • Check termination conditions                                  │    │
│  │                                                                          │    │
│  │  Termination Conditions:                                                │    │
│  │  ✅ Claude returns stop_reason="end_turn"                               │    │
│  │  ✅ Task completed successfully                                         │    │
│  │  ⏱️  Max iterations reached                                              │    │
│  │  ❌ Critical error occurred                                              │    │
│  │  🛑 User cancellation requested                                         │    │
│  └────────────────────────────┬───────────────────────────────────────────┘    │
│                                │                                                │
│                                ▼                                                │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │                    ⚙️ EXECUTION LAYER                                   │    │
│  │                    (Tool Implementations)                               │    │
│  │                                                                          │    │
│  │  Available Tools:                                                       │    │
│  │                                                                          │    │
│  │  ┌────────────────────────────────────────────────────────────┐        │    │
│  │  │ 🐍 execute_python(code: str) → dict                        │        │    │
│  │  │                                                             │        │    │
│  │  │ • Write code to temp file                                  │        │    │
│  │  │ • Execute: python temp_script.py                           │        │    │
│  │  │ • Capture stdout, stderr, exit_code                        │        │    │
│  │  │ • Return: {success, stdout, stderr, exit_code}             │        │    │
│  │  └────────────────────────────────────────────────────────────┘        │    │
│  │                                                                          │    │
│  │  ┌────────────────────────────────────────────────────────────┐        │    │
│  │  │ 📖 read_file(path: str) → str                              │        │    │
│  │  │                                                             │        │    │
│  │  │ • Validate path (within /app/workspace/)                   │        │    │
│  │  │ • Read file contents                                       │        │    │
│  │  │ • Return text (with line numbers optional)                 │        │    │
│  │  └────────────────────────────────────────────────────────────┘        │    │
│  │                                                                          │    │
│  │  ┌────────────────────────────────────────────────────────────┐        │    │
│  │  │ 📝 write_file(path: str, content: str) → dict              │        │    │
│  │  │                                                             │        │    │
│  │  │ • Validate path (within /app/workspace/)                   │        │    │
│  │  │ • Create parent directories if needed                      │        │    │
│  │  │ • Write content to file                                    │        │    │
│  │  │ • Return: {success, bytes_written}                         │        │    │
│  │  └────────────────────────────────────────────────────────────┘        │    │
│  │                                                                          │    │
│  │  ┌────────────────────────────────────────────────────────────┐        │    │
│  │  │ ✏️ edit_file(path: str, old: str, new: str) → dict         │        │    │
│  │  │                                                             │        │    │
│  │  │ • Read file                                                 │        │    │
│  │  │ • Find old_text (must be unique)                           │        │    │
│  │  │ • Replace with new_text                                    │        │    │
│  │  │ • Write back to file                                       │        │    │
│  │  └────────────────────────────────────────────────────────────┘        │    │
│  │                                                                          │    │
│  │  ┌────────────────────────────────────────────────────────────┐        │    │
│  │  │ 📦 install_package(package: str) → dict                    │        │    │
│  │  │                                                             │        │    │
│  │  │ • Validate package name (no shell injection)               │        │    │
│  │  │ • Execute: pip install {package}                           │        │    │
│  │  │ • Return installation result                               │        │    │
│  │  └────────────────────────────────────────────────────────────┘        │    │
│  │                                                                          │    │
│  │  ┌────────────────────────────────────────────────────────────┐        │    │
│  │  │ 💻 run_bash(command: str) → dict                           │        │    │
│  │  │                                                             │        │    │
│  │  │ • Check against blocklist (rm -rf /, etc.)                 │        │    │
│  │  │ • Execute in /app/workspace/                               │        │    │
│  │  │ • Timeout: 60 seconds                                      │        │    │
│  │  │ • Return: {success, stdout, stderr}                        │        │    │
│  │  └────────────────────────────────────────────────────────────┘        │    │
│  │                                                                          │    │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │                    📂 WORKSPACE                                         │    │
│  │                    /app/workspace/                                      │    │
│  │                                                                          │    │
│  │  ├── input/                  ← User uploaded files                     │    │
│  │  │   └── sales_data.csv                                                │    │
│  │  │                                                                      │    │
│  │  ├── output/                 ← Generated artifacts                     │    │
│  │  │   ├── eda_report.md                                                 │    │
│  │  │   ├── distribution.png                                              │    │
│  │  │   ├── correlation_matrix.png                                        │    │
│  │  │   └── analysis_script.py                                            │    │
│  │  │                                                                      │    │
│  │  ├── temp/                   ← Temporary execution files               │    │
│  │  │   └── temp_script.py                                                │    │
│  │  │                                                                      │    │
│  │  └── .state/                 ← Agent state persistence                 │    │
│  │      ├── conversation.json                                             │    │
│  │      └── context.json                                                  │    │
│  └────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │                    🔌 COMMUNICATION LAYER                               │    │
│  │                                                                          │    │
│  │  • Redis client (for event streaming)                                  │    │
│  │  • Publishes events to: agent:events:{task_id}                         │    │
│  │  • Event types: thinking, tool_call, tool_result, artifact, complete   │    │
│  └────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ On completion
                                    ▼
                          ┌─────────────────────┐
                          │  Artifacts → MinIO  │
                          │  State → Database   │
                          │  Cleanup container  │
                          └─────────────────────┘
```

---

## 🐳 Sandbox Container Structure

### Dockerfile for Agent Runtime

```dockerfile
FROM python:3.11-slim

# ═══════════════════════════════════════════════════════════
# LAYER 1: System Dependencies
# ═══════════════════════════════════════════════════════════

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# ═══════════════════════════════════════════════════════════
# LAYER 2: Python Environment (Data Science Stack)
# ═══════════════════════════════════════════════════════════

RUN pip install --no-cache-dir \
    # Core libraries
    pandas numpy scipy \
    # Visualization
    matplotlib seaborn plotly \
    # ML
    scikit-learn \
    # Vision
    pillow opencv-python \
    # Web
    requests beautifulsoup4 \
    # Utilities
    python-dotenv pyyaml \
    # Communication
    redis anthropic

# ═══════════════════════════════════════════════════════════
# LAYER 3: Agent Code (Orchestration + Loop + Execution)
# ═══════════════════════════════════════════════════════════

WORKDIR /app

# Copy agent implementation
COPY agent_runtime/ /app/agent_runtime/
COPY entrypoint.py /app/entrypoint.py

# Agent structure:
# /app/
# ├── agent_runtime/
# │   ├── __init__.py
# │   ├── orchestration/           ← ORCHESTRATION LAYER
# │   │   ├── session_manager.py
# │   │   ├── context_manager.py
# │   │   ├── tool_registry.py
# │   │   └── safety_layer.py
# │   ├── agentic_loop/             ← AGENTIC LOOP
# │   │   ├── agent_loop.py
# │   │   ├── think.py
# │   │   ├── plan.py
# │   │   ├── act.py
# │   │   └── observe.py
# │   ├── execution/                ← EXECUTION LAYER
# │   │   ├── python_executor.py
# │   │   ├── file_ops.py
# │   │   ├── bash_executor.py
# │   │   └── package_installer.py
# │   └── communication/
# │       └── redis_client.py
# └── entrypoint.py

# ═══════════════════════════════════════════════════════════
# LAYER 4: Security & Isolation
# ═══════════════════════════════════════════════════════════

# Create non-root user
RUN useradd -m -u 1000 sandbox && \
    mkdir -p /app/workspace && \
    chown -R sandbox:sandbox /app

USER sandbox

# ═══════════════════════════════════════════════════════════
# LAYER 5: Workspace
# ═══════════════════════════════════════════════════════════

WORKDIR /app/workspace

# Entry point: Start the agent
ENTRYPOINT ["python", "/app/entrypoint.py"]
```

---

## 📋 Implementation Structure

### Backend (FastAPI) - Minimal Orchestration

```python
# backend/app/services/agent_sandbox_manager.py

import docker
import asyncio
import json
from pathlib import Path
from typing import Dict, Any

class AgentSandboxManager:
    """
    Manages sandbox container lifecycle

    IMPORTANT: This is just a lightweight manager.
    All orchestration/agentic logic runs INSIDE the container.
    """

    def __init__(self):
        self.docker_client = docker.from_env()
        self.active_sandboxes = {}

    async def create_and_run_agent(
        self,
        task_id: str,
        session_id: str,
        query: str,
        input_files: list,
        user_preferences: dict
    ) -> Dict[str, Any]:
        """
        Create sandbox and run autonomous agent inside it

        Returns immediately with task_id. Agent runs async in container.
        """

        # Prepare workspace
        workspace = Path(f"/tmp/agent_workspaces/{task_id}")
        workspace.mkdir(parents=True, exist_ok=True)

        # Copy input files
        input_dir = workspace / "input"
        input_dir.mkdir(exist_ok=True)
        for file in input_files:
            # Copy file to input_dir
            pass

        # Prepare environment variables (pass to container)
        env_vars = {
            "TASK_ID": task_id,
            "SESSION_ID": session_id,
            "USER_QUERY": query,
            "ANTHROPIC_API_KEY": settings.ANTHROPIC_API_KEY,
            "REDIS_URL": settings.REDIS_URL,
            "MAX_ITERATIONS": "50",
            "TIMEOUT_SECONDS": "600"
        }

        # Start container
        container = self.docker_client.containers.run(
            "chatbot-agent-runtime:latest",

            # Environment
            environment=env_vars,

            # Volumes (workspace)
            volumes={
                str(workspace): {"bind": "/app/workspace", "mode": "rw"}
            },

            # Security
            user="sandbox",
            network_mode="bridge",  # or "none" for full isolation
            mem_limit="2g",
            cpu_period=100000,
            cpu_quota=50000,  # 50% of 1 core

            # Execution
            detach=True,  # Run in background
            remove=True,  # Auto-remove on completion

            # Labels for tracking
            labels={
                "task_id": task_id,
                "session_id": session_id,
                "type": "agent_runtime"
            }
        )

        self.active_sandboxes[task_id] = {
            "container": container,
            "workspace": workspace,
            "started_at": datetime.now()
        }

        return {
            "task_id": task_id,
            "container_id": container.id,
            "status": "running"
        }

    async def monitor_agent(self, task_id: str):
        """
        Monitor agent execution (logs, status)

        Agent streams events to Redis, so we mostly just wait for completion.
        """

        if task_id not in self.active_sandboxes:
            raise ValueError(f"No sandbox found for task {task_id}")

        sandbox = self.active_sandboxes[task_id]
        container = sandbox["container"]

        # Wait for container to complete (with timeout)
        try:
            exit_code = container.wait(timeout=600)  # 10 minutes

            # Get logs (for debugging)
            logs = container.logs().decode('utf-8')

            return {
                "exit_code": exit_code,
                "logs": logs,
                "status": "completed" if exit_code == 0 else "failed"
            }

        except Exception as e:
            logger.error(f"Agent monitoring error: {e}")
            container.stop()
            return {"status": "failed", "error": str(e)}

    async def cleanup(self, task_id: str):
        """Cleanup sandbox (container auto-removes, but cleanup workspace)"""

        if task_id in self.active_sandboxes:
            sandbox = self.active_sandboxes[task_id]

            # Upload artifacts to MinIO before cleanup
            await self._upload_artifacts(sandbox["workspace"], task_id)

            # Remove workspace (optional, keep for debugging)
            # shutil.rmtree(sandbox["workspace"])

            del self.active_sandboxes[task_id]
```

---

### Container Entry Point

```python
# entrypoint.py (runs INSIDE container)

import os
import sys
import asyncio
from agent_runtime.orchestration.session_manager import SessionManager
from agent_runtime.agentic_loop.agent_loop import AgentLoop
from agent_runtime.communication.redis_client import RedisEventPublisher

async def main():
    """
    Container entry point - runs the full agent workflow

    This is the main process inside the sandbox container.
    It coordinates all three layers: Orchestration, Agentic Loop, Execution.
    """

    # Get environment variables (passed from backend)
    task_id = os.getenv("TASK_ID")
    session_id = os.getenv("SESSION_ID")
    user_query = os.getenv("USER_QUERY")
    max_iterations = int(os.getenv("MAX_ITERATIONS", "50"))

    print(f"🚀 Starting agent for task: {task_id}")
    print(f"📝 Query: {user_query}")

    try:
        # ═══════════════════════════════════════════════════════════
        # ORCHESTRATION LAYER: Initialize
        # ═══════════════════════════════════════════════════════════

        session_manager = SessionManager(task_id, session_id)
        event_publisher = RedisEventPublisher(task_id)

        await event_publisher.publish({
            "type": "started",
            "task_id": task_id,
            "query": user_query
        })

        # ═══════════════════════════════════════════════════════════
        # AGENTIC LOOP: Run autonomous workflow
        # ═══════════════════════════════════════════════════════════

        agent_loop = AgentLoop(
            session_manager=session_manager,
            event_publisher=event_publisher,
            max_iterations=max_iterations
        )

        result = await agent_loop.run(user_query)

        # ═══════════════════════════════════════════════════════════
        # COMPLETION: Publish final result
        # ═══════════════════════════════════════════════════════════

        await event_publisher.publish({
            "type": "completed",
            "task_id": task_id,
            "result": result,
            "artifacts": session_manager.list_output_files()
        })

        print(f"✅ Agent completed successfully")
        sys.exit(0)

    except Exception as e:
        print(f"❌ Agent failed: {e}")

        await event_publisher.publish({
            "type": "failed",
            "task_id": task_id,
            "error": str(e)
        })

        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

---

### Agentic Loop Implementation (Inside Container)

```python
# agent_runtime/agentic_loop/agent_loop.py

import anthropic
import os
from typing import Dict, Any, List

class AgentLoop:
    """
    Main agentic loop: THINK → PLAN → ACT → OBSERVE

    Runs entirely inside the sandbox container.
    """

    def __init__(self, session_manager, event_publisher, max_iterations=50):
        self.session_manager = session_manager
        self.event_publisher = event_publisher
        self.max_iterations = max_iterations

        # Initialize Claude client
        self.claude = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )

        # Initialize tool registry (from orchestration layer)
        from agent_runtime.orchestration.tool_registry import get_tool_registry
        self.tool_registry = get_tool_registry()

        # Conversation history
        self.messages = []

    async def run(self, user_query: str) -> Dict[str, Any]:
        """
        Main agentic loop

        Returns final result after completion or max iterations
        """

        # Initialize conversation
        self.messages.append({
            "role": "user",
            "content": user_query
        })

        for iteration in range(self.max_iterations):

            print(f"🔄 Iteration {iteration + 1}/{self.max_iterations}")

            # ═══════════════════════════════════════════════════
            # 1️⃣ THINK: Call Claude to analyze and plan
            # ═══════════════════════════════════════════════════

            response = self.claude.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=self._build_system_prompt(),
                tools=self.tool_registry.get_tools(),
                messages=self.messages
            )

            # ═══════════════════════════════════════════════════
            # 2️⃣ PLAN: Check what Claude wants to do
            # ═══════════════════════════════════════════════════

            # Termination condition
            if response.stop_reason == "end_turn":
                final_response = self._extract_final_response(response)

                await self.event_publisher.publish({
                    "type": "completed",
                    "iteration": iteration + 1,
                    "response": final_response
                })

                return {
                    "success": True,
                    "response": final_response,
                    "iterations": iteration + 1
                }

            # Tool use requested
            if response.stop_reason == "tool_use":

                # ═══════════════════════════════════════════════
                # 3️⃣ ACT: Execute tools
                # ═══════════════════════════════════════════════

                tool_results = await self._execute_tools(response, iteration)

                # Add to conversation history
                self.messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                self.messages.append({
                    "role": "user",
                    "content": tool_results
                })

                # ═══════════════════════════════════════════════
                # 4️⃣ OBSERVE: Continue loop
                # ═══════════════════════════════════════════════

                continue

        # Max iterations reached
        return {
            "success": False,
            "error": "Max iterations reached",
            "iterations": self.max_iterations
        }

    async def _execute_tools(self, response, iteration: int) -> List[Dict]:
        """Execute all tool calls from Claude's response"""

        tool_results = []

        for block in response.content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input
                tool_id = block.id

                print(f"🔧 Executing tool: {tool_name}")

                # Publish event
                await self.event_publisher.publish({
                    "type": "tool_call",
                    "iteration": iteration + 1,
                    "tool": tool_name,
                    "input": tool_input
                })

                # Execute via tool registry (→ EXECUTION LAYER)
                try:
                    result = await self.tool_registry.execute(
                        tool_name,
                        tool_input
                    )

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": str(result)
                    })

                    # Publish result
                    await self.event_publisher.publish({
                        "type": "tool_result",
                        "iteration": iteration + 1,
                        "tool": tool_name,
                        "result": result
                    })

                except Exception as e:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "is_error": True,
                        "content": str(e)
                    })

        return tool_results

    def _build_system_prompt(self) -> str:
        """Build system prompt with workspace context"""

        # Get current workspace state from orchestration layer
        workspace_files = self.session_manager.list_workspace_files()

        return f"""You are an autonomous coding agent running in a sandboxed Python environment.

Your goal: Complete the user's task by writing and executing code.

## Workspace
You have access to /app/workspace/ with these files:
{workspace_files}

## Available Tools
You can use these tools to accomplish your goal:
- execute_python: Run Python code
- read_file: Read file contents
- write_file: Create/overwrite files
- edit_file: Make targeted edits
- install_package: Install Python packages
- run_bash: Run shell commands (restricted)

## Guidelines
1. Break complex tasks into small steps
2. Verify each step before proceeding
3. Save important outputs to /app/workspace/output/
4. Handle errors gracefully
5. When complete, provide a clear summary

Think step by step and explain your reasoning before each action."""

    def _extract_final_response(self, response) -> str:
        """Extract final text response from Claude"""
        for block in response.content:
            if hasattr(block, 'text'):
                return block.text
        return ""


# Global instance
agent_loop = AgentLoop()
```

---

## 🔑 Key Benefits of This Architecture

### 1. **True Isolation**
- Entire agent stack runs in container
- No code execution on host
- Easy to kill/restart

### 2. **Portability**
- Container is self-contained
- Can run anywhere (local, K8s, cloud)
- Easy to version and deploy

### 3. **Scalability**
- Spin up multiple containers in parallel
- Each task gets its own isolated environment
- No cross-contamination

### 4. **Security**
- Orchestration + Execution in same security boundary
- No need to expose internal APIs
- All dangerous operations contained

### 5. **Simplicity**
- Backend just starts container and monitors
- All complexity inside container
- Clean separation of concerns

---

## 📊 Comparison: Old vs New Architecture

| Aspect | ❌ Old (Incorrect) | ✅ New (Correct) |
|--------|-------------------|------------------|
| **Orchestration Layer** | Backend (FastAPI) | Inside container |
| **Agentic Loop** | Backend (FastAPI) | Inside container |
| **Execution Layer** | Docker exec from backend | Inside container |
| **Security Boundary** | Mixed (host + container) | Pure (container only) |
| **Portability** | Tied to backend | Standalone container |
| **Complexity** | Backend manages everything | Container self-manages |

---

This is the correct architecture! The backend is now just a lightweight launcher/monitor, while all the intelligence runs inside the sandbox. Want me to start implementing this? 🚀
