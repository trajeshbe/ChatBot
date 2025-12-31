# Streaming Chat Integration Guide

**Date**: 2025-12-13
**Feature**: ChatGPT-like Real-Time Streaming Responses
**Status**: ✅ Backend Complete | 🔨 Frontend Integration Needed

---

## 📋 What's Been Completed

### ✅ Backend (100%)
1. **SSE Dependency**: Added `sse-starlette==1.8.2`
2. **LLM Service Streaming**: Implemented streaming for OpenAI, Claude, and Ollama
3. **SSE Endpoint**: Created `GET /api/v1/chat/stream`

### ✅ Frontend Hook (100%)
1. **useStreamingChat Hook**: Created `frontend/src/hooks/useStreamingChat.ts`
   - EventSource connection management
   - Auto-reconnect with exponential backoff
   - Error handling
   - Cleanup on unmount

---

## 🔧 Integration Steps for ChatInterfaceEnhanced

### Step 1: Import the Hook

Add this import at the top of `ChatInterfaceEnhanced.tsx`:

```typescript
import { useStreamingChat } from '../hooks/useStreamingChat'
```

### Step 2: Initialize the Hook

Add this inside the component function (after existing useState declarations):

```typescript
const ChatInterfaceEnhanced: React.FC<ChatInterfaceEnhancedProps> = ({ ... }) => {
  // ... existing state ...

  // Add streaming hook
  const {
    streamingContent,
    isStreaming,
    error: streamingError,
    startStreaming,
    stopStreaming,
    resetStream
  } = useStreamingChat(API_URL)

  // Add streaming toggle state
  const [enableStreaming, setEnableStreaming] = useState<boolean>(false)

  // ... rest of component ...
}
```

### Step 3: Add Streaming Toggle to UI

Find the settings section (around line 600-700) and add a toggle switch:

```typescript
{/* Add this near Model Selector */}
<div className="flex items-center justify-between mb-4 px-4 py-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
  <div className="flex items-center gap-2">
    <Zap className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
      Enable Streaming (ChatGPT-like)
    </span>
  </div>
  <label className="relative inline-flex items-center cursor-pointer">
    <input
      type="checkbox"
      checked={enableStreaming}
      onChange={(e) => setEnableStreaming(e.target.checked)}
      className="sr-only peer"
    />
    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 dark:peer-focus:ring-indigo-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-indigo-600"></div>
  </label>
</div>
```

Don't forget to import Zap icon at the top:
```typescript
import { Send, Loader2, FileText, ExternalLink, Paperclip, X, Trash2, ChevronDown, ChevronUp, ArrowLeft, Download, Zap } from 'lucide-react'
```

### Step 4: Modify Message Submission Logic

Find the function that handles message submission (around line 1100-1200) and add streaming logic:

```typescript
// Find the existing submission handler and wrap it like this:

const handleSubmit = async () => {
  if (!inputValue.trim() || (isLoading && !enableStreaming) || (isStreaming && enableStreaming)) {
    return
  }

  // Add user message
  const userMessage: Message = {
    role: 'user',
    content: inputValue,
    timestamp: new Date(),
  }

  setMessages(prev => [...prev, userMessage])
  setInputValue('')

  // STREAMING MODE
  if (enableStreaming) {
    setIsLoading(true)  // Show loading indicator

    try {
      // Start streaming
      startStreaming(inputValue, {
        modelId: selectedModel,
        sessionId: currentSessionId || undefined,
        maxTokens: 1024,
        temperature: 0.7
      })

      // Wait for streaming to complete (poll streamingContent)
      // Note: This is handled by the hook's event listeners
      // We'll add the message when streaming completes

    } catch (error: any) {
      console.error('Streaming error:', error)
      setErrorMessage(error.message || 'Failed to start streaming')
    }
  }
  // NON-STREAMING MODE (existing logic)
  else {
    setIsLoading(true)

    try {
      // Your existing axios.post logic here
      const formData = new FormData()
      formData.append('query', inputValue)
      // ... rest of existing code ...

      const response = await axios.post(`${API_URL}/api/v1/query`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources,
        // ... rest of existing fields ...
      }

      setMessages(prev => [...prev, assistantMessage])
      setIsLoading(false)

    } catch (error: any) {
      console.error('Query error:', error)
      setIsLoading(false)
    }
  }
}
```

### Step 5: Add Real-Time Streaming Display

Add an effect to handle streaming content updates:

```typescript
// Add this useEffect to display streaming content in real-time
useEffect(() => {
  if (isStreaming && streamingContent) {
    // Update or create assistant message with streaming content
    setMessages(prev => {
      const lastMessage = prev[prev.length - 1]

      // If last message is from assistant and is being streamed, update it
      if (lastMessage?.role === 'assistant' && lastMessage?.isStreaming) {
        return [
          ...prev.slice(0, -1),
          {
            ...lastMessage,
            content: streamingContent
          }
        ]
      }
      // Otherwise, create new streaming message
      else {
        return [
          ...prev,
          {
            role: 'assistant' as const,
            content: streamingContent,
            timestamp: new Date(),
            isStreaming: true  // Flag to indicate this is a streaming message
          }
        ]
      }
    })
  }
}, [streamingContent, isStreaming])

// Add this useEffect to finalize the message when streaming completes
useEffect(() => {
  if (!isStreaming && streamingContent && !streamingError) {
    // Mark the last message as complete
    setMessages(prev => {
      const lastMessage = prev[prev.length - 1]
      if (lastMessage?.isStreaming) {
        return [
          ...prev.slice(0, -1),
          {
            ...lastMessage,
            isStreaming: false,
            model: selectedModel  // Add final metadata
          }
        ]
      }
      return prev
    })

    // Reset streaming state
    resetStream()
    setIsLoading(false)
  }
}, [isStreaming, streamingContent, streamingError, selectedModel, resetStream])

// Add this useEffect to handle streaming errors
useEffect(() => {
  if (streamingError) {
    setErrorMessage(`Streaming error: ${streamingError}`)
    setIsLoading(false)
    resetStream()
  }
}, [streamingError, resetStream])
```

### Step 6: Update Message Interface

Add the `isStreaming` flag to the Message interface:

```typescript
interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  timestamp: Date
  model?: string
  model_name?: string
  contextInfo?: string
  isStreaming?: boolean  // 🆕 Add this field
  // ... rest of existing fields ...
}
```

### Step 7: Add Streaming Indicator to Message Display

In the message rendering section, add a typing indicator for streaming messages:

```typescript
{/* Find the assistant message rendering and add this: */}
{message.role === 'assistant' && (
  <div className={`flex ${message.role === 'assistant' ? 'justify-start' : 'justify-end'} mb-4`}>
    <div className={`max-w-3xl px-4 py-3 rounded-lg ${
      message.role === 'assistant' ? 'bg-white dark:bg-gray-800' : 'bg-indigo-600 text-white'
    }`}>
      <ReactMarkdown>{message.content}</ReactMarkdown>

      {/* 🆕 Add streaming indicator */}
      {message.isStreaming && (
        <div className="flex items-center gap-1 mt-2 text-gray-500 dark:text-gray-400">
          <Loader2 className="w-3 h-3 animate-spin" />
          <span className="text-xs">Streaming...</span>
        </div>
      )}

      {/* Existing sources, metadata, etc. */}
    </div>
  </div>
)}
```

### Step 8: Add Stop Streaming Button

Add a button to stop mid-stream:

```typescript
{/* Add this near the Send button when streaming is active */}
{isStreaming && (
  <button
    onClick={stopStreaming}
    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2"
  >
    <X className="w-4 h-4" />
    Stop Streaming
  </button>
)}
```

---

## 🎨 Complete UI Layout Example

Here's how the updated chat interface should look:

```
┌────────────────────────────────────────────────────────────┐
│  Chat Interface                                    [Settings│
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Model: GPT-4 Turbo ▼                                      │
│  ☑ Enable Streaming (ChatGPT-like)                        │
│                                                             │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  User: What is machine learning?                           │
│                                                             │
│  Assistant: (streaming...)                                 │
│  Machine learning is a subset of artificial intelligence▊  │
│  🔄 Streaming...                                           │
│                                                             │
├────────────────────────────────────────────────────────────┤
│  [Your message...]                        [Stop] [Send] 📤 │
└────────────────────────────────────────────────────────────┘
```

---

## 🧪 Testing Checklist

After integration, test the following:

### Basic Functionality
- [ ] Streaming toggle can be enabled/disabled
- [ ] With streaming ON: Response appears character-by-character
- [ ] With streaming OFF: Response appears all at once (existing behavior)
- [ ] Model selector works with streaming
- [ ] Session ID is passed correctly

### Error Scenarios
- [ ] Network error during streaming shows error message
- [ ] Invalid model shows error
- [ ] Stop button works correctly
- [ ] Reconnection works after temporary disconnection

### UI/UX
- [ ] Streaming indicator appears during streaming
- [ ] Stop button is visible when streaming
- [ ] Loading state is correct
- [ ] Messages scroll automatically
- [ ] Dark mode works correctly

---

## 🐛 Common Issues & Solutions

### Issue 1: EventSource Not Connecting
**Symptom**: Console shows "EventSource failed to connect"

**Solution**:
- Check backend is running: `curl http://localhost:8000/health`
- Verify CORS is enabled (already configured in backend)
- Check browser console for CORS errors

### Issue 2: Streaming Content Not Appearing
**Symptom**: isStreaming is true but streamingContent is empty

**Debug**:
```typescript
// Add this in useEffect to debug:
useEffect(() => {
  console.log('Streaming state:', { isStreaming, streamingContent, error: streamingError })
}, [isStreaming, streamingContent, streamingError])
```

**Common Causes**:
- Backend not sending `event: message` correctly
- Frontend not parsing JSON correctly
- Model not available on backend

### Issue 3: Memory Leak Warning
**Symptom**: "Can't perform a React state update on an unmounted component"

**Solution**: Ensure `useStreamingChat` hook properly cleans up in useEffect:
```typescript
useEffect(() => {
  return () => {
    stopStreaming()  // This is already in the hook
  }
}, [stopStreaming])
```

---

## 📊 Performance Considerations

### EventSource Connection Limits
- Browsers limit EventSource connections per domain (typically 6)
- One connection per chat session is fine
- Connections are auto-closed on completion

### Memory Management
- `streamingContent` is reset after each message
- EventSource is properly closed to prevent leaks
- Reconnection has max attempts (3) to prevent infinite loops

---

## 🚀 Deployment

### Backend
```bash
# Install SSE dependency
cd backend
pip install sse-starlette==1.8.2

# Rebuild Docker container
docker-compose build backend
docker-compose up -d backend
```

### Frontend
```bash
# No new dependencies needed (EventSource is built-in)
# Rebuild if using Docker
docker-compose build frontend
docker-compose up -d frontend
```

---

## 📚 API Reference

### Backend SSE Endpoint

**URL**: `GET /api/v1/chat/stream`

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | User question |
| model_id | string | No | Model to use |
| session_id | string | No | Session for history |
| max_tokens | integer | No | Max response length (default: 512) |
| temperature | float | No | Sampling temp (default: 0.7) |

**Response Events**:
- `event: message` → Content chunks
- `event: done` → Streaming complete
- `event: error` → Error occurred

**Example**:
```bash
curl -N http://localhost:8000/api/v1/chat/stream?query="Hello"
```

### Frontend Hook API

```typescript
const {
  streamingContent,   // Current streamed content
  isStreaming,        // Is currently streaming
  error,              // Error message if any
  startStreaming,     // Start streaming function
  stopStreaming,      // Stop streaming function
  resetStream         // Reset state function
} = useStreamingChat(apiUrl)

// Start streaming
startStreaming('Your question here', {
  modelId: 'gpt-4',
  sessionId: 'session-123',
  maxTokens: 1024,
  temperature: 0.7
})
```

---

## ✅ Integration Completion Checklist

- [x] Backend SSE endpoint created
- [x] LLM service streaming methods added
- [x] useStreamingChat hook created
- [ ] Import hook in ChatInterfaceEnhanced
- [ ] Add streaming toggle to UI
- [ ] Add streaming mode to message submission
- [ ] Add streaming content display logic
- [ ] Add streaming indicator to messages
- [ ] Add stop streaming button
- [ ] Test with all models (OpenAI, Claude, Ollama)
- [ ] Test error scenarios
- [ ] Test reconnection logic
- [ ] Deploy to production

---

**Status**: ✅ **Ready for Integration**

Follow the steps above to complete the streaming chat feature!
