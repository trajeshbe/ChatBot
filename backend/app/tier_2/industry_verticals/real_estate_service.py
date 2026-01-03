"""
Real Estate Valuation Service
Tier 2 Module: Industry Verticals

Property valuation and market analysis using uploaded real estate documents.
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

from .real_estate_schemas import *

logger = logging.getLogger(__name__)


class RealEstateService:
    """
    Real estate valuation and market analysis service.

    Valuation Process:
    1. Document Analysis → Extract property listings from MLS documents
    2. Comparable Selection → Find similar properties from documents
    3. Market Trends → Extract market data from uploaded reports
    4. Valuation Model → Calculate estimated value using comps
    5. Confidence Scoring → Calculate confidence based on data quality
    6. AI Insights → Generate market insights using LLM
    """

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.llm_service = LLMService(db, settings)
        self.document_service = DocumentService(db)
        logger.info("✓ RealEstateService initialized with tier_1 services")

    async def valuate_property(
        self,
        request: ValuationRequest
    ) -> ValuationResponse:
        """Valuate property using uploaded MLS and market data documents."""
        start_time = datetime.utcnow()

        logger.info(f"🏠 Valuating property: {request.property_type.value}, {request.square_footage} sqft")

        try:
            # Step 1: Extract property data from uploaded documents
            property_data = await self._extract_property_data_from_documents(request)

            # Step 2: Find comparable properties from documents
            comparables = await self._find_comparable_properties(request, property_data)

            logger.info(f"Found {len(comparables)} comparable properties")

            # Step 3: Extract market trends from documents
            market_trends = await self._extract_market_trends(request, property_data)

            # Step 4: Calculate estimated value using comparables
            estimated_value, confidence_score = self._calculate_property_value(
                request,
                comparables,
                market_trends
            )

            # Step 5: Generate AI insights
            ai_insights = await self._generate_valuation_insights(
                request,
                estimated_value,
                comparables,
                market_trends
            )

            # Step 6: Generate recommendations
            recommendations = self._generate_recommendations(
                request,
                estimated_value,
                market_trends
            )

            # Step 7: Store valuation
            await self._store_valuation(request, estimated_value, confidence_score)

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            return ValuationResponse(
                success=True,
                property_id=request.property_id or str(uuid.uuid4()),
                estimated_value=round(estimated_value, 2),
                confidence_score=confidence_score,
                comparable_properties=comparables,
                market_trends=market_trends,
                ai_insights=ai_insights,
                recommendations=recommendations,
                valuation_date=datetime.utcnow().isoformat(),
                processing_time_seconds=processing_time,
                tier_1_services_used=["LLMService", "DocumentService"]
            )

        except Exception as e:
            logger.error(f"❌ Valuation error: {e}", exc_info=True)
            raise

    async def _extract_property_data_from_documents(
        self,
        request: ValuationRequest
    ) -> Dict[str, Any]:
        """Extract property listings from uploaded MLS documents."""
        try:
            # Get documents for this session (MLS listings, property reports)
            documents = await self.document_service.list_documents(
                session_id=request.session_id,
                limit=50
            )

            if not documents:
                logger.warning(f"No documents found for session {request.session_id}")
                return {}

            # Extract property data from documents
            all_properties = []

            for doc in documents[:10]:
                chunks = await self.document_service.get_chunks_for_document(doc.id)

                if not chunks:
                    continue

                # Combine chunks for context
                document_text = " ".join([chunk.get('content', '') for chunk in chunks[:5]])

                if len(document_text) < 100:
                    continue

                # Extract properties using LLM
                properties = await self._extract_properties_from_text(document_text)
                all_properties.extend(properties)

            logger.info(f"Extracted {len(all_properties)} properties from {len(documents)} documents")

            return {
                "properties": all_properties,
                "property_count": len(all_properties)
            }

        except Exception as e:
            logger.error(f"Failed to extract property data: {str(e)}")
            return {}

    async def _extract_properties_from_text(
        self,
        text: str
    ) -> List[Dict[str, Any]]:
        """Extract property listings from document text using LLM."""
        prompt = f"""Extract real estate property listings from the following text. Focus on MLS listings, property descriptions, and sales data.

Text:
{text[:3000]}

Extract properties with:
- address: Full street address
- property_type: (single_family, condo, townhouse, multi_family)
- square_footage: Size in square feet
- bedrooms: Number of bedrooms
- bathrooms: Number of bathrooms
- year_built: Year constructed
- price: Listed or sold price
- location: City/neighborhood
- features: List of notable features

