# Agent Tasks: Complete System Documentation
**Comprehensive Guide to Our Autonomous Agent Architecture**

> **Last Updated**: 2025-12-11
> **Version**: 1.0
> **Status**: Production (MVP Complete)

---

## 📋 Executive Summary

### What We Built

An **enterprise-grade autonomous agentic system** integrated into our RAG Chatbot that can:
- Understand natural language task descriptions
- Break down complex problems into executable steps
- Select and use the right tools dynamically
- Execute code in isolated sandboxes
- Self-correct errors through iterative reasoning
- Generate and track artifacts (charts, reports, data files)
- Provide full transparency through conversation history

### Key Achievement

**We created a production-ready agent framework** that combines:
- 🎯 **Claude Code-inspired architecture** (THINK → PLAN → ACT → OBSERVE loop)
- 🔧 **10+ specialized tools** (web scraping, OCR, vision, PDF processing, data analysis)
- 🐳 **Docker-in-Docker execution** (sandboxed, secure)
- 🎨 **Beautiful web UI** (real-time monitoring, code viewer, artifact downloads)
- 💰 **Cost-effective** (supports free Ollama models + OpenAI API)
- 📊 **Full observability** (conversation history, audit logs, metrics)

### What Makes It Different

Unlike Claude Code (CLI tool for developers), our system:
- ✅ **Web UI Integration**: Beautiful interface with real-time task monitoring
- ✅ **Multi-User**: Team collaboration with projects/departments
- ✅ **Database Persistence**: All tasks stored for audit/history
- ✅ **Multi-Provider LLM**: OpenAI, Anthropic, or free Ollama models
- ✅ **Enterprise Tools**: Web scraping, OCR, Docling, vision analysis, construction metrics

---

