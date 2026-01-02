"""
British Council Profile Analyzer - Extract User Profiles from Natural Language

Uses LLM to extract structured profiles for course matching.
Integrates with existing tier_1 LLM service.

Author: Claude Code
Date: 2026-01-02
"""

from pydantic import BaseModel, Field
from typing import List, Optional
import json
import logging
from app.tier_1.llm.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class UserProfile(BaseModel):
    """Structured user profile for British Council course matching."""

    skills: List[str] = Field(default_factory=list, description="User's current skills")
    interests: List[str] = Field(default_factory=list, description="Learning interests")
    education_level: str = Field(default="intermediate", description="beginner, intermediate, or advanced")
    career_goals: List[str] = Field(default_factory=list, description="Career aspirations")
    preferred_format: str = Field(default="online", description="online, in-person, or hybrid")
    language_proficiency: str = Field(default="B1", description="CEFR level: A1, A2, B1, B2, C1, C2")
    availability: Optional[str] = Field(default="flexible", description="weekdays, weekends, or flexible")

    class Config:
        json_schema_extra = {
            "example": {
                "skills": ["software engineering", "programming", "data analysis"],
                "interests": ["business English", "professional development"],
                "education_level": "intermediate",
                "career_goals": ["work at international companies", "leadership roles"],
                "preferred_format": "online",
                "language_proficiency": "B1",
                "availability": "weekends"
            }
        }


class ProfileAnalyzerService:
    """
    Extract structured user profiles using LLM.

    Reuses:
    - tier_1.llm.llm_service: Multi-LLM interface (GPT-4, Claude, Ollama)

    Example:
        analyzer = ProfileAnalyzerService()
        profile = await analyzer.analyze_profile(
            "I'm a software engineer wanting to improve my business English"
        )
    """

    def __init__(self, llm_service=None):
        """
        Initialize profile analyzer.

        Args:
            llm_service: Optional LLM service (uses singleton if not provided)
        """
        self.llm = llm_service or get_llm_service()
        logger.info("🎓 ProfileAnalyzerService initialized")

    async def analyze_profile(
        self,
        user_input: str,
        model_id: Optional[str] = None
    ) -> UserProfile:
        """
        Extract structured profile from natural language input.

        Args:
            user_input: User's description of their goals/needs
            model_id: Optional LLM model to use (defaults to GPT-4o-mini)

        Returns:
            UserProfile with extracted fields

        Example:
            input_text = "I'm a software engineer looking to improve my business English.
                         I have intermediate level English (B1) and prefer online courses
                         on weekends. I want to advance my career in international companies."

            profile = await analyzer.analyze_profile(input_text)
            # Returns:
            # UserProfile(
            #     skills=["software engineering", "programming"],
            #     interests=["business English", "career development"],
            #     education_level="intermediate",
            #     career_goals=["international companies", "career advancement"],
            #     preferred_format="online",
            #     language_proficiency="B1",
            #     availability="weekends"
            # )
        """
        logger.info(f"📝 Analyzing profile from user input (length: {len(user_input)})")

        # Build prompt for profile extraction
        prompt = self._build_extraction_prompt(user_input)

        try:
            # Use LLM to extract profile
            response = await self.llm.generate(
                prompt=prompt,
                messages=None,  # Single-turn extraction
                model_id=model_id or "gpt-4o-mini",
                temperature=0.0,  # Deterministic extraction
                max_tokens=800
            )

            # Parse JSON response
            content = response.get("content", "{}").strip()

            # Handle markdown code blocks if present
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()

            profile_data = json.loads(content)

            # Create and validate profile
            profile = UserProfile(**profile_data)

            logger.info(f"✅ Profile extracted: {len(profile.skills)} skills, "
                       f"{len(profile.interests)} interests, "
                       f"{profile.education_level} level, "
                       f"{profile.language_proficiency} CEFR")

            return profile

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response content: {content[:200]}")

            # Return default profile with error handling
            return UserProfile(
                interests=["general English"],
                education_level="intermediate",
                career_goals=["improve English skills"]
            )

        except Exception as e:
            logger.error(f"❌ Profile analysis failed: {e}")
            raise

    def _build_extraction_prompt(self, user_input: str) -> str:
        """
        Build prompt for profile extraction.

        Args:
            user_input: Raw user input text

        Returns:
            Formatted prompt for LLM
        """
        prompt = f"""You are a profile analyzer for the British Council course recommendation system.

Extract a structured profile from this user input:

"{user_input}"

Return JSON with these exact fields:
- skills: List[str] (user's current skills, e.g., ["software engineering", "data analysis"])
- interests: List[str] (learning interests, e.g., ["business English", "career development"])
- education_level: str (one of: "beginner", "intermediate", "advanced")
- career_goals: List[str] (career aspirations, e.g., ["work internationally", "leadership"])
- preferred_format: str (one of: "online", "in-person", "hybrid")
- language_proficiency: str (CEFR level: "A1", "A2", "B1", "B2", "C1", "C2")
- availability: str (one of: "weekdays", "weekends", "flexible")

Rules:
1. If education level is not mentioned, infer from context or use "intermediate"
2. If language proficiency is not mentioned, infer from context or use "B1"
3. If availability is not mentioned, use "flexible"
4. Extract at least 1-3 interests from the input
5. Skills should be specific and relevant to English learning context

Return ONLY the JSON object, no additional text.

Example output:
{{
  "skills": ["software engineering", "programming"],
  "interests": ["business English", "professional communication"],
  "education_level": "intermediate",
  "career_goals": ["work at international companies"],
  "preferred_format": "online",
  "language_proficiency": "B1",
  "availability": "weekends"
}}

JSON:"""

        return prompt

    async def validate_profile(self, profile: UserProfile) -> bool:
        """
        Validate profile fields are within expected ranges.

        Args:
            profile: UserProfile to validate

        Returns:
            True if valid, raises ValueError if invalid
        """
        valid_education_levels = {"beginner", "intermediate", "advanced"}
        valid_formats = {"online", "in-person", "hybrid"}
        valid_cefr_levels = {"A1", "A2", "B1", "B2", "C1", "C2"}
        valid_availability = {"weekdays", "weekends", "flexible"}

        if profile.education_level not in valid_education_levels:
            raise ValueError(f"Invalid education_level: {profile.education_level}. "
                           f"Must be one of: {valid_education_levels}")

        if profile.preferred_format not in valid_formats:
            raise ValueError(f"Invalid preferred_format: {profile.preferred_format}. "
                           f"Must be one of: {valid_formats}")

        if profile.language_proficiency not in valid_cefr_levels:
            raise ValueError(f"Invalid language_proficiency: {profile.language_proficiency}. "
                           f"Must be one of: {valid_cefr_levels}")

        if profile.availability and profile.availability not in valid_availability:
            raise ValueError(f"Invalid availability: {profile.availability}. "
                           f"Must be one of: {valid_availability}")

        logger.info("✅ Profile validation passed")
        return True


# Singleton instance
_profile_analyzer = None

def get_profile_analyzer() -> ProfileAnalyzerService:
    """
    Get singleton ProfileAnalyzerService instance.

    Returns:
        ProfileAnalyzerService instance
    """
    global _profile_analyzer
    if _profile_analyzer is None:
        _profile_analyzer = ProfileAnalyzerService()
    return _profile_analyzer
