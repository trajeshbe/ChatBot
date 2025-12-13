# CLI Agents Implementation Plan - Codex CLI & Claude Code CLI

**Date**: 2025-12-13
**Status**: 📋 PLANNED
**Priority**: P0 - Critical Feature

---

## 🎯 Correct Requirements

### What User Actually Wants

Run **CLI tools** inside the Docker sandbox container and visualize their execution in the Task Details UI:

1. ✨ **Streaming Response in Chat UI** (like ChatGPT) - KEEP THIS
2. 🔧 **Codex CLI in Agent Sandbox** - Run OpenAI Codex CLI tool autonomously
3. 🎯 **Claude Code CLI in Agent Sandbox** - Run Anthropic Claude Code CLI tool autonomously
4. 🤖 **Interactive Task Details UI** - Visualize and interact with CLI execution in real-time

### Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                            │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ AgentTaskMonitor.tsx                                       │   │
│  │  • Create Task Form                                        │   │
│  │  • Execution Mode Selector:                                │   │
│  │    ○ 🐳 Local Mini Agent (Python - current)               │   │
│  │    ○ 🔧 Codex CLI (NEW)                                   │   │
│  │    ○ 🎯 Claude Code CLI (NEW)                             │   │
│  └────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ TaskDetailsInteractive.tsx (NEW)                           │   │
│  │  • WebSocket connection to task stream                     │   │
│  │  • Real-time CLI output display                            │   │
│  │  • Terminal-like interface                                 │   │
│  │  • Interactive controls (pause, resume, cancel)            │   │
│  └────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                               │ HTTP + WebSocket
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Backend (FastAPI)                             │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ /api/v1/agent/tasks (POST)                                 │   │
│  │  • Create task with execution_mode parameter:              │   │
│  │    - "local_agent" (default)                               │   │
│  │    - "codex_cli"                                           │   │
│  │    - "claude_code_cli"                                     │   │
│  └────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ /api/v1/agent/tasks/{id}/stream (WebSocket)               │   │
│  │  • Stream CLI output in real-time                          │   │
│  │  • Broadcast stdout/stderr                                 │   │
│  │  • Send status updates                                     │   │
│  └────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ agent_sandbox_manager.py                                   │   │
│  │  • Route to correct CLI executor:                          │   │
│  │    - execute_local_agent()                                 │   │
│  │    - execute_codex_cli()    ← NEW                         │   │
│  │    - execute_claude_code_cli() ← NEW                       │   │
│  └────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                               │ docker exec
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Docker Container: agent-runtime                         │
│              (Ubuntu 24.04 + Python 3.11)                            │
│                                                                      │
│  Installed CLI Tools:                                                │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ 1. Local Mini Agent (Current)                              │   │
│  │    • python3 entrypoint_agent.py                           │   │
│  │    • Custom agentic loop                                   │   │
│  │    • Uses Ollama/OpenAI API                                │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ 2. Codex CLI (NEW)                                         │   │
│  │    • npm install -g @openai/codex-cli (hypothetical)       │   │
│  │    OR                                                       │   │
│  │    • GitHub Copilot CLI (gh copilot)                       │   │
│  │    OR                                                       │   │
│  │    • Custom OpenAI Codex wrapper script                    │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ 3. Claude Code CLI (NEW)                                   │   │
│  │    • curl -fsSL https://anthropic.com/.../install.sh | sh  │   │
│  │    • claude-code <task-description>                        │   │
│  │    • Runs autonomously with MCP tools                      │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  Workspace Structure:                                                │
│  /workspace/                                                         │
│    ├── input/        # Input files                                  │
│    ├── output/       # Output files                                 │
│    ├── artifacts/    # Generated artifacts                          │
│    └── temp/         # Temporary files                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Implementation 1: Streaming Response in Chat UI

**(Keep from previous plan - this is still needed)**

See `NEXT_IMPLEMENTATIONS_PLAN.md` for full details on SSE implementation.

---

## Implementation 2: Codex CLI in Agent Sandbox

### 🎯 Goal
Install and run OpenAI Codex CLI inside the Docker container, stream output to UI.

### 📊 Current State

**Codex CLI Options**:
1. **GitHub Copilot CLI** - `gh copilot` (official, free tier available)
2. **OpenAI CLI** - Custom wrapper using OpenAI API
3. **Aider** - Open-source AI coding assistant (uses GPT-4)

