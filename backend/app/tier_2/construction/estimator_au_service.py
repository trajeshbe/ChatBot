"""
Estimator One AU Service
Tier 2 Module: Construction

Australian construction cost estimation using tier_1 services.
100% tier_1 service reuse - zero new dependencies.
"""

import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from app.tier_1.document_processing.document_service import DocumentService

from .estimator_au_schemas import (
    CostEstimateRequest,
    CostEstimateResponse,
    EstimateBreakdown,
    CostItem,
    ProjectType,
    AustralianState,
    BuildingClass,
    EstimateComparisonRequest,
    EstimateComparisonResponse
)

logger = logging.getLogger(__name__)


# Cost rates will be loaded from uploaded documents (cost databases, project data)


class EstimatorAUService:
    """
    Australian construction cost estimation service.

    Estimation Process:
    1. Document Analysis → Extract project details if document provided
    2. Project Classification → Classify project type and building class
    3. Base Cost Calculation → Calculate base cost using regional rates
    4. Elemental Breakdown → Break down into cost elements
    5. Statutory Costs → Add authority fees, consultants
    6. Margins → Add contingency and profit
    7. GST Calculation → Apply 10% GST
    8. Comparables → Find market comparables
    """

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

        # Tier 1 service dependencies
        self.llm_service = LLMService(db, settings)
        self.document_service = DocumentService(db, settings)

        # Cost rates loaded from documents
        self.cost_rates_cache: Dict[str, Any] = {}

        logger.info("✓ EstimatorAUService initialized with tier_1 services")

    async def generate_estimate(
        self,
        request: CostEstimateRequest
    ) -> CostEstimateResponse:
        """Generate Australian construction cost estimate."""
        start_time = datetime.utcnow()
        estimate_id = str(uuid.uuid4())

        logger.info(f"💰 Generating AU cost estimate for {request.state.value}")

        try:
            # Step 1: Extract project details from document if provided
            if request.document_id and request.use_document_extraction:
                extracted_details = await self._extract_project_details(request.document_id)
                # Merge extracted details with request
                request = self._merge_details(request, extracted_details)

            # Step 2: Load cost rates from documents if not cached
            if not self.cost_rates_cache:
                self.cost_rates_cache = await self._extract_cost_rates_from_documents(session_id=request.session_id)

            # Get base cost rate
            base_rate_per_sqm = self._get_base_cost_rate(
                request.state,
                request.project_type,
                request.quality_level
            )

            gross_floor_area = request.gross_floor_area_sqm or 150.0  # Default 150 m²

            # Step 3: Calculate base construction cost
            base_construction_cost = base_rate_per_sqm * gross_floor_area

            # Step 4: Build detailed breakdown
            breakdown = self._calculate_breakdown(
                base_construction_cost,
                request.state,
                request.include_site_costs
            )

            # Step 5: Generate line items
            line_items = []
            if request.include_detailed_breakdown:
                line_items = self._generate_line_items(breakdown, gross_floor_area)

            # Step 6: Find market comparables
            comparables = []
            state_avg = None
            variance = None
            if request.include_comparables:
                comparables, state_avg = self._get_market_comparables(
                    request.state,
                    request.project_type,
                    gross_floor_area
                )
                if state_avg:
                    variance = ((breakdown.total_inc_gst_aud / gross_floor_area) - state_avg) / state_avg * 100

            # Step 7: Build response
            response = CostEstimateResponse(
                estimate_id=estimate_id,
                document_id=request.document_id,
                project_type=request.project_type,
                state=request.state,
                building_class=request.building_class,
                gross_floor_area_sqm=gross_floor_area,
                quality_level=request.quality_level,
                total_cost_ex_gst_aud=breakdown.subtotal_ex_gst_aud,
                total_cost_inc_gst_aud=breakdown.total_inc_gst_aud,
                cost_per_sqm_aud=breakdown.total_inc_gst_aud / gross_floor_area,
                breakdown=breakdown if request.include_detailed_breakdown else None,
                line_items=line_items,
                market_comparables=comparables,
                state_avg_cost_per_sqm_aud=state_avg,
                variance_from_average=variance,
                key_assumptions=self._get_key_assumptions(request),
                exclusions=self._get_exclusions(),
                estimate_date=datetime.utcnow(),
                valid_until=datetime.utcnow() + timedelta(days=90),
                confidence_level=0.85,
                tier_1_services_used=["LLMService", "DocumentService"] if request.document_id else ["LLMService"]
            )

            # Store estimate
            await self._store_estimate(request, response)

            logger.info(f"✓ Estimate complete: AUD ${breakdown.total_inc_gst_aud:,.2f} (${response.cost_per_sqm_aud:,.2f}/m²)")
            return response

        except Exception as e:
            logger.error(f"❌ Estimation failed: {str(e)}", exc_info=True)
            raise

    async def _extract_project_details(self, document_id: str) -> Dict[str, Any]:
        """Extract project details from document using LLMService."""
        try:
            from app.models.database import Document
            doc = self.db.query(Document).filter(Document.id == document_id).first()

            if not doc:
                raise ValueError(f"Document {document_id} not found")

            chunks = await self.document_service.get_document_chunks(document_id)
            text = "\n".join([chunk.content for chunk in chunks[:3]])

            prompt = f"""Extract construction project details from this Australian document:

{text}

Extract:
- Project type (residential, commercial, industrial)
- Gross floor area in m²
- Number of bedrooms, bathrooms, storeys
- Quality level (basic, standard, high, premium)
- Building class (BCA classification)

Return JSON:
{{
    "project_type": "residential_house",
    "gross_floor_area_sqm": 250,
    "num_bedrooms": 4,
    "num_bathrooms": 2,
    "num_storeys": 2,
    "quality_level": "standard"
}}

Return ONLY JSON."""

            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.0,
                max_tokens=300
            )

            return json.loads(response.strip())

        except Exception as e:
            logger.warning(f"Failed to extract details: {str(e)}")
            return {}

    def _merge_details(
        self,
        request: CostEstimateRequest,
        extracted: Dict[str, Any]
    ) -> CostEstimateRequest:
        """Merge extracted details with request."""
        if not request.gross_floor_area_sqm and extracted.get("gross_floor_area_sqm"):
            request.gross_floor_area_sqm = extracted["gross_floor_area_sqm"]

        if not request.project_type and extracted.get("project_type"):
            try:
                request.project_type = ProjectType(extracted["project_type"])
            except:
                pass

        if not request.quality_level and extracted.get("quality_level"):
            request.quality_level = extracted["quality_level"]

        return request

    async def _extract_cost_rates_from_documents(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Extract cost rates from uploaded cost databases"""
        try:
            documents = await self.document_service.list_documents(session_id=session_id)

            if not documents:
                logger.warning("No documents found for cost extraction - using fallback rates")
                return self._get_fallback_rates()

            all_rates = []

            for doc in documents[:10]:
                try:
                    chunks = await self.document_service.get_chunks_for_document(doc.id)
                    document_text = " ".join([chunk.get('content', '') for chunk in chunks[:5]])

                    rates = await self._extract_rates_from_text(document_text)
                    all_rates.extend(rates)
                except Exception as e:
                    logger.warning(f"Failed to extract rates from document {doc.id}: {e}")
                    continue

            # Build rate database from extracted rates
            rate_db = {}
            for rate in all_rates:
                state = rate.get("state", "nsw").upper()
                if state not in rate_db:
                    rate_db[state] = {}

                project_type = rate.get("project_type", "residential_house")
                if project_type not in rate_db[state]:
                    rate_db[state][project_type] = {}

                quality = rate.get("quality_level", "standard")
                rate_db[state][project_type][quality] = float(rate.get("rate_per_sqm", 2500))

            logger.info(f"✓ Loaded cost rates for {len(rate_db)} states from documents")
            return rate_db if rate_db else self._get_fallback_rates()

        except Exception as e:
            logger.error(f"Failed to load cost rates from documents: {e}")
            return self._get_fallback_rates()

    async def _extract_rates_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract cost rates using LLM"""
        prompt = f"""Extract Australian construction cost rates from this document:

{text[:3000]}

Return JSON array:
[
  {{
    "state": "NSW/VIC/QLD/WA/SA",
    "project_type": "residential_house/commercial_office/industrial",
    "quality_level": "basic/standard/high/premium",
    "rate_per_sqm": 2500
  }}
]

Return ONLY valid JSON array."""

        try:
            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.0,
                max_tokens=1000
            )

            rates = json.loads(response.strip())
            return rates if isinstance(rates, list) else []

        except Exception as e:
            logger.warning(f"Rate extraction failed: {e}")
            return []

    def _get_fallback_rates(self) -> Dict[str, Any]:
        """Fallback rates when no documents available"""
        return {
            "NSW": {
                "residential_house": {"basic": 1800, "standard": 2500, "high": 3500, "premium": 5000}
            }
        }

    def _get_base_cost_rate(
        self,
        state: AustralianState,
        project_type: Optional[ProjectType],
        quality_level: str
    ) -> float:
        """Get base construction cost rate (AUD/m²)."""
        # Default to residential house if not specified
        project_category = "residential_house"
        if project_type:
            if "commercial" in project_type.value:
                project_category = "commercial_office"
            elif "industrial" in project_type.value:
                project_category = "industrial"

        state_key = state.value.upper()
        return self.cost_rates_cache.get(state_key, {}).get(project_category, {}).get(quality_level, 2500)

    def _calculate_breakdown(
        self,
        base_cost: float,
        state: AustralianState,
        include_site_costs: bool
    ) -> EstimateBreakdown:
        """Calculate detailed cost breakdown."""
        # Elemental percentages
        preliminaries = base_cost * 0.10
        substructure = base_cost * 0.12
        superstructure = base_cost * 0.25
        external_walls = base_cost * 0.15
        internal_walls = base_cost * 0.08
        finishes = base_cost * 0.12
        services = base_cost * 0.15
        external_works = base_cost * 0.03 if include_site_costs else 0

        subtotal_construction = (
            preliminaries + substructure + superstructure +
            external_walls + internal_walls + finishes +
            services + external_works
        )

        # Statutory costs
        authority_fees = subtotal_construction * 0.015  # ~1.5%
        consultants = subtotal_construction * 0.08      # ~8%

        # Margins
        contingency = subtotal_construction * 0.05      # 5%
        profit_margin = subtotal_construction * 0.10    # 10%

        # Totals
        subtotal_ex_gst = (
            subtotal_construction + authority_fees +
            consultants + contingency + profit_margin
        )
        gst = subtotal_ex_gst * 0.10  # 10% GST
        total_inc_gst = subtotal_ex_gst + gst

        return EstimateBreakdown(
            preliminaries_aud=preliminaries,
            substructure_aud=substructure,
            superstructure_aud=superstructure,
            external_walls_aud=external_walls,
            internal_walls_aud=internal_walls,
            finishes_aud=finishes,
            services_aud=services,
            external_works_aud=external_works,
            authority_fees_aud=authority_fees,
            consultants_aud=consultants,
            contingency_aud=contingency,
            profit_margin_aud=profit_margin,
            subtotal_ex_gst_aud=subtotal_ex_gst,
            gst_aud=gst,
            total_inc_gst_aud=total_inc_gst
        )

    def _generate_line_items(
        self,
        breakdown: EstimateBreakdown,
        gross_floor_area: float
    ) -> List[CostItem]:
        """Generate detailed line items."""
        items = [
            CostItem(
                item_id="PRELIM-001",
                category="preliminaries",
                description="Site establishment and management",
                quantity=1,
                unit="sum",
                rate_aud=breakdown.preliminaries_aud,
                total_aud=breakdown.preliminaries_aud
            ),
            CostItem(
                item_id="SUB-001",
                category="substructure",
                description="Foundations and slab",
                quantity=gross_floor_area,
                unit="m²",
                rate_aud=breakdown.substructure_aud / gross_floor_area,
                total_aud=breakdown.substructure_aud
            ),
            CostItem(
                item_id="SUPER-001",
                category="superstructure",
                description="Frame, roof, and floors",
                quantity=gross_floor_area,
                unit="m²",
                rate_aud=breakdown.superstructure_aud / gross_floor_area,
                total_aud=breakdown.superstructure_aud
            )
        ]
        return items

    def _get_market_comparables(
        self,
        state: AustralianState,
        project_type: Optional[ProjectType],
        gross_floor_area: float
    ) -> Tuple[List[Dict[str, Any]], Optional[float]]:
        """Get market comparables (simplified)."""
        # Simplified: return state average
        state_avg = COST_RATES_PER_SQM_AUD.get(state, {}).get("residential_house", {}).get("standard", 2500)

        comparables = [
            {
                "project_name": "Similar project in " + state.value.upper(),
                "cost_per_sqm_aud": state_avg,
                "gross_floor_area_sqm": gross_floor_area,
                "year": 2024
            }
        ]

        return comparables, state_avg

    def _get_key_assumptions(self, request: CostEstimateRequest) -> List[str]:
        """Get key assumptions for estimate."""
        return [
            "Rates based on 2024 Australian market averages",
            f"Location: {request.state.value.upper()}",
            f"Quality level: {request.quality_level}",
            "Rates exclude land cost",
            "10% GST applicable",
            "90-day validity period"
        ]

    def _get_exclusions(self) -> List[str]:
        """Get standard exclusions."""
        return [
            "Land acquisition cost",
            "Finance and interest charges",
            "Stamp duty and legal fees",
            "Owner-supplied fixtures and fittings",
            "Temporary accommodation during construction"
        ]

    async def _store_estimate(
        self,
        request: CostEstimateRequest,
        response: CostEstimateResponse
    ):
        """Store estimate in database."""
        try:
            from app.models.database_enhanced import CostEstimateResults

            estimate_record = CostEstimateResults(
                id=uuid.uuid4(),
                estimate_id=uuid.UUID(response.estimate_id),
                module_id="estimator-one-au",
                document_id=uuid.UUID(request.document_id) if request.document_id else None,
                session_id=request.session_id,
                project_id=uuid.UUID(request.project_id) if request.project_id else None,
                result_data={
                    "project_summary": {
                        "project_type": response.project_type.value if response.project_type else None,
                        "state": response.state.value,
                        "gross_floor_area_sqm": response.gross_floor_area_sqm,
                        "quality_level": response.quality_level
                    },
                    "cost_summary": {
                        "total_ex_gst_aud": response.total_cost_ex_gst_aud,
                        "total_inc_gst_aud": response.total_cost_inc_gst_aud,
                        "cost_per_sqm_aud": response.cost_per_sqm_aud
                    },
                    "breakdown": response.breakdown.dict() if response.breakdown else None
                },
                created_at=datetime.utcnow()
            )

            self.db.add(estimate_record)
            self.db.commit()

            logger.info(f"✓ Stored estimate")

        except Exception as e:
            logger.error(f"Failed to store estimate: {str(e)}")
