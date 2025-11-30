# Multi-Strategy RAG vs RAG Pipeline - Architecture Analysis

**Date**: 2025-11-30
**Finding**: Discovered two separate RAG systems with different weight handling

---

## Executive Summary

You were **absolutely correct** - I was testing the wrong endpoint!

The system has **TWO separate RAG endpoints**:

1. **`/api/v1/rag-pipeline/query`** - Simple RAG pipeline (doesn't use weights)
2. **`/api/v1/multi-strategy/query`** - Multi-Strategy RAG (USES WEIGHTS!)

The Multi-Strategy endpoint is designed exactly for your use case - it can enable/disable different strategies (Direct LLM vs RAG) based on flags and weights.

---

## Architecture Overview

### System 1: RAG Pipeline (What I Tested ❌)

**Endpoint**: `/api/v1/rag-pipeline/query`

**File**: `backend/app/rag_pipeline/pipeline.py`

**Behavior**:
- Always retrieves documents
- Always uses RAG
- Does NOT consult strategy weights
- Simple, single-strategy approach

**Schema**:
```json
{
  "query": "string",
  "session_id": "string",
  "model_name": "ollama/qwen2.5:1.5b",
  "use_cache": false
}
```

**Use Case**: When you ALWAYS want RAG with document retrieval

---

### System 2: Multi-Strategy RAG (What I Should Have Tested ✅)

**Endpoint**: `/api/v1/multi-strategy/query`

**File**: `backend/app/services/multi_strategy_rag.py`

**Behavior**:
- Executes MULTIPLE strategies in parallel
- Can enable/disable each strategy via flags:
  - `enable_direct_llm` - Direct LLM (no RAG)
  - `enable_rag_short_term` - Session documents only
  - `enable_rag_long_term` - All documents
  - `enable_tools` - Tool-based strategies
- Uses strategy weights to score and rank answers
- Returns the BEST answer based on weighted scoring

**Schema**:
```json
{
  "query": "string",
  "session_id": "string",
  "model_id": "string",
  "enable_direct_llm": true/false,
  "enable_rag_short_term": true/false,
  "enable_rag_long_term": true/false,
  "enable_tools": false,
  "min_confidence": 0.3,
  "diversity_bonus": 0.1
}
```

**Use Case**: When you want multiple strategies evaluated and the best one selected

---

## How Multi-Strategy RAG Works

### Step 1: Execute Strategies in Parallel

```python
# If enable_direct_llm=True, executes Direct LLM (no document retrieval)
# If enable_rag_short_term=True, executes RAG with session documents
# If enable_rag_long_term=True, executes RAG with all documents
```

Each strategy returns a `CandidateAnswer` with:
- Answer text
- Confidence score
- Sources (if RAG)
- Metadata

### Step 2: Score Each Candidate

```python
# Formula (from line 469-476):
final_score = (
    strategy_weight * 0.30 +        # Base strategy weight
    confidence * 0.25 +              # LLM confidence
    source_quality_score * 0.25 +   # Quality of sources
    relevance_score * 0.15 +        # Relevance to query
    completeness_score * 0.05 +     # Answer completeness
    diversity_bonus                  # Bonus if has sources
)
```

**Strategy Weights** (currently hardcoded, line 84-93):
```python
self.strategy_weights = {
    AnswerStrategy.RAG_SHORT_TERM: 1.0,   # HIGHEST
    AnswerStrategy.RAG_HYBRID: 0.95,
    AnswerStrategy.RAG_LONG_TERM: 0.85,
    AnswerStrategy.DIRECT_LLM: 0.75,       # LOWEST
    AnswerStrategy.TOOL_NAVIGATION: 0.90,
    AnswerStrategy.TOOL_OCR: 0.90,
    AnswerStrategy.TOOL_WEB_SCRAPING: 0.85,
    AnswerStrategy.TOOL_DOCLING: 0.90
}
```

### Step 3: Select Best Answer

Returns the candidate with the **highest final_score**

---

## Testing the Correct Way

### Scenario 1: Force Direct LLM (No Documents)

**Request**:
```json
POST /api/v1/multi-strategy/query
{
  "query": "What is the secret code?",
  "session_id": "test-session",
  "model_id": "ollama/qwen2.5:1.5b",
  "enable_direct_llm": true,       // ✅ Enable Direct LLM
  "enable_rag_short_term": false,  // ❌ Disable RAG short-term
  "enable_rag_long_term": false,   // ❌ Disable RAG long-term
  "enable_tools": false
}
```

**Expected Behavior**:
- ONLY executes Direct LLM strategy
- No document retrieval
- Answer from general knowledge only
- Won't know about unique codes in uploaded document

---

### Scenario 2: Force RAG Long-term (Use Documents)

**Request**:
```json
POST /api/v1/multi-strategy/query
{
  "query": "What is the secret code?",
  "session_id": "test-session",
  "model_id": "ollama/qwen2.5:1.5b",
  "enable_direct_llm": false,      // ❌ Disable Direct LLM
  "enable_rag_short_term": false,
  "enable_rag_long_term": true,    // ✅ Enable RAG long-term ONLY
  "enable_tools": false
}
```

**Expected Behavior**:
- ONLY executes RAG long-term strategy
- Retrieves documents from vector store
- Answer should contain information from uploaded document
- Should mention unique codes if found in chunks

---

### Scenario 3: Competition (All Strategies Enabled, Weights Matter)

**Request**:
```json
POST /api/v1/multi-strategy/query
{
  "query": "What is the secret code?",
  "session_id": "test-session",
  "model_id": "ollama/qwen2.5:1.5b",
  "enable_direct_llm": true,       // ✅ Enable all
  "enable_rag_short_term": true,   // ✅ Enable all
  "enable_rag_long_term": true,    // ✅ Enable all
  "enable_tools": false
}
```

**Expected Behavior**:
- Executes all three strategies in parallel
- Scores each answer using weights formula
- Returns the BEST answer
- **If weights favor Direct LLM** → Likely returns direct LLM answer
- **If weights favor RAG** → Likely returns RAG answer with sources

**This is where strategy weights matter!**

---

## Weight Configuration Integration

### Current State

Weights are **hardcoded** in `multi_strategy_rag.py` (lines 84-93).

### What Should Happen

Weights should be loaded from `WeightsConfigService`:

```python
# In MultiStrategyRAG.__init__():
from app.services.weights_config_service import weights_config_service

def __init__(self):
    # Load weights from config instead of hardcoding
    config_weights = weights_config_service.get_strategy_weights()

    self.strategy_weights = {
        AnswerStrategy.RAG_SHORT_TERM: config_weights.get('rag_short_term', 1.0),
        AnswerStrategy.RAG_HYBRID: config_weights.get('rag_hybrid', 0.95),
        AnswerStrategy.RAG_LONG_TERM: config_weights.get('rag_long_term', 0.85),
        AnswerStrategy.DIRECT_LLM: config_weights.get('direct_llm', 0.75),
        # ... etc
    }
```

**Why this matters**: Then the `/api/v1/config/weights` endpoint would actually control behavior!

---

## Corrected Test Approach

### Test 1: Direct LLM Only (Disable RAG)

```python
response = await client.post(
    f"{self.base_url}/api/v1/multi-strategy/query",
    headers=headers,
    json={
        "query": "What is the secret code mentioned in the document?",
        "session_id": self.session_id,
        "model_id": "ollama/qwen2.5:1.5b",
        "enable_direct_llm": True,
        "enable_rag_short_term": False,  # Disable RAG
        "enable_rag_long_term": False,   # Disable RAG
        "enable_tools": False
    }
)
```

**Expected**:
- ✅ Answer from general knowledge
- ✅ No sources cited
- ✅ Won't contain unique codes

---

### Test 2: RAG Long-term Only (Disable Direct LLM)

```python
response = await client.post(
    f"{self.base_url}/api/v1/multi-strategy/query",
    headers=headers,
    json={
        "query": "What is the secret code mentioned in the document?",
        "session_id": self.session_id,
        "model_id": "ollama/qwen2.5:1.5b",
        "enable_direct_llm": False,      # Disable Direct LLM
        "enable_rag_short_term": False,
        "enable_rag_long_term": True,    # Enable RAG
        "enable_tools": False
    }
)
```

**Expected**:
- ✅ Answer from documents
- ✅ Sources cited
- ✅ Should contain unique codes (if model can extract them)

---

### Test 3: Weight-based Competition

```python
# First, update weights to favor Direct LLM
await self.set_weights(client, {
    "strategy_weights": {
        "direct_llm": 1.5,      # Very high
        "rag_long_term": 0.3    # Very low
    }
})

# Then query with ALL strategies enabled
response = await client.post(
    f"{self.base_url}/api/v1/multi-strategy/query",
    headers=headers,
    json={
        "query": "What is the secret code?",
        "enable_direct_llm": True,
        "enable_rag_short_term": True,
        "enable_rag_long_term": True
    }
)

# Check which strategy won
selected_strategy = response.json()["selected_strategy"]
# Should be "direct_llm" due to high weight
```

---

## Key Findings

### ✅ What Works

1. **Multi-Strategy Endpoint Exists** - `/api/v1/multi-strategy/query`
2. **Strategy Enable/Disable Flags** - Can control which strategies run
3. **Strategy Weights** - Used in scoring formula
4. **Parallel Execution** - All strategies run concurrently
5. **Weighted Scoring** - Best answer selected based on comprehensive scoring

### ❌ What's Missing

1. **Weights Not Loaded from Config**
   - Currently hardcoded in `multi_strategy_rag.py`
   - Should load from `weights_config_service`
   - Weight updates via `/api/v1/config/weights` don't affect multi-strategy

2. **No Direct Weight Integration**
   - Need to add import and initialization
   - Need to refresh weights when config changes

---

## Recommended Fixes

### Fix #1: Load Weights from Config Service (15 min)

**File**: `backend/app/services/multi_strategy_rag.py`

```python
# Add at top
from app.services.weights_config_service import weights_config_service

# Modify __init__
class MultiStrategyRAG:
    def __init__(self):
        # Load from config instead of hardcoding
        self._load_weights_from_config()

        # Source weights
        self.source_weights = {...}

    def _load_weights_from_config(self):
        """Load strategy weights from config service"""
        config_weights = weights_config_service.get_strategy_weights()

        self.strategy_weights = {
            AnswerStrategy.RAG_SHORT_TERM: config_weights.get('rag_short_term', 1.0),
            AnswerStrategy.RAG_HYBRID: config_weights.get('rag_hybrid', 0.95),
            AnswerStrategy.RAG_LONG_TERM: config_weights.get('rag_long_term', 0.85),
            AnswerStrategy.DIRECT_LLM: config_weights.get('direct_llm', 0.75),
            AnswerStrategy.TOOL_NAVIGATION: config_weights.get('tool_navigation', 0.90),
            AnswerStrategy.TOOL_OCR: config_weights.get('tool_ocr', 0.90),
            AnswerStrategy.TOOL_WEB_SCRAPING: config_weights.get('tool_web_scraping', 0.85),
            AnswerStrategy.TOOL_DOCLING: config_weights.get('tool_docling', 0.90)
        }

        logger.info(f"📊 Loaded strategy weights: {self.strategy_weights}")
```

### Fix #2: Add Weight Refresh Method (5 min)

```python
def refresh_weights(self):
    """Refresh weights from config (call after config update)"""
    self._load_weights_from_config()
    logger.info("♻️  Strategy weights refreshed from config")
```

Then call this from the weight update endpoint.

---

## Corrected Test File

I should create a NEW test file:
- `test_multi_strategy_rag_weights.py`

That uses:
- `/api/v1/multi-strategy/query` endpoint
- `enable_*` flags to control strategies
- Tests both flag-based control AND weight-based scoring

---

## Summary for User

**Your Question**: "reg rag vs direct llm, it has to tested via weight settings... are you checking in enhanced rag pipeline?"

**Answer**: You were RIGHT! I was testing the wrong endpoint.

**Correct Endpoint**: `/api/v1/multi-strategy/query`

**How to Control Behavior**:
1. **Use Enable Flags** (simplest way):
   - `enable_direct_llm: true/false`
   - `enable_rag_long_term: true/false`

2. **Use Weights** (when multiple strategies enabled):
   - Set `direct_llm` weight high → Direct LLM likely wins
   - Set `rag_long_term` weight high → RAG likely wins
   - BUT: Weights currently hardcoded, need to integrate with config service

**Next Step**: Create corrected test using `/api/v1/multi-strategy/query` endpoint

---

**Files Referenced**:
- `backend/app/services/multi_strategy_rag.py` (Main logic)
- `backend/app/api/routes/multi_strategy_routes.py` (API endpoints)
- `backend/app/services/weights_config_service.py` (Weight storage)

**Recommendation**:
1. Integrate weights_config_service into multi_strategy_rag.py
2. Re-run test with correct endpoint
3. Test both flag-based and weight-based control
