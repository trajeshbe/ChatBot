# Claude Code Integration - Implementation Plan

> **Status**: 🟡 Planning Phase
> **Last Updated**: 2025-11-30
> **Owner**: System Architect
> **Priority**: P1 - High Impact Feature

---

## 📋 Executive Summary

This document outlines the implementation plan for integrating autonomous coding agent capabilities into the RAG chatbot, enabling it to handle complex tasks like:

- **Exploratory Data Analysis (EDA)** on uploaded datasets
- **Complex vision tasks** with multi-step processing
- **Code generation** for custom scripts and applications
- **Multi-file project creation** with full autonomy
- **Research and investigation** tasks requiring multiple tools

---

## 🎯 Goals and Non-Goals

### Goals
✅ Enable autonomous code execution for complex tasks
✅ Provide seamless UX with checkbox toggle ("Use Claude Code")
✅ Return executable results (scripts, visualizations, reports) to UI
✅ Maintain security through Docker-in-Docker isolation
✅ Support both local LLM fallback and full Claude API mode

### Non-Goals
❌ Replace existing RAG functionality (this enhances it)
❌ Support arbitrary code execution without sandboxing
❌ Implement full IDE features in the browser

---

## 🏗️ Architecture Overview

### Three-Tier Approach

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE (Frontend)                      │
│  ┌────────────────────┐    ┌────────────────────┐                       │
│  │  Chat Interface    │    │  Agent Execution   │                       │
│  │  with Checkbox:    │    │  Streaming View    │                       │
│  │  □ Use Claude Code │    │  (terminal output) │                       │
│  └────────────────────┘    └────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     ENHANCED RAG AGENT (Backend)                         │
│                                                                          │
│  User Query → Complexity Analyzer                                       │
│                      │                                                   │
│      ┌───────────────┴───────────────┐                                  │
│      │                               │                                  │
│   Simple/Medium                   Complex                               │
│   (existing flow)              (agent flow)                             │
│      │                               │                                  │
│      ├─ Direct LLM           ┌──────┴──────┐                           │
│      ├─ RAG Pipeline         │             │                           │
│      └─ Single Tool   Option 1 (Local)  Option 2 (CLI)                 │
│                               │             │                           │
│                        Mini Agent Loop  Claude Code CLI                 │
│                               │             │                           │
└───────────────────────────────┼─────────────┼───────────────────────────┘
                                │             │
                                ▼             ▼
                    ┌─────────────────────────────────┐
                    │   Docker-in-Docker Sandbox      │
                    │   (Isolated Execution)          │
                    │                                 │
                    │   - File System (workspace/)    │
                    │   - Python 3.11 + common libs   │
                    │   - Network isolation           │
                    │   - Resource limits (CPU/RAM)   │
                    └─────────────────────────────────┘
                                │
                                ▼
                    ┌─────────────────────────────────┐
                    │   MinIO Storage                 │
                    │   - Generated scripts           │
                    │   - Visualizations (PNG, HTML)  │
                    │   - Reports (PDF, MD)           │
                    │   - Datasets (CSV, JSON)        │
                    └─────────────────────────────────┘
                                │
                                ▼
                    ┌─────────────────────────────────┐
                    │   Results Viewer (Frontend)     │
                    │   - Interactive notebooks       │
                    │   - Downloadable artifacts      │
                    │   - Execution logs              │
                    └─────────────────────────────────┘
```

---

## 📦 Implementation Options

### **Option 1: Local Mini Agent (RECOMMENDED FOR MVP)**

**Pros**:
- ✅ Lower cost (use Ollama for tool selection, Claude for generation)
- ✅ Full control over agent loop
- ✅ Easier to customize for your use cases
- ✅ Faster iteration during development
- ✅ Integrates seamlessly with existing `EnhancedRAGAgent`

**Cons**:
- ⚠️ Need to build and maintain agent loop
- ⚠️ Requires defining custom tools
- ⚠️ Quality depends on your prompting

**Best For**:
- Data analysis scripts (Pandas, NumPy, Matplotlib)
- Simple code generation (functions, classes)
- File transformations (CSV → JSON, etc.)
- Quick visualizations

**Implementation Time**: 2-3 weeks

---

### **Option 2: Full Claude Code CLI**

**Pros**:
- ✅ Production-ready, maintained by Anthropic
- ✅ Pre-built tools (Bash, Read, Write, Edit, etc.)
- ✅ Proven agent loop with self-correction
- ✅ Handles complex multi-step tasks

**Cons**:
- ⚠️ Higher API costs (full Claude usage)
- ⚠️ Less customization flexibility
- ⚠️ Docker-in-Docker complexity
- ⚠️ Requires parsing CLI output

**Best For**:
- Research tasks (web search + synthesis)
- Complex refactoring across multiple files
- Full application scaffolding
- Tasks requiring 10+ steps

**Implementation Time**: 4-6 weeks

---

### **Hybrid Approach (RECOMMENDED FOR PRODUCTION)**

Start with **Option 1** for MVP, then add **Option 2** for specific complex use cases:

```python
if task_complexity == "COMPLEX" and task_type in ["RESEARCH", "FULL_APPLICATION"]:
    use_claude_code_cli()
else:
    use_local_mini_agent()
```

---

## 🔧 Phase 1: Foundation (Week 1-2)

### 1.1 Complexity Classification ✅ (Already Created)

- **File**: `backend/app/services/task_complexity_analyzer.py`
- **Purpose**: Classify queries as SIMPLE, MEDIUM, or COMPLEX
- **Integration Point**: Called before `EnhancedRAGAgent.run()`

### 1.2 Mini Agent Loop (Option 1)

**File**: `backend/app/agents/mini_coding_agent.py`

**Key Components**:
1. **Tool Definitions** (Anthropic API format)
   - `execute_python`: Run Python code in sandbox
   - `read_file`: Read file from workspace
   - `write_file`: Write file to workspace
   - `install_package`: Install Python package (pip)
   - `run_bash`: Execute bash command (restricted)

2. **Agentic Loop**
   - Initialize Docker sandbox
   - Call Claude with tools
   - Execute tool calls in sandbox
   - Stream results to frontend (via Redis pub/sub)
   - Return final artifacts

3. **Safety Layer**
   - Command filtering (block dangerous commands)
   - Path traversal protection
   - Resource limits (2GB RAM, 1 CPU core, 10-minute timeout)
   - Network isolation (optional)

### 1.3 Docker Sandbox Manager

**File**: `backend/app/services/sandbox_manager.py`

**Key Features**:
- Spin up Python 3.11 containers on demand
- Mount workspace volume (`/workspace`)
- Execute commands with timeout
- Capture stdout/stderr
- Clean up after completion

**Docker-in-Docker Setup**:
```yaml
# docker-compose.yml addition
services:
  backend:
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # Docker-in-Docker
```

**Sandbox Base Image**:
```dockerfile
# sandbox-base/Dockerfile
FROM python:3.11-slim

# Install common data science packages
RUN pip install --no-cache-dir \
    pandas numpy matplotlib seaborn \
    scikit-learn jupyter plotly \
    requests beautifulsoup4

# Security: Non-root user
RUN useradd -m -u 1000 sandbox
USER sandbox

WORKDIR /workspace
```

---

## 🚀 Phase 2: Frontend Integration (Week 2)

### 2.1 UI Components

**1. Checkbox Toggle**

Add to `ChatInterface.tsx`:
```typescript
const [useAgentMode, setUseAgentMode] = useState(false);

<label className="flex items-center gap-2">
  <input
    type="checkbox"
    checked={useAgentMode}
    onChange={(e) => setUseAgentMode(e.target.checked)}
  />
  <span>🤖 Use Claude Code (for complex tasks)</span>
</label>
```

**2. Streaming Terminal Component**

New component: `StreamingTerminal.tsx`
- Displays real-time tool execution
- Shows stdout/stderr with ANSI colors
- Displays file operations
- Shows thinking/reasoning steps

**3. Results Viewer**

New component: `AgentResultsViewer.tsx`
- File browser for generated artifacts
- Inline preview for images/HTML
- Download buttons
- Execution summary

### 2.2 WebSocket Integration

Use existing Redis pub/sub pattern:

```typescript
// Subscribe to agent events
const ws = new WebSocket(`ws://localhost:8000/ws/agent/${taskId}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case 'thinking':
      // Show Claude's reasoning
      break;
    case 'tool_call':
      // Show tool being executed
      break;
    case 'tool_result':
      // Show tool output
      break;
    case 'artifact_created':
      // Show new file created
      break;
    case 'completed':
      // Show final summary
      break;
  }
};
```

---

## 🛠️ Phase 3: Backend Implementation (Week 2-3)

### 3.1 Enhance RAG Agent Router

**Modify**: `backend/app/agents/enhanced_rag_agent.py`

```python
async def run(
    self,
    query: str,
    session_id: Optional[str] = None,
    user_preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Execute agent workflow with optional autonomous coding"""

    # Check if user enabled agent mode
    use_agent_mode = user_preferences.get('use_agent_mode', False)

    if use_agent_mode:
        # Analyze complexity
        from app.services.task_complexity_analyzer import task_complexity_analyzer

        complexity, task_type, metadata = task_complexity_analyzer.analyze(
            query=query,
            conversation_history=conversation_history,
            uploaded_files=uploaded_files
        )

        # Route to agent if complex
        if complexity in [TaskComplexity.MEDIUM, TaskComplexity.COMPLEX]:
            logger.info(f"🤖 Routing to agent: complexity={complexity}, type={task_type}")

            # Use Mini Agent (Option 1)
            from app.agents.mini_coding_agent import mini_coding_agent

            result = await mini_coding_agent.run(
                query=query,
                task_type=task_type,
                session_id=session_id,
                user_preferences=user_preferences
            )

            return result

    # Existing RAG flow for simple tasks
    ...
```

### 3.2 Mini Coding Agent

**Create**: `backend/app/agents/mini_coding_agent.py`

**Key Methods**:

```python
class MiniCodingAgent:
    async def run(self, query: str, task_type: str, session_id: str):
        """Execute autonomous coding task"""

        # 1. Start sandbox
        sandbox = await self.sandbox_manager.create_sandbox(session_id)

        # 2. Run agentic loop
        result = await self._agentic_loop(
            query=query,
            sandbox=sandbox,
            max_iterations=20
        )

        # 3. Upload artifacts to MinIO
        artifacts = await self._collect_artifacts(sandbox)
        artifact_urls = await self._upload_artifacts(artifacts, session_id)

        # 4. Cleanup
        await sandbox.cleanup()

        return {
            "answer": result["final_response"],
            "artifacts": artifact_urls,
            "execution_log": result["events"],
            "metadata": {
                "tool_calls": len(result["tool_calls"]),
                "iterations": result["iterations"],
                "execution_time_ms": result["execution_time_ms"]
            }
        }

    async def _agentic_loop(self, query: str, sandbox, max_iterations: int):
        """Main agent loop with tool calling"""

        conversation_history = [{"role": "user", "content": query}]

        for iteration in range(max_iterations):
            # Call Claude with tools
            response = await self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=self._build_system_prompt(),
                tools=self.tools,
                messages=conversation_history
            )

            # Check termination
            if response.stop_reason == "end_turn":
                return self._extract_final_response(response)

            # Execute tool calls
            if response.stop_reason == "tool_use":
                tool_results = await self._execute_tools(response, sandbox)

                # Add to history
                conversation_history.append({
                    "role": "assistant",
                    "content": response.content
                })
                conversation_history.append({
                    "role": "user",
                    "content": tool_results
                })

                # Stream to frontend
                await self._publish_event(session_id, {
                    "type": "iteration",
                    "iteration": iteration,
                    "tool_calls": tool_results
                })

        return {"error": "Max iterations reached"}
```

### 3.3 Sandbox Manager

**Create**: `backend/app/services/sandbox_manager.py`

```python
import docker
from pathlib import Path

class SandboxManager:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.active_sandboxes = {}

    async def create_sandbox(self, session_id: str) -> "Sandbox":
        """Spin up isolated Docker container"""

        workspace = Path(f"/tmp/agent_workspaces/{session_id}")
        workspace.mkdir(parents=True, exist_ok=True)

        container = self.docker_client.containers.run(
            "chatbot-sandbox-base:latest",  # Pre-built image
            command="tail -f /dev/null",  # Keep alive
            detach=True,
            working_dir="/workspace",
            volumes={
                str(workspace): {"bind": "/workspace", "mode": "rw"}
            },
            mem_limit="2g",
            cpu_period=100000,
            cpu_quota=50000,  # 50% of 1 core
            network_mode="none",  # Isolated (or "bridge" if need internet)
            remove=False  # Keep for debugging
        )

        sandbox = Sandbox(container, workspace, session_id)
        self.active_sandboxes[session_id] = sandbox

        return sandbox

class Sandbox:
    def __init__(self, container, workspace, session_id):
        self.container = container
        self.workspace = workspace
        self.session_id = session_id

    async def execute_python(self, code: str, timeout: int = 30) -> dict:
        """Execute Python code in sandbox"""

        # Write code to temp file
        code_file = self.workspace / "temp_script.py"
        code_file.write_text(code)

        # Execute in container
        exit_code, output = self.container.exec_run(
            f"python /workspace/temp_script.py",
            workdir="/workspace",
            stream=False,
            demux=True
        )

        stdout, stderr = output

        return {
            "success": exit_code == 0,
            "stdout": stdout.decode("utf-8") if stdout else "",
            "stderr": stderr.decode("utf-8") if stderr else "",
            "exit_code": exit_code
        }

    async def read_file(self, path: str) -> str:
        """Read file from workspace"""
        file_path = self.workspace / path.lstrip("/")

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        return file_path.read_text()

    async def write_file(self, path: str, content: str):
        """Write file to workspace"""
        file_path = self.workspace / path.lstrip("/")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)

    async def cleanup(self):
        """Stop and remove container"""
        self.container.stop()
        self.container.remove()
```

---

## 📊 Database Schema Updates

Add new tables for agent execution tracking:

```sql
-- Agent tasks
CREATE TABLE agent_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    user_id UUID REFERENCES users(id),
    query TEXT NOT NULL,
    task_type VARCHAR(50),  -- 'data_analysis', 'code_generation', etc.
    complexity VARCHAR(20),  -- 'SIMPLE', 'MEDIUM', 'COMPLEX'
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'failed'
    agent_type VARCHAR(50),  -- 'mini_agent', 'claude_code_cli'
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    execution_time_ms FLOAT
);

-- Agent execution events (for streaming)
CREATE TABLE agent_events (
    id SERIAL PRIMARY KEY,
    task_id UUID REFERENCES agent_tasks(id) ON DELETE CASCADE,
    event_type VARCHAR(50),  -- 'thinking', 'tool_call', 'tool_result', 'artifact_created'
    payload JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Generated artifacts
CREATE TABLE agent_artifacts (
    id SERIAL PRIMARY KEY,
    task_id UUID REFERENCES agent_tasks(id) ON DELETE CASCADE,
    filename VARCHAR(255),
    file_path VARCHAR(512),
    file_size BIGINT,
    mime_type VARCHAR(100),
    minio_url VARCHAR(1024),
    preview_available BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_agent_tasks_session ON agent_tasks(session_id);
CREATE INDEX idx_agent_events_task ON agent_events(task_id);
CREATE INDEX idx_agent_artifacts_task ON agent_artifacts(task_id);
```

---

## 🎨 UI/UX Flow

### User Journey

1. **User uploads CSV** → "Perform comprehensive EDA on this dataset"
2. **Checks "Use Claude Code" checkbox**
3. **Submits query**
4. **UI shows**:
   - Complexity detected: COMPLEX
   - Task type: Data Analysis
   - Estimated steps: 10
   - Starting autonomous agent...
5. **Streaming terminal shows**:
   ```
   🤔 Thinking: I'll analyze this dataset step by step...

   🔧 Tool: execute_python
   Code: import pandas as pd
         df = pd.read_csv('/workspace/data.csv')
         print(df.head())

   ✅ Output:
      col1  col2  col3
   0    1     2     3
   ...

   🔧 Tool: execute_python
   Code: df.describe()
   ...

   📊 Creating visualization: distribution.png

   ✅ Analysis complete!
   ```
6. **Results panel shows**:
   - 📄 `eda_report.md` (summary)
   - 📊 `distribution.png` (chart)
   - 📈 `correlation_matrix.png` (heatmap)
   - 🐍 `analysis_script.py` (reproducible code)
   - [Download All]

---

## 🔒 Security Considerations

### 1. Sandbox Isolation
- ✅ Docker container per session
- ✅ No network access (or restricted)
- ✅ Resource limits (CPU, RAM, disk)
- ✅ Timeout enforcement

### 2. Command Filtering
```python
BLOCKED_PATTERNS = [
    r"rm\s+-rf\s+/",  # Delete root
    r"mkfs",          # Format disk
    r"dd\s+if=",      # Disk operations
    r":\(\)\{",       # Fork bomb
    r"curl.*\|.*sh",  # Remote script execution
]
```

### 3. Path Traversal Protection
```python
def validate_path(path: str, workspace: Path) -> bool:
    resolved = (workspace / path).resolve()
    return str(resolved).startswith(str(workspace))
```

### 4. Token Budget Limits
```python
MAX_TOKENS_PER_TASK = 100_000  # Prevent runaway costs
if total_tokens > MAX_TOKENS_PER_TASK:
    raise Exception("Token budget exceeded")
```

---

## 💰 Cost Analysis

### Option 1: Mini Agent (Local)

**Per Complex Task**:
- Tool selection: Ollama (free)
- Code generation: Claude Sonnet (~20K tokens) = $0.60
- **Total**: ~$0.60 per task

### Option 2: Full Claude Code CLI

**Per Complex Task**:
- Full agent loop: Claude Sonnet (~50K tokens) = $1.50
- **Total**: ~$1.50 per task

**Monthly Estimate** (100 complex tasks/month):
- Option 1: $60/month
- Option 2: $150/month

---

## 📈 Success Metrics

### Phase 1 MVP (Weeks 1-3)
- ✅ Complexity classifier accuracy > 85%
- ✅ Mini agent can handle 3 task types (data analysis, code gen, vision)
- ✅ Sandbox spins up < 3 seconds
- ✅ Artifacts uploaded to MinIO successfully
- ✅ Streaming events display in real-time

### Phase 2 Production (Week 4+)
- ✅ Handle 50+ concurrent agent tasks
- ✅ 95% task completion rate (no crashes)
- ✅ Average execution time < 2 minutes
- ✅ User satisfaction > 80%

---

## 🚧 Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Runaway costs (infinite loops) | High | Medium | Token budgets, max iterations, timeouts |
| Docker-in-Docker security | High | Low | Network isolation, command filtering, non-root containers |
| Poor agent performance | Medium | Medium | Start with Option 1, improve prompts iteratively |
| UI/UX complexity | Medium | Low | Progressive disclosure (hide unless checked) |
| Storage costs (MinIO) | Low | Low | Cleanup old artifacts after 30 days |

---

## 🗓️ Implementation Timeline

### Week 1: Foundation
- ✅ Day 1-2: Complexity classifier (DONE)
- ⬜ Day 3-4: Sandbox manager + Docker setup
- ⬜ Day 5: Mini agent skeleton

### Week 2: Core Agent
- ⬜ Day 1-3: Agentic loop with tool calling
- ⬜ Day 4-5: Streaming events + Redis pub/sub

### Week 3: Frontend + Testing
- ⬜ Day 1-2: UI components (checkbox, terminal, results)
- ⬜ Day 3-4: End-to-end testing
- ⬜ Day 5: Documentation + demo

### Week 4: Production Hardening (if needed)
- ⬜ Scale testing (50 concurrent tasks)
- ⬜ Security audit
- ⬜ Cost optimization
- ⬜ (Optional) Add Option 2 for specific use cases

---

## 📚 References

- Your reference doc: `docs/claude_code_integration_ideas/Claude_Integration_Ideas.md`
- Anthropic Tool Use Guide: https://docs.anthropic.com/en/docs/build-with-claude/tool-use
- Docker SDK for Python: https://docker-py.readthedocs.io/
- Existing agent: `backend/app/agents/enhanced_rag_agent.py`

---

## ✅ Next Steps

1. **Review this plan** - Confirm architecture and priorities
2. **Choose option** - Start with Option 1 (Mini Agent) or Option 2 (CLI)?
3. **Set up Docker base image** - Build `chatbot-sandbox-base:latest`
4. **Implement Sandbox Manager** - Test Docker-in-Docker locally
5. **Build Mini Agent skeleton** - Prove end-to-end flow
6. **Iterate on prompts** - Improve agent performance

---

**Questions?** Let's discuss before we start building! 🚀
