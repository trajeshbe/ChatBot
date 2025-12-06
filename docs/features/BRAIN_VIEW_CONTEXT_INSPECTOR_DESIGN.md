# Brain View - Real-Time Context Inspector

**Date**: 2025-12-06
**Feature Request**: Real-time visualization of LLM context, memory, and tools for debugging and understanding

---

## Concept

A **"Brain View"** panel that shows in real-time:
- What conversation history the LLM sees
- What documents/chunks are retrieved
- What tools are being used
- Routing decisions and strategy weights
- Complete context window sent to the LLM

Think of it as **DevTools for LLM interactions** - like Chrome DevTools but for AI context.

---

## UI Design

### Layout Option 1: Side Panel (Recommended)

```
┌─────────────────────────────────────────────────────────┐
│  Chat Interface               │   Brain View            │
│                               │                         │
│  User: Ram is good boy        │  📊 ROUTING DECISION    │
│  AI: [Response]               │  Strategy: DIRECT_LLM   │
│                               │  Confidence: 0.85       │
│  User: Rahul is naughty       │                         │
│  AI: [Response]               │  🧠 CONTEXT SENT TO LLM │
│                               │  ┌───────────────────┐  │
│  User: Tell me about Ram      │  │ Conversation (4)  │  │
│  AI: [Generating...]          │  │ User: Ram is...   │  │
│                               │  │ AI: ...           │  │
│                               │  └───────────────────┘  │
│                               │                         │
│                               │  🔧 TOOLS ACTIVE        │
│                               │  • None                 │
│                               │                         │
│                               │  📄 DOCUMENTS           │
│                               │  • None                 │
└───────────────────────────────┴─────────────────────────┘
```

### Layout Option 2: Bottom Panel

```
┌─────────────────────────────────────────────────────────┐
│  Chat Interface                                         │
│                                                         │
│  User: Tell me about Ram and Rahul                      │
│  AI: [Generating...]                                    │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  🧠 Brain View                                [Collapse]│
│  ┌──────────────┬──────────────┬──────────────┐        │
│  │ 📊 Routing   │ 🧠 Context   │ 🔧 Tools     │        │
│  └──────────────┴──────────────┴──────────────┘        │
│  📌 CONVERSATION_ONLY (weight=0.90)                     │
│  💬 Using 7 messages from conversation history          │
│  ✅ No RAG retrieval (conversation-only mode)           │
└─────────────────────────────────────────────────────────┘
```

### Layout Option 3: Expandable Modal (Developer Mode)

```
┌─────────────────────────────────────────────────────────┐
│  Chat Interface                     [🧠 Brain View]     │
│                                                         │
│  User: Tell me about Ram and Rahul                      │
│  AI: Based on our conversation...                       │
│                                                         │
└─────────────────────────────────────────────────────────┘

[Click 🧠 Brain View button]

┌─────────────────────────────────────────────────────────┐
│  Brain View - Real-Time Context Inspector       [Close] │
├─────────────────────────────────────────────────────────┤
│  📊 Routing │ 🧠 Context │ 🔧 Tools │ 📄 Docs │ ⚡ Perf  │
├─────────────────────────────────────────────────────────┤
│  [Detailed view with tabs...]                           │
└─────────────────────────────────────────────────────────┘
```

---

## Feature Breakdown

### Tab 1: 📊 Routing Decision

Shows the routing logic and strategy weights.

