# Multi-Engine Agent Execution Framework

> **Last Updated**: 2025-12-12
> **Status**: 🎨 Design Proposal
> **Purpose**: Support multiple execution engines (Native, Claude Code CLI, OpenAI, E2B) with unified MinIO integration

---

## 📋 Table of Contents

1. [Vision & Goals](#vision--goals)
2. [Architecture Overview](#architecture-overview)
3. [Execution Modes](#execution-modes)
4. [Detailed Design](#detailed-design)
5. [UI/UX Design](#uiux-design)
6. [Implementation Roadmap](#implementation-roadmap)
7. [Technical Challenges](#technical-challenges)
8. [Security Considerations](#security-considerations)
9. [Cost Analysis](#cost-analysis)
10. [Recommendations](#recommendations)

---

## Vision & Goals

### What We're Building

A **unified agent task execution platform** that allows users to choose their preferred execution engine while maintaining enterprise features:

- **Project-based file access** (MinIO organizational hierarchy)
- **Consistent audit logging** (PostgreSQL)
- **Multi-tenant isolation** (RBAC)
- **Interactive chat capabilities** (real-time streaming)
- **Session management** (resume, replay, fork)

### User Story

> "As a data analyst, I want to analyze sales data using my preferred AI tool (Claude Code, GPT-4, or our native agent), have an interactive conversation about the analysis, and automatically save results to my project's storage, all within a single interface."

### Success Criteria

- ✅ Support 3+ execution engines
- ✅ Seamless engine switching (same UI)
- ✅ Interactive chat for all engines
- ✅ <5s engine initialization time
- ✅ 100% MinIO integration (all engines)
- ✅ Zero manual file management for users

---

## Architecture Overview

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (React/Next.js)                        │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  AgentTaskCreator Component                                      │  │
│  │  ┌────────────┬──────────────┬──────────────┬──────────────┐    │  │
│  │  │  Engine:   │              │              │              │    │  │
│  │  │  [Native ▾]│  Claude Code │   OpenAI    │     E2B      │    │  │
│  │  └────────────┴──────────────┴──────────────┴──────────────┘    │  │
│  │                                                                   │  │
│  │  Mode: [ ] One-shot   [✓] Interactive Chat                       │  │
│  │  Project: [Construction-Intelligence ▾]                           │  │
│  │  Files: [Select from project...] [+]                             │  │
│  │  Task: "Analyze Q4 sales and create forecast charts"            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  InteractiveAgentChat Component                                  │  │
│  │                                                                   │  │
│  │  Agent: Analyzing sales data...                                  │  │
│  │  Agent: I found revenue data for Q4. Should I include Q3 for     │  │
│  │         comparison?                                               │  │
│  │                                                                   │  │
│  │  You:  [Yes, show both quarters                    ] [Send]      │  │
│  │                                                                   │  │
│  │  [ Pause ] [ Provide Context ] [ Cancel ] [ Download Results ]   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │ WebSocket (interactive) / REST (one-shot)
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       BACKEND (FastAPI)                                  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Agent Execution Router                                          │  │
│  │  • Route to appropriate engine based on user selection           │  │
│  │  • Manage WebSocket connections for interactive mode             │  │
│  │  • Handle session state and resumption                           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                 ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Execution Engine Abstraction Layer                              │  │
│  │                                                                   │  │
│  │  class AgentEngine(ABC):                                         │  │
│  │      @abstractmethod                                             │  │
│  │      async def execute(task, files, mode) -> Stream              │  │
│  │      async def chat(message) -> Stream                           │  │
│  │      async def stop() -> None                                    │  │
│  │                                                                   │  │
│  │  ┌──────────┬──────────────┬──────────────┬──────────────┐      │  │
│  │  │ Native   │ ClaudeCode   │   OpenAI     │     E2B      │      │  │
│  │  │ Engine   │   Engine     │   Engine     │   Engine     │      │  │
│  │  └──────────┴──────────────┴──────────────┴──────────────┘      │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                 ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  MinIO File Orchestrator                                         │  │
│  │  • Download files from project MinIO path                        │  │
│  │  • Prepare workspace for selected engine                         │  │
│  │  • Upload results to org hierarchy                               │  │
│  │  • Clean up temporary files                                      │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                ┌────────────────┼────────────────┬─────────────┐
                ▼                ▼                ▼             ▼
    ┌──────────────────┐  ┌──────────────┐  ┌──────────┐  ┌────────┐
    │  Native Agent    │  │ Claude Code  │  │  OpenAI  │  │  E2B   │
    │  Container       │  │     CLI      │  │   API    │  │  API   │
    │  (Current)       │  │  Container   │  │          │  │        │
    └──────────────────┘  └──────────────┘  └──────────┘  └────────┘
                ↓                ↓                ↓             ↓
            [Execute]        [Execute]        [API Call]   [API Call]
                ↓                ↓                ↓             ↓
            [Results]        [Results]        [Results]    [Results]
                ↓                ↓                ↓             ↓
                └────────────────┴────────────────┴─────────────┘
                                 ↓
                    ┌────────────────────────┐
                    │  MinIO Org Hierarchy   │
                    │  Technology/           │
                    │    Backend-Dev/        │
                    │      Project-X/        │
                    │        admin/          │
                    │          agent-tasks/  │
                    │            task-123/   │
                    │              results/  │
                    └────────────────────────┘
```

---

## Execution Modes

### 1. Native Interactive Agent (Enhanced Current)

**Description**: Our current Docker-based agent with added interactive chat capabilities.

**Architecture**:
```
User → WebSocket → Backend → Docker Exec → Agent Container
                                              ↓ (streaming)
User ← WebSocket ← Backend ← STDOUT ← Agent Container
```

**Key Features**:
- ✅ Already implemented (base)
- ✅ Full control over execution
- ✅ Local LLM support (Ollama)
- ✅ Custom tools
- ✅ No API costs (with Ollama)

**Enhancements Needed**:
- [ ] WebSocket support for streaming
- [ ] User input during execution
- [ ] Pause/resume capabilities
- [ ] Interactive prompts

**Implementation**:
```python
# backend/app/services/engines/native_engine.py

class NativeInteractiveEngine(AgentEngine):
    def __init__(self, task_id: str, project: str):
        self.task_id = task_id
        self.project = project
        self.process = None
        self.websocket = None

    async def execute(
        self,
        task: str,
        files: List[str],
        mode: str = "interactive"
    ) -> AsyncGenerator:
        """Execute task with streaming output"""

        # 1. Prepare workspace with MinIO files
        workspace = await self.prepare_workspace(files)

        # 2. Start agent container with streaming
        cmd = [
            "docker", "exec", "-i",
            "-e", f"TASK_ID={self.task_id}",
            "-e", f"MODE={mode}",
            "rag-agent-runtime",
            "python3", "/app/entrypoint_agent.py",
            "--task-id", self.task_id,
            "--description", task,
            "--workspace", workspace,
            "--stream"  # NEW: Enable streaming mode
        ]

        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # 3. Stream output line-by-line
        async for line in self.process.stdout:
            data = json.loads(line.decode())

            if data["type"] == "thought":
                yield {"event": "thinking", "content": data["content"]}

            elif data["type"] == "action":
                yield {"event": "action", "tool": data["tool"], "input": data["input"]}

            elif data["type"] == "observation":
                yield {"event": "result", "content": data["content"]}

            elif data["type"] == "user_input_needed":
                yield {"event": "prompt", "question": data["question"]}
                # Wait for user response via stdin
                user_input = await self.wait_for_user_input()
                self.process.stdin.write((user_input + "\n").encode())
                await self.process.stdin.drain()

            elif data["type"] == "final_answer":
                yield {"event": "complete", "answer": data["answer"]}
                break

        # 4. Upload results to MinIO
        await self.upload_results()

    async def chat(self, message: str):
        """Send message to running agent"""
        if self.process and self.process.stdin:
            self.process.stdin.write((message + "\n").encode())
            await self.process.stdin.drain()

    async def stop(self):
        """Stop execution gracefully"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
```

**Pros**:
- Full control
- No API costs (Ollama)
- Already implemented (base)
- On-premise friendly

**Cons**:
- Requires enhancement for interactivity
- Limited to our tools
- Manual LLM integration

---

### 2. Claude Code CLI Integration

**Description**: Integrate Anthropic's official Claude Code CLI tool within our sandbox.

**Architecture**:
```
User → Backend → Docker Container (with Claude Code CLI installed)
                         ↓
                  Claude Code CLI → Anthropic API
                         ↓
                  Results captured → MinIO
```

**Authentication Flow**:
```
1. User initiates Claude Code task
2. Backend checks for valid session key
3. If not found:
   a. Backend generates auth URL
   b. User opens browser and logs in
   c. User copies session key from browser
   d. User pastes key in UI
   e. Backend stores encrypted key in database
4. Backend passes key to Docker container
5. Claude Code CLI uses key for authentication
```

**Implementation**:

```python
# backend/app/services/engines/claude_code_engine.py

class ClaudeCodeEngine(AgentEngine):
    def __init__(self, task_id: str, project: str):
        self.task_id = task_id
        self.project = project
        self.session_key = None

    async def authenticate(self, user_id: str) -> dict:
        """Handle Claude Code authentication"""

        # Check for existing session key
        key = await self.get_stored_key(user_id)

        if not key or not await self.validate_key(key):
            # Generate auth URL
            return {
                "authenticated": False,
                "auth_url": "https://claude.ai/login",
                "instructions": (
                    "1. Visit the URL above and log in\n"
                    "2. Open browser DevTools → Application → Cookies\n"
                    "3. Copy the 'sessionKey' cookie value\n"
                    "4. Paste it in the field below"
                )
            }

        self.session_key = key
        return {"authenticated": True}

    async def save_session_key(self, user_id: str, key: str):
        """Encrypt and store session key"""
        from cryptography.fernet import Fernet

        # Encrypt key
        cipher = Fernet(settings.ENCRYPTION_KEY)
        encrypted = cipher.encrypt(key.encode())

        # Store in database
        await db.execute(
            """
            INSERT INTO claude_code_sessions (user_id, encrypted_key, created_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (user_id)
            DO UPDATE SET encrypted_key = $2, updated_at = NOW()
            """,
            user_id, encrypted.decode()
        )

    async def execute(
        self,
        task: str,
        files: List[str],
        mode: str = "interactive"
    ) -> AsyncGenerator:
        """Execute task using Claude Code CLI"""

        # 1. Prepare workspace with MinIO files
        workspace = await self.prepare_workspace(files)

        # 2. Create Dockerfile with Claude Code CLI
        dockerfile = f"""
FROM python:3.11-slim

# Install Claude Code CLI
RUN pip install anthropic-claude-code

# Set working directory
WORKDIR /workspace

# Copy files from MinIO
COPY {workspace}/* /workspace/

# Set session key
ENV CLAUDE_SESSION_KEY={self.session_key}

CMD ["claude-code"]
"""

        # 3. Build and run container
        container_name = f"claude-code-{self.task_id}"

        # Build image
        await self.build_image(dockerfile, f"claude-code-{self.task_id}")

        # 4. Run Claude Code with task
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{workspace}:/workspace",
            "-e", f"CLAUDE_SESSION_KEY={self.session_key}",
            container_name,
            "claude-code", "run",
            "--task", task,
            "--workspace", "/workspace"
        ]

        if mode == "interactive":
            cmd.extend(["--interactive"])

        # 5. Stream output
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        async for line in process.stdout:
            yield {
                "event": "output",
                "content": line.decode().strip()
            }

        # 6. Upload results to MinIO
        await self.upload_results(workspace)

    async def chat(self, message: str):
        """Send message to Claude Code"""
        # Claude Code CLI handles this automatically in interactive mode
        pass
```

**Docker Image Enhancement**:

```dockerfile
# backend/Dockerfile.claude-code

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI (hypothetical - check actual installation method)
RUN pip install anthropic-cli

# Install common data science libraries
RUN pip install pandas numpy matplotlib seaborn plotly

# Create workspace
WORKDIR /workspace

# Entry point
CMD ["bash"]
```

**UI Component for Authentication**:

```typescript
// frontend/src/components/ClaudeCodeAuth.tsx

export const ClaudeCodeAuth: React.FC = () => {
  const [authStatus, setAuthStatus] = useState<'checking' | 'needed' | 'authenticated'>('checking');
  const [sessionKey, setSessionKey] = useState('');

  useEffect(() => {
    checkAuthentication();
  }, []);

  const checkAuthentication = async () => {
    const response = await fetch('/api/v1/agent/claude-code/auth-status');
    const data = await response.json();

    if (data.authenticated) {
      setAuthStatus('authenticated');
    } else {
      setAuthStatus('needed');
    }
  };

  const saveSessionKey = async () => {
    await fetch('/api/v1/agent/claude-code/save-key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sessionKey })
    });

    setAuthStatus('authenticated');
  };

  if (authStatus === 'checking') {
    return <div>Checking Claude Code authentication...</div>;
  }

  if (authStatus === 'authenticated') {
    return <div className="text-green-600">✓ Claude Code authenticated</div>;
  }

  return (
    <div className="border rounded p-4 bg-blue-50">
      <h3 className="font-semibold mb-2">Claude Code Authentication Required</h3>

      <ol className="list-decimal ml-4 mb-4 text-sm space-y-1">
        <li>Visit <a href="https://claude.ai/login" target="_blank" className="text-blue-600">claude.ai/login</a></li>
        <li>Log in with your Anthropic account</li>
        <li>Open browser DevTools (F12) → Application → Cookies</li>
        <li>Find and copy the <code>sessionKey</code> cookie value</li>
        <li>Paste it below</li>
      </ol>

      <input
        type="password"
        value={sessionKey}
        onChange={(e) => setSessionKey(e.target.value)}
        placeholder="Paste session key here..."
        className="w-full border rounded px-3 py-2 mb-2"
      />

      <button
        onClick={saveSessionKey}
        disabled={!sessionKey}
        className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
      >
        Save & Continue
      </button>
    </div>
  );
};
```

**Pros**:
- Official Anthropic tool
- Latest features
- Best Claude integration
- Automatic tool selection

**Cons**:
- Requires API key management
- API costs
- Browser-based authentication flow
- Cloud-dependent
- Session key expiration handling

---

### 3. OpenAI Code Interpreter Integration

**Description**: Use OpenAI's Assistants API with Code Interpreter tool.

**Architecture**:
```
User → Backend → OpenAI Assistants API
                     ↓ (Code Interpreter)
                  Results → MinIO
```

**Implementation**:

```python
# backend/app/services/engines/openai_engine.py

from openai import AsyncOpenAI
import asyncio

class OpenAICodeInterpreterEngine(AgentEngine):
    def __init__(self, task_id: str, project: str):
        self.task_id = task_id
        self.project = project
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.assistant_id = None
        self.thread_id = None

    async def execute(
        self,
        task: str,
        files: List[str],
        mode: str = "interactive"
    ) -> AsyncGenerator:
        """Execute task using OpenAI Code Interpreter"""

        # 1. Download files from MinIO to temp location
        temp_files = await self.download_from_minio(files)

        # 2. Upload files to OpenAI
        file_ids = []
        for file_path in temp_files:
            file_obj = await self.client.files.create(
                file=open(file_path, "rb"),
                purpose="assistants"
            )
            file_ids.append(file_obj.id)
            yield {
                "event": "file_uploaded",
                "filename": file_path,
                "file_id": file_obj.id
            }

        # 3. Create assistant with Code Interpreter
        assistant = await self.client.beta.assistants.create(
            name=f"Agent Task {self.task_id}",
            instructions=(
                f"You are a helpful data analyst. "
                f"Complete this task: {task}\n\n"
                f"Upload all generated files (charts, CSVs, etc.) so they can be downloaded."
            ),
            model="gpt-4-turbo",
            tools=[{"type": "code_interpreter"}],
            file_ids=file_ids
        )
        self.assistant_id = assistant.id

        yield {
            "event": "assistant_created",
            "assistant_id": assistant.id
        }

        # 4. Create thread
        thread = await self.client.beta.threads.create()
        self.thread_id = thread.id

        # 5. Add message to thread
        await self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=task
        )

        # 6. Run assistant with streaming
        async with self.client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=assistant.id
        ) as stream:
            async for event in stream:
                if event.event == "thread.message.delta":
                    yield {
                        "event": "message",
                        "content": event.data.delta.content[0].text.value
                    }

                elif event.event == "thread.run.step.created":
                    step = event.data
                    if step.type == "tool_calls":
                        yield {
                            "event": "tool_call",
                            "tool": "code_interpreter",
                            "status": "running"
                        }

                elif event.event == "thread.run.step.completed":
                    step = event.data
                    if step.type == "tool_calls":
                        # Extract code and output
                        for tool_call in step.step_details.tool_calls:
                            if tool_call.type == "code_interpreter":
                                yield {
                                    "event": "code_executed",
                                    "code": tool_call.code_interpreter.input,
                                    "output": tool_call.code_interpreter.outputs
                                }

        # 7. Download generated files from OpenAI
        messages = await self.client.beta.threads.messages.list(
            thread_id=thread.id
        )

        for message in messages.data:
            if message.role == "assistant":
                for content in message.content:
                    if content.type == "image_file":
                        # Download image
                        file_data = await self.client.files.content(content.image_file.file_id)
                        local_path = f"/tmp/{content.image_file.file_id}.png"
                        with open(local_path, "wb") as f:
                            f.write(file_data.read())

                        # Upload to MinIO
                        minio_path = await self.upload_to_minio(
                            local_path,
                            f"artifacts/{content.image_file.file_id}.png"
                        )

                        yield {
                            "event": "artifact_created",
                            "type": "image",
                            "path": minio_path
                        }

        # 8. Clean up
        await self.client.beta.assistants.delete(assistant.id)

        yield {"event": "complete"}

    async def chat(self, message: str) -> AsyncGenerator:
        """Continue conversation with assistant"""
        if not self.thread_id:
            raise ValueError("No active thread")

        # Add user message
        await self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content=message
        )

        # Run assistant again with streaming
        async with self.client.beta.threads.runs.stream(
            thread_id=self.thread_id,
            assistant_id=self.assistant_id
        ) as stream:
            async for event in stream:
                if event.event == "thread.message.delta":
                    yield {
                        "event": "message",
                        "content": event.data.delta.content[0].text.value
                    }
```

**Pros**:
- Official OpenAI integration
- Excellent for data analysis
- File upload/download built-in
- Stateful conversations
- Good visualization support

**Cons**:
- API costs
- 512MB file size limit
- Cloud-dependent
- Limited execution time (~120s)
- OpenAI only (no other LLMs)

---

### 4. E2B Sandbox Integration (Optional)

**Description**: Use E2B's cloud sandbox for best interactive experience.

**Implementation**:

```python
# backend/app/services/engines/e2b_engine.py

from e2b import Sandbox

class E2BSandboxEngine(AgentEngine):
    def __init__(self, task_id: str, project: str):
        self.task_id = task_id
        self.project = project
        self.sandbox = None

    async def execute(
        self,
        task: str,
        files: List[str],
        mode: str = "interactive"
    ) -> AsyncGenerator:
        """Execute task using E2B sandbox"""

        # 1. Create sandbox
        self.sandbox = Sandbox(template="base")

        yield {"event": "sandbox_created", "sandbox_id": self.sandbox.id}

        # 2. Download files from MinIO and upload to E2B
        for file_path in files:
            local_file = await self.download_from_minio(file_path)
            file_content = open(local_file, "rb").read()

            self.sandbox.files.write(
                f"/workspace/{os.path.basename(file_path)}",
                file_content
            )

            yield {
                "event": "file_uploaded",
                "filename": file_path
            }

        # 3. Install required packages
        yield {"event": "installing_packages"}
        self.sandbox.run_code("pip install pandas matplotlib seaborn plotly openai anthropic")

        # 4. Create agent script
        agent_code = f"""
import os
from anthropic import Anthropic

client = Anthropic(api_key='{settings.ANTHROPIC_API_KEY}')

# Task description
task = '''{task}'''

# Execute with Claude
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    messages=[{{"role": "user", "content": task}}]
)

print(response.content[0].text)
"""

        # 5. Run agent
        result = self.sandbox.run_code(agent_code)

        yield {
            "event": "code_executed",
            "stdout": result.stdout,
            "stderr": result.stderr
        }

        # 6. Download generated files
        workspace_files = self.sandbox.files.list("/workspace")

        for file in workspace_files:
            if file.startswith("/workspace/output_"):
                content = self.sandbox.files.read(file)

                # Upload to MinIO
                minio_path = await self.upload_to_minio(
                    content,
                    f"artifacts/{os.path.basename(file)}"
                )

                yield {
                    "event": "artifact_created",
                    "path": minio_path
                }

        # 7. Close sandbox
        self.sandbox.close()

        yield {"event": "complete"}

    async def chat(self, message: str):
        """Execute additional code in existing sandbox"""
        if not self.sandbox:
            raise ValueError("No active sandbox")

        result = self.sandbox.run_code(message)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr
        }
```

**Pros**:
- Best interactive experience
- Stateful sessions
- Jupyter-like environment
- Fast execution
- Multi-language support

**Cons**:
- Highest cost at scale
- Cloud-dependent
- Requires API key
- External dependency

---

## Detailed Design

### Unified Engine Interface

```python
# backend/app/services/engines/base_engine.py

from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Dict, Any
from enum import Enum

class ExecutionMode(str, Enum):
    ONE_SHOT = "one_shot"
    INTERACTIVE = "interactive"

class EngineType(str, Enum):
    NATIVE = "native"
    CLAUDE_CODE = "claude_code"
    OPENAI = "openai"
    E2B = "e2b"

class AgentEngine(ABC):
    """Base class for all execution engines"""

    @abstractmethod
    async def execute(
        self,
        task: str,
        files: List[str],
        mode: ExecutionMode = ExecutionMode.ONE_SHOT
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute a task and stream results

        Yields events like:
            {"event": "thinking", "content": "..."}
            {"event": "action", "tool": "...", "input": {...}}
            {"event": "result", "content": "..."}
            {"event": "artifact_created", "path": "..."}
            {"event": "complete", "answer": "..."}
        """
        pass

    @abstractmethod
    async def chat(self, message: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Send a message during interactive execution"""
        pass

    @abstractmethod
    async def stop(self):
        """Stop execution gracefully"""
        pass

    async def prepare_workspace(self, files: List[str]) -> str:
        """Download files from MinIO to workspace"""
        workspace = f"/tmp/workspace_{self.task_id}"
        os.makedirs(workspace, exist_ok=True)

        for file_path in files:
            # Download from MinIO
            local_path = await self.minio_client.download_file(file_path, workspace)

        return workspace

    async def upload_results(self, workspace: str):
        """Upload results from workspace to MinIO org hierarchy"""
        minio_base_path = (
            f"Technology/Backend-Development/{self.project}/"
            f"admin/agent-tasks/{self.task_name}/{self.task_id}/"
        )

        # Upload artifacts
        artifacts_dir = f"{workspace}/artifacts"
        if os.path.exists(artifacts_dir):
            for file in os.listdir(artifacts_dir):
                await self.minio_client.upload_file(
                    f"{artifacts_dir}/{file}",
                    f"{minio_base_path}artifacts/{file}"
                )

        # Upload logs
        log_file = f"{workspace}/agent.log"
        if os.path.exists(log_file):
            await self.minio_client.upload_file(
                log_file,
                f"{minio_base_path}logs/agent.log"
            )
```

### Engine Factory

```python
# backend/app/services/engines/factory.py

class EngineFactory:
    """Factory for creating appropriate engine instances"""

    @staticmethod
    def create_engine(
        engine_type: EngineType,
        task_id: str,
        project: str,
        user_id: str
    ) -> AgentEngine:
        """Create engine instance based on type"""

        if engine_type == EngineType.NATIVE:
            return NativeInteractiveEngine(task_id, project)

        elif engine_type == EngineType.CLAUDE_CODE:
            return ClaudeCodeEngine(task_id, project)

        elif engine_type == EngineType.OPENAI:
            return OpenAICodeInterpreterEngine(task_id, project)

        elif engine_type == EngineType.E2B:
            return E2BSandboxEngine(task_id, project)

        else:
            raise ValueError(f"Unknown engine type: {engine_type}")
```

### WebSocket Handler for Interactive Mode

```python
# backend/app/api/routes/agent_ws.py

from fastapi import WebSocket, WebSocketDisconnect

@router.websocket("/ws/agent/{task_id}")
async def agent_websocket(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for interactive agent execution"""

    await websocket.accept()

    try:
        # Get task details
        task = await get_task(task_id)

        # Create appropriate engine
        engine = EngineFactory.create_engine(
            engine_type=task.engine_type,
            task_id=task_id,
            project=task.project,
            user_id=task.user_id
        )

        # Start execution
        execution_task = asyncio.create_task(
            execute_and_stream(engine, task, websocket)
        )

        # Listen for user messages
        while True:
            data = await websocket.receive_json()

            if data["type"] == "message":
                # User sent a message during execution
                async for event in engine.chat(data["content"]):
                    await websocket.send_json(event)

            elif data["type"] == "stop":
                await engine.stop()
                execution_task.cancel()
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for task {task_id}")
        await engine.stop()

async def execute_and_stream(engine: AgentEngine, task: Task, websocket: WebSocket):
    """Execute task and stream events to WebSocket"""
    try:
        async for event in engine.execute(
            task=task.description,
            files=task.input_files,
            mode=ExecutionMode.INTERACTIVE
        ):
            await websocket.send_json(event)

    except Exception as e:
        await websocket.send_json({
            "event": "error",
            "error": str(e)
        })
```

---

## UI/UX Design

### Task Creation UI

```typescript
// frontend/src/components/AgentTaskCreator.tsx

interface EngineConfig {
  type: 'native' | 'claude_code' | 'openai' | 'e2b';
  name: string;
  description: string;
  requiresAuth: boolean;
  cost: string;
  icon: string;
}

const ENGINES: EngineConfig[] = [
  {
    type: 'native',
    name: 'Native Agent',
    description: 'Our custom agent with Ollama (free) or cloud LLMs',
    requiresAuth: false,
    cost: 'Free (Ollama) or API costs',
    icon: '🤖'
  },
  {
    type: 'claude_code',
    name: 'Claude Code',
    description: 'Anthropic\'s official CLI tool',
    requiresAuth: true,
    cost: 'Claude API costs',
    icon: '🔮'
  },
  {
    type: 'openai',
    name: 'OpenAI Code Interpreter',
    description: 'GPT-4 with Code Interpreter',
    requiresAuth: true,
    cost: 'OpenAI API costs',
    icon: '🧠'
  },
  {
    type: 'e2b',
    name: 'E2B Sandbox',
    description: 'Cloud sandbox with best interactive experience',
    requiresAuth: true,
    cost: '$0.10-1.50/hour',
    icon: '☁️'
  }
];

export const AgentTaskCreator: React.FC = () => {
  const [selectedEngine, setSelectedEngine] = useState<EngineConfig>(ENGINES[0]);
  const [mode, setMode] = useState<'one_shot' | 'interactive'>('interactive');
  const [project, setProject] = useState('');
  const [files, setFiles] = useState<string[]>([]);
  const [task, setTask] = useState('');

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6">Create Agent Task</h2>

      {/* Engine Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">Execution Engine</label>
        <div className="grid grid-cols-2 gap-4">
          {ENGINES.map(engine => (
            <div
              key={engine.type}
              onClick={() => setSelectedEngine(engine)}
              className={`
                border rounded-lg p-4 cursor-pointer transition
                ${selectedEngine.type === engine.type
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-blue-300'
                }
              `}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{engine.icon}</span>
                  <span className="font-semibold">{engine.name}</span>
                </div>
                {engine.requiresAuth && <span className="text-xs text-gray-500">🔑 Auth required</span>}
              </div>
              <p className="text-sm text-gray-600 mb-2">{engine.description}</p>
              <p className="text-xs text-gray-500">Cost: {engine.cost}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Authentication (if required) */}
      {selectedEngine.requiresAuth && selectedEngine.type === 'claude_code' && (
        <ClaudeCodeAuth />
      )}

      {/* Execution Mode */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">Execution Mode</label>
        <div className="flex gap-4">
          <label className="flex items-center gap-2">
            <input
              type="radio"
              value="one_shot"
              checked={mode === 'one_shot'}
              onChange={(e) => setMode('one_shot')}
            />
            <span>One-shot (autonomous)</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="radio"
              value="interactive"
              checked={mode === 'interactive'}
              onChange={(e) => setMode('interactive')}
            />
            <span>Interactive Chat</span>
          </label>
        </div>
        {mode === 'interactive' && (
          <p className="text-sm text-gray-600 mt-1">
            💬 You'll be able to guide the agent during execution
          </p>
        )}
      </div>

      {/* Project Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">Project</label>
        <select
          value={project}
          onChange={(e) => setProject(e.target.value)}
          className="w-full border rounded px-3 py-2"
        >
          <option value="">Select project...</option>
          <option value="Construction-Intelligence">Construction Intelligence</option>
          <option value="Sales-Analytics">Sales Analytics</option>
        </select>
      </div>

      {/* File Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">Input Files</label>
        <FileSelector
          project={project}
          selectedFiles={files}
          onFilesChange={setFiles}
        />
      </div>

      {/* Task Description */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">Task Description</label>
        <textarea
          value={task}
          onChange={(e) => setTask(e.target.value)}
          rows={4}
          placeholder="Describe what you want the agent to do..."
          className="w-full border rounded px-3 py-2"
        />
      </div>

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={!project || !task}
        className="bg-blue-600 text-white px-6 py-3 rounded-lg disabled:opacity-50"
      >
        {mode === 'interactive' ? '🚀 Start Interactive Session' : '▶️ Execute Task'}
      </button>
    </div>
  );
};
```

### Interactive Chat UI

```typescript
// frontend/src/components/InteractiveAgentChat.tsx

export const InteractiveAgentChat: React.FC<{ taskId: string }> = ({ taskId }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [userInput, setUserInput] = useState('');
  const [status, setStatus] = useState<'connecting' | 'running' | 'completed' | 'error'>('connecting');
  const wsRef = useRef<WebSocket>();

  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/agent/${taskId}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.event === 'thinking') {
        setMessages(m => [...m, {
          role: 'agent',
          type: 'thinking',
          content: data.content
        }]);
      }
      else if (data.event === 'action') {
        setMessages(m => [...m, {
          role: 'agent',
          type: 'action',
          tool: data.tool,
          input: data.input
        }]);
      }
      else if (data.event === 'result') {
        setMessages(m => [...m, {
          role: 'agent',
          type: 'result',
          content: data.content
        }]);
      }
      else if (data.event === 'prompt') {
        setMessages(m => [...m, {
          role: 'agent',
          type: 'prompt',
          question: data.question
        }]);
        setStatus('waiting_input');
      }
      else if (data.event === 'complete') {
        setMessages(m => [...m, {
          role: 'agent',
          type: 'complete',
          answer: data.answer
        }]);
        setStatus('completed');
      }
    };

    ws.onerror = () => setStatus('error');
    ws.onopen = () => setStatus('running');

    wsRef.current = ws;

    return () => ws.close();
  }, [taskId]);

  const sendMessage = () => {
    wsRef.current?.send(JSON.stringify({
      type: 'message',
      content: userInput
    }));

    setMessages(m => [...m, {
      role: 'user',
      content: userInput
    }]);

    setUserInput('');
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="bg-gray-100 p-4 border-b">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">Interactive Agent Session</h2>
            <p className="text-sm text-gray-600">Task ID: {taskId}</p>
          </div>
          <div className="flex gap-2">
            <StatusBadge status={status} />
            <button
              onClick={() => wsRef.current?.send(JSON.stringify({ type: 'stop' }))}
              className="px-3 py-1 bg-red-600 text-white rounded text-sm"
            >
              Stop
            </button>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} />
        ))}
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder={
              status === 'waiting_input'
                ? 'Agent is waiting for your response...'
                : 'Send a message to guide the agent...'
            }
            className="flex-1 border rounded px-3 py-2"
            disabled={status === 'completed'}
          />
          <button
            onClick={sendMessage}
            disabled={!userInput || status === 'completed'}
            className="bg-blue-600 text-white px-6 py-2 rounded disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};
```

---

## Implementation Roadmap

### Phase 1: Foundation (2 weeks)

**Goals**: Set up multi-engine architecture

**Tasks**:
- [ ] Create `AgentEngine` abstract base class
- [ ] Implement `EngineFactory`
- [ ] Add WebSocket support to backend
- [ ] Create database schema for engine configurations
- [ ] Build UI for engine selection

**Deliverable**: Users can select engine (UI only, no execution yet)

---

### Phase 2: Native Interactive Agent (3 weeks)

**Goals**: Enhance current agent with interactivity

**Tasks**:
- [ ] Modify `entrypoint_agent.py` for streaming mode
- [ ] Add stdin handling for user input
- [ ] Implement `NativeInteractiveEngine`
- [ ] Build `InteractiveAgentChat` UI component
- [ ] Add pause/resume capabilities

**Deliverable**: Fully interactive native agent

---

### Phase 3: Claude Code Integration (4 weeks)

**Goals**: Integrate Claude Code CLI

**Tasks**:
- [ ] Research Claude Code CLI authentication
- [ ] Build session key management system
- [ ] Create `ClaudeCodeEngine` implementation
- [ ] Build authentication UI flow
- [ ] Create Claude Code Docker image
- [ ] Test with MinIO file integration

**Deliverable**: Working Claude Code execution

---

### Phase 4: OpenAI Code Interpreter (2 weeks)

**Goals**: Integrate OpenAI Assistants API

**Tasks**:
- [ ] Implement `OpenAICodeInterpreterEngine`
- [ ] File upload/download flow
- [ ] API key management
- [ ] Test with MinIO integration

**Deliverable**: Working OpenAI execution

---

### Phase 5: E2B Integration (Optional, 2 weeks)

**Goals**: Add E2B sandbox support

**Tasks**:
- [ ] Implement `E2BSandboxEngine`
- [ ] E2B API key management
- [ ] File sync with MinIO
- [ ] Test stateful sessions

**Deliverable**: Working E2B execution

---

### Phase 6: Polish & Optimization (2 weeks)

**Goals**: Production-ready release

**Tasks**:
- [ ] Performance optimization
- [ ] Error handling improvements
- [ ] Cost tracking per engine
- [ ] Usage analytics
- [ ] Documentation
- [ ] End-to-end testing

**Deliverable**: Production release

---

**Total Timeline**: 15-17 weeks (3.5-4 months)

---

## Technical Challenges

### Challenge 1: Claude Code CLI Authentication

**Problem**: Claude Code CLI requires browser-based authentication.

**Solutions**:

**Option A: Session Key Extraction** (Recommended)
- User logs in via browser
- User copies session key from cookies
- Backend stores encrypted key
- Pass key to Docker container

**Option B: Headless Browser**
- Use Playwright to automate login
- Extract session key programmatically
- More complex, fragile

**Recommendation**: Option A - simpler and more reliable

---

### Challenge 2: File Synchronization

**Problem**: Different engines have different file systems.

**Solutions**:

**Unified Approach**:
1. Always download files from MinIO to temp workspace
2. Pass workspace path to engine
3. Engine executes within workspace
4. Upload results back to MinIO

**Engine-Specific Handling**:
- **Native**: Direct filesystem access ✅
- **Claude Code**: Volume mounting to Docker
- **OpenAI**: Upload via API (max 512MB)
- **E2B**: Upload via SDK

---

### Challenge 3: Cost Tracking

**Problem**: Different engines have different cost structures.

**Solution**: Implement cost tracking middleware

```python
class CostTracker:
    COSTS = {
        'native_ollama': 0,  # Free
        'native_openai': 0.01,  # Per 1K tokens
        'claude_code': 0.015,  # Per 1K tokens
        'openai': 0.01,  # Per 1K tokens
        'e2b': 0.025  # Per minute
    }

    async def track_execution(self, engine_type, duration, tokens):
        cost = self.calculate_cost(engine_type, duration, tokens)

        await db.execute(
            """
            INSERT INTO agent_task_costs
            (task_id, engine_type, duration, tokens, cost)
            VALUES ($1, $2, $3, $4, $5)
            """,
            task_id, engine_type, duration, tokens, cost
        )
```

---

### Challenge 4: Session Management

**Problem**: Interactive sessions need state persistence.

**Solution**: Store session state in Redis

```python
class SessionManager:
    async def save_state(self, task_id: str, state: dict):
        await redis.set(
            f"agent_session:{task_id}",
            json.dumps(state),
            ex=3600  # 1 hour expiry
        )

    async def restore_state(self, task_id: str) -> dict:
        data = await redis.get(f"agent_session:{task_id}")
        return json.loads(data) if data else {}
```

---

## Security Considerations

### 1. API Key Management

**Store keys encrypted**:
```python
from cryptography.fernet import Fernet

class SecretManager:
    def __init__(self):
        self.cipher = Fernet(settings.ENCRYPTION_KEY)

    def encrypt_key(self, key: str) -> str:
        return self.cipher.encrypt(key.encode()).decode()

    def decrypt_key(self, encrypted: str) -> str:
        return self.cipher.decrypt(encrypted.encode()).decode()
```

### 2. Session Key Rotation

**Auto-expire and rotate**:
```python
# Store session keys with TTL
await db.execute(
    """
    INSERT INTO api_keys (user_id, service, encrypted_key, expires_at)
    VALUES ($1, $2, $3, NOW() + INTERVAL '7 days')
    """,
    user_id, service, encrypted_key
)

# Background task to clean expired keys
@scheduler.task("daily")
async def cleanup_expired_keys():
    await db.execute(
        "DELETE FROM api_keys WHERE expires_at < NOW()"
    )
```

### 3. Rate Limiting

**Prevent abuse**:
```python
from slowapi import Limiter

limiter = Limiter(key_func=get_user_id)

@router.post("/agent/tasks")
@limiter.limit("10/hour")  # Max 10 tasks per hour per user
async def create_task(...):
    ...
```

---

## Cost Analysis

### Monthly Cost Comparison (1000 tasks, 5-min avg)

| Engine | Compute | API | Total |
|--------|---------|-----|-------|
| **Native (Ollama)** | $0 | $0 | **$0** |
| **Native (GPT-4)** | $0 | $40 | **$40** |
| **Claude Code** | $0 | $60 | **$60** |
| **OpenAI** | $0 | $40 | **$40** |
| **E2B** | $40 | $40 | **$80** |

### Cost Optimization Strategies

1. **Default to Ollama for simple tasks**
2. **Use Claude Code for complex reasoning**
3. **Use OpenAI for data analysis**
4. **Reserve E2B for collaborative sessions**

---

## Recommendations

### Recommended Implementation Order

1. ✅ **Phase 1**: Foundation (2 weeks)
2. ✅ **Phase 2**: Native Interactive (3 weeks)
3. ⭐ **Phase 3**: OpenAI Integration (2 weeks) - **Start here**
   - Easiest to implement
   - Well-documented API
   - Good for data analysis use cases
4. ⭐ **Phase 4**: Claude Code (4 weeks) - **High value**
   - Most powerful for complex tasks
   - Official Anthropic tool
5. ⚠️ **Phase 5**: E2B (2 weeks) - **Optional**
   - Only if budget allows
   - Best for notebook-like experiences

### MVP Recommendation (8 weeks)

**Phase 1-3 only**:
- Native Interactive Agent
- OpenAI Code Interpreter
- Engine selection UI
- Basic cost tracking

This provides:
- ✅ Free option (Ollama)
- ✅ Best data analysis (OpenAI)
- ✅ Interactive chat
- ✅ Full MinIO integration
- ✅ Reasonable development timeline

### Decision Factors

| Factor | Choose Native | Choose Claude Code | Choose OpenAI | Choose E2B |
|--------|---------------|-------------------|---------------|------------|
| **Cost** | Free (Ollama) | Medium | Medium | High |
| **Complexity** | High reasoning needed | High reasoning needed | Data analysis | Interactive work |
| **Data sensitivity** | High (on-prem) | Medium | Medium | Low |
| **Execution time** | >10 min | <10 min | <2 min | Any |

---

## Next Steps

### Immediate Actions

1. **Decide on MVP scope**
   - Which engines to implement first?
   - Interactive vs one-shot priority?

2. **Set up development environment**
   - Branch: `feature/multi-engine-agents`
   - Create project board

3. **Start Phase 1**
   - Define `AgentEngine` interface
   - Create database migrations
   - Build UI mockups

4. **Prototype OpenAI integration** (quickest win)
   - Test Assistants API
   - Validate file upload/download
   - Measure costs

### Questions to Answer

1. **Budget**: What's acceptable monthly cost for external APIs?
2. **Priority**: Which engine is most valuable to users?
3. **Timeline**: 8-week MVP or 17-week full implementation?
4. **Authentication**: Centralized API key management or user-provided keys?

---

## Conclusion

This multi-engine architecture provides:

✅ **Flexibility**: Users choose the right tool for the job
✅ **Cost optimization**: Free option (Ollama) + paid options
✅ **Best-in-class**: Leverage official tools (Claude Code, OpenAI)
✅ **Enterprise features**: Maintain MinIO integration, RBAC, audit logs
✅ **Future-proof**: Easy to add new engines

**Recommended MVP** (8 weeks):
1. Native Interactive Agent (current + enhancements)
2. OpenAI Code Interpreter integration
3. Engine selection UI
4. Basic cost tracking

This delivers maximum value with reasonable development effort while maintaining your enterprise architecture.

---

**Document Version**: 1.0
**Created**: 2025-12-12
**Status**: Design Proposal
**Next Review**: After stakeholder feedback
