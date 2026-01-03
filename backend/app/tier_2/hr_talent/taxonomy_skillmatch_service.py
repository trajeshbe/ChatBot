"""
Taxonomy Skillmatch Service
Tier 2 Module: HR & Talent

Service for mapping skills to taxonomy and matching skill sets.
Leverages Tier 1 LLMService for intelligent skill matching.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from .taxonomy_skillmatch_schemas import (
    SkillTaxonomyRequest,
    SkillTaxonomyResponse,
    SkillMatchRequest,
    SkillMatchResponse,
    SkillMapping,
    SkillSet,
    SkillMatchResult,
    SkillGap,
    SkillCategory,
    TaxonomyNode
)

logger = logging.getLogger(__name__)


class TaxonomySkillmatchService:
    """Service for skill taxonomy and matching"""

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        # Tier 1 service dependencies
        self.llm_service = LLMService(db, settings)

        # Import DocumentService for extracting skills from documents
        from app.tier_1.document_processing.document_service import DocumentService
        self.document_service = DocumentService(db, settings)

        # Taxonomy loaded dynamically from documents
        self.taxonomy: Dict[str, TaxonomyNode] = {}

        logger.info("✓ TaxonomySkillmatchService initialized with tier_1 services")

    async def _load_taxonomy_from_documents(self, session_id: Optional[str] = None) -> Dict[str, TaxonomyNode]:
        """Load skill taxonomy from uploaded job descriptions and competency frameworks"""
        try:
            documents = await self.document_service.list_documents(session_id=session_id)

            if not documents:
                logger.warning("No documents found for taxonomy extraction - returning empty taxonomy")
                return {}

            all_skills = []

            # Extract skills from first 10 documents
            for doc in documents[:10]:
                try:
                    chunks = await self.document_service.get_chunks_for_document(doc.id)
                    document_text = " ".join([chunk.get('content', '') for chunk in chunks[:5]])

                    skills = await self._extract_skills_from_text(document_text)
                    all_skills.extend(skills)
                except Exception as e:
                    logger.warning(f"Failed to extract skills from document {doc.id}: {e}")
                    continue

            # Build taxonomy from extracted skills
            taxonomy = {}
            for skill in all_skills:
                normalized = self._normalize_skill_name(skill.get("skill_name", ""))
                if normalized and normalized not in taxonomy:
                    taxonomy[normalized] = TaxonomyNode(
                        skill_name=skill.get("skill_name", ""),
                        category=SkillCategory(skill.get("category", "technical")),
                        synonyms=skill.get("synonyms", []),
                        related_skills=skill.get("related_skills", []),
                        child_skills=skill.get("child_skills", [])
                    )

            logger.info(f"✓ Loaded {len(taxonomy)} skills from documents")
            return taxonomy

        except Exception as e:
            logger.error(f"Failed to load taxonomy from documents: {e}")
            return {}

    async def _extract_skills_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract structured skill data using LLM"""
        prompt = f"""Extract all skills mentioned in this job description or competency framework:

{text[:3000]}

Extract technical skills, soft skills, leadership skills, domain knowledge, and methodologies.

Return JSON array:
[
  {{
    "skill_name": "Python",
    "category": "technical/soft_skills/leadership/domain_knowledge/methodologies",
    "synonyms": ["python programming", "python3"],
    "related_skills": ["Django", "FastAPI", "Flask"],
    "child_skills": ["Django", "FastAPI", "NumPy"]
  }}
]

Extract 20+ skills. Return ONLY valid JSON array."""

        try:
            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.1,
                max_tokens=1500
            )

            skills = json.loads(response.strip())
            return skills if isinstance(skills, list) else []

        except Exception as e:
            logger.warning(f"Skill extraction failed: {e}")
            return []

    async def map_skills_to_taxonomy(self, request: SkillTaxonomyRequest) -> SkillTaxonomyResponse:
        """Map skills to standard taxonomy"""
        logger.info(f"📚 Mapping {len(request.skills)} skills to taxonomy")

        # Load taxonomy from documents if not already loaded
        if not self.taxonomy:
            self.taxonomy = await self._load_taxonomy_from_documents(session_id=request.session_id)

        mappings: List[SkillMapping] = []
        unmapped: List[str] = []

        for skill in request.skills:
            mapping = await self._map_single_skill(
                skill,
                use_llm=request.use_llm_mapping,
                include_related=request.include_related_skills
            )

            if mapping:
                mappings.append(mapping)
            else:
                unmapped.append(skill)

        coverage = (len(mappings) / len(request.skills) * 100) if request.skills else 0.0

        logger.info(f"✓ Mapped {len(mappings)}/{len(request.skills)} skills ({coverage:.1f}% coverage)")

        return SkillTaxonomyResponse(
            mappings=mappings,
            unmapped_skills=unmapped,
            total_skills_processed=len(request.skills),
            taxonomy_coverage_percent=round(coverage, 2)
        )

    async def match_skillsets(self, request: SkillMatchRequest) -> SkillMatchResponse:
        """Match two skill sets and identify gaps"""
        logger.info(f"🔄 Matching skillsets: {len(request.source_skills)} source vs {len(request.target_skills)} target")

        # Build skill sets
        source_skillset = SkillSet(
            skills=request.source_skills,
            total_skills=len(request.source_skills)
        )
        target_skillset = SkillSet(
            skills=request.target_skills,
            total_skills=len(request.target_skills)
        )

        # Normalize skill names
        source_names = {self._normalize_skill_name(s.get("skill_name", "")) for s in request.source_skills}
        target_names = {self._normalize_skill_name(s.get("skill_name", "")) for s in request.target_skills}

        # Find matches and gaps
        matched_skills = list(source_names.intersection(target_names))
        missing_skills = list(target_names - source_names)

        # Calculate match percentage
        match_percentage = (len(matched_skills) / len(target_names) * 100) if target_names else 100.0

        # Analyze gaps if requested
        skill_gaps: List[SkillGap] = []
        if request.identify_gaps and missing_skills:
            skill_gaps = await self._analyze_skill_gaps(
                missing_skills,
                suggest_learning_paths=request.suggest_learning_paths
            )

        # Calculate category breakdown
        category_breakdown = self._calculate_category_breakdown(
            request.source_skills,
            request.target_skills
        )

        match_result = SkillMatchResult(
            source_skillset=source_skillset,
            target_skillset=target_skillset,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            skill_gaps=skill_gaps,
            match_percentage=round(match_percentage, 2),
            category_breakdown=category_breakdown
        )

        # Generate recommendations
        recommendations = self._generate_match_recommendations(match_result)

        # Determine match quality
        if match_percentage >= 80:
            match_quality = "excellent"
        elif match_percentage >= 60:
            match_quality = "good"
        elif match_percentage >= 40:
            match_quality = "fair"
        else:
            match_quality = "poor"

        logger.info(f"✓ Match complete: {match_percentage:.1f}% ({match_quality})")

        return SkillMatchResponse(
            match_result=match_result,
            recommendations=recommendations,
            match_quality=match_quality
        )

    async def _map_single_skill(
        self,
        skill: str,
        use_llm: bool = True,
        include_related: bool = True
    ) -> Optional[SkillMapping]:
        """Map a single skill to taxonomy"""
        normalized_skill = self._normalize_skill_name(skill)

        # Direct match
        if normalized_skill in self.taxonomy:
            node = self.taxonomy[normalized_skill]
            return SkillMapping(
                input_skill=skill,
                mapped_skill=node.skill_name,
                category=node.category,
                confidence_score=100.0,
                synonyms_found=[],
                related_skills=node.related_skills if include_related else []
            )

        # Synonym match
        for tax_skill, node in self.taxonomy.items():
            if normalized_skill in [s.lower() for s in node.synonyms]:
                return SkillMapping(
                    input_skill=skill,
                    mapped_skill=node.skill_name,
                    category=node.category,
                    confidence_score=95.0,
                    synonyms_found=[normalized_skill],
                    related_skills=node.related_skills if include_related else []
                )

        # LLM-based fuzzy matching
        if use_llm:
            llm_mapping = await self._llm_skill_mapping(skill)
            if llm_mapping:
                return llm_mapping

        return None

    async def _llm_skill_mapping(self, skill: str) -> Optional[SkillMapping]:
        """Use LLM to map skill to taxonomy"""
        taxonomy_skills = list(self.taxonomy.keys())

        prompt = f"""Map this skill to the closest match in the taxonomy:
Skill: {skill}
Taxonomy: {', '.join(taxonomy_skills)}

Return JSON: {{"mapped_skill": "skill_name", "confidence": 0-100, "category": "category"}}
If no good match, return {{"mapped_skill": null}}
Return ONLY valid JSON."""

        try:
            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.0,
                max_tokens=100
            )

            result = json.loads(response.strip())

            if result.get("mapped_skill"):
                mapped_name = result["mapped_skill"]
                normalized = self._normalize_skill_name(mapped_name)

                if normalized in self.taxonomy:
                    node = self.taxonomy[normalized]
                    return SkillMapping(
                        input_skill=skill,
                        mapped_skill=node.skill_name,
                        category=node.category,
                        confidence_score=float(result.get("confidence", 75)),
                        synonyms_found=[],
                        related_skills=node.related_skills
                    )
        except Exception as e:
            logger.warning(f"LLM mapping failed for '{skill}': {e}")

        return None

    async def _analyze_skill_gaps(
        self,
        missing_skills: List[str],
        suggest_learning_paths: bool = False
    ) -> List[SkillGap]:
        """Analyze skill gaps and suggest learning paths"""
        gaps: List[SkillGap] = []

        for skill in missing_skills:
            normalized = self._normalize_skill_name(skill)

            # Get category from taxonomy
            category = SkillCategory.TECHNICAL
            if normalized in self.taxonomy:
                category = self.taxonomy[normalized].category

            # Determine importance (simplified)
            importance = "high" if category in [SkillCategory.TECHNICAL, SkillCategory.DOMAIN_KNOWLEDGE] else "medium"

            learning_path = None
            learning_time = None

            if suggest_learning_paths:
                # Simplified learning path suggestion
                learning_path = [f"Beginner {skill}", f"Intermediate {skill}", f"Advanced {skill}"]
                learning_time = 12  # weeks

            gaps.append(SkillGap(
                missing_skill=skill,
                category=category,
                importance=importance,
                suggested_learning_path=learning_path,
                estimated_learning_time_weeks=learning_time
            ))

        return gaps

    def _calculate_category_breakdown(
        self,
        source_skills: List[Dict[str, Any]],
        target_skills: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate skill match breakdown by category"""
        breakdown = {}

        # Group target skills by category
        target_by_category: Dict[SkillCategory, List[str]] = {}
        for skill_dict in target_skills:
            skill_name = skill_dict.get("skill_name", "")
            normalized = self._normalize_skill_name(skill_name)

            category = SkillCategory.TECHNICAL
            if normalized in self.taxonomy:
                category = self.taxonomy[normalized].category

            if category not in target_by_category:
                target_by_category[category] = []
            target_by_category[category].append(normalized)

        # Check source against each category
        source_names = {self._normalize_skill_name(s.get("skill_name", "")) for s in source_skills}

        for category, target_list in target_by_category.items():
            matched = len([s for s in target_list if s in source_names])
            total = len(target_list)

            breakdown[category.value] = {
                "matched": matched,
                "total": total,
                "percentage": round((matched / total * 100) if total > 0 else 0, 2)
            }

        return breakdown

    def _generate_match_recommendations(self, match_result: SkillMatchResult) -> List[str]:
        """Generate recommendations based on match result"""
        recommendations = []

        if match_result.match_percentage >= 80:
            recommendations.append("Excellent skill match - candidate meets most requirements")
        elif match_result.match_percentage >= 60:
            recommendations.append("Good skill match - minor gaps can be addressed through training")
        else:
            recommendations.append("Significant skill gaps identified - extensive training may be required")

        if match_result.skill_gaps:
            critical_gaps = [g for g in match_result.skill_gaps if g.importance == "critical"]
            if critical_gaps:
                recommendations.append(f"{len(critical_gaps)} critical skill gaps identified")

        return recommendations

    def _normalize_skill_name(self, skill: str) -> str:
        """Normalize skill name for matching"""
        return skill.lower().strip().replace(" ", "").replace("-", "")
