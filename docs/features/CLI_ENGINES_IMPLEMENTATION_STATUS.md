# CLI Engines Implementation Status

> **Date**: 2025-12-13
> **Feature**: Codex CLI and Claude Code CLI Agent Engines
> **Status**: ✅ Backend Complete | ⏸️ Frontend Pending

---

## Overview

Implemented support for multiple agent execution engines, allowing users to choose between:

1. **DEFAULT Engine**: Existing LangGraph-based agentic workflow
2. **CODEX-CLI Engine**: OpenAI Codex CLI running in Docker sandbox
3. **CLAUDE-CODE-CLI Engine**: Anthropic Claude Code CLI running in Docker sandbox

This provides flexibility in agent execution while maintaining a unified API interface.

---

## Architecture

### Engine Abstraction Pattern

```
AgentOrchestrationService
       ↓
   _execute_task_async(task_id, engine)
       ↓
       ├── default → _execute_task_default_engine()
       │            (existing Docker container execution)
       │
       └── CLI engines → _execute_task_cli_engine()
                    ↓
                    ├── CodexCLIEngine
                    └── ClaudeCodeCLIEngine
```

### Base Class: AgentEngine

All engines implement a common interface:

```python
class AgentEngine(ABC):
    @abstractmethod
    async def execute(...) -> Dict[str, Any]

    @abstractmethod
    async def stream_events(...) -> AsyncIterator[Dict[str, Any]]

    @abstractmethod
    async def cancel(execution_id: str) -> bool

    @abstractmethod
    async def health_check() -> Dict[str, Any]
```

---

## Implementation Details

### 1. Engine Base Classes

**File**: `backend/app/services/engines/base.py`

**Components**:
- `EngineType` enum: DEFAULT, CODEX_CLI, CLAUDE_CODE_CLI
- `AgentEngine` abstract base class
- `_format_event()` helper for standardized event formatting

**Key Features**:
- Abstract methods enforce consistent interface
- Event streaming support for real-time updates
- Health check system for availability detection
- Cancellation support for running tasks

### 2. Default Engine

**File**: `backend/app/services/engines/default_engine.py`

**Purpose**: Wrapper for existing LangGraph agent implementation

**Key Points**:
- Maintains backward compatibility
- Delegates to existing AgentOrchestrationService
- Placeholder implementation (actual work done in agent-runtime container)

### 3. Codex CLI Engine

**File**: `backend/app/services/engines/codex_cli_engine.py`

**Features**:
- Uses OpenAI API with GPT-4-turbo-preview (Codex API deprecated)
- Subprocess execution with `asyncio.create_subprocess_exec`
- Streaming output parsing (JSON and plain text)
- Timeout management with `asyncio.wait_for`
- Artifact collection from workspace
- Environment variable handling for API keys

**Model**: `gpt-4-turbo-preview`

**Health Check**:
```python
# Checks for 'python -m codex_cli --version'
# Returns availability status and capabilities
```

### 4. Claude Code CLI Engine

**File**: `backend/app/services/engines/claude_code_cli_engine.py`

**Features**:
- Uses Anthropic Claude API (Claude 3.5 Sonnet)
- Similar execution pattern to Codex engine
- Subprocess execution with streaming
- Artifact collection
- ANTHROPIC_API_KEY environment variable

**Model**: `claude-3-5-sonnet-20241022`

**Capabilities**:
- Code generation
- Code execution
- File operations
- Data analysis
- Long context (200k tokens)
- Advanced reasoning

---

## API Integration

### 1. Schema Updates

**File**: `backend/app/schemas/agent_schemas.py`

**Added Field**:
```python
class AgentTaskCreate(BaseModel):
    # ... existing fields ...
    engine: Optional[str] = Field(
        "default",
        description="Execution engine: default, codex-cli, or claude-code-cli"
    )
```

### 2. Service Updates

**File**: `backend/app/services/agent_service.py`

**Changes**:

#### 1. Engine Validation in `create_task()`
```python
# Validate and normalize engine selection
engine = (request.engine or "default").lower()
valid_engines = ["default", "codex-cli", "claude-code-cli"]
if engine not in valid_engines:
    logger.warning(f"⚠️ Invalid engine '{engine}', defaulting to 'default'")
    engine = "default"

# Pass engine to execution
asyncio.create_task(self._execute_task_async(task_id, engine))
```

#### 2. Router Method: `_execute_task_async()`
```python
async def _execute_task_async(self, task_id: str, engine: str = "default"):
    """Route to appropriate engine"""
    if engine == "default":
        await self._execute_task_default_engine(task_id)
    elif engine in ["codex-cli", "claude-code-cli"]:
        await self._execute_task_cli_engine(task_id, engine)
    else:
        logger.error(f"❌ Unknown engine: {engine}")
        await self._execute_task_default_engine(task_id)  # Fallback
```

#### 3. Default Engine Execution
```python
async def _execute_task_default_engine(self, task_id: str):
    """Execute using existing agent-runtime Docker container"""
    # Original implementation unchanged
    # Executes: docker exec rag-agent-runtime python /app/entrypoint_agent.py
```

#### 4. CLI Engine Execution
```python
async def _execute_task_cli_engine(self, task_id: str, engine: str):
    """Execute using CLI engine (Codex or Claude Code)"""

    # Create workspace and artifacts directories
    workspace_path = f"/workspace/{task.task_name or task_id}"
    artifacts_path = f"{workspace_path}/artifacts"

    # Instantiate engine
    if engine == "codex-cli":
        cli_engine = CodexCLIEngine()
    elif engine == "claude-code-cli":
        cli_engine = ClaudeCodeCLIEngine()

    # Execute task
    result_dict = await cli_engine.execute(
        task_description=task.task_description,
        workspace_path=workspace_path,
        artifacts_path=artifacts_path,
        max_iterations=task.max_iterations,
        timeout_seconds=task.timeout_seconds,
        model=task.model
    )

    # Update task with results
    if result_dict.get("success"):
        task.status = TaskStatus.COMPLETED
        task.result = result_dict.get("result")
        task.artifacts = result_dict.get("artifacts", [])
    else:
        task.status = TaskStatus.FAILED
        task.error = result_dict.get("error")
```

---

## Usage

### API Request Example

```bash
curl -X POST "http://localhost:8000/api/v1/agents/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Create a Python script that analyzes sales data",
    "session_id": "session-123",
    "document_ids": ["doc-uuid-1"],
    "max_iterations": 20,
    "timeout_seconds": 600,
    "model": "claude-3-5-sonnet-20241022",
    "engine": "claude-code-cli"
  }'
```

### Response

```json
{
  "task_id": "task-abc123",
  "status": "pending",
  "message": "Task created and queued for execution",
  "created_at": "2025-12-13T10:00:00Z"
}
```

### Status Check

```bash
curl "http://localhost:8000/api/v1/agents/tasks/task-abc123"
```

---

## File Structure

```
backend/app/
├── services/
│   ├── engines/
│   │   ├── __init__.py                  # Package initialization
│   │   ├── base.py                      # Abstract base class & EngineType enum
│   │   ├── default_engine.py            # Default LangGraph wrapper
│   │   ├── codex_cli_engine.py          # OpenAI Codex CLI implementation
│   │   └── claude_code_cli_engine.py    # Anthropic Claude Code CLI implementation
│   │
│   └── agent_service.py                 # Updated orchestration service
│
└── schemas/
    └── agent_schemas.py                 # Updated with engine field
```

---

## Testing

### Health Check Endpoint

```python
# Add to agent routes:
@router.get("/api/v1/agents/engines/health")
async def check_engines_health():
    """Check availability of all engines"""
    from app.services.engines import (
        DefaultAgentEngine,
        CodexCLIEngine,
        ClaudeCodeCLIEngine
    )

    default = await DefaultAgentEngine().health_check()
    codex = await CodexCLIEngine().health_check()
    claude = await ClaudeCodeCLIEngine().health_check()

    return {
        "engines": {
            "default": default,
            "codex-cli": codex,
            "claude-code-cli": claude
        }
    }
```

