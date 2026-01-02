"""
Vendor Recommendation Service
Tier 2 Module: Procurement

Vendor recommendation and evaluation using tier_1 services.
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

from .vendor_recommendation_schemas import (
    VendorRecommendationRequest,
    VendorRecommendationResponse,
    VendorRecommendation,
    VendorProfile,
    VendorPerformance,
    VendorScore,
    VendorCategory,
    EvaluationCriteria,
    SelectionCriteria
)

logger = logging.getLogger(__name__)


# Mock vendor database (in production, this would come from a real database)
MOCK_VENDORS = {
    VendorCategory.IT_HARDWARE: [
        {"vendor_id": "v1", "vendor_name": "TechSupply Corp", "avg_cost_per_unit": 100, "quality_rating": 4.5, "delivery_days": 3, "certifications": ["ISO9001"]},
        {"vendor_id": "v2", "vendor_name": "Hardware Plus", "avg_cost_per_unit": 95, "quality_rating": 4.2, "delivery_days": 5, "certifications": ["ISO9001", "ISO14001"]},
        {"vendor_id": "v3", "vendor_name": "Global IT Solutions", "avg_cost_per_unit": 110, "quality_rating": 4.8, "delivery_days": 2, "certifications": ["ISO9001", "SOC2"]},
    ],
    VendorCategory.IT_SERVICES: [
        {"vendor_id": "v4", "vendor_name": "CloudExperts Inc", "avg_cost_per_unit": 150, "quality_rating": 4.7, "delivery_days": 7, "certifications": ["SOC2", "ISO27001"]},
        {"vendor_id": "v5", "vendor_name": "DevOps Masters", "avg_cost_per_unit": 140, "quality_rating": 4.4, "delivery_days": 10, "certifications": ["ISO27001"]},
    ],
    VendorCategory.PROFESSIONAL_SERVICES: [
        {"vendor_id": "v6", "vendor_name": "ConsultPro LLC", "avg_cost_per_unit": 200, "quality_rating": 4.6, "delivery_days": 14, "certifications": ["CPA"]},
        {"vendor_id": "v7", "vendor_name": "Advisory Group", "avg_cost_per_unit": 180, "quality_rating": 4.3, "delivery_days": 10, "certifications": []},
    ]
}


class VendorRecommendationService:
    """
    Vendor recommendation service.

    Recommendation Process:
    1. Requirement Analysis → Understand procurement requirements using LLM
    2. Vendor Discovery → Find relevant vendors from database
    3. Criteria Scoring → Score vendors against weighted criteria
    4. Performance Analysis → Analyze historical performance data
    5. Risk Assessment → Identify potential risks
    6. Ranking → Rank vendors by total score
    7. Justification → Generate recommendation reasons using LLM
    8. Confidence Calculation → Calculate recommendation confidence
    """

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

        # Tier 1 service dependencies
        self.llm_service = LLMService(db, settings)

        logger.info("✓ VendorRecommendationService initialized with tier_1 services")

    async def recommend_vendors(
        self,
        request: VendorRecommendationRequest
    ) -> VendorRecommendationResponse:
        """Generate vendor recommendations based on criteria."""
        start_time = datetime.utcnow()

        logger.info(f"🏢 Generating vendor recommendations for {request.category.value}")

        try:
            # Step 1: Get candidate vendors
            candidate_vendors = self._get_candidate_vendors(request)

            logger.info(f"Found {len(candidate_vendors)} candidate vendors")

            # Step 2: Score each vendor
            vendor_scores = []
            for vendor in candidate_vendors:
                score = self._calculate_vendor_score(vendor, request)
                vendor_scores.append(score)

            # Step 3: Filter by minimum quality rating
            vendor_scores = [
                v for v in vendor_scores
                if vendor.get("quality_rating", 0) >= request.minimum_quality_rating
            ]

            # Step 4: Sort by total score
            vendor_scores.sort(key=lambda x: x.total_score, reverse=True)

            # Step 5: Take top N
            top_vendors = vendor_scores[:request.top_n]

            # Step 6: Generate recommendations with LLM justifications
            recommendations = []
            for rank, vendor_score in enumerate(top_vendors, 1):
                vendor = next(v for v in candidate_vendors if v["vendor_id"] == vendor_score.vendor_id)

                recommendation = await self._create_recommendation(
                    vendor,
                    vendor_score,
                    rank,
                    request
                )
                recommendations.append(recommendation)

            # Step 7: Store recommendations
            await self._store_recommendations(request, recommendations)

            # Step 8: Build response
            processing_time = (datetime.utcnow() - start_time).total_seconds()

            response = VendorRecommendationResponse(
                category=request.category,
                requirement_description=request.requirement_description,
                total_vendors_evaluated=len(candidate_vendors),
                recommendations=recommendations,
                selection_criteria_used=request.selection_criteria,
                processing_time_seconds=processing_time,
                tier_1_services_used=["LLMService"]
            )

            logger.info(f"✓ Generated {len(recommendations)} vendor recommendations")
            return response

        except Exception as e:
            logger.error(f"❌ Recommendation generation failed: {str(e)}", exc_info=True)
            raise

    def _get_candidate_vendors(
        self,
        request: VendorRecommendationRequest
    ) -> List[Dict[str, Any]]:
        """Get candidate vendors for the category."""
        # In production, query from database
        # For now, use mock data
        vendors = MOCK_VENDORS.get(request.category, [])

        # Filter by exclusions
        if request.exclude_vendor_ids:
            vendors = [v for v in vendors if v["vendor_id"] not in request.exclude_vendor_ids]

        # Filter by certifications
        if request.required_certifications:
            vendors = [
                v for v in vendors
                if all(cert in v.get("certifications", []) for cert in request.required_certifications)
            ]

        # Filter by budget
        if request.budget_range_max:
            vendors = [v for v in vendors if v.get("avg_cost_per_unit", 0) <= request.budget_range_max]

        # Filter by delivery time
        if request.required_delivery_days:
            vendors = [v for v in vendors if v.get("delivery_days", 999) <= request.required_delivery_days]

        return vendors

    def _calculate_vendor_score(
        self,
        vendor: Dict[str, Any],
        request: VendorRecommendationRequest
    ) -> VendorScore:
        """Calculate weighted score for vendor."""
        criteria_scores = {}
        total_weight = 0.0

        # Default criteria if none specified
        if not request.selection_criteria:
            criteria = [
                SelectionCriteria(criteria=EvaluationCriteria.COST, weight=0.3),
                SelectionCriteria(criteria=EvaluationCriteria.QUALITY, weight=0.3),
                SelectionCriteria(criteria=EvaluationCriteria.DELIVERY_TIME, weight=0.2),
                SelectionCriteria(criteria=EvaluationCriteria.CERTIFICATIONS, weight=0.2),
            ]
        else:
            criteria = request.selection_criteria

        # Calculate scores for each criterion
        for criterion in criteria:
            if criterion.criteria == EvaluationCriteria.COST:
                # Lower cost = higher score
                cost = vendor.get("avg_cost_per_unit", 100)
                max_cost = request.budget_range_max or 200
                score = max(0, (max_cost - cost) / max_cost * 100)

            elif criterion.criteria == EvaluationCriteria.QUALITY:
                # Quality rating out of 5 → convert to 100
                quality = vendor.get("quality_rating", 3.0)
                score = (quality / 5.0) * 100

            elif criterion.criteria == EvaluationCriteria.DELIVERY_TIME:
                # Faster delivery = higher score
                delivery = vendor.get("delivery_days", 30)
                max_delivery = request.required_delivery_days or 30
                score = max(0, (max_delivery - delivery) / max_delivery * 100)

            elif criterion.criteria == EvaluationCriteria.CERTIFICATIONS:
                # More certifications = higher score
                certs = len(vendor.get("certifications", []))
                score = min(100, certs * 25)  # Each cert = 25 points

            else:
                # Default score
                score = 70.0

            criteria_scores[criterion.criteria.value] = score * criterion.weight
            total_weight += criterion.weight

        # Calculate total score
        total_score = sum(criteria_scores.values()) / total_weight if total_weight > 0 else 0

        # Identify strengths and weaknesses
        strengths = []
        weaknesses = []

        if vendor.get("quality_rating", 0) >= 4.5:
            strengths.append("Excellent quality rating")
        elif vendor.get("quality_rating", 0) < 3.5:
            weaknesses.append("Below average quality rating")

        if vendor.get("delivery_days", 999) <= 3:
            strengths.append("Fast delivery time")
        elif vendor.get("delivery_days", 999) >= 14:
            weaknesses.append("Slow delivery time")

        if len(vendor.get("certifications", [])) >= 2:
            strengths.append("Multiple industry certifications")

        return VendorScore(
            vendor_id=vendor["vendor_id"],
            vendor_name=vendor["vendor_name"],
            total_score=total_score,
            criteria_scores=criteria_scores,
            strengths=strengths,
            weaknesses=weaknesses,
            risk_factors=[],
            opportunities=[]
        )

    async def _create_recommendation(
        self,
        vendor: Dict[str, Any],
        vendor_score: VendorScore,
        rank: int,
        request: VendorRecommendationRequest
    ) -> VendorRecommendation:
        """Create vendor recommendation with LLM-generated justification."""

        # Generate recommendation reason using LLM
        prompt = f"""Generate a concise recommendation reason for this vendor:

Vendor: {vendor_score.vendor_name}
Category: {request.category.value}
Requirement: {request.requirement_description}
Total Score: {vendor_score.total_score:.1f}/100
Rank: #{rank}

Strengths:
{chr(10).join(f'- {s}' for s in vendor_score.strengths)}

Weaknesses:
{chr(10).join(f'- {w}' for w in vendor_score.weaknesses)}

Generate a 1-2 sentence recommendation reason explaining why this vendor is a good fit.
Return ONLY the recommendation text, no prefix."""

        try:
            recommendation_reason = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=100
            )
        except:
            recommendation_reason = f"Ranked #{rank} with a score of {vendor_score.total_score:.1f}/100 based on evaluation criteria."

        return VendorRecommendation(
            vendor_id=vendor["vendor_id"],
            vendor_name=vendor["vendor_name"],
            category=request.category,
            total_score=vendor_score.total_score,
            rank=rank,
            recommendation_reason=recommendation_reason.strip(),
            key_strengths=vendor_score.strengths,
            potential_risks=vendor_score.weaknesses,
            estimated_cost=vendor.get("avg_cost_per_unit"),
            estimated_delivery_days=vendor.get("delivery_days"),
            confidence_level=min(1.0, vendor_score.total_score / 100.0),
            performance_metrics=VendorPerformance(
                vendor_id=vendor["vendor_id"],
                vendor_name=vendor["vendor_name"],
                quality_rating=vendor.get("quality_rating"),
                avg_delivery_days=vendor.get("delivery_days"),
                certifications=vendor.get("certifications", [])
            )
        )

    async def _store_recommendations(
        self,
        request: VendorRecommendationRequest,
        recommendations: List[VendorRecommendation]
    ):
        """Store recommendations in database."""
        try:
            from app.models.database_enhanced import VendorRecommendationResults

            for rec in recommendations:
                rec_record = VendorRecommendationResults(
                    id=uuid.uuid4(),
                    recommendation_id=uuid.UUID(rec.recommendation_id),
                    module_id="vendor-recommendation",
                    session_id=request.session_id,
                    project_id=uuid.UUID(request.project_id) if request.project_id else None,
                    recommendation_data={
                        "vendor_id": rec.vendor_id,
                        "vendor_name": rec.vendor_name,
                        "category": rec.category.value,
                        "total_score": rec.total_score,
                        "rank": rec.rank,
                        "recommendation_reason": rec.recommendation_reason,
                        "confidence_level": rec.confidence_level
                    },
                    created_at=datetime.utcnow()
                )

                self.db.add(rec_record)

            self.db.commit()
            logger.info(f"✓ Stored {len(recommendations)} recommendations")

        except Exception as e:
            logger.error(f"Failed to store recommendations: {str(e)}")
