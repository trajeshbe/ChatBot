# Claude Code Frontend UI Implementation Guide

> **Status**: Components Created ✅
> **Theme**: Sage Green/Teal (matches existing app)
> **Next**: Backend API endpoint + Integration

---

## 🎨 Theme Compliance

All components use the app's existing sage green/teal theme:

**Color Classes** (Already in Tailwind config):
- **Primary** (Sage Green): `text-primary-500`, `bg-primary-500`, `border-primary-500`
- **Secondary** (Teal): `text-secondary-500`, `bg-secondary-500`
- **Slate** (Backgrounds): `bg-slate-50` (light), `bg-slate-900` (dark)
- **Success**: `text-green-500`, `bg-green-500`
- **Warning**: `text-amber-500`, `bg-amber-500`
- **Error**: `text-red-500`, `bg-red-500`

**Components Should Use**:
- Replace `blue-*` → `primary-*`
- Replace `gray-*` → `slate-*` (for backgrounds/borders)
- Keep semantic colors (green, red, amber, purple) for indicators

---

## 📦 Components Created

### 1. AgentModeToggle.tsx ✅

**Location**: `frontend/src/components/AgentModeToggle.tsx`

**Purpose**: Main control for enabling agent mode with budget display

**Features**:
- ☑️ "Use Claude Code Agent" checkbox
- 📊 Budget display (daily & monthly)
- 📈 Progress bars with color coding
- ⚠️ Budget warnings
- 🔧 Advanced options (Force Claude CLI)

**Props**:
```typescript
interface AgentModeToggleProps {
  useAgentMode: boolean;
  onToggleAgentMode: (enabled: boolean) => void;
  forceClaudeCli?: boolean;
  onToggleForceClaudeCli?: (enabled: boolean) => void;
}
```

**Theme Updates Needed**:
Replace these in the file:
- `text-blue-600` → `text-primary-600`
- `focus:ring-blue-500` → `focus:ring-primary-500`
- All `gray-*` → `slate-*`

---

### 2. AgentStreamingTerminal.tsx ✅

**Location**: `frontend/src/components/AgentStreamingTerminal.tsx`

**Purpose**: Real-time display of agent execution

**Features**:
- 📟 Terminal-style output
- 🔄 Iteration progress bar
- 🔧 Tool execution display
- ✅ Status indicators
- 💰 Cost tracking

**Props**:
```typescript
interface AgentStreamingTerminalProps {
  taskId: string;
  sessionId: string;
  onComplete?: (result: any) => void;
  onError?: (error: string) => void;
}
```

**Event Types Handled**:
- `agent_started`
- `iteration_started`
- `tool_execution`
- `tool_result`
- `agent_completed`
- `agent_failed`
- `budget_limit_reached`

**Theme Updates Needed**:
- `text-blue-500` → `text-primary-500`
- `bg-blue-500` → `bg-primary-500`
- All `gray-*` → `slate-*`

---

### 3. AgentArtifactsViewer.tsx (TO CREATE)

**Location**: `frontend/src/components/AgentArtifactsViewer.tsx`

**Purpose**: View and download generated files

**Features Needed**:
- 📁 List of generated files
- 👁️ Preview (images, code, markdown)
- ⬇️ Download buttons
- 📦 "Download All" option
- 🔍 Syntax highlighting for code

