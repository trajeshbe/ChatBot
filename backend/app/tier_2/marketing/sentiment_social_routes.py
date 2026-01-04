"""
Sentiment Social API Routes
Tier 2 Module: Marketing

REST endpoints for social media sentiment analysis and brand monitoring.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from app.services.module_config_helper import load_module_config
from .sentiment_social_service import SentimentSocialService
from .sentiment_social_schemas import (
    SentimentSocialRequest,
    SentimentSocialResponse,
    SearchSentimentRequest,
    ExportSentimentRequest,
    SentimentStatsResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/modules/sentiment-social",
    tags=["Marketing", "Tier 2 Modules", "Social Media Sentiment"]
)


@router.post("/analyze", response_model=SentimentSocialResponse)
async def analyze_social_sentiment(
    request: SentimentSocialRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    Analyze social media posts for sentiment, trends, and brand perception.

    **Platforms Supported:**
    - Twitter, Facebook, Instagram, LinkedIn
    - Reddit, YouTube, TikTok, Custom

    **Analysis Features:**
    - **Sentiment Classification**: Very Positive → Very Negative (5-point scale)
    - **Emotion Detection**: 8 emotion types (joy, trust, fear, surprise, sadness, disgust, anger, anticipation)
    - **Polarity Scoring**: -1.0 (negative) to +1.0 (positive)
    - **Subjectivity Analysis**: 0.0 (objective) to 1.0 (subjective)
    - **Topic Extraction**: AI-identified discussion topics
    - **Key Phrase Extraction**: Important phrases and keywords

    **Influencer Analysis:**
    - Tier classification (Nano → Mega based on followers)
    - Engagement rate calculation
    - Reach estimation
    - Average sentiment per influencer

    **Trending Topics:**
    - Topic mention frequency
    - Sentiment distribution per topic
    - Associated hashtags
    - Influencers discussing topic
    - Engagement score ranking

    **Brand Mention Analysis:**
    - Total mentions count
    - Sentiment breakdown (positive/neutral/negative)
    - Net sentiment score (positive% - negative%)
    - Share of voice (% of total conversation)
    - Associated keywords and phrases
    - Competitor comparison (optional)

    **Example request:**
    ```json
    {
      "posts": [
        {
          "post_id": "tweet123",
          "platform": "twitter",
          "post_type": "post",
          "content": "Just tried the new product - amazing quality!",
          "author": "john_doe",
          "author_followers": 5000,
          "likes_count": 25,
          "shares_count": 5,
          "hashtags": ["product", "review"]
        }
      ],
      "brand_names": ["YourBrand", "CompetitorBrand"],
      "include_influencer_analysis": true,
      "include_trending_topics": true,
      "include_emotion_analysis": true
    }
    ```

    **Response includes:**
    - Individual sentiment analyses for each post
    - Overall sentiment and distribution
    - Average polarity score
    - Influencer impact analyses
    - Trending topics list
    - Brand mention analyses
    - Total engagement metrics
    - AI-generated insights
    """
    try:
        logger.info(f"📱 Social sentiment request for {len(request.posts)} posts")

        # Load module configuration
        module_config = await load_module_config(db, "sentiment_social")
        logger.info(f"✓ Loaded config for sentiment_social")

        # Initialize service with config
        service = SentimentSocialService(db, settings, config=module_config)
        result = await service.analyze_social_sentiment(request)

        logger.info(f"✓ Analyzed {result.total_posts_analyzed} posts: {result.overall_sentiment.value}")
        return result

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Sentiment analysis failed: {str(e)}")


@router.post("/search")
async def search_sentiment_analyses(request: SearchSentimentRequest, db: Session = Depends(get_db)):
    """Search historical sentiment analyses."""
    try:
        from app.models.database_enhanced import SentimentResults
        import uuid

        logger.info(f"🔍 Search sentiment analyses")

        query = db.query(SentimentResults).filter(SentimentResults.module_id == "sentiment-social")

        if request.session_id:
            query = query.filter(SentimentResults.session_id == request.session_id)
        if request.project_id:
            query = query.filter(SentimentResults.project_id == uuid.UUID(request.project_id))
        if request.platform:
            query = query.filter(SentimentResults.sentiment_data["platform"].astext == request.platform.value)
        if request.sentiment:
            query = query.filter(SentimentResults.sentiment_data["overall_sentiment"].astext == request.sentiment.value)
        if request.brand_name:
            query = query.filter(SentimentResults.sentiment_data["brand_name"].astext.ilike(f"%{request.brand_name}%"))

        results = query.limit(request.limit).all()

        analyses = [
            {
                "analysis_id": str(r.sentiment_id),
                "platform": r.sentiment_data.get("platform"),
                "sentiment": r.sentiment_data.get("overall_sentiment"),
                "brand": r.sentiment_data.get("brand_name"),
                "created_at": r.created_at.isoformat()
            }
            for r in results
        ]

        return {"analyses": analyses, "count": len(analyses)}

    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Search failed: {str(e)}")


