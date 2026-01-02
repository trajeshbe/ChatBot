"""
Sentiment Social Service
Tier 2 Module: Marketing

Service for social media sentiment analysis and brand monitoring.
Leverages Tier 1 LLMService for AI-powered sentiment and emotion analysis.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from collections import Counter

from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from .sentiment_social_schemas import (
    SentimentSocialRequest,
    SentimentSocialResponse,
    SocialPost,
    SentimentAnalysis,
    InfluencerAnalysis,
    TrendingTopic,
    BrandMentionAnalysis,
    SentimentScore,
    EmotionType,
    InfluencerTier,
    SocialPlatform
)

logger = logging.getLogger(__name__)


class SentimentSocialService:
    """Service for social media sentiment analysis"""

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        # Tier 1 service dependencies
        self.llm_service = LLMService(db, settings)

        logger.info("✓ SentimentSocialService initialized with tier_1 services")

    async def analyze_social_sentiment(self, request: SentimentSocialRequest) -> SentimentSocialResponse:
        """Analyze social media posts for sentiment, trends, and brand perception"""
        logger.info(f"📱 Analyzing {len(request.posts)} social media posts")

        # Filter by language if specified
        posts_to_analyze = request.posts
        if request.language_filter:
            # In production, would detect language first
            pass

        # Analyze sentiment for each post
        sentiment_analyses = await self._analyze_posts_sentiment(
            posts_to_analyze,
            include_emotions=request.include_emotion_analysis
        )

        # Calculate overall sentiment
        overall_sentiment, sentiment_distribution = self._calculate_overall_sentiment(sentiment_analyses)
        average_polarity = sum(sa.polarity_score for sa in sentiment_analyses) / len(sentiment_analyses) if sentiment_analyses else 0.0

        # Analyze influencers
        influencer_analyses = []
        if request.include_influencer_analysis:
            influencer_analyses = self._analyze_influencers(request.posts, sentiment_analyses)

        # Identify trending topics
        trending_topics = []
        if request.include_trending_topics:
            trending_topics = self._identify_trending_topics(request.posts, sentiment_analyses)

        # Brand mention analysis
        brand_mentions = []
        if request.brand_names:
            brand_mentions = self._analyze_brand_mentions(request.brand_names, request.posts, sentiment_analyses)

        # Calculate total engagement
        total_engagement = sum(
            (post.likes_count or 0) + (post.shares_count or 0) + (post.comments_count or 0)
            for post in request.posts
        )

        # Generate AI insights
        ai_insights = await self._generate_ai_insights(
            overall_sentiment,
            trending_topics,
            brand_mentions,
            len(request.posts)
        )

        logger.info(f"✓ Analyzed {len(sentiment_analyses)} posts: {overall_sentiment.value} sentiment")

        return SentimentSocialResponse(
            sentiment_analyses=sentiment_analyses,
            overall_sentiment=overall_sentiment,
            sentiment_distribution=sentiment_distribution,
            average_polarity=round(average_polarity, 3),
            influencer_analyses=influencer_analyses,
            trending_topics=trending_topics,
            brand_mentions=brand_mentions,
            total_posts_analyzed=len(sentiment_analyses),
            total_engagement=total_engagement,
            ai_insights=ai_insights
        )

    async def _analyze_posts_sentiment(
        self,
        posts: List[SocialPost],
        include_emotions: bool = True
    ) -> List[SentimentAnalysis]:
        """Analyze sentiment for individual posts"""
        analyses = []

        for post in posts:
            analysis = await self._analyze_single_post(post, include_emotions)
            if analysis:
                analyses.append(analysis)

        return analyses

    async def _analyze_single_post(
        self,
        post: SocialPost,
        include_emotions: bool
    ) -> Optional[SentimentAnalysis]:
        """Analyze sentiment for a single post using LLM"""

        prompt = f"""Analyze the sentiment of this social media post:

Platform: {post.platform.value}
Content: "{post.content}"

Provide JSON response:
{{
  "sentiment": "very_positive/positive/neutral/negative/very_negative",
  "confidence": 0-100,
  "polarity": -1.0 to 1.0,
  "subjectivity": 0.0 to 1.0,
  "primary_emotion": "joy/trust/fear/surprise/sadness/disgust/anger/anticipation",
  "emotion_scores": {{"joy": 0-100, "anger": 0-100, ...}},
  "key_phrases": ["phrase1", "phrase2"],
  "topics": ["topic1", "topic2"],
  "language": "en"
}}

