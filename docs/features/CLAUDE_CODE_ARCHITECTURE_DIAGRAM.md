# Claude Code Integration - Architecture Diagrams

## 🎨 Visual Architecture Guide

---

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE (Frontend)                           │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │                         Chat Interface                                  │    │
│  │                                                                          │    │
│  │  User Input: "Perform EDA on sales_data.csv"                           │    │
│  │                                                                          │    │
│  │  ☑ Use Claude Code (for complex tasks)  ← NEW CHECKBOX                │    │
│  │                                                                          │    │
│  │  [Send Query]                                                           │    │
│  └────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │                    Agent Execution View (NEW)                           │    │
│  │                                                                          │    │
│  │  📊 Task Complexity: COMPLEX                                            │    │
│  │  🎯 Task Type: Data Analysis                                            │    │
│  │  ⏱️  Estimated Steps: 10                                                 │    │
│  │                                                                          │    │
│  │  🔄 Streaming Terminal:                                                 │    │
│  │  ┌──────────────────────────────────────────────────────────────┐      │    │
│  │  │ 🤔 Thinking: I'll analyze this CSV step by step...          │      │    │
│  │  │                                                              │      │    │
│  │  │ 🔧 Tool: execute_python                                      │      │    │
│  │  │ Code: import pandas as pd                                   │      │    │
│  │  │       df = pd.read_csv('/workspace/sales_data.csv')        │      │    │
│  │  │       print(df.head())                                      │      │    │
│  │  │                                                              │      │    │
│  │  │ ✅ Output: (5 rows displayed)                                │      │    │
│  │  │                                                              │      │    │
│  │  │ 🔧 Tool: execute_python                                      │      │    │
│  │  │ Code: df.describe()                                         │      │    │
│  │  │ ...                                                          │      │    │
│  │  └──────────────────────────────────────────────────────────────┘      │    │
│  │                                                                          │    │
│  │  📁 Generated Artifacts:                                                │    │
│  │  ┌──────────────────────────────────────────────────────────────┐      │    │
│  │  │ 📄 eda_report.md          [Preview] [Download]              │      │    │
│  │  │ 📊 distribution.png       [Preview] [Download]              │      │    │
│  │  │ 📈 correlation_matrix.png [Preview] [Download]              │      │    │
│  │  │ 🐍 analysis_script.py     [Preview] [Download]              │      │    │
│  │  │                                                              │      │    │
│  │  │ [Download All as ZIP]                                       │      │    │
│  │  └──────────────────────────────────────────────────────────────┘      │    │
│  └────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ HTTP/WebSocket
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND (FastAPI)                                      │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │                      Enhanced RAG Agent                                 │    │
│  │                                                                          │    │
│  │  async def run(query, user_preferences):                               │    │
│  │      use_agent = user_preferences.get('use_agent_mode')  ← NEW        │    │
│  │                                                                          │    │
│  │      if use_agent:                                                     │    │
│  │          # Analyze complexity                                           │    │
│  │          complexity, task_type, metadata =                             │    │
│  │              task_complexity_analyzer.analyze(query)                   │    │
│  │                                                                          │    │
│  │          if complexity in [MEDIUM, COMPLEX]:                           │    │
│  │              # Route to coding agent                                    │    │
│  │              return await mini_coding_agent.run(...)                   │    │
│  │                                                                          │    │
│  │      # Existing RAG flow                                               │    │
│  │      return await rag_service.query(...)                               │    │
│  └────────────────────────────────────────────────────────────────────────┘    │
│                                       │                                          │
│                    ┌──────────────────┼──────────────────┐                      │
│                    ▼                  ▼                  ▼                      │
│           ┌────────────────┐ ┌────────────────┐ ┌────────────────┐            │
│           │  Complexity    │ │  Mini Coding   │ │  Sandbox       │            │
│           │  Analyzer      │ │  Agent         │ │  Manager       │            │
│           │                │ │                │ │                │            │
│           │  - Keyword     │ │  - Agentic     │ │  - Docker API  │            │
│           │    matching    │ │    loop        │ │  - Container   │            │
│           │  - File type   │ │  - Tool calls  │ │    lifecycle   │            │
│           │    detection   │ │  - Streaming   │ │  - Security    │            │
│           └────────────────┘ └────────────────┘ └────────────────┘            │
│                                       │                  │                      │
└───────────────────────────────────────┼──────────────────┼──────────────────────┘
                                        │                  │
                                        ▼                  ▼
                            ┌──────────────────────────────────────┐
                            │       Redis Pub/Sub                   │
                            │       (Event Streaming)               │
                            │                                       │
                            │  Channels:                            │
                            │  - task:{task_id}                     │
                            │  - agent:events                       │
                            └──────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     SANDBOX ENVIRONMENT (Docker-in-Docker)                       │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │                    Isolated Container (Per Session)                     │    │
