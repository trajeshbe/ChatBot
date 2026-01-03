"""
Talent Pulse Service
Tier 2 Module: HR & Talent

Service for analyzing employee sentiment, engagement, and attrition risk.
Leverages Tier 1 LLMService for sentiment analysis.
"""

import logging
import json
from typing import List, Dict, Any
from collections import Counter
from sqlalchemy.orm import Session

from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from .talent_pulse_schemas import (
    TalentPulseRequest,
    TalentPulseResponse,
    EmployeeFeedback,
    SentimentAnalysis,
    EngagementMetrics,
    AttritionRisk,
    SentimentScore,
    EngagementLevel,
    RiskLevel,
    FeedbackCategory
)

logger = logging.getLogger(__name__)


class TalentPulseService:
    """Service for employee sentiment and engagement analysis"""

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        # Tier 1 service dependencies
        self.llm_service = LLMService(db, settings)

        # Import DocumentService for extracting employee data
        from app.tier_1.document_processing.document_service import DocumentService
        self.document_service = DocumentService(db, settings)

        logger.info("✓ TalentPulseService initialized with tier_1 services")

    async def analyze_talent_pulse(self, request: TalentPulseRequest) -> TalentPulseResponse:
        """
        Analyze employee sentiment and engagement from feedback data.

        Performs:
        1. Sentiment analysis using LLM
        2. Engagement score calculation
        3. Category-based insights
        4. Department-level breakdowns
        5. Attrition risk assessment
        6. Trend identification
        """
        logger.info(f"📊 Analyzing {len(request.feedback_data)} feedback items")

        # Sentiment analysis
        overall_sentiment = None
        if request.analyze_sentiment:
            overall_sentiment = await self._analyze_sentiment(request.feedback_data)

        # Engagement metrics
        engagement_metrics = None
        if request.calculate_engagement:
            engagement_metrics = self._calculate_engagement(request.feedback_data, overall_sentiment)

        # Department breakdown
        department_breakdown = self._analyze_by_department(request.feedback_data)

        # Category insights
        category_insights = await self._analyze_by_category(request.feedback_data)

        # Attrition risk
        attrition_risks = []
        if request.assess_attrition_risk:
            attrition_risks = await self._assess_attrition_risk(request.feedback_data, overall_sentiment)

        # Generate key insights and action items
        key_insights = await self._generate_insights(overall_sentiment, engagement_metrics, category_insights)
        action_items = self._generate_action_items(overall_sentiment, engagement_metrics, attrition_risks)

        logger.info(f"✓ Analysis complete: {engagement_metrics.engagement_level if engagement_metrics else 'N/A'} engagement")

        return TalentPulseResponse(
            overall_sentiment=overall_sentiment,
            engagement_metrics=engagement_metrics,
            department_breakdown=department_breakdown,
            category_insights=category_insights,
            attrition_risks=attrition_risks,
            trends=[],
            key_insights=key_insights,
            action_items=action_items,
            total_feedback_analyzed=len(request.feedback_data)
        )

    async def _analyze_sentiment(self, feedback_data: List[EmployeeFeedback]) -> SentimentAnalysis:
        """Analyze overall sentiment using LLM"""
        # Combine feedback texts
        all_feedback = "\n".join([f.feedback_text[:200] for f in feedback_data[:50]])  # Sample first 50

        prompt = f"""Analyze the overall sentiment from this employee feedback:

{all_feedback}

Provide JSON response:
{{
  "sentiment": "very_positive/positive/neutral/negative/very_negative",
  "confidence": 0-100,
  "key_phrases": ["phrase1", "phrase2", ...],
  "topics": ["topic1", "topic2", ...],
  "emotions": {{"joy": 0-100, "anger": 0-100, "sadness": 0-100}}
}}

Return ONLY valid JSON."""

        try:
            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=300
            )

            result = json.loads(response.strip())

            sentiment_map = {
                "very_positive": SentimentScore.VERY_POSITIVE,
                "positive": SentimentScore.POSITIVE,
                "neutral": SentimentScore.NEUTRAL,
                "negative": SentimentScore.NEGATIVE,
                "very_negative": SentimentScore.VERY_NEGATIVE
            }

            return SentimentAnalysis(
                sentiment_score=sentiment_map.get(result["sentiment"], SentimentScore.NEUTRAL),
                confidence=float(result.get("confidence", 75)),
                key_phrases=result.get("key_phrases", []),
                topics=result.get("topics", []),
                emotions=result.get("emotions", {})
            )

        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}, using neutral default")
            return SentimentAnalysis(
                sentiment_score=SentimentScore.NEUTRAL,
                confidence=50.0,
                key_phrases=[],
                topics=[],
                emotions={}
            )

    def _calculate_engagement(
        self,
        feedback_data: List[EmployeeFeedback],
        sentiment: SentimentAnalysis
    ) -> EngagementMetrics:
        """Calculate engagement metrics"""
        # Simplified engagement score based on sentiment and participation
        sentiment_scores = {
            SentimentScore.VERY_POSITIVE: 90,
            SentimentScore.POSITIVE: 75,
            SentimentScore.NEUTRAL: 50,
            SentimentScore.NEGATIVE: 30,
            SentimentScore.VERY_NEGATIVE: 10
        }

        base_score = sentiment_scores.get(sentiment.sentiment_score, 50)

        # Adjust based on confidence
        engagement_score = base_score * (sentiment.confidence / 100)

        # Calculate satisfaction (similar logic)
        satisfaction_score = engagement_score * 0.9

        # Determine engagement level
        if engagement_score >= 75:
            level = EngagementLevel.HIGHLY_ENGAGED
        elif engagement_score >= 60:
            level = EngagementLevel.ENGAGED
        elif engagement_score >= 40:
            level = EngagementLevel.MODERATELY_ENGAGED
        elif engagement_score >= 25:
            level = EngagementLevel.DISENGAGED
        else:
            level = EngagementLevel.HIGHLY_DISENGAGED

        # Calculate participation rate from document metadata
        participation_rate = await self._calculate_participation_rate(feedback_data)

        return EngagementMetrics(
            engagement_level=level,
            engagement_score=round(engagement_score, 2),
            satisfaction_score=round(satisfaction_score, 2),
            eNPS=round(engagement_score - 50, 2),  # Simplified eNPS
            participation_rate=participation_rate
        )

    def _analyze_by_department(self, feedback_data: List[EmployeeFeedback]) -> Dict[str, Dict[str, Any]]:
        """Analyze feedback by department"""
        dept_groups = {}

        for feedback in feedback_data:
            dept = feedback.department or "Unknown"
            if dept not in dept_groups:
                dept_groups[dept] = []
            dept_groups[dept].append(feedback)

        breakdown = {}
        for dept, feedbacks in dept_groups.items():
            breakdown[dept] = {
                "feedback_count": len(feedbacks),
                "avg_tenure_months": sum(f.tenure_months for f in feedbacks if f.tenure_months) / len(feedbacks) if feedbacks else 0,
                "sample_feedback": feedbacks[0].feedback_text[:100] if feedbacks else ""
            }

        return breakdown

    async def _analyze_by_category(self, feedback_data: List[EmployeeFeedback]) -> Dict[str, Dict[str, Any]]:
        """Categorize feedback using LLM"""
        # Simplified: analyze a sample
        sample_texts = [f.feedback_text[:150] for f in feedback_data[:20]]

        prompt = f"""Categorize these employee feedback items into topics:
Categories: compensation, work_life_balance, career_growth, management, culture, workload, recognition, team_collaboration, tools_resources, general

Feedback:
{chr(10).join(f'- {text}' for text in sample_texts)}

Return JSON: {{"category_distribution": {{"category": count, ...}}, "top_issues": ["issue1", "issue2"]}}
Return ONLY valid JSON."""

        try:
            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=200
            )

            result = json.loads(response.strip())

            insights = {}
            for category, count in result.get("category_distribution", {}).items():
                insights[category] = {
                    "mention_count": count,
                    "percentage": round((count / len(sample_texts) * 100), 2) if sample_texts else 0
                }

            return insights

        except Exception as e:
            logger.warning(f"Category analysis failed: {e}")
            return {
                "general": {"mention_count": len(feedback_data), "percentage": 100.0}
            }

    async def _assess_attrition_risk(
        self,
        feedback_data: List[EmployeeFeedback],
        sentiment: SentimentAnalysis
    ) -> List[AttritionRisk]:
        """Assess attrition risk for employees"""
        risks = []

        # Identify employees with negative sentiment
        for feedback in feedback_data:
            if feedback.employee_id:
                # Simplified risk assessment
                if sentiment.sentiment_score in [SentimentScore.NEGATIVE, SentimentScore.VERY_NEGATIVE]:
                    risk_score = 75.0 if sentiment.sentiment_score == SentimentScore.VERY_NEGATIVE else 60.0

                    risk_level = RiskLevel.HIGH if risk_score >= 70 else RiskLevel.MEDIUM

                    risks.append(AttritionRisk(
                        employee_id=feedback.employee_id,
                        risk_level=risk_level,
                        risk_score=risk_score,
                        risk_factors=["Negative sentiment", "Low engagement indicators"],
                        recommended_actions=["Schedule 1-on-1 meeting", "Review compensation", "Career development discussion"],
                        predicted_departure_window_months=6 if risk_score >= 70 else 12
                    ))

        # Limit to top 10 highest risk
        risks.sort(key=lambda r: r.risk_score, reverse=True)
        return risks[:10]

    async def _generate_insights(
        self,
        sentiment: SentimentAnalysis,
        engagement: EngagementMetrics,
        categories: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Generate key insights using LLM"""
        prompt = f"""Generate 3-5 key insights from this employee analysis:

Sentiment: {sentiment.sentiment_score.value} ({sentiment.confidence}% confidence)
Engagement: {engagement.engagement_level.value} ({engagement.engagement_score}/100)
Top Topics: {', '.join(sentiment.topics[:3])}
Category Distribution: {', '.join(categories.keys())}

Provide actionable insights for HR leadership.
Return as JSON array: ["insight1", "insight2", ...]
Return ONLY valid JSON."""

        try:
            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.5,
                max_tokens=200
            )

            insights = json.loads(response.strip())
            return insights if isinstance(insights, list) else []

        except Exception as e:
            logger.warning(f"Insight generation failed: {e}")
            return [
                f"Overall engagement level is {engagement.engagement_level.value}",
                f"Sentiment analysis shows {sentiment.sentiment_score.value} mood",
                "Further investigation recommended in key areas"
            ]

    def _generate_action_items(
        self,
        sentiment: SentimentAnalysis,
        engagement: EngagementMetrics,
        attrition_risks: List[AttritionRisk]
    ) -> List[str]:
        """Generate recommended action items"""
        actions = []

        if engagement.engagement_score < 50:
            actions.append("Launch employee engagement initiative")
            actions.append("Conduct focus groups to understand concerns")

        if sentiment.sentiment_score in [SentimentScore.NEGATIVE, SentimentScore.VERY_NEGATIVE]:
            actions.append("Address negative sentiment drivers immediately")

        if attrition_risks:
            actions.append(f"Prioritize retention efforts for {len(attrition_risks)} high-risk employees")

        if not actions:
            actions.append("Continue monitoring employee sentiment")
            actions.append("Maintain current engagement programs")

        return actions

    async def _calculate_participation_rate(self, feedback_data: List[EmployeeFeedback]) -> float:
        """Calculate participation rate from employee database or HR reports"""
        try:
            # Extract total employee count from uploaded HR documents
            documents = await self.document_service.list_documents()

            total_employees = None
            for doc in documents[:10]:
                try:
                    chunks = await self.document_service.get_chunks_for_document(doc.id)
                    document_text = " ".join([chunk.get('content', '') for chunk in chunks[:3]])

                    # Extract employee count using LLM
                    employee_count = await self._extract_employee_count(document_text)
                    if employee_count:
                        total_employees = employee_count
                        break
                except Exception as e:
                    continue

            if total_employees and total_employees > 0:
                rate = (len(feedback_data) / total_employees) * 100
                return min(100.0, rate)

            # Fallback: return calculated rate based on feedback volume
            return min(100.0, len(feedback_data) * 0.5)  # Assume feedback represents 50% sample

        except Exception as e:
            logger.warning(f"Participation rate calculation failed: {e}")
            return 50.0  # Default fallback

    async def _extract_employee_count(self, text: str) -> Optional[int]:
        """Extract total employee count from HR document"""
        prompt = f"""Extract the total number of employees from this HR document:

{text[:2000]}

Return JSON: {{"total_employees": number}}
If not found, return {{"total_employees": null}}
Return ONLY valid JSON."""

        try:
            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.0,
                max_tokens=50
            )

            result = json.loads(response.strip())
            return result.get("total_employees")

        except Exception as e:
            return None
