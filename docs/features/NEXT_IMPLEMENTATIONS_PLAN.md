# Next Implementations Plan - 2025-12-13

**Date**: 2025-12-13
**Priority**: P0 - Critical UX Improvements
**Status**: 📋 PLANNED

---

## 📋 Overview

Four major enhancements to improve user experience and bring ChatGPT-like and Claude Code-like interactivity:

1. ✨ **Streaming Response in Chat UI** (like ChatGPT)
2. 🤖 **Interactive Agent Tasks** (like Claude Code)
3. 🔧 **OpenAI Codex Option in Agent Tasks**
4. 🎯 **Claude Code Option in Agent Tasks**

---

## Implementation 1: Streaming Response in Chat UI

### 🎯 Goal
Real-time streaming of LLM responses character-by-character in the chat UI, similar to ChatGPT's typing effect.

### 📊 Current State

**Chat Interface**: `/frontend/src/components/ChatInterfaceEnhanced.tsx`
- Currently uses blocking HTTP POST request
- Waits for entire response before displaying
- Shows loading spinner during generation
- No real-time feedback

**Backend API**: `/backend/app/api/routes/`
- Uses standard JSON responses
- No Server-Sent Events (SSE) implementation
- LLM calls are synchronous

### 🔧 Required Changes

#### Phase 1: Backend Streaming Infrastructure

**File 1: Add SSE Route** (`backend/app/api/routes/chat_routes.py` - NEW)

```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

router = APIRouter()

@router.post("/api/v1/chat/stream")
async def stream_chat_response(
    query: str,
    session_id: str,
    model_id: str,
    db: Session = Depends(get_db)
):
    """
    Stream chat response using Server-Sent Events (SSE)

    Returns:
        EventSource stream with incremental chunks
    """

    async def event_generator():
        try:
            # Classify query
            yield {
                "event": "status",
                "data": json.dumps({"status": "classifying", "message": "Analyzing query..."})
            }

            # Get RAG context if needed
            yield {
                "event": "status",
                "data": json.dumps({"status": "retrieving", "message": "Searching documents..."})
            }

            # Stream LLM response
            yield {
                "event": "status",
                "data": json.dumps({"status": "generating", "message": "Generating response..."})
            }

            # Call LLM with streaming
            async for chunk in llm_service.generate_stream(
                prompt=augmented_prompt,
                model_id=model_id
            ):
                yield {
                    "event": "chunk",
                    "data": json.dumps({"content": chunk})
                }

            # Send completion with metadata
            yield {
                "event": "done",
                "data": json.dumps({
                    "sources": sources,
                    "latency_ms": latency,
                    "tokens_used": tokens
                })
            }

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }

    return EventSourceResponse(event_generator())
```

**File 2: Extend LLM Service** (`backend/app/services/llm_service.py`)

Add streaming support:

```python
async def generate_stream(
    self,
    prompt: str,
    model_id: str,
    temperature: float = 0.7,
    max_tokens: int = 2000
) -> AsyncIterator[str]:
    """
    Stream LLM response chunk by chunk

    Yields:
        str: Text chunks as they are generated
    """

    if model_id.startswith("gpt-"):
        # OpenAI streaming
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.openai_api_key)

        stream = await client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    elif model_id.startswith("claude-"):
        # Anthropic streaming
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=self.anthropic_api_key)

        async with client.messages.stream(
            model=model_id,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            async for text in stream.text_stream:
                yield text

    else:
        # Ollama streaming
        import httpx
        ollama_url = f"{self.ollama_host}/api/generate"

        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                ollama_url,
                json={
                    "model": model_id,
                    "prompt": prompt,
                    "stream": True
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
```

**File 3: Add SSE Dependency** (`backend/requirements.txt`)

```txt
sse-starlette==1.8.2
```

#### Phase 2: Frontend Streaming UI

**File 1: Add Streaming Hook** (`frontend/src/hooks/useStreamingChat.ts` - NEW)

