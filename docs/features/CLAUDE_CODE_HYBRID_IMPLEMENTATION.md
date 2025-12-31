# Claude Code Integration - Hybrid Implementation Plan

> **Approved**: Hybrid approach with Option 1 (local LLMs) + Option 2 (Claude CLI with API caps)
> **Timeline**: 4-5 weeks for complete hybrid system
> **Cost Model**: Smart routing to minimize API usage

---

## 🎯 Hybrid Architecture Overview

### Intelligent Routing Strategy

```
User Query → Complexity Analyzer
                    │
        ┌───────────┴───────────┐
        │                       │
    SIMPLE/MEDIUM           COMPLEX
        │                       │
        ▼                       ▼
┌────────────────┐    ┌─────────────────────┐
│ Direct RAG/LLM │    │ Agent Router        │
│ (existing)     │    │ (NEW - Smart)       │
└────────────────┘    └──────┬──────────────┘
                              │
                    ┌─────────┴──────────┐
                    │                    │
              Cost-Effective        Maximum Capability
              (Local LLMs)         (Claude API)
                    │                    │
                    ▼                    ▼
        ┌─────────────────────┐  ┌──────────────────────┐
        │ OPTION 1:           │  │ OPTION 2:            │
        │ Local Mini Agent    │  │ Claude Code CLI      │
        │                     │  │                      │
        │ Models:             │  │ Model:               │
        │ - Qwen 2.5 Coder    │  │ - Claude Sonnet 4.5  │
        │ - Llama Vision      │  │                      │
        │ - DeepSeek Coder    │  │ Features:            │
        │                     │  │ - Self-correction    │
        │ Cost: FREE          │  │ - 50+ iterations     │
        │ Speed: FAST         │  │ - Full tool suite    │
        │                     │  │                      │
        │ Best for:           │  │ Cost: $1.50/task     │
        │ - EDA               │  │ (with API cap)       │
        │ - Code generation   │  │                      │
        │ - Vision tasks      │  │ Best for:            │
        │ - 80% of tasks      │  │ - Research           │
        └─────────────────────┘  │ - Multi-file debug   │
                                 │ - 20% edge cases     │
                                 └──────────────────────┘
                    │                    │
                    └─────────┬──────────┘
                              ▼
                    ┌─────────────────────┐
                    │ API Usage Tracker   │
                    │ - Daily limits      │
                    │ - Cost monitoring   │
                    │ - Auto-fallback     │
                    └─────────────────────┘
```

---

## 🏗️ Implementation Plan

### Phase 1: Foundation (Week 1)
**Build shared infrastructure for both options**

#### 1.1 Complexity Analyzer (Already Done! ✅)
- Uses `task_complexity_analyzer.py`

#### 1.2 Agent Router (NEW)
**File**: `backend/app/agents/hybrid_agent_router.py`

