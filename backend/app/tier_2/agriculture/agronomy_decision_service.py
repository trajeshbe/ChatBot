"""
Agronomy Decision Service
Tier 2 Module: Agriculture

Service for agronomy decision support and farm management recommendations.
Leverages Tier 1 LLMService for intelligent agricultural decision-making.
"""

import logging
import json
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from .agronomy_decision_schemas import (
    AgronomyDecisionRequest,
    AgronomyDecisionResponse,
    DecisionAnalysis,
    AgronomyRecommendation,
    DecisionType,
    RecommendationPriority,
    DecisionContext,
    SoilCondition,
    WeatherData,
    CropHealthIndicators,
    CropHealthStatus,
    WeatherPattern
)

logger = logging.getLogger(__name__)


class AgronomyDecisionService:
    """Service for agronomy decision support and recommendations"""

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        # Tier 1 service dependencies
        self.llm_service = LLMService(db, settings)

        # Import DocumentService for extracting decision rules
        from app.tier_1.document_processing.document_service import DocumentService
        self.document_service = DocumentService(db, settings)

        # Knowledge base loaded from agricultural research documents
        self.decision_rules: Dict[str, Dict[str, Any]] = {}

        logger.info("✓ AgronomyDecisionService initialized with tier_1 services")

    async def _load_decision_rules_from_documents(self, session_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Load decision rules from uploaded agricultural research documents"""
        try:
            documents = await self.document_service.list_documents(session_id=session_id)

            if not documents:
                logger.warning("No documents found for decision rules - using fallback rules")
                return self._get_fallback_rules()

            all_rules = []

            for doc in documents[:10]:
                try:
                    chunks = await self.document_service.get_chunks_for_document(doc.id)
                    document_text = " ".join([chunk.get('content', '') for chunk in chunks[:5]])

                    rules = await self._extract_rules_from_text(document_text)
                    all_rules.extend(rules)
                except Exception as e:
                    logger.warning(f"Failed to extract rules from document {doc.id}: {e}")
                    continue

            # Build rules database
            rules_db = {}
            for rule in all_rules:
                decision_type = rule.get("decision_type", "").lower()
                if decision_type and decision_type not in rules_db:
                    rules_db[decision_type] = rule.get("thresholds", {})

            logger.info(f"✓ Loaded decision rules for {len(rules_db)} decision types from documents")
            return rules_db if rules_db else self._get_fallback_rules()

        except Exception as e:
            logger.error(f"Failed to load decision rules from documents: {e}")
            return self._get_fallback_rules()

    async def _extract_rules_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract decision rules using LLM"""
        prompt = f"""Extract agronomy decision rules and thresholds from this agricultural research document:

{text[:3000]}

Return JSON array:
[
  {{
    "decision_type": "irrigation/fertilization/planting/harvesting/pest_control",
    "thresholds": {{
      "soil_moisture_threshold": 30.0,
      "critical_threshold": 20.0,
      "optimal_range": [40.0, 60.0]
    }}
  }}
]

Extract as many decision rules as possible. Return ONLY valid JSON array."""

        try:
            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.0,
                max_tokens=1000
            )

            rules = json.loads(response.strip())
            return rules if isinstance(rules, list) else []

        except Exception as e:
            logger.warning(f"Rules extraction failed: {e}")
            return []

    def _get_fallback_rules(self) -> Dict[str, Dict[str, Any]]:
        """Fallback rules when no documents available"""
        return {
            "irrigation": {
                "soil_moisture_threshold": 30.0,
                "critical_threshold": 20.0,
                "optimal_range": (40.0, 60.0)
            },
            "fertilization": {
                "nitrogen_low": 20.0,
                "phosphorus_low": 15.0,
                "potassium_low": 100.0,
                "optimal_ph_range": (6.0, 7.5)
            }
        }

    async def make_decisions(self, request: AgronomyDecisionRequest) -> AgronomyDecisionResponse:
        """Analyze context and provide agronomy recommendations"""
        logger.info(f"🌾 Making {len(request.decision_types)} agronomy decisions")

        # Load decision rules from documents if not already loaded
        if not self.decision_rules:
            self.decision_rules = await self._load_decision_rules_from_documents(session_id=request.session_id)

        analyses: List[DecisionAnalysis] = []

        for decision_type in request.decision_types:
            analysis = await self._analyze_decision(
                decision_type,
                request.context,
                use_ai=request.use_ai_analysis,
                include_alternatives=request.include_alternatives,
                budget_constraint=request.budget_constraint,
                prioritize_sustainability=request.prioritize_sustainability
            )
            if analysis:
                analyses.append(analysis)

        # Calculate overall metrics
        overall_health_score = self._calculate_farm_health_score(request.context)
        critical_actions = sum(
            1 for analysis in analyses
            for rec in analysis.recommendations
            if rec.priority == RecommendationPriority.CRITICAL
        )
        total_cost = sum(
            rec.estimated_cost or 0
            for analysis in analyses
            for rec in analysis.recommendations
        )

        # Generate AI insights if requested
        ai_insights = []
        if request.use_ai_analysis:
            ai_insights = await self._generate_ai_insights(request.context, analyses)

        sustainability_rating = self._calculate_sustainability_rating(
            analyses,
            request.prioritize_sustainability
        )

        logger.info(f"✓ Generated {len(analyses)} decision analyses with {critical_actions} critical actions")

        return AgronomyDecisionResponse(
            analyses=analyses,
            overall_farm_health_score=overall_health_score,
            critical_actions_count=critical_actions,
            estimated_total_cost=total_cost if total_cost > 0 else None,
            sustainability_rating=sustainability_rating,
            ai_insights=ai_insights
        )

    async def _analyze_decision(
        self,
        decision_type: DecisionType,
        context: DecisionContext,
        use_ai: bool = True,
        include_alternatives: bool = True,
        budget_constraint: Optional[float] = None,
        prioritize_sustainability: bool = False
    ) -> Optional[DecisionAnalysis]:
        """Analyze a specific decision type"""

        if decision_type == DecisionType.IRRIGATION:
            return await self._analyze_irrigation(context, use_ai, include_alternatives)
        elif decision_type == DecisionType.FERTILIZATION:
            return await self._analyze_fertilization(context, use_ai, include_alternatives)
        elif decision_type == DecisionType.PLANTING:
            return await self._analyze_planting(context, use_ai, include_alternatives)
        elif decision_type == DecisionType.HARVESTING:
            return await self._analyze_harvesting(context, use_ai, include_alternatives)
        elif decision_type == DecisionType.PEST_CONTROL:
            return await self._analyze_pest_control(context, use_ai, include_alternatives)
        elif decision_type == DecisionType.DISEASE_MANAGEMENT:
            return await self._analyze_disease_management(context, use_ai, include_alternatives)
        elif decision_type == DecisionType.CROP_ROTATION:
            return await self._analyze_crop_rotation(context, use_ai, include_alternatives)
        elif decision_type == DecisionType.SOIL_AMENDMENT:
            return await self._analyze_soil_amendment(context, use_ai, include_alternatives)
        else:
            # Generic LLM-based analysis
            if use_ai:
                return await self._llm_decision_analysis(decision_type, context, include_alternatives)

        return None

    async def _analyze_irrigation(
        self,
        context: DecisionContext,
        use_ai: bool,
        include_alternatives: bool
    ) -> DecisionAnalysis:
        """Analyze irrigation decision"""
        recommendations = []

        if context.soil_condition and context.soil_condition.moisture_percent is not None:
            moisture = context.soil_condition.moisture_percent
            rules = self.decision_rules["irrigation"]

            if moisture < rules["critical_threshold"]:
                recommendations.append(AgronomyRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    decision_type=DecisionType.IRRIGATION,
                    priority=RecommendationPriority.CRITICAL,
                    action=f"Immediate irrigation required - soil moisture critically low at {moisture:.1f}%",
                    reasoning=f"Soil moisture ({moisture:.1f}%) is below critical threshold ({rules['critical_threshold']}%)",
                    expected_outcome="Prevent crop water stress and potential yield loss",
                    timing="Within 24 hours",
                    estimated_cost=150.0,
                    confidence_score=95.0,
                    alternative_options=["Drip irrigation", "Sprinkler irrigation", "Flood irrigation"] if include_alternatives else []
                ))
            elif moisture < rules["soil_moisture_threshold"]:
                recommendations.append(AgronomyRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    decision_type=DecisionType.IRRIGATION,
                    priority=RecommendationPriority.HIGH,
                    action=f"Schedule irrigation soon - soil moisture at {moisture:.1f}%",
                    reasoning=f"Soil moisture approaching low threshold ({rules['soil_moisture_threshold']}%)",
                    expected_outcome="Maintain optimal soil moisture for crop growth",
                    timing="Within 2-3 days",
                    estimated_cost=150.0,
                    confidence_score=90.0
                ))
            elif moisture > rules["optimal_range"][1]:
                recommendations.append(AgronomyRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    decision_type=DecisionType.IRRIGATION,
                    priority=RecommendationPriority.MEDIUM,
                    action=f"Delay irrigation - soil moisture high at {moisture:.1f}%",
                    reasoning=f"Soil moisture above optimal range ({rules['optimal_range'][1]}%)",
                    expected_outcome="Prevent overwatering and root oxygen deprivation",
                    timing="No irrigation needed for 7-10 days",
                    estimated_cost=0.0,
                    confidence_score=85.0
                ))

        # Check weather forecast
        if context.weather_data and context.weather_data.rainfall_forecast_7days_mm:
            if context.weather_data.rainfall_forecast_7days_mm > 20:
                recommendations.append(AgronomyRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    decision_type=DecisionType.IRRIGATION,
                    priority=RecommendationPriority.LOW,
                    action="Delay irrigation - significant rainfall forecasted",
                    reasoning=f"Expected {context.weather_data.rainfall_forecast_7days_mm:.1f}mm rain in next 7 days",
                    expected_outcome="Reduce water costs and prevent overwatering",
                    timing="Wait for rainfall, reassess in 7 days",
                    estimated_cost=0.0,
                    confidence_score=80.0
                ))

        return DecisionAnalysis(
            decision_type=DecisionType.IRRIGATION,
            recommendations=recommendations,
            risk_factors=["Water stress risk", "Drought conditions"] if context.weather_data and context.weather_data.drought_risk else [],
            opportunities=["Optimize water usage", "Reduce irrigation costs"],
            key_considerations=["Soil moisture levels", "Weather forecast", "Crop water requirements"]
        )

    async def _analyze_fertilization(
        self,
        context: DecisionContext,
        use_ai: bool,
        include_alternatives: bool
    ) -> DecisionAnalysis:
        """Analyze fertilization decision"""
        recommendations = []
        rules = self.decision_rules["fertilization"]

        if context.soil_condition:
            soil = context.soil_condition

            # Check nitrogen levels
            if soil.nitrogen_ppm is not None and soil.nitrogen_ppm < rules["nitrogen_low"]:
                recommendations.append(AgronomyRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    decision_type=DecisionType.FERTILIZATION,
                    priority=RecommendationPriority.HIGH,
                    action=f"Apply nitrogen fertilizer - current level {soil.nitrogen_ppm:.1f} ppm is low",
                    reasoning=f"Nitrogen below optimal ({rules['nitrogen_low']} ppm threshold)",
                    expected_outcome="Improve vegetative growth and leaf development",
                    timing="Within 1 week",
                    estimated_cost=200.0,
                    confidence_score=90.0,
                    alternative_options=["Urea", "Ammonium nitrate", "Organic compost"] if include_alternatives else []
                ))

            # Check phosphorus
            if soil.phosphorus_ppm is not None and soil.phosphorus_ppm < rules["phosphorus_low"]:
                recommendations.append(AgronomyRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    decision_type=DecisionType.FERTILIZATION,
                    priority=RecommendationPriority.MEDIUM,
                    action=f"Apply phosphorus fertilizer - current level {soil.phosphorus_ppm:.1f} ppm",
                    reasoning="Phosphorus essential for root development and flowering",
                    expected_outcome="Enhanced root growth and earlier flowering",
                    timing="Within 2 weeks",
                    estimated_cost=150.0,
                    confidence_score=85.0
                ))

            # Check pH
            if soil.ph_level is not None:
                if soil.ph_level < rules["optimal_ph_range"][0]:
                    recommendations.append(AgronomyRecommendation(
                        recommendation_id=str(uuid.uuid4()),
                        decision_type=DecisionType.SOIL_AMENDMENT,
                        priority=RecommendationPriority.MEDIUM,
                        action=f"Apply lime to raise pH from {soil.ph_level:.1f}",
                        reasoning=f"Soil pH below optimal range ({rules['optimal_ph_range']})",
                        expected_outcome="Improve nutrient availability",
                        timing="Before next planting season",
                        estimated_cost=100.0,
                        confidence_score=88.0
                    ))
                elif soil.ph_level > rules["optimal_ph_range"][1]:
                    recommendations.append(AgronomyRecommendation(
                        recommendation_id=str(uuid.uuid4()),
                        decision_type=DecisionType.SOIL_AMENDMENT,
                        priority=RecommendationPriority.MEDIUM,
                        action=f"Apply sulfur to lower pH from {soil.ph_level:.1f}",
                        reasoning=f"Soil pH above optimal range ({rules['optimal_ph_range']})",
                        expected_outcome="Improve nutrient availability",
                        timing="Before next planting season",
                        estimated_cost=120.0,
                        confidence_score=88.0
                    ))

        return DecisionAnalysis(
            decision_type=DecisionType.FERTILIZATION,
            recommendations=recommendations,
            risk_factors=["Nutrient deficiency", "Soil pH imbalance"],
            opportunities=["Optimize nutrient uptake", "Improve soil health"],
            key_considerations=["NPK levels", "Soil pH", "Crop growth stage", "Organic matter content"]
        )

    async def _analyze_planting(
        self,
        context: DecisionContext,
        use_ai: bool,
        include_alternatives: bool
    ) -> DecisionAnalysis:
        """Analyze planting decision"""
        recommendations = []
        rules = self.decision_rules["planting"]

        ready_to_plant = True
        issues = []

        # Check soil temperature
        if context.soil_condition and context.soil_condition.temperature_celsius is not None:
            if context.soil_condition.temperature_celsius < rules["min_soil_temp_celsius"]:
                ready_to_plant = False
                issues.append(f"Soil temperature too low ({context.soil_condition.temperature_celsius:.1f}°C)")

        # Check frost risk
        if context.weather_data and context.weather_data.frost_risk:
            ready_to_plant = False
            issues.append("Frost risk detected in forecast")

        if ready_to_plant:
            recommendations.append(AgronomyRecommendation(
                recommendation_id=str(uuid.uuid4()),
                decision_type=DecisionType.PLANTING,
                priority=RecommendationPriority.HIGH,
                action=f"Optimal conditions for planting {context.crop_type}",
                reasoning="Soil temperature, moisture, and weather conditions are favorable",
                expected_outcome="Successful germination and early growth",
                timing="Within next 3-5 days",
                estimated_cost=500.0,
                confidence_score=92.0
            ))
        else:
            recommendations.append(AgronomyRecommendation(
                recommendation_id=str(uuid.uuid4()),
                decision_type=DecisionType.PLANTING,
                priority=RecommendationPriority.MEDIUM,
                action=f"Delay planting - conditions not optimal",
                reasoning="; ".join(issues),
                expected_outcome="Avoid poor germination and seedling establishment",
                timing=f"Wait {rules['frost_risk_delay_days']} days, reassess",
                estimated_cost=0.0,
                confidence_score=88.0
            ))

        return DecisionAnalysis(
            decision_type=DecisionType.PLANTING,
            recommendations=recommendations,
            risk_factors=issues,
            opportunities=["Optimal planting window", "Early market advantage"] if ready_to_plant else [],
            key_considerations=["Soil temperature", "Frost risk", "Soil moisture", "Weather forecast"]
        )

    async def _analyze_harvesting(
        self,
        context: DecisionContext,
        use_ai: bool,
        include_alternatives: bool
    ) -> DecisionAnalysis:
        """Analyze harvesting decision"""
        recommendations = []
        rules = self.decision_rules["harvesting"]

        ready_to_harvest = False

        if context.crop_health and context.crop_health.growth_stage == "maturity":
            ready_to_harvest = True

        # Check weather conditions
        weather_suitable = True
        if context.weather_data:
            if context.weather_data.rainfall_forecast_7days_mm and context.weather_data.rainfall_forecast_7days_mm > rules["rain_delay_threshold_mm"]:
                weather_suitable = False
            if context.weather_data.wind_speed_kmh and context.weather_data.wind_speed_kmh > rules["wind_speed_limit_kmh"]:
                weather_suitable = False

        if ready_to_harvest and weather_suitable:
            recommendations.append(AgronomyRecommendation(
                recommendation_id=str(uuid4()),
                decision_type=DecisionType.HARVESTING,
                priority=RecommendationPriority.HIGH,
                action=f"Proceed with harvesting {context.crop_type}",
                reasoning="Crop reached maturity and weather conditions are favorable",
                expected_outcome="Optimal yield and quality",
                timing="Within next 2-3 days",
                estimated_cost=800.0,
                confidence_score=93.0
            ))
        elif ready_to_harvest and not weather_suitable:
            recommendations.append(AgronomyRecommendation(
                recommendation_id=str(uuid.uuid4()),
                decision_type=DecisionType.HARVESTING,
                priority=RecommendationPriority.MEDIUM,
                action="Delay harvesting - weather conditions unfavorable",
                reasoning="High wind or rain forecast - wait for better conditions",
                expected_outcome="Prevent harvest losses and maintain quality",
                timing="Wait 3-5 days, monitor weather",
                estimated_cost=0.0,
                confidence_score=85.0
            ))

        return DecisionAnalysis(
            decision_type=DecisionType.HARVESTING,
            recommendations=recommendations,
            risk_factors=["Weather damage", "Overmaturity", "Quality degradation"],
            opportunities=["Peak market prices", "Optimal quality"],
            key_considerations=["Crop maturity", "Weather forecast", "Market prices", "Storage availability"]
        )

    async def _analyze_pest_control(
        self,
        context: DecisionContext,
        use_ai: bool,
        include_alternatives: bool
    ) -> DecisionAnalysis:
        """Analyze pest control decision"""
        recommendations = []

        if context.crop_health and context.crop_health.pest_infestation_level:
            infestation = context.crop_health.pest_infestation_level

            if infestation > 50:
                recommendations.append(AgronomyRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    decision_type=DecisionType.PEST_CONTROL,
                    priority=RecommendationPriority.CRITICAL,
                    action=f"Immediate pest control required - infestation at {infestation:.1f}%",
                    reasoning="High pest pressure threatens crop yield",
                    expected_outcome="Prevent severe yield loss",
                    timing="Within 24-48 hours",
                    estimated_cost=250.0,
                    confidence_score=90.0,
                    alternative_options=["Chemical pesticide", "Biological control", "Integrated pest management"] if include_alternatives else []
                ))
            elif infestation > 20:
                recommendations.append(AgronomyRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    decision_type=DecisionType.PEST_CONTROL,
                    priority=RecommendationPriority.HIGH,
                    action=f"Apply pest control measures - infestation at {infestation:.1f}%",
                    reasoning="Moderate pest pressure detected",
                    expected_outcome="Limit pest population growth",
                    timing="Within 3-5 days",
                    estimated_cost=180.0,
                    confidence_score=85.0
                ))

        return DecisionAnalysis(
            decision_type=DecisionType.PEST_CONTROL,
            recommendations=recommendations,
            risk_factors=["Yield loss", "Crop damage", "Secondary pest outbreaks"],
            opportunities=["Preventive control", "Integrated pest management"],
            key_considerations=["Infestation level", "Pest species", "Crop growth stage", "Weather conditions"]
        )

    async def _analyze_disease_management(
        self,
        context: DecisionContext,
        use_ai: bool,
        include_alternatives: bool
    ) -> DecisionAnalysis:
        """Analyze disease management decision"""
        recommendations = []

        if context.crop_health and context.crop_health.disease_severity:
            severity = context.crop_health.disease_severity

            if severity > 40:
                recommendations.append(AgronomyRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    decision_type=DecisionType.DISEASE_MANAGEMENT,
                    priority=RecommendationPriority.CRITICAL,
                    action=f"Immediate disease treatment - severity at {severity:.1f}%",
                    reasoning="High disease pressure threatens crop health",
                    expected_outcome="Control disease spread and minimize damage",
                    timing="Immediate action required",
                    estimated_cost=300.0,
                    confidence_score=88.0
                ))

        return DecisionAnalysis(
            decision_type=DecisionType.DISEASE_MANAGEMENT,
            recommendations=recommendations,
            risk_factors=["Disease spread", "Yield loss", "Quality degradation"],
            opportunities=["Early intervention", "Disease-resistant varieties"],
            key_considerations=["Disease type", "Severity", "Weather conditions", "Crop susceptibility"]
        )

    async def _analyze_crop_rotation(
        self,
        context: DecisionContext,
        use_ai: bool,
        include_alternatives: bool
    ) -> DecisionAnalysis:
        """Analyze crop rotation decision"""
        recommendations = []

        # Use LLM for crop rotation advice
        if use_ai and context.previous_crops:
            rotation_advice = await self._get_llm_crop_rotation_advice(
                context.crop_type,
                context.previous_crops,
                context.soil_condition
            )
            if rotation_advice:
                recommendations.append(rotation_advice)

        return DecisionAnalysis(
            decision_type=DecisionType.CROP_ROTATION,
            recommendations=recommendations,
            risk_factors=["Soil nutrient depletion", "Pest/disease buildup"],
            opportunities=["Soil health improvement", "Pest/disease break"],
            key_considerations=["Previous crops", "Soil condition", "Market demand", "Nutrient balance"]
        )

    async def _analyze_soil_amendment(
        self,
        context: DecisionContext,
        use_ai: bool,
        include_alternatives: bool
    ) -> DecisionAnalysis:
        """Analyze soil amendment decision"""
        # This is often handled within fertilization analysis
        return DecisionAnalysis(
            decision_type=DecisionType.SOIL_AMENDMENT,
            recommendations=[],
            key_considerations=["Soil pH", "Organic matter", "Nutrient levels", "Soil structure"]
        )

    async def _llm_decision_analysis(
        self,
        decision_type: DecisionType,
        context: DecisionContext,
        include_alternatives: bool
    ) -> Optional[DecisionAnalysis]:
        """Use LLM for generic decision analysis"""
        prompt = f"""As an agronomy expert, analyze this {decision_type.value} decision:

Crop: {context.crop_type}
Location: {context.farm_location or 'Not specified'}
Soil Condition: {context.soil_condition.model_dump() if context.soil_condition else 'Unknown'}
Weather: {context.weather_data.model_dump() if context.weather_data else 'Unknown'}
Crop Health: {context.crop_health.model_dump() if context.crop_health else 'Unknown'}

Provide JSON response:
{{
  "recommendations": [
    {{
      "action": "specific action to take",
      "reasoning": "why this action",
      "priority": "critical/high/medium/low",
      "timing": "when to implement",
      "confidence": 0-100
    }}
  ],
  "risk_factors": ["risk 1", "risk 2"],
  "opportunities": ["opportunity 1"]
}}

Return ONLY valid JSON."""

        try:
            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.2,
                max_tokens=500
            )

            result = json.loads(response.strip())

            recommendations = []
            for rec_data in result.get("recommendations", []):
                recommendations.append(AgronomyRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    decision_type=decision_type,
                    priority=RecommendationPriority(rec_data.get("priority", "medium")),
                    action=rec_data.get("action", ""),
                    reasoning=rec_data.get("reasoning", ""),
                    expected_outcome="See reasoning",
                    timing=rec_data.get("timing"),
                    confidence_score=float(rec_data.get("confidence", 75))
                ))

            return DecisionAnalysis(
                decision_type=decision_type,
                recommendations=recommendations,
                risk_factors=result.get("risk_factors", []),
                opportunities=result.get("opportunities", []),
                key_considerations=[]
            )

        except Exception as e:
            logger.warning(f"LLM decision analysis failed: {e}")
            return None

    async def _get_llm_crop_rotation_advice(
        self,
        current_crop: str,
        previous_crops: List[str],
        soil_condition: Optional[SoilCondition]
    ) -> Optional[AgronomyRecommendation]:
        """Get LLM-powered crop rotation advice"""
        prompt = f"""As an agronomy expert, recommend crop rotation for:
Current crop: {current_crop}
Previous crops: {', '.join(previous_crops)}
Soil pH: {soil_condition.ph_level if soil_condition and soil_condition.ph_level else 'Unknown'}

Recommend next crop for rotation and explain benefits.
JSON: {{"next_crop": "crop name", "reasoning": "why", "benefits": ["benefit 1", "benefit 2"]}}
Return ONLY valid JSON."""

        try:
            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=200
            )

            result = json.loads(response.strip())

            return AgronomyRecommendation(
                recommendation_id=str(uuid.uuid4()),
                decision_type=DecisionType.CROP_ROTATION,
                priority=RecommendationPriority.MEDIUM,
                action=f"Plant {result['next_crop']} in next season",
                reasoning=result.get("reasoning", ""),
                expected_outcome="; ".join(result.get("benefits", [])),
                timing="Next planting season",
                confidence_score=80.0
            )

        except Exception as e:
            logger.warning(f"LLM crop rotation advice failed: {e}")
            return None

    async def _generate_ai_insights(
        self,
        context: DecisionContext,
        analyses: List[DecisionAnalysis]
    ) -> List[str]:
        """Generate AI-powered insights from decision analyses"""
        summary = f"""Farm: {context.farm_location or 'Unknown'}
Crop: {context.crop_type}
Decisions analyzed: {len(analyses)}
Total recommendations: {sum(len(a.recommendations) for a in analyses)}"""

        prompt = f"""As an agronomy expert, provide 3-5 key insights from this farm analysis:

{summary}

Return JSON: {{"insights": ["insight 1", "insight 2", ...]}}
Return ONLY valid JSON."""

        try:
            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=200
            )

            result = json.loads(response.strip())
            return result.get("insights", [])

        except Exception as e:
            logger.warning(f"AI insights generation failed: {e}")
            return []

    def _calculate_farm_health_score(self, context: DecisionContext) -> Optional[float]:
        """Calculate overall farm health score"""
        if not context.crop_health:
            return None

        health_map = {
            CropHealthStatus.EXCELLENT: 100,
            CropHealthStatus.GOOD: 80,
            CropHealthStatus.FAIR: 60,
            CropHealthStatus.POOR: 40,
            CropHealthStatus.CRITICAL: 20
        }

        base_score = health_map.get(context.crop_health.overall_health_status, 60)

        # Adjust for soil and weather
        adjustments = 0
        if context.soil_condition and context.soil_condition.moisture_percent:
            if 40 <= context.soil_condition.moisture_percent <= 60:
                adjustments += 5
            elif context.soil_condition.moisture_percent < 30:
                adjustments -= 10

        if context.weather_data:
            if context.weather_data.drought_risk:
                adjustments -= 15
            if context.weather_data.frost_risk:
                adjustments -= 10

        return max(0, min(100, base_score + adjustments))

    def _calculate_sustainability_rating(
        self,
        analyses: List[DecisionAnalysis],
        prioritize_sustainability: bool
    ) -> str:
        """Calculate sustainability rating"""
        # Simplified rating based on recommendations
        total_recs = sum(len(a.recommendations) for a in analyses)

        if total_recs == 0:
            return "N/A"

        # In real implementation, would analyze recommendation types
        if prioritize_sustainability:
            return "High - Sustainable practices prioritized"
        else:
            return "Medium - Balance of productivity and sustainability"