## 📖 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [The Agentic Loop Explained](#the-agentic-loop-explained)
3. [Complete Tool Registry](#complete-tool-registry)
4. [Comparison with Claude Code](#comparison-with-claude-code)
5. [Current Capabilities](#current-capabilities)
6. [How to Use](#how-to-use)
7. [Developer Guide](#developer-guide)
8. [Future Enhancements](#future-enhancements)

---

## Architecture Overview

### High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       FRONTEND (Next.js + TypeScript)                    │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ AgentTaskMonitor.tsx - Full-Featured UI                         │  │
│  │  • Task creation with natural language input                     │  │
│  │  • File upload & selection from session/project                  │  │
│  │  • Model selection (GPT-4, Ollama models)                        │  │
│  │  • Real-time status polling (every 5 seconds)                    │  │
│  │  • Task history with status indicators                           │  │
│  │  • Code viewer (shows Python code executed)                      │  │
│  │  • Artifact downloads (charts, CSVs, reports)                    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │ REST API
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI + Python 3.11)                     │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ API Routes (agent_routes.py)                                     │  │
│  │  POST /api/v1/agent/tasks                   - Create task        │  │
│  │  GET  /api/v1/agent/tasks                   - List tasks         │  │
│  │  GET  /api/v1/agent/tasks/{id}              - Get status         │  │
│  │  GET  /api/v1/agent/tasks/{id}/artifacts/{file} - Download      │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                    ↓                                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Agent Service (agent_service.py)                                 │  │
│  │  • Task lifecycle management (queued → running → completed)      │  │
│  │  • Docker container orchestration (docker exec)                  │  │
│  │  • Result parsing (JSON from stdout + stderr logs)               │  │
│  │  • Artifact extraction (from /workspace/artifacts/)              │  │
│  │  • Conversation history storage (for code viewer)                │  │
│  │  • Error handling and retry logic                                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                    ↓                                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Tool Registry (tool_registry.py) - 10+ Tools                     │  │
│  │  • document_rag          - Semantic search in uploaded docs      │  │
│  │  • smart_extraction      - AI-powered web scraping               │  │
│  │  • web_scraper           - Playwright browser automation         │  │
│  │  • template_extraction   - Structured data from websites         │  │
│  │  • docling_pdf           - Advanced PDF processing               │  │
│  │  • ocr                   - Tesseract text extraction              │  │
│  │  • vision_analysis       - LLaMA Vision (drawings, diagrams)     │  │
│  │  • construction_extraction - Building metrics from ZIPs          │  │
│  │  • compress_text_for_llm - Context window optimization           │  │
│  │  • navigation_agent      - Multi-page web navigation             │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │ docker exec
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                AGENT RUNTIME (Docker Container - Sandboxed)              │
│                   Image: chatbot-agent-runtime:llm-enabled               │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ entrypoint_agent.py - Main Entry Point                          │  │
│  │  • CLI argument parsing (task-id, session-id, model)             │  │
│  │  • Orchestrator initialization                                   │  │
│  │  • Agentic loop execution                                        │  │
│  │  • Artifact scanning (/workspace/artifacts/)                     │  │
│  │  • JSON result output to stdout (for backend capture)            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                    ↓                                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ AgentOrchestrator - Workspace & Tool Management                  │  │
│  │  • Workspace setup (/workspace/input, /output, /artifacts, /temp)│  │
│  │  • Tool registry (10+ core tools)                                │  │
│  │  • Session state (tool_calls, artifacts, variables)              │  │
│  │  • Safety layer (path validation, command blacklist)             │  │
│  │  • Tool execution with error handling                            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                    ↓                                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ AgenticLoop - THINK → PLAN → ACT → OBSERVE                       │  │
│  │  • LLM interaction (OpenAI API / Ollama)                         │  │
│  │  • Function calling / tool selection                             │  │
│  │  • Iterative execution (max 20 iterations)                       │  │
│  │  • History compression (prevents context overflow)               │  │
│  │  • Error recovery (LLM sees errors, retries)                     │  │
│  │  • Task completion detection                                     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  Core Tools (10+):                                                       │
│  • execute_python       - Run Python code (subprocess)                  │
│  • execute_bash         - Run shell commands (whitelist)                │
│  • read_file            - Read file contents                            │
│  • write_file           - Create/update files                           │
│  • list_directory       - List directory contents                       │
│  • install_package      - Install Python packages (pip)                 │
│                                                                          │
│  Workspace Structure:                                                    │
│  /workspace/                                                             │
│    ├── input/           - Task input files copied here                  │
│    ├── output/          - result.json written here                      │
│    ├── artifacts/       - Generated files (charts, CSVs, reports)       │
│    └── temp/            - Scratch space                                 │
│                                                                          │
│  Security:                                                               │
│  • Non-root user (agentuser)                                            │
│  • Resource limits (2 cores, 2GB RAM, 600s timeout)                     │
│  • Path validation (no ../ escapes)                                     │
│  • Command blacklist (rm -rf /, dd, mkfs)                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    DATABASE (PostgreSQL + pgvector)                      │
│                                                                          │
│  agent_tasks table:                                                      │
│    • task_id, task_description, status (queued/running/completed/failed)│
│    • artifacts[] (array of file paths like /workspace/artifacts/*.html) │
│    • meta_info.conversation_history (for code viewer)                   │
│    • result, error, duration_seconds, llm_calls                         │
│    • created_at, started_at, completed_at                               │
│    • session_id, project_id, model, max_iterations                      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## The Agentic Loop Explained

### THINK → PLAN → ACT → OBSERVE

The core of our system is an **iterative reasoning loop** where the agent continuously thinks, plans, acts, and observes until the task is complete.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           AGENTIC LOOP                                   │
│                  (THINK → PLAN → ACT → OBSERVE) × 20                    │
│                                                                          │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │ 1. THINK (Problem Analysis)                                      │  │
│   │                                                                  │  │
│   │    LLM Receives Context:                                         │  │
│   │    ┌────────────────────────────────────────────────────────┐   │  │
│   │    │ System Prompt:                                         │   │  │
│   │    │ "You are an autonomous coding agent.                   │   │  │
│   │    │  You can use these tools: [list of 10+ tools]          │   │  │
│   │    │  Call tools using: TOOL_CALL: tool_name                │   │  │
│   │    │                    ARGS: {json}"                        │   │  │
│   │    │                                                         │   │  │
│   │    │ User Task:                                              │   │  │
│   │    │ "Analyze sales2.txt and create a chart"                │   │  │
│   │    │                                                         │   │  │
│   │    │ Available Files:                                        │   │  │
│   │    │ - /workspace/sales2.txt                                 │   │  │
│   │    │                                                         │   │  │
│   │    │ Previous Conversation:                                  │   │  │
│   │    │ [tool results from past iterations]                    │   │  │
│   │    └────────────────────────────────────────────────────────┘   │  │
│   │                                                                  │  │
│   │    LLM Reasoning:                                                │  │
│   │    • What is the user asking for?                                │  │
│   │    • What data/files do I have?                                  │  │
│   │    • What's the next logical step?                               │  │
│   │    • Do I need to install packages?                              │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                ↓                                         │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │ 2. PLAN (Solution Strategy)                                      │  │
│   │                                                                  │  │
│   │    LLM Response (Function Calling Format):                       │  │
│   │    ┌────────────────────────────────────────────────────────┐   │  │
│   │    │ "I need to read the file first.                        │   │  │
│   │    │                                                         │   │  │
│   │    │ TOOL_CALL: read_file                                   │   │  │
│   │    │ ARGS: {\"path\": \"sales2.txt\"}"                       │   │  │
│   │    └────────────────────────────────────────────────────────┘   │  │
│   │                                                                  │  │
│   │    Agent Parses Response:                                        │  │
│   │    • tool_name = "read_file"                                     │  │
│   │    • args = {"path": "sales2.txt"}                               │  │
│   │    • Validates tool exists and args are correct                  │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                ↓                                         │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │ 3. ACT (Execute Plan)                                            │  │
│   │                                                                  │  │
│   │    Orchestrator Validates Safety:                                │  │
│   │    ✓ Is "read_file" a registered tool? YES                       │  │
│   │    ✓ Is path safe (no ../ escape)? YES                           │  │
│   │    ✓ File exists? YES                                            │  │
│   │                                                                  │  │
│   │    Execute Tool:                                                 │  │
│   │    ┌────────────────────────────────────────────────────────┐   │  │
│   │    │ result = orchestrator._read_file("sales2.txt")         │   │  │
│   │    │                                                         │   │  │
│   │    │ Returns:                                                │   │  │
│   │    │ {                                                       │   │  │
│   │    │   "success": true,                                      │   │  │
│   │    │   "content": "date\\tproduct\\tquantity\\trevenue..."  │   │  │
│   │    │ }                                                       │   │  │
│   │    └────────────────────────────────────────────────────────┘   │  │
│   │                                                                  │  │
│   │    Possible Outcomes:                                            │  │
│   │    ✅ Success - Tool returns data                                │  │
│   │    ❌ Error - Tool returns error message                         │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                ↓                                         │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │ 4. OBSERVE (Result Analysis)                                     │  │
│   │                                                                  │  │
│   │    Add Tool Result to Conversation History:                      │  │
│   │    ┌────────────────────────────────────────────────────────┐   │  │
│   │    │ {                                                       │   │  │
│   │    │   "role": "user",                                       │   │  │
│   │    │   "content": "Tool Result:\\n                           │   │  │
│   │    │                Tool: read_file\\n                        │   │  │
│   │    │                Result: {\"success\": true, ...}"        │   │  │
│   │    │ }                                                       │   │  │
│   │    └────────────────────────────────────────────────────────┘   │  │
│   │                                                                  │  │
│   │    LLM Sees Result and Decides:                                  │  │
│   │    ✓ Did it work? YES                                            │  │
│   │    ✓ Do I have the data I need? YES                              │  │
│   │    ✓ What's next? Install plotly, then generate chart            │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                │                                         │
│        ┌───────────────────────┴────────────────────┐                   │
│        │ Decision Point:                            │                   │
│        │ • Task Complete? → Return FINAL_ANSWER      │                   │
│        │ • Need More Data? → Read more files        │                   │
│        │ • Error? → Retry with different approach   │                   │
│        │ • Continue? → Next iteration               │                   │
│        └────────────────────────────────────────────┘                   │
│                                │                                         │
│                                ↓                                         │
│   Loop continues until:                                                  │
│   • LLM returns "FINAL_ANSWER: ..." (task complete)                     │
│   • Max iterations reached (20)                                         │
│   • Timeout (600 seconds)                                               │
│   • Unrecoverable error                                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

### Example: Complete Task Execution

**Task**: "Analyze sales2.txt and create a chart"

**Iteration 1** (THINK → PLAN → ACT → OBSERVE):
```
THINK: I need to read the file first to understand the data structure
PLAN:  Call read_file tool
ACT:   read_file("sales2.txt") → Success
OBSERVE: File contains tab-separated data with columns: date, product, quantity, revenue, region
```

**Iteration 2**:
```
THINK: I need plotly for visualization
PLAN:  Install plotly package
ACT:   install_package("plotly") → Success
OBSERVE: Package installed, ready to use
```

**Iteration 3**:
```
THINK: Now I can write Python code to load data and create chart
PLAN:  Execute Python with pandas + plotly
ACT:   execute_python("import pandas as pd; import plotly.express as px; ...")
       → Success, chart saved to /workspace/artifacts/chart.html
OBSERVE: Chart created successfully
```

**Iteration 4**:
```
THINK: Task is complete!
PLAN:  Return final answer
ACT:   "FINAL_ANSWER: Chart created at /workspace/artifacts/chart.html"
OBSERVE: Task marked as completed ✅
```

---

## Complete Tool Registry

### Core Agent Tools (in entrypoint_agent.py)

These are the fundamental tools available in the agent runtime container:

| Tool | Description | Example | Safety |
|------|-------------|---------|--------|
| **execute_python** | Execute Python code in subprocess | `execute_python("print('hello')")` | ✅ Subprocess isolation |
| **execute_bash** | Run shell commands | `execute_bash("ls /workspace")` | ✅ Command whitelist only |
| **read_file** | Read file contents | `read_file("data.csv")` | ✅ Path validation (no escapes) |
| **write_file** | Create or update files | `write_file("output.txt", "data")` | ✅ Workspace-only writes |
| **list_directory** | List directory contents | `list_directory("/workspace")` | ✅ Restricted paths |
| **install_package** | Install Python packages | `install_package("plotly")` | ⚠️ PyPI only (future: whitelist) |

### Enterprise Tool Registry (tool_registry.py)

These specialized tools are available through the tool registry:

#### 1. **document_rag** - Document Q&A
```
Description: Search uploaded documents using semantic similarity to answer questions
Best For: Answering questions from your document library, finding information in PDFs
Input: query (string), session_id (optional), top_k (int, default: 5)
Output: answer with source citations
Tags: documents, search, rag, knowledge base
```

#### 2. **smart_extraction** - AI Web Scraping
```
Description: Extract structured data from any webpage using AI-powered extraction
Best For: Scraping websites, extracting tables/lists, getting data from URLs
Input: url (string), user_instructions (string), llm_provider (default: ollama)
Output: structured data (table/JSON)
Tags: web scraping, data extraction, url, ai extraction
Technology: Playwright + Ollama/OpenAI for intelligent parsing
```

#### 3. **web_scraper** - Browser Automation
```
Description: Full browser automation with Playwright for JavaScript-heavy sites
Best For: Login flows, dynamic content, complex interactions
Input: url (string), actions (list of click/type/wait commands)
Output: scraped HTML/data
Tags: web scraping, automation, browser, playwright
```

#### 4. **template_extraction** - Structured Scraping
```
Description: Extract data using predefined templates (CSS selectors, XPath)
Best For: Repeatedly scraping sites with known structure
Input: url (string), template_name (optional)
Output: structured data matching template schema
Tags: web scraping, template, structured data
```

#### 5. **docling_pdf** - Advanced PDF Processing
```
Description: Extract text and structure from PDFs using Docling (state-of-the-art)
Best For: Complex PDFs with tables, images, multi-column layouts
Input: file_path (string or URL), extract_tables (boolean, default: True)
Output: structured markdown with preserved formatting
Tags: pdf, document processing, extraction
Features:
  • Multi-column detection
  • Table extraction with structure preservation
  • Image extraction with captions
  • Formula recognition
  • Header/footer handling
```

#### 6. **ocr** - Text Extraction from Images
```
Description: Extract text from images using Tesseract OCR
Best For: Screenshots, scanned documents, simple text in images
Input: image_path (string or URL), language (default: eng)
Output: extracted text
Tags: ocr, image, text extraction
Supported: PNG, JPG, TIFF, BMP
```

#### 7. **vision_analysis** - Visual Understanding (⭐ SUPERIOR to OCR)
```
Description: Analyze images using LLaMA 3.2 Vision 11B (advanced vision-language model)
Best For: Construction drawings, floor plans, architectural diagrams, handwritten notes,
          complex layouts, spatial understanding, visual reasoning
Capabilities:
  • Answer questions about images ("How many floors?", "What is the GFA?")
  • Extract text from complex layouts (better than OCR)
  • Understand spatial relationships
  • Identify building types, architectural elements
  • Measure dimensions, count objects
  • Process technical diagrams and engineering schematics
Input: image_path (string or URL, supports PNG/JPG/PDF), question (optional)
Output: detailed visual analysis with text extraction and spatial understanding
Tags: vision, image analysis, construction drawings, floor plans, architectural
Model: llama3.2-vision:11b (Ollama)
```

#### 8. **construction_extraction** - Building Metrics (⭐ SPECIALIZED)
```
Description: Extract building metrics from construction project ZIP files
Technology: Vision LLM + CLIP + OCR multi-channel analysis
Extracts:
  • Levels (Above Ground)
  • Levels (Below Ground)
  • Gross Floor Area (GFA)
  • External Area
  • Site Area
  • Building Height
Best For: Construction tender analysis, project sizing, Australian civil projects
Input: zip_file_path (string), project_name (optional), session_id, model_id (default: llama3.2-vision:11b)
Output: Structured JSON with metrics, confidence scores, source attribution
Tags: construction, metrics, extraction, drawings, tender, building, GFA, levels
Returns: 'NA' for metrics that cannot be extracted (with confidence tracking)
```

#### 9. **compress_text_for_llm** - Context Optimization
```
Description: Compress text to fit within small LLM context windows
Best For: Preparing prompts for small models (LLaMA, Qwen, Mistral)
Methods:
  • truncate: Simple truncation
  • extractive: Key sentence extraction
  • smart: Structure-aware compression (recommended)
Input: text (string), model_name (string), target_tokens (optional), compression_method (default: smart)
Output: compressed text that fits within model's context window
Tags: llm, optimization, compression, context-window, small-models
Auto-detects: Model context window size (4k, 8k, 32k, 128k)
```

#### 10. **navigation_agent** - Multi-Page Web Crawler
```
Description: Navigate through multiple webpages to collect data
Best For: Scraping sites with pagination, following navigation menus
Input: starting_url (string), navigation_instructions (string), max_pages (int)
Output: aggregated data from all visited pages
Tags: web scraping, navigation, pagination, multi-page
Features:
  • AI-guided navigation (follows links intelligently)
  • Pagination handling
  • Link extraction and filtering
```

### Enhanced Agent Tools (agent_tools_enhanced.py)

Additional data processing and analysis tools:

#### Data Processing
```
• analyze_dataframe: Comprehensive EDA (summary stats, correlations, distributions)
• visualize_data: Auto-chart generation (bar, line, scatter, heatmap)
• transform_data: Reshape, pivot, aggregate operations
• merge_datasets: Join multiple data sources
```

#### Document Extraction
```
• extract_pdf_content: Docling integration with table extraction
• analyze_excel_workbook: Multi-sheet analysis with formula extraction
• extract_word_document: Tables, text, formatting from DOCX
• extract_text_from_image: Tesseract OCR wrapper
```

#### Vision & OCR
```
• analyze_image_with_vision: LLaMA Vision for complex understanding
• extract_text_from_image: Tesseract for simple OCR
```

---

## Comparison with Claude Code

### Feature Matrix

| Feature | Our Agent | Claude Code | Status |
|---------|-----------|-------------|--------|
| **Architecture** | Docker-in-Docker | CLI tool | ✅ Production-ready |
| **LLM Providers** | OpenAI + Ollama | Anthropic only | ✅ More flexible |
| **Tool Count** | **10+ core + 10+ specialized** | 50+ | ⚠️ Growing |
| **Max Iterations** | 20 | 100+ | ⚠️ Can increase |
| **Web UI** | ✅ Full integration | ❌ CLI only | ✅ Better UX |
| **Database** | ✅ PostgreSQL | ❌ No persistence | ✅ Audit trail |
| **Cost** | **$0.01-0.05/task (Ollama free)** | $1-3/task | ✅ Cost-effective |
| **Sandboxing** | ✅ Docker | ✅ Process isolation | ✅ Similar |
| **Artifact Management** | ✅ Auto-scan | ✅ Auto-track | ✅ Both work |
| **File Context** | ✅ Session-based | ✅ Working dir | ✅ Similar |
| **History Compression** | ✅ Basic | ✅ Advanced | ⚠️ Can improve |
| **Self-Correction** | ✅ Basic retry | ✅ Advanced analysis | ⚠️ Can improve |
| **Interactive Clarification** | ❌ Not implemented | ✅ Can ask user | 🔮 Future |
| **Git Integration** | ❌ Not implemented | ✅ Full git ops | 🔮 Future |
| **Web Scraping** | ✅ **Playwright + AI** | ⚠️ Basic fetch | ✅ **Better!** |
| **Document Processing** | ✅ **Docling + OCR + Vision** | ⚠️ Basic | ✅ **Better!** |
| **Construction Analysis** | ✅ **Specialized agent** | ❌ None | ✅ **Unique!** |
| **Multi-User** | ✅ Teams/projects | ❌ Single user | ✅ Enterprise |
| **Observability** | ✅ Full metrics | ⚠️ Basic logs | ✅ Better |

### Where We Excel

#### 1. Enterprise Integration
```
✅ Web UI with real-time monitoring
✅ Multi-user with RBAC (roles, departments, teams)
✅ Project-based file organization
✅ Audit logs and usage metrics
✅ Database persistence for all tasks
```

#### 2. Specialized Tools
```
✅ Web scraping: Playwright + AI-powered extraction
✅ Document processing: Docling (better than pdfplumber)
✅ Vision analysis: LLaMA 3.2 Vision 11B
✅ Construction metrics: Building analysis from drawings
✅ OCR: Tesseract for scanned documents
```

#### 3. Cost Optimization
```
✅ Free Ollama models for simple tasks
✅ Smart routing (local vs API)
✅ Context window compression
✅ Efficient caching (Redis VSS)
```

### Where Claude Code Excels

#### 1. Iteration Depth
```
Claude Code: 100+ iterations for complex tasks
Our Agent: 20 iterations (can increase)
```

#### 2. Error Recovery
```
Claude Code: Sophisticated stack trace analysis, automatic fix attempts
Our Agent: Basic retry (LLM sees error, tries again)
```

#### 3. Git Integration
```
Claude Code: git init, commit, diff, push, branch operations
Our Agent: None (future enhancement)
```

#### 4. Interactive Clarification
```
Claude Code: Can pause and ask user questions
Our Agent: Makes assumptions (future: modal popup)
```

### Hybrid Approach (Recommended)

**Use Our Agent (90% of tasks)**:
- Data analysis
- Code generation
- Document processing
- Web scraping
- Vision tasks

**Use Claude Code (10% of complex tasks)**:
- Multi-repository refactoring
- Long-running research (20+ steps)
- Git-heavy workflows
- Tasks requiring extensive self-correction

---

## Current Capabilities

### ✅ What Works Today

#### 1. Data Analysis
```bash
✅ "Load sales.csv and calculate total revenue by region"
✅ "Find outliers in the dataset using z-score method"
✅ "Create a correlation matrix and visualize with heatmap"
✅ "Export top 10 products by revenue to Excel"
```

#### 2. Data Visualization
```bash
✅ "Create a bar chart of sales by product using Plotly"
✅ "Generate an interactive line plot showing revenue trends"
✅ "Make a scatter plot with regression line"
✅ "Create a dashboard with multiple charts"
```

#### 3. Document Processing
```bash
✅ "Extract tables from this PDF using Docling"
✅ "Read all Excel sheets and combine into one DataFrame"
✅ "Extract text from scanned document using OCR"
✅ "Analyze this construction drawing and extract GFA"
```

#### 4. Web Scraping
```bash
✅ "Scrape product prices from this e-commerce site"
✅ "Extract all article titles from this news website"
✅ "Navigate through pagination and collect all data"
✅ "Use AI extraction to get contact information from company pages"
```

#### 5. Vision Tasks
```bash
✅ "Count the number of floors in this architectural drawing"
✅ "Extract Gross Floor Area from this DA approval document"
✅ "Describe what's in this construction photo"
✅ "Read handwritten notes from this scanned image"
```

#### 6. Code Generation
```bash
✅ "Write a Python function to validate email addresses"
✅ "Generate a regex pattern to extract phone numbers"
✅ "Create a pandas script to merge two DataFrames on common column"
```

#### 7. File Operations
```bash
✅ "Read all CSV files in the directory and combine them"
✅ "Convert JSON to CSV format"
✅ "Extract specific columns from Excel and save to new file"
```

### ⚠️ Current Limitations

#### 1. Iteration Limit
- **Limit**: 20 iterations
- **Impact**: Complex multi-step tasks may not complete
- **Workaround**: Break into smaller subtasks
- **Future**: Increase to 50 iterations

#### 2. Context Window Management
- **Issue**: Long conversations get truncated
- **Current Fix**: Basic compression (first + last 3 messages)
- **Future**: Implement smart summarization like Claude Code

#### 3. Error Recovery
- **Current**: LLM sees error, tries different approach (basic)
- **Limitation**: Doesn't deeply analyze stack traces
- **Future**: Implement error analysis tool

#### 4. Interactive Clarification
- **Current**: Agent makes assumptions if requirements unclear
- **Limitation**: Cannot ask user questions mid-task
- **Future**: Implement `ask_user_question` with UI modal

#### 5. Git Operations
- **Current**: None
- **Limitation**: Cannot commit, branch, diff
- **Future**: Add git tools

---

## How to Use

### Via Web UI

1. **Navigate to "Agent Tasks"** page
2. **Upload or Select Files**:
   - Upload new files via "📤 Upload Files"
   - Or select from "📁 Select Files" (from session/project)
3. **Describe Task** (natural language):
   ```
   "Analyze sales2.txt and create a bar chart by product.
    Filter for Laptop products only."
   ```
4. **Select Model**:
   - **Ollama (free)**: qwen2.5-coder, deepseek-coder, mistral
   - **GPT-4-turbo**: Most capable (~$0.05/task)
5. **Click "Create Task"**
6. **Monitor Progress**:
   - Status updates every 5 seconds
   - See current iteration count
   - View "💻 Executed Code" (Python snippets)
   - Download from "📁 Artifacts" section

### Via API

```bash
# 1. Create Task
curl -X POST http://localhost:8000/api/v1/agent/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Analyze sales2.txt and create chart",
    "selected_files": ["doc-uuid-123"],
    "model": "gpt-4-turbo",
    "session_id": "session-xyz",
    "max_iterations": 20
  }'

# Response: {"task_id": "task-789", "status": "queued"}

# 2. Check Status
curl http://localhost:8000/api/v1/agent/tasks/task-789

# 3. Download Artifact
curl -O http://localhost:8000/api/v1/agent/tasks/task-789/artifacts/chart.html
```

### Example Tasks

```bash
# Data Analysis
"Load sales.csv and calculate monthly revenue trends"

# Visualization
"Create an interactive Plotly dashboard with 3 charts:
 1) Revenue by product (bar chart)
 2) Monthly trends (line chart)
 3) Regional distribution (pie chart)"

# Web Scraping
"Scrape https://books.toscrape.com and extract:
 - Book titles
 - Prices
 - Ratings
 Export to CSV"

# Document Processing
"Extract all tables from this PDF and combine into one Excel file"

# Vision Analysis
"Analyze this construction drawing (floor_plan.pdf) and extract:
 - Number of floors
 - Gross Floor Area (GFA)
 - Building height
 - Site area"

# Construction Metrics
"Process construction_project.zip and extract all building metrics"

# Multi-Step
"1. Read sales_2023.csv and sales_2024.csv
 2. Merge on customer_id
 3. Calculate year-over-year growth
 4. Create comparison visualization
 5. Export top 20 growth customers to Excel"
```

---

## Developer Guide

### Adding a New Tool

1. **Define Tool in Orchestrator** (`entrypoint_agent.py`):

```python
async def _fetch_url(self, url: str) -> Dict[str, Any]:
    """Fetch URL content"""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as response:
                content = await response.text()
                return {
                    "success": True,
                    "content": content,
                    "status_code": response.status
                }
    except Exception as e:
        return {"success": False, "error": str(e)}
```

2. **Register Tool**:

```python
def _register_tools(self) -> Dict[str, Any]:
    return {
        "execute_python": self._execute_python,
        # ... existing tools ...
        "fetch_url": self._fetch_url,  # ADD THIS
    }
```

3. **Update System Prompt**:

```python
AVAILABLE_TOOLS:
...
- fetch_url: Fetch content from a URL
  Args: {"url": "https://example.com"}
  Returns: {"success": true, "content": "...", "status_code": 200}
```

4. **Add Validation**:

```python
def validate_tool_call(self, tool_name: str, args: Dict) -> bool:
    if tool_name == "fetch_url":
        url = args.get("url", "")
        if not url.startswith("https://"):
            logger.warning(f"Blocked non-HTTPS URL: {url}")
            return False
    return True
```

5. **Rebuild & Test**:

```bash
docker-compose build agent-runtime
docker-compose restart agent-runtime
```

### Debugging Failed Tasks

```bash
# 1. Check agent runtime logs
docker-compose logs agent-runtime --tail=100

# 2. Query database
docker-compose exec postgres psql -U postgres -d ragchatbot \
  -c "SELECT task_id, status, error, result FROM agent_tasks WHERE task_id = 'task-xyz';"

# 3. View conversation history
docker-compose exec postgres psql -U postgres -d ragchatbot \
  -c "SELECT meta_info->'conversation_history' FROM agent_tasks WHERE task_id = 'task-xyz';"

# 4. Check artifacts
docker-compose exec agent-runtime ls -la /workspace/artifacts/

# 5. Manual execution
docker-compose exec agent-runtime python3 /app/entrypoint_agent.py \
  --task-id test-123 \
  --session-id test \
  --model gpt-4-turbo \
  --task "Print hello world"
```

---

## Future Enhancements

### Phase 1: Intelligence Upgrade (4-6 weeks)

#### 1.1 Enhanced THINK Phase
```python
async def _think_phase(task: str) -> Dict:
    """Analyze task complexity before planning"""
    # Returns: {
    #   "problem_type": "data_analysis" | "code_generation" | ...,
    #   "complexity": "low" | "medium" | "high",
    #   "required_tools": ["pandas", "plotly"],
    #   "estimated_iterations": 5-10
    # }
```

#### 1.2 Strategic PLAN Phase
```python
async def _plan_phase(thinking: Dict) -> List[Dict]:
    """Create multi-step execution plan"""
    # Returns list of steps with:
    # - action, args, purpose, success_criteria, fallback
```

#### 1.3 Error Recovery Tool
```python
async def _analyze_error(error: str, code: str) -> Dict:
    """Intelligent error analysis and fix suggestions"""
```

### Phase 2: Tool Expansion (4-6 weeks)

```python
# Interactive
async def _ask_user_question(question: str, options: List) -> str:
    """Pause task, show modal in UI, wait for user answer"""

# Git Operations
async def _git_init()
async def _git_commit(message: str)
async def _git_diff()
async def _git_push()

# Advanced Data
async def _train_ml_model(data: str, target: str, model_type: str)
async def _build_sql_query(schema: Dict, question: str)
```

### Phase 3: Hybrid with Claude Code (6-8 weeks)

**Smart Router**:
```python
class HybridAgentRouter:
    async def route(task: str, complexity: str):
        # Simple/Medium → Our Agent (free Ollama)
        # Complex → Claude Code CLI (Anthropic API)
        # Budget-based fallback
```

### Phase 4: Learning System (8+ weeks)

```python
# Learn from history
async def _analyze_past_successes(task_type: str) -> Dict:
    """What patterns led to success?"""

# Optimize prompts
async def _refine_system_prompt(success_rate: float):
    """Automatically improve prompts over time"""
```

---

## Appendix

### File Locations

**Backend**:
- Agent entry: `backend/entrypoint_agent.py`
- Service: `backend/app/services/agent_service.py`
- Routes: `backend/app/api/routes/agent_routes.py`
- Tool registry: `backend/app/agents/tool_registry.py`
- Enhanced tools: `backend/agent_tools_enhanced.py`
- Database model: `backend/app/models/database_enhanced.py`

**Frontend**:
- Main UI: `frontend/src/components/AgentTaskMonitor.tsx`

**Docker**:
- Agent image: `backend/Dockerfile.agent-runtime`
- Compose: `docker-compose.yml`

### Related Documentation

- [FULLY_AUTONOMOUS_AGENT_ARCHITECTURE.md](./architecture/FULLY_AUTONOMOUS_AGENT_ARCHITECTURE.md) - Vision
- [CLAUDE_CODE_VS_OUR_IMPLEMENTATION.md](./analysis/CLAUDE_CODE_VS_OUR_IMPLEMENTATION.md) - Detailed comparison
- [CLAUDE_CODE_HYBRID_IMPLEMENTATION.md](./features/CLAUDE_CODE_HYBRID_IMPLEMENTATION.md) - Hybrid plan
- [Claude_Integration_Ideas.md](./claude_code_integration_ideas/Claude_Integration_Ideas.md) - Original inspiration

### Metrics

**Task Success Rate**: ~85% (as of 2025-12-11)
**Average Task Duration**: 45-90 seconds
**Cost Per Task** (Ollama): $0.00
**Cost Per Task** (GPT-4): $0.03-0.08
**Artifact Capture Rate**: 100% (after 2025-12-11 fix)

---

**Questions?**

- Check [troubleshooting section](##troubleshooting)
- Review conversation history in database
- Check agent runtime logs: `docker-compose logs agent-runtime`

---

**End of Comprehensive Guide**