### 🔧 Required Changes

#### Phase 1: Install Codex CLI in Docker

**File 1: Update Dockerfile** (`backend/Dockerfile.agent-runtime`)

```dockerfile
FROM ubuntu:24.04

# ... existing setup ...

# ============================================
# Install GitHub Copilot CLI (Codex CLI Option 1)
# ============================================
RUN apt-get update && apt-get install -y \
    gh \
    && gh extension install github/gh-copilot

# OR

# ============================================
# Install Aider (Codex CLI Option 2 - Open Source)
# ============================================
RUN pip install aider-chat

# OR

# ============================================
# Install Custom OpenAI Codex Wrapper (Option 3)
# ============================================
COPY codex_cli_wrapper.py /usr/local/bin/codex-cli
RUN chmod +x /usr/local/bin/codex-cli

# Environment variables
ENV OPENAI_API_KEY=""
ENV GITHUB_TOKEN=""
```

**File 2: Codex CLI Wrapper** (`backend/codex_cli_wrapper.py` - Option 3)

```python
#!/usr/bin/env python3
"""
Custom Codex CLI wrapper using OpenAI API

Usage:
    codex-cli "Create a Python script that analyzes CSV data"
"""

import sys
import os
import json
from openai import OpenAI

def main():
    if len(sys.argv) < 2:
        print("Usage: codex-cli <task-description>")
        sys.exit(1)

    task_description = " ".join(sys.argv[1:])
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    # System prompt for Codex
    system_prompt = """You are an expert coding assistant. You have access to the following workspace:
- /workspace/input - Input files
- /workspace/output - Output files
- /workspace/artifacts - Generated artifacts

Generate clean, production-ready code with proper error handling and documentation.
Save output files to /workspace/output/ and artifacts to /workspace/artifacts/.
"""

    print(f"🤖 Codex CLI: Processing task...\n")

    # Stream response
    stream = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task_description}
        ],
        stream=True,
        temperature=0.3
    )

    full_response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            print(content, end="", flush=True)
            full_response += content

    print("\n\n✅ Codex CLI: Task completed")

    # Save response to artifacts
    with open("/workspace/artifacts/codex_response.txt", "w") as f:
        f.write(full_response)

if __name__ == "__main__":
    main()
```

#### Phase 2: Backend Execution Wrapper

**File 1: Add Codex Executor** (`backend/app/services/agent_sandbox_manager.py`)

```python
class AgentSandboxManager:
    async def execute_codex_cli(
        self,
        task_id: str,
        task_description: str,
        session_id: str,
        workspace_path: str,
        broadcast_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Execute task using Codex CLI in Docker container

        Args:
            task_id: Unique task identifier
            task_description: Natural language task description
            session_id: User session ID
            workspace_path: Path to workspace
            broadcast_callback: Callback to stream output to WebSocket

        Returns:
            Execution result with stdout/stderr
        """

        container_name = "rag-agent-runtime"

        # Prepare environment variables
        env_vars = {
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "TASK_ID": task_id,
            "SESSION_ID": session_id
        }

        env_args = " ".join([f"-e {k}={v}" for k, v in env_vars.items()])

        # OPTION 1: GitHub Copilot CLI
        # command = f'docker exec {env_args} {container_name} gh copilot suggest "{task_description}"'

        # OPTION 2: Aider
        # command = f'docker exec {env_args} {container_name} aider --yes --message "{task_description}"'

        # OPTION 3: Custom wrapper
        command = f'docker exec {env_args} {container_name} codex-cli "{task_description}"'

        logger.info(f"🔧 Executing Codex CLI for task {task_id}")

        if broadcast_callback:
            await broadcast_callback({
                "type": "started",
                "message": "🤖 Codex CLI started...",
                "execution_mode": "codex_cli"
            })

        # Execute and stream output
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout_lines = []
        stderr_lines = []

        # Stream stdout
        async for line in process.stdout:
            line_text = line.decode('utf-8', errors='ignore')
            stdout_lines.append(line_text)
            print(line_text, end='')  # Local logging

            if broadcast_callback:
                await broadcast_callback({
                    "type": "stdout",
                    "content": line_text,
                    "timestamp": datetime.utcnow().isoformat()
                })

        # Stream stderr
        async for line in process.stderr:
            line_text = line.decode('utf-8', errors='ignore')
            stderr_lines.append(line_text)

            if broadcast_callback:
                await broadcast_callback({
                    "type": "stderr",
                    "content": line_text,
                    "timestamp": datetime.utcnow().isoformat()
                })

        await process.wait()

        # Check artifacts
        artifacts = self._scan_artifacts(workspace_path)

        result = {
            "success": process.returncode == 0,
            "stdout": "".join(stdout_lines),
            "stderr": "".join(stderr_lines),
            "return_code": process.returncode,
            "artifacts": artifacts,
            "execution_mode": "codex_cli"
        }

        if broadcast_callback:
            await broadcast_callback({
                "type": "completed",
                "message": "✅ Codex CLI completed" if result["success"] else "❌ Codex CLI failed",
                "result": result
            })

        return result
```

