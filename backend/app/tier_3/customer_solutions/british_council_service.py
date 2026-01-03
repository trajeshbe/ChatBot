"""British Council POC - Enhanced Business Logic Service with Profile Analysis and Course Matching"""
import logging
import json
from sqlalchemy.orm import Session
from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService, get_llm_service
from app.tier_1.rag.intelligent_retrieval_service import IntelligentRetrievalService
from app.tier_1.embeddings.reranker_service import CrossEncoderReranker, get_reranker
from .british_council_schemas import *

logger = logging.getLogger(__name__)

class ProfileAnalyzer:
    """Extracts structured user profiles from natural language using LLM"""

    def __init__(self, llm_service: LLMService = None):
        self.llm = llm_service or get_llm_service()

    async def analyze_profile(self, user_input: str) -> UserProfile:
        """Extract structured profile from free-text user input"""
        try:
            prompt = f"""Extract a structured user profile from this text. Return ONLY valid JSON with these exact fields:
{{
  "skills": ["list", "of", "skills"],
  "interests": ["list", "of", "interests"],
  "education_level": "beginner|intermediate|advanced",
  "career_goals": ["list", "of", "goals"],
  "preferred_format": "online|in-person|hybrid|flexible",
  "language_proficiency": "A1|A2|B1|B2|C1|C2",
  "availability": "weekdays|weekends|flexible"
}}

Text: "{user_input}"

Return only the JSON, no other text."""

            response = await self.llm.generate_response(prompt, model="gpt-4o-mini", temperature=0.0, max_tokens=500)

            # Parse JSON response
            profile_data = json.loads(response)
            profile = UserProfile(**profile_data)
            logger.info(f"📋 Extracted profile: {profile.education_level} level, {profile.language_proficiency} CEFR")
            return profile

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error, using defaults: {e}")
            return UserProfile()
        except Exception as e:
            logger.error(f"Profile analysis error: {e}", exc_info=True)
            return UserProfile()


class CourseRecommender:
    """Hybrid recommendation system combining semantic search and profile matching"""

    def __init__(self, db: Session):
        self.db = db
        self.retrieval = IntelligentRetrievalService()
        self.reranker = get_reranker()
        self.semantic_weight = 0.6
        self.profile_weight = 0.4

    async def recommend_courses(self, profile: UserProfile, top_k: int = 5) -> List[CourseRecommendation]:
        """Generate hybrid course recommendations"""
        try:
            # Build semantic query
            query = self._build_query_from_profile(profile)
            logger.info(f"🔍 Query: {query}")

            # Semantic search (top 10)
            results = await self.retrieval.intelligent_search(
                query_text=query,
                company="british_council",
                usecase="course_recommendation",
                top_k=10,
                db=self.db
            )

            if not results:
                logger.warning("⚠️ No courses found in vector store")
                return []

            # Rerank
            reranked = await self.reranker.rerank(query, results, top_k=top_k)

            # Generate recommendations
            recommendations = []
            for idx, item in enumerate(reranked[:top_k]):
                metadata = item.get("metadata", {})
                semantic_score = item.get("score", 0.5)
                profile_score = self._calculate_profile_score(profile, metadata)
                match_score = (self.semantic_weight * semantic_score) + (self.profile_weight * profile_score)

                recommendation = CourseRecommendation(
                    course_id=metadata.get("course_id", f"course-{idx}"),
                    course_name=metadata.get("course_name", "Course Name"),
                    description=item.get("content", ""),
                    match_score=match_score,
                    semantic_score=semantic_score,
                    profile_score=profile_score,
                    reasons=self._generate_reasons(profile, metadata, match_score),
                    metadata=metadata
                )
                recommendations.append(recommendation)

            return recommendations

        except Exception as e:
            logger.error(f"Course recommendation error: {e}", exc_info=True)
            return []

    def _build_query_from_profile(self, profile: UserProfile) -> str:
        """Build semantic search query"""
        parts = []
        if profile.skills:
            parts.append(f"Skills: {', '.join(profile.skills[:3])}")
        if profile.interests:
            parts.append(f"Interests: {', '.join(profile.interests[:3])}")
        parts.append(f"Level: {profile.education_level}")
        parts.append(f"CEFR: {profile.language_proficiency}")
        return " | ".join(parts)

    def _calculate_profile_score(self, profile: UserProfile, metadata: Dict) -> float:
        """Calculate profile-based match score"""
        score = 0.0

        # Education level match (30%)
        if metadata.get("level", "").lower() == profile.education_level.lower():
            score += 0.3

        # Format match (20%)
        if metadata.get("format", "").lower() == profile.preferred_format.lower():
            score += 0.2

        # Availability match (20%)
        if metadata.get("schedule", "").lower() == profile.availability.lower():
            score += 0.2

        # Skill intersection (30%)
        course_skills = set(metadata.get("skills", []))
        if course_skills.intersection(set(profile.skills)):
            score += 0.3

        return min(score, 1.0)

    def _generate_reasons(self, profile: UserProfile, metadata: Dict, match_score: float) -> List[str]:
        """Generate explanation for match"""
        reasons = []
        if match_score >= 0.8:
            reasons.append(f"Excellent match for your {profile.education_level} level")
        if metadata.get("format") == profile.preferred_format:
            reasons.append(f"Available in {profile.preferred_format} format")
        if profile.career_goals:
            reasons.append(f"Aligned with your career goals")
        return reasons or ["Good general match"]


