"""
Taxonomy Skillmatch Schemas
Tier 2 Module: HR & Talent

Pydantic models for skill taxonomy mapping and matching.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class SkillCategory(str, Enum):
    """Skill taxonomy categories"""
    TECHNICAL = "technical"
    SOFT_SKILLS = "soft_skills"
    LEADERSHIP = "leadership"
    DOMAIN_KNOWLEDGE = "domain_knowledge"
    TOOLS_PLATFORMS = "tools_platforms"
    LANGUAGES = "languages"
    CERTIFICATIONS = "certifications"
    METHODOLOGIES = "methodologies"


class SkillLevel(str, Enum):
    """Skill proficiency levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class TaxonomyNode(BaseModel):
    """Node in skill taxonomy tree"""
    skill_name: str
    category: SkillCategory
    parent_skill: Optional[str] = None
    child_skills: List[str] = Field(default_factory=list)
    synonyms: List[str] = Field(default_factory=list)
    related_skills: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class SkillMapping(BaseModel):
    """Map a skill to taxonomy"""
    input_skill: str
    mapped_skill: str
    category: SkillCategory
    confidence_score: float = Field(..., ge=0.0, le=100.0)
    synonyms_found: List[str] = Field(default_factory=list)
    related_skills: List[str] = Field(default_factory=list)


class SkillSet(BaseModel):
    """Collection of skills with proficiency levels"""
    skills: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of {skill_name, proficiency, years_exp}"
    )
    total_skills: int = 0


class SkillGap(BaseModel):
    """Identified skill gap"""
    missing_skill: str
    category: SkillCategory
    importance: str = Field(..., pattern="^(critical|high|medium|low)$")
    suggested_learning_path: Optional[List[str]] = None
    estimated_learning_time_weeks: Optional[int] = None


class SkillMatchResult(BaseModel):
    """Result of skill matching"""
    source_skillset: SkillSet
    target_skillset: SkillSet
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    skill_gaps: List[SkillGap] = Field(default_factory=list)
    match_percentage: float = Field(..., ge=0.0, le=100.0)
    category_breakdown: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class SkillTaxonomyRequest(BaseModel):
    """Request to map skills to taxonomy"""
    skills: List[str] = Field(..., description="List of skill names to map")
    use_llm_mapping: bool = Field(True, description="Use LLM for fuzzy matching")
    include_related_skills: bool = Field(True, description="Include related skills in response")
    session_id: Optional[str] = None
    project_id: Optional[str] = None


class SkillTaxonomyResponse(BaseModel):
    """Response with mapped skills"""
    mappings: List[SkillMapping]
    unmapped_skills: List[str] = Field(default_factory=list)
    total_skills_processed: int
    taxonomy_coverage_percent: float


class SkillMatchRequest(BaseModel):
    """Request to match two skill sets"""
    source_skills: List[Dict[str, Any]] = Field(
        ...,
        description="Source skillset (candidate skills)"
    )
    target_skills: List[Dict[str, Any]] = Field(
        ...,
        description="Target skillset (required skills)"
    )
    identify_gaps: bool = Field(True, description="Identify and analyze skill gaps")
    suggest_learning_paths: bool = Field(False, description="Suggest learning paths for gaps")
    session_id: Optional[str] = None
    project_id: Optional[str] = None


class SkillMatchResponse(BaseModel):
    """Response with skill matching results"""
    match_result: SkillMatchResult
    recommendations: List[str] = Field(default_factory=list)
    match_quality: str = Field(..., description="excellent, good, fair, poor")


class SearchTaxonomyRequest(BaseModel):
    """Search skill taxonomy mappings"""
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    skill_name: Optional[str] = None
    category: Optional[SkillCategory] = None
    limit: int = Field(20, ge=1, le=100)


class ExportTaxonomyRequest(BaseModel):
    """Export skill taxonomy data"""
    mapping_ids: Optional[List[str]] = None
    session_id: Optional[str] = None
    category: Optional[SkillCategory] = None
    format: str = Field("json", pattern="^(json|csv|excel)$")


class TaxonomyStatsResponse(BaseModel):
    """Skill taxonomy statistics"""
    total_skills_in_taxonomy: int
    total_categories: int
    total_mappings_performed: int
    avg_confidence_score: float
    top_mapped_skills: List[Dict[str, Any]] = Field(default_factory=list)
    category_distribution: Dict[str, int] = Field(default_factory=dict)
