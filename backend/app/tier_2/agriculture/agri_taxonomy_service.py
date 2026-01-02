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

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        # Tier 1 service dependencies
        self.llm_service = LLMService(db, settings)

        # Load basic crop taxonomy (hardcoded for demo, would be from DB in production)
        self.taxonomy = self._load_basic_taxonomy()

        logger.info("✓ AgriTaxonomyService initialized with tier_1 services")

    def _load_basic_taxonomy(self) -> Dict[str, Dict[str, Any]]:
        """Load basic crop taxonomy database"""
        return {
            "rice": {
                "common_name": "Rice",
                "scientific_name": "Oryza sativa",
                "category": CropCategory.CEREALS,
                "family": "Poaceae",
                "climate_zones": [ClimateZone.TROPICAL, ClimateZone.SUBTROPICAL],
                "soil_types": [SoilType.CLAY, SoilType.LOAMY],
                "growth_duration_days": 120
            },
            "wheat": {
                "common_name": "Wheat",
                "scientific_name": "Triticum aestivum",
                "category": CropCategory.CEREALS,
                "family": "Poaceae",
                "climate_zones": [ClimateZone.TEMPERATE, ClimateZone.CONTINENTAL],
                "soil_types": [SoilType.LOAMY, SoilType.CLAY],
                "growth_duration_days": 150
            },
            "corn": {
                "common_name": "Corn (Maize)",
                "scientific_name": "Zea mays",
                "category": CropCategory.CEREALS,
                "family": "Poaceae",
                "climate_zones": [ClimateZone.TEMPERATE, ClimateZone.TROPICAL],
                "soil_types": [SoilType.LOAMY, SoilType.SANDY],
                "growth_duration_days": 90
            },
            "tomato": {
                "common_name": "Tomato",
                "scientific_name": "Solanum lycopersicum",
                "category": CropCategory.VEGETABLES,
                "family": "Solanaceae",
                "climate_zones": [ClimateZone.TEMPERATE, ClimateZone.SUBTROPICAL],
                "soil_types": [SoilType.LOAMY, SoilType.SANDY],
                "growth_duration_days": 75
            },
            "soybean": {
                "common_name": "Soybean",
                "scientific_name": "Glycine max",
                "category": CropCategory.LEGUMES,
                "family": "Fabaceae",
                "climate_zones": [ClimateZone.TEMPERATE, ClimateZone.SUBTROPICAL],
                "soil_types": [SoilType.LOAMY, SoilType.CLAY],
                "growth_duration_days": 100
            },
            "cotton": {
                "common_name": "Cotton",
                "scientific_name": "Gossypium hirsutum",
                "category": CropCategory.FIBER_CROPS,
                "family": "Malvaceae",
                "climate_zones": [ClimateZone.TROPICAL, ClimateZone.SUBTROPICAL],
                "soil_types": [SoilType.LOAMY, SoilType.CLAY],
                "growth_duration_days": 180
            }
        }

    async def classify_crops(self, request: TaxonomyClassificationRequest) -> TaxonomyClassificationResponse:
        """Classify crops and build taxonomy"""
        logger.info(f"🌾 Classifying {len(request.crop_names)} crops")

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
            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.0,
                max_tokens=300
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
