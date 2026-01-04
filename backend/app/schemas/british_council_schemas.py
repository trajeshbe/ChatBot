"""
British Council Schemas

Pydantic models for British Council course recommendation system.

Author: Claude Code
Date: 2026-01-04
"""

from typing import Optional, List
from pydantic import BaseModel, Field


# ============================================================================
# Request Schemas
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


class CourseRecommendRequest(BaseModel):
    """Request for course recommendations."""
    profile: Optional[dict] = Field(
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


# ============================================================================
# Response Schemas
# ============================================================================

class UserProfile(BaseModel):
    """Extracted user profile."""
    english_level: str = Field(
        description="English level (A1, A2, B1, B2, C1, C2)"
    )
    learning_goals: List[str] = Field(
        description="User's learning goals"
    )
    interests: List[str] = Field(
        description="User's interests and focus areas"
    )
    preferred_schedule: Optional[str] = Field(
        default=None,
        description="Preferred study schedule"
    )
    budget_range: Optional[str] = Field(
        default=None,
        description="Budget range"
    )
    study_mode_preference: Optional[str] = Field(
        default=None,
        description="Preferred study mode (online, in-person, hybrid)"
    )


class CourseRecommendation(BaseModel):
    """Single course recommendation."""
    course_title: str
    course_level: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    match_reasons: List[str]
    description: Optional[str] = None
    duration: Optional[str] = None
    price: Optional[str] = None
    delivery_mode: Optional[str] = None


class ProfileAnalyzeResponse(BaseModel):
    """Response with extracted user profile."""
    profile: UserProfile
    status: str = "success"


class CourseRecommendResponse(BaseModel):
    """Response with course recommendations."""
    recommendations: List[CourseRecommendation]
    profile: UserProfile
    total_courses_analyzed: int
    status: str = "success"


# ============================================================================
# Health Check Schema
# ============================================================================

class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    service: str = "British Council"
    version: str = "1.0.0"
