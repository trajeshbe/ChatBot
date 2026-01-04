"""
Talent Search Service
Tier 2 Module: HR & Talent

AI-powered talent search and candidate-to-job matching service.
Leverages Tier 1 LLMService for semantic matching.
"""

import logging
import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from .talent_search_schemas import (
    TalentSearchRequest,
    TalentSearchResponse,
    JobRequirement,
    CandidateProfile,
    TalentMatch,
    MatchScore,
    ExperienceLevel,
    Skill
)

logger = logging.getLogger(__name__)


class TalentSearchService:
    """Service for AI-powered talent search and matching"""

    def __init__(self, db: Session, settings: Settings, config: Optional[Dict[str, Any]] = None):
        self.db = db
        self.settings = settings
        self.config = config or {}
        # Tier 1 service dependencies
        self.llm_service = LLMService()

        # Import DocumentService for extracting candidate profiles
        from app.tier_1.document_processing.document_service import DocumentService
        self.document_service = DocumentService(db, settings)

        logger.info("✓ TalentSearchService initialized with tier_1 services")
        if config:
            logger.info(f"✓ Using module config with model: {config.get(\'llm\', {}).get(\'default\', {}).get(\'model\', \'default\')}")

    async def search_talent(self, request: TalentSearchRequest) -> TalentSearchResponse:
        """
        Search for talent matching job requirements.

        Performs multi-dimensional matching:
        1. Skills matching (required vs. preferred)
        2. Experience level and years matching
        3. Education matching
        4. Location compatibility
        5. Salary alignment
        6. Semantic resume-to-JD matching (optional)
        """
        logger.info(f"🔍 Talent search for job: {request.job_requirement.job_title}")

        # Get candidate pool (use provided or fetch from documents)
        candidates = request.candidate_pool if request.candidate_pool else await self._get_candidate_pool(session_id=request.session_id)

        logger.info(f"Evaluating {len(candidates)} candidates")

        # Calculate match scores for each candidate
        matches: List[TalentMatch] = []
        for candidate in candidates:
            match_score = await self._calculate_match_score(
                candidate,
                request.job_requirement,
                request.weights,
                request.use_semantic_matching
            )

            if match_score.overall_score >= request.min_score_threshold:
                matched_skills, missing_skills = self._analyze_skills_match(
                    candidate.skills,
                    request.job_requirement.required_skills,
                    request.job_requirement.preferred_skills
                )

                strengths, gaps = await self._analyze_candidate_fit(
                    candidate,
                    request.job_requirement,
                    match_score
                )

                recommendation = await self._generate_recommendation(
                    candidate,
                    request.job_requirement,
                    match_score,
                    strengths,
                    gaps
                )

                matches.append(TalentMatch(
                    candidate=candidate,
                    match_score=match_score,
                    matched_skills=matched_skills,
                    missing_skills=missing_skills,
                    strengths=strengths,
                    gaps=gaps,
                    recommendation=recommendation,
                    rank=0  # Will be set after sorting
                ))

        # Sort by overall score and assign ranks
        matches.sort(key=lambda m: m.match_score.overall_score, reverse=True)
        for idx, match in enumerate(matches[:request.top_n], start=1):
            match.rank = idx

        logger.info(f"✓ Found {len(matches[:request.top_n])} matches above threshold")

        return TalentSearchResponse(
            job_requirement=request.job_requirement,
            matches=matches[:request.top_n],
            total_candidates_evaluated=len(candidates),
            total_matches_found=len(matches),
            search_metadata={
                "min_score_threshold": request.min_score_threshold,
                "semantic_matching_used": request.use_semantic_matching,
                "top_match_score": matches[0].match_score.overall_score if matches else 0.0
            }
        )

    async def _calculate_match_score(
        self,
        candidate: CandidateProfile,
        job: JobRequirement,
        custom_weights: Dict[str, float] = None,
        use_semantic: bool = True
    ) -> MatchScore:
        """Calculate comprehensive match score"""

        # Default weights
        weights = custom_weights or {
            "skills": 0.35,
            "experience": 0.25,
            "education": 0.15,
            "location": 0.10,
            "salary": 0.10,
            "semantic": 0.05
        }

        # Skills matching
        skills_score = self._calculate_skills_score(
            candidate.skills,
            job.required_skills,
            job.preferred_skills
        )

        # Experience matching
        experience_score = self._calculate_experience_score(
            candidate.years_of_experience,
            candidate.experience_level,
            job.years_of_experience_min,
            job.years_of_experience_max,
            job.experience_level
        )

        # Education matching
        education_score = self._calculate_education_score(
            candidate.education,
            job.education_requirements
        )

        # Location matching
        location_score = self._calculate_location_score(
            candidate.location,
            job.location
        )

        # Salary matching
        salary_score = self._calculate_salary_score(
            candidate.expected_salary,
            job.salary_range_min,
            job.salary_range_max
        )

        # Semantic matching (optional, LLM-based)
        semantic_score = None
        if use_semantic and candidate.resume_text and job.job_description:
            semantic_score = await self._calculate_semantic_score(
                candidate.resume_text,
                job.job_description
            )

        # Calculate weighted overall score
        overall = (
            skills_score * weights["skills"] +
            experience_score * weights["experience"] +
            education_score * weights["education"] +
            location_score * weights["location"] +
            salary_score * weights["salary"]
        )

        if semantic_score is not None:
            overall += semantic_score * weights.get("semantic", 0.05)

        return MatchScore(
            overall_score=round(overall, 2),
            skills_match_score=round(skills_score, 2),
            experience_match_score=round(experience_score, 2),
            education_match_score=round(education_score, 2),
            location_match_score=round(location_score, 2),
            salary_match_score=round(salary_score, 2),
            semantic_similarity_score=round(semantic_score, 2) if semantic_score else None
        )

    def _calculate_skills_score(
        self,
        candidate_skills: List[Skill],
        required_skills: List[Skill],
        preferred_skills: List[Skill]
    ) -> float:
        """Calculate skills match score"""
        if not required_skills and not preferred_skills:
            return 100.0

        candidate_skill_names = {s.name.lower() for s in candidate_skills}

        # Required skills matching (70% weight)
        required_matches = 0
        for req_skill in required_skills:
            if req_skill.name.lower() in candidate_skill_names:
                required_matches += 1

        required_score = (required_matches / len(required_skills) * 100) if required_skills else 100.0

        # Preferred skills matching (30% weight)
        preferred_matches = 0
        for pref_skill in preferred_skills:
            if pref_skill.name.lower() in candidate_skill_names:
                preferred_matches += 1

        preferred_score = (preferred_matches / len(preferred_skills) * 100) if preferred_skills else 100.0

        return required_score * 0.7 + preferred_score * 0.3

    def _calculate_experience_score(
        self,
        candidate_years: float,
        candidate_level: ExperienceLevel,
        min_years: float,
        max_years: float,
        required_level: ExperienceLevel
    ) -> float:
        """Calculate experience match score"""
        score = 0.0

        # Years of experience matching (50%)
        if candidate_years >= min_years:
            if max_years is None or candidate_years <= max_years:
                score += 50.0
            elif candidate_years <= max_years * 1.5:  # Allow some over-qualification
                score += 40.0
            else:
                score += 25.0
        elif candidate_years >= min_years * 0.8:  # Allow slight under-qualification
            score += 35.0

        # Experience level matching (50%)
        level_order = {
            ExperienceLevel.ENTRY_LEVEL: 1,
            ExperienceLevel.MID_LEVEL: 2,
            ExperienceLevel.SENIOR: 3,
            ExperienceLevel.LEAD: 4,
            ExperienceLevel.PRINCIPAL: 5,
            ExperienceLevel.EXECUTIVE: 6
        }

        candidate_level_num = level_order.get(candidate_level, 0)
        required_level_num = level_order.get(required_level, 0)

        if candidate_level_num == required_level_num:
            score += 50.0
        elif abs(candidate_level_num - required_level_num) == 1:
            score += 35.0
        elif candidate_level_num > required_level_num:
            score += 25.0

        return min(score, 100.0)

    def _calculate_education_score(
        self,
        candidate_education: List[Any],
        required_education: List[Any]
    ) -> float:
        """Calculate education match score"""
        if not required_education:
            return 100.0

        if not candidate_education:
            return 0.0

        # Simple matching: if candidate has any required degrees
        candidate_degrees = {ed.degree.lower() for ed in candidate_education}
        required_degrees = {ed.degree.lower() for ed in required_education if ed.required}

        if not required_degrees:
            return 100.0

        matches = len(candidate_degrees.intersection(required_degrees))
        return (matches / len(required_degrees)) * 100

    def _calculate_location_score(self, candidate_location: str, job_location: str) -> float:
        """Calculate location compatibility score"""
        if not job_location:
            return 100.0

        if not candidate_location:
            return 50.0  # Unknown location = neutral

        # Simple string matching (in production, use geocoding/distance)
        if candidate_location.lower() == job_location.lower():
            return 100.0
        elif "remote" in job_location.lower() or "remote" in candidate_location.lower():
            return 90.0
        else:
            return 40.0

    def _calculate_salary_score(
        self,
        candidate_expected: float,
        salary_min: float,
        salary_max: float
    ) -> float:
        """Calculate salary alignment score"""
        if not salary_min and not salary_max:
            return 100.0

        if not candidate_expected:
            return 75.0  # Unknown expectation = neutral

        if salary_min and candidate_expected < salary_min:
            return 50.0  # Undervalued
        elif salary_max and candidate_expected > salary_max:
            gap_percent = ((candidate_expected - salary_max) / salary_max) * 100
            if gap_percent > 20:
                return 20.0  # Too expensive
            else:
                return 60.0  # Slightly expensive
        else:
            return 100.0  # Within range

    async def _calculate_semantic_score(self, resume_text: str, job_description: str) -> float:
        """Calculate semantic similarity using LLM"""
        prompt = f"""Rate the match between this candidate resume and job description on a scale of 0-100.
Consider skills, experience, and overall fit.

Resume (first 1000 chars):
{resume_text[:1000]}

Job Description (first 1000 chars):
{job_description[:1000]}

Respond with ONLY a number between 0 and 100 representing the match score."""

        try:
            # Get LLM parameters from module config
            llm_config = self.config.get('llm', {}).get('default', {})
            model = llm_config.get('model', 'gpt-4o-mini')
            temperature = llm_config.get('temperature', 0.0)
            max_tokens = llm_config.get('max_tokens', 10)

            response = await self.llm_service.generate_response(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            score = float(response.strip())
            return max(0.0, min(100.0, score))
        except Exception as e:
            logger.warning(f"Semantic scoring failed: {e}")
            return 75.0  # Default neutral score

    def _analyze_skills_match(
        self,
        candidate_skills: List[Skill],
        required_skills: List[Skill],
        preferred_skills: List[Skill]
    ) -> tuple[List[str], List[str]]:
        """Analyze which skills match and which are missing"""
        candidate_skill_names = {s.name.lower() for s in candidate_skills}

        matched = [
            s.name for s in (required_skills + preferred_skills)
            if s.name.lower() in candidate_skill_names
        ]

        missing = [
            s.name for s in required_skills
            if s.name.lower() not in candidate_skill_names
        ]

        return matched, missing

    async def _analyze_candidate_fit(
        self,
        candidate: CandidateProfile,
        job: JobRequirement,
        match_score: MatchScore
    ) -> tuple[List[str], List[str]]:
        """Analyze candidate strengths and gaps using LLM"""
        strengths = []
        gaps = []

        # Rule-based strengths
        if match_score.skills_match_score >= 80:
            strengths.append("Strong skills alignment")
        if match_score.experience_match_score >= 80:
            strengths.append("Excellent experience match")
        if match_score.education_match_score >= 90:
            strengths.append("Meets education requirements")

        # Rule-based gaps
        if match_score.skills_match_score < 60:
            gaps.append("Skills gap in key areas")
        if match_score.experience_match_score < 50:
            gaps.append("Experience level mismatch")

        return strengths, gaps

    async def _generate_recommendation(
        self,
        candidate: CandidateProfile,
        job: JobRequirement,
        match_score: MatchScore,
        strengths: List[str],
        gaps: List[str]
    ) -> str:
        """Generate AI recommendation summary"""
        prompt = f"""Generate a concise hiring recommendation for this candidate:

Candidate: {candidate.name or candidate.candidate_id}
Role: {job.job_title}
Match Score: {match_score.overall_score}/100
Strengths: {', '.join(strengths) if strengths else 'None identified'}
Gaps: {', '.join(gaps) if gaps else 'None identified'}

Provide a 1-2 sentence recommendation (e.g., "Strong candidate", "Consider with reservations", "Not recommended").
Return ONLY the recommendation text."""

        try:
            recommendation = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=100
            )
            return recommendation.strip()
        except Exception as e:
            logger.warning(f"Recommendation generation failed: {e}")
            if match_score.overall_score >= 75:
                return "Strong candidate for this role."
            elif match_score.overall_score >= 50:
                return "Consider with reservations - some gaps identified."
            else:
                return "Not recommended - significant gaps in requirements."

    async def _get_candidate_pool(self, session_id: Optional[str] = None) -> List[CandidateProfile]:
        """Get candidate pool from uploaded resumes and CVs"""
        try:
            documents = await self.document_service.list_documents(session_id=session_id)

            if not documents:
                logger.warning("No documents found for candidate extraction - returning empty pool")
                return []

            candidates = []

            # Extract candidate profiles from first 20 documents
            for doc in documents[:20]:
                try:
                    chunks = await self.document_service.get_chunks_for_document(doc.id)
                    resume_text = " ".join([chunk.get('content', '') for chunk in chunks])

                    profile = await self._extract_candidate_profile(resume_text, doc.filename)
                    if profile:
                        candidates.append(profile)
                except Exception as e:
                    logger.warning(f"Failed to extract candidate from document {doc.id}: {e}")
                    continue

            logger.info(f"✓ Extracted {len(candidates)} candidates from documents")
            return candidates

        except Exception as e:
            logger.error(f"Failed to load candidate pool: {e}")
            return []

    async def _extract_candidate_profile(self, resume_text: str, filename: str) -> Optional[CandidateProfile]:
        """Extract candidate profile from resume using LLM"""
        prompt = f"""Extract candidate information from this resume:

{resume_text[:3000]}

Return JSON:
{{
  "candidate_id": "unique_id",
  "name": "Full Name",
  "email": "email@example.com",
  "location": "City, State",
  "years_of_experience": 5.0,
  "experience_level": "entry_level/mid_level/senior/lead/principal/executive",
  "expected_salary": 100000.0,
  "skills": [{{"name": "Python", "proficiency_level": "expert", "years_experience": 3.0}}],
  "education": [{{"degree": "Bachelor of Science", "field": "Computer Science", "institution": "University", "required": false}}],
  "resume_text": "summary"
}}

Return ONLY valid JSON."""

        try:
            # Get LLM parameters from module config
            llm_config = self.config.get('llm', {}).get('default', {})
            model = llm_config.get('model', 'gpt-4o-mini')
            temperature = llm_config.get('temperature', 0.0)
            max_tokens = llm_config.get('max_tokens', 1000)

            response = await self.llm_service.generate_response(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

            data = json.loads(response.strip())

            # Convert to CandidateProfile
            return CandidateProfile(
                candidate_id=data.get("candidate_id", filename),
                name=data.get("name"),
                email=data.get("email"),
                phone=data.get("phone"),
                location=data.get("location", ""),
                years_of_experience=float(data.get("years_of_experience", 0)),
                experience_level=ExperienceLevel(data.get("experience_level", "mid_level")),
                expected_salary=data.get("expected_salary"),
                skills=[Skill(**s) for s in data.get("skills", [])],
                education=[],  # Simplified for now
                resume_text=resume_text[:1000]
            )

        except Exception as e:
            logger.warning(f"Candidate extraction failed: {e}")
            return None
