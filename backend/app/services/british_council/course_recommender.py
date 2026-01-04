"""
British Council Course Recommender - Hybrid Recommendation Engine

Combines semantic search (pgvector) + cross-encoder reranking + profile-based scoring
for personalized course recommendations.

Reuses:
- tier_1.rag.intelligent_retrieval_service: Semantic search with pgvector
- tier_1.embeddings.reranker_service: Cross-encoder reranking (BAAI/bge)
- services.british_council.profile_analyzer: User profile extraction

Author: Claude Code
Date: 2026-01-02
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, Float

from app.models.database import DocumentChunk, Document
from app.tier_1.rag.intelligent_retrieval_service import IntelligentRetrievalService
from app.tier_1.embeddings.reranker_service import CrossEncoderReranker
from app.services.british_council.profile_analyzer import UserProfile

logger = logging.getLogger(__name__)


class CourseRecommendation(BaseModel):
    """Single course recommendation with score breakdown."""

    course_id: str = Field(description="Unique course identifier")
    course_name: str = Field(description="Course title")
    description: str = Field(description="Course description")
    match_score: float = Field(description="Final combined match score (0.0 - 1.0)")
    semantic_score: float = Field(description="Semantic similarity score from reranker")
    profile_score: float = Field(description="Profile-based rule match score")
    reasons: List[str] = Field(default_factory=list, description="Why this course matches")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional course metadata")

    class Config:
        json_schema_extra = {
            "example": {
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
                    "level": "intermediate"
                }
            }
        }


class CourseRecommenderService:
    """
    Hybrid course recommendation engine.

    Architecture:
    1. Semantic Search: Find courses matching interests/goals (pgvector, top 50)
    2. Reranking: BAAI/bge-reranker-large (rerank to top 20)
    3. Profile Scoring: Rule-based matching (level, format, availability)
    4. Final Ranking: Weighted combination (60% semantic + 40% profile)

    Example:
        recommender = CourseRecommenderService(db)
        recommendations = await recommender.recommend_courses(
            profile=user_profile,
            top_k=10
        )
    """

    def __init__(self, db: Session):
        """
        Initialize course recommender.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.retrieval_service = IntelligentRetrievalService()
        self.reranker = CrossEncoderReranker(model_name="accurate")

        # Scoring weights
        self.semantic_weight = 0.6
        self.profile_weight = 0.4

        logger.info("🎯 CourseRecommenderService initialized")

    async def recommend_courses(
        self,
        profile: UserProfile,
        top_k: int = 10,
        session_id: Optional[str] = None
    ) -> List[CourseRecommendation]:
        """
        Recommend courses using hybrid approach.

        Steps:
        1. Build semantic query from profile
        2. Semantic search with pgvector (top 50)
        3. Rerank with BAAI cross-encoder (top 20)
        4. Profile-based scoring
        5. Weighted combination and final ranking

        Args:
            profile: User profile with skills, interests, goals
            top_k: Number of recommendations to return
            session_id: Optional session ID for filtering

        Returns:
            List of CourseRecommendation sorted by match_score

        Example:
            profile = UserProfile(
                skills=["software engineering"],
                interests=["business English"],
                education_level="intermediate",
                career_goals=["work internationally"],
                preferred_format="online",
                language_proficiency="B1",
                availability="weekends"
            )

            recommendations = await recommender.recommend_courses(profile, top_k=5)
        """
        logger.info(f"🔍 Recommending courses for profile: {len(profile.interests)} interests, "
                   f"{profile.education_level} level, {profile.language_proficiency} CEFR")

        # Step 1: Build semantic query
        query = self._build_query_from_profile(profile)
        logger.info(f"📝 Query built: {query[:100]}...")

        # Step 2: Semantic search with pgvector
        try:
            search_results = await self._semantic_search(
                query=query,
                company="british_council",
                usecase="course_recommendation",
                top_k=min(50, top_k * 5),  # Retrieve 5x for reranking
                session_id=session_id
            )

            logger.info(f"🔎 Semantic search returned {len(search_results)} results")

            if not search_results:
                logger.warning("⚠️ No courses found in semantic search")
                return []

            # Step 3: Rerank with cross-encoder
            reranked_results = await self._rerank_results(
                query=query,
                results=search_results,
                top_k=min(20, len(search_results))
            )

            logger.info(f"🏆 Reranked to top {len(reranked_results)} courses")

            # Step 4 & 5: Profile scoring + final ranking
            recommendations = await self._create_recommendations(
                profile=profile,
                reranked_results=reranked_results,
                top_k=top_k
            )

            logger.info(f"✅ Returning {len(recommendations)} course recommendations")
            return recommendations

        except Exception as e:
            logger.error(f"❌ Course recommendation failed: {e}")
            raise

    def _build_query_from_profile(self, profile: UserProfile) -> str:
        """
        Convert user profile to semantic search query.

        Args:
            profile: UserProfile object

        Returns:
            Formatted query string
        """
        parts = []

        # Add interests (primary signal)
        if profile.interests:
            parts.extend(profile.interests)

        # Add career goals
        if profile.career_goals:
            parts.extend(profile.career_goals)

        # Add education level context
        parts.append(f"{profile.education_level} level English")

        # Add CEFR level
        parts.append(f"{profile.language_proficiency} proficiency")

        # Add skills (secondary signal)
        if profile.skills:
            parts.append(f"relevant to {', '.join(profile.skills[:3])}")

        query = " ".join(parts)
        return query

    async def _direct_vector_search(
        self,
        query: str,
        company: str,
        usecase: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Direct vector similarity search bypassing IntelligentRetrievalService.

        This method performs a simple, direct pgvector similarity search without
        LLM-based query classification. It's more predictable and avoids issues
        with LLM classification failures.

        Args:
            query: Search query
            company: Company filter (british_council)
            usecase: Use case filter (course_recommendation)
            top_k: Number of results

        Returns:
            List of chunks with similarity scores
        """
        from app.tier_1.embeddings.embedding_service import EmbeddingService
        from sqlalchemy import select, func, and_, or_, desc

        logger.info(f"🔍 Direct vector search: query='{query[:50]}...', company={company}, usecase={usecase}, top_k={top_k}")

        # Generate embedding for query
        embedding_service = EmbeddingService()
        query_embedding = await embedding_service.get_embedding(query)

        logger.info(f"✅ Generated query embedding: {len(query_embedding)} dimensions")

        # Direct vector similarity query using pgvector <=> operator
        # Note: Document.meta_info is mapped to 'metadata' column in DB (Column('metadata', JSON))
        # Similarity = 1 - cosine_distance (pgvector's <=> operator)
        from sqlalchemy import literal_column, text

        # Convert embedding list to pgvector format
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

        stmt = (
            select(
                DocumentChunk,
                (1 - DocumentChunk.embedding.op('<=>', return_type=Float)(
                    literal_column(f"'{embedding_str}'::vector")
                )).label('similarity')
            )
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(
                and_(
                    DocumentChunk.embedding.isnot(None),
                    # Use ->> operator for JSONB text extraction (not -> which returns JSON)
                    text("documents.metadata->>'company' = :company").bindparams(company=company),
                    text("documents.metadata->>'usecase' = :usecase").bindparams(usecase=usecase)
                )
            )
            .order_by(desc('similarity'))
            .limit(top_k)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        logger.info(f"📊 Direct search found {len(rows)} results")

        # Convert to expected format
        results = []
        for chunk, similarity in rows:
            # Extract metadata from chunk (chunks inherit metadata from documents during ingestion)
            metadata = chunk.meta_info if chunk.meta_info else {}

            results.append({
                "content": chunk.content,
                "metadata": metadata,
                "score": float(similarity),
                "similarity": float(similarity),  # Alias for compatibility
                "chunk_id": str(chunk.id),
                "document_id": str(chunk.document_id)
            })

            logger.debug(f"   Result: score={similarity:.3f}, content={chunk.content[:50]}...")

        logger.info(f"✅ Direct vector search complete: {len(results)} results")
        return results

    async def _semantic_search(
        self,
        query: str,
        company: str,
        usecase: str,
        top_k: int,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for courses using pgvector semantic search.

        Args:
            query: Search query
            company: Company name (british_council)
            usecase: Use case name (course_recommendation)
            top_k: Number of results
            session_id: Optional session filter

        Returns:
            List of search results with chunks and metadata
        """
        # Use direct vector search (bypasses IntelligentRetrievalService)
        # This is simpler and avoids LLM classification issues
        logger.info("🎯 Using direct vector search for British Council")
        results = await self._direct_vector_search(
            query=query,
            company=company,
            usecase=usecase,
            top_k=top_k
        )

        return results

    async def _rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Rerank search results using cross-encoder.

        Args:
            query: Original query
            results: Search results from semantic search
            top_k: Number of results to keep

        Returns:
            Reranked results with updated scores
        """
        if not results:
            return []

        # Rerank with cross-encoder
        # CrossEncoderReranker expects chunks (list of dicts with 'content' field)
        reranked = self.reranker.rerank(
            query=query,
            chunks=results,
            top_k=top_k
        )

        # CrossEncoderReranker returns chunks with 'rerank_score' field already added
        return reranked

    async def _create_recommendations(
        self,
        profile: UserProfile,
        reranked_results: List[Dict[str, Any]],
        top_k: int
    ) -> List[CourseRecommendation]:
        """
        Create final recommendations with profile scoring.

        Args:
            profile: User profile
            reranked_results: Reranked search results
            top_k: Number of recommendations to return

        Returns:
            List of CourseRecommendation objects
        """
        recommendations = []

        for result in reranked_results:
            # Extract metadata
            metadata = result.get("metadata", {})
            semantic_score = result.get("rerank_score", 0.0)  # CrossEncoderReranker uses 'rerank_score'

            # Calculate profile-based score
            profile_score = self._calculate_profile_score(profile, metadata)

            # Weighted combination: 60% semantic + 40% profile
            match_score = (
                self.semantic_weight * semantic_score +
                self.profile_weight * profile_score
            )

            # Generate human-readable reasons
            reasons = self._generate_reasons(profile, metadata, semantic_score, profile_score)

            # Extract course info
            course_id = metadata.get("course_id", metadata.get("document_id", "unknown"))
            course_name = metadata.get("course_name", metadata.get("title", "Untitled Course"))

            recommendation = CourseRecommendation(
                course_id=course_id,
                course_name=course_name,
                description=result.get("content", "")[:500],  # Truncate for display
                match_score=round(match_score, 3),
                semantic_score=round(semantic_score, 3),
                profile_score=round(profile_score, 3),
                reasons=reasons,
                metadata=metadata
            )

            recommendations.append(recommendation)

        # Sort by match score (descending)
        recommendations.sort(key=lambda x: x.match_score, reverse=True)

        # Return top K
        return recommendations[:top_k]

    def _calculate_profile_score(
        self,
        profile: UserProfile,
        metadata: Dict[str, Any]
    ) -> float:
        """
        Calculate rule-based profile match score.

        Scoring breakdown:
        - Education level match: 30%
        - Format match: 20%
        - Availability match: 20%
        - Skill intersection: 30%

        Args:
            profile: User profile
            metadata: Course metadata

        Returns:
            Profile match score (0.0 - 1.0)
        """
        score = 0.0

        # Education level match (0.3)
        course_level = metadata.get("level", "").lower()
        if course_level == profile.education_level.lower():
            score += 0.3
        elif course_level and profile.education_level:
            # Partial credit for adjacent levels
            levels = ["beginner", "intermediate", "advanced"]
            try:
                profile_idx = levels.index(profile.education_level.lower())
                course_idx = levels.index(course_level)
                if abs(profile_idx - course_idx) == 1:
                    score += 0.15  # Half credit for adjacent level
            except ValueError:
                pass

        # Format match (0.2)
        course_format = metadata.get("format", "").lower()
        if course_format == profile.preferred_format.lower():
            score += 0.2
        elif course_format == "hybrid" or profile.preferred_format == "hybrid":
            score += 0.1  # Half credit for hybrid (flexible)

        # Availability match (0.2)
        course_schedule = metadata.get("schedule", "").lower()
        if profile.availability:
            if course_schedule == profile.availability.lower():
                score += 0.2
            elif course_schedule == "flexible" or profile.availability == "flexible":
                score += 0.1  # Half credit for flexible

        # Skill intersection (0.3)
        course_skills = set(s.lower() for s in metadata.get("skills", []))
        user_skills = set(s.lower() for s in profile.skills)
        user_interests = set(i.lower() for i in profile.interests)

        # Match skills or interests
        matching_skills = course_skills.intersection(user_skills)
        matching_interests = course_skills.intersection(user_interests)

        if matching_skills or matching_interests:
            overlap_count = len(matching_skills) + len(matching_interests)
            total_user = len(user_skills) + len(user_interests)
            if total_user > 0:
                overlap_ratio = min(overlap_count / total_user, 1.0)
                score += 0.3 * overlap_ratio

        return min(score, 1.0)  # Cap at 1.0

    def _generate_reasons(
        self,
        profile: UserProfile,
        metadata: Dict[str, Any],
        semantic_score: float,
        profile_score: float
    ) -> List[str]:
        """
        Generate human-readable reasons for recommendation.

        Args:
            profile: User profile
            metadata: Course metadata
            semantic_score: Semantic similarity score
            profile_score: Profile match score

        Returns:
            List of reason strings
        """
        reasons = []

        # High semantic match
        if semantic_score >= 0.8:
            reasons.append("Highly relevant to your interests and goals")

        # Education level match
        if metadata.get("level", "").lower() == profile.education_level.lower():
            reasons.append(f"Matches your {profile.education_level} level")

        # Format match
        if metadata.get("format", "").lower() == profile.preferred_format.lower():
            reasons.append(f"Available in {profile.preferred_format} format")

        # Availability match
        if metadata.get("schedule", "").lower() == profile.availability:
            reasons.append(f"{profile.availability.capitalize()} schedule available")

        # Skill/interest match
        course_skills = set(s.lower() for s in metadata.get("skills", []))
        user_skills = set(s.lower() for s in profile.skills)
        user_interests = set(i.lower() for i in profile.interests)

        matching = (course_skills.intersection(user_skills) |
                   course_skills.intersection(user_interests))

        if matching:
            matching_list = list(matching)[:3]  # Show max 3
            reasons.append(f"Covers: {', '.join(matching_list)}")

        # Language proficiency match
        course_cefr = metadata.get("cefr_level", "").upper()
        if course_cefr == profile.language_proficiency.upper():
            reasons.append(f"Designed for {profile.language_proficiency} proficiency")

        # Default if no specific reasons
        if not reasons:
            reasons.append("Good overall match for your profile")

        return reasons


# Factory function
def get_course_recommender(db: Session) -> CourseRecommenderService:
    """
    Get CourseRecommenderService instance.

    Args:
        db: Database session

    Returns:
        CourseRecommenderService instance
    """
    return CourseRecommenderService(db)