```python
"""
Hybrid Agent Router

Intelligently routes tasks between:
- Option 1: Local mini agent (free, fast)
- Option 2: Claude Code CLI (powerful, costly)

Routing logic:
1. Check API budget remaining
2. Evaluate task complexity + type
3. Route to most cost-effective option
4. Fallback if primary option fails
"""

from typing import Dict, Any, Optional
from enum import Enum
import logging

from app.services.task_complexity_analyzer import (
    task_complexity_analyzer,
    TaskComplexity,
    TaskType
)
from app.services.api_usage_tracker import api_usage_tracker

logger = logging.getLogger(__name__)


class AgentOption(str, Enum):
    """Available agent implementations"""
    LOCAL_MINI = "local_mini"      # Option 1: Local LLMs
    CLAUDE_CLI = "claude_cli"      # Option 2: Anthropic CLI
    DIRECT_RAG = "direct_rag"      # Fallback: No agent


class HybridAgentRouter:
    """
    Routes tasks to optimal agent based on:
    - Task complexity & type
    - API budget remaining
    - User preferences
    - Historical success rates
    """

    def __init__(self):
        """Initialize router with usage tracker"""
        self.usage_tracker = api_usage_tracker

        # Routing rules (configurable)
        self.routing_rules = {
            # Option 1 (Local) preferred for these types
            "local_preferred": [
                TaskType.DATA_ANALYSIS,
                TaskType.CODE_GENERATION,
                TaskType.VISION_TASK,
                TaskType.DOCUMENT_PROCESSING
            ],

            # Option 2 (Claude CLI) preferred for these
            "claude_preferred": [
                TaskType.RESEARCH,
                TaskType.WEB_AUTOMATION
            ],

            # Always use local if complexity is MEDIUM
            "local_mandatory_complexity": [
                TaskComplexity.MEDIUM
            ]
        }

    async def route(
        self,
        query: str,
        session_id: str,
        user_preferences: Dict[str, Any] = None
    ) -> tuple[AgentOption, Dict[str, Any]]:
        """
        Route task to optimal agent

        Returns:
            (agent_option, routing_metadata)
        """

        user_preferences = user_preferences or {}

        # Step 1: Analyze complexity
        complexity, task_type, metadata = task_complexity_analyzer.analyze(
            query=query,
            conversation_history=user_preferences.get("conversation_history"),
            uploaded_files=user_preferences.get("uploaded_files")
        )

        # Step 2: Check if agent mode is enabled
        use_agent_mode = user_preferences.get("use_agent_mode", False)

        if not use_agent_mode:
            return (AgentOption.DIRECT_RAG, {
                "reason": "Agent mode not enabled by user",
                "complexity": complexity.value
            })

        # Simple tasks don't need agent
        if complexity == TaskComplexity.SIMPLE:
            return (AgentOption.DIRECT_RAG, {
                "reason": "Task is simple, direct RAG sufficient",
                "complexity": complexity.value
            })

        # Step 3: Check API budget (for Claude CLI)
        daily_budget_remaining = await self.usage_tracker.get_daily_budget_remaining()
        task_estimated_cost = self._estimate_cost(complexity, task_type, AgentOption.CLAUDE_CLI)

        can_afford_claude = daily_budget_remaining >= task_estimated_cost

        logger.info(
            f"💰 Budget check: Remaining ${daily_budget_remaining:.2f}, "
            f"Task estimate ${task_estimated_cost:.2f}, "
            f"Can afford Claude: {can_afford_claude}"
        )

        # Step 4: Apply routing logic
        selected_option, reason = self._apply_routing_rules(
            complexity=complexity,
            task_type=task_type,
            can_afford_claude=can_afford_claude,
            user_preferences=user_preferences
        )

        # Step 5: Build routing metadata
        routing_metadata = {
            "complexity": complexity.value,
            "task_type": task_type.value,
            "selected_option": selected_option.value,
            "reason": reason,
            "estimated_cost": self._estimate_cost(complexity, task_type, selected_option),
            "budget_remaining": daily_budget_remaining,
            "indicators": metadata.get("indicators", [])
        }

        logger.info(
            f"🎯 Routing decision: {selected_option.value} "
            f"(Reason: {reason})"
        )

        return (selected_option, routing_metadata)

    def _apply_routing_rules(
        self,
        complexity: TaskComplexity,
        task_type: TaskType,
        can_afford_claude: bool,
        user_preferences: Dict[str, Any]
    ) -> tuple[AgentOption, str]:
        """Apply routing rules to select agent"""

        # Rule 1: MEDIUM complexity → Always local
        if complexity in self.routing_rules["local_mandatory_complexity"]:
            return (
                AgentOption.LOCAL_MINI,
                f"Medium complexity tasks use local agent for cost efficiency"
            )

        # Rule 2: COMPLEX + Research/Web Automation → Prefer Claude (if budget allows)
        if (complexity == TaskComplexity.COMPLEX and
            task_type in self.routing_rules["claude_preferred"]):

            if can_afford_claude:
                return (
                    AgentOption.CLAUDE_CLI,
                    f"Research/Web tasks benefit from Claude CLI's advanced capabilities"
                )
            else:
                return (
                    AgentOption.LOCAL_MINI,
                    f"Budget limit reached, falling back to local agent"
                )

        # Rule 3: COMPLEX + Data/Code/Vision → Prefer Local (faster, free)
        if (complexity == TaskComplexity.COMPLEX and
            task_type in self.routing_rules["local_preferred"]):

            return (
                AgentOption.LOCAL_MINI,
                f"{task_type.value} tasks work well with local models (Qwen/Llama Vision)"
            )

        # Rule 4: User explicitly requests Claude (via preference)
        force_claude = user_preferences.get("force_claude_cli", False)
        if force_claude and can_afford_claude:
            return (
                AgentOption.CLAUDE_CLI,
                "User explicitly requested Claude CLI"
            )

        # Rule 5: Default to local for cost efficiency
        return (
            AgentOption.LOCAL_MINI,
            "Default to local agent for cost efficiency"
        )

    def _estimate_cost(
        self,
        complexity: TaskComplexity,
        task_type: TaskType,
        agent_option: AgentOption
    ) -> float:
        """Estimate cost for this task"""

        if agent_option == AgentOption.LOCAL_MINI:
            return 0.0  # Free!

        elif agent_option == AgentOption.CLAUDE_CLI:
            # Claude Sonnet 4.5 pricing: $3/MTok input, $15/MTok output
            # Average task uses ~50K tokens (conservative)

            if complexity == TaskComplexity.MEDIUM:
                estimated_tokens = 20_000
            elif complexity == TaskComplexity.COMPLEX:
                estimated_tokens = 50_000
            else:
                estimated_tokens = 5_000

            # Assume 70% input, 30% output
            input_tokens = estimated_tokens * 0.7
            output_tokens = estimated_tokens * 0.3

            cost = (input_tokens / 1_000_000 * 3.0) + (output_tokens / 1_000_000 * 15.0)
            return round(cost, 2)

        else:
            return 0.0


# Global instance
hybrid_agent_router = HybridAgentRouter()
```