#### Phase 3: Frontend UI

**File 1: Update Execution Mode Selector** (`frontend/src/components/AgentTaskMonitor.tsx`)

```typescript
export const AgentTaskMonitor: React.FC = () => {
  const [executionMode, setExecutionMode] = useState<'local_agent' | 'codex_cli' | 'claude_code_cli'>('local_agent');

  return (
    <div className="space-y-4">
      <div className="p-4 border rounded">
        <h3 className="font-semibold mb-3">🤖 Execution Mode</h3>

        <div className="space-y-2">
          {/* Option 1: Local Agent */}
          <label className="flex items-center gap-3 p-3 border rounded cursor-pointer hover:bg-gray-50">
            <input
              type="radio"
              name="execution_mode"
              value="local_agent"
              checked={executionMode === 'local_agent'}
              onChange={() => setExecutionMode('local_agent')}
            />
            <div className="flex-1">
              <div className="font-semibold">🐳 Local Mini Agent (Default)</div>
              <div className="text-sm text-gray-600">
                Custom Python agent with 10+ tools. Uses Ollama (free) or OpenAI API.
              </div>
            </div>
          </label>

          {/* Option 2: Codex CLI */}
          <label className="flex items-center gap-3 p-3 border rounded cursor-pointer hover:bg-gray-50">
            <input
              type="radio"
              name="execution_mode"
              value="codex_cli"
              checked={executionMode === 'codex_cli'}
              onChange={() => setExecutionMode('codex_cli')}
            />
            <div className="flex-1">
              <div className="font-semibold">🔧 Codex CLI (OpenAI GPT-4)</div>
              <div className="text-sm text-gray-600">
                GitHub Copilot CLI or custom Codex wrapper. Best for code generation.
              </div>
              <div className="text-xs text-yellow-600 mt-1">
                💰 Requires OPENAI_API_KEY (~$0.10-$0.50 per task)
              </div>
            </div>
          </label>

          {/* Option 3: Claude Code CLI */}
          <label className="flex items-center gap-3 p-3 border rounded cursor-pointer hover:bg-gray-50">
            <input
              type="radio"
              name="execution_mode"
              value="claude_code_cli"
              checked={executionMode === 'claude_code_cli'}
              onChange={() => setExecutionMode('claude_code_cli')}
            />
            <div className="flex-1">
              <div className="font-semibold">🎯 Claude Code CLI (Anthropic)</div>
              <div className="text-sm text-gray-600">
                Official Claude Code CLI with extended thinking. Best for complex reasoning.
              </div>
              <div className="text-xs text-yellow-600 mt-1">
                💰 Requires ANTHROPIC_API_KEY (~$0.50-$2.00 per task)
              </div>
            </div>
          </label>
        </div>
      </div>

      {/* Show API key status */}
      {executionMode !== 'local_agent' && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded">
          <p className="text-sm text-blue-800">
            🔑 <strong>API Key Required:</strong> Make sure your{' '}
            {executionMode === 'codex_cli' ? 'OPENAI_API_KEY' : 'ANTHROPIC_API_KEY'}{' '}
            is configured in the backend environment.
          </p>
        </div>
      )}
    </div>
  );
};
```

### 📦 Dependencies

