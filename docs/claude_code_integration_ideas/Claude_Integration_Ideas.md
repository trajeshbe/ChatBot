Can i integrte claude code into my Application . Example : I have a conversational agent and if an user asks for a complex task to be performed, would love claude code to be pick it up, perform the deeep dive analysis and come back with the response to the UI, if can spin of a new container, create the application and give the user to access the results.. like an complex Exploratory Data Analyis OR a Complex Vision task etc.. whats your thoughts on it ?

This is a really interesting architecture you're describing! Let me share my thoughts on how you could approach this.

## What You're Describing

You want a hybrid system where:

1. A conversational agent handles normal interactions
2. Complex tasks get delegated to an autonomous coding environment
3. Results (files, apps, analysis) get served back to users

## Current Options

**Claude Code CLI** is designed for developer terminals, not programmatic integration into applications. It's meant for interactive use, not as an API you'd call from your backend.

**What you'd actually want to use is the Anthropic API directly** with agentic patterns. Here's how this could work:

### Architecture Approach

```
User Request → Your Orchestrator Agent → Determines Complexity
                                              ↓
                        ┌─────────────────────┴─────────────────────┐
                        ↓                                           ↓
                  Simple Task                               Complex Task
                        ↓                                           ↓
              Direct Claude Response              Spin up sandboxed container
                                                           ↓
                                                  Claude API + Tool Use
                                                  (file ops, code execution,
                                                   data analysis, etc.)
                                                           ↓
                                                  Return artifacts/URL to user
```

### Key Components You'd Need

1. **Container orchestration** — Spin up isolated environments (Docker, Kubernetes, or services like Modal, E2B, or Fly.io)
2. **Tool-use with the API** — Claude's API supports tool use where you define tools for file creation, code execution, shell commands, etc.
3. **Artifact serving** — A way to host and serve generated outputs (dashboards, reports, apps)

### Services Worth Exploring

- **E2B (e2b.dev)** — Sandboxed code execution environments designed for AI agents
- **Modal** — Serverless containers, great for spinning up compute on demand
- **Replicate / RunPod** — If you need GPU for vision tasks

## Would This Work Today?

Yes, but you'd be building the orchestration layer yourself. The pattern would be:

1. Your app calls the Anthropic API with tool definitions
2. Claude returns tool calls (e.g., "execute this Python code")
3. Your backend executes those in a sandboxed container
4. Results feed back to Claude for synthesis
5. Final output (files, URLs, reports) returns to your UI

This is essentially what Claude Code does internally, but packaged for CLI use. You'd replicate that pattern with the API.

Would you like me to search for more specific documentation on tool use patterns or any of these sandboxing services?

what does it take to implement claude code from scratch..  can you give the methodology, architecture, process etc

This is a great deep-dive question. Let me break down what it would take to build something like Claude Code from scratch.

## Core Concept

Claude Code is essentially an **agentic loop** where an LLM can:

1. Understand a task
2. Plan an approach
3. Execute actions (run code, read/write files, use shell)
4. Observe results
5. Iterate until complete

------

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE                                 │
│                    (CLI / Web UI / API Endpoint)                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATION LAYER                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Session   │  │   Context   │  │    Tool     │  │   Safety    │    │
│  │  Manager    │  │   Manager   │  │  Registry   │  │   Layer     │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           AGENTIC LOOP                                   │
│                                                                          │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│   │  THINK   │ -> │   PLAN   │ -> │   ACT    │ -> │ OBSERVE  │ ──┐     │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘   │     │
│        ▲                                                          │     │
│        └──────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          EXECUTION LAYER                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Bash      │  │    File     │  │    Code     │  │   Custom    │    │
│  │  Executor   │  │   System    │  │  Execution  │  │   Tools     │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         SANDBOXED ENVIRONMENT                            │
│                  (Docker Container / VM / Isolated FS)                   │
└─────────────────────────────────────────────────────────────────────────┘
```

------

## Component Breakdown

### 1. Tool Definitions

You need to define tools that Claude can invoke. Using the Anthropic API's tool-use format:

python

```python
TOOLS = [
    {
        "name": "bash",
        "description": "Execute a bash command in the sandboxed environment",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute"
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "file_read",
        "description": "Read contents of a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to file"},
                "start_line": {"type": "integer", "description": "Optional start line"},
                "end_line": {"type": "integer", "description": "Optional end line"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "file_write",
        "description": "Write or create a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "file_edit",
        "description": "Edit a file using search/replace",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_text": {"type": "string"},
                "new_text": {"type": "string"}
            },
            "required": ["path", "old_text", "new_text"]
        }
    }
]
```

### 2. The Agentic Loop (Core Engine)

python

```python
import anthropic
from typing import Any

class AgentLoop:
    def __init__(self, sandbox: "Sandbox", max_iterations: int = 50):
        self.client = anthropic.Anthropic()
        self.sandbox = sandbox
        self.max_iterations = max_iterations
        self.conversation_history = []
        
    def run(self, user_task: str) -> str:
        """Main agentic loop"""
        
        # Initialize with system prompt and user task
        system_prompt = self._build_system_prompt()
        self.conversation_history.append({
            "role": "user",
            "content": user_task
        })
        
        for iteration in range(self.max_iterations):
            # Call Claude
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8096,
                system=system_prompt,
                tools=TOOLS,
                messages=self.conversation_history
            )
            
            # Check stop conditions
            if response.stop_reason == "end_turn":
                # Extract final text response
                return self._extract_text(response)
            
            if response.stop_reason == "tool_use":
                # Process tool calls
                tool_results = self._execute_tools(response)
                
                # Add assistant response and tool results to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response.content
                })
                self.conversation_history.append({
                    "role": "user",
                    "content": tool_results
                })
        
        return "Max iterations reached"
    
    def _execute_tools(self, response) -> list:
        """Execute all tool calls and return results"""
        results = []
        
        for block in response.content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input
                tool_id = block.id
                
                # Execute in sandbox
                output = self.sandbox.execute_tool(tool_name, tool_input)
                
                results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": output
                })
        
        return results
    
    def _build_system_prompt(self) -> str:
        return """You are an autonomous coding agent. You have access to a 
        sandboxed environment where you can execute bash commands, read/write 
        files, and run code.
        
        When given a task:
        1. Think through the approach
        2. Break it into steps
        3. Execute each step using available tools
        4. Verify results before moving on
        5. Handle errors gracefully
        
        Always explain what you're doing and why."""
    
    def _extract_text(self, response) -> str:
        for block in response.content:
            if hasattr(block, 'text'):
                return block.text
        return ""
```

### 3. Sandbox Execution Layer

python

```python
import docker
import subprocess
import os
from pathlib import Path

