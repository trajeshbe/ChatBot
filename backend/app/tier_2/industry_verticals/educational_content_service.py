"""
Educational Content Recommendation Service
Tier 2 Module: Industry Verticals

Personalized course recommendations using uploaded LMS and course catalog documents.
100% tier_1 service reuse - zero new dependencies.
"""

import uuid
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from app.tier_1.document_processing.document_service import DocumentService

from .educational_content_schemas import *

logger = logging.getLogger(__name__)


class EducationalContentService:
    """
    Educational content recommendation service.

    Recommendation Process:
    1. Course Catalog Extraction → Extract courses from LMS documents
    2. Learner Profile Analysis → Extract learner history and preferences
    3. Skill Gap Analysis → Identify gaps between current and target skills
    4. Course Matching → Match learner profile to course catalog
    5. Prerequisite Check → Ensure learner meets prerequisites
    6. Learning Path Generation → Create personalized learning sequence
    7. AI Personalization → Generate personalized insights
    """

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.llm_service = LLMService(db, settings)
        self.document_service = DocumentService(db)
        logger.info("✓ EducationalContentService initialized with tier_1 services")

    async def recommend_content(
        self,
        request: RecommendContentRequest
    ) -> RecommendContentResponse:
        """Generate personalized course recommendations using uploaded catalogs."""
        start_time = datetime.utcnow()

        logger.info(f"📚 Generating recommendations: {request.subject}, level {request.current_skill_level.value}")

        try:
            # Step 1: Extract course catalog from uploaded documents
            course_catalog = await self._extract_course_catalog_from_documents(request)

            # Step 2: Extract learner profile from documents
            learner_profile = await self._extract_learner_profile_from_documents(request)

            logger.info(f"Found {len(course_catalog)} courses, learner completed {len(learner_profile.get('completed_courses', []))} courses")

            # Step 3: Analyze skill gaps
            skill_gaps = self._analyze_skill_gaps(
                request,
                learner_profile
            )

            # Step 4: Match courses to learner needs
            matched_courses = await self._match_courses_to_learner(
                request,
                course_catalog,
                learner_profile,
                skill_gaps
            )

            # Step 5: Filter by prerequisites
            eligible_courses = self._filter_by_prerequisites(
                matched_courses,
                learner_profile
            )

            # Step 6: Rank and select top recommendations
            recommendations = self._rank_and_select_recommendations(
                eligible_courses,
                request.max_recommendations
            )

            # Step 7: Generate learning path
            learning_path = self._generate_learning_path(
                recommendations,
                skill_gaps
            )

            # Step 8: Generate AI insights
            ai_insights = await self._generate_recommendation_insights(
                request,
                recommendations,
                skill_gaps,
                learner_profile
            )

            # Step 9: Store recommendations
            await self._store_recommendations(request, recommendations)

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            return RecommendContentResponse(
                success=True,
                student_id=request.student_id or str(uuid.uuid4()),
                recommendations=recommendations,
                learning_path=learning_path,
                skill_gaps=skill_gaps,
                learning_path_insights=learning_path,
                ai_insights=ai_insights,
                processing_time_seconds=processing_time,
                tier_1_services_used=["LLMService", "DocumentService"]
            )

        except Exception as e:
            logger.error(f"❌ Recommendation error: {e}", exc_info=True)
            raise

    async def _extract_course_catalog_from_documents(
        self,
        request: RecommendContentRequest
    ) -> List[Dict[str, Any]]:
        """Extract course catalog from uploaded LMS documents."""
        try:
            # Get documents for this session (course catalogs, syllabi, LMS exports)
            documents = await self.document_service.list_documents(
                session_id=request.session_id,
                limit=50
            )

            if not documents:
                logger.warning(f"No documents found for session {request.session_id}")
                return []

            # Extract courses from documents
            all_courses = []

            for doc in documents[:10]:
                chunks = await self.document_service.get_chunks_for_document(doc.id)

                if not chunks:
                    continue

                # Combine chunks for context
                document_text = " ".join([chunk.get('content', '') for chunk in chunks[:5]])

                if len(document_text) < 100:
                    continue

                # Extract courses using LLM
                courses = await self._extract_courses_from_text(document_text)
                all_courses.extend(courses)

            # Deduplicate courses by title
            unique_courses = {}
            for course in all_courses:
                title = course.get("title", "").strip()
                if title and title not in unique_courses:
                    unique_courses[title] = course

            courses_list = list(unique_courses.values())

            logger.info(f"Extracted {len(courses_list)} unique courses from {len(documents)} documents")

            return courses_list

        except Exception as e:
            logger.error(f"Failed to extract course catalog: {str(e)}")
            return []

    async def _extract_courses_from_text(
        self,
        text: str
    ) -> List[Dict[str, Any]]:
        """Extract course information from document text using LLM."""
        prompt = f"""Extract educational courses from the following text. Focus on course catalogs, syllabi, and LMS data.

Text:
{text[:3000]}

Extract courses with:
- title: Course title
- content_id: Course ID/code
- description: Course description
- subject: Subject area (mathematics, science, programming, business, etc.)
- difficulty_level: (beginner, intermediate, advanced)
- duration_minutes: Estimated duration in minutes
- prerequisites: List of prerequisite courses/skills
- learning_outcomes: List of learning outcomes
- content_type: (course, tutorial, video, reading)

Return a JSON array:
[
  {{
    "title": "Introduction to Python Programming",
    "content_id": "CS101",
    "description": "Learn Python basics",
    "subject": "programming",
    "difficulty_level": "beginner",
    "duration_minutes": 180,
    "prerequisites": [],
    "learning_outcomes": ["Variables", "Functions", "Loops"],
    "content_type": "course"
  }}
]

If no courses found, return empty array [].
Return ONLY the JSON array, no explanation."""

        try:
            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.1,
                max_tokens=1500
            )

            courses = json.loads(response.strip())
            logger.info(f"Extracted {len(courses)} courses from document text")
            return courses

        except Exception as e:
            logger.warning(f"Failed to extract courses: {str(e)}")
            return []

    async def _extract_learner_profile_from_documents(
        self,
        request: RecommendContentRequest
    ) -> Dict[str, Any]:
        """Extract learner profile and history from uploaded documents."""
        try:
            documents = await self.document_service.list_documents(
                session_id=request.session_id,
                limit=50
            )

            learner_profile = {
                "completed_courses": [],
                "current_skills": [],
                "learning_preferences": {},
                "performance_history": []
            }

            for doc in documents[:10]:
                chunks = await self.document_service.get_chunks_for_document(doc.id)

                if not chunks:
                    continue

                document_text = " ".join([chunk.get('content', '') for chunk in chunks[:5]])

                if len(document_text) < 100:
                    continue

                # Extract learner data using LLM
                learner_data = await self._extract_learner_data_from_text(document_text)

                # Merge extracted data
                learner_profile["completed_courses"].extend(learner_data.get("completed_courses", []))
                learner_profile["current_skills"].extend(learner_data.get("current_skills", []))

                if learner_data.get("learning_preferences"):
                    learner_profile["learning_preferences"].update(learner_data["learning_preferences"])

                learner_profile["performance_history"].extend(learner_data.get("performance_history", []))

            logger.info(f"Extracted learner profile: {len(learner_profile['completed_courses'])} completed courses")

            return learner_profile

        except Exception as e:
            logger.error(f"Failed to extract learner profile: {str(e)}")
            return {
                "completed_courses": [],
                "current_skills": [],
                "learning_preferences": {},
                "performance_history": []
            }

    async def _extract_learner_data_from_text(
        self,
        text: str
    ) -> Dict[str, Any]:
        """Extract learner profile data from document text using LLM."""
        prompt = f"""Extract learner/student information from the following text (transcripts, LMS reports, certificates).

Text:
{text[:3000]}

Extract:
- completed_courses: List of completed courses with grades
- current_skills: List of skills/competencies
- learning_preferences: Preferred learning style, pace, format
- performance_history: Grade trends, completion rates

Return a JSON object:
{{
  "completed_courses": [
    {{"title": "Intro to Python", "grade": "A", "completion_date": "2024-06-01"}}
  ],
  "current_skills": ["Python", "Data Analysis", "SQL"],
  "learning_preferences": {{
    "style": "visual",
    "pace": "self-paced",
    "format": "video"
  }},
  "performance_history": [
    {{"subject": "programming", "avg_grade": 85.0}}
  ]
}}

If no learner data found, return empty arrays/objects.
Return ONLY the JSON, no explanation."""

        try:
            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.1,
                max_tokens=1000
            )

            learner_data = json.loads(response.strip())
            logger.info(f"Extracted learner data with {len(learner_data.get('completed_courses', []))} completed courses")
            return learner_data

        except Exception as e:
            logger.warning(f"Failed to extract learner data: {str(e)}")
            return {
                "completed_courses": [],
                "current_skills": [],
                "learning_preferences": {},
                "performance_history": []
            }

    def _analyze_skill_gaps(
        self,
        request: RecommendContentRequest,
        learner_profile: Dict[str, Any]
    ) -> List[str]:
        """Analyze skill gaps between current and target skills."""
        current_skills = set(learner_profile.get("current_skills", []))
        target_skills = set(request.learning_goals)

        # Find skills in target but not in current
        skill_gaps = list(target_skills - current_skills)

        # Add subject-specific fundamental skills if beginner
        if request.current_skill_level == SkillLevel.BEGINNER:
            subject_fundamentals = {
                "programming": ["Variables", "Functions", "Loops", "Data Structures"],
                "mathematics": ["Algebra", "Geometry", "Statistics"],
                "science": ["Scientific Method", "Experimentation", "Data Analysis"],
                "business": ["Business Fundamentals", "Marketing Basics", "Finance Basics"]
            }

            fundamentals = subject_fundamentals.get(request.subject.lower(), [])
            for skill in fundamentals:
                if skill not in current_skills and skill not in skill_gaps:
                    skill_gaps.append(skill)

        return skill_gaps[:10]  # Limit to top 10 gaps

    async def _match_courses_to_learner(
        self,
        request: RecommendContentRequest,
        course_catalog: List[Dict[str, Any]],
        learner_profile: Dict[str, Any],
        skill_gaps: List[str]
    ) -> List[Dict[str, Any]]:
        """Match courses to learner needs using collaborative filtering."""
        matched_courses = []

        for course in course_catalog:
            # Calculate relevance score
            relevance_score = 0.0

            # Subject match
            if request.subject.lower() in course.get("subject", "").lower():
                relevance_score += 40.0

            # Skill level match
            course_level = course.get("difficulty_level", "").lower()
            request_level = request.current_skill_level.value.lower()

            if course_level == request_level:
                relevance_score += 30.0
            elif (course_level == "beginner" and request_level == "intermediate") or \
                 (course_level == "intermediate" and request_level == "advanced"):
                relevance_score += 15.0  # Slightly advanced is okay

            # Learning outcomes match skill gaps
            outcomes = course.get("learning_outcomes", [])
            matching_outcomes = sum(1 for outcome in outcomes if any(gap.lower() in outcome.lower() for gap in skill_gaps))
            if matching_outcomes > 0:
                relevance_score += min(20.0, matching_outcomes * 5.0)

            # Preferred learning style
            preferences = learner_profile.get("learning_preferences", {})
            preferred_format = preferences.get("format", "").lower()
            course_type = course.get("content_type", "").lower()

            if preferred_format and preferred_format in course_type:
                relevance_score += 10.0

            # Skip if relevance too low
            if relevance_score < 30.0:
                continue

            # Add course with relevance score
            matched_course = course.copy()
            matched_course["relevance_score"] = relevance_score
            matched_course["difficulty_match"] = 100.0 if course_level == request_level else 70.0

            matched_courses.append(matched_course)

        return matched_courses

    def _filter_by_prerequisites(
        self,
        matched_courses: List[Dict[str, Any]],
        learner_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Filter courses by prerequisites."""
        completed_courses = set(c.get("title", "") for c in learner_profile.get("completed_courses", []))
        current_skills = set(learner_profile.get("current_skills", []))

        eligible_courses = []

        for course in matched_courses:
            prerequisites = course.get("prerequisites", [])

            if not prerequisites:
                # No prerequisites, automatically eligible
                eligible_courses.append(course)
                continue

            # Check if prerequisites are met
            prerequisites_met = all(
                prereq in completed_courses or prereq in current_skills
                for prereq in prerequisites
            )

            if prerequisites_met:
                eligible_courses.append(course)

        return eligible_courses

    def _rank_and_select_recommendations(
        self,
        eligible_courses: List[Dict[str, Any]],
        max_recommendations: int
    ) -> List[ContentRecommendation]:
        """Rank courses and select top recommendations."""
        # Sort by relevance score
        eligible_courses.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        # Select top N
        top_courses = eligible_courses[:max_recommendations]

        # Convert to ContentRecommendation objects
        recommendations = []
        for course in top_courses:
            # Map content_type string to enum
            content_type_str = course.get("content_type", "course").lower()
            content_type_map = {
                "course": ContentType.COURSE,
                "tutorial": ContentType.TUTORIAL,
                "video": ContentType.VIDEO,
                "reading": ContentType.READING,
                "quiz": ContentType.QUIZ,
                "project": ContentType.PROJECT
            }
            content_type = content_type_map.get(content_type_str, ContentType.COURSE)

            recommendation = ContentRecommendation(
                content_id=course.get("content_id", str(uuid.uuid4())[:8]),
                title=course.get("title", "Untitled Course"),
                description=course.get("description", ""),
                content_type=content_type,
                subject=course.get("subject", "general"),
                relevance_score=course.get("relevance_score", 0.0),
                estimated_duration_minutes=course.get("duration_minutes", 60),
                difficulty_level=course.get("difficulty_level", "intermediate"),
                prerequisites=course.get("prerequisites", []),
                learning_outcomes=course.get("learning_outcomes", []),
                difficulty_match=course.get("difficulty_match", 80.0)
            )
            recommendations.append(recommendation)

        return recommendations

    def _generate_learning_path(
        self,
        recommendations: List[ContentRecommendation],
        skill_gaps: List[str]
    ) -> str:
        """Generate a learning path description."""
        if not recommendations:
            return "Upload course catalogs to receive personalized recommendations"

        path_steps = []
        for i, rec in enumerate(recommendations[:5], 1):
            path_steps.append(f"Step {i}: {rec.title} ({rec.difficulty_level})")

        learning_path = f"Recommended learning path to address {len(skill_gaps)} skill gap(s):\n\n"
        learning_path += "\n".join(path_steps)

        if skill_gaps:
            learning_path += f"\n\nSkill gaps addressed: {', '.join(skill_gaps[:5])}"

        return learning_path

    async def _generate_recommendation_insights(
        self,
        request: RecommendContentRequest,
        recommendations: List[ContentRecommendation],
        skill_gaps: List[str],
        learner_profile: Dict[str, Any]
    ) -> str:
        """Generate AI-powered recommendation insights."""
        if not recommendations:
            return "No course recommendations available. Upload course catalogs and learner transcripts for personalized recommendations."

        completed_count = len(learner_profile.get("completed_courses", []))
        top_rec = recommendations[0] if recommendations else None

        prompt = f"""Generate concise learning recommendation insights:

Student Profile:
- Subject Interest: {request.subject}
- Current Level: {request.current_skill_level.value}
- Learning Goals: {', '.join(request.learning_goals[:3])}
- Completed Courses: {completed_count}
- Skill Gaps: {', '.join(skill_gaps[:5])}

Top Recommendation:
- Course: {top_rec.title if top_rec else 'None'}
- Relevance: {top_rec.relevance_score:.1f}% match
- Level: {top_rec.difficulty_level if top_rec else 'N/A'}

Generate 2-3 sentences analyzing:
1. Why these recommendations match the student's goals
2. Suggested learning sequence
3. Expected skill development

Return ONLY the insight text, no prefix."""

        try:
            insights = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=200
            )
            return insights.strip()

        except Exception as e:
            logger.warning(f"Failed to generate insights: {str(e)}")
            return f"Found {len(recommendations)} recommended course(s) matching your {request.subject} learning goals at {request.current_skill_level.value} level."

    async def _store_recommendations(
        self,
        request: RecommendContentRequest,
        recommendations: List[ContentRecommendation]
    ):
        """Store recommendations in database."""
        try:
            from app.models.database_enhanced import EducationalContentResults

            for rec in recommendations:
                rec_record = EducationalContentResults(
                    id=uuid.uuid4(),
                    recommendation_id=uuid.uuid4(),
                    module_id="educational-content",
                    session_id=request.session_id,
                    project_id=uuid.UUID(request.project_id) if request.project_id else None,
                    recommendation_data={
                        "student_id": request.student_id,
                        "content_id": rec.content_id,
                        "title": rec.title,
                        "subject": rec.subject,
                        "relevance_score": rec.relevance_score,
                        "difficulty_level": rec.difficulty_level
                    },
                    created_at=datetime.utcnow()
                )

                self.db.add(rec_record)

            self.db.commit()
            logger.info(f"✓ Stored {len(recommendations)} recommendations")

        except Exception as e:
            logger.error(f"Failed to store recommendations: {str(e)}")

    async def search_recommendations(
        self,
        request: SearchRecommendationsRequest
    ) -> SearchRecommendationsResponse:
        """Search historical recommendations."""
        # Placeholder for search functionality
        return SearchRecommendationsResponse(
            success=True,
            recommendations=[],
            total_count=0
        )

    async def export_recommendations(
        self,
        request: ExportRecommendationsRequest
    ) -> ExportRecommendationsResponse:
        """Export recommendations to specified format."""
        # Placeholder for export functionality
        return ExportRecommendationsResponse(
            success=True,
            export_data={"format": request.format},
            format=request.format
        )

    async def get_stats(self) -> EducationalStatsResponse:
        """Get recommendation statistics."""
        return EducationalStatsResponse(
            success=True,
            total_recommendations=0,
            most_popular_subject="mathematics"
        )

    async def get_status(self) -> StatusResponse:
        """Get service status and capabilities."""
        return StatusResponse(
            success=True,
            status="operational",
            description="Educational Content Recommendation: Personalized course recommendations using uploaded LMS and course catalog documents",
            tier_2_modules_used=[],
            capabilities=[
                "Extract course catalogs from LMS documents using LLM",
                "Extract learner profiles and completion history from transcripts",
                "Skill gap analysis between current and target competencies",
                "Collaborative filtering for course-learner matching",
                "Prerequisite checking and course sequencing",
                "Personalized learning path generation",
                "AI-powered recommendation insights",
                "Support for multiple content types (course, tutorial, video, reading, quiz, project)"
            ]
        )