```
┌─────────────────────────────────────────────────────────┐
│ 📊 ROUTING DECISION                                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Strategy Selected: CONVERSATION_ONLY                   │
│  Reason: conversation_only weight (0.90) > 0.8 threshold│
│                                                         │
│  Strategy Weights:                                      │
│  ┌───────────────────────────────────────┐             │
│  │ conversation_only  █████████  0.90    │             │
│  │ rag_short_term     ███        0.30    │             │
│  │ rag_long_term      ███        0.30    │             │
│  │ rag_hybrid         ██         0.25    │             │
│  │ direct_llm         █          0.05    │             │
│  │ tool_navigation    █          0.15    │             │
│  └───────────────────────────────────────┘             │
│                                                         │
│  Query Classification:                                  │
│  • Type: ai_personal                                    │
│  • Confidence: 0.75                                     │
│  • Proper Nouns Detected: Yes (Ram, Rahul)             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Tab 2: 🧠 Context Window

Shows exactly what was sent to the LLM.

```
┌─────────────────────────────────────────────────────────┐
│ 🧠 CONTEXT SENT TO LLM                                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Model: llama3.2-vision:11b                             │
│  Context Size: 2,457 tokens / 8,192 max                 │
│  Messages in Context: 7                                 │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 💬 Conversation History (Last 10 messages)      │   │
│  ├─────────────────────────────────────────────────┤   │
│  │ User: Hello                                     │   │
│  │ AI: Hi! How can I help you today?               │   │
│  │ User: Ram is good boy                           │   │
│  │ AI: I'm sorry, but I don't have any...          │   │
│  │ User: Rahul is a naughty boy                    │   │
│  │ AI: I'm sorry, but I cannot provide...          │   │
│  │ User: tell me about Rahul and Ram               │   │
│  │ [Current query - awaiting response]             │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 📄 Retrieved Documents (0)                      │   │
│  ├─────────────────────────────────────────────────┤   │
│  │ No documents retrieved (conversation-only mode) │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 🎯 System Prompt                                │   │
│  ├─────────────────────────────────────────────────┤   │
│  │ You are a helpful AI assistant. Answer based    │   │
│  │ on the conversation history provided...         │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  [📋 Copy Full Context] [📥 Export as JSON]             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Tab 3: 🔧 Tools & Actions

Shows what tools were triggered and their outputs.

```
┌─────────────────────────────────────────────────────────┐
│ 🔧 TOOLS & ACTIONS                                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Active Tools: None                                     │
│  Reason: CONVERSATION_ONLY mode (no tool usage)         │
│                                                         │
│  Available Tools (not used):                            │
│  ┌─────────────────────────────────────────────────┐   │
│  │ ❌ Navigation Agent (tool_navigation=0.15)      │   │
│  │ ❌ OCR Tool (tool_ocr=0.10)                     │   │
│  │ ❌ Docling Analysis (tool_docling=0.15)         │   │
│  │ ❌ Web Scraping (tool_web_scraping=0.20)        │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Tool Execution Timeline:                               │
│  [Empty - no tools executed]                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Example when tools ARE used:**

```
┌─────────────────────────────────────────────────────────┐
│ 🔧 TOOLS & ACTIONS                                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Tool Execution Timeline:                               │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 1. 🔍 Document Retrieval (t=0ms)                │   │
│  ├─────────────────────────────────────────────────┤   │
│  │ Query: "architecture diagram"                   │   │
│  │ Vector Search: pgvector (cosine similarity)     │   │
│  │ Results: 5 chunks found                         │   │
│  │ Avg Similarity: 0.87                            │   │
│  │ Duration: 45ms                                  │   │
│  │ [View Chunks]                                   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 2. 🎨 Vision Analysis (t=45ms)                  │   │
│  ├─────────────────────────────────────────────────┤   │
│  │ Triggered: Image detected in chunk #2           │   │
│  │ Model: gpt-4o-mini (vision)                     │   │
│  │ Image: architecture_diagram.png                 │   │
│  │ Analysis: "This diagram shows 3 floors..."      │   │
│  │ Duration: 2,300ms                               │   │
│  │ [View Image] [View Full Analysis]               │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 3. 🔄 Reranking (t=2,345ms)                     │   │
│  ├─────────────────────────────────────────────────┤   │
│  │ Initial Chunks: 5                               │   │
│  │ Reranked Chunks: 3                              │   │
│  │ Method: Semantic + Keyword (0.7 + 0.2)          │   │
│  │ Duration: 15ms                                  │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Total Tool Execution Time: 2,360ms                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Tab 4: 📄 Documents & Chunks

Shows retrieved documents and their content.

