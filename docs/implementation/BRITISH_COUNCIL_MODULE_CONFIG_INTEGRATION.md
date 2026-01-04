# British Council Module Configuration Integration Plan

> **Date**: 2026-01-03
> **Purpose**: Integrate British Council POC with Module Configuration system to enable dynamic LLM selection and RAG parameter tuning

---

## Executive Summary

The British Council POC currently:
- ❌ Returns 0 course recommendations despite having 4 courses in database
- ❌ Uses hardcoded IntelligentRetrievalService with default settings
- ❌ Uses qwen2.5vl (vision model) for query classification, which fails at JSON output
- ✅ Has Module Configuration UI already implemented (POCConfigManager)
- ✅ Has backend API for module configuration (`/api/v1/module-config`)

**Solution**: Integrate British Council POC with Module Configuration system to:
1. Allow users to select LLM model (override default qwen2.5vl)
2. Configure RAG parameters dynamically (top_k, similarity_threshold, weights)
3. Fix the 0 results issue by switching to direct vector search or fixing LLM classification

---

## Current Architecture Analysis

### Frontend (Already Implemented ✅)

**Component**: `POCConfigManager.tsx` (frontend/src/components/POCConfigManager.tsx)

**Features**:
- 6 tabs: Prompts, Models, Parameters, Thresholds, Scoring, Advanced
- Load config: `GET /api/v1/module-config/modules/{module_name}`
- Save config: `PUT /api/v1/module-config/modules/{module_name}`

**Integration in BritishCouncilRecommender**:
```typescript
// Line 4: Already imported
import POCConfigManager from './POCConfigManager'

// Line 40: Already has state
const [showConfig, setShowConfig] = useState(false)

// UI includes Settings button to open POCConfigManager
```

### Backend API (Already Implemented ✅)

**Routes**: `module_config_routes.py` (backend/app/api/routes/module_config_routes.py)

**Key Endpoints**:
1. `GET /api/v1/module-config/modules/{module_name}` - Get merged config
2. `PUT /api/v1/module-config/modules/{module_name}` - Update config
3. `POST /api/v1/module-config/modules/{module_name}/overrides` - User-specific overrides

**3-Level Config Resolution**:
1. Global defaults
2. Module-specific configuration
3. User-specific overrides

### Current British Council POC Flow

```
BritishCouncilRecommender (UI)
  ↓
POST /api/v1/british-council/courses/recommend
  ↓
CourseRecommenderService.recommend_courses()
  ↓
IntelligentRetrievalService.intelligent_search()
  ↓ (company="british_council", usecase="course_recommendation")
IntelligentRetrievalService.retrieve()
  ↓
LLM Classification (uses qwen2.5vl - FAILS)
  ↓
text_semantic strategy selected
  ↓
Database query with vector similarity
  ↓
❌ Returns 0 results (ISSUE)
```

---

## Problem Analysis

### Issue 1: LLM Classification Failure

**Root Cause**:
```
INFO - 🎯 No model specified, using default: qwen2.5vl:latest
ERROR - Failed to parse LLM response as JSON: Expecting value: line 1 column 1 (char 0)
WARNING - ⚠️ LLM classification failed: LLM returned invalid JSON, using keyword result
```

**Impact**: Falls back to keyword classification → selects text_semantic (correct) → but still returns 0 results

### Issue 2: Zero Results from Vector Search

**Verified**:
- ✅ 4 courses exist in database
- ✅ 4 chunks with embeddings (sentence-transformers/all-MiniLM-L6-v2, 384-dim)
- ✅ Metadata correct: `company="british_council"`, `usecase="course_recommendation"`
- ✅ Strategy: text_semantic → uses `embedding` column

**Unknown**: Why `retrieve()` returns 0 chunks

**Hypothesis**: Database query is filtering out all results due to:
- Session/project/user filters (unlikely - all None)
- Embedding strategy mismatch (unlikely - verified correct)
- **Database schema mismatch** - metadata stored in `meta_info` not `metadata`?

---

## Implementation Plan

### Phase 1: Fix Zero Results Issue (PRIORITY 1)

#### Option A: Switch to Direct Vector Search ⭐ RECOMMENDED

**Rationale**:
- Simpler, more predictable
- No LLM classification overhead
- Direct control over query
- Filters at database level (more efficient)

**Implementation**:

1. Update `course_recommender.py` to add a new method:

