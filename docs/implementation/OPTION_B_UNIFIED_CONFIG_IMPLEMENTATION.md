# Option B: Unified Configuration - Implementation Plan

**Date**: 2025-11-24
**Goal**: ALL ~60 parameters from Weights Config flow through every query as single unified context
**Status**: Ready to implement

---

## Current State Analysis

### Parameters Currently in WeightsConfig (44 total):

```typescript
interface WeightsConfig {
  // 1. Strategy Weights (8 params)
  strategy_weights: {
    rag_short_term: 0.3
    rag_hybrid: 0.25
    tool_navigation: 0.15
    tool_ocr: 0.1
    tool_docling: 0.1
    tool_web_scraping: 0.05
    rag_long_term: 0.03
    direct_llm: 0.02
  }

  // 2. Scoring Formula (6 params)
  scoring_formula_weights: {
    strategy_weight: 0.3
    confidence: 0.25
    source_quality_score: 0.2
    relevance_score: 0.15
    completeness_score: 0.05
    diversity_bonus: 0.05
  }

  // 3. Source Quality (5 params)
  source_quality_weights: {
    short_term: 1.0
    long_term: 0.8
    general: 0.7
    scraped: 0.6
    ocr: 0.5
  }

  // 4. Classification Thresholds (4 params)
  classification_thresholds: {
    general_knowledge_skip: 0.8
    ai_personal_skip: 0.7
    ambiguous_use_rag: 0.4
    min_llm_classification_confidence: 0.6
  }

  // 5. Similarity Thresholds (5 params)
  similarity_thresholds: {
    default: 0.5
    proper_nouns: 0.4
    short_query: 0.45
    minimum: 0.3
    maximum: 0.95
  }

  // 6. Reranking Weights (3 params)
  reranking_weights: {
    semantic: 0.8    // ⚠️ OVERLAP with semantic_weight in RAGSettings!
    keyword: 0.2     // ⚠️ OVERLAP with keyword_weight in RAGSettings!
    recency: 0.0
  }

  // 7. Query Preprocessing (3 params)
  query_preprocessing: {
    max_length_for_expansion: 50
    min_query_length: 3
    max_query_length: 500
  }

  // 8. Cache Settings (2 params)
  cache: {
    similarity_threshold: 0.95
    ttl_seconds: 3600
  }

  // 9. Multi-tool Weights (5 params)
  multi_tool_weights: {
    document_rag: 0.4
    navigation_agent: 0.25
    ocr_tool: 0.15
    web_scraping: 0.15
    docling: 0.05
  }

  // 10. Answer Fusion (3 params)
  answer_fusion: {
    best_answer_weight: 0.6
    second_best_weight: 0.3
    third_best_weight: 0.1
  }
}
```

**Total: 44 parameters in WeightsConfig**

### Parameters Currently in RAGSettings (6 total):

```typescript
interface RAGConfig {
  top_k: 5
  similarity_threshold: 0.50
  min_similarity_threshold: 0.40
  no_relevant_docs_threshold: 0.35
  semantic_weight: 0.8   // ⚠️ DUPLICATE of reranking_weights.semantic
  keyword_weight: 0.2    // ⚠️ DUPLICATE of reranking_weights.keyword
}
```

**Total: 6 parameters in RAGSettings**

### ⚠️ **IDENTIFIED OVERLAPS** (2 duplicates):
1. **semantic_weight**: Exists in BOTH RAGSettings AND WeightsConfig.reranking_weights.semantic
2. **keyword_weight**: Exists in BOTH RAGSettings AND WeightsConfig.reranking_weights.keyword

---

## Required Changes

### Step 1: Resolve Duplicates

**Decision**: Use the WeightsConfig version (reranking_weights.semantic/keyword) as the single source of truth. Remove from RAGSettings.

**Reasoning**:
- WeightsConfig is more comprehensive
- Reranking weights is the semantically correct place for semantic/keyword weights
- RAGSettings will become a tab IN WeightsConfig, so it makes sense to defer to the parent

### Step 2: Consolidate RAGSettings as Tab

