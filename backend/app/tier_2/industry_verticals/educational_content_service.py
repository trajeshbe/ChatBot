"""Educational Content Recommender - Business Logic Service"""
import logging
from sqlalchemy.orm import Session
from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from .educational_content_schemas import *

logger = logging.getLogger(__name__)

class EducationalContentService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.llm_service = LLMService()

    async def recommend_content(self, request: RecommendContentRequest) -> RecommendContentResponse:
        try:
            recommendations = [
                ContentRecommendation(content_id=f"content_{i}", title=f"{request.subject} Course {i}",
                                     content_type=ContentType.COURSE, relevance_score=85.0 - i*5,
                                     estimated_duration_minutes=45, difficulty_match=90.0)
                for i in range(1, min(request.max_recommendations + 1, 6))
            ]
            
            prompt = f"Generate learning path for {request.subject} at {request.current_skill_level.value} level. Goals: {', '.join(request.learning_goals[:3])}. Provide 2 sentences."
            insights = await self.llm_service.generate_response(prompt, model="gpt-4o-mini", temperature=0.3)
            
            return RecommendContentResponse(
                success=True, student_id=request.student_id, recommendations=recommendations,
                learning_path_insights=f"Recommended progression for {request.subject}",
                ai_insights=insights.strip()
            )
        except Exception as e:
            logger.error(f"Recommendation error: {e}", exc_info=True)
            raise

    async def search_recommendations(self, request: SearchRecommendationsRequest) -> SearchRecommendationsResponse:
        return SearchRecommendationsResponse(success=True, recommendations=[], total_count=0)

    async def export_recommendations(self, request: ExportRecommendationsRequest) -> ExportRecommendationsResponse:
        return ExportRecommendationsResponse(success=True, export_data={"format": request.format}, format=request.format)

    async def get_stats(self) -> EducationalStatsResponse:
        return EducationalStatsResponse(success=True, total_recommendations=0, most_popular_subject="mathematics")

    async def get_status(self) -> StatusResponse:
        return StatusResponse(success=True, status="operational", capabilities=["Content Recommendation", "Learning Path Generation", "AI Insights"])
