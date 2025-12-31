# Model Switching in Same Conversation

## Feature Overview

You can **switch between different LLM models mid-conversation** while maintaining full conversation history. Each model will see all previous messages regardless of which model answered them.

This works just like ChatGPT where you can switch between GPT-3.5 and GPT-4 in the same conversation.

## How It Works

### Current Implementation

**Frontend** (`ChatInterfaceEnhanced.tsx:1175-1179`):
```typescript
// Sends last 10 messages with ONLY role and content
const recentMessages = messages.slice(-10).map(msg => ({
  role: msg.role,      // 'user' or 'assistant'
  content: msg.content // The actual message text
  // ⚠️ Does NOT include: model, model_name, sources, etc.
}))
formData.append('conversation_history', JSON.stringify(recentMessages))
```

**Backend** (`enhanced_rag_agent.py:1602-1604`):
```python
# Uses conversation history with current model
conversation_history = user_preferences.get('conversation_history', [])
messages = conversation_history + [{"role": "user", "content": query}]

# Calls CURRENT selected model (not the model from history)
result = await llm_service.generate(
    prompt=query,
    messages=messages,
    model_id=model_id  # Current model
)
```

### Why It Works

✅ **Model-Agnostic History**: Only stores role + content, no model info
✅ **Current Model Selection**: Each query uses currently selected model
✅ **Full Context**: New model sees all previous messages
✅ **Persistent Storage**: Messages saved with model info for reference

## Example Use Case

**Scenario**: Compare responses from different models

```
Step 1: Select GPT-4
User: "What is quantum computing?"
GPT-4: [detailed technical answer]

Step 2: Switch to Claude 3
User: "Can you explain that in simpler terms?"
Claude 3: [sees GPT-4's answer, provides simpler explanation]

Step 3: Switch to Llama 3
User: "What did the first model say about qubits?"
Llama 3: [sees full conversation, references GPT-4's answer]
```

## Testing Model Switching

### Test 1: Basic Model Switch

```
1. Select Model: GPT-4
2. Ask: "Ram is 25 years old"
3. GPT-4 responds

4. Switch to Model: Claude 3
5. Ask: "How old is Ram?"
6. ✅ Claude 3 should answer "25 years old"
```

### Test 2: Multi-Model Context

```
1. Model: GPT-4
   Ask: "Tell me about artificial intelligence"

2. Model: Claude 3
   Ask: "What are the risks mentioned?"

3. Model: Llama 3
   Ask: "Summarize both previous answers"

✅ Each model sees the full conversation history
```

### Test 3: Conversation-Only Mode with Model Switching

```
1. Set conversation_only = 1.0 in Weights Config
2. Model: GPT-4
   Say: "Ram is an engineer"

3. Model: Claude 3
   Say: "Rahul is a scientist"

4. Model: Llama 3
   Ask: "What do Ram and Rahul do?"

✅ Llama 3 should answer using both previous messages
```

## Console Debug Output

When you switch models, you'll see in browser console (F12):

```javascript
// First query with GPT-4
📤 Querying with session session-123... and 2 context messages
🎯 Model selected: gpt-4
💬 Conversation history (last 2 messages):
  ["user: Ram is 25 years old", "assistant: Got it, Ram is 25..."]

// Second query with Claude 3 (different model)
📤 Querying with session session-123... and 4 context messages
🎯 Model selected: claude-3-opus-20240229
💬 Conversation history (last 4 messages):
  ["user: Ram is 25...", "assistant: Got it...", "user: How old is Ram?"]
```

## Backend Logs

Backend logs show conversation history being used:

```
📜 Received conversation history with 4 messages
💬 Using 4 messages from frontend conversation history
📝 Conversation context preview: User: Ram is 25 years old
Assistant: Got it, Ram is 25...
```

## Database Storage

Messages are stored with model information for audit:

```sql
SELECT role, LEFT(content, 50) as content, model_id, model_name
FROM conversation_messages
WHERE session_id = 'xyz'
ORDER BY created_at;

-- Results show mixed models in same conversation:
-- user  | Ram is 25 years old           | NULL | NULL
-- asst  | Got it, Ram is 25...          | gpt-4 | GPT-4 Turbo
-- user  | How old is Ram?               | NULL | NULL
-- asst  | Ram is 25 years old           | claude-3 | Claude 3 Opus
```

## Important Notes

### ✅ What Works

1. **Model switching mid-conversation** - Full context maintained
2. **Conversation-only mode** - Works across models
3. **RAG mode** - Document context + conversation history
4. **Mixed modes** - Some messages with RAG, some with conversation-only

### ⚠️ Limitations

1. **Last 10 messages only** - Currently hardcoded (line 1175)
2. **Model-specific quirks** - Different models may interpret context differently
3. **Token limits** - Larger history may exceed some model context windows
4. **Model availability** - Switching to unavailable model falls back to default