```typescript
import { useState, useCallback } from 'react';

interface StreamingMessage {
  role: 'user' | 'assistant';
  content: string;
  isStreaming?: boolean;
  sources?: Source[];
  metadata?: any;
}

export const useStreamingChat = (apiUrl: string) => {
  const [messages, setMessages] = useState<StreamingMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentStream, setCurrentStream] = useState('');

  const sendMessage = useCallback(async (
    query: string,
    sessionId: string,
    modelId: string
  ) => {
    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: query }]);

    // Add empty assistant message for streaming
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: '',
      isStreaming: true
    }]);

    setIsStreaming(true);
    setCurrentStream('');

    try {
      const eventSource = new EventSource(
        `${apiUrl}/api/v1/chat/stream?query=${encodeURIComponent(query)}&session_id=${sessionId}&model_id=${modelId}`
      );

      let accumulatedContent = '';
      let sources = [];
      let metadata = {};

      eventSource.addEventListener('status', (e) => {
        const data = JSON.parse(e.data);
        console.log('Status:', data.message);
        // Could show in UI: "Searching documents...", etc.
      });

      eventSource.addEventListener('chunk', (e) => {
        const data = JSON.parse(e.data);
        accumulatedContent += data.content;
        setCurrentStream(accumulatedContent);

        // Update last message with accumulated content
        setMessages(prev => {
          const newMessages = [...prev];
          newMessages[newMessages.length - 1] = {
            role: 'assistant',
            content: accumulatedContent,
            isStreaming: true
          };
          return newMessages;
        });
      });

      eventSource.addEventListener('done', (e) => {
        const data = JSON.parse(e.data);
        sources = data.sources || [];
        metadata = data;

        // Finalize message
        setMessages(prev => {
          const newMessages = [...prev];
          newMessages[newMessages.length - 1] = {
            role: 'assistant',
            content: accumulatedContent,
            isStreaming: false,
            sources: sources,
            metadata: metadata
          };
          return newMessages;
        });

        setIsStreaming(false);
        setCurrentStream('');
        eventSource.close();
      });

      eventSource.addEventListener('error', (e) => {
        console.error('Streaming error:', e);
        setIsStreaming(false);
        eventSource.close();
      });

    } catch (error) {
      console.error('Stream setup error:', error);
      setIsStreaming(false);
    }
  }, [apiUrl]);

  return { messages, isStreaming, sendMessage };
};
```

**File 2: Update Chat Interface** (`frontend/src/components/ChatInterfaceEnhanced.tsx`)

Replace current `handleSubmit` with streaming hook:

```typescript
import { useStreamingChat } from '../hooks/useStreamingChat';

export default function ChatInterfaceEnhanced() {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const { messages, isStreaming, sendMessage } = useStreamingChat(API_URL);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const query = input.trim();
    setInput('');

    await sendMessage(query, sessionId, selectedModel);
  };

  return (
    <div className="chat-container">
      {messages.map((msg, idx) => (
        <div key={idx} className={msg.role === 'user' ? 'user-message' : 'assistant-message'}>
          {msg.isStreaming && <span className="typing-indicator">▊</span>}
          <ReactMarkdown>{msg.content}</ReactMarkdown>
        </div>
      ))}
    </div>
  );
}
```

### 📦 Dependencies

```bash
# Backend
pip install sse-starlette==1.8.2

# Frontend
npm install eventsource
```

### ✅ Testing Plan

1. Test OpenAI streaming (gpt-4-turbo)
2. Test Claude streaming (claude-3-sonnet)
3. Test Ollama streaming (qwen2.5-coder:7b)
4. Test error handling (timeout, network failure)
5. Test rapid consecutive queries
6. Test with RAG context (sources display after stream completes)

### 🎨 UI Enhancements

- Add typing indicator (blinking cursor) during stream
- Show status messages ("Searching documents...", "Generating...")
- Display sources after stream completes
- Add "Stop Generation" button

---

## Implementation 2: Interactive Agent Tasks (Claude Code-like)

### 🎯 Goal
Real-time interactive agent execution with conversation display, step-by-step progress, and code execution visibility - similar to Claude Code's terminal experience.

### 📊 Current State

**Agent Task UI**: `/frontend/src/components/AgentTaskMonitor.tsx`
- Polls every 5 seconds for status updates
- Shows final result only after completion
- No real-time conversation visibility
- No step-by-step progress

**Agent Backend**: `/backend/entrypoint_agent.py`
- Agentic loop (THINK → PLAN → ACT → OBSERVE)
- Stores conversation history in memory
- Returns final JSON result only

### 🔧 Required Changes

#### Phase 1: Backend Real-Time Progress

**File 1: Add WebSocket Support** (`backend/app/api/routes/agent_routes.py`)

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio

# Store active WebSocket connections per task
active_connections: Dict[str, Set[WebSocket]] = {}

