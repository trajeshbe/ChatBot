"""
Agri Taxonomy Service
Tier 2 Module: Agriculture

Service for agricultural crop classification and taxonomy.
Leverages Tier 1 LLMService for crop data enrichment.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from .agri_taxonomy_schemas import (
    TaxonomyClassificationRequest,
    TaxonomyClassificationResponse,
    CropTaxonomy,
    CropClassification,
    GrowingRequirements,
    SeasonalInfo,
    CropCategory,
    SoilType,
    ClimateZone
)

logger = logging.getLogger(__name__)


class AgriTaxonomyService:
    """Service for agricultural taxonomy and crop classification"""

    def __init__(self, db: Session, settings: Settings, config: Optional[Dict[str, Any]] = None):
        self.db = db
        self.settings = settings
        self.config = config or {}
        # Tier 1 service dependencies
        self.llm_service = LLMService()

        # Import DocumentService for extracting crop data
        from app.tier_1.document_processing.document_service import DocumentService
        self.document_service = DocumentService(db, settings)

        # Taxonomy loaded dynamically from agricultural knowledge base documents
        self.taxonomy: Dict[str, Dict[str, Any]] = {}

        logger.info("✓ AgriTaxonomyService initialized with tier_1 services")
        if config:
            logger.info(f"✓ Using module config with model: {config.get(\'llm\', {}).get(\'default\', {}).get(\'model\', \'default\')}")

    async def _load_taxonomy_from_documents(self, session_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Load crop taxonomy from uploaded agricultural knowledge base documents"""
        try:
            documents = await self.document_service.list_documents(session_id=session_id)

            if not documents:
                logger.warning("No documents found for crop taxonomy extraction - returning empty taxonomy")
                return {}

            all_crops = []

            for doc in documents[:10]:
                try:
                    chunks = await self.document_service.get_chunks_for_document(doc.id)
                    document_text = " ".join([chunk.get('content', '') for chunk in chunks[:5]])

                    crops = await self._extract_crops_from_text(document_text)
                    all_crops.extend(crops)
                except Exception as e:
                    logger.warning(f"Failed to extract crops from document {doc.id}: {e}")
                    continue

            # Build taxonomy database
            taxonomy = {}
            for crop in all_crops:
                crop_key = crop.get("common_name", "").lower().strip()
                if crop_key and crop_key not in taxonomy:
                    taxonomy[crop_key] = crop

            logger.info(f"✓ Loaded taxonomy for {len(taxonomy)} crops from documents")
            return taxonomy

        except Exception as e:
            logger.error(f"Failed to load taxonomy from documents: {e}")
            return {}

    async def _extract_crops_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract crop taxonomy data using LLM"""
        prompt = f"""Extract all crop information from this agricultural document:

{text[:3000]}

Return JSON array:
[
  {{
    "common_name": "Rice",
    "scientific_name": "Oryza sativa",
    "category": "cereals/legumes/vegetables/fruits/oilseeds/fiber_crops/forage_crops/tuber_crops/spices/medicinal_plants",
    "family": "Poaceae",
    "climate_zones": ["tropical", "subtropical"],
    "soil_types": ["clay", "loamy"],
    "growth_duration_days": 120
  }}
]