class Sandbox:
    """Isolated execution environment"""
    
    def __init__(self, workspace_dir: str = "/tmp/agent_workspace"):
        self.workspace = Path(workspace_dir)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.docker_client = docker.from_env()
        self.container = None
        
    def start_container(self):
        """Spin up isolated Docker container"""
        self.container = self.docker_client.containers.run(
            "python:3.11-slim",  # Base image
            command="tail -f /dev/null",  # Keep alive
            detach=True,
            working_dir="/workspace",
            volumes={
                str(self.workspace): {"bind": "/workspace", "mode": "rw"}
            },
            mem_limit="2g",
            cpu_period=100000,
            cpu_quota=50000,  # 50% CPU
            network_mode="bridge",  # Or "none" for isolation
        )
        
    def execute_tool(self, tool_name: str, params: dict) -> str:
        """Route tool execution"""
        handlers = {
            "bash": self._exec_bash,
            "file_read": self._exec_file_read,
            "file_write": self._exec_file_write,
            "file_edit": self._exec_file_edit,
        }
        
        handler = handlers.get(tool_name)
        if not handler:
            return f"Unknown tool: {tool_name}"
            
        try:
            return handler(params)
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
    
    def _exec_bash(self, params: dict) -> str:
        """Execute bash command in container"""
        command = params["command"]
        
        # Security checks
        if self._is_dangerous_command(command):
            return "Command blocked for security reasons"
        
        exit_code, output = self.container.exec_run(
            f"bash -c '{command}'",
            workdir="/workspace"
        )
        
        return f"Exit code: {exit_code}\n{output.decode('utf-8')}"
    
    def _exec_file_read(self, params: dict) -> str:
        """Read file contents"""
        path = self.workspace / params["path"].lstrip("/")
        
        if not path.exists():
            return f"File not found: {params['path']}"
        
        content = path.read_text()
        
        # Handle line ranges
        if "start_line" in params:
            lines = content.split("\n")
            start = params.get("start_line", 1) - 1
            end = params.get("end_line", len(lines))
            content = "\n".join(lines[start:end])
        
        return content
    
    def _exec_file_write(self, params: dict) -> str:
        """Write file"""
        path = self.workspace / params["path"].lstrip("/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(params["content"])
        return f"Successfully wrote {len(params['content'])} bytes to {params['path']}"
    
    def _exec_file_edit(self, params: dict) -> str:
        """Search and replace in file"""
        path = self.workspace / params["path"].lstrip("/")
        
        if not path.exists():
            return f"File not found: {params['path']}"
        
        content = path.read_text()
        
        if params["old_text"] not in content:
            return "Old text not found in file"
        
        new_content = content.replace(params["old_text"], params["new_text"], 1)
        path.write_text(new_content)
        
        return "File updated successfully"
    
    def _is_dangerous_command(self, command: str) -> bool:
        """Basic security checks"""
        dangerous_patterns = [
            "rm -rf /",
            "mkfs",
            "> /dev/",
            "dd if=",
            ":(){ :|:& };:",  # Fork bomb
        ]
        return any(p in command for p in dangerous_patterns)
    
    def cleanup(self):
        """Destroy container"""
        if self.container:
            self.container.stop()
            self.container.remove()
```

### 4. Context Management

python

```python
class ContextManager:
    """Manage what context gets sent to the model"""
    
    def __init__(self, max_tokens: int = 100000):
        self.max_tokens = max_tokens
        self.file_cache = {}
        
    def build_context(self, workspace: Path) -> str:
        """Build context about the current workspace state"""
        context_parts = []
        
        # Directory structure
        context_parts.append("## Current Workspace Structure")
        context_parts.append(self._get_tree(workspace))
        
        # Recently accessed files
        context_parts.append("\n## Recently Accessed Files")
        for path, content in list(self.file_cache.items())[-5:]:
            context_parts.append(f"\n### {path}")
            context_parts.append(self._truncate(content, 500))
        
        return "\n".join(context_parts)
    
    def _get_tree(self, path: Path, prefix: str = "", max_depth: int = 3) -> str:
        """Generate directory tree"""
        if max_depth == 0:
            return ""
        
        lines = []
        try:
            entries = sorted(path.iterdir())
            for i, entry in enumerate(entries):
                is_last = i == len(entries) - 1
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}{entry.name}")
                
                if entry.is_dir() and not entry.name.startswith("."):
                    extension = "    " if is_last else "│   "
                    lines.append(
                        self._get_tree(entry, prefix + extension, max_depth - 1)
                    )
        except PermissionError:
            pass
        
        return "\n".join(lines)
    
    def _truncate(self, text: str, max_lines: int) -> str:
        lines = text.split("\n")
        if len(lines) > max_lines:
            return "\n".join(lines[:max_lines]) + f"\n... ({len(lines) - max_lines} more lines)"
        return text
```

### 5. Safety Layer

python

```python
class SafetyLayer:
    """Security and safety controls"""
    
    def __init__(self):
        self.blocked_commands = set()
        self.rate_limits = {}
        self.audit_log = []
        
    def check_command(self, command: str) -> tuple[bool, str]:
        """Validate command before execution"""
        
        # Check for dangerous patterns
        dangers = [
            (r"rm\s+-rf\s+/", "Cannot delete root filesystem"),
            (r"curl.*\|.*sh", "Cannot pipe remote scripts to shell"),
            (r"wget.*\|.*sh", "Cannot pipe remote scripts to shell"),
            (r"chmod\s+777", "Overly permissive file permissions"),
            (r">\s*/etc/", "Cannot write to system directories"),
        ]
        
        import re
        for pattern, reason in dangers:
            if re.search(pattern, command):
                self.audit_log.append(f"BLOCKED: {command} - {reason}")
                return False, reason
        
        return True, ""
    
    def check_file_access(self, path: str, workspace: str) -> tuple[bool, str]:
        """Ensure file access stays within workspace"""
        
        from pathlib import Path
        
        resolved = Path(path).resolve()
        workspace_resolved = Path(workspace).resolve()
        
        if not str(resolved).startswith(str(workspace_resolved)):
            return False, "Path escapes workspace boundary"
        
        return True, ""
    
    def log_action(self, action: str, params: dict, result: str):
        """Audit logging"""
        import datetime
        self.audit_log.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action,
            "params": params,
            "result_preview": result[:200]
        })
```

### 6. Putting It All Together

python

```python
class ClaudeCodeEngine:
    """Main entry point"""
    
    def __init__(self):
        self.sandbox = Sandbox()
        self.context_manager = ContextManager()
        self.safety = SafetyLayer()
        self.agent = AgentLoop(self.sandbox)
        
    def start(self):
        """Initialize the environment"""
        self.sandbox.start_container()
        print("Agent environment ready")
        
    def execute_task(self, task: str) -> dict:
        """Execute a user task"""
        
        # Add workspace context
        context = self.context_manager.build_context(self.sandbox.workspace)
        full_task = f"{context}\n\n## User Task\n{task}"
        
        # Run the agent
        result = self.agent.run(full_task)
        
        return {
            "result": result,
            "workspace": str(self.sandbox.workspace),
            "files_created": self._list_outputs(),
            "audit_log": self.safety.audit_log
        }
    
    def _list_outputs(self) -> list:
        """List files created in workspace"""
        return [str(f) for f in self.sandbox.workspace.rglob("*") if f.is_file()]
    
    def cleanup(self):
        """Tear down"""
        self.sandbox.cleanup()


# Usage
if __name__ == "__main__":
    engine = ClaudeCodeEngine()
    engine.start()
    
    result = engine.execute_task("""
        Create a Python script that:
        1. Fetches data from a public API
        2. Processes it into a pandas DataFrame
        3. Generates a visualization
        4. Saves results to output.html
    """)
    
    print(result)
    engine.cleanup()
```

------

## Key Challenges You'll Face

```
ChallengeSolution Approach
Context window limitsSummarize old context, keep recent actions, smart truncation
Runaway loopsMax iterations, cost limits, timeout per action
SecuritySandboxing, command filtering, network isolation
State managementPersist workspace, checkpoint conversations
Error recoveryLet the model see errors and self-correct
Cost controlToken budgets, caching, smaller models for simple tasks
Streaming UIStream tool outputs to user in real-time
```

------

## For Your Use Case (Serving Results Back to Users)

Add an output serving layer:

python

```python
class OutputServer:
    """Serve generated artifacts to users"""
    
    def __init__(self, base_url: str = "https://your-app.com"):
        self.base_url = base_url
        
    def publish_output(self, workspace: Path, output_files: list) -> dict:
        """Make outputs accessible to users"""
        
        urls = {}
        for file_path in output_files:
            # Copy to serving location / upload to S3 / etc.
            public_id = self._upload_file(file_path)
            urls[file_path.name] = f"{self.base_url}/outputs/{public_id}"
        
        return urls
