# Next Implementations - Quick Reference

**Date**: 2025-12-13
**Full Plan**: See `NEXT_IMPLEMENTATIONS_PLAN.md`

---

## 🎯 Four Features Overview

| # | Feature | Goal | Key Tech | Effort | Priority |
|---|---------|------|----------|--------|----------|
| 1 | **Streaming Chat** | Real-time LLM response like ChatGPT | SSE, EventSource | 2-3 days | P0 |
| 2 | **Interactive Agent** | Live agent execution view | WebSocket | 2-3 days | P0 |
| 3 | **OpenAI Codex** | Add GPT-4 Turbo as option | Model selector | 1-2 days | P1 |
| 4 | **Claude Code** | Add Claude 3.5 Sonnet | Anthropic API | 2-3 days | P1 |

---

## 1️⃣ Streaming Response (ChatGPT-like)

### What It Does
Shows LLM response character-by-character in real-time instead of waiting for complete response.

### Key Files to Create
```
backend/app/api/routes/chat_routes.py        - SSE endpoint
frontend/src/hooks/useStreamingChat.ts       - React hook
```

### Key Changes
```python
# Backend
@router.post("/api/v1/chat/stream")
async def stream_chat_response():
    async def event_generator():
        async for chunk in llm_service.generate_stream():
            yield {"event": "chunk", "data": chunk}
    return EventSourceResponse(event_generator())
```

```typescript
// Frontend
const eventSource = new EventSource(`${apiUrl}/chat/stream?query=...`);
eventSource.addEventListener('chunk', (e) => {
  setContent(prev => prev + JSON.parse(e.data).content);
});
```

### Dependencies
```bash
pip install sse-starlette==1.8.2
npm install eventsource  # (built into browsers)
```

---

## 2️⃣ Interactive Agent Tasks (Claude Code-like)

### What It Does
Shows real-time agent execution: thinking, tool calls, code execution, results - all streamed live.

### Key Files to Create
```
backend/app/api/routes/agent_routes.py         - Add WebSocket endpoint
frontend/src/components/AgentTaskInteractive.tsx  - Interactive view
```

### Key Changes
```python
# Backend
@router.websocket("/api/v1/agent/tasks/{task_id}/stream")
async def stream_agent_progress(websocket: WebSocket):
    # Broadcast real-time updates
    await websocket.send_json({"type": "thinking", "message": "..."})
    await websocket.send_json({"type": "tool_result", "output": "..."})
```

```typescript
// Frontend
const ws = new WebSocket(`${wsUrl}/tasks/${taskId}/stream`);
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  setMessages(prev => [...prev, data]);  // Real-time updates
};
```

### Dependencies
```bash
pip install websockets==12.0
# Frontend: WebSocket is built into browsers
```

---

## 3️⃣ OpenAI Codex Option

### What It Does
Adds GPT-4 Turbo, GPT-4, GPT-3.5 Turbo as selectable models in Agent Task UI with cost estimates.

### Key Files to Modify
```
frontend/src/components/AgentTaskMonitor.tsx   - Add model selector
backend/entrypoint_agent.py                    - Optimize prompts for Codex
```

### Key Changes
```typescript
// Frontend
const CODEX_MODELS = [
  { id: 'gpt-4-turbo-preview', name: 'GPT-4 Turbo (Codex)', cost: 10.00 },
  { id: 'gpt-4', name: 'GPT-4 (Codex)', cost: 30.00 },
  { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', cost: 0.50 }
];
```

```python
# Backend
def _get_system_prompt(model: str):
    if model.startswith('gpt-'):
        return base_prompt + "CODEX OPTIMIZATION: Use clean, production-ready code..."
```

### Dependencies
None (OpenAI already installed)

---

## 4️⃣ Claude Code Option

### What It Does
Integrates Claude 3.5 Sonnet as execution option for agent tasks with extended thinking.

### Key Files to Create
```
backend/app/services/claude_code_service.py    - Claude API integration
frontend/src/components/AgentModeComparison.tsx  - Comparison UI
```

### Key Changes
```python
# Backend
class ClaudeCodeService:
    async def execute_agent_task(task_description: str, tools: List):
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            tools=tools,
            messages=[{"role": "user", "content": task_description}]
        )
        # Handle tool use and extended thinking
```

```typescript
// Frontend
<select onChange={(e) => setExecutionMode(e.target.value)}>
  <option value="default">🐳 Local Agent (Free)</option>
  <option value="claude_code">🚀 Claude Code (Premium)</option>
</select>
```

### Dependencies
```bash
pip install anthropic==0.39.0
```

---

## 🗓️ Recommended Implementation Order

