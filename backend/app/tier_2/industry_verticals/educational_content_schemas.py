"""Educational Content Recommender - Data Schemas"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum

class ContentType(str, Enum):
    VIDEO = "video"
    ARTICLE = "article"
    COURSE = "course"
    QUIZ = "quiz"

class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class RecommendContentRequest(BaseModel):
    student_id: str
    subject: str
    current_skill_level: SkillLevel
    learning_goals: List[str]
    max_recommendations: int = Field(default=10, ge=1, le=50)

class ContentRecommendation(BaseModel):
    content_id: str
    title: str
    content_type: ContentType
    relevance_score: float = Field(..., ge=0.0, le=100.0)
    estimated_duration_minutes: int
    difficulty_match: float

class RecommendContentResponse(BaseModel):
    success: bool
    student_id: str
    recommendations: List[ContentRecommendation]
    learning_path_insights: str
    ai_insights: str

class SearchRecommendationsRequest(BaseModel):
    student_ids: Optional[List[str]] = None
    limit: int = Field(default=100, ge=1, le=1000)

class SearchRecommendationsResponse(BaseModel):
    success: bool
    recommendations: List[Dict]
    total_count: int

class ExportRecommendationsRequest(BaseModel):
    student_ids: List[str]
    format: str = Field(default="pdf", pattern="^(pdf|csv|json)$")

class ExportRecommendationsResponse(BaseModel):
    success: bool
    export_data: Dict
    format: str

class EducationalStatsResponse(BaseModel):
    success: bool
    total_recommendations: int
    most_popular_subject: str

class StatusResponse(BaseModel):
    success: bool
    status: str
    capabilities: List[str]
