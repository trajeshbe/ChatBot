# Multi-Tool Agent Architecture

> **Purpose**: Transform RAG Chat into an intelligent multi-tool AI agent that can leverage all existing services (Smart Extraction, Docling PDF, OCR, Web Scraping, Navigation) plus MCP servers for unlimited extensibility
>
> **Framework**: Extends existing LangGraph agent (`backend/app/agents/rag_agent.py`)
>
> **Created**: 2025-01-22

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Design](#architecture-design)
3. [Tool Registry](#tool-registry)
4. [LangGraph Workflow](#langgraph-workflow)
5. [MCP Server Integration](#mcp-server-integration)
6. [Implementation Plan](#implementation-plan)
7. [Usage Examples](#usage-examples)

---

## Overview

### Current State

The existing RAG Chat has:
- Simple keyword-based intent detection
- Basic document RAG retrieval
- Prefect workflow orchestration
- LangGraph foundation (4 nodes: analyze → retrieve → generate → validate)

### Desired State

**Unified AI Agent** that intelligently selects from:

| **Category** | **Tools Available** |
|-------------|---------------------|
| **Document Processing** | RAG retrieval, Docling PDF processing, OCR (Tesseract) |
| **Web Extraction** | Ultra-Smart extraction, Template extraction, Navigation agent, Playwright scraping |
| **Data Processing** | CSV/Excel generation, Data transformation, Schema validation |
| **External Services** | MCP servers (unlimited extensibility) |

### Key Requirements

1. ✅ **Use Existing LangGraph Framework** - Extend `backend/app/agents/rag_agent.py`
2. ✅ **Tool Registry Pattern** - Dictionary-based tool discovery
3. ✅ **LLM-based Tool Selection** - Intelligent routing based on user query
4. ✅ **MCP Server Support** - Plug-and-play external tool integration
5. ✅ **Backward Compatible** - Existing RAG queries still work
6. ✅ **Observable** - Track which tools were used and why

---

## Architecture Design

### High-Level Flow

```
User Query
    ↓
┌─────────────────────────────────────────────────────────┐
│  ENHANCED LANGGRAPH AGENT                               │
│                                                          │
│  1. Intent Analysis (LLM-powered)                       │
│     ↓                                                   │
│  2. Tool Selection (Function Calling)                   │
│     ↓                                                   │
│  3. Tool Execution (Parallel when possible)             │
│     ↓                                                   │
│  4. Result Synthesis (Combine multi-tool results)       │
│     ↓                                                   │
│  5. Response Generation (with tool usage metadata)      │
└─────────────────────────────────────────────────────────┘
    ↓
Response + Tool Usage Info
```

### Components

#### 1. Tool Registry (`app/agents/tool_registry.py`)

Central registry of all available tools:

```python
{
    "document_rag": {
        "name": "Document RAG Retrieval",
        "description": "Search uploaded documents using semantic similarity",
        "function": rag_service.query,
        "input_schema": {...},
        "use_cases": ["answer questions", "find information", "summarize documents"]
    },
    "smart_extraction": {
        "name": "Smart Web Extraction",
        "description": "Extract structured data from web pages using AI",
        "function": extract_ultra_smart,
        "input_schema": {...},
        "use_cases": ["scrape website", "extract data", "get web content"]
    },
    "template_extraction": {
        "name": "Template-based Extraction",
        "description": "Extract data using predefined templates",
        "function": extract_with_template,
        "input_schema": {...},
        "use_cases": ["structured extraction", "consistent format", "batch scraping"]
    },
    "docling_pdf": {
        "name": "Advanced PDF Processing",
        "description": "Extract text, tables, and images from complex PDFs using Docling",
        "function": docling_service.process_pdf,
        "input_schema": {...},
        "use_cases": ["pdf processing", "complex documents", "tables and charts"]
    },
    "ocr": {
        "name": "OCR Text Extraction",
        "description": "Extract text from images using Tesseract OCR",
        "function": ocr_service.extract_text,
        "input_schema": {...},
        "use_cases": ["image to text", "scanned documents", "screenshots"]
    },
    "navigation_agent": {
        "name": "Web Navigation Agent",
        "description": "Navigate multi-page websites to find and extract information",
        "function": navigation_agent.navigate_and_extract,
        "input_schema": {...},
        "use_cases": ["multi-page scraping", "navigate website", "find specific page"]
    },
    "web_scraper": {
        "name": "General Web Scraper",
        "description": "Scrape web pages using Playwright",
        "function": scraper_service.scrape_url,
        "input_schema": {...},
        "use_cases": ["basic scraping", "javascript sites", "dynamic content"]
    },
    # MCP Servers (dynamically loaded)
    "mcp_*": {
        # Auto-discovered from MCP server registry
    }
}
```

#### 2. Enhanced LangGraph Agent (`app/agents/enhanced_rag_agent.py`)

Extends existing `RAGAgent` with new nodes:

```python
class EnhancedRAGAgent(RAGAgent):
    """
    Multi-tool AI agent that extends basic RAG with intelligent tool selection
    """

    def __init__(self):
        self.tool_registry = ToolRegistry()
        self.mcp_client = MCPClient()  # For MCP server integration
        super().__init__()

    def _build_graph(self):
        """Build enhanced workflow graph"""
        workflow = StateGraph(EnhancedAgentState)

        # Enhanced nodes
        workflow.add_node("analyze_intent", self.analyze_intent)
        workflow.add_node("select_tools", self.select_tools)
        workflow.add_node("execute_tools", self.execute_tools)
        workflow.add_node("synthesize_results", self.synthesize_results)
        workflow.add_node("generate_response", self.generate_response)

        # Workflow
        workflow.set_entry_point("analyze_intent")
        workflow.add_edge("analyze_intent", "select_tools")
        workflow.add_edge("select_tools", "execute_tools")
        workflow.add_edge("execute_tools", "synthesize_results")
        workflow.add_edge("synthesize_results", "generate_response")
        workflow.add_edge("generate_response", END)

        self.graph = workflow.compile()
```

#### 3. Agent State (`app/agents/agent_state.py`)

```python
class EnhancedAgentState(TypedDict):
    """Extended state for multi-tool agent"""

    # Input
    query: str
    session_id: Optional[str]
    user_preferences: Dict[str, Any]

    # Intent analysis
    detected_intent: str
    confidence: float

    # Tool selection
    selected_tools: List[str]  # List of tool IDs
    tool_params: Dict[str, Any]  # Parameters for each tool

    # Tool execution
    tool_results: Dict[str, Any]  # Results from each tool
    tool_errors: Dict[str, str]  # Any errors

    # Response synthesis
    answer: str
    sources: List[Dict]
    metadata: Dict[str, Any]  # Tool usage, timing, etc.
```

---

## Tool Registry

### Registration Mechanism

```python
# app/agents/tool_registry.py

class ToolRegistry:
    """Central registry for all agent tools"""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._register_builtin_tools()
        self._discover_mcp_servers()

    def _register_builtin_tools(self):
        """Register built-in tools from existing services"""

        # Document RAG
        self.register(
            tool_id="document_rag",
            name="Document RAG Retrieval",
            description="Search uploaded documents using semantic similarity to answer questions based on your document library",
            function=self._wrap_rag_service,
            input_schema={
                "query": "str",
                "session_id": "Optional[str]",
                "top_k": "int = 5"
            },
            tags=["documents", "search", "knowledge base"]
        )

        # Smart Web Extraction
        self.register(
            tool_id="smart_extraction",
            name="Smart Web Extraction",
            description="Extract structured data from any web page using AI. Can handle dynamic content, JavaScript, and complex layouts",
            function=self._wrap_smart_extraction,
            input_schema={
                "url": "str",
                "user_instructions": "str",
                "llm_provider": "str = 'openai'"
            },
            tags=["web scraping", "data extraction", "url"]
        )

        # Template Extraction
        self.register(
            tool_id="template_extraction",
            name="Template-based Extraction",
            description="Extract data using predefined templates for consistent, repeatable extraction from similar pages",
            function=self._wrap_template_extraction,
            input_schema={
                "url": "str",
                "template_id": "str"
            },
            tags=["web scraping", "template", "structured data"]
        )

        # Docling PDF Processing
        self.register(
            tool_id="docling_pdf",
            name="Advanced PDF Processing",
            description="Process complex PDFs with tables, charts, and multi-column layouts using Docling. Best for academic papers, reports, and structured documents",
            function=self._wrap_docling,
            input_schema={
                "file_path": "str",
                "extract_tables": "bool = True",
                "extract_images": "bool = False"
            },
            tags=["pdf", "documents", "tables"]
        )

        # OCR
        self.register(
            tool_id="ocr",
            name="OCR Text Extraction",
            description="Extract text from images and scanned documents using Tesseract OCR. Supports multiple languages",
            function=self._wrap_ocr,
            input_schema={
                "image_path": "str",
                "language": "str = 'eng'"
            },
            tags=["ocr", "image to text", "scanned documents"]
        )

        # Navigation Agent
        self.register(
            tool_id="navigation_agent",
            name="Web Navigation Agent",
            description="Navigate multi-page websites intelligently to find and extract specific information. Can follow links, click buttons, and traverse site structure",
            function=self._wrap_navigation_agent,
            input_schema={
                "start_url": "str",
                "goal": "str",
                "max_steps": "int = 10"
            },
            tags=["navigation", "multi-page", "web automation"]
        )

        # General Web Scraper
        self.register(
            tool_id="web_scraper",
            name="General Web Scraper",
            description="Basic web scraping using Playwright. Good for simple pages and when you need full browser rendering",
            function=self._wrap_scraper,
            input_schema={
                "url": "str",
                "wait_for": "Optional[str]"
            },
            tags=["web scraping", "playwright", "browser automation"]
        )

    def _discover_mcp_servers(self):
        """Auto-discover and register MCP servers"""
        # Will implement MCP discovery mechanism
        pass

    def get_tool(self, tool_id: str) -> Optional[Tool]:
        """Get a specific tool by ID"""
        return self.tools.get(tool_id)

    def search_tools(self, query: str, tags: List[str] = None) -> List[Tool]:
        """Search tools by natural language query or tags"""
        # Implement semantic search over tool descriptions
        pass

    def get_tools_for_llm(self) -> List[Dict]:
        """
        Get tools in OpenAI function calling format
        For LLM-based tool selection
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": tool_id,
                    "description": tool.description,
                    "parameters": tool.input_schema
                }
            }
            for tool_id, tool in self.tools.items()
        ]
```

---

## LangGraph Workflow

### Node Implementations

#### 1. Analyze Intent

```python
async def analyze_intent(self, state: EnhancedAgentState) -> EnhancedAgentState:
    """
    Analyze user query to understand intent
    Uses LLM to classify query type
    """
    logger.info(f"Analyzing intent for: {state['query']}")

    # Use LLM for intent classification
    system_prompt = """You are an intent classifier. Analyze the user's query and determine what they want to do.

Possible intents:
- document_qa: Answer questions based on uploaded documents
- web_extraction: Extract data from a website
- pdf_processing: Process a PDF document
- image_ocr: Extract text from an image
- web_navigation: Navigate a website to find information
- general_search: General web search or information lookup

Respond in JSON format:
{
    "intent": "intent_type",
    "confidence": 0.0-1.0,
    "reasoning": "why you chose this intent"
}
"""

    response = await self.llm_service.chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": state['query']}
        ],
        response_format={"type": "json_object"}
    )

    intent_data = json.loads(response['content'])

    state['detected_intent'] = intent_data['intent']
    state['confidence'] = intent_data['confidence']
    state['metadata']['intent_reasoning'] = intent_data['reasoning']

    logger.info(f"Detected intent: {intent_data['intent']} (confidence: {intent_data['confidence']})")

    return state
```

#### 2. Select Tools

```python
async def select_tools(self, state: EnhancedAgentState) -> EnhancedAgentState:
    """
    Select appropriate tools based on intent and query
    Uses OpenAI function calling for tool selection
    """
    logger.info("Selecting tools...")

    # Get available tools in function calling format
    tools = self.tool_registry.get_tools_for_llm()

    # Use LLM with function calling to select tools
    system_prompt = """You are a tool selection expert. Based on the user's query, select the most appropriate tool(s) to use.

You can select one or multiple tools if the task requires it. For example:
- To extract data from a PDF on a website: use web_scraper + docling_pdf
- To answer a question: use document_rag
- To get data from a website: use smart_extraction or navigation_agent

Consider:
1. What is the user asking for?
2. What data sources are involved (documents, web, images)?
3. What level of complexity is needed?
"""

    response = await self.llm_service.chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Query: {state['query']}\nDetected intent: {state['detected_intent']}"}
        ],
        tools=tools,
        tool_choice="auto"  # Let LLM decide which tools to call
    )

    # Extract tool calls
    tool_calls = response.get('tool_calls', [])

    selected_tools = []
    tool_params = {}

    for tool_call in tool_calls:
        tool_id = tool_call['function']['name']
        params = json.loads(tool_call['function']['arguments'])

        selected_tools.append(tool_id)
        tool_params[tool_id] = params

        logger.info(f"Selected tool: {tool_id} with params: {params}")

    state['selected_tools'] = selected_tools
    state['tool_params'] = tool_params

    return state
```

#### 3. Execute Tools

```python
async def execute_tools(self, state: EnhancedAgentState) -> EnhancedAgentState:
    """
    Execute selected tools in parallel when possible
    """
    logger.info(f"Executing {len(state['selected_tools'])} tools...")

    tool_results = {}
    tool_errors = {}

    # Execute tools in parallel using asyncio.gather
    tasks = []
    for tool_id in state['selected_tools']:
        tool = self.tool_registry.get_tool(tool_id)
        params = state['tool_params'].get(tool_id, {})

        tasks.append(self._execute_single_tool(tool_id, tool, params))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for tool_id, result in zip(state['selected_tools'], results):
        if isinstance(result, Exception):
            tool_errors[tool_id] = str(result)
            logger.error(f"Tool {tool_id} failed: {result}")
        else:
            tool_results[tool_id] = result
            logger.info(f"Tool {tool_id} succeeded")

    state['tool_results'] = tool_results
    state['tool_errors'] = tool_errors

    return state

async def _execute_single_tool(self, tool_id: str, tool: Tool, params: Dict) -> Any:
    """Execute a single tool with error handling"""
    try:
        start_time = time.time()

        result = await tool.function(**params)

        execution_time = time.time() - start_time

        return {
            "success": True,
            "result": result,
            "execution_time_ms": execution_time * 1000
        }

    except Exception as e:
        logger.error(f"Error executing tool {tool_id}: {e}")
        raise
```

#### 4. Synthesize Results

```python
async def synthesize_results(self, state: EnhancedAgentState) -> EnhancedAgentState:
    """
    Combine results from multiple tools into coherent information
    """
    logger.info("Synthesizing results from tools...")

    # If only one tool was used, simple passthrough
    if len(state['tool_results']) == 1:
        tool_id = list(state['tool_results'].keys())[0]
        state['synthesized_data'] = state['tool_results'][tool_id]['result']
        return state

    # Multiple tools: use LLM to synthesize
    system_prompt = """You are a data synthesis expert. Combine information from multiple tools into a coherent dataset.

Your job:
1. Identify common fields across results
2. Merge related information
3. Preserve all unique data
4. Flag any conflicts or inconsistencies
"""

    # Prepare tool results for LLM
    results_summary = {}
    for tool_id, result_data in state['tool_results'].items():
        tool = self.tool_registry.get_tool(tool_id)
        results_summary[tool.name] = result_data['result']

    response = await self.llm_service.chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Combine these results:\n\n{json.dumps(results_summary, indent=2)}"}
        ]
    )

    state['synthesized_data'] = response['content']

    return state
```

#### 5. Generate Response

```python
async def generate_response(self, state: EnhancedAgentState) -> EnhancedAgentState:
    """
    Generate final user-facing response with tool usage transparency
    """
    logger.info("Generating final response...")

    # Build response with tool usage metadata
    response_parts = []

    # Main answer
    response_parts.append(state['synthesized_data'])

    # Tool usage footer
    if state['selected_tools']:
        tools_used = [
            self.tool_registry.get_tool(tid).name
            for tid in state['selected_tools']
        ]
        response_parts.append(f"\n\n🔧 **Tools Used**: {', '.join(tools_used)}")

    # Timing info
    total_time = sum(
        r['execution_time_ms']
        for r in state['tool_results'].values()
    )
    response_parts.append(f"⏱️ **Processing Time**: {total_time:.0f}ms")

    state['answer'] = "\n".join(response_parts)

    # Build sources from tool results
    sources = []
    for tool_id, result_data in state['tool_results'].items():
        if 'sources' in result_data.get('result', {}):
            sources.extend(result_data['result']['sources'])

    state['sources'] = sources

    # Metadata for frontend
    state['metadata']['tools_used'] = state['selected_tools']
    state['metadata']['tool_timing'] = {
        tid: state['tool_results'][tid]['execution_time_ms']
        for tid in state['selected_tools']
    }

    return state
```

---

## MCP Server Integration

### What is MCP?

**Model Context Protocol (MCP)** is Anthropic's open standard for connecting AI assistants to external data sources and tools. It provides:

- **Standardized interface** for tool discovery and invocation
- **Security** through capability-based access control
- **Extensibility** via plug-and-play server architecture

### Integration Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Enhanced RAG Agent                                       │
│                                                            │
│  ┌──────────────┐                                        │
│  │ Tool Registry│                                        │
│  │              │                                        │
│  │  Built-in    │                                        │
│  │  Tools       │                                        │
│  │  ┌────────┐  │                                        │
│  │  │ RAG    │  │                                        │
│  │  │ Smart  │  │                                        │
│  │  │ Scrape │  │                                        │
│  │  └────────┘  │                                        │
│  │              │                                        │
│  │  MCP Tools   │         ┌─────────────────────────┐   │
│  │  ┌────────┐  │◄────────│  MCP Client             │   │
│  │  │ GitHub │  │         │                         │   │
│  │  │ Slack  │  │         │  - Tool Discovery       │   │
│  │  │ Custom │  │         │  - Schema Validation    │   │
│  │  └────────┘  │         │  - Invocation           │   │
│  └──────────────┘         └─────────────────────────┘   │
│                                      │                    │
└──────────────────────────────────────┼────────────────────┘
                                       │
                     ┌─────────────────┴─────────────────┐
                     │                                   │
              ┌──────▼──────┐                   ┌───────▼────────┐
              │ MCP Server  │                   │  MCP Server    │
              │             │                   │                │
              │  GitHub     │                   │   Slack        │
              │  - Issues   │                   │   - Messages   │
              │  - PRs      │                   │   - Channels   │
              │  - Code     │                   │   - Users      │
              └─────────────┘                   └────────────────┘
```

### MCP Client Implementation

```python
# app/agents/mcp_client.py

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
from typing import List, Dict, Any

class MCPClient:
    """Client for interacting with MCP servers"""

    def __init__(self):
        self.servers: Dict[str, ClientSession] = {}
        self.available_tools: Dict[str, Dict] = {}

    async def register_server(self, server_name: str, command: str, args: List[str] = None):
        """
        Register an MCP server

        Example:
            await mcp_client.register_server(
                "github",
                "npx",
                ["-y", "@modelcontextprotocol/server-github"]
            )
        """
        logger.info(f"Registering MCP server: {server_name}")

        server_params = StdioServerParameters(
            command=command,
            args=args or [],
            env=None
        )

        # Connect to server
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize connection
                await session.initialize()

                # Get available tools
                tools_response = await session.list_tools()

                # Store session and tools
                self.servers[server_name] = session

                for tool in tools_response.tools:
                    tool_id = f"mcp_{server_name}_{tool.name}"
                    self.available_tools[tool_id] = {
                        "server": server_name,
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    }

                logger.info(f"Registered {len(tools_response.tools)} tools from {server_name}")

    async def call_tool(self, tool_id: str, arguments: Dict[str, Any]) -> Any:
        """
        Call an MCP tool

        Args:
            tool_id: Tool identifier (e.g., "mcp_github_create_issue")
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        if tool_id not in self.available_tools:
            raise ValueError(f"Unknown MCP tool: {tool_id}")

        tool_info = self.available_tools[tool_id]
        server_name = tool_info['server']
        tool_name = tool_info['name']

        session = self.servers[server_name]

        # Call tool
        result = await session.call_tool(tool_name, arguments=arguments)

        return result.content

    def get_tools_for_registry(self) -> List[Dict]:
        """
        Get MCP tools in a format suitable for Tool Registry
        """
        tools = []

        for tool_id, tool_info in self.available_tools.items():
            tools.append({
                "tool_id": tool_id,
                "name": f"{tool_info['server'].title()} - {tool_info['name']}",
                "description": tool_info['description'],
                "function": lambda args, tid=tool_id: self.call_tool(tid, args),
                "input_schema": tool_info['input_schema'],
                "tags": ["mcp", tool_info['server']],
                "source": "mcp"
            })

        return tools
```

### Auto-Discovery of MCP Servers

```python
# app/core/config.py

class Settings(BaseSettings):
    # Existing settings...

    # MCP Server Configuration
    MCP_SERVERS: List[Dict[str, Any]] = Field(
        default=[
            {
                "name": "github",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {
                    "GITHUB_TOKEN": "${GITHUB_TOKEN}"
                }
            },
            {
                "name": "slack",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-slack"],
                "env": {
                    "SLACK_TOKEN": "${SLACK_TOKEN}"
                }
            }
        ],
        description="MCP servers to auto-register"
    )

# In tool_registry.py

async def _discover_mcp_servers(self):
    """Auto-discover and register MCP servers from config"""
    settings = get_settings()

    for server_config in settings.MCP_SERVERS:
        try:
            await self.mcp_client.register_server(
                server_name=server_config['name'],
                command=server_config['command'],
                args=server_config.get('args', [])
            )

            # Add MCP tools to registry
            mcp_tools = self.mcp_client.get_tools_for_registry()
            for tool_info in mcp_tools:
                self.register(**tool_info)

            logger.info(f"✅ MCP server '{server_config['name']}' registered")

        except Exception as e:
            logger.warning(f"⚠️  Failed to register MCP server '{server_config['name']}': {e}")
```

### Example: GitHub MCP Server

Once registered, the GitHub MCP server adds these tools:

- `mcp_github_create_issue`: Create GitHub issues
- `mcp_github_search_code`: Search code across repositories
- `mcp_github_get_pr`: Get pull request details
- `mcp_github_create_pr`: Create pull requests

**User Query**: "Create a GitHub issue to track the bug in the login flow"

**Agent Response**:
1. Detects intent: "github_operation"
2. Selects tool: `mcp_github_create_issue`
3. Executes with params: `{repo: "...", title: "Bug in login flow", body: "..."}`
4. Returns: "✅ Created issue #123"

---

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1)

**Goal**: Build foundation for multi-tool agent

**Tasks**:
1. ✅ Create `app/agents/tool_registry.py` with `ToolRegistry` class
2. ✅ Create `app/agents/agent_state.py` with `EnhancedAgentState`
3. ✅ Create `app/agents/enhanced_rag_agent.py` extending `RAGAgent`
4. ✅ Register 2-3 existing tools (RAG, Smart Extraction, Web Scraper) as proof of concept
5. ✅ Write unit tests for tool registry

**Files to Create**:
- `backend/app/agents/tool_registry.py`
- `backend/app/agents/agent_state.py`
- `backend/app/agents/enhanced_rag_agent.py`
- `backend/tests/test_tool_registry.py`

### Phase 2: Tool Integration (Week 2)

**Goal**: Register all existing services as tools

**Tasks**:
1. ✅ Wrap all existing services with tool interface:
   - `document_rag` → `rag_service.query`
   - `smart_extraction` → Ultra-smart extraction endpoint
   - `template_extraction` → Template extraction endpoint
   - `docling_pdf` → Docling PDF processing
   - `ocr` → Tesseract OCR service
   - `navigation_agent` → Navigation agent
   - `web_scraper` → Playwright scraper
2. ✅ Implement tool wrapper functions in `tool_registry.py`
3. ✅ Test each tool individually
4. ✅ Document tool usage examples

**Files to Modify**:
- `backend/app/agents/tool_registry.py` (add all tools)

### Phase 3: LLM-based Tool Selection (Week 3)

**Goal**: Implement intelligent tool selection using LLM function calling

**Tasks**:
1. ✅ Implement `analyze_intent()` node with LLM-based classification
2. ✅ Implement `select_tools()` node with OpenAI function calling
3. ✅ Implement tool schema generation for function calling
4. ✅ Add fallback logic (if tool selection fails, default to RAG)
5. ✅ Test with various query types

**Files to Modify**:
- `backend/app/agents/enhanced_rag_agent.py` (add nodes)

### Phase 4: Parallel Tool Execution (Week 4)

**Goal**: Execute multiple tools in parallel when possible

**Tasks**:
1. ✅ Implement `execute_tools()` with `asyncio.gather`
2. ✅ Add error handling for individual tool failures
3. ✅ Implement timeout mechanism (max execution time per tool)
4. ✅ Add retry logic for transient failures
5. ✅ Test parallel execution with 2-3 tools

**Files to Modify**:
- `backend/app/agents/enhanced_rag_agent.py` (execute_tools node)

### Phase 5: MCP Integration (Week 5)

**Goal**: Add MCP server support

**Tasks**:
1. ✅ Install MCP Python SDK: `pip install mcp`
2. ✅ Create `app/agents/mcp_client.py` with `MCPClient` class
3. ✅ Implement MCP server registration
4. ✅ Implement MCP tool discovery
5. ✅ Add MCP tools to tool registry
6. ✅ Test with sample MCP server (GitHub or filesystem)

**Files to Create**:
- `backend/app/agents/mcp_client.py`
- `backend/tests/test_mcp_client.py`

**Dependencies to Add**:
```
# requirements.txt
mcp>=0.1.0
```

### Phase 6: API Integration (Week 6)

**Goal**: Expose enhanced agent through chat API

**Tasks**:
1. ✅ Modify `/api/v1/query` to use `EnhancedRAGAgent`
2. ✅ Add `tool_usage` field to response schema
3. ✅ Add endpoint to list available tools: `/api/v1/tools`
4. ✅ Add endpoint to get tool details: `/api/v1/tools/{tool_id}`
5. ✅ Update OpenAPI docs

**Files to Modify**:
- `backend/app/main.py` or `backend/app/api/routes/models.py`
- Add `backend/app/api/routes/tools.py` (new)

### Phase 7: Frontend Integration (Week 7)

**Goal**: Display tool usage in chat UI

**Tasks**:
1. ✅ Update `ChatInterfaceEnhanced.tsx` to show tool usage badges
2. ✅ Add tooltip showing tool execution details
3. ✅ Add "Tools" section in sidebar showing available tools
4. ✅ Add visual indicator when multiple tools are used
5. ✅ Test UX flow

**Files to Modify**:
- `frontend/src/components/ChatInterfaceEnhanced.tsx`
- `frontend/src/components/Sidebar.tsx`

### Phase 8: Testing & Documentation (Week 8)

**Goal**: Comprehensive testing and docs

**Tasks**:
1. ✅ Write integration tests for multi-tool scenarios
2. ✅ Write E2E tests for common workflows
3. ✅ Performance testing (latency, throughput)
4. ✅ Update user documentation
5. ✅ Create developer guide for adding new tools

**Files to Create**:
- `backend/tests/integration/test_multi_tool_agent.py`
- `docs/guides/MULTI_TOOL_AGENT_GUIDE.md`
- `docs/guides/ADDING_CUSTOM_TOOLS.md`
- `docs/guides/MCP_SERVER_INTEGRATION.md`

---

## Usage Examples

### Example 1: Simple Document Q&A

**User**: "What is the main topic of the uploaded research paper?"

**Agent Workflow**:
1. **Intent**: `document_qa`
2. **Tool Selected**: `document_rag`
3. **Execution**: Query document embeddings
4. **Response**: "The research paper focuses on transformer architectures for NLP..."

**Response Metadata**:
```json
{
  "tools_used": ["document_rag"],
  "tool_timing": {
    "document_rag": 234.5
  }
}
```

### Example 2: Web Data Extraction

**User**: "Get me all the mystery books from books.toscrape.com"

**Agent Workflow**:
1. **Intent**: `web_extraction`
2. **Tool Selected**: `smart_extraction`
3. **Execution**: Ultra-smart extraction with navigation
4. **Response**: Table with 20 mystery books

**Response Metadata**:
```json
{
  "tools_used": ["smart_extraction"],
  "tool_timing": {
    "smart_extraction": 3421.0
  },
  "extraction_method": "playwright+openai"
}
```

### Example 3: Multi-Tool Workflow

**User**: "Download the PDF from example.com/report.pdf and tell me what the key findings are"

**Agent Workflow**:
1. **Intent**: `multi_step_extraction`
2. **Tools Selected**: `web_scraper` + `docling_pdf` + `document_rag`
3. **Execution** (parallel):
   - `web_scraper`: Download PDF → `/tmp/report.pdf`
   - `docling_pdf`: Process PDF → Extract text and tables
   - `document_rag`: Query processed content → Answer question
4. **Response**: "The key findings are: 1) Revenue increased 23%, 2) Customer satisfaction up 15%..."

**Response Metadata**:
```json
{
  "tools_used": ["web_scraper", "docling_pdf", "document_rag"],
  "tool_timing": {
    "web_scraper": 1234.5,
    "docling_pdf": 2341.2,
    "document_rag": 456.7
  },
  "total_time_ms": 4032.4
}
```

### Example 4: MCP Server Usage

**User**: "Create a GitHub issue to track the login bug"

**Agent Workflow**:
1. **Intent**: `github_operation`
2. **Tool Selected**: `mcp_github_create_issue`
3. **Execution**: Call GitHub MCP server
4. **Response**: "✅ Created issue #456: 'Bug in login flow' at username/repo"

**Response Metadata**:
```json
{
  "tools_used": ["mcp_github_create_issue"],
  "tool_timing": {
    "mcp_github_create_issue": 892.3
  },
  "issue_url": "https://github.com/username/repo/issues/456"
}
```

### Example 5: Complex Multi-Step Query

**User**: "Search for all TypeScript files in my GitHub repo that mention 'authentication', then summarize the current auth implementation"

**Agent Workflow**:
1. **Intent**: `code_analysis`
2. **Tools Selected**: `mcp_github_search_code` + `document_rag`
3. **Execution**:
   - `mcp_github_search_code`: Find all `.ts` files with "authentication"
   - `document_rag`: Analyze code snippets and summarize
4. **Response**: "Your authentication implementation uses JWT tokens with..."

---

## Benefits of This Architecture

### 1. **Extensibility**
- ✅ Add new tools by simply registering them
- ✅ MCP servers provide unlimited external integrations
- ✅ No core code changes needed for new capabilities

### 2. **Intelligence**
- ✅ LLM automatically selects best tool(s) for the task
- ✅ Can combine multiple tools when needed
- ✅ Self-optimizing based on query patterns

### 3. **Transparency**
- ✅ Users see which tools were used
- ✅ Execution timing visible
- ✅ Easy to debug and optimize

### 4. **Performance**
- ✅ Parallel tool execution when possible
- ✅ Caching at tool level
- ✅ Async/await throughout

### 5. **Future-Proof**
- ✅ MCP standard ensures compatibility
- ✅ Easy to add new services (databases, APIs, etc.)
- ✅ Modular architecture allows independent updates

---

## Next Steps

1. **Review this architecture** - Confirm approach is sound
2. **Start Phase 1** - Build tool registry foundation
3. **Iterative development** - Test each phase before moving to next
4. **Gather feedback** - Adjust based on usage patterns

**Ready to begin implementation!** 🚀
