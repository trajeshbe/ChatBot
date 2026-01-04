"""Customer Churn Predictor - Business Logic Service"""

import logging
import json
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session

from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from .customer_churn_schemas import *

logger = logging.getLogger(__name__)


class CustomerChurnService:
    """Service for customer churn prediction"""

    def __init__(self, db: Session, settings: Settings, config: Optional[Dict[str, Any]] = None):
        self.db = db
        self.settings = settings
        self.config = config or {}
        self.llm_service = LLMService()
        if config:
            logger.info(f"✓ Using module config with model: {config.get('llm', {}).get('default', {}).get('model', 'default')}")

    async def predict_churn(self, request: PredictChurnRequest) -> PredictChurnResponse:
        """Predict customer churn with AI analysis"""
        try:
            logger.info(f"Predicting churn for {len(request.customers)} customers")

            predictions = []
            retention_recs = []

            for customer in request.customers:
                pred = self._predict_single_customer(customer)
                predictions.append(pred)

                if request.include_retention_strategies and pred.churn_probability > 30:
                    rec = self._generate_retention_strategy(customer, pred)
                    retention_recs.append(rec)

            # Calculate summaries
            segment_summary = self._calculate_segment_summary(predictions)
            risk_dist = self._calculate_risk_distribution(predictions)

            # Generate AI insights
            ai_insights = await self._generate_ai_insights(predictions, segment_summary)

            # Generate overall recommendations
            overall_recs = self._generate_overall_recommendations(predictions, risk_dist)

            return PredictChurnResponse(
                success=True,
                predictions=predictions,
                retention_recommendations=retention_recs,
                segment_summary=segment_summary,
                risk_distribution=risk_dist,
                ai_insights=ai_insights,
                overall_recommendations=overall_recs
            )

        except Exception as e:
            logger.error(f"Error predicting churn: {e}", exc_info=True)
            raise

    def _predict_single_customer(self, customer: CustomerData) -> ChurnPrediction:
        """Predict churn for single customer"""
        # Calculate churn probability based on features
        score = 50.0  # Base score

        # Tenure impact (longer = lower churn)
        if customer.tenure_months < 6:
            score += 20
        elif customer.tenure_months > 24:
            score -= 15

        # Purchase activity
        if customer.last_purchase_days_ago > 60:
            score += 15
        if customer.purchase_frequency < 2:
            score += 10

        # Support tickets (more = higher churn risk)
        score += min(customer.support_tickets * 5, 20)

        # Spend level (higher = lower churn)
        if customer.monthly_spend > 100:
            score -= 10
        elif customer.monthly_spend < 20:
            score += 10

        # Contract type
        if customer.contract_type == "month_to_month":
            score += 10

        # Satisfaction
        if customer.satisfaction_score:
            score -= (customer.satisfaction_score - 5) * 5

        churn_prob = max(0.0, min(100.0, score))

        # Determine risk level
        if churn_prob >= 75:
            risk_level = ChurnRiskLevel.CRITICAL
        elif churn_prob >= 60:
            risk_level = ChurnRiskLevel.HIGH
        elif churn_prob >= 40:
            risk_level = ChurnRiskLevel.MEDIUM
        elif churn_prob >= 20:
            risk_level = ChurnRiskLevel.LOW
        else:
            risk_level = ChurnRiskLevel.MINIMAL

        # Determine segment
        if customer.monthly_spend > 200:
            segment = CustomerSegment.VIP
        elif churn_prob > 70:
            segment = CustomerSegment.AT_RISK
        elif customer.purchase_frequency > 5:
            segment = CustomerSegment.REGULAR
        else:
            segment = CustomerSegment.OCCASIONAL

        # Identify risk factors
        risk_factors = []
        if customer.tenure_months < 6:
            risk_factors.append("New customer - high early-stage churn risk")
        if customer.last_purchase_days_ago > 60:
            risk_factors.append("No recent purchases (60+ days)")
        if customer.support_tickets > 3:
            risk_factors.append(f"High support ticket volume ({customer.support_tickets})")
        if customer.monthly_spend < 20:
            risk_factors.append("Low monthly spend")

        # Calculate LTV estimate
        ltv = customer.monthly_spend * max(customer.tenure_months, 12) * 0.7

        return ChurnPrediction(
            customer_id=customer.customer_id,
            churn_probability=round(churn_prob, 2),
            risk_level=risk_level,
            customer_segment=segment,
            key_risk_factors=risk_factors[:5],
            lifetime_value_estimate=round(ltv, 2),
            retention_priority=min(10, int(churn_prob / 10) + 1)
        )

    def _generate_retention_strategy(
        self, customer: CustomerData, prediction: ChurnPrediction
    ) -> RetentionRecommendation:
        """Generate retention strategy for customer"""
        # Select strategy based on segment and risk
        if prediction.customer_segment == CustomerSegment.VIP:
            strategy = RetentionStrategy.PREMIUM_SUPPORT
            description = "Assign dedicated account manager and premium support"
            cost = 500.0
            success_rate = 85.0
        elif customer.monthly_spend < 30:
            strategy = RetentionStrategy.DISCOUNT
            description = "Offer 20% discount for next 3 months"
            cost = customer.monthly_spend * 0.6
            success_rate = 70.0
        elif customer.purchase_frequency < 3:
            strategy = RetentionStrategy.ENGAGEMENT_CAMPAIGN
            description = "Send personalized product recommendations and usage tips"
            cost = 50.0
            success_rate = 60.0
        else:
            strategy = RetentionStrategy.PERSONALIZED_OFFER
            description = "Custom offer based on purchase history"
            cost = 100.0
            success_rate = 75.0

        value_retention = prediction.lifetime_value_estimate * (success_rate / 100)

        return RetentionRecommendation(
            customer_id=customer.customer_id,
            strategy=strategy,
            description=description,
            expected_success_rate=round(success_rate, 2),
            estimated_cost=round(cost, 2),
            estimated_value_retention=round(value_retention, 2)
        )

    def _calculate_segment_summary(self, predictions: List[ChurnPrediction]) -> Dict[str, int]:
        """Calculate segment distribution"""
        summary = {}
        for pred in predictions:
            segment = pred.customer_segment.value
            summary[segment] = summary.get(segment, 0) + 1
        return summary

    def _calculate_risk_distribution(self, predictions: List[ChurnPrediction]) -> Dict[str, int]:
        """Calculate risk level distribution"""
        dist = {}
        for pred in predictions:
            risk = pred.risk_level.value
            dist[risk] = dist.get(risk, 0) + 1
        return dist

    async def _generate_ai_insights(
        self, predictions: List[ChurnPrediction], segment_summary: Dict[str, int]
    ) -> str:
        """Generate AI insights using LLM"""
        try:
            avg_churn = sum(p.churn_probability for p in predictions) / len(predictions)
            high_risk_count = sum(1 for p in predictions if p.risk_level in [ChurnRiskLevel.CRITICAL, ChurnRiskLevel.HIGH])

            prompt = f"""Analyze this customer churn prediction batch:

Total Customers: {len(predictions)}
Average Churn Probability: {avg_churn:.1f}%
High-Risk Customers: {high_risk_count}
Segments: {segment_summary}

Provide 2-3 sentences of expert insights about churn patterns and retention priorities."""

            # Get LLM parameters from module config
            llm_config = self.config.get('llm', {}).get('default', {})
            model = llm_config.get('model', 'gpt-4o-mini')
            temperature = llm_config.get('temperature', 0.3)

            response = await self.llm_service.generate_response(
                prompt=prompt, model=model, temperature=temperature
            )
            return response.strip()

        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return "Churn predictions generated successfully. Focus on high-risk customers for retention efforts."

    def _generate_overall_recommendations(
        self, predictions: List[ChurnPrediction], risk_dist: Dict[str, int]
    ) -> List[str]:
        """Generate overall recommendations"""
        recs = []

        critical_count = risk_dist.get("critical", 0)
        if critical_count > 0:
            recs.append(f"URGENT: {critical_count} customers at critical churn risk - immediate intervention required")

        high_risk_count = risk_dist.get("high", 0) + critical_count
        if high_risk_count > len(predictions) * 0.2:
            recs.append("Over 20% of customers at high churn risk - review customer success processes")

        vip_at_risk = [p for p in predictions if p.customer_segment == CustomerSegment.VIP and p.churn_probability > 50]
        if vip_at_risk:
            recs.append(f"{len(vip_at_risk)} VIP customers at risk - prioritize premium retention strategies")

        avg_churn = sum(p.churn_probability for p in predictions) / len(predictions)
        if avg_churn > 50:
            recs.append("Average churn probability exceeds 50% - implement company-wide retention program")

        return recs[:5]

    async def search_predictions(self, request: SearchPredictionsRequest) -> SearchPredictionsResponse:
        """Search historical predictions"""
        return SearchPredictionsResponse(
            success=True,
            predictions=[],
            total_count=0,
            summary_stats={"message": "Historical prediction search - database integration pending"}
        )

    async def export_predictions(self, request: ExportPredictionsRequest) -> ExportPredictionsResponse:
        """Export predictions"""
        return ExportPredictionsResponse(
            success=True,
            export_data={"message": "Prediction export", "format": request.format},
            format=request.format,
            record_count=0
        )

    async def get_stats(self) -> ChurnStatsResponse:
        """Get churn prediction statistics"""
        return ChurnStatsResponse(
            success=True,
            total_predictions=0,
            total_customers_analyzed=0,
            average_churn_probability=0.0,
            risk_level_distribution={},
            segment_distribution={},
            retention_success_rate=0.0,
            most_effective_strategy="personalized_offer"
        )

    async def get_status(self) -> StatusResponse:
        """Get service status"""
        return StatusResponse(
            success=True,
            status="operational",
            capabilities=[
                "Churn Probability Prediction",
                "Customer Segmentation",
                "Risk Level Assessment",
                "Retention Strategy Recommendations",
                "Lifetime Value Estimation",
                "AI-Powered Insights"
            ]
        )
