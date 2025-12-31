# Multi-Strategy RAG with Answer Fusion - Usage Guide

**Date**: 2025-11-24
**Status**: ✅ IMPLEMENTED & INTEGRATED
**API Prefix**: `/api/v1/multi-strategy`

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [API Endpoints](#api-endpoints)
4. [Usage Examples](#usage-examples)
5. [Strategy Weights](#strategy-weights)
6. [Response Format](#response-format)
7. [Advanced Usage](#advanced-usage)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### What is Multi-Strategy RAG?

Multi-Strategy RAG is an intelligent answer fusion system that:

1. **Executes multiple answer strategies in parallel**:
   - Direct LLM (no RAG)
   - RAG with short-term memory (session documents) - **HIGHEST WEIGHT**
   - RAG with long-term memory (all documents)
   - RAG hybrid (short + long combined)
   - Tool-based answers (OCR, web scraping, etc.)

2. **Scores each candidate answer** using weighted formula:
   ```
   final_score = (
       strategy_weight * 0.30 +       # Short-term: 1.0, Direct: 0.75
       confidence * 0.25 +             # LLM confidence
       source_quality_score * 0.25 +  # Short-term: 1.0, Long-term: 0.7
       relevance_score * 0.15 +       # Answer relevance
       completeness_score * 0.05      # Answer completeness
   ) + diversity_bonus                # +0.1 if has sources
   ```

3. **Selects the best answer** based on final score

4. **Prioritizes recent uploads** (short-term memory gets highest weight)

### Why Use Multi-Strategy RAG?

- **Robust**: No single point of failure - best answer wins
- **Context-Aware**: Recent uploads automatically prioritized
- **Adaptive**: Works correctly even if classification would be wrong
- **Transparent**: Shows all candidates evaluated and their scores
- **Efficient**: Strategies run in parallel (asyncio)

---

## Quick Start

### 1. Check Service Health

```bash
curl http://localhost:8000/api/v1/multi-strategy/health | jq '.'
```

**Expected Response**:
```json
{
  "status": "healthy",
  "service": "multi-strategy-rag",
  "strategies_available": [
    "direct_llm",
    "rag_short_term",
    "rag_long_term",
    "rag_hybrid",
    "tool_navigation",
    "tool_ocr",
    "tool_web_scraping",
    "tool_docling"
  ],
  "current_weights": {
    "rag_short_term": 1.0,
    "rag_hybrid": 0.95,
    "rag_long_term": 0.85,
    "direct_llm": 0.75,
    "tool_navigation": 0.9,
    "tool_ocr": 0.9
  }
}
```

### 2. Execute Multi-Strategy Query

```bash
curl -X POST http://localhost:8000/api/v1/multi-strategy/query-form \
  -F "query=Who is Aadhan?" \
  -F "session_id=my-session-123" \
  -F "model_id=llama3.1:8b" \
  -F "enable_direct_llm=true" \
  -F "enable_rag_short_term=true" \
  -F "enable_rag_long_term=true" | jq '.'
```

**What Happens**:
1. System executes Direct LLM, RAG Short-term, RAG Long-term in parallel
2. Each strategy generates a candidate answer
3. Candidates are scored using the weighted formula
4. Best answer is selected and returned

---

## API Endpoints

### 1. `/api/v1/multi-strategy/query-form` (POST)

Execute multi-strategy query (form-encoded for easy testing)

**Parameters**:
- `query` (required): User query text
- `session_id` (optional): Session ID for short-term memory
- `model_id` (optional, default: "llama3.1:8b"): LLM model to use
- `enable_direct_llm` (optional, default: true): Enable direct LLM strategy
- `enable_rag_short_term` (optional, default: true): Enable short-term RAG
- `enable_rag_long_term` (optional, default: true): Enable long-term RAG
- `enable_tools` (optional, default: false): Enable tool-based strategies

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/multi-strategy/query-form \
  -F "query=What is machine learning?" \
  -F "model_id=llama3.1:8b"
```

---

### 2. `/api/v1/multi-strategy/query` (POST)

Execute multi-strategy query (JSON request body)

**Request Body**:
```json
{
  "query": "Who is Aadhan?",
  "session_id": "session-123",
  "model_id": "llama3.1:8b",
  "enable_direct_llm": true,
  "enable_rag_short_term": true,
  "enable_rag_long_term": true,
  "enable_tools": false,
  "min_confidence": 0.3,
  "diversity_bonus": 0.1
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/multi-strategy/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the capital of France?",
    "model_id": "llama3.1:8b"
  }' | jq '.'
```

---

### 3. `/api/v1/multi-strategy/weights` (GET)

Get current strategy weights

**Example**:
```bash
curl http://localhost:8000/api/v1/multi-strategy/weights | jq '.'
```

**Response**:
```json
{
  "strategy_weights": {
    "rag_short_term": 1.0,
    "rag_long_term": 0.85,
    "direct_llm": 0.75,
    "tool_navigation": 0.9
  },
  "source_weights": {
    "short_term": 1.0,
    "long_term": 0.7,
    "general": 0.5
  },
  "description": {
    "strategy_weights": "Weight given to each strategy (higher = more trusted)",
    "source_weights": "Quality score for different source types"
  }
}
```

---

### 4. `/api/v1/multi-strategy/weights` (POST)

Update strategy weights dynamically

**Request Body**:
```json
{
  "rag_short_term": 1.2,
  "rag_long_term": 0.8,
  "direct_llm": 0.6
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/multi-strategy/weights \
  -H "Content-Type: application/json" \
  -d '{
    "rag_short_term": 1.2,
    "direct_llm": 0.6
  }' | jq '.'
```

**Response**:
```json
{
  "success": true,
  "updated_weights": {
    "rag_short_term": 1.2,
    "direct_llm": 0.6
  },
  "current_weights": {
    "rag_short_term": 1.2,
    "rag_long_term": 0.85,
    "direct_llm": 0.6
  }
}
```

---

### 5. `/api/v1/multi-strategy/compare` (POST)

Compare all strategies side-by-side (debugging)

**Parameters**:
- `query` (required): User query
- `session_id` (optional): Session ID
- `model_id` (optional): LLM model

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/multi-strategy/compare \
  -F "query=Who is Aadhan?" \
  -F "session_id=my-session" | jq '.'
```

**Response**:
```json
{
  "query": "Who is Aadhan?",
  "winner": {
    "strategy": "rag_short_term",
    "score": 0.970,
    "confidence": 0.90,
    "answer": "According to your uploaded document, Aadhan is...",
    "sources": 2
  },
  "all_candidates": [
    {
      "strategy": "rag_short_term",
      "score": 0.970,
      "confidence": 0.90
    },
    {
      "strategy": "direct_llm",
      "score": 0.435,
      "confidence": 0.30
    },
    {
      "strategy": "rag_long_term",
      "score": 0.335,
      "confidence": 0.20
    }
  ],
  "strategy_weights_used": {
    "rag_short_term": 1.0,
    "direct_llm": 0.75,
    "rag_long_term": 0.85
  },
  "explanation": "Winner selected based on highest final score. rag_short_term scored 0.970"
}
```

---

### 6. `/api/v1/multi-strategy/health` (GET)

Health check for multi-strategy RAG service

**Example**:
```bash
curl http://localhost:8000/api/v1/multi-strategy/health | jq '.'
```

---

## Usage Examples

### Example 1: Custom Entity Query ("Who is Aadhan?")

**Scenario**: You uploaded a document about "Aadhan" to your session

```bash
curl -X POST http://localhost:8000/api/v1/multi-strategy/query-form \
  -F "query=Who is Aadhan?" \
  -F "session_id=my-session-123" \
  -F "model_id=llama3.1:8b" | jq '{
    strategy_used: .strategy_used,
    final_score: .final_score,
    answer: (.answer[:200] + "..."),
    num_sources: .num_sources,
    top_3: .metadata.top_3_strategies
  }'
```

**Expected Output**:
```json
{
  "strategy_used": "rag_short_term",
  "final_score": 0.970,
  "answer": "According to your uploaded document, Aadhan is...",
  "num_sources": 2,
  "top_3": [
    {"strategy": "rag_short_term", "score": 0.970},
    {"strategy": "direct_llm", "score": 0.435},
    {"strategy": "rag_long_term", "score": 0.335}
  ]
}
```

**Why RAG Short-term Won**:
- Strategy weight: 1.0 (highest)
- Has relevant sources from session documents
- High confidence from LLM
- Source quality score: 1.0 (short-term)
- **Final score: 0.970** 🏆

---

### Example 2: General Knowledge Query

**Scenario**: No documents uploaded, asking about world capitals

```bash
curl -X POST http://localhost:8000/api/v1/multi-strategy/query-form \
  -F "query=What is the capital of France?" \
  -F "model_id=llama3.1:8b" | jq '{
    strategy_used: .strategy_used,
    final_score: .final_score,
    answer: .answer,
    num_sources: .num_sources
  }'
```

**Expected Output**:
```json
{
  "strategy_used": "direct_llm",
  "final_score": 0.800,
  "answer": "Paris",
  "num_sources": 0
}
```

**Why Direct LLM Won**:
- No relevant documents found
- High LLM confidence (0.95)
- Simple factual answer
- **Final score: 0.800** 🏆

---

### Example 3: Famous Person (Override General Knowledge)

**Scenario**: Asking about Vishwanath Anand WITH a document uploaded

```bash
curl -X POST http://localhost:8000/api/v1/multi-strategy/query-form \
  -F "query=Who is Vishwanath Anand?" \
  -F "session_id=my-session-123" \
  -F "model_id=llama3.1:8b" | jq '{
    strategy_used: .strategy_used,
    answer: (.answer[:200] + "..."),
    sources: [.sources[].filename]
  }'
```

**If Document Uploaded**:
```json
{
  "strategy_used": "rag_short_term",
  "answer": "According to your uploaded document, Vishwanath Anand...",
  "sources": ["my_document_about_anand.pdf"]
}
```
✅ **YOUR content overrides general knowledge!**

**If NO Document**:
```json
{
  "strategy_used": "direct_llm",
  "answer": "Vishwanath Anand is an Indian chess grandmaster..."
}
```
✅ **Falls back to general knowledge**

---

## Response Format

### Success Response

```json
{
  "success": true,
  "answer": "The answer text...",
  "strategy_used": "rag_short_term",
  "final_score": 0.970,
  "confidence": 0.90,
  "num_sources": 2,
  "sources": [
    {
      "document_id": "uuid",
      "filename": "document.pdf",
      "content": "Relevant chunk...",
      "score": 0.95
    }
  ],
  "metadata": {
    "candidates_evaluated": 3,
    "top_3_strategies": [
      {
        "strategy": "rag_short_term",
        "score": 0.970,
        "confidence": 0.90
      },
      {
        "strategy": "direct_llm",
        "score": 0.435,
        "confidence": 0.30
      },
      {
        "strategy": "rag_long_term",
        "score": 0.335,
        "confidence": 0.20
      }
    ],
    "strategy_weights_used": {
      "rag_short_term": 1.0,
      "rag_long_term": 0.85,
      "direct_llm": 0.75
    }
  }
}
```

### Error Response

```json
{
  "success": false,
  "detail": "Error message"
}
```

---

## Strategy Weights

### Default Weights

```python
strategy_weights = {
    "rag_short_term": 1.0,     # Highest - recent uploads
    "rag_hybrid": 0.95,         # Combined short + long
    "rag_long_term": 0.85,      # Historical documents
    "direct_llm": 0.75,         # Lowest - no sources
    "tool_navigation": 0.9,     # Web scraping with navigation
    "tool_ocr": 0.9,            # Image text extraction
    "tool_web_scraping": 0.85,  # Basic web scraping
    "tool_docling": 0.9         # Advanced PDF processing
}
```

### Tuning Weights

**Increase short-term memory priority even more**:
```bash
curl -X POST http://localhost:8000/api/v1/multi-strategy/weights \
  -H "Content-Type: application/json" \
  -d '{"rag_short_term": 1.2}'
```

**Decrease direct LLM priority**:
```bash
curl -X POST http://localhost:8000/api/v1/multi-strategy/weights \
  -H "Content-Type: application/json" \
  -d '{"direct_llm": 0.6}'
```

**Reset to defaults**:
```bash
curl -X POST http://localhost:8000/api/v1/multi-strategy/weights \
  -H "Content-Type: application/json" \
  -d '{
    "rag_short_term": 1.0,
    "rag_long_term": 0.85,
    "direct_llm": 0.75
  }'
```

---

## Advanced Usage

### Python Client Example

```python
import requests

# Multi-strategy query
response = requests.post(
    "http://localhost:8000/api/v1/multi-strategy/query",
    json={
        "query": "Who is Aadhan?",
        "session_id": "my-session-123",
        "model_id": "llama3.1:8b",
        "enable_direct_llm": True,
        "enable_rag_short_term": True,
        "enable_rag_long_term": True,
        "enable_tools": False
    }
)

result = response.json()

print(f"Answer: {result['answer']}")
print(f"Strategy used: {result['strategy_used']}")
print(f"Final score: {result['final_score']:.3f}")
print(f"Confidence: {result['confidence']:.2f}")
print(f"Sources: {result['num_sources']}")

# Show all candidates evaluated
print("\nAll candidates:")
for candidate in result['metadata']['top_3_strategies']:
    print(f"  - {candidate['strategy']}: {candidate['score']:.3f}")
```

---

### JavaScript/TypeScript Client Example

```typescript
interface MultiStrategyQueryRequest {
  query: string;
  session_id?: string;
  model_id?: string;
  enable_direct_llm?: boolean;
  enable_rag_short_term?: boolean;
  enable_rag_long_term?: boolean;
  enable_tools?: boolean;
}

async function multiStrategyQuery(request: MultiStrategyQueryRequest) {
  const response = await fetch(
    "http://localhost:8000/api/v1/multi-strategy/query",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request)
    }
  );

  const result = await response.json();

  console.log(`Answer: ${result.answer}`);
  console.log(`Strategy: ${result.strategy_used}`);
  console.log(`Score: ${result.final_score.toFixed(3)}`);
  console.log(`Candidates evaluated: ${result.metadata.candidates_evaluated}`);

  return result;
}

// Usage
await multiStrategyQuery({
  query: "Who is Aadhan?",
  session_id: "my-session-123",
  model_id: "llama3.1:8b"
});
```

---

## Troubleshooting

### Issue: Multi-strategy endpoint returns 404

**Solution**: Ensure backend is running and routes are registered
```bash
# Check backend logs
docker-compose logs backend | grep "Multi-Strategy"

# Should see:
# "✓ Multi-Strategy RAG API router registered (answer fusion...)"
```

---

### Issue: All strategies return low scores

**Cause**: No relevant documents, LLM confidence low

**Solution**: Check that documents are uploaded and processed
```bash
# List documents in session
curl http://localhost:8000/api/v1/documents?session_id=my-session-123 | jq '.'
```

---

### Issue: Short-term memory not prioritized

**Cause**: Strategy weights may have been changed

**Solution**: Check and reset weights
```bash
# Check current weights
curl http://localhost:8000/api/v1/multi-strategy/weights | jq '.strategy_weights'

# Reset short-term to highest
curl -X POST http://localhost:8000/api/v1/multi-strategy/weights \
  -H "Content-Type: application/json" \
  -d '{"rag_short_term": 1.0}'
```

---

### Issue: Query takes too long

**Cause**: Multiple strategies executing in parallel

**Solution**: Disable strategies you don't need
```bash
# Only use short-term RAG and direct LLM
curl -X POST http://localhost:8000/api/v1/multi-strategy/query-form \
  -F "query=Who is Aadhan?" \
  -F "enable_rag_short_term=true" \
  -F "enable_rag_long_term=false" \
  -F "enable_tools=false"
```

---

## Summary

### Key Features

✅ **Multiple strategies evaluated** in parallel
✅ **Best answer selected** via weighted scoring
✅ **Short-term memory prioritized** (weight 1.0)
✅ **Transparent** - shows all candidates and scores
✅ **Robust** - no single point of failure
✅ **Tunable** - adjust weights dynamically

### Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/multi-strategy/query-form` | POST | Execute multi-strategy query (form) |
| `/api/v1/multi-strategy/query` | POST | Execute multi-strategy query (JSON) |
| `/api/v1/multi-strategy/weights` | GET | Get current strategy weights |
| `/api/v1/multi-strategy/weights` | POST | Update strategy weights |
| `/api/v1/multi-strategy/compare` | POST | Compare strategies side-by-side |
| `/api/v1/multi-strategy/health` | GET | Health check |

### Default Strategy Weights

- **rag_short_term**: 1.0 (HIGHEST)
- **rag_hybrid**: 0.95
- **rag_long_term**: 0.85
- **tool_navigation**: 0.9
- **direct_llm**: 0.75 (LOWEST)

---

**End of Guide**

For implementation details, see:
- `backend/app/services/multi_strategy_rag.py` (600+ lines)
- `backend/app/api/routes/multi_strategy_routes.py` (250+ lines)
- `MULTI_STRATEGY_RAG_GUIDE.md` (Quick reference)
- `DYNAMIC_QUERY_CLASSIFICATION_GUIDE.md` (Classification system)