```dockerfile
# Dockerfile.agent-runtime
# Option 1: GitHub Copilot CLI
RUN gh extension install github/gh-copilot

# Option 2: Aider (open source)
RUN pip install aider-chat

# Option 3: Custom wrapper (no extra deps, just OpenAI API)
```

---

## Implementation 3: Claude Code CLI in Agent Sandbox

### 🎯 Goal
Install official Claude Code CLI in Docker container, run autonomously.

### 📊 Claude Code CLI

**Official Tool**: https://docs.anthropic.com/claude-code
**Installation**:
```bash
curl -fsSL https://install.anthropic.com/claude-code | sh
```

**Usage**:
```bash
claude-code "Analyze this CSV file and create visualizations"
```

**Features**:
- Extended thinking mode
- Multi-tool use (file operations, bash, web search)
- Autonomous planning and execution
- MCP (Model Context Protocol) support

### 🔧 Required Changes

#### Phase 1: Install Claude Code CLI

**File 1: Update Dockerfile** (`backend/Dockerfile.agent-runtime`)

```dockerfile
# ============================================
# Install Claude Code CLI (Official)
# ============================================
RUN curl -fsSL https://install.anthropic.com/claude-code | sh

# Add to PATH
ENV PATH="/root/.local/bin:${PATH}"

# Environment variables
ENV ANTHROPIC_API_KEY=""
```

#### Phase 2: Backend Execution Wrapper

**File 1: Add Claude Code Executor** (`backend/app/services/agent_sandbox_manager.py`)

```python
async def execute_claude_code_cli(
    self,
    task_id: str,
    task_description: str,
    session_id: str,
    workspace_path: str,
    broadcast_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Execute task using Claude Code CLI in Docker container

    Features:
    - Extended thinking mode
    - Autonomous execution
    - MCP tool integration
    """

    container_name = "rag-agent-runtime"

    # Environment variables
    env_vars = {
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "TASK_ID": task_id,
        "SESSION_ID": session_id,
        "WORKSPACE": "/workspace"
    }

    env_args = " ".join([f"-e {k}={v}" for k, v in env_vars.items()])

    # Claude Code CLI command
    command = f'''docker exec {env_args} {container_name} /bin/bash -c '
        cd /workspace && \
        claude-code "{task_description}" \
        --workspace /workspace \
        --output /workspace/output \
        --artifacts /workspace/artifacts \
        --verbose
    ' '''

    logger.info(f"🎯 Executing Claude Code CLI for task {task_id}")

    if broadcast_callback:
        await broadcast_callback({
            "type": "started",
            "message": "🎯 Claude Code CLI started...",
            "execution_mode": "claude_code_cli"
        })

    # Execute and stream output
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout_lines = []
    stderr_lines = []

    # Stream stdout (includes thinking process)
    async for line in process.stdout:
        line_text = line.decode('utf-8', errors='ignore')
        stdout_lines.append(line_text)

        # Parse Claude Code output for structured events
        if "<thinking>" in line_text:
            event_type = "thinking"
        elif "[TOOL:" in line_text:
            event_type = "tool_use"
        elif "[RESULT:" in line_text:
            event_type = "tool_result"
        else:
            event_type = "stdout"

        if broadcast_callback:
            await broadcast_callback({
                "type": event_type,
                "content": line_text,
                "timestamp": datetime.utcnow().isoformat()
            })

    # Stream stderr
    async for line in process.stderr:
        line_text = line.decode('utf-8', errors='ignore')
        stderr_lines.append(line_text)

        if broadcast_callback:
            await broadcast_callback({
                "type": "stderr",
                "content": line_text,
                "timestamp": datetime.utcnow().isoformat()
            })

    await process.wait()

    # Scan artifacts
    artifacts = self._scan_artifacts(workspace_path)

    result = {
        "success": process.returncode == 0,
        "stdout": "".join(stdout_lines),
        "stderr": "".join(stderr_lines),
        "return_code": process.returncode,
        "artifacts": artifacts,
        "execution_mode": "claude_code_cli"
    }

    if broadcast_callback:
        await broadcast_callback({
            "type": "completed",
            "message": "✅ Claude Code CLI completed" if result["success"] else "❌ Claude Code CLI failed",
            "result": result
        })

    return result
```

---

## Implementation 4: Interactive Task Details UI