### 🔮 Future Enhancements

1. **Configurable history depth** - Slider to control 1-50 messages
2. **Smart context pruning** - Summarize old messages to fit context window
3. **Model comparison view** - Side-by-side comparison of different model responses
4. **Model recommendations** - Suggest best model for query type

## Architecture

### Message Storage

**localStorage** (per-session):
```javascript
chat_messages_{sessionId} = [
  {
    role: 'user',
    content: 'Ram is 25',
    timestamp: '2025-12-12T...'
  },
  {
    role: 'assistant',
    content: 'Got it!',
    model: 'gpt-4',
    model_name: 'GPT-4 Turbo',
    timestamp: '2025-12-12T...'
  }
]
```

**Database** (persistent):
```sql
CREATE TABLE conversation_messages (
    id UUID,
    session_id UUID REFERENCES chat_sessions(id),
    role VARCHAR(50),
    content TEXT,
    model_id VARCHAR(100),      -- Which model answered
    model_name VARCHAR(255),    -- Display name
    created_at TIMESTAMP
);
```

### Request Flow

```
┌─────────────────────────────────────────────────────┐
│ Frontend                                            │
│                                                     │
│  1. User selects Model B (was Model A)             │
│  2. User types message                             │
│  3. Get last 10 messages from localStorage         │
│  4. Extract only role + content (drop model info)  │
│  5. Send to backend with current Model B           │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Backend                                             │
│                                                     │
│  1. Receive query + conversation_history           │
│  2. Receive selected model_id (Model B)            │
│  3. Build messages array with history              │
│  4. Call LLM Service with Model B                  │
│  5. Model B sees all history (even Model A msgs)   │
│  6. Return response                                │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Storage                                             │
│                                                     │
│  1. Save user message (no model)                   │
│  2. Save assistant response with Model B           │
│  3. Update localStorage with both                  │
│  4. Save to database with model_id = Model B       │
└─────────────────────────────────────────────────────┘
```

## Troubleshooting

### Issue: Model doesn't see previous messages

**Check**:
```javascript
// Browser console (F12)
const sessionId = sessionStorage.getItem('chat_session_id');
const messages = JSON.parse(localStorage.getItem(`chat_messages_${sessionId}`));
console.log('Total messages:', messages.length);
console.log('Last 10:', messages.slice(-10));
```

**Solution**: Ensure messages are being saved to localStorage

### Issue: Context too long for model

**Symptom**: Error "context length exceeded"

**Solution**: Some models have smaller context windows. Either:
1. Start a new chat
2. Use a model with larger context (GPT-4, Claude 3)
3. Wait for configurable history depth feature

### Issue: Model gives inconsistent answers

**Cause**: Different models interpret context differently

**Not a bug**: This is expected behavior. Each model has different:
- Training data
- Reasoning style
- Temperature settings
- Instruction following

## Best Practices

### 1. Start with Strong Context

```
✅ Good:
User: "Ram is 25 years old and works as a software engineer"
[Switch model]
User: "What does Ram do?"

❌ Bad:
User: "Ram"
[Switch model]
User: "What does he do?"  // Too vague
```

### 2. Verify Context is Maintained

After switching models, ask a question that requires previous context:

```
Model A: "The capital of France is Paris"
[Switch to Model B]
Model B: "What capital did we just discuss?"
Expected: "Paris"
```

### 3. Use Appropriate Models

- **GPT-4**: Complex reasoning, longer context
- **Claude 3**: Nuanced understanding, helpful responses
- **Llama 3**: Fast, good for simple queries
- **Qwen**: Vision + text, multilingual

### 4. Monitor Token Usage

Longer conversations use more tokens. With conversation_only=1.0:
- 10 messages ≈ 500-2000 tokens
- Plus current query
- Plus system message

## Configuration

### Change History Depth (Future)

Currently hardcoded to 10 messages. To change:

**Frontend** (`ChatInterfaceEnhanced.tsx:1175`):
```typescript
// Current:
const recentMessages = messages.slice(-10)

// Configurable:
const conversationDepth = parseInt(localStorage.getItem('conversation_depth') || '10')
const recentMessages = messages.slice(-conversationDepth)
```

**Add UI Control** (in RAGSettings or new panel):
```typescript
<input
  type="range"
  min={1}
  max={50}
  value={conversationDepth}
  onChange={(e) => setConversationDepth(parseInt(e.target.value))}
/>
```

## Summary

✅ **Model switching is fully supported**
✅ **Conversation history maintained across models**
✅ **No special configuration needed**
✅ **Works with all modes** (conversation-only, RAG, direct LLM)

Just select a different model and continue your conversation!