│  │                                                                          │    │
│  │  Image: chatbot-sandbox-base:latest                                    │    │
│  │  User: sandbox (non-root)                                              │    │
│  │  Network: isolated (no internet) OR bridge (limited)                   │    │
│  │  Resources: 2GB RAM, 0.5 CPU cores, 10-minute timeout                  │    │
│  │                                                                          │    │
│  │  /workspace/                                                            │    │
│  │  ├── sales_data.csv           ← Uploaded file                          │    │
│  │  ├── temp_script.py            ← Generated code                        │    │
│  │  ├── eda_report.md             ← Output artifact                       │    │
│  │  ├── distribution.png          ← Generated chart                       │    │
│  │  └── analysis_script.py        ← Final reproducible script            │    │
│  │                                                                          │    │
│  │  Installed Packages:                                                    │    │
│  │  - pandas, numpy, matplotlib, seaborn                                  │    │
│  │  - scikit-learn, plotly                                                │    │
│  │  - pillow, opencv-python (for vision tasks)                            │    │
│  └────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ Upload artifacts
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          MinIO Object Storage                                    │
│                                                                                  │
│  Bucket: task-outputs/                                                          │
│  ├── {session_id}/                                                              │
│  │   ├── {task_id}/                                                             │
│  │   │   ├── eda_report.md                                                      │
│  │   │   ├── distribution.png                                                   │
│  │   │   ├── correlation_matrix.png                                             │
│  │   │   └── analysis_script.py                                                 │
│  │   │                                                                           │
│  │   └── Public URLs: http://minio:9000/task-outputs/{session_id}/{task_id}/... │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Agent Execution Flow (Detailed)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         MINI CODING AGENT LOOP                                │
└──────────────────────────────────────────────────────────────────────────────┘