**New Structure**:
```
Weights Configuration (Main Component)
├── Tab 1: Strategy Weights
├── Tab 2: Scoring Formula
├── Tab 3: Source Quality
├── Tab 4: Classification
├── Tab 5: Similarity Thresholds  ← ⚠️ MERGE with RAG Settings
├── Tab 6: Hybrid Search (Reranking)  ← ⚠️ semantic/keyword weights HERE
├── Tab 7: Query Preprocessing
├── Tab 8: Cache Settings
├── Tab 9: Multi-tool Weights
└── Tab 10: Answer Fusion
```

**Tab 5 "Retrieval & Search"** (merging Similarity + RAG Settings):
```typescript
{
  retrieval_and_search: {
    // From WeightsConfig.similarity_thresholds
    default_similarity: 0.5,
    proper_nouns_threshold: 0.4,
    short_query_threshold: 0.45,
    minimum_threshold: 0.3,
    maximum_threshold: 0.95,

    // From RAGSettings (no duplicates)
    top_k: 5,
    no_relevant_docs_threshold: 0.35,

    // Removed duplicates:
    // semantic_weight - MOVED to Tab 6 (Reranking)
    // keyword_weight - MOVED to Tab 6 (Reranking)
    // similarity_threshold - MERGED with default_similarity
    // min_similarity_threshold - MERGED with minimum_threshold
  }
}
```

**Tab 6 "Hybrid Search (Reranking)"**:
```typescript
{
  reranking_weights: {
    semantic: 0.8,    // ✅ Single source of truth
    keyword: 0.2,     // ✅ Single source of truth
    recency: 0.0,
  }
}
```

### Step 3: Update Interface

**New Unified Interface** (48 parameters total after deduplication):

```typescript
interface UnifiedWeightsConfig {
  // 1. Strategy Weights (8)
  strategy_weights: { ... }

  // 2. Scoring Formula (6)
  scoring_formula_weights: { ... }

  // 3. Source Quality (5)
  source_quality_weights: { ... }

  // 4. Classification Thresholds (4)
  classification_thresholds: { ... }

  // 5. Retrieval & Search (7) ← MERGED from similarity_thresholds + RAGSettings
  retrieval_and_search: {
    default_similarity: number;
    proper_nouns_threshold: number;
    short_query_threshold: number;
    minimum_threshold: number;
    maximum_threshold: number;
    top_k: number;
    no_relevant_docs_threshold: number;
  }

  // 6. Hybrid Search / Reranking (3) ← semantic/keyword are HERE
  reranking_weights: {
    semantic: number;
    keyword: number;
    recency: number;
  }

  // 7. Query Preprocessing (3)
  query_preprocessing: { ... }

  // 8. Cache Settings (2)
  cache: { ... }

  // 9. Multi-tool Weights (5)
  multi_tool_weights: { ... }

  // 10. Answer Fusion (3)
  answer_fusion: { ... }
}
```

**Total: 48 parameters (44 + 7 new from RAGSettings - 2 duplicates - 1 merged)**

---

## Implementation Steps

### Task 1: Update WeightsConfig Interface ✅

**File**: `frontend/src/components/WeightsConfigManager.tsx`

**Changes**:
1. Add `retrieval_and_search` section
2. Remove old `similarity_thresholds` (merged into retrieval_and_search)
3. Update TabType to include 'retrieval' instead of 'similarity'

```typescript
interface UnifiedWeightsConfig {
  strategy_weights: { ... };
  scoring_formula_weights: { ... };
  source_quality_weights: { ... };
  classification_thresholds: { ... };

  // NEW: Merged section
  retrieval_and_search: {
    default_similarity: number;
    proper_nouns_threshold: number;
    short_query_threshold: number;
    minimum_threshold: number;
    maximum_threshold: number;
    top_k: number;
    no_relevant_docs_threshold: number;
  };

  reranking_weights: { ... };  // semantic/keyword stay here
  query_preprocessing: { ... };
  cache: { ... };
  multi_tool_weights: { ... };
  answer_fusion: { ... };
}

type TabType =
  | 'strategy'
  | 'scoring'
  | 'source_quality'
  | 'classification'
  | 'retrieval'        // RENAMED from 'similarity'
  | 'reranking'
  | 'preprocessing'
  | 'cache'
  | 'multi_tool'
  | 'fusion';
```

