"""
Mine Scope Service
Tier 2 Module: Construction

Analyzes mining scope documents using tier_1 services.
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
from app.tier_1.document_processing.vision_service import VisionService
from app.tier_1.document_processing.document_service import DocumentService

from .mine_scope_schemas import (
    MineScopeAnalysisRequest,
    MineScopeAnalysisResponse,
    ScopeSearchRequest,
    ScopeSearchResponse,
    ScopeComparisonRequest,
    ScopeComparisonResponse,
    ScopeRequirement,
    ExtractedMetrics,
    IdentifiedRisk,
    ComplianceRequirement,
    MineScopeType,
    MiningSector,
    MiningMethod
)

logger = logging.getLogger(__name__)


class MineScopeService:
    """
    Analyze mining scope documents for requirements and metrics.

    Analysis Pipeline:
    1. Document Processing → Extract text and diagrams
    2. Classification → Identify scope type, sector, method
    3. Requirements Extraction → Extract scope requirements
    4. Metrics Extraction → Extract quantitative metrics
    5. Risk Identification → Identify and categorize risks
    6. Compliance Extraction → Extract regulatory requirements
    7. Summary Generation → Generate executive summary
    """

    def __init__(self, db: Session, settings: Settings, config: Optional[Dict[str, Any]] = None):
        self.db = db
        self.settings = settings
        self.config = config or {}

        # Tier 1 service dependencies
        self.llm_service = LLMService()
        self.vision_service = VisionService(db, settings)
        self.document_service = DocumentService(db, settings)

        logger.info("✓ MineScopeService initialized with tier_1 services")
        if config:
            logger.info(f"✓ Using module config with model: {config.get('llm', {}).get('default', {}).get('model', 'default')}")

    async def analyze_scope(
        self,
        request: MineScopeAnalysisRequest
    ) -> MineScopeAnalysisResponse:
        """Analyze a mining scope document."""
        start_time = datetime.utcnow()
        analysis_id = str(uuid.uuid4())

        logger.info(f"⛏️ Analyzing mining scope document {request.document_id}")

        try:
            # Step 1: Get document content
            document_content = await self._get_document_content(request.document_id)

            # Step 2: Classify scope
            scope_type, mining_sector, mining_method, confidence = None, None, None, 0.0
            if request.classify_scope_type or request.identify_sector or request.identify_mining_method:
                scope_type, mining_sector, mining_method, confidence = await self._classify_scope(
                    document_content,
                    request
                )
                logger.info(f"   Classified: {scope_type} / {mining_sector} / {mining_method}")

            # Step 3: Extract requirements
            requirements = []
            if request.extract_requirements:
                requirements = await self._extract_requirements(document_content, request.min_confidence)
                logger.info(f"   Extracted {len(requirements)} requirements")

            # Step 4: Extract metrics
            metrics = None
            if request.extract_metrics:
                metrics = await self._extract_metrics(document_content)

            # Step 5: Identify risks
            risks = []
            if request.identify_risks:
                risks = await self._identify_risks(document_content, request.min_confidence)
                logger.info(f"   Identified {len(risks)} risks")

            # Step 6: Extract compliance
            compliance_requirements = []
            if request.extract_compliance:
                compliance_requirements = await self._extract_compliance(document_content)

            # Step 7: Generate summary
            executive_summary, key_findings = await self._generate_summary(
                document_content,
                requirements,
                risks,
                metrics
            )

            # Calculate counts
            critical_requirements = sum(1 for r in requirements if r.priority == "critical")
            high_severity_risks = sum(1 for r in risks if r.severity in ["critical", "high"])

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            response = MineScopeAnalysisResponse(
                analysis_id=analysis_id,
                document_id=request.document_id,
                scope_type=scope_type,
                mining_sector=mining_sector,
                mining_method=mining_method,
                classification_confidence=confidence,
                requirements=requirements,
                metrics=metrics,
                risks=risks,
                compliance_requirements=compliance_requirements,
                executive_summary=executive_summary,
                key_findings=key_findings,
                total_requirements=len(requirements),
                critical_requirements=critical_requirements,
                total_risks=len(risks),
                high_severity_risks=high_severity_risks,
                processing_time_seconds=processing_time,
                tier_1_services_used=self._get_services_used(request)
            )

            # Store results
            await self._store_analysis(request, response)

            logger.info(f"✓ Analysis complete: {len(requirements)} requirements, {len(risks)} risks")
            return response

        except Exception as e:
            logger.error(f"❌ Analysis failed: {str(e)}", exc_info=True)
            raise

    async def _get_document_content(self, document_id: str) -> Dict[str, Any]:
        """Get document content using DocumentService."""
        try:
            from app.models.database import Document
            doc = self.db.query(Document).filter(Document.id == document_id).first()

            if not doc:
                raise ValueError(f"Document {document_id} not found")

            chunks = await self.document_service.get_document_chunks(document_id)
            text = "\n\n".join([chunk.content for chunk in chunks])

            return {
                "document_id": document_id,
                "filename": doc.filename,
                "text": text,
                "file_type": doc.file_type
            }
        except Exception as e:
            logger.error(f"Failed to get document: {str(e)}")
            raise

    async def _classify_scope(
        self,
        document_content: Dict[str, Any],
        request: MineScopeAnalysisRequest
    ) -> tuple[Optional[MineScopeType], Optional[MiningSector], Optional[MiningMethod], float]:
        """Classify mining scope document."""

        prompt = f"""Analyze this mining scope document and classify:

Document: {document_content['text'][:3000]}

Classify:
1. Scope Type: exploration, development, production, reclamation, feasibility_study, environmental_assessment, safety_plan, equipment_specification, operational_plan
2. Mining Sector: coal, gold, iron_ore, copper, lithium, rare_earth, nickel, zinc, bauxite, diamond, other
3. Mining Method: open_pit, underground, placer, in_situ, strip_mining, dredging, solution_mining

Return JSON:
{{
    "scope_type": "type",
    "mining_sector": "sector",
    "mining_method": "method",
    "confidence": 0.95
}}

Return ONLY JSON."""

        try:
            # Get LLM parameters from module config
            llm_config = self.config.get('llm', {}).get('default', {})
            model = llm_config.get('model', 'gpt-4o-mini')
            temperature = llm_config.get('temperature', 0.0)
            max_tokens = llm_config.get('max_tokens', 300)

            response = await self.llm_service.generate_response(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

            data = json.loads(response.strip())
            return (
                MineScopeType(data.get("scope_type", "unknown")),
                MiningSector(data.get("mining_sector", "other")),
                MiningMethod(data.get("mining_method", "unknown")),
                data.get("confidence", 0.7)
            )
        except Exception as e:
            logger.error(f"Classification failed: {str(e)}")
            return None, None, None, 0.0

    async def _extract_requirements(
        self,
        document_content: Dict[str, Any],
        min_confidence: float
    ) -> List[ScopeRequirement]:
        """Extract requirements from scope document."""

        prompt = f"""Extract all requirements from this mining scope document:

{document_content['text'][:4000]}

Extract requirements with:
- Type: technical, regulatory, safety, environmental, operational, financial
- Priority: critical, high, medium, low

Return JSON array:
[
  {{
    "requirement_id": "REQ-001",
    "requirement_type": "safety",
    "description": "All personnel must wear PPE",
    "priority": "critical",
    "source_section": "Section 3.2",
    "confidence": 0.95
  }}
]

