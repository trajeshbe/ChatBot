# Brain View for Non-RAG Paths - Implementation Plan

**Date**: 2025-12-06
**Status**: 📋 PLANNING
**Requested By**: User asked "can we also brain view for conversation as well?"
**Purpose**: Add debug_context (Brain View) support for CONVERSATION_ONLY and DIRECT_LLM paths

---

## Current Status

### Brain View Support Matrix

| Path | Brain View Supported | Reason |
|------|---------------------|---------|
| **CONVERSATION_ONLY** | ❌ NO | Bypasses RAGService, no debug_context generated |
| **DIRECT_LLM** | ❌ NO | Bypasses RAGService, no debug_context generated |
| **FORCE_RAG** | ✅ YES | Calls RAGService with unified_config |
| **BALANCED/TaskRouter** | ✅ YES | Calls RAGService via TaskRouter |

---

## Problem Statement

Currently, Brain View (debug_context) is only generated in RAGService when document retrieval happens. The CONVERSATION_ONLY and DIRECT_LLM paths skip RAGService entirely and call LLM directly, which means:

1. **No debug_context** is generated
2. **Brain View button** never appears in frontend
3. **Users cannot see** routing decisions, LLM params, or performance metrics for these query types

---

## Proposed Solution

Add `debug_context` generation to `_direct_llm_query()` method (used by both CONVERSATION_ONLY and DIRECT_LLM paths) when `enable_brain_view=true`.

---

## Implementation Details

### Step 1: Extract enable_brain_view Flag

**File**: `backend/app/agents/enhanced_rag_agent.py`
**Method**: `_direct_llm_query()` (Lines 1496-1572)

**Add at line 1520 (after imports)**:

```python
# 🧠 BRAIN VIEW: Extract enable_brain_view flag
enable_brain_view = False
if user_preferences:
    unified_config = user_preferences.get('unified_config', {})
    if unified_config:
        strategy_weights = unified_config.get('strategy_weights', {})
        enable_brain_view = strategy_weights.get('enable_brain_view', False)
        if enable_brain_view:
            logger.info("🧠 Brain View ENABLED for non-RAG path")
```

### Step 2: Collect Debug Information

**Add after LLM call (line 1550)**:

```python
import time

# Track timing
start_time = time.time()

result = await llm_service.generate(
    prompt=query,
    messages=messages,
    model_id=model_id,
    max_tokens=1024,
    temperature=0.7
)

end_time = time.time()
llm_latency_ms = (end_time - start_time) * 1000
```

### Step 3: Build debug_context

**Add before return statement (line 1552)**:

```python
# 🧠 BRAIN VIEW: Build debug_context if enabled
debug_context = None
if enable_brain_view:
    # Determine routing strategy
    routing_strategy = "conversation_only" if conversation_context else "direct_llm"

    debug_context = {
        "routing": {
            "selected_strategy": routing_strategy,
            "strategy_weights": unified_config.get('strategy_weights', {}) if unified_config else {},
            "routing_reason": (
                f"User set conversation_only weight > 0.9 (using {len(conversation_history)} messages)"
                if conversation_context
                else f"User set direct_llm weight > 0.8"
            ),
            "timestamp": time.time()
        },
        "tools_executed": [
            {
                "tool_id": "llm_direct",
                "tool_name": "Direct LLM Query",
                "success": True,
                "execution_time_ms": llm_latency_ms
            }
        ],
        "documents_retrieved": [],  # No documents in non-RAG paths
        "llm_params": {
            "model_id": model_id or "default",
            "max_tokens": 1024,
            "temperature": 0.7,
            "messages_count": len(messages),
            "conversation_messages": len(conversation_history) if conversation_history else 0,
            "has_conversation_context": bool(conversation_context)
        },
        "performance": {
            "total_time_ms": llm_latency_ms,
            "llm_time_ms": llm_latency_ms,
            "retrieval_time_ms": 0,  # No retrieval in non-RAG paths
            "reranking_time_ms": 0
        },
        "query_analysis": {
            "original_query": query,
            "query_length": len(query),
            "uses_rag": False,
            "uses_conversation_history": bool(conversation_context),
            "conversation_context_length": len(conversation_context) if conversation_context else 0
        }
    }

    logger.info(f"🧠 Brain View debug_context generated for {routing_strategy} path")
```

