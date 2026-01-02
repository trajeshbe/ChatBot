"""
Talent Search Schemas
Tier 2 Module: HR & Talent

Pydantic models for AI-powered talent search and matching.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class ExperienceLevel(str, Enum):
    """Experience level categories"""
    ENTRY_LEVEL = "entry_level"
    MID_LEVEL = "mid_level"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"
    EXECUTIVE = "executive"


class EmploymentType(str, Enum):
    """Employment type preferences"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"


class SkillProficiency(str, Enum):
    """Skill proficiency levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Skill(BaseModel):
    """Individual skill with proficiency"""
    name: str = Field(..., description="Skill name (e.g., 'Python', 'Leadership')")
    proficiency: SkillProficiency = Field(default=SkillProficiency.INTERMEDIATE)
    years_of_experience: Optional[float] = Field(None, ge=0.0, description="Years of experience with this skill")
    required: bool = Field(default=False, description="Whether this skill is required vs. nice-to-have")


class Education(BaseModel):
    """Education requirement or credential"""
    degree: str = Field(..., description="Degree type (e.g., 'Bachelor', 'Master', 'PhD')")
    field: Optional[str] = Field(None, description="Field of study (e.g., 'Computer Science', 'Business')")
    required: bool = Field(default=False)


class CandidateProfile(BaseModel):
    """Candidate profile for matching"""
    candidate_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    skills: List[Skill] = Field(default_factory=list)
    years_of_experience: float = Field(..., ge=0.0)
    experience_level: ExperienceLevel
    education: List[Education] = Field(default_factory=list)
    current_role: Optional[str] = None
    location: Optional[str] = None
    expected_salary: Optional[float] = Field(None, ge=0.0)
    availability: Optional[str] = None
    resume_text: Optional[str] = Field(None, description="Full resume text for semantic search")


class JobRequirement(BaseModel):
    """Job requirements for talent search"""
    job_id: str
    job_title: str
    department: Optional[str] = None
    experience_level: ExperienceLevel
    required_skills: List[Skill] = Field(default_factory=list)
    preferred_skills: List[Skill] = Field(default_factory=list)
    education_requirements: List[Education] = Field(default_factory=list)
    years_of_experience_min: float = Field(0.0, ge=0.0)
    years_of_experience_max: Optional[float] = Field(None, ge=0.0)
    employment_type: EmploymentType
    location: Optional[str] = None
    salary_range_min: Optional[float] = Field(None, ge=0.0)
    salary_range_max: Optional[float] = Field(None, ge=0.0)
    job_description: Optional[str] = Field(None, description="Full job description for semantic matching")


class MatchScore(BaseModel):
    """Detailed match score breakdown"""
    overall_score: float = Field(..., ge=0.0, le=100.0)
    skills_match_score: float = Field(..., ge=0.0, le=100.0)
    experience_match_score: float = Field(..., ge=0.0, le=100.0)
    education_match_score: float = Field(..., ge=0.0, le=100.0)
    location_match_score: float = Field(..., ge=0.0, le=100.0)
    salary_match_score: float = Field(..., ge=0.0, le=100.0)
    semantic_similarity_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Resume-to-JD semantic similarity")


class TalentMatch(BaseModel):
    """Candidate-to-job match result"""
    candidate: CandidateProfile
    match_score: MatchScore
    matched_skills: List[str] = Field(default_factory=list, description="Skills that match job requirements")
    missing_skills: List[str] = Field(default_factory=list, description="Required skills candidate lacks")
    strengths: List[str] = Field(default_factory=list, description="Candidate strengths for this role")
    gaps: List[str] = Field(default_factory=list, description="Areas where candidate may need development")
    recommendation: str = Field(..., description="AI-generated recommendation summary")
    rank: int = Field(..., ge=1, description="Ranking among all matched candidates")


class TalentSearchRequest(BaseModel):
    """Request to search for talent matching job requirements"""
    job_requirement: JobRequirement
    candidate_pool: Optional[List[CandidateProfile]] = Field(None, description="Specific candidates to evaluate (optional)")
    top_n: int = Field(10, ge=1, le=100, description="Return top N matches")
    min_score_threshold: float = Field(50.0, ge=0.0, le=100.0, description="Minimum match score to include")
    use_semantic_matching: bool = Field(True, description="Use LLM for semantic resume-JD matching")
    weights: Optional[Dict[str, float]] = Field(
        None,
        description="Custom weights for scoring components (skills, experience, education, location, salary)"
    )
    session_id: Optional[str] = None
    project_id: Optional[str] = None


class TalentSearchResponse(BaseModel):
    """Response with matched candidates"""
    job_requirement: JobRequirement
    matches: List[TalentMatch]
    total_candidates_evaluated: int
    total_matches_found: int
    search_metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchTalentMatchesRequest(BaseModel):
    """Search historical talent matches"""
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    job_id: Optional[str] = None
    candidate_id: Optional[str] = None
    min_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    limit: int = Field(20, ge=1, le=100)


class ExportTalentMatchesRequest(BaseModel):
    """Export talent matches"""
    match_ids: Optional[List[str]] = None
    session_id: Optional[str] = None
    job_id: Optional[str] = None
    format: str = Field("json", pattern="^(json|csv|excel|pdf)$")


class TalentSearchStatsResponse(BaseModel):
    """Talent search statistics"""
    total_searches_performed: int
    total_candidates_matched: int
    avg_match_score: float
    avg_matches_per_search: float
    top_matched_skills: List[Dict[str, Any]] = Field(default_factory=list)
    top_job_titles: List[Dict[str, Any]] = Field(default_factory=list)
