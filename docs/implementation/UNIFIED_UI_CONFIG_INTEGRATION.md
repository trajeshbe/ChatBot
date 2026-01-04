# Unified UI Configure Settings - Integration Status

## Question
> Can we leverage the chat UI LLM selection for verticals and company selection? I think we have "Configure" settings in all the menu.. is it being used/passed to backend?

## Answer: **YES** - Configure Settings Exist But **NOT Currently Used by POCs**

---

## Current Configure Settings (Frontend)

### RAG Settings (`RAGSettings.tsx`)
**Available in localStorage as `rag_config`**:
```typescript
interface RAGConfig {
  top_k: number                    // Default: 5
  similarity_threshold: number      // Default: 0.50
  min_similarity_threshold: number  // Default: 0.40
  no_relevant_docs_threshold: number// Default: 0.35
  chunk_size: number               // Default: 800
  chunk_overlap: number            // Default: 150
  semantic_weight: number          // Default: 0.8 (80% semantic)
  keyword_weight: number           // Default: 0.2 (20% keyword)
}
```

**Passed to ChatInterface**: ✅ Yes
```tsx
// index.tsx:145
<ChatInterfaceEnhanced ragConfig={ragConfig} />
```

**Sent to Backend**: ✅ Yes (in query requests)
```typescript
// ChatInterface sends ragConfig in API calls
POST /api/v1/query
{
  "query": "...",
  "rag_config": { /* config from UI */ }
}
```

### Model Selection
**Available in UI**: ✅ Yes (`ModelSelector` component)
- User can select LLM model
- Stored in component state
- Sent with each query

### Missing: Company/Vertical Selection
**Available in UI**: ❌ **NO**
- No company selector in RAG settings
- No vertical/industry selector
- No POC-specific configuration UI

---

## Integration Status by Component

### 1. Unified Chat UI (Main Interface)
- ✅ **RAG Settings**: Passed to backend in query requests
- ✅ **Model Selection**: Passed to backend
- ❌ **Company Filter**: Not implemented
- ❌ **Vertical Filter**: Not implemented

### 2. Tier 2 Domain Verticals
**Status**: Most use own config, **ignore** Unified UI settings

**Example** (`generic_rag_service.py`):
```python
async def query(self, request: RAGQueryRequest):
    # Uses request.rag_config if provided
    config = request.rag_config or default_config
```

**Integration**: ✅ **Partial** - Accept config but don't require it

### 3. Tier 3 POCs (British Council, CRU, etc.)
**Status**: **Completely bypass** Unified UI settings

**British Council Example**:
```python
# course_recommender.py - No rag_config parameter
await recommender.recommend_courses(
    profile=profile,
    top_k=request.top_k  # Only this parameter passed
)
```

**Integration**: ❌ **NONE** - Don't accept or use Unified UI config

---

## Opportunity: Leverage Configure Settings for POCs

### Current Gap
POCs like British Council are **hardcoded** to use:
- Default LLM model from system (qwen2.5vl:latest)
- Hardcoded IntelligentRetrievalService settings
- No user control over RAG strategy

### Proposed Enhancement

#### 1. Add Company/Vertical Selector to RAG Settings

```tsx
// RAGSettings.tsx - Add new fields
interface RAGConfig {
  // ... existing fields ...
  company?: string          // e.g., "british_council", "cru", "grant_thornton"
  vertical?: string         // e.g., "education", "mining", "finance"
  llm_model_override?: string  // Override default LLM for this session
}
```

**UI Addition**:
```tsx
<select onChange={(e) => updateConfig('company', e.target.value)}>
  <option value="">All Companies</option>
  <option value="british_council">British Council</option>
  <option value="cru">CRU Mining</option>
  <option value="grant_thornton">Grant Thornton</option>
  {/* ... */}
</select>
```

#### 2. Update POC Routes to Accept RAG Config

**British Council Example**:
```python
# british_council_routes.py
class CourseRecommendRequest(BaseModel):
    profile: Optional[UserProfile] = None
    user_input: Optional[str] = None
    top_k: int = 10
    rag_config: Optional[RAGConfig] = None  # ✨ NEW

@router.post("/courses/recommend")
async def recommend_courses(
    request: CourseRecommendRequest,
    db: Session = Depends(get_db)
):
    # Use RAG config if provided
    top_k = request.rag_config.top_k if request.rag_config else request.top_k
    llm_model = request.rag_config.llm_model_override if request.rag_config else None

    # Pass to service
    recommender = get_course_recommender(db, rag_config=request.rag_config)
```

#### 3. Update POC Services to Use Config

**British Council Service**:
```python
# course_recommender.py
class CourseRecommenderService:
    def __init__(self, db: Session, rag_config: Optional[RAGConfig] = None):
        self.db = db
        self.config = rag_config or default_rag_config

        # Use config for LLM model selection
        self.llm_model = self.config.get('llm_model_override', 'gpt-4o-mini')

        # Use config for top_k
        self.default_top_k = self.config.get('top_k', 10)

        # Use config for similarity threshold
        self.similarity_threshold = self.config.get('similarity_threshold', 0.7)
```

---

## Benefits of Integration

### For Users
1. **Control LLM Model**: Choose faster/cheaper models for testing, better models for production
2. **Tune Relevance**: Adjust similarity thresholds per use case
3. **Filter by Company/Vertical**: Focus search on specific POCs
4. **Consistent Experience**: Same settings UI across all modules

### For POCs
1. **Reuse Existing UI**: No need to build custom config for each POC
2. **Standard Interface**: All POCs accept same `RAGConfig` schema
3. **Flexibility**: Users can override defaults without code changes
4. **Better LLM Selection**: Current issue (qwen2.5vl fails at JSON) could be user-configurable

---

## Implementation Priority

### Phase 1: **LLM Model Override** (Quick Win) ⭐
**Effort**: 1-2 days
**Impact**: HIGH - Solves current qwen2.5vl JSON issue

```python
# In IntelligentRetrievalService
async def retrieve(self, query, db, rag_config=None, ...):
    llm_model = rag_config.get('llm_model_override') if rag_config else None
    classification = await self.classify_query(query, llm_model=llm_model)
```

### Phase 2: **Company/Vertical Filter UI** (Medium Effort)
**Effort**: 3-5 days
**Impact**: MEDIUM - Better filtering, cleaner results

Add dropdown selectors to RAGSettings component

### Phase 3: **Full POC Integration** (Large Effort)
**Effort**: 1-2 weeks
**Impact**: HIGH - Standardizes all POCs

Update all 6 Tier 3 POCs to accept and use `RAGConfig`

---

## Recommendation

**YES, absolutely leverage Unified UI Configure settings!**

**Immediate Action**:
1. Add `llm_model_override` to RAGConfig (solves qwen2.5vl issue)
2. Update British Council to use this override
3. Test with `gpt-4o-mini` instead of vision model

**Next Sprint**:
1. Add company/vertical selectors to UI
2. Update all POC routes to accept RAGConfig
3. Standardize POC service constructors

This will give users consistent control and solve the current British Council vector search issue!