### Step 4: Include debug_context in Response

**Modify return statement (lines 1552-1564)**:

```python
response = {
    "answer": result.get("content", ""),
    "sources": [],
    "num_sources": 0,
    "model": model_id or result.get("model", "default"),
    "metadata": {
        "routing_strategy": "conversation_only" if conversation_context else "direct_llm",
        "routing_reason": (
            "User set conversation_only weight > 0.9"
            if conversation_context
            else "User set direct_llm weight > 0.8"
        ),
        "chunks_retrieved": 0,
        "use_documents": False,
        "latency_ms": llm_latency_ms
    }
}

# 🧠 BRAIN VIEW: Add debug_context if present
if debug_context:
    response["debug_context"] = debug_context

return response
```

---

## Complete Modified Method

Here's the complete `_direct_llm_query()` method with Brain View support:

```python
async def _direct_llm_query(
    self,
    query: str,
    session_id: Optional[str] = None,
    user_preferences: Optional[Dict[str, Any]] = None,
    conversation_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Direct LLM query WITHOUT document retrieval

    Now supports Brain View (debug_context) generation when enabled
    """
    from app.services.llm_service import llm_service
    import time

    try:
        model_id = user_preferences.get('model_id') if user_preferences else None

        # 🧠 BRAIN VIEW: Extract enable_brain_view flag
        enable_brain_view = False
        unified_config = {}
        if user_preferences:
            unified_config = user_preferences.get('unified_config', {})
            if unified_config:
                strategy_weights = unified_config.get('strategy_weights', {})
                enable_brain_view = strategy_weights.get('enable_brain_view', False)
                if enable_brain_view:
                    logger.info("🧠 Brain View ENABLED for non-RAG path")

        # Determine if we're in conversation-only mode
        if conversation_context:
            logger.info(f"💬 CONVERSATION_ONLY: Answering '{query[:100]}...' using conversation history")
            logger.info(f"   Conversation context length: {len(conversation_context)} chars")
        else:
            logger.info(f"🤖 DIRECT_LLM: Answering '{query[:100]}...' using LLM knowledge only")

        # Build messages
        conversation_history = user_preferences.get('conversation_history', []) if user_preferences else []
        messages = conversation_history + [{"role": "user", "content": query}]

        if conversation_context:
            context_message = {
                "role": "system",
                "content": f"Previous conversation context:\n{conversation_context}\n\nUse this conversation history to answer the user's question."
            }
            messages = [context_message] + messages

        # Track timing
        start_time = time.time()

        # Call LLM
        result = await llm_service.generate(
            prompt=query,
            messages=messages,
            model_id=model_id,
            max_tokens=1024,
            temperature=0.7
        )

        end_time = time.time()
        llm_latency_ms = (end_time - start_time) * 1000

        # 🧠 BRAIN VIEW: Build debug_context if enabled
        debug_context = None
        if enable_brain_view:
            routing_strategy = "conversation_only" if conversation_context else "direct_llm"

            debug_context = {
                "routing": {
                    "selected_strategy": routing_strategy,
                    "strategy_weights": unified_config.get('strategy_weights', {}),
                    "routing_reason": (
                        f"User set conversation_only weight > 0.9 (using {len(conversation_history)} messages)"
                        if conversation_context
                        else "User set direct_llm weight > 0.8"
                    ),
                    "timestamp": end_time
                },
                "tools_executed": [
                    {
                        "tool_id": "llm_direct",
                        "tool_name": "Direct LLM Query",
                        "success": True,
                        "execution_time_ms": llm_latency_ms
                    }
                ],
                "documents_retrieved": [],
                "llm_params": {
                    "model_id": model_id or "default",
                    "max_tokens": 1024,
                    "temperature": 0.7,
                    "messages_count": len(messages),
                    "conversation_messages": len(conversation_history),
                    "has_conversation_context": bool(conversation_context)
                },
                "performance": {
                    "total_time_ms": llm_latency_ms,
                    "llm_time_ms": llm_latency_ms,
                    "retrieval_time_ms": 0,
                    "reranking_time_ms": 0
                },
                "query_analysis": {
                    "original_query": query,
                    "query_length": len(query),
                    "uses_rag": False,
                    "uses_conversation_history": bool(conversation_context),
                    "conversation_context_length": len(conversation_context) if conversation_context else 0
                }
            }

            logger.info(f"🧠 Brain View debug_context generated for {routing_strategy} path")

        # Build response
        response = {
            "answer": result.get("content", ""),
            "sources": [],
            "num_sources": 0,
            "model": model_id or result.get("model", "default"),
            "metadata": {
                "routing_strategy": "conversation_only" if conversation_context else "direct_llm",
                "routing_reason": (
                    "User set conversation_only weight > 0.9"
                    if conversation_context
                    else "User set direct_llm weight > 0.8"
                ),
                "chunks_retrieved": 0,
                "use_documents": False,
                "latency_ms": llm_latency_ms
            }
        }

        # 🧠 BRAIN VIEW: Add debug_context if present
        if debug_context:
            response["debug_context"] = debug_context

        return response

    except Exception as e:
        logger.error(f"Direct LLM query failed: {e}")
        return {
            "answer": f"I apologize, but I encountered an error: {str(e)}",
            "sources": [],
            "metadata": {"error": str(e)}
        }
```