```

------

## Recommended Tech Stack

```
ComponentOptions
Container RuntimeDocker, Firecracker, gVisor
OrchestrationKubernetes, Docker Compose, Modal, E2B
API FrameworkFastAPI, Flask
Queue (for async)Redis, RabbitMQ, SQS
File StorageS3, GCS, MinIO
FrontendReact, Next.js with streaming
```

------

Would you like me to dive deeper into any specific component—for example, the streaming UI, the container orchestration for scale, or how to handle long-running tasks?

if i have to implment using the follwowing tech stack // Docker,Docker Compose,FastAPI,Redis,MinIO,React, Next.js with streaming // give me a road map

This is a comprehensive implementation roadmap. Let me break this down into phases with detailed architecture and code.

------

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    FRONTEND                                          │
│                              Next.js + React                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │   Task UI    │  │   Streaming  │  │    File      │  │   Results    │            │
│  │   Input      │  │   Terminal   │  │   Browser    │  │   Viewer     │            │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         │ WebSocket / SSE
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                   API GATEWAY                                        │
│                                    FastAPI                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │   REST API   │  │  WebSocket   │  │     Auth     │  │   Rate       │            │
│  │   Endpoints  │  │   Handler    │  │   Middleware │  │   Limiter    │            │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                          ┌──────────────┼──────────────┐
                          ▼              ▼              ▼
                    ┌──────────┐  ┌──────────────┐  ┌──────────┐
                    │  Redis   │  │    MinIO     │  │ Postgres │
                    │  Queue   │  │   Storage    │  │ Metadata │
                    │  Pub/Sub │  │              │  │          │
                    └──────────┘  └──────────────┘  └──────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                               WORKER POOL                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                          Agent Worker (Python)                               │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │    │
│  │  │  Task        │  │   Agentic    │  │   Tool       │  │   Stream     │    │    │
│  │  │  Consumer    │  │   Loop       │  │   Executor   │  │   Publisher  │    │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                         │                                            │
│                                         ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                        Sandbox Container (Docker-in-Docker)                  │    │
│  │                              Isolated Execution                              │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

------

## Project Structure

```
claude-code-platform/
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
├── README.md
│
├── frontend/                    # Next.js Application
│   ├── Dockerfile
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   └── tasks/
│   │   │       └── [taskId]/
│   │   │           └── page.tsx
│   │   ├── components/
│   │   │   ├── TaskInput.tsx
│   │   │   ├── StreamingTerminal.tsx
│   │   │   ├── FileBrowser.tsx
│   │   │   └── ResultsViewer.tsx
│   │   ├── hooks/
│   │   │   ├── useTaskStream.ts
│   │   │   └── useWebSocket.ts
│   │   └── lib/
│   │       └── api.ts
│   └── public/
│
├── api/                         # FastAPI Backend
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── src/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routers/
│   │   │   ├── tasks.py
│   │   │   ├── files.py
│   │   │   └── websocket.py
│   │   ├── models/
│   │   │   ├── task.py
│   │   │   └── schemas.py
│   │   ├── services/
│   │   │   ├── queue.py
│   │   │   ├── storage.py
│   │   │   └── stream.py
│   │   └── middleware/
│   │       ├── auth.py
│   │       └── rate_limit.py
│   └── tests/
│
├── worker/                      # Agent Worker
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── src/
│   │   ├── main.py
│   │   ├── agent/
│   │   │   ├── loop.py
│   │   │   ├── tools.py
│   │   │   └── prompts.py
│   │   ├── sandbox/
│   │   │   ├── manager.py
│   │   │   ├── executor.py
│   │   │   └── security.py
│   │   └── streaming/
│   │       └── publisher.py
│   └── tests/
│
├── sandbox-base/                # Base image for sandboxes
│   ├── Dockerfile
│   └── requirements.txt
│
└── infrastructure/
    ├── nginx/
    │   └── nginx.conf
    └── scripts/
        ├── init-minio.sh
        └── init-db.sql
```

------

## Phase 1: Infrastructure Setup

### docker-compose.yml

yaml

```yaml
version: '3.8'

services:
  # ===================
  # CORE INFRASTRUCTURE
  # ===================
  
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:-minioadmin}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-minioadmin}
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"   # API
      - "9001:9001"   # Console
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
      timeout: 5s
      retries: 3

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-claude}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-claude}
      POSTGRES_DB: ${POSTGRES_DB:-claude_code}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infrastructure/scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U claude"]
      interval: 5s
      timeout: 3s
      retries: 5

  # ===================
  # APPLICATION SERVICES
  # ===================

  api:
    build:
      context: ./api
      dockerfile: Dockerfile
    environment:
      - REDIS_URL=redis://redis:6379
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=${MINIO_ROOT_USER:-minioadmin}
      - MINIO_SECRET_KEY=${MINIO_ROOT_PASSWORD:-minioadmin}
      - DATABASE_URL=postgresql://${POSTGRES_USER:-claude}:${POSTGRES_PASSWORD:-claude}@postgres:5432/${POSTGRES_DB:-claude_code}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    ports:
      - "8000:8000"
    depends_on:
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
      postgres:
        condition: service_healthy
    volumes:
      - ./api/src:/app/src:ro  # Dev: hot reload

  worker:
    build:
      context: ./worker
      dockerfile: Dockerfile
    environment:
      - REDIS_URL=redis://redis:6379
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=${MINIO_ROOT_USER:-minioadmin}
      - MINIO_SECRET_KEY=${MINIO_ROOT_PASSWORD:-minioadmin}
      - DATABASE_URL=postgresql://${POSTGRES_USER:-claude}:${POSTGRES_PASSWORD:-claude}@postgres:5432/${POSTGRES_DB:-claude_code}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DOCKER_HOST=unix:///var/run/docker.sock
    depends_on:
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # Docker-in-Docker
      - worker_workspaces:/workspaces
    deploy:
      replicas: 2  # Scale workers

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_WS_URL=ws://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      - api

  # ===================
  # REVERSE PROXY
  # ===================

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./infrastructure/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api
      - frontend

volumes:
  redis_data:
  minio_data:
  postgres_data:
  worker_workspaces:
```

### infrastructure/scripts/init-db.sql

sql

```sql
-- Task tracking
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    task_type VARCHAR(100),
    input_prompt TEXT NOT NULL,
    result JSONB,
    workspace_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    token_usage JSONB,
    metadata JSONB DEFAULT '{}'
);

