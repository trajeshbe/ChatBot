"""
Product Recommendation Service
Tier 2 Module: E-commerce

Service for AI-powered product recommendation engine.
Leverages Tier 1 LLMService for personalized recommendations.
"""

import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from collections import Counter
from datetime import datetime, timedelta

from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from .product_recommendation_schemas import (
    ProductRecommendationRequest,
    ProductRecommendationResponse,
    Product,
    ProductRecommendation,
    UserInteraction,
    UserProfile,
    RecommendationMetrics,
    RecommendationStrategy,
    UserInteractionType,
    ProductCategory
)

logger = logging.getLogger(__name__)


class ProductRecommendationService:
    """Service for AI-powered product recommendations"""

    def __init__(self, db: Session, settings: Settings, config: Optional[Dict[str, Any]] = None):
        self.db = db
        self.settings = settings
        self.config = config or {}
        # Tier 1 service dependencies
        self.llm_service = LLMService()

        logger.info("✓ ProductRecommendationService initialized with tier_1 services")
        if config:
            logger.info(f"✓ Using module config with model: {config.get(\'llm\', {}).get(\'default\', {}).get(\'model\', \'default\')}")

    async def recommend_products(self, request: ProductRecommendationRequest) -> ProductRecommendationResponse:
        """Generate personalized product recommendations"""
        start_time = datetime.now()
        logger.info(f"🛍️ Generating recommendations for {len(request.product_catalog)} products")

        # Apply filters first
        filtered_catalog = self._filter_products(
            request.product_catalog,
            request.exclude_product_ids,
            request.filter_categories,
            request.price_range_min,
            request.price_range_max
        )

        logger.info(f"📦 Filtered catalog: {len(filtered_catalog)} products")

        # Generate recommendations based on strategy
        if request.recommendation_strategy == RecommendationStrategy.COLLABORATIVE_FILTERING:
            recommendations = await self._collaborative_filtering(request, filtered_catalog)
        elif request.recommendation_strategy == RecommendationStrategy.CONTENT_BASED:
            recommendations = self._content_based_filtering(request, filtered_catalog)
        elif request.recommendation_strategy == RecommendationStrategy.TRENDING:
            recommendations = self._trending_products(filtered_catalog)
        elif request.recommendation_strategy == RecommendationStrategy.SIMILAR_PRODUCTS:
            recommendations = await self._similar_products(request, filtered_catalog)
        elif request.recommendation_strategy == RecommendationStrategy.CROSS_SELL:
            recommendations = await self._cross_sell_recommendations(request, filtered_catalog)
        elif request.recommendation_strategy == RecommendationStrategy.UPSELL:
            recommendations = self._upsell_recommendations(request, filtered_catalog)
        elif request.recommendation_strategy == RecommendationStrategy.PERSONALIZED:
            recommendations = await self._personalized_recommendations(request, filtered_catalog)
        else:  # HYBRID
            recommendations = await self._hybrid_recommendations(request, filtered_catalog)

        # Filter by minimum relevance score
        recommendations = [
            r for r in recommendations
            if r.relevance_score >= request.min_relevance_score
        ]

        # Sort by relevance and limit
        recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
        recommendations = recommendations[:request.max_recommendations]

        # Get trending products
        trending = self._trending_products(filtered_catalog)[:5]

        # Generate cross-sell and upsell if not already the main strategy
        cross_sell = []
        upsell = []
        if request.recommendation_strategy not in [RecommendationStrategy.CROSS_SELL, RecommendationStrategy.UPSELL]:
            cross_sell = await self._cross_sell_recommendations(request, filtered_catalog)
            cross_sell = cross_sell[:3]
            upsell = self._upsell_recommendations(request, filtered_catalog)
            upsell = upsell[:3]

        # Generate personalization insights
        insights = await self._generate_personalization_insights(request, recommendations)

        # Calculate metrics
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        metrics = RecommendationMetrics(
            total_products_analyzed=len(request.product_catalog),
            recommendations_generated=len(recommendations),
            average_relevance_score=round(sum(r.relevance_score for r in recommendations) / len(recommendations), 2) if recommendations else 0.0,
            average_confidence_score=round(sum(r.confidence_score for r in recommendations) / len(recommendations), 2) if recommendations else 0.0,
            strategy_used=request.recommendation_strategy,
            personalization_applied=request.user_profile is not None or len(request.user_interactions) > 0,
            processing_time_ms=round(processing_time, 2)
        )

        logger.info(f"✓ Generated {len(recommendations)} recommendations (avg relevance: {metrics.average_relevance_score:.1f})")

        return ProductRecommendationResponse(
            recommendations=recommendations,
            metrics=metrics,
            trending_products=[t.product for t in trending],
            personalization_insights=insights,
            cross_sell_opportunities=cross_sell,
            upsell_opportunities=upsell
        )

    def _filter_products(
        self,
        catalog: List[Product],
        exclude_ids: List[str],
        filter_categories: List[ProductCategory],
        price_min: Optional[float],
        price_max: Optional[float]
    ) -> List[Product]:
        """Apply filters to product catalog"""
        filtered = catalog

        # Exclude specific products
        if exclude_ids:
            filtered = [p for p in filtered if p.product_id not in exclude_ids]

        # Filter by category
        if filter_categories:
            filtered = [p for p in filtered if p.category in filter_categories]

        # Filter by price range
        if price_min is not None:
            filtered = [p for p in filtered if p.price >= price_min]
        if price_max is not None:
            filtered = [p for p in filtered if p.price <= price_max]

        # Only in-stock products
        filtered = [p for p in filtered if p.in_stock]

        return filtered

    async def _collaborative_filtering(
        self,
        request: ProductRecommendationRequest,
        catalog: List[Product]
    ) -> List[ProductRecommendation]:
        """Collaborative filtering based on user interactions"""
        recommendations = []

        # Analyze user interactions to find patterns
        purchased_products = [
            i.product_id for i in request.user_interactions
            if i.interaction_type == UserInteractionType.PURCHASE
        ]

        viewed_products = [
            i.product_id for i in request.user_interactions
            if i.interaction_type == UserInteractionType.VIEW
        ]

        # Score products based on interaction similarity
        for product in catalog:
            if product.product_id in purchased_products or product.product_id in viewed_products:
                continue

            # Simple scoring based on category overlap with purchased/viewed products
            purchased_cats = [p.category for p in catalog if p.product_id in purchased_products]
            viewed_cats = [p.category for p in catalog if p.product_id in viewed_products]

            category_match_score = 0
            if product.category in purchased_cats:
                category_match_score = 80
            elif product.category in viewed_cats:
                category_match_score = 60

            if category_match_score > 0:
                recommendations.append(ProductRecommendation(
                    product=product,
                    relevance_score=min(100, category_match_score + (product.rating or 0) * 10),
                    confidence_score=70.0,
                    reasoning=f"Users with similar interests often purchase {product.category.value} products",
                    recommendation_strategy=RecommendationStrategy.COLLABORATIVE_FILTERING,
                    expected_conversion_probability=0.15
                ))

        return recommendations

    def _content_based_filtering(
        self,
        request: ProductRecommendationRequest,
        catalog: List[Product]
    ) -> List[ProductRecommendation]:
        """Content-based filtering using product attributes"""
        recommendations = []

        # Extract user preferences from profile and interactions
        preferred_categories = set()
        favorite_brands = set()

        if request.user_profile:
            preferred_categories.update(request.user_profile.preferred_categories)
            favorite_brands.update(request.user_profile.favorite_brands)

        # Analyze past purchases
        for interaction in request.user_interactions:
            if interaction.interaction_type == UserInteractionType.PURCHASE:
                product = next((p for p in catalog if p.product_id == interaction.product_id), None)
                if product:
                    preferred_categories.add(product.category)
                    if product.brand:
                        favorite_brands.add(product.brand)

        # Score products
        for product in catalog:
            score = 50  # Base score

            # Category match
            if product.category in preferred_categories:
                score += 30

            # Brand match
            if product.brand and product.brand in favorite_brands:
                score += 20

            # Rating boost
            if product.rating:
                score += product.rating * 2

            if score > 50:
                recommendations.append(ProductRecommendation(
                    product=product,
                    relevance_score=min(100, score),
                    confidence_score=75.0,
                    reasoning=f"Matches your preference for {product.category.value}" + (f" by {product.brand}" if product.brand else ""),
                    recommendation_strategy=RecommendationStrategy.CONTENT_BASED,
                    expected_conversion_probability=0.20
                ))

        return recommendations

    def _trending_products(self, catalog: List[Product]) -> List[ProductRecommendation]:
        """Identify trending/popular products"""
        # Sort by rating and review count
        trending = sorted(
            catalog,
            key=lambda p: (p.rating or 0) * (p.review_count or 0),
            reverse=True
        )

        recommendations = []
        for i, product in enumerate(trending[:20]):
            popularity_score = 100 - (i * 3)  # Decreasing score
            recommendations.append(ProductRecommendation(
                product=product,
                relevance_score=max(50, popularity_score),
                confidence_score=90.0,
                reasoning=f"Trending product with {product.rating or 0:.1f}★ rating ({product.review_count or 0} reviews)",
                recommendation_strategy=RecommendationStrategy.TRENDING,
                expected_conversion_probability=0.25
            ))

        return recommendations

    async def _similar_products(
        self,
        request: ProductRecommendationRequest,
        catalog: List[Product]
    ) -> List[ProductRecommendation]:
        """Find products similar to a specific product"""
        if not request.current_product_id:
            return []

        current_product = next(
            (p for p in catalog if p.product_id == request.current_product_id),
            None
        )

        if not current_product:
            return []

        recommendations = []

        for product in catalog:
            if product.product_id == request.current_product_id:
                continue

            similarity_score = 0

            # Category match
            if product.category == current_product.category:
                similarity_score += 40

            # Brand match
            if product.brand and product.brand == current_product.brand:
                similarity_score += 20

            # Price similarity (within 30%)
            if current_product.price > 0:
                price_diff = abs(product.price - current_product.price) / current_product.price
                if price_diff < 0.3:
                    similarity_score += 25

            # Tag overlap
            common_tags = set(product.tags) & set(current_product.tags)
            if common_tags:
                similarity_score += len(common_tags) * 5

            if similarity_score >= 40:
                recommendations.append(ProductRecommendation(
                    product=product,
                    relevance_score=min(100, similarity_score),
                    confidence_score=85.0,
                    reasoning=f"Similar to {current_product.name} - same category and price range",
                    recommendation_strategy=RecommendationStrategy.SIMILAR_PRODUCTS,
                    expected_conversion_probability=0.30
                ))

        return recommendations

    async def _cross_sell_recommendations(
        self,
        request: ProductRecommendationRequest,
        catalog: List[Product]
    ) -> List[ProductRecommendation]:
        """Cross-sell recommendations (frequently bought together)"""
        if not request.cart_product_ids:
            return []

        cart_products = [p for p in catalog if p.product_id in request.cart_product_ids]
        if not cart_products:
            return []

        cart_categories = set(p.category for p in cart_products)

        recommendations = []

        # Complementary product logic
        complementary_map = {
            ProductCategory.ELECTRONICS: [ProductCategory.ELECTRONICS, ProductCategory.OFFICE],
            ProductCategory.CLOTHING: [ProductCategory.CLOTHING, ProductCategory.JEWELRY],
            ProductCategory.SPORTS: [ProductCategory.SPORTS, ProductCategory.HEALTH],
            ProductCategory.HOME_GARDEN: [ProductCategory.HOME_GARDEN, ProductCategory.OFFICE],
        }

        complementary_categories = set()
        for cart_cat in cart_categories:
            complementary_categories.update(complementary_map.get(cart_cat, [cart_cat]))

        for product in catalog:
            if product.product_id in request.cart_product_ids:
                continue

            if product.category in complementary_categories:
                relevance = 70 if product.category in cart_categories else 55

                recommendations.append(ProductRecommendation(
                    product=product,
                    relevance_score=relevance,
                    confidence_score=70.0,
                    reasoning=f"Frequently purchased with {cart_categories.pop().value if cart_categories else 'your items'}",
                    recommendation_strategy=RecommendationStrategy.CROSS_SELL,
                    expected_conversion_probability=0.18
                ))

        return recommendations

    def _upsell_recommendations(
        self,
        request: ProductRecommendationRequest,
        catalog: List[Product]
    ) -> List[ProductRecommendation]:
        """Upsell recommendations (higher-value alternatives)"""
        if not request.current_product_id:
            return []

        current_product = next(
            (p for p in catalog if p.product_id == request.current_product_id),
            None
        )

        if not current_product:
            return []

        recommendations = []

        # Find higher-priced products in the same category
        for product in catalog:
            if product.product_id == request.current_product_id:
                continue

            if product.category != current_product.category:
                continue

            # Price should be 20%-100% higher
            if product.price <= current_product.price * 1.2:
                continue
            if product.price > current_product.price * 2.0:
                continue

            value_score = 75
            if product.rating and current_product.rating:
                if product.rating > current_product.rating:
                    value_score += 15

            recommendations.append(ProductRecommendation(
                product=product,
                relevance_score=value_score,
                confidence_score=65.0,
                reasoning=f"Premium alternative - {int((product.price - current_product.price) / current_product.price * 100)}% more with better features",
                recommendation_strategy=RecommendationStrategy.UPSELL,
                expected_conversion_probability=0.12
            ))

        return recommendations

    async def _personalized_recommendations(
        self,
        request: ProductRecommendationRequest,
        catalog: List[Product]
    ) -> List[ProductRecommendation]:
        """AI-powered personalized recommendations"""
        # Use LLM to generate personalized insights
        user_summary = self._build_user_summary(request)

        # Generate base recommendations using content-based filtering
        base_recommendations = self._content_based_filtering(request, catalog)

        # Enhance with AI insights
        if base_recommendations and user_summary:
            try:
                # Use LLM to rank and enhance recommendations
                top_products = base_recommendations[:10]
                product_info = "\n".join([
                    f"- {p.product.name} ({p.product.category.value}, ${p.product.price:.2f})"
                    for p in top_products
                ])

                prompt = f"""Given this user profile:
{user_summary}

And these product options:
{product_info}

Provide a JSON array with personalized insights for each product, ordered by relevance:
{{"insights": ["insight for product 1", "insight for product 2", ...]}}

Return ONLY valid JSON."""

                # Get LLM parameters from module config
            llm_config = self.config.get('llm', {}).get('default', {})
            model = llm_config.get('model', 'gpt-4o-mini')
            temperature = llm_config.get('temperature', 0.3)
            max_tokens = llm_config.get('max_tokens', 300)

            response = await self.llm_service.generate_response(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

                result = json.loads(response.strip())
                insights = result.get("insights", [])

                # Update reasoning with AI insights
                for i, rec in enumerate(top_products):
                    if i < len(insights):
                        rec.reasoning = insights[i]
                        rec.confidence_score = min(100, rec.confidence_score + 10)

                return top_products

            except Exception as e:
                logger.warning(f"AI personalization failed: {e}")

        return base_recommendations

    async def _hybrid_recommendations(
        self,
        request: ProductRecommendationRequest,
        catalog: List[Product]
    ) -> List[ProductRecommendation]:
        """Hybrid approach combining multiple strategies"""
        # Combine collaborative and content-based
        collaborative = await self._collaborative_filtering(request, catalog)
        content_based = self._content_based_filtering(request, catalog)
        trending = self._trending_products(catalog)

        # Merge and deduplicate
        all_recommendations = {}

        for rec in collaborative:
            all_recommendations[rec.product.product_id] = rec

        for rec in content_based:
            if rec.product.product_id in all_recommendations:
                # Average the scores
                existing = all_recommendations[rec.product.product_id]
                existing.relevance_score = (existing.relevance_score + rec.relevance_score) / 2
                existing.confidence_score = (existing.confidence_score + rec.confidence_score) / 2
                existing.reasoning = "Recommended based on multiple factors: user behavior and preferences"
            else:
                all_recommendations[rec.product.product_id] = rec

        for rec in trending[:5]:
            if rec.product.product_id not in all_recommendations:
                rec.relevance_score = rec.relevance_score * 0.8  # Slightly reduce trending score
                all_recommendations[rec.product.product_id] = rec

        return list(all_recommendations.values())

    def _build_user_summary(self, request: ProductRecommendationRequest) -> str:
        """Build a summary of user preferences"""
        summary_parts = []

        if request.user_profile:
            if request.user_profile.preferred_categories:
                cats = [c.value for c in request.user_profile.preferred_categories]
                summary_parts.append(f"Prefers: {', '.join(cats)}")

            if request.user_profile.favorite_brands:
                summary_parts.append(f"Favorite brands: {', '.join(request.user_profile.favorite_brands[:3])}")

            if request.user_profile.price_sensitivity:
                summary_parts.append(f"Price range: {request.user_profile.price_sensitivity.value}")

        if request.user_interactions:
            purchase_count = sum(1 for i in request.user_interactions if i.interaction_type == UserInteractionType.PURCHASE)
            summary_parts.append(f"{purchase_count} past purchases")

        return ". ".join(summary_parts) if summary_parts else "New user"

    async def _generate_personalization_insights(
        self,
        request: ProductRecommendationRequest,
        recommendations: List[ProductRecommendation]
    ) -> List[str]:
        """Generate AI insights about user preferences"""
        if not recommendations:
            return []

        user_summary = self._build_user_summary(request)

        prompt = f"""User profile: {user_summary}

Top recommendations: {', '.join([r.product.name for r in recommendations[:5]])}

Provide 3 brief insights about this user's shopping preferences.

Return JSON: {{"insights": ["insight 1", "insight 2", "insight 3"]}}
Return ONLY valid JSON."""

        try:
            # Get LLM parameters from module config
            llm_config = self.config.get('llm', {}).get('default', {})
            model = llm_config.get('model', 'gpt-4o-mini')
            temperature = llm_config.get('temperature', 0.3)
            max_tokens = llm_config.get('max_tokens', 150)

            response = await self.llm_service.generate_response(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

            result = json.loads(response.strip())
            return result.get("insights", [])

        except Exception as e:
            logger.warning(f"Personalization insights generation failed: {e}")
            return []