### Test Execution

```python
# Test each engine
test_engines = ["default", "codex-cli", "claude-code-cli"]

for engine in test_engines:
    response = client.post("/api/v1/agents/tasks", json={
        "task_description": "Print 'Hello World'",
        "engine": engine
    })
    task_id = response.json()["task_id"]

    # Poll for completion
    while True:
        status = client.get(f"/api/v1/agents/tasks/{task_id}").json()
        if status["status"] in ["completed", "failed"]:
            break
        time.sleep(1)
```

---

## Next Steps

### ✅ Completed

1. ✅ Create AgentEngine base class
2. ✅ Implement DefaultAgentEngine wrapper
3. ✅ Implement CodexCLIEngine
4. ✅ Implement ClaudeCodeCLIEngine
5. ✅ Update AgentTaskCreate schema with engine field
6. ✅ Update AgentOrchestrationService for engine routing
7. ✅ Add CLI engine execution method

### ✅ Phase 1 Complete

1. ✅ **Frontend UI**: Engine selector dropdown added
   - Location: `frontend/src/components/AgentTaskMonitor.tsx`
   - Component: Three-option dropdown (Default, Codex CLI, Claude Code CLI)
   - Default: "default"

2. ✅ **Engine Architecture**: Complete abstraction layer
   - Base class: `AgentEngine` with standard interface
   - Three implementations: Default, Codex CLI, Claude Code CLI
   - Service routing: `_execute_task_cli_engine()` method

3. ✅ **Container Integration**: Reuse existing agent-runtime
   - CLI engines execute via `docker exec rag-agent-runtime`
   - No new containers needed
   - Maintains existing security isolation

### ⏸️ Phase 2 Pending

1. **Dockerfile Updates**: Install CLI tools in agent-runtime
   ```dockerfile
   # backend/Dockerfile.agent-runtime

   # Install Node.js (required for Claude Code CLI)
   RUN apt-get update && apt-get install -y \
       nodejs \
       npm \
       && rm -rf /var/lib/apt/lists/*

   # Install Claude Code CLI
   RUN npm install -g @anthropic-ai/claude-code-cli

   # Install OpenAI CLI
   RUN pip install openai-cli

   # Verify installations
   RUN claude --version || echo "Claude CLI not found"
   RUN openai --version || echo "OpenAI CLI not found"
   ```

2. **Environment Variables**: Add to `.env` and docker-compose.yml
   ```bash
   # .env
   ANTHROPIC_API_KEY=sk-ant-...
   OPENAI_API_KEY=sk-...
   ```

   ```yaml
   # docker-compose.yml
   rag-agent-runtime:
     environment:
       - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
       - OPENAI_API_KEY=${OPENAI_API_KEY}
   ```

3. **Interactive Authentication Flow**:
   - Detect auth prompts from CLI stdout
   - Send auth URL to frontend via WebSocket
   - Receive auth key from frontend via WebSocket
   - Pass key to CLI stdin
   - Continue execution

   **Required Components**:
   - WebSocket bidirectional enhancement
   - Auth URL detection (regex parsing)
   - Frontend auth UI (URL display + key input)
   - Stdin/stdout bridge

4. **API Documentation**: Update Swagger docs
   - Document new `engine` parameter
   - Add engine health check endpoint
   - Provide usage examples

5. **Integration Tests**:
   - Test engine selection
   - Test engine fallback behavior
   - Test error handling for unavailable engines
   - Test artifact collection for CLI engines
   - Test interactive authentication flow

6. **WebSocket Streaming**: Integrate stream_events()
   - Already implemented in CLI engines
   - Need WebSocket endpoint for real-time updates
   - Stream events from CLI engine execution
   - Display in Task Details UI

---

## Engine Comparison

