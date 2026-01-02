"""
Sentiment Social Schemas
Tier 2 Module: Marketing

Pydantic models for social media sentiment analysis and brand monitoring.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class SocialPlatform(str, Enum):
    """Social media platforms"""
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    REDDIT = "reddit"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    CUSTOM = "custom"


class SentimentScore(str, Enum):
    """Sentiment classification"""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class EmotionType(str, Enum):
    """Emotion classifications"""
    JOY = "joy"
    TRUST = "trust"
    FEAR = "fear"
    SURPRISE = "surprise"
    SADNESS = "sadness"
    DISGUST = "disgust"
    ANGER = "anger"
    ANTICIPATION = "anticipation"


class PostType(str, Enum):
    """Type of social media content"""
    POST = "post"
    COMMENT = "comment"
    REVIEW = "review"
    REPLY = "reply"
    SHARE = "share"
    MENTION = "mention"


class InfluencerTier(str, Enum):
    """Influencer categorization by follower count"""
    NANO = "nano"  # <10K
    MICRO = "micro"  # 10K-100K
    MID_TIER = "mid_tier"  # 100K-500K
    MACRO = "macro"  # 500K-1M
    MEGA = "mega"  # >1M


class SocialPost(BaseModel):
    """Individual social media post/comment"""
    post_id: str
    platform: SocialPlatform
    post_type: PostType
    content: str = Field(..., description="Post text content")
    author: Optional[str] = None
    author_followers: Optional[int] = Field(None, ge=0)
    posted_at: Optional[str] = None
    likes_count: Optional[int] = Field(None, ge=0)
    shares_count: Optional[int] = Field(None, ge=0)
    comments_count: Optional[int] = Field(None, ge=0)
    hashtags: List[str] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)
    url: Optional[str] = None


class SentimentAnalysis(BaseModel):
    """Sentiment analysis result for a post"""
    post_id: str
    sentiment_score: SentimentScore
    confidence: float = Field(..., ge=0.0, le=100.0)
    polarity_score: float = Field(..., ge=-1.0, le=1.0, description="Negative to positive scale")
    subjectivity_score: float = Field(..., ge=0.0, le=1.0, description="Objective to subjective scale")
    primary_emotion: Optional[EmotionType] = None
    emotion_scores: Dict[str, float] = Field(default_factory=dict)
    key_phrases: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    language: Optional[str] = Field(None, description="Detected language (ISO 639-1)")


class InfluencerAnalysis(BaseModel):
    """Influencer impact analysis"""
    author: str
    follower_count: int
    influencer_tier: InfluencerTier
    posts_analyzed: int
    average_sentiment: SentimentScore
    total_engagement: int = Field(..., description="Total likes + shares + comments")
    engagement_rate: float = Field(..., ge=0.0, le=100.0, description="Engagement / followers * 100")
    reach_estimate: int = Field(..., description="Estimated reach based on followers + shares")


class TrendingTopic(BaseModel):
    """Trending topic identification"""
    topic: str
    mention_count: int
    sentiment_distribution: Dict[str, int] = Field(default_factory=dict)
    dominant_sentiment: SentimentScore
    hashtags: List[str] = Field(default_factory=list)
    influencers_discussing: List[str] = Field(default_factory=list)
    engagement_score: float = Field(..., ge=0.0, description="Weighted engagement score")


class BrandMentionAnalysis(BaseModel):
    """Brand mention and perception analysis"""
    brand_name: str
    total_mentions: int
    sentiment_breakdown: Dict[str, int] = Field(default_factory=dict)
    net_sentiment_score: float = Field(..., ge=-100.0, le=100.0, description="Positive% - Negative%")
    share_of_voice: Optional[float] = Field(None, ge=0.0, le=100.0, description="% of total mentions in category")
    top_associated_keywords: List[str] = Field(default_factory=list)
    competitor_comparison: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SentimentSocialRequest(BaseModel):
    """Request for social media sentiment analysis"""
    posts: List[SocialPost] = Field(..., description="Social media posts to analyze")
    brand_names: List[str] = Field(default_factory=list, description="Brands to track")
    include_influencer_analysis: bool = Field(True, description="Analyze influencer impact")
    include_trending_topics: bool = Field(True, description="Identify trending topics")
    include_emotion_analysis: bool = Field(True, description="Detailed emotion classification")
    language_filter: Optional[str] = Field(None, description="Filter by language (ISO 639-1)")
    session_id: Optional[str] = None
    project_id: Optional[str] = None


class SentimentSocialResponse(BaseModel):
    """Response with sentiment analysis results"""
    sentiment_analyses: List[SentimentAnalysis]
    overall_sentiment: SentimentScore
    sentiment_distribution: Dict[str, int] = Field(default_factory=dict)
    average_polarity: float = Field(..., ge=-1.0, le=1.0)
    influencer_analyses: List[InfluencerAnalysis] = Field(default_factory=list)
    trending_topics: List[TrendingTopic] = Field(default_factory=list)
    brand_mentions: List[BrandMentionAnalysis] = Field(default_factory=list)
    total_posts_analyzed: int
    total_engagement: int
    ai_insights: List[str] = Field(default_factory=list)


class SearchSentimentRequest(BaseModel):
    """Search historical sentiment analyses"""
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    platform: Optional[SocialPlatform] = None
    sentiment: Optional[SentimentScore] = None
    brand_name: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    limit: int = Field(20, ge=1, le=100)


class ExportSentimentRequest(BaseModel):
    """Export sentiment data"""
    analysis_ids: Optional[List[str]] = None
    session_id: Optional[str] = None
    platform: Optional[SocialPlatform] = None
    format: str = Field("json", pattern="^(json|csv|excel|pdf)$")


class SentimentStatsResponse(BaseModel):
    """Sentiment statistics"""
    total_analyses_performed: int
    analyses_by_platform: Dict[str, int] = Field(default_factory=dict)
    sentiment_distribution: Dict[str, int] = Field(default_factory=dict)
    average_engagement_rate: Optional[float] = Field(None, ge=0.0, le=100.0)
    top_brands_monitored: List[str] = Field(default_factory=list)
    top_influencers: List[str] = Field(default_factory=list)
    trending_topics_summary: List[Dict[str, Any]] = Field(default_factory=list)