#### 1.3 API Usage Tracker
**File**: `backend/app/services/api_usage_tracker.py`

```python
"""
API Usage Tracker

Tracks Anthropic API usage and enforces daily/monthly caps.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class APIUsageTracker:
    """
    Tracks API usage and enforces budget limits

    Features:
    - Daily budget caps
    - Monthly budget caps
    - Real-time usage tracking
    - Auto-fallback when limits reached
    """

    def __init__(self):
        """Initialize tracker with default limits"""

        # Configurable limits (from settings/database)
        self.daily_budget_limit = 10.0   # $10/day default
        self.monthly_budget_limit = 200.0  # $200/month default

        # In-memory tracking (would use Redis in production)
        self.usage_cache = {
            "daily": {"date": None, "spent": 0.0, "tasks": 0},
            "monthly": {"month": None, "spent": 0.0, "tasks": 0}
        }

    async def get_daily_budget_remaining(self) -> float:
        """Get remaining daily budget"""

        today = datetime.now().date()

        # Reset if new day
        if self.usage_cache["daily"]["date"] != today:
            self.usage_cache["daily"] = {
                "date": today,
                "spent": 0.0,
                "tasks": 0
            }

        spent_today = self.usage_cache["daily"]["spent"]
        remaining = max(0, self.daily_budget_limit - spent_today)

        return remaining

    async def get_monthly_budget_remaining(self) -> float:
        """Get remaining monthly budget"""

        current_month = datetime.now().strftime("%Y-%m")

        # Reset if new month
        if self.usage_cache["monthly"]["month"] != current_month:
            self.usage_cache["monthly"] = {
                "month": current_month,
                "spent": 0.0,
                "tasks": 0
            }

        spent_this_month = self.usage_cache["monthly"]["spent"]
        remaining = max(0, self.monthly_budget_limit - spent_this_month)

        return remaining

    async def record_usage(
        self,
        cost: float,
        task_id: str,
        agent_option: str,
        tokens_used: int = 0
    ):
        """Record API usage"""

        today = datetime.now().date()
        current_month = datetime.now().strftime("%Y-%m")

        # Update daily
        if self.usage_cache["daily"]["date"] != today:
            self.usage_cache["daily"] = {
                "date": today,
                "spent": 0.0,
                "tasks": 0
            }

        self.usage_cache["daily"]["spent"] += cost
        self.usage_cache["daily"]["tasks"] += 1

        # Update monthly
        if self.usage_cache["monthly"]["month"] != current_month:
            self.usage_cache["monthly"] = {
                "month": current_month,
                "spent": 0.0,
                "tasks": 0
            }

        self.usage_cache["monthly"]["spent"] += cost
        self.usage_cache["monthly"]["tasks"] += 1

        logger.info(
            f"💳 API Usage Recorded: ${cost:.2f} "
            f"(Daily: ${self.usage_cache['daily']['spent']:.2f}/"
            f"${self.daily_budget_limit:.2f}, "
            f"Monthly: ${self.usage_cache['monthly']['spent']:.2f}/"
            f"${self.monthly_budget_limit:.2f})"
        )

        # TODO: Store in database for persistence

    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""

        daily_remaining = await self.get_daily_budget_remaining()
        monthly_remaining = await self.get_monthly_budget_remaining()

        return {
            "daily": {
                "limit": self.daily_budget_limit,
                "spent": self.usage_cache["daily"]["spent"],
                "remaining": daily_remaining,
                "tasks": self.usage_cache["daily"]["tasks"],
                "percentage_used": (self.usage_cache["daily"]["spent"] / self.daily_budget_limit * 100)
                    if self.daily_budget_limit > 0 else 0
            },
            "monthly": {
                "limit": self.monthly_budget_limit,
                "spent": self.usage_cache["monthly"]["spent"],
                "remaining": monthly_remaining,
                "tasks": self.usage_cache["monthly"]["tasks"],
                "percentage_used": (self.usage_cache["monthly"]["spent"] / self.monthly_budget_limit * 100)
                    if self.monthly_budget_limit > 0 else 0
            }
        }

    async def set_limits(self, daily_limit: float = None, monthly_limit: float = None):
        """Update budget limits"""

        if daily_limit is not None:
            self.daily_budget_limit = daily_limit
            logger.info(f"💰 Daily budget limit updated: ${daily_limit:.2f}")

        if monthly_limit is not None:
            self.monthly_budget_limit = monthly_limit
            logger.info(f"💰 Monthly budget limit updated: ${monthly_limit:.2f}")


# Global instance
api_usage_tracker = APIUsageTracker()
```