### Week 1: Foundation (Days 1-5)
```
Day 1-2: Feature 1 - Streaming Chat Response
         - Backend SSE endpoint
         - Frontend EventSource hook
         - Test with all 3 LLM providers

Day 3-4: Feature 2 - Interactive Agent Tasks
         - WebSocket infrastructure
         - Real-time broadcast from agent loop
         - Interactive UI component

Day 5:   Testing & Bug Fixes
         - Integration testing
         - Performance testing
         - Edge case handling
```

### Week 2: Model Options (Days 6-10)
```
Day 6-7: Feature 3 - OpenAI Codex
         - Model selector UI
         - Cost estimation
         - Codex-optimized prompts

Day 8-9: Feature 4 - Claude Code
         - Claude API service
         - Execution mode toggle
         - Tool format converter

Day 10:  Testing & Documentation
         - Compare output quality
         - Cost tracking
         - User guide
```

### Week 3: Polish (Days 11-15)
```
Day 11:  Budget Controls
         - Daily/monthly limits
         - Cost warnings
         - Auto-fallback

Day 12:  Performance Optimization
         - Connection pooling
         - Memory management
         - Caching

Day 13:  Error Handling
         - Reconnection logic
         - Timeout handling
         - Graceful degradation

Day 14:  User Testing
         - Beta user feedback
         - UI/UX improvements
         - Documentation review

Day 15:  Production Deployment
         - Final testing
         - Rollout plan
         - Monitoring setup
```

---

## 🎯 Quick Start Commands

### Test Streaming Chat
```bash
# Start backend with SSE support
docker-compose up -d backend

# Test SSE endpoint
curl -N http://localhost:8000/api/v1/chat/stream?query="Hello"&model=gpt-4-turbo
```

### Test Interactive Agent
```bash
# Start agent runtime
docker-compose up -d agent-runtime

# Test WebSocket connection (use websocat or browser DevTools)
websocat ws://localhost:8000/api/v1/agent/tasks/{task_id}/stream
```

### Test OpenAI Codex
```bash
# Set API key
export OPENAI_API_KEY="sk-..."

# Create task with Codex
curl -X POST http://localhost:8000/api/v1/agent/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Generate a Python script", "model": "gpt-4-turbo-preview"}'
```

### Test Claude Code
```bash
# Set API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Create task with Claude
curl -X POST http://localhost:8000/api/v1/agent/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Analyze this data", "execution_mode": "claude_code"}'
```

---

## 📊 Success Criteria

| Feature | Metric | Target |
|---------|--------|--------|
| Streaming Chat | First chunk latency | < 2s |
| Streaming Chat | Chunk delivery rate | < 100ms/chunk |
| Interactive Agent | WebSocket uptime | > 99.9% |
| Interactive Agent | Update frequency | Real-time (no polling) |
| Codex Option | Model selection UX | 1-click switch |
| Codex Option | Cost estimate accuracy | ±10% |
| Claude Code | Reasoning visibility | Full thinking shown |
| Claude Code | Tool execution success | > 95% |

---

## 🚨 Common Pitfalls

### Streaming Chat
- ❌ **Mistake**: Not handling browser EventSource limitations
- ✅ **Solution**: Implement fallback to polling for old browsers

- ❌ **Mistake**: Memory leaks from unclosed EventSource connections
- ✅ **Solution**: Always close EventSource in useEffect cleanup

### Interactive Agent
- ❌ **Mistake**: Too many WebSocket connections overwhelm server
- ✅ **Solution**: Connection pooling + rate limiting

- ❌ **Mistake**: Not showing historical messages when reconnecting
- ✅ **Solution**: Send conversation history on new WebSocket connection

### Codex Option
- ❌ **Mistake**: No cost warnings before expensive operations
- ✅ **Solution**: Show cost estimate + require confirmation

- ❌ **Mistake**: Generic prompts don't leverage Codex strengths
- ✅ **Solution**: Codex-specific prompts emphasizing code quality

### Claude Code
- ❌ **Mistake**: Not converting tool formats correctly
- ✅ **Solution**: Comprehensive tool format converter with validation

- ❌ **Mistake**: Extended thinking output hidden from user
- ✅ **Solution**: Display <thinking> tags in UI

---

## 📚 Reference Links

- **Full Implementation Plan**: `NEXT_IMPLEMENTATIONS_PLAN.md`
- **Current Agent Docs**: `AGENT_TASKS_COMPREHENSIVE_GUIDE.md`
- **Claude Code Status**: `CLAUDE_CODE_HYBRID_IMPLEMENTATION_STATUS.md`
- **OpenAI Fallback**: `AGENT_TASKS_OPENAI_FALLBACK_COMPLETE.md`

---

**Ready to implement? Start with Feature 1 (Streaming Chat) for immediate UX impact!**
