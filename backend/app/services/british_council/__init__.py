"""
British Council Course Recommendation POC

Services:
- ProfileAnalyzerService: Extract user profiles from natural language
- CourseRecommenderService: Hybrid recommendation engine (semantic + profile-based)

Reuses:
- tier_1.llm.llm_service: Multi-LLM support (GPT-4, Claude, Ollama)
- tier_1.rag.intelligent_retrieval_service: Semantic search with pgvector
- tier_1.embeddings.reranker_service: Cross-encoder reranking (BAAI/bge)

MinIO Path: british_council/course_recommendation/{document_id}

Author: Claude Code
Date: 2026-01-02
"""

from app.services.british_council.profile_analyzer import (
    ProfileAnalyzerService,
    UserProfile,
    get_profile_analyzer
)

from app.services.british_council.course_recommender import (
    CourseRecommenderService,
    CourseRecommendation,
    get_course_recommender
)

__all__ = [
    "ProfileAnalyzerService",
    "UserProfile",
    "get_profile_analyzer",
    "CourseRecommenderService",
    "CourseRecommendation",
    "get_course_recommender"
]
