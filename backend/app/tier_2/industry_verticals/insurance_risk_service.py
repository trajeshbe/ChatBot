"""Insurance Risk Assessor - Business Logic Service"""
import logging
from sqlalchemy.orm import Session
from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from .insurance_risk_schemas import *

logger = logging.getLogger(__name__)

class InsuranceRiskService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.llm_service = LLMService()

    async def assess_risk(self, request: AssessRiskRequest) -> AssessRiskResponse:
        try:
            risk_score = 50.0
            if request.applicant_age < 25:
                risk_score += 15
            elif request.applicant_age > 65:
                risk_score += 10
            risk_score += len(request.risk_factors) * 5
            risk_score = min(100.0, risk_score)
            
            if risk_score >= 70:
                risk_level = RiskLevel.HIGH
            elif risk_score >= 40:
                risk_level = RiskLevel.MEDIUM
            else:
                risk_level = RiskLevel.LOW
            
            base_premium = request.coverage_amount * 0.01
            premium = base_premium * (1 + risk_score / 100)
            
            prompt = f"Analyze insurance risk: {request.insurance_type.value}, age {request.applicant_age}, risk score {risk_score:.1f}. Provide 2 sentences on premium justification."
            insights = await self.llm_service.generate_response(prompt, model="gpt-4o-mini", temperature=0.3)
            
            return AssessRiskResponse(
                success=True, policy_id=request.policy_id, risk_score=round(risk_score, 2),
                risk_level=risk_level, premium_estimate=round(premium, 2),
                risk_factors_analysis=[{"factor": f, "impact": "medium"} for f in request.risk_factors[:3]],
                ai_insights=insights.strip()
            )
        except Exception as e:
            logger.error(f"Risk assessment error: {e}", exc_info=True)
            raise

    async def search_assessments(self, request: SearchAssessmentsRequest) -> SearchAssessmentsResponse:
        return SearchAssessmentsResponse(success=True, assessments=[], total_count=0)

    async def export_assessments(self, request: ExportAssessmentsRequest) -> ExportAssessmentsResponse:
        return ExportAssessmentsResponse(success=True, export_data={"format": request.format}, format=request.format)

    async def get_stats(self) -> InsuranceStatsResponse:
        return InsuranceStatsResponse(success=True, total_assessments=0, average_risk_score=0.0)

    async def get_status(self) -> StatusResponse:
        return StatusResponse(success=True, status="operational", capabilities=["Risk Assessment", "Premium Calculation", "AI Insights"])
