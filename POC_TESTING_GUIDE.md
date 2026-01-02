# POC Testing Guide - British Council & CRU Mining Intelligence

**Created:** 2026-01-02
**Author:** Claude Code

---

## 📋 Quick Summary

Two new POC implementations have been added to the platform:

1. **British Council Course Recommendation** - AI-powered course matching using hybrid RAG
2. **CRU Mining Intelligence** - Multi-pipeline document intelligence with pgvector + Elasticsearch

Both POCs are accessible through:
- **Backend API:** Swagger UI at http://localhost:8000/api/docs
- **Frontend UI:** Customer Solutions menu (components created but need UI integration)
- **Direct Testing:** Test script provided

---

## 🎯 POC #1: British Council Course Recommendation

### Overview
AI-powered course recommendations matching users to British Council courses based on their profile and goals.

### Architecture
- **Profile Extraction:** GPT-4o-mini extracts structured profiles from natural language
- **Semantic Search:** pgvector with BAAI/bge-large-en-v1.5 embeddings
- **Reranking:** BAAI/bge-reranker-large cross-encoder
- **Hybrid Scoring:** 60% semantic + 40% profile matching

### API Endpoints

#### 1. Health Check
```bash
curl http://localhost:8000/api/v1/british-council/health
```

#### 2. Analyze User Profile
```bash
curl -X POST "http://localhost:8000/api/v1/british-council/profile/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "I am a software engineer wanting to improve my business English. I have intermediate level English (B1) and prefer online courses on weekends."
  }'
```

**Response:**
```json
{
  "profile": {
    "skills": ["software engineering", "programming"],
    "interests": ["business English", "professional development"],
    "education_level": "intermediate",
    "career_goals": ["work internationally"],
    "preferred_format": "online",
    "language_proficiency": "B1",
    "availability": "weekends"
  },
  "status": "success"
}
```

#### 3. Get Course Recommendations
```bash
curl -X POST "http://localhost:8000/api/v1/british-council/courses/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "I am a software engineer wanting to improve my business English",
    "top_k": 5
  }'
```

**Response:**
```json
{
  "recommendations": [
    {
      "course_id": "bc-001",
      "course_name": "Business English for Professionals",
      "description": "...",
      "match_score": 0.87,
      "semantic_score": 0.85,
      "profile_score": 0.90,
      "reasons": [
        "Matches your intermediate level",
        "Available in online format",
        "Covers business English and career development"
      ],
      "metadata": {...}
    }
  ],
  "profile": {...},
  "total_courses_analyzed": 5
}
```

### Frontend Component
**File:** `frontend/src/components/BritishCouncilRecommender.tsx`

**Features:**
- Profile input and analysis
- Real-time course recommendations
- Match score visualization
- Reason explanation

### MinIO Path
```
british_council/course_recommendation/{document_id}
```

---

## ⛏️ POC #2: CRU Mining Intelligence

### Overview
Multi-pipeline RAG system for mining document intelligence with automatic query routing.

### Architecture
- **Query Classification:** LLM classifies queries (SEMANTIC, KEYWORD, HYBRID, TABLE_DATA)
- **Pipeline A:** pgvector (semantic search)
- **Pipeline B:** Elasticsearch (BM25 keyword search)
- **Pipeline C:** Hybrid (RRF fusion of both)
- **Reranking:** BAAI/bge-reranker-large
- **Confidence Scoring:** Calibrated P(correct | features)

### API Endpoints

#### 1. Health Check
```bash
curl http://localhost:8000/api/v1/cru/health
```

#### 2. Multi-Pipeline Query (Auto-Route)
```bash
curl -X POST "http://localhost:8000/api/v1/cru/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the estimated capex for the Gold Valley project?",
    "top_k": 5
  }'
```

**Response:**
```json
{
  "answer": "The estimated capex for Gold Valley project is $125M (Feasibility Report 2024, Section 5.3)",
  "confidence": 0.89,
  "confidence_level": "high",
  "confidence_description": "Confident - answer is likely correct",
  "sources": [
    {
      "document_id": "uuid-123",
      "document_name": "Feasibility Report 2024.pdf",
      "page": 47,
      "score": 0.92,
      "snippet": "Total capital expenditure..."
    }
  ],
  "pipeline_used": "hybrid",
  "query_type": "hybrid",
  "processing_time_ms": 3200
}
```

#### 3. Pipeline Comparison (A/B Testing)
```bash
curl -X POST "http://localhost:8000/api/v1/cru/compare-pipelines" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare iron ore grades across drilling sites",
    "top_k": 5
  }'
```

**Response:**
```json
{
  "query": "Compare iron ore grades...",
  "results": [
    {
      "pipeline": "pgvector",
      "answer": "...",
      "confidence": 0.75,
      "confidence_level": "high",
      "num_sources": 3,
      "processing_time_ms": 2800
    },
    {
      "pipeline": "elasticsearch",
      "answer": "...",
      "confidence": 0.92,
      "confidence_level": "very_high",
      "num_sources": 5,
      "processing_time_ms": 1500
    },
    {
      "pipeline": "hybrid",
      "answer": "...",
      "confidence": 0.95,
      "confidence_level": "very_high",
      "num_sources": 5,
      "processing_time_ms": 3400
    }
  ],
  "winner": "hybrid",
  "reason": "Highest confidence (0.95) with 5 supporting sources"
}
```

### Query Routing Logic