**Example Code**:
```typescript
import React from 'react';

interface Artifact {
  name: string;
  type: 'image' | 'code' | 'markdown' | 'data' | 'other';
  path: string;
  size: number;
  preview?: string;
}

interface AgentArtifactsViewerProps {
  artifacts: Artifact[];
  onDownload: (artifact: Artifact) => void;
  onDownloadAll: () => void;
}

export const AgentArtifactsViewer: React.FC<AgentArtifactsViewerProps> = ({
  artifacts,
  onDownload,
  onDownloadAll
}) => {
  const getFileIcon = (type: string): string => {
    switch (type) {
      case 'image': return '🖼️';
      case 'code': return '📝';
      case 'markdown': return '📄';
      case 'data': return '📊';
      default: return '📁';
    }
  };

  return (
    <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 bg-white dark:bg-slate-800">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
          📁 Generated Artifacts
        </h3>
        {artifacts.length > 0 && (
          <button
            onClick={onDownloadAll}
            className="px-3 py-1 text-sm bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors"
          >
            ⬇️ Download All
          </button>
        )}
      </div>

      {/* Artifacts List */}
      {artifacts.length === 0 ? (
        <div className="text-center py-8 text-slate-500 dark:text-slate-400">
          No artifacts generated yet
        </div>
      ) : (
        <div className="space-y-2">
          {artifacts.map((artifact, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
            >
              <div className="flex items-center space-x-3 flex-1 min-w-0">
                <span className="text-2xl">{getFileIcon(artifact.type)}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-slate-900 dark:text-white truncate">
                    {artifact.name}
                  </div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">
                    {(artifact.size / 1024).toFixed(1)} KB
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                {artifact.preview && (
                  <button
                    className="px-2 py-1 text-xs text-primary-600 dark:text-primary-400 hover:underline"
                  >
                    👁️ Preview
                  </button>
                )}
                <button
                  onClick={() => onDownload(artifact)}
                  className="px-3 py-1 text-xs bg-primary-500 hover:bg-primary-600 text-white rounded transition-colors"
                >
                  ⬇️ Download
                  </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
```

---

## 🔌 Backend API Endpoint Needed

### GET /api/v1/agent/budget-stats

**Purpose**: Fetch current budget usage

**Response**:
```json
{
  "daily": {
    "limit": 10.0,
    "spent": 2.50,
    "remaining": 7.50,
    "percentage_used": 25.0,
    "tasks": 5,
    "date": "2025-11-30"
  },
  "monthly": {
    "limit": 200.0,
    "spent": 45.30,
    "remaining": 154.70,
    "percentage_used": 22.7,
    "tasks": 67,
    "month": "2025-11"
  },
  "warnings": [
    {
      "level": "warning",
      "message": "Daily budget 80% consumed"
    }
  ]
}
```

**Implementation**:
```python
# backend/app/api/routes/agent_routes.py

from fastapi import APIRouter, Depends
from app.services.api_usage_tracker import api_usage_tracker

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])

@router.get("/budget-stats")
async def get_budget_stats():
    """Get current API budget usage statistics"""
    stats = await api_usage_tracker.get_usage_stats()
    return stats
```

**Register Route**:
```python
# backend/app/main.py

from app.api.routes import agent_routes

app.include_router(agent_routes.router)
```

---

## 🔗 Integration with ChatInterface

### Update ChatInterfaceEnhanced.tsx

**Add State**:
```typescript
const [useAgentMode, setUseAgentMode] = useState(false);
const [forceClaudeCli, setForceClaudeCli] = useState(false);
const [agentTaskId, setAgentTaskId] = useState<string | null>(null);
const [agentArtifacts, setAgentArtifacts] = useState<any[]>([]);
```

**Add Components Before Chat Input**:
```typescript
{/* Agent Mode Toggle */}
<AgentModeToggle
  useAgentMode={useAgentMode}
  onToggleAgentMode={setUseAgentMode}
  forceClaudeCli={forceClaudeCli}
  onToggleForceClaudeCli={setForceClaudeCli}
/>

{/* Streaming Terminal (only show when agent is running) */}
{agentTaskId && (
  <AgentStreamingTerminal
    taskId={agentTaskId}
    sessionId={sessionId}
    onComplete={(result) => {
      setAgentTaskId(null);
      setAgentArtifacts(result.artifacts || []);
    }}
    onError={(error) => {
      setAgentTaskId(null);
      // Show error message
    }}
  />
)}

{/* Artifacts Viewer (show after completion) */}
{agentArtifacts.length > 0 && (
  <AgentArtifactsViewer
    artifacts={agentArtifacts}
    onDownload={(artifact) => {
      // Download single artifact
      window.open(`/api/v1/agent/artifact/${artifact.path}`, '_blank');
    }}
    onDownloadAll={() => {
      // Download all as zip
      window.open(`/api/v1/agent/artifacts-zip/${agentTaskId}`, '_blank');
    }}
  />
)}
```

**Update Send Message**:
```typescript
const handleSendMessage = async () => {
  const messageText = message.trim();
  if (!messageText) return;

  // Add user preferences with agent mode
  const userPreferences = {
    ...getRAGSettings(), // Existing settings
    use_agent_mode: useAgentMode,
    force_claude_cli: forceClaudeCli,
    uploaded_files: uploadedFiles.map(f => ({ filename: f.filename }))
  };

  // Send to backend
  const response = await axios.post('/api/v1/query', {
    query: messageText,
    session_id: sessionId,
    user_preferences: userPreferences
  });

  // If agent mode was used, set task ID for streaming
  if (response.data.metadata?.agent_routing) {
    setAgentTaskId(response.data.metadata.task_id);
  }
};
```

