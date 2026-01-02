"""
Product Recommendation Schemas
Tier 2 Module: E-commerce

Pydantic models for AI-powered product recommendation engine.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class ProductCategory(str, Enum):
    """Product categories"""
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    BOOKS = "books"
    HOME_GARDEN = "home_garden"
    SPORTS = "sports"
    TOYS = "toys"
    BEAUTY = "beauty"
    FOOD_BEVERAGE = "food_beverage"
    AUTOMOTIVE = "automotive"
    HEALTH = "health"
    JEWELRY = "jewelry"
    PET_SUPPLIES = "pet_supplies"
    OFFICE = "office"
    OTHER = "other"


class RecommendationStrategy(str, Enum):
    """Recommendation algorithm strategies"""
    COLLABORATIVE_FILTERING = "collaborative_filtering"  # Based on user behavior patterns
    CONTENT_BASED = "content_based"  # Based on product attributes
    HYBRID = "hybrid"  # Combination of collaborative and content-based
    TRENDING = "trending"  # Popular products
    PERSONALIZED = "personalized"  # AI-powered personalization
    SIMILAR_PRODUCTS = "similar_products"  # Similar to a specific product
    CROSS_SELL = "cross_sell"  # Frequently bought together
    UPSELL = "upsell"  # Higher-value alternatives


class UserInteractionType(str, Enum):
    """Types of user interactions"""
    VIEW = "view"
    ADD_TO_CART = "add_to_cart"
    PURCHASE = "purchase"
    WISHLIST = "wishlist"
    SEARCH = "search"
    RATING = "rating"
    REVIEW = "review"


class PriceRange(str, Enum):
    """Price range categories"""
    BUDGET = "budget"  # <$25
    AFFORDABLE = "affordable"  # $25-$100
    MID_RANGE = "mid_range"  # $100-$500
    PREMIUM = "premium"  # $500-$2000
    LUXURY = "luxury"  # >$2000


class Product(BaseModel):
    """Product information"""
    product_id: str
    name: str
    description: Optional[str] = None
    category: ProductCategory
    price: float = Field(..., ge=0.0)
    brand: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    review_count: Optional[int] = Field(None, ge=0)
    in_stock: bool = True
    image_url: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Custom product attributes")


class UserInteraction(BaseModel):
    """User interaction with a product"""
    user_id: str
    product_id: str
    interaction_type: UserInteractionType
    timestamp: datetime
    interaction_value: Optional[float] = Field(None, description="Rating value or purchase amount")
    session_id: Optional[str] = None


class UserProfile(BaseModel):
    """User profile for personalization"""
    user_id: str
    preferred_categories: List[ProductCategory] = Field(default_factory=list)
    price_sensitivity: Optional[PriceRange] = None
    favorite_brands: List[str] = Field(default_factory=list)
    recent_searches: List[str] = Field(default_factory=list)
    purchase_history_count: int = Field(0, ge=0)
    average_order_value: Optional[float] = Field(None, ge=0.0)


class ProductRecommendation(BaseModel):
    """Single product recommendation with scoring"""
    product: Product
    relevance_score: float = Field(..., ge=0.0, le=100.0, description="How relevant this product is (0-100)")
    confidence_score: float = Field(..., ge=0.0, le=100.0, description="Confidence in recommendation (0-100)")
    reasoning: str = Field(..., description="Why this product is recommended")
    recommendation_strategy: RecommendationStrategy
    expected_conversion_probability: Optional[float] = Field(None, ge=0.0, le=1.0)


class ProductRecommendationRequest(BaseModel):
    """Request for product recommendations"""
    user_id: Optional[str] = None
    user_profile: Optional[UserProfile] = None
    user_interactions: List[UserInteraction] = Field(default_factory=list)
    product_catalog: List[Product] = Field(..., description="Available products to recommend from")
    current_product_id: Optional[str] = Field(None, description="Product being viewed (for similar products)")
    cart_product_ids: List[str] = Field(default_factory=list, description="Products in cart (for cross-sell)")
    recommendation_strategy: RecommendationStrategy = RecommendationStrategy.HYBRID
    max_recommendations: int = Field(10, ge=1, le=50)
    min_relevance_score: float = Field(50.0, ge=0.0, le=100.0)
    exclude_product_ids: List[str] = Field(default_factory=list)
    filter_categories: List[ProductCategory] = Field(default_factory=list, description="Filter by categories")
    price_range_min: Optional[float] = Field(None, ge=0.0)
    price_range_max: Optional[float] = Field(None, ge=0.0)
    session_id: Optional[str] = None
    project_id: Optional[str] = None


class RecommendationMetrics(BaseModel):
    """Metrics about recommendation performance"""
    total_products_analyzed: int
    recommendations_generated: int
    average_relevance_score: float
    average_confidence_score: float
    strategy_used: RecommendationStrategy
    personalization_applied: bool
    processing_time_ms: Optional[float] = None


class ProductRecommendationResponse(BaseModel):
    """Response with product recommendations"""
    recommendations: List[ProductRecommendation] = Field(default_factory=list)
    metrics: RecommendationMetrics
    trending_products: List[Product] = Field(default_factory=list)
    personalization_insights: List[str] = Field(default_factory=list, description="AI insights on user preferences")
    cross_sell_opportunities: List[ProductRecommendation] = Field(default_factory=list)
    upsell_opportunities: List[ProductRecommendation] = Field(default_factory=list)


class SearchRecommendationsRequest(BaseModel):
    """Search historical recommendations"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    recommendation_strategy: Optional[RecommendationStrategy] = None
    min_relevance_score: Optional[float] = None
    limit: int = Field(20, ge=1, le=100)


class ExportRecommendationsRequest(BaseModel):
    """Export recommendation data"""
    recommendation_ids: Optional[List[str]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    format: str = Field("json", pattern="^(json|csv|excel|pdf)$")


class RecommendationStatsResponse(BaseModel):
    """Recommendation engine statistics"""
    total_recommendations_generated: int
    recommendations_by_strategy: Dict[str, int] = Field(default_factory=dict)
    average_relevance_score: Optional[float] = None
    average_confidence_score: Optional[float] = None
    top_recommended_categories: List[str] = Field(default_factory=list)
    total_users_served: int = 0
    average_conversion_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