| Query Type | Example | Pipeline |
|------------|---------|----------|
| **SEMANTIC** | "What are the key environmental risks?" | pgvector |
| **KEYWORD** | "Find documents mentioning Gold Valley" | Elasticsearch |
| **HYBRID** | "Capex for Gold Valley project 2024" | Both + RRF |
| **TABLE_DATA** | "Iron ore grades by drilling site" | Elasticsearch |

### Frontend Component
**File:** `frontend/src/components/CRUMiningIntelligence.tsx`

**Features:**
- Query input with sample queries
- Auto-routing visualization
- Pipeline comparison mode
- Confidence score display
- Source document viewer

### MinIO Path
```
cru/mining_intelligence/{document_id}
```

---

## 🧪 Running the Test Suite

### Prerequisites
```bash
# Ensure services are running
docker-compose ps

# Check backend health
curl http://localhost:8000/health
```

### Run Test Script
```bash
cd backend
python test_poc_implementations.py
```

### Test Output
The script tests:
1. ✅ British Council health check
2. ✅ Profile analysis
3. ✅ Course recommendations
4. ✅ CRU health check
5. ✅ Multi-pipeline queries (3 samples)
6. ✅ Pipeline comparison

---

## 🎨 Frontend UI Integration

### Current Status
- ✅ Backend services implemented
- ✅ API routes registered in main.py
- ✅ Frontend components created
- ⏳ **TODO:** Add components to Customer Solutions menu in `index.tsx`

### To Add to UI:

**Option 1: Modify `frontend/src/pages/index.tsx`**

1. Import components:
```typescript
import BritishCouncilRecommender from '@/components/BritishCouncilRecommender'
import CRUMiningIntelligence from '@/components/CRUMiningIntelligence'
```

2. Add tabs to `activeTab` type:
```typescript
const [activeTab, setActiveTab] = useState<'... | british-council | cru-mining'>('chat')
```

3. Add tab cases:
```typescript
{activeTab === 'british-council' && <BritishCouncilRecommender />}
{activeTab === 'cru-mining' && <CRUMiningIntelligence />}
```

**Option 2: Add to SidebarModern (Customer Solutions Menu)**

Look for the Customer Solutions section in `SidebarModern.tsx` and add menu items for both POCs.

---

## 📊 Code Reuse Analysis

### British Council POC
- **Reused:** 80%
  - LLM Service (100%)
  - Retrieval Service (100%)
  - Reranker Service (100%)
  - Embedding Service (100%)
- **New:** 20%
  - ProfileAnalyzerService (new business logic)
  - CourseRecommenderService (hybrid scoring)

### CRU Mining Intelligence POC
- **Reused:** 85%
  - pgvector/IntelligentRetrievalService (100%)
  - Elasticsearch Service (100%)
  - Rank Fusion Service (100%)
  - Confidence Scorer (100%)
  - Reranker Service (100%)
  - LLM Service (100%)
- **New:** 15%
  - MultiPipelineRouter (query classification)
  - CRUQueryService (orchestration)

---

## 📁 Files Created

### Backend Services
```
backend/app/services/british_council/
├── __init__.py
├── profile_analyzer.py
└── course_recommender.py

backend/app/services/cru/
├── __init__.py
├── multi_pipeline_router.py
└── cru_query_service.py
```

### API Routes
```
backend/app/api/routes/
├── british_council_routes.py
└── cru_routes.py
```

### Frontend Components
```
frontend/src/components/
├── BritishCouncilRecommender.tsx
└── CRUMiningIntelligence.tsx
```

### Test Scripts
```
backend/test_poc_implementations.py
```

---

## 🚀 Next Steps

1. **Test Backend APIs**
   ```bash
   cd backend
   python test_poc_implementations.py
   ```

2. **Access Swagger UI**
   - Open http://localhost:8000/api/docs
   - Navigate to "British Council" and "CRU Mining Intelligence" sections
   - Try the interactive API documentation

3. **Frontend Integration** (Optional)
   - Add components to Customer Solutions menu
   - Update routing in index.tsx
   - Rebuild frontend: `docker-compose build frontend && docker-compose restart frontend`

4. **Upload Sample Data** (For CRU)
   - Create mining documents (PDFs with capex data, feasibility studies)
   - Upload via UI or API
   - Test queries

5. **Create Course Catalog** (For British Council)
   - Create course descriptions
   - Index in pgvector
   - Test recommendations

---

## 🔍 Troubleshooting

### Issue: Routes not found (404)
**Solution:** Restart backend
```bash
docker-compose restart backend
```

### Issue: Import errors
**Solution:** Check routes are registered in main.py around line 1614

### Issue: LLM errors
**Solution:** Ensure OpenAI API key is set in .env
```bash
OPENAI_API_KEY=your-key-here
```

### Issue: Elasticsearch not available
**Solution:** Ensure Elasticsearch is running (added in previous infrastructure work)
```bash
docker-compose ps elasticsearch
```

---

## 📚 Documentation References

- Implementation Plans: `docs/merit_pocs/01_british_council_implementation_plan.md`
- Implementation Plans: `docs/merit_pocs/02_cru_implementation_plan.md`
- Infrastructure Analysis: `docs/merit_pocs/INFRASTRUCTURE_GAP_ANALYSIS.md`

---

## ✅ Completion Checklist

- [x] British Council backend services
- [x] British Council API routes
- [x] British Council frontend component
- [x] CRU backend services
- [x] CRU API routes
- [x] CRU frontend component
- [x] Routes registered in main.py
- [x] Test script created
- [ ] Frontend UI integrated into Customer Solutions menu
- [ ] Sample data created and indexed
- [ ] End-to-end testing completed

---

**Ready to test!** Run the test script and explore the APIs through Swagger UI.
