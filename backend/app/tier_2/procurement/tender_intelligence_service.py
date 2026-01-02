"""
Tender Intelligence Service
Tier 2 Module: Procurement

Tender/RFP analysis using tier_1 services.
100% tier_1 service reuse - zero new dependencies.
"""

import uuid
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from app.tier_1.document_processing.document_service import DocumentService

from .tender_intelligence_schemas import (
    TenderAnalysisRequest,
    TenderAnalysisResponse,
    TenderRequirement,
    EvaluationCriterion,
    TenderType,
    BidRecommendation
)

logger = logging.getLogger(__name__)


class TenderIntelligenceService:
    """Tender/RFP analysis service."""

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.llm_service = LLMService(db, settings)
        self.document_service = DocumentService(db, settings)
        logger.info("✓ TenderIntelligenceService initialized")

    async def analyze_tender(self, request: TenderAnalysisRequest) -> TenderAnalysisResponse:
        """Analyze tender document."""
        start_time = datetime.utcnow()
        analysis_id = str(uuid.uuid4())

        logger.info(f"📋 Analyzing tender document {request.document_id}")

        try:
            # Extract tender text
            from app.models.database import Document
            doc = self.db.query(Document).filter(Document.id == request.document_id).first()
            if not doc:
                raise ValueError(f"Document {request.document_id} not found")

            chunks = await self.document_service.get_document_chunks(request.document_id)
            text = "\n".join([chunk.content for chunk in chunks[:10]])

            # Analyze using LLM
            analysis_data = await self._analyze_with_llm(text, request)

            # Generate bid recommendation
            bid_rec, rec_reason, win_prob = await self._generate_bid_recommendation(analysis_data)

            # Store analysis
            await self._store_analysis(request, analysis_data, bid_rec)

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            return TenderAnalysisResponse(
                analysis_id=analysis_id,
                document_id=request.document_id,
                tender_summary=analysis_data.get("summary", {}),
                tender_type=TenderType(analysis_data.get("tender_type", "rfp")),
                requirements=analysis_data.get("requirements", []),
                evaluation_criteria=analysis_data.get("evaluation_criteria", []),
                key_deadlines=analysis_data.get("deadlines", []),
                estimated_contract_value=analysis_data.get("contract_value"),
                contract_duration_months=analysis_data.get("duration_months"),
                bid_viability=analysis_data.get("viability", {}),
                compliance_requirements=analysis_data.get("compliance", []),
                bid_recommendation=bid_rec,
                recommendation_reason=rec_reason,
                win_probability=win_prob,
                confidence_level=0.75,
                processing_time_seconds=processing_time,
                tier_1_services_used=["LLMService", "DocumentService"]
            )

        except Exception as e:
            logger.error(f"❌ Tender analysis failed: {str(e)}", exc_info=True)
            raise

    async def _analyze_with_llm(self, text: str, request: TenderAnalysisRequest) -> Dict[str, Any]:
        """Analyze tender using LLM."""
        prompt = f"""Analyze this tender/RFP document:

{text[:3000]}

Extract the following:
1. Tender type (open_tender, rfp, rfq, etc.)
2. Summary (title, issuer, scope)
3. Requirements (technical, financial, legal) - at least 3
4. Evaluation criteria with weights
5. Key deadlines
6. Estimated contract value
7. Contract duration in months
8. Compliance requirements

Return JSON:
{{
    "tender_type": "rfp",
    "summary": {{"title": "...", "issuer": "...", "scope": "..."}},
    "requirements": [
        {{"category": "technical", "description": "...", "mandatory": true}}
    ],
    "evaluation_criteria": [
        {{"name": "Price", "description": "...", "weight": 0.4}}
    ],
    "deadlines": [{{"type": "submission", "date": "2024-12-31"}}],
    "contract_value": 1000000.0,
    "duration_months": 12,
    "viability": {{"competitive": true, "resources_available": true}},
    "compliance": ["ISO9001", "Financial audits"]
}}

Return ONLY valid JSON."""

        response = await self.llm_service.generate_response(
            prompt=prompt, model="gpt-4o-mini", temperature=0.0, max_tokens=1500
        )

        return json.loads(response.strip())

    async def _generate_bid_recommendation(self, data: Dict[str, Any]) -> tuple:
        """Generate bid/no-bid recommendation."""
        viability = data.get("viability", {})
        competitive = viability.get("competitive", False)
        resources = viability.get("resources_available", False)

        if competitive and resources:
            return BidRecommendation.STRONG_BID, "Strong alignment with capabilities and resources available", 0.75
        elif competitive or resources:
            return BidRecommendation.BID_WITH_CONDITIONS, "Partial alignment - assess resource gaps", 0.50
        else:
            return BidRecommendation.NO_BID, "Low competitiveness or resource constraints", 0.25

    async def _store_analysis(self, request: TenderAnalysisRequest, data: Dict, bid_rec: BidRecommendation):
        """Store tender analysis."""
        try:
            from app.models.database_enhanced import TenderAnalysisResults

            record = TenderAnalysisResults(
                id=uuid.uuid4(),
                analysis_id=uuid.uuid4(),
                module_id="tender-intelligence",
                document_id=uuid.UUID(request.document_id),
                session_id=request.session_id,
                project_id=uuid.UUID(request.project_id) if request.project_id else None,
                analysis_data={"summary": data.get("summary"), "bid_recommendation": bid_rec.value},
                created_at=datetime.utcnow()
            )

            self.db.add(record)
            self.db.commit()
            logger.info(f"✓ Stored tender analysis")

        except Exception as e:
            logger.error(f"Failed to store analysis: {str(e)}")