### 🎯 Goal
Real-time terminal-like UI showing CLI output with syntax highlighting and interaction.

### 🔧 Required Changes

**File 1: Create Interactive Terminal Component** (`frontend/src/components/TaskDetailsInteractive.tsx`)

```typescript
import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Pause, Play, X, Download } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface TerminalMessage {
  type: 'started' | 'stdout' | 'stderr' | 'thinking' | 'tool_use' | 'tool_result' | 'completed' | 'error';
  content?: string;
  message?: string;
  timestamp: string;
}

interface TaskDetailsInteractiveProps {
  taskId: string;
  executionMode: 'local_agent' | 'codex_cli' | 'claude_code_cli';
}

export const TaskDetailsInteractive: React.FC<TaskDetailsInteractiveProps> = ({
  taskId,
  executionMode
}) => {
  const [messages, setMessages] = useState<TerminalMessage[]>([]);
  const [isRunning, setIsRunning] = useState(true);
  const [isPaused, setIsPaused] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const terminalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Connect to WebSocket
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const wsUrl = API_URL.replace('http', 'ws');
    const ws = new WebSocket(`${wsUrl}/api/v1/agent/tasks/${taskId}/stream`);

    ws.onopen = () => {
      console.log('✅ Connected to task stream');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages(prev => [...prev, data]);

      // Auto-scroll to bottom
      if (!isPaused) {
        setTimeout(() => {
          terminalRef.current?.scrollTo({
            top: terminalRef.current.scrollHeight,
            behavior: 'smooth'
          });
        }, 100);
      }

      if (data.type === 'completed' || data.type === 'error') {
        setIsRunning(false);
      }
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      setIsRunning(false);
    };

    ws.onclose = () => {
      console.log('🔌 Disconnected from task stream');
      setIsRunning(false);
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [taskId, isPaused]);

  const renderMessage = (msg: TerminalMessage, index: number) => {
    const timestamp = new Date(msg.timestamp).toLocaleTimeString();

    switch (msg.type) {
      case 'started':
        return (
          <div key={index} className="flex items-center gap-2 p-2 bg-blue-900 text-blue-200 rounded">
            <Terminal className="w-4 h-4" />
            <span className="text-sm">[{timestamp}] {msg.message}</span>
          </div>
        );

      case 'stdout':
        return (
          <div key={index} className="p-1 font-mono text-sm text-green-400">
            <span className="text-gray-500">[{timestamp}]</span> {msg.content}
          </div>
        );

      case 'stderr':
        return (
          <div key={index} className="p-1 font-mono text-sm text-red-400">
            <span className="text-gray-500">[{timestamp}]</span> {msg.content}
          </div>
        );

      case 'thinking':
        return (
          <div key={index} className="p-3 bg-purple-900/30 border-l-4 border-purple-500 rounded">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-purple-400 text-sm font-semibold">🧠 Thinking...</span>
              <span className="text-xs text-gray-500">{timestamp}</span>
            </div>
            <ReactMarkdown className="text-purple-300 text-sm whitespace-pre-wrap">
              {msg.content || ''}
            </ReactMarkdown>
          </div>
        );

      case 'tool_use':
        return (
          <div key={index} className="p-3 bg-yellow-900/30 border-l-4 border-yellow-500 rounded">
            <div className="flex items-center gap-2">
              <span className="text-yellow-400 text-sm">🔧 Tool Use</span>
              <span className="text-xs text-gray-500">{timestamp}</span>
            </div>
            <pre className="text-yellow-300 text-sm mt-1">{msg.content}</pre>
          </div>
        );

      case 'tool_result':
        return (
          <div key={index} className="p-3 bg-green-900/30 border-l-4 border-green-500 rounded">
            <div className="flex items-center gap-2">
              <span className="text-green-400 text-sm">✅ Tool Result</span>
              <span className="text-xs text-gray-500">{timestamp}</span>
            </div>
            <pre className="text-green-300 text-sm mt-1 max-h-64 overflow-y-auto">
              {msg.content}
            </pre>
          </div>
        );

      case 'completed':
        return (
          <div key={index} className="p-3 bg-green-600 text-white rounded font-semibold">
            ✅ {msg.message}
          </div>
        );

      case 'error':
        return (
          <div key={index} className="p-3 bg-red-600 text-white rounded font-semibold">
            ❌ {msg.message}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-900 text-white rounded-lg shadow-2xl">
      {/* Header */}
      <div className="p-4 border-b border-gray-700 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">
            {executionMode === 'codex_cli' && '🔧 Codex CLI'}
            {executionMode === 'claude_code_cli' && '🎯 Claude Code CLI'}
            {executionMode === 'local_agent' && '🐳 Local Agent'}
          </h2>
          <p className="text-xs text-gray-400">Task ID: {taskId}</p>
        </div>
        <div className="flex items-center gap-2">
          {isRunning && (
            <button
              onClick={() => setIsPaused(!isPaused)}
              className="p-2 hover:bg-gray-700 rounded"
              title={isPaused ? 'Resume auto-scroll' : 'Pause auto-scroll'}
            >
              {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
            </button>
          )}
          <button
            onClick={() => {
              const text = messages.map(m => m.content || m.message).join('\n');
              const blob = new Blob([text], { type: 'text/plain' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `task_${taskId}_output.txt`;
              a.click();
            }}
            className="p-2 hover:bg-gray-700 rounded"
            title="Download output"
          >
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Terminal Output */}
      <div
        ref={terminalRef}
        className="flex-1 overflow-y-auto p-4 space-y-2 bg-black/50 font-mono text-sm"
      >
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            Waiting for {executionMode} to start...
          </div>
        ) : (
          messages.map((msg, idx) => renderMessage(msg, idx))
        )}
      </div>

      {/* Status Bar */}
      <div className="p-3 border-t border-gray-700 bg-gray-800 text-xs flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className={`px-2 py-1 rounded ${isRunning ? 'bg-green-600' : 'bg-gray-600'}`}>
            {isRunning ? 'Running' : 'Stopped'}
          </span>
          <span className="text-gray-400">{messages.length} messages</span>
        </div>
        {isPaused && (
          <span className="text-yellow-400">⏸ Auto-scroll paused</span>
        )}
      </div>
    </div>
  );
};
```

