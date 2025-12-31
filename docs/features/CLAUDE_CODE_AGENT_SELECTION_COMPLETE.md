# Claude Code Agent - Manual Selection Implementation

> **Status**: ✅ Complete
> **Date**: 2025-11-30
> **Phase**: Frontend UI + Backend Routing Logic

---

## Summary

Implemented **three-mode agent selection** UI with backend support, giving users full control over agent routing:

1. **🎯 Automatic (Smart Routing)** - Recommended
2. **💻 Local Agent Only** - Free
3. **☁️ Claude CLI Only** - Premium

---

## Frontend Changes

### Component Updated: `AgentModeToggle.tsx`

**New Interface:**
```typescript
export type AgentSelectionMode = 'automatic' | 'local_only' | 'claude_only';

interface AgentModeToggleProps {
  useAgentMode: boolean;
  onToggleAgentMode: (enabled: boolean) => void;
  agentSelection?: AgentSelectionMode;
  onAgentSelectionChange?: (mode: AgentSelectionMode) => void;
}
```

**UI Features:**
- ✅ Three radio button options with descriptions
- ✅ Sage green/teal theme compliance (replaced all `blue-*` → `primary-*`, `gray-*` → `slate-*`)
- ✅ Visual indicators (🎯, 💻, ☁️)
- ✅ Status badges (Recommended, Free, Premium)
- ✅ Cost information ($3-15/MTok for Claude)
- ✅ Model information (Qwen2.5-Coder, Llama-Vision, DeepSeek)
- ✅ Removed old "Force Claude CLI" checkbox (replaced by new UI)

**Radio Button Layout:**
```
Agent Selection:

○ 🎯 Automatic (Smart Routing) [Recommended]
  Intelligently routes between local and cloud agents based on
  task complexity and budget. Best balance of cost and performance.

○ 💻 Local Agent Only [Free]
  Uses only local Ollama models (Qwen2.5-Coder, Llama-Vision, DeepSeek).
  No API costs, runs on your hardware.

○ ☁️ Claude CLI Only [Premium]
  Always uses Anthropic's Claude API. Highest quality for research
  and complex tasks. Costs apply ($3-15/MTok).
```

---

## Backend Changes

### File Updated: `backend/app/agents/hybrid_agent_router.py`

**New Routing Logic:**

```python
# Step 2.5: Check for manual agent selection override
agent_selection = user_preferences.get("agent_selection", "automatic")

if agent_selection == "local_only":
    # Always use local agent (free, no budget check needed)
    return (AgentOption.LOCAL_MINI, {
        "reason": "User manually selected Local Agent Only mode",
        "estimated_cost": 0.0,
        "user_override": True
    })

elif agent_selection == "claude_only":
    # Always use Claude CLI if budget allows
    if daily_budget_remaining >= task_estimated_cost:
        return (AgentOption.CLAUDE_CLI, {
            "reason": "User manually selected Claude CLI Only mode",
            "estimated_cost": task_estimated_cost,
            "user_override": True
        })
    else:
        # Budget insufficient - fallback to local with warning
        return (AgentOption.LOCAL_MINI, {
            "reason": f"Claude CLI requested but budget insufficient. Falling back to Local Agent.",
            "budget_warning": True
        })

# For 'automatic' mode, continue with smart routing logic
```

**Behavior Summary:**

| Selection | Routing Logic | Budget Check | Cost |
|-----------|---------------|--------------|------|
| **Automatic** | Smart routing (complexity + task type + budget) | Yes (for Claude) | Variable |
| **Local Only** | Always LOCAL_MINI | No | $0 |
| **Claude Only** | Always CLAUDE_CLI (or fallback if no budget) | Yes | $$ |

---

## User Experience

### When User Enables Agent Mode:

```
┌─────────────────────────────────────────────────┐
│ ☑ Use Claude Code Agent                        │
│                                                  │
│ Agent Selection:                                 │
│  ● Automatic (Smart Routing) [Recommended]      │
│  ○ Local Agent Only [Free]                      │
│  ○ Claude CLI Only [Premium]                    │
│                                                  │
│ Daily: $2.50 / $10.00           [████░░] 25%    │
└──────────────────────────────────────────────────┘
```