### Task 2: Update ChatInterface to Pass Unified Config ✅

**File**: `frontend/src/components/ChatInterface.tsx` (or ChatInterfaceEnhanced.tsx)

**Changes**:
1. Remove separate RAGSettings state
2. Fetch unified config from WeightsConfig API
3. Pass ALL 48 parameters as FormData

```typescript
const [unifiedConfig, setUnifiedConfig] = useState<UnifiedWeightsConfig | null>(null);

useEffect(() => {
  // Fetch unified config on mount
  fetch('http://localhost:8000/api/v1/config/weights')
    .then(res => res.json())
    .then(data => setUnifiedConfig(data.data));
}, []);

const sendQuery = async (query: string) => {
  if (!unifiedConfig) return;

  const formData = new FormData();
  formData.append('query', query);

  // Pass ALL 48 parameters as JSON string for "unified_config"
  formData.append('unified_config', JSON.stringify(unifiedConfig));

  // OR pass individually (backend can handle either)
  // Strategy weights (8)
  Object.entries(unifiedConfig.strategy_weights).forEach(([key, value]) => {
    formData.append(`strategy_weights_${key}`, value.toString());
  });

  // Scoring formula (6)
  Object.entries(unifiedConfig.scoring_formula_weights).forEach(([key, value]) => {
    formData.append(`scoring_formula_${key}`, value.toString());
  });

  // ... all other sections

  const response = await fetch('/api/v1/query', {
    method: 'POST',
    body: formData,
  });
};
```

### Task 3: Update Backend to Accept Unified Config ✅

**File**: `backend/app/main.py` or `backend/app/api/routes/__init__.py`

**Changes**:
1. Add `unified_config` parameter (JSON string)
2. Parse and pass to RAG agent

```python
from typing import Optional
from fastapi import Form
import json

@router.post("/api/v1/query")
async def query(
    query: str = Form(...),
    session_id: Optional[str] = Form(None),
    model_id: Optional[str] = Form(None),

    # NEW: Unified config as JSON string
    unified_config: Optional[str] = Form(None),

    # Database dependency
    db: AsyncSession = Depends(get_db)
):
    """
    Query endpoint that accepts unified configuration.
    unified_config contains ALL 48 parameters in JSON format.
    """

    # Parse unified config
    user_preferences = {}
    if unified_config:
        try:
            user_preferences = json.loads(unified_config)
            logger.info(f"✅ Received unified config with {len(str(user_preferences))} chars")
        except json.JSONDecodeError:
            logger.warning("⚠️ Failed to parse unified_config, using defaults")

    # Pass to enhanced RAG agent with ALL parameters
    result = await enhanced_rag_agent.query(
        query_text=query,
        session_id=session_id,
        user_preferences=user_preferences,  # ✅ ALL 48 parameters here
        db=db
    )

    return result
```

### Task 4: Update RAG Agent to Use Unified Config ✅

**File**: `backend/app/agents/enhanced_rag_agent.py`

**Changes**:
1. Accept `user_preferences` dict with ALL 48 parameters
2. Extract and apply parameters before LLM call

```python
async def query(
    self,
    query_text: str,
    session_id: Optional[str] = None,
    user_id: Optional[uuid.UUID] = None,
    conversation_history: Optional[List[Dict]] = None,
    user_preferences: Optional[Dict] = None,  # ✅ ALL 48 parameters
    db: AsyncSession = None
) -> Dict:
    """
    Process query with unified configuration in context.
    user_preferences contains ALL 48 weight/config parameters.
    """

    # Apply unified config (with defaults from config.py)
    config = user_preferences or {}

    # Extract retrieval parameters
    top_k = config.get('retrieval_and_search', {}).get('top_k', settings.TOP_K_RESULTS)
    default_similarity = config.get('retrieval_and_search', {}).get('default_similarity', settings.SIMILARITY_THRESHOLD)

    # Extract reranking weights (semantic/keyword are HERE now)
    semantic_weight = config.get('reranking_weights', {}).get('semantic', settings.SEMANTIC_WEIGHT)
    keyword_weight = config.get('reranking_weights', {}).get('keyword', settings.KEYWORD_WEIGHT)

    # Extract strategy weights
    strategy_weights = config.get('strategy_weights', {
        'rag_short_term': 0.3,
        'rag_hybrid': 0.25,
        # ... defaults
    })

    # Extract all other sections (scoring, source_quality, etc.)
    scoring_weights = config.get('scoring_formula_weights', {})
    source_quality = config.get('source_quality_weights', {})
    # ... etc

    logger.info(f"🎯 Using unified config: top_k={top_k}, semantic={semantic_weight}, strategy_weights={strategy_weights}")

    # Build context for LLM with ALL parameters
    llm_context = {
        'user_configuration': config,  # ✅ ENTIRE unified config available to LLM
        'active_parameters': {
            'retrieval': {'top_k': top_k, 'similarity': default_similarity},
            'reranking': {'semantic': semantic_weight, 'keyword': keyword_weight},
            'strategy': strategy_weights,
            # ... all sections
        }
    }

    # Pass context to RAG service and LLM
    rag_response = await enhanced_rag_service.query(
        query_text=query_text,
        session_id=session_id,
        top_k=top_k,
        similarity_threshold=default_similarity,
        semantic_weight=semantic_weight,
        keyword_weight=keyword_weight,
        # ... all parameters extracted from unified config
        llm_context=llm_context,  # ✅ Unified config in LLM context
        db=db
    )

    return rag_response
```

---

## Benefits of This Approach

1. **✅ Single Source of Truth**: One unified config object
2. **✅ No Duplicates**: semantic/keyword only in reranking_weights
3. **✅ Complete Context**: ALL 48 parameters available to LLM
4. **✅ UI Consolidation**: RAG Settings is now a tab in Weights Config
5. **✅ Easy to Extend**: Add new parameters to unified config
6. **✅ Consistent Flow**: UI → FormData → Backend → Agent → LLM (one path)

---

## Testing Plan

### Test 1: Verify Unified Config Flows Through
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -F "query=test" \
  -F 'unified_config={"strategy_weights":{"rag_short_term":0.5},"reranking_weights":{"semantic":0.9,"keyword":0.1},...}'
```

**Expected**: Backend logs show "✅ Received unified config" and all 48 parameters extracted correctly

### Test 2: Verify No Duplicates
```bash
# Check frontend state
console.log(unifiedConfig.reranking_weights.semantic)  // Should be 0.8
console.log(unifiedConfig.retrieval_and_search.top_k)  // Should be 5
// Should NOT have semantic_weight at top level (removed)
```

### Test 3: Verify LLM Receives Context
```bash
# Check agent logs
# Should show: "🎯 Using unified config: ... strategy_weights={...}"
# Should show: LLM context includes user_configuration with all 48 params
```

---

## Implementation Timeline

**Total Effort**: 2-3 days

### Day 1: Interface Updates
- Morning: Update WeightsConfig interface (Task 1)
- Afternoon: Test WeightsConfig UI still works

### Day 2: Integration
- Morning: Update ChatInterface to pass unified config (Task 2)
- Afternoon: Update backend endpoint (Task 3)

### Day 3: Agent & Testing
- Morning: Update RAG agent (Task 4)
- Afternoon: End-to-end testing

---

## Success Criteria

- ✅ No duplicate parameters (semantic/keyword only in reranking_weights)
- ✅ All 48 parameters accessible in UI (one component with tabs)
- ✅ All 48 parameters flow to backend as `unified_config`
- ✅ Backend logs show unified config received and parsed
- ✅ RAG agent extracts parameters from unified config
- ✅ LLM receives complete context with all parameters
- ✅ Queries work exactly as before (backward compatible)
- ✅ Can adjust ANY parameter and see effect on query results

---

**Status**: ✅ Ready to implement - Option B fully planned
**Next Step**: Start with Task 1 (Update WeightsConfig interface)