-- Task events for streaming history
CREATE TABLE IF NOT EXISTS task_events (
    id SERIAL PRIMARY KEY,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Output files
CREATE TABLE IF NOT EXISTS task_outputs (
    id SERIAL PRIMARY KEY,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    minio_bucket VARCHAR(100),
    minio_key VARCHAR(500),
    public_url VARCHAR(1000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_task_events_task_id ON task_events(task_id);
CREATE INDEX idx_task_outputs_task_id ON task_outputs(task_id);
```

------

## Phase 2: FastAPI Backend

### api/Dockerfile

dockerfile

~~~dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/

# Run with uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### api/requirements.txt
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6
websockets==12.0
redis==5.0.1
minio==7.2.3
sqlalchemy==2.0.25
asyncpg==0.29.0
psycopg2-binary==2.9.9
pydantic==2.5.3
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.26.0
~~~

### api/src/config.py

python

```python
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # API
    api_title: str = "Claude Code Platform"
    api_version: str = "1.0.0"
    debug: bool = False
    
    # Database
    database_url: str
    
    # Redis
    redis_url: str
    
    # MinIO
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str = "task-outputs"
    minio_secure: bool = False
    
    # Anthropic
    anthropic_api_key: str
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

### api/src/main.py

python

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.config import get_settings
from src.routers import tasks, files, websocket
from src.services.storage import init_minio
from src.services.queue import init_redis


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_redis()
    await init_minio()
    yield
    # Shutdown
    pass


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])


@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### api/src/models/schemas.py

python

```python
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from enum import Enum
import uuid


class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    CODE_GENERATION = "code_generation"
    DATA_ANALYSIS = "data_analysis"
    DOCUMENT_PROCESSING = "document_processing"
    VISION_TASK = "vision_task"
    CUSTOM = "custom"


class TaskCreate(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=50000)
    task_type: TaskType = TaskType.CUSTOM
    metadata: Optional[dict] = None


class TaskResponse(BaseModel):
    id: uuid.UUID
    status: TaskStatus
    task_type: TaskType
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[dict] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class TaskEvent(BaseModel):
    task_id: uuid.UUID
    event_type: str
    payload: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FileOutput(BaseModel):
    id: int
    task_id: uuid.UUID
    file_name: str
    file_size: int
    mime_type: str
    public_url: str
    created_at: datetime
```

### api/src/routers/tasks.py

python

```python
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List
import uuid

from src.models.schemas import TaskCreate, TaskResponse, TaskStatus
from src.services.queue import enqueue_task
from src.services.database import get_db, create_task, get_task, list_tasks

router = APIRouter()


@router.post("/", response_model=TaskResponse)
async def create_new_task(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """Create a new task and queue it for processing"""
    
    # Create task in database
    task = await create_task(db, task_data)
    
    # Queue for worker processing
    await enqueue_task(str(task.id), task_data.prompt, task_data.task_type)
    
    return task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: uuid.UUID,
    db = Depends(get_db)
):
    """Get task status and results"""
    
    task = await get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@router.get("/", response_model=List[TaskResponse])
async def list_user_tasks(
    skip: int = 0,
    limit: int = 20,
    status: TaskStatus = None,
    db = Depends(get_db)
):
    """List all tasks for the current user"""
    
    tasks = await list_tasks(db, skip=skip, limit=limit, status=status)
    return tasks


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: uuid.UUID,
    db = Depends(get_db)
):
    """Cancel a running task"""
    
    task = await get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status not in [TaskStatus.PENDING, TaskStatus.QUEUED, TaskStatus.RUNNING]:
        raise HTTPException(status_code=400, detail="Task cannot be cancelled")
    
    # Publish cancel signal
    from src.services.queue import publish_cancel
    await publish_cancel(str(task_id))
    
    return {"status": "cancellation_requested"}
```

### api/src/routers/websocket.py

python

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio
import json

from src.services.stream import subscribe_to_task

router = APIRouter()

# Active connections per task
connections: Dict[str, Set[WebSocket]] = {}


@router.websocket("/tasks/{task_id}")
async def task_stream(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for streaming task updates"""
    
    await websocket.accept()
    
    # Track connection
    if task_id not in connections:
        connections[task_id] = set()
    connections[task_id].add(websocket)
    
    try:
        # Subscribe to Redis pub/sub for this task
        async for event in subscribe_to_task(task_id):
            await websocket.send_json(event)
            
            # Check for terminal events
            if event.get("type") in ["completed", "failed", "cancelled"]:
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        connections[task_id].discard(websocket)
        if not connections[task_id]:
            del connections[task_id]
```

### api/src/services/queue.py

python

```python
import redis.asyncio as redis
import json
from typing import AsyncGenerator

from src.config import get_settings

settings = get_settings()
redis_client: redis.Redis = None


async def init_redis():
    global redis_client
    redis_client = redis.from_url(settings.redis_url)


async def enqueue_task(task_id: str, prompt: str, task_type: str):
    """Add task to the processing queue"""
    
    task_data = {
        "task_id": task_id,
        "prompt": prompt,
        "task_type": task_type
    }
    
    await redis_client.lpush("task_queue", json.dumps(task_data))
    await redis_client.publish(f"task:{task_id}", json.dumps({
        "type": "queued",
        "task_id": task_id
    }))


async def publish_cancel(task_id: str):
    """Publish cancellation signal"""
    await redis_client.publish(f"task:{task_id}:control", json.dumps({
        "type": "cancel"
    }))


async def publish_event(task_id: str, event: dict):
    """Publish event to task channel"""
    await redis_client.publish(f"task:{task_id}", json.dumps(event))
```

### api/src/services/stream.py

python

```python
import redis.asyncio as redis
import json
from typing import AsyncGenerator

from src.config import get_settings

settings = get_settings()


async def subscribe_to_task(task_id: str) -> AsyncGenerator[dict, None]:
    """Subscribe to task events via Redis pub/sub"""
    
    client = redis.from_url(settings.redis_url)
    pubsub = client.pubsub()
    
    await pubsub.subscribe(f"task:{task_id}")
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                yield data
    finally:
        await pubsub.unsubscribe(f"task:{task_id}")
        await client.close()
```

### api/src/services/storage.py

python

```python
from minio import Minio
from minio.error import S3Error
import io
from datetime import timedelta

from src.config import get_settings

settings = get_settings()
minio_client: Minio = None


async def init_minio():
    global minio_client
    
    minio_client = Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure
    )
    
    # Ensure bucket exists
    if not minio_client.bucket_exists(settings.minio_bucket):
        minio_client.make_bucket(settings.minio_bucket)
        
        # Set public read policy for outputs
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{settings.minio_bucket}/public/*"]
                }
            ]
        }
        minio_client.set_bucket_policy(settings.minio_bucket, json.dumps(policy))


async def upload_file(
    task_id: str,
    file_name: str,
    content: bytes,
    content_type: str = "application/octet-stream"
) -> str:
    """Upload file to MinIO and return public URL"""
    
    object_name = f"public/{task_id}/{file_name}"
    
    minio_client.put_object(
        settings.minio_bucket,
        object_name,
        io.BytesIO(content),
        length=len(content),
        content_type=content_type
    )
    
    # Generate public URL
    url = f"http://{settings.minio_endpoint}/{settings.minio_bucket}/{object_name}"
    
    return url


async def get_presigned_url(task_id: str, file_name: str) -> str:
    """Generate presigned URL for private files"""
    
    object_name = f"private/{task_id}/{file_name}"
    
    url = minio_client.presigned_get_object(
        settings.minio_bucket,
        object_name,
        expires=timedelta(hours=1)
    )
    
    return url
```

------

## Phase 3: Worker Service

### worker/Dockerfile

dockerfile

~~~dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Docker CLI for managing sandbox containers
RUN apt-get update && apt-get install -y \
    docker.io \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

CMD ["python", "-m", "src.main"]
```

### worker/requirements.txt
```
anthropic==0.18.1
redis==5.0.1
minio==7.2.3
sqlalchemy==2.0.25
asyncpg==0.29.0
psycopg2-binary==2.9.9
docker==7.0.0
pydantic==2.5.3
pydantic-settings==2.1.0
~~~

### worker/src/main.py

python

```python
import asyncio
import json
import signal
from typing import Optional

import redis.asyncio as redis

from src.config import get_settings
from src.agent.loop import AgentLoop
from src.sandbox.manager import SandboxManager
from src.streaming.publisher import EventPublisher

settings = get_settings()


class Worker:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.sandbox_manager = SandboxManager()
        self.running = True
        self.current_task: Optional[str] = None
        
    async def start(self):
        """Main worker loop"""
        
        self.redis = redis.from_url(settings.redis_url)
        
        print("Worker started, waiting for tasks...")
        
        while self.running:
            try:
                # Block waiting for task (with timeout for graceful shutdown)
                result = await self.redis.brpop("task_queue", timeout=5)
                
                if result:
                    _, task_data = result
                    task = json.loads(task_data)
                    await self.process_task(task)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error processing task: {e}")
                await asyncio.sleep(1)
    
    async def process_task(self, task: dict):
        """Process a single task"""
        
        task_id = task["task_id"]
        prompt = task["prompt"]
        task_type = task["task_type"]
        
        self.current_task = task_id
        publisher = EventPublisher(self.redis, task_id)
        
        try:
            # Notify task started
            await publisher.publish("started", {"task_id": task_id})
            
            # Create sandbox
            sandbox = await self.sandbox_manager.create_sandbox(task_id)
            
            # Subscribe to control channel for cancellation
            cancel_task = asyncio.create_task(
                self._watch_for_cancel(task_id)
            )
            
            # Run agent loop
            agent = AgentLoop(
                sandbox=sandbox,
                publisher=publisher,
                task_type=task_type
            )
            
            result = await agent.run(prompt)
            
            # Cancel the cancel watcher
            cancel_task.cancel()
            
            # Upload outputs to MinIO
            outputs = await self._upload_outputs(task_id, sandbox)
            
            # Publish completion
            await publisher.publish("completed", {
                "task_id": task_id,
                "result": result,
                "outputs": outputs
            })
            
        except asyncio.CancelledError:
            await publisher.publish("cancelled", {"task_id": task_id})
        except Exception as e:
            await publisher.publish("failed", {
                "task_id": task_id,
                "error": str(e)
            })
        finally:
            # Cleanup sandbox
            await self.sandbox_manager.destroy_sandbox(task_id)
            self.current_task = None
    
    async def _watch_for_cancel(self, task_id: str):
        """Watch for cancellation signals"""
        
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(f"task:{task_id}:control")
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                if data.get("type") == "cancel":
                    raise asyncio.CancelledError()
    
    async def _upload_outputs(self, task_id: str, sandbox) -> list:
        """Upload sandbox outputs to MinIO"""
        
        from src.services.storage import upload_output_files
        return await upload_output_files(task_id, sandbox.workspace_path)
    
    def shutdown(self):
        self.running = False


async def main():
    worker = Worker()
    
    # Handle shutdown signals
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, worker.shutdown)
    
    await worker.start()


if __name__ == "__main__":
    asyncio.run(main())
```

### worker/src/agent/loop.py

python

```python
import anthropic
from typing import Optional, Any
import asyncio

from src.agent.tools import TOOLS, execute_tool
from src.agent.prompts import build_system_prompt
from src.streaming.publisher import EventPublisher


class AgentLoop:
    def __init__(
        self,
        sandbox,
        publisher: EventPublisher,
        task_type: str,
        max_iterations: int = 100,
        model: str = "claude-sonnet-4-20250514"
    ):
        self.client = anthropic.Anthropic()
        self.sandbox = sandbox
        self.publisher = publisher
        self.task_type = task_type
        self.max_iterations = max_iterations
        self.model = model
        self.conversation_history = []
        
    async def run(self, user_prompt: str) -> dict:
        """Execute the agentic loop"""
        
        system_prompt = build_system_prompt(self.task_type, self.sandbox.workspace_path)
        
        self.conversation_history.append({
            "role": "user",
            "content": user_prompt
        })
        
        total_tokens = {"input": 0, "output": 0}
        
        for iteration in range(self.max_iterations):
            # Publish thinking event
            await self.publisher.publish("thinking", {
                "iteration": iteration + 1,
                "max_iterations": self.max_iterations
            })
            
            # Call Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8096,
                system=system_prompt,
                tools=TOOLS,
                messages=self.conversation_history
            )
            
            # Track token usage
            total_tokens["input"] += response.usage.input_tokens
            total_tokens["output"] += response.usage.output_tokens
            
            # Process response content
            assistant_content = []
            tool_calls = []
            
            for block in response.content:
                if block.type == "text":
                    assistant_content.append(block)
                    # Stream text to user
                    await self.publisher.publish("assistant_text", {
                        "text": block.text
                    })
                elif block.type == "tool_use":
                    assistant_content.append(block)
                    tool_calls.append(block)
            
            # Add assistant message to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_content
            })
            
            # Check if we're done
            if response.stop_reason == "end_turn":
                return {
                    "status": "completed",
                    "final_response": self._extract_text(response),
                    "iterations": iteration + 1,
                    "token_usage": total_tokens
                }
            
            # Execute tool calls
            if tool_calls:
                tool_results = await self._execute_tools(tool_calls)
                
                self.conversation_history.append({
                    "role": "user",
                    "content": tool_results
                })
        
        return {
            "status": "max_iterations_reached",
            "iterations": self.max_iterations,
            "token_usage": total_tokens
        }
    
    async def _execute_tools(self, tool_calls: list) -> list:
        """Execute tool calls and return results"""
        
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.name
            tool_input = tool_call.input
            tool_id = tool_call.id
            
            # Publish tool execution event
            await self.publisher.publish("tool_start", {
                "tool": tool_name,
                "input": tool_input
            })
            
            # Execute tool
            output = await execute_tool(
                self.sandbox,
                tool_name,
                tool_input
            )
            
            # Publish tool result
            await self.publisher.publish("tool_result", {
                "tool": tool_name,
                "output": output[:2000]  # Truncate for streaming
            })
            
            results.append({
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": output
            })
        
        return results
    
    def _extract_text(self, response) -> str:
        for block in response.content:
            if hasattr(block, 'text'):
                return block.text
        return ""
```

### worker/src/agent/tools.py

python

```python
from typing import Any
import asyncio

TOOLS = [
    {
        "name": "bash",
        "description": "Execute a bash command in the sandboxed environment. Use for running scripts, installing packages, and system operations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 120)",
                    "default": 120
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "file_read",
        "description": "Read the contents of a file. Can optionally read specific line ranges.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read"
                },
                "start_line": {
                    "type": "integer",
                    "description": "Starting line number (1-indexed)"
                },
                "end_line": {
                    "type": "integer",
                    "description": "Ending line number (inclusive)"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "file_write",
        "description": "Create or overwrite a file with the given content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to write"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                }
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "file_edit",
        "description": "Edit a file by replacing a specific string with another. The old_text must match exactly.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to edit"
                },
                "old_text": {
                    "type": "string",
                    "description": "Text to find and replace (must be unique in file)"
                },
                "new_text": {
                    "type": "string",
                    "description": "Text to replace with"
                }
            },
            "required": ["path", "old_text", "new_text"]
        }
    },
    {
        "name": "list_directory",
        "description": "List files and directories at a given path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to list"
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Whether to list recursively",
                    "default": False
                }
            },
            "required": ["path"]
        }
    }
]


async def execute_tool(sandbox, tool_name: str, params: dict) -> str:
    """Route and execute tool calls"""
    
    handlers = {
        "bash": sandbox.execute_bash,
        "file_read": sandbox.read_file,
        "file_write": sandbox.write_file,
        "file_edit": sandbox.edit_file,
        "list_directory": sandbox.list_directory,
    }
    
    handler = handlers.get(tool_name)
    if not handler:
        return f"Unknown tool: {tool_name}"
    
    try:
        # Run in thread pool for blocking operations
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: handler(**params)
        )
        return result
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"
```

### worker/src/sandbox/manager.py

python

```python
import docker
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Optional

from src.sandbox.executor import SandboxExecutor


class SandboxManager:
    """Manages Docker sandbox containers"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.active_sandboxes: Dict[str, SandboxExecutor] = {}
        self.base_workspace = Path("/workspaces")
        self.base_workspace.mkdir(exist_ok=True)
        
    async def create_sandbox(self, task_id: str) -> SandboxExecutor:
        """Create a new sandbox for a task"""
        
        # Create workspace directory
        workspace_path = self.base_workspace / task_id
        workspace_path.mkdir(exist_ok=True)
        
        # Start container
        container = self.docker_client.containers.run(
            "claude-sandbox:latest",  # Our custom base image
            command="tail -f /dev/null",  # Keep alive
            detach=True,
            name=f"sandbox-{task_id}",
            working_dir="/workspace",
            volumes={
                str(workspace_path): {"bind": "/workspace", "mode": "rw"}
            },
            mem_limit="4g",
            cpu_period=100000,
            cpu_quota=100000,  # 1 CPU
            network_mode="bridge",
            # Security options
            security_opt=["no-new-privileges"],
            cap_drop=["ALL"],
            cap_add=["CHOWN", "SETUID", "SETGID"],
        )
        
        executor = SandboxExecutor(
            container=container,
            workspace_path=workspace_path
        )
        
        self.active_sandboxes[task_id] = executor
        return executor
    
    async def destroy_sandbox(self, task_id: str):
        """Destroy a sandbox and clean up"""
        
        executor = self.active_sandboxes.pop(task_id, None)
        
        if executor:
            try:
                executor.container.stop(timeout=5)
                executor.container.remove(force=True)
            except Exception as e:
                print(f"Error destroying container: {e}")
        
        # Optionally clean up workspace (or keep for debugging)
        # shutil.rmtree(self.base_workspace / task_id, ignore_errors=True)
```

### worker/src/sandbox/executor.py

python

```python
from pathlib import Path
from typing import Optional
import re


class SandboxExecutor:
    """Executes commands in a sandbox container"""
    
    def __init__(self, container, workspace_path: Path):
        self.container = container
        self.workspace_path = workspace_path
        
    def execute_bash(self, command: str, timeout: int = 120) -> str:
        """Execute bash command in container"""
        
        # Security validation
        if self._is_dangerous(command):
            return "Command blocked for security reasons"
        
        try:
            exit_code, output = self.container.exec_run(
                f"bash -c {repr(command)}",
                workdir="/workspace",
                timeout=timeout
            )
            
            output_text = output.decode("utf-8", errors="replace")
            
            # Truncate very long outputs
            if len(output_text) > 50000:
                output_text = output_text[:25000] + "\n...[truncated]...\n" + output_text[-25000:]
            
            return f"Exit code: {exit_code}\n{output_text}"
            
        except Exception as e:
            return f"Execution error: {str(e)}"
    
    def read_file(self, path: str, start_line: int = None, end_line: int = None) -> str:
        """Read file contents"""
        
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            return f"File not found: {path}"
        
        if not file_path.is_file():
            return f"Not a file: {path}"
        
        try:
            content = file_path.read_text(errors="replace")
            
            # Handle line ranges
            if start_line is not None:
                lines = content.split("\n")
                start_idx = max(0, start_line - 1)
                end_idx = end_line if end_line else len(lines)
                
                selected_lines = lines[start_idx:end_idx]
                content = "\n".join(
                    f"{i+start_line}: {line}" 
                    for i, line in enumerate(selected_lines)
                )
            
            return content
            
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def write_file(self, path: str, content: str) -> str:
        """Write content to file"""
        
        file_path = self._resolve_path(path)
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            return f"Successfully wrote {len(content)} bytes to {path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"
    
    def edit_file(self, path: str, old_text: str, new_text: str) -> str:
        """Edit file by replacing text"""
        
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            return f"File not found: {path}"
        
        try:
            content = file_path.read_text()
            
            if old_text not in content:
                return f"Text not found in file. File content preview:\n{content[:500]}"
            
            # Ensure unique match
            if content.count(old_text) > 1:
                return f"Text appears {content.count(old_text)} times. Please provide more unique text."
            
            new_content = content.replace(old_text, new_text, 1)
            file_path.write_text(new_content)
            
            return f"Successfully edited {path}"
            
        except Exception as e:
            return f"Error editing file: {str(e)}"
    
    def list_directory(self, path: str, recursive: bool = False) -> str:
        """List directory contents"""
        
        dir_path = self._resolve_path(path)
        
        if not dir_path.exists():
            return f"Directory not found: {path}"
        
        if not dir_path.is_dir():
            return f"Not a directory: {path}"
        
        try:
            if recursive:
                items = list(dir_path.rglob("*"))
            else:
                items = list(dir_path.iterdir())
            
            # Format output
            output = []
            for item in sorted(items)[:500]:  # Limit to 500 items
                rel_path = item.relative_to(dir_path)
                prefix = "📁 " if item.is_dir() else "📄 "
                size = f" ({item.stat().st_size} bytes)" if item.is_file() else ""
                output.append(f"{prefix}{rel_path}{size}")
            
            return "\n".join(output) if output else "(empty directory)"
            
        except Exception as e:
            return f"Error listing directory: {str(e)}"
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve path relative to workspace"""
        
        # Ensure path stays within workspace
        if path.startswith("/"):
            path = path.lstrip("/")
        
        resolved = (self.workspace_path / path).resolve()
        
        # Security: prevent path traversal
        if not str(resolved).startswith(str(self.workspace_path.resolve())):
            raise ValueError("Path escapes workspace boundary")
        
        return resolved
    
    def _is_dangerous(self, command: str) -> bool:
        """Check for dangerous commands"""
        
        dangerous_patterns = [
            r"rm\s+-rf\s+/(?!workspace)",  # rm -rf outside workspace
            r"dd\s+if=.*of=/dev/",         # Writing to devices
            r"mkfs\.",                      # Formatting filesystems
            r":\(\)\s*\{\s*:\|:&\s*\}\s*;", # Fork bomb
            r">\s*/dev/sd",                 # Writing to disks
            r"curl.*\|.*bash",              # Piping to bash
            r"wget.*\|.*bash",              # Piping to bash
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        
        return False
```

### worker/src/streaming/publisher.py

python

```python
import json
from datetime import datetime
from typing import Any

import redis.asyncio as redis


class EventPublisher:
    """Publishes task events to Redis for streaming"""
    
    def __init__(self, redis_client: redis.Redis, task_id: str):
        self.redis = redis_client
        self.task_id = task_id
        self.channel = f"task:{task_id}"
        
    async def publish(self, event_type: str, payload: dict):
        """Publish an event"""
        
        event = {
            "type": event_type,
            "task_id": self.task_id,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": payload
        }
        
        await self.redis.publish(self.channel, json.dumps(event))
        
        # Also store in a list for replay
        await self.redis.lpush(
            f"task:{self.task_id}:events",
            json.dumps(event)
        )
        await self.redis.expire(f"task:{self.task_id}:events", 86400)  # 24 hours
```

------

## Phase 4: Frontend (Next.js)

### frontend/Dockerfile

dockerfile

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
```

### frontend/package.json

json

```json
{
  "name": "claude-code-frontend",
  "version": "1.0.0",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "14.1.0",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "@tanstack/react-query": "5.17.19",
    "zustand": "4.5.0",
    "lucide-react": "0.312.0",
    "clsx": "2.1.0",
    "tailwind-merge": "2.2.0"
  },
  "devDependencies": {
    "@types/node": "20.11.5",
    "@types/react": "18.2.48",
    "autoprefixer": "10.4.17",
    "postcss": "8.4.33",
    "tailwindcss": "3.4.1",
    "typescript": "5.3.3"
  }
}
```

### frontend/src/app/page.tsx

tsx

```tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { TaskInput } from '@/components/TaskInput';
import { TaskList } from '@/components/TaskList';
import { api } from '@/lib/api';

export default function Home() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (prompt: string, taskType: string) => {
    setIsSubmitting(true);
    try {
      const task = await api.createTask({ prompt, task_type: taskType });
      router.push(`/tasks/${task.id}`);
    } catch (error) {
      console.error('Failed to create task:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-950 text-gray-100">
      <div className="max-w-6xl mx-auto px-4 py-12">
        <header className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4">Claude Code Platform</h1>
          <p className="text-gray-400 text-lg">
            Describe complex tasks and let AI handle the execution
          </p>
        </header>

        <TaskInput onSubmit={handleSubmit} isSubmitting={isSubmitting} />
        
        <div className="mt-16">
          <h2 className="text-2xl font-semibold mb-6">Recent Tasks</h2>
          <TaskList />
        </div>
      </div>
    </main>
  );
}
```

### frontend/src/app/tasks/[taskId]/page.tsx

tsx

```tsx
'use client';

import { useParams } from 'next/navigation';
import { useTaskStream } from '@/hooks/useTaskStream';
import { StreamingTerminal } from '@/components/StreamingTerminal';
import { FileBrowser } from '@/components/FileBrowser';
import { ResultsViewer } from '@/components/ResultsViewer';
import { TaskHeader } from '@/components/TaskHeader';

export default function TaskPage() {
  const { taskId } = useParams<{ taskId: string }>();
  const { events, status, result, outputs } = useTaskStream(taskId);

  return (
    <main className="min-h-screen bg-gray-950 text-gray-100">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <TaskHeader taskId={taskId} status={status} />
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8">
          {/* Main Terminal */}
          <div className="lg:col-span-2">
            <StreamingTerminal events={events} />
          </div>
          
          {/* Sidebar */}
          <div className="space-y-6">
            <FileBrowser outputs={outputs} />
            {result && <ResultsViewer result={result} />}
          </div>
        </div>
      </div>
    </main>
  );
}
```

### frontend/src/hooks/useTaskStream.ts

tsx

```tsx
import { useState, useEffect, useCallback, useRef } from 'react';

interface TaskEvent {
  type: string;
  task_id: string;
  timestamp: string;
  payload: any;
}

interface TaskOutput {
  file_name: string;
  public_url: string;
  mime_type: string;
}

export function useTaskStream(taskId: string) {
  const [events, setEvents] = useState<TaskEvent[]>([]);
  const [status, setStatus] = useState<string>('connecting');
  const [result, setResult] = useState<any>(null);
  const [outputs, setOutputs] = useState<TaskOutput[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);

  const connect = useCallback(() => {
    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/ws/tasks/${taskId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus('connected');
      reconnectAttempts.current = 0;
    };

    ws.onmessage = (event) => {
      const data: TaskEvent = JSON.parse(event.data);
      
      setEvents((prev) => [...prev, data]);

      // Update status based on event type
      switch (data.type) {
        case 'started':
          setStatus('running');
          break;
        case 'completed':
          setStatus('completed');
          setResult(data.payload.result);
          setOutputs(data.payload.outputs || []);
          break;
        case 'failed':
          setStatus('failed');
          break;
        case 'cancelled':
          setStatus('cancelled');
          break;
      }
    };

    ws.onerror = () => {
      setStatus('error');
    };

    ws.onclose = () => {
      // Attempt reconnect if not terminal state
      if (!['completed', 'failed', 'cancelled'].includes(status)) {
        if (reconnectAttempts.current < 5) {
          reconnectAttempts.current++;
          setTimeout(connect, 2000 * reconnectAttempts.current);
        }
      }
    };
  }, [taskId, status]);

  useEffect(() => {
    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { events, status, result, outputs };
}
```

### frontend/src/components/StreamingTerminal.tsx

tsx

```tsx
'use client';

import { useEffect, useRef } from 'react';
import { Terminal, Play, Check, X, Loader2 } from 'lucide-react';
import clsx from 'clsx';

interface TaskEvent {
  type: string;
  timestamp: string;
  payload: any;
}

interface StreamingTerminalProps {
  events: TaskEvent[];
}

export function StreamingTerminal({ events }: StreamingTerminalProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [events]);

  const renderEvent = (event: TaskEvent, index: number) => {
    switch (event.type) {
      case 'thinking':
        return (
          <div key={index} className="flex items-center gap-2 text-blue-400 py-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Thinking... (iteration {event.payload.iteration})</span>
          </div>
        );

      case 'assistant_text':
        return (
          <div key={index} className="py-2 text-gray-100 whitespace-pre-wrap">
            {event.payload.text}
          </div>
        );

      case 'tool_start':
        return (
          <div key={index} className="mt-4 border-l-2 border-yellow-500 pl-4">
            <div className="flex items-center gap-2 text-yellow-400">
              <Play className="w-4 h-4" />
              <span className="font-mono">{event.payload.tool}</span>
            </div>
            <pre className="mt-2 text-sm text-gray-400 overflow-x-auto">
              {JSON.stringify(event.payload.input, null, 2)}
            </pre>
          </div>
        );

      case 'tool_result':
        return (
          <div key={index} className="border-l-2 border-green-500 pl-4 mb-4">
            <div className="flex items-center gap-2 text-green-400">
              <Check className="w-4 h-4" />
              <span>Result</span>
            </div>
            <pre className="mt-2 text-sm text-gray-300 overflow-x-auto max-h-64 overflow-y-auto bg-gray-900 p-2 rounded">
              {event.payload.output}
            </pre>
          </div>
        );

      case 'completed':
        return (
          <div key={index} className="mt-6 p-4 bg-green-900/30 border border-green-700 rounded-lg">
            <div className="flex items-center gap-2 text-green-400">
              <Check className="w-5 h-5" />
              <span className="font-semibold">Task Completed</span>
            </div>
          </div>
        );

      case 'failed':
        return (
          <div key={index} className="mt-6 p-4 bg-red-900/30 border border-red-700 rounded-lg">
            <div className="flex items-center gap-2 text-red-400">
              <X className="w-5 h-5" />
              <span className="font-semibold">Task Failed</span>
            </div>
            <p className="mt-2 text-red-300">{event.payload.error}</p>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 bg-gray-800 border-b border-gray-700">
        <Terminal className="w-5 h-5 text-gray-400" />
        <span className="font-medium">Execution Log</span>
      </div>
      
      <div
        ref={containerRef}
        className="p-4 h-[600px] overflow-y-auto font-mono text-sm"
      >
        {events.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            Waiting for task to start...
          </div>
        ) : (
          events.map(renderEvent)
        )}
      </div>
    </div>
  );
}
```

### frontend/src/components/FileBrowser.tsx

tsx

```tsx
'use client';

import { FileText, Download, ExternalLink } from 'lucide-react';

interface FileOutput {
  file_name: string;
  public_url: string;
  mime_type: string;
}

interface FileBrowserProps {
  outputs: FileOutput[];
}

export function FileBrowser({ outputs }: FileBrowserProps) {
  if (outputs.length === 0) {
    return (
      <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
        <h3 className="font-medium mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5" />
          Output Files
        </h3>
        <p className="text-gray-500 text-sm">No files generated yet</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
      <h3 className="font-medium mb-4 flex items-center gap-2">
        <FileText className="w-5 h-5" />
        Output Files ({outputs.length})
      </h3>
      
      <div className="space-y-2">
        {outputs.map((file, index) => (
          <div
            key={index}
            className="flex items-center justify-between p-3 bg-gray-800 rounded-lg hover:bg-gray-750 transition-colors"
          >
            <div className="flex items-center gap-3 min-w-0">
              <FileText className="w-4 h-4 text-gray-400 flex-shrink-0" />
              <span className="text-sm truncate">{file.file_name}</span>
            </div>
            
            <div className="flex items-center gap-2">
              
                href={file.public_url}
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 hover:bg-gray-700 rounded transition-colors"
                title="Open in new tab"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
              
                href={file.public_url}
                download={file.file_name}
                className="p-2 hover:bg-gray-700 rounded transition-colors"
                title="Download"
              >
                <Download className="w-4 h-4" />
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### frontend/src/components/TaskInput.tsx

tsx

```tsx
'use client';

import { useState } from 'react';
import { Send, Loader2 } from 'lucide-react';

interface TaskInputProps {
  onSubmit: (prompt: string, taskType: string) => Promise<void>;
  isSubmitting: boolean;
}

const TASK_TYPES = [
  { value: 'data_analysis', label: 'Data Analysis' },
  { value: 'code_generation', label: 'Code Generation' },
  { value: 'document_processing', label: 'Document Processing' },
  { value: 'vision_task', label: 'Vision Task' },
  { value: 'custom', label: 'Custom' },
];

export function TaskInput({ onSubmit, isSubmitting }: TaskInputProps) {
  const [prompt, setPrompt] = useState('');
  const [taskType, setTaskType] = useState('custom');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isSubmitting) return;
    await onSubmit(prompt, taskType);
  };

  return (
    <form onSubmit={handleSubmit} className="bg-gray-900 rounded-xl p-6 border border-gray-800">
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Task Type
        </label>
        <select
          value={taskType}
          onChange={(e) => setTaskType(e.target.value)}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {TASK_TYPES.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Describe your task
        </label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="e.g., Analyze the CSV file I uploaded and create a visualization dashboard showing sales trends..."
          rows={6}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
        />
      </div>

      <button
        type="submit"
        disabled={!prompt.trim() || isSubmitting}
        className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-medium py-3 px-6 rounded-lg transition-colors"
      >
        {isSubmitting ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Creating Task...
          </>
        ) : (
          <>
            <Send className="w-5 h-5" />
            Start Task
          </>
        )}
      </button>
    </form>
  );
}
```

### frontend/src/lib/api.ts

tsx

```tsx
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface CreateTaskParams {
  prompt: string;
  task_type: string;
  metadata?: Record<string, any>;
}

interface Task {
  id: string;
  status: string;
  task_type: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  result?: any;
  error_message?: string;
}

export const api = {
  async createTask(params: CreateTaskParams): Promise<Task> {
    const response = await fetch(`${API_URL}/api/tasks/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      throw new Error('Failed to create task');
    }

    return response.json();
  },

  async getTask(taskId: string): Promise<Task> {
    const response = await fetch(`${API_URL}/api/tasks/${taskId}`);

    if (!response.ok) {
      throw new Error('Failed to get task');
    }

    return response.json();
  },

  async listTasks(params?: {
    skip?: number;
    limit?: number;
    status?: string;
  }): Promise<Task[]> {
    const searchParams = new URLSearchParams();
    if (params?.skip) searchParams.set('skip', String(params.skip));
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.status) searchParams.set('status', params.status);

    const response = await fetch(`${API_URL}/api/tasks/?${searchParams}`);

    if (!response.ok) {
      throw new Error('Failed to list tasks');
    }

    return response.json();
  },

  async cancelTask(taskId: string): Promise<void> {
    const response = await fetch(`${API_URL}/api/tasks/${taskId}/cancel`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error('Failed to cancel task');
    }
  },
};
```

------

## Phase 5: Sandbox Base Image

### sandbox-base/Dockerfile

dockerfile

~~~dockerfile
FROM python:3.11-slim

# Install common tools and languages
RUN apt-get update && apt-get install -y \
    # Build tools
    build-essential \
    gcc \
    g++ \
    make \
    cmake \
    # Version control
    git \
    # Networking
    curl \
    wget \
    # Utilities
    vim \
    less \
    jq \
    tree \
    zip \
    unzip \
    # Image processing
    imagemagick \
    libmagickwand-dev \
    # Node.js
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages commonly needed
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Create non-root user
RUN useradd -m -s /bin/bash agent
USER agent

WORKDIR /workspace
```

### sandbox-base/requirements.txt
```
# Data Science
pandas>=2.0.0
numpy>=1.24.0
scipy>=1.10.0
scikit-learn>=1.3.0
matplotlib>=3.7.0
seaborn>=0.12.0
plotly>=5.15.0

# Data Processing
openpyxl>=3.1.0
xlrd>=2.0.0
python-docx>=0.8.11
PyPDF2>=3.0.0
beautifulsoup4>=4.12.0
lxml>=4.9.0

# Web & API
requests>=2.31.0
httpx>=0.24.0
aiohttp>=3.8.0
fastapi>=0.100.0
flask>=2.3.0

# Database
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0

# Image Processing
pillow>=10.0.0
opencv-python-headless>=4.8.0

# Utilities
python-dotenv>=1.0.0
pyyaml>=6.0.0
tqdm>=4.65.0
rich>=13.5.0

# Jupyter (for notebook support)
jupyter>=1.0.0
ipykernel>=6.25.0
~~~

------

## Implementation Roadmap

```
PhaseDurationDeliverables
Phase 1: InfrastructureWeek 1Docker Compose, Redis, MinIO, Postgres running
Phase 2: APIWeek 2FastAPI with task CRUD, WebSocket streaming
Phase 3: WorkerWeek 3-4Agentic loop, sandbox execution, tool implementation
Phase 4: FrontendWeek 4-5Next.js app with streaming terminal, file browser
Phase 5: IntegrationWeek 5-6End-to-end testing, error handling, polish
Phase 6: ProductionWeek 6-7Security hardening, monitoring, deployment
```

------

## Getting Started Commands

bash

```bash
# 1. Clone and setup
git clone <your-repo>
cd claude-code-platform

# 2. Create environment file
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# 3. Build sandbox base image
docker build -t claude-sandbox:latest ./sandbox-base

# 4. Start infrastructure
docker-compose up -d redis minio postgres

# 5. Initialize MinIO buckets
docker-compose exec minio mc alias set local http://localhost:9000 minioadmin minioadmin
docker-compose exec minio mc mb local/task-outputs

# 6. Start all services
docker-compose up -d

# 7. View logs
docker-compose logs -f worker

# 8. Open frontend
open http://localhost:3000
```





Reference:

There is a similar implemenation - https://github.com/bitswired/demos/tree/main/projects/agentic-loop



Claude Codebox: https://www.reddit.com/r/ClaudeAI/comments/1l56jrs/i_made_claudebox_run_claude_code_without/



https://github.com/RchGrav/claudebox