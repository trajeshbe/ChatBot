# Complete Query Routing Flow Documentation

**Date**: 2025-12-06
**Purpose**: Comprehensive documentation of ALL query routing paths in EnhancedRAGAgent
**Status**: ✅ COMPLETE - All 4 paths documented

---

## Overview

Queries in the ChatBot system go through **EnhancedRAGAgent** which implements **4 distinct routing paths** based on user-configured strategy weights. This document traces the complete flow for each path, including Brain View (debug_context) support.

---

## Table of Contents

1. [Entry Point: main.py → EnhancedRAGAgent](#entry-point)
2. [Path 0: CONVERSATION_ONLY (conversation_only weight > 0.9)](#path-0-conversation_only)
3. [Path 1: DIRECT_LLM (direct_llm weight > 0.8)](#path-1-direct_llm)
4. [Path 2: FORCE_RAG (rag weights > 0.8)](#path-2-force_rag)
5. [Path 3: BALANCED/TaskRouter (default)](#path-3-balanced-taskrouter)
6. [Special Cases and Edge Cases](#special-cases)
7. [Brain View Support Matrix](#brain-view-support-matrix)
8. [Code References](#code-references)

---

## Entry Point

### Frontend → main.py

**File**: `backend/app/main.py`

```
Frontend sends query with unified_config:
{
  "query": "hello world",
  "session_id": "test123",
  "model": "gpt-4o-mini",
  "unified_config": {
    "strategy_weights": {
      "conversation_only": 0.50,
      "rag_short_term": 0.48,
      "rag_long_term": 0.40,
      "direct_llm": 0.38,
      "enable_brain_view": true
    }
  }
}
```

**main.py Processing** (Lines 629-749):

1. **Line 629**: Receives `unified_config` as form data
2. **Lines 716-723**: Parses JSON string to dict
   ```python
   unified_config_dict = {}
   if unified_config:
       try:
           unified_config_dict = json.loads(unified_config)
           logger.info(f"✅ Received unified config with strategy_weights: {unified_config_dict.get('strategy_weights', {})}")
       except json.JSONDecodeError as e:
           logger.warning(f"⚠️ Failed to parse unified_config JSON: {e}")
   ```

3. **Lines 738-749**: Builds `user_preferences` dict containing unified_config
   ```python
   user_preferences = {
       'top_k': top_k,
       'similarity_threshold': similarity_threshold,
       'semantic_weight': semantic_weight,
       'keyword_weight': keyword_weight,
       'model_id': model,
       'project_id': project_id,
       'db': db,
       'unified_config': unified_config_dict,  # ✅ Included here
       # ... other params ...
   }
   ```

4. **Line 711**: Routes to EnhancedRAGAgent
   ```python
   from app.agents.enhanced_rag_agent import enhanced_rag_agent
   logger.info(f"🤖 Using EnhancedRAGAgent for query: {query[:100]}...")

   result = await enhanced_rag_agent.run(
       query=query,
       session_id=session_id,
       user_preferences=user_preferences  # Contains unified_config
   )
   ```

---

## Path 0: CONVERSATION_ONLY

### When Activated
- **Condition**: `conversation_only` weight > 0.9
- **Purpose**: Uses ONLY conversation history, NO document RAG
- **Brain View**: ❌ NOT APPLICABLE (no RAG service called)

### Code Location
**File**: `backend/app/agents/enhanced_rag_agent.py`
**Lines**: 159-200

### Flow Diagram

```
EnhancedRAGAgent.run()
  ↓
Line 159: Check conversation_only_weight > 0.9
  ↓ TRUE
Line 165-183: Format conversation history from frontend
  ↓
Line 186-191: Call _direct_llm_query() with conversation_context
  ↓
LLM generates response using ONLY conversation history
  ↓
Line 194-199: Add routing metadata
  ↓
Return response (NO debug_context)
```

### Code

```python
# Line 159-200
if conversation_only_weight > 0.9:
    logger.info("📌 ROUTING: CONVERSATION_ONLY (using conversation history, no document search)")
    logger.info(f"   Reason: conversation_only weight ({conversation_only_weight:.2f}) > 0.9 threshold")

    # Get conversation history from user_preferences
    conversation_history = user_preferences.get('conversation_history', [])

    if not conversation_history:
        logger.warning("⚠️ CONVERSATION_ONLY selected but no conversation_history provided!")
        conversation_history = []

    # Extract session_id for metadata
    metadata = {
        'conversation_only': True,
        'conversation_messages_count': len(conversation_history),
        'session_id': session_id
    }

    # Format conversation context from passed history
    conversation_context = "\n".join([
        f"{msg['role'].capitalize()}: {msg['content']}"
        for msg in conversation_history
    ])

    logger.info(f"💬 Using {len(conversation_history)} messages from frontend conversation history")

    # Use LLM with ONLY conversation history (no document search)
    result = await self._direct_llm_query(
        query=query,
        session_id=session_id,
        user_preferences=user_preferences,
        conversation_context=conversation_context  # 🆕 Pass conversation history
    )

    # Add routing metadata
    result['metadata'] = result.get('metadata', {})
    result['metadata']['routing_strategy'] = 'conversation_only'
    result['metadata']['routing_reason'] = f'User set conversation_only={conversation_only_weight:.2f}'
    result['metadata']['conversation_messages_used'] = len(conversation_history)
    result['metadata']['strategy_weights'] = strategy_weights

    return result
```

### Example Query

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What did I just ask you?" \
  -F "session_id=conv_test" \
  -F "model=gpt-4o-mini" \
  -F 'unified_config={"strategy_weights":{"conversation_only":0.95}}'
```

### Response

```json
{
  "answer": "You asked me...",
  "metadata": {
    "routing_strategy": "conversation_only",
    "routing_reason": "User set conversation_only=0.95",
    "conversation_messages_used": 5
  }
  // NO debug_context (not RAG)
}
```

---

## Path 1: DIRECT_LLM

### When Activated
- **Condition**: `direct_llm` weight > 0.8
- **Purpose**: Skip RAG for general knowledge queries
- **Brain View**: ❌ NOT APPLICABLE (no RAG service called)

### Code Location
**File**: `backend/app/agents/enhanced_rag_agent.py`
**Lines**: 202-220

### Flow Diagram

```
EnhancedRAGAgent.run()
  ↓
Line 203: Check direct_llm_weight > 0.8
  ↓ TRUE
Line 208-212: Call _direct_llm_query()
  ↓
LLM generates response using general knowledge
  ↓
Line 214-218: Add routing metadata
  ↓
Return response (NO debug_context)
```

### Code

```python
# Line 202-220
if direct_llm_weight > 0.8:
    logger.info("📌 ROUTING: DIRECT_LLM (skipping RAG per user's strategy_weights)")
    logger.info(f"   Reason: direct_llm weight ({direct_llm_weight:.2f}) > 0.8 threshold")

    # Use LLM directly without document retrieval
    result = await self._direct_llm_query(
        query=query,
        session_id=session_id,
        user_preferences=user_preferences
    )

    # Add routing metadata
    result['metadata'] = result.get('metadata', {})
    result['metadata']['routing_strategy'] = 'direct_llm'
    result['metadata']['routing_reason'] = f'User set direct_llm={direct_llm_weight:.2f}'
    result['metadata']['strategy_weights'] = strategy_weights

    return result
```

### Example Query

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What is the capital of France?" \
  -F "session_id=directllm_test" \
  -F "model=gpt-4o-mini" \
  -F 'unified_config={"strategy_weights":{"direct_llm":0.85}}'
```

### Response

```json
{
  "answer": "The capital of France is Paris.",
  "metadata": {
    "routing_strategy": "direct_llm",
    "routing_reason": "User set direct_llm=0.85"
  }
  // NO debug_context (not RAG)
}
```

---

## Path 2: FORCE_RAG

### When Activated
- **Condition**: `rag_short_term` > 0.8 OR `rag_long_term` > 0.8
- **Purpose**: Forces document search even for conversational queries
- **Brain View**: ✅ SUPPORTED (unified_config passed to RAGService)

### Code Location
**File**: `backend/app/agents/enhanced_rag_agent.py`
**Lines**: 241-269

### Flow Diagram

```
EnhancedRAGAgent.run()
  ↓
Line 241: Check rag weights > 0.8
  ↓ TRUE
Line 243-254: Build tool_params_rag with unified_config
  ↓
Line 256-260: Call _execute_tool_document_rag(tool_params_rag)
  ↓
_execute_tool_document_rag (Lines 1605-1617)
  ↓
Line 1616: Call rag_service.query(unified_config=tool_params.get('unified_config'))
  ↓
RAGService.query() (rag_service.py Line 65)
  ↓
Lines 155-164: Extract enable_brain_view from unified_config
  ↓
Generate debug_context if enable_brain_view=true
  ↓
Return rag_response with debug_context
  ↓
Return to _execute_tool_document_rag
  ↓
Return to run() (Line 261: result)
  ↓
Call _generate_response(result) (Line 265)
  ↓
_generate_response (Lines 1286-1318)
  ↓
Line 1314-1316: Pass through debug_context ✅
  ↓
Return response with debug_context to API
```

### Code

#### EnhancedRAGAgent.run() (Lines 241-269)

```python
# Line 241-269
elif rag_short_term_weight > 0.8 or rag_long_term_weight > 0.8:
    logger.info("📌 ROUTING: FORCE_RAG (document search required per user's strategy_weights)")

    tool_params_rag = {
        "top_k": top_k,
        "similarity_threshold": similarity_threshold,
        "semantic_weight": semantic_weight,
        "keyword_weight": keyword_weight,
        "model_id": user_preferences.get('model_id') if user_preferences else None,
        "project_id": user_preferences.get('project_id') if user_preferences else None,
        "db": user_preferences.get('db') if user_preferences else None,
        "unified_config": user_preferences.get('unified_config') if user_preferences else None  # ✅ Line 254
    }

    result = await self._execute_tool_document_rag(
        query=query,
        session_id=session_id,
        tool_params=tool_params_rag
    )

    # Line 265: Generate response
    response = await self._generate_response(
        tool_id="document_rag",
        result_data=result,  # Contains debug_context from RAGService
        query=query,
        state={
            "user_preferences": user_preferences,
            "query": query
        }
    )

    return response
```

#### _execute_tool_document_rag() (Lines 1605-1617)

```python
# Line 1605-1617
async def _execute_tool_document_rag(
    self,
    query: str,
    session_id: Optional[str],
    tool_params: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute document RAG tool."""

    rag_response = await rag_service.query(
        query_text=query,
        session_id=session_id,
        top_k=tool_params.get('top_k'),
        similarity_threshold=tool_params.get('similarity_threshold'),
        semantic_weight=tool_params.get('semantic_weight'),
        keyword_weight=tool_params.get('keyword_weight'),
        model_id=tool_params.get('model_id'),
        project_id=tool_params.get('project_id'),
        db=tool_params.get('db'),
        force_rag=True,
        unified_config=tool_params.get('unified_config')  # ✅ Line 1616 - Passes unified_config
    )

    return rag_response  # Contains debug_context if enable_brain_view=true
```

#### _generate_response() (Lines 1286-1318)

```python
# Line 1286-1318
async def _generate_response(
    self,
    tool_id: str,
    result_data: Dict[str, Any],
    query: str,
    state: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate final response from tool result."""

    # Special handling for document_rag - it already has answer from RAG service
    if tool_id == "document_rag":
        sources = result_data.get("sources", [])
        answer = result_data.get("answer", "I don't have any information about that in my documents.")

        response = {
            "answer": answer,
            "sources": sources,
            "metadata": {
                **result_data.get("metadata", {}),
                "synthesis_method": "rag_service"
            }
        }

        # ✅ Pass through quality_metrics if present
        if "quality_metrics" in result_data:
            response["quality_metrics"] = result_data["quality_metrics"]

        # ✅ Pass through model information if present
        if "model" in result_data:
            response["model"] = result_data["model"]
        if "model_name" in result_data:
            response["model_name"] = result_data["model_name"]

        # 🧠 BRAIN VIEW: Pass through debug_context if present (Lines 1314-1316)
        if "debug_context" in result_data:
            response["debug_context"] = result_data["debug_context"]

        return response
```

#### RAGService.query() (Lines 155-164)

```python
# rag_service.py Lines 155-164
# 🧠 BRAIN VIEW: Extract enable_brain_view flag from unified_config
enable_brain_view = False
if unified_config:
    logger.info(f"🧠 DEBUG [RAGService.query]: unified_config received = {unified_config is not None}")
    strategy_weights = unified_config.get('strategy_weights', {})
    enable_brain_view = strategy_weights.get('enable_brain_view', False)
    if enable_brain_view:
        logger.info("🧠 Brain View ENABLED via unified_config")
    else:
        logger.debug("🧠 Brain View disabled (enable_brain_view=False or not in unified_config)")
```

### Example Query

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=Tell me about the documents" \
  -F "session_id=forcerag_test" \
  -F "model=gpt-4o-mini" \
  -F 'unified_config={"strategy_weights":{"rag_short_term":0.85,"enable_brain_view":true}}'
```

### Response

```json
{
  "answer": "Based on the documents...",
  "sources": [...],
  "debug_context": {
    "routing": {
      "selected_strategy": "force_rag",
      "strategy_weights": {...}
    },
    "tools_executed": ["document_rag"],
    "documents_retrieved": [...],
    "performance": {...}
  }
}
```

---

## Path 3: BALANCED/TaskRouter

### When Activated
- **Condition**: DEFAULT path (all weights < 0.8)
- **Purpose**: Intelligent routing using TaskRouter based on query analysis
- **Brain View**: ✅ SUPPORTED (unified_config passed through TaskRouter)

### Code Location
**File**: `backend/app/agents/enhanced_rag_agent.py`
**Lines**: 324-660

### Flow Diagram

```
EnhancedRAGAgent.run()
  ↓
Line 324: Default path (BALANCED)
  ↓
Line 364: Call task_router.route(user_preferences)
  ↓
TaskRouter.route() (task_router.py Lines 583-592)
  ↓
Line 592: tool_params.update(user_preferences) ✅ Includes unified_config
  ↓
Return routing_decision with tool_params
  ↓
Line 419: tool_params = routing_decision.tool_params.copy()
  ↓
Line 491: Call tool (e.g., _execute_tool_document_rag)
  ↓
_execute_tool_document_rag (Lines 1605-1617)
  ↓
Line 1616: Call rag_service.query(unified_config=tool_params.get('unified_config'))
  ↓
RAGService.query() (rag_service.py Line 65)
  ↓
Lines 155-164: Extract enable_brain_view from unified_config
  ↓
Generate debug_context if enable_brain_view=true
  ↓
Return rag_response with debug_context
  ↓
Return to _execute_tool_document_rag
  ↓
Return to run() (Line 534: result)
  ↓
Call _generate_response(result) (Line 651)
  ↓
_generate_response (Lines 1286-1318)
  ↓
Line 1314-1316: Pass through debug_context ✅
  ↓
Return response with debug_context to API
```

### Code

#### EnhancedRAGAgent.run() (Lines 324-419)

```python
# Line 324-419
logger.info("📌 ROUTING: BALANCED (using intelligent TaskRouter)")

# Call TaskRouter
routing_decision = await task_router.route(
    query=query,
    documents=documents_metadata,
    session_id=session_id,
    user_preferences=user_preferences  # ✅ Contains unified_config
)

if routing_decision:
    # Use TaskRouter decision
    primary_tool = routing_decision.primary_tool
    fallback_chain = routing_decision.fallback_chain

    # Build tool params from routing decision
    tool_params = routing_decision.tool_params.copy()  # ✅ Line 419 - Already contains unified_config from TaskRouter
```

#### TaskRouter.route() (Lines 583-592)

```python
# task_router.py Lines 583-592
# Build tool parameters
tool_params = {
    "query": query,
    "session_id": session_id,
    "complexity": complexity.value,
    "available_memory_mb": available_memory
}

# Merge user preferences
if user_preferences:
    tool_params.update(user_preferences)  # ✅ Line 592 - This passes unified_config through
```

### Example Query (This is the path "hello world" takes!)

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=hello world" \
  -F "session_id=balanced_test" \
  -F "model=gpt-4o-mini" \
  -F 'unified_config={"strategy_weights":{"enable_brain_view":true}}'
```

### Response

```json
{
  "answer": "Hello! I'm a chatbot designed to assist...",
  "sources": [],
  "debug_context": {
    "routing": {
      "selected_strategy": "balanced",
      "primary_tool": "document_rag",
      "fallback_chain": ["navigation_agent", "llm"]
    },
    "tools_executed": ["document_rag"],
    "documents_retrieved": [],
    "performance": {...}
  }
}
```

---

## Special Cases

### URL Navigation Override

**Code Location**: Lines 222-237

Even if FORCE_RAG is triggered, URL navigation queries bypass it:

```python
# Line 222-237
# 🌐 PRIORITY: Check for URLs BEFORE applying FORCE_RAG
import re
url_pattern = r'https?://[^\s]+'
navigation_keywords = ['navigate', 'scrape', 'get details', 'fetch from', 'access', 'browse', 'visit']

has_url = re.search(url_pattern, query)
has_navigation_intent = any(keyword in query.lower() for keyword in navigation_keywords)

if has_url and has_navigation_intent:
    logger.info("🌐 ROUTING: NAVIGATION (URL detected with navigation intent - bypassing FORCE_RAG)")
    logger.info(f"   URL found: {has_url.group()}")
    logger.info(f"   Navigation keywords detected in query")

    # Use navigation agent even if RAG weights are high
    # This will be handled by the balanced routing below
```

---

## Brain View Support Matrix

| Path | Brain View Supported | Reason |
|------|---------------------|---------|
| **Path 0: CONVERSATION_ONLY** | ❌ NO | No RAG service called (LLM only) |
| **Path 1: DIRECT_LLM** | ❌ NO | No RAG service called (LLM only) |
| **Path 2: FORCE_RAG** | ✅ YES | unified_config passed to RAGService (Line 254) |
| **Path 3: BALANCED/TaskRouter** | ✅ YES | unified_config passed through TaskRouter (Line 592) |

### Brain View Implementation Status

✅ **COMPLETE** - All RAG paths now support Brain View:

1. **rag_service.py**:
   - ✅ Line 12: Fixed import to include `Any`
   - ✅ Line 65: Has `unified_config` parameter
   - ✅ Lines 155-164: Extracts `enable_brain_view` flag
   - ✅ Generates `debug_context` when enabled

2. **enhanced_rag_agent.py**:
   - ✅ Line 254: FORCE_RAG passes unified_config
   - ✅ Line 1363: Synthesis path passes unified_config
   - ✅ Line 1616: _execute_tool_document_rag passes unified_config
   - ✅ Lines 1314-1316: _generate_response passes through debug_context

3. **task_router.py**:
   - ✅ Line 592: Merges user_preferences (containing unified_config) into tool_params

---

## Code References

### File: backend/app/main.py

| Line Range | Purpose |
|------------|---------|
| 629 | Receives unified_config from frontend |
| 716-723 | Parses unified_config JSON |
| 738-749 | Builds user_preferences dict with unified_config |
| 711 | Routes to EnhancedRAGAgent |

### File: backend/app/agents/enhanced_rag_agent.py

| Line Range | Purpose |
|------------|---------|
| 92-96 | run() method signature with user_preferences |
| 159-200 | **Path 0: CONVERSATION_ONLY** |
| 202-220 | **Path 1: DIRECT_LLM** |
| 222-237 | URL navigation override logic |
| 241-269 | **Path 2: FORCE_RAG** |
| 254 | ✅ Passes unified_config in FORCE_RAG |
| 324-660 | **Path 3: BALANCED/TaskRouter** |
| 364 | Calls TaskRouter.route() |
| 419 | Copies tool_params from routing_decision |
| 1286-1318 | _generate_response() method |
| 1314-1316 | ✅ Passes through debug_context |
| 1347-1364 | Synthesis path (calls rag_service.query) |
| 1363 | ✅ Passes unified_config in synthesis |
| 1605-1617 | _execute_tool_document_rag() method |
| 1616 | ✅ Passes unified_config to RAGService |

### File: backend/app/services/rag_service.py

| Line Range | Purpose |
|------------|---------|
| 12 | ✅ Import statement (includes `Any`) |
| 65 | ✅ query() signature with unified_config |
| 155-164 | ✅ Extracts enable_brain_view from unified_config |

### File: backend/app/services/task_router.py

| Line Range | Purpose |
|------------|---------|
| 583-592 | Builds tool_params and merges user_preferences |
| 592 | ✅ tool_params.update(user_preferences) |

---

## Summary

**Total Query Routing Paths**: 4

1. **CONVERSATION_ONLY** (weight > 0.9) - LLM with conversation history only
2. **DIRECT_LLM** (weight > 0.8) - LLM for general knowledge
3. **FORCE_RAG** (rag weights > 0.8) - Forces document search
4. **BALANCED/TaskRouter** (default) - Intelligent routing

**Brain View Supported**: Paths 2 and 3 (any path that calls RAGService)

**Implementation Status**: ✅ **COMPLETE**

All RAG paths now correctly pass `unified_config` to `RAGService`, which extracts `enable_brain_view` and generates `debug_context` when enabled. The `debug_context` is properly passed through to the API response.

---

**Last Updated**: 2025-12-06
**Debugging Session**: Brain View EnhancedRAGAgent Fix
**Related Docs**:
- `docs/fixes/BRAIN_VIEW_ENHANCED_RAG_AGENT_ROOT_CAUSE.md`
- `docs/fixes/BRAIN_VIEW_RUNTIME_ERROR_FIX.md`
- `docs/fixes/BRAIN_VIEW_STATE_PERSISTENCE_FIX.md`
