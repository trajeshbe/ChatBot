"""
Insurance Risk Assessment Service
Tier 2 Module: Industry Verticals

Risk assessment and premium calculation using uploaded insurance documents.
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

from .insurance_risk_schemas import *

logger = logging.getLogger(__name__)


class InsuranceRiskService:
    """
    Insurance risk assessment and premium calculation service.

    Assessment Process:
    1. Document Analysis → Extract policy data, medical records, claim history
    2. Risk Factor Identification → Identify risk factors from documents
    3. Risk Scoring → Calculate risk score using actuarial models
    4. Premium Calculation → Calculate premium based on risk and coverage
    5. Underwriting Decision → Approve/deny/refer policy
    6. AI Insights → Generate risk insights using LLM
    """

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.llm_service = LLMService(db, settings)
        self.document_service = DocumentService(db)
        logger.info("✓ InsuranceRiskService initialized with tier_1 services")

    async def assess_risk(
        self,
        request: AssessRiskRequest
    ) -> AssessRiskResponse:
        """Assess insurance risk using uploaded policy documents."""
        start_time = datetime.utcnow()

        logger.info(f"🛡️ Assessing risk: {request.insurance_type.value}, age {request.applicant_age}")

        try:
            # Step 1: Extract risk data from uploaded documents
            risk_data = await self._extract_risk_data_from_documents(request)

            # Step 2: Identify and analyze risk factors
            identified_risk_factors = await self._identify_risk_factors(
                request,
                risk_data
            )

            logger.info(f"Identified {len(identified_risk_factors)} risk factors")

            # Step 3: Calculate risk score
            risk_score, risk_level = self._calculate_risk_score(
                request,
                identified_risk_factors,
                risk_data
            )

            # Step 4: Calculate premium estimate
            premium_estimate = self._calculate_premium(
                request,
                risk_score,
                risk_level
            )

            # Step 5: Determine underwriting decision
            underwriting_decision = self._make_underwriting_decision(
                risk_score,
                risk_level,
                identified_risk_factors
            )

            # Step 6: Generate AI insights
            ai_insights = await self._generate_risk_insights(
                request,
                risk_score,
                risk_level,
                identified_risk_factors,
                premium_estimate
            )

            # Step 7: Generate recommendations
            recommendations = self._generate_recommendations(
                risk_level,
                identified_risk_factors,
                underwriting_decision
            )

            # Step 8: Store assessment
            await self._store_assessment(request, risk_score, premium_estimate)

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            return AssessRiskResponse(
                success=True,
                policy_id=request.policy_id or str(uuid.uuid4()),
                risk_score=round(risk_score, 2),
                risk_level=risk_level,
                premium_estimate=round(premium_estimate, 2),
                risk_factors_analysis=identified_risk_factors,
                underwriting_decision=underwriting_decision,
                ai_insights=ai_insights,
                recommendations=recommendations,
                assessment_date=datetime.utcnow().isoformat(),
                processing_time_seconds=processing_time,
                tier_1_services_used=["LLMService", "DocumentService"]
            )

        except Exception as e:
            logger.error(f"❌ Risk assessment error: {e}", exc_info=True)
            raise

    async def _extract_risk_data_from_documents(
        self,
        request: AssessRiskRequest
    ) -> Dict[str, Any]:
        """Extract risk-related data from uploaded insurance documents."""
        try:
            # Get documents for this session (policies, medical records, claims)
            documents = await self.document_service.list_documents(
                session_id=request.session_id,
                limit=50
            )

            if not documents:
                logger.warning(f"No documents found for session {request.session_id}")
                return {}

            # Extract risk data from documents
            all_risk_data = {
                "medical_conditions": [],
                "claim_history": [],
                "lifestyle_factors": [],
                "occupation_details": {}
            }

            for doc in documents[:10]:
                chunks = await self.document_service.get_chunks_for_document(doc.id)

                if not chunks:
                    continue

                # Combine chunks for context
                document_text = " ".join([chunk.get('content', '') for chunk in chunks[:5]])

                if len(document_text) < 100:
                    continue

                # Extract risk data using LLM
                risk_info = await self._extract_risk_info_from_text(
                    document_text,
                    request.insurance_type
                )

                # Merge extracted data
                all_risk_data["medical_conditions"].extend(risk_info.get("medical_conditions", []))
                all_risk_data["claim_history"].extend(risk_info.get("claim_history", []))
                all_risk_data["lifestyle_factors"].extend(risk_info.get("lifestyle_factors", []))

                if risk_info.get("occupation_details"):
                    all_risk_data["occupation_details"].update(risk_info["occupation_details"])

            logger.info(f"Extracted risk data: {len(all_risk_data['medical_conditions'])} conditions, {len(all_risk_data['claim_history'])} claims")

            return all_risk_data

        except Exception as e:
            logger.error(f"Failed to extract risk data: {str(e)}")
            return {}

    async def _extract_risk_info_from_text(
        self,
        text: str,
        insurance_type: InsuranceType
    ) -> Dict[str, Any]:
        """Extract insurance risk information from document text using LLM."""
        prompt = f"""Extract insurance risk information from the following document for {insurance_type.value} insurance.