class British_councilService:
    """Enhanced British Council POC - AI-powered course recommendations"""

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.profile_analyzer = ProfileAnalyzer()
        self.course_recommender = CourseRecommender(db)
        self.llm = get_llm_service()

    async def process_request(self, request: British_councilRequest) -> British_councilResponse:
        """Process course recommendation request"""
        try:
            logger.info(f"🎓 British Council request: {request.query[:100]}")

            # Step 1: Analyze user profile from query
            profile = await self.profile_analyzer.analyze_profile(request.query)

            # Step 2: Get course recommendations
            recommendations = await self.course_recommender.recommend_courses(profile, top_k=5)

            # Step 3: Generate insights
            if recommendations:
                top_match = recommendations[0]
                insights = f"Found {len(recommendations)} courses. Top match: {top_match.course_name} ({int(top_match.match_score*100)}% match). Profile: {profile.education_level} level, {profile.language_proficiency} CEFR."

                recommendation_list = [
                    f"{rec.course_name} ({int(rec.match_score*100)}% match)"
                    for rec in recommendations[:3]
                ]
            else:
                insights = f"Profile analyzed: {profile.education_level} level, {profile.language_proficiency} CEFR. No courses found in database yet."
                recommendation_list = ["Upload course catalog documents to enable recommendations"]

            return British_councilResponse(
                success=True,
                session_id=request.session_id,
                result={
                    "profile": profile.dict(),
                    "courses": [rec.dict() for rec in recommendations],
                    "total_analyzed": len(recommendations)
                },
                insights=insights,
                recommendations=recommendation_list
            )

        except Exception as e:
            logger.error(f"British Council POC error: {e}", exc_info=True)
            return British_councilResponse(
                success=False,
                session_id=request.session_id,
                result={"error": str(e)},
                insights=f"Error processing request: {str(e)}",
                recommendations=["Please try again or contact support"]
            )

    async def get_status(self) -> StatusResponse:
        """Get POC status and integrated modules"""
        return StatusResponse(
            success=True,
            status="operational",
            description="AI-powered course recommendations with hybrid RAG (60% semantic + 40% profile matching)",
            tier_2_modules_used=[
                "intelligent-retrieval (pgvector)",
                "reranker (BAAI/bge-reranker-large)",
                "llm-service (GPT-4o-mini)"
            ],
            capabilities=[
                "LLM-based profile extraction from natural language",
                "Semantic search with BAAI/bge-large-en-v1.5 embeddings",
                "Cross-encoder reranking for precision",
                "Hybrid scoring (semantic + profile attributes)",
                "CEFR level matching (A1-C2)",
                "MinIO path: british_council/course_recommendation/{doc_id}"
            ]
        )