---

## Testing Plan

### Test Case 1: CONVERSATION_ONLY with Brain View

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What did I ask before?" \
  -F "session_id=convtest" \
  -F "model=gpt-4o-mini" \
  -F 'unified_config={"strategy_weights":{"conversation_only":0.95,"enable_brain_view":true}}'
```

**Expected Response**:
```json
{
  "answer": "You asked...",
  "sources": [],
  "debug_context": {
    "routing": {
      "selected_strategy": "conversation_only",
      "routing_reason": "User set conversation_only weight > 0.9 (using 3 messages)"
    },
    "tools_executed": [
      {
        "tool_id": "llm_direct",
        "tool_name": "Direct LLM Query",
        "success": true,
        "execution_time_ms": 456.78
      }
    ],
    "documents_retrieved": [],
    "llm_params": {
      "model_id": "gpt-4o-mini",
      "messages_count": 4,
      "conversation_messages": 3,
      "has_conversation_context": true
    },
    "performance": {
      "total_time_ms": 456.78,
      "llm_time_ms": 456.78,
      "retrieval_time_ms": 0
    },
    "query_analysis": {
      "uses_rag": false,
      "uses_conversation_history": true
    }
  }
}
```

### Test Case 2: DIRECT_LLM with Brain View

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What is the capital of France?" \
  -F "session_id=directtest" \
  -F "model=gpt-4o-mini" \
  -F 'unified_config={"strategy_weights":{"direct_llm":0.85,"enable_brain_view":true}}'
```

**Expected Response**:
```json
{
  "answer": "The capital of France is Paris.",
  "sources": [],
  "debug_context": {
    "routing": {
      "selected_strategy": "direct_llm",
      "routing_reason": "User set direct_llm weight > 0.8"
    },
    "tools_executed": [
      {
        "tool_id": "llm_direct",
        "success": true
      }
    ],
    "llm_params": {
      "model_id": "gpt-4o-mini",
      "has_conversation_context": false
    },
    "query_analysis": {
      "uses_rag": false,
      "uses_conversation_history": false
    }
  }
}
```