User Query: "Perform EDA on sales_data.csv"
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Initialize Sandbox                                      │
│                                                                  │
│  sandbox = await sandbox_manager.create_sandbox(session_id)    │
│                                                                  │
│  ✅ Container started: chatbot-sandbox-abc123                   │
│  ✅ Workspace: /tmp/agent_workspaces/session-xyz/              │
│  ✅ Files copied: sales_data.csv → /workspace/                 │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Agentic Loop (Iteration 1)                             │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ Claude API Call                                      │      │
│  │                                                       │      │
│  │ System Prompt:                                       │      │
│  │ "You are an autonomous coding agent. You have access│      │
│  │  to a Python sandbox with pandas, matplotlib, etc.  │      │
│  │  The user uploaded sales_data.csv and wants EDA."   │      │
│  │                                                       │      │
│  │ Tools Available:                                     │      │
│  │ - execute_python(code: str)                          │      │
│  │ - read_file(path: str)                               │      │
│  │ - write_file(path: str, content: str)                │      │
│  │ - install_package(package: str)                      │      │
│  │ - run_bash(command: str)                             │      │
│  └──────────────────────────────────────────────────────┘      │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ Claude Response (Iteration 1)                        │      │
│  │                                                       │      │
│  │ Text: "Let me start by loading the CSV and          │      │
│  │        examining its structure."                     │      │
│  │                                                       │      │
│  │ Tool Call:                                           │      │
│  │   name: "execute_python"                             │      │
│  │   arguments:                                         │      │
│  │     code: |                                          │      │
│  │       import pandas as pd                            │      │
│  │       df = pd.read_csv('/workspace/sales_data.csv')│      │
│  │       print(f"Shape: {df.shape}")                   │      │
│  │       print(df.head())                               │      │
│  │       print(df.info())                               │      │
│  └──────────────────────────────────────────────────────┘      │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ Tool Execution (In Sandbox)                          │      │
│  │                                                       │      │
│  │ $ docker exec chatbot-sandbox-abc123 \              │      │
│  │     python /workspace/temp_script.py                 │      │
│  │                                                       │      │
│  │ Output:                                              │      │
│  │   Shape: (1000, 8)                                   │      │
│  │   (5 rows of data)                                   │      │
│  │   (column info)                                      │      │
│  │                                                       │      │
│  │ ✅ Success: exit_code=0                              │      │
│  └──────────────────────────────────────────────────────┘      │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ Stream Event to Frontend (via Redis)                │      │
│  │                                                       │      │
│  │ {                                                    │      │
│  │   "type": "tool_call",                              │      │
│  │   "tool": "execute_python",                         │      │
│  │   "code": "...",                                    │      │
│  │   "output": "Shape: (1000, 8)..."                  │      │
│  │ }                                                    │      │
│  └──────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Agentic Loop (Iteration 2)                             │
│                                                                  │
│  Conversation History:                                          │
│  - User: "Perform EDA..."                                       │
│  - Assistant: Tool call (execute_python)                        │
│  - User: Tool result (Shape: 1000x8...)                         │
│                                                                  │
│  Claude Response (Iteration 2):                                 │
│    Text: "Now let me create visualizations..."                 │
│                                                                  │
│    Tool Call: execute_python                                    │
│      code: |                                                    │
│        import matplotlib.pyplot as plt                          │
│        df['sales'].hist(bins=30)                               │
│        plt.savefig('/workspace/distribution.png')              │
│        print('Saved: distribution.png')                        │
│                                                                  │
│  ✅ Execution succeeds → Stream to frontend                     │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
    ... (Iterations 3-10: More analysis, charts, summary)
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Final Response (Iteration 11)                          │
│                                                                  │
│  Claude Response:                                               │
│    stop_reason: "end_turn"                                      │
│                                                                  │
│    Text:                                                        │
│    "I've completed the exploratory data analysis:              │
│                                                                  │
│     Key Findings:                                               │
│     - Dataset has 1000 rows and 8 columns                      │
│     - Sales range from $100 to $5000                           │
│     - Strong correlation between price and sales               │
│                                                                  │
│     Generated Files:                                            │
│     - eda_report.md: Full analysis report                      │
│     - distribution.png: Sales distribution chart               │
│     - correlation_matrix.png: Feature correlations             │
│     - analysis_script.py: Reproducible Python script"          │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: Collect & Upload Artifacts                             │
│                                                                  │
│  artifacts = list_files('/tmp/agent_workspaces/session-xyz/')  │
│                                                                  │
│  For each file:                                                 │
│    ✅ eda_report.md → MinIO: task-outputs/session-xyz/task-1/  │
│    ✅ distribution.png → MinIO: ...                            │
│    ✅ correlation_matrix.png → MinIO: ...                      │
│    ✅ analysis_script.py → MinIO: ...                          │
│                                                                  │
│  artifact_urls = [                                              │
│    "http://minio:9000/.../eda_report.md",                     │
│    "http://minio:9000/.../distribution.png",                  │
│    ...                                                          │
│  ]                                                              │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 6: Cleanup Sandbox                                        │
│                                                                  │
│  await sandbox.cleanup()                                        │
│                                                                  │
│  ✅ Container stopped                                           │
│  ✅ Container removed                                           │
│  ✅ Workspace preserved (for debugging)                         │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 7: Return Results to User                                 │
│                                                                  │
│  return {                                                       │
│    "answer": "I've completed the EDA...",                      │
│    "artifacts": [                                               │
│      {                                                          │
│        "filename": "eda_report.md",                            │
│        "url": "http://minio:9000/...",                         │
│        "preview_available": true                               │
│      },                                                         │
│      ...                                                        │
│    ],                                                           │
│    "execution_log": [...],                                     │
│    "metadata": {                                                │
│      "tool_calls": 11,                                         │
│      "iterations": 11,                                         │
│      "execution_time_ms": 45000                                │
│    }                                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
[Frontend displays results with download links]
```

---

## 3. Data Flow Diagram

```
┌─────────────┐
│    User     │
│  (Frontend) │
└──────┬──────┘
       │ 1. POST /api/v1/query
       │    {
       │      "query": "Perform EDA on sales_data.csv",
       │      "session_id": "session-xyz",
       │      "use_agent_mode": true
       │    }
       ▼
┌──────────────────────┐
│  Enhanced RAG Agent  │
│                      │
│  Complexity Analysis │ → COMPLEX + DATA_ANALYSIS
└──────┬───────────────┘
       │ 2. Route to agent
       ▼
┌──────────────────────┐
│ Mini Coding Agent    │
│                      │
│ Start agentic loop   │
└──────┬───────────────┘
       │ 3. Initialize sandbox
       ▼
┌──────────────────────┐         ┌─────────────────┐
│  Sandbox Manager     │────────▶│ Docker Engine   │
│                      │         │                 │
│  Create container    │         │ Pull/Start      │
│  Mount workspace     │         │ Container       │
└──────┬───────────────┘         └─────────────────┘
       │ 4. Container ready
       ▼
┌──────────────────────┐         ┌─────────────────┐
│ Agentic Loop         │────────▶│ Claude API      │
│                      │         │                 │
│ Call with tools      │◀────────│ Returns tool    │
│                      │         │ calls           │
└──────┬───────────────┘         └─────────────────┘
       │ 5. Execute tool
       ▼
┌──────────────────────┐         ┌─────────────────┐
│ Tool Executor        │────────▶│ Sandbox         │
│                      │         │ (Docker exec)   │
│ execute_python()     │         │                 │
└──────┬───────────────┘         └─────────────────┘
       │ 6. Stream event
       ▼
┌──────────────────────┐         ┌─────────────────┐
│ Redis Pub/Sub        │────────▶│ WebSocket       │
│                      │         │ (Frontend)      │
│ Publish event        │         │                 │
└──────┬───────────────┘         └─────────────────┘
       │ 7. Loop continues (iterations 1-10)
       │
       │ 8. Final response
       ▼
┌──────────────────────┐
│ Collect Artifacts    │
│                      │
│ List workspace files │
└──────┬───────────────┘
       │ 9. Upload
       ▼
┌──────────────────────┐         ┌─────────────────┐
│ MinIO Uploader       │────────▶│ MinIO Storage   │
│                      │         │                 │
│ Upload each file     │         │ Public URLs     │
└──────┬───────────────┘         └─────────────────┘
       │ 10. Return results
       ▼
┌──────────────────────┐
│   User (Frontend)    │
│                      │
│   Display:           │
│   - Answer           │
│   - Artifacts        │
│   - Download links   │
└──────────────────────┘
```

---

## 4. Complexity Routing Decision Tree

```
User Query
    │
    ▼
┌─────────────────────────┐
│ use_agent_mode enabled? │
└─────────┬───────────────┘
          │
    ┌─────┴─────┐
    │           │
   NO          YES
    │           │
    │           ▼
    │   ┌──────────────────────┐
    │   │ Complexity Analyzer  │
    │   └──────┬───────────────┘
    │          │
    │   ┌──────┴───────┬──────────┬──────────┐
    │   │              │          │          │
    │  SIMPLE        MEDIUM     COMPLEX    COMPLEX
    │   │              │          │          │
    │   │         EDA/Code   Vision/ML   Research
    │   │         Gen Task   Task        /Multi-repo
    │   │              │          │          │
    ▼   ▼              ▼          ▼          ▼
┌────────┐    ┌─────────────┐ ┌─────────────┐ ┌──────────────┐
│ Direct │    │ Mini Coding │ │ Mini Coding │ │ Claude Code  │
│ RAG    │    │ Agent       │ │ Agent       │ │ CLI (Option2)│
│ /LLM   │    │ (Option 1)  │ │ (Option 1)  │ │              │
└────────┘    └─────────────┘ └─────────────┘ └──────────────┘
    │                │              │                │
    │                │              │                │
    └────────────────┴──────────────┴────────────────┘
                            │
                            ▼
                    [Return to User]
```

---

## 5. Security Layers

```
┌───────────────────────────────────────────────────────────────┐
│                    SECURITY ONION MODEL                        │
└───────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Request Validation                                 │
│                                                              │
│ ✅ Auth token validation                                    │
│ ✅ Rate limiting (10 tasks/hour per user)                   │
│ ✅ Input sanitization (XSS, injection)                      │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Complexity Analysis                                │
│                                                              │
│ ✅ Token budget check (max 100K tokens/task)                │
│ ✅ Cost estimation                                          │
│ ✅ Task timeout limits                                      │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Sandbox Isolation                                  │
│                                                              │
│ ✅ Docker container (isolated filesystem)                   │
│ ✅ Non-root user (uid=1000)                                 │
│ ✅ Network: none (or restricted bridge)                     │
│ ✅ Resource limits: 2GB RAM, 0.5 CPU                        │
│ ✅ Timeout: 10 minutes max                                  │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Command Filtering                                  │
│                                                              │
│ 🚫 BLOCKED: rm -rf /, mkfs, dd, fork bombs                  │
│ 🚫 BLOCKED: curl | sh, wget | bash                          │
│ 🚫 BLOCKED: /etc/ writes, /sys/ access                      │
│ ✅ ALLOWED: Python, pip install, file ops in /workspace     │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 5: Path Validation                                    │
│                                                              │
│ ✅ All file ops restricted to /workspace/                   │
│ ✅ Resolve symlinks, check path traversal                   │
│ ✅ Block access to /, /var/, /usr/, etc.                    │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 6: Audit Logging                                      │
│                                                              │
│ 📝 Log every tool call                                      │
│ 📝 Log command + args + result                              │
│ 📝 Log resource usage                                       │
│ 📝 Alert on suspicious patterns                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Cost Breakdown

```
┌──────────────────────────────────────────────────────────────┐
│           COST ANALYSIS (Per Complex Task)                   │
└──────────────────────────────────────────────────────────────┘

Option 1: Mini Agent
════════════════════

┌─────────────────────┬──────────┬─────────┬──────────┐
│ Component           │ Tokens   │ Cost    │ % Total  │
├─────────────────────┼──────────┼─────────┼──────────┤
│ Tool Selection      │ 1K       │ $0.00   │ 0%       │
│ (Ollama local)      │          │ (free)  │          │
├─────────────────────┼──────────┼─────────┼──────────┤
│ Code Generation     │ 20K      │ $0.60   │ 100%     │
│ (Claude Sonnet)     │ (avg)    │         │          │
├─────────────────────┼──────────┼─────────┼──────────┤
│ Infrastructure      │ -        │ $0.00   │ 0%       │
│ (Docker, Redis)     │          │ (local) │          │
├─────────────────────┼──────────┼─────────┼──────────┤
│ TOTAL               │ ~21K     │ $0.60   │ 100%     │
└─────────────────────┴──────────┴─────────┴──────────┘


Option 2: Claude Code CLI
═══════════════════════════

┌─────────────────────┬──────────┬─────────┬──────────┐
│ Component           │ Tokens   │ Cost    │ % Total  │
├─────────────────────┼──────────┼─────────┼──────────┤
│ CLI Overhead        │ 10K      │ $0.30   │ 20%      │
│ (system prompts)    │          │         │          │
├─────────────────────┼──────────┼─────────┼──────────┤
│ Task Execution      │ 40K      │ $1.20   │ 80%      │
│ (Claude Sonnet)     │ (avg)    │         │          │
├─────────────────────┼──────────┼─────────┼──────────┤
│ Infrastructure      │ -        │ $0.00   │ 0%       │
│ (Docker, Redis)     │          │ (local) │          │
├─────────────────────┼──────────┼─────────┼──────────┤
│ TOTAL               │ ~50K     │ $1.50   │ 100%     │
└─────────────────────┴──────────┴─────────┴──────────┘

Savings: 2.5x cheaper with Option 1
```

---

## 7. User Journey Map

```
┌────────────────────────────────────────────────────────────────────┐
│                        USER JOURNEY                                 │
└────────────────────────────────────────────────────────────────────┘

Step 1: Upload File
═══════════════════
User: Uploads sales_data.csv (100 KB)
UI:   ✅ File uploaded successfully

Step 2: Ask Complex Question
═════════════════════════════
User: Types: "Perform comprehensive EDA on this data"
UI:   🤖 Checkbox: "Use Claude Code" (checked)
      [Send Query]

Step 3: Complexity Detection
═════════════════════════════
Backend: Analyzing query...
         ✅ Complexity: COMPLEX
         ✅ Task Type: Data Analysis
         ✅ Estimated Steps: 10

UI: Shows:
    ┌──────────────────────────────────────────┐
    │ 📊 Task Complexity: COMPLEX               │
    │ 🎯 Task Type: Data Analysis               │
    │ ⏱️  Estimated Time: 2-3 minutes            │
    │ 💰 Estimated Cost: $0.60                  │
    │                                           │
    │ 🤖 Starting autonomous agent...           │
    └──────────────────────────────────────────┘

Step 4: Live Execution (Streaming)
═══════════════════════════════════
UI: Streaming Terminal appears:

    ┌──────────────────────────────────────────┐
    │ 🤔 Thinking: I'll analyze this CSV...    │
    │                                           │
    │ 🔧 Tool: execute_python                   │
    │ Code: import pandas as pd                │
    │       df = pd.read_csv(...)              │
    │       print(df.head())                   │
    │                                           │
    │ ✅ Output:                                │
    │    Shape: (1000, 8)                      │
    │    (5 rows displayed)                    │
    │ ─────────────────────────────────────────│
    │ 🔧 Tool: execute_python                   │
    │ Code: df.describe()                      │
    │                                           │
    │ ✅ Output: (statistics)                   │
    │ ─────────────────────────────────────────│
    │ 🔧 Tool: execute_python                   │
    │ Code: plt.savefig('distribution.png')    │
    │                                           │
    │ ✅ Created: distribution.png              │
    │ ─────────────────────────────────────────│
    │ ... (8 more iterations)                  │
    │ ─────────────────────────────────────────│
    │ ✅ Analysis complete!                     │
    └──────────────────────────────────────────┘

Step 5: View Results
════════════════════
UI: Results Panel appears:

    ┌──────────────────────────────────────────┐
    │ 📁 Generated Artifacts (4 files)          │
    │                                           │
    │ 📄 eda_report.md                          │
    │    Size: 15 KB                            │
    │    [👁️ Preview] [⬇️ Download]              │
    │                                           │
    │ 📊 distribution.png                       │
    │    Size: 45 KB                            │
    │    [👁️ Preview] [⬇️ Download]              │
    │    ┌─────────────────────────┐           │
    │    │ [Inline chart preview]  │           │
    │    └─────────────────────────┘           │
    │                                           │
    │ 📈 correlation_matrix.png                 │
    │    Size: 38 KB                            │
    │    [👁️ Preview] [⬇️ Download]              │
    │                                           │
    │ 🐍 analysis_script.py                     │
    │    Size: 2 KB                             │
    │    [👁️ Preview] [⬇️ Download]              │
    │                                           │
    │ [📦 Download All as ZIP]                  │
    └──────────────────────────────────────────┘

Step 6: Chat Response
══════════════════════
UI: Chat bubble with summary:

    ┌──────────────────────────────────────────┐
    │ 🤖 Assistant:                             │
    │                                           │
    │ I've completed the exploratory data      │
    │ analysis of your sales data.             │
    │                                           │
    │ Key Findings:                             │
    │ • Dataset: 1000 rows × 8 columns         │
    │ • Sales range: $100 - $5000              │
    │ • Strong positive correlation between    │
    │   price and sales volume                 │
    │                                           │
    │ Generated 4 files for you (see above).   │
    │                                           │
    │ ⏱️ Execution Time: 2m 15s                 │
    │ 💰 Cost: $0.58                            │
    └──────────────────────────────────────────┘
```

---

This visual guide should help you understand the complete architecture! Let me know if you'd like me to elaborate on any specific component. 🚀