```python
# backend/app/services/british_council/course_recommender.py

from app.tier_1.embeddings.embedding_service import EmbeddingService
from sqlalchemy import select, func, and_
from app.models.database import Document

async def _direct_vector_search(
    self,
    query: str,
    company: str,
    usecase: str,
    top_k: int,
) -> List[Dict[str, Any]]:
    """
    Direct vector similarity search bypassing IntelligentRetrievalService.

    Args:
        query: Search query
        company: Company filter (british_council)
        usecase: Use case filter (course_recommendation)
        top_k: Number of results

    Returns:
        List of chunks with similarity scores
    """
    # Generate embedding
    embedding_service = EmbeddingService()
    query_embedding = await embedding_service.get_embedding(query)

    # Direct vector similarity query
    # Note: Check if metadata is stored in 'meta_info' or 'metadata' column
    stmt = (
        select(
            DocumentChunk,
            func.cosine_similarity(DocumentChunk.embedding, query_embedding).label('similarity')
        )
        .join(Document, DocumentChunk.document_id == Document.id)
        .where(
            and_(
                DocumentChunk.embedding.isnot(None),
                # Check both meta_info and metadata columns
                or_(
                    Document.meta_info['company'].astext == company,
                    Document.metadata['company'].astext == company
                ),
                or_(
                    Document.meta_info['usecase'].astext == usecase,
                    Document.metadata['usecase'].astext == usecase
                )
            )
        )
        .order_by(func.cosine_similarity(DocumentChunk.embedding, query_embedding).desc())
        .limit(top_k)
    )

    result = await self.db.execute(stmt)
    rows = result.all()

    # Convert to expected format
    results = []
    for chunk, similarity in rows:
        results.append({
            "content": chunk.content,
            "metadata": chunk.metadata or {},
            "score": float(similarity),
            "chunk_id": str(chunk.id),
            "document_id": str(chunk.document_id)
        })

    return results
```

2. Update `recommend_courses()` to use direct search:

```python
# Replace intelligent_search() call with direct search
search_results = await self._direct_vector_search(
    query=query,
    company="british_council",
    usecase="course_recommendation",
    top_k=min(50, top_k * 5)
)
```

#### Option B: Fix LLM Classification Model

**Implementation**:

1. Pass LLM model override to IntelligentRetrievalService:

```python
# backend/app/tier_1/rag/intelligent_retrieval_service.py

async def retrieve(
    self,
    query: str,
    db: Session,
    top_k: int = 5,
    session_id: Optional[str] = None,
    llm_model: Optional[str] = None,  # NEW PARAMETER
    **kwargs
) -> Dict[str, Any]:
    """
    Args:
        llm_model: Override default LLM model for query classification
    """
    # Use override if provided
    classification = await self.classify_query(
        query,
        llm_model=llm_model or "gpt-4o-mini"  # Default to good JSON model
    )
```

2. Update `course_recommender.py` to pass model:

```python
results = await self.retrieval_service.intelligent_search(
    query=query,
    db=self.db,
    top_k=top_k,
    session_id=session_id,
    company=company,
    usecase=usecase,
    llm_model="gpt-4o-mini"  # Override qwen2.5vl
)
```

### Phase 2: Module Configuration Integration

#### Step 1: Create British Council Module Config

**Backend**: Create initial configuration in database

```python
# backend/scripts/british_council/create_module_config.py

from app.services.poc_config_service import poc_config_service
from app.tier_1.infrastructure.database import get_db

async def create_british_council_config():
    """Create module configuration for British Council POC"""

    config = {
        "llm": {
            "profile_extraction": {
                "model": "gpt-4o-mini",
                "temperature": 0.2,
                "max_tokens": 1000
            },
            "query_classification": {
                "model": "gpt-4o-mini",  # Override qwen2.5vl
                "temperature": 0.0,
                "max_tokens": 150
            }
        },
        "retrieval": {
            "top_k": 50,
            "rerank_top_k": 20,
            "min_score": 0.3,
            "use_direct_search": True  # Feature flag
        },
        "scoring": {
            "weights": {
                "semantic": 0.6,
                "profile": 0.4
            },
            "factors": {
                "level_match": 0.3,
                "format_match": 0.2,
                "availability_match": 0.2,
                "skill_match": 0.3
            }
        },
        "thresholds": {
            "similarity_threshold": 0.7,
            "min_profile_score": 0.3,
            "high_confidence": 0.8
        },
        "prompts": {
            "system": {
                "profile_extraction": """Extract user profile from natural language input..."""
            }
        }
    }

    db = next(get_db())
    await poc_config_service.create_module_config(
        db=db,
        module_name="british_council",
        display_name="British Council Course Recommender",
        module_type="tier3_customer_solution",
        config=config,
        description="Personalized English course recommendations",
        category="education"
    )
```

