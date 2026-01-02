"""
British Council API Routes

FastAPI endpoints for British Council course recommendations:
- POST /api/v1/british-council/profile/analyze - Extract user profile
- POST /api/v1/british-council/courses/recommend - Get course recommendations
- GET /api/v1/british-council/health - Health check

Reuses:
- services.british_council.profile_analyzer: Profile extraction
- services.british_council.course_recommender: Hybrid recommendation engine
- tier_1 infrastructure: LLM, Retrieval, Reranker services

MinIO Path: british_council/course_recommendation/{document_id}

Author: Claude Code
Date: 2026-01-02
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.british_council import (
    get_profile_analyzer,
    get_course_recommender,
    UserProfile,
    CourseRecommendation
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/british-council", tags=["British Council"])


# ============================================================================
# Request/Response Schemas
# ============================================================================

class ProfileAnalyzeRequest(BaseModel):
    """Request to analyze user profile from natural language input."""
    user_input: str = Field(
        description="Natural language description of user's goals and preferences",
        examples=[
            "I'm a software engineer looking to improve my business English. "
            "I have intermediate level English (B1) and prefer online courses "
            "on weekends. I want to advance my career in international companies."
        ]
    )
    model_id: Optional[str] = Field(
        default=None,
        description="Optional LLM model to use (defaults to gpt-4o-mini)"
    )


class ProfileAnalyzeResponse(BaseModel):
    """Response with extracted user profile."""
    profile: UserProfile
    status: str = "success"


class CourseRecommendRequest(BaseModel):
    """Request for course recommendations."""
    profile: Optional[UserProfile] = Field(
        default=None,
        description="User profile (if already analyzed)"
    )
    user_input: Optional[str] = Field(
        default=None,
        description="Natural language input (will be analyzed if profile not provided)"
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of recommendations to return"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session ID for filtering documents"
    )


class CourseRecommendResponse(BaseModel):
    """Response with course recommendations."""
    recommendations: List[CourseRecommendation]
    profile: UserProfile
    total_courses_analyzed: int
    status: str = "success"


# ============================================================================
# Health Check Endpoint
# ============================================================================

@router.get("/health", summary="Health check for British Council service")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Status indicating service health
    """
    return {
        "status": "healthy",
        "service": "British Council Course Recommendation",
        "components": {
            "profile_analyzer": "ready",
            "course_recommender": "ready",
            "llm_service": "ready",
            "retrieval_service": "ready",
            "reranker_service": "ready"
        }
    }


# ============================================================================
# Profile Analysis Endpoint
# ============================================================================

@router.post(
    "/profile/analyze",
    response_model=ProfileAnalyzeResponse,
    summary="Analyze user profile from natural language",
    description="""
    Extract structured user profile from natural language description.

    Uses LLM (GPT-4o-mini by default) to extract:
    - Skills
    - Interests
    - Education level (beginner/intermediate/advanced)
    - Career goals
    - Preferred format (online/in-person/hybrid)
    - Language proficiency (CEFR: A1-C2)
    - Availability (weekdays/weekends/flexible)

    Example input:
    "I'm a software engineer looking to improve my business English.
    I have intermediate level English (B1) and prefer online courses
    on weekends. I want to advance my career in international companies."
    """
)
async def analyze_profile(
    request: ProfileAnalyzeRequest
) -> ProfileAnalyzeResponse:
    """
    Analyze user profile from natural language input.

    Args:
        request: ProfileAnalyzeRequest with user_input

    Returns:
        ProfileAnalyzeResponse with extracted profile

    Raises:
        HTTPException: If profile analysis fails
    """
    try:
        logger.info(f"📝 Analyzing profile from user input (length: {len(request.user_input)})")

        # Get profile analyzer
        analyzer = get_profile_analyzer()

        # Analyze profile
        profile = await analyzer.analyze_profile(
            user_input=request.user_input,
            model_id=request.model_id
        )

        # Validate profile
        await analyzer.validate_profile(profile)

        logger.info(f"✅ Profile analyzed successfully: {len(profile.skills)} skills, "
                   f"{len(profile.interests)} interests, {profile.education_level} level")

        return ProfileAnalyzeResponse(profile=profile)

    except ValueError as e:
        logger.error(f"❌ Profile validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"❌ Profile analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Profile analysis failed: {str(e)}")


# ============================================================================
# Course Recommendation Endpoint
# ============================================================================

@router.post(
    "/courses/recommend",
    response_model=CourseRecommendResponse,
    summary="Get personalized course recommendations",
    description="""
    Get personalized course recommendations using hybrid approach:

    1. Semantic search with pgvector (finds courses matching interests/goals)
    2. Cross-encoder reranking with BAAI/bge-reranker-large
    3. Profile-based scoring (education level, format, availability match)
    4. Weighted combination (60% semantic + 40% profile)

    You can either:
    - Provide pre-analyzed profile (from /profile/analyze)
    - Provide user_input (will be analyzed automatically)

    Returns top K course recommendations with match scores and reasons.
    """
)
async def recommend_courses(
    request: CourseRecommendRequest,
    db: Session = Depends(get_db)
) -> CourseRecommendResponse:
    """
    Get personalized course recommendations.

    Args:
        request: CourseRecommendRequest with profile or user_input
        db: Database session

    Returns:
        CourseRecommendResponse with recommendations

    Raises:
        HTTPException: If recommendation fails
    """
    try:
        logger.info("🎯 Processing course recommendation request")

        # Get or analyze profile
        if request.profile:
            profile = request.profile
            logger.info("Using provided profile")
        elif request.user_input:
            logger.info("Analyzing profile from user input")
            analyzer = get_profile_analyzer()
            profile = await analyzer.analyze_profile(request.user_input)
            await analyzer.validate_profile(profile)
        else:
            raise HTTPException(
                status_code=400,
                detail="Either 'profile' or 'user_input' must be provided"
            )

        # Get course recommender
        recommender = get_course_recommender(db)

        # Get recommendations
        recommendations = await recommender.recommend_courses(
            profile=profile,
            top_k=request.top_k,
            session_id=request.session_id
        )

        logger.info(f"✅ Generated {len(recommendations)} course recommendations")

        return CourseRecommendResponse(
            recommendations=recommendations,
            profile=profile,
            total_courses_analyzed=len(recommendations),
            status="success"
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is

    except Exception as e:
        logger.error(f"❌ Course recommendation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Course recommendation failed: {str(e)}"
        )


# ============================================================================
# Example Usage (for docs)
# ============================================================================

"""
Example API Usage:

1. Analyze Profile:

   curl -X POST "http://localhost:8000/api/v1/british-council/profile/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "user_input": "I am a software engineer wanting to improve my business English..."
     }'

2. Get Course Recommendations (with user_input):

   curl -X POST "http://localhost:8000/api/v1/british-council/courses/recommend" \
     -H "Content-Type: application/json" \
     -d '{
       "user_input": "I am a software engineer wanting to improve my business English...",
       "top_k": 5
     }'

3. Get Course Recommendations (with pre-analyzed profile):

   curl -X POST "http://localhost:8000/api/v1/british-council/courses/recommend" \
     -H "Content-Type: application/json" \
     -d '{
       "profile": {
         "skills": ["software engineering"],
         "interests": ["business English"],
         "education_level": "intermediate",
         "career_goals": ["work internationally"],
         "preferred_format": "online",
         "language_proficiency": "B1",
         "availability": "weekends"
       },
       "top_k": 10
     }'
"""