---

### Phase 2: Option 1 - Local Mini Agent (Week 2-3)

**Uses local LLMs for cost efficiency**

#### 2.1 Local Model Configuration

**Supported Models**:
1. **Qwen 2.5 Coder (7B/14B)** - Code generation, EDA
2. **Llama Vision (11B)** - Image analysis, OCR
3. **DeepSeek Coder (6.7B)** - Alternative code model

**Setup** (via Ollama):
```bash
# Pull models
ollama pull qwen2.5-coder:7b
ollama pull llama3.2-vision:11b
ollama pull deepseek-coder:6.7b

# Verify
ollama list
```

#### 2.2 Local Agent Implementation

**File**: `backend/app/agents/local_mini_agent.py`

```python
"""
Local Mini Agent (Option 1)

Uses local LLMs via Ollama for cost-free autonomous coding.

Models:
- Qwen 2.5 Coder: Code generation, data analysis
- Llama Vision: Image/vision tasks
- DeepSeek Coder: Backup for coding tasks

Architecture:
- Runs in sandbox container (same as Claude CLI)
- Uses local Ollama instead of Claude API
- Same tool suite (execute_python, read_file, etc.)
"""

from typing import Dict, Any, Optional
import logging
import json
import httpx

logger = logging.getLogger(__name__)


class LocalMiniAgent:
    """
    Mini agent using local LLMs (Ollama)

    Cost: FREE (runs locally)
    Speed: FAST (no API latency)
    Capability: Good for 80% of tasks
    """

    def __init__(self, ollama_url: str = "http://ollama:11434"):
        """Initialize with Ollama connection"""
        self.ollama_url = ollama_url
        self.http_client = httpx.AsyncClient(timeout=300.0)  # 5 min timeout

        # Model selection based on task type
        self.model_mapping = {
            "code": "qwen2.5-coder:7b",
            "vision": "llama3.2-vision:11b",
            "general": "qwen2.5-coder:7b"
        }

    async def run(
        self,
        query: str,
        task_type: str,
        session_id: str,
        user_preferences: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Run local mini agent

        Same interface as Claude CLI agent for consistency
        """

        # Select model based on task type
        model = self._select_model(task_type)

        logger.info(f"🤖 Starting LOCAL mini agent with model: {model}")

        # Create sandbox and run agent loop
        # (Implementation mirrors Claude agent but uses Ollama API)

        # TODO: Implement full agentic loop with Ollama
        # For now, return placeholder

        return {
            "answer": f"Local agent executed with {model}",
            "artifacts": [],
            "metadata": {
                "agent_type": "local_mini",
                "model_used": model,
                "cost": 0.0  # FREE!
            }
        }

    def _select_model(self, task_type: str) -> str:
        """Select appropriate local model for task"""

        if "vision" in task_type.lower() or "image" in task_type.lower():
            return self.model_mapping["vision"]
        else:
            return self.model_mapping["code"]

    async def _call_ollama(
        self,
        model: str,
        messages: list,
        tools: list = None
    ) -> Dict[str, Any]:
        """
        Call Ollama API (same format as OpenAI/Anthropic)

        Ollama supports OpenAI-compatible API
        """

        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }

        if tools:
            payload["tools"] = tools

        response = await self.http_client.post(
            f"{self.ollama_url}/v1/chat/completions",
            json=payload
        )

        return response.json()


# Global instance
local_mini_agent = LocalMiniAgent()
```