| Feature | DEFAULT | CODEX-CLI | CLAUDE-CODE-CLI |
|---------|---------|-----------|-----------------|
| **Model** | qwen2.5-coder:7b (local) | gpt-4-turbo-preview | claude-3-5-sonnet-20241022 |
| **Execution** | Docker container | CLI subprocess | CLI subprocess |
| **Context** | ~8k tokens | ~128k tokens | ~200k tokens |
| **Cost** | Free (local) | $$ (OpenAI API) | $$ (Anthropic API) |
| **Tools** | 13 custom tools | OpenAI code interpreter | Claude code capabilities |
| **Streaming** | Logs only | JSON events + logs | JSON events + logs |
| **Artifacts** | File system | File system | File system |
| **Cancellation** | Process kill | Process kill | Process kill |

---

## Technical Notes

### 1. Subprocess Management

All CLI engines use `asyncio.create_subprocess_exec`:
- Non-blocking execution
- Streaming stdout/stderr
- Timeout support
- Environment variable passing

### 2. Event Streaming

CLI engines support two output modes:

**JSON Events**:
```json
{"type": "thinking", "thought": "...", "iteration": 1}
{"type": "tool_use", "tool_name": "...", "tool_input": {...}}
{"type": "tool_result", "result": "...", "success": true}
```

**Plain Text Logs**:
```
Processing task...
Executing Python code...
Task completed successfully
```

### 3. Error Handling

- Invalid engine → fallback to DEFAULT
- CLI not installed → error in health check
- Execution timeout → task marked as FAILED
- Process crash → captured in stderr

### 4. API Key Management

- Codex: Reads `OPENAI_API_KEY` from environment
- Claude: Reads `ANTHROPIC_API_KEY` from environment
- Passed to subprocess via environment variables
- Never stored in database

---

## Known Limitations

1. **CLI Availability**: Codex CLI and Claude Code CLI must be installed separately
   - Not included in current Docker images
   - Requires manual installation
   - Health check will show `available: false` if not installed

2. **Model Configuration**: Models are hardcoded in engine classes
   - Codex: `gpt-4-turbo-preview`
   - Claude: `claude-3-5-sonnet-20241022`
   - Can override via `model` parameter in request

3. **Artifact Paths**: Assumes file system access
   - CLI engines write to `/workspace/{task_name}/artifacts/`
   - May need volume mounts for Docker execution

4. **Process Tracking**: Basic implementation
   - No detailed progress updates during CLI execution
   - Relies on CLI output parsing

---

## Future Enhancements

### 1. Dynamic Engine Registration

Allow adding new engines without code changes:

```python
# registry.py
ENGINES = {
    "default": DefaultAgentEngine,
    "codex-cli": CodexCLIEngine,
    "claude-code-cli": ClaudeCodeCLIEngine,
    # Add more engines here
}
```

### 2. Engine Configuration

Per-engine settings in database:

```python
class EngineConfig(Base):
    __tablename__ = "engine_configs"

    engine_name = Column(String, primary_key=True)
    enabled = Column(Boolean, default=True)
    config = Column(JSONB)  # Model, timeouts, etc.
```

### 3. Cost Tracking

Track API costs per engine:

```python
class EngineUsage(Base):
    __tablename__ = "engine_usage"

    task_id = Column(String, ForeignKey("agent_tasks.task_id"))
    engine = Column(String)
    tokens_used = Column(Integer)
    estimated_cost = Column(Float)
```

### 4. Engine Selection UI

Smart engine recommendation based on:
- Task complexity
- Required context length
- User budget
- Engine availability

---

## References

- Base Implementation: `backend/app/services/engines/base.py`
- Service Integration: `backend/app/services/agent_service.py`
- Schema Definition: `backend/app/schemas/agent_schemas.py`
- Feature Spec: `docs/features/STREAMING_AND_CLI_AGENTS_IMPLEMENTATION_STATUS.md`

---

## Conclusion

The CLI engines implementation is **complete on the backend**, providing:

✅ Flexible engine selection via API
✅ Clean abstraction with AgentEngine base class
✅ Support for OpenAI Codex and Anthropic Claude Code
✅ Backward compatibility with existing DEFAULT engine
✅ Unified API interface across all engines

**Next Priority**: Frontend UI engine selector and Docker CLI installation.