```
┌─────────────────────────────────────────────────────────┐
│ 📄 DOCUMENTS & CHUNKS                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Retrieved Chunks: 5                                    │
│  Source Type: Short-term memory (session documents)     │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 📄 Chunk #1 (similarity: 0.92)                  │   │
│  ├─────────────────────────────────────────────────┤   │
│  │ Document: project_spec.pdf (Page 3)             │   │
│  │ Content:                                        │   │
│  │ "The architecture diagram shows a 3-tier...     │   │
│  │  system with frontend, backend, and database    │   │
│  │  layers. The building has 3 floors..."          │   │
│  │                                                 │   │
│  │ Metadata:                                       │   │
│  │ • Source: upload                                │   │
│  │ • Upload Date: 2025-12-06                       │   │
│  │ • Chunk Index: 12/45                            │   │
│  │ • Embedding Model: sentence-transformers        │   │
│  │                                                 │   │
│  │ [📋 Copy] [📥 View Full Document]               │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 📄 Chunk #2 (similarity: 0.89)                  │   │
│  ├─────────────────────────────────────────────────┤   │
│  │ [Similar layout...]                             │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  [Show More Chunks...]                                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Tab 5: ⚡ Performance Metrics

Shows timing and performance data.

```
┌─────────────────────────────────────────────────────────┐
│ ⚡ PERFORMANCE METRICS                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Total Response Time: 3,650ms                           │
│                                                         │
│  Breakdown:                                             │
│  ┌───────────────────────────────────────┐             │
│  │ Query Classification    ███  50ms     │             │
│  │ Strategy Routing        █    10ms     │             │
│  │ Context Assembly        ██   25ms     │             │
│  │ LLM Inference          ███████████████ 3,500ms │     │
│  │ Response Processing    ██   65ms      │             │
│  └───────────────────────────────────────┘             │
│                                                         │
│  LLM Metrics:                                           │
│  • Model: llama3.2-vision:11b                           │
│  • Tokens Generated: 127                                │
│  • Tokens/Second: 36.3                                  │
│  • Context Tokens: 2,457                                │
│  • Total Tokens: 2,584                                  │
│                                                         │
│  Resource Usage:                                        │
│  • GPU: Yes (CUDA)                                      │
│  • Memory: 4.2 GB                                       │
│  • Cache Hit: No                                        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Backend - Add Context Debug Endpoint

**File**: `backend/app/api/routes/agent_routes.py`

```python
@router.post("/api/v1/query/debug")
async def query_with_debug_context(
    query: str = Form(...),
    session_id: str = Form(None),
    model: str = Form("gpt-4o-mini"),
    strategy_weights: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Enhanced query endpoint that returns full context debugging info
    """

    # Parse strategy weights
    weights = json.loads(strategy_weights) if strategy_weights else None

    # Create debug context collector
    debug_context = {
        "routing_decision": {},
        "conversation_history": [],
        "retrieved_documents": [],
        "tools_executed": [],
        "performance_metrics": {},
        "llm_context": {}
    }

    # Execute query with debug tracking
    result = await enhanced_rag_agent.query(
        query=query,
        session_id=session_id,
        model_id=model,
        user_preferences={"strategy_weights": weights},
        debug_mode=True  # 🆕 Enable debug tracking
    )

    # Populate debug context
    debug_context["routing_decision"] = result.get("metadata", {}).get("routing_strategy")
    debug_context["conversation_history"] = result.get("debug_info", {}).get("conversation_history", [])
    debug_context["retrieved_documents"] = result.get("sources", [])
    debug_context["performance_metrics"] = {
        "total_time_ms": result.get("metadata", {}).get("latency_ms"),
        "llm_time_ms": result.get("debug_info", {}).get("llm_time_ms"),
        "retrieval_time_ms": result.get("debug_info", {}).get("retrieval_time_ms")
    }

    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "metadata": result["metadata"],
        "debug_context": debug_context  # 🆕 Debug information
    }
```

### Phase 2: Backend - Enhance Enhanced RAG Agent

**File**: `backend/app/agents/enhanced_rag_agent.py`

Add debug tracking throughout the query method:

```python
async def query(
    self,
    query: str,
    session_id: str = None,
    model_id: str = "gpt-4o-mini",
    user_preferences: Dict[str, Any] = None,
    debug_mode: bool = False  # 🆕 Debug flag
) -> Dict[str, Any]:
    """Enhanced query with optional debug tracking"""

    debug_info = {
        "conversation_history": [],
        "retrieved_chunks": [],
        "tools_executed": [],
        "routing_decision": {},
        "context_sent_to_llm": "",
        "timings": {}
    } if debug_mode else None

    # Track routing decision
    if debug_mode:
        debug_info["routing_decision"] = {
            "strategy": "conversation_only",
            "reason": f"conversation_only weight ({conversation_only_weight}) > 0.8",
            "weights": strategy_weights
        }

    # Track conversation history
    if conversation_only_weight > 0.8:
        conversation_history = user_preferences.get('conversation_history', [])

        if debug_mode:
            debug_info["conversation_history"] = conversation_history

        conversation_context = "\n".join([
            f"{msg['role'].capitalize()}: {msg['content']}"
            for msg in conversation_history
        ])

        if debug_mode:
            debug_info["context_sent_to_llm"] = conversation_context

        # Execute LLM query
        result = await self._direct_llm_query(
            query=query,
            conversation_context=conversation_context
        )

        if debug_mode:
            result["debug_info"] = debug_info

        return result
```