### Test Case 3: Brain View Disabled

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=hello" \
  -F "model=gpt-4o-mini" \
  -F 'unified_config={"strategy_weights":{"direct_llm":0.85,"enable_brain_view":false}}'
```

**Expected**: NO `debug_context` in response

---

## Frontend Impact

### Brain View Panel - New Tabs for Non-RAG Paths

When `routing.selected_strategy` is `conversation_only` or `direct_llm`, the Brain View panel should adapt:

#### Routing Tab (Always Present)
```typescript
{
  "routing": {
    "selected_strategy": "conversation_only",  // or "direct_llm"
    "routing_reason": "User set conversation_only weight > 0.9"
  }
}
```

#### Tools Tab (Modified)
- Show "Direct LLM Query" instead of "Document RAG"
- Display LLM parameters
- Show conversation messages count if applicable

#### Documents Tab (Modified)
- Display message: "No documents retrieved (non-RAG path)"
- Show "Using conversation history" if conversation_only
- Show "Using LLM knowledge" if direct_llm

#### Performance Tab (Simplified)
- Total time = LLM time only
- No retrieval or reranking time

---

## Benefits

✅ **Consistent debugging experience** across all query paths
✅ **Visibility into conversation-only routing** decisions
✅ **LLM performance metrics** for non-RAG queries
✅ **Frontend doesn't need path-specific handling** - debug_context always present when enabled
✅ **Better user understanding** of why certain queries skip RAG

---

## Risks & Considerations

### Low Risk Implementation
- Only adds debug_context generation, doesn't change query logic
- debug_context is optional, no breaking changes
- Performance impact minimal (only when enable_brain_view=true)

### Potential Issues
1. **Performance**: Additional dict building and logging
   - **Mitigation**: Only happens when enable_brain_view=true

2. **Memory**: debug_context adds ~1-2KB to response
   - **Mitigation**: Negligible compared to answer content

3. **Consistency**: debug_context schema must match RAGService format
   - **Mitigation**: Use same keys/structure as existing Brain View

---

## Implementation Checklist

- [ ] Extract enable_brain_view flag in `_direct_llm_query()`
- [ ] Add timing tracking around LLM call
- [ ] Build debug_context dict with all required fields
- [ ] Include debug_context in response when enabled
- [ ] Test CONVERSATION_ONLY path with Brain View
- [ ] Test DIRECT_LLM path with Brain View
- [ ] Test with Brain View disabled (no debug_context)
- [ ] Verify frontend Brain View panel displays correctly
- [ ] Update documentation
- [ ] Add to COMPLETE_QUERY_ROUTING_FLOW_DOCUMENTATION.md

---

## Related Documentation

- `docs/architecture/COMPLETE_QUERY_ROUTING_FLOW_DOCUMENTATION.md` - All query paths
- `docs/fixes/BRAIN_VIEW_ENHANCED_RAG_AGENT_ROOT_CAUSE.md` - Original Brain View fix
- `docs/fixes/BRAIN_VIEW_RUNTIME_ERROR_FIX.md` - Frontend fixes
- `docs/fixes/BRAIN_VIEW_STATE_PERSISTENCE_FIX.md` - State management

---

## Future Enhancements

1. **Conversation Analysis**: Add debug info about conversation turns analyzed
2. **LLM Reasoning**: Capture chain-of-thought if available
3. **Cost Tracking**: Include token costs for non-RAG LLM calls
4. **Comparative View**: Compare RAG vs non-RAG performance

---

**Status**: 📋 Ready for implementation
**Priority**: MEDIUM - Nice to have for complete debugging experience
**Effort**: 1-2 hours (low complexity)
**Files to Modify**: 1 (`backend/app/agents/enhanced_rag_agent.py`)

---

**Created**: 2025-12-06
**Author**: Based on user request for Brain View in conversation paths