Return ONLY valid JSON."""

        try:
            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.1,
                max_tokens=400
            )

            result = json.loads(response.strip())

            # Build emotion scores
            emotion_scores = {}
            if include_emotions and "emotion_scores" in result:
                emotion_scores = {k: float(v) for k, v in result["emotion_scores"].items()}

            return SentimentAnalysis(
                post_id=post.post_id,
                sentiment_score=SentimentScore(result.get("sentiment", "neutral")),
                confidence=float(result.get("confidence", 75)),
                polarity_score=float(result.get("polarity", 0.0)),
                subjectivity_score=float(result.get("subjectivity", 0.5)),
                primary_emotion=EmotionType(result["primary_emotion"]) if "primary_emotion" in result else None,
                emotion_scores=emotion_scores,
                key_phrases=result.get("key_phrases", []),
                topics=result.get("topics", []),
                language=result.get("language", "en")
            )

        except Exception as e:
            logger.warning(f"Sentiment analysis failed for post {post.post_id}: {e}")
            # Return neutral fallback
            return SentimentAnalysis(
                post_id=post.post_id,
                sentiment_score=SentimentScore.NEUTRAL,
                confidence=50.0,
                polarity_score=0.0,
                subjectivity_score=0.5
            )

    def _calculate_overall_sentiment(
        self,
        analyses: List[SentimentAnalysis]
    ) -> tuple[SentimentScore, Dict[str, int]]:
        """Calculate overall sentiment and distribution"""
        if not analyses:
            return SentimentScore.NEUTRAL, {}

        # Count sentiment distribution
        sentiment_counts = Counter(a.sentiment_score.value for a in analyses)
        distribution = dict(sentiment_counts)

        # Determine overall sentiment (most common)
        most_common_sentiment = sentiment_counts.most_common(1)[0][0]

        return SentimentScore(most_common_sentiment), distribution

    def _analyze_influencers(
        self,
        posts: List[SocialPost],
        sentiment_analyses: List[SentimentAnalysis]
    ) -> List[InfluencerAnalysis]:
        """Analyze influencer impact"""
        # Group posts by author
        influencer_data: Dict[str, List[tuple[SocialPost, SentimentAnalysis]]] = {}

        sentiment_map = {sa.post_id: sa for sa in sentiment_analyses}

        for post in posts:
            if post.author and post.author_followers is not None:
                if post.author not in influencer_data:
                    influencer_data[post.author] = []

                if post.post_id in sentiment_map:
                    influencer_data[post.author].append((post, sentiment_map[post.post_id]))

        influencer_analyses = []

        for author, post_sentiment_pairs in influencer_data.items():
            if not post_sentiment_pairs:
                continue

            follower_count = post_sentiment_pairs[0][0].author_followers or 0

            # Determine influencer tier
            if follower_count < 10000:
                tier = InfluencerTier.NANO
            elif follower_count < 100000:
                tier = InfluencerTier.MICRO
            elif follower_count < 500000:
                tier = InfluencerTier.MID_TIER
            elif follower_count < 1000000:
                tier = InfluencerTier.MACRO
            else:
                tier = InfluencerTier.MEGA

            # Calculate average sentiment
            sentiments = [sa.sentiment_score for _, sa in post_sentiment_pairs]
            sentiment_counts = Counter(s.value for s in sentiments)
            avg_sentiment = SentimentScore(sentiment_counts.most_common(1)[0][0])

            # Calculate total engagement
            total_engagement = sum(
                (post.likes_count or 0) + (post.shares_count or 0) + (post.comments_count or 0)
                for post, _ in post_sentiment_pairs
            )

            # Engagement rate
            engagement_rate = (total_engagement / follower_count * 100) if follower_count > 0 else 0.0

            # Reach estimate (followers + shares)
            total_shares = sum(post.shares_count or 0 for post, _ in post_sentiment_pairs)
            reach_estimate = follower_count + (total_shares * 10)  # Assume 10x multiplier for shares

            influencer_analyses.append(InfluencerAnalysis(
                author=author,
                follower_count=follower_count,
                influencer_tier=tier,
                posts_analyzed=len(post_sentiment_pairs),
                average_sentiment=avg_sentiment,
                total_engagement=total_engagement,
                engagement_rate=round(engagement_rate, 2),
                reach_estimate=reach_estimate
            ))

        # Sort by reach estimate (descending)
        influencer_analyses.sort(key=lambda x: x.reach_estimate, reverse=True)

        return influencer_analyses[:10]  # Top 10

    def _identify_trending_topics(
        self,
        posts: List[SocialPost],
        sentiment_analyses: List[SentimentAnalysis]
    ) -> List[TrendingTopic]:
        """Identify trending topics from posts"""
        sentiment_map = {sa.post_id: sa for sa in sentiment_analyses}

        # Collect all topics
        topic_data: Dict[str, Dict[str, Any]] = {}

        for post in posts:
            if post.post_id not in sentiment_map:
                continue

            sentiment = sentiment_map[post.post_id]

            # Use topics from sentiment analysis
            for topic in sentiment.topics:
                if topic not in topic_data:
                    topic_data[topic] = {
                        "mention_count": 0,
                        "sentiment_counts": Counter(),
                        "hashtags": set(),
                        "influencers": set(),
                        "total_engagement": 0
                    }

                topic_data[topic]["mention_count"] += 1
                topic_data[topic]["sentiment_counts"][sentiment.sentiment_score.value] += 1
                topic_data[topic]["hashtags"].update(post.hashtags)

                if post.author:
                    topic_data[topic]["influencers"].add(post.author)

                topic_data[topic]["total_engagement"] += (
                    (post.likes_count or 0) + (post.shares_count or 0) + (post.comments_count or 0)
                )

        # Build trending topics
        trending_topics = []

        for topic, data in topic_data.items():
            # Dominant sentiment
            dominant_sentiment = SentimentScore(data["sentiment_counts"].most_common(1)[0][0])

            # Engagement score (weighted by mentions and engagement)
            engagement_score = (data["mention_count"] * 10) + (data["total_engagement"] / 100)

            trending_topics.append(TrendingTopic(
                topic=topic,
                mention_count=data["mention_count"],
                sentiment_distribution=dict(data["sentiment_counts"]),
                dominant_sentiment=dominant_sentiment,
                hashtags=list(data["hashtags"])[:5],
                influencers_discussing=list(data["influencers"])[:5],
                engagement_score=round(engagement_score, 2)
            ))

        # Sort by engagement score
        trending_topics.sort(key=lambda x: x.engagement_score, reverse=True)

        return trending_topics[:10]  # Top 10

    def _analyze_brand_mentions(
        self,
        brand_names: List[str],
        posts: List[SocialPost],
        sentiment_analyses: List[SentimentAnalysis]
    ) -> List[BrandMentionAnalysis]:
        """Analyze brand mentions and perception"""
        sentiment_map = {sa.post_id: sa for sa in sentiment_analyses}

        brand_data: Dict[str, Dict[str, Any]] = {
            brand: {
                "mention_count": 0,
                "sentiment_counts": Counter(),
                "keywords": Counter(),
                "total_posts": len(posts)
            }
            for brand in brand_names
        }

        for post in posts:
            if post.post_id not in sentiment_map:
                continue

            sentiment = sentiment_map[post.post_id]
            content_lower = post.content.lower()

            for brand in brand_names:
                if brand.lower() in content_lower:
                    brand_data[brand]["mention_count"] += 1
                    brand_data[brand]["sentiment_counts"][sentiment.sentiment_score.value] += 1

                    # Collect keywords from key phrases
                    for phrase in sentiment.key_phrases:
                        brand_data[brand]["keywords"][phrase] += 1

        brand_mentions = []

        for brand, data in brand_data.items():
            if data["mention_count"] == 0:
                continue

            # Calculate net sentiment score
            positive_count = (
                data["sentiment_counts"].get("very_positive", 0) +
                data["sentiment_counts"].get("positive", 0)
            )
            negative_count = (
                data["sentiment_counts"].get("very_negative", 0) +
                data["sentiment_counts"].get("negative", 0)
            )

            positive_pct = (positive_count / data["mention_count"] * 100) if data["mention_count"] > 0 else 0
            negative_pct = (negative_count / data["mention_count"] * 100) if data["mention_count"] > 0 else 0

            net_sentiment_score = positive_pct - negative_pct

            # Share of voice
            share_of_voice = (data["mention_count"] / data["total_posts"] * 100) if data["total_posts"] > 0 else 0

            # Top keywords
            top_keywords = [kw for kw, _ in data["keywords"].most_common(5)]

            brand_mentions.append(BrandMentionAnalysis(
                brand_name=brand,
                total_mentions=data["mention_count"],
                sentiment_breakdown=dict(data["sentiment_counts"]),
                net_sentiment_score=round(net_sentiment_score, 2),
                share_of_voice=round(share_of_voice, 2),
                top_associated_keywords=top_keywords
            ))

        return brand_mentions

    async def _generate_ai_insights(
        self,
        overall_sentiment: SentimentScore,
        trending_topics: List[TrendingTopic],
        brand_mentions: List[BrandMentionAnalysis],
        total_posts: int
    ) -> List[str]:
        """Generate AI-powered insights from social media analysis"""

        topics_summary = ", ".join([t.topic for t in trending_topics[:3]]) if trending_topics else "None"
        brands_summary = ", ".join([b.brand_name for b in brand_mentions]) if brand_mentions else "None"

        prompt = f"""Provide 3-5 key insights from this social media analysis:

Overall Sentiment: {overall_sentiment.value}
Total Posts: {total_posts}
Top Trending Topics: {topics_summary}
Brands Monitored: {brands_summary}

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
