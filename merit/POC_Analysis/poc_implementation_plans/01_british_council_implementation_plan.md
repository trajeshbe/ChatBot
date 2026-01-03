# British Council POC - Implementation Plan

> **Customer:** British Council
> **Use Case:** Course Recommendation RAG System
> **Priority:** Tier 1 (High - 80% code reuse from Grant Thornton)
> **Estimated Effort:** 2-3 weeks
> **Created:** 2026-01-02

---

## Table of Contents
1. [Business Requirements](#1-business-requirements)
2. [Technical Architecture](#2-technical-architecture)
3. [Reusable Components](#3-reusable-components-from-grant-thornton)
4. [New Components](#4-new-components-to-build)
5. [Data Flow](#5-data-flow)
6. [API Endpoints](#6-api-endpoints)
7. [Database Schema](#7-database-schema)
8. [Frontend UI](#8-frontend-ui-components)
9. [Testing Strategy](#9-testing-strategy)
10. [Deployment](#10-deployment)
11. [Timeline](#11-implementation-timeline)

---

## 1. Business Requirements

### 1.1 Core Functionality
- **Course Recommendation Engine**: Match user profiles to relevant British Council courses
- **Profile Analysis**: Extract skills, interests, education level, career goals from user input
- **Document Q&A**: Answer questions about course content, schedules, prerequisites
- **Chatbot Integration**: Azure Bot Framework for conversational interface

### 1.2 User Personas
- **International Students**: Seeking English language courses (IELTS, General English)
- **Professionals**: Business English, professional development
- **Academic Researchers**: Research support, academic writing
- **Career Changers**: Skill-based learning paths

### 1.3 Success Metrics
- Recommendation accuracy: >85% user satisfaction
- Response time: <3 seconds for course recommendations
- Document retrieval precision: >90%
- Chatbot engagement: >70% completion rate

---

## 2. Technical Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     BRITISH COUNCIL POC STACK                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐      ┌──────────────────────────────────┐    │
│  │ Azure Bot    │──────▶│  FastAPI Backend                 │    │
│  │ Framework    │      │  - Profile Analyzer               │    │
│  │ (Teams/Web)  │      │  - Course Recommender             │    │
│  └──────────────┘      │  - RAG Service (reused)           │    │
│                         │  - LLM Agent (LangChain)          │    │
│  ┌──────────────┐      └──────────────────────────────────┘    │
│  │ React UI     │                    │                           │
│  │ - Course     │────────────────────┘                           │
│  │   Browser    │                    │                           │
│  │ - Profile    │                    ▼                           │
│  │   Builder    │      ┌──────────────────────────────────┐    │
│  └──────────────┘      │  Vector Store (ChromaDB)         │    │
│                         │  - Course Catalog Embeddings     │    │
│                         │  - Course Descriptions           │    │
│                         │  - Prerequisites                 │    │
│                         └──────────────────────────────────┘    │
│                                       │                           │
│                                       ▼                           │
│                         ┌──────────────────────────────────┐    │
│                         │  PostgreSQL + pgvector           │    │
│                         │  - User profiles                 │    │
│                         │  - Recommendation history        │    │
│                         │  - Course metadata               │    │
│                         └──────────────────────────────────┘    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Embeddings** | BAAI/bge-large-en-v1.5 (1024-dim) | Same as Grant Thornton, GPU-accelerated |
| **Vector DB** | ChromaDB | Reuse existing infrastructure |
| **LLM** | OpenAI GPT-4o-mini | Cost-effective, fast, proven |
| **Agent Framework** | LangChain + LangGraph | Structured course matching workflow |
| **Chatbot** | Azure Bot Framework | Native Microsoft Teams integration |
| **Backend** | FastAPI + Pydantic | Existing stack |
| **Frontend** | React + TypeScript | Existing stack |
| **Storage** | MinIO (course materials) + PostgreSQL (metadata) | Existing infrastructure |

### 2.3 Reranking Strategy
- **Stage 1**: Semantic search (ChromaDB, top 50 courses)
- **Stage 2**: BAAI/bge-reranker-large (rerank to top 10)
- **Stage 3**: Profile matching score (combine with user preferences)

---

## 3. Reusable Components from Grant Thornton

### 3.1 Backend Services (80% Reuse)

| Service | File | Reuse % | Modifications Needed |
|---------|------|---------|---------------------|
| **Embedding Service** | `app/services/embedding_service.py` | 100% | None - works as-is |
| **Vector Store** | `app/rag_pipeline/retrieval.py` | 90% | Add course catalog collection |
| **Reranker Service** | `app/services/reranker_service.py` | 100% | None - works as-is |
| **LLM Service** | `app/services/llm_service.py` | 100% | None - works as-is |
| **Document Service** | `app/services/document_service.py` | 80% | Adapt for course PDFs/catalogs |
| **MinIO Path Builder** | `app/services/minio_path_builder.py` | 90% | Add british-council paths |

### 3.2 RAG Pipeline Architecture
```python
# Reuse entire Grant Thornton RAG workflow:
# 1. Load course catalog into ChromaDB
# 2. User query → embedding → semantic search
# 3. Rerank results with BAAI reranker
# 4. LLM synthesis with course recommendations
```

### 3.3 Database Models
- Reuse `documents` table for course materials
- Reuse `document_chunks` table for course descriptions
- Reuse `chat_sessions` for conversation tracking

---

## 4. New Components to Build

### 4.1 Profile Analyzer Service

**File:** `backend/app/services/british_council/profile_analyzer.py`

**Purpose:** Extract structured profile from user input

```python
from pydantic import BaseModel
from typing import List, Optional
import json

class UserProfile(BaseModel):
    """Structured user profile for course matching."""
    skills: List[str]
    interests: List[str]
    education_level: str  # "beginner", "intermediate", "advanced"
    career_goals: List[str]
    preferred_format: str  # "online", "in-person", "hybrid"
    language_proficiency: str  # "A1", "A2", "B1", "B2", "C1", "C2"
    availability: Optional[str] = None  # "weekdays", "weekends", "flexible"

class ProfileAnalyzerService:
    """Extract user profile using LLM."""

    def __init__(self, llm_service):
        self.llm = llm_service

    async def analyze_profile(self, user_input: str) -> UserProfile:
        """
        Extract structured profile from natural language input.

        Example input:
        "I'm a software engineer looking to improve my business English.
        I have intermediate level English (B1) and prefer online courses
        on weekends. I want to advance my career in international companies."

        Returns:
            UserProfile with extracted fields
        """
        prompt = f"""You are a profile analyzer for the British Council.
Extract a structured profile from this user input:

{user_input}

Return JSON with fields:
- skills: List[str] (e.g., ["software engineering", "programming"])
- interests: List[str] (e.g., ["business English", "career development"])
- education_level: str ("beginner", "intermediate", "advanced")
- career_goals: List[str]
- preferred_format: str ("online", "in-person", "hybrid")
- language_proficiency: str (A1, A2, B1, B2, C1, C2)
- availability: str ("weekdays", "weekends", "flexible")

JSON:"""

        response = await self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"}
        )

        profile_data = json.loads(response["content"])
        return UserProfile(**profile_data)
```

### 4.2 Course Recommender Service

**File:** `backend/app/services/british_council/course_recommender.py`

**Purpose:** Rank courses based on profile + semantic similarity

```python
from typing import List, Dict, Any
import numpy as np

class CourseRecommendation(BaseModel):
    """Single course recommendation with score breakdown."""
    course_id: str
    course_name: str
    description: str
    match_score: float  # 0.0 - 1.0
    semantic_score: float
    profile_score: float
    reasons: List[str]  # Why this course matches

class CourseRecommenderService:
    """Hybrid recommendation: semantic + rule-based."""

    def __init__(self, retrieval_service, reranker_service):
        self.retrieval = retrieval_service
        self.reranker = reranker_service

    async def recommend_courses(
        self,
        profile: UserProfile,
        top_k: int = 10
    ) -> List[CourseRecommendation]:
        """
        Recommend courses using hybrid approach.

        Steps:
        1. Semantic search: Find courses matching interests/goals (top 50)
        2. Rerank with BAAI reranker (top 20)
        3. Rule-based filtering: education level, format, availability
        4. Profile scoring: Bonus for skill matches
        5. Final ranking: weighted combination

        Returns:
            Top K course recommendations with scores
        """
        # 1. Build semantic query from profile
        query = self._build_query(profile)

        # 2. Semantic search
        results = await self.retrieval.search(
            query=query,
            collection="british_council_courses",
            top_k=50
        )

        # 3. Rerank
        reranked = await self.reranker.rerank(
            query=query,
            documents=[r["content"] for r in results],
            top_n=20
        )

        # 4. Profile-based scoring
        recommendations = []
        for idx, course in enumerate(reranked):
            semantic_score = course["score"]
            profile_score = self._calculate_profile_score(profile, course["metadata"])

            # Weighted combination: 60% semantic, 40% profile
            match_score = 0.6 * semantic_score + 0.4 * profile_score

            recommendations.append(CourseRecommendation(
                course_id=course["metadata"]["course_id"],
                course_name=course["metadata"]["course_name"],
                description=course["content"],
                match_score=match_score,
                semantic_score=semantic_score,
                profile_score=profile_score,
                reasons=self._generate_reasons(profile, course["metadata"])
            ))

        # 5. Sort by match score
        recommendations.sort(key=lambda x: x.match_score, reverse=True)
        return recommendations[:top_k]

    def _build_query(self, profile: UserProfile) -> str:
        """Convert profile to search query."""
        parts = []
        parts.extend(profile.interests)
        parts.extend(profile.career_goals)
        parts.append(f"{profile.education_level} level")
        parts.append(f"{profile.language_proficiency} proficiency")
        return " ".join(parts)

    def _calculate_profile_score(self, profile: UserProfile, metadata: Dict) -> float:
        """Rule-based scoring based on profile match."""
        score = 0.0

        # Education level match (0.3)
        if metadata.get("level") == profile.education_level:
            score += 0.3

        # Format match (0.2)
        if metadata.get("format") == profile.preferred_format:
            score += 0.2

        # Availability match (0.2)
        if metadata.get("schedule") == profile.availability:
            score += 0.2

        # Skill match (0.3)
        course_skills = set(metadata.get("skills", []))
        user_skills = set(profile.skills)
        if course_skills.intersection(user_skills):
            score += 0.3

        return min(score, 1.0)

    def _generate_reasons(self, profile: UserProfile, metadata: Dict) -> List[str]:
        """Generate human-readable reasons for recommendation."""
        reasons = []

        if metadata.get("level") == profile.education_level:
            reasons.append(f"Matches your {profile.education_level} level")

        if metadata.get("format") == profile.preferred_format:
            reasons.append(f"Available in {profile.preferred_format} format")

        course_skills = set(metadata.get("skills", []))
        user_skills = set(profile.skills)
        matching_skills = course_skills.intersection(user_skills)
        if matching_skills:
            reasons.append(f"Covers your interests: {', '.join(list(matching_skills)[:3])}")

        return reasons
```

### 4.3 Azure Bot Framework Connector

**File:** `backend/app/services/british_council/bot_connector.py`

**Purpose:** Connect to Azure Bot Framework for Teams/Web chat

```python
from fastapi import APIRouter, Request
from botbuilder.core import BotFrameworkAdapter, TurnContext
from botbuilder.schema import Activity

router = APIRouter()

# Bot Framework Adapter
ADAPTER = BotFrameworkAdapter(
    settings={
        "app_id": os.getenv("AZURE_BOT_APP_ID"),
        "app_password": os.getenv("AZURE_BOT_APP_PASSWORD")
    }
)

@router.post("/api/v1/british-council/bot/messages")
async def bot_messages(request: Request):
    """Handle incoming messages from Azure Bot Framework."""
    body = await request.json()
    activity = Activity().deserialize(body)

    async def turn_callback(turn_context: TurnContext):
        """Process single turn of conversation."""
        if turn_context.activity.type == "message":
            user_input = turn_context.activity.text

            # 1. Analyze profile
            profile = await profile_analyzer.analyze_profile(user_input)

            # 2. Recommend courses
            recommendations = await course_recommender.recommend_courses(profile)

            # 3. Format response
            response_text = format_recommendations(recommendations)

            # 4. Send response
            await turn_context.send_activity(response_text)

    await ADAPTER.process_activity(activity, "", turn_callback)
    return {"status": "ok"}
```

---

## 5. Data Flow

### 5.1 Course Recommendation Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                  COURSE RECOMMENDATION FLOW                       │
└──────────────────────────────────────────────────────────────────┘

1. USER INPUT
   ├─ "I'm a software engineer wanting to improve business English"
   └─ Via: Web UI / Azure Bot / API

2. PROFILE ANALYSIS
   ├─ ProfileAnalyzerService.analyze_profile()
   ├─ LLM extraction → UserProfile
   └─ Output: {skills: ["software engineering"], interests: ["business English"], ...}

3. SEMANTIC SEARCH
   ├─ Build query from profile
   ├─ Embed query with BAAI/bge-large-en-v1.5
   ├─ ChromaDB similarity search (top 50)
   └─ Retrieve course documents + metadata

4. RERANKING
   ├─ BAAI/bge-reranker-large
   ├─ Query-document cross-encoding
   └─ Top 20 most relevant courses

5. PROFILE SCORING
   ├─ Rule-based scoring (level, format, schedule match)
   ├─ Skill intersection bonus
   └─ Weighted combination: 60% semantic + 40% profile

6. RESPONSE GENERATION
   ├─ Top 10 courses with scores
   ├─ LLM synthesis of recommendations
   └─ Human-readable reasons for each course

7. OUTPUT
   └─ Formatted course list with:
       - Course name
       - Match score (85%)
       - Reasons: ["Matches intermediate level", "Online format", ...]
       - CTA: "Enroll now" link
```

### 5.2 Document Q&A Flow

```
USER QUESTION: "What are the prerequisites for Advanced Business English?"

1. Query → Embedding → Vector Search
2. Retrieve course descriptions (top 10)
3. Rerank with BAAI reranker (top 3)
4. LLM synthesis with context
5. Response: "Prerequisites: B2 level English, basic business vocabulary..."
```

---

## 6. API Endpoints

### 6.1 Profile Analysis

```http
POST /api/v1/british-council/profile/analyze
Content-Type: application/json

{
  "user_input": "I'm a software engineer looking to improve my business English..."
}

Response:
{
  "profile": {
    "skills": ["software engineering", "programming"],
    "interests": ["business English", "career development"],
    "education_level": "intermediate",
    "career_goals": ["international companies", "leadership roles"],
    "preferred_format": "online",
    "language_proficiency": "B1",
    "availability": "weekends"
  }
}
```

### 6.2 Course Recommendations

```http
POST /api/v1/british-council/courses/recommend
Content-Type: application/json

{
  "profile": { ... },  # UserProfile object
  "top_k": 10
}

Response:
{
  "recommendations": [
    {
      "course_id": "bc-bus-eng-001",
      "course_name": "Business English for Professionals",
      "description": "Improve your business communication skills...",
      "match_score": 0.87,
      "semantic_score": 0.85,
      "profile_score": 0.90,
      "reasons": [
        "Matches your intermediate level",
        "Available in online format",
        "Covers business English and career development"
      ],
      "metadata": {
        "duration": "12 weeks",
        "schedule": "Weekends",
        "price": "$499",
        "enrollment_link": "https://britishcouncil.org/courses/bc-bus-eng-001"
      }
    },
    ...
  ]
}
```

### 6.3 Document Q&A

```http
POST /api/v1/british-council/courses/query
Content-Type: application/json

{
  "question": "What are the prerequisites for Advanced Business English?",
  "session_id": "uuid-here"
}

Response:
{
  "answer": "Prerequisites for Advanced Business English:\n- B2 level English proficiency\n- Basic business vocabulary\n- Completed Intermediate Business English or equivalent",
  "sources": [
    {
      "course_id": "bc-bus-eng-002",
      "course_name": "Advanced Business English",
      "page": 1
    }
  ]
}
```

### 6.4 Azure Bot Endpoint

```http
POST /api/v1/british-council/bot/messages
Content-Type: application/json
Authorization: Bearer <bot-token>

{
  "type": "message",
  "text": "I want to learn business English",
  "from": { "id": "user-123" },
  "conversation": { "id": "conv-456" }
}

Response:
{
  "status": "ok"
}
```

---

## 7. Database Schema

### 7.1 New Tables

```sql
-- User profiles table
CREATE TABLE british_council_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id TEXT,
    skills TEXT[],
    interests TEXT[],
    education_level TEXT,
    career_goals TEXT[],
    preferred_format TEXT,
    language_proficiency TEXT,
    availability TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Course catalog metadata
CREATE TABLE british_council_courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id TEXT UNIQUE NOT NULL,
    course_name TEXT NOT NULL,
    description TEXT,
    level TEXT,  -- beginner, intermediate, advanced
    format TEXT,  -- online, in-person, hybrid
    schedule TEXT,  -- weekdays, weekends, flexible
    duration TEXT,
    price DECIMAL(10,2),
    skills TEXT[],
    prerequisites TEXT[],
    enrollment_link TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Recommendation history
CREATE TABLE british_council_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES british_council_profiles(id),
    course_id UUID REFERENCES british_council_courses(id),
    match_score FLOAT,
    semantic_score FLOAT,
    profile_score FLOAT,
    reasons TEXT[],
    clicked BOOLEAN DEFAULT FALSE,
    enrolled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_bc_courses_level ON british_council_courses(level);
CREATE INDEX idx_bc_courses_format ON british_council_courses(format);
CREATE INDEX idx_bc_recommendations_profile ON british_council_recommendations(profile_id);
```

### 7.2 Reuse Existing Tables

- `documents` - Store course PDFs, catalogs
- `document_chunks` - Course descriptions with embeddings
- `chat_sessions` - Track conversations
- `messages` - Store Q&A history

---

## 8. Frontend UI Components

### 8.1 Profile Builder Component

**File:** `frontend/src/components/BritishCouncilProfileBuilder.tsx`

**Purpose:** Interactive form to capture user profile

```typescript
interface ProfileBuilderProps {
  onProfileComplete: (profile: UserProfile) => void;
}

export const ProfileBuilder: React.FC<ProfileBuilderProps> = ({ onProfileComplete }) => {
  // Multi-step form:
  // Step 1: Skills & Interests (multi-select)
  // Step 2: Education Level (dropdown)
  // Step 3: Career Goals (text input)
  // Step 4: Preferences (format, availability)
  // Step 5: Language Proficiency (CEFR selector)

  return (
    <div className="max-w-2xl mx-auto">
      <h2>Tell us about yourself</h2>
      <Stepper steps={5} currentStep={currentStep} />

      {currentStep === 1 && <SkillsInterestsSelector />}
      {currentStep === 2 && <EducationLevelSelector />}
      {/* ... */}

      <button onClick={handleNext}>Next</button>
    </div>
  );
};
```

### 8.2 Course Browser Component

**File:** `frontend/src/components/BritishCouncilCourseBrowser.tsx`

**Purpose:** Display recommended courses with filtering

```typescript
export const CourseBrowser: React.FC = () => {
  const [recommendations, setRecommendations] = useState<CourseRecommendation[]>([]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {recommendations.map((course) => (
        <CourseCard
          key={course.course_id}
          course={course}
          matchScore={course.match_score}
          reasons={course.reasons}
        />
      ))}
    </div>
  );
};
```

### 8.3 Chatbot Widget

**File:** `frontend/src/components/BritishCouncilChatbot.tsx`

**Purpose:** Embedded chat widget for course Q&A

```typescript
export const BritishCouncilChatbot: React.FC = () => {
  // Azure Bot Framework Web Chat integration
  return (
    <div className="fixed bottom-4 right-4 w-96 h-[500px]">
      <ReactWebChat
        directLine={directLine}
        userID="user-123"
        username="Student"
      />
    </div>
  );
};
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

```python
# tests/services/british_council/test_profile_analyzer.py
async def test_profile_analyzer_extracts_skills():
    input_text = "I'm a software engineer wanting business English"
    profile = await profile_analyzer.analyze_profile(input_text)

    assert "software engineering" in profile.skills
    assert "business English" in profile.interests
    assert profile.education_level in ["beginner", "intermediate", "advanced"]

# tests/services/british_council/test_course_recommender.py
async def test_course_recommender_returns_top_k():
    profile = UserProfile(
        skills=["software engineering"],
        interests=["business English"],
        education_level="intermediate",
        # ...
    )

    recommendations = await recommender.recommend_courses(profile, top_k=5)

    assert len(recommendations) == 5
    assert all(0.0 <= r.match_score <= 1.0 for r in recommendations)
    assert recommendations[0].match_score >= recommendations[-1].match_score
```

### 9.2 Integration Tests

```python
# tests/integration/british_council/test_end_to_end.py
async def test_full_recommendation_flow(client):
    # 1. Analyze profile
    response = client.post("/api/v1/british-council/profile/analyze", json={
        "user_input": "Software engineer wanting business English"
    })
    profile = response.json()["profile"]

    # 2. Get recommendations
    response = client.post("/api/v1/british-council/courses/recommend", json={
        "profile": profile,
        "top_k": 10
    })
    recommendations = response.json()["recommendations"]

    assert len(recommendations) == 10
    assert recommendations[0]["match_score"] > 0.5
```

### 9.3 E2E Tests (Playwright)

```typescript
// tests/e2e/british_council/test_course_browser.spec.ts
test('User can browse and filter courses', async ({ page }) => {
  await page.goto('http://localhost:3001?tab=british-council');

  // Fill profile
  await page.fill('#skills-input', 'software engineering');
  await page.selectOption('#education-level', 'intermediate');
  await page.click('button:has-text("Get Recommendations")');

  // Wait for results
  await page.waitForSelector('.course-card');

  // Verify courses displayed
  const courseCards = await page.$$('.course-card');
  expect(courseCards.length).toBeGreaterThan(0);
});
```

---

## 10. Deployment

### 10.1 Environment Variables

Add to `.env`:

```bash
# British Council Configuration
AZURE_BOT_APP_ID=your-bot-app-id
AZURE_BOT_APP_PASSWORD=your-bot-password
BRITISH_COUNCIL_API_KEY=your-api-key

# Course Catalog Settings
BC_COURSE_CATALOG_PATH=/data/british_council/courses.json
BC_ENABLE_RERANKING=true
BC_RERANK_MODEL=BAAI/bge-reranker-large
```

### 10.2 Data Ingestion

**Script:** `backend/scripts/british_council/ingest_course_catalog.py`

```python
#!/usr/bin/env python3
"""Ingest British Council course catalog into ChromaDB."""

import json
from app.services.embedding_service import EmbeddingService
from app.rag_pipeline.retrieval import RetrievalService

async def ingest_courses():
    """Load courses from JSON and embed."""
    with open("/data/british_council/courses.json") as f:
        courses = json.load(f)

    embedding_service = EmbeddingService()
    retrieval_service = RetrievalService()

    for course in courses:
        # Embed course description
        embedding = await embedding_service.embed_text(course["description"])

        # Store in ChromaDB
        await retrieval_service.add_document(
            collection="british_council_courses",
            document_id=course["course_id"],
            content=course["description"],
            embedding=embedding,
            metadata={
                "course_name": course["course_name"],
                "level": course["level"],
                "format": course["format"],
                "skills": course["skills"],
                # ...
            }
        )

    print(f"✅ Ingested {len(courses)} courses")

if __name__ == "__main__":
    import asyncio
    asyncio.run(ingest_courses())
```

### 10.3 Deployment Steps

```bash
# 1. Add new service routes
cd backend
# Edit app/main_enhanced.py to include british_council routes

# 2. Database migrations
alembic revision --autogenerate -m "add british council tables"
alembic upgrade head

# 3. Ingest course catalog
docker-compose exec backend python scripts/british_council/ingest_course_catalog.py

# 4. Build frontend with new components
cd frontend
npm run build

# 5. Restart services
docker-compose restart backend frontend

# 6. Verify
curl http://localhost:8000/api/v1/british-council/health
```

---

## 11. Implementation Timeline

### Week 1: Foundation (Jan 2-8, 2026)
- **Day 1-2**: Set up database tables, MinIO paths
- **Day 3-4**: Implement ProfileAnalyzerService
- **Day 5**: Implement CourseRecommenderService core logic

### Week 2: Integration (Jan 9-15, 2026)
- **Day 1-2**: Build API endpoints
- **Day 3-4**: Frontend ProfileBuilder + CourseBrowser components
- **Day 5**: Azure Bot Framework integration

### Week 3: Testing & Optimization (Jan 16-22, 2026)
- **Day 1-2**: Unit tests + integration tests
- **Day 3**: E2E tests with Playwright
- **Day 4**: Performance optimization (caching, batching)
- **Day 5**: Documentation + deployment

### Total Effort: 15 working days (3 weeks)

---

## 12. Success Criteria

- [ ] Profile analyzer extracts 95%+ accurate profiles
- [ ] Course recommendations have >85% user satisfaction (survey)
- [ ] API response time <3 seconds for recommendations
- [ ] Azure Bot responds within 5 seconds
- [ ] 100% test coverage for core services
- [ ] E2E tests pass for full user journey

---

## 13. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **Profile extraction accuracy low** | Fine-tune LLM prompts, add validation layer |
| **Course catalog data quality issues** | Implement data validation pipeline, manual review |
| **Azure Bot Framework complexity** | Start with simple webhook, iterate |
| **Semantic search not finding relevant courses** | Add hybrid search (keyword + semantic), tune reranking |

---

**Status:** Ready for implementation
**Dependencies:** Grant Thornton POC complete (✅)
**Next Steps:** Create CRU implementation plan, then start coding
