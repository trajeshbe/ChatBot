# Project Estimator: Workflow Visualization Guide

**Feature**: LangGraph Workflow Visualization  
**Endpoint**: `GET /api/v1/project-estimator/workflow/visualization`

---

## 🎨 Quick Access

```bash
# Get visualization
curl http://localhost:8000/api/v1/project-estimator/workflow/visualization | jq
```

## 📊 View Workflow Diagram

### Method 1: Mermaid Live Editor (Recommended)

```bash
# 1. Get the Mermaid diagram
curl -s http://localhost:8000/api/v1/project-estimator/workflow/visualization \
  | jq -r '.visualization.mermaid_diagram'

# 2. Copy output and paste at https://mermaid.live/
```

### Method 2: Save as File

```bash
# Save Mermaid diagram
curl -s http://localhost:8000/api/v1/project-estimator/workflow/visualization \
  | jq -r '.visualization.mermaid_diagram' > workflow.mmd

# View in VS Code with Mermaid Preview extension
```

---

## 🔍 Workflow Overview

**6 Agents in Sequential Flow**:

```
User Input → Analyst → Team Planner → Task Generator 
          → Workflow Agent → Rate Assignment → Document Generator → Output
```

**Each agent**:
- Takes output from previous agent
- Makes LLM-powered decisions
- Passes enriched state to next agent

---

## ✨ Key Features Visualized

1. **LLM-First**: Every agent uses LLM (no hardcoded logic)
2. **Example-Guided**: Agents learn from uploaded references
3. **Sequential**: Clear data flow dependencies
4. **State Passing**: Purple boxes show intermediate state
5. **New Workflow Agent**: Yellow box highlights phase-4 agent

---

## 🚀 API Response Structure

```json
{
  "success": true,
  "visualization": {
    "mermaid_diagram": "graph TD\n    Start([User Input]) --> ...",
    "metadata": {
      "total_agents": 6,
      "agents": [
        {
          "name": "Analyst",
          "purpose": "Analyze examples and extract requirements"
        }
      ],
      "execution_flow": "Sequential: Analyst → ...",
      "key_features": ["LLM-First", "Example-Guided", ...]
    }
  },
  "usage": {
    "mermaid_live_editor": "https://mermaid.live/"
  }
}
```

---

**Status**: ✅ Visualization available at `/api/v1/project-estimator/workflow/visualization`