#### Step 2: Update API to Accept Module Config

```python
# backend/app/api/routes/british_council_routes.py

class CourseRecommendRequest(BaseModel):
    """Request for course recommendations."""
    profile: Optional[UserProfile] = None
    user_input: Optional[str] = None
    top_k: int = 10
    session_id: Optional[str] = None
    module_config: Optional[Dict[str, Any]] = None  # ✨ NEW

@router.post("/courses/recommend")
async def recommend_courses(
    request: CourseRecommendRequest,
    db: Session = Depends(get_db)
):
    """Get personalized course recommendations."""

    # Load module config if not provided
    if not request.module_config:
        from app.services.poc_config_service import poc_config_service
        request.module_config = await poc_config_service.get_config(
            db=db,
            module_name="british_council",
            include_overrides=True
        )

    # Get course recommender with config
    recommender = get_course_recommender(db, config=request.module_config)

    # ... rest of endpoint
```

#### Step 3: Update CourseRecommenderService to Use Config

```python
# backend/app/services/british_council/course_recommender.py

class CourseRecommenderService:
    """Hybrid course recommendation engine."""

    def __init__(self, db: Session, config: Optional[Dict[str, Any]] = None):
        """
        Initialize course recommender.

        Args:
            db: Database session
            config: Module configuration (from Module Config system)
        """
        self.db = db
        self.config = config or {}

        # Extract config values
        retrieval_config = self.config.get("retrieval", {})
        scoring_config = self.config.get("scoring", {})

        # Use config for feature flags
        self.use_direct_search = retrieval_config.get("use_direct_search", False)

        # Use config for scoring weights
        weights = scoring_config.get("weights", {})
        self.semantic_weight = weights.get("semantic", 0.6)
        self.profile_weight = weights.get("profile", 0.4)

        # Initialize services
        if not self.use_direct_search:
            self.retrieval_service = IntelligentRetrievalService()
        self.reranker = CrossEncoderReranker(model_name="accurate")

        logger.info(f"🎯 CourseRecommenderService initialized with config: "
                   f"direct_search={self.use_direct_search}, "
                   f"semantic_weight={self.semantic_weight}")

    async def _semantic_search(self, ...):
        """Search using configured strategy."""

        if self.use_direct_search:
            return await self._direct_vector_search(...)
        else:
            # Get LLM model from config
            llm_config = self.config.get("llm", {}).get("query_classification", {})
            llm_model = llm_config.get("model", "gpt-4o-mini")

            return await self.retrieval_service.intelligent_search(
                ...,
                llm_model=llm_model
            )
```

#### Step 4: Update Frontend to Load and Pass Config

```typescript
// frontend/src/components/BritishCouncilRecommender.tsx

export default function BritishCouncilRecommender() {
  const [userInput, setUserInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [recommendations, setRecommendations] = useState<CourseRecommendation[]>([])
  const [error, setError] = useState<string | null>(null)
  const [showConfig, setShowConfig] = useState(false)
  const [moduleConfig, setModuleConfig] = useState<any>(null)  // ✨ NEW

  // Load module config on mount
  useEffect(() => {
    loadModuleConfig()
  }, [])

  const loadModuleConfig = async () => {
    try {
      const response = await axios.get(
        'http://localhost:8000/api/v1/module-config/modules/british_council',
        {
          params: {
            include_overrides: true,
            include_metadata: false
          }
        }
      )
      setModuleConfig(response.data.config)
    } catch (err) {
      console.error('Failed to load module config:', err)
      // Use defaults if config fails to load
    }
  }

  const handleGetRecommendations = async () => {
    // ... validation ...

    try {
      const response = await axios.post<RecommendationResponse>(
        'http://localhost:8000/api/v1/british-council/courses/recommend',
        {
          user_input: userInput,
          top_k: moduleConfig?.retrieval?.top_k || 10,  // Use config
          module_config: moduleConfig  // ✨ Pass config
        }
      )

      setRecommendations(response.data.recommendations)
      setProfile(response.data.profile)
      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to get recommendations')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      {/* ... existing UI ... */}

      {/* Settings button */}
      <button onClick={() => setShowConfig(true)}>
        <Settings className="w-5 h-5" />
        Configure
      </button>

      {/* Config modal */}
      {showConfig && (
        <POCConfigManager
          moduleName="british_council"
          onClose={() => {
            setShowConfig(false)
            loadModuleConfig()  // Reload after config changes
          }}
        />
      )}
    </div>
  )
}
```