---

## 📝 Implementation Checklist

### Frontend (4-6 hours)
- [x] Create AgentModeToggle component
- [x] Create AgentStreamingTerminal component
- [ ] Update components to use `primary-*` theme classes (10 min)
- [ ] Create AgentArtifactsViewer component (30 min)
- [ ] Integrate into ChatInterfaceEnhanced (1 hour)
- [ ] Add WebSocket connection for streaming (2 hours)
- [ ] Test UI components (30 min)

### Backend (1-2 hours)
- [ ] Create `/api/v1/agent/budget-stats` endpoint (15 min)
- [ ] Create `/api/v1/agent/artifact/{path}` endpoint (15 min)
- [ ] Create `/api/v1/agent/artifacts-zip/{task_id}` endpoint (30 min)
- [ ] Add WebSocket support for agent events (1 hour)
- [ ] Test API endpoints (30 min)

### Testing (1 hour)
- [ ] Test agent mode toggle
- [ ] Test budget display
- [ ] Test streaming terminal
- [ ] Test artifacts download
- [ ] Test theme consistency
- [ ] Test dark mode

---

## 🚀 Quick Theme Fix

To quickly fix the theme in existing components, run:

```bash
cd frontend/src/components

# Replace blue with primary
sed -i 's/text-blue-/text-primary-/g' AgentModeToggle.tsx
sed -i 's/bg-blue-/bg-primary-/g' AgentModeToggle.tsx
sed -i 's/border-blue-/border-primary-/g' AgentModeToggle.tsx
sed -i 's/ring-blue-/ring-primary-/g' AgentModeToggle.tsx

sed -i 's/text-blue-/text-primary-/g' AgentStreamingTerminal.tsx
sed -i 's/bg-blue-/bg-primary-/g' AgentStreamingTerminal.tsx

# Replace gray with slate
sed -i 's/text-gray-/text-slate-/g' AgentModeToggle.tsx
sed -i 's/bg-gray-/bg-slate-/g' AgentModeToggle.tsx
sed -i 's/border-gray-/border-slate-/g' AgentModeToggle.tsx

sed -i 's/text-gray-/text-slate-/g' AgentStreamingTerminal.tsx
sed -i 's/bg-gray-/bg-slate-/g' AgentStreamingTerminal.tsx
sed -i 's/border-gray-/border-slate-/g' AgentStreamingTerminal.tsx
```

---

## 📊 Final UI Result

**Agent Mode Off** (Default):
```
┌─────────────────────────────────────┐
│ Regular chat interface              │
│ (no agent components visible)       │
└─────────────────────────────────────┘
```

**Agent Mode On** (With Budget Display):
```
┌───────────────────────────────────────────────┐
│ ☑️ Use Claude Code Agent                      │
│ Autonomous coding agent will handle...        │
│                                                │
│ Daily: $2.50 / $10.00           [████░░] 25%  │
└───────────────────────────────────────────────┘
│                                                │
│ [Chat messages...]                             │
│                                                │
│ ┌─────────────────────────────────────────┐  │
│ │ ⏳ Agent Execution  Iter 3/20  $0.45    │  │
│ │ ════════════════════════════════════    │  │
│ │ [12:34:56] 🚀 Agent started             │  │
│ │ [12:35:01] 🔧 Tool: execute_python      │  │
│ │ [12:35:03] 📤 Result: Success           │  │
│ │ [12:35:05] ▊                            │  │
│ └─────────────────────────────────────────┘  │
│                                                │
│ ┌─────────────────────────────────────────┐  │
│ │ 📁 Generated Artifacts  [Download All]  │  │
│ │ 🖼️ chart.png         2.3 KB [Download]  │  │
│ │ 📝 analysis.py       5.1 KB [Download]  │  │
│ │ 📄 report.md        12.8 KB [Download]  │  │
│ └─────────────────────────────────────────┘  │
└───────────────────────────────────────────────┘
```

---

**Status**: Frontend components created, theme compliance documented, backend API spec ready. Next: Sandbox container implementation.