@router.websocket("/api/v1/agent/tasks/{task_id}/stream")
async def stream_agent_progress(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time agent task progress

    Streams:
        - Conversation messages (THINK, PLAN, ACT, OBSERVE)
        - Tool executions
        - Code being executed
        - Intermediate results
        - Errors and retries
    """
    await websocket.accept()

    # Add connection to active set
    if task_id not in active_connections:
        active_connections[task_id] = set()
    active_connections[task_id].add(websocket)

    try:
        # Send historical messages first
        task = await agent_service.get_task(task_id)
        if task and task.conversation_history:
            for msg in task.conversation_history:
                await websocket.send_json({
                    "type": "history",
                    "message": msg
                })

        # Keep connection alive and stream updates
        while True:
            # Wait for updates from agent execution
            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        active_connections[task_id].remove(websocket)
        if not active_connections[task_id]:
            del active_connections[task_id]


async def broadcast_agent_update(task_id: str, message: dict):
    """
    Broadcast update to all WebSocket clients watching this task
    """
    if task_id in active_connections:
        for connection in active_connections[task_id]:
            try:
                await connection.send_json(message)
            except:
                pass
```

**File 2: Modify Agent Loop to Broadcast** (`backend/entrypoint_agent.py`)

Add broadcasting to the agentic loop:

```python
class AgenticLoop:
    def __init__(self, task_id: str, ...):
        self.task_id = task_id
        # ... existing init

    async def run(self) -> Dict[str, Any]:
        """Main agentic loop with real-time broadcasting"""

        for iteration in range(self.max_iterations):
            # THINK step
            await self._broadcast({
                "type": "thinking",
                "iteration": iteration,
                "message": "Analyzing task and planning next step..."
            })

            # Call LLM
            response = await self._call_llm()

            await self._broadcast({
                "type": "llm_response",
                "iteration": iteration,
                "content": response,
                "model": self.model
            })

            # Check for tool calls
            if has_tool_call:
                await self._broadcast({
                    "type": "tool_selected",
                    "tool_name": tool_name,
                    "arguments": tool_args
                })

                # ACT step
                result = await self._execute_tool(tool_name, tool_args)

                await self._broadcast({
                    "type": "tool_result",
                    "tool_name": tool_name,
                    "success": result.success,
                    "output": result.output
                })

            # Check completion
            if self._is_task_complete():
                await self._broadcast({
                    "type": "completed",
                    "message": "✅ Task completed successfully"
                })
                break

    async def _broadcast(self, message: dict):
        """Send update to WebSocket clients"""
        try:
            # Import broadcast function from routes
            from app.api.routes.agent_routes import broadcast_agent_update
            await broadcast_agent_update(self.task_id, message)
        except:
            pass  # Fail gracefully if broadcasting unavailable
```

#### Phase 2: Frontend Interactive UI

**File 1: Create Interactive Agent View** (`frontend/src/components/AgentTaskInteractive.tsx` - NEW)

```typescript
import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Code, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

interface ConversationMessage {
  type: 'thinking' | 'llm_response' | 'tool_selected' | 'tool_result' | 'completed' | 'error';
  iteration?: number;
  content?: string;
  tool_name?: string;
  output?: string;
  success?: boolean;
  message?: string;
}

interface AgentTaskInteractiveProps {
  taskId: string;
}

export const AgentTaskInteractive: React.FC<AgentTaskInteractiveProps> = ({ taskId }) => {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [isRunning, setIsRunning] = useState(true);
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Connect to WebSocket
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const wsUrl = API_URL.replace('http', 'ws');
    const ws = new WebSocket(`${wsUrl}/api/v1/agent/tasks/${taskId}/stream`);

    ws.onopen = () => {
      console.log('✅ Connected to agent task stream');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages(prev => [...prev, data]);

      // Auto-scroll to bottom
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);

      if (data.type === 'completed' || data.type === 'error') {
        setIsRunning(false);
      }
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      setIsRunning(false);
    };

    ws.onclose = () => {
      console.log('🔌 Disconnected from agent task stream');
      setIsRunning(false);
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [taskId]);

  const renderMessage = (msg: ConversationMessage, index: number) => {
    switch (msg.type) {
      case 'thinking':
        return (
          <div key={index} className="flex items-center gap-2 p-3 bg-blue-50 rounded">
            <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
            <span className="text-blue-800">Iteration {msg.iteration}: {msg.message}</span>
          </div>
        );

      case 'llm_response':
        return (
          <div key={index} className="p-3 bg-gray-50 rounded">
            <div className="flex items-center gap-2 mb-2">
              <Terminal className="w-4 h-4 text-gray-600" />
              <span className="text-sm font-semibold text-gray-700">LLM Response</span>
            </div>
            <pre className="whitespace-pre-wrap text-sm text-gray-800">{msg.content}</pre>
          </div>
        );

      case 'tool_selected':
        return (
          <div key={index} className="p-3 bg-purple-50 rounded">
            <div className="flex items-center gap-2">
              <Code className="w-4 h-4 text-purple-600" />
              <span className="text-purple-800">
                🔧 Executing tool: <strong>{msg.tool_name}</strong>
              </span>
            </div>
          </div>
        );

      case 'tool_result':
        return (
          <div key={index} className={`p-3 rounded ${msg.success ? 'bg-green-50' : 'bg-red-50'}`}>
            <div className="flex items-center gap-2 mb-2">
              {msg.success ? (
                <CheckCircle className="w-4 h-4 text-green-600" />
              ) : (
                <AlertCircle className="w-4 h-4 text-red-600" />
              )}
              <span className={`text-sm font-semibold ${msg.success ? 'text-green-700' : 'text-red-700'}`}>
                Tool Result: {msg.tool_name}
              </span>
            </div>
            <pre className="whitespace-pre-wrap text-sm text-gray-800 max-h-64 overflow-y-auto">
              {msg.output}
            </pre>
          </div>
        );

      case 'completed':
        return (
          <div key={index} className="p-3 bg-green-100 rounded">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <span className="text-green-800 font-semibold">{msg.message}</span>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="h-full flex flex-col bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="p-4 border-b flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">
          Agent Task Execution
        </h2>
        {isRunning && (
          <div className="flex items-center gap-2 text-blue-600">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-sm">Running...</span>
          </div>
        )}
      </div>

      {/* Conversation Stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            Waiting for agent to start...
          </div>
        ) : (
          messages.map((msg, idx) => renderMessage(msg, idx))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Status Bar */}
      <div className="p-3 border-t bg-gray-50 text-sm text-gray-600">
        {messages.length} messages • Task ID: {taskId}
      </div>
    </div>
  );
};
```

**File 2: Integrate into AgentTaskMonitor** (`frontend/src/components/AgentTaskMonitor.tsx`)

Add tab view to switch between "List View" and "Interactive View":

```typescript
import { AgentTaskInteractive } from './AgentTaskInteractive';

export const AgentTaskMonitor: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'list' | 'interactive'>('list');
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

  return (
    <div className="h-screen flex flex-col">
      {/* Tab Navigation */}
      <div className="border-b flex gap-4 p-4">
        <button
          className={`px-4 py-2 rounded ${activeTab === 'list' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          onClick={() => setActiveTab('list')}
        >
          Task List
        </button>
        {selectedTaskId && (
          <button
            className={`px-4 py-2 rounded ${activeTab === 'interactive' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
            onClick={() => setActiveTab('interactive')}
          >
            Interactive View
          </button>
        )}
      </div>

      {/* Content */}
      {activeTab === 'list' ? (
        <div className="flex-1 overflow-auto p-4">
          {/* Existing task list UI */}
          {tasks.map(task => (
            <div
              key={task.task_id}
              onClick={() => {
                setSelectedTaskId(task.task_id);
                setActiveTab('interactive');
              }}
              className="cursor-pointer hover:bg-gray-50 p-4 border rounded"
            >
              {task.task_description}
            </div>
          ))}
        </div>
      ) : (
        <div className="flex-1 overflow-hidden">
          {selectedTaskId && <AgentTaskInteractive taskId={selectedTaskId} />}
        </div>
      )}
    </div>
  );
};
```

### 📦 Dependencies

```bash
# Backend
pip install websockets==12.0

# Frontend
# WebSocket API is built into browsers
```

### ✅ Testing Plan

1. Create simple agent task and watch real-time execution
2. Test tool execution visibility
3. Test error handling and retries
4. Test multiple concurrent tasks
5. Test WebSocket reconnection
6. Test with long-running tasks (>5 minutes)

---

## Implementation 3: OpenAI Codex Option in Agent Tasks

### 🎯 Goal
Add OpenAI Codex models (gpt-4, gpt-4-turbo, gpt-3.5-turbo) as selectable options in Agent Task UI with proper configuration.

### 📊 Current State

**Supported Models**: Currently supports:
- ✅ OpenAI GPT-4, GPT-4-Turbo (via OPENAI_API_KEY)
- ✅ Ollama models (qwen2.5-coder:7b, llama3.2-vision:11b)
- ❌ No explicit "Codex" branding or optimization

**Documentation**: `/docs/features/AGENT_TASKS_OPENAI_FALLBACK_COMPLETE.md`
- OpenAI support already implemented
- Model detection based on `gpt-` prefix
- Automatic fallback to Ollama if OpenAI fails

### 🔧 Required Changes

#### Phase 1: Add Codex Models to UI

**File 1: Update Model Selector** (`frontend/src/components/AgentTaskMonitor.tsx`)

```typescript
// Add Codex model options
const CODEX_MODELS = [
  {
    id: 'gpt-4-turbo-preview',
    name: 'GPT-4 Turbo (Codex)',
    description: 'Most capable for code generation and complex reasoning',
    provider: 'OpenAI',
    costPerMillion: 10.00 // $10/1M tokens
  },
  {
    id: 'gpt-4',
    name: 'GPT-4 (Codex)',
    description: 'Reliable and accurate code generation',
    provider: 'OpenAI',
    costPerMillion: 30.00
  },
  {
    id: 'gpt-3.5-turbo',
    name: 'GPT-3.5 Turbo (Fast)',
    description: 'Fast and cost-effective for simpler tasks',
    provider: 'OpenAI',
    costPerMillion: 0.50
  },
  {
    id: 'code-davinci-002',
    name: 'Codex (Legacy)',
    description: 'Original Codex model (deprecated)',
    provider: 'OpenAI',
    costPerMillion: 2.00,
    deprecated: true
  }
];

const OLLAMA_MODELS = [
  {
    id: 'qwen2.5-coder:7b',
    name: 'Qwen 2.5 Coder 7B',
    description: 'Free local model, good for code tasks',
    provider: 'Ollama',
    costPerMillion: 0
  },
  {
    id: 'deepseek-coder:6.7b',
    name: 'DeepSeek Coder 6.7B',
    description: 'Specialized in code generation',
    provider: 'Ollama',
    costPerMillion: 0
  }
];

export const AgentTaskMonitor: React.FC = () => {
  const [selectedModel, setSelectedModel] = useState('gpt-4-turbo-preview');
  const [modelCategory, setModelCategory] = useState<'codex' | 'ollama'>('codex');

  return (
    <div className="space-y-4">
      {/* Model Category Toggle */}
      <div className="flex gap-2">
        <button
          className={`px-4 py-2 rounded ${modelCategory === 'codex' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          onClick={() => {
            setModelCategory('codex');
            setSelectedModel('gpt-4-turbo-preview');
          }}
        >
          🚀 OpenAI Codex (Premium)
        </button>
        <button
          className={`px-4 py-2 rounded ${modelCategory === 'ollama' ? 'bg-green-600 text-white' : 'bg-gray-200'}`}
          onClick={() => {
            setModelCategory('ollama');
            setSelectedModel('qwen2.5-coder:7b');
          }}
        >
          💻 Local Models (Free)
        </button>
      </div>

      {/* Model Dropdown */}
      <select
        value={selectedModel}
        onChange={(e) => setSelectedModel(e.target.value)}
        className="w-full p-2 border rounded"
      >
        {(modelCategory === 'codex' ? CODEX_MODELS : OLLAMA_MODELS).map(model => (
          <option key={model.id} value={model.id} disabled={model.deprecated}>
            {model.name} - {model.description}
            {model.costPerMillion > 0 && ` ($${model.costPerMillion}/1M tokens)`}
            {model.deprecated && ' (DEPRECATED)'}
          </option>
        ))}
      </select>

      {/* Cost Estimation */}
      {modelCategory === 'codex' && (
        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded">
          <p className="text-sm text-yellow-800">
            💰 <strong>Cost Estimate:</strong> This will use OpenAI API credits.
            Estimated cost: ~$0.10 - $0.50 per task depending on complexity.
          </p>
        </div>
      )}
    </div>
  );
};
```

#### Phase 2: Backend Configuration

**File 1: Add Codex-Specific Prompts** (`backend/entrypoint_agent.py`)

Optimize system prompt for Codex models:

```python
def _get_system_prompt(self, model: str) -> str:
    """Get system prompt optimized for specific model"""

    base_prompt = """You are an expert coding assistant with access to various tools..."""

    if model.startswith('gpt-'):
        # Codex-optimized prompt
        return base_prompt + """

        CODEX OPTIMIZATION:
        - Prioritize clean, production-ready code
        - Use modern Python best practices (type hints, docstrings)
        - Prefer well-known libraries (pandas, numpy, matplotlib)
        - Write unit tests when appropriate
        - Include error handling and input validation
        - Use descriptive variable names

        CODE STYLE:
        - Follow PEP 8 style guide
        - Use f-strings for formatting
        - Add type hints to all functions
        - Write docstrings for public functions
        """
    else:
        # Ollama models - simpler prompt
        return base_prompt
```

**File 2: Add Model-Specific Configurations** (`backend/app/core/config.py`)

```python
# OpenAI Codex Configuration
CODEX_MODELS_CONFIG = {
    "gpt-4-turbo-preview": {
        "max_tokens": 4096,
        "temperature": 0.2,  # Lower for more deterministic code
        "top_p": 0.95,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.1
    },
    "gpt-4": {
        "max_tokens": 2048,
        "temperature": 0.3,
        "top_p": 0.95
    },
    "gpt-3.5-turbo": {
        "max_tokens": 2048,
        "temperature": 0.5,
        "top_p": 1.0
    }
}
```

### 📦 Dependencies

No new dependencies needed (OpenAI already installed).

### ✅ Testing Plan

1. Test gpt-4-turbo for complex data analysis task
2. Test gpt-3.5-turbo for simple code generation
3. Verify cost tracking and budget limits
4. Test fallback to Ollama if OPENAI_API_KEY missing
5. Compare code quality between Codex and Ollama models

---

## Implementation 4: Claude Code Option in Agent Tasks

### 🎯 Goal
Integrate Claude Code as an execution option for agent tasks, leveraging its advanced coding capabilities.

### 📊 Current State

**Documentation**: Multiple docs about Claude Code integration:
- `/docs/features/CLAUDE_CODE_HYBRID_IMPLEMENTATION_STATUS.md`
- `/docs/features/CLAUDE_CODE_INTEGRATION_SUMMARY.md`
- `/docs/analysis/CLAUDE_CODE_VS_OUR_IMPLEMENTATION.md`

**Current Agent Architecture**:
- Uses OpenAI or Ollama LLMs
- Custom agentic loop (THINK → PLAN → ACT → OBSERVE)
- 10+ specialized tools
- Docker-in-Docker sandbox execution

**Claude Code Architecture** (from docs):
- CLI tool for developers
- Autonomous code editing
- Multi-tool support (bash, file operations, web search)
- Context-aware reasoning

### 🔧 Required Changes

#### Phase 1: Claude API Integration

**File 1: Add Claude Code Service** (`backend/app/services/claude_code_service.py` - NEW)

```python
import anthropic
import os
import json
from typing import Dict, Any, List

class ClaudeCodeService:
    """
    Service to interact with Claude API for code generation tasks

    Uses Claude's extended thinking and tool use capabilities
    """

    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        self.model = "claude-3-5-sonnet-20241022"  # Latest Claude with extended thinking

    async def execute_agent_task(
        self,
        task_description: str,
        available_tools: List[Dict[str, Any]],
        workspace_path: str,
        max_iterations: int = 20
    ) -> Dict[str, Any]:
        """
        Execute agentic task using Claude's tool use and extended thinking

        Args:
            task_description: Natural language task description
            available_tools: List of tool definitions (Anthropic format)
            workspace_path: Path to workspace directory
            max_iterations: Maximum iterations allowed

        Returns:
            Task result with conversation history and artifacts
        """

        conversation_history = []
        iteration = 0

        # Initial system prompt
        system_prompt = f"""You are an expert coding assistant working in a sandboxed environment.

Workspace: {workspace_path}
Available directories:
- /workspace/input - Input files
- /workspace/output - Output files
- /workspace/artifacts - Generated artifacts (charts, reports)
- /workspace/temp - Temporary files

TASK: {task_description}

You have access to the following tools:
{json.dumps([tool['name'] for tool in available_tools], indent=2)}

Work step-by-step:
1. Analyze the task requirements
2. Plan your approach
3. Use tools to execute your plan
4. Verify results
5. Report completion

Use <thinking> tags to show your reasoning process.
"""

        messages = [
            {"role": "user", "content": task_description}
        ]

        while iteration < max_iterations:
            iteration += 1

            # Call Claude with tool use
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
                tools=available_tools,
                temperature=0.3  # Lower for more deterministic behavior
            )

            # Store response in history
            conversation_history.append({
                "iteration": iteration,
                "role": "assistant",
                "content": response.content,
                "stop_reason": response.stop_reason
            })

            # Check if Claude wants to use a tool
            if response.stop_reason == "tool_use":
                tool_results = []

                for content_block in response.content:
                    if content_block.type == "tool_use":
                        # Execute the tool
                        tool_name = content_block.name
                        tool_input = content_block.input

                        result = await self._execute_tool(
                            tool_name,
                            tool_input,
                            workspace_path
                        )

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": json.dumps(result)
                        })

                # Add tool results to conversation
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

            else:
                # Task completed or max iterations reached
                break

        # Extract final answer
        final_answer = ""
        for content_block in response.content:
            if hasattr(content_block, 'text'):
                final_answer += content_block.text

        return {
            "success": True,
            "result": final_answer,
            "conversation_history": conversation_history,
            "iterations": iteration,
            "model": self.model
        }

    async def _execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        workspace_path: str
    ) -> Dict[str, Any]:
        """Execute a tool and return result"""

        # Map tool name to actual tool implementation
        # This would call our existing tool registry
        from app.agents.tool_registry import get_tool_registry

        tool_registry = get_tool_registry()
        result = await tool_registry.execute_tool(
            tool_name=tool_name,
            tool_input=tool_input,
            workspace_path=workspace_path
        )

        return result
```

**File 2: Update Agent Service** (`backend/app/services/agent_service.py`)

Add Claude Code as an execution option:

```python
class AgentService:
    async def create_task(
        self,
        task_description: str,
        session_id: str,
        model: str,
        execution_mode: str = "default",  # NEW: "default", "claude_code"
        ...
    ):
        """Create agent task with optional Claude Code execution"""

        # Detect if user selected Claude Code mode
        if execution_mode == "claude_code" or model.startswith("claude-3"):
            # Use Claude Code Service instead of local agent
            from app.services.claude_code_service import ClaudeCodeService

            claude_service = ClaudeCodeService()

            # Convert our tool registry to Anthropic tool format
            tools_anthropic_format = self._convert_tools_to_anthropic_format()

            result = await claude_service.execute_agent_task(
                task_description=task_description,
                available_tools=tools_anthropic_format,
                workspace_path=workspace_path,
                max_iterations=max_iterations
            )

            # Store result same as local agent
            task_record.status = "completed"
            task_record.result = result["result"]
            task_record.conversation_history = result["conversation_history"]
            ...
        else:
            # Use existing local agent (Docker execution)
            result = await self.agent_sandbox.execute_task(...)
```

**File 3: Tool Format Converter** (`backend/app/agents/tool_registry.py`)

Add method to convert tools to Anthropic format:

```python
def convert_tools_to_anthropic_format(self) -> List[Dict[str, Any]]:
    """
    Convert our tool definitions to Anthropic Claude tool format

    Returns:
        List of tool definitions compatible with Claude API
    """

    anthropic_tools = []

    for tool_name, tool_def in self.tools.items():
        anthropic_tool = {
            "name": tool_name,
            "description": tool_def.get("description", ""),
            "input_schema": {
                "type": "object",
                "properties": tool_def.get("parameters", {}),
                "required": tool_def.get("required", [])
            }
        }
        anthropic_tools.append(anthropic_tool)

    return anthropic_tools
```

#### Phase 2: Frontend UI Updates

**File 1: Add Claude Code Toggle** (`frontend/src/components/AgentTaskMonitor.tsx`)

```typescript
export const AgentTaskMonitor: React.FC = () => {
  const [executionMode, setExecutionMode] = useState<'default' | 'claude_code'>('default');
  const [selectedModel, setSelectedModel] = useState('qwen2.5-coder:7b');

  return (
    <div className="space-y-4">
      {/* Execution Mode Selection */}
      <div className="p-4 border rounded">
        <h3 className="font-semibold mb-2">Execution Mode</h3>

        <div className="space-y-2">
          <label className="flex items-center gap-2 p-3 border rounded cursor-pointer hover:bg-gray-50">
            <input
              type="radio"
              name="execution_mode"
              value="default"
              checked={executionMode === 'default'}
              onChange={() => {
                setExecutionMode('default');
                setSelectedModel('qwen2.5-coder:7b');
              }}
            />
            <div>
              <div className="font-semibold">🐳 Local Agent (Default)</div>
              <div className="text-sm text-gray-600">
                Runs in Docker sandbox using OpenAI/Ollama models. Full control, customizable.
              </div>
            </div>
          </label>

          <label className="flex items-center gap-2 p-3 border rounded cursor-pointer hover:bg-gray-50">
            <input
              type="radio"
              name="execution_mode"
              value="claude_code"
              checked={executionMode === 'claude_code'}
              onChange={() => {
                setExecutionMode('claude_code');
                setSelectedModel('claude-3-5-sonnet-20241022');
              }}
            />
            <div>
              <div className="font-semibold">🚀 Claude Code (Premium)</div>
              <div className="text-sm text-gray-600">
                Anthropic's Claude 3.5 Sonnet with extended thinking. Best for complex reasoning.
              </div>
            </div>
          </label>
        </div>
      </div>

      {/* Model Selection (conditional) */}
      {executionMode === 'default' ? (
        <ModelSelector
          value={selectedModel}
          onChange={setSelectedModel}
          options={CODEX_MODELS.concat(OLLAMA_MODELS)}
        />
      ) : (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded">
          <p className="text-sm text-blue-800">
            🤖 <strong>Model:</strong> Claude 3.5 Sonnet (claude-3-5-sonnet-20241022)
          </p>
          <p className="text-xs text-blue-600 mt-1">
            Features: Extended thinking, multi-tool use, 200K context window
          </p>
        </div>
      )}

      {/* Cost Warning for Claude Code */}
      {executionMode === 'claude_code' && (
        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded">
          <p className="text-sm text-yellow-800">
            💰 <strong>Cost Warning:</strong> Claude 3.5 Sonnet costs $3/million input tokens,
            $15/million output tokens. Estimated $0.50-$2.00 per complex task.
          </p>
        </div>
      )}
    </div>
  );
};
```

#### Phase 3: Feature Comparison UI

**File 1: Add Comparison Guide** (`frontend/src/components/AgentModeComparison.tsx` - NEW)

```typescript
export const AgentModeComparison: React.FC = () => {
  return (
    <div className="grid grid-cols-2 gap-4 p-4">
      {/* Local Agent Column */}
      <div className="border rounded p-4">
        <h3 className="font-bold text-lg mb-3">🐳 Local Agent</h3>

        <div className="space-y-2 text-sm">
          <div className="flex items-start gap-2">
            <span className="text-green-600">✅</span>
            <span>FREE - Uses Ollama (no API costs)</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-green-600">✅</span>
            <span>Full control over execution</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-green-600">✅</span>
            <span>10+ custom tools (OCR, vision, web scraping)</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-green-600">✅</span>
            <span>Docker sandbox isolation</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-yellow-600">⚠️</span>
            <span>Limited reasoning vs Claude</span>
          </div>
        </div>

        <div className="mt-4 p-2 bg-gray-100 rounded text-xs">
          <strong>Best for:</strong> Data analysis, web scraping, OCR tasks,
          document processing, budget-conscious users
        </div>
      </div>

      {/* Claude Code Column */}
      <div className="border rounded p-4">
        <h3 className="font-bold text-lg mb-3">🚀 Claude Code</h3>

        <div className="space-y-2 text-sm">
          <div className="flex items-start gap-2">
            <span className="text-green-600">✅</span>
            <span>Advanced reasoning (extended thinking)</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-green-600">✅</span>
            <span>200K context window</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-green-600">✅</span>
            <span>Better code quality</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-green-600">✅</span>
            <span>Multi-step planning</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-red-600">❌</span>
            <span>Costs $0.50-$2 per task</span>
          </div>
        </div>

        <div className="mt-4 p-2 bg-blue-100 rounded text-xs">
          <strong>Best for:</strong> Complex reasoning, research tasks,
          multi-file code generation, when quality > cost
        </div>
      </div>
    </div>
  );
};
```

### 📦 Dependencies

```bash
# Backend
pip install anthropic==0.39.0

# Frontend
# No new dependencies
```

### ✅ Testing Plan

1. Test Claude Code with simple Python script generation
2. Test with complex multi-file project
3. Compare output quality vs local agent
4. Test cost tracking and budget enforcement
5. Test tool use (file operations, bash commands)
6. Verify extended thinking output visibility

---

## 🗓️ Implementation Timeline

### Phase 1: Foundation (Week 1)
- [ ] Day 1-2: Streaming Response (Backend SSE + Frontend EventSource)
- [ ] Day 3-4: Interactive Agent Tasks (WebSocket infrastructure)
- [ ] Day 5: Testing and bug fixes

### Phase 2: Model Options (Week 2)
- [ ] Day 1-2: OpenAI Codex integration and UI
- [ ] Day 3-4: Claude Code service and UI
- [ ] Day 5: Comparison UI and documentation

### Phase 3: Polish (Week 3)
- [ ] Day 1: Cost tracking and budget controls
- [ ] Day 2: Performance optimizations
- [ ] Day 3: Error handling and edge cases
- [ ] Day 4: User testing and feedback
- [ ] Day 5: Final deployment

---

## 📊 Success Metrics

### User Experience
- [ ] Average response time < 2s for first chunk (streaming)
- [ ] Real-time task visibility (no polling delays)
- [ ] Clear cost estimates before execution
- [ ] 90%+ user satisfaction with interactivity

### Technical Performance
- [ ] WebSocket stability > 99.9% uptime
- [ ] SSE streaming < 100ms latency per chunk
- [ ] Concurrent task limit: 10+ simultaneous tasks
- [ ] Memory footprint < 500MB per task

### Cost Efficiency
- [ ] 70%+ tasks use free local agent
- [ ] Average cost per task < $0.20 (with Claude Code option)
- [ ] Budget controls prevent overspending
- [ ] Clear cost breakdowns in UI

---

## 🚨 Risks & Mitigation

### Risk 1: Streaming Complexity
**Risk**: SSE/WebSocket can fail in various network conditions
**Mitigation**: Implement automatic reconnection, fallback to polling, clear error messages

### Risk 2: Claude Code API Costs
**Risk**: Users accidentally run expensive tasks
**Mitigation**: Show cost estimates upfront, require confirmation for expensive models, budget limits

### Risk 3: Browser Compatibility
**Risk**: Older browsers may not support EventSource/WebSocket
**Mitigation**: Feature detection, graceful degradation to polling

### Risk 4: Concurrent Connection Limits
**Risk**: Too many WebSocket connections overwhelm server
**Mitigation**: Connection pooling, rate limiting, auto-disconnect inactive connections

---

## 📚 Documentation Updates Needed

1. **User Guide**: How to use streaming chat
2. **User Guide**: How to monitor interactive agent tasks
3. **Developer Guide**: How to add new streaming endpoints
4. **API Reference**: WebSocket/SSE endpoint documentation
5. **Cost Calculator**: Tool to estimate costs for different models

---

## ✅ Definition of Done

- [ ] All 4 features implemented and tested
- [ ] Documentation updated
- [ ] User acceptance testing passed
- [ ] Performance benchmarks met
- [ ] Cost tracking validated
- [ ] Deployed to production
- [ ] User training materials created

---

**End of Implementation Plan**