---

## 📦 Summary: What Gets Installed

### Docker Container (agent-runtime)

```dockerfile
# Base: Ubuntu 24.04 + Python 3.11

# Current (already installed):
- Python 3.11
- Node.js 20
- Playwright
- Tesseract OCR
- OpenCV
- Our custom agent tools

# NEW - Option 1: GitHub Copilot CLI
RUN gh extension install github/gh-copilot

# NEW - Option 2: Aider (open source alternative)
RUN pip install aider-chat

# NEW - Option 3: Claude Code CLI (official)
RUN curl -fsSL https://install.anthropic.com/claude-code | sh
```

### Environment Variables

```bash
# .env (backend)
OPENAI_API_KEY=sk-...          # For Codex CLI
ANTHROPIC_API_KEY=sk-ant-...   # For Claude Code CLI
GITHUB_TOKEN=ghp_...           # For GitHub Copilot CLI (if used)
```

---

## 🗓️ Implementation Timeline

### Week 1: Streaming Chat + CLI Infrastructure
- Day 1-2: Streaming response in chat UI (SSE)
- Day 3: Install Codex CLI in Docker (choose best option)
- Day 4: Backend executor for Codex CLI
- Day 5: Install Claude Code CLI in Docker

### Week 2: Interactive UI + Testing
- Day 1-2: TaskDetailsInteractive component
- Day 3: WebSocket streaming from CLI
- Day 4: Syntax highlighting, thinking display
- Day 5: Testing all 3 execution modes

### Week 3: Polish + Deployment
- Day 1: Cost tracking, budget limits
- Day 2: Error handling, retry logic
- Day 3: Documentation, user guide
- Day 4: Performance testing
- Day 5: Production deployment

---

## ✅ Success Criteria

- [ ] User can select execution mode (Local/Codex/Claude Code)
- [ ] Codex CLI runs autonomously in Docker
- [ ] Claude Code CLI runs autonomously in Docker
- [ ] Task Details UI streams output in real-time
- [ ] Extended thinking visible in UI (Claude Code)
- [ ] Tool usage visible in UI (both CLIs)
- [ ] Artifacts downloadable after completion
- [ ] Cost estimates shown before execution

---

**This is the correct architecture - CLIs run in Docker, UI visualizes execution!**
