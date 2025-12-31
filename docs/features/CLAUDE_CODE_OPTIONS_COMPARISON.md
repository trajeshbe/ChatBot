# Claude Code Integration - Options Comparison

> **Decision Framework**: Choosing between local mini agent vs full Claude Code CLI

---

## 🎯 Quick Recommendation

### For MVP (Next 2-3 weeks)
**Start with Option 1: Local Mini Agent**

**Why?**
- ✅ Faster to build and iterate
- ✅ Lower costs during development
- ✅ Full control for debugging
- ✅ Seamlessly integrates with your existing `EnhancedRAGAgent`
- ✅ Good enough for 80% of use cases

### For Production Scale (Month 2+)
**Add Option 2 selectively** for specific complex use cases like:
- Long-running research tasks (10+ tool calls)
- Multi-repository code analysis
- Tasks requiring self-correction loops

---

## 📊 Detailed Comparison

| Feature | Option 1: Local Mini Agent | Option 2: Claude Code CLI |
|---------|----------------------------|---------------------------|
| **Implementation** | | |
| Complexity | Medium (build agent loop) | High (wrap CLI in Docker) |
| Time to MVP | 2-3 weeks | 4-6 weeks |
| Code to Write | ~1000 lines | ~1500 lines |
| Dependencies | Anthropic SDK, Docker SDK | Claude Code CLI, Docker-in-Docker |
| | | |
| **Cost** | | |
| Per Task (Simple) | $0.10 (tool selection only) | $0.50 (full CLI overhead) |
| Per Task (Complex) | $0.60 (20K tokens) | $1.50 (50K tokens) |
| Monthly (100 tasks) | ~$60 | ~$150 |
| | | |
| **Performance** | | |
| Startup Time | 2-3 seconds (container only) | 5-8 seconds (CLI init) |
| Iteration Speed | Fast (direct API) | Moderate (CLI parsing) |
| Max Token Efficiency | High (you control context) | Lower (CLI adds overhead) |
| | | |
| **Capabilities** | | |
| Code Execution | ✅ Python + Bash | ✅ Full shell access |
| File Operations | ✅ Read/Write/Edit | ✅ Read/Write/Edit/Glob |
| Multi-step Tasks | ✅ Up to 20 iterations | ✅ Up to 50+ iterations |
| Self-correction | ⚠️ Manual (you build it) | ✅ Built-in |
| Error Recovery | ⚠️ Manual retry logic | ✅ Automatic |
| Web Search | ❌ (would need to add) | ✅ (if enabled) |
| Git Operations | ❌ (would need to add) | ✅ Built-in |
| | | |
| **Customization** | | |
| Tool Definition | ✅ Full control | ⚠️ Limited (CLI tools only) |
| Prompt Engineering | ✅ Complete freedom | ⚠️ CLI system prompts |
| Streaming Events | ✅ Custom granularity | ⚠️ Parse CLI output |
| UI Integration | ✅ Native (your design) | ⚠️ Terminal emulation |
| | | |
| **Maintenance** | | |
| Codebase Ownership | You maintain | Anthropic maintains |
| Updates Required | On breaking API changes | On CLI version updates |
| Debugging | Easy (you wrote it) | Harder (black box) |
| Testing | Unit + integration tests | E2E tests only |
| | | |
| **Security** | | |
| Sandbox Isolation | ✅ Docker container | ✅ Docker container |
| Command Filtering | ✅ Your custom rules | ✅ CLI built-in |
| Network Access | ✅ Configurable | ⚠️ CLI defaults |
| Resource Limits | ✅ Full control | ⚠️ CLI config |
| | | |
| **Best For** | | |
| Use Cases | Data analysis, code generation, simple workflows | Research, complex refactoring, multi-repo tasks |
| User Skill Level | Intermediate Python users | Power users, developers |
| Task Complexity | MEDIUM, some COMPLEX | COMPLEX only |

---

## 🏗️ Hybrid Architecture (Recommended)

```python
async def route_to_agent(
    query: str,
    complexity: TaskComplexity,
    task_type: TaskType,
    user_preferences: dict
):
    """Smart routing between agent types"""

    # Simple tasks: Use RAG/LLM directly
    if complexity == TaskComplexity.SIMPLE:
        return await rag_service.query(query)

    # Medium tasks: Use local mini agent
    if complexity == TaskComplexity.MEDIUM:
        return await mini_coding_agent.run(query, task_type)

    # Complex tasks: Route based on type
    if complexity == TaskComplexity.COMPLEX:

        # Research, multi-repo → Claude Code CLI
        if task_type in [TaskType.RESEARCH, "multi_repository"]:
            return await claude_code_cli_agent.run(query)

        # Data analysis, vision, single-file code gen → Mini Agent
        else:
            return await mini_coding_agent.run(query, task_type)
```

**Why This Works**:
- 90% of tasks go through fast, cheap mini agent
- 10% of complex tasks leverage full CLI power
- Best of both worlds: speed + capability

---

## 💡 My Recommendation

### Phase 1 (Weeks 1-3): **Build Option 1 Only**

**Focus**:
1. ✅ Complexity classifier (already done!)
2. ⬜ Sandbox manager with Docker-in-Docker
3. ⬜ Mini agent with 5 core tools:
   - `execute_python`
   - `read_file`
   - `write_file`
   - `install_package`
   - `run_bash`
4. ⬜ Frontend checkbox + streaming terminal
5. ⬜ Results viewer with artifact downloads

**Validate with 3 use cases**:
- ✅ EDA on CSV file
- ✅ Image analysis with vision
- ✅ Simple code generation

**Exit Criteria**:
- 80% task success rate
- < 2 min average execution time
- User can download generated artifacts

### Phase 2 (Week 4+): **Add Option 2 Selectively**

**Only if** you encounter:
- Tasks requiring 20+ tool calls
- Multi-step research workflows
- Git repository operations
- Tasks where mini agent fails repeatedly

**Implementation**:
- Wrap Claude Code CLI in Docker container
- Parse stdout for streaming events
- Use same frontend components (reuse!)

---

## 🚀 Quick Start Guide

### Option 1: Local Mini Agent

**1. Create Sandbox Base Image**
```bash
cd backend
mkdir sandbox-base

cat > sandbox-base/Dockerfile <<EOF
FROM python:3.11-slim

# Install common packages
RUN pip install --no-cache-dir \\
    pandas numpy matplotlib seaborn \\
    scikit-learn plotly requests \\
    pillow opencv-python

RUN useradd -m -u 1000 sandbox
USER sandbox
WORKDIR /workspace
EOF

docker build -t chatbot-sandbox-base:latest sandbox-base/
```

**2. Enable Docker-in-Docker**
```yaml
# docker-compose.yml
services:
  backend:
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```

**3. Test Sandbox**
```python
from app.services.sandbox_manager import SandboxManager

manager = SandboxManager()
sandbox = await manager.create_sandbox("test-session")

result = await sandbox.execute_python("""
import pandas as pd
df = pd.DataFrame({'a': [1,2,3], 'b': [4,5,6]})
print(df.describe())
""")

print(result["stdout"])  # Should see statistics
await sandbox.cleanup()
```

**4. Build Mini Agent**
```python
# See: backend/app/agents/mini_coding_agent.py
# Core loop: Claude API → Tool calls → Sandbox execution → Results
```

---

### Option 2: Claude Code CLI (Future)

**1. Install CLI in Container**
```dockerfile
# worker/Dockerfile
FROM python:3.11-slim

# Install Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Your worker code
COPY . /app
CMD ["python", "worker.py"]
```

**2. Wrap CLI Calls**
```python
import subprocess
import json

def run_claude_code(query: str, workspace: str) -> dict:
    """Execute Claude Code CLI and parse output"""

    result = subprocess.run(
        ["claude-code", "--workspace", workspace, "--prompt", query],
        capture_output=True,
        text=True,
        timeout=600  # 10 min
    )

    # Parse output for artifacts, events, etc.
    return parse_cli_output(result.stdout)
```

---

## 📈 Success Metrics

### Option 1 Goals
- ✅ Handle 80% of complex tasks successfully
- ✅ < $1 per task average
- ✅ < 2 minute execution time
- ✅ 5 tool types supported

### Option 2 Goals (if added)
- ✅ Handle 95% of complex tasks
- ✅ < $2 per task average
- ✅ < 5 minute execution time
- ✅ Full CLI tool suite

---

## 🎓 Learning from Your Reference Doc

Your reference document (`Claude_Integration_Ideas.md`) provides excellent guidance. Key takeaways:

1. **Agentic Loop Pattern** - Both options use this:
   ```
   THINK → PLAN → ACT (tool use) → OBSERVE (results) → Repeat
   ```

2. **Sandbox Isolation** - Critical for security:
   - Docker containers
   - Resource limits
   - Command filtering
   - Path validation

3. **Streaming UX** - Users want to see progress:
   - Real-time tool execution
   - Thinking/reasoning steps
   - File operations
   - Error handling

4. **Artifact Serving** - Results must be accessible:
   - MinIO for storage
   - Public URLs for downloads
   - Preview capabilities

---

## ✅ Decision Matrix

| If you prioritize... | Choose... |
|---------------------|-----------|
| **Speed to market** | Option 1 |
| **Cost efficiency** | Option 1 |
| **Full control** | Option 1 |
| **Rapid iteration** | Option 1 |
| **Production stability** | Option 2 |
| **Complex tasks (20+ steps)** | Option 2 |
| **Research workflows** | Option 2 |
| **Git operations** | Option 2 |

---

## 🎯 Final Recommendation

**Start with Option 1**, validate with real users, then **add Option 2 selectively** if needed.

**Next Steps**:
1. Review the implementation plan: `CLAUDE_CODE_INTEGRATION_IMPLEMENTATION_PLAN.md`
2. Set up Docker-in-Docker locally
3. Build sandbox base image
4. Implement mini agent skeleton
5. Test with EDA use case

**Questions to Answer Before Building**:
- ❓ Which 3 use cases are most important to you? (EDA, code gen, vision, etc.)
- ❓ What's your monthly budget for API costs?
- ❓ Do you need git operations? (if yes, Option 2 becomes more attractive)
- ❓ What's your timeline? (3 weeks → Option 1, 6 weeks → Hybrid)

Let me know your thoughts! 🚀