### Phase 3: Frontend - Brain View Component

**File**: `frontend/src/components/BrainView.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { Brain, Activity, FileText, Wrench, BarChart3 } from 'lucide-react';

interface BrainViewProps {
  debugContext: any;
  isVisible: boolean;
  onClose: () => void;
}

export const BrainView: React.FC<BrainViewProps> = ({ debugContext, isVisible, onClose }) => {
  const [activeTab, setActiveTab] = useState<'routing' | 'context' | 'tools' | 'docs' | 'perf'>('routing');

  if (!isVisible) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-1/3 bg-white border-l border-gray-200 shadow-2xl overflow-y-auto z-50">
      {/* Header */}
      <div className="sticky top-0 bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="w-6 h-6" />
          <h2 className="text-lg font-bold">Brain View</h2>
        </div>
        <button onClick={onClose} className="hover:bg-white/20 rounded p-1">✕</button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 bg-gray-50">
        <Tab icon={<Activity />} label="Routing" active={activeTab === 'routing'} onClick={() => setActiveTab('routing')} />
        <Tab icon={<Brain />} label="Context" active={activeTab === 'context'} onClick={() => setActiveTab('context')} />
        <Tab icon={<Wrench />} label="Tools" active={activeTab === 'tools'} onClick={() => setActiveTab('tools')} />
        <Tab icon={<FileText />} label="Docs" active={activeTab === 'docs'} onClick={() => setActiveTab('docs')} />
        <Tab icon={<BarChart3 />} label="Perf" active={activeTab === 'perf'} onClick={() => setActiveTab('perf')} />
      </div>

      {/* Content */}
      <div className="p-4">
        {activeTab === 'routing' && <RoutingTab data={debugContext?.routing_decision} />}
        {activeTab === 'context' && <ContextTab data={debugContext?.conversation_history} />}
        {activeTab === 'tools' && <ToolsTab data={debugContext?.tools_executed} />}
        {activeTab === 'docs' && <DocsTab data={debugContext?.retrieved_documents} />}
        {activeTab === 'perf' && <PerfTab data={debugContext?.performance_metrics} />}
      </div>
    </div>
  );
};

// Tab Components
const Tab = ({ icon, label, active, onClick }) => (
  <button
    onClick={onClick}
    className={`flex items-center gap-2 px-4 py-2 border-b-2 ${
      active
        ? 'border-blue-600 text-blue-600 bg-white'
        : 'border-transparent text-gray-600 hover:text-gray-900'
    }`}
  >
    {icon}
    <span className="text-sm font-medium">{label}</span>
  </button>
);

// Routing Tab
const RoutingTab = ({ data }) => (
  <div className="space-y-4">
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <h3 className="font-bold text-blue-900 mb-2">📌 Strategy Selected</h3>
      <p className="text-lg font-semibold">{data?.strategy || 'N/A'}</p>
      <p className="text-sm text-gray-600 mt-1">{data?.reason || 'N/A'}</p>
    </div>

    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <h3 className="font-bold mb-3">Strategy Weights</h3>
      {data?.weights && Object.entries(data.weights).map(([key, value]) => (
        <div key={key} className="mb-2">
          <div className="flex justify-between text-sm mb-1">
            <span>{key}</span>
            <span className="font-semibold">{value}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full"
              style={{ width: `${value * 100}%` }}
            ></div>
          </div>
        </div>
      ))}
    </div>
  </div>
);

// Context Tab
const ContextTab = ({ data }) => (
  <div className="space-y-4">
    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
      <h3 className="font-bold text-purple-900 mb-2">💬 Conversation History</h3>
      <p className="text-sm text-gray-600">Messages in context: {data?.length || 0}</p>
    </div>

    <div className="space-y-2">
      {data?.map((msg, idx) => (
        <div key={idx} className={`p-3 rounded-lg ${
          msg.role === 'user' ? 'bg-blue-50 border border-blue-200' : 'bg-gray-50 border border-gray-200'
        }`}>
          <div className="text-xs font-semibold text-gray-500 mb-1">
            {msg.role === 'user' ? '👤 User' : '🤖 Assistant'}
          </div>
          <div className="text-sm">{msg.content}</div>
        </div>
      ))}
    </div>
  </div>
);

// Tools Tab
const ToolsTab = ({ data }) => (
  <div className="space-y-4">
    {data && data.length > 0 ? (
      data.map((tool, idx) => (
        <div key={idx} className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="font-bold mb-2">{tool.name}</h3>
          <p className="text-sm text-gray-600">{tool.description}</p>
          <div className="mt-2 text-xs text-gray-500">
            Duration: {tool.duration_ms}ms
          </div>
        </div>
      ))
    ) : (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center text-gray-500">
        No tools executed
      </div>
    )}
  </div>
);

// Docs Tab
const DocsTab = ({ data }) => (
  <div className="space-y-4">
    {data && data.length > 0 ? (
      data.map((doc, idx) => (
        <div key={idx} className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex justify-between items-start mb-2">
            <h3 className="font-bold">{doc.filename}</h3>
            <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
              {(doc.score * 100).toFixed(0)}% match
            </span>
          </div>
          <p className="text-sm text-gray-700 line-clamp-3">{doc.content}</p>
        </div>
      ))
    ) : (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center text-gray-500">
        No documents retrieved
      </div>
    )}
  </div>
);

// Performance Tab
const PerfTab = ({ data }) => (
  <div className="space-y-4">
    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
      <h3 className="font-bold text-green-900 mb-2">⚡ Total Time</h3>
      <p className="text-2xl font-bold">{data?.total_time_ms || 0}ms</p>
    </div>

    <div className="space-y-2">
      <PerfBar label="LLM Inference" time={data?.llm_time_ms} total={data?.total_time_ms} />
      <PerfBar label="Retrieval" time={data?.retrieval_time_ms} total={data?.total_time_ms} />
      <PerfBar label="Other" time={(data?.total_time_ms - data?.llm_time_ms - data?.retrieval_time_ms)} total={data?.total_time_ms} />
    </div>
  </div>
);

const PerfBar = ({ label, time, total }) => (
  <div>
    <div className="flex justify-between text-sm mb-1">
      <span>{label}</span>
      <span className="font-semibold">{time || 0}ms</span>
    </div>
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div
        className="bg-green-600 h-2 rounded-full"
        style={{ width: `${((time || 0) / total) * 100}%` }}
      ></div>
    </div>
  </div>
);
```

