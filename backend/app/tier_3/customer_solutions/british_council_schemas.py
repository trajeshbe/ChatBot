"""British Council POC - Data Schemas"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum

class British_councilRequest(BaseModel):
    session_id: str
    query: str = Field(..., min_length=1, max_length=5000)
    context: Optional[Dict] = None

class British_councilResponse(BaseModel):
    success: bool
    session_id: str
    result: Dict
    insights: str
    recommendations: List[str]

class StatusResponse(BaseModel):
    success: bool
    status: str
    description: str
    tier_2_modules_used: List[str]
    capabilities: Optional[List[str]] = None

# Extended schemas for detailed British Council functionality
class UserProfile(BaseModel):
    """Structured user profile for course matching"""
    skills: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    education_level: str = Field(default="intermediate")
    career_goals: List[str] = Field(default_factory=list)
    preferred_format: str = Field(default="online")
    language_proficiency: str = Field(default="B1")  # CEFR: A1, A2, B1, B2, C1, C2
    availability: Optional[str] = Field(default="flexible")

class CourseRecommendation(BaseModel):
    """Single course recommendation"""
    course_id: str
    course_name: str
    description: str
    match_score: float
    semantic_score: float
    profile_score: float
    reasons: List[str]
    metadata: Dict