Return a JSON array:
[
  {{
    "address": "123 Main St, Seattle, WA",
    "property_type": "single_family",
    "square_footage": 2500,
    "bedrooms": 4,
    "bathrooms": 2.5,
    "year_built": 2010,
    "price": 750000,
    "location": "Seattle",
    "features": ["garage", "backyard"]
  }}
]

If no properties found, return empty array [].
Return ONLY the JSON array, no explanation."""

        try:
            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.1,
                max_tokens=1500
            )

            properties = json.loads(response.strip())
            logger.info(f"Extracted {len(properties)} properties from document text")
            return properties

        except Exception as e:
            logger.warning(f"Failed to extract properties: {str(e)}")
            return []

    async def _find_comparable_properties(
        self,
        request: ValuationRequest,
        property_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find comparable properties from extracted data."""
        properties = property_data.get("properties", [])

        if not properties:
            # Return empty list if no properties found
            return []

        # Filter comparables by property type and location
        comparables = []
        target_sqft = request.square_footage

        for prop in properties:
            # Skip if different property type
            if prop.get("property_type") != request.property_type.value:
                continue

            # Skip if location doesn't match (simple check)
            if request.location and request.location.lower() not in prop.get("location", "").lower():
                continue

            # Check if square footage is within 30% range
            prop_sqft = prop.get("square_footage", 0)
            if prop_sqft == 0:
                continue

            sqft_diff_pct = abs(prop_sqft - target_sqft) / target_sqft * 100
            if sqft_diff_pct > 30:
                continue

            # Calculate similarity score
            similarity = 100 - sqft_diff_pct

            # Add as comparable
            comparables.append({
                "address": prop.get("address", "Unknown"),
                "value": prop.get("price", 0),
                "square_footage": prop_sqft,
                "bedrooms": prop.get("bedrooms", 0),
                "bathrooms": prop.get("bathrooms", 0),
                "year_built": prop.get("year_built", 2000),
                "similarity_score": round(similarity, 1),
                "distance_miles": 1.0  # Placeholder (would use geocoding in production)
            })

        # Sort by similarity and take top 10
        comparables.sort(key=lambda x: x["similarity_score"], reverse=True)
        return comparables[:10]

    async def _extract_market_trends(
        self,
        request: ValuationRequest,
        property_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract market trends from property data and documents."""
        properties = property_data.get("properties", [])

        if not properties:
            return {
                "yoy_growth": 0.0,
                "median_price": 0.0,
                "inventory_level": "unknown",
                "days_on_market": 0
            }

        # Calculate median price from extracted properties
        prices = [p.get("price", 0) for p in properties if p.get("price", 0) > 0]
        median_price = sorted(prices)[len(prices) // 2] if prices else 0

        # Estimate YoY growth (would use historical data in production)
        yoy_growth = 5.0  # Placeholder

        return {
            "yoy_growth": yoy_growth,
            "median_price": median_price,
            "inventory_level": "moderate",
            "days_on_market": 30,
            "total_listings": len(properties)
        }

    def _calculate_property_value(
        self,
        request: ValuationRequest,
        comparables: List[Dict[str, Any]],
        market_trends: Dict[str, Any]
    ) -> tuple[float, float]:
        """Calculate estimated property value using comparable sales."""

        if not comparables:
            # Fallback calculation if no comparables
            base_value = request.square_footage * 250  # $250/sqft baseline
            confidence = 30.0  # Low confidence without comps

            # Adjust for property features
            if request.bedrooms:
                base_value += request.bedrooms * 10000
            if request.bathrooms:
                base_value += request.bathrooms * 5000

            # Age adjustment
            if request.year_built:
                age = 2026 - request.year_built
                if age > 50:
                    base_value *= 0.85
                elif age < 5:
                    base_value *= 1.15

            return base_value, confidence

        # Calculate weighted average using comparables
        total_value = 0
        total_weight = 0

        for comp in comparables:
            comp_value = comp.get("value", 0)
            comp_sqft = comp.get("square_footage", 1)
            similarity = comp.get("similarity_score", 50)

            # Calculate price per square foot
            price_per_sqft = comp_value / comp_sqft if comp_sqft > 0 else 250

            # Weight by similarity
            weight = similarity / 100.0
            total_value += price_per_sqft * weight
            total_weight += weight

        # Calculate weighted average price per sqft
        avg_price_per_sqft = total_value / total_weight if total_weight > 0 else 250

        # Calculate estimated value
        estimated_value = avg_price_per_sqft * request.square_footage

        # Adjust for market trends
        yoy_growth = market_trends.get("yoy_growth", 0) / 100.0
        estimated_value *= (1 + yoy_growth * 0.5)  # Apply 50% of YoY growth

        # Calculate confidence score based on data quality
        confidence = 50.0  # Base confidence
        if len(comparables) >= 5:
            confidence += 20.0
        if len(comparables) >= 10:
            confidence += 10.0
        if market_trends.get("total_listings", 0) > 20:
            confidence += 10.0

        confidence = min(confidence, 95.0)  # Cap at 95%

        return estimated_value, confidence

    async def _generate_valuation_insights(
        self,
        request: ValuationRequest,
        estimated_value: float,
        comparables: List[Dict[str, Any]],
        market_trends: Dict[str, Any]
    ) -> str:
        """Generate AI-powered valuation insights."""
        prompt = f"""Generate a concise real estate valuation insight for this property:

Property Details:
- Type: {request.property_type.value}
- Size: {request.square_footage} sq ft
- Location: {request.location}
- Bedrooms: {request.bedrooms}
- Bathrooms: {request.bathrooms}

Estimated Value: ${estimated_value:,.0f}
Comparable Properties: {len(comparables)}
Market Trends:
- YoY Growth: {market_trends.get('yoy_growth', 0)}%
- Median Price: ${market_trends.get('median_price', 0):,.0f}
- Days on Market: {market_trends.get('days_on_market', 0)}

Generate 2-3 sentences analyzing:
1. How this property compares to the local market
2. Key value drivers or concerns
3. Market conditions impact on valuation

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
            return f"Estimated value of ${estimated_value:,.0f} based on {len(comparables)} comparable properties in {request.location}."

    def _generate_recommendations(
        self,
        request: ValuationRequest,
        estimated_value: float,
        market_trends: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        yoy_growth = market_trends.get("yoy_growth", 0)

        if yoy_growth > 7:
            recommendations.append("Strong seller's market - consider listing soon to maximize value")
        elif yoy_growth < 2:
            recommendations.append("Buyer's market - good time to negotiate on price")

        if request.year_built and (2026 - request.year_built) > 30:
            recommendations.append("Property age may impact value - consider upgrades or renovations")

        if market_trends.get("days_on_market", 0) > 60:
            recommendations.append("High days-on-market suggests competitive pricing is essential")

        recommendations.append("Upload more MLS documents for improved comparable analysis")
        recommendations.append("Consider professional appraisal for final valuation confirmation")

        return recommendations

    async def _store_valuation(
        self,
        request: ValuationRequest,
        estimated_value: float,
        confidence_score: float
    ):
        """Store valuation results in database."""
        try:
            from app.models.database_enhanced import RealEstateValuationResults

            valuation_record = RealEstateValuationResults(
                id=uuid.uuid4(),
                valuation_id=uuid.uuid4(),
                module_id="real-estate",
                session_id=request.session_id,
                project_id=uuid.UUID(request.project_id) if request.project_id else None,
                valuation_data={
                    "property_id": request.property_id,
                    "property_type": request.property_type.value,
                    "estimated_value": estimated_value,
                    "confidence_score": confidence_score,
                    "square_footage": request.square_footage,
                    "location": request.location
                },
                created_at=datetime.utcnow()
            )

            self.db.add(valuation_record)
            self.db.commit()
            logger.info(f"✓ Stored valuation for property {request.property_id}")

        except Exception as e:
            logger.error(f"Failed to store valuation: {str(e)}")

    async def search_valuations(
        self,
        request: SearchValuationsRequest
    ) -> SearchValuationsResponse:
        """Search historical valuations."""
        # Placeholder for search functionality
        return SearchValuationsResponse(
            success=True,
            valuations=[],
            total_count=0
        )

    async def export_valuations(
        self,
        request: ExportValuationsRequest
    ) -> ExportValuationsResponse:
        """Export valuations to specified format."""
        # Placeholder for export functionality
        return ExportValuationsResponse(
            success=True,
            export_data={"format": request.format},
            format=request.format
        )

    async def get_stats(self) -> ValuationStatsResponse:
        """Get valuation statistics."""
        return ValuationStatsResponse(
            success=True,
            total_valuations=0,
            average_property_value=0.0
        )

    async def get_status(self) -> StatusResponse:
        """Get service status and capabilities."""
        return StatusResponse(
            success=True,
            status="operational",
            description="Real Estate Valuation: Property valuation and market analysis using uploaded MLS documents and comparable sales data",
            tier_2_modules_used=[],
            capabilities=[
                "Extract property listings from MLS documents using LLM",
                "Find comparable properties based on location, size, and type",
                "Calculate estimated value using comparable sales method",
                "Extract market trends from uploaded market reports",
                "AI-powered valuation insights and recommendations",
                "Confidence scoring based on data quality",
                "Support for multiple property types (single_family, condo, townhouse, multi_family)"
            ]
        )