### Phase 4: Integrate into ChatInterface

**File**: `frontend/src/components/ChatInterfaceEnhanced.tsx`

```typescript
import { BrainView } from './BrainView';

export const ChatInterfaceEnhanced = () => {
  const [brainViewVisible, setBrainViewVisible] = useState(false);
  const [debugContext, setDebugContext] = useState(null);

  const sendMessage = async () => {
    // ... existing code ...

    // 🆕 Use debug endpoint
    const response = await axios.post(`${API_URL}/api/v1/query/debug`, formData);

    // 🆕 Store debug context
    setDebugContext(response.data.debug_context);

    // Update messages
    setMessages([...messages, userMessage, aiMessage]);
  };

  return (
    <div className="relative h-screen flex">
      {/* Existing chat interface */}
      <div className={`flex-1 ${brainViewVisible ? 'w-2/3' : 'w-full'}`}>
        {/* ... existing chat UI ... */}

        {/* Brain View Toggle Button */}
        <button
          onClick={() => setBrainViewVisible(!brainViewVisible)}
          className="fixed bottom-20 right-4 bg-purple-600 text-white p-3 rounded-full shadow-lg hover:bg-purple-700"
          title="Toggle Brain View"
        >
          <Brain className="w-6 h-6" />
        </button>
      </div>

      {/* Brain View Panel */}
      <BrainView
        debugContext={debugContext}
        isVisible={brainViewVisible}
        onClose={() => setBrainViewVisible(false)}
      />
    </div>
  );
};
```

---

## Summary

The **Brain View** feature provides:
- ✅ Real-time visibility into LLM context
- ✅ Routing decision transparency
- ✅ Tool execution tracking
- ✅ Document retrieval visualization
- ✅ Performance profiling
- ✅ Developer-friendly debugging

This is like **Chrome DevTools for AI** - essential for understanding and debugging complex RAG systems!

Would you like me to start implementing this feature?