---

### Phase 3: Option 2 - Claude Code CLI (Week 3-4)

**Uses official Claude Code CLI for maximum capability**

#### 3.1 Claude CLI Wrapper

**File**: `backend/app/agents/claude_cli_agent.py`

```python
"""
Claude Code CLI Agent (Option 2)

Wraps official @anthropic-ai/claude-code CLI in container.

Features:
- Full Claude Code capabilities
- Self-correction loops
- 50+ iterations
- Complete tool suite

Cost: ~$1.50 per complex task (with API caps)
"""

import subprocess
import json
import asyncio
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class ClaudeCodeCLIAgent:
    """
    Wrapper for official Claude Code CLI

    Runs in sandbox container, parses output for streaming
    """

    def __init__(self):
        """Initialize CLI wrapper"""
        self.cli_path = "claude-code"  # Installed in container

    async def run(
        self,
        query: str,
        task_type: str,
        session_id: str,
        user_preferences: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Run Claude Code CLI in sandbox

        Returns artifacts and execution log
        """

        logger.info(f"🚀 Starting CLAUDE CODE CLI for complex task")

        # Run CLI (inside container)
        workspace = f"/app/workspace"

        command = [
            self.cli_path,
            "--workspace", workspace,
            "--prompt", query,
            "--max-iterations", "50"
        ]

        try:
            # Execute CLI
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            # Parse output
            result = self._parse_cli_output(stdout.decode())

            return result

        except Exception as e:
            logger.error(f"Claude CLI failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _parse_cli_output(self, output: str) -> Dict[str, Any]:
        """Parse Claude Code CLI output"""

        # TODO: Parse CLI output for:
        # - Tool calls
        # - Generated files
        # - Final answer

        return {
            "answer": "Claude CLI completed",
            "artifacts": [],
            "metadata": {
                "agent_type": "claude_cli",
                "model": "claude-sonnet-4.5"
            }
        }


# Global instance
claude_cli_agent = ClaudeCodeCLIAgent()
```

