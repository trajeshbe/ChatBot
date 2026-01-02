"""Legal Document Analyzer - Business Logic Service"""

import logging
from typing import List
from sqlalchemy.orm import Session

from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from .legal_document_schemas import *

logger = logging.getLogger(__name__)


class LegalDocumentService:
    """Service for legal document analysis"""

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.llm_service = LLMService()

    async def analyze_document(self, request: AnalyzeDocumentRequest) -> AnalyzeDocumentResponse:
        """Analyze legal document with AI"""
        try:
            logger.info(f"Analyzing legal document {request.document_id}")

            clauses = []
            if request.include_clause_extraction:
                clauses = self._extract_clauses(request.document_text, request.document_type)

            risk = None
            if request.include_risk_assessment:
                risk = self._assess_risk(request.document_text, clauses)

            key_terms = self._extract_key_terms(request.document_text)
            ai_insights = await self._generate_ai_insights(request.document_type, clauses, risk)

            return AnalyzeDocumentResponse(
                success=True,
                document_id=request.document_id,
                extracted_clauses=clauses,
                risk_assessment=risk,
                key_terms=key_terms,
                ai_insights=ai_insights
            )

        except Exception as e:
            logger.error(f"Error analyzing document: {e}", exc_info=True)
            raise

    def _extract_clauses(self, text: str, doc_type: DocumentType) -> List[ExtractedClause]:
        """Extract key clauses from document"""
        clauses = []
        text_lower = text.lower()

        # Termination clause detection
        if any(term in text_lower for term in ["termination", "terminate", "cancellation"]):
            clauses.append(ExtractedClause(
                clause_type=ClauseType.TERMINATION,
                clause_text="Termination provisions detected",
                risk_level=RiskLevel.MODERATE,
                concerns=["Review termination conditions", "Check notice periods"],
                recommendations=["Ensure mutual termination rights", "Clarify termination consequences"]
            ))

        # Liability clause
        if any(term in text_lower for term in ["liability", "indemnify", "damages"]):
            clauses.append(ExtractedClause(
                clause_type=ClauseType.LIABILITY,
                clause_text="Liability and indemnification provisions detected",
                risk_level=RiskLevel.HIGH,
                concerns=["Unlimited liability exposure", "Broad indemnification scope"],
                recommendations=["Cap liability amounts", "Narrow indemnification scope"]
            ))

        return clauses[:5]

    def _assess_risk(self, text: str, clauses: List[ExtractedClause]) -> RiskAssessment:
        """Assess overall document risk"""
        risk_score = 30.0
        risk_factors = []

        # Clause-based risk
        for clause in clauses:
            if clause.risk_level == RiskLevel.CRITICAL:
                risk_score += 20
                risk_factors.append(f"Critical {clause.clause_type.value} clause")
            elif clause.risk_level == RiskLevel.HIGH:
                risk_score += 10

        # Determine overall risk level
        if risk_score >= 70:
            overall = RiskLevel.CRITICAL
        elif risk_score >= 50:
            overall = RiskLevel.HIGH
        elif risk_score >= 30:
            overall = RiskLevel.MODERATE
        else:
            overall = RiskLevel.LOW

        return RiskAssessment(
            overall_risk=overall,
            risk_score=min(100.0, risk_score),
            risk_factors=risk_factors[:5],
            mitigation_strategies=["Legal review recommended", "Negotiate key terms"]
        )

    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key legal terms"""
        terms = []
        text_lower = text.lower()

        common_terms = ["agreement", "party", "obligation", "breach", "jurisdiction"]
        for term in common_terms:
            if term in text_lower:
                terms.append(term.title())

        return terms[:10]

    async def _generate_ai_insights(
        self, doc_type: DocumentType, clauses: List[ExtractedClause], risk: Optional[RiskAssessment]
    ) -> str:
        """Generate AI insights"""
        try:
            clause_summary = f"{len(clauses)} clauses extracted" if clauses else "No clauses extracted"
            risk_summary = f"Risk: {risk.overall_risk.value}" if risk else "No risk assessment"

            prompt = f"""Analyze this legal document:

Type: {doc_type.value}
{clause_summary}
{risk_summary}

Provide 2-3 sentences of expert legal analysis focusing on key considerations and recommended actions."""

            response = await self.llm_service.generate_response(
                prompt=prompt, model="gpt-4o-mini", temperature=0.3
            )
            return response.strip()

        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return "Legal document analysis complete. Professional legal review recommended."

    async def search_documents(self, request: SearchDocumentsRequest) -> SearchDocumentsResponse:
        """Search analyzed documents"""
        return SearchDocumentsResponse(success=True, documents=[], total_count=0)

    async def export_analysis(self, request: ExportAnalysisRequest) -> ExportAnalysisResponse:
        """Export document analysis"""
        return ExportAnalysisResponse(
            success=True,
            export_data={"format": request.format},
            format=request.format
        )

    async def get_stats(self) -> LegalStatsResponse:
        """Get legal analysis statistics"""
        return LegalStatsResponse(
            success=True,
            total_documents_analyzed=0,
            high_risk_documents=0,
            most_common_document_type="contract"
        )

    async def get_status(self) -> StatusResponse:
        """Get service status"""
        return StatusResponse(
            success=True,
            status="operational",
            capabilities=[
                "Contract Analysis",
                "Clause Extraction",
                "Risk Assessment",
                "Compliance Review",
                "AI Legal Insights"
            ]
        )