Text:
{text[:3000]}

Extract:
- medical_conditions: List of medical conditions/diagnoses
- claim_history: List of past insurance claims with amounts
- lifestyle_factors: Smoking, alcohol use, dangerous hobbies, etc.
- occupation_details: Job title, industry, hazard level

Return a JSON object:
{{
  "medical_conditions": [
    {{"condition": "Hypertension", "severity": "moderate", "controlled": true}}
  ],
  "claim_history": [
    {{"date": "2024-05-01", "type": "auto", "amount": 5000, "at_fault": false}}
  ],
  "lifestyle_factors": [
    {{"factor": "smoking", "frequency": "occasional"}}
  ],
  "occupation_details": {{
    "job_title": "Software Engineer",
    "industry": "Technology",
    "hazard_level": "low"
  }}
}}

If no risk information found, return empty arrays/objects.
Return ONLY the JSON, no explanation."""

        try:
            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.1,
                max_tokens=1000
            )

            risk_info = json.loads(response.strip())
            logger.info(f"Extracted risk info with {len(risk_info.get('medical_conditions', []))} conditions")
            return risk_info

        except Exception as e:
            logger.warning(f"Failed to extract risk info: {str(e)}")
            return {
                "medical_conditions": [],
                "claim_history": [],
                "lifestyle_factors": [],
                "occupation_details": {}
            }

    async def _identify_risk_factors(
        self,
        request: AssessRiskRequest,
        risk_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify and analyze risk factors from request and extracted data."""
        risk_factors = []

        # Age-based risk factors
        if request.applicant_age < 25:
            risk_factors.append({
                "factor": "Young driver (under 25)" if request.insurance_type == InsuranceType.AUTO else "Young age",
                "impact": "high",
                "score_increase": 15,
                "description": "Higher risk due to limited experience"
            })
        elif request.applicant_age > 70:
            risk_factors.append({
                "factor": "Senior age (over 70)",
                "impact": "medium",
                "score_increase": 10,
                "description": "Increased health and mobility risks"
            })

        # Medical conditions from documents
        for condition in risk_data.get("medical_conditions", []):
            severity = condition.get("severity", "unknown")
            impact_score = {
                "severe": 20,
                "moderate": 10,
                "mild": 5
            }.get(severity, 5)

            risk_factors.append({
                "factor": f"Medical condition: {condition.get('condition', 'Unknown')}",
                "impact": severity,
                "score_increase": impact_score,
                "description": f"Pre-existing medical condition ({severity} severity)"
            })

        # Claim history from documents
        claim_history = risk_data.get("claim_history", [])
        if len(claim_history) > 0:
            at_fault_claims = sum(1 for c in claim_history if c.get("at_fault", False))
            total_claim_amount = sum(c.get("amount", 0) for c in claim_history)

            if at_fault_claims > 0:
                risk_factors.append({
                    "factor": f"{at_fault_claims} at-fault claim(s)",
                    "impact": "high",
                    "score_increase": at_fault_claims * 10,
                    "description": f"Total claim amount: ${total_claim_amount:,.0f}"
                })
            else:
                risk_factors.append({
                    "factor": f"{len(claim_history)} not-at-fault claim(s)",
                    "impact": "low",
                    "score_increase": len(claim_history) * 2,
                    "description": "Claims without fault assignment"
                })

        # Lifestyle factors from documents
        for lifestyle in risk_data.get("lifestyle_factors", []):
            factor_name = lifestyle.get("factor", "")
            if "smoking" in factor_name.lower():
                risk_factors.append({
                    "factor": "Smoking",
                    "impact": "high",
                    "score_increase": 15,
                    "description": "Increased health risks"
                })
            elif "alcohol" in factor_name.lower():
                risk_factors.append({
                    "factor": "Alcohol use",
                    "impact": "medium",
                    "score_increase": 8,
                    "description": "Moderate health and liability risks"
                })

        # Occupation hazard from documents
        occupation = risk_data.get("occupation_details", {})
        hazard_level = occupation.get("hazard_level", "").lower()
        if hazard_level == "high":
            risk_factors.append({
                "factor": f"High-hazard occupation: {occupation.get('job_title', 'Unknown')}",
                "impact": "high",
                "score_increase": 18,
                "description": "Occupation involves significant physical risk"
            })
        elif hazard_level == "medium":
            risk_factors.append({
                "factor": f"Medium-hazard occupation: {occupation.get('job_title', 'Unknown')}",
                "impact": "medium",
                "score_increase": 8,
                "description": "Occupation involves moderate risk"
            })

        # User-provided risk factors
        for user_factor in request.risk_factors:
            risk_factors.append({
                "factor": user_factor,
                "impact": "medium",
                "score_increase": 5,
                "description": "User-reported risk factor"
            })

        return risk_factors

    def _calculate_risk_score(
        self,
        request: AssessRiskRequest,
        risk_factors: List[Dict[str, Any]],
        risk_data: Dict[str, Any]
    ) -> tuple[float, RiskLevel]:
        """Calculate overall risk score using actuarial model."""

        # Base risk score by insurance type
        base_scores = {
            InsuranceType.LIFE: 30.0,
            InsuranceType.HEALTH: 35.0,
            InsuranceType.AUTO: 40.0,
            InsuranceType.HOME: 25.0,
            InsuranceType.TRAVEL: 20.0
        }

        risk_score = base_scores.get(request.insurance_type, 35.0)

        # Add risk factor scores
        for factor in risk_factors:
            risk_score += factor.get("score_increase", 0)

        # Cap risk score
        risk_score = min(100.0, max(0.0, risk_score))

        # Determine risk level
        if risk_score >= 70:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 40:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        return risk_score, risk_level

    def _calculate_premium(
        self,
        request: AssessRiskRequest,
        risk_score: float,
        risk_level: RiskLevel
    ) -> float:
        """Calculate insurance premium based on risk."""

        # Base premium as percentage of coverage
        base_rates = {
            InsuranceType.LIFE: 0.008,  # 0.8% of coverage
            InsuranceType.HEALTH: 0.015,  # 1.5% of coverage
            InsuranceType.AUTO: 0.025,  # 2.5% of coverage
            InsuranceType.HOME: 0.012,  # 1.2% of coverage
            InsuranceType.TRAVEL: 0.005  # 0.5% of coverage
        }

        base_rate = base_rates.get(request.insurance_type, 0.01)
        base_premium = request.coverage_amount * base_rate

        # Apply risk multiplier
        risk_multiplier = 1 + (risk_score / 100)

        # Calculate final premium
        premium = base_premium * risk_multiplier

        return premium

    def _make_underwriting_decision(
        self,
        risk_score: float,
        risk_level: RiskLevel,
        risk_factors: List[Dict[str, Any]]
    ) -> str:
        """Make underwriting decision based on risk assessment."""

        high_impact_factors = sum(1 for f in risk_factors if f.get("impact") == "high")

        if risk_score >= 85 or high_impact_factors >= 3:
            return "DECLINED - Risk exceeds underwriting guidelines"
        elif risk_score >= 70 or high_impact_factors >= 2:
            return "REFERRED - Requires manual underwriter review"
        elif risk_score >= 50:
            return "APPROVED - Standard terms with risk loading"
        else:
            return "APPROVED - Preferred rates offered"

    async def _generate_risk_insights(
        self,
        request: AssessRiskRequest,
        risk_score: float,
        risk_level: RiskLevel,
        risk_factors: List[Dict[str, Any]],
        premium_estimate: float
    ) -> str:
        """Generate AI-powered risk assessment insights."""

        top_factors = sorted(risk_factors, key=lambda x: x.get("score_increase", 0), reverse=True)[:3]
        factors_summary = ", ".join([f["factor"] for f in top_factors]) if top_factors else "No significant factors"

        prompt = f"""Generate a concise insurance risk assessment insight:

Policy Details:
- Type: {request.insurance_type.value}
- Coverage Amount: ${request.coverage_amount:,.0f}
- Applicant Age: {request.applicant_age}

Risk Assessment:
- Risk Score: {risk_score:.1f}/100
- Risk Level: {risk_level.value}
- Premium Estimate: ${premium_estimate:,.2f}
- Top Risk Factors: {factors_summary}

Generate 2-3 sentences analyzing:
1. Overall risk profile assessment
2. Key factors driving the premium
3. Recommendations for risk mitigation

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
            return f"Risk assessment complete. Risk score: {risk_score:.1f}/100 ({risk_level.value}). Estimated premium: ${premium_estimate:,.2f}."

    def _generate_recommendations(
        self,
        risk_level: RiskLevel,
        risk_factors: List[Dict[str, Any]],
        underwriting_decision: str
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if risk_level == RiskLevel.HIGH:
            recommendations.append("Consider risk mitigation strategies to reduce premium")
            recommendations.append("Review and update policy documentation for accuracy")

        # Specific recommendations based on risk factors
        for factor in risk_factors:
            factor_name = factor.get("factor", "").lower()

            if "smoking" in factor_name:
                recommendations.append("Complete smoking cessation program for premium reduction")
            elif "claim" in factor_name and "at-fault" in factor_name:
                recommendations.append("Consider defensive driving course to improve record")
            elif "medical" in factor_name:
                recommendations.append("Provide medical records showing condition management")

        if "DECLINED" in underwriting_decision:
            recommendations.append("Contact underwriting for appeal process and alternative coverage options")
        elif "REFERRED" in underwriting_decision:
            recommendations.append("Prepare additional documentation for underwriter review")

        recommendations.append("Upload medical records, claim history, and policy documents for accurate assessment")

        return recommendations[:5]  # Limit to top 5

    async def _store_assessment(
        self,
        request: AssessRiskRequest,
        risk_score: float,
        premium_estimate: float
    ):
        """Store risk assessment in database."""
        try:
            from app.models.database_enhanced import InsuranceRiskResults

            assessment_record = InsuranceRiskResults(
                id=uuid.uuid4(),
                assessment_id=uuid.uuid4(),
                module_id="insurance-risk",
                session_id=request.session_id,
                project_id=uuid.UUID(request.project_id) if request.project_id else None,
                assessment_data={
                    "policy_id": request.policy_id,
                    "insurance_type": request.insurance_type.value,
                    "risk_score": risk_score,
                    "premium_estimate": premium_estimate,
                    "applicant_age": request.applicant_age,
                    "coverage_amount": request.coverage_amount
                },
                created_at=datetime.utcnow()
            )

            self.db.add(assessment_record)
            self.db.commit()
            logger.info(f"✓ Stored risk assessment for policy {request.policy_id}")

        except Exception as e:
            logger.error(f"Failed to store assessment: {str(e)}")

    async def search_assessments(
        self,
        request: SearchAssessmentsRequest
    ) -> SearchAssessmentsResponse:
        """Search historical risk assessments."""
        # Placeholder for search functionality
        return SearchAssessmentsResponse(
            success=True,
            assessments=[],
            total_count=0
        )

    async def export_assessments(
        self,
        request: ExportAssessmentsRequest
    ) -> ExportAssessmentsResponse:
        """Export assessments to specified format."""
        # Placeholder for export functionality
        return ExportAssessmentsResponse(
            success=True,
            export_data={"format": request.format},
            format=request.format
        )

    async def get_stats(self) -> InsuranceStatsResponse:
        """Get assessment statistics."""
        return InsuranceStatsResponse(
            success=True,
            total_assessments=0,
            average_risk_score=0.0
        )

    async def get_status(self) -> StatusResponse:
        """Get service status and capabilities."""
        return StatusResponse(
            success=True,
            status="operational",
            description="Insurance Risk Assessment: Comprehensive risk assessment and premium calculation using uploaded policy documents and medical records",
            tier_2_modules_used=[],
            capabilities=[
                "Extract risk data from insurance documents using LLM",
                "Identify medical conditions, claim history, and lifestyle factors",
                "Calculate risk scores using actuarial models",
                "Premium calculation with risk-based pricing",
                "Underwriting decision automation (approve/refer/decline)",
                "AI-powered risk insights and mitigation recommendations",
                "Support for 5 insurance types (life, health, auto, home, travel)"
            ]
        )