---

### Phase 4: Integration & UI (Week 4-5)

#### 4.1 Update Enhanced RAG Agent

**Modify**: `backend/app/agents/enhanced_rag_agent.py`

```python
async def run(
    self,
    query: str,
    session_id: Optional[str] = None,
    user_preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Execute with hybrid agent routing"""

    use_agent_mode = user_preferences.get('use_agent_mode', False)

    if use_agent_mode:
        # Route to appropriate agent
        from app.agents.hybrid_agent_router import hybrid_agent_router
        from app.agents.local_mini_agent import local_mini_agent
        from app.agents.claude_cli_agent import claude_cli_agent

        agent_option, routing_metadata = await hybrid_agent_router.route(
            query=query,
            session_id=session_id,
            user_preferences=user_preferences
        )

        logger.info(f"🎯 Routed to: {agent_option.value}")

        # Execute selected agent
        if agent_option == "local_mini":
            result = await local_mini_agent.run(
                query, task_type, session_id, user_preferences
            )

        elif agent_option == "claude_cli":
            result = await claude_cli_agent.run(
                query, task_type, session_id, user_preferences
            )

        else:
            # Fallback to direct RAG
            result = await rag_service.query(query, session_id)

        # Add routing metadata
        result["routing"] = routing_metadata

        return result

    # Existing RAG flow
    ...
```

#### 4.2 Frontend UI Enhancements

**Add to** `frontend/src/components/ChatInterface.tsx`:

```typescript
// Agent mode controls
const [useAgentMode, setUseAgentMode] = useState(false);
const [forceClaudeCLI, setForceClaudeCLI] = useState(false);
const [budgetStats, setBudgetStats] = useState(null);

// Fetch budget stats
useEffect(() => {
  fetch('/api/v1/usage/stats')
    .then(res => res.json())
    .then(data => setBudgetStats(data));
}, []);

// UI
<div className="agent-controls">
  <label>
    <input
      type="checkbox"
      checked={useAgentMode}
      onChange={(e) => setUseAgentMode(e.target.checked)}
    />
    🤖 Use Autonomous Agent
  </label>

  {useAgentMode && (
    <div className="agent-options">
      <label>
        <input
          type="checkbox"
          checked={forceClaudeCLI}
          onChange={(e) => setForceClaudeCLI(e.target.checked)}
        />
        Force Claude CLI (costs API credits)
      </label>

      {budgetStats && (
        <div className="budget-display">
          <div>
            Daily: ${budgetStats.daily.spent.toFixed(2)} /
            ${budgetStats.daily.limit.toFixed(2)}
            <ProgressBar
              percentage={budgetStats.daily.percentage_used}
            />
          </div>
          <div>
            Monthly: ${budgetStats.monthly.spent.toFixed(2)} /
            ${budgetStats.monthly.limit.toFixed(2)}
            <ProgressBar
              percentage={budgetStats.monthly.percentage_used}
            />
          </div>
        </div>
      )}
    </div>
  )}
</div>
```

---

## 💰 Hybrid Cost Model

### Routing Decision Tree