@router.post("/export")
async def export_sentiment_data(request: ExportSentimentRequest, db: Session = Depends(get_db)):
    """Export sentiment analysis data."""
    try:
        from app.models.database_enhanced import SentimentResults
        import uuid

        logger.info(f"📥 Export request in {request.format} format")

        query = db.query(SentimentResults).filter(SentimentResults.module_id == "sentiment-social")

        if request.analysis_ids:
            analysis_uuids = [uuid.UUID(aid) for aid in request.analysis_ids]
            query = query.filter(SentimentResults.sentiment_id.in_(analysis_uuids))
        elif request.session_id:
            query = query.filter(SentimentResults.session_id == request.session_id)
        elif request.platform:
            query = query.filter(SentimentResults.sentiment_data["platform"].astext == request.platform.value)

        results = query.all()

        if not results:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sentiment data found")

        export_data = [{
            "analysis_id": str(r.sentiment_id),
            "data": r.sentiment_data,
            "created_at": r.created_at.isoformat()
        } for r in results]

        return {"format": request.format, "data": export_data, "count": len(export_data)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Export failed: {str(e)}")


@router.get("/stats", response_model=SentimentStatsResponse)
async def get_sentiment_stats(session_id: str = None, db: Session = Depends(get_db)):
    """Get sentiment analysis statistics."""
    try:
        from app.models.database_enhanced import SentimentResults

        logger.info(f"📊 Stats request")

        query = db.query(SentimentResults).filter(SentimentResults.module_id == "sentiment-social")

        if session_id:
            query = query.filter(SentimentResults.session_id == session_id)

        results = query.all()

        total_analyses = len(results)

        # Count by platform
        analyses_by_platform = {}
        sentiment_distribution = {}
        brands_monitored = set()
        influencers = set()

        for r in results:
            platform = r.sentiment_data.get("platform", "unknown")
            analyses_by_platform[platform] = analyses_by_platform.get(platform, 0) + 1

            sentiment = r.sentiment_data.get("overall_sentiment", "neutral")
            sentiment_distribution[sentiment] = sentiment_distribution.get(sentiment, 0) + 1

            if "brand_mentions" in r.sentiment_data:
                for brand_mention in r.sentiment_data["brand_mentions"]:
                    brands_monitored.add(brand_mention.get("brand_name"))

            if "influencer_analyses" in r.sentiment_data:
                for influencer in r.sentiment_data["influencer_analyses"]:
                    influencers.add(influencer.get("author"))

        top_brands = list(brands_monitored)[:10]
        top_influencers = list(influencers)[:10]

        return SentimentStatsResponse(
            total_analyses_performed=total_analyses,
            analyses_by_platform=analyses_by_platform,
            sentiment_distribution=sentiment_distribution,
            average_engagement_rate=None,  # Would be calculated from actual data
            top_brands_monitored=top_brands,
            top_influencers=top_influencers,
            trending_topics_summary=[]
        )

    except Exception as e:
        logger.error(f"Stats retrieval failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Stats retrieval failed: {str(e)}")


@router.get("/status")
async def get_module_status() -> Dict[str, Any]:
    """Get sentiment-social module status."""
    return {
        "module_id": "sentiment-social",
        "name": "Social Media Sentiment Analysis",
        "version": "1.0.0",
        "tier": 2,
        "category": "marketing",
        "description": "AI-powered social media sentiment analysis and brand monitoring",

        "platforms_supported": [
            "twitter", "facebook", "instagram", "linkedin",
            "reddit", "youtube", "tiktok", "custom"
        ],

        "sentiment_levels": ["very_positive", "positive", "neutral", "negative", "very_negative"],

        "emotion_types": [
            "joy", "trust", "fear", "surprise",
            "sadness", "disgust", "anger", "anticipation"
        ],

        "influencer_tiers": {
            "nano": "<10K followers",
            "micro": "10K-100K followers",
            "mid_tier": "100K-500K followers",
            "macro": "500K-1M followers",
            "mega": ">1M followers"
        },

        "features": {
            "sentiment_classification": True,
            "emotion_detection": True,
            "topic_extraction": True,
            "influencer_analysis": True,
            "trending_topics": True,
            "brand_monitoring": True,
            "competitor_analysis": True,
            "engagement_metrics": True,
            "ai_insights": True,
            "multi_language_support": True,
            "export_formats": ["json", "csv", "excel", "pdf"]
        },

        "tier_1_dependencies": ["LLMService"],

        "endpoints": {
            "analyze": "POST /api/v1/modules/sentiment-social/analyze",
            "search": "POST /api/v1/modules/sentiment-social/search",
            "export": "POST /api/v1/modules/sentiment-social/export",
            "stats": "GET /api/v1/modules/sentiment-social/stats",
            "status": "GET /api/v1/modules/sentiment-social/status"
        },

        "performance": {
            "avg_analysis_time_per_post": "0.5-1 second",
            "posts_analyzed_per_request": "1-1000",
            "ai_confidence_threshold": "75%"
        },

        "use_cases": [
            "Brand reputation monitoring",
            "Social media listening and tracking",
            "Competitive intelligence",
            "Influencer marketing campaign analysis",
            "Crisis management and PR monitoring",
            "Product launch sentiment tracking",
            "Customer feedback analysis",
            "Trend identification and forecasting",
            "Campaign performance measurement"
        ]
    }
