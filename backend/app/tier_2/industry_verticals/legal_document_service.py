"""Legal Document Analyzer - Business Logic Service"""

import logging
from typing import List, Any
from sqlalchemy.orm import Session

from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from .legal_document_schemas import *

logger = logging.getLogger(__name__)


class LegalDocumentService:
    """Service for legal document analysis"""

    def __init__(self, db: Session, settings: Settings, config: Optional[Dict[str, Any]] = None):
        self.db = db
        self.settings = settings
        self.config = config or {}
        self.llm_service = LLMService()

        # Import DocumentService for extracting legal documents
        from app.tier_1.document_processing.document_service import DocumentService
        self.document_service = DocumentService(db, settings)

    async def analyze_document(self, request: AnalyzeDocumentRequest) -> AnalyzeDocumentResponse:
        """Analyze legal document with AI"""
        try:
            logger.info(f"Analyzing legal document {request.document_id}")

            # Extract document text if document_id provided
            document_text = request.document_text
            if request.document_id and not document_text:
                document_text = await self._extract_document_text(request.document_id)

            clauses = []
            if request.include_clause_extraction:
                clauses = await self._extract_clauses_llm(document_text, request.document_type)

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

    async def _extract_document_text(self, document_id: str) -> str:
        """Extract text from uploaded legal document"""
        try:
            chunks = await self.document_service.get_chunks_for_document(document_id)
            text = " ".join([chunk.get('content', '') for chunk in chunks])
            logger.info(f"Extracted {len(text)} characters from document {document_id}")
            return text
        except Exception as e:
            logger.error(f"Failed to extract document text: {e}")
            return ""

    async def _extract_clauses_llm(self, text: str, doc_type: DocumentType) -> List[ExtractedClause]:
        """Extract legal clauses using LLM-based analysis"""
        if not text:
            return []

        prompt = f"""Extract key legal clauses from this {doc_type.value} document:

{text[:5000]}

Return JSON array:
[
  {{
    "clause_type": "termination/liability/confidentiality/payment/indemnification/jurisdiction/dispute_resolution/intellectual_property/warranty/limitation_of_liability",
    "clause_text": "Full text of the clause",
    "risk_level": "low/moderate/high/critical",
    "concerns": ["concern1", "concern2"],
    "recommendations": ["recommendation1", "recommendation2"]
  }}
]

Extract all important clauses. Return ONLY valid JSON array."""

        try:
            # Get LLM parameters from module config
            llm_config = self.config.get('llm', {}).get('default', {})
            model = llm_config.get('model', 'gpt-4o-mini')
            temperature = llm_config.get('temperature', 0.1)
            max_tokens = llm_config.get('max_tokens', 2000)

            response = await self.llm_service.generate_response(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

            clauses_data = json.loads(response.strip())

            clauses = []
            for clause in clauses_data:
                clauses.append(ExtractedClause(
                    clause_type=ClauseType(clause.get("clause_type", "confidentiality")),
                    clause_text=clause.get("clause_text", ""),
                    risk_level=RiskLevel(clause.get("risk_level", "moderate")),
                    concerns=clause.get("concerns", []),
                    recommendations=clause.get("recommendations", [])
                ))

            return clauses[:10]

        except Exception as e:
            logger.warning(f"LLM clause extraction failed: {e}, using keyword fallback")
            return self._extract_clauses_fallback(text, doc_type)

    def _extract_clauses_fallback(self, text: str, doc_type: DocumentType) -> List[ExtractedClause]:
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

            # Get LLM parameters from module config
            llm_config = self.config.get('llm', {}).get('default', {})
            model = llm_config.get('model', 'gpt-4o-mini')
            temperature = llm_config.get('temperature', 0.3)

            response = await self.llm_service.generate_response(
                prompt=prompt,
                model=model,
                temperature=temperature
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