```
Task Arrives
    │
    ▼
┌──────────────┐
│ Complexity?  │
└───────┬──────┘
        │
   ┌────┴────┐
   │         │
SIMPLE/   MEDIUM/COMPLEX
MEDIUM        │
   │          ▼
   │    ┌─────────────┐
   │    │ Task Type?  │
   │    └──────┬──────┘
   │           │
   │      ┌────┴────┬────────┬────────┐
   │      │         │        │        │
   │    EDA/Code  Vision  Research  Web
   │      │         │        │        │
   ▼      ▼         ▼        ▼        ▼
┌──────┐ ┌────┐  ┌────┐  ┌──────┐  ┌──────┐
│ RAG  │ │Loc │  │Loc │  │Claud │  │Claud │
│      │ │al  │  │al  │  │e CLI │  │e CLI │
│      │ │    │  │    │  │(if $)│  │(if $)│
└──────┘ └────┘  └────┘  └──────┘  └──────┘
  FREE    FREE    FREE    $1.50    $1.50
```

### Cost Projections

**Scenario 1: 100 tasks/month, mixed complexity**

| Task Type | Count | Agent Used | Cost/Task | Total |
|-----------|-------|------------|-----------|-------|
| Simple (RAG) | 40 | Direct RAG | $0 | $0 |
| Medium (EDA/Code) | 40 | Local Mini | $0 | $0 |
| Complex (Research) | 20 | Claude CLI | $1.50 | $30 |
| **TOTAL** | **100** | - | - | **$30** |

**Scenario 2: Heavy usage (200 tasks/month)**

| Task Type | Count | Agent Used | Cost/Task | Total |
|-----------|-------|------------|-----------|-------|
| Simple | 80 | Direct RAG | $0 | $0 |
| Medium | 80 | Local Mini | $0 | $0 |
| Complex | 40 | Claude CLI | $1.50 | $60 |
| **TOTAL** | **200** | - | - | **$60** |

**With API Caps**: $200/month max (enforced by tracker)

---

## 🔧 Configuration

### Settings File

**Add to** `backend/app/core/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Hybrid Agent Configuration
    AGENT_MODE_ENABLED: bool = True

    # Option 1: Local Models (Ollama)
    OLLAMA_URL: str = "http://ollama:11434"
    LOCAL_CODE_MODEL: str = "qwen2.5-coder:7b"
    LOCAL_VISION_MODEL: str = "llama3.2-vision:11b"

    # Option 2: Claude CLI
    CLAUDE_CLI_ENABLED: bool = True
    CLAUDE_API_KEY: str  # For CLI

    # API Budget Caps
    DAILY_API_BUDGET: float = 10.0   # $10/day
    MONTHLY_API_BUDGET: float = 200.0  # $200/month

    # Routing Preferences
    PREFER_LOCAL_FOR_TASKS: list = ["data_analysis", "code_generation", "vision"]
    PREFER_CLAUDE_FOR_TASKS: list = ["research", "web_automation"]
```

### Environment Variables

```bash
# .env additions
AGENT_MODE_ENABLED=true

# Ollama
OLLAMA_URL=http://ollama:11434

# Claude CLI
CLAUDE_CLI_ENABLED=true
CLAUDE_API_KEY=sk-ant-...

# Budget caps
DAILY_API_BUDGET=10.00
MONTHLY_API_BUDGET=200.00
```

---

## 📊 Success Metrics

### Week 2-3 (Option 1 Complete)
- ✅ Local mini agent handles EDA, code gen, vision
- ✅ 0 API costs for 80% of tasks
- ✅ <5s startup time

### Week 4-5 (Hybrid Complete)
- ✅ Intelligent routing working
- ✅ API budget tracking functional
- ✅ Claude CLI handles complex research
- ✅ <$50/month average cost
- ✅ 95% task success rate

---

## 🚀 Next Steps

1. **Week 1**: Build hybrid router + API tracker
2. **Week 2-3**: Implement Option 1 (local models)
3. **Week 3-4**: Implement Option 2 (Claude CLI)
4. **Week 4-5**: Frontend + testing

Ready to start building? 🎉
