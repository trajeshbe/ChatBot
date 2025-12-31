# Weights Config - UI Reference Guide

**Date**: 2025-12-06
**Purpose**: Complete reference for all UI configuration parameters available in Advanced Settings

---

## 📋 Table of Contents

1. [Strategy Weights](#strategy-weights)
2. [Retrieval Parameters](#retrieval-parameters)
3. [Query Classification Thresholds](#query-classification-thresholds)
4. [Context Window Limits](#context-window-limits)
5. [Model Selection](#model-selection)
6. [Advanced Features](#advanced-features)
7. [Embedding Configuration](#embedding-configuration)
8. [Reranking Settings](#reranking-settings)
9. [Semantic Cache](#semantic-cache)
10. [Query Reformulation](#query-reformulation)
11. [Usage Examples](#usage-examples)

---

## Strategy Weights

### Overview
Strategy weights determine which query routing path the system uses. Higher weights (closer to 1.0) make that strategy more likely to be selected.

### Parameters

#### `rag_long_term`
- **Type**: Float (0.0 - 1.0)
- **Default**: 0.5
- **Description**: Weight for long-term RAG retrieval (all documents)
- **Use Case**: When you want answers from your entire document library
- **Example**: Set to 0.9 to prioritize searching all uploaded documents

#### `rag_short_term`
- **Type**: Float (0.0 - 1.0)
- **Default**: 0.3
- **Description**: Weight for short-term RAG retrieval (session documents only)
- **Use Case**: When you want answers from recently uploaded documents in current session
- **Example**: Set to 0.8 for session-specific document queries

#### `rag_hybrid`
- **Type**: Float (0.0 - 1.0)
- **Default**: 0.4
- **Description**: Weight for hybrid RAG (combines short-term and long-term)
- **Use Case**: Balanced approach searching both session and all documents
- **Example**: Set to 0.7 for comprehensive search

#### `direct_llm`
- **Type**: Float (0.0 - 1.0)
- **Default**: 0.2
- **Description**: Weight for direct LLM queries (no document retrieval)
- **Use Case**: General knowledge questions that don't require your documents
- **Example**: Set to 0.85 for questions like "What is Python?"

#### `conversation_only`
- **Type**: Float (0.0 - 1.0)
- **Default**: 0.1
- **Description**: Weight for conversation history-based responses
- **Use Case**: Follow-up questions based on chat history
- **Example**: Set to 0.9 for "tell me more about that" queries

---

## Retrieval Parameters

### Vector Search Settings

#### `top_k`
- **Type**: Integer
- **Default**: 5
- **Range**: 1-20
- **Description**: Number of document chunks to retrieve
- **Impact**: More chunks = more context but slower
- **Recommendation**:
  - 3-5 for fast queries
  - 10-15 for comprehensive answers
  - 20 for research tasks

#### `similarity_threshold`
- **Type**: Float (0.0 - 1.0)
- **Default**: 0.7
- **Description**: Minimum similarity score for retrieved chunks
- **Impact**: Higher = more relevant but fewer results
- **Recommendation**:
  - 0.6 for broad search
  - 0.75 for precise matching
  - 0.85 for exact matches only

#### `max_tokens_per_chunk`
- **Type**: Integer
- **Default**: 512
- **Range**: 256-2048
- **Description**: Maximum tokens per document chunk
- **Impact**: Larger chunks = more context per retrieval
- **Recommendation**:
  - 256 for quick answers
  - 512 for balanced
  - 1024 for detailed context

---

## Query Classification Thresholds

### Classification Confidence

#### `classification_threshold`
- **Type**: Float (0.0 - 1.0)
- **Default**: 0.6
- **Description**: Minimum confidence to use classified strategy
- **Impact**: Higher = stricter classification, fallback to hybrid more often
- **Recommendation**: 0.5-0.7 range

#### `enable_query_classification`
- **Type**: Boolean
- **Default**: true
- **Description**: Enable/disable automatic query classification
- **Options**: true | false

---

## Context Window Limits

### Conversation History

#### `max_conversation_history`
- **Type**: Integer
- **Default**: 10
- **Range**: 1-50
- **Description**: Maximum previous messages to include
- **Impact**: More history = better context but uses more tokens
- **Recommendation**:
  - 5 for simple Q&A
  - 10-15 for conversational
  - 20+ for complex discussions

#### `max_context_tokens`
- **Type**: Integer
- **Default**: 4000
- **Range**: 1000-16000
- **Description**: Maximum total context tokens (chunks + history)
- **Impact**: Must fit within model's context window
- **Recommendation** (by model):
  - GPT-3.5: 3000-4000
  - GPT-4: 6000-8000
  - Claude: 8000-12000

---

## Model Selection

### LLM Models

#### `model_id`
- **Type**: String
- **Options**:
  - `gpt-4o` - Latest GPT-4 (best quality)
  - `gpt-4o-mini` - Faster GPT-4 (balanced)
  - `gpt-3.5-turbo` - Fast and cheap
  - `claude-3-opus-20240229` - Best Claude model
  - `claude-3-sonnet-20240229` - Balanced Claude
  - `claude-3-haiku-20240307` - Fast Claude
  - `ollama/mistral` - Local Mistral model
  - `ollama/llama3` - Local Llama 3 model
- **Default**: gpt-4o-mini

### Embedding Models

#### `embedding_model`
- **Type**: String
- **Options**:
  - `all-MiniLM-L6-v2` - Fast, 384 dimensions (default)
  - `multi-qa-MiniLM-L6-cos-v1` - Q&A optimized
  - `all-mpnet-base-v2` - High quality, 768 dimensions
  - `paraphrase-multilingual-MiniLM-L12-v2` - Multilingual
- **Default**: all-MiniLM-L6-v2

---

## Advanced Features

### Brain View

#### `enable_brain_view`
- **Type**: Boolean
- **Default**: false
- **Description**: Show detailed debugging information
- **Displays**:
  - Routing decision and reason
  - Conversation history used
  - Tools executed with timing
  - Documents retrieved with scores
  - Performance metrics
- **Use Case**: Understanding how the system processes queries

### Multi-Strategy

#### `enable_multi_strategy`
- **Type**: Boolean
- **Default**: false
- **Description**: Use multiple strategies and combine results
- **Impact**: More comprehensive but slower
- **Use Case**: When single strategy isn't giving good results

#### `multi_strategy_top_n`
- **Type**: Integer
- **Default**: 3
- **Range**: 2-5
- **Description**: Number of strategies to use simultaneously

---

## Embedding Configuration

### Intelligent Embeddings

#### `enable_intelligent_embeddings`
- **Type**: Boolean
- **Default**: true
- **Description**: Auto-select best embedding strategy per query
- **Strategies**:
  - Visual (for images/diagrams)
  - Semantic (for text)
  - Hybrid (combined)

#### `visual_embedding_weight`
- **Type**: Float (0.0 - 1.0)
- **Default**: 0.5
- **Description**: Weight for visual embeddings in hybrid mode

---

## Reranking Settings

### Reranker Configuration

#### `enable_reranker`
- **Type**: Boolean
- **Default**: true
- **Description**: Use reranking to improve result quality
- **Impact**: Better relevance but adds latency

#### `reranker_model`
- **Type**: String
- **Options**:
  - `cross-encoder/ms-marco-MiniLM-L-6-v2` (default)
  - `cross-encoder/ms-marco-MiniLM-L-12-v2` (better quality)
- **Default**: ms-marco-MiniLM-L-6-v2

#### `reranker_top_n`
- **Type**: Integer
- **Default**: 3
- **Range**: 1-10
- **Description**: Number of top results after reranking

---

## Semantic Cache

### Cache Settings

#### `enable_semantic_cache`
- **Type**: Boolean
- **Default**: true
- **Description**: Cache similar query results
- **Impact**: Faster responses for similar questions

#### `cache_similarity_threshold`
- **Type**: Float (0.0 - 1.0)
- **Default**: 0.95
- **Description**: Minimum similarity to use cached result
- **Recommendation**: 0.90-0.98 range

#### `cache_ttl`
- **Type**: Integer (seconds)
- **Default**: 3600
- **Description**: Time to live for cached results
- **Options**:
  - 1800 (30 minutes)
  - 3600 (1 hour) - default
  - 7200 (2 hours)
  - 86400 (24 hours)

---

## Query Reformulation

### Reformulation Settings

#### `enable_query_reformulation`
- **Type**: Boolean
- **Default**: false
- **Description**: Automatically improve query phrasing
- **Impact**: Better retrieval but adds LLM call

#### `reformulation_strategies`
- **Type**: Array
- **Options**:
  - `expand` - Add related terms
  - `clarify` - Make query more specific
  - `decompose` - Break into sub-queries
- **Default**: ["expand"]

---

## Usage Examples

### Example 1: Document Research Mode

**Scenario**: Deep research across all uploaded documents

```json
{
  "strategy_weights": {
    "rag_long_term": 0.9,
    "enable_brain_view": true
  },
  "retrieval_params": {
    "top_k": 15,
    "similarity_threshold": 0.65,
    "max_tokens_per_chunk": 1024
  },
  "model_id": "gpt-4o",
  "enable_reranker": true,
  "reranker_top_n": 5
}
```

### Example 2: Session-Focused Q&A

**Scenario**: Quick answers from recently uploaded docs

```json
{
  "strategy_weights": {
    "rag_short_term": 0.85
  },
  "retrieval_params": {
    "top_k": 5,
    "similarity_threshold": 0.75
  },
  "model_id": "gpt-4o-mini",
  "enable_semantic_cache": true
}
```

### Example 3: Conversational Mode

**Scenario**: Multi-turn conversation with context

```json
{
  "strategy_weights": {
    "conversation_only": 0.9,
    "rag_hybrid": 0.3
  },
  "context_limits": {
    "max_conversation_history": 15,
    "max_context_tokens": 6000
  },
  "model_id": "claude-3-sonnet-20240229"
}
```

### Example 4: General Knowledge Mode

**Scenario**: Questions that don't need documents

```json
{
  "strategy_weights": {
    "direct_llm": 0.85
  },
  "model_id": "gpt-4o",
  "enable_semantic_cache": true,
  "cache_ttl": 7200
}
```

### Example 5: Comprehensive Search

**Scenario**: When you need the best possible answer

```json
{
  "strategy_weights": {
    "rag_hybrid": 0.8
  },
  "retrieval_params": {
    "top_k": 20,
    "similarity_threshold": 0.6
  },
  "enable_multi_strategy": true,
  "multi_strategy_top_n": 3,
  "enable_reranker": true,
  "enable_query_reformulation": true,
  "reformulation_strategies": ["expand", "clarify"],
  "model_id": "gpt-4o"
}
```

### Example 6: Fast Mode

**Scenario**: Quick responses with minimal latency

```json
{
  "strategy_weights": {
    "rag_short_term": 0.7
  },
  "retrieval_params": {
    "top_k": 3,
    "similarity_threshold": 0.8
  },
  "model_id": "gpt-3.5-turbo",
  "enable_reranker": false,
  "enable_semantic_cache": true
}
```

### Example 7: Visual Document Analysis

**Scenario**: Working with PDFs containing diagrams/images

```json
{
  "strategy_weights": {
    "rag_long_term": 0.85
  },
  "retrieval_params": {
    "top_k": 10
  },
  "embedding_config": {
    "enable_intelligent_embeddings": true,
    "visual_embedding_weight": 0.7
  },
  "model_id": "gpt-4o",
  "enable_brain_view": true
}
```

---

## How to Apply Configuration

### Method 1: UI Advanced Settings

1. Open http://localhost:3001
2. Click "⚙️ Advanced Settings" button
3. Adjust sliders and toggles
4. Click "Apply to My Session"

### Method 2: localStorage (JavaScript Console)

```javascript
const config = {
  strategy_weights: {
    rag_long_term: 0.9,
    enable_brain_view: true
  },
  retrieval_params: {
    top_k: 10
  }
};

localStorage.setItem('userWeightsConfig', JSON.stringify(config));
window.dispatchEvent(new CustomEvent('weightsConfigUpdated', { detail: config }));
```

### Method 3: Direct API Call

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=Your question here" \
  -F "session_id=test_session" \
  -F "model=gpt-4o-mini" \
  -F 'unified_config={"strategy_weights":{"rag_long_term":0.9}}'
```

---

## Configuration Presets

### Preset 1: "Research Mode"
```json
{
  "strategy_weights": {"rag_long_term": 0.9},
  "retrieval_params": {"top_k": 15, "similarity_threshold": 0.65},
  "enable_reranker": true
}
```

### Preset 2: "Chat Mode"
```json
{
  "strategy_weights": {"conversation_only": 0.85, "rag_hybrid": 0.3},
  "context_limits": {"max_conversation_history": 15}
}
```

### Preset 3: "Fast Mode"
```json
{
  "strategy_weights": {"rag_short_term": 0.7},
  "retrieval_params": {"top_k": 3},
  "enable_semantic_cache": true
}
```

### Preset 4: "Debug Mode"
```json
{
  "strategy_weights": {"rag_long_term": 0.8, "enable_brain_view": true},
  "enable_multi_strategy": true
}
```

---

## Parameter Validation

### Valid Ranges

| Parameter | Min | Max | Type |
|-----------|-----|-----|------|
| `strategy_weights.*` | 0.0 | 1.0 | Float |
| `top_k` | 1 | 20 | Integer |
| `similarity_threshold` | 0.0 | 1.0 | Float |
| `max_conversation_history` | 1 | 50 | Integer |
| `max_context_tokens` | 1000 | 16000 | Integer |
| `cache_ttl` | 60 | 86400 | Integer |

### Invalid Configurations

❌ **Don't do this**:
```json
{
  "strategy_weights": {
    "rag_long_term": 1.5  // ❌ > 1.0
  },
  "retrieval_params": {
    "top_k": 0  // ❌ Must be >= 1
  }
}
```

✅ **Do this**:
```json
{
  "strategy_weights": {
    "rag_long_term": 0.9  // ✅ Valid
  },
  "retrieval_params": {
    "top_k": 5  // ✅ Valid
  }
}
```

---

## Troubleshooting

### Config Not Saving

**Problem**: Settings not persisting after clicking "Apply to My Session"

**Solution**:
1. Clear browser cache (`Ctrl + Shift + Delete`)
2. Check browser console for errors
3. Verify localStorage works:
   ```javascript
   localStorage.setItem('test', 'value');
   console.log(localStorage.getItem('test'));
   ```

### Config Not Being Used

**Problem**: Queries not using custom config

**Solution**:
1. Check Network tab → `/api/v1/query` → Payload
2. Verify `unified_config` field is present
3. Check browser console for `weightsConfigUpdated` event

### Routing Not Working

**Problem**: Query not routing to expected strategy

**Solution**:
1. Enable Brain View to see routing decision
2. Check classification threshold
3. Verify strategy weight is high enough (>0.8 for priority)

---

## Performance Tips

### For Faster Responses

- Use `gpt-3.5-turbo` or `gpt-4o-mini`
- Set `top_k` to 3-5
- Enable semantic cache
- Disable reranker
- Use `rag_short_term` instead of `rag_long_term`

### For Better Quality

- Use `gpt-4o` or `claude-3-opus`
- Set `top_k` to 10-15
- Enable reranker
- Use `rag_hybrid` or `multi_strategy`
- Enable query reformulation

### For Visual Documents

- Enable intelligent embeddings
- Set `visual_embedding_weight` to 0.6-0.8
- Use `gpt-4o` (has vision capabilities)
- Set `top_k` to 10+

---

## Related Documentation

- **Implementation**: `docs/fixes/WEIGHTS_CONFIG_FIX_APPLIED.md`
- **Investigation**: `docs/fixes/WEIGHTS_CONFIG_LOCALSTORAGE_INVESTIGATION.md`
- **RAG Routing**: `docs/fixes/RAG_ROUTING_UI_CONFIG_INVESTIGATION.md`

---

**Last Updated**: 2025-12-06
**Version**: 1.0
**Status**: Complete Reference Guide