Return ONLY JSON array."""

        try:
            # Get LLM parameters from module config
            llm_config = self.config.get('llm', {}).get('default', {})
            model = llm_config.get('model', 'gpt-4o')
            temperature = llm_config.get('temperature', 0.1)
            max_tokens = llm_config.get('max_tokens', 3000)

            response = await self.llm_service.generate_response(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

            reqs_data = json.loads(response.strip())
            requirements = [
                ScopeRequirement(
                    requirement_id=r["requirement_id"],
                    requirement_type=r["requirement_type"],
                    description=r["description"],
                    priority=r["priority"],
                    source_section=r.get("source_section"),
                    confidence=r.get("confidence", 0.8),
                    metadata={}
                )
                for r in reqs_data
                if r.get("confidence", 0.8) >= min_confidence
            ]

            return requirements

        except Exception as e:
            logger.error(f"Requirement extraction failed: {str(e)}")
            return []

    async def _extract_metrics(
        self,
        document_content: Dict[str, Any]
    ) -> Optional[ExtractedMetrics]:
        """Extract quantitative metrics."""

        prompt = f"""Extract quantitative metrics from this mining scope:

{document_content['text'][:3000]}

Extract:
- Production rates, targets, reserves
- Operational details (mine life, depth, dimensions)
- Equipment and workforce
- Financial estimates (CAPEX, OPEX, ROI)
- Timelines

Return JSON with all available metrics (use null if not found):
{{
    "target_production_rate": "10,000 tonnes/day",
    "mine_life_years": 15,
    "workforce_size": 500,
    "capex_estimate": "$200M"
}}

Return ONLY JSON."""

        try:
            # Get LLM parameters from module config
            llm_config = self.config.get('llm', {}).get('default', {})
            model = llm_config.get('model', 'gpt-4o-mini')
            temperature = llm_config.get('temperature', 0.0)
            max_tokens = llm_config.get('max_tokens', 800)

            response = await self.llm_service.generate_response(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

            metrics_data = json.loads(response.strip())
            return ExtractedMetrics(**metrics_data)

        except Exception as e:
            logger.warning(f"Metrics extraction failed: {str(e)}")
            return ExtractedMetrics()

    async def _identify_risks(
        self,
        document_content: Dict[str, Any],
        min_confidence: float
    ) -> List[IdentifiedRisk]:
        """Identify risks in scope document."""

        prompt = f"""Identify risks in this mining scope:

{document_content['text'][:3000]}

Identify risks with:
- Category: safety, environmental, geological, operational, financial, regulatory
- Severity: critical, high, medium, low
- Likelihood: high, medium, low

Return JSON array:
[
  {{
    "risk_id": "RISK-001",
    "risk_category": "safety",
    "description": "Underground flooding risk",
    "severity": "high",
    "likelihood": "medium",
    "mitigation_strategy": "Install dewatering system",
    "confidence": 0.90
  }}
]

Return ONLY JSON array."""

        try:
            # Get LLM parameters from module config
            llm_config = self.config.get('llm', {}).get('default', {})
            model = llm_config.get('model', 'gpt-4o')
            temperature = llm_config.get('temperature', 0.1)
            max_tokens = llm_config.get('max_tokens', 2000)

            response = await self.llm_service.generate_response(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

            risks_data = json.loads(response.strip())
            risks = [
                IdentifiedRisk(
                    risk_id=r["risk_id"],
                    risk_category=r["risk_category"],
                    description=r["description"],
                    severity=r["severity"],
                    likelihood=r["likelihood"],
                    mitigation_strategy=r.get("mitigation_strategy"),
                    confidence=r.get("confidence", 0.8)
                )
                for r in risks_data
                if r.get("confidence", 0.8) >= min_confidence
            ]

            return risks

        except Exception as e:
            logger.error(f"Risk identification failed: {str(e)}")
            return []

    async def _extract_compliance(
        self,
        document_content: Dict[str, Any]
    ) -> List[ComplianceRequirement]:
        """Extract compliance requirements."""
        # Simplified for now
        return []

    async def _generate_summary(
        self,
        document_content: Dict[str, Any],
        requirements: List[ScopeRequirement],
        risks: List[IdentifiedRisk],
        metrics: Optional[ExtractedMetrics]
    ) -> tuple[str, List[str]]:
        """Generate executive summary and key findings."""

        prompt = f"""Generate an executive summary for this mining scope analysis:

Requirements: {len(requirements)} total
Critical Requirements: {sum(1 for r in requirements if r.priority == 'critical')}
Risks: {len(risks)} total
High Severity Risks: {sum(1 for r in risks if r.severity in ['critical', 'high'])}

Document Text (excerpt): {document_content['text'][:2000]}

Provide:
1. Executive summary (2-3 paragraphs)
2. Key findings (5-7 bullet points)

Return JSON:
{{
    "executive_summary": "...",
    "key_findings": ["finding 1", "finding 2", ...]
}}

Return ONLY JSON."""

        try:
            # Get LLM parameters from module config
            llm_config = self.config.get('llm', {}).get('default', {})
            model = llm_config.get('model', 'gpt-4o')
            temperature = llm_config.get('temperature', 0.3)
            max_tokens = llm_config.get('max_tokens', 1000)

            response = await self.llm_service.generate_response(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

            data = json.loads(response.strip())
            return data.get("executive_summary", ""), data.get("key_findings", [])

        except Exception as e:
            logger.warning(f"Summary generation failed: {str(e)}")
            return "", []

    def _get_services_used(self, request: MineScopeAnalysisRequest) -> List[str]:
        """Get list of tier_1 services used."""
        services = ["DocumentService", "LLMService"]
        if request.use_vision:
            services.append("VisionService")
        return services

    async def _store_analysis(
        self,
        request: MineScopeAnalysisRequest,
        response: MineScopeAnalysisResponse
    ):
        """Store analysis results in database."""
        try:
            from app.models.database_enhanced import ScopeAnalysisResults

            analysis_record = ScopeAnalysisResults(
                id=uuid.uuid4(),
                analysis_id=uuid.UUID(response.analysis_id),
                module_id="mine-scope",
                document_id=uuid.UUID(request.document_id),
                session_id=request.session_id,
                project_id=uuid.UUID(request.project_id) if request.project_id else None,
                result_data={
                    "classification": {
                        "scope_type": response.scope_type.value if response.scope_type else None,
                        "mining_sector": response.mining_sector.value if response.mining_sector else None,
                        "mining_method": response.mining_method.value if response.mining_method else None,
                        "confidence": response.classification_confidence
                    },
                    "requirements": [r.dict() for r in response.requirements],
                    "risks": [r.dict() for r in response.risks],
                    "metrics": response.metrics.dict() if response.metrics else None,
                    "executive_summary": response.executive_summary,
                    "key_findings": response.key_findings
                },
                confidence_score=response.classification_confidence,
                created_at=datetime.utcnow()
            )

            self.db.add(analysis_record)
            self.db.commit()

            logger.info(f"✓ Stored analysis results")

        except Exception as e:
            logger.error(f"Failed to store analysis: {str(e)}")

    async def search_analyses(
        self,
        request: ScopeSearchRequest
    ) -> ScopeSearchResponse:
        """Search for analyzed scopes."""
        try:
            from app.models.database_enhanced import ScopeAnalysisResults

            query = self.db.query(ScopeAnalysisResults).filter(
                ScopeAnalysisResults.module_id == "mine-scope"
            )

            if request.session_id:
                query = query.filter(ScopeAnalysisResults.session_id == request.session_id)

            if request.project_id:
                query = query.filter(ScopeAnalysisResults.project_id == uuid.UUID(request.project_id))

            total_count = query.count()
            records = query.order_by(
                ScopeAnalysisResults.created_at.desc()
            ).limit(request.limit).offset(request.offset).all()

            # Convert to response models (simplified)
            results = []

            return ScopeSearchResponse(
                total_count=total_count,
                returned_count=len(results),
                results=results,
                scope_type_counts={},
                sector_counts={},
                method_counts={},
                limit=request.limit,
                offset=request.offset,
                has_more=(request.offset + request.limit) < total_count
            )

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise
