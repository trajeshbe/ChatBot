"""
Campaign Optimizer Service
Tier 2 Module: Marketing

Service for marketing campaign optimization and performance analysis.
Leverages Tier 1 LLMService for AI-powered optimization recommendations.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from .campaign_optimizer_schemas import (
    CampaignOptimizationRequest,
    CampaignOptimizationResponse,
    CampaignPerformance,
    BudgetAllocation,
    ChannelPerformanceAnalysis,
    MarketingChannel,
    OptimizationGoal
)

logger = logging.getLogger(__name__)


class CampaignOptimizerService:
    """Service for marketing campaign optimization"""

    def __init__(self, db: Session, settings: Settings, config: Optional[Dict[str, Any]] = None):
        self.db = db
        self.settings = settings
        self.config = config or {}
        # Tier 1 service dependencies
        self.llm_service = LLMService()

        logger.info("✓ CampaignOptimizerService initialized with tier_1 services")
        if config:
            logger.info(f"✓ Using module config with model: {config.get('llm', {}).get('default', {}).get('model', 'default')}")

    async def optimize_campaigns(self, request: CampaignOptimizationRequest) -> CampaignOptimizationResponse:
        """Analyze campaigns and provide optimization recommendations"""
        logger.info(f"📊 Optimizing {len(request.campaigns)} campaigns for {request.optimization_goal.value}")

        # Calculate current performance
        current_roi = self._calculate_overall_roi(request.campaigns)
        performance_score = self._calculate_performance_score(request.campaigns, request.optimization_goal)

        # Analyze channels
        channel_analyses = []
        if request.include_channel_analysis:
            channel_analyses = self._analyze_channels(request.campaigns)

        # Recommend budget allocation
        budget_allocations = []
        if request.include_budget_reallocation:
            budget_allocations = await self._recommend_budget_allocation(
                request.campaigns,
                request.total_budget,
                request.optimization_goal,
                channel_analyses
            )

        # Identify top/underperforming campaigns
        top_performing, underperforming = self._classify_campaigns(request.campaigns)

        # Generate optimization recommendations
        recommendations = await self._generate_optimization_recommendations(
            request.campaigns,
            request.optimization_goal,
            channel_analyses,
            budget_allocations
        )

        # AI insights
        ai_insights = await self._generate_ai_insights(
            request.campaigns,
            request.optimization_goal,
            current_roi,
            budget_allocations
        )

        # Calculate projected improvement
        projected_roi = self._calculate_projected_roi(current_roi, budget_allocations, channel_analyses)
        expected_improvement = ((projected_roi - current_roi) / current_roi * 100) if current_roi > 0 else 0.0

        logger.info(f"✓ Optimization complete: {expected_improvement:.1f}% improvement projected")

        return CampaignOptimizationResponse(
            overall_performance_score=round(performance_score, 2),
            current_total_roi=round(current_roi, 2),
            projected_roi_after_optimization=round(projected_roi, 2),
            budget_allocations=budget_allocations,
            channel_analyses=channel_analyses,
            top_performing_campaigns=top_performing[:5],
            underperforming_campaigns=underperforming[:5],
            ab_test_results=[],
            optimization_recommendations=recommendations,
            ai_insights=ai_insights,
            expected_improvement_percent=round(expected_improvement, 2)
        )

    def _calculate_overall_roi(self, campaigns: List[CampaignPerformance]) -> float:
        """Calculate overall ROI across all campaigns"""
        total_spend = sum(c.budget_spent for c in campaigns)
        total_revenue = sum(c.revenue_generated for c in campaigns)

        if total_spend == 0:
            return 0.0

        return ((total_revenue - total_spend) / total_spend) * 100

    def _calculate_performance_score(
        self,
        campaigns: List[CampaignPerformance],
        goal: OptimizationGoal
    ) -> float:
        """Calculate overall performance score based on optimization goal"""
        if not campaigns:
            return 0.0

        scores = []

        for campaign in campaigns:
            if goal == OptimizationGoal.MAXIMIZE_ROI:
                roi = campaign.roi or 0.0
                score = min(100, max(0, roi + 50))  # Normalize -50 to 50 ROI to 0-100 score
            elif goal == OptimizationGoal.MINIMIZE_CPA:
                cpa = campaign.cost_per_conversion or float('inf')
                score = 100 - min(100, cpa)  # Lower CPA = higher score
            elif goal == OptimizationGoal.MAXIMIZE_CONVERSIONS:
                score = min(100, campaign.conversions / 10)  # Normalize
            elif goal == OptimizationGoal.MAXIMIZE_REACH:
                score = min(100, campaign.impressions / 1000)
            else:
                # Balance all metrics
                roi_score = min(100, max(0, (campaign.roi or 0) + 50))
                conv_rate = campaign.conversion_rate or 0
                score = (roi_score + conv_rate) / 2

            scores.append(score)

        return sum(scores) / len(scores)

    def _analyze_channels(self, campaigns: List[CampaignPerformance]) -> List[ChannelPerformanceAnalysis]:
        """Analyze performance by marketing channel"""
        channel_data: Dict[MarketingChannel, Dict[str, Any]] = {}

        for campaign in campaigns:
            if campaign.channel not in channel_data:
                channel_data[campaign.channel] = {
                    "total_spend": 0.0,
                    "total_revenue": 0.0,
                    "total_conversions": 0,
                    "campaigns_count": 0
                }

            channel_data[campaign.channel]["total_spend"] += campaign.budget_spent
            channel_data[campaign.channel]["total_revenue"] += campaign.revenue_generated
            channel_data[campaign.channel]["total_conversions"] += campaign.conversions
            channel_data[campaign.channel]["campaigns_count"] += 1

        analyses = []

        for channel, data in channel_data.items():
            total_spend = data["total_spend"]
            total_revenue = data["total_revenue"]
            total_conversions = data["total_conversions"]

            # Average CPA
            avg_cpa = total_spend / total_conversions if total_conversions > 0 else 0.0

            # Average ROI
            avg_roi = ((total_revenue - total_spend) / total_spend * 100) if total_spend > 0 else 0.0

            # Channel efficiency score (0-100)
            efficiency = min(100, max(0, avg_roi + 50))

            # Recommended action
            if efficiency >= 75:
                action = "Increase budget allocation - high performing channel"
            elif efficiency >= 50:
                action = "Maintain current strategy - performing well"
            elif efficiency >= 25:
                action = "Optimize campaigns - moderate performance"
            else:
                action = "Consider reducing budget or major optimization needed"

            analyses.append(ChannelPerformanceAnalysis(
                channel=channel,
                total_spend=total_spend,
                total_conversions=total_conversions,
                average_cpa=round(avg_cpa, 2),
                average_roi=round(avg_roi, 2),
                channel_efficiency_score=round(efficiency, 2),
                recommended_action=action
            ))

        # Sort by efficiency score (descending)
        analyses.sort(key=lambda x: x.channel_efficiency_score, reverse=True)

        return analyses

    async def _recommend_budget_allocation(
        self,
        campaigns: List[CampaignPerformance],
        total_budget: float,
        goal: OptimizationGoal,
        channel_analyses: List[ChannelPerformanceAnalysis]
    ) -> List[BudgetAllocation]:
        """Recommend budget reallocation across channels"""

        # Group by channel
        channel_spend = {}
        for campaign in campaigns:
            channel_spend[campaign.channel] = channel_spend.get(campaign.channel, 0.0) + campaign.budget_spent

        total_spend = sum(channel_spend.values())

        allocations = []

        # Use channel efficiency scores to recommend allocation
        channel_score_map = {ca.channel: ca.channel_efficiency_score for ca in channel_analyses}

        total_score = sum(channel_score_map.values())

        for channel, current_spend in channel_spend.items():
            current_allocation = (current_spend / total_spend * 100) if total_spend > 0 else 0.0

            # Recommend allocation based on efficiency score
            if total_score > 0:
                recommended_allocation = (channel_score_map.get(channel, 0) / total_score * 100)
            else:
                recommended_allocation = current_allocation

            # Calculate expected ROI improvement
            current_roi = next((ca.average_roi for ca in channel_analyses if ca.channel == channel), 0.0)
            expected_improvement = (recommended_allocation - current_allocation)

            reasoning = f"Channel efficiency score: {channel_score_map.get(channel, 0):.1f}/100. "
            if recommended_allocation > current_allocation:
                reasoning += "Increase budget due to strong performance."
            elif recommended_allocation < current_allocation:
                reasoning += "Decrease budget due to underperformance."
            else:
                reasoning += "Maintain current allocation."

            allocations.append(BudgetAllocation(
                channel=channel,
                current_allocation=round(current_allocation, 2),
                recommended_allocation=round(recommended_allocation, 2),
                expected_roi_improvement=round(expected_improvement, 2),
                reasoning=reasoning
            ))

        return allocations

    def _classify_campaigns(
        self,
        campaigns: List[CampaignPerformance]
    ) -> tuple[List[CampaignPerformance], List[CampaignPerformance]]:
        """Classify campaigns as top performing or underperforming"""

        # Calculate campaign scores based on ROI
        campaign_scores = [(c, c.roi or 0.0) for c in campaigns]
        campaign_scores.sort(key=lambda x: x[1], reverse=True)

        # Top 30% are top performing, bottom 30% are underperforming
        top_count = max(1, int(len(campaigns) * 0.3))
        bottom_count = max(1, int(len(campaigns) * 0.3))

        top_performing = [c for c, _ in campaign_scores[:top_count]]
        underperforming = [c for c, _ in campaign_scores[-bottom_count:]]

        return top_performing, underperforming

    async def _generate_optimization_recommendations(
        self,
        campaigns: List[CampaignPerformance],
        goal: OptimizationGoal,
        channel_analyses: List[ChannelPerformanceAnalysis],
        budget_allocations: List[BudgetAllocation]
    ) -> List[str]:
        """Generate specific optimization recommendations"""

        recommendations = []

        # Channel-based recommendations
        if channel_analyses:
            top_channel = channel_analyses[0]
            recommendations.append(
                f"Focus on {top_channel.channel.value} - highest efficiency score ({top_channel.channel_efficiency_score:.1f}/100)"
            )

            if len(channel_analyses) > 1:
                weak_channel = channel_analyses[-1]
                if weak_channel.channel_efficiency_score < 40:
                    recommendations.append(
                        f"Consider pausing or heavily optimizing {weak_channel.channel.value} campaigns - low efficiency ({weak_channel.channel_efficiency_score:.1f}/100)"
                    )

        # Budget reallocation recommendations
        significant_changes = [ba for ba in budget_allocations if abs(ba.recommended_allocation - ba.current_allocation) > 10]
        if significant_changes:
            recommendations.append(
                f"Reallocate budget across {len(significant_changes)} channels for {sum(ba.expected_roi_improvement for ba in significant_changes):.1f}% improvement"
            )

        # Goal-specific recommendations
        if goal == OptimizationGoal.MAXIMIZE_ROI:
            recommendations.append("Focus budget on campaigns with ROI > 100% and reduce spending on negative ROI campaigns")
        elif goal == OptimizationGoal.MINIMIZE_CPA:
            recommendations.append("Optimize targeting and ad creative to reduce cost per acquisition")
        elif goal == OptimizationGoal.MAXIMIZE_CONVERSIONS:
            recommendations.append("Increase budget for high-conversion campaigns and test new audience segments")

        return recommendations

    async def _generate_ai_insights(
        self,
        campaigns: List[CampaignPerformance],
        goal: OptimizationGoal,
        current_roi: float,
        budget_allocations: List[BudgetAllocation]
    ) -> List[str]:
        """Generate AI-powered insights"""

        summary = f"""Marketing Campaign Analysis:
Total Campaigns: {len(campaigns)}
Current ROI: {current_roi:.1f}%
Optimization Goal: {goal.value}
Budget Reallocation Recommendations: {len(budget_allocations)}"""

        prompt = f"""{summary}

Provide 3-5 strategic insights for optimizing these marketing campaigns.
Focus on actionable recommendations.

Return JSON: {{"insights": ["insight 1", "insight 2", ...]}}
Return ONLY valid JSON."""

        try:
            # Get LLM parameters from module config
            llm_config = self.config.get('llm', {}).get('default', {})
            model = llm_config.get('model', 'gpt-4o-mini')
            temperature = llm_config.get('temperature', 0.3)
            max_tokens = llm_config.get('max_tokens', 200)

            response = await self.llm_service.generate_response(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

            result = json.loads(response.strip())
            return result.get("insights", [])

        except Exception as e:
            logger.warning(f"AI insights generation failed: {e}")
            return []

    def _calculate_projected_roi(
        self,
        current_roi: float,
        budget_allocations: List[BudgetAllocation],
        channel_analyses: List[ChannelPerformanceAnalysis]
    ) -> float:
        """Calculate projected ROI after optimization"""

        # Simple projection: assume 50% of expected improvement is realized
        total_expected_improvement = sum(ba.expected_roi_improvement for ba in budget_allocations)

        projected_roi = current_roi + (total_expected_improvement * 0.5)

        return max(current_roi, projected_roi)  # Never project lower ROI
