# UI Config - Backend Logs Reference Guide

**Date**: 2025-12-06
**Purpose**: Show exactly what backend logs look like when using different UI configurations

---

## 📋 How to Monitor Logs in Real-Time

### Method 1: Follow All Logs
```bash
docker logs rag-backend --follow --tail=50
```

### Method 2: Filter for Config-Related Logs
```bash
docker logs rag-backend --follow --tail=100 2>&1 | grep -E "(Processing query|strategy_weights|unified_config|rag_long_term|Routing|ROUTING|📌|🎯)"
```

### Method 3: Watch in Separate Terminal
```bash
# Terminal 1: Monitor logs
docker logs rag-backend --follow

# Terminal 2: Use the UI
# Open http://localhost:3001
```

---

## 🎯 Example 1: Long-Term RAG with Brain View

### UI Configuration:
```
Advanced Settings:
- Long-term RAG: 0.9
- Enable Brain View: ON
- Top K: 10
```

### What You'll See in Backend Logs:

```
INFO:     POST /api/v1/query
2025-12-06 10:15:23 - INFO - 📌 Processing query: "Who is Aadhan?"
2025-12-06 10:15:23 - INFO - Session ID: user_session_123
2025-12-06 10:15:23 - INFO - Model: gpt-4o-mini

2025-12-06 10:15:23 - INFO - 📦 Unified config received with strategy_weights:
{
  "strategy_weights": {
    "rag_long_term": 0.9,
    "rag_short_term": 0.3,
    "rag_hybrid": 0.4,
    "direct_llm": 0.2,
    "conversation_only": 0.1,
    "enable_brain_view": true
  },
  "retrieval_params": {
    "top_k": 10,
    "similarity_threshold": 0.7
  }
}

2025-12-06 10:15:23 - INFO - 🎯 Query classification result:
{
  "strategy": "rag_long_term",
  "confidence": 0.92,
  "reason": "Question requires document retrieval from knowledge base"
}

2025-12-06 10:15:23 - INFO - 📌 ROUTING DECISION: rag_long_term weight (0.90) > threshold
2025-12-06 10:15:23 - INFO - Using RAG retrieval for long-term memory

2025-12-06 10:15:24 - INFO - 🔍 Generating embedding for query... (384 dimensions)
2025-12-06 10:15:24 - INFO - ✅ Embedding generated in 120ms

2025-12-06 10:15:24 - INFO - 🔎 Searching database for similar chunks...
2025-12-06 10:15:24 - INFO - Database status: Searching all documents (long-term memory)
2025-12-06 10:15:24 - INFO - Query: Vector similarity search with threshold 0.70

2025-12-06 10:15:24 - INFO - 📄 Found 8 chunks above threshold:
  - aadhan_story.txt (similarity: 0.92)
  - kingdom_history.pdf (similarity: 0.88)
  - characters.md (similarity: 0.85)
  ... (5 more)

2025-12-06 10:15:24 - INFO - 🎯 Using top 10 chunks for context assembly

2025-12-06 10:15:24 - INFO - 🤖 Calling LLM (gpt-4o-mini) with context...
2025-12-06 10:15:24 - INFO - Context tokens: 3,245
2025-12-06 10:15:24 - INFO - Max response tokens: 2,000

2025-12-06 10:15:27 - INFO - ✅ LLM response received (2,890ms)
2025-12-06 10:15:27 - INFO - Tokens used: Input: 3,245 | Output: 487 | Total: 3,732

2025-12-06 10:15:27 - INFO - 🧠 Brain View enabled - generating debug_context
2025-12-06 10:15:27 - INFO - Debug context includes:
  - routing_decision
  - conversation_history
  - tools_executed
  - documents_retrieved
  - performance_metrics

2025-12-06 10:15:27 - INFO - ✅ Query completed successfully
2025-12-06 10:15:27 - INFO - Total latency: 3,956ms
2025-12-06 10:15:27 - INFO - Response sent with 8 source documents
```

---

## 🎯 Example 2: Direct LLM (No Documents)

### UI Configuration:
```
Advanced Settings:
- Direct LLM: 0.85
- All RAG weights: < 0.3
```

### What You'll See in Backend Logs:

```
INFO:     POST /api/v1/query
2025-12-06 10:20:15 - INFO - 📌 Processing query: "What is Python?"
2025-12-06 10:20:15 - INFO - Session ID: user_session_123
2025-12-06 10:20:15 - INFO - Model: gpt-4o-mini

2025-12-06 10:20:15 - INFO - 📦 Unified config received with strategy_weights:
{
  "strategy_weights": {
    "rag_long_term": 0.2,
    "direct_llm": 0.85,
    "enable_brain_view": false
  }
}

2025-12-06 10:20:15 - INFO - 🎯 Query classification result:
{
  "strategy": "direct_llm",
  "confidence": 0.95,
  "reason": "General knowledge question, no document retrieval needed"
}

2025-12-06 10:20:15 - INFO - 📌 ROUTING: direct_llm weight (0.85) > threshold
2025-12-06 10:20:15 - INFO - Using DIRECT LLM path - no document retrieval

2025-12-06 10:20:15 - INFO - ⚡ FAST PATH: Skipping embedding and retrieval
2025-12-06 10:20:15 - INFO - 🤖 Calling LLM directly (gpt-4o-mini)

2025-12-06 10:20:17 - INFO - ✅ LLM response received (1,845ms)
2025-12-06 10:20:17 - INFO - Tokens used: Input: 156 | Output: 342 | Total: 498

2025-12-06 10:20:17 - INFO - ✅ Query completed successfully
2025-12-06 10:20:17 - INFO - Total latency: 1,890ms
2025-12-06 10:20:17 - INFO - Response sent (no sources)
```

---

## 🎯 Example 3: Conversation Mode

### UI Configuration:
```
Advanced Settings:
- Conversation Only: 0.9
- Max History: 15 messages
```

### What You'll See in Backend Logs:

```
INFO:     POST /api/v1/query
2025-12-06 10:25:30 - INFO - 📌 Processing query: "Tell me more about that"
2025-12-06 10:25:30 - INFO - Session ID: user_session_123
2025-12-06 10:25:30 - INFO - Model: gpt-4o-mini

2025-12-06 10:25:30 - INFO - 📦 Unified config received with strategy_weights:
{
  "strategy_weights": {
    "conversation_only": 0.9,
    "rag_long_term": 0.2
  },
  "context_limits": {
    "max_conversation_history": 15
  }
}

2025-12-06 10:25:30 - INFO - 🎯 Query classification result:
{
  "strategy": "conversation_only",
  "confidence": 0.88,
  "reason": "Follow-up question requiring conversation context"
}

2025-12-06 10:25:30 - INFO - 📌 ROUTING: conversation_only weight (0.90) > threshold
2025-12-06 10:25:30 - INFO - Using CONVERSATION ONLY path

2025-12-06 10:25:30 - INFO - 💬 Loading conversation history...
2025-12-06 10:25:30 - INFO - Found 8 previous messages in session
2025-12-06 10:25:30 - INFO - Using last 8 messages (max: 15)

2025-12-06 10:25:30 - INFO - 💬 Conversation context assembled:
  - Messages: 8
  - Total tokens: 1,234
  - Oldest message: "Who is Aadhan?" (2 minutes ago)
  - Latest message: "What kingdom does he rule?" (30 seconds ago)

2025-12-06 10:25:30 - INFO - 🤖 Calling LLM with conversation context (gpt-4o-mini)

2025-12-06 10:25:32 - INFO - ✅ LLM response received (2,145ms)
2025-12-06 10:25:32 - INFO - Tokens used: Input: 1,456 | Output: 298 | Total: 1,754

2025-12-06 10:25:32 - INFO - ✅ Query completed successfully
2025-12-06 10:25:32 - INFO - Total latency: 2,234ms
2025-12-06 10:25:32 - INFO - Response sent (based on conversation history)
```

---

## 🎯 Example 4: Hybrid RAG (Session + All Docs)

### UI Configuration:
```
Advanced Settings:
- Hybrid RAG: 0.8
- Top K: 15
- Similarity Threshold: 0.65
```

### What You'll See in Backend Logs:

```
INFO:     POST /api/v1/query
2025-12-06 10:30:45 - INFO - 📌 Processing query: "Compare the architecture diagrams"
2025-12-06 10:30:45 - INFO - Session ID: user_session_123
2025-12-06 10:30:45 - INFO - Model: gpt-4o-mini

2025-12-06 10:30:45 - INFO - 📦 Unified config received with strategy_weights:
{
  "strategy_weights": {
    "rag_hybrid": 0.8,
    "rag_short_term": 0.3,
    "rag_long_term": 0.5
  },
  "retrieval_params": {
    "top_k": 15,
    "similarity_threshold": 0.65
  }
}

2025-12-06 10:30:45 - INFO - 🎯 Query classification result:
{
  "strategy": "rag_hybrid",
  "confidence": 0.85,
  "reason": "Document comparison requires hybrid search"
}

2025-12-06 10:30:45 - INFO - 📌 ROUTING: rag_hybrid weight (0.80) > threshold
2025-12-06 10:30:45 - INFO - Using HYBRID RAG path

2025-12-06 10:30:45 - INFO - 🔍 Phase 1: Searching session documents (short-term)...
2025-12-06 10:30:45 - INFO - Database status: Searching session-specific documents
2025-12-06 10:30:45 - INFO - Found 3 documents in session

2025-12-06 10:30:46 - INFO - 📄 Session results: 5 chunks found
  - architecture_v2.pdf (session) - 0.89
  - latest_design.pdf (session) - 0.82
  - notes.txt (session) - 0.76

2025-12-06 10:30:46 - INFO - 🔍 Phase 2: Searching all documents (long-term)...
2025-12-06 10:30:46 - INFO - Database status: Searching all documents
2025-12-06 10:30:46 - INFO - Total documents in database: 247

2025-12-06 10:30:47 - INFO - 📄 Long-term results: 12 chunks found
  - old_architecture.pdf (global) - 0.91
  - system_design.docx (global) - 0.87
  - reference_docs.pdf (global) - 0.83
  ... (9 more)

2025-12-06 10:30:47 - INFO - 🔗 Merging and ranking results...
2025-12-06 10:30:47 - INFO - Combined: 17 total chunks
2025-12-06 10:30:47 - INFO - After deduplication: 15 unique chunks
2025-12-06 10:30:47 - INFO - Applying top_k limit: 15

2025-12-06 10:30:47 - INFO - 🎯 Final context: 15 chunks (3 session + 12 global)

2025-12-06 10:30:47 - INFO - 🤖 Calling LLM (gpt-4o-mini) with hybrid context...
2025-12-06 10:30:47 - INFO - Context tokens: 5,678

2025-12-06 10:30:50 - INFO - ✅ LLM response received (3,245ms)
2025-12-06 10:30:50 - INFO - Tokens used: Input: 5,678 | Output: 612 | Total: 6,290

2025-12-06 10:30:50 - INFO - ✅ Query completed successfully
2025-12-06 10:30:50 - INFO - Total latency: 5,123ms
2025-12-06 10:30:50 - INFO - Response sent with 15 source documents
```

---

## 🎯 Example 5: With Reranking Enabled

### UI Configuration:
```
Advanced Settings:
- Long-term RAG: 0.9
- Enable Reranker: ON
- Reranker Top N: 5
- Top K: 20
```

### What You'll See in Backend Logs:

```
INFO:     POST /api/v1/query
2025-12-06 10:35:12 - INFO - 📌 Processing query: "Detailed analysis of project requirements"
2025-12-06 10:35:12 - INFO - Session ID: user_session_123
2025-12-06 10:35:12 - INFO - Model: gpt-4o-mini

2025-12-06 10:35:12 - INFO - 📦 Unified config received with strategy_weights:
{
  "strategy_weights": {
    "rag_long_term": 0.9
  },
  "retrieval_params": {
    "top_k": 20,
    "enable_reranker": true,
    "reranker_top_n": 5
  }
}

2025-12-06 10:35:12 - INFO - 📌 ROUTING: rag_long_term weight (0.90) > threshold
2025-12-06 10:35:12 - INFO - Using RAG retrieval for long-term memory

2025-12-06 10:35:13 - INFO - 🔎 Searching database...
2025-12-06 10:35:13 - INFO - 📄 Found 20 chunks (top_k: 20)

2025-12-06 10:35:13 - INFO - 🔄 RERANKING ENABLED - Using cross-encoder
2025-12-06 10:35:13 - INFO - Reranker model: ms-marco-MiniLM-L-6-v2
2025-12-06 10:35:13 - INFO - Processing 20 chunks for reranking...

2025-12-06 10:35:14 - INFO - ✅ Reranking completed (980ms)
2025-12-06 10:35:14 - INFO - 📊 Reranking results:
  Before reranking (vector similarity):
    1. doc_A.pdf - 0.87
    2. doc_B.txt - 0.85
    3. doc_C.docx - 0.84
    ...

  After reranking (cross-encoder scores):
    1. doc_C.docx - 0.94 (↑ was #3)
    2. doc_F.pdf - 0.92 (↑ was #6)
    3. doc_A.pdf - 0.89 (↓ was #1)
    4. doc_M.txt - 0.87 (↑ was #13)
    5. doc_B.txt - 0.86 (↓ was #2)

2025-12-06 10:35:14 - INFO - 🎯 Using top 5 reranked chunks (reranker_top_n: 5)

2025-12-06 10:35:14 - INFO - 🤖 Calling LLM with reranked context...

2025-12-06 10:35:17 - INFO - ✅ Query completed successfully
2025-12-06 10:35:17 - INFO - Total latency: 4,856ms (includes 980ms reranking)
2025-12-06 10:35:17 - INFO - Response sent with 5 source documents
```

---

## 🎯 Example 6: Semantic Cache Hit

### UI Configuration:
```
Advanced Settings:
- Long-term RAG: 0.9
- Enable Semantic Cache: ON
- Cache Threshold: 0.95
```

### What You'll See in Backend Logs:

**First Query (Cache Miss)**:
```
2025-12-06 10:40:00 - INFO - 📌 Processing query: "Who is Aadhan?"
2025-12-06 10:40:00 - INFO - 🔍 Checking semantic cache...
2025-12-06 10:40:00 - INFO - ❌ Cache MISS - No similar query found (threshold: 0.95)
2025-12-06 10:40:00 - INFO - Proceeding with full RAG pipeline...
2025-12-06 10:40:00 - INFO - [... normal RAG processing ...]
2025-12-06 10:40:04 - INFO - ✅ Query completed - Total latency: 4,123ms
2025-12-06 10:40:04 - INFO - 💾 Caching result for future queries (TTL: 3600s)
```

**Second Similar Query (Cache Hit)**:
```
2025-12-06 10:42:15 - INFO - 📌 Processing query: "Tell me about Aadhan"
2025-12-06 10:42:15 - INFO - 🔍 Checking semantic cache...
2025-12-06 10:42:15 - INFO - 🎯 Calculating similarity with cached queries...

2025-12-06 10:42:15 - INFO - ✅ Cache HIT! Similar query found:
  Cached query: "Who is Aadhan?"
  Similarity: 0.97 (threshold: 0.95)
  Cached: 2 minutes ago
  TTL remaining: 3,480 seconds

2025-12-06 10:42:15 - INFO - ⚡ FAST PATH: Returning cached result
2025-12-06 10:42:15 - INFO - ✅ Query completed - Total latency: 156ms (CACHED)
2025-12-06 10:42:15 - INFO - Performance improvement: 96.2% faster (4123ms → 156ms)
```

---

## 🎯 Example 7: Query Reformulation

### UI Configuration:
```
Advanced Settings:
- Long-term RAG: 0.85
- Enable Query Reformulation: ON
- Strategies: ["expand", "clarify"]
```

### What You'll See in Backend Logs:

```
2025-12-06 10:45:00 - INFO - 📌 Processing query: "How does it work?"
2025-12-06 10:45:00 - INFO - 📌 ROUTING: rag_long_term

2025-12-06 10:45:00 - INFO - 🔄 QUERY REFORMULATION ENABLED
2025-12-06 10:45:00 - INFO - Original query: "How does it work?"
2025-12-06 10:45:00 - INFO - Strategies: expand, clarify

2025-12-06 10:45:00 - INFO - 🤖 Calling LLM for query reformulation...

2025-12-06 10:45:01 - INFO - ✅ Reformulated queries generated:
  1. EXPANDED: "How does the authentication system work in the application?"
  2. CLARIFIED: "What is the step-by-step process of user authentication and authorization?"

2025-12-06 10:45:01 - INFO - 🔍 Executing multi-query search...

2025-12-06 10:45:02 - INFO - Query 1 results: 12 chunks
2025-12-06 10:45:02 - INFO - Query 2 results: 15 chunks
2025-12-06 10:45:02 - INFO - Merging and deduplicating: 18 unique chunks

2025-12-06 10:45:02 - INFO - 🎯 Final context: 18 chunks

2025-12-06 10:45:02 - INFO - 🤖 Calling LLM with enriched context...

2025-12-06 10:45:05 - INFO - ✅ Query completed successfully
2025-12-06 10:45:05 - INFO - Total latency: 5,234ms (includes reformulation)
```

---

## 📊 Log Patterns by Configuration

### High rag_long_term Weight (0.8-1.0)
```
✅ You will see:
- "ROUTING: rag_long_term weight (0.XX) > threshold"
- "Database status: Searching all documents (long-term memory)"
- "Total documents in database: XXX"
- Document retrieval from entire knowledge base
- Multiple source documents in response
```

### High direct_llm Weight (0.8-1.0)
```
✅ You will see:
- "ROUTING: direct_llm weight (0.XX) > threshold"
- "Using DIRECT LLM path - no document retrieval"
- "⚡ FAST PATH: Skipping embedding and retrieval"
- "Calling LLM directly"
- No source documents
- Faster latency (~2s vs ~4s)
```

### High conversation_only Weight (0.8-1.0)
```
✅ You will see:
- "ROUTING: conversation_only weight (0.XX) > threshold"
- "💬 Loading conversation history..."
- "Found X previous messages in session"
- "Using last X messages (max: Y)"
- "Conversation context assembled"
- Conversation-based response
```

### Brain View Enabled
```
✅ You will see:
- "🧠 Brain View enabled - generating debug_context"
- "Debug context includes:"
- Full routing decision details
- Performance breakdown
- Tool execution times
- Document retrieval metrics
```

---

## 🔍 How to Test Each Configuration

### Test 1: Verify Config is Being Sent

1. Open browser DevTools (F12)
2. Go to Network tab
3. Send a query from UI
4. Click on `/api/v1/query` request
5. Check **Payload** tab - you should see:
   ```
   unified_config: {"strategy_weights":{"rag_long_term":0.9,...},...}
   ```

### Test 2: Verify Backend Receives Config

Watch logs while sending query:
```bash
docker logs rag-backend --follow | grep "Unified config received"
```

Should show:
```
📦 Unified config received with strategy_weights: {...}
```

### Test 3: Verify Routing Decision

```bash
docker logs rag-backend --follow | grep -E "(ROUTING|routing_decision)"
```

Should show:
```
📌 ROUTING DECISION: rag_long_term weight (0.90) > threshold
```

---

## 🚨 Troubleshooting Log Patterns

### ❌ Config Not Sent from UI

**What you WON'T see in logs**:
```
# Missing: "📦 Unified config received"
# Instead you see: "Using default config"
```

**Fix**: Clear browser cache, verify localStorage has config

### ❌ Config Sent But Not Used

**What you see**:
```
📦 Unified config received with strategy_weights: {...}
⚠️  Invalid config - using defaults
```

**Fix**: Check config format, ensure values in valid ranges

### ❌ Wrong Routing Decision

**What you see**:
```
📦 Config has rag_long_term: 0.9
📌 ROUTING: direct_llm  # ← Wrong!
```

**Fix**: Check query classification threshold, verify weight values

---

## Quick Reference Command

**Monitor all config-related logs in real-time**:

```bash
docker logs rag-backend --follow --tail=100 2>&1 | \
  grep -E "(Processing query|Unified config|strategy_weights|ROUTING|rag_long_term|direct_llm|conversation_only|Brain View|Cache HIT|Cache MISS|Reranking)" \
  --line-buffered
```

Then use the UI and watch logs update in real-time!

---

**Last Updated**: 2025-12-06
**Status**: Complete Reference Guide