Extract 10+ crops. Return ONLY valid JSON array."""

        try:
            # Get LLM parameters from module config
            llm_config = self.config.get('llm', {}).get('default', {})
            model = llm_config.get('model', 'gpt-4o-mini')
            temperature = llm_config.get('temperature', 0.0)
            max_tokens = llm_config.get('max_tokens', 1500)

            response = await self.llm_service.generate_response(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

            crops = json.loads(response.strip())
            return crops if isinstance(crops, list) else []

        except Exception as e:
            logger.warning(f"Crop extraction failed: {e}")
            return []

    async def classify_crops(self, request: TaxonomyClassificationRequest) -> TaxonomyClassificationResponse:
        """Classify crops and build taxonomy"""
        logger.info(f"🌾 Classifying {len(request.crop_names)} crops")

        # Load taxonomy from documents if not already loaded
        if not self.taxonomy:
            self.taxonomy = await self._load_taxonomy_from_documents(session_id=request.session_id)

        classifications: List[CropTaxonomy] = []
        unclassified: List[str] = []

        for crop_name in request.crop_names:
            taxonomy = await self._classify_single_crop(
                crop_name,
                include_requirements=request.include_requirements,
                include_seasonal=request.include_seasonal_info,
                use_llm=request.use_llm_enrichment
            )

            if taxonomy:
                classifications.append(taxonomy)
            else:
                unclassified.append(crop_name)

        coverage = (len(classifications) / len(request.crop_names) * 100) if request.crop_names else 0.0

        logger.info(f"✓ Classified {len(classifications)}/{len(request.crop_names)} crops ({coverage:.1f}% coverage)")

        return TaxonomyClassificationResponse(
            classifications=classifications,
            unclassified_crops=unclassified,
            total_crops_processed=len(request.crop_names),
            taxonomy_coverage_percent=round(coverage, 2)
        )

    async def _classify_single_crop(
        self,
        crop_name: str,
        include_requirements: bool = True,
        include_seasonal: bool = True,
        use_llm: bool = True
    ) -> Optional[CropTaxonomy]:
        """Classify a single crop"""
        normalized_name = crop_name.lower().strip()

        # Check basic taxonomy
        if normalized_name in self.taxonomy:
            base_data = self.taxonomy[normalized_name]

            classification = CropClassification(
                common_name=base_data["common_name"],
                scientific_name=base_data.get("scientific_name"),
                category=base_data["category"],
                family=base_data.get("family")
            )

            growing_reqs = GrowingRequirements(
                preferred_soil_types=base_data.get("soil_types", []),
                climate_zones=base_data.get("climate_zones", [])
            ) if include_requirements else GrowingRequirements()

            seasonal = SeasonalInfo(
                growth_duration_days=base_data.get("growth_duration_days")
            ) if include_seasonal else SeasonalInfo()

            return CropTaxonomy(
                crop_id=normalized_name,
                classification=classification,
                growing_requirements=growing_reqs,
                seasonal_info=seasonal
            )

        # LLM-based classification fallback
        if use_llm:
            return await self._llm_classify_crop(crop_name, include_requirements, include_seasonal)

        return None

    async def _llm_classify_crop(
        self,
        crop_name: str,
        include_requirements: bool,
        include_seasonal: bool
    ) -> Optional[CropTaxonomy]:
        """Use LLM to classify unknown crops"""
        prompt = f"""Classify this agricultural crop: {crop_name}

Provide JSON response:
{{
  "common_name": "crop name",
  "scientific_name": "scientific name",
  "category": "cereals/legumes/vegetables/fruits/oilseeds/fiber_crops/forage_crops/tuber_crops/spices/medicinal_plants",
  "family": "botanical family",
  "climate_zones": ["tropical/subtropical/temperate/continental/polar/arid/semi_arid"],
  "soil_types": ["sandy/loamy/clay/silt/peaty/chalky/saline"],
  "growth_duration_days": number,
  "temperature_optimal_celsius": number,
  "ph_optimal": number
}}

Return ONLY valid JSON. If crop is unknown, return null."""

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

            result = json.loads(response.strip())

            if result is None:
                return None

            classification = CropClassification(
                common_name=result.get("common_name", crop_name),
                scientific_name=result.get("scientific_name"),
                category=CropCategory(result["category"]) if "category" in result else CropCategory.VEGETABLES,
                family=result.get("family")
            )

            growing_reqs = GrowingRequirements()
            if include_requirements:
                growing_reqs.climate_zones = [ClimateZone(z) for z in result.get("climate_zones", [])]
                growing_reqs.preferred_soil_types = [SoilType(s) for s in result.get("soil_types", [])]
                growing_reqs.temperature_optimal_celsius = result.get("temperature_optimal_celsius")
                growing_reqs.ph_optimal = result.get("ph_optimal")

            seasonal = SeasonalInfo()
            if include_seasonal:
                seasonal.growth_duration_days = result.get("growth_duration_days")

            return CropTaxonomy(
                crop_id=crop_name.lower().strip(),
                classification=classification,
                growing_requirements=growing_reqs,
                seasonal_info=seasonal
            )

        except Exception as e:
            logger.warning(f"LLM classification failed for '{crop_name}': {e}")
            return None