---

## Testing Plan

### Test 1: Direct Vector Search Fix

```bash
# 1. Update course_recommender.py with direct search method
# 2. Set use_direct_search=True in config
# 3. Test API

curl -X POST "http://localhost:8000/api/v1/british-council/courses/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "I am a software engineer wanting to improve my business English",
    "top_k": 5
  }'

# Expected: Returns 4 courses (all courses match query)
```

### Test 2: Module Config Creation

```bash
# Run creation script
cd backend
python scripts/british_council/create_module_config.py

# Verify in database
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT module_name, display_name, module_type FROM module_configurations WHERE module_name='british_council';"
```

### Test 3: Frontend Config UI

```
1. Open http://localhost:3001
2. Navigate to British Council POC
3. Click "Configure" button
4. Verify POCConfigManager opens with british_council config
5. Change LLM model from qwen2.5vl to gpt-4o-mini
6. Save changes
7. Test recommendation - should use new model
```

### Test 4: User-Specific Overrides

```bash
# Set user override for testing
curl -X POST "http://localhost:8000/api/v1/module-config/modules/british_council/overrides" \
  -H "Content-Type: application/json" \
  -d '{
    "overrides": {
      "retrieval": {
        "top_k": 20
      },
      "scoring": {
        "weights": {
          "semantic": 0.8,
          "profile": 0.2
        }
      }
    }
  }'

# Test with override
curl -X POST "http://localhost:8000/api/v1/british-council/courses/recommend?user_id={user_id}" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "..."}'

# Verify top_k=20 used and weights are 0.8/0.2
```

---

## Rollout Plan

### Week 1: Fix Zero Results Issue
- ✅ Implement direct vector search method
- ✅ Test with existing data
- ✅ Verify 4 courses returned
- ✅ Compare quality vs IntelligentRetrievalService

### Week 2: Module Config Integration
- ✅ Create british_council module config
- ✅ Update API to accept module_config parameter
- ✅ Update CourseRecommenderService to use config
- ✅ Add feature flag: `use_direct_search`

### Week 3: Frontend Integration
- ✅ Load module config on component mount
- ✅ Pass config to API calls
- ✅ Test Settings button → POCConfigManager flow
- ✅ User testing and feedback

### Week 4: Production Readiness
- ✅ Add unit tests for config integration
- ✅ Add E2E tests for config UI
- ✅ Documentation for users
- ✅ Performance benchmarks (direct vs intelligent search)

---

## Benefits

### For Users
1. **Dynamic LLM Selection**: Choose faster/cheaper models for testing, better models for production
2. **Tunable RAG Parameters**: Adjust top_k, similarity thresholds per use case
3. **Personalized Weights**: Fine-tune semantic vs profile scoring balance
4. **A/B Testing**: Test different configurations without code changes

### For Developers
1. **Reuse Existing Infrastructure**: Module Configuration system already built
2. **Standard Interface**: Same config pattern across all POCs
3. **Version Control**: Full history of config changes
4. **User Overrides**: Support customer-specific tuning

### For System
1. **Consistent Pattern**: All Tier 3 POCs use same config approach
2. **Reduced Hardcoding**: Move settings to database
3. **Easier Debugging**: Config visible in UI, not buried in code
4. **Scalable**: Templates for new POCs

---

## Next Steps

1. **Immediate (TODAY)**:
   - Implement direct vector search fix (Option A)
   - Test and verify 4 courses returned

2. **This Week**:
   - Create british_council module config
   - Update API to accept module_config
   - Test end-to-end

3. **Next Week**:
   - Frontend integration
   - User testing
   - Documentation

---

## Success Metrics

- ✅ British Council POC returns >0 course recommendations
- ✅ Users can change LLM model via UI
- ✅ Users can adjust RAG parameters via UI
- ✅ Config changes reflected in API calls
- ✅ Version history tracks config changes
- ✅ Performance: Direct search < 200ms vs IntelligentRetrievalService

---

**End of Integration Plan**