### Routing Examples:

**Scenario 1: User selects "Automatic" + asks "Analyze this CSV"**
→ Routes to LOCAL_MINI (data analysis = local preferred)

**Scenario 2: User selects "Automatic" + asks "Research quantum computing trends"**
→ Routes to CLAUDE_CLI if budget allows (research = Claude preferred)

**Scenario 3: User selects "Local Only" + asks "Research quantum computing trends"**
→ Routes to LOCAL_MINI (user override, ignores preferences)

**Scenario 4: User selects "Claude Only" + asks "What is Python?"**
→ Routes to CLAUDE_CLI if budget allows (user override, even for simple task)

**Scenario 5: User selects "Claude Only" but daily budget $0.10 remaining, task needs $0.65**
→ Routes to LOCAL_MINI with warning message

---

## Integration Guide

### Frontend Integration Example:

```typescript
import { AgentModeToggle, AgentSelectionMode } from '../components/AgentModeToggle';

const [useAgentMode, setUseAgentMode] = useState(false);
const [agentSelection, setAgentSelection] = useState<AgentSelectionMode>('automatic');

<AgentModeToggle
  useAgentMode={useAgentMode}
  onToggleAgentMode={setUseAgentMode}
  agentSelection={agentSelection}
  onAgentSelectionChange={setAgentSelection}
/>
```

### Backend API Call:

```typescript
const userPreferences = {
  ...getRAGSettings(),
  use_agent_mode: useAgentMode,
  agent_selection: agentSelection,  // 'automatic' | 'local_only' | 'claude_only'
  uploaded_files: uploadedFiles
};

await axios.post('/api/v1/query', {
  query: messageText,
  session_id: sessionId,
  user_preferences: userPreferences
});
```

---

## Testing

### Test Cases:

1. ✅ **Automatic Mode** - Verify smart routing based on complexity
2. ✅ **Local Only** - Verify always routes to LOCAL_MINI (no budget checks)
3. ✅ **Claude Only with sufficient budget** - Verify routes to CLAUDE_CLI
4. ✅ **Claude Only with insufficient budget** - Verify fallback to LOCAL_MINI with warning
5. ✅ **Theme compliance** - Verify sage green/teal colors, no blue
6. ✅ **Dark mode** - Verify all three modes work in dark theme

### Example Test Script:

```bash
# Test automatic routing
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze this CSV file",
    "user_preferences": {
      "use_agent_mode": true,
      "agent_selection": "automatic",
      "uploaded_files": [{"filename": "data.csv"}]
    }
  }'

# Test local only override
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Research quantum computing",
    "user_preferences": {
      "use_agent_mode": true,
      "agent_selection": "local_only"
    }
  }'
```

---

## Files Modified

### Frontend:
- `frontend/src/components/AgentModeToggle.tsx` - Added radio buttons, removed old checkbox, theme fixes

### Backend:
- `backend/app/agents/hybrid_agent_router.py` - Added manual selection logic with budget checks

### Documentation:
- `docs/features/CLAUDE_CODE_AGENT_SELECTION_COMPLETE.md` - This file

---

## Next Steps

To complete the full implementation:

1. **Integrate into ChatInterfaceEnhanced.tsx** (add state + pass props)
2. **Create AgentArtifactsViewer.tsx** component
3. **Add backend API endpoints**:
   - `/api/v1/agent/budget-stats` - Get budget info
   - `/api/v1/agent/artifact/{path}` - Download single artifact
   - `/api/v1/agent/artifacts-zip/{task_id}` - Download all artifacts
4. **WebSocket support** for real-time streaming
5. **Sandbox container implementation** (Docker-in-Docker)

---

## Summary of User Options

| Setting | What It Does | When To Use |
|---------|-------------|-------------|
| **Agent Mode OFF** | Standard RAG (no agent) | Simple Q&A, knowledge retrieval |
| **Automatic** | Smart routing based on task | Most use cases (recommended) |
| **Local Only** | Free Ollama models | No API budget, local privacy |
| **Claude Only** | Premium Anthropic API | Maximum quality, complex research |

---

**Status**: Frontend UI complete with theme compliance ✅
**Next**: Continue with sandbox container implementation as per user request "continue 1 and 2"
